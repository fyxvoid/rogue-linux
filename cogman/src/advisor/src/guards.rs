// Output sanitization and safety checks.
// The AI output is untrusted text.

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
