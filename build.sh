#!/usr/bin/env bash
# build.sh — Rogue Linux master build pipeline
#
# Phases:
#   1. Download    — fetch all source packages
#   2. Build       — compile cogman (planner, executor, supervisor, daemon)
#   3. Rootfs      — install base packages into rootfs via cogman pipeline
#   4. Install     — copy cogman binaries + config into rootfs
#   5. Test        — run the full validation suite
#
# Usage:
#   ./build.sh [--rootfs DIR] [--dry-run] [--resume] [--no-download]
#              [--no-build] [--no-rootfs] [--no-install] [--no-test]
#              [--skip-phase PHASE]  # PHASE: download|build|rootfs|install|test
#
# Examples:
#   ./build.sh                          # full pipeline, rootfs at ./rootfs
#   ./build.sh --rootfs /mnt/rogue      # custom rootfs location
#   ./build.sh --no-download --resume   # skip download, resume rootfs build
#   ./build.sh --dry-run                # print plan without executing

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────

ROOT="$(cd "$(dirname "$0")" && pwd)"
ROOTFS="$ROOT/rootfs"
LOG_DIR="$ROOT/logs"
LOG_FILE="$LOG_DIR/build-$(date +%Y%m%d-%H%M%S).log"

DO_DOWNLOAD=1
DO_BUILD=1
DO_ROOTFS=1
DO_INSTALL=1
DO_TEST=1
DRY_RUN=0
RESUME=0

# ── Colour helpers ────────────────────────────────────────────────

RED='\033[91m'; GRN='\033[92m'; YLW='\033[93m'
CYN='\033[96m'; WHT='\033[97m'; DIM='\033[90m'; RST='\033[0m'; BOLD='\033[1m'

log() {
    local level="$1"; shift
    local ts; ts="$(date '+%H:%M:%S')"
    local line="[$ts][$level] $*"
    echo "$line" >> "$LOG_FILE"
    case "$level" in
        INFO)  printf "${DIM}[%s]${RST} ${CYN}${BOLD}▐ INFO ▌${RST} ${WHT}%s${RST}\n" "$ts" "$*" ;;
        OK)    printf "${DIM}[%s]${RST} ${GRN}${BOLD}▐  OK  ▌${RST} ${WHT}%s${RST}\n" "$ts" "$*" ;;
        WARN)  printf "${DIM}[%s]${RST} ${YLW}${BOLD}▐ WARN ▌${RST} ${YLW}%s${RST}\n" "$ts" "$*" ;;
        ERROR) printf "${DIM}[%s]${RST} ${RED}${BOLD}▐ FAIL ▌${RST} ${RED}%s${RST}\n" "$ts" "$*" ;;
        PHASE) printf "\n${DIM}[%s]${RST} ${BOLD}══════ %s ══════${RST}\n"            "$ts" "$*" ;;
    esac
}

die() { log ERROR "$*"; exit "${2:-1}"; }

# ── Argument parsing ──────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --rootfs)       ROOTFS="$2";  shift 2 ;;
        --dry-run)      DRY_RUN=1;    shift   ;;
        --resume)       RESUME=1;     shift   ;;
        --no-download)  DO_DOWNLOAD=0; shift  ;;
        --no-build)     DO_BUILD=0;   shift   ;;
        --no-rootfs)    DO_ROOTFS=0;  shift   ;;
        --no-install)   DO_INSTALL=0; shift   ;;
        --no-test)      DO_TEST=0;    shift   ;;
        --skip-phase)
            case "$2" in
                download) DO_DOWNLOAD=0 ;;
                build)    DO_BUILD=0    ;;
                rootfs)   DO_ROOTFS=0  ;;
                install)  DO_INSTALL=0 ;;
                test)     DO_TEST=0    ;;
                *) die "Unknown phase: $2" ;;
            esac
            shift 2 ;;
        -h|--help)
            sed -n '3,17p' "$0" | sed 's/^# \?//'
            exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
done

mkdir -p "$LOG_DIR"

log INFO "Rogue Linux Build Pipeline"
log INFO "Root      : $ROOT"
log INFO "Rootfs    : $ROOTFS"
log INFO "Log       : $LOG_FILE"
log INFO "Dry run   : $([ "$DRY_RUN" -eq 1 ] && echo YES || echo no)"
[[ "$DRY_RUN" -eq 1 ]] && log WARN "DRY RUN — no filesystem changes will be made"

run() {
    log INFO "  $ $*"
    if [[ "$DRY_RUN" -eq 0 ]]; then
        "$@" >> "$LOG_FILE" 2>&1 || die "Command failed: $*"
    fi
}

# ── Phase 1: Download ─────────────────────────────────────────────

if [[ "$DO_DOWNLOAD" -eq 1 ]]; then
    log PHASE "Phase 1 — Download packages"

    [[ -f "$ROOT/down_script.sh" ]] || die "down_script.sh not found"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        log INFO "  [DRY RUN] Would run: bash $ROOT/down_script.sh"
    else
        log INFO "  Running down_script.sh ..."
        bash "$ROOT/down_script.sh" 2>&1 | tee -a "$LOG_FILE" \
            | grep -E '^\[' || true
    fi

    log OK "Phase 1 complete"
fi

# ── Phase 2: Build cogman ─────────────────────────────────────────

if [[ "$DO_BUILD" -eq 1 ]]; then
    log PHASE "Phase 2 — Build cogman"

    # Verify Rust toolchain
    command -v cargo >/dev/null 2>&1 || die "cargo not found — install Rust toolchain"
    command -v cc    >/dev/null 2>&1 || die "C compiler not found"

    log INFO "  Building planner, executor, supervisor, cogman daemon ..."

    if [[ "$DRY_RUN" -eq 1 ]]; then
        log INFO "  [DRY RUN] Would run: make all"
    else
        make -C "$ROOT" all 2>&1 | tee -a "$LOG_FILE" | tail -5 || die "make all failed"
    fi

    # Verify expected binaries exist
    for bin in cogman cogman-planner cogman-executor cogman-supervisor cogman-ctl; do
        if [[ "$DRY_RUN" -eq 0 ]]; then
            [[ -x "$ROOT/bin/$bin" ]] || die "Build failed: bin/$bin not found"
        fi
    done

    log OK "Phase 2 complete — cogman binaries in bin/"
fi

# ── Phase 3: Build rootfs packages ───────────────────────────────

if [[ "$DO_ROOTFS" -eq 1 ]]; then
    log PHASE "Phase 3 — Build rootfs packages"

    ROOTFS_SCRIPT="$ROOT/scripts/build/rootfs.sh"
    [[ -f "$ROOTFS_SCRIPT" ]] || die "rootfs build script not found: $ROOTFS_SCRIPT"

    ROOTFS_FLAGS=("--rootfs" "$ROOTFS" "--packages-dir" "$ROOT/packages")
    [[ "$RESUME"  -eq 1 ]] && ROOTFS_FLAGS+=("--resume")
    [[ "$DRY_RUN" -eq 1 ]] && ROOTFS_FLAGS+=("--dry-run")

    log INFO "  Running rootfs.sh ${ROOTFS_FLAGS[*]}"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        log INFO "  [DRY RUN] Would run: bash $ROOTFS_SCRIPT ${ROOTFS_FLAGS[*]}"
    else
        bash "$ROOTFS_SCRIPT" "${ROOTFS_FLAGS[@]}" 2>&1 | tee -a "$LOG_FILE" \
            | grep -E '▐' || true
    fi

    log OK "Phase 3 complete"
fi

# ── Phase 4: Install cogman into rootfs ───────────────────────────

if [[ "$DO_INSTALL" -eq 1 ]]; then
    log PHASE "Phase 4 — Install cogman into rootfs"

    USR_BIN="$ROOTFS/usr/bin"
    ETC_COGMAN="$ROOTFS/etc/cogman"

    if [[ "$DRY_RUN" -eq 0 ]]; then
        mkdir -p "$USR_BIN" "$ETC_COGMAN/plans" "$ETC_COGMAN/services"
    fi

    # Binary map: src (bin/) → dest name in rootfs/usr/bin/
    declare -A BINS=(
        [cogman]="cogman"
        [cogman-planner]="cogman-planner"
        [cogman-executor]="cogman-exec"
        [cogman-supervisor]="cogman-supervisor"
        [cogman-ctl]="cogman-ctl"
    )

    for src_name in "${!BINS[@]}"; do
        src="$ROOT/bin/$src_name"
        dest="$USR_BIN/${BINS[$src_name]}"
        if [[ "$DRY_RUN" -eq 0 ]]; then
            [[ -x "$src" ]] || die "Missing binary: $src"
            cp -f "$src" "$dest"
            chmod 755 "$dest"
            log INFO "  Installed: usr/bin/${BINS[$src_name]}"
        else
            log INFO "  [DRY RUN] Would install: $src_name → rootfs/usr/bin/${BINS[$src_name]}"
        fi
    done

    # Convenience symlink: cogman_planner → cogman-planner (legacy)
    if [[ "$DRY_RUN" -eq 0 ]]; then
        ln -sf cogman-planner "$USR_BIN/cogman_planner" 2>/dev/null || true
    fi

    # Seed etc/cogman config tree from the project's cogman config if present
    COGMAN_ETC_SRC="$ROOT/cogman/etc"
    if [[ -d "$COGMAN_ETC_SRC" ]] && [[ "$DRY_RUN" -eq 0 ]]; then
        cp -rn "$COGMAN_ETC_SRC/." "$ETC_COGMAN/" 2>/dev/null || true
        log INFO "  Seeded etc/cogman from cogman/etc/"
    fi

    log OK "Phase 4 complete — cogman installed in $ROOTFS/usr/bin/"
fi

# ── Phase 5: Test ─────────────────────────────────────────────────

if [[ "$DO_TEST" -eq 1 ]]; then
    log PHASE "Phase 5 — Run validation suite"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        log INFO "  [DRY RUN] Would run: make test"
    else
        log INFO "  Running make test ..."
        make -C "$ROOT" test 2>&1 | tee -a "$LOG_FILE" || die "Test suite failed — see $LOG_FILE"
    fi

    log OK "Phase 5 complete — all tests passed"
fi

# ── Summary ───────────────────────────────────────────────────────

echo ""
log INFO "════════════════════════════════"
log OK   "Build pipeline complete"
log INFO "Rootfs  : $ROOTFS"
log INFO "Log     : $LOG_FILE"
log INFO "════════════════════════════════"
