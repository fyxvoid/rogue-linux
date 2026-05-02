#!/usr/bin/env bash
# boot-disk.sh — Boot Rogue Linux from disk image via UEFI GRUB
#
# Boots the full hardware-compatible path:
#   OVMF (UEFI) → GRUB EFI → kernel → ext4 root → cogman PID 1
#
# Press Ctrl-A X to exit QEMU.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMG="$ROOT/build/rogue-linux-disk.img"
OVMF_CODE="/usr/share/OVMF/OVMF_CODE_4M.fd"
OVMF_VARS_SRC="/usr/share/OVMF/OVMF_VARS_4M.fd"
OVMF_VARS_RUN="/tmp/rogue-ovmf-vars.fd"

[ -f "$IMG"       ] || { echo "ERROR: disk image not found. Run: sudo bash build/build-disk.sh"; exit 1; }
[ -f "$OVMF_CODE" ] || { echo "ERROR: OVMF firmware not found at $OVMF_CODE"; exit 1; }

# Copy OVMF VARS (writable per-VM state — UEFI variables)
cp -f "$OVMF_VARS_SRC" "$OVMF_VARS_RUN"

# KVM detection
KVM_ARGS=""
if [ -e /dev/kvm ]; then
    KVM_ARGS="-enable-kvm -cpu host"
    echo "  KVM: enabled"
else
    echo "  KVM: not available (TCG — will be slow)"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Rogue Linux — UEFI Disk Boot           ║"
echo "╚══════════════════════════════════════════╝"
echo "  disk   : $(du -h "$IMG" | cut -f1)  $IMG"
echo "  path   : OVMF → GRUB EFI → cogman PID 1"
echo "  Press Ctrl-A X to exit QEMU"
echo ""

exec qemu-system-x86_64 \
    $KVM_ARGS \
    -m 512M \
    -smp 1 \
    -drive if=pflash,format=raw,readonly=on,file="$OVMF_CODE" \
    -drive if=pflash,format=raw,file="$OVMF_VARS_RUN" \
    -drive file="$IMG",format=raw,if=virtio \
    -nographic \
    -serial mon:stdio \
    -no-reboot
