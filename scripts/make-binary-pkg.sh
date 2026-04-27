#!/usr/bin/env bash
# make-binary-pkg.sh — Bundle a host binary + all its shared libs into a cogman binary package tarball
# Usage: bash make-binary-pkg.sh <binary-path> <pkg-name> <category> <version>
# Output: packages/<category>/<pkg-name>/tar/<pkg-name>-<version>.tar.gz
#         packages/<category>/<pkg-name>/<pkg-name>.toml
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BINARY="$1"
NAME="$2"
CATEGORY="$3"
VERSION="$4"

PKG_DIR="$ROOT/packages/$CATEGORY/$NAME"
TAR_DIR="$PKG_DIR/tar"
STAGE="$(mktemp -d)"
TARBALL="$TAR_DIR/$NAME-$VERSION.tar.gz"

echo "[make-binary-pkg] $NAME $VERSION from $BINARY"

mkdir -p "$TAR_DIR"
mkdir -p "$STAGE/usr/bin"
mkdir -p "$STAGE/lib/x86_64-linux-gnu"

# Copy the binary
install -m755 "$BINARY" "$STAGE/usr/bin/$NAME"

# Collect all shared library dependencies (excluding vdso and ld-linux)
ldd "$BINARY" 2>/dev/null | grep "=> /" | awk '{print $3}' | while read -r lib; do
    [ -f "$lib" ] || continue
    echo "  bundling lib: $lib"
    cp -n "$lib" "$STAGE/lib/x86_64-linux-gnu/" 2>/dev/null || true
    # Also follow any symlinks (soname aliases)
    real=$(readlink -f "$lib")
    [ "$real" = "$lib" ] || cp -n "$real" "$STAGE/lib/x86_64-linux-gnu/" 2>/dev/null || true
done

# Build tarball
tar -czf "$TARBALL" -C "$STAGE" .
rm -rf "$STAGE"

SIZE=$(du -h "$TARBALL" | cut -f1)
echo "[make-binary-pkg] tarball: $TARBALL ($SIZE)"

# Count bundled files
N_LIBS=$(tar -tzf "$TARBALL" | grep "lib/x86_64-linux-gnu/" | wc -l)
echo "[make-binary-pkg] bundled: 1 binary + $N_LIBS libs"

# Generate .toml
cat > "$PKG_DIR/$NAME.toml" << TOML
[identity]
name     = "$NAME"
version  = "$VERSION"
category = "$CATEGORY"
summary  = "$NAME $VERSION — binary package bundled from host"

[identity.source]
kind = "tarball"
file = "$NAME-$VERSION.tar.gz"

[identity.depends]
build   = []
runtime = []

[build]
system  = "make"
variant = "binary"
steps   = []

[installer]
steps = []

[installer.verify]
expected_files = ["usr/bin/$NAME"]

[policy.filesystem]
read  = ["/"]
write = ["/"]
TOML

echo "[make-binary-pkg] toml: $PKG_DIR/$NAME.toml"
echo "DONE"
