# Deterministic Build Guarantees

Cogman aims for **Reproducible Builds to the Bit**.
While full bit-for-bit reproducibility depends on the compiler toolchain, Cogman enforces **process determinism**.

## Guarantees

1.  **Fixed Build Order**: The topological sort of the dependency graph is stable. If the graph shape is identical, the execution order is identical.
2.  **Ephemerality**: Every build starts in a pristine, empty `/tmp` directory. No state leaks from previous builds (stateless executor).
3.  **Isolation**: The build environment is minimal. (Future: namespace isolation / chroot).
4.  **No Network (Planned)**: In Native mode, network access is disabled by default during the `build` phase, forcing all inputs to be declared in `sources`.

## Rules for Package Maintainers

To maintain determinism:
-   **Do not use `/tmp` or `/var/tmp`** for inter-step communication. Use the provided build directory.
-   **Do not rely on valid timestamps**. The build system may clamp mtimes.
-   **Explicitly list all dependencies**. Implicit dependencies (e.g., relying on system tools not in `base`) are forbidden.

## Validation
The Planner hashes the input TOML.
Changing whitespace in TOML -> New Hash -> Rebuild (future optimization).
Currently, the system rebuilds everything requested.
