# Cogman Documentation

This directory contains the authoritative documentation for the **Roguelinux Build System (Cogman)**.
These documents define the system contract, architecture, and behavior.

> **Status**: Production-Ready (Validation Complete)
> **Version**: 1.0 (Pre-Rootfs)

## System Overview
- **[COGMAN-IDENTITY.md](COGMAN-IDENTITY.md)**: What cogman is (Build System) and what it is not (Package Manager).
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: High-level design: Rust Planner + C Executor.
- **[DATA-FLOW.md](DATA-FLOW.md)**: Traceability from TOML source code to executed syscalls.
- **[METADATA.md](METADATA.md)**: The schema contract for package definitions (TOML v1.0).

## Core Concepts
- **[INSTALL-VARIANTS.md](INSTALL-VARIANTS.md)**: Build from source (Native) vs Installation (Binary).
- **[EXECUTION.md](EXECUTION.md)**: The lifecycle of a build execution (steps, environment).
- **[DETERMINISM.md](DETERMINISM.md)**: Guarantees for reproducible builds and caching.
- **[FAILURE-MODEL.md](FAILURE-MODEL.md)**: How dependencies handle failure (Abort vs Warn).
- **[TMP-LIFECYCLE.md](TMP-LIFECYCLE.md)**: Management of ephemeral build directories.

## Developer Guide
- **[LOGGING.md](LOGGING.md)**: Philosophy of "Butler Personality" logging.
- **[TESTING.md](TESTING.md)**: Strategy, harness, and regression suite.
- **[BENCHMARKING.md](BENCHMARKING.md)**: Performance metrics against legacy and reference systems.
- **[AI-BOUNDARIES.md](AI-BOUNDARIES.md)**: Proper usage of AI assistance within the codebase.

## Future Integration
- **[ROOTFS-INTERFACE.md](ROOTFS-INTERFACE.md)**: Contract for the upcoming rootfs construction phase.

## Quick Start
```bash
# Build planner & executor
make

# Run unit & integration tests
make test

# Build a package
./cogman build metadata/base/bash/bash.toml --native
```
