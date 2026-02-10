# cogmanII

> **Status**: [FROZEN] Pre-Rootfs Integration
> **Architecture Contract**: [ARCHITECTURE.md](ARCHITECTURE.md)

A deterministic, clean-room build orchestrator for Rogue Linux.
**Rust** Planner (decisions) + **C** Executor (actions).

## The Human Mental Model

1.  **Input**: You define a package in a simple TOML file (identity, build steps).
2.  **Plan**: The Rust Planner reads your TOML and resolves the dependency graph.
3.  **Resolve**: It calculates the exact, topological build order required.
4.  **Emit**: It generates a single, immutable `.plan` binary file.
5.  **Execution**: The C Executor maps this file into memory.
6.  **Timeline**: It plays the plan like a tape (Mkdir → Exec → Copy → Verify).
7.  **Isolation**: Each step runs in a fresh, isolated process; no state leaks.
8.  **Output**: If successful, a directory map is created at `$PKGROOT`.
9.  **Handoff**: This directory is passed to the rootfs builder for merging.
10. **Philosophy**: No magic, no runtime solving, just deterministic execution.

## Usage

### 1. Build a Plan
```bash
# Binary mode (default)
cogmanII build metadata/profiles/base.toml -o install.plan

# Native build mode
cogmanII build --build --native metadata/profiles/base.toml -o build.plan
```

### 2. Execute a Plan
```bash
# Execute (requires root or permission to write to /mnt/rogue/pkgroot)
sudo cogmanII-exec install.plan
```

## Project Structure

- **planner/**: Rust. Logic, graphs, decisions.
- **executor/**: C. Syscalls, process lifecycle, strict obedience.
- **metadata/**: TOML. Single source of truth.

## Documentation

See [ARCHITECTURE.md](ARCHITECTURE.md) for:
- Identity & Boundaries (The "Never" List)
- Metadata Schema v1.0
- Failure Philosophy
- System Interfaces
