#!/usr/bin/env bash
# boot-minimal.sh — Build initramfs and boot Rogue Linux with cogman as PID 1
#
# Minimal mode: no X11, no alacritty, no probes.
# Services: rcs (filesystem init) + console (getty on ttyS0).
# Press Ctrl-A X to exit QEMU.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KERNEL="$ROOT/rootfs/boot/vmlinuz-6.6.75"
INITRD="$ROOT/build/rogue-linux.cpio.gz"

[ -f "$KERNEL" ] || { echo "ERROR: kernel not found at $KERNEL"; exit 1; }

echo "=== Rogue Linux — minimal boot (cogman as PID 1) ==="
echo ""

# ── Rebuild initramfs ────────────────────────────────────────────────
echo "--- building initramfs ---"
bash "$ROOT/build/build-initramfs.sh" --minimal
echo ""

# ── KVM detection ────────────────────────────────────────────────────
KVM_ARGS=""
if [ -e /dev/kvm ] && qemu-system-x86_64 -enable-kvm -version >/dev/null 2>&1; then
    KVM_ARGS="-enable-kvm -cpu host"
    echo "  KVM: enabled"
else
    echo "  KVM: not available (TCG — will be slow)"
fi

echo "  kernel  : $(du -h "$KERNEL" | cut -f1)"
echo "  initrd  : $(du -h "$INITRD" | cut -f1)"
echo ""
echo "  cogman-supervisor is PID 1"
echo "  services: rcs + getty on ttyS0"
echo ""
echo "  Press Ctrl-A X to exit QEMU"
echo "─────────────────────────────────────────────────────"
echo ""

exec qemu-system-x86_64 \
    $KVM_ARGS \
    -m 512M \
    -smp 1 \
    -kernel "$KERNEL" \
    -initrd "$INITRD" \
    -append "console=ttyS0 rdinit=/init quiet -- --services-dir /etc/cogman/services-minimal" \
    -nographic \
    -serial mon:stdio \
    -no-reboot
