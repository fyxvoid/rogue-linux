#![allow(dead_code)]
// cogmanII planner — ai/mod.rs
// This module exists because cogmanII can optionally use a local LLM
// for ADVISORY tasks (explaining failures, suggesting fixes).
//
// The AI backend is:
// - Feature-flagged at compile time (no cost when disabled)
// - NEVER invoked during plan generation or execution
// - ONLY invoked on failure or explicit user request
// - Text-only output (no code execution)
//
// The default backend is NoopAdvisor which does nothing.
// An Ollama adapter is available behind the "ai" feature flag.

pub mod interface;
pub mod noop;

#[cfg(feature = "ai")]
pub mod ollama;

use interface::AiAdvisor;
use noop::NoopAdvisor;

/// Create the appropriate AI advisor based on compile-time features.
/// When the "ai" feature is disabled, this always returns NoopAdvisor.
/// When enabled, it attempts to connect to a local Ollama instance.
pub fn create_advisor() -> Box<dyn AiAdvisor> {
    #[cfg(feature = "ai")]
    {
        match ollama::OllamaAdvisor::try_connect() {
            Some(advisor) => Box::new(advisor),
            None => Box::new(NoopAdvisor),
        }
    }

    #[cfg(not(feature = "ai"))]
    {
        Box::new(NoopAdvisor)
    }
}
