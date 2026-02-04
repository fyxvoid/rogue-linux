#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
PKGROOT="$ROOT/packages/toolchain"

echo "[+] Fetching toolchain sources (LFS reference, wget-only)"

# Ordered list (important)
PKGS=(
  linux-headers
  binutils
  gmp
  mpfr
  mpc
  gcc
)

URL_linux_headers="https://mirrors.edge.kernel.org/pub/linux/kernel/v6.x/linux-6.7.tar.xz"
URL_binutils="https://ftp.gnu.org/gnu/binutils/binutils-2.43.tar.xz"
URL_gmp="https://ftp.gnu.org/gnu/gmp/gmp-6.3.0.tar.xz"
URL_mpfr="https://ftp.gnu.org/gnu/mpfr/mpfr-4.2.1.tar.xz"
URL_mpc="https://ftp.gnu.org/gnu/mpc/mpc-1.3.1.tar.gz"
URL_gcc="https://ftp.gnu.org/gnu/gcc/gcc-14.1.0/gcc-14.1.0.tar.xz"

for pkg in "${PKGS[@]}"; do
  url_var="URL_${pkg//-/_}"
  url="${!url_var}"

  tar_dir="$PKGROOT/$pkg/tar"
  src_dir="$PKGROOT/$pkg/source"

  mkdir -p "$tar_dir" "$src_dir"

  file="$tar_dir/$(basename "$url")"
  extracted_flag="$src_dir/.extracted"

  echo "  • $pkg"

  if [[ ! -f "$file" ]]; then
    echo "    - downloading $(basename "$file")"
    wget -c --progress=bar:force:noscroll \
         -O "$file" \
         "$url"
  else
    echo "    - tarball already exists"
  fi

  if [[ ! -f "$extracted_flag" ]]; then
    echo "    - extracting"
    rm -rf "$src_dir"/*
    tar -xf "$file" -C "$src_dir"
    touch "$extracted_flag"
  else
    echo "    - already extracted"
  fi
done

echo "[✓] Toolchain sources ready"
