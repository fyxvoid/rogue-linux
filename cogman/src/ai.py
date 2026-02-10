"""
Cogman Inference Engine
Handles loading of GGUF models and generating responses.
"""
import os
import sys

# Try to import llama_cpp, handle if missing (dev environment)
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

# Path relative to this file: ../../models/cogman-3b.gguf
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "cogman-3b.gguf")

class CogmanBrain:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        """Loads the quantized GGUF model."""
        if not Llama:
            print("[!] Cogman Warining: `llama-cpp-python` not installed.")
            print("    Run: pip install llama-cpp-python")
            return

        if not os.path.exists(MODEL_PATH):
            # Model not trained/moved yet.
            return

        try:
            print(f"[*] Loading Cogman Brain from {MODEL_PATH}...")
            self.model = Llama(
                model_path=MODEL_PATH,
                n_ctx=2048,
                n_threads=4, # Adjust based on CPU
                verbose=False
            )
            print("[+] Brain Loaded.")
        except Exception as e:
            print(f"[-] Brain Damage: {e}")

    def ask(self, query, context=""):
        """
        Generates a response to a user query.
        """
        if not self.model:
            # Fallback / Mock for when model isn't trained yet
            return self._mock_response(query)

        prompt = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
You are Cogman, an elite Linux and Pentesting assistant. 
Answer the following question concisely and technically.

### Input:
{query}

### Response:
"""
        output = self.model(
            prompt, 
            max_tokens=512, 
            stop=["### Instruction:", "EOS"], 
            echo=False
        )
        return output['choices'][0]['text']

    def _mock_response(self, query):
        """Fallback response when AI is offline."""
        return (
            f"[!] Neural Net Offline (Model not found at {MODEL_PATH}).\n"
            f"[!] Please train the model using `training/scripts/train_lora.py` and move the GGUF here.\n"
            f"\n"
            f"You asked: {query}\n"
            f"Standard Reply: Check the man pages, Operator."
        )
