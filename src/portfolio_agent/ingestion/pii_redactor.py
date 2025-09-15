"""
PII Redaction module for portfolio-agent.

This module provides functionality to detect and redact personally identifiable information (PII)
from text content to ensure privacy and compliance.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PIIRedactor:
    """PII detection and redaction utility."""
    
    def __init__(self, redact_patterns: Optional[Dict[str, str]] = None):
        """Initialize PII redactor.
        
        Args:
            redact_patterns: Custom regex patterns for PII detection
        """
        self.patterns = redact_patterns or self._get_default_patterns()
        self.redaction_count = 0
    
    def redact_pii(self, text: str, replacement: str = "[REDACTED]") -> Tuple[str, Dict[str, int]]:
        """Redact PII from text content.
        
        Args:
            text: Input text to process
            replacement: Replacement string for redacted content
            
        Returns:
            Tuple of (redacted_text, redaction_stats)
        """
        if not text:
            return text, {}
        
        redacted_text = text
        redaction_stats = {}
        
        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, redacted_text, re.IGNORECASE)
            if matches:
                redacted_text = re.sub(pattern, replacement, redacted_text, flags=re.IGNORECASE)
                redaction_stats[pii_type] = len(matches)
                logger.debug(f"Redacted {len(matches)} {pii_type} instances")
        
        # Update total redaction count
        total_redactions = sum(redaction_stats.values())
        if total_redactions > 0:
            self.redaction_count += total_redactions
            logger.info(f"Redacted {total_redactions} PII instances from text")
        
        return redacted_text, redaction_stats
    
    def _get_default_patterns(self) -> Dict[str, str]:
        """Get default PII detection patterns."""
        return {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'address': r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)',
            'zip_code': r'\b\d{5}(?:-\d{4})?\b',
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'url': r'https?://[^\s<>"{}|\\^`\[\]]+',
            'github_token': r'ghp_[a-zA-Z0-9]{36}',
            'openai_key': r'sk-[a-zA-Z0-9]{48}',
            'aws_key': r'AKIA[0-9A-Z]{16}',
            'private_key': r'-----BEGIN [A-Z ]+ PRIVATE KEY-----',
        }
    
    def add_custom_pattern(self, name: str, pattern: str) -> None:
        """Add a custom PII detection pattern.
        
        Args:
            name: Name of the PII type
            pattern: Regex pattern for detection
        """
        self.patterns[name] = pattern
        logger.info(f"Added custom PII pattern: {name}")
    
    def get_redaction_stats(self) -> Dict[str, int]:
        """Get overall redaction statistics."""
        return {
            'total_redactions': self.redaction_count,
            'patterns_configured': len(self.patterns)
        }
    
    def validate_text(self, text: str) -> Dict[str, bool]:
        """Validate text for PII presence without redacting.
        
        Args:
            text: Text to validate
            
        Returns:
            Dictionary of PII types found
        """
        validation_results = {}
        
        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            validation_results[pii_type] = len(matches) > 0
        
        return validation_results


# Global PII redactor instance
pii_redactor = PIIRedactor()
