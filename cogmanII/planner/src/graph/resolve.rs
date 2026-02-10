// cogmanII planner — graph/resolve.rs
// This module exists because building a dependency graph is distinct
// from sorting it. This file handles adding packages and edges.
// It knows nothing about ordering — that's topo.rs's job.

use petgraph::graph::{DiGraph, NodeIndex};
use std::collections::HashMap;
use crate::error::PlannerError;

/// Dependency graph builder.
/// Nodes are package names, edges encode "A depends on B".
pub struct DepGraph {
    pub(crate) graph: DiGraph<String, ()>,
    pub(crate) nodes: HashMap<String, NodeIndex>,
}

impl DepGraph {
    pub fn new() -> Self {
        Self {
            graph: DiGraph::new(),
            nodes: HashMap::new(),
        }
    }

    /// Get or create a node for a package name.
    fn node(&mut self, name: &str) -> NodeIndex {
        if let Some(&idx) = self.nodes.get(name) {
            idx
        } else {
            let idx = self.graph.add_node(name.to_string());
            self.nodes.insert(name.to_string(), idx);
            idx
        }
    }

    /// Register a package (even if it has no dependencies).
    pub fn add_package(&mut self, pkg: &str) {
        self.node(pkg);
    }

    /// Add a dependency edge: `pkg` depends on `dep`.
    /// Edge direction: dep → pkg (dep must be built first).
    pub fn add_dep(&mut self, pkg: &str, dep: &str) {
        let pkg_idx = self.node(pkg);
        let dep_idx = self.node(dep);
        self.graph.add_edge(dep_idx, pkg_idx, ());
    }
}
