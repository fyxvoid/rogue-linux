# Rogue Linux — Documentation Index

---

## Getting Started

New here? Read these first:

1. [../README.md](../README.md) — project overview, quick start, architecture summary
2. [rootfs-build.md](rootfs-build.md) — build a bootable rootfs from scratch
3. [package-format.md](package-format.md) — write your first package definition

---

## Reference

| Document | Description |
|----------|-------------|
| [package-format.md](package-format.md) | TOML schema for `*.toml` package definitions |
| [cogman-daemon.md](cogman-daemon.md) | Unified cogman CLI, daemon modes, socket protocol, health checks |
| [service-files.md](service-files.md) | `*.service` INI format for the runtime supervisor |
| [architecture.md](architecture.md) | Planner, executor, binary plan format, AI advisor |
| [rootfs-build.md](rootfs-build.md) | Step-by-step rootfs build guide |

---

## Architecture (existing)

| Document | Description |
|----------|-------------|
| [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) | Two-stage pipeline deep dive |
| [architecture/DATA-FLOW.md](architecture/DATA-FLOW.md) | Immutable data transformation |
| [architecture/DETERMINISM.md](architecture/DETERMINISM.md) | Reproducible build strategy |
| [architecture/FAILURE-MODEL.md](architecture/FAILURE-MODEL.md) | Error handling across planner/executor |
| [architecture/ROOTFS-CONTRACT.md](architecture/ROOTFS-CONTRACT.md) | Package manager / filesystem interface |
| [architecture/AI-BOUNDARIES.md](architecture/AI-BOUNDARIES.md) | AI advisor safety boundaries |
| [architecture/ai_architecture.md](architecture/ai_architecture.md) | Model selection and training pipeline |

## Implementation (existing)

| Document | Description |
|----------|-------------|
| [implementation/EXECUTION.md](implementation/EXECUTION.md) | How build plans are executed |
| [implementation/PACKAGE-LIFECYCLE.md](implementation/PACKAGE-LIFECYCLE.md) | From source tarball to installed package |
| [implementation/METADATA.md](implementation/METADATA.md) | Package TOML schema (legacy reference) |
| [implementation/LOGGING.md](implementation/LOGGING.md) | Logging conventions |

## Project

| Document | Description |
|----------|-------------|
| [project/HISTORY.md](project/HISTORY.md) | Project evolution |
| [project/FINAL_REPORT.md](project/FINAL_REPORT.md) | Build system achievement summary |
| [../VERIFICATION_AUDIT.md](../VERIFICATION_AUDIT.md) | Final audit results |

---

## Key Source Locations

| Path | Description |
|------|-------------|
| `cogman/src/planner/` | cogman-planner (Rust) — TOML → binary plan |
| `cogman/src/executor/` | cogman-executor (C) — plan → installed files |
| `cogman/src/cogman/` | unified cogman daemon (Rust v2) |
| `cogman/src/advisor/` | AI advisor crate |
| `packages/` | Package definitions (TOML + tarballs) |
| `etc/cogman/services/` | Runtime service definitions |
| `scripts/build/` | rootfs.sh, fetch.sh |
