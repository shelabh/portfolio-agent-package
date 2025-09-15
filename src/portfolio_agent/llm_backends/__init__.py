"""
LLM backends module for portfolio-agent.

This module provides LLM provider adapters:
- OpenAI client
- Hugging Face client
- AWS Bedrock client (optional)
"""

from .openai_client import OpenAIClient
from .hf_client import HuggingFaceClient
from .bedrock_client import BedrockClient

__all__ = [
    "OpenAIClient",
    "HuggingFaceClient",
    "BedrockClient"
]
