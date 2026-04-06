"""
Fine-tuning Module

This module provides PEFT/LoRA fine-tuning capabilities for LLM adaptation
with advanced prompt templates and quality assessment.
"""

from .peft_trainer import PEFTTrainer, PEFTConfig, PEFTTrainingResult
from .prompt_templates import PromptTemplate, AdvancedPromptTemplate, FewShotTemplate, ChainOfThoughtTemplate
from .quality_assessor import QualityAssessor, QualityMetrics, ResponseEvaluator
from .performance_optimizer import PerformanceOptimizer, CacheManager, BatchProcessor
from .security_manager import SecurityManager, InputValidator, OutputSanitizer

__all__ = [
    'PEFTTrainer',
    'PEFTConfig', 
    'PEFTTrainingResult',
    'PromptTemplate',
    'AdvancedPromptTemplate',
    'FewShotTemplate',
    'ChainOfThoughtTemplate',
    'QualityAssessor',
    'QualityMetrics',
    'ResponseEvaluator',
    'PerformanceOptimizer',
    'CacheManager',
    'BatchProcessor',
    'SecurityManager',
    'InputValidator',
    'OutputSanitizer'
]
