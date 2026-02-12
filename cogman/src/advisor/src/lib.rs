/*
 * cogman/src/advisor/src/lib.rs - AI Advisor Infrastructure
 *
 * This module serves as the primary gateway for Cogman's localized 
 * intelligence features, providing traits and backends for 
 * tactical build diagnostics.
 *
 * Why: To enable AI-augmented troubleshooting that aligns with 
 * the Rogue Linux system persona.
 */
pub mod guards;
pub mod interface;
pub mod ollama;
pub mod local_inference;
pub mod noop;
pub mod prompt;
pub mod metadata;

pub use interface::AiAdvisor;

/// Factory to create the best available advisor.
/// Priority: Ollama > Local GGUF > Noop.
pub fn create_advisor() -> Box<dyn AiAdvisor> {
    if let Some(ollama) = ollama::OllamaAdvisor::try_connect() {
        return Box::new(ollama);
    }

    // Paths are now relative to the advisor directory
    let base_dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR"));
    let script = base_dir.join("ai.py").to_string_lossy().to_string();
    let model = base_dir.join("models/cogman-1b.gguf").to_string_lossy().to_string();

    let local = local_inference::LocalAdvisor::new(&script, &model);
    if local.is_available() {
        return Box::new(local);
    }

    Box::new(noop::NoopAdvisor)
}
