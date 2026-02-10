# Metadata Specification (v1.0)

This document defines the schema for `package.toml`.

## [identity]
Core package identification.
```toml
[identity]
name = "bash"           # Unique package name
version = "5.2"         # Upstream version
category = "base"       # Group (base, libs, extra)
summary = "GNU Bourne-Again SHell"
```

## [identity.source]
Source code retrieval.
```toml
[identity.source]
kind = "tarball"        # "tarball", "git", "local"
file = "bash-5.2.tar.gz" # File name in tar/ directory
url = "..."             # Optional upstream URL (informational)
sha256 = "..."          # Checksum (enforced)
```

## [identity.depends]
Dependency declaration.
```toml
[identity.depends]
build = ["libs/readline", "libs/ncurses"] # Build-time deps
runtime = []                             # Runtime deps (future use)
```

## [build]
Build instructions (Native mode).
```toml
[build]
system = "autotools"    # "make", "autotools", "cmake", "meson"
steps = [               # Custom steps override system defaults
    "./configure --prefix=/usr",
    "make -j$(nproc)",
    "make install DESTDIR=${d}"
]
```

## [installer]
Installation instructions (Binary/Package mode).
```toml
[installer]
steps = [
    # Commands to run inside pkgroot
    "install -Dm755 bash /bin/bash"
]
```

## [policy] (Optional)
Behavioral constraints.
```toml
[policy]
# Defaults to standard strictness if omitted.
[policy.filesystem]
read = ["/usr", "/bin"] # Allowed read paths
write = ["/tmp", "${d}"] # Allowed write paths
```
