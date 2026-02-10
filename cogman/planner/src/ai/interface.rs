// cogmanII planner — ai/interface.rs
// LLM trait definition.
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

use super::context::AiContext;

/// Trait for AI advisory backends.
/// Implementations receive error context and return human-readable advice.
pub trait AiAdvisor {
    /// Explain a build failure given the error output and metadata context.
    fn explain_failure(&self, ctx: &AiContext) -> Option<String>;

    /// Whether this backend is actually connected and functional.
    fn is_available(&self) -> bool;
}
