// cogmanII planner — ai/ollama.rs
// This module exists to provide an optional local LLM backend
// via Ollama's HTTP API. It is feature-gated behind "ai" and
// only compiled when explicitly requested.
//
// Target models: 1–2B parameter (e.g. qwen2.5-coder:1.5b)
// GPU training/fine-tuning happens on another machine (RTX 3050)
// This adapter only does inference via HTTP to localhost.
//
// Not in the hot path: only called on failure or explicit request.

use crate::ai::interface::AiAdvisor;

const OLLAMA_URL: &str = "http://localhost:11434/api/generate";
const DEFAULT_MODEL: &str = "qwen2.5-coder:1.5b";

pub struct OllamaAdvisor {
    url: String,
    model: String,
}

impl OllamaAdvisor {
    /// Try to connect to a local Ollama instance.
    /// Returns None if Ollama is not reachable (graceful degradation).
    pub fn try_connect() -> Option<Self> {
        // Attempt a lightweight health check — if Ollama is not running,
        // fall back to NoopAdvisor without error.
        // Uses a simple TCP connect check to avoid pulling in reqwest.
        let addr = "127.0.0.1:11434";
        match std::net::TcpStream::connect_timeout(
            &addr.parse().ok()?,
            std::time::Duration::from_millis(500),
        ) {
            Ok(_) => Some(Self {
                url: OLLAMA_URL.to_string(),
                model: std::env::var("COGMAN_AI_MODEL")
                    .unwrap_or_else(|_| DEFAULT_MODEL.to_string()),
            }),
            Err(_) => None,
        }
    }

    /// Send a prompt to Ollama and return the response text.
    /// This is a blocking call — only used outside the hot path.
    fn query(&self, prompt: &str) -> Option<String> {
        // Minimal HTTP POST using std::net only (no external deps).
        // Real implementation would use ureq or reqwest, but we
        // avoid adding dependencies to keep cogmanII lightweight.
        // This is a design placeholder — the interface is stable,
        // the transport can be swapped.
        let _ = prompt;
        let _ = &self.url;
        let _ = &self.model;
        // TODO: implement HTTP POST when Ollama integration is tested
        None
    }
}

impl AiAdvisor for OllamaAdvisor {
    fn explain_failure(
        &self,
        error_output: &str,
        package_name: &str,
        build_system: &str,
    ) -> Option<String> {
        let prompt = format!(
            "You are a Linux build system expert. Explain this build failure \
             for package '{}' using build system '{}'. Be concise.\n\n\
             Error output:\n{}",
            package_name, build_system, error_output
        );
        self.query(&prompt)
    }

    fn suggest_dependencies(
        &self,
        error_output: &str,
        package_name: &str,
    ) -> Option<Vec<String>> {
        let prompt = format!(
            "List missing dependencies for package '{}' based on this error. \
             Return ONLY package names, one per line.\n\n{}",
            package_name, error_output
        );
        self.query(&prompt).map(|resp| {
            resp.lines()
                .map(|l| l.trim().to_string())
                .filter(|l| !l.is_empty())
                .collect()
        })
    }

    fn ask(&self, question: &str, context: &str) -> Option<String> {
        let prompt = format!(
            "Context (cogmanII build system):\n{}\n\nQuestion: {}",
            context, question
        );
        self.query(&prompt)
    }

    fn is_available(&self) -> bool {
        true
    }
}
