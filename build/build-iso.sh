#!/usr/bin/env bash
# build-iso.sh — Create a bootable hybrid ISO (BIOS + UEFI) from the Rogue Linux rootfs
#
# Requires: grub-mkrescue, xorriso, mtools, kernel already built
# Usage: sudo bash build/build-iso.sh [output.iso]
#
# The ISO uses a small squashfs-compressed rootfs overlaid at boot,
# with a live-style layout compatible with GRUB's iso9660 module.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ROOTFS="$ROOT/rootfs"
BUILD="$ROOT/build"
ISO_OUT="${1:-$BUILD/rogue-linux.iso}"
STAGING="$BUILD/iso-staging"
KERNEL="$ROOTFS/boot/vmlinuz-6.6.75"
INITRAMFS="$BUILD/rogue-linux.cpio.gz"

# ── preflight ────────────────────────────────────────────────────────────────
[ "$(id -u)" = "0" ] || { echo "ERROR: run with sudo"; exit 1; }
[ -f "$KERNEL" ] || { echo "ERROR: kernel not found — run build-kernel.sh first"; exit 1; }
for cmd in grub-mkrescue xorriso mtools; do
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

# ── step 2: copy kernel and initramfs ────────────────────────────────────────
echo "[2/5] Copying kernel..."
cp "$KERNEL" "$STAGING/boot/vmlinuz"
echo "  vmlinuz: $(du -h "$STAGING/boot/vmlinuz" | cut -f1)"

if [ -f "$INITRAMFS" ]; then
    cp "$INITRAMFS" "$STAGING/boot/initramfs.cpio.gz"
    echo "  initramfs: $(du -h "$STAGING/boot/initramfs.cpio.gz" | cut -f1)"
else
    echo "  initramfs: not found — will boot without initramfs"
fi

# ── step 3: pack rootfs as squashfs ──────────────────────────────────────────
echo "[3/5] Compressing rootfs into squashfs..."
mkdir -p "$STAGING/live"
if command -v mksquashfs >/dev/null 2>&1; then
    mksquashfs "$ROOTFS" "$STAGING/live/filesystem.squashfs" \
        -comp xz -Xbcj x86 \
        -e boot \
        -no-progress 2>&1 | tail -3
    echo "  squashfs: $(du -h "$STAGING/live/filesystem.squashfs" | cut -f1)"
else
    echo "  squashfs: mksquashfs not found — copying rootfs directly (no compression)"
    cp -a "$ROOTFS/." "$STAGING/"
fi

# ── step 4: write GRUB config ────────────────────────────────────────────────
echo "[4/5] Writing GRUB config..."
INITRD_LINE=""
[ -f "$STAGING/boot/initramfs.cpio.gz" ] && INITRD_LINE="  initrd /boot/initramfs.cpio.gz"

cat > "$STAGING/boot/grub/grub.cfg" << GRUBCFG
# Rogue Linux — GRUB ISO configuration
set default=0
set timeout=5
set timeout_style=menu

insmod all_video
insmod gfxterm
terminal_output gfxterm

insmod png

set menu_color_normal=white/black
set menu_color_highlight=black/light-blue

menuentry "Rogue Linux (dwm + X11)" {
    linux  /boot/vmlinuz \\
           root=live:LABEL=ROGUE_LINUX \\
           init=/init \\
           console=tty1 \\
           -- --services-dir /etc/cogman/services
${INITRD_LINE}
    echo "Booting Rogue Linux..."
}

menuentry "Rogue Linux (console only)" {
    linux  /boot/vmlinuz \\
           root=live:LABEL=ROGUE_LINUX \\
           init=/init \\
           console=ttyS0,115200 \\
           -- --services-dir /etc/cogman/services-minimal
${INITRD_LINE}
}

menuentry "Rogue Linux (single user / rescue)" {
    linux  /boot/vmlinuz \\
           root=live:LABEL=ROGUE_LINUX \\
           init=/bin/sh \\
           console=tty1
}
GRUBCFG

# ── step 5: build the ISO ────────────────────────────────────────────────────
echo "[5/5] Building ISO with grub-mkrescue..."
grub-mkrescue \
    --output="$ISO_OUT" \
    "$STAGING" \
    -- \
    -volid "ROGUE_LINUX" \
    2>&1 | tail -5

echo ""
echo "ISO BUILD OK"
echo "  iso    : $ISO_OUT  ($(du -h "$ISO_OUT" | cut -f1))"
echo ""
echo "  Boot in QEMU (UEFI):"
echo "    qemu-system-x86_64 -m 1G -smp 2 -enable-kvm \\"
echo "      -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE.fd \\"
echo "      -cdrom $ISO_OUT -boot d -vga virtio -display sdl"
echo ""
echo "  Boot in QEMU (BIOS/legacy):"
echo "    qemu-system-x86_64 -m 1G -smp 2 -enable-kvm \\"
echo "      -cdrom $ISO_OUT -boot d -vga virtio -display sdl"
