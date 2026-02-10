# PRE-ROOTFS CONSOLIDATION CHECKLIST

This document certifies that the **Cogman Build System** is ready for the Rootfs Construction Phase.

## 1. Documentation (Authoritative)
- [x] `docs/README.md` (Index)
- [x] `docs/ARCHITECTURE.md` (System Design)
- [x] `docs/METADATA.md` (Schema v1.0)
- [x] `docs/DATA-FLOW.md` (Pipeline)
- [x] `docs/FAILURE-MODEL.md` (Reliability)

## 2. Legacy Retirement
- [x] `archived/cogman-python/` exists and contains old code.
- [x] `cogman/` contains ONLY the new Rust/C implementation.
- [x] No active scripts reference `cogman.py`.

## 3. Renaming (Rebranding)
- [x] Directory: `cogmanII/` -> `cogman/`.
- [x] Binary: `cogman-planner` (v1.0.0).
- [x] Binary: `cogman-exec`.
- [x] Doc references updated to `cogman`.

## 4. Code Hygiene
- [x] `make` builds without error.
- [x] `make test` runs validation suite (11/11 pass).
- [x] `target/` dirs are ignored/cleaned.
- [x] No "cogmanII" artifacts in active source comments.

## 5. Benchmarks
- [x] `benchmarks/` directory consolidated.
- [x] `benchmark.py` updated and moved.
- [x] Results archived.

## 6. System Contract
- [x] **Native Mode**: Builds from source (`--native`).
- [x] **Binary Mode**: Installs from archive (default).
- [x] **Isolation**: `/tmp` usage is strictly scoped.
- [x] **Output**: Writes ONLY to `pkgroot`.

> **Status**: READY FOR ROOTFS
> **Date**: 2026-02-10
