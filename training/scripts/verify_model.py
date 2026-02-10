"""
Verification Script for Trained Model.
Loads the test dataset and runs inference on every question to check model recall/reasoning.
"""
import json
import sys
from unsloth import FastLanguageModel
from transformers import TextStreamer

# Path to trained adapter (default: database_adapter matching train_lora.py)
ADAPTER_PATH = "cogman_adapter"
DATA_PATH = "training/data/debug_data_100.json"

def verify():
    # 1. Load Model
    print(f"[*] Loading Trained Adapter from {ADAPTER_PATH}...")
    try:
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name = ADAPTER_PATH,
            max_seq_length = 2048,
            dtype = None,
            load_in_4bit = True,
        )
        FastLanguageModel.for_inference(model)
    except Exception as e:
        print(f"[-] Failed to load model: {e}")
        print("    Ensure you have run `python scripts/train_lora.py` first.")
        sys.exit(1)

    # 2. Load Questions
    with open(DATA_PATH, "r") as f:
        qa_pairs = json.load(f)

    print(f"[*] Loaded {len(qa_pairs)} test cases.")

    # 3. Alpaca Prompt Template
    alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
"""

    # 4. Infer
    correct_format_count = 0
    
    print("-" * 50)
    for i, item in enumerate(qa_pairs):
        instruction = item["instruction"]
        input_text = item.get("input", "")
        
        inputs = tokenizer(
            [alpaca_prompt.format(instruction, input_text)], 
            return_tensors = "pt"
        ).to("cuda")

        print(f"[{i+1}/{len(qa_pairs)}] Q: {instruction}")
        
        # streaming output
        text_streamer = TextStreamer(tokenizer)
        _ = model.generate(**inputs, streamer = text_streamer, max_new_tokens = 128)
        
        print("\n" + "-" * 20)

    print("[+] Verification Complete.")

if __name__ == "__main__":
    verify()
