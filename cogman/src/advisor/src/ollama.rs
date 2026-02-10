use crate::interface::AiAdvisor;
use crate::context::AiContext;
use crate::prompt::build_prompt;
use crate::guards::{sanitize_response, validate_safety};
use serde_json::json;

pub struct OllamaAdvisor {
    model: String,
    endpoint: String,
}

impl OllamaAdvisor {
    pub fn try_connect() -> Option<Self> {
        let advisor = Self {
            model: "mistral".to_string(), // Default, can be config'd later
            endpoint: "http://localhost:11434/api/generate".to_string(),
        };
        if advisor.is_available() {
            Some(advisor)
        } else {
            None
        }
    }
}

impl AiAdvisor for OllamaAdvisor {
    fn explain_failure(&self, ctx: &AiContext) -> Option<String> {
        let prompt = build_prompt(ctx);
        
        let client = reqwest::blocking::Client::new();
        let res = client.post(&self.endpoint)
            .json(&json!({
                "model": self.model,
                "prompt": prompt,
                "stream": false
            }))
            .send();

        match res {
            Ok(resp) => {
                if let Ok(json) = resp.json::<serde_json::Value>() {
                    if let Some(text) = json["response"].as_str() {
                        let sane = sanitize_response(text);
                        if validate_safety(&sane) {
                            return Some(sane);
                        }
                    }
                }
            }
            Err(_) => {
                // Connection failed. Fail silently.
            }
        }
        None
    }
    
    fn is_available(&self) -> bool {
        let client = reqwest::blocking::Client::new();
        // Check API health
        client.get("http://localhost:11434/").send().is_ok()
    }
}
