#!/usr/bin/env bash
# make-xorg-pkg.sh — Bundle the full Xorg server stack into a cogman package
# Bundles: Xorg binary, all modules, drivers, XKB data, fonts, input drivers
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG_DIR="$ROOT/packages/graphical/xorg-server"
TAR_DIR="$PKG_DIR/tar"
STAGE="$(mktemp -d)"
TARBALL="$TAR_DIR/xorg-server-bundle.tar.gz"

echo "[xorg-pkg] Staging Xorg server bundle..."
mkdir -p "$TAR_DIR"

# ── Xorg server binary ──────────────────────────────────────────────
mkdir -p "$STAGE/usr/lib/xorg"
mkdir -p "$STAGE/usr/bin"
cp /usr/lib/xorg/Xorg       "$STAGE/usr/lib/xorg/Xorg"
cp /usr/lib/xorg/Xorg.wrap  "$STAGE/usr/lib/xorg/Xorg.wrap" 2>/dev/null || true
# Wrapper script
cat > "$STAGE/usr/bin/Xorg" << 'WRAP'
#!/bin/sh
exec /usr/lib/xorg/Xorg "$@"
WRAP
chmod +x "$STAGE/usr/bin/Xorg"
cat > "$STAGE/usr/bin/X" << 'XWRAP'
#!/bin/sh
exec /usr/lib/xorg/Xorg "$@"
XWRAP
chmod +x "$STAGE/usr/bin/X"

# ── Xorg modules (drivers + input + extensions) ─────────────────────
mkdir -p "$STAGE/usr/lib/xorg/modules"
cp -r /usr/lib/xorg/modules/. "$STAGE/usr/lib/xorg/modules/"

# ── Shared libraries for Xorg + all modules ─────────────────────────
mkdir -p "$STAGE/lib/x86_64-linux-gnu"
collect_libs() {
    local bin="$1"
    local libs
    libs=$(ldd "$bin" 2>/dev/null | grep "=> /" | awk '{print $3}')
    for lib in $libs; do
        [ -f "$lib" ] || continue
        cp -n "$lib" "$STAGE/lib/x86_64-linux-gnu/" 2>/dev/null || true
        real=$(readlink -f "$lib")
        [ "$real" != "$lib" ] && cp -n "$real" "$STAGE/lib/x86_64-linux-gnu/" 2>/dev/null || true
    done
}
collect_libs /usr/lib/xorg/Xorg
for mod in /usr/lib/xorg/modules/drivers/*.so \
           /usr/lib/xorg/modules/input/*.so \
           /usr/lib/xorg/modules/*.so; do
    [ -f "$mod" ] && collect_libs "$mod" || true
done

# ── XKB keyboard data ───────────────────────────────────────────────
mkdir -p "$STAGE/usr/share/X11"
cp -r /usr/share/X11/xkb "$STAGE/usr/share/X11/"

# ── X11 Fonts ───────────────────────────────────────────────────────
mkdir -p "$STAGE/usr/share/fonts"
cp -r /usr/share/fonts/X11 "$STAGE/usr/share/fonts/" 2>/dev/null || true

# ── xkbcomp binary (needed by Xorg for keyboard setup) ──────────────
if [ -f /usr/bin/xkbcomp ]; then
    cp /usr/bin/xkbcomp "$STAGE/usr/bin/xkbcomp"
    collect_libs /usr/bin/xkbcomp
fi

# ── Xorg.conf.d ─────────────────────────────────────────────────────
mkdir -p "$STAGE/etc/X11/xorg.conf.d"
cat > "$STAGE/etc/X11/xorg.conf" << 'XCONF'
Section "ServerFlags"
  Option "AutoAddDevices" "true"
  Option "AutoEnableDevices" "true"
EndSection

Section "Device"
  Identifier "virtio-gpu"
  Driver     "modesetting"
  Option     "AccelMethod" "none"
EndSection

Section "Monitor"
  Identifier "Monitor0"
  Option     "DPMS" "false"
EndSection

Section "Screen"
  Identifier "Screen0"
  Device     "virtio-gpu"
  Monitor    "Monitor0"
  DefaultDepth 24
  SubSection "Display"
    Depth 24
    Modes "1280x800" "1024x768" "800x600"
  EndSubSection
EndSection

Section "InputClass"
  Identifier "keyboard"
  MatchIsKeyboard "yes"
  Driver "libinput"
EndSection

Section "InputClass"
  Identifier "pointer"
  MatchIsPointer "yes"
  Driver "libinput"
EndSection
XCONF

# ── libinput Xorg input driver ───────────────────────────────────────
LIBINPUT_DRV="/usr/lib/xorg/modules/input/libinput_drv.so"
[ -f "$LIBINPUT_DRV" ] || LIBINPUT_DRV=$(find /usr/lib -name "libinput_drv.so" 2>/dev/null | head -1)
if [ -f "$LIBINPUT_DRV" ]; then
    mkdir -p "$STAGE/usr/lib/xorg/modules/input"
    cp "$LIBINPUT_DRV" "$STAGE/usr/lib/xorg/modules/input/"
    collect_libs "$LIBINPUT_DRV"
fi

tar -czf "$TARBALL" -C "$STAGE" .
rm -rf "$STAGE"

echo "[xorg-pkg] tarball: $TARBALL ($(du -h "$TARBALL" | cut -f1))"
echo "[xorg-pkg] DONE"
