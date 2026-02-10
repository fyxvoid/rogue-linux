# Logging Philosophy

Cogman uses a distinct "Butler Personality" for its logging.
This is not just for flavor—it serves a functional purpose: **Distinctiveness**.

## The Persona
-   **Name**: Cogman (The Butler).
-   **Tone**: Polite, precise, subservient but firm.
-   **Markers**:
    -   Header: `▐ COGMAN ▌` (ANSI Blue/Bold).
    -   Suffix: `, sir.`

## Rationale
In a unified build log, output from `make`, `gcc`, `tar`, and kernel messages are mixed.
Cogman's logs must be instantly recognizable to the human eye as **System Messages** versus **Build Output**.

## Log Levels

1.  **Info (White)**: Progress markers.
    > "Resolving dependency graph, sir."
2.  **Success (Green)**: Validation passes, completion.
    > "Metadata validation passed. Quite satisfactory, sir."
3.  **Error (Red)**: Critical failures.
    > "Dependency cycle detected. Deeply unfortunate, sir."

## Rules
-   **No Debug by Default**: Normal execution is quiet except for phase transitions.
-   **Zero-Cost Debug**: Debug logging (`log_debug`) is compiled out in Release builds (Rust feature gate / C macro).
-   **Stderr Only**: All logs go to stderr. Stdout is reserved for the binary plan (if pipelined).
