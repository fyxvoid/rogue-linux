// cogmanII planner — ai/interface.rs
// This module exists because the AI backend must be swappable
// without touching planner core logic. The trait defines the
// contract: all backends must implement these methods, and all
// inputs/outputs are text-only.
//
// AI must NEVER:
//   - Decide execution steps
//   - Modify plans
//   - Run during executor phase
//
// AI MAY:
//   - Explain build failures
//   - Suggest missing dependencies
//   - Generate config hints
//   - Answer "why did this fail?"

/// Trait for AI advisory backends.
/// Implementations receive error context and return human-readable advice.
pub trait AiAdvisor {
    /// Explain a build failure given the error output and metadata context.
    fn explain_failure(
        &self,
        error_output: &str,
        package_name: &str,
        build_system: &str,
    ) -> Option<String>;

    /// Suggest possible missing dependencies based on error messages.
    fn suggest_dependencies(
        &self,
        error_output: &str,
        package_name: &str,
    ) -> Option<Vec<String>>;

    /// Free-form question about a build issue.
    fn ask(&self, question: &str, context: &str) -> Option<String>;

    /// Whether this backend is actually connected and functional.
    fn is_available(&self) -> bool;
}
