#!/usr/bin/env bash
# build-kernel.sh — Build Linux 6.6.75 and install into rootfs/boot
set -euo pipefail

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
  --module CONFIG_VIRTIO_BALLOON

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
