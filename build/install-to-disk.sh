#!/usr/bin/env bash
# install-to-disk.sh — Install Rogue Linux onto a real disk
#
# Usage: sudo bash build/install-to-disk.sh /dev/sdX
# WARNING: completely wipes the target device.
#
# Partition layout:
#   p1 — 512 MB  EFI System (FAT32)
#   p2 — rest    Linux root (ext4)

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ROOTFS="$ROOT/rootfs"
TARGET="${1:-}"

# ── preflight ────────────────────────────────────────────────────────────────
[ "$(id -u)" = "0" ] || { echo "ERROR: run with sudo"; exit 1; }
[ -n "$TARGET" ] || { echo "Usage: $0 /dev/sdX"; exit 1; }
[ -b "$TARGET" ] || { echo "ERROR: $TARGET is not a block device"; exit 1; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Rogue Linux — Disk Installer           ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Target : $TARGET"
echo "  Rootfs : $ROOTFS"
echo ""
echo "  WARNING: ALL DATA ON $TARGET WILL BE ERASED"
read -r -p "  Type YES to continue: " confirm
[ "$confirm" = "YES" ] || { echo "Aborted."; exit 1; }

# ── partition ────────────────────────────────────────────────────────────────
echo "[1/6] Partitioning $TARGET ..."
sgdisk --zap-all "$TARGET"
sgdisk \
  --new=1:0:+512M --typecode=1:ef00 --change-name=1:"EFI" \
  --new=2:0:0     --typecode=2:8300 --change-name=2:"ROOT" \
  "$TARGET"
partprobe "$TARGET"
sleep 1

# Resolve partition names (/dev/sda1 vs /dev/nvme0n1p1)
if [[ "$TARGET" == *nvme* ]] || [[ "$TARGET" == *mmcblk* ]]; then
  EFI="${TARGET}p1"
  ROOT_PART="${TARGET}p2"
else
  EFI="${TARGET}1"
  ROOT_PART="${TARGET}2"
fi

# ── format ───────────────────────────────────────────────────────────────────
echo "[2/6] Formatting partitions ..."
mkfs.fat -F32 -n "ROGUEEFI" "$EFI"
mkfs.ext4 -L "ROGUEROOT" -F "$ROOT_PART"

# ── mount ────────────────────────────────────────────────────────────────────
echo "[3/6] Mounting ..."
MNT=$(mktemp -d /tmp/rogue-install.XXXXX)
mount "$ROOT_PART" "$MNT"
mkdir -p "$MNT/boot/efi"
mount "$EFI" "$MNT/boot/efi"

# ── copy rootfs ──────────────────────────────────────────────────────────────
echo "[4/6] Copying rootfs (this may take a few minutes) ..."
rsync -aAX --exclude=/boot/efi "$ROOTFS/" "$MNT/"

# ── fstab with real UUIDs ────────────────────────────────────────────────────
echo "[5/6] Writing /etc/fstab ..."
ROOT_UUID=$(blkid -s UUID -o value "$ROOT_PART")
EFI_UUID=$(blkid  -s UUID -o value "$EFI")
cat > "$MNT/etc/fstab" << FSTAB
# <device>                                <mountpoint>  <type>  <options>          <dump> <pass>
UUID=$ROOT_UUID  /             ext4    errors=remount-ro  0      1
UUID=$EFI_UUID   /boot/efi     vfat    umask=0077         0      2
tmpfs            /tmp          tmpfs   defaults,noatime   0      0
tmpfs            /run          tmpfs   defaults,noatime   0      0
FSTAB

# ── GRUB ─────────────────────────────────────────────────────────────────────
echo "[6/6] Installing GRUB ..."
mount --bind /dev  "$MNT/dev"
mount --bind /proc "$MNT/proc"
mount --bind /sys  "$MNT/sys"

grub-install \
  --target=x86_64-efi \
  --efi-directory="$MNT/boot/efi" \
  --boot-directory="$MNT/boot" \
  --removable \
  --no-nvram

cat > "$MNT/boot/grub/grub.cfg" << GRUBCFG
set default=0
set timeout=5

insmod all_video
insmod gfxterm
terminal_output gfxterm

menuentry "Rogue Linux" {
    linux  /boot/vmlinuz-6.6.75 \
           root=UUID=$ROOT_UUID \
           init=/init \
           console=tty1 \
           quiet \
           -- --services-dir /etc/cogman/services
    initrd /boot/initramfs.cpio.gz
}

menuentry "Rogue Linux — recovery" {
    linux  /boot/vmlinuz-6.6.75 \
           root=UUID=$ROOT_UUID \
           init=/bin/sh \
           console=tty1
    initrd /boot/initramfs.cpio.gz
}
GRUBCFG

umount "$MNT/dev" "$MNT/proc" "$MNT/sys"
umount "$MNT/boot/efi"
umount "$MNT"
rmdir "$MNT"

echo ""
echo "  Installation complete!"
echo "  Boot from $TARGET to start Rogue Linux."
echo ""
