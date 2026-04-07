"""
Prompt templates for portfolio-agent.

This module provides configurable prompt templates for different use cases.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PromptTemplates:
    """Prompt template manager for different personas and use cases."""
    
    def __init__(self):
        """Initialize prompt templates."""
        self.templates = {
            "persona": self._get_persona_template(),
            "recruiter": self._get_recruiter_template(),
            "assistant": self._get_assistant_template()
        }
    
    def get_template(self, template_name: str, **kwargs) -> str:
        """Get a formatted prompt template.
        
        Args:
            template_name: Name of the template
            **kwargs: Variables to format into the template
            
        Returns:
            Formatted prompt string
        """
        if template_name not in self.templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = self.templates[template_name]
        return template.format(**kwargs)
    
    def _get_persona_template(self) -> str:
        """Get persona prompt template."""
        return """You are a professional portfolio assistant. Maintain a formal, concise tone.
Cite sources when providing factual claims using [[source_id]] notation.

Context: {context}
Query: {query}

Please provide a helpful response based on the context provided."""
    
    def _get_recruiter_template(self) -> str:
        """Get recruiter prompt template."""
        return """You are a recruiter assistant helping evaluate candidates.
Provide objective, professional assessments based on available information.

Context: {context}
Query: {query}

Please provide an assessment based on the candidate information."""
    
    def _get_assistant_template(self) -> str:
        """Get personal assistant prompt template."""
        return """You are a helpful personal assistant. Be friendly, efficient, and proactive.

Context: {context}
Query: {query}

Please provide a helpful response."""
