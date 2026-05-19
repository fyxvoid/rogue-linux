#!/usr/bin/env bash
# boot-console.sh — Boot Rogue Linux to a working shell in the GTK window.
#
# Uses services-minimal (rcs + tty1-6 gettys) which is proven stable.
# The GTK window shows the framebuffer console; type at the login prompt.
# Serial console also available (ttyS0 in the terminal).
#
# Usage: sudo bash build/boot-console.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KERNEL="$ROOT/rootfs/boot/vmlinuz-6.6.75"
INITRD="$ROOT/build/rogue-linux.cpio.gz"
IMG="$ROOT/build/rogue-linux-disk.img"

[ -f "$KERNEL" ] || { echo "ERROR: kernel not found: $KERNEL"; exit 1; }
[ -f "$INITRD" ] || { echo "ERROR: initramfs not found — run: bash build/build-initramfs.sh"; exit 1; }
[ -f "$IMG"    ] || { echo "ERROR: disk not found — run: sudo bash build/build-disk.sh"; exit 1; }

echo "Booting Rogue Linux console (minimal services, GTK framebuffer)..."
echo "  Login: root (no password)  or  void (no password)"
echo "  GTK window: framebuffer console on tty1"
echo "  Terminal:   serial console on ttyS0"
echo ""

exec qemu-system-x86_64 \
    -m 1G \
    -smp "$(nproc)" \
    -enable-kvm \
    -kernel "$KERNEL" \
    -initrd "$INITRD" \
    -append "rdinit=/init console=ttyS0 -- --services-dir /etc/cogman/services-minimal" \
    -drive file="$IMG",format=raw,if=virtio \
    -vga virtio \
    -display gtk,zoom-to-fit=on \
    -device virtio-keyboard-pci \
    -device virtio-mouse-pci \
    -serial mon:stdio \
    "$@"
