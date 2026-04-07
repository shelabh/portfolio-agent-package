#!/usr/bin/env python3
"""
Fine-tuning Demo

This script demonstrates the complete fine-tuning pipeline with PEFT/LoRA,
advanced prompt templates, quality assessment, and performance optimization.
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from portfolio_agent.finetuning import (
    PEFTTrainer, PEFTConfig, PEFTTrainingResult,
    AdvancedPromptTemplate, FewShotTemplate, ChainOfThoughtTemplate,
    QualityAssessor, ResponseEvaluator,
    PerformanceOptimizer, CacheManager,
    SecurityManager, InputValidator, OutputSanitizer
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FineTuningDemo:
    """Comprehensive fine-tuning demonstration."""
    
    def __init__(self):
        """Initialize the demo."""
        self.output_dir = Path("finetuning_demo_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.quality_assessor = None
        self.response_evaluator = None
        self.performance_optimizer = None
        self.security_manager = None
        
    def setup_components(self):
        """Set up all demo components."""
        logger.info("Setting up demo components...")
        
        # Quality assessment
        self.quality_assessor = QualityAssessor(use_sklearn=False)
        self.response_evaluator = ResponseEvaluator(self.quality_assessor)
        
        # Performance optimization
        self.performance_optimizer = PerformanceOptimizer(
            cache_size=1000,
            cache_ttl=None,
            batch_size=16,
            max_concurrent=8
        )
        self.performance_optimizer.start()
        
        # Security management
        self.security_manager = SecurityManager()
        
        logger.info("Demo components setup complete!")
    
    def create_sample_training_data(self) -> List[Dict[str, str]]:
        """Create sample training data for fine-tuning."""
        logger.info("Creating sample training data...")
        
        training_data = [
            {
                "input": "What programming languages do you know?",
                "output": "I have experience with Python, JavaScript, Java, and Go. Python is my strongest language, particularly for data science and web development."
            },
            {
                "input": "Tell me about your experience with machine learning.",
                "output": "I have 3+ years of experience with machine learning, including supervised and unsupervised learning, deep learning with TensorFlow and PyTorch, and MLOps practices."
            },
            {
                "input": "What projects have you worked on?",
                "output": "I've worked on several key projects including an e-commerce platform with microservices architecture, a real-time chat application, and a machine learning pipeline for data analysis."
            },
            {
                "input": "How do you approach problem-solving?",
                "output": "I follow a systematic approach: understand the problem, break it down into smaller components, research solutions, implement iteratively, and test thoroughly."
            },
            {
                "input": "What are your technical strengths?",
                "output": "My technical strengths include full-stack development, cloud architecture (AWS, Azure), database design, API development, and DevOps practices including CI/CD."
            },
            {
                "input": "Describe your leadership experience.",
                "output": "I've led development teams of 5-8 engineers, mentored junior developers, conducted code reviews, and implemented agile methodologies to improve team productivity."
            },
            {
                "input": "What tools and technologies do you use?",
                "output": "I use a wide range of tools including Git, Docker, Kubernetes, Jenkins, PostgreSQL, MongoDB, Redis, and various cloud services for deployment and monitoring."
            },
            {
                "input": "How do you stay updated with technology?",
                "output": "I stay updated through technical blogs, online courses, attending conferences, contributing to open source projects, and experimenting with new technologies."
            }
        ]
        
        logger.info(f"Created {len(training_data)} training examples")
        return training_data
    
    def demonstrate_prompt_templates(self):
        """Demonstrate advanced prompt templates."""
        logger.info("Demonstrating advanced prompt templates...")
        
        # Portfolio Q&A template
        portfolio_template = AdvancedPromptTemplate(
            name="portfolio_qa",
            template="Question: {question}\n\nContext: {context}\n\nAnswer:",
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
        
        # Few-shot template
        from unittest.mock import Mock
        examples = [
            Mock(input="What is Python?", output="Python is a high-level programming language known for its simplicity and readability."),
            Mock(input="What is JavaScript?", output="JavaScript is a programming language primarily used for web development and creating interactive web pages.")
        ]
        
        few_shot_template = FewShotTemplate(
            name="few_shot_qa",
            template="Question: {question}\nAnswer:",
            examples=examples,
            max_examples=2,
            example_selection_strategy="random"
        )
        
        # Chain-of-thought template
        cot_template = ChainOfThoughtTemplate(
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
        
        # Demonstrate templates
        print("\n" + "="*80)
        print("PROMPT TEMPLATES DEMONSTRATION")
        print("="*80)
        
        # Portfolio template
        portfolio_prompt = portfolio_template.format_prompt(
            question="What programming languages do you know?",
            context="I have experience with Python, JavaScript, Java, and Go programming languages."
        )
        print("\n1. Portfolio Q&A Template:")
        print(portfolio_prompt[:200] + "...")
        
        # Few-shot template
        few_shot_prompt = few_shot_template.format_prompt(
            question="What is machine learning?"
        )
        print("\n2. Few-Shot Template:")
        print(few_shot_prompt[:200] + "...")
        
        # Chain-of-thought template
        cot_prompt = cot_template.format_prompt(
            concept="microservices architecture",
            context="A microservices architecture is a method of developing software systems."
        )
        print("\n3. Chain-of-Thought Template:")
        print(cot_prompt[:200] + "...")
        
        print("="*80)
    
    def demonstrate_quality_assessment(self):
        """Demonstrate quality assessment capabilities."""
        logger.info("Demonstrating quality assessment...")
        
        # Sample responses to evaluate
        responses = [
            "Python is a programming language used for web development and data science. It's known for its simplicity and readability.",
            "Python is good for coding stuff and making websites.",
            "I don't know much about Python programming languages."
        ]
        
        query = "What is Python programming?"
        context = "Python is a high-level programming language known for its simplicity and versatility."
        
        print("\n" + "="*80)
        print("QUALITY ASSESSMENT DEMONSTRATION")
        print("="*80)
        
        # Evaluate responses
        results = self.response_evaluator.compare_responses(
            responses, query, context
        )
        
        for i, (response, metrics) in enumerate(results, 1):
            print(f"\nResponse {i} (Score: {metrics.overall_score:.3f}):")
            print(f"  Text: {response[:100]}...")
            print(f"  Relevance: {metrics.relevance_score:.3f}")
            print(f"  Coherence: {metrics.coherence_score:.3f}")
            print(f"  Fluency: {metrics.fluency_score:.3f}")
            print(f"  Completeness: {metrics.completeness_score:.3f}")
        
        # Get best response
        best_response, best_metrics = self.response_evaluator.get_best_response(
            responses, query, context
        )
        
        print(f"\nBest Response (Score: {best_metrics.overall_score:.3f}):")
        print(f"  {best_response}")
        
        print("="*80)
    
    def demonstrate_performance_optimization(self):
        """Demonstrate performance optimization features."""
        logger.info("Demonstrating performance optimization...")
        
        print("\n" + "="*80)
        print("PERFORMANCE OPTIMIZATION DEMONSTRATION")
        print("="*80)
        
        # Caching demonstration
        @self.performance_optimizer.cached_function()
        def expensive_computation(n):
            """Simulate expensive computation."""
            time.sleep(0.1)  # Simulate work
            return n * n * n
        
        print("\n1. Caching Demonstration:")
        
        # First call (cache miss)
        start_time = time.time()
        result1 = expensive_computation(5)
        time1 = time.time() - start_time
        print(f"  First call: {result1} (took {time1:.3f}s)")
        
        # Second call (cache hit)
        start_time = time.time()
        result2 = expensive_computation(5)
        time2 = time.time() - start_time
        print(f"  Second call: {result2} (took {time2:.3f}s)")
        
        print(f"  Speedup: {time1/time2:.1f}x faster")
        
        # Performance statistics
        stats = self.performance_optimizer.get_performance_stats()
        print(f"\n2. Performance Statistics:")
        print(f"  Cache hit rate: {stats['cache_hit_rate']:.2%}")
        print(f"  Total operations: {stats['metrics']['total_operations']}")
        print(f"  Cache hits: {stats['metrics']['cache_hits']}")
        print(f"  Cache misses: {stats['metrics']['cache_misses']}")
        
        print("="*80)
    
    def demonstrate_security_features(self):
        """Demonstrate security features."""
        logger.info("Demonstrating security features...")
        
        print("\n" + "="*80)
        print("SECURITY FEATURES DEMONSTRATION")
        print("="*80)
        
        # Input validation
        print("\n1. Input Validation:")
        test_inputs = [
            "Hello, how are you?",  # Valid
            "x" * 10000,  # Too long
            "<script>alert('xss')</script>",  # XSS attempt
            "'; DROP TABLE users; --",  # SQL injection
            "../../../etc/passwd"  # Path traversal
        ]
        
        for test_input in test_inputs:
            is_valid, sanitized, violations = self.security_manager.validate_and_sanitize_input(test_input)
            print(f"  '{test_input[:30]}...': {'✓ Valid' if is_valid else '✗ Invalid'}")
        
        # Output sanitization
        print("\n2. Output Sanitization:")
        test_outputs = [
            "This is a clean response.",
            "This has <script>alert('xss')</script> in it.",
            "User input: '; DROP TABLE users; --",
            "File path: ../../../etc/passwd"
        ]
        
        for test_output in test_outputs:
            sanitized = self.security_manager.output_sanitizer.sanitize_output(test_output)
            print(f"  Original: {test_output[:40]}...")
            print(f"  Sanitized: {sanitized[:40]}...")
            print()
        
        # Rate limiting
        print("3. Rate Limiting:")
        user_id = "demo_user"
        for i in range(8):
            allowed, reason = self.security_manager.rate_limiter.is_allowed(user_id, "default")
            print(f"  Request {i+1}: {'✓ Allowed' if allowed else '✗ Blocked'}")
        
        print("="*80)
    
    async def demonstrate_async_processing(self):
        """Demonstrate async processing capabilities."""
        logger.info("Demonstrating async processing...")
        
        print("\n" + "="*80)
        print("ASYNC PROCESSING DEMONSTRATION")
        print("="*80)
        
        async def simulate_api_call(delay: float, result: str) -> str:
            """Simulate an API call with delay."""
            await asyncio.sleep(delay)
            return result
        
        # Process multiple API calls concurrently
        tasks = [
            simulate_api_call(0.1, "Result 1"),
            simulate_api_call(0.2, "Result 2"),
            simulate_api_call(0.15, "Result 3"),
            simulate_api_call(0.05, "Result 4")
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        print(f"\nProcessed {len(tasks)} async tasks in {total_time:.3f}s")
        print("Results:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result}")
        
        print("="*80)
    
    def demonstrate_peft_training(self):
        """Demonstrate PEFT training (simulated)."""
        logger.info("Demonstrating PEFT training...")
        
        print("\n" + "="*80)
        print("PEFT TRAINING DEMONSTRATION")
        print("="*80)
        
        # Create PEFT configuration
        config = PEFTConfig(
            model_name="microsoft/DialoGPT-small",  # Use smaller model for demo
            r=8,
            lora_alpha=16,
            lora_dropout=0.1,
            learning_rate=2e-4,
            num_train_epochs=1,
            per_device_train_batch_size=2
        )
        
        print(f"\nPEFT Configuration:")
        print(f"  Model: {config.model_name}")
        print(f"  LoRA rank: {config.r}")
        print(f"  LoRA alpha: {config.lora_alpha}")
        print(f"  Learning rate: {config.learning_rate}")
        print(f"  Epochs: {config.num_train_epochs}")
        
        # Create training data
        training_data = self.create_sample_training_data()
        
        print(f"\nTraining Data:")
        print(f"  Examples: {len(training_data)}")
        print(f"  Sample: {training_data[0]['input'][:50]}...")
        
        # Note: Actual training would require PEFT libraries
        print(f"\nNote: Actual PEFT training requires:")
        print(f"  - PEFT library: pip install peft")
        print(f"  - Transformers: pip install transformers")
        print(f"  - Datasets: pip install datasets")
        print(f"  - Sufficient GPU memory")
        
        print("="*80)
    
    def run_comprehensive_evaluation(self):
        """Run comprehensive evaluation of the system."""
        logger.info("Running comprehensive evaluation...")
        
        print("\n" + "="*80)
        print("COMPREHENSIVE EVALUATION")
        print("="*80)
        
        # Test data for evaluation
        test_data = [
            {
                "query": "What programming languages do you know?",
                "context": "I have experience with Python, JavaScript, Java, and Go.",
                "reference": "I know Python, JavaScript, Java, and Go programming languages."
            },
            {
                "query": "Tell me about your machine learning experience.",
                "context": "I have 3+ years of ML experience with TensorFlow and PyTorch.",
                "reference": "I have over 3 years of machine learning experience using TensorFlow and PyTorch."
            }
        ]
        
        # Generate responses (simulated)
        model_responses = [
            "I have experience with Python, JavaScript, Java, and Go programming languages.",
            "I have 3+ years of machine learning experience with TensorFlow and PyTorch frameworks."
        ]
        
        # Evaluate performance
        performance_metrics = self.response_evaluator.evaluate_model_performance(
            test_data, model_responses
        )
        
        print(f"\nModel Performance Metrics:")
        for metric, score in performance_metrics.items():
            print(f"  {metric.capitalize()}: {score:.3f}")
        
        # Overall assessment
        overall_score = performance_metrics['overall']
        if overall_score >= 0.8:
            grade = "Excellent"
        elif overall_score >= 0.6:
            grade = "Good"
        elif overall_score >= 0.4:
            grade = "Fair"
        else:
            grade = "Needs Improvement"
        
        print(f"\nOverall Assessment: {grade} ({overall_score:.3f})")
        
        print("="*80)
    
    async def run_demo(self):
        """Run the complete fine-tuning demo."""
        print("🚀 Fine-tuning & Advanced Features Demo")
        print("="*60)
        
        try:
            # Setup components
            self.setup_components()
            
            # Demonstrate each component
            self.demonstrate_prompt_templates()
            self.demonstrate_quality_assessment()
            self.demonstrate_performance_optimization()
            self.demonstrate_security_features()
            await self.demonstrate_async_processing()
            self.demonstrate_peft_training()
            self.run_comprehensive_evaluation()
            
            print("\n🎉 Fine-tuning demo completed successfully!")
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            raise
        finally:
            # Cleanup
            if self.performance_optimizer:
                self.performance_optimizer.stop()

def main():
    """Main demonstration function."""
    demo = FineTuningDemo()
    
    try:
        # Run the demo
        asyncio.run(demo.run_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise

if __name__ == "__main__":
    main()
