from unsloth import FastLanguageModel
import torch
from datasets import Dataset
import os

# Configuration
max_seq_length = 2048
dtype = None # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
load_in_4bit = True # Use 4bit quantization to reduce memory usage. Can be False.

model_name = "unsloth/Qwen2.5-3B-Instruct-bnb-4bit" # 3B - Better Reasoning
output_dir = "cogman_adapter"
DEBUG_DATA = "training/data/debug_data_100.json"

def train():
    print(f"[*] Loading Model: {model_name}...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = model_name,
        max_seq_length = max_seq_length,
        dtype = dtype,
        load_in_4bit = load_in_4bit,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r = 16, 
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj",],
        lora_alpha = 16,
        lora_dropout = 0, 
        bias = "none",    
        use_gradient_checkpointing = "unsloth", 
        random_state = 3407,
        use_rslora = False,  
        loftq_config = None, 
    )

    # Load Data
    print("[*] Loading Training Data...")
    
    if os.path.exists(DEBUG_DATA):
        print(f"[*] Debug Mode: Using {DEBUG_DATA}")
        dataset = Dataset.from_json(DEBUG_DATA)
    else:
        # Fallback to collection script output
        data_files = []
        for f in os.listdir("training/data"):
            if f.endswith(".txt"):
                with open(os.path.join("training/data", f), "r") as d:
                    data_files.append(d.read())
        
        train_dataset = []
        for text_block in data_files:
            chunks = [text_block[i:i+2000] for i in range(0, len(text_block), 2000)]
            for chunk in chunks:
                train_dataset.append({
                    "instruction": "Explain the following Linux/Kernel concept.",
                    "input": chunk,
                    "output": "Summary based on context..." 
                })
        dataset = Dataset.from_list(train_dataset)

    # Standard Alpaca/Instuct Prompt
    alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}
"""

    EOS_TOKEN = tokenizer.eos_token # Must add EOS_TOKEN
    def formatting_prompts_func(examples):
        instructions = examples["instruction"]
        inputs       = examples["input"]
        outputs      = examples["output"]
        texts = []
        for instruction, input, output in zip(instructions, inputs, outputs):
            # Must add EOS_TOKEN, otherwise your generation will go on forever!
            text = alpaca_prompt.format(instruction, input, output) + EOS_TOKEN
            texts.append(text)
        return { "text" : texts, }

    dataset = dataset.map(formatting_prompts_func, batched = True,)

    print("[*] Starting Training...")
    from trl import SFTTrainer
    from transformers import TrainingArguments

    trainer = SFTTrainer(
        model = model,
        tokenizer = tokenizer,
        train_dataset = dataset,
        dataset_text_field = "text",
        max_seq_length = max_seq_length,
        dataset_num_proc = 2,
        packing = False, # Can make training 5x faster for short sequences.
        args = TrainingArguments(
            per_device_train_batch_size = 2,
            gradient_accumulation_steps = 4,
            warmup_steps = 5,
            max_steps = 60, # Increase for real run!
            learning_rate = 2e-4,
            fp16 = not torch.cuda.is_bf16_supported(),
            bf16 = torch.cuda.is_bf16_supported(),
            logging_steps = 1,
            optim = "adamw_8bit",
            weight_decay = 0.01,
            lr_scheduler_type = "linear",
            seed = 3407,
            output_dir = "outputs",
        ),
    )

    trainer.train()

    print(f"[*] Saving Adapter to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print("[*] Merging to GGUF (Quantized format for 2GB RAM inference)...")
    # model.save_pretrained_gguf("model_q4_k_m", tokenizer, quantization_method = "q4_k_m")
    # This requires llama.cpp installed. 

if __name__ == "__main__":
    train()
