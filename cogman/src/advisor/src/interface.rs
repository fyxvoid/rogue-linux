/*
 * cogman/src/advisor/src/interface.rs - AI Interaction Trait
 *
 * This file defines the core contract for all AI backends, 
 * ensuring that inference logic is strictly decoupled from the 
 * build planner's deterministic core.
 *
 * Why: To allow seamless swapping between local GGUF models and 
 * remote LLM endpoints without altering system logic.
 */
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

    /// General technical query to the assistant.
    fn ask(&self, query: &str) -> Option<String>;

    /// Whether this backend is actually connected and functional.
    fn is_available(&self) -> bool;
}
