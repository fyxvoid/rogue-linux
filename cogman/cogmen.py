#!/usr/bin/env python3

import sys
from pathlib import Path

from core.log.voice import info, ok, err
from builder.builder import build_package
from metadata.loader import PackageMetadata
from metadata.verifier import verify


def main():
    if len(sys.argv) < 3:
        err("Usage: cogmen <verify|build|install> <package-path>")
        sys.exit(1)

    cmd, pkg = sys.argv[1], sys.argv[2]
    pkg_path = Path("packages") / pkg
    metadata_path = pkg_path / "metadata"

    info(f"Preparing to operate on package '{pkg}'")

    # Load metadata
    meta = PackageMetadata(metadata_path).load()

    # Always verify first
    verify(meta)

    if cmd == "verify":
        ok("Verification completed successfully")
        sys.exit(0)

    elif cmd == "build":
        build_package(pkg, pkg_path, meta)
        sys.exit(0)

    elif cmd == "install":
        err("Installation phase is not implemented yet")
        sys.exit(1)

    else:
        err(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
