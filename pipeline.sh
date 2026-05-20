#!/usr/bin/env bash
# pipeline.sh — Rogue Linux modular development pipeline
#
# Usage:
#   ./pipeline.sh [FLAGS] STAGE [STAGE...]
#   ./pipeline.sh status
#   ./pipeline.sh clean [STAGE|all]
#
# Stages (run in any combination):
#   deps        Install host build dependencies (apt-get)
#   cogman      Build cogman suite (Rust planner + C executor/supervisor)
#   kernel      Build Linux 6.6.75 kernel
#   sync        Sync cogman bins → rootfs, fix busybox, strip debug syms, copy pentest tools
#   initramfs   Pack rootfs into cpio.gz initramfs
#   disk        Build GPT disk image (EFI + ext4 root)    [needs sudo]
#   iso         Build hybrid BIOS/UEFI ISO                [needs sudo]
#   pentest     Verify pentest tools (nmap/tcpdump/socat) are in rootfs with all deps
#   verify      Headless QEMU boot verification (boot → milestone checks → pass/fail)
#   verify-x11  Headless X11 verification (Xorg+DWM running checks)
#   test        Run cogman test suite
#   boot        Launch QEMU (--mode x11 for initramfs X11 graphical)
#   all         Run: cogman kernel sync pentest initramfs disk iso
#   rebuild     Clean everything, then run: all
#   ci          Run: cogman kernel test sync pentest initramfs verify verify-x11
#
# Flags:
#   --force         Rebuild even if artifacts are up to date
#   --no-deps       Skip auto-running prerequisite stages
#   --minimal       Use minimal services set (initramfs + boot)
#   --mode MODE     Boot mode: x11 | disk | iso | console | shell (default: x11)
#   --size MB       Disk image size in MB (default: 1024)
#   --jobs N        Parallel build jobs (default: nproc)
#   --timeout N     Verify timeout in seconds (default: 60)
#   -v, --verbose   Show full sub-command output
#   -h, --help      Show this help

# END-HELP

set -euo pipefail

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD="$ROOT/build"
ROOTFS="$ROOT/rootfs"
BIN="$ROOT/bin"

# ── Defaults ─────────────────────────────────────────────────────────────────
FORCE=0
NO_DEPS=0
MINIMAL=0
BOOT_MODE="x11"
DISK_SIZE_MB=1024
JOBS="$(nproc)"
VERBOSE=0
VERIFY_TIMEOUT=60

# ── Colors ───────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
    C_RESET='\033[0m'
    C_BOLD='\033[1m'
    C_DIM='\033[2m'
    C_GREEN='\033[32m'
    C_YELLOW='\033[33m'
    C_BLUE='\033[34m'
    C_CYAN='\033[36m'
    C_RED='\033[31m'
    C_MAGENTA='\033[35m'
else
    C_RESET='' C_BOLD='' C_DIM='' C_GREEN='' C_YELLOW=''
    C_BLUE='' C_CYAN='' C_RED='' C_MAGENTA=''
fi

# ── Helpers ──────────────────────────────────────────────────────────────────
log()    { printf "${C_BOLD}${C_BLUE}[pipeline]${C_RESET} %s\n" "$*"; }
ok()     { printf "${C_GREEN}  ✓${C_RESET} %s\n" "$*"; }
warn()   { printf "${C_YELLOW}  !${C_RESET} %s\n" "$*"; }
err()    { printf "${C_RED}  ✗${C_RESET} %s\n" "$*" >&2; }
skip()   { printf "${C_DIM}  ~${C_RESET} %s ${C_DIM}(skip — use --force to rebuild)${C_RESET}\n" "$*"; }
info()   { printf "    ${C_DIM}%s${C_RESET}\n" "$*"; }
divider(){ printf "${C_DIM}%s${C_RESET}\n" "────────────────────────────────────────────────────"; }

die() { err "$*"; exit 1; }

need_sudo() {
    if [ "$(id -u)" != "0" ]; then
        log "Stage requires root — re-running with sudo..."
        exec sudo bash "${BASH_SOURCE[0]}" "${_ORIG_ARGS[@]}"
    fi
}

run() {
    if [ "$VERBOSE" = "1" ]; then
        "$@"
    else
        "$@" 2>&1 | tail -5 || true
    fi
}

elapsed() {
    local secs=$(( SECONDS - _STAGE_START ))
    printf "%dm%02ds" $(( secs / 60 )) $(( secs % 60 ))
}

# Freshness check: is artifact newer than all sources in a dir?
fresh() {
    local artifact="$1" src_dir="$2"
    [ -e "$artifact" ] || return 1
    [ "$FORCE" = "1" ] && return 1
    if [ -n "$src_dir" ] && [ -d "$src_dir" ]; then
        # artifact must be newer than newest source file
        local newest_src
        newest_src=$(find "$src_dir" -newer "$artifact" -type f 2>/dev/null | head -1 || true)
        [ -z "$newest_src" ]
    else
        return 0
    fi
}

# ── Stage: deps ──────────────────────────────────────────────────────────────
stage_deps() {
    need_sudo
    log "Installing host build dependencies..."
    apt-get install -y \
        bison flex bc \
        libssl-dev libelf-dev \
        gcc make binutils \
        grub-efi-amd64-bin grub-pc-bin grub-common \
        xorriso mtools dosfstools gdisk \
        squashfs-tools e2fsprogs \
        libx11-dev libxft-dev libxinerama-dev \
        libfreetype-dev libfontconfig1-dev \
        cargo rustc \
        qemu-system-x86 ovmf 2>&1 | grep -E "^(Get|Unpacking|Setting|E:)" || true
    ok "All dependencies installed"
}

# ── Stage: cogman ────────────────────────────────────────────────────────────
stage_cogman() {
    local SRC="$ROOT/cogman/src"
    if fresh "$BIN/cogman" "$SRC" && fresh "$BIN/cogman-supervisor" "$SRC"; then
        skip "cogman (all binaries up to date)"; return 0
    fi
    log "Building cogman suite (Rust + C, jobs=$JOBS)..."
    run make -C "$ROOT" all -j"$JOBS"
    # Strip debug symbols from large Rust binaries to keep initramfs small
    # (cogman debug build is 22MB; stripped is 3MB — 7x smaller)
    for b in cogman cogman-planner; do
        if file "$BIN/$b" | grep -q "not stripped"; then
            strip --strip-debug "$BIN/$b" 2>/dev/null && \
                info "stripped: $b → $(du -h $BIN/$b | cut -f1)"
        fi
    done
    ok "cogman  → $BIN/cogman  ($(du -h $BIN/cogman | cut -f1))"
    ok "planner → $BIN/cogman-planner  ($(du -h $BIN/cogman-planner | cut -f1))"
    ok "exectr  → $BIN/cogman-executor"
    ok "supvsr  → $BIN/cogman-supervisor"
    ok "ctl     → $BIN/cogman-ctl"
}

# ── Stage: kernel ────────────────────────────────────────────────────────────
stage_kernel() {
    local VMLINUZ="$ROOTFS/boot/vmlinuz-6.6.75"
    local KCONFIG="$BUILD/kernel.config"
    if fresh "$VMLINUZ" "$BUILD/kernel/linux-6.6.75"; then
        skip "kernel ($VMLINUZ)"; return 0
    fi
    log "Building Linux 6.6.75 kernel (jobs=$JOBS)..."
    MAKEFLAGS="-j$JOBS" run bash "$BUILD/build-kernel.sh"
    ok "kernel → $VMLINUZ  ($(du -h "$VMLINUZ" | cut -f1))"
}

# ── Stage: sync ──────────────────────────────────────────────────────────────
stage_sync() {
    log "Syncing binaries into rootfs + verifying rootfs integrity..."
    local changed=0

    # 1. cogman binaries
    local bins=(cogman cogman-planner cogman-executor cogman-supervisor cogman-ctl)
    for b in "${bins[@]}"; do
        local src="$BIN/$b" dst="$ROOTFS/usr/bin/$b"
        if [ ! -f "$src" ]; then
            warn "$b not in $BIN — run cogman stage first"
            continue
        fi
        if [ ! -f "$dst" ] || ! cmp -s "$src" "$dst" || [ "$FORCE" = "1" ]; then
            \cp -f "$src" "$dst"
            ok "sync: $b → rootfs/usr/bin/"
            changed=$(( changed + 1 ))
        fi
    done

    # 2. /init symlink (PID 1 entry point)
    if [ ! -L "$ROOTFS/init" ] || [ "$(readlink $ROOTFS/init)" != "usr/bin/cogman-supervisor" ]; then
        ln -sf usr/bin/cogman-supervisor "$ROOTFS/init"
        ok "created /init → usr/bin/cogman-supervisor"
        changed=$(( changed + 1 ))
    fi

    # 3. Strip debug symbols from cogman binaries (reduces initramfs from ~400MB to ~120MB)
    local stripped=0
    for b in cogman cogman-planner; do
        local dst="$ROOTFS/usr/bin/$b"
        if [ -f "$dst" ] && file "$dst" | grep -q "not stripped"; then
            strip --strip-debug "$dst" 2>/dev/null && \
                { ok "stripped: $b  ($(du -h $dst | cut -f1))"; stripped=$(( stripped + 1 )); }
        fi
    done
    [ "$stripped" -gt 0 ] && ok "$stripped binaries stripped" || info "binaries already stripped"

    # 4. Verify busybox integrity (critical — was corrupted before)
    local bb="$ROOTFS/usr/bin/busybox"
    if ! "$bb" --list 2>/dev/null | grep -q "^sh$"; then
        warn "BUSYBOX CORRUPTED — replacing with host busybox"
        \cp -f /usr/bin/busybox "$bb"
        ok "busybox replaced from host"
        changed=$(( changed + 1 ))
    fi
    local n_applets; n_applets=$("$bb" --list 2>/dev/null | wc -l || echo 0)
    info "busybox: $n_applets applets  ($(du -h $bb | cut -f1))"

    # 5. Ensure pentest tools are in rootfs
    local pentest_ok=1
    for tool_info in "nmap:usr/lib/nmap/nmap" "tcpdump:usr/bin/tcpdump" "socat:usr/bin/socat"; do
        local tool="${tool_info%%:*}" path="${tool_info#*:}"
        if [ ! -f "$ROOTFS/$path" ]; then
            warn "$tool binary missing from rootfs — run: ./pipeline.sh pentest"
            pentest_ok=0
        fi
    done
    [ "$pentest_ok" = "1" ] && ok "pentest tools present in rootfs"

    # 6. Ensure /var/lib/cogman exists
    mkdir -p "$ROOTFS/var/lib/cogman"

    [ "$changed" = "0" ] && skip "rootfs already in sync (use --force to re-sync)"
    return 0
}

# ── Stage: pentest ────────────────────────────────────────────────────────────
stage_pentest() {
    log "Installing and verifying pentest tools in rootfs..."
    local LIBDIR="$ROOTFS/lib/x86_64-linux-gnu"
    local errors=0

    # ── nmap ──────────────────────────────────────────────────────────
    if [ ! -f "$ROOTFS/usr/lib/nmap/nmap" ] || [ "$FORCE" = "1" ]; then
        log "Installing nmap 7.99..."
        [ -f /usr/lib/nmap/nmap ] || die "nmap not installed on host — run: sudo apt-get install nmap"
        mkdir -p "$ROOTFS/usr/lib/nmap"
        \cp -f /usr/lib/nmap/nmap "$ROOTFS/usr/lib/nmap/nmap"
        ok "nmap binary → rootfs/usr/lib/nmap/"
        # Missing libs: liblinear, liblua5.4
        for libinfo in "liblinear.so.4.2.:liblinear.so.4" "liblua5.4.so.0.0.0:liblua5.4.so.0"; do
            local real="${libinfo%%:*}" link="${libinfo#*:}"
            if [ ! -f "$LIBDIR/$real" ] || [ "$FORCE" = "1" ]; then
                \cp -f "/usr/lib/x86_64-linux-gnu/$real" "$LIBDIR/"
                ln -sf "$real" "$LIBDIR/$link"
                ok "lib: $link → $real"
            fi
        done
    else
        skip "nmap ($(du -h $ROOTFS/usr/lib/nmap/nmap | cut -f1))"
    fi

    # ── tcpdump ───────────────────────────────────────────────────────
    if [ ! -f "$ROOTFS/usr/bin/tcpdump" ] || [ "$FORCE" = "1" ]; then
        log "Installing tcpdump..."
        [ -f /usr/bin/tcpdump ] || die "tcpdump not on host — run: sudo apt-get install tcpdump"
        \cp -f /usr/bin/tcpdump "$ROOTFS/usr/bin/tcpdump"
        ok "tcpdump binary → rootfs/usr/bin/"
    else
        skip "tcpdump ($(du -h $ROOTFS/usr/bin/tcpdump | cut -f1))"
    fi

    # ── socat ─────────────────────────────────────────────────────────
    if [ ! -f "$ROOTFS/usr/bin/socat" ] || [ "$FORCE" = "1" ]; then
        log "Installing socat..."
        local socat_bin; socat_bin=$(command -v socat1 2>/dev/null || command -v socat 2>/dev/null)
        [ -n "$socat_bin" ] || die "socat not on host — run: sudo apt-get install socat"
        \cp -f "$socat_bin" "$ROOTFS/usr/bin/socat"
        # socat needs libwrap
        if [ ! -f "$LIBDIR/libwrap.so.0.7.6" ]; then
            \cp -f /usr/lib/x86_64-linux-gnu/libwrap.so.0.7.6 "$LIBDIR/"
            ln -sf libwrap.so.0.7.6 "$LIBDIR/libwrap.so.0"
            ok "lib: libwrap.so.0"
        fi
        ok "socat binary → rootfs/usr/bin/"
    else
        skip "socat ($(du -h $ROOTFS/usr/bin/socat | cut -f1))"
    fi

    # ── Verify all library deps ────────────────────────────────────────
    log "Verifying library dependencies..."
    local dep_check_ok=1
    declare -A TOOL_DEPS=(
        [nmap]="libpcre2-8.so.0 libpcap.so.0.8 libssh2.so.1 libssl.so.3 libcrypto.so.3 libz.so.1 liblinear.so.4 liblua5.4.so.0 libstdc++.so.6 libm.so.6 libgcc_s.so.1 libc.so.6"
        [tcpdump]="libpcap.so.0.8 libcrypto.so.3 libc.so.6"
        [socat]="libwrap.so.0 libssl.so.3 libcrypto.so.3 libc.so.6"
    )
    for tool in nmap tcpdump socat; do
        for lib in ${TOOL_DEPS[$tool]}; do
            if ls "$LIBDIR/$lib" >/dev/null 2>&1; then
                true
            else
                fail "MISSING dep for $tool: $lib"
                errors=$(( errors + 1 ))
                dep_check_ok=0
            fi
        done
    done
    [ "$dep_check_ok" = "1" ] && ok "all library deps satisfied for nmap/tcpdump/socat"

    # ── Fix libpcap symlinks ───────────────────────────────────────────
    [ ! -e "$LIBDIR/libpcap.so.1" ] && ln -sf libpcap.so.1.10.6 "$LIBDIR/libpcap.so.1" && ok "libpcap.so.1 symlink created"

    if [ "$errors" -gt 0 ]; then
        err "$errors library dependency errors — pentest tools may not work in VM"
        return 1
    fi
    ok "pentest stage complete: nmap + tcpdump + socat ready"
}

# ── Stage: verify ─────────────────────────────────────────────────────────────
stage_verify() {
    local mode="minimal"
    [ "$MINIMAL" = "0" ] && mode="full"

    log "Running headless QEMU boot verification (mode=$mode timeout=${VERIFY_TIMEOUT}s)..."
    [ -f "$BUILD/rogue-linux.cpio.gz" ] || die "initramfs not found — run: ./pipeline.sh initramfs"
    [ -f "$ROOTFS/boot/vmlinuz-6.6.75"  ] || die "kernel not found — run: ./pipeline.sh kernel"

    local extra=""
    [ "$VERBOSE" = "1" ] && extra="--debug"
    [ "$MINIMAL" = "1" ] && extra="$extra --mode minimal" || extra="$extra --mode full"

    if bash "$BUILD/verify-boot.sh" --timeout "$VERIFY_TIMEOUT" $extra; then
        ok "Boot verification PASSED"
    else
        err "Boot verification FAILED — see $BUILD/verify-boot.log"
        return 1
    fi
}

# ── Stage: verify-x11 ────────────────────────────────────────────────────────
stage_verify_x11() {
    log "Running headless X11 verification (Xorg+DWM, timeout=${VERIFY_TIMEOUT}s)..."
    [ -f "$BUILD/rogue-linux.cpio.gz" ] || die "initramfs not found — run: ./pipeline.sh initramfs"
    [ -f "$ROOTFS/boot/vmlinuz-6.6.75" ] || die "kernel not found — run: ./pipeline.sh kernel"

    local extra=""
    [ "$VERBOSE" = "1" ] && extra="--debug"

    if bash "$BUILD/verify-x11-headless.sh" --timeout "$VERIFY_TIMEOUT" $extra; then
        ok "X11 verification PASSED — Xorg+DWM confirmed running"
    else
        err "X11 verification FAILED — see $BUILD/verify-x11.log"
        return 1
    fi
}

# ── Stage: initramfs ─────────────────────────────────────────────────────────
stage_initramfs() {
    local OUT="$BUILD/rogue-linux.cpio.gz"
    if fresh "$OUT" "$ROOTFS"; then
        skip "initramfs ($OUT)"; return 0
    fi
    log "Packing rootfs → initramfs..."
    local args=""
    [ "$MINIMAL" = "1" ] && args="--minimal"
    run bash "$BUILD/build-initramfs.sh" $args
    ok "initramfs → $OUT  ($(du -h "$OUT" | cut -f1))"
}

# ── Stage: disk ──────────────────────────────────────────────────────────────
stage_disk() {
    local IMG="$BUILD/rogue-linux-disk.img"
    if fresh "$IMG" "$ROOTFS" && [ "$FORCE" = "0" ]; then
        skip "disk image ($IMG)"; return 0
    fi
    need_sudo
    log "Building GPT disk image (${DISK_SIZE_MB}MB)..."
    run bash "$BUILD/build-disk.sh" "$DISK_SIZE_MB"
    ok "disk → $IMG  ($(du -h "$IMG" | cut -f1))"
}

# ── Stage: iso ───────────────────────────────────────────────────────────────
stage_iso() {
    local ISO="$BUILD/rogue-linux.iso"
    if fresh "$ISO" "$ROOTFS" && [ "$FORCE" = "0" ]; then
        skip "ISO ($ISO)"; return 0
    fi
    need_sudo
    log "Building hybrid BIOS/UEFI ISO..."
    run bash "$BUILD/build-iso.sh"
    ok "ISO → $ISO  ($(du -h "$ISO" | cut -f1))"
}

# ── Stage: test ──────────────────────────────────────────────────────────────
stage_test() {
    log "Running cogman test suite..."
    run make -C "$ROOT" test
    ok "All tests passed"
}

# ── Stage: boot ──────────────────────────────────────────────────────────────
stage_boot() {
    log "Launching QEMU — mode: ${C_CYAN}${BOOT_MODE}${C_RESET}"
    divider
    case "$BOOT_MODE" in
        x11)
            [ -f "$ROOTFS/boot/vmlinuz-6.6.75" ] || die "kernel not found — run: ./pipeline.sh kernel"
            [ -f "$BUILD/rogue-linux-disk.img"  ] || die "disk not found — run: ./pipeline.sh disk"
            exec bash "$BUILD/boot-x11.sh"
            ;;
        x11-init)
            [ -f "$ROOTFS/boot/vmlinuz-6.6.75" ] || die "kernel not found — run: ./pipeline.sh kernel"
            [ -f "$BUILD/rogue-linux.cpio.gz"   ] || die "initramfs not found — run: ./pipeline.sh initramfs"
            exec bash "$BUILD/boot-x11-init.sh"
            ;;
        disk)
            [ -f "$BUILD/rogue-linux-disk.img" ] || die "disk not found — run: ./pipeline.sh disk"
            exec bash "$BUILD/boot-disk.sh"
            ;;
        iso)
            [ -f "$BUILD/rogue-linux.iso" ] || die "ISO not found — run: ./pipeline.sh iso"
            exec bash "$BUILD/boot-iso.sh"
            ;;
        console)
            exec bash "$BUILD/boot-console.sh"
            ;;
        shell)
            exec bash "$BUILD/boot-shell.sh"
            ;;
        minimal)
            exec bash "$BUILD/boot-minimal.sh"
            ;;
        *)
            die "Unknown boot mode '$BOOT_MODE'. Valid: x11 | disk | iso | console | shell | minimal"
            ;;
    esac
}

# ── Stage: status ────────────────────────────────────────────────────────────
stage_status() {
    printf "\n${C_BOLD}  Rogue Linux — Build Status${C_RESET}\n"
    divider

    artifact_row() {
        local label="$1" path="$2" src_dir="${3:-}"
        local state size age
        if [ -e "$path" ]; then
            size=$(du -h "$path" 2>/dev/null | cut -f1)
            age=$(( $(date +%s) - $(stat -c %Y "$path") ))
            local age_str
            if   (( age < 60    )); then age_str="${age}s ago"
            elif (( age < 3600  )); then age_str="$(( age/60 ))m ago"
            elif (( age < 86400 )); then age_str="$(( age/3600 ))h ago"
            else                         age_str="$(( age/86400 ))d ago"
            fi

            if [ -n "$src_dir" ] && [ -d "$src_dir" ]; then
                local stale
                stale=$(find "$src_dir" -newer "$path" -type f 2>/dev/null | head -1 || true)
                if [ -n "$stale" ]; then
                    state="${C_YELLOW}STALE${C_RESET}"
                else
                    state="${C_GREEN}OK${C_RESET}"
                fi
            else
                state="${C_GREEN}OK${C_RESET}"
            fi
            printf "  %-16s  %b  %-8s  %-10s  %s\n" "$label" "$state" "$size" "$age_str" "$path"
        else
            printf "  %-16s  ${C_DIM}missing${C_RESET}  %-8s  %-10s  %s\n" "$label" "" "" "$path"
        fi
    }

    printf "  %-16s  %-9s  %-8s  %-10s  %s\n" "Stage" "Status" "Size" "Age" "Artifact"
    divider
    artifact_row "cogman"      "$BIN/cogman"                       "$ROOT/cogman/src"
    artifact_row "kernel"      "$ROOTFS/boot/vmlinuz-6.6.75"       "$BUILD/kernel/linux-6.6.75"
    artifact_row "initramfs"   "$BUILD/rogue-linux.cpio.gz"        "$ROOTFS"
    artifact_row "disk"        "$BUILD/rogue-linux-disk.img"       "$ROOTFS"
    artifact_row "iso"         "$BUILD/rogue-linux.iso"            "$ROOTFS"
    artifact_row "verify-log"  "$BUILD/verify-boot.log"            ""
    divider

    printf "\n${C_BOLD}  Pentest Tools${C_RESET}\n"
    local LIBDIR="$ROOTFS/lib/x86_64-linux-gnu"
    for tool_path in "nmap:usr/lib/nmap/nmap" "tcpdump:usr/bin/tcpdump" "socat:usr/bin/socat"; do
        local tool="${tool_path%%:*}" path="${tool_path#*:}"
        if [ -f "$ROOTFS/$path" ]; then
            printf "  %-12s  ${C_GREEN}present${C_RESET}  %s\n" "$tool" "$(du -h $ROOTFS/$path | cut -f1)"
        else
            printf "  %-12s  ${C_RED}MISSING${C_RESET}\n" "$tool"
        fi
    done

    # rootfs bin sync check
    printf "\n${C_BOLD}  Rootfs Sync${C_RESET}\n"
    local bins=(cogman cogman-planner cogman-executor cogman-supervisor cogman-ctl)
    for b in "${bins[@]}"; do
        local src="$BIN/$b" dst="$ROOTFS/usr/bin/$b"
        if [ ! -f "$src" ]; then
            printf "  %-24s  ${C_DIM}not built${C_RESET}\n" "$b"
        elif [ ! -f "$dst" ]; then
            printf "  %-24s  ${C_YELLOW}not in rootfs${C_RESET}\n" "$b"
        elif cmp -s "$src" "$dst"; then
            printf "  %-24s  ${C_GREEN}synced${C_RESET}\n" "$b"
        else
            printf "  %-24s  ${C_YELLOW}STALE in rootfs${C_RESET}\n" "$b"
        fi
    done
    printf "\n"
}

# ── Stage: clean ─────────────────────────────────────────────────────────────
stage_clean() {
    local target="${1:-all}"
    case "$target" in
        cogman)
            log "Cleaning cogman artifacts..."
            make -C "$ROOT" clean 2>/dev/null || true
            ok "cogman artifacts removed"
            ;;
        kernel)
            log "Cleaning kernel artifacts..."
            rm -f "$ROOTFS/boot/vmlinuz-6.6.75" \
                  "$ROOTFS/boot/System.map-6.6.75" \
                  "$ROOTFS/boot/config-6.6.75"
            rm -rf "$ROOTFS/lib/modules"
            ok "kernel artifacts removed"
            ;;
        initramfs)
            log "Cleaning initramfs..."
            rm -f "$BUILD/rogue-linux.cpio.gz"
            ok "initramfs removed"
            ;;
        disk)
            log "Cleaning disk image..."
            rm -f "$BUILD/rogue-linux-disk.img"
            ok "disk image removed"
            ;;
        iso)
            log "Cleaning ISO..."
            rm -f "$BUILD/rogue-linux.iso"
            ok "ISO removed"
            ;;
        sync)
            log "Removing synced cogman binaries from rootfs..."
            local bins=(cogman cogman-planner cogman-executor cogman-supervisor cogman-ctl)
            for b in "${bins[@]}"; do rm -f "$ROOTFS/usr/bin/$b"; done
            rm -f "$ROOTFS/init"
            ok "rootfs sync cleaned"
            ;;
        all)
            stage_clean cogman
            stage_clean kernel
            stage_clean initramfs
            stage_clean disk
            stage_clean iso
            stage_clean sync
            ok "All artifacts cleaned"
            ;;
        *)
            die "Unknown clean target '$target'. Valid: cogman | kernel | initramfs | disk | iso | sync | all"
            ;;
    esac
}

# ── Stage dispatcher ─────────────────────────────────────────────────────────
run_stage() {
    local stage="$1"
    _STAGE_START=$SECONDS
    printf "\n${C_BOLD}${C_MAGENTA}▶ stage: ${stage}${C_RESET}\n"
    divider

    case "$stage" in
        deps)       stage_deps ;;
        cogman)     stage_cogman ;;
        kernel)     stage_kernel ;;
        sync)       stage_sync ;;
        pentest)    stage_pentest ;;
        initramfs)  stage_initramfs ;;
        disk)       stage_disk ;;
        iso)        stage_iso ;;
        verify)     stage_verify ;;
        verify-x11) stage_verify_x11 ;;
        test)       stage_test ;;
        boot)       stage_boot ;;  # exec — never returns
        status)     stage_status; return 0 ;;
        clean)      shift; stage_clean "${1:-all}"; return 0 ;;
        *)          die "Unknown stage '$stage'. Run ./pipeline.sh --help for usage." ;;
    esac

    printf "${C_DIM}   done in $(elapsed)${C_RESET}\n"
}

# ── Composite stages ─────────────────────────────────────────────────────────
expand_stage() {
    case "$1" in
        all)     echo "cogman kernel sync pentest initramfs disk iso" ;;
        rebuild) echo "_clean_all cogman kernel sync pentest initramfs disk iso" ;;
        ci)      echo "cogman kernel test sync pentest initramfs verify verify-x11" ;;
        images)  echo "sync initramfs disk iso" ;;
        check)   echo "pentest verify" ;;
        *)       echo "$1" ;;
    esac
}

# ── Argument parsing ─────────────────────────────────────────────────────────
usage() {
    sed -n '2,/^# END-HELP/{ /^# END-HELP/d; s/^# \{0,1\}//; p }' "${BASH_SOURCE[0]}"
    exit 0
}

STAGES=()
_ORIG_ARGS=("$@")

while [[ $# -gt 0 ]]; do
    case "$1" in
        --force)        FORCE=1 ;;
        --no-deps)      NO_DEPS=1 ;;
        --minimal)      MINIMAL=1 ;;
        --mode)         BOOT_MODE="$2"; shift ;;
        --mode=*)       BOOT_MODE="${1#--mode=}" ;;
        --size)         DISK_SIZE_MB="$2"; shift ;;
        --size=*)       DISK_SIZE_MB="${1#--size=}" ;;
        --timeout)      VERIFY_TIMEOUT="$2"; shift ;;
        --timeout=*)    VERIFY_TIMEOUT="${1#--timeout=}" ;;
        --jobs|-j)      JOBS="$2"; shift ;;
        --jobs=*)       JOBS="${1#--jobs=}" ;;
        -v|--verbose)   VERBOSE=1 ;;
        -h|--help)      usage ;;
        clean)
            # clean is special: consume optional next arg as target
            if [[ "${2:-}" =~ ^(cogman|kernel|initramfs|disk|iso|sync|all)$ ]]; then
                STAGES+=("clean:$2"); shift
            else
                STAGES+=("clean:all")
            fi
            ;;
        *)              STAGES+=("$1") ;;
    esac
    shift
done

[ "${#STAGES[@]}" -eq 0 ] && { stage_status; exit 0; }

# ── Main ─────────────────────────────────────────────────────────────────────
PIPELINE_START=$SECONDS

printf "\n${C_BOLD}${C_CYAN}"
printf "╔══════════════════════════════════════════════╗\n"
printf "║        Rogue Linux — Dev Pipeline            ║\n"
printf "╚══════════════════════════════════════════════╝"
printf "${C_RESET}\n"
info "force=$FORCE  minimal=$MINIMAL  jobs=$JOBS  verbose=$VERBOSE"

# Expand composite stage names and run each
EXPANDED=()
for s in "${STAGES[@]}"; do
    if [[ "$s" == clean:* ]]; then
        EXPANDED+=("$s")
    else
        read -ra parts <<< "$(expand_stage "$s")"
        EXPANDED+=("${parts[@]}")
    fi
done

for stage in "${EXPANDED[@]}"; do
    if [[ "$stage" == clean:* ]]; then
        target="${stage#clean:}"
        stage_clean "$target"
    elif [[ "$stage" == "_clean_all" ]]; then
        stage_clean all
    else
        run_stage "$stage"
    fi
done

total=$(( SECONDS - PIPELINE_START ))
printf "\n${C_BOLD}${C_GREEN}Pipeline complete${C_RESET} — total time: %dm%02ds\n\n" \
    $(( total / 60 )) $(( total % 60 ))
