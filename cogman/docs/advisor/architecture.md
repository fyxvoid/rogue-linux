# Advisor: Localized Intelligence

The Advisor is what makes Cogman a "Tactical Build System." It provides neural-augmented diagnostics to help pentesting distro developers fix build issues instantly.

## 🤖 Neural Architecture

The Advisor uses a **1B-2B parameter Language Model** optimized for specialized technical reasoning.

### Tech Stack
-   **Model**: Cogman-1B (Fine-tuned from Llama/Qwen architectures).
-   **Format**: GGUF (4-bit quantization).
-   **Inference**: `llama-cpp-python` backend managed by a Rust interface.
-   **Integration**: Communication via CLI arguments (`ai.py --query`) or IPC.

## 🔍 How it Works: The Diagnostic Loop

When a build fails in the Executor:
1.  **Context Capture**: The Executor captures the last 50 lines of STDOUT/STDERR and the failed command.
2.  **Prompt Construction**: The Advisor crate (`src/advisor`) builds a high-fidelity prompt:
    > "You are Cogman, the Tactical Butler. A build failed during the `configure` phase of `pentest/metasploit`. Error: `cannot find openssl/ssl.h`. Context: [Build Logs]. What is the tactical solution, sir?"
3.  **Localized Inference**: The GGUF model runs locally (GPU or CPU) to generate an answer.
4.  **Presentation**: The response is sanitized and presented in the HUD using the "Butler" persona.

## 🧪 Training & Fine-Tuning

We use **QLoRA** to specialize the model on Rogue Linux internals.
-   **Dataset**: 
    -   1,000+ Linux man pages.
    -   500+ build failure/fix pairs for common security tools (Nmap, Metasploit, Cracking tools).
    -   The official Rogue Linux architecture documents.
-   **Goal**: Ensure the AI understands the "Cogman Way" (BTM, RMAN, zero-latency) and can suggest fixes that align with our system philosophy.

## 🛡️ Safety & Reliability (The Air Gap)

The AI Advisor is strictly **Informational**:
-   **No System Access**: It cannot read files outside the build tree.
-   **No Execution**: It cannot modify `package.toml` or run `make`.
-   **Manual Implementation**: The human operator must always review and implement the suggested fix. This prevents AI hallucinations from compromising the system root.
