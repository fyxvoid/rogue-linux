use crate::interface::AiAdvisor;
use crate::context::AiContext;
use crate::prompt::build_prompt;
/*
 * cogman/src/advisor/src/local_inference.rs - GGUF Inference Backend
 *
 * This file implements the localized AI advisor backend, calling 
 * the Python-based neural engine to get tactical diagnostics.
 *
 * Why: To provide a secure, offline alternative to remote LLM 
 * services in sensitive environments.
 */

pub struct LocalAdvisor {
    python_script: String,
    model_path: String,
}

impl LocalAdvisor {
    pub fn new(script: &str, model: &str) -> Self {
        Self {
            python_script: script.to_string(),
            model_path: model.to_string(),
        }
    }
}

impl AiAdvisor for LocalAdvisor {
    fn explain_failure(&self, ctx: &AiContext) -> Option<String> {
        let prompt = build_prompt(ctx);
        
        let output = Command::new("python3")
            .arg(&self.python_script)
            .arg("--query")
            .arg(prompt)
            .output();

        match output {
            Ok(out) => {
                if out.status.success() {
                    let text = String::from_utf8_lossy(&out.stdout).trim().to_string();
                    if !text.is_empty() {
                        return Some(text);
                    }
                }
            }
            Err(_) => {}
        }
        None
    }

    fn ask(&self, query: &str) -> Option<String> {
        let output = Command::new("python3")
            .arg(&self.python_script)
            .arg("--query")
            .arg(query)
            .output();

        match output {
            Ok(out) => {
                if out.status.success() {
                    let text = String::from_utf8_lossy(&out.stdout).trim().to_string();
                    if !text.is_empty() {
                        return Some(text);
                    }
                }
            }
            Err(_) => {}
        }
        None
    }

    fn is_available(&self) -> bool {
        std::path::Path::new(&self.model_path).exists()
    }
}
