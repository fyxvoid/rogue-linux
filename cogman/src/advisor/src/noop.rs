/*
 * cogman/src/advisor/src/noop.rs - Zero-Cost AI Advisor
 *
 * This file implements a hollow advisor backend that returns None 
 * for all queries and claims unavailability.
 *
 * Why: To provide a safe, zero-cost default when no AI model is 
 * present or compiled into the system.
 */

use crate::interface::AiAdvisor;

/// Default AI backend — does nothing.
/// Used when the "ai" feature is not compiled in, or when
/// no local LLM is available.
pub struct NoopAdvisor;

use super::context::AiContext;

impl AiAdvisor for NoopAdvisor {
    fn explain_failure(&self, _ctx: &AiContext) -> Option<String> { None }
    fn ask(&self, _query: &str) -> Option<String> { None }
    fn is_available(&self) -> bool { false }
}
