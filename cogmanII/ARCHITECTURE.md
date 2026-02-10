# CogmanII Architecture Contract (v1.0)

> "Determinism over convenience. Explicit over implicit. Speed over features."

## 1. Identity & Boundaries

### 1.1 What It Is
**cogmanII** is a deterministic, low-level build orchestrator for the Rogue Linux rootfs.
- It maps TOML metadata to a linear sequence of syscalls (Plan).
- It executes that sequence with zero deviation.

### 1.2 What It Is Not
- **NOT a Package Manager**: No runtime dependency resolution. No remote repository fetching.
- **NOT a Build System**: It assumes `make`, `cmake`, etc., exist. It just invokes them.
- **NOT a Shell**: It executes commands, but maintains no shell session state between steps.

### 1.3 Forbidden Responsibilities (The "Never" List)
1.   **Network Access during Execution**: The Executor MUST NOT access the network. (Source fetching happens in Planning or outside).
2.  **Root Privileges (mostly)**: The Executor should run as an unprivileged user where possible, operating only on `$PKGROOT`.
3.  **Interactive Prompts**: Execution is headless. Any prompt causes failure.
4.  **State Persistence**: Results of one step (env vars, CWD) DO NOT persist to the next.

## 2. Metadata Contract (Schema v1.0)

All packages must define a `package.toml` conforming to this strict schema.

```toml
[identity]
name = "string"
version = "string"
category = "string" # e.g., "base", "libs"
summary = "string"

[identity.source]
kind = "tarball" | "git"
file = "filename"

[identity.depends]
build = ["list", "of", "deps"]
runtime = ["list", "of", "deps"]

[build]
system = "autotools" | "make" | "cmake" # (informational)
steps = [
    "command 1",
    "command 2"
]

[installer]
steps = [
    "command 1"
]

[installer.verify]
paths = ["/usr/bin/foo"]
checksum = "sha256..." # Optional

[policy]
# Capabilities and filesystem constraints
```

### 2.1 Guarantees
- **Unknown Fields**: Ignored (forward compatibility).
- **Format**: All strings are UTF-8. Multiline strings allowed.

## 3. Determinism & Execution Model

### 3.1 The "Stateless Step" Rule
Each step in `steps` is executed in a **fresh process context**.
- **CWD**: Resets to build root (or specific `wdir`) every step.
- **Environment**: Resets to base environment every step. `export FOO=bar` in Step 1 DOES NOT affect Step 2.
- **Consequence**: Multi-command logic (configure -> make) must be **chained** (`cd dir && ./configure && make`) or put in a script. This enforces explicit dependencies.

### 3.2 Environment Isolation
- `PATH` is restricted.
- `LC_ALL=C` is enforced.
- Host environment leakage is minimized.

## 4. Failure Philosophy

- **Abort on Error**: If a step returns `exit_code != 0`, execution **STOPS IMMEDIATELY**.
- **No Retries**: Flakiness is a bug. Fix the bug, don't retry.
- **Cleanup**: On failure, `cogmanII` attempts to remove `$PKGROOT` artifacts to prevent partial installs, unless `--keep-failed` is passed.

## 5. Logging & Observability

- **Levels**:
    - `ERROR`: Fatal issues (Executor exit).
    - `WARN`: Non-fatal issues (if policy allows).
    - `INFO`: Step progress (e.g., "Step 1/10").
    - `DEBUG`: Tracing (Compiled out by default for speed).
- **Format**: ANSI-colored, structured text.

## 6. System Interfaces

### 6.1 Input (Planner)
- **Profile**: A TOML list of packages to install.
- **Metadata**: The database of package definitions.

### 6.2 Output (Executor)
- **$PKGROOT**: A directory containing the file tree of the installed package (e.g., `/tmp/pkgroot/bash/usr/bin/bash`).
- **Plan File**: A binary `.plan` file (intermediate artifact).

### 6.3 Rootfs Contract
1.  `cogmanII` populates `$PKGROOT`.
2.  Rootfs builder (external tool) merges `$PKGROOT` into the target image.
3.  `cogmanII` **NEVER** writes directly to `/` (host system) or target image file.

## 7. AI Boundaries
- **Advisory Only**: AI modules (if enabled) can analyze logs to explain failure.
- **Read-Only**: AI cannot modify the plan, code, or filesystem.
- **Optional**: The system must build and run correctly without AI features.
