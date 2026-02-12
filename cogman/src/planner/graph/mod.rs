/*
 * cogman/src/planner/graph/mod.rs - Dependency Graph Engine
 *
 * This module manages the high-level dependency structures and 
 * graph theory abstractions for the build planner.
 *
 * Why: To provide a centralized interface for complex relational 
 * data processing during the planning phase.
 */

pub mod resolve;
pub mod topo;

pub use resolve::DepGraph;
