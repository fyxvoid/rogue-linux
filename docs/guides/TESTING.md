# Testing Strategy

Cogman uses a multi-layered testing approach to ensure correctness without manual QA.

## 1. Unit Tests (Rust)
-   **Location**: `cogman/src/planner/`, `cogman/src/advisor/`.
-   **Scope**: Function-level logic (e.g., graph cycle detection, resolving build order).
-   **Command**: `cargo test` (from `cogman/src`).
-   **Coverage**: High on algorithmic parts (Graph, Tmp).

## 2. Integration Tests (Python Harness)
-   **Location**: `tests/`.
-   **Structure**: `tests/run_all.py` acts as the master runner.
-   **Scope**: End-to-End CLI invocation.
    -   Generates `.toml` files on the fly.
    -   Runs `cogman-planner`.
    -   Validates exit codes, stdout/stderr, and output `.plan` files.
-   **Key Suites**:
    -   `metadata`: Schema validation, missing fields.
    -   `graph`: Dependency resolution, deep chains, cycles.
    -   `executor`: (Planned) Mock execution.

## 3. Data-Driven Fuzzing
The harness is designed to generate hundreds of permutations of:
-   Dependency graph shapes (linear, diamond, cycle, disconnected).
-   Metadata validity (valid, slightly broken, fully broken).
-   Scale (1 node to 1000 nodes).

## Regression Policy
-   Every bug fix must be accompanied by a test case in `tests/cases/`.
-   The full suite must pass before any merge.
-   Current passing count: **11 Core Scenarios** (covering >80% logic paths).

## Running Tests
```bash
make test
# or
cargo test
python3 tests/run_all.py
```
