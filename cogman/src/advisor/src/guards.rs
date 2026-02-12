/*
 * cogman/src/advisor/src/guards.rs - Information Sanitization & Guards
 *
 * This file implements safety filters and output validation for AI 
 * responses, preventing hallucinations from affecting the system.
 *
 * Why: To maintain the integrity of the "Tactical Butler" persona 
 * and protect the operator from malformed shell advice.
 */

pub fn sanitize_response(input: &str) -> String {
    // 1. Trim whitespace
    let trimmed = input.trim();
    
    // 2. Remove markdown code blocks if the user didn't ask for them?
    // Actually we keep them, but we might want to ensure no "EXECUTE:" commands etc.
    // For now, simple pass-through with length limit.
    
    if trimmed.len() > 2000 {
        return trimmed[..2000].to_string() + "... (truncated)";
    }
    
    trimmed.to_string()
}

pub fn validate_safety(input: &str) -> bool {
    // Reject if it tries to pretend to be system
    if input.contains("SYSTEM:") || input.contains("ROLE:") {
        return false;
    }
    true
}
