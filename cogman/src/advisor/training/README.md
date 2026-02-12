# Cogman AI Training Guide

This directory contains the pipeline to train **Cogman**, the AI Assistant for Rogue Linux.

## 1. Components
- **`data/`**: Text data collected from Man pages, Kernel docs, and Security guides.
- **`scripts/collect_data.py`**: Automates data scraping and formatting.
- **`scripts/train_lora.py`**: Fine-tunes a 3B parameter model using QLoRA.

## 2. Requirements (Training Machine)
**Note**: Do NOT run this on the Rogue Linux low-spec environment. Transfer this `training/` folder to a machine with:
- **GPU**: NVIDIA GPU with >= 8GB VRAM (Tesla T4, RTX 3060, or better).
- **RAM**: 16GB+ System RAM.
- **Python**: 3.10+.

## 3. Setup (On GPU Machine)
```bash
# Install dependencies
pip install unsloth "unsloth[colab-new]" @ git+https://github.com/unslothai/unsloth.git
pip install --no-deps "xformers<0.0.26" trl peft accelerate bitsandbytes
```

## 4. Execution
```bash
# 1. Prototype/Debug Run (Single Shot)
# This uses the small debug_data.json to verify the pipeline.
python scripts/train_lora.py --debug

# 2. Full Training (On GPU Machine)
# Ensure data is collected first:
python scripts/collect_data.py
python scripts/train_lora.py
```

## 5. Output
The script will save the trained adapters to `cogman_adapter/` and optionally merge them into a `.gguf` file.
Copy the `.gguf` file back to `rogue-linux/cogman/models/` to enable local inference on valid hardware.
