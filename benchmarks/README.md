# Benchmarking Methodology

This directory contains the scripts and data used to validate Cogman's performance.

## Structure
- `scripts/`: Python scripts to execute benchmarks.
- `results/raw-data/`: CSV outputs from runs.

## Running Benchmarks
```bash
# Requires root for Arch comparison (pacman)
# If not root, Arch steps are skipped.
python3 scripts/benchmark.py
```

## Methodology
We compare three systems:
1.  **Cogman (Legacy)**: Python implementation (reference for improvement).
2.  **Cogman (Current)**: Rust/C implementation.
3.  **Arch Linux**: `pacman` binary install (reference for theoretical max speed).

## Metrics
-   **Planner Time**: Time to resolve graph and emit plan.
-   **Exec Time**: Time to execute the plan (syscall overhead).
-   **Memory**: RSS peak.
