# Data Flow Specification

The build process is a pipeline of **Immutable Data Transformations**.

## 1. Source (TOML) -> Model (Rust)
The Planner reads a `package.toml` file.
- **Input**: Text (UTF-8).
- **Process**: serde (Toml) deserialization.
- **Output**: `PackageMetadata` struct (Rust Heap).
- **Validation**: Fields checked for type/presence.

## 2. Model -> Graph (Petgraph)
The Planner recursively loads dependencies.
- **Input**: `PackageMetadata` (Root) + File system.
- **Process**: DFS traversal using `RecursiveLoader`.
- **Output**: `DepGraph` (NodeIndex -> String).
- **Validation**: Cycle detection.

## 3. Graph -> Build Order (Vec)
The dependency graph is topologically sorted.
- **Input**: `DepGraph`.
- **Process**: Kahn's Algorithm (`petgraph::algo::toposort`).
- **Output**: `Vec<NodeIndex>` (Linear sequence).

## 4. Build Order -> Build Plan (Vec<Step>)
The Planner iterates the build order and generates steps for *each* package.
- **Input**: `Vec<PackageMetadata>` (cached).
- **Process**:
    - **Native Variant**: `mkdir`, `cd`, `configure`, `make`, `install`, `cp`.
    - **Binary Variant**: `mkdir`, `cp`.
- **Output**: `Vec<PlanStep>` (Internal Rust representation).

## 5. Build Plan -> Binary Plan (*.plan)
The Planner serializes steps into the `cogman-plan` binary format.
- **Input**: `Vec<PlanStep>`.
- **Process**:
    - Build String Table (deduplicated strings).
    - Write Header (`magic`, `version`, `count`).
    - Write `StepRecord` array (fixed size structs).
    - Write String Table blob.
- **Output**: `out.plan` (File / Stdout).

## 6. Binary Plan -> Execution (C)
The Executor loads the plan.
- **Input**: `out.plan`.
- **Process**: `mmap()` (Read-Only).
- **Validation**: Magic check, bounds check.
- **Effect**: Sequential execution of mapped instructions via `fork/exec`.
