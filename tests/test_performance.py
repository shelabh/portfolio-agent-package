"""
Performance Tests

This module contains performance tests and benchmarks for the portfolio agent
components including RAG pipeline, vector operations, and agent performance.
"""

import pytest
import time
import asyncio
from typing import List, Dict, Any
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from portfolio_agent.embeddings.openai_embedder import OpenAIEmbedder
from portfolio_agent.vector_stores.faiss_store import FAISSVectorStore
from portfolio_agent.rag_pipeline import RAGPipeline
from portfolio_agent.agents.router import RouterAgent
from portfolio_agent.agents.retriever import RetrieverAgent
from portfolio_agent.agents.reranker import RerankerAgent
from portfolio_agent.agents.persona import PersonaAgent
from portfolio_agent.security.pii_detector import AdvancedPIIDetector
from portfolio_agent.security.data_encryption import DataEncryption

class TestPerformance:
    """Performance test suite for portfolio agent components."""
    
    @pytest.fixture
    def sample_documents(self):
        """Generate sample documents for testing."""
        return [
            {
                "id": f"doc_{i}",
                "content": f"This is sample document {i} with some content about machine learning and AI. " * 10,
                "metadata": {"source": f"test_source_{i}", "type": "test"}
            }
            for i in range(100)
        ]
    
    @pytest.fixture
    def sample_queries(self):
        """Generate sample queries for testing."""
        return [
            "What is machine learning?",
            "How does AI work?",
            "Explain neural networks",
            "What are the benefits of deep learning?",
            "How to implement a chatbot?"
        ] * 20  # 100 queries total
    
    @pytest.mark.asyncio
    async def test_embedding_performance(self, sample_documents):
        """Test embedding generation performance."""
        from unittest.mock import AsyncMock, patch
        
        # Mock the OpenAI client to avoid API calls
        with patch('portfolio_agent.embeddings.openai_embedder.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.data = [AsyncMock()]
            mock_response.data[0].embedding = [0.1] * 1536  # Mock embedding
            mock_response.usage.total_tokens = 100
            
            mock_client.return_value.embeddings.create = AsyncMock(return_value=mock_response)
            
            embedder = OpenAIEmbedder()
            
            # Test single document embedding
            start_time = time.time()
            result = await embedder.embed_texts([sample_documents[0]["content"]])
            single_time = time.time() - start_time
            
            assert single_time < 2.0  # Should complete within 2 seconds
            assert len(result.embeddings) == 1
            assert len(result.embeddings[0]) > 0
    
    def test_vector_store_performance(self, sample_documents):
        """Test vector store operations performance."""
        from portfolio_agent.vector_stores.faiss_store import VectorDocument
        
        store = FAISSVectorStore()
        
        # Convert sample documents to VectorDocument objects with mock vectors
        documents = []
        for doc in sample_documents[:50]:
            document = VectorDocument(
                id=doc["id"],
                content=doc["content"],
                metadata=doc["metadata"],
                vector=[0.1] * 384,  # Mock vector (384 dimensions for sentence-transformers)
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            documents.append(document)
        
        # Test batch insertion
        start_time = time.time()
        store.add_documents(documents)
        insertion_time = time.time() - start_time
        
        assert insertion_time < 5.0  # Should complete within 5 seconds
        
        # Test search performance
        start_time = time.time()
        query_vector = [0.1] * 384  # Mock query vector
        results = store.search(query_vector, k=10)
        search_time = time.time() - start_time
        
        assert search_time < 1.0  # Should complete within 1 second
        assert len(results) <= 10
    
    def test_rag_pipeline_performance(self, sample_documents, sample_queries):
        """Test RAG pipeline performance."""
        # Setup pipeline components
        embedder = OpenAIEmbedder()
        vector_store = FAISSVectorStore()
        
        # Add documents to vector store
        vector_store.add_documents(sample_documents[:20])
        
        # Create RAG pipeline
        pipeline = RAGPipeline(
            embedder=embedder,
            vector_store=vector_store,
            llm_client=None  # Mock for performance testing
        )
        
        # Test single query performance
        start_time = time.time()
        result = pipeline.process_query(sample_queries[0])
        query_time = time.time() - start_time
        
        assert query_time < 10.0  # Should complete within 10 seconds
        assert result is not None
    
    def test_agent_performance(self):
        """Test individual agent performance."""
        # Test Router Agent
        router = RouterAgent()
        start_time = time.time()
        decision = router.route_query("What is machine learning?")
        router_time = time.time() - start_time
        
        assert router_time < 1.0  # Should complete within 1 second
        assert decision in ["retriever", "direct", "tool"]
        
        # Test Retriever Agent
        retriever = RetrieverAgent()
        start_time = time.time()
        results = retriever.retrieve_documents("machine learning", k=5)
        retriever_time = time.time() - start_time
        
        assert retriever_time < 2.0  # Should complete within 2 seconds
        assert isinstance(results, list)
        
        # Test Reranker Agent
        reranker = RerankerAgent()
        start_time = time.time()
        reranked = reranker.rerank_documents(results, "machine learning")
        reranker_time = time.time() - start_time
        
        assert reranker_time < 3.0  # Should complete within 3 seconds
        assert isinstance(reranked, list)
        
        # Test Persona Agent
        persona = PersonaAgent()
        start_time = time.time()
        response = persona.generate_response("machine learning", reranked)
        persona_time = time.time() - start_time
        
        assert persona_time < 5.0  # Should complete within 5 seconds
        assert isinstance(response, str)
    
    def test_security_performance(self):
        """Test security component performance."""
        # Test PII Detection
        detector = AdvancedPIIDetector()
        test_text = "Contact me at john.doe@example.com or call 555-123-4567. My SSN is 123-45-6789."
        
        start_time = time.time()
        result = detector.detect_pii(test_text)
        pii_time = time.time() - start_time
        
        assert pii_time < 2.0  # Should complete within 2 seconds
        assert len(result.detected_pii) > 0
        
        # Test Data Encryption
        encryption = DataEncryption()
        test_data = {"name": "John Doe", "email": "john@example.com"}
        
        start_time = time.time()
        key_id = encryption.generate_key()
        encrypted = encryption.encrypt_data(test_data, key_id)
        encryption_time = time.time() - start_time
        
        assert encryption_time < 1.0  # Should complete within 1 second
        
        start_time = time.time()
        decrypted = encryption.decrypt_data(encrypted, key_id)
        decryption_time = time.time() - start_time
        
        assert decryption_time < 1.0  # Should complete within 1 second
        assert decrypted == test_data
    
    def test_memory_usage(self, sample_documents):
        """Test memory usage during operations."""
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        store = FAISSVectorStore()
        store.add_documents(sample_documents)
        
        # Check memory usage
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - initial_memory
        
        # Should not use more than 100MB for 100 documents
        assert memory_increase < 100.0
        
        # Clean up
        del store
        gc.collect()
    
    def test_concurrent_operations(self, sample_documents, sample_queries):
        """Test concurrent operations performance."""
        import concurrent.futures
        
        store = FAISSVectorStore()
        store.add_documents(sample_documents[:20])
        
        def process_query(query):
            return store.search(query, k=5)
        
        # Test concurrent searches
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_query, query) for query in sample_queries[:10]]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        concurrent_time = time.time() - start_time
        
        # Concurrent operations should be faster than sequential
        assert concurrent_time < 15.0  # Should complete within 15 seconds
        assert len(results) == 10
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_benchmark_embedding_generation(self, benchmark, sample_documents):
        """Benchmark embedding generation."""
        from unittest.mock import AsyncMock, patch
        
        # Mock the OpenAI client to avoid API calls
        with patch('portfolio_agent.embeddings.openai_embedder.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.data = [AsyncMock() for _ in range(10)]
            for i, data in enumerate(mock_response.data):
                data.embedding = [0.1] * 1536  # Mock embedding
            mock_response.usage.total_tokens = 1000
            
            mock_client.return_value.embeddings.create = AsyncMock(return_value=mock_response)
            
            embedder = OpenAIEmbedder()
            
            async def embed_documents():
                return await embedder.embed_texts([doc["content"] for doc in sample_documents[:10]])
            
            result = await benchmark(embed_documents)
            assert len(result.embeddings) == 10
    
    @pytest.mark.benchmark
    def test_benchmark_vector_search(self, benchmark, sample_documents):
        """Benchmark vector search operations."""
        store = FAISSVectorStore()
        store.add_documents(sample_documents)
        
        def search_operation():
            return store.search("machine learning", k=10)
        
        result = benchmark(search_operation)
        assert len(result) <= 10
    
    @pytest.mark.benchmark
    def test_benchmark_pii_detection(self, benchmark):
        """Benchmark PII detection."""
        detector = AdvancedPIIDetector()
        test_text = "Contact me at john.doe@example.com or call 555-123-4567. My SSN is 123-45-6789."
        
        def detect_pii():
            return detector.detect_pii(test_text)
        
        result = benchmark(detect_pii)
        assert len(result.detected_pii) > 0
    
    @pytest.mark.benchmark
    def test_benchmark_encryption(self, benchmark):
        """Benchmark encryption operations."""
        encryption = DataEncryption()
        key_id = encryption.generate_key()
        test_data = {"name": "John Doe", "email": "john@example.com"}
        
        def encrypt_data():
            return encryption.encrypt_data(test_data, key_id)
        
        result = benchmark(encrypt_data)
        assert result.encrypted_data is not None

class TestLoadTesting:
    """Load testing for high-volume scenarios."""
    
    def test_high_volume_documents(self):
        """Test performance with high volume of documents."""
        store = FAISSVectorStore()
        
        # Generate 1000 documents
        documents = [
            {
                "id": f"doc_{i}",
                "content": f"Document {i} content about various topics including AI, ML, and data science. " * 5,
                "metadata": {"source": f"source_{i}", "type": "test"}
            }
            for i in range(1000)
        ]
        
        start_time = time.time()
        store.add_documents(documents)
        insertion_time = time.time() - start_time
        
        # Should handle 1000 documents within reasonable time
        assert insertion_time < 30.0  # 30 seconds for 1000 documents
        
        # Test search performance with large index
        start_time = time.time()
        results = store.search("artificial intelligence", k=20)
        search_time = time.time() - start_time
        
        assert search_time < 2.0  # Should still be fast
        assert len(results) <= 20
    
    def test_high_volume_queries(self):
        """Test performance with high volume of queries."""
        store = FAISSVectorStore()
        
        # Add some documents
        documents = [
            {
                "id": f"doc_{i}",
                "content": f"Document {i} about machine learning and AI",
                "metadata": {"source": f"source_{i}"}
            }
            for i in range(100)
        ]
        store.add_documents(documents)
        
        # Generate 100 queries
        queries = [f"Query {i} about machine learning" for i in range(100)]
        
        start_time = time.time()
        results = []
        for query in queries:
            results.append(store.search(query, k=5))
        total_time = time.time() - start_time
        
        # Should handle 100 queries within reasonable time
        assert total_time < 20.0  # 20 seconds for 100 queries
        assert len(results) == 100

class TestScalability:
    """Scalability tests for different system sizes."""
    
    def test_scalability_documents(self):
        """Test scalability with increasing document count."""
        store = FAISSVectorStore()
        
        document_counts = [10, 50, 100, 200]
        times = []
        
        for count in document_counts:
            documents = [
                {
                    "id": f"doc_{i}",
                    "content": f"Document {i} content",
                    "metadata": {"source": f"source_{i}"}
                }
                for i in range(count)
            ]
            
            start_time = time.time()
            store.add_documents(documents)
            insertion_time = time.time() - start_time
            times.append(insertion_time)
        
        # Times should scale reasonably (not exponentially)
        for i in range(1, len(times)):
            # Each doubling should not take more than 3x the time
            ratio = times[i] / times[i-1]
            assert ratio < 3.0, f"Scalability issue: ratio {ratio} too high"
    
    def test_scalability_queries(self):
        """Test scalability with increasing query count."""
        store = FAISSVectorStore()
        
        # Add base documents
        documents = [
            {
                "id": f"doc_{i}",
                "content": f"Document {i} about various topics",
                "metadata": {"source": f"source_{i}"}
            }
            for i in range(100)
        ]
        store.add_documents(documents)
        
        query_counts = [10, 50, 100]
        times = []
        
        for count in query_counts:
            queries = [f"Query {i}" for i in range(count)]
            
            start_time = time.time()
            for query in queries:
                store.search(query, k=5)
            total_time = time.time() - start_time
            times.append(total_time)
        
        # Times should scale linearly
        for i in range(1, len(times)):
            ratio = times[i] / times[i-1]
            expected_ratio = query_counts[i] / query_counts[i-1]
            # Allow some variance but should be roughly linear
            assert ratio < expected_ratio * 1.5, f"Query scalability issue: ratio {ratio} vs expected {expected_ratio}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
