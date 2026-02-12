# Planner: The Cognitive Engine

The Planner (`cogman-planner`) is responsible for the complex "thinking" phase of the system. It is written in **Rust** to provide memory safety and high-level abstractions for graph-based logic.

## 🧠 How it Works

The Planner operates in a linear pipeline:

1.  **Metadata Ingestion**: Parses `package.toml` utilizing `serde`. It validates schema v1.0, ensuring all mandatory fields (identity, source, build) are present.
2.  **Dependency Graph Construction**:
    -   Uses a Directed Acyclic Graph (DAG) implemented via `petgraph`.
    -   **Recursive Loading**: When a package is loaded, the planner recursively searches the local repository for its dependencies, adding nodes to the graph.
    -   **Cycle Detection**: If a circular dependency is found (A -> B -> A), the planner aborts immediately to prevent infinite build loops.
3.  **Topological Sort**: Implements Kahn's algorithm to determine a valid linear sequence of builds where every dependency is satisfied before its parent starts.
4.  **Binary Plan Compilation**: 
    -   Translates high-level metadata into a list of specific `OP_CODE` instructions (e.g., `OP_MKDIR`, `OP_EXEC`, `OP_CHDIR`).
    -   **String Table Deduping**: All strings (paths, commands, environments) are stored in a deduplicated table at the end of the file. Instructions reference these via 32-bit offsets.
    -   **Zero-Parsing Layout**: The resulting `.plan` file is a direct binary representation of C structs, making it "ready to mmap" for the Executor.

## 🛠️ Developer Guide: Extending the Planner

To add a new operation (e.g., `OP_STRIP_ARCHIVE`):
1.  Define the operation in the `cogman-common` shared header (C and Rust).
2.  Add a generator function in `planner/src/plan/generator.rs`.
3.  Ensure the `cogman-exec` has a corresponding handler in its switch-case execution loop.

## 📊 Logic Performance
- **Graph Resolution**: O(V + E) where V is package count and E is dependency count.
- **Serialization**: O(S) where S is the total size of command strings.
- **Safety**: 100% memory safe (no `unsafe` block in the core planner module).
