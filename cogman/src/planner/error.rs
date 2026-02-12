/*
 * cogman/src/planner/error.rs - Planner Error Definitions
 *
 * This file defines the custom error types used throughout the 
 * Cogman Planner, enabling precise failure diagnostics.
 *
 * Why: To provide detailed, actionable feedback to the operator 
 * when the planning pipeline encounters an invalid state.
 */

use std::fmt;

#[allow(dead_code)]
/// Unified error type for the planner.
/// Every module returns this — no stringly-typed errors leak out.
#[derive(Debug)]
pub enum PlannerError {
    /// TOML file could not be read or parsed.
    MetadataLoad(String),
    /// Metadata parsed but failed semantic validation.
    Validation(Vec<String>),
    /// Dependency cycle or unresolvable graph.
    DependencyGraph(String),
    /// Plan could not be written to output.
    PlanEmit(String),
    /// CLI flag conflict or missing argument.
    Cli(String),
}

impl fmt::Display for PlannerError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::MetadataLoad(e) => write!(f, "metadata: {}", e),
            Self::Validation(errs) => {
                for e in errs {
                    writeln!(f, "  - {}", e)?;
                }
                Ok(())
            }
            Self::DependencyGraph(e) => write!(f, "dependency: {}", e),
            Self::PlanEmit(e) => write!(f, "plan: {}", e),
            Self::Cli(e) => write!(f, "cli: {}", e),
        }
    }
}
