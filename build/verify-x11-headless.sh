#!/usr/bin/env bash
# verify-x11-headless.sh — Headless X11 boot verification
#
# Boots the full services (including x11) with virtio-vga in headless mode.
# Captures serial output and looks for X11 startup milestones.
#
# Usage: bash build/verify-x11-headless.sh [--timeout N] [--debug]

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
KERNEL="$ROOT/rootfs/boot/vmlinuz-6.6.75"
INITRD="$BUILD/rogue-linux.cpio.gz"
LOG="$BUILD/verify-x11.log"

TIMEOUT=90
DEBUG=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --timeout) TIMEOUT="$2"; shift ;;
        --debug)   DEBUG=1 ;;
    esac
    shift
done

for f in "$KERNEL" "$INITRD"; do
    [ -f "$f" ] || { echo "ERROR: missing $f"; exit 1; }
done

echo ""
echo "╔═════════════════════════════════════════════════════════╗"
echo "║   Rogue Linux — X11 Headless Verification              ║"
echo "╚═════════════════════════════════════════════════════════╝"
echo "  initrd  : $INITRD  ($(du -h "$INITRD" | cut -f1))"
echo "  timeout : ${TIMEOUT}s"
echo "  log     : $LOG"
echo ""

KVM_ARGS=""
[ -e /dev/kvm ] && KVM_ARGS="-enable-kvm -cpu host"

: > "$LOG"

echo "Launching QEMU with virtio-vga (headless, no display window)..."
timeout "${TIMEOUT}s" qemu-system-x86_64 \
    $KVM_ARGS \
    -m 1G \
    -smp 2 \
    -no-reboot \
    -kernel "$KERNEL" \
    -initrd "$INITRD" \
    -append "rdinit=/init console=ttyS0 -- --services-dir /etc/cogman/services" \
    -vga virtio \
    -display none \
    -device virtio-keyboard-pci \
    -device virtio-mouse-pci \
    -device virtio-net-pci,netdev=eth0 \
    -netdev user,id=eth0 \
    -serial "file:$LOG" \
    2>/dev/null || true

echo ""
echo "── Serial log: $(wc -l < "$LOG") lines ─────────────────────────────"
if [ "$DEBUG" = "1" ]; then
    cat "$LOG"
    echo ""
fi

PASS=0; FAIL=0; WARN=0

check() {
    local pat="$1" label="$2"
    if grep -qE "$pat" "$LOG" 2>/dev/null; then
        printf "  \033[32mPASS\033[0m  %s\n" "$label"
        PASS=$((PASS+1))
    else
        printf "  \033[31mFAIL\033[0m  %s\n" "$label"
        FAIL=$((FAIL+1))
    fi
}
warn_check() {
    local pat="$1" label="$2"
    if grep -qE "$pat" "$LOG" 2>/dev/null; then
        printf "  \033[32mPASS\033[0m  %s\n" "$label"
        PASS=$((PASS+1))
    else
        printf "  \033[33mWARN\033[0m  %s\n" "$label"
        WARN=$((WARN+1))
    fi
}

echo ""
echo "── Base system milestones ───────────────────────────────────────"
check "cogman-supervisor starting \(pid=1\)"  "cogman PID 1 confirmed"
check "Rogue Linux 1.0 — booted OK"           "rcS completed"
check "svc_spawn: started mdev"               "mdev (device manager) started"
check "svc_spawn: started input-probe"        "input-probe started"
check "input-probe-done"                      "input-probe: found /dev/input devices"

echo ""
echo "── X11 milestones ───────────────────────────────────────────────"
check "svc_spawn: started x11"               "x11 service spawned"
check "startx: kbd=/dev/input/"              "startx: keyboard device detected"
warn_check "startx: ptr=/dev/input/"         "startx: pointer device detected"
warn_check "X11-DIAG START"                  "x11-diag diagnostic ran"
warn_check "DRM|modesetting|virtio|Screen"   "Xorg initialised display"

echo ""
echo "── Error checks ────────────────────────────────────────────────"
if grep -qE "Kernel panic|Oops:|BUG:" "$LOG" 2>/dev/null; then
    printf "  \033[31mFAIL\033[0m  Kernel panic / oops\n"
    FAIL=$((FAIL+1))
else
    printf "  \033[32mPASS\033[0m  No kernel panic\n"
    PASS=$((PASS+1))
fi

if grep -qE "\(EE\)" "$LOG" 2>/dev/null; then
    EE_LINES=$(grep -c "(EE)" "$LOG" 2>/dev/null; true)
    EE_LINES="${EE_LINES//[^0-9]/}"; EE_LINES="${EE_LINES:-0}"
    printf "  \033[33mWARN\033[0m  Xorg EE errors: %s (check log)\n" "$EE_LINES"
    WARN=$((WARN+1))
else
    printf "  \033[32mPASS\033[0m  No Xorg (EE) errors in serial\n"
    PASS=$((PASS+1))
fi

# Show x11-diag output if present
if grep -q "X11-DIAG START" "$LOG" 2>/dev/null; then
    echo ""
    echo "── x11-diag output ─────────────────────────────────────────────"
    sed -n '/X11-DIAG START/,/X11-DIAG END/p' "$LOG" | head -30
fi

# Show X11 failure reason if startx failed
if ! grep -q "svc_spawn: started x11" "$LOG" 2>/dev/null || \
   grep -qE "service 'x11'.*exited, code=[^0]" "$LOG" 2>/dev/null; then
    echo ""
    echo "── X11 failure context (last 20 x11/Xorg lines) ────────────────"
    grep -E "x11|Xorg|startx|evdev|modesetting|xinit|EE|WW|Fatal" "$LOG" 2>/dev/null | tail -20
fi

echo ""
echo "────────────────────────────────────────────────────────────────"
printf "  PASS: %d  |  FAIL: %d  |  WARN: %d\n" "$PASS" "$FAIL" "$WARN"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo "RESULT: FAIL — see $LOG"
    exit 1
else
    echo "RESULT: PASS"
    [ "$WARN" -gt 0 ] && echo "  (with $WARN warning(s))"
    exit 0
fi
