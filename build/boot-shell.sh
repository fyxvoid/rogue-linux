#!/usr/bin/env bash
# boot-shell.sh — bypass GRUB, boot direct to services-minimal shell
# Uses -kernel so the cmdline is set here, not inside the disk image.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KERNEL="$ROOT/rootfs/boot/vmlinuz-6.6.75"
IMG="$ROOT/build/rogue-linux-disk.img"

exec qemu-system-x86_64 \
    -m 1G \
    -smp "$(nproc)" \
    -enable-kvm \
    -kernel "$KERNEL" \
    -append "root=/dev/vda2 rw init=/init console=ttyS0 -- --services-dir /etc/cogman/services-minimal" \
    -drive file="$IMG",format=raw,if=virtio \
    -vga virtio \
    -display gtk,zoom-to-fit=on \
    -device virtio-keyboard-pci \
    -device virtio-mouse-pci \
    -serial mon:stdio \
    "$@"
