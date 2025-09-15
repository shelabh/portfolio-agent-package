"""
Advanced Prompt Templates

This module provides sophisticated prompt templates with few-shot examples,
chain-of-thought reasoning, and dynamic template generation.
"""

import logging
import json
import random
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)

class PromptType(Enum):
    """Types of prompt templates."""
    SIMPLE = "simple"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    ROLE_BASED = "role_based"
    CONTEXTUAL = "contextual"
    CONVERSATIONAL = "conversational"

@dataclass
class PromptExample:
    """A single prompt example."""
    input: str
    output: str
    explanation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class PromptTemplate:
    """Base prompt template."""
    name: str
    template: str
    prompt_type: PromptType = PromptType.SIMPLE
    variables: List[str] = None
    examples: List[PromptExample] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = self._extract_variables()
        if self.examples is None:
            self.examples = []
        if self.metadata is None:
            self.metadata = {}
    
    def _extract_variables(self) -> List[str]:
        """Extract variables from template string."""
        import re
        variables = re.findall(r'\{(\w+)\}', self.template)
        return list(set(variables))

class AdvancedPromptTemplate(PromptTemplate):
    """Advanced prompt template with sophisticated features."""
    
    def __init__(
        self,
        name: str,
        template: str,
        prompt_type: PromptType = PromptType.SIMPLE,
        examples: List[PromptExample] = None,
        system_prompt: Optional[str] = None,
        instructions: List[str] = None,
        constraints: List[str] = None,
        output_format: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """Initialize advanced prompt template.
        
        Args:
            name: Template name
            template: Template string with variables
            prompt_type: Type of prompt template
            examples: Few-shot examples
            system_prompt: System-level instructions
            instructions: Step-by-step instructions
            constraints: Output constraints
            output_format: Expected output format
            metadata: Additional metadata
        """
        super().__init__(name, template, prompt_type, None, examples, metadata)
        
        self.system_prompt = system_prompt
        self.instructions = instructions or []
        self.constraints = constraints or []
        self.output_format = output_format
    
    def format_prompt(
        self,
        **kwargs
    ) -> str:
        """Format the prompt with given variables.
        
        Args:
            **kwargs: Variables to substitute in template
            
        Returns:
            Formatted prompt string
        """
        # Start with system prompt if available
        prompt_parts = []
        
        if self.system_prompt:
            prompt_parts.append(f"System: {self.system_prompt}")
        
        # Add instructions
        if self.instructions:
            prompt_parts.append("Instructions:")
            for i, instruction in enumerate(self.instructions, 1):
                prompt_parts.append(f"{i}. {instruction}")
        
        # Add constraints
        if self.constraints:
            prompt_parts.append("Constraints:")
            for constraint in self.constraints:
                prompt_parts.append(f"- {constraint}")
        
        # Add few-shot examples if available
        if self.examples and self.prompt_type == PromptType.FEW_SHOT:
            prompt_parts.append("Examples:")
            for i, example in enumerate(self.examples, 1):
                prompt_parts.append(f"Example {i}:")
                prompt_parts.append(f"Input: {example.input}")
                prompt_parts.append(f"Output: {example.output}")
                if example.explanation:
                    prompt_parts.append(f"Explanation: {example.explanation}")
                prompt_parts.append("")
        
        # Add chain-of-thought reasoning if applicable
        if self.prompt_type == PromptType.CHAIN_OF_THOUGHT:
            prompt_parts.append("Please think step by step and explain your reasoning.")
        
        # Add the main template
        try:
            formatted_template = self.template.format(**kwargs)
            prompt_parts.append(formatted_template)
        except KeyError as e:
            logger.error(f"Missing variable in template: {e}")
            raise
        
        # Add output format if specified
        if self.output_format:
            prompt_parts.append(f"Please format your response as: {self.output_format}")
        
        return "\n".join(prompt_parts)
    
    def add_example(self, example: PromptExample):
        """Add a new example to the template."""
        self.examples.append(example)
    
    def get_random_examples(self, n: int) -> List[PromptExample]:
        """Get n random examples from the template."""
        if len(self.examples) <= n:
            return self.examples
        return random.sample(self.examples, n)

class FewShotTemplate(AdvancedPromptTemplate):
    """Specialized template for few-shot learning."""
    
    def __init__(
        self,
        name: str,
        template: str,
        examples: List[PromptExample],
        max_examples: int = 5,
        example_selection_strategy: str = "random",
        **kwargs
    ):
        """Initialize few-shot template.
        
        Args:
            name: Template name
            template: Template string
            examples: Available examples
            max_examples: Maximum number of examples to include
            example_selection_strategy: Strategy for selecting examples
            **kwargs: Additional arguments
        """
        super().__init__(
            name=name,
            template=template,
            prompt_type=PromptType.FEW_SHOT,
            examples=examples,
            **kwargs
        )
        
        self.max_examples = max_examples
        self.example_selection_strategy = example_selection_strategy
    
    def select_examples(
        self,
        query: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[PromptExample]:
        """Select examples based on strategy.
        
        Args:
            query: Current query for similarity-based selection
            context: Additional context for selection
            
        Returns:
            Selected examples
        """
        if self.example_selection_strategy == "random":
            return self.get_random_examples(self.max_examples)
        elif self.example_selection_strategy == "first":
            return self.examples[:self.max_examples]
        elif self.example_selection_strategy == "similarity" and query:
            # Simple similarity-based selection (could be enhanced with embeddings)
            return self._select_similar_examples(query, self.max_examples)
        else:
            return self.examples[:self.max_examples]
    
    def _select_similar_examples(
        self,
        query: str,
        n: int
    ) -> List[PromptExample]:
        """Select examples similar to the query."""
        # Simple keyword-based similarity
        query_words = set(query.lower().split())
        
        scored_examples = []
        for example in self.examples:
            example_words = set(example.input.lower().split())
            similarity = len(query_words.intersection(example_words))
            scored_examples.append((similarity, example))
        
        # Sort by similarity and return top n
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        return [example for _, example in scored_examples[:n]]
    
    def format_prompt(
        self,
        query: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Format prompt with selected examples."""
        # Select examples
        selected_examples = self.select_examples(query, context)
        
        # Temporarily replace examples
        original_examples = self.examples
        self.examples = selected_examples
        
        # Format prompt
        formatted = super().format_prompt(**kwargs)
        
        # Restore original examples
        self.examples = original_examples
        
        return formatted

class ChainOfThoughtTemplate(AdvancedPromptTemplate):
    """Template for chain-of-thought reasoning."""
    
    def __init__(
        self,
        name: str,
        template: str,
        reasoning_steps: List[str] = None,
        **kwargs
    ):
        """Initialize chain-of-thought template.
        
        Args:
            name: Template name
            template: Template string
            reasoning_steps: Suggested reasoning steps
            **kwargs: Additional arguments
        """
        super().__init__(
            name=name,
            template=template,
            prompt_type=PromptType.CHAIN_OF_THOUGHT,
            **kwargs
        )
        
        self.reasoning_steps = reasoning_steps or [
            "Understand the problem",
            "Identify key information",
            "Apply relevant knowledge",
            "Reason through the solution",
            "Provide the final answer"
        ]
    
    def format_prompt(self, **kwargs) -> str:
        """Format prompt with chain-of-thought instructions."""
        # Add reasoning steps to instructions
        if not any("reasoning" in inst.lower() for inst in self.instructions):
            self.instructions.extend([
                "Think through the problem step by step",
                "Show your reasoning process",
                "Explain each step clearly"
            ])
        
        return super().format_prompt(**kwargs)

class PromptTemplateManager:
    """Manager for prompt templates."""
    
    def __init__(self):
        """Initialize template manager."""
        self.templates: Dict[str, AdvancedPromptTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default prompt templates."""
        # Portfolio Q&A template
        portfolio_template = AdvancedPromptTemplate(
            name="portfolio_qa",
            template="Question: {question}\n\nContext: {context}\n\nAnswer:",
            prompt_type=PromptType.CONTEXTUAL,
            system_prompt="You are a professional portfolio assistant. Provide accurate, helpful responses based on the given context.",
            instructions=[
                "Read the question carefully",
                "Use the provided context to answer",
                "Be specific and professional",
                "Cite relevant information from the context"
            ],
            constraints=[
                "Stay within the provided context",
                "Be accurate and factual",
                "Use professional language"
            ],
            output_format="Clear, concise answer with relevant details"
        )
        
        # Technical explanation template
        technical_template = ChainOfThoughtTemplate(
            name="technical_explanation",
            template="Explain the following technical concept: {concept}\n\nContext: {context}",
            system_prompt="You are a technical expert. Explain complex concepts clearly and accurately.",
            reasoning_steps=[
                "Identify the core concept",
                "Break down complex ideas",
                "Provide examples and analogies",
                "Explain practical applications",
                "Summarize key points"
            ]
        )
        
        # Conversation template
        conversation_template = AdvancedPromptTemplate(
            name="conversation",
            template="Previous conversation:\n{conversation_history}\n\nCurrent question: {question}\n\nResponse:",
            prompt_type=PromptType.CONVERSATIONAL,
            system_prompt="You are having a natural conversation. Be engaging and contextually aware.",
            instructions=[
                "Consider the conversation history",
                "Maintain context and continuity",
                "Be natural and conversational",
                "Ask follow-up questions when appropriate"
            ]
        )
        
        # Add templates
        self.add_template(portfolio_template)
        self.add_template(technical_template)
        self.add_template(conversation_template)
    
    def add_template(self, template: AdvancedPromptTemplate):
        """Add a template to the manager."""
        self.templates[template.name] = template
        logger.info(f"Added template: {template.name}")
    
    def get_template(self, name: str) -> Optional[AdvancedPromptTemplate]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def list_templates(self) -> List[str]:
        """List all available template names."""
        return list(self.templates.keys())
    
    def format_prompt(
        self,
        template_name: str,
        **kwargs
    ) -> str:
        """Format a prompt using a template."""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        return template.format_prompt(**kwargs)
    
    def save_templates(self, filepath: str):
        """Save templates to a file."""
        templates_data = {}
        for name, template in self.templates.items():
            templates_data[name] = {
                "name": template.name,
                "template": template.template,
                "prompt_type": template.prompt_type.value,
                "system_prompt": template.system_prompt,
                "instructions": template.instructions,
                "constraints": template.constraints,
                "output_format": template.output_format,
                "examples": [
                    {
                        "input": ex.input,
                        "output": ex.output,
                        "explanation": ex.explanation,
                        "metadata": ex.metadata
                    }
                    for ex in template.examples
                ],
                "metadata": template.metadata
            }
        
        with open(filepath, 'w') as f:
            json.dump(templates_data, f, indent=2)
        
        logger.info(f"Saved templates to {filepath}")
    
    def load_templates(self, filepath: str):
        """Load templates from a file."""
        with open(filepath, 'r') as f:
            templates_data = json.load(f)
        
        for name, data in templates_data.items():
            # Create examples
            examples = [
                PromptExample(
                    input=ex["input"],
                    output=ex["output"],
                    explanation=ex.get("explanation"),
                    metadata=ex.get("metadata")
                )
                for ex in data.get("examples", [])
            ]
            
            # Create template
            template = AdvancedPromptTemplate(
                name=data["name"],
                template=data["template"],
                prompt_type=PromptType(data["prompt_type"]),
                examples=examples,
                system_prompt=data.get("system_prompt"),
                instructions=data.get("instructions", []),
                constraints=data.get("constraints", []),
                output_format=data.get("output_format"),
                metadata=data.get("metadata", {})
            )
            
            self.add_template(template)
        
        logger.info(f"Loaded templates from {filepath}")

# Convenience functions
def create_portfolio_template() -> AdvancedPromptTemplate:
    """Create a portfolio Q&A template."""
    return AdvancedPromptTemplate(
        name="portfolio_qa",
        template="Question: {question}\n\nContext: {context}\n\nAnswer:",
        prompt_type=PromptType.CONTEXTUAL,
        system_prompt="You are a professional portfolio assistant.",
        instructions=["Use the context to answer accurately", "Be professional and specific"],
        constraints=["Stay within the provided context", "Be factual"]
    )

def create_technical_template() -> ChainOfThoughtTemplate:
    """Create a technical explanation template."""
    return ChainOfThoughtTemplate(
        name="technical_explanation",
        template="Explain: {concept}\n\nContext: {context}",
        system_prompt="You are a technical expert.",
        reasoning_steps=["Understand the concept", "Break it down", "Provide examples", "Summarize"]
    )

# Global template manager instance
template_manager = PromptTemplateManager()
