# AI Boundaries

Cogman was built with AI assistance, but operates under strict "Human-Defined" rules.

## The Rules

1.  **Architecture is Human**: The module boundaries, failure models, and core philosophy were defined by the Architect, not the AI.
2.  **Code is Verify-First**: AI-generated code is treated as "untrusted input" until verified by compilation and tests.
3.  **No "Hallucinated" Features**: We do not add features just because the AI suggested them. (e.g., "AI optimization of build flags" is out of scope).
4.  **Documentation is Contract**: This documentation overrides any AI inference. If the docs say X and the code does Y, the code is wrong.

## Usage in Development
-   **Review**: Human reviews every diff.
-   **Refactor**: AI is used to strictly refactor existing logic (e.g., "move this struct to a new file").
-   **Tests**: AI generates test cases based on the schema specs.
