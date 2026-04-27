#!/usr/bin/env bash
set -euo pipefail

ROOT="$PWD"
PKG_DIR="$ROOT/packages"

mkdir -p "$PKG_DIR"

log() { echo "[+] $1"; }
fail() { echo "[!] $1"; exit 1; }

download() {
    local url="$1"
    local file="$PKG_DIR/$(basename "$url")"

    if [[ -f "$file" ]]; then
        log "Exists: $(basename "$file")"
    else
        log "Downloading: $(basename "$file")"
        curl -L --fail -o "$file" "$url" || fail "Download failed: $url"
    fi
}

log "==== Core Xorg + i3 + polybar dependencies ===="

# ===== XORG CORE =====
download https://www.x.org/releases/individual/xserver/xorg-server-21.1.8.tar.xz
download https://www.x.org/releases/individual/lib/libX11-1.8.7.tar.xz
download https://www.x.org/releases/individual/lib/libXext-1.3.5.tar.xz
download https://www.x.org/releases/individual/lib/libxcb-1.15.tar.xz
download https://www.x.org/releases/individual/lib/libXrandr-1.5.3.tar.xz
download https://www.x.org/releases/individual/lib/libXinerama-1.1.5.tar.xz
download https://www.x.org/releases/individual/lib/libXcursor-1.2.1.tar.xz
download https://www.x.org/releases/individual/lib/libXrender-0.9.11.tar.xz
download https://www.x.org/releases/individual/lib/libXfixes-6.0.1.tar.xz
download https://www.x.org/releases/individual/lib/libXi-1.8.1.tar.xz
# ===== XCB (CRITICAL FOR i3) =====
download https://xcb.freedesktop.org/dist/xcb-proto-1.15.2.tar.xz
download https://xcb.freedesktop.org/dist/libxcb-1.15.tar.xz
download https://xorg.freedesktop.org/archive/individual/lib/xcb-util-0.4.1.tar.xz
download https://xcb.freedesktop.org/dist/xcb-util-keysyms-0.4.0.tar.xz
download https://xcb.freedesktop.org/dist/xcb-util-wm-0.4.2.tar.xz
download https://xcb.freedesktop.org/dist/xcb-util-xrm-1.3.tar.xz

# ===== FONT + RENDERING =====
download https://download.savannah.gnu.org/releases/freetype/freetype-2.13.2.tar.xz
download https://www.freedesktop.org/software/fontconfig/release/fontconfig-2.15.0.tar.xz
download https://cairographics.org/releases/cairo-1.18.0.tar.xz
download https://github.com/harfbuzz/harfbuzz/releases/download/8.3.0/harfbuzz-8.3.0.tar.xz
download https://github.com/libexpat/libexpat/releases/download/R_2_6_2/expat-2.6.2.tar.xz

# ===== SYSTEM LIBS =====
download https://pkgconfig.freedesktop.org/releases/pkg-config-0.29.2.tar.gz
download https://dbus.freedesktop.org/releases/dbus/dbus-1.14.10.tar.xz
download https://github.com/libev/libev/archive/refs/tags/v4.33.tar.gz
download https://github.com/yshui/picom/archive/refs/tags/v10.2.tar.gz

# ===== AUDIO (polybar optional but common) =====
download https://www.alsa-project.org/files/pub/lib/alsa-lib-1.2.11.tar.bz2

# ===== JSON + IPC =====
download https://github.com/DaveGamble/cJSON/archive/refs/tags/v1.7.17.tar.gz
download https://github.com/libuv/libuv/archive/refs/tags/v1.48.0.tar.gz

# ===== i3 WINDOW MANAGER =====
download https://i3wm.org/downloads/i3-4.23.tar.xz

# ===== polybar =====
download https://github.com/polybar/polybar/archive/refs/tags/3.7.0.tar.gz

log "==== Download complete ===="
echo "All packages are in: $PKG_DIR"
