#!/usr/bin/env bash
# boot-qemu.sh — Boot Rogue Linux in QEMU using initramfs
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KERNEL="$ROOT/rootfs/boot/vmlinuz-6.6.75"
INITRD="$ROOT/build/rogue-linux.cpio.gz"

if [ ! -f "$KERNEL" ]; then
    echo "ERROR: Kernel not found at $KERNEL"
    exit 1
fi
if [ ! -f "$INITRD" ]; then
    echo "ERROR: Initramfs not found at $INITRD"
    exit 1
fi

echo "Booting Rogue Linux..."
echo "  kernel : $KERNEL ($(du -h "$KERNEL" | cut -f1))"
echo "  initrd : $INITRD ($(du -h "$INITRD" | cut -f1))"
echo "  Press Ctrl-A X to exit QEMU"
echo ""

exec qemu-system-x86_64 \
    -m 256M \
    -smp 2 \
    -kernel "$KERNEL" \
    -initrd "$INITRD" \
    -append "console=ttyS0 rdinit=/sbin/init quiet" \
    -nographic \
    -serial mon:stdio \
    -no-reboot
