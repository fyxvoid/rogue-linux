# Failure Model

Cogman implements a **Fail-Fast** philosophy.

## Default Policy: Abort
If *any* step in the execution plan returns a non-zero exit code:
1.  The executor immediately stops.
2.  No further steps are executed.
3.  The process exits with code `1`.
4.  The failure is logged to stderr with context (Step X/Y failed).

**Rationale**: A partial system is a broken system. Better to stop and fix than to proceed with corruption.

## Exception: Warn Policy (Future)
The binary plan format supports a `fail_policy` field per step.
-   `FailPolicy::Abort` (0): Default.
-   `FailPolicy::Warn` (1): Log warning, continue.

*Note: As of v1.0, the Planner generates only Abort steps.*

## Error Hierarchy
1.  **Metadata Error**: Invalid TOML, bad types, missing fields.
    -   *Result*: Planner exit (1). No plan generated.
2.  **Graph Error**: Cycle detected, missing dependency.
    -   *Result*: Planner exit (1).
3.  **System Error**: `fork` failed, `mmap` failed.
    -   *Result*: Executor exit (1).
4.  **Build Error**: `make` returned error.
    -   *Result*: Executor exit (1).
