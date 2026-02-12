# Cogman Identity

## What is Cogman?

**Cogman** (Coordinate & Manage) is the **Low-Level Build System** for Roguelinux.
Its sole responsibility is to transform a package definition (TOML) into a sequence of shell commands and execute them in a controlled environment.

It is analogous to `makepkg` (Arch) or `rpmbuild` (RedHat), but with integrated dependency resolution for local builds.

### Key Characteristics
1.  **Split Architecture**:
    -   **Planner (Rust)**: Resolves dependencies, validates metadata, and generates a static execution plan.
    -   **Executor (C)**: Reads the plan and executes it with zero logic variance.
2.  **Stateless Execution**: The executor has no memory of past builds. Input -> Output.
3.  **Strict Isolation**: Builds occur in ephemeral directories; artifacts are installed to a staging root (pkgroot).

## What is Cogman NOT?

1.  **Not a Package Manager**: Cogman does not manage the *installed* system state (like `pacman` or `dpkg`). It builds artifacts *to be installed* by a future package manager.
2.  **Not a Scraper**: It does not fetch metadata from the internet (except source tarballs). It operates on a local repository of TOML files.
3.  **Not AI-Generated**: While AI assisted in code generation, the **logic and architecture are human-defined and deterministic**.

## Design Philosophy

> "The Planner thinks so the Executor doesn't have to."

-   **Planner**: Validates everything. Resolves graphs. Handles complexity. Output is a dumb list of steps.
-   **Executor**: Just executes. Fast, safe, dumb. 110 lines of C for the main loop.

## Evolution
-   **cogman (Legacy)**: Python prototype. Deprecated.
-   **cogman (Current)**: The modular Rust+C implementation.
