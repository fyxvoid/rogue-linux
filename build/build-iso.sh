#!/usr/bin/env bash
# build-iso.sh — Create a bootable hybrid ISO (BIOS + UEFI) for Rogue Linux
#
# Boot model: kernel + initramfs loaded by GRUB from ISO9660.
#   /init detects no root= on cmdline → stays in RAM (cpio rootfs).
#   This is simpler than live-boot overlayfs and works on the first try.
#
# Requires: grub-mkrescue, xorriso, kernel already built
# Usage: sudo bash build/build-iso.sh [output.iso]

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ROOTFS="$ROOT/rootfs"
BUILD="$ROOT/build"
ISO_OUT="${1:-$BUILD/rogue-linux.iso}"
STAGING="$(mktemp -d /tmp/rogue-staging.XXXXX)"
trap 'rm -rf "$STAGING"' EXIT
KERNEL="$ROOTFS/boot/vmlinuz-6.6.75"

# ── preflight ────────────────────────────────────────────────────────────────
# root check removed — grub-mkrescue works as non-root
[ -f "$KERNEL" ] || { echo "ERROR: kernel not found — run build-kernel.sh first"; exit 1; }
for cmd in grub-mkrescue xorriso; do
    command -v $cmd >/dev/null || { echo "ERROR: $cmd not found — run setup-deps.sh first"; exit 1; }
done

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Rogue Linux — ISO Image Builder        ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── step 1: staging area ─────────────────────────────────────────────────────
echo "[1/5] Preparing ISO staging area..."
rm -rf "$STAGING"
mkdir -p "$STAGING/boot/grub"

# ── step 2: copy kernel ──────────────────────────────────────────────────────
echo "[2/5] Copying kernel..."
cp "$KERNEL" "$STAGING/boot/vmlinuz"
echo "  vmlinuz: $(du -h "$STAGING/boot/vmlinuz" | cut -f1)"

# ── step 3: pack fresh initramfs from rootfs ─────────────────────────────────
echo "[3/5] Packing rootfs into initramfs (cpio.gz)..."
INITRAMFS="$STAGING/boot/initramfs.cpio.gz"

# Ensure /init exists in rootfs
if [ ! -e "$ROOTFS/init" ]; then
    ln -sf usr/bin/cogman-supervisor "$ROOTFS/init"
fi

cd "$ROOTFS"
find . | cpio --quiet -H newc -o | gzip -9 > "$INITRAMFS"
cd - >/dev/null
echo "  initramfs: $(du -h "$INITRAMFS" | cut -f1)"

# ── step 4: write GRUB config ────────────────────────────────────────────────
echo "[4/5] Writing GRUB config..."

cat > "$STAGING/boot/grub/grub.cfg" << 'GRUBCFG'
# Rogue Linux — GRUB ISO boot config
# Boot model: kernel + initramfs, rootfs in RAM (no root= needed).
# /init script detects no root= and boots cogman directly from ramfs.

set default=0
set timeout=5
set timeout_style=menu

insmod all_video
insmod gfxterm
terminal_output gfxterm

set menu_color_normal=white/black
set menu_color_highlight=black/light-blue

menuentry "Rogue Linux — dwm + X11" {
    linux  /boot/vmlinuz \
           init=/init \
           console=tty1 \
           quiet \
           -- --services-dir /etc/cogman/services
    initrd /boot/initramfs.cpio.gz
    echo "Booting Rogue Linux..."
}

menuentry "Rogue Linux — console only" {
    linux  /boot/vmlinuz \
           init=/init \
           console=tty1 console=ttyS0,115200 \
           -- --services-dir /etc/cogman/services-minimal
    initrd /boot/initramfs.cpio.gz
}

menuentry "Rogue Linux — single user (rescue)" {
    linux  /boot/vmlinuz \
           init=/bin/sh \
           console=tty1
    initrd /boot/initramfs.cpio.gz
}
GRUBCFG

# ── step 5: build the ISO ────────────────────────────────────────────────────
echo "[5/5] Building ISO with grub-mkrescue..."
grub-mkrescue \
    --output="$ISO_OUT" \
    "$STAGING" \
    -- \
    -volid "ROGUE_LINUX" \
    2>&1 | grep -v "^$" | tail -8

echo ""
echo "ISO BUILD OK"
echo "  iso    : $ISO_OUT  ($(du -h "$ISO_OUT" | cut -f1))"
echo ""
echo "  Boot (UEFI + KVM):"
echo "    qemu-system-x86_64 -m 1G -smp 2 -enable-kvm \\"
echo "      -drive if=pflash,format=raw,readonly=on,file=/usr/share/ovmf/OVMF.fd \\"
echo "      -cdrom $ISO_OUT -boot d -vga virtio -display sdl -usb -device usb-tablet"
echo ""
echo "  Boot (BIOS + KVM):"
echo "    qemu-system-x86_64 -m 1G -smp 2 -enable-kvm \\"
echo "      -cdrom $ISO_OUT -boot d -vga virtio -display sdl -usb -device usb-tablet"
