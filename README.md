# Rogue Linux

A from-scratch Linux distribution built around **cogman** — a custom init system, service supervisor, and package manager written in Rust and C.

Rogue Linux boots to a real shell, runs a window manager (dwm), manages services declaratively, and installs packages via TOML plans compiled to binary. No systemd, no glibc package manager, no distribution scaffolding.

---

## What It Is

Rogue Linux is a complete operating system built from the ground up:

- **Custom kernel** — Linux 6.6.75, hand-tuned config (`build/kernel.config`): DRM/KMS, BPF, netfilter, VIRTIO, WiFi drivers (iwlwifi, ath9k, ath10k, rtl8xxxu, mac80211_hwsim), pentest subsystems
- **Custom init** — `cogman-supervisor` runs as PID 1; spawns, monitors, and heals services from `.service` definition files
- **Custom package manager** — `cogman-planner` (Rust) compiles TOML package plans to binary; `cogman-executor` (C) executes them; signed plans verified via minisign before execution
- **Minimal rootfs** — busybox + GNU coreutils + util-linux, X11 + dwm, pentest tools available as cogman plans
- **Reproducible builds** — ISO and disk images built from shell scripts with no external tooling

The design goal is a lean, auditable OS where every component is understood and controlled. Secondary goal: a capable pentest distribution that doesn't carry Kali's bloat.

---

## Architecture

### Boot Flow

```
GRUB2 (EFI)
    │
    ▼
initramfs  ──→  parses root=UUID= from cmdline
    │            waits for block device
    │            mounts ext4 root
    ▼
switch_root / exec  ──→  rootfs/init (shell script)
    │                     mounts /proc /sys /dev /run
    ▼
cogman-supervisor  (PID 1)
    │  reads /etc/cogman/services/*.service
    │  resolves dependency graph (DFS cycle detection)
    │  starts services in topological order
    ▼
rcs → mdev → tty1-6 → syslogd → ntpd → dropbear → eth0-dhcp → iwd → x11 …
```

Two boot paths are supported:
- **initramfs path**: GRUB loads `vmlinuz + initramfs.cpio.gz`; pivot_root into the disk partition
- **Direct disk path**: QEMU boots directly from the ext4 partition; no initramfs needed

### Cogman Components

```
cogman/src/
├── planner/        Rust — reads package.toml, resolves deps, emits .plan binary
├── executor/       C11 — mmaps .plan, verifies minisign signature, executes steps
├── cogman/         Rust — unified daemon: init supervisor + service control + pkg mgmt
├── supervisor/     Shell — cogman-supervisor (PID 1 wrapper) and cogman-ctl CLI
├── advisor/        Rust — AI advisor (local llama.cpp inference or Ollama backend)
└── messenger/      RMAN protocol — structured inter-component messaging
```

### Package System

A package is a TOML file. The planner compiles it to a binary `.plan`; the executor verifies its signature (if a pubkey is configured) then runs it:

```toml
[identity]
name    = "curl"
version = "8.7.1"
category = "base"
summary  = "Command-line HTTP client"

[identity.source]
kind = "none"

[build]
system = "autotools"
steps  = []

[installer]
steps = [
    """
    wget https://curl.se/download/curl-8.7.1.tar.gz
    tar -xzf curl-8.7.1.tar.gz && cd curl-8.7.1
    ./configure --with-openssl --prefix=/usr
    make -j$(nproc) && make install
    """,
]
manifest = [
    "/usr/bin/curl",
    "/usr/lib/libcurl.so.4",
]

[uninstaller]
steps = ["rm -f /usr/bin/curl /usr/lib/libcurl*"]

[checksums]
"curl-8.7.1.tar.gz" = "<sha256-hex>"

[policy]
[policy.filesystem]
read  = ["/"]
write = ["/usr", "/tmp"]
[policy.network]
outbound = true
```

The planner enforces dependency ordering, verifies checksums, and detects cycles before a single step executes. The `manifest` field records every installed file — used for automatic cleanup on uninstall without relying solely on the `[uninstaller]` stanza.

### Package Signing

Plans can be signed with [minisign](https://jedisct1.github.io/minisign/). When a public key is configured, the executor verifies the `.plan.minisig` file before executing any step:

```sh
# Sign a plan (on the build machine)
minisign -S -s cogman.key -m package.plan

# Install with signature enforcement
cogman-exec package.plan --pubkey /etc/cogman/cogman.pub

# cogman-planner install passes --pubkey automatically if /etc/cogman/cogman.pub exists
cogman-planner install /path/to/package.toml
```

If `/etc/cogman/cogman.pub` exists but `--pubkey` is not passed, the executor warns. Once all plans are signed, the warning can be made a hard error.

### Service Definitions

Services are declarative `.service` files:

```ini
[service]
name    = dropbear
type    = process
command = /usr/sbin/dropbear -F -E -p 22
restart = on-failure
depends = rcs, dropbear-keygen
```

`cogman-supervisor` reads all files in `/etc/cogman/services/`, builds a dependency graph, and starts them in order. `cogman-ctl` controls running services over a Unix socket at `/run/cogman-supervisor.sock`.

---

## What Works

| Feature | Status |
|---|---|
| Boot to shell (QEMU + real hardware) | Done |
| cogman-supervisor as PID 1 | Done |
| Service dependency graph + cycle detection | Done |
| Multi-TTY (tty1–tty6) with PAM login | Done |
| Package install / uninstall / upgrade | Done |
| Package install records to `installed.db` automatically | Done |
| File manifests for clean uninstall | Done |
| Plan signature verification (minisign) | Done |
| Persistent disk image (GPT + ext4 + EFI) | Done |
| GRUB2 EFI bootloader | Done |
| initramfs pivot_root | Done |
| DHCP client + DNS | Done |
| SSH (dropbear) with first-boot key gen | Done |
| Firewall (nftables, drop-by-default) | Done |
| X11 + dwm window manager | Done |
| Syslog + klog daemons | Done |
| NTP sync | Done |
| `void` user, `doas` privilege escalation | Done |
| GNU coreutils + util-linux + iproute2 | Done |
| Binary analysis tools (strace, nm, readelf…) | Done |
| Dev toolchain (gcc, make, python3) | Done |
| Cogman web dashboard (port 7070) | Done |
| Kernel config tracked in repo (`build/kernel.config`) | Done |
| WiFi kernel drivers (iwlwifi, ath9k, ath10k, rtl8xxxu) | Config ready — needs kernel rebuild |
| WiFi daemon (iwd) | Plan + service written |
| Audio (ALSA/PipeWire) | Not yet |
| Online package repository | Not yet |
| Full disk encryption (LUKS) | Not yet |

---

## Repository Layout

```
rogue-linux/
├── build/                  Build scripts and QEMU boot helpers
│   ├── kernel.config       Kernel .config tracked here (source tree is gitignored)
│   ├── build-iso.sh        Assemble bootable ISO
│   ├── build-disk.sh       Create GPT disk image with GRUB
│   ├── build-kernel.sh     Compile Linux kernel
│   ├── build-initramfs.sh  Pack rootfs into cpio.gz initramfs
│   ├── boot-iso.sh         Boot ISO in QEMU
│   ├── boot-disk.sh        Boot disk image via UEFI GRUB in QEMU
│   ├── boot-qemu-gui.sh    Boot with GTK display (X11 testing)
│   ├── setup-deps.sh       Install host build dependencies
│   └── install-to-disk.sh  Write distribution to a real disk
├── cogman/
│   ├── src/                All cogman source code (Rust workspace + C)
│   └── docs/               Per-component documentation
├── plans/                  Cogman package plans (TOML)
│   ├── base/               Base system packages (iwd, …)
│   └── pentest/            Pentest tool plans (nmap, tcpdump, netcat, socat, gdb)
├── rootfs/                 The actual root filesystem (tracked in git)
│   ├── boot/               Kernel image
│   ├── etc/cogman/         Service definitions and config
│   ├── init                Boot init script (pivot_root logic)
│   └── usr/bin/            Binaries: cogman-planner, cogman-exec, busybox, coreutils…
├── benchmarks/             Benchmark scripts and raw results
├── archived/               Old Python prototype of cogman
└── pending.md              Roadmap and feature status
```

---

## Building

### Host Dependencies

```sh
# Debian / Kali
bash build/setup-deps.sh
```

Requires: `gcc`, `rustup`, `nasm`, `grub-pc-bin`, `grub-efi-amd64-bin`, `xorriso`, `qemu-system-x86_64`, `mtools`

### Build Everything

```sh
# 1. Compile cogman tools
cd cogman/src && cargo build --release
cp target/release/cogman_planner ../../rootfs/usr/bin/cogman-planner
cd executor && make && cp cogman-exec ../../rootfs/usr/bin/

# 2. Build kernel using the tracked config
cp build/kernel.config build/kernel/linux-6.6.75/.config
bash build/build-kernel.sh

# 3. Pack initramfs
bash build/build-initramfs.sh

# 4. Build ISO
bash build/build-iso.sh
# Output: build/rogue-linux.iso

# 5. (Optional) Build persistent disk image
bash build/build-disk.sh
# Output: build/rogue-linux-disk.img
```

### Run in QEMU

```sh
# ISO (RAM only, no persistence)
bash build/boot-iso.sh

# Disk image with persistence
bash build/boot-disk.sh

# GUI mode (for X11 / dwm)
bash build/boot-qemu-gui.sh
```

### Install to Real Hardware

```sh
# WARNING: destructive — replaces the target disk
sudo bash build/install-to-disk.sh /dev/sdX
```

---

## Service Management

```sh
cogman-ctl list              # show all services and their state
cogman-ctl status dropbear   # inspect a specific service
cogman-ctl start x11         # start a service
cogman-ctl stop x11          # stop a service
cogman-ctl restart dropbear  # restart a service
cogman-ctl stop-all          # graceful reverse-order shutdown
cogman-ctl list-pkgs         # show installed packages
```

The web dashboard at `http://localhost:7070` provides a browser-based view of service state.

---

## Package Management

```sh
# Install from a local plan — compiles plan + executes + records in installed.db
cogman-planner install /path/to/nmap.toml

# Install with signature verification
cogman-planner install /path/to/nmap.toml --pubkey /etc/cogman/cogman.pub

# Upgrade an installed package
cogman-planner upgrade nmap 7.96 /path/to/nmap-7.96.toml

# Generate and run an uninstall plan
cogman-planner uninstall --metadata /path/to/nmap.toml

# List installed packages
cogman-ctl list-pkgs
```

Package plans live in `plans/`. Installed packages are recorded in `/var/lib/cogman/installed.db`. File manifests are written to `/var/lib/cogman/manifests/<name>.manifest` and used for automatic cleanup on uninstall.

### Available Plans

| Category | Plan | Version | Description |
|---|---|---|---|
| base | `plans/base/iwd.toml` | 2.21 | WiFi daemon (iNet Wireless Daemon) |
| pentest | `plans/pentest/nmap.toml` | 7.95 | Network scanner + ncat |
| pentest | `plans/pentest/tcpdump.toml` | 4.99.5 | Packet capture |
| pentest | `plans/pentest/netcat.toml` | 1.229 | OpenBSD netcat |
| pentest | `plans/pentest/socat.toml` | 1.8.0.1 | Bidirectional relay |
| pentest | `plans/pentest/gdb.toml` | 15.2 | Debugger + gdbserver |

---

## WiFi Setup

WiFi kernel modules (iwlwifi, ath9k, ath10k, rtl8xxxu, mac80211_hwsim) are enabled in `build/kernel.config` but require a kernel rebuild to activate:

```sh
cp build/kernel.config build/kernel/linux-6.6.75/.config
bash build/build-kernel.sh
```

Once the kernel is rebuilt, install and start iwd:

```sh
cogman-planner install plans/base/iwd.toml
cogman-ctl start iwd
```

Connect to a network using `iwctl`:

```sh
iwctl
[iwd]# device list
[iwd]# station wlan0 scan
[iwd]# station wlan0 get-networks
[iwd]# station wlan0 connect "MyNetwork"
```

For QEMU testing, `mac80211_hwsim` creates a virtual wireless interface — load it with `modprobe mac80211_hwsim`.

---

## Default Credentials

| Field | Value |
|---|---|
| Username | `void` |
| Password | `rogue` |
| SSH port | `22` |
| Dashboard | `http://localhost:7070` |

---

## Project Status

Started February 2026. Currently boots on QEMU (x86_64) and real hardware (UEFI). X11 and dwm are working. Package signing, file manifests, and WiFi infrastructure are in place. The main remaining gaps are a kernel rebuild to activate WiFi modules, audio support, and an online package repository.

See [pending.md](pending.md) for the full roadmap and per-feature status.

---

## License

MIT
