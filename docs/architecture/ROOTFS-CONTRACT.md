# ROOTFS CONSTRUCTION CONTRACT

**Status**: VALIDATED (Dry-Run Passed)
**Date**: 2026-02-10

## 1. Directory Layout
The rootfs MUST adhere to the following FHS-compliant structure:

| Path | Type | Target | Permissions |
|---|---|---|---|
| `/` | Dir | - | 0755 |
| `/bin` | Link | `usr/bin` | - |
| `/sbin` | Link | `usr/bin` | - |
| `/lib` | Link | `usr/lib` | - |
| `/lib64` | Link | `usr/lib` | - |
| `/usr` | Dir | - | 0755 |
| `/etc` | Dir | - | 0755 |
| `/var` | Dir | - | 0755 |
| `/tmp` | Dir | - | 1777 (Sticky) |
| `/run` | Dir | - | 0755 |

## 2. Input Contract (Cogman)
- **Source**: Cogman writes to `$PKGROOT` (e.g., `/tmp/cogman-build-bash/root`).
- **Dest**: Rootfs Constructor copies `$PKGROOT/*` to `$ROOTFS/*`.
- **Constraint**: Cogman MUST NOT produce absolute symlinks targeting outside `$PKGROOT`.
- **Constraint**: Cogman MUST NOT produce files owned by non-root users (UID 0).

## 3. Output Contract (Rootfs)
- **Isolation**: The rootfs directory is a chroot jail candidate.
- **Escape**: No symlink within rootfs may point outside the rootfs tree.
- **Mutable State**: 
    - `/tmp`: Writable, cleared on boot.
    - `/run`: Writable, cleared on boot.
    - `/var`: Writable, persistent.
    - `/usr`: Read-only (conceptually).

## 4. Safety Verification
- **Traversal Check**: All symlinks must resolve to paths within the rootfs.
- **Permission Check**: `/tmp` must have sticky bit (1777).
- **Ownership Check**: All files must be owned by Root (0:0).

## 5. Failure Policy
If any contract violation is detected during construction:
1.  **Abort** immediately.
2.  **Clean** the partial rootfs.
3.  **Report** the offending package and file.
