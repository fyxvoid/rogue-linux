# Build System Architecture

This document describes how cogman turns package definitions into an installed rootfs.

---

## Overview

The build system is split into two processes with a well-defined binary interface between them. This separation keeps validation logic (Rust, safe) separate from execution logic (C, fast).

```
package.toml  ──►  cogman-planner  ──►  .plan (binary)  ──►  cogman-executor  ──►  $PKGROOT/
```

Neither process is a general-purpose shell script runner. The planner understands dependency graphs and security policy; the executor understands only a handful of typed step operations.

---

## cogman-planner

**Language:** Rust  
**Binary:** `bin/cogman-planner`  
**Source:** `cogman/src/planner/`

### Responsibilities

1. **Load and validate** — parses `package.toml` using the `serde`/`toml` crate and validates against the v1.0 schema.
2. **Resolve dependencies** — builds a directed acyclic graph of package dependencies using `petgraph`. Detects cycles and missing packages.
3. **Topological sort** — emits packages in build order (dependencies first).
4. **Emit binary plan** — serialises the build + install steps into the CGM2PLAN binary format.
5. **Apply policy** — embeds filesystem restriction metadata into the plan for the executor to enforce.
6. **Cache** — plans are content-addressed by input hash; re-planning is skipped if the plan is current.

### Dependency resolution

Dependencies are declared as `category/name` strings. The resolver scans the `packages/` tree, loads all available TOML files, and builds a full graph before emitting any plan. This means a single invocation can plan an entire dependency closure.

---

## CGM2PLAN Binary Format

The plan file is a compact binary read by the executor via `mmap`. Zero allocation, zero parsing overhead.

```
┌─────────────────────────────────────┐
│ Header (64 bytes)                    │
│   magic:            [u8; 8]          │  = b"CGM2PLAN"
│   version:          u32              │
│   step_count:       u32              │
│   str_table_offset: u64              │
│   str_table_len:    u64              │
│   flags:            u32              │
│   reserved:         [u8; 24]         │
├─────────────────────────────────────┤
│ Step records (128 bytes × N)         │
│   op:          u8                    │  1=EXEC 2=MKDIR 3=COPY 4=VERIFY 5=CLEANUP
│   flags:       u8                    │  0x01=STEP_FLAG_SERVICE
│   reserved:    [u8; 6]               │
│   arg_offsets: [u64; 8]              │  offsets into string table
│   reserved:    [u8; 56]              │
├─────────────────────────────────────┤
│ String table (variable)              │
│   NUL-terminated strings             │
└─────────────────────────────────────┘
```

### Step operations

| Op | Constant | Description |
|----|----------|-------------|
| 1 | `OP_EXEC` | Run a shell command (`/bin/sh -c arg[0]`) in the staging directory |
| 2 | `OP_MKDIR` | Create directory `arg[0]` with parents |
| 3 | `OP_COPY` | Copy file `arg[0]` to `arg[1]` |
| 4 | `OP_VERIFY` | Assert that path `arg[0]` exists; fail otherwise |
| 5 | `OP_CLEANUP` | Remove staging temp directory |

### Native variant step sequence

For source-built packages, the planner emits steps in this order:

```
OP_MKDIR  tmpdir
OP_EXEC   extract tarball
OP_EXEC   build step 1
OP_EXEC   build step 2
…
OP_EXEC   installer step 1
…
OP_VERIFY expected_file_1
OP_VERIFY expected_file_2
…
OP_CLEANUP
```

---

## cogman-executor

**Language:** C11  
**Binary:** `bin/cogman-executor`  
**Source:** `cogman/src/executor/`

### Responsibilities

1. **Open and mmap** the plan file (zero-copy read).
2. **Validate header** — checks magic bytes, version, and step count.
3. **Execute each step** in order:
   - `OP_EXEC` — `fork()` + `execve("/bin/sh", ["-c", cmd], envp)`; waits for completion.
   - `OP_MKDIR` — `mkdir -p` equivalent using `mkdirat`.
   - `OP_COPY` — `sendfile`-based copy with path traversal guard.
   - `OP_VERIFY` — `access(path, F_OK)`.
   - `OP_CLEANUP` — `rm -rf` of the temp directory.
4. **Write manifest** — if `--manifest-out` is given, writes the list of installed paths (one per line) for the package database.
5. **Abort on first failure** — any non-zero exit from a step terminates the executor with a non-zero exit code.

### Security

- **Path traversal guard** — `OP_COPY` destination is validated to remain within `$PKGROOT`. Any path that escapes via `..` is rejected with exit code 2.
- **SHA-256 verification** — `OP_VERIFY` can optionally check a hash: `verify path sha256=<hex>`.
- **No implicit shell** — only `OP_EXEC` runs a shell. `OP_COPY` and `OP_MKDIR` use syscalls directly.

---

## cogman (Unified Rust Daemon)

**Language:** Rust  
**Binary:** `bin/cogman`  
**Source:** `cogman/src/cogman/`  
**Version:** 2.0.0

The unified daemon integrates three previously separate concerns:

### Internal modules

| Module | Path | Role |
|--------|------|------|
| `db` | `src/db/mod.rs` | Binary package database (read/write) |
| `installer` | `src/installer/mod.rs` | Calls planner + executor; records manifest |
| `supervisor` | `src/supervisor/mod.rs` | Service lifecycle, health checks, restart |
| `supervisor/service` | `src/supervisor/service.rs` | Service definition parser |
| `ctl` | `src/ctl/mod.rs` | Unix socket server (daemon) and client helper |
| `policy` | `src/policy/mod.rs` | Landlock syscall wrappers (raw syscalls 444/445/446) |
| `main` | `src/main.rs` | CLI entry point (clap) |

### Landlock implementation

`policy/mod.rs` uses raw Linux syscall numbers (444=`landlock_create_ruleset`, 445=`landlock_add_rule`, 446=`landlock_restrict_self`) via `libc::syscall`. This avoids any dependency on kernel headers and will work on the Kingdom kernel if `CONFIG_SECURITY_LANDLOCK=y` is enabled.

Fallback: `ENOSYS` or `EOPNOTSUPP` → print warning, return `Ok(false)`, service starts without restriction.

---

## AI Advisor

**Language:** Rust  
**Crate:** `cogman/src/advisor/`

The advisor is an optional component that provides failure analysis via a locally-running LLM. It is gated by build flags and never called in the critical path.

- **Model:** Qwen2.5-3B-Instruct (4-bit quantized, ~2 GB VRAM)
- **Backend:** Ollama HTTP API or llama-cpp-python (configurable)
- **Training:** QLoRA fine-tuning on Rogue Linux build logs via `unsloth`
- **Trigger:** Called when the executor exits with a non-zero code
- **Output:** Plain-text diagnosis and suggested fix written to stderr

The advisor has no write access to the build environment. It reads failure context (last 50 lines of executor output + package metadata) and produces a suggestion. The operator decides what to do with it.

---

## Testing

```sh
# Unit + integration tests
python3 tests/run_all.py

# Test categories
tests/metadata/    Schema and validation tests (400+ cases)
tests/graph/       Dependency resolution tests (50+ cases)
tests/plan/        Plan generation and cache tests
tests/executor/    Path traversal, safety tests
tests/security/    Isolation and policy tests
tests/perf/        Performance regression tests
```
