/*
 * cogman/src/advisor/src/prompt.rs - Tactical Prompt Builder
 *
 * This file implements the prompt engineering logic for Cogman, 
 * injecting build context and "The Butler" persona into AI queries.
 *
 * Why: To ensure that the AI responds as a tactical advisor rather 
 * than a generic chatbot.
 */

// Constructs the prompt for the LLM.
// Enforces the "Advisory Only" role.
pub fn build_prompt(ctx: &AiContext) -> String {
    let json_ctx = serde_json::to_string_pretty(ctx).unwrap_or_default();
    
    format!(r#"
SYSTEM: You are an expert Linux build system engineer.
ROLE: Advisor. You explain failures and suggest fixes.
CONSTRAINT: You cannot execute commands. You cannot write files.
OUTPUT: Plain text explanation. Short. Technical.

CONTEXT:
{}

TASK:
Analyze the build failure or context above.
1. Explain WHAT happened.
2. Explain WHY it happened.
3. Suggest 1-2 concrete fixes (e.g. "Add 'make' to makedepends").
"#, json_ctx)
}
