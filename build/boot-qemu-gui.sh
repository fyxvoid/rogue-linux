#!/usr/bin/env bash
# boot-qemu-gui.sh — Boot Rogue Linux with GTK display + VirtIO input
# Working configuration: evdev Xorg driver, virtio-keyboard-pci, virtio-mouse-pci
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMG="$ROOT/build/rogue-linux-disk.img"
KERNEL="$ROOT/rootfs/boot/vmlinuz-6.6.75"
OVMF="/usr/share/ovmf/OVMF.fd"

[ -f "$IMG" ]    || { echo "ERROR: disk image not found — run: sudo bash build/build-disk.sh"; exit 1; }
[ -f "$KERNEL" ] || { echo "ERROR: kernel not found — run: bash build/build-kernel.sh"; exit 1; }

echo "Booting Rogue Linux (GTK + VirtIO input)..."
exec qemu-system-x86_64 \
    -m 1G \
    -smp "$(nproc)" \
    -enable-kvm \
    -drive if=pflash,format=raw,readonly=on,file="$OVMF" \
    -drive file="$IMG",format=raw,if=virtio \
    -vga virtio \
    -display gtk,zoom-to-fit=on \
    -device virtio-keyboard-pci \
    -device virtio-mouse-pci \
    -serial mon:stdio \
    "$@"
