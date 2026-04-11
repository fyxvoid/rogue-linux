# Package Format Reference

Packages are defined by TOML files (`<name>.toml`). The planner reads these to build a dependency graph, validate steps, and emit a binary build plan.

---

## Minimal Example

```toml
[identity]
name    = "hello"
version = "1.0.0"
category = "base"

[build]
system = "make"
steps  = ["tar -xf tar/hello-1.0.tar.gz", "make -C hello-1.0"]

[installer]
steps = ["make -C hello-1.0 install PREFIX=$PKGROOT"]
verify = ["usr/bin/hello"]
```

---

## Sections

### `[identity]`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Package name (lowercase, hyphens allowed) |
| `version` | string | yes | Version string |
| `category` | string | yes | Logical group: `base`, `toolchain`, `net`, etc. |
| `description` | string | no | One-line human description |

#### `[identity.source]`

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Upstream download URL |
| `sha256` | string | Hex-encoded SHA-256 of the tarball |
| `filename` | string | Local filename in `tar/` directory |

#### `[identity.depends]`

```toml
[identity.depends]
build   = ["toolchain/linux-headers"]   # needed at build time
runtime = ["base/busybox"]              # needed at runtime on the target
```

Dependencies are specified as `"category/name"` strings. The planner resolves these into a topological order.

---

### `[build]`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `system` | string | yes | Build system hint: `make`, `cmake`, `autoconf`, `meson`, `custom` |
| `steps` | string[] | yes | Shell commands to run in order |

Steps are run with `sh -c` inside the build staging directory. The following environment variables are available:

| Variable | Value |
|----------|-------|
| `$PKGROOT` | Staging install root for this package |
| `$SRCDIR` | Directory where build is run |
| `$(nproc)` | Number of available CPU cores |

**Example — busybox static build:**
```toml
[build]
system = "make"
steps = [
    "tar -xf tar/busybox-1.36.1.tar.bz2",
    "make -C busybox-1.36.1 defconfig",
    "sed -i '/^# CONFIG_STATIC is not set/d' busybox-1.36.1/.config",
    "echo CONFIG_STATIC=y >> busybox-1.36.1/.config",
    "make -C busybox-1.36.1 oldconfig < /dev/null",
    "make -C busybox-1.36.1 -j$(nproc) V=0",
]
```

---

### `[installer]`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `steps` | string[] | yes | Installation commands (must not be empty) |
| `verify` | string[] | no | Paths relative to `$PKGROOT` that must exist after install |

The executor checks every path in `verify` after running `steps`. If any is missing, the install is marked failed.

**Example:**
```toml
[installer]
steps = [
    "make -C busybox-1.36.1 CONFIG_PREFIX=$PKGROOT install",
    "mkdir -p $PKGROOT/sbin",
    "test -f $PKGROOT/sbin/init || ln -sf ../bin/busybox $PKGROOT/sbin/init",
]
verify = ["bin/busybox", "sbin/init"]
```

---

### `[policy]`

Optional. Declares filesystem access policy enforced by the executor and (on Linux ≥ 5.13) by Landlock at runtime.

```toml
[policy.filesystem]
read  = ["/", "/usr"]          # paths that build steps may read
write = ["/tmp", "$PKGROOT"]   # paths that build steps may write
```

If omitted, the executor applies no Landlock restrictions (build has full filesystem access within the staging environment).

---

## Complete Example — linux-headers

```toml
[identity]
name     = "linux-headers"
version  = "6.6.75"
category = "toolchain"
description = "Linux kernel headers for userspace compilation"

[identity.source]
url      = "https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.6.75.tar.xz"
sha256   = "..."
filename = "linux-6.6.75.tar.xz"

[identity.depends]
build = []

[build]
system = "make"
steps  = ["tar -xf tar/linux-6.6.75.tar.xz"]

[installer]
steps = [
    "make -C linux-6.6.75 headers_install INSTALL_HDR_PATH=$PKGROOT/usr ARCH=x86_64",
    "find $PKGROOT/usr/include -name '*.install*' -delete",
]
verify = ["usr/include/linux/types.h", "usr/include/asm/types.h"]

[policy.filesystem]
read  = ["/"]
write = ["/"]
```

---

## Complete Example — base-files

```toml
[identity]
name     = "base-files"
version  = "1.0"
category = "base"
description = "Minimal /etc configuration files"

[identity.depends]
build = ["base/busybox"]

[build]
system = "custom"
steps  = ["tar -xzf tar/base-files-1.0.tar.gz -C $PKGROOT"]

[installer]
steps = [
    "mkdir -p $PKGROOT/{proc,sys,dev,tmp,run,var/log,var/run}",
]
verify = [
    "etc/inittab",
    "etc/passwd",
    "etc/hostname",
]

[policy.filesystem]
read  = ["/"]
write = ["$PKGROOT"]
```

---

## Naming Conventions

- File must be at `packages/<category>/<name>/<name>.toml`
- Source tarballs must be in `packages/<category>/<name>/tar/`
- The `category/name` identifier (used in `depends`) must match the directory path

---

## Validation Rules (enforced by planner)

1. `name`, `version`, `category` must be non-empty
2. `build.steps` must be non-empty
3. `installer.steps` must be non-empty
4. `identity.depends` entries must be resolvable (all referenced packages must exist)
5. No circular dependencies (planner performs cycle detection)
6. `installer.verify` paths must be relative (no leading `/`)
