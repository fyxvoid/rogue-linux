#!/usr/bin/env bash
# verify-boot.sh — Headless QEMU boot verification for Rogue Linux
#
# Boots the VM with initramfs in console-only mode, captures serial output,
# and checks for expected milestone strings.  Exits 0 on pass, 1 on fail.
#
# Usage:
#   bash build/verify-boot.sh [--timeout N] [--mode console|minimal] [--debug]
#
# Requires: qemu-system-x86_64, kernel + initramfs already built.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
KERNEL="$ROOT/rootfs/boot/vmlinuz-6.6.75"
INITRD="$BUILD/rogue-linux.cpio.gz"
LOG="$BUILD/verify-boot.log"
SERVICES_DIR="/etc/cogman/services-minimal"

TIMEOUT=60
MODE="minimal"
DEBUG=0
EXTRA_CMDLINE=""

# ── Argument parsing ──────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --timeout)  TIMEOUT="$2"; shift ;;
        --mode)     MODE="$2"; shift ;;
        --debug)    DEBUG=1 ;;
        --pentest)  SERVICES_DIR="/etc/cogman/services"
                    EXTRA_CMDLINE="pentest_verify=1"
                    TIMEOUT=90 ;;
        *) ;;
    esac
    shift
done

if [ "$MODE" = "full" ]; then
    SERVICES_DIR="/etc/cogman/services"
fi

# ── Preflight ─────────────────────────────────────────────────────────
for f in "$KERNEL" "$INITRD"; do
    [ -f "$f" ] || { echo "ERROR: missing $f — run pipeline first"; exit 1; }
done

command -v qemu-system-x86_64 >/dev/null || { echo "ERROR: qemu-system-x86_64 not found"; exit 1; }

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   Rogue Linux — Headless Boot Verification            ║"
echo "╚════════════════════════════════════════════════════════╝"
echo "  kernel  : $KERNEL  ($(du -h "$KERNEL" | cut -f1))"
echo "  initrd  : $INITRD  ($(du -h "$INITRD" | cut -f1))"
echo "  services: $SERVICES_DIR"
echo "  timeout : ${TIMEOUT}s"
echo "  log     : $LOG"
echo ""

# ── Expected milestone strings ────────────────────────────────────────
# The verify logic checks for these strings in the serial output.
declare -a MILESTONES=(
    "cogman-supervisor starting"          # PID 1 started
    "loaded.*service"                     # services loaded
    "svc_spawn: started rcs"              # rcs started (rcS init script)
    "Rogue Linux 1.0 — booted OK"         # rcS completed
    "svc_spawn: started mdev"             # device manager started
    "svc_spawn: started tty1"             # getty on tty1
)

# Extra milestones when running full services
if [ "$MODE" = "full" ] || [ -n "$EXTRA_CMDLINE" ]; then
    MILESTONES+=(
        "svc_spawn: started firewall"
        "svc_spawn: started eth0-dhcp"
    )
fi

# ── QEMU launch ──────────────────────────────────────────────────────
KVM_ARGS=""
if [ -e /dev/kvm ]; then
    KVM_ARGS="-enable-kvm -cpu host"
fi

QEMU_CMDLINE="rdinit=/init console=ttyS0 quiet $EXTRA_CMDLINE -- --services-dir $SERVICES_DIR"
[ "$DEBUG" = "1" ] && QEMU_CMDLINE="${QEMU_CMDLINE/ quiet/}"

echo "Launching QEMU (headless, ${TIMEOUT}s timeout)..."
: > "$LOG"

# Run QEMU, capturing serial output to log file and piping it through
# timeout.  We use a pipe so we can grep in real time.
timeout "${TIMEOUT}s" qemu-system-x86_64 \
    $KVM_ARGS \
    -m 1G \
    -smp 2 \
    -nographic \
    -no-reboot \
    -kernel "$KERNEL" \
    -initrd "$INITRD" \
    -append "$QEMU_CMDLINE" \
    -device virtio-net-pci,netdev=eth0 \
    -netdev user,id=eth0 \
    -serial "file:$LOG" \
    2>/dev/null || true   # timeout exits non-zero — that's expected

echo ""
echo "── Serial output captured ($(wc -l < "$LOG") lines) ──────────────────"
if [ "$DEBUG" = "1" ]; then
    cat "$LOG"
    echo ""
fi

# ── Milestone verification ────────────────────────────────────────────
PASS=0
FAIL=0
WARN=0

check_milestone() {
    local pattern="$1"
    if grep -qE "$pattern" "$LOG" 2>/dev/null; then
        printf "  \033[32mPASS\033[0m  %s\n" "$pattern"
        PASS=$((PASS+1))
    else
        printf "  \033[31mFAIL\033[0m  %s\n" "$pattern"
        FAIL=$((FAIL+1))
    fi
}

echo ""
echo "── Milestone checks ─────────────────────────────────────────────"
for m in "${MILESTONES[@]}"; do
    check_milestone "$m"
done

# ── Binary sanity checks from log ────────────────────────────────────
echo ""
echo "── Service state analysis ───────────────────────────────────────"

# Count services loaded
N_LOADED=$(grep -c "svc_load_dir: loaded service" "$LOG" 2>/dev/null; true)
N_LOADED="${N_LOADED//[^0-9]/}"; N_LOADED="${N_LOADED:-0}"
printf "  Services loaded : %s\n" "$N_LOADED"

N_STARTED=$(grep -c "svc_spawn: started" "$LOG" 2>/dev/null; true)
N_STARTED="${N_STARTED//[^0-9]/}"; N_STARTED="${N_STARTED:-0}"
printf "  Services started: %s\n" "$N_STARTED"

N_FAILED=$(grep -cE "state = SVC_FAILED|state SVC_FAILED" "$LOG" 2>/dev/null; true)
N_FAILED="${N_FAILED//[^0-9]/}"; N_FAILED="${N_FAILED:-0}"
printf "  Services failed : %s\n" "$N_FAILED"
[ "$N_FAILED" -gt 0 ] && WARN=$((WARN+N_FAILED)) || true

# Panic check
if grep -qiE "kernel panic|oops:|BUG:|segfault" "$LOG" 2>/dev/null; then
    printf "  \033[31mFAIL\033[0m  KERNEL PANIC or OOPS detected in log!\n"
    FAIL=$((FAIL+1))
else
    printf "  \033[32mPASS\033[0m  No kernel panic / oops\n"
    PASS=$((PASS+1))
fi

# Check cogman PID is 1
if grep -q "cogman-supervisor starting (pid=1)" "$LOG" 2>/dev/null; then
    printf "  \033[32mPASS\033[0m  cogman-supervisor confirmed as PID 1\n"
    PASS=$((PASS+1))
else
    printf "  \033[33mWARN\033[0m  Could not confirm cogman-supervisor PID 1\n"
    WARN=$((WARN+1))
fi

# ── Pentest tool log checks ───────────────────────────────────────────
if [ -n "$EXTRA_CMDLINE" ]; then
    echo ""
    echo "── Pentest service verification ─────────────────────────────────"
    for tool in nmap tcpdump socat; do
        if grep -qi "${tool}.*ok\|${tool}.*version\|${tool}.*OK" "$LOG" 2>/dev/null; then
            printf "  \033[32mPASS\033[0m  %s verified in boot log\n" "$tool"
            PASS=$((PASS+1))
        else
            printf "  \033[33mWARN\033[0m  %s not confirmed in boot log\n" "$tool"
            WARN=$((WARN+1))
        fi
    done
fi

# ── Summary ───────────────────────────────────────────────────────────
echo ""
echo "────────────────────────────────────────────────────────────────"
printf "  PASS: %d  |  FAIL: %d  |  WARN: %d\n" "$PASS" "$FAIL" "$WARN"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo "RESULT: FAIL — see $LOG for full output"
    echo ""
    echo "Last 20 lines of boot log:"
    tail -20 "$LOG"
    exit 1
else
    echo "RESULT: PASS"
    if [ "$WARN" -gt 0 ]; then
        echo "  (with $WARN warning(s) — check $LOG)"
    fi
    exit 0
fi
