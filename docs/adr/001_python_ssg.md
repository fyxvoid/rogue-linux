# ADR 001: Python-based Static Site Generation

## Context
Rogue Linux needs a website to distribute packages and documentation. The project is heavily reliant on Python (Cogman build system). We needed a way to build the website that was:
1.  **Lightweight**: No heavy Nodejs/npm dependencies if possible.
2.  **Integrated**: Able to parse `package.toml` and other build artifacts directly.
3.  **Maintainable**: Understandable by the same engineers working on the OS.

## Decision
We decided to write a custom **Static Site Generator (SSG)** in Python (`website/tools/build_site.py`).

## Consequences
### Positive
-   **Zero external dependencies**: Runs with standard Python libraries.
-   **Tight Integration**: Can import `cogman_utils` to log in the "Butler" persona.
-   **Performance**: Generates pure HTML/CSS with no client-side JS framework overhead.

### Negative
-   **Maintenance**: We own the build logic; no plugins ecosystem like Jekyll/Hugo.
-   **Features**: We have to implement features like "partials" manually.

## Status
ACCEPTED
