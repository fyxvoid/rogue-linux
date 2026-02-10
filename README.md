# rogue-linux

A minimal, deterministic Linux distribution build system.

## What This Project Is
Rogue Linux is a metadata-driven build system for creating Linux distributions. It is designed to be deterministic—given the same inputs, it produces the same outputs. It uses a strict two-stage pipeline to separate planning (what to do) from execution (actually doing it). It prioritizes correctness and speed over convenience.

## What This Project Is NOT
- **Not a package manager**: It doesn't handle runtime updates or repository syncing.
- **Not an init system**: It builds the OS; it doesn't manage services at boot.
- **Not a runtime configuration tool**: It builds stable images.
- **Not AI-driven execution**: AI is used for advice, not for deciding what code runs on your hardware.

## Core Component: cogman
`cogman` is the engine that drives rogue-linux. 
- **What it does**: Resolves dependencies, generates build plans, and executes them in isolated environments.
- **What it never does**: Improvises. If a step isn't in the plan, it won't happen.
- **Planner vs Executor**: The system is split into a Rust planner (`cogman-planner`) and a C executor (`cogman-exec`).
- **Why?**: Rust handles complex metadata and graphs safely. C executes the resulting plan with near-zero overhead and absolute obedience.

## High-Level Architecture
1. **TOML**: You define your package metadata in TOML.
2. **Plan**: The planner validates the metadata and emits a binary `.plan` file.
3. **Executor**: The C executor maps the plan and runs the steps.

This one-directional flow means you can verify exactly what a build will do before it ever touches your filesystem.

## Performance Summary
The rewrite from legacy Python to Rust/C changed everything:
- **Planner**: 30x to 80x faster resolution.
- **Executor**: 50x less overhead on process startup.
- **Memory**: 20x reduction in peak usage.

Speed comes from Rust's `serde` for metadata and a "stateless" C executor that removes runtime logic entirely. For details, see [docs/BENCHMARKING.md](docs/BENCHMARKING.md).

## Testing & Validation
We don't guess. The system is verified by a suite of 500–600 generated test cases covering metadata failures, graph cycles, and plan correctness. We only move toward rootfs construction when the tooling is 100% validated for determinism. See [docs/TESTING.md](docs/TESTING.md).

## AI Assistance (Clear Boundaries)
AI is used in the planner for **Advisory Only** tasks—like explaining why a build failed.
- AI is optional (gated by a build flag).
- AI never executes code or modifies the binary plan.
- AI runs locally.
- See [docs/AI-BOUNDARIES.md](docs/AI-BOUNDARIES.md).

## Documentation Map
Detailed deep-dives are in the `docs/` directory:
- [ARCHITECTURE.md](docs/ARCHITECTURE.md): The two-stage design.
- [METADATA.md](docs/METADATA.md): How to define packages.
- [TESTING.md](docs/TESTING.md): Our validation strategy.
- [BENCHMARKING.md](docs/BENCHMARKING.md): Performance results.
- [ROOTFS-INTERFACE.md](docs/ROOTFS-INTERFACE.md): How we talk to the filesystem.
- [AI-BOUNDARIES.md](docs/AI-BOUNDARIES.md): Strict rules for LLM usage.

## Project Status
The **Toolchain and Validation** phase is complete. The binaries are stable, documentation is authoritative, and the performance baseline is set. **Rootfs work is intentionally not started yet**; we build the tool correctly before we build the system.

## How to Read This Repo
1. Start with [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). It’s the mental model.
2. Read [docs/METADATA.md](docs/METADATA.md) to see how components are defined.
3. If you care about numbers, check [docs/BENCHMARKING.md](docs/BENCHMARKING.md).

Deep dives into failure models and lifecycle live in `docs/` as well.

## Philosophy
- **Determinism over convenience**: We would rather a build fail than be "guessable."
- **Planning over improvisation**: The host system is never a side effect.
- **Boring systems are good systems**: No magic, just a pipeline.
