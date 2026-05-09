#!/usr/bin/env bash
# boot-iso.sh — Boot Rogue Linux ISO with GTK display + VirtIO input
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ISO="${1:-$ROOT/build/rogue-linux.iso}"
OVMF="/usr/share/ovmf/OVMF.fd"

[ -f "$ISO" ] || { echo "ERROR: ISO not found at $ISO"; exit 1; }

echo "Booting Rogue Linux ISO (GTK + VirtIO input)..."
exec qemu-system-x86_64 \
    -m 1G \
    -smp "$(nproc)" \
    -enable-kvm \
    -drive if=pflash,format=raw,readonly=on,file="$OVMF" \
    -cdrom "$ISO" -boot d \
    -vga virtio \
    -display gtk,zoom-to-fit=on \
    -device virtio-keyboard-pci \
    -device virtio-mouse-pci \
    -serial file:/tmp/rogue-serial.log \
    "$@"
