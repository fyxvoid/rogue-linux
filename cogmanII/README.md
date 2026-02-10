# cogmanII

A clean-room reimplementation of `cogman` using a high-performance stack:
**TOML** for metadata, **Rust** for planning, **C** for execution.

## Architecture

```
TOML metadata ──→ Rust planner ──→ binary plan ──→ C executor
      │                │                │               │
   metadata/       planner/          .plan file     executor/
   (human)        (decisions)        (mmap-able)    (machine)
```

**One-directional data flow.** No feedback loops, no runtime configuration.

### cogman → cogmanII Mapping

| cogman component | cogmanII equivalent | Language |
|---|---|---|
| `metadata/loader.py` | `planner/src/parse.rs` | YAML → TOML |
| `metadata/verifier.py` | `planner/src/validate.rs` | Python → Rust |
| *(not implemented)* | `planner/src/graph.rs` | — → Rust |
| `builder/builder.py` | `planner/src/variants.rs` | Python → Rust |
| `core/executor.py` | `executor/src/proc.c` | Python → C |
| `deployer/*.py` | `executor/src/fs.c` | Python → C |
| `core/log/voice.py` | `executor/src/log.c` | Python → C |

## Install Variants

cogmanII supports exactly **two** installation variants, mutually exclusive:

### Binary Install (default)

Installs prebuilt binaries. No compilation on the target machine.

```
cogmanII build --binary metadata/profiles/bash.toml -o plan.bin
cogmanII-exec plan.bin
```

Steps: extract archive → verify → copy into rootfs.

### Native Build

Compiles packages on the user's machine. Optional CPU-native optimizations.

```
cogmanII build --build metadata/profiles/bash.toml -o plan.bin
cogmanII build --build --native metadata/profiles/bash.toml -o plan.bin
```

Steps: create tmpdir → extract → configure → build → verify → install → cleanup.

The `--native` flag injects:
```
CFLAGS="-march=native -mtune=native -O2"
CXXFLAGS="-march=native -mtune=native -O2"
```

### Temporary Build Directory Lifecycle

```
create → build → verify → install → cleanup
```

- All native builds occur in `/tmp/cogmanII-build-<name>/`
- Verification checks artifact presence before installation
- Failed verification aborts — no partial installs
- `--keep-tmp` preserves temp dirs for debugging

## CLI

```
cogmanII build   <metadata.toml> [--binary|--build] [--native] [--keep-tmp] [-o plan.bin]
cogmanII install <metadata.toml> [-o plan.bin]
cogmanII deploy  <metadata.toml> [--binary|--build] [--native] [--keep-tmp] [-o plan.bin]

cogmanII-exec <plan.bin>
```

| Flag | Meaning |
|---|---|
| `--binary` | Binary install variant (default) |
| `--build` | Native build variant |
| `--native` | CPU-native optimizations (requires `--build`) |
| `--keep-tmp` | Preserve temporary build directories |
| `-o` | Output plan file (default: stdout) |
| `--rootfs` | Target rootfs path (default: `/mnt/rogue`) |

## Plan Artifact Format

Binary, mmap-friendly, zero-copy:

```
┌──────────────────────────────┐
│ PlanHeader      (64 bytes)   │  magic: "CGM2PLAN", version, variant, step_count
├──────────────────────────────┤
│ StepRecord[0]  (128 bytes)   │  op, fail_policy, offsets into string table
│ StepRecord[1]  (128 bytes)   │
│ ...                          │
├──────────────────────────────┤
│ String Table   (variable)    │  null-terminated command strings, env pairs
└──────────────────────────────┘
```

The C executor `mmap()`s this file and walks it without allocating or parsing.

## Building

### Planner (Rust)

```
cd planner
cargo build --release
```

Binary: `planner/target/release/cogman2-planner`

### Executor (C)

```
cd executor
make
```

Binary: `executor/cogmanII-exec`

## Why cogmanII Is Faster

| Factor | cogman | cogmanII |
|---|---|---|
| Startup | Python interpreter (~50ms) | Native binary (~1ms) |
| Metadata parse | PyYAML + jsonschema | `serde` + typed structs |
| Plan transfer | In-memory Python dicts | mmap'd flat binary |
| Execution | `subprocess.run()` via shell | `fork()/execve()` direct |
| Memory | Python runtime (~30MB RSS) | C executor (~1MB RSS) |
| Dependency resolution | Not implemented | `petgraph` topological sort |

## Design Philosophy

- **dwm-style minimalism**: small, sharp, explicit
- **No plugin systems**: compile what you need
- **No dynamic configuration**: all decisions at plan time
- **Determinism over convenience**: same input → same plan → same result
- **Speed over extensibility**: one purpose, done well
