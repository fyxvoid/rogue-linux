// cogmanII planner — ai/noop.rs
// This module exists because cogmanII must run perfectly without AI.
// NoopAdvisor is the default backend: all methods return None,
// is_available() returns false. Zero cost, zero side effects.

use crate::ai::interface::AiAdvisor;

/// Default AI backend — does nothing.
/// Used when the "ai" feature is not compiled in, or when
/// no local LLM is available.
pub struct NoopAdvisor;

impl AiAdvisor for NoopAdvisor {
    fn explain_failure(&self, _: &str, _: &str, _: &str) -> Option<String> {
        None
    }

    fn suggest_dependencies(&self, _: &str, _: &str) -> Option<Vec<String>> {
        None
    }

    fn ask(&self, _: &str, _: &str) -> Option<String> {
        None
    }

    fn is_available(&self) -> bool {
        false
    }
}
