"""
cogman/src/advisor/ai.py - Localized Neural Inference Engine

This file implements the high-performance inference wrapper for 
Cogman-1B/2B models using llama-cpp, providing real-time build 
diagnostics to the terminal.

Why: To provide senior-level system expertise in air-gapped or 
disconnected environments.
"""
import os
import sys
import argparse

# Try to import llama_cpp, handle if missing
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

# Default path for the 1B/2B Cogman model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL = os.path.join(BASE_DIR, "models", "cogman-1b.gguf")

class CogmanBrain:
    def __init__(self, model_path=DEFAULT_MODEL):
        self.model_path = model_path
        self.model = None
        self.load_model()

    def load_model(self):
        if not Llama:
            return
        if not os.path.exists(self.model_path):
            return

        try:
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=2048,
                n_threads=4,
                verbose=False
            )
        except Exception:
            pass

    def ask(self, query):
        if not self.model:
            return f"[!] Cogman Offline: Model not found at {self.model_path}"

        prompt = f"### Instruction:\nYou are Cogman, an elite Linux assistant.\n\n### Input:\n{query}\n\n### Response:\n"
        output = self.model(prompt, max_tokens=256, stop=["###", "EOS"], echo=False)
        return output['choices'][0]['text'].strip()

def main():
    parser = argparse.ArgumentParser(description="Cogman AI Inference Engine")
    parser.add_argument("--query", type=str, help="Query to ask the brain")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Path to GGUF model")
    args = parser.parse_args()

    if args.query:
        brain = CogmanBrain(args.model)
        print(brain.ask(args.query))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
