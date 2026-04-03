#!/usr/bin/env bash
# scripts/build/rootfs.sh — Rogue Linux Rootfs Bootstrap
#
# Orchestrates the full rootfs construction pipeline:
#   1. Create the FHS skeleton at $ROOTFS
#   2. Iterate through the base package list in dependency order
#   3. For each package: plan → execute → verify
#
# Usage:
#   ./scripts/build/rootfs.sh [--rootfs /mnt/rogue] [--packages-dir ./packages]
#                             [--native] [--no-cache] [--dry-run] [--resume]
#
# Requirements:
#   - cogman-planner and cogman-executor must be in ./bin/ or $PATH
#   - Package sources must be present under packages/<cat>/<name>/tar/
#
# Exit codes:
#   0  — success
#   1  — argument / environment error
#   2  — FHS skeleton creation failed
#   3  — package planning failed
#   4  — package execution failed

set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────

ROOTFS="/mnt/rogue"
PACKAGES_DIR="$(cd "$(dirname "$0")/../.." && pwd)/packages"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PLANNER="$ROOT_DIR/bin/cogman-planner"
EXECUTOR="$ROOT_DIR/bin/cogman-executor"
NATIVE=0
NO_CACHE=0
DRY_RUN=0
RESUME=0
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/rootfs-$(date +%Y%m%d-%H%M%S).log"

# Colour codes
RED='\033[91m'; GRN='\033[92m'; YLW='\033[93m'
CYN='\033[96m'; WHT='\033[97m'; DIM='\033[90m'; RST='\033[0m'; BOLD='\033[1m'

# ── Argument parsing ──────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --rootfs)        ROOTFS="$2";        shift 2 ;;
        --packages-dir)  PACKAGES_DIR="$2";  shift 2 ;;
        --native)        NATIVE=1;           shift   ;;
        --no-cache)      NO_CACHE=1;         shift   ;;
        --dry-run)       DRY_RUN=1;          shift   ;;
        --resume)        RESUME=1;           shift   ;;
        -h|--help)
            sed -n '2,20p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown argument: $1${RST}" >&2
            exit 1
            ;;
    esac
done

# ── Logging helpers ───────────────────────────────────────────────

mkdir -p "$LOG_DIR"

log() {
    local level="$1"; shift
    local ts; ts="$(date '+%H:%M:%S')"
    local line="[$ts] [$level] $*"
    echo "$line" >> "$LOG_FILE"
    case "$level" in
        INFO)  echo -e "${DIM}[$ts]${RST} ${CYN}${BOLD}▐ BOOT ▌${RST} ${WHT}$*${RST}" ;;
        OK)    echo -e "${DIM}[$ts]${RST} ${GRN}${BOLD}▐  OK  ▌${RST} ${WHT}$*${RST}" ;;
        WARN)  echo -e "${DIM}[$ts]${RST} ${YLW}${BOLD}▐ WARN ▌${RST} ${YLW}$*${RST}" ;;
        ERROR) echo -e "${DIM}[$ts]${RST} ${RED}${BOLD}▐ FAIL ▌${RST} ${RED}$*${RST}" ;;
    esac
}

die() { log ERROR "$*"; exit "${2:-1}"; }

# ── Pre-flight checks ─────────────────────────────────────────────

log INFO "Rogue Linux Rootfs Bootstrap"
log INFO "Rootfs target  : $ROOTFS"
log INFO "Packages dir   : $PACKAGES_DIR"
log INFO "Variant        : $([ "$NATIVE" -eq 1 ] && echo 'native (compile)' || echo 'binary (prebuilt)')"
log INFO "Dry run        : $([ "$DRY_RUN" -eq 1 ] && echo 'YES — no changes will be made' || echo 'no')"
log INFO "Log file       : $LOG_FILE"

[[ -x "$PLANNER"  ]] || die "cogman-planner not found or not executable: $PLANNER" 1
[[ -x "$EXECUTOR" ]] || die "cogman-executor not found or not executable: $EXECUTOR" 1
[[ -d "$PACKAGES_DIR" ]] || die "Packages directory not found: $PACKAGES_DIR" 1

if [[ "$DRY_RUN" -eq 0 ]] && [[ "$EUID" -ne 0 ]] && [[ "$ROOTFS" == /mnt/* ]]; then
    log WARN "Writing to $ROOTFS as non-root. This may fail for system paths."
fi

# ── FHS skeleton ──────────────────────────────────────────────────

fhs_dirs=(
    usr/bin usr/sbin usr/lib usr/lib64 usr/libexec
    usr/include usr/share/doc usr/share/man
    usr/local/bin usr/local/lib usr/local/share
    bin sbin lib lib64
    etc etc/ld.so.conf.d etc/sysconfig
    var/log var/run var/cache var/tmp var/lib
    tmp proc sys dev run
    boot boot/efi
    home root
    opt srv mnt media
)

log INFO "Creating FHS directory skeleton under $ROOTFS"

if [[ "$DRY_RUN" -eq 0 ]]; then
    for d in "${fhs_dirs[@]}"; do
        if ! mkdir -p "$ROOTFS/$d" 2>/dev/null; then
            die "Failed to create $ROOTFS/$d — check permissions or use sudo" 2
        fi
    done

    # Compatibility symlinks (FHS 3.0)
    for link in bin sbin lib lib64; do
        target="$ROOTFS/$link"
        if [[ ! -L "$target" ]] && [[ -d "$target" ]]; then
            rmdir "$target" 2>/dev/null || true
        fi
        if [[ ! -e "$target" ]]; then
            ln -sf "usr/$link" "$target"
        fi
    done

    # Essential /etc files
    [[ -f "$ROOTFS/etc/hostname"  ]] || echo "rogue" > "$ROOTFS/etc/hostname"
    [[ -f "$ROOTFS/etc/os-release" ]] || cat > "$ROOTFS/etc/os-release" << 'OSRELEASE'
NAME="Rogue Linux"
VERSION="1.0"
ID=rogue
PRETTY_NAME="Rogue Linux 1.0"
HOME_URL="https://rogue-linux.dev"
OSRELEASE

    log OK "FHS skeleton created"
else
    log INFO "[DRY RUN] Would create ${#fhs_dirs[@]} FHS directories under $ROOTFS"
fi

# ── Package installation helpers ──────────────────────────────────

PLAN_DIR="$ROOTFS/.cogman-plans"
STATE_DIR="$ROOTFS/.cogman-state"

[[ "$DRY_RUN" -eq 0 ]] && mkdir -p "$PLAN_DIR" "$STATE_DIR"

# Returns 0 if package was already successfully installed (resume mode).
is_installed() {
    local pkg="$1"
    [[ "$RESUME" -eq 1 ]] && [[ -f "$STATE_DIR/${pkg//\//_}.done" ]]
}

mark_installed() {
    local pkg="$1"
    [[ "$DRY_RUN" -eq 0 ]] && touch "$STATE_DIR/${pkg//\//_}.done"
}

install_package() {
    local toml_path="$1"
    local cat_name
    # Derive "category/name" from the path: packages/<cat>/<name>/<name>.toml
    cat_name="$(basename "$(dirname "$(dirname "$toml_path")")")/$(basename "$(dirname "$toml_path")")"

    if is_installed "$cat_name"; then
        log INFO "  [SKIP] $cat_name (already installed)"
        return 0
    fi

    local plan_file="$PLAN_DIR/${cat_name//\//_}.plan"
    local planner_flags=("build" "$toml_path" "--output" "$plan_file" "--rootfs" "$ROOTFS")

    [[ "$NATIVE"   -eq 1 ]] && planner_flags+=("--build")
    [[ "$NO_CACHE" -eq 1 ]] && planner_flags+=("--no-cache")

    log INFO "  Planning  : $cat_name"

    if [[ "$DRY_RUN" -eq 0 ]]; then
        if ! "$PLANNER" "${planner_flags[@]}" >> "$LOG_FILE" 2>&1; then
            log ERROR "  Planning FAILED for $cat_name — see $LOG_FILE"
            return 3
        fi

        log INFO "  Executing : $cat_name"
        if ! "$EXECUTOR" "$plan_file" >> "$LOG_FILE" 2>&1; then
            log ERROR "  Execution FAILED for $cat_name — see $LOG_FILE"
            return 4
        fi

        mark_installed "$cat_name"
        log OK "  Installed : $cat_name"
    else
        log INFO "  [DRY RUN] Would plan + execute: $cat_name"
    fi
}

# ── Build order: base system packages ─────────────────────────────
#
# Order matters — listed dependency-first. The planner also enforces
# this via topological sort, but we iterate in a known-safe order here
# to give clearer progress output.
#
# To add packages, place their .toml in packages/<cat>/<name>/
# and add the path to this list.

log INFO "Scanning package tree: $PACKAGES_DIR"

# Collect all .toml files grouped by category, in dependency-safe order
ORDERED_CATEGORIES=(
    toolchain   # gcc, glibc, binutils, make
    base        # bash, coreutils, util-linux, etc.
    libs        # zlib, openssl, curl, etc.
    security    # openssh, cryptsetup, wireguard
    shells      # zsh, fish, dash
    editors     # vim, neovim, nano
    tools       # ripgrep, bat, fzf, tmux
    ui          # dwm, alacritty, dmenu
    extra       # everything else
)

FAILED_PKGS=()
INSTALLED=0
SKIPPED=0

for cat in "${ORDERED_CATEGORIES[@]}"; do
    cat_dir="$PACKAGES_DIR/$cat"
    [[ -d "$cat_dir" ]] || continue

    while IFS= read -r -d '' toml; do
        rc=0
        install_package "$toml" || rc=$?
        case $rc in
            0) ((INSTALLED++)) ;;
            3) FAILED_PKGS+=("$toml (plan)");   ((SKIPPED++)) ;;
            4) FAILED_PKGS+=("$toml (execute)"); ((SKIPPED++)) ;;
        esac
    done < <(find "$cat_dir" -name "*.toml" -print0 | sort -z)
done

# Also handle any packages not in the ordered categories
while IFS= read -r -d '' toml; do
    # Skip if already handled above
    already=0
    for cat in "${ORDERED_CATEGORIES[@]}"; do
        [[ "$toml" == "$PACKAGES_DIR/$cat"* ]] && { already=1; break; }
    done
    [[ $already -eq 1 ]] && continue

    rc=0
    install_package "$toml" || rc=$?
    case $rc in
        0) ((INSTALLED++)) ;;
        3|4) FAILED_PKGS+=("$toml"); ((SKIPPED++)) ;;
    esac
done < <(find "$PACKAGES_DIR" -name "*.toml" -print0 | sort -z)

# ── Summary ───────────────────────────────────────────────────────

echo ""
log INFO "═══════════════════════════════════════════"
log INFO " Rootfs Bootstrap Complete"
log INFO "═══════════════════════════════════════════"
log INFO " Rootfs     : $ROOTFS"
log OK   " Installed  : $INSTALLED package(s)"

if [[ "${#FAILED_PKGS[@]}" -gt 0 ]]; then
    log WARN " Failed     : ${#FAILED_PKGS[@]} package(s)"
    for p in "${FAILED_PKGS[@]}"; do
        log WARN "   - $p"
    done
    log WARN " Check $LOG_FILE for details"
else
    log OK  " All packages installed successfully"
fi

if [[ "$DRY_RUN" -eq 0 ]] && [[ $INSTALLED -gt 0 ]]; then
    log INFO "Next steps:"
    log INFO "  1. Configure bootloader:  grub-install --target=i386-pc $ROOTFS"
    log INFO "  2. Set root password:     chroot $ROOTFS passwd root"
    log INFO "  3. Configure network:     edit $ROOTFS/etc/sysconfig/network"
    log INFO "  4. Create initramfs:      chroot $ROOTFS dracut /boot/initramfs.img"
fi

[[ "${#FAILED_PKGS[@]}" -gt 0 ]] && exit 4 || exit 0
