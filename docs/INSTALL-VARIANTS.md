# Install Variants

Cogman supports two primary modes of operation for *every* package.

## 1. Native Build (`--build --native`)
**"Compile from Source"**
-   **Context**: Building the foundational system, bootstrapping, or user preference for optimization (`-march=native`).
-   **Input**: Source code tarball (`tar/`).
-   **Process**:
    1.  Unpack tarball to ephemeral build dir.
    2.  Run `[build]` steps (configure, compile).
    3.  Install artifacts to `${d}` (pkgroot).
-   **Result**: Binaries optimized for the build host.

## 2. Binary Install (`--build` default)
**"Install Pre-built"**
-   **Context**: Rapid deployment, installing pre-compiled packages (like a package manager).
-   **Input**: Pre-built package archive (or mocked via `installer` steps in current dev phase).
-   **Process**:
    1.  Unpack package archive directly to `${d}`.
    2.  Run `[installer]` hooks if any.
-   **Result**: Generic binaries.

## The Hybrid Model
The `planner` supports mixing strategies in the future, but currently enforces a global mode via CLI flags (`--native`).
If `--native` is set, **all** dependencies in the graph are built from source recursively.
If not set, **all** dependencies are installed as binaries.
