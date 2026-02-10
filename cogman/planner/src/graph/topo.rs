// cogmanII planner — graph/topo.rs
// Topological sort implementation.
// from graph construction. If we ever change the sort strategy (e.g.
// parallel build groups), only this file changes.

use petgraph::algo::toposort;
use crate::graph::resolve::DepGraph;
use crate::error::PlannerError;

/// A resolved build order — packages listed dependency-first.
pub struct BuildOrder {
    pub order: Vec<String>,
}

/// Perform topological sort on the dependency graph.
/// Returns an error with the cycle participant if a cycle is detected.
pub fn resolve_order(graph: &DepGraph) -> Result<BuildOrder, PlannerError> {
    match toposort(&graph.graph, None) {
        Ok(sorted) => {
            let order = sorted
                .iter()
                .map(|idx| graph.graph[*idx].clone())
                .collect();
            Ok(BuildOrder { order })
        }
        Err(cycle) => {
            let node = &graph.graph[cycle.node_id()];
            Err(PlannerError::DependencyGraph(
                format!("dependency cycle detected involving: {}", node)
            ))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::graph::DepGraph;

    #[test]
    fn test_linear_deps() {
        let mut g = DepGraph::new();
        g.add_dep("bash", "readline");
        g.add_dep("readline", "ncurses");
        g.add_dep("ncurses", "gcc");

        let order = resolve_order(&g).unwrap();
        let pos = |name: &str| order.order.iter().position(|n| n == name).unwrap();
        assert!(pos("gcc") < pos("ncurses"));
        assert!(pos("ncurses") < pos("readline"));
        assert!(pos("readline") < pos("bash"));
    }

    #[test]
    fn test_cycle_detection() {
        let mut g = DepGraph::new();
        g.add_dep("a", "b");
        g.add_dep("b", "c");
        g.add_dep("c", "a");

        assert!(resolve_order(&g).is_err());
    }

    #[test]
    fn test_standalone_package() {
        let mut g = DepGraph::new();
        g.add_package("standalone");
        let order = resolve_order(&g).unwrap();
        assert_eq!(order.order.len(), 1);
        assert_eq!(order.order[0], "standalone");
    }
}
