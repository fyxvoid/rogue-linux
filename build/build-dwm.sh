#!/usr/bin/env bash
# build-dwm.sh — Build dwm 6.5, st 0.9.2, and dmenu 5.3 and install into rootfs
# Requires: libx11-dev, libxft-dev, libxinerama-dev, libfreetype-dev
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ROOTFS="$ROOT/rootfs"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

DWM_VER="6.5"
ST_VER="0.9.2"
DMENU_VER="5.3"

for cmd in cc make pkg-config; do
    command -v $cmd >/dev/null || { echo "ERROR: $cmd not found"; exit 1; }
done

echo "[1/4] Downloading sources..."
curl -fsSL "https://dl.suckless.org/dwm/dwm-${DWM_VER}.tar.gz"   -o "$TMP/dwm.tar.gz"
curl -fsSL "https://dl.suckless.org/st/st-${ST_VER}.tar.gz"      -o "$TMP/st.tar.gz"
curl -fsSL "https://dl.suckless.org/tools/dmenu-${DMENU_VER}.tar.gz" -o "$TMP/dmenu.tar.gz"

cd "$TMP"
tar -xf dwm.tar.gz
tar -xf st.tar.gz
tar -xf dmenu.tar.gz

echo "[2/4] Installing dwm config..."
cp "$ROOT/rootfs/etc/dwm/config.h" "$TMP/dwm-${DWM_VER}/config.h" 2>/dev/null || \
    cp "$ROOT/build/dwm-config.h"   "$TMP/dwm-${DWM_VER}/config.h" 2>/dev/null || \
    echo "  using default dwm config"

echo "[3/4] Compiling dwm, st, dmenu..."
make -C "dwm-${DWM_VER}"   -j"$(nproc)"
make -C "st-${ST_VER}"     -j"$(nproc)"
make -C "dmenu-${DMENU_VER}" -j"$(nproc)"

echo "[4/4] Installing into rootfs..."
install -m755 "dwm-${DWM_VER}/dwm"      "$ROOTFS/usr/bin/dwm"
install -m755 "st-${ST_VER}/st"         "$ROOTFS/usr/bin/st"
install -m755 "dmenu-${DMENU_VER}/dmenu" "$ROOTFS/usr/bin/dmenu"
install -m755 "dmenu-${DMENU_VER}/dmenu_run" "$ROOTFS/usr/bin/dmenu_run"

echo ""
echo "DWM BUILD OK"
echo "  dwm   : $(du -h "$ROOTFS/usr/bin/dwm" | cut -f1)"
echo "  st    : $(du -h "$ROOTFS/usr/bin/st" | cut -f1)"
echo "  dmenu : $(du -h "$ROOTFS/usr/bin/dmenu" | cut -f1)"
