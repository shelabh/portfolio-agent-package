import tempfile
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest

from portfolio_agent.embeddings import HuggingFaceEmbedder, OpenAIEmbedder
from portfolio_agent.vector_stores import FAISSVectorStore, VectorDocument


class TestOpenAIEmbedder:
    @pytest.fixture
    def mock_clients(self):
        with patch("portfolio_agent.embeddings.openai_embedder.AsyncOpenAI") as async_client_cls, patch(
            "portfolio_agent.embeddings.openai_embedder.OpenAI"
        ) as sync_client_cls:
            async_client = AsyncMock()
            sync_client = Mock()

            async_response = Mock()
            async_response.data = [Mock(embedding=[0.1] * 1536), Mock(embedding=[0.2] * 1536)]
            async_response.usage.total_tokens = 10
            async_client.embeddings.create.return_value = async_response

            sync_response = Mock()
            sync_response.data = [Mock(embedding=[0.3] * 1536)]
            sync_response.usage.total_tokens = 5
            sync_client.embeddings.create.return_value = sync_response

            async_client_cls.return_value = async_client
            sync_client_cls.return_value = sync_client
            yield async_client, sync_client

    @pytest.mark.asyncio
    async def test_embed_texts(self, mock_clients):
        embedder = OpenAIEmbedder(api_key="test-key")
        result = await embedder.embed_texts(["a", "b"])
        assert len(result.embeddings) == 2
        assert len(result.embeddings[0]) == 1536

    def test_embed_texts_sync(self, mock_clients):
        embedder = OpenAIEmbedder(api_key="test-key")
        result = embedder.embed_texts_sync(["a"])
        assert len(result.embeddings) == 1
        assert len(result.embeddings[0]) == 1536


class TestHuggingFaceEmbedder:
    @pytest.fixture
    def mock_sentence_transformers(self):
        with patch("portfolio_agent.embeddings.hf_embedder.SentenceTransformer") as model_cls:
            model = Mock()
            model.encode.return_value = np.array(
                [
                    [0.1, 0.2, 0.3, 0.4, 0.5, 0.6] * 64,
                    [0.2, 0.3, 0.4, 0.5, 0.6, 0.7] * 64,
                ]
            )
            model_cls.return_value = model
            yield model

    def test_embed_single(self, mock_sentence_transformers):
        embedder = HuggingFaceEmbedder()
        embedding = embedder.embed_single("hello")
        assert len(embedding) == 384


class TestFAISSVectorStore:
    def test_search_by_text_uses_sync_embedder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = FAISSVectorStore(index_path=f"{temp_dir}/index", dimension=3)
            docs = [
                VectorDocument(
                    id="doc1",
                    content="python backend",
                    vector=[1.0, 0.0, 0.0],
                    metadata={"source": "doc1.txt"},
                    created_at="2024-01-01T00:00:00",
                    updated_at="2024-01-01T00:00:00",
                )
            ]
            store.add_documents(docs, normalize_vectors=False)

            embedder = Mock()
            embedder.embed_single_sync.return_value = [1.0, 0.0, 0.0]

            results = store.search_by_text("python", embedder=embedder, k=1)
            assert len(results) == 1
            assert results[0].document.id == "doc1"
