# Metadata Specification (v1.0)

Cogman uses `package.toml` for standardized metadata declaration.

## [identity]
- `name`: Unique package identifier.
- `version`: Upstream version string.
- `category`: System group (base, libs, etc.).

## [identity.depends]
- `build`: Build-time dependency list.
- `runtime`: Runtime dependency list.

## [build]
- `system`: Build system type (autotools, cmake, make).
- `steps`: Custom shell commands for the build lifecycle.

## [policy]
- `filesystem`: Read/Write path constraints for the executor sandbox.
