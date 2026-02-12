# Execution Lifecycle

The lifecycle follows a high-speed "Map and Execute" loop.

1. **Load**: The `.plan` file is mapped into memory via `mmap()`.
2. **Validate**: Header magic (`COG1`) and step counts are verified.
3. **Loop**: The executor iterates through the `Step` array.
4. **Fork/Exec**: Each step is executed in a child process with a sanitized environment.
5. **Monitor**: The parent waits for the child and checks the exit status.
6. **Cleanup**: Upon success, temporary build directories are removed.
