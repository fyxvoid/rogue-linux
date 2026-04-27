#!/usr/bin/env bash
# boot-qemu-gui.sh — Boot Rogue Linux with i3 graphical session in QEMU
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KERNEL="$ROOT/rootfs/boot/vmlinuz-6.6.75"
INITRD="$ROOT/build/rogue-linux.cpio.gz"

[ -f "$KERNEL" ] || { echo "ERROR: kernel not found at $KERNEL"; exit 1; }
[ -f "$INITRD" ] || { echo "ERROR: initramfs not found at $INITRD"; exit 1; }

# KVM: use qemu64 CPU model — host passthrough triggers LAPIC SMP hang
KVM_ARGS=""
if [ -e /dev/kvm ] && qemu-system-x86_64 -enable-kvm -version >/dev/null 2>&1; then
    KVM_ARGS="-enable-kvm -cpu qemu64"
    echo "  KVM: enabled (hardware acceleration)"
else
    echo "  KVM: not available — boot will be slow (TCG)"
fi

# Single CPU — avoids SMP LAPIC wakeup hang with virtio-vga
NCPUS=1

echo "Booting Rogue Linux — i3 graphical session"
echo "  kernel : $(du -h "$KERNEL" | cut -f1)"
echo "  initrd : $(du -h "$INITRD" | cut -f1)"
echo "  cpus   : $NCPUS"
echo ""
echo "  i3 keybindings (Super = Win/Meta key):"
echo "    Super+Return   — Alacritty terminal"
echo "    Super+d        — dmenu launcher"
echo "    Super+q        — close window"
echo "    Super+h/j/k/l  — focus left/down/up/right"
echo "    Super+1..4     — switch workspace"
echo "    Super+f        — fullscreen"
echo "    Super+Shift+e  — exit i3"
echo ""
echo "  Serial log: this terminal (ttyS0 console)"
echo "  Press Ctrl-C here to kill QEMU"
echo ""

exec qemu-system-x86_64 \
    $KVM_ARGS \
    -m 1G \
    -smp "$NCPUS" \
    -kernel "$KERNEL" \
    -initrd "$INITRD" \
    -append "console=ttyS0 console=tty1 rdinit=/sbin/init maxcpus=1" \
    -device virtio-vga \
    -display gtk,zoom-to-fit=on \
    -usb \
    -device usb-tablet \
    -device usb-kbd \
    -serial mon:stdio \
    -no-reboot
