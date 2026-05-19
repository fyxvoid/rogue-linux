#!/usr/bin/env bash
# fix-and-boot.sh — Patch the disk image with all X11 fixes, then boot.
#
# Fixes applied:
#   1. xkbcomp shim  — precompiled us-pc105.xkm, avoids broken XKM in VM
#   2. startx        — dynamic input-event detection, generates runtime
#                      xorg.conf, uses vt7 to avoid getty/tty1 conflict
#   3. x11.service   — direct command (no shell wrapper), correct exit code
#
# Run with: sudo bash build/fix-and-boot.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMG="$ROOT/build/rogue-linux-disk.img"
MNT=$(mktemp -d)
LOOP=""

cleanup() {
    umount "$MNT"  2>/dev/null || true
    rmdir  "$MNT"  2>/dev/null || true
    [ -n "$LOOP" ] && losetup -d "$LOOP" 2>/dev/null || true
}
trap cleanup EXIT

[ "$(id -u)" = "0" ] || { echo "ERROR: run with sudo"; exit 1; }
[ -f "$IMG" ] || { echo "ERROR: disk image not found: $IMG"; exit 1; }

echo "[1/4] Attaching ${IMG}..."
LOOP=$(losetup -fP --show "$IMG")
echo "      loop: $LOOP"

echo "[2/4] Mounting root partition..."
mount "${LOOP}p2" "$MNT"

# ── Fix 1: xkbcomp shim ────────────────────────────────────────────────────
echo "[3/4] Patching disk image..."

# Try to compile the keymap on the host; fall back to copying the pre-built
# us-pc105.xkm from the rootfs (if it exists there).
XKM_SRC="$ROOT/rootfs/etc/X11/us-pc105.xkm"
if command -v xkbcomp >/dev/null 2>&1 && [ -d "$MNT/usr/share/X11/xkb" ]; then
    echo "      compiling keymap on host..."
    echo 'xkb_keymap {
  xkb_keycodes { include "evdev+aliases(qwerty)" };
  xkb_types    { include "complete" };
  xkb_compat   { include "complete" };
  xkb_symbols  { include "pc+us" };
  xkb_geometry { include "pc(pc105)" };
};' | xkbcomp -w0 -R"$MNT/usr/share/X11/xkb" -xkm - "$MNT/etc/X11/us-pc105.xkm" 2>/dev/null \
        || cp -v "$XKM_SRC" "$MNT/etc/X11/us-pc105.xkm" 2>/dev/null || true
elif [ -f "$XKM_SRC" ]; then
    echo "      copying pre-built us-pc105.xkm..."
    cp "$XKM_SRC" "$MNT/etc/X11/us-pc105.xkm"
else
    echo "WARNING: no keymap source — xkbcomp shim will fall back to xkbcomp.real"
fi

# xkbcomp shim: drain stdin, copy precompiled keymap to the requested output path
cat > "$MNT/usr/bin/xkbcomp" << 'XKBSHIM'
#!/bin/sh
cat > /dev/null
eval "LAST=\${$#}"
cp /etc/X11/us-pc105.xkm "$LAST" && exit 0
exit 1
XKBSHIM
chmod 755 "$MNT/usr/bin/xkbcomp"

# ── Fix 2: startx — dynamic input detection, vt7, runtime xorg.conf ────────
cat > "$MNT/usr/bin/startx" << 'STARTX'
#!/bin/sh
mkdir -p /tmp/.X11-unix /tmp/.ICE-unix /var/log
chmod 1777 /tmp/.X11-unix /tmp/.ICE-unix

# Reinstall xkbcomp shim on every start
cat > /usr/bin/xkbcomp << 'SHIM'
#!/bin/sh
cat > /dev/null
eval "LAST=\${$#}"
cp /etc/X11/us-pc105.xkm "$LAST" && exit 0
exit 1
SHIM
chmod 755 /usr/bin/xkbcomp

# Dynamically detect virtio input event nodes.
# QEMU's default PS/2 devices can push virtio devices to event2+.
KBD_EV=""
PTR_EV=""
in_kbd=0; in_ptr=0
while IFS= read -r line; do
    case "$line" in
        N:*[Kk]ey*|N:*keyboard*)         in_kbd=1; in_ptr=0 ;;
        N:*[Mm]ouse*|N:*[Pp]oint*|N:*[Tt]ouch*|N:*[Tt]ablet*)
                                           in_kbd=0; in_ptr=1 ;;
        N:*)                               in_kbd=0; in_ptr=0 ;;
        H:*Handlers*)
            ev=$(printf '%s' "$line" | grep -oE 'event[0-9]+' | head -1)
            [ -n "$ev" ] && [ "$in_kbd" = 1 ] && [ -z "$KBD_EV" ] && KBD_EV=$ev
            [ -n "$ev" ] && [ "$in_ptr" = 1 ] && [ -z "$PTR_EV" ] && PTR_EV=$ev
            ;;
    esac
done < /proc/bus/input/devices

# /sys fallback
if [ -z "$KBD_EV" ]; then
    for d in /dev/input/event*; do
        nm=$(cat "/sys/class/input/$(basename "$d")/device/name" 2>/dev/null)
        case "$nm" in *eyboard*|*KEY*) KBD_EV=$(basename "$d"); break ;; esac
    done
fi
if [ -z "$PTR_EV" ]; then
    for d in /dev/input/event*; do
        nm=$(cat "/sys/class/input/$(basename "$d")/device/name" 2>/dev/null)
        case "$nm" in *ouse*|*ointer*) PTR_EV=$(basename "$d"); break ;; esac
    done
fi
[ -z "$KBD_EV" ] && KBD_EV=event0
[ -z "$PTR_EV" ] && PTR_EV=event1

echo "startx: kbd=/dev/input/$KBD_EV  ptr=/dev/input/$PTR_EV"

# Generate runtime xorg.conf with detected input device paths.
cat > /tmp/xorg-runtime.conf << XORGEOF
Section "ServerFlags"
  Option "AutoAddDevices"    "false"
  Option "AutoEnableDevices" "false"
  Option "AllowEmptyInput"   "false"
EndSection
Section "Device"
  Identifier "gpu0"
  Driver     "modesetting"
  Option     "AccelMethod" "none"
EndSection
Section "Monitor"
  Identifier "Monitor0"
  Option     "DPMS" "false"
EndSection
Section "Screen"
  Identifier "Screen0"
  Device     "gpu0"
  Monitor    "Monitor0"
  DefaultDepth 24
  SubSection "Display"
    Depth 24
    Modes "1280x800" "1024x768" "800x600"
  EndSubSection
EndSection
Section "InputDevice"
  Identifier  "vkbd"
  Driver      "evdev"
  Option      "Device"      "/dev/input/$KBD_EV"
  Option      "XkbRules"    "evdev"
  Option      "XkbModel"    "pc105"
  Option      "XkbLayout"   "us"
  Option      "XkbVariant"  ""
  Option      "XkbOptions"  ""
EndSection
Section "InputDevice"
  Identifier  "vmouse"
  Driver      "evdev"
  Option      "Device"      "/dev/input/$PTR_EV"
  Option      "Protocol"    "auto"
EndSection
Section "ServerLayout"
  Identifier   "Layout0"
  Screen       "Screen0"
  InputDevice  "vkbd"    "CoreKeyboard"
  InputDevice  "vmouse"  "CorePointer"
EndSection
Section "Module"
  Disable "glx"
  Disable "dri"
  Disable "dri2"
  Disable "dri3"
EndSection
XORGEOF

# Switch to vt7 first so the QEMU GTK window shows X on startup.
chvt 7 2>/dev/null || true

xinit /etc/X11/xinit/xinitrc -- /usr/lib/xorg/Xorg :0 vt7 \
  -nolisten tcp -novtswitch \
  -config /tmp/xorg-runtime.conf \
  -logfile /tmp/Xorg.log \
  -logverbose 3

RC=$?
if [ $RC -ne 0 ]; then
    echo "=== Xorg failed (exit $RC) ===" >&2
    grep -E "\(EE\)|\(WW\)|Fatal|Cannot|No screens|modesetting|evdev" \
        /tmp/Xorg.log 2>/dev/null | head -40 >&2
fi
exit $RC
STARTX
chmod 755 "$MNT/usr/bin/startx"

# ── Fix 3: x11.service — direct command, correct exit code propagation ─────
# The old shell wrapper used "; echo ..." which always exited 0 so
# restart=on-failure could never fire.  Run startx directly instead.
cat > "$MNT/etc/cogman/services/x11.service" << 'X11SVC'
[service]
name          = x11
type          = process
command       = /usr/bin/startx
restart       = on-failure
restart_delay = 5
depends       = rcs, mdev, input-probe

[env]
PATH                  = /usr/bin:/bin:/usr/sbin:/sbin
HOME                  = /home/void
USER                  = void
LOGNAME               = void
TERM                  = xterm-256color
LIBINPUT_QUIRKS_DIR   = /usr/share/libinput
X11SVC

echo "      patched: xkbcomp  startx  x11.service"

echo "[4/4] Installing fresh initramfs into disk /boot..."
# The system runs from the initramfs (switch_root to disk has issues).
# Putting the updated initramfs inside the disk fixes the GRUB boot path too.
INITRD_SRC="$ROOT/build/rogue-linux.cpio.gz"
if [ -f "$INITRD_SRC" ]; then
    cp "$INITRD_SRC" "$MNT/boot/initramfs.cpio.gz"
    echo "      initramfs : $(du -h "$MNT/boot/initramfs.cpio.gz" | cut -f1)"
else
    echo "      WARNING: $INITRD_SRC not found — run: bash build/build-initramfs.sh first"
fi

echo "[5/5] Unmounting and detaching..."
sync
umount "$MNT"
losetup -d "$LOOP"
LOOP=""
trap - EXIT
rmdir "$MNT"

echo ""
echo "Disk patched. Two boot options:"
echo ""
echo "  RECOMMENDED (bypasses initramfs, uses disk directly):"
echo "    sudo bash $(realpath "$ROOT/build/boot-x11.sh")"
echo ""
echo "  GRUB path (uses updated initramfs in disk):"
echo "    sudo bash $(realpath "$ROOT/build/boot-qemu-gui.sh")"
