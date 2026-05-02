#!/usr/bin/env bash
# boot-disk-direct.sh — Boot Rogue Linux from disk with direct kernel load
#
# Faster dev path: QEMU loads the kernel directly (no GRUB),
# disk is the persistent root filesystem.
# Functionally identical to the GRUB path once booted.
#
# Press Ctrl-A X to exit QEMU.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KERNEL="$ROOT/rootfs/boot/vmlinuz-6.6.75"
IMG="$ROOT/build/rogue-linux-disk.img"

[ -f "$KERNEL" ] || { echo "ERROR: kernel not found at $KERNEL"; exit 1; }
[ -f "$IMG"    ] || { echo "ERROR: disk image not found. Run: sudo bash build/build-disk.sh"; exit 1; }

# Extract UUID from image for root= arg
ROOT_UUID=$(blkid -s UUID -o value -t LABEL=rogue-linux "$IMG" 2>/dev/null \
            || blkid "$IMG" | grep -o 'UUID="[^"]*"' | tail -1 | tr -d 'UUID="')

if [ -z "$ROOT_UUID" ]; then
    echo "  WARNING: could not read UUID from image, falling back to /dev/vda2"
    ROOT_ARG="/dev/vda2"
else
    ROOT_ARG="UUID=$ROOT_UUID"
    echo "  root   : $ROOT_ARG"
fi

KVM_ARGS=""
if [ -e /dev/kvm ]; then
    KVM_ARGS="-enable-kvm -cpu host"
    echo "  KVM: enabled"
else
    echo "  KVM: not available (TCG)"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Rogue Linux — Direct Disk Boot         ║"
echo "╚══════════════════════════════════════════╝"
echo "  kernel : $(du -h "$KERNEL" | cut -f1)"
echo "  disk   : $(du -h "$IMG" | cut -f1)"
echo "  path   : QEMU -kernel → ext4 root → cogman PID 1"
echo "  Press Ctrl-A X to exit QEMU"
echo ""

exec qemu-system-x86_64 \
    $KVM_ARGS \
    -m 512M \
    -smp 1 \
    -kernel "$KERNEL" \
    -append "root=$ROOT_ARG rw init=/init console=ttyS0 quiet -- --services-dir /etc/cogman/services-minimal" \
    -drive file="$IMG",format=raw,if=virtio \
    -nographic \
    -serial mon:stdio \
    -no-reboot
