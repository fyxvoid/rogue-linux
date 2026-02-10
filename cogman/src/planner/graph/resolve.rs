// cogman planner — graph/resolve.rs
// Graph-based dependency resolution logic.
// from sorting it. This file handles adding packages and edges.
// It knows nothing about ordering — that's topo.rs's job.

use petgraph::graph::{DiGraph, NodeIndex};
use std::collections::HashMap;
use crate::error::PlannerError;
use std::path::PathBuf;
use std::collections::HashSet;
use crate::metadata;

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

pub struct RecursiveLoader {
    dir: PathBuf,
    pub graph: DepGraph,
    pub metadata: HashMap<String, metadata::PackageMetadata>,
    visited: HashSet<String>,
}

impl RecursiveLoader {
    pub fn new(metadata_dir: PathBuf) -> Self {
        Self {
            dir: metadata_dir,
            graph: DepGraph::new(),
            metadata: HashMap::new(),
            visited: HashSet::new(),
        }
    }

    pub fn inject_root(&mut self, meta: &metadata::PackageMetadata) -> Result<(), PlannerError> {
        let name = format!("{}/{}", meta.identity.category, meta.identity.name);
        if self.visited.contains(&name) { return Ok(()); }
        
        self.metadata.insert(name.clone(), meta.clone());
        self.visited.insert(name.clone());
        self.graph.add_package(&name);
        
        for dep in &meta.identity.depends.build {
            self.graph.add_dep(&name, dep);
            self.load(dep)?;
        }
        Ok(())
    }

    fn load(&mut self, pkg_name: &str) -> Result<(), PlannerError> {
        if self.visited.contains(pkg_name) {
            return Ok(());
        }
        self.visited.insert(pkg_name.to_string());
        self.graph.add_package(pkg_name);

        // Path construction: dir/<category>/<name>/<name>.toml
        let parts: Vec<&str> = pkg_name.split('/').collect();
        if parts.len() != 2 {
            return Err(PlannerError::MetadataLoad(format!(
                "Invalid package ID '{}': must be group/name", pkg_name
            )));
        }
        let (group, name) = (parts[0], parts[1]);
        let path = self.dir.join(group).join(name).join(format!("{}.toml", name));

        let meta = metadata::load_metadata(&path)?;
        
        self.metadata.insert(pkg_name.to_string(), meta.clone());
        
        for dep in &meta.identity.depends.build {
            self.graph.add_dep(pkg_name, dep);
            self.load(dep)?;
        }
        Ok(())
    }
}
