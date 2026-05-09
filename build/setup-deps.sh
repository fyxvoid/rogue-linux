#!/usr/bin/env bash
# setup-deps.sh — Install all build dependencies for Rogue Linux ISO creation
# Run once as root before building.
set -euo pipefail

echo "Installing kernel build dependencies..."
apt-get install -y \
    bison flex bc \
    libssl-dev libelf-dev \
    gcc make \
    binutils

echo "Installing disk/ISO build tools..."
apt-get install -y \
    grub-efi-amd64-bin \
    grub-pc-bin \
    grub-common \
    xorriso \
    mtools \
    dosfstools \
    gdisk \
    squashfs-tools \
    e2fsprogs

echo "Installing X11 dev libs (for dwm/st)..."
apt-get install -y \
    libx11-dev \
    libxft-dev \
    libxinerama-dev \
    libfreetype-dev \
    libfontconfig1-dev

echo ""
echo "All dependencies installed. You can now run:"
echo "  bash build/build-kernel.sh"
echo "  sudo bash build/build-disk.sh"
echo "  sudo bash build/build-iso.sh"
