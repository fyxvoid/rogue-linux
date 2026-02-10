# Cogman AI Architecture

## Overview
Cogman is the "Teacher" persona of Rogue Linux, providing context-aware guidance on Linux internals and offensive security without compromising safety.

## 1. Model Selection
We selected **Qwen2.5-3B-Instruct** for the prototype phase.
- **Reasoning**: It outperforms Llama-2-7B and StableLM-3B in logic and coding tasks while remaining small enough for quantized execution.
- **Quantization**: 4-bit (q4_k_m) via `llama.cpp`.
- **Target Hardware**: 
  - VRAM: < 3GB (CPU Offload supported).
  - RAM: < 4GB System RAM.

## 2. Training Strategy
- **Method**: QLoRA (Quantized Low-Rank Adaptation) via `unsloth`.
- **Base Model**: `unsloth/Qwen2.5-3B-Instruct-bnb-4bit`.
- **Pipeline**:
    1. **Data Collection**: `training/scripts/collect_data.py`.
    2. **Synthetic Expansion**: `training/scripts/generate_synthetic_data.py` (100+ Q&A).
    3. **Fine-Tuning**: `training/scripts/train_lora.py`.
    4. **Verification**: `training/scripts/verify_model.py`.

## 3. Data Strategy
- **Sources**:
    - Local Man Pages (`/usr/share/man`).
    - Linux Kernel Documentation (`kernel.org`).
    - Synthetic Reasoning Pairs (created via `generate_synthetic_data.py`).
- **Format**: Alpaca-style JSON (`instruction`, `input`, `output`).

## 4. Inference Engine (`cogman/src/ai.py`)
- **Backend**: `llama-cpp-python`.
- **Interface**: Decoupled from the Planner via the `advisor` crate.
- **Fallback**: Graceful degradation when model weights are missing.
