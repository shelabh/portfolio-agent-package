"""
Fine-tuning module for portfolio-agent.

This module provides PEFT/LoRA fine-tuning examples:
- LoRA training scripts
- Example notebooks
- Quantized serving notes
"""

from .lora_train import LoRATrainer

__all__ = [
    "LoRATrainer"
]
