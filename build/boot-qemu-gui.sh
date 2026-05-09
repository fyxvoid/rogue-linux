#!/usr/bin/env bash
# boot-qemu-gui.sh — Boot Rogue Linux disk image in QEMU with VirtIO GPU + SDL display
# Usage: bash build/boot-qemu-gui.sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMG="$ROOT/build/rogue-linux-disk.img"
KERNEL="$ROOT/rootfs/boot/vmlinuz-6.6.75"
OVMF="/usr/share/OVMF/OVMF_CODE.fd"

[ -f "$IMG" ]    || { echo "ERROR: disk image not found — run: sudo bash build/build-disk.sh"; exit 1; }
[ -f "$KERNEL" ] || { echo "ERROR: kernel not found — run: bash build/build-kernel.sh"; exit 1; }

# Use UEFI if OVMF is available, otherwise fall back to BIOS
if [ -f "$OVMF" ]; then
    echo "Booting with UEFI (OVMF)..."
    exec qemu-system-x86_64 \
        -m 1G \
        -smp "$(nproc)" \
        -enable-kvm \
        -drive if=pflash,format=raw,readonly=on,file="$OVMF" \
        -drive file="$IMG",format=raw,if=virtio \
        -vga virtio \
        -display sdl,gl=off \
        -usb -device usb-tablet \
        -audiodev none,id=audio \
        -serial mon:stdio \
        "$@"
else
    echo "OVMF not found — booting with BIOS..."
    exec qemu-system-x86_64 \
        -m 1G \
        -smp "$(nproc)" \
        -enable-kvm \
        -drive file="$IMG",format=raw,if=virtio \
        -vga virtio \
        -display sdl,gl=off \
        -usb -device usb-tablet \
        -serial mon:stdio \
        "$@"
fi
