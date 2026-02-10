// cogmanII planner — ai/noop.rs
// Default zero-cost Advisor (Noop).
// NoopAdvisor is the default backend: all methods return None,
// is_available() returns false. Zero cost, zero side effects.

use crate::ai::interface::AiAdvisor;

/// Default AI backend — does nothing.
/// Used when the "ai" feature is not compiled in, or when
/// no local LLM is available.
pub struct NoopAdvisor;

use super::context::AiContext;

impl AiAdvisor for NoopAdvisor {
    fn explain_failure(&self, _ctx: &AiContext) -> Option<String> {
        None
    }

    fn is_available(&self) -> bool {
        false
    }
}
