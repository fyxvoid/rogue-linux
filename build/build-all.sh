#!/usr/bin/env bash
# build-all.sh — Full Rogue Linux ISO build pipeline
#
# Usage:
#   sudo bash build/setup-deps.sh   # once, installs host dependencies
#   bash build/build-all.sh         # builds everything, produces rogue-linux.iso
#
# Steps:
#   1. build-kernel.sh   — compiles Linux 6.6.75 with DRM+X11+VirtIO config
#   2. build-dwm.sh      — compiles dwm 6.5, st 0.9.2, dmenu 5.3 into rootfs
#   3. build-initramfs.sh — packs initramfs cpio.gz (optional)
#   4. build-iso.sh      — wraps everything into a hybrid BIOS/UEFI ISO
#
# The disk image (build-disk.sh) is produced separately for QEMU testing.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"

die() { echo "ERROR: $*" >&2; exit 1; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Rogue Linux — Full Build Pipeline      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── Step 1: kernel ───────────────────────────────────────────────────────────
echo "━━━ Step 1/4: Kernel ━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "$ROOT/rootfs/boot/vmlinuz-6.6.75" ]; then
    echo "  kernel already built — skipping (delete rootfs/boot/vmlinuz-* to rebuild)"
else
    bash "$BUILD/build-kernel.sh"
fi

# ── Step 2: dwm + st + dmenu ─────────────────────────────────────────────────
echo ""
echo "━━━ Step 2/4: dwm / st / dmenu ━━━━━━━━━━━━━━"
if [ -f "$ROOT/rootfs/usr/bin/dwm" ]; then
    echo "  dwm already built — skipping (delete rootfs/usr/bin/dwm to rebuild)"
else
    bash "$BUILD/build-dwm.sh"
fi

# ── Step 3: initramfs (optional) ─────────────────────────────────────────────
echo ""
echo "━━━ Step 3/4: initramfs ━━━━━━━━━━━━━━━━━━━━━"
if [ -f "$BUILD/rogue-linux.cpio.gz" ]; then
    echo "  initramfs exists — skipping"
else
    if [ -f "$BUILD/build-initramfs.sh" ]; then
        bash "$BUILD/build-initramfs.sh"
    else
        echo "  build-initramfs.sh not found — booting without initramfs"
    fi
fi

# ── Step 4: ISO ───────────────────────────────────────────────────────────────
echo ""
echo "━━━ Step 4/4: ISO ━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$(id -u)" != "0" ]; then
    echo "  ISO build requires root — re-running step 4 with sudo..."
    sudo bash "$BUILD/build-iso.sh"
else
    bash "$BUILD/build-iso.sh"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "BUILD COMPLETE"
echo "  ISO: $BUILD/rogue-linux.iso"
echo ""
echo "Test with QEMU (UEFI + KVM + VirtIO GPU):"
echo "  qemu-system-x86_64 -m 1G -smp 2 -enable-kvm \\"
echo "    -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE.fd \\"
echo "    -cdrom $BUILD/rogue-linux.iso -boot d \\"
echo "    -vga virtio -display sdl -usb -device usb-tablet"
echo ""
echo "Test with QEMU (BIOS, no KVM):"
echo "  qemu-system-x86_64 -m 1G -smp 2 \\"
echo "    -cdrom $BUILD/rogue-linux.iso -boot d \\"
echo "    -vga virtio -display sdl -usb -device usb-tablet"
