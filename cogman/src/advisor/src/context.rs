/*
 * cogman/src/advisor/src/context.rs - AI Reasoning Context
 *
 * This file defines the data structures that provide the AI with 
 * a sanitized, high-fidelity view of the build failure state.
 *
 * Why: To ensure the Advisor has all necessary indicators (logs, 
 * metadata, environment) to produce accurate tactical advice.
 */
use crate::metadata::PackageMetadata;

// Safe, serializable view of the world for the AI.
// Only includes what is necessary for reasoning.
#[derive(Debug, Serialize)]
pub struct AiContext {
    pub package: PackageMetadata,
    pub step: Option<String>,
    pub error: Option<String>,
    pub env: Vec<String>,
    pub cwd: String,
}

impl AiContext {
    pub fn new(pkg: PackageMetadata) -> Self {
        Self {
            package: pkg,
            step: None,
            error: None,
            env: Vec::new(),
            cwd: String::new(),
        }
    }

    pub fn with_error(mut self, err: String) -> Self {
        self.error = Some(err);
        self
    }
}
