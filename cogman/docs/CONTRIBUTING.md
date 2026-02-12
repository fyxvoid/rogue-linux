# Contributing to Cogman

Welcome to the team. Cogman is open to contributors who share our passion for high-performance, minimalist, and intelligent systems.

## 🗺️ How to Get Started

1.  **Read the [Architecture Docs](../docs/README.md)**: Solidify your understanding of the Planner/Executor split.
2.  **Clone & Build**:
    ```bash
    cargo build  # Builds the Planner and Advisor
    cd src/executor && make  # Builds the Executor
    ```
3.  **Explore the Issues**: Look for "Beginner" or "Optimization" tags.

## 🛠️ The Developer Workflow

-   **Bug in Logic?** Check the Rust codebase in `src/planner`.
-   **Bug in Execution?** Check the C codebase in `src/executor`.
-   **Adding a HUD Icon?** Modify `rman.h` and the Messenger module.
-   **Fine-Tuning the AI?** See the `src/advisor/training` directory.

## 📏 Coding Standards

-   **Rust**: Use `cargo fmt` and `cargo clippy`. No `unsafe` without an architecture review.
-   **C**: Strictly C11. No heap allocation (malloc/free) in the execution hot-path. Use static buffers and `mmap` for data.
-   **Comments**: Documentation should be generated from code where possible, but architectural "Why" comments are mandatory for complex logic.

## 🧪 Testing

We believe in **Automated Precision**.
-   `cargo test`: For all planner and advisor logic.
-   `src/executor/tests`: Unit tests for binary plan parsing.
-   `./bin/cogman-planner demo-packages/bash/package.toml`: A full integration test.

## 💡 Philosophy
> **"Elegance is not when there is nothing more to add, but when there is nothing left to take away."**

Keep it small, keep it fast, and keep it tactical.
