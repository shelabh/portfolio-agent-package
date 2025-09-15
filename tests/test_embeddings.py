"""
Tests for embedding adapters and vector stores.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os

# Test imports
try:
    from src.portfolio_agent.embeddings import OpenAIEmbedder, HuggingFaceEmbedder
    from src.portfolio_agent.vector_stores import FAISSVectorStore, VectorDocument, SearchResult
except ImportError:
    pytest.skip("Embedding modules not available", allow_module_level=True)


class TestOpenAIEmbedder:
    """Test OpenAI embedding adapter."""
    
    @pytest.fixture
    def mock_openai(self):
        """Mock OpenAI client."""
        with patch('src.portfolio_agent.embeddings.openai_embedder.AsyncOpenAI') as mock:
            mock_client = AsyncMock()
            mock.return_value = mock_client
            
            # Mock embedding response
            mock_response = Mock()
            mock_response.data = [
                Mock(embedding=[0.1, 0.2, 0.3, 0.4, 0.5] * 307)  # 1535 dimensions
            ]
            mock_response.usage.total_tokens = 10
            mock_client.embeddings.create.return_value = mock_response
            
            yield mock_client
    
    @pytest.mark.asyncio
    async def test_embed_texts(self, mock_openai):
        """Test embedding multiple texts."""
        embedder = OpenAIEmbedder(api_key="test-key")
        
        texts = ["Hello world", "Test text"]
        result = await embedder.embed_texts(texts)
        
        assert len(result.embeddings) == 2
        assert len(result.embeddings[0]) == 1535
        assert result.tokens_used == 10
        assert result.model_used == "text-embedding-3-small"
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_embed_single(self, mock_openai):
        """Test embedding a single text."""
        embedder = OpenAIEmbedder(api_key="test-key")
        
        embedding = await embedder.embed_single("Hello world")
        
        assert len(embedding) == 1535
        assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5] * 307
    
    def test_get_embedding_dimension(self):
        """Test getting embedding dimension."""
        embedder = OpenAIEmbedder(api_key="test-key")
        
        dimension = embedder.get_embedding_dimension()
        assert dimension == 1536  # text-embedding-3-small
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_openai):
        """Test health check."""
        embedder = OpenAIEmbedder(api_key="test-key")
        
        is_healthy = await embedder.health_check()
        assert is_healthy is True
    
    def test_init_without_api_key(self):
        """Test initialization without API key."""
        with patch('src.portfolio_agent.embeddings.openai_embedder.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                OpenAIEmbedder()


class TestHuggingFaceEmbedder:
    """Test Hugging Face embedding adapter."""
    
    @pytest.fixture
    def mock_sentence_transformers(self):
        """Mock sentence-transformers."""
        with patch('src.portfolio_agent.embeddings.hf_embedder.SentenceTransformer') as mock:
            mock_model = Mock()
            # Return embeddings for 2 texts
            mock_model.encode.return_value = np.array([
                [0.1, 0.2, 0.3, 0.4, 0.5, 0.6] * 64,  # 384 dimensions for first text
                [0.2, 0.3, 0.4, 0.5, 0.6, 0.7] * 64   # 384 dimensions for second text
            ])
            mock.return_value = mock_model
            
            yield mock_model
    
    def test_embed_texts(self, mock_sentence_transformers):
        """Test embedding multiple texts."""
        embedder = HuggingFaceEmbedder()
        
        texts = ["Hello world", "Test text"]
        result = embedder.embed_texts(texts)
        
        assert len(result.embeddings) == 2
        assert len(result.embeddings[0]) == 384
        assert result.model_used == "sentence-transformers/all-MiniLM-L6-v2"
        assert result.processing_time > 0
    
    def test_embed_single(self, mock_sentence_transformers):
        """Test embedding a single text."""
        embedder = HuggingFaceEmbedder()
        
        embedding = embedder.embed_single("Hello world")
        
        assert len(embedding) == 384
        assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5, 0.6] * 64
    
    def test_get_embedding_dimension(self, mock_sentence_transformers):
        """Test getting embedding dimension."""
        embedder = HuggingFaceEmbedder()
        
        dimension = embedder.get_embedding_dimension()
        assert dimension == 384
    
    def test_health_check(self, mock_sentence_transformers):
        """Test health check."""
        embedder = HuggingFaceEmbedder()
        
        is_healthy = embedder.health_check()
        assert is_healthy is True
    
    def test_get_model_info(self, mock_sentence_transformers):
        """Test getting model information."""
        embedder = HuggingFaceEmbedder()
        
        info = embedder.get_model_info()
        assert info['model_name'] == "sentence-transformers/all-MiniLM-L6-v2"
        assert info['embedding_dimension'] == 384
        assert info['device'] in ['cpu', 'cuda', 'mps']


class TestFAISSVectorStore:
    """Test FAISS vector store."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def vector_store(self, temp_dir):
        """Create FAISS vector store for testing."""
        index_path = os.path.join(temp_dir, "test_index")
        return FAISSVectorStore(index_path=index_path, dimension=384)
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            VectorDocument(
                id="doc1",
                content="This is a test document about machine learning.",
                vector=[0.1] * 384,
                metadata={"source": "test", "category": "ml"},
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            ),
            VectorDocument(
                id="doc2", 
                content="This is another document about artificial intelligence.",
                vector=[0.2] * 384,
                metadata={"source": "test", "category": "ai"},
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            ),
            VectorDocument(
                id="doc3",
                content="This document is about natural language processing.",
                vector=[0.3] * 384,
                metadata={"source": "test", "category": "nlp"},
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            )
        ]
    
    def test_add_documents(self, vector_store, sample_documents):
        """Test adding documents to the store."""
        added_ids = vector_store.add_documents(sample_documents)
        
        assert len(added_ids) == 3
        assert "doc1" in added_ids
        assert "doc2" in added_ids
        assert "doc3" in added_ids
        assert len(vector_store.documents) == 3
    
    def test_add_texts(self, vector_store):
        """Test adding texts with vectors."""
        texts = ["Hello world", "Test text"]
        vectors = [[0.1] * 384, [0.2] * 384]
        metadatas = [{"source": "test1"}, {"source": "test2"}]
        
        added_ids = vector_store.add_texts(texts, vectors, metadatas)
        
        assert len(added_ids) == 2
        assert len(vector_store.documents) == 2
    
    def test_search(self, vector_store, sample_documents):
        """Test vector search."""
        # Add documents
        vector_store.add_documents(sample_documents)
        
        # Search with query vector
        query_vector = [0.15] * 384  # Similar to doc1
        results = vector_store.search(query_vector, k=2)
        
        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].document.id == "doc1"  # Should be most similar
        assert results[0].score > 0
    
    def test_search_with_filter(self, vector_store, sample_documents):
        """Test search with metadata filter."""
        # Add documents
        vector_store.add_documents(sample_documents)
        
        # Search with filter
        query_vector = [0.1] * 384
        results = vector_store.search(
            query_vector, 
            k=5, 
            filter_metadata={"category": "ml"}
        )
        
        assert len(results) == 1
        assert results[0].document.metadata["category"] == "ml"
    
    def test_get_document(self, vector_store, sample_documents):
        """Test getting document by ID."""
        vector_store.add_documents(sample_documents)
        
        doc = vector_store.get_document("doc1")
        assert doc is not None
        assert doc.id == "doc1"
        assert doc.content == "This is a test document about machine learning."
        
        # Test non-existent document
        doc = vector_store.get_document("nonexistent")
        assert doc is None
    
    def test_get_stats(self, vector_store, sample_documents):
        """Test getting store statistics."""
        vector_store.add_documents(sample_documents)
        
        stats = vector_store.get_stats()
        assert stats['total_documents'] == 3
        assert stats['dimension'] == 384
        assert stats['index_type'] == "flat"
        assert stats['metric'] == "cosine"
    
    def test_save_and_load(self, vector_store, sample_documents, temp_dir):
        """Test saving and loading the vector store."""
        # Add documents
        vector_store.add_documents(sample_documents)
        
        # Save
        vector_store.save()
        
        # Create new store and load
        new_store = FAISSVectorStore(index_path=os.path.join(temp_dir, "test_index"))
        new_store.load()
        
        assert len(new_store.documents) == 3
        assert new_store.get_document("doc1") is not None
        
        # Test search still works
        query_vector = [0.1] * 384
        results = new_store.search(query_vector, k=1)
        assert len(results) == 1
    
    def test_wrong_dimension(self, vector_store):
        """Test handling of wrong vector dimension."""
        doc = VectorDocument(
            id="wrong_dim",
            content="Test",
            vector=[0.1] * 100,  # Wrong dimension
            metadata={},
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
        added_ids = vector_store.add_documents([doc])
        assert len(added_ids) == 0  # Should be skipped
    
    def test_empty_search(self, vector_store):
        """Test search with empty store."""
        query_vector = [0.1] * 384
        results = vector_store.search(query_vector, k=5)
        assert len(results) == 0
    
    def test_search_by_text(self, vector_store, sample_documents):
        """Test search by text using embedder."""
        # Add documents
        vector_store.add_documents(sample_documents)
        
        # Mock embedder
        mock_embedder = Mock()
        mock_embedder.embed_single.return_value = [0.1] * 384
        
        results = vector_store.search_by_text("machine learning", mock_embedder, k=2)
        
        assert len(results) == 2
        mock_embedder.embed_single.assert_called_once_with("machine learning")


class TestVectorDocument:
    """Test VectorDocument dataclass."""
    
    def test_vector_document_creation(self):
        """Test creating a VectorDocument."""
        doc = VectorDocument(
            id="test_doc",
            content="Test content",
            vector=[0.1, 0.2, 0.3],
            metadata={"source": "test"},
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
        assert doc.id == "test_doc"
        assert doc.content == "Test content"
        assert doc.vector == [0.1, 0.2, 0.3]
        assert doc.metadata == {"source": "test"}


class TestSearchResult:
    """Test SearchResult dataclass."""
    
    def test_search_result_creation(self):
        """Test creating a SearchResult."""
        doc = VectorDocument(
            id="test_doc",
            content="Test content",
            vector=[0.1, 0.2, 0.3],
            metadata={"source": "test"},
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
        result = SearchResult(
            document=doc,
            score=0.95,
            rank=1
        )
        
        assert result.document == doc
        assert result.score == 0.95
        assert result.rank == 1
