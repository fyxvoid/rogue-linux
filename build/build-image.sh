#!/usr/bin/env bash
# build-image.sh — Build a bootable ext4 disk image for Rogue Linux
# Usage: bash build-image.sh [SIZE_MB]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ROOTFS="$ROOT/rootfs"
KERNEL_SRC="$ROOT/build/kernel/linux-6.6.75"
IMG="$ROOT/build/rogue-linux.img"
MNT="$ROOT/build/mnt"
SIZE_MB="${1:-512}"

# ── Preflight checks ────────────────────────────────────────────────

if [ ! -f "$KERNEL_SRC/arch/x86/boot/bzImage" ]; then
    echo "ERROR: Kernel not built yet. Run build-kernel.sh first."
    exit 1
fi

echo "[step 1/5] Installing kernel + modules into rootfs/boot..."
mkdir -p "$ROOTFS/boot"
cp -f "$KERNEL_SRC/arch/x86/boot/bzImage"  "$ROOTFS/boot/vmlinuz-6.6.75"
cp -f "$KERNEL_SRC/System.map"              "$ROOTFS/boot/System.map-6.6.75"
cp -f "$KERNEL_SRC/.config"                 "$ROOTFS/boot/config-6.6.75"

# Install kernel modules
make -C "$KERNEL_SRC" modules_install INSTALL_MOD_PATH="$ROOTFS" 2>&1 | tail -3
echo "  vmlinuz : $(du -h "$ROOTFS/boot/vmlinuz-6.6.75" | cut -f1)"

echo "[step 2/5] Creating ${SIZE_MB}MB raw disk image..."
rm -f "$IMG"
dd if=/dev/zero of="$IMG" bs=1M count="$SIZE_MB" status=none
mkfs.ext4 -q -L "rogue-linux" "$IMG"
echo "  image   : $IMG"

echo "[step 3/5] Mounting image and copying rootfs..."
mkdir -p "$MNT"
mount -o loop "$IMG" "$MNT"
cp -a "$ROOTFS/." "$MNT/"
umount "$MNT"
rmdir "$MNT"
echo "  copied  : rootfs → image"

echo "[step 4/5] Writing QEMU boot script..."
cat > "$ROOT/build/boot-qemu.sh" << 'QSCRIPT'
#!/usr/bin/env bash
# boot-qemu.sh — Boot Rogue Linux in QEMU
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMG="$ROOT/build/rogue-linux.img"
KERNEL="$ROOT/rootfs/boot/vmlinuz-6.6.75"

exec qemu-system-x86_64 \
    -m 256M \
    -smp 2 \
    -kernel "$KERNEL" \
    -drive  file="$IMG",format=raw,if=virtio \
    -append "console=ttyS0 rdinit=/sbin/init quiet" \
    -nographic \
    -serial mon:stdio \
    -no-reboot
QSCRIPT
chmod +x "$ROOT/build/boot-qemu.sh"
echo "  script  : $ROOT/build/boot-qemu.sh"

echo ""
echo "IMAGE BUILD OK"
echo "  Boot with: bash $ROOT/build/boot-qemu.sh"
