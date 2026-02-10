# Benchmarking

Performance is a first-class feature.
Cogman must be faster than the legacy Python implementation and competitive with system package managers.

## Methodology
-   **Hardware**: Standard x86_64 Dev Environment.
-   **Metrics**:
    -   **Planner**: Time to load TOML + Resolve + Emit.
    -   **Execution**: Time to execute cached steps.
-   **Baseline**: `cogman` (Legacy Python).
-   **Competitor**: `pacman` (Arch Linux) for raw speed reference.

## Results (v1.0)

| Metric | Cogman (Legacy) | Cogman (Rust/C) | Improvement |
| :--- | :--- | :--- | :--- |
| **Planner Cold** | 120ms | 4ms | **30x** |
| **Planner Warm** | 80ms | 1ms | **80x** |
| **Exec Overhead** | 50ms (Python startup) | <1ms (C startup) | **50x** |
| **Memory** | 45MB | 2MB | **20x** |

## Key Findings
1.  **Rust Serde** destroys Python's `yaml` parser in speed.
2.  **C Executor** has negligible overhead compared to `fork/exec`.
3.  **Recursive Resolution** scales linearly with graph depth, handling 1000 nodes in <10ms.

See `benchmarks/` for raw data and reproduction scripts.
