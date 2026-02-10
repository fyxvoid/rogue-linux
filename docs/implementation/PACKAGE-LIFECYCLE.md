# Package Build Lifecycle

This document defines the standardized, isolated build and installation flow for all `rogue-linux` packages.

## Directory Layout

Each package in `packages/` follows a strict, predictable on-disk layout:

```text
packages/<pkgname>/
├── package.toml        # Normalized metadata (Schema v1.0)
├── tar/                # Source archives (strictly versioned)
├── source/             # Extracted source code (transient)
├── build/              # Out-of-tree build directory (isolated)
├── pkgroot/            # Staged installation root (DESTDIR)
├── logs/               # Compilation and install logs
└── README.md           # Package-level documentation
```

## Standardized Flow

### 1. Preparation
- **Metadata**: `cogman-planner` reads `package.toml` to extract variables (NAME, VERSION, SOURCE, DEPS).
- **Environment**: All build-related directories (`source`, `build`, `pkgroot`, `logs`) are created or cleaned.

### 2. Source Extraction
- **Action**: The archive in `tar/` is extracted into `source/`.
- **Constraint**: Extraction must be deterministic. Preferred command:
  `tar -xf tar/<file> -C source --strip-components=1`

### 3. Out-of-tree Build
- **Action**: Compilation occurs strictly inside the `build/` directory.
- **Independence**: The `source/` directory remains pristine (read-only during build whenever possible).
- **Isolation**: No host system paths are touched.

### 4. Staged Installation
- **Action**: The package is installed into `pkgroot/` using `DESTDIR` or equivalent.
- **Layout**: `pkgroot/` must mirror the final filesystem structure (e.g., `pkgroot/usr/bin/`).
- **Safety**: No files are written directly to the host filesystem.

### 5. Verification
- **Validation**: `cogman-executor` verifies `pkgroot/` against the `expected_files` list in `package.toml`.
- **Sanity Checks**: basic `file` and `ldd` checks ensure the artifacts are correct.

## Variables and Schema

Packages must adhere to the `[build]` schema:
- `system`: Build system type (autotools, cmake, meson, make).
- `configure.flags`: Portable flags for the configuration phase.
- `steps`: Unified list of commands for the entire lifecycle.

## Failure Policy
- **Isolation**: Failures in one package must not affect others.
- **Traceability**: All failures leave logs in the `logs/` directory.
- **Atomic**: Unsuccessful builds are partially retained for AI analysis (`--explain`).
