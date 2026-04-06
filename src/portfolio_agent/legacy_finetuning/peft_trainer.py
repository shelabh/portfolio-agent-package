"""
PEFT/LoRA Fine-tuning Trainer

This module provides Parameter-Efficient Fine-Tuning (PEFT) capabilities
using LoRA (Low-Rank Adaptation) for LLM adaptation.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import torch
from pathlib import Path

try:
    from peft import LoraConfig, get_peft_model, TaskType, PeftModel
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, TrainingArguments, 
        Trainer, DataCollatorForLanguageModeling
    )
    from datasets import Dataset
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
    logging.warning("PEFT libraries not available. Install with: pip install peft transformers datasets")

from ..config import settings

logger = logging.getLogger(__name__)

@dataclass
class PEFTConfig:
    """Configuration for PEFT/LoRA fine-tuning."""
    model_name: str = "microsoft/DialoGPT-medium"
    task_type: str = "CAUSAL_LM"
    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: List[str] = None
    bias: str = "none"
    use_rslora: bool = False
    loftq_config: Optional[Dict] = None
    
    # Training parameters
    learning_rate: float = 2e-4
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 1
    warmup_steps: int = 100
    weight_decay: float = 0.01
    logging_steps: int = 10
    save_steps: int = 500
    eval_steps: int = 500
    save_total_limit: int = 2
    
    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = ["q_proj", "v_proj"]

@dataclass
class PEFTTrainingResult:
    """Result of PEFT training."""
    model_path: str
    training_loss: float
    eval_loss: float
    training_time: float
    config: PEFTConfig
    metrics: Dict[str, Any]
    created_at: str

class PEFTTrainer:
    """PEFT/LoRA fine-tuning trainer for LLM adaptation."""
    
    def __init__(
        self,
        config: PEFTConfig,
        output_dir: str = "finetuned_models",
        device: Optional[str] = None
    ):
        """Initialize PEFT trainer.
        
        Args:
            config: PEFT configuration
            output_dir: Directory to save fine-tuned models
            device: Device to use for training (auto-detect if None)
        """
        if not PEFT_AVAILABLE:
            raise ImportError(
                "PEFT libraries not available. Install with: pip install peft transformers datasets"
            )
        
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Device setup
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        # Initialize components
        self.tokenizer = None
        self.model = None
        self.peft_model = None
        self.trainer = None
        
        logger.info(f"PEFT trainer initialized on {self.device}")
    
    def load_model_and_tokenizer(self):
        """Load the base model and tokenizer."""
        logger.info(f"Loading model: {self.config.model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None
        )
        
        logger.info("Model and tokenizer loaded successfully")
    
    def setup_peft_model(self):
        """Setup PEFT model with LoRA configuration."""
        logger.info("Setting up PEFT model with LoRA")
        
        # Create LoRA config
        lora_config = LoraConfig(
            task_type=getattr(TaskType, self.config.task_type),
            r=self.config.r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=self.config.target_modules,
            bias=self.config.bias,
            use_rslora=self.config.use_rslora,
            loftq_config=self.config.loftq_config
        )
        
        # Apply PEFT to model
        self.peft_model = get_peft_model(self.model, lora_config)
        
        # Print trainable parameters
        trainable_params = sum(p.numel() for p in self.peft_model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.peft_model.parameters())
        
        logger.info(f"Trainable parameters: {trainable_params:,}")
        logger.info(f"Total parameters: {total_params:,}")
        logger.info(f"Trainable %: {100 * trainable_params / total_params:.2f}%")
    
    def prepare_dataset(
        self,
        data: List[Dict[str, str]],
        max_length: int = 512,
        test_size: float = 0.1
    ) -> tuple:
        """Prepare dataset for training.
        
        Args:
            data: List of training examples with 'input' and 'output' keys
            max_length: Maximum sequence length
            test_size: Fraction of data to use for testing
            
        Returns:
            Tuple of (train_dataset, eval_dataset)
        """
        logger.info(f"Preparing dataset with {len(data)} examples")
        
        # Tokenize data
        def tokenize_function(examples):
            # Combine input and output
            texts = [f"{ex['input']} {self.tokenizer.eos_token} {ex['output']}" 
                    for ex in examples]
            
            # Tokenize
            tokenized = self.tokenizer(
                texts,
                truncation=True,
                padding=True,
                max_length=max_length,
                return_tensors="pt"
            )
            
            # Set labels (same as input_ids for causal LM)
            tokenized["labels"] = tokenized["input_ids"].clone()
            
            return tokenized
        
        # Create dataset
        dataset = Dataset.from_list(data)
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        
        # Split dataset
        if test_size > 0:
            split_dataset = tokenized_dataset.train_test_split(test_size=test_size)
            train_dataset = split_dataset["train"]
            eval_dataset = split_dataset["test"]
        else:
            train_dataset = tokenized_dataset
            eval_dataset = None
        
        logger.info(f"Train dataset: {len(train_dataset)} examples")
        if eval_dataset:
            logger.info(f"Eval dataset: {len(eval_dataset)} examples")
        
        return train_dataset, eval_dataset
    
    def setup_trainer(
        self,
        train_dataset,
        eval_dataset=None,
        data_collator=None
    ):
        """Setup the trainer."""
        logger.info("Setting up trainer")
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            learning_rate=self.config.learning_rate,
            num_train_epochs=self.config.num_train_epochs,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            warmup_steps=self.config.warmup_steps,
            weight_decay=self.config.weight_decay,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_steps=self.config.eval_steps,
            save_total_limit=self.config.save_total_limit,
            evaluation_strategy="steps" if eval_dataset else "no",
            save_strategy="steps",
            load_best_model_at_end=True if eval_dataset else False,
            metric_for_best_model="eval_loss" if eval_dataset else None,
            greater_is_better=False,
            report_to=None,  # Disable wandb/tensorboard
            remove_unused_columns=False,
        )
        
        # Data collator
        if data_collator is None:
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False
            )
        
        # Create trainer
        self.trainer = Trainer(
            model=self.peft_model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        logger.info("Trainer setup complete")
    
    def train(
        self,
        data: List[Dict[str, str]],
        max_length: int = 512,
        test_size: float = 0.1
    ) -> PEFTTrainingResult:
        """Train the model with PEFT/LoRA.
        
        Args:
            data: Training data
            max_length: Maximum sequence length
            test_size: Fraction of data for testing
            
        Returns:
            PEFTTrainingResult with training results
        """
        import time
        start_time = time.time()
        
        logger.info("Starting PEFT training")
        
        try:
            # Load model and tokenizer
            self.load_model_and_tokenizer()
            
            # Setup PEFT model
            self.setup_peft_model()
            
            # Prepare dataset
            train_dataset, eval_dataset = self.prepare_dataset(
                data, max_length, test_size
            )
            
            # Setup trainer
            self.setup_trainer(train_dataset, eval_dataset)
            
            # Train
            logger.info("Beginning training...")
            training_result = self.trainer.train()
            
            # Save model
            model_save_path = self.output_dir / "final_model"
            self.trainer.save_model(str(model_save_path))
            self.tokenizer.save_pretrained(str(model_save_path))
            
            # Save config
            config_save_path = model_save_path / "peft_config.json"
            with open(config_save_path, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)
            
            training_time = time.time() - start_time
            
            # Create result
            result = PEFTTrainingResult(
                model_path=str(model_save_path),
                training_loss=training_result.training_loss,
                eval_loss=training_result.metrics.get("eval_loss", 0.0),
                training_time=training_time,
                config=self.config,
                metrics=training_result.metrics,
                created_at=datetime.now().isoformat()
            )
            
            logger.info(f"Training completed in {training_time:.2f}s")
            logger.info(f"Final training loss: {result.training_loss:.4f}")
            if result.eval_loss > 0:
                logger.info(f"Final eval loss: {result.eval_loss:.4f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise
    
    def load_finetuned_model(self, model_path: str):
        """Load a fine-tuned model.
        
        Args:
            model_path: Path to the fine-tuned model
        """
        logger.info(f"Loading fine-tuned model from {model_path}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None
        )
        
        # Load PEFT model
        self.peft_model = PeftModel.from_pretrained(self.model, model_path)
        
        logger.info("Fine-tuned model loaded successfully")
    
    def generate_response(
        self,
        prompt: str,
        max_length: int = 100,
        temperature: float = 0.7,
        do_sample: bool = True
    ) -> str:
        """Generate response using the fine-tuned model.
        
        Args:
            prompt: Input prompt
            max_length: Maximum generation length
            temperature: Sampling temperature
            do_sample: Whether to use sampling
            
        Returns:
            Generated response
        """
        if self.peft_model is None or self.tokenizer is None:
            raise ValueError("Model not loaded. Call load_finetuned_model() first.")
        
        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.peft_model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove input prompt from response
        if response.startswith(prompt):
            response = response[len(prompt):].strip()
        
        return response
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get training statistics.
        
        Returns:
            Dictionary with training statistics
        """
        return {
            "config": asdict(self.config),
            "device": self.device,
            "model_loaded": self.model is not None,
            "peft_model_loaded": self.peft_model is not None,
            "tokenizer_loaded": self.tokenizer is not None,
            "trainer_ready": self.trainer is not None
        }

# Convenience function for easy access
def create_peft_trainer(config: PEFTConfig, **kwargs) -> PEFTTrainer:
    """Create a PEFT trainer with the given configuration.
    
    Args:
        config: PEFT configuration
        **kwargs: Additional arguments to pass to PEFTTrainer
        
    Returns:
        Configured PEFTTrainer instance
    """
    return PEFTTrainer(config, **kwargs)
