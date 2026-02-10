# Rogue Linux: Project History & Evolution

## The Genesis
Rogue Linux began as a quest to create a **pentesting distribution** that was not just a collection of tools, but a **precision instrument**. We rejected the bloat of traditional distros in favor of a **LFS (Linux From Scratch)** base, ensuring we knew every line of code running on the metal.

## Phase 1: The Core & Cogman
Instead of relying on `apt` or `pacman`, we built **Cogman** (Cognitive Manager).
- **Philosophy**: "A digital butler for the elite hacker."
- **Stack**: Python-based build system using `package.toml` manifests.
- **Key Decision**: We chose **Python** over Bash for manageability and future AI integration potential.

## Phase 2: The Website & Identity
We needed a face for the project.
- **Aesthetic**: We moved from a generic dark theme to a **Cyberpunk/Holographic** identity.
    - **Blue (#00f3ff)**: Core system functions.
    - **Red (#ff003c)**: "Rogue" branding and critical actions.
- **Architecture**: We rejected heavy frameworks (React/Vue) for a **Static Site Generator (SSG)** written in Python.
    - **Why?**: To keep the tech stack consistent with Cogman and ensure maximum performance (76KB total payload).
    - **Evolution**: We started with full HTML pages but refactored to a **Fragment-based architecture** where `build_site.py` injects content into a global layout, mimicking a modern SPA without the JS bloat.

## Phase 3: Production Hardening
As the user base verified our direction (targeting 2M+ users), we hardened the infrastructure.
- **Modular Refactor**: Transitioned from a monolithic Rust planner to a workspace-based architecture (`planner`, `advisor`).
- **Binary Plan Link**: Solidified the `.plan` interface between the Rust Planner and C Executor.
- **Gated AI**: Integrated the `Qwen2.5-3B-Instruct` advisor with feature-flag support for zero-host-dependency builds.
- **SSG Finalization**: Completed the fragment-based website engine for 2M user scalability.

## Current State
We now have a fully modular, static-first website and a robust package manager, all adhering to a strict performance and aesthetic code.
