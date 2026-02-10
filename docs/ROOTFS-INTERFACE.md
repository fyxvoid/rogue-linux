# Rootfs Interface (Future)

This document defines the contract between Cogman and the future `rootfs` construction stage.

## The Hand-off
Cogman's job ends when artifacts are installed to `pkgroot`.
It does **not** create the final bootable image.

## Contract
1.  **Output Directory**: `/mnt/rogue/pkgroot`.
2.  **Structure**:
    ```
    /mnt/rogue/pkgroot/
    ├── bash/
    │   ├── bin/bash
    │   └── usr/share/man/...
    ├── zlib/
    │   └── usr/lib/libz.so
    ```
3.  **Metadata**:
    -   Cogman will (in future) generate a manifest file describing what was installed.
    -   `pkgroot/manifest.json`? (TBD)

## Rootfs Constructor Responsibilities
The next tool (not Cogman) will:
1.  Read the list of installed packages in `pkgroot`.
2.  Merge them into a single filesystem tree (handling conflicts?).
3.  Install strict configuration (`/etc`).
4.  Generate initramfs / bootloader config.
5.  Pack into `.img` or `.iso`.

## Cogman Constraints
-   Cogman **never** modifies `/etc` or `/boot` of the host.
-   Cogman **never** writes outside of `pkgroot` (except `/tmp`).
