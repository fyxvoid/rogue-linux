#!/usr/bin/env bash
# build-kernel.sh — Build Linux 6.6.75 and install into rootfs/boot
set -euo pipefail

# ── dependency check ──────────────────────────────────────────────────────────
MISSING=""
for cmd in bison flex bc; do
    command -v $cmd >/dev/null 2>&1 || MISSING="$MISSING $cmd"
done
for lib in libssl-dev libelf-dev; do
    dpkg -l "$lib" 2>/dev/null | grep -q "^ii" || MISSING="$MISSING $lib"
done
if [ -n "$MISSING" ]; then
    echo "ERROR: Missing build dependencies:$MISSING"
    echo "  Fix with: sudo apt-get install -y bison flex bc libssl-dev libelf-dev"
    echo "  Or run:   sudo bash build/setup-deps.sh"
    exit 1
fi

ROOTFS="$(cd "$(dirname "$0")/.." && pwd)/rootfs"
BUILD="$(cd "$(dirname "$0")" && pwd)/kernel"
SRC="$BUILD/linux-6.6.75"
PKGROOT="$ROOTFS/pkgroot/linux-kernel"

echo "[1/6] Configuring kernel (x86_64_defconfig)..."
make -C "$SRC" x86_64_defconfig

echo "[2/6] Enabling required kernel options..."
"$SRC/scripts/config" --file "$SRC/.config" \
  --enable CONFIG_DEVTMPFS \
  --enable CONFIG_DEVTMPFS_MOUNT \
  --enable CONFIG_TMPFS \
  --enable CONFIG_PROC_FS \
  --enable CONFIG_SYSFS \
  --enable CONFIG_EXT4_FS \
  --enable CONFIG_BLK_DEV_INITRD \
  --enable CONFIG_MULTIUSER \
  --enable CONFIG_TTY \
  --enable CONFIG_SERIAL_8250 \
  --enable CONFIG_SERIAL_8250_CONSOLE \
  --enable CONFIG_PRINTK

echo "[3/6] Enabling VirtIO drivers (QEMU)..."
"$SRC/scripts/config" --file "$SRC/.config" \
  --enable CONFIG_VIRTIO \
  --enable CONFIG_VIRTIO_PCI \
  --enable CONFIG_VIRTIO_BLK \
  --enable CONFIG_VIRTIO_NET \
  --enable CONFIG_VIRTIO_CONSOLE \
  --enable CONFIG_HW_RANDOM_VIRTIO \
  --enable CONFIG_VIRTIO_INPUT \
  --module CONFIG_VIRTIO_BALLOON

echo "[3b/6] Enabling DRM / GPU (X11 + QEMU graphics)..."
"$SRC/scripts/config" --file "$SRC/.config" \
  --enable CONFIG_DRM \
  --enable CONFIG_DRM_VIRTIO_GPU \
  --enable CONFIG_DRM_FBDEV_EMULATION \
  --enable CONFIG_FB \
  --enable CONFIG_FB_VESA \
  --enable CONFIG_FRAMEBUFFER_CONSOLE \
  --enable CONFIG_FRAMEBUFFER_CONSOLE_DETECT_PRIMARY \
  --enable CONFIG_VGA_CONSOLE

echo "[3c/6] Enabling input subsystem (keyboard/mouse for X11)..."
"$SRC/scripts/config" --file "$SRC/.config" \
  --enable CONFIG_INPUT \
  --enable CONFIG_INPUT_EVDEV \
  --enable CONFIG_INPUT_KEYBOARD \
  --enable CONFIG_INPUT_MOUSE \
  --enable CONFIG_INPUT_MOUSEDEV \
  --enable CONFIG_INPUT_MOUSEDEV_PSAUX \
  --enable CONFIG_HID \
  --enable CONFIG_HID_GENERIC \
  --enable CONFIG_USB_HID \
  --enable CONFIG_UNIX98_PTYS

echo "[3d/6] Enabling USB host controllers (real hardware)..."
"$SRC/scripts/config" --file "$SRC/.config" \
  --enable CONFIG_USB_SUPPORT \
  --enable CONFIG_USB \
  --enable CONFIG_USB_XHCI_HCD \
  --enable CONFIG_USB_EHCI_HCD \
  --enable CONFIG_USB_OHCI_HCD

echo "[3e/6] Enabling network firewall support (nftables)..."
"$SRC/scripts/config" --file "$SRC/.config" \
  --enable CONFIG_NETFILTER \
  --enable CONFIG_NF_TABLES \
  --enable CONFIG_NF_TABLES_INET \
  --enable CONFIG_NFT_FILTER \
  --enable CONFIG_NFT_CT \
  --enable CONFIG_NF_CONNTRACK

echo "[4/6] Reconciling config (oldconfig)..."
yes '' | make -C "$SRC" oldconfig 2>&1 | tail -3

echo "[5/6] Compiling bzImage + modules ($(nproc) jobs)..."
# CC="gcc -std=gnu11" required: GCC 15 defaults to C23 which breaks kernel 6.6.x
make -C "$SRC" -j"$(nproc)" bzImage modules CC="gcc -std=gnu11" 2>&1 | tail -10

echo "[6/6] Installing into rootfs..."
mkdir -p "$PKGROOT/boot"
make -C "$SRC" modules_install INSTALL_MOD_PATH="$PKGROOT"
cp "$SRC/arch/x86/boot/bzImage" "$PKGROOT/boot/vmlinuz-6.6.75"
cp "$SRC/System.map"             "$PKGROOT/boot/System.map-6.6.75"
cp "$SRC/.config"                "$PKGROOT/boot/config-6.6.75"

# Copy into final rootfs
mkdir -p "$ROOTFS/boot"
cp "$PKGROOT/boot/vmlinuz-6.6.75"    "$ROOTFS/boot/"
cp "$PKGROOT/boot/System.map-6.6.75" "$ROOTFS/boot/"
cp -r "$PKGROOT/lib" "$ROOTFS/"

echo ""
echo "KERNEL BUILD OK"
echo "  vmlinuz : $ROOTFS/boot/vmlinuz-6.6.75"
echo "  size    : $(du -h "$ROOTFS/boot/vmlinuz-6.6.75" | cut -f1)"
