#!/usr/bin/env bash
# boot-x11-init.sh — Boot Rogue Linux with X11+DWM using initramfs (no disk required)
#
# Uses the cpio initramfs directly (-initrd) so no disk image rebuild is needed.
# Boots full services including x11.service → startx → Xorg → xinitrc → dwm.
#
# Controls:
#   GTK window: click to focus, then use normal DWM keys
#   DWM keybindings (default):  Mod=Alt
#     Alt+Shift+Enter  → open st terminal
#     Alt+p            → dmenu (app launcher)
#     Alt+Shift+c      → close focused window
#     Alt+Shift+q      → quit dwm (will cause x11 service restart)
#   Serial console:   Ctrl-A then C  → QEMU monitor
#                     Ctrl-A then X  → exit QEMU
#
# Usage: bash build/boot-x11-init.sh [extra qemu args]

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KERNEL="$ROOT/rootfs/boot/vmlinuz-6.6.75"
INITRD="$ROOT/build/rogue-linux.cpio.gz"

[ -f "$KERNEL" ] || { echo "ERROR: kernel not found — run: ./pipeline.sh kernel"; exit 1; }
[ -f "$INITRD" ] || { echo "ERROR: initramfs not found — run: ./pipeline.sh initramfs"; exit 1; }

KVM_ARGS=""
if [ -e /dev/kvm ]; then
    KVM_ARGS="-enable-kvm -cpu host"
    echo "  KVM: enabled"
else
    echo "  KVM: not available (TCG — slower)"
fi

echo ""
echo "╔═════════════════════════════════════════════════════════╗"
echo "║   Rogue Linux — X11 + DWM (initramfs boot)            ║"
echo "╚═════════════════════════════════════════════════════════╝"
echo "  kernel : $KERNEL  ($(du -h "$KERNEL" | cut -f1))"
echo "  initrd : $INITRD  ($(du -h "$INITRD" | cut -f1))"
echo ""
echo "  DWM keys:  Alt+Shift+Enter=terminal  Alt+p=dmenu  Alt+Shift+q=quit"
echo "  QEMU:      Ctrl-A X = exit  |  Ctrl-A C = monitor"
echo ""
echo "  X11 will appear in the GTK window within ~10-15 seconds."
echo ""

exec qemu-system-x86_64 \
    $KVM_ARGS \
    -m 1G \
    -smp "$(nproc)" \
    -kernel "$KERNEL" \
    -initrd "$INITRD" \
    -append "rdinit=/init console=ttyS0 -- --services-dir /etc/cogman/services" \
    -vga virtio \
    -display gtk,zoom-to-fit=on \
    -device virtio-keyboard-pci \
    -device virtio-mouse-pci \
    -device virtio-net-pci,netdev=eth0 \
    -netdev user,id=eth0 \
    -serial mon:stdio \
    "$@"
