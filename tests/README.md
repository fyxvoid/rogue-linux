# CogmanII Validation Suite

> **Objective**: 500+ tests traversing 10 critical categories.
> **Harness**: `unittest` (Standard Library) + Custom Runner (`run_all.py`).

## Test Categories

1.  **Metadata Tests (120)**
    - Schema validation (missing fields, type mismatches).
    - Generator: `tests/metadata/gen_cases.py`.

2.  **Dependency Graph Tests (80)**
    - Cycles, diamonds, deep chains.
    - `cargo test` integration for core Rust logic.
    - Integration tests for end-to-end resolution.

3.  **Plan Generation Tests (90)**
    - Binary plan artifacts.
    - Header validation (magic bytes, version).

4.  **Executor Safety Tests (80)**
    - Fork/Exec isolation.
    - Permission handling.
    - Cleanup guarantees.

5.  **Tmp Directory Tests (50)**
    - Lifecycle, collision handling, `--keep-tmp`.

6.  **CLI & Flag Validation (40)**
    - Argument parsing, invalid combos.

7.  **Cross-Implementation Parity (40)**
    - `cogman` vs `cogmanII` output comparison.

8.  **Security & Isolation (30)**
    - Path traversal, env injection.

9.  **Performance Regression (30)**
    - Timing thresholds.

10. **AI-Boundary Tests (20)**
    - Containment verification.

## Directory Structure
```
tests/
  run_all.py        # Main entrypoint
  metadata/         # Category 1
  graph/            # Category 2
  plan/             # Category 3
  executor/         # Category 4
  tmp/              # Category 5
  cli/              # Category 6
  parity/           # Category 7
  security/         # Category 8
  perf/             # Category 9
  ai/               # Category 10
  utils/            # Shared helpers
```

## Running Tests
```bash
python3 tests/run_all.py
```
