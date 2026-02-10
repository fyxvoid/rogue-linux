use serde::Serialize;
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
