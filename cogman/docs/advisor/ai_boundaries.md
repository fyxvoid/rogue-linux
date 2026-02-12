# AI Boundaries & Safety

To ensure system reliability, the AI Advisor operates under strict constraints.

- **Read-Only**: The AI has access to logs and metadata but cannot modify the filesystem.
- **Advisor-Only**: The AI *explains*, it does not *execute*. It cannot change build plans or run arbitrary commands.
- **Sanitized Output**: Responses are filtered to prevent malicious instruction or system-compromising advice.
- **Deterministic Override**: If the AI's advice conflicts with human-defined documentation or code, the deterministic system always wins.
