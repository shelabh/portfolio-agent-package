"""
Ingestion module for portfolio-agent.

This module provides content ingestor adapters for various sources:
- GitHub repositories
- Resume PDFs
- Website HTML content
- Generic file readers
- PII redaction utilities
- Text chunking utilities
"""

from .github_ingestor import GitHubIngestor
from .resume_ingestor import ResumeIngestor
from .website_ingestor import WebsiteIngestor
from .generic_ingestor import GenericIngestor
from .pii_redactor import PIIRedactor, pii_redactor
from .chunker import TextChunker, text_chunker

__all__ = [
    "GitHubIngestor",
    "ResumeIngestor", 
    "WebsiteIngestor",
    "GenericIngestor",
    "PIIRedactor",
    "pii_redactor",
    "TextChunker",
    "text_chunker"
]
