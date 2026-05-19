#!/usr/bin/env bash
# boot-x11.sh — Boot Rogue Linux with GTK display, no initramfs.
#
# Uses QEMU -kernel to load the kernel directly from the host, bypassing
# GRUB and the initramfs entirely.  The kernel mounts vda2 (ext4) as root
# and /init immediately takes Branch B (already on real disk), so all
# patched files on the disk are used: startx, xkbcomp shim, x11.service.
#
# Usage: bash build/boot-x11.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KERNEL="$ROOT/rootfs/boot/vmlinuz-6.6.75"
IMG="$ROOT/build/rogue-linux-disk.img"

[ -f "$KERNEL" ] || { echo "ERROR: kernel not found at $KERNEL"; exit 1; }
[ -f "$IMG"    ] || { echo "ERROR: disk image not found — run: sudo bash build/build-disk.sh"; exit 1; }

echo "Booting Rogue Linux (direct kernel, GTK display)..."
echo "  kernel : $KERNEL"
echo "  disk   : $IMG ($(du -h "$IMG" | cut -f1))"
echo ""

exec qemu-system-x86_64 \
    -m 1G \
    -smp "$(nproc)" \
    -enable-kvm \
    -kernel "$KERNEL" \
    -append "root=/dev/vda2 rw init=/init console=ttyS0 -- --services-dir /etc/cogman/services" \
    -drive file="$IMG",format=raw,if=virtio \
    -vga virtio \
    -display gtk,zoom-to-fit=on \
    -device virtio-keyboard-pci \
    -device virtio-mouse-pci \
    -serial mon:stdio \
    "$@"
