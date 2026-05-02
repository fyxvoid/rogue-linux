#!/usr/bin/env bash
# build-initramfs.sh — Pack rootfs into a gzip'd cpio initramfs
# Usage: bash build-initramfs.sh [--minimal]
#
# --minimal: use services-minimal/ (cogman + console only, no X11)
#            default services dir (/etc/cogman/services) is left in place;
#            the initramfs kernel cmdline selects which dir cogman uses.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ROOTFS="$ROOT/rootfs"
OUT="$ROOT/build/rogue-linux.cpio.gz"

MINIMAL=0
for arg in "$@"; do
    [ "$arg" = "--minimal" ] && MINIMAL=1
done

# Ensure /init → cogman-supervisor (kernel looks for /init in initramfs)
if [ ! -e "$ROOTFS/init" ]; then
    ln -sf usr/bin/cogman-supervisor "$ROOTFS/init"
    echo "  created : /init → usr/bin/cogman-supervisor"
fi

echo "[1/2] Packing rootfs into cpio archive..."
cd "$ROOTFS"
find . | cpio --quiet -H newc -o | gzip -9 > "$OUT"
cd - >/dev/null

SIZE="$(du -h "$OUT" | cut -f1)"
echo "[2/2] Done."
echo "  initramfs : $OUT ($SIZE)"
if [ "$MINIMAL" = "1" ]; then
    echo "  mode      : minimal (boot with --services-minimal flag)"
else
    echo "  mode      : full"
fi
echo ""
echo "  Boot with:"
if [ "$MINIMAL" = "1" ]; then
    echo "    bash $ROOT/build/boot-minimal.sh"
else
    echo "    bash $ROOT/build/boot-qemu.sh"
fi
