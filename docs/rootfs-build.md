# Rootfs Build Guide

This guide walks through building a bootable minimal root filesystem using cogman.

---

## Prerequisites

- Linux x86_64 host with `gcc`, `make`, `nproc`
- Rust toolchain (`cargo build` must work)
- Sufficient disk space: ~2 GB for sources and build artifacts

### Install the tools

```sh
cd /path/to/rogue-linux
make all
# Verifies: bin/cogman-planner, bin/cogman-executor, bin/cogman exist
```

---

## Step 1 — Fetch Package Sources

Source tarballs are not committed to the repository. Fetch them before building.

```sh
# Linux kernel headers (6.6.75)
scripts/build/fetch.sh packages/toolchain/linux-headers/linux-headers.toml

# BusyBox (1.36.1, static)
scripts/build/fetch.sh packages/base/busybox/busybox.toml

# base-files is self-contained (tarball is committed)
```

Tarballs land in `packages/<category>/<name>/tar/`. They are `.gitignore`d to keep the repo small.

### Manual fetch (if fetch script is unavailable)

```sh
mkdir -p packages/toolchain/linux-headers/tar
cd packages/toolchain/linux-headers/tar
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.6.75.tar.xz

mkdir -p packages/base/busybox/tar
cd packages/base/busybox/tar
wget https://busybox.net/downloads/busybox-1.36.1.tar.bz2
```

---

## Step 2 — Build Each Package

### Option A — Full rootfs script

```sh
sudo scripts/build/rootfs.sh --native
```

This script iterates over all `packages/**/*.toml` files in dependency order, runs the planner then executor for each, and assembles the result under `/mnt/rogue/pkgroot/`.

### Option B — Build packages individually

```sh
PKGROOT=/tmp/pkg-root

# 1. Linux headers
bin/cogman-planner packages/toolchain/linux-headers/linux-headers.toml \
    --output /tmp/linux-headers.plan --root $PKGROOT
bin/cogman-executor /tmp/linux-headers.plan --manifest-out /tmp/linux-headers.manifest

# 2. BusyBox (depends on linux-headers)
bin/cogman-planner packages/base/busybox/busybox.toml \
    --output /tmp/busybox.plan --root $PKGROOT
bin/cogman-executor /tmp/busybox.plan --manifest-out /tmp/busybox.manifest

# 3. base-files (depends on busybox)
bin/cogman-planner packages/base/base-files/base-files.toml \
    --output /tmp/base-files.plan --root $PKGROOT
bin/cogman-executor /tmp/base-files.plan --manifest-out /tmp/base-files.manifest
```

---

## Step 3 — Finalize the Rootfs

After all packages are built, merge and finalize:

```sh
python3 scripts/utils/finalize_rootfs.py \
    --pkgroot /mnt/rogue/pkgroot \
    --output  /mnt/rogue
```

This copies staged files from each package's directory into the merged rootfs and applies any final fixups (symlinks, permissions, etc.).

---

## Step 4 — Install Cogman

Copy the cogman binary into the rootfs so it can run as init:

```sh
mkdir -p /mnt/rogue/usr/bin /mnt/rogue/etc/cogman/services
cp bin/cogman /mnt/rogue/usr/bin/cogman
chmod +x /mnt/rogue/usr/bin/cogman

# Install default service files
cp etc/cogman/services/*.service /mnt/rogue/etc/cogman/services/
```

---

## Step 5 — Configure Boot

### Kernel command line

Tell the kernel to use cogman as init:

```
init=/usr/bin/cogman daemon --services /etc/cogman/services
```

With GRUB:
```
linux /boot/vmlinuz root=/dev/sda1 init=/usr/bin/cogman daemon --services /etc/cogman/services
```

### Inittab fallback (if using busybox init)

If you want busybox's `init` to spawn cogman (rather than using cogman directly as PID 1):

```
# /etc/inittab
::sysinit:/usr/bin/cogman daemon --services /etc/cogman/services
::respawn:/bin/sh
```

---

## Step 6 — Create a Bootable Image

### Using QEMU (disk image)

```sh
# Create a 2 GB ext4 image
dd if=/dev/zero of=rootfs.img bs=1M count=2048
mkfs.ext4 rootfs.img
mkdir -p /mnt/img
mount rootfs.img /mnt/img
cp -a /mnt/rogue/. /mnt/img/
umount /mnt/img

# Boot
qemu-system-x86_64 \
  -kernel /boot/vmlinuz \
  -append "root=/dev/sda rw init=/usr/bin/cogman daemon --services /etc/cogman/services console=ttyS0" \
  -hda rootfs.img \
  -serial stdio -nographic
```

---

## Minimal Rootfs Contents

After a successful build, `/mnt/rogue` should contain at minimum:

```
bin/busybox               BusyBox multi-call binary
bin/sh → busybox          Shell symlink
sbin/init → busybox       Init symlink (fallback)
usr/bin/cogman            Cogman supervisor + package manager
usr/include/linux/        Linux kernel headers
usr/include/asm/
etc/
  cogman/services/        Service definitions
  inittab                 BusyBox init configuration
  passwd                  Users (root + nobody)
  group                   Groups
  hostname
  hosts
  fstab
  nsswitch.conf
  profile
  os-release
  init.d/rcS              System startup script
proc/                     Mount point for procfs
sys/                      Mount point for sysfs
dev/                      Device nodes (or devtmpfs mount point)
tmp/
var/log/
var/run/
```

---

## Troubleshooting

### Build fails: `installer.steps must not be empty`
The TOML file has an empty `[installer] steps = []`. Move build steps that produce output into `[installer]`.

### BusyBox fails: `silentoldconfig: command not found`
The `.config` was modified without running `oldconfig`. The busybox.toml includes the fix:
```toml
"make -C busybox-1.36.1 oldconfig < /dev/null",
```
Ensure this step is present.

### `((INSTALLED++))` causes script to exit
This is a bash `set -e` interaction with arithmetic expansion. Fixed in `scripts/build/rootfs.sh`:
```bash
INSTALLED=$((INSTALLED + 1))   # correct
# NOT: ((INSTALLED++))         # wrong — exits when INSTALLED=0
```

### Linux headers too large for Git (100 MB limit)
The `linux-6.6.75.tar.xz` is 140 MB. It is excluded from the repository via `.gitignore`:
```
packages/toolchain/*/tar/*.xz
packages/toolchain/*/tar/*.gz
```
Always fetch tarballs locally after cloning.
