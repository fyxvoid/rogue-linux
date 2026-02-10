// cogmanII planner — graph/mod.rs
// Graph data structure and algorithms.
// It is split into two concerns:
// - resolve.rs: building the graph (adding nodes and edges)
// - topo.rs: extracting a valid build order (topological sort)

pub mod resolve;
pub mod topo;

pub use resolve::DepGraph;
