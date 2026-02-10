# Temporary Directory Lifecycle

Cogman manages ephemeral directories for the build process.

## The Contract

1.  **Creation**:
    -   Planner generates a unique path schema: `/tmp/cogman-build-<pkg>`.
    -   Executor validates `mkdir` success.

2.  **Usage**:
    -   The `[build]` steps are executed inside this directory as `CWD`.
    -   Source tarballs are extracted here.

3.  **Destruction**:
    -   **Success**: The directory is automatically removed (`rm -rf`) after the package is installed to pkgroot.
    -   **Failure**: The directory is **preserved** to aid debugging.
    -   **Flags**:
        -   `--keep-tmp`: Forces preservation even on success.

## Safety
-   The executor uses strictly scoped `rm -rf` on the specific path it created.
-   It will never traverse up (`..`) or delete outside `/tmp/cogmanII-*`.

## Example
```bash
# Plan Step:
MKDIR /tmp/cogman-build-bash
CWD   /tmp/cogman-build-bash
EXEC  tar -xf bash.tar
EXEC  ./configure
...
RMDIR /tmp/cogman-build-bash
```
