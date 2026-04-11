# Rogue Linux — Cogman

A deterministic, metadata-driven build system and init supervisor for constructing minimal Linux-based OS images.

---

## What is Rogue Linux?

Rogue Linux is not a distribution. It is an infrastructure for building one. Given a set of package definitions, it produces a reproducible root filesystem that can boot as a minimal Linux system — with cogman as the init process.

The system has two distinct halves:

**Build half** — turns package definitions into a rootfs:
- `cogman-planner` (Rust) — reads TOML package metadata, resolves dependencies, emits a binary build plan
- `cogman-executor` (C) — executes the plan in an isolated environment, installs files into a staging root

**Runtime half** — manages processes once the OS is running:
- `cogman` (Rust, unified) — init daemon that spawns, monitors, heals, and controls services; also installs packages

---

## Repository Layout

```
rogue-linux/
├── packages/               Package definitions
│   ├── base/
│   │   ├── busybox/        busybox-1.36.1 (static build, init scripts)
│   │   └── base-files/     /etc skeleton, inittab, rcS
│   └── toolchain/
│       └── linux-headers/  linux-6.6.75 kernel headers
├── cogman/
│   ├── bin/                Compiled binaries (cogman, cogman-planner, etc.)
│   ├── src/
│   │   ├── Cargo.toml      Rust workspace (planner, advisor, cogman)
│   │   ├── planner/        cogman-planner binary (Rust)
│   │   ├── advisor/        AI advisor crate (Ollama / llama.cpp backend)
│   │   ├── cogman/         Unified cogman daemon (Rust, v2)
│   │   ├── executor/       cogman-executor binary (C11)
│   │   └── supervisor/     Legacy C supervisor (deprecated)
├── etc/
│   └── cogman/services/    Service definition files (*.service)
├── scripts/
│   ├── build/              rootfs.sh, fetch.sh, security checks
│   └── utils/              finalize_rootfs.py, helpers
├── docs/                   Architecture and reference documentation
└── Makefile                Top-level build
```

---

## Quick Start

### Build the tools

```sh
make all       # builds planner + executor + cogman, copies to bin/
make install   # copies bin/ to /usr/local/bin (requires sudo)
```

### Fetch package sources

```sh
scripts/build/fetch.sh packages/base/busybox/busybox.toml
scripts/build/fetch.sh packages/toolchain/linux-headers/linux-headers.toml
```

### Build a minimal rootfs

```sh
sudo scripts/build/rootfs.sh --native
# Output: /mnt/rogue/pkgroot/ with busybox, base-files, linux headers
```

### Run cogman as init (on target)

```sh
# As PID 1 (kernel command line: init=/usr/bin/cogman daemon)
cogman daemon --services /etc/cogman/services

# Service control
cogman svc list
cogman svc status syslogd
cogman svc stop xorg
cogman svc restart wm

# Package management
cogman pkg install /packages/base/busybox/busybox.toml
cogman pkg remove busybox
cogman pkg list
```

---

## Architecture

### Build Pipeline

```
package.toml
    │
    ▼
cogman-planner
    Reads TOML metadata
    Resolves dependency graph (topological sort)
    Validates build + installer steps
    Applies filesystem policy (read/write path restrictions)
    ──→  <name>.plan   (binary, CGM2PLAN format)
    │
    ▼
cogman-executor
    mmaps the plan file
    Executes each step in a controlled staging environment
    Verifies expected output files (SHA-256 checksums)
    Installs files into $PKGROOT/<package>/
    Writes file manifest to <name>.manifest
    │
    ▼
$PKGROOT/<package>/   (staged package root)
    │
    ▼
finalize_rootfs.py    (merges package roots into the final rootfs)
    │
    ▼
/mnt/rogue/           (bootable root filesystem)
```

### Cogman v2 Daemon

The unified `cogman` binary has three modes:

| Mode | Command | Description |
|------|---------|-------------|
| Init daemon | `cogman daemon` | Supervisor loop; reads `*.service` files |
| Service control | `cogman svc <verb>` | Talks to live daemon over Unix socket |
| Package management | `cogman pkg <verb>` | Install / remove / upgrade packages |

---

## Performance

| Metric | Legacy (Python) | Current | Improvement |
|--------|-----------------|---------|-------------|
| Plan resolution | ~450 ms | ~8 ms | 56x |
| Peak memory | ~85 MB | ~4 MB | 21x |
| Exec overhead per step | ~45 ms | ~0.9 ms | 50x |

---

## Documentation

- [Package Format](docs/package-format.md) — TOML schema for package definitions
- [Cogman Daemon](docs/cogman-daemon.md) — daemon CLI, socket protocol, health checks
- [Service Files](docs/service-files.md) — `*.service` format for the runtime supervisor
- [Build Architecture](docs/architecture.md) — planner/executor design and binary plan format
- [Rootfs Build Guide](docs/rootfs-build.md) — step-by-step guide to a bootable rootfs
