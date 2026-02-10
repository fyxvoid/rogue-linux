# Execution Lifecycle

This document describes the step-by-step lifecycle of a Cogman execution.

## 1. Initialization
-   **Planner**: Parses CLI args. Check if `metadata` exists.
-   **Logging**: Initializes strictly controlled stdout/stderr channels.

## 2. Planning
-   **Load**: Reads target TOML. Recursively finds dependencies.
-   **Sort**: Determines build order (e.g., `zlib` -> `bash`).
-   **Generate**:
    -   Allocates `PlanStep` vector.
    -   For each package in order:
        -   **Prepare**: `mkdir -p /tmp/build/<pkg>`
        -   **Unpack**: `tar -xf ...`
        -   **Build**: Execute `steps` from TOML in `/tmp/build/<pkg>`.
        -   **Install**: Copy artifacts to `/mnt/rogue/pkgroot/<pkg>`.
        -   **Cleanup**: `rm -rf /tmp/build/<pkg>` (unless `--keep-tmp`).
    -   **Emit**: Writes `.plan` file.

## 3. Hand-off
-   Planner exits (0).
-   User (or script) calls `cogman-exec`.

## 4. Execution
-   **Load**: `mmap` the plan file. Validates header.
-   **Loop**:
    -   Read Step `N`.
    -   `fork()` child process.
    -   **Child**:
        -   `setenv` variables.
        -   `chdir` to `workdir`.
        -   `execvp` the command.
    -   **Parent**:
        -   `waitpid`.
        -   Check exit code.
        -   If != 0, ABORT immediately (unless `FailPolicy::Warn`).

## 5. Completion
-   Executor exits (0) if all steps passed.
-   Artifacts are now present in `/mnt/rogue/pkgroot`.
