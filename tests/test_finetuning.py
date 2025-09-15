"""
Tests for fine-tuning and advanced features.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from datetime import datetime, timedelta

# Test imports
try:
    from src.portfolio_agent.finetuning import (
        PEFTTrainer, PEFTConfig, PEFTTrainingResult,
        PromptTemplate, AdvancedPromptTemplate, FewShotTemplate, ChainOfThoughtTemplate,
        QualityAssessor, QualityMetrics, ResponseEvaluator,
        PerformanceOptimizer, CacheManager, BatchProcessor,
        SecurityManager, InputValidator, OutputSanitizer
    )
    FINETUNING_AVAILABLE = True
except ImportError:
    FINETUNING_AVAILABLE = False
    pytest.skip("Fine-tuning modules not available", allow_module_level=True)


class TestPEFTConfig:
    """Test PEFT configuration."""
    
    def test_default_config(self):
        """Test default PEFT configuration."""
        config = PEFTConfig()
        
        assert config.model_name == "microsoft/DialoGPT-medium"
        assert config.task_type == "CAUSAL_LM"
        assert config.r == 16
        assert config.lora_alpha == 32
        assert config.lora_dropout == 0.1
        assert config.target_modules == ["q_proj", "v_proj"]
        assert config.bias == "none"
        assert config.use_rslora == False
    
    def test_custom_config(self):
        """Test custom PEFT configuration."""
        config = PEFTConfig(
            model_name="custom-model",
            r=32,
            lora_alpha=64,
            learning_rate=1e-4,
            num_train_epochs=5
        )
        
        assert config.model_name == "custom-model"
        assert config.r == 32
        assert config.lora_alpha == 64
        assert config.learning_rate == 1e-4
        assert config.num_train_epochs == 5


class TestPromptTemplates:
    """Test prompt templates."""
    
    def test_simple_template(self):
        """Test simple prompt template."""
        template = PromptTemplate(
            name="test_template",
            template="Hello {name}, how are you?",
            variables=["name"]
        )
        
        assert template.name == "test_template"
        assert "name" in template.variables
        assert template.prompt_type.value == "simple"
    
    def test_advanced_template(self):
        """Test advanced prompt template."""
        template = AdvancedPromptTemplate(
            name="advanced_test",
            template="Question: {question}\nAnswer:",
            system_prompt="You are a helpful assistant.",
            instructions=["Be helpful", "Be accurate"],
            constraints=["Stay on topic"]
        )
        
        formatted = template.format_prompt(question="What is AI?")
        
        assert "System: You are a helpful assistant." in formatted
        assert "Instructions:" in formatted
        assert "Question: What is AI?" in formatted
        assert "Answer:" in formatted
    
    def test_few_shot_template(self):
        """Test few-shot template."""
        examples = [
            Mock(input="What is Python?", output="Python is a programming language."),
            Mock(input="What is Java?", output="Java is a programming language.")
        ]
        
        template = FewShotTemplate(
            name="few_shot_test",
            template="Question: {question}\nAnswer:",
            examples=examples,
            max_examples=2
        )
        
        formatted = template.format_prompt(question="What is JavaScript?")
        
        assert "Examples:" in formatted
        assert "What is Python?" in formatted
        assert "Python is a programming language." in formatted
    
    def test_chain_of_thought_template(self):
        """Test chain-of-thought template."""
        template = ChainOfThoughtTemplate(
            name="cot_test",
            template="Solve: {problem}",
            reasoning_steps=["Understand", "Plan", "Execute", "Verify"]
        )
        
        formatted = template.format_prompt(problem="2 + 2 = ?")
        
        assert "Solve: 2 + 2 = ?" in formatted
        assert "Think through the problem step by step" in formatted


class TestQualityAssessor:
    """Test quality assessment."""
    
    @pytest.fixture
    def quality_assessor(self):
        """Create quality assessor for testing."""
        return QualityAssessor(use_sklearn=False)
    
    def test_relevance_calculation(self, quality_assessor):
        """Test relevance score calculation."""
        response = "Python is a programming language used for web development and data science."
        query = "What is Python programming?"
        
        relevance = quality_assessor._calculate_relevance(response, query)
        
        assert 0.0 <= relevance <= 1.0
        assert relevance > 0.5  # Should be relevant
    
    def test_coherence_calculation(self, quality_assessor):
        """Test coherence score calculation."""
        response = "Python is great. However, it has some limitations. Therefore, choose wisely."
        
        coherence = quality_assessor._calculate_coherence(response)
        
        assert 0.0 <= coherence <= 1.0
    
    def test_fluency_calculation(self, quality_assessor):
        """Test fluency score calculation."""
        response = "This is a well-written sentence with proper grammar and structure."
        
        fluency = quality_assessor._calculate_fluency(response)
        
        assert 0.0 <= fluency <= 1.0
    
    def test_completeness_calculation(self, quality_assessor):
        """Test completeness score calculation."""
        response = "Python is a programming language that is widely used."
        query = "What is Python?"
        
        completeness = quality_assessor._calculate_completeness(response, query)
        
        assert 0.0 <= completeness <= 1.0
    
    def test_full_assessment(self, quality_assessor):
        """Test full quality assessment."""
        response = "Python is a high-level programming language known for its simplicity and readability."
        query = "What is Python programming?"
        
        metrics = quality_assessor.assess_response(response, query)
        
        assert isinstance(metrics, QualityMetrics)
        assert 0.0 <= metrics.overall_score <= 1.0
        assert metrics.relevance_score > 0
        assert metrics.coherence_score > 0
        assert metrics.fluency_score > 0


class TestResponseEvaluator:
    """Test response evaluator."""
    
    @pytest.fixture
    def evaluator(self):
        """Create response evaluator for testing."""
        quality_assessor = QualityAssessor(use_sklearn=False)
        return ResponseEvaluator(quality_assessor)
    
    def test_compare_responses(self, evaluator):
        """Test response comparison."""
        responses = [
            "Python is a programming language.",
            "Python is a high-level programming language known for its simplicity.",
            "I don't know about Python."
        ]
        query = "What is Python?"
        
        results = evaluator.compare_responses(responses, query)
        
        assert len(results) == 3
        assert results[0][1].overall_score >= results[1][1].overall_score
        assert results[1][1].overall_score >= results[2][1].overall_score
    
    def test_get_best_response(self, evaluator):
        """Test getting best response."""
        responses = [
            "Python is a programming language.",
            "Python is a high-level programming language known for its simplicity."
        ]
        query = "What is Python?"
        
        best_response, metrics = evaluator.get_best_response(responses, query)
        
        assert best_response in responses
        assert isinstance(metrics, QualityMetrics)


class TestCacheManager:
    """Test cache manager."""
    
    @pytest.fixture
    def cache_manager(self):
        """Create cache manager for testing."""
        return CacheManager(max_size=10, eviction_policy="lru")
    
    def test_cache_set_get(self, cache_manager):
        """Test basic cache set and get operations."""
        cache_manager.set("key1", "value1")
        
        result = cache_manager.get("key1")
        assert result == "value1"
    
    def test_cache_miss(self, cache_manager):
        """Test cache miss."""
        result = cache_manager.get("nonexistent")
        assert result is None
    
    def test_cache_ttl(self, cache_manager):
        """Test cache TTL expiration."""
        cache_manager.set("key1", "value1", ttl=timedelta(milliseconds=100))
        
        # Should be available immediately
        assert cache_manager.get("key1") == "value1"
        
        # Wait for expiration
        import time
        time.sleep(0.2)
        
        # Should be expired
        assert cache_manager.get("key1") is None
    
    def test_cache_eviction(self, cache_manager):
        """Test cache eviction."""
        # Fill cache beyond max size
        for i in range(15):
            cache_manager.set(f"key{i}", f"value{i}")
        
        # Should have evicted some entries
        assert len(cache_manager.cache) <= 10
    
    def test_cache_decorator(self, cache_manager):
        """Test cache decorator."""
        call_count = 0
        
        @cache_manager.cached()
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call (should use cache)
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment


class TestBatchProcessor:
    """Test batch processor."""
    
    @pytest.fixture
    def batch_processor(self):
        """Create batch processor for testing."""
        return BatchProcessor(batch_size=3, max_wait_time=0.5)
    
    def test_batch_processor_initialization(self, batch_processor):
        """Test batch processor initialization."""
        assert batch_processor.batch_size == 3
        assert batch_processor.max_wait_time == 0.5
        assert not batch_processor.processing
    
    def test_add_request(self, batch_processor):
        """Test adding requests to batch."""
        callback_called = False
        
        def callback(result):
            nonlocal callback_called
            callback_called = True
        
        batch_processor.add_request("test_request", callback)
        
        # Start processor
        batch_processor.start()
        
        # Wait a bit for processing
        import time
        time.sleep(1.0)
        
        batch_processor.stop()
        
        # Callback should have been called
        assert callback_called


class TestPerformanceOptimizer:
    """Test performance optimizer."""
    
    @pytest.fixture
    def optimizer(self):
        """Create performance optimizer for testing."""
        return PerformanceOptimizer(cache_size=100, batch_size=5)
    
    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization."""
        assert optimizer.cache_manager.max_size == 100
        assert optimizer.batch_processor.batch_size == 5
        assert optimizer.async_processor.max_concurrent == 10
    
    def test_cached_function_decorator(self, optimizer):
        """Test cached function decorator."""
        call_count = 0
        
        @optimizer.cached_function()
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call (cached)
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 1
        
        # Check metrics
        stats = optimizer.get_performance_stats()
        assert stats['metrics']['cache_hits'] == 1
        assert stats['metrics']['cache_misses'] == 1
    
    def test_performance_stats(self, optimizer):
        """Test performance statistics."""
        stats = optimizer.get_performance_stats()
        
        assert 'cache_stats' in stats
        assert 'cache_hit_rate' in stats
        assert 'metrics' in stats
        assert 'batch_processor_active' in stats


class TestSecurityManager:
    """Test security manager."""
    
    @pytest.fixture
    def security_manager(self):
        """Create security manager for testing."""
        return SecurityManager()
    
    def test_input_validation(self, security_manager):
        """Test input validation."""
        # Valid input
        assert security_manager.validate_input("Hello world") == True
        
        # Invalid input (too long)
        long_input = "x" * 10000
        assert security_manager.validate_input(long_input) == False
        
        # Invalid input (suspicious patterns)
        assert security_manager.validate_input("<script>alert('xss')</script>") == False
    
    def test_output_sanitization(self, security_manager):
        """Test output sanitization."""
        # Clean output
        clean_output = "This is a clean response."
        sanitized = security_manager.sanitize_output(clean_output)
        assert sanitized == clean_output
        
        # Output with potential issues
        dirty_output = "This has <script>alert('xss')</script> in it."
        sanitized = security_manager.sanitize_output(dirty_output)
        assert "<script>" not in sanitized
    
    def test_rate_limiting(self, security_manager):
        """Test rate limiting."""
        user_id = "test_user"
        
        # Should allow first few requests
        for i in range(5):
            assert security_manager.check_rate_limit(user_id) == True
        
        # Should block after rate limit
        for i in range(10):
            result = security_manager.check_rate_limit(user_id)
            if not result:
                break
        
        # At least one should be blocked
        assert security_manager.check_rate_limit(user_id) == False


class TestInputValidator:
    """Test input validator."""
    
    @pytest.fixture
    def validator(self):
        """Create input validator for testing."""
        return InputValidator()
    
    def test_validate_length(self, validator):
        """Test length validation."""
        assert validator.validate_length("short") == True
        assert validator.validate_length("x" * 10000) == False
    
    def test_validate_content(self, validator):
        """Test content validation."""
        assert validator.validate_content("Hello world") == True
        assert validator.validate_content("<script>alert('xss')</script>") == False
    
    def test_validate_format(self, validator):
        """Test format validation."""
        assert validator.validate_format("valid@email.com") == True
        assert validator.validate_format("invalid-email") == False


class TestOutputSanitizer:
    """Test output sanitizer."""
    
    @pytest.fixture
    def sanitizer(self):
        """Create output sanitizer for testing."""
        return OutputSanitizer()
    
    def test_sanitize_html(self, sanitizer):
        """Test HTML sanitization."""
        dirty = "<script>alert('xss')</script>Hello world"
        clean = sanitizer.sanitize_html(dirty)
        assert "<script>" not in clean
        assert "Hello world" in clean
    
    def test_sanitize_sql(self, sanitizer):
        """Test SQL injection sanitization."""
        dirty = "'; DROP TABLE users; --"
        clean = sanitizer.sanitize_sql(dirty)
        assert "DROP TABLE" not in clean
    
    def test_sanitize_path(self, sanitizer):
        """Test path traversal sanitization."""
        dirty = "../../../etc/passwd"
        clean = sanitizer.sanitize_path(dirty)
        assert "../" not in clean


class TestIntegration:
    """Integration tests for fine-tuning features."""
    
    def test_prompt_template_with_quality_assessment(self):
        """Test prompt template with quality assessment."""
        # Create template
        template = AdvancedPromptTemplate(
            name="test_template",
            template="Answer: {question}",
            system_prompt="You are a helpful assistant."
        )
        
        # Format prompt
        formatted = template.format_prompt(question="What is AI?")
        
        # Assess quality
        assessor = QualityAssessor(use_sklearn=False)
        metrics = assessor.assess_response(
            response="AI is artificial intelligence.",
            query="What is AI?"
        )
        
        assert metrics.overall_score > 0
        assert "Answer: What is AI?" in formatted
    
    def test_performance_optimization_with_caching(self):
        """Test performance optimization with caching."""
        optimizer = PerformanceOptimizer()
        
        @optimizer.cached_function()
        def expensive_operation(x):
            return x * x
        
        # First call
        result1 = expensive_operation(5)
        assert result1 == 25
        
        # Second call (should be cached)
        result2 = expensive_operation(5)
        assert result2 == 25
        
        # Check cache hit rate
        stats = optimizer.get_performance_stats()
        assert stats['cache_hit_rate'] > 0
    
    def test_security_with_validation_and_sanitization(self):
        """Test security with validation and sanitization."""
        security_manager = SecurityManager()
        
        # Test input validation
        valid_input = "Hello world"
        assert security_manager.validate_input(valid_input) == True
        
        # Test output sanitization
        clean_output = "This is a clean response."
        sanitized = security_manager.sanitize_output(clean_output)
        assert sanitized == clean_output
        
        # Test rate limiting
        user_id = "test_user"
        assert security_manager.check_rate_limit(user_id) == True
