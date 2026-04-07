import pytest
from unittest.mock import Mock

from portfolio_agent import PortfolioAgent
from portfolio_agent.vector_stores import FAISSVectorStore

pytest.importorskip("faiss", reason="FAISS is required for SDK vector store tests")


class FakeEmbedder:
    def embed_texts_sync(self, texts):
        return Mock(embeddings=[self.embed_single_sync(text) for text in texts])

    def embed_single_sync(self, text):
        text = text.lower()
        return [
            1.0 if "python" in text else 0.0,
            1.0 if "fastapi" in text else 0.0,
            1.0 if "ml" in text or "machine learning" in text else 0.0,
        ]

    def get_embedding_dimension(self):
        return 3


def test_sdk_ingest_and_query(tmp_path):
    vector_store = FAISSVectorStore(index_path=str(tmp_path / "sdk_index"), dimension=3)
    agent = PortfolioAgent(embedder=FakeEmbedder(), vector_store=vector_store)
    result = agent.add_text(
        "Jane builds Python APIs with FastAPI and works on machine learning systems.",
        source="profile.txt",
        document_type="txt",
    )

    assert result.chunks_created >= 1

    response = agent.query("What Python and FastAPI work has Jane done?", session_id="test")
    assert "Python" in response.response or "FastAPI" in response.response
    assert response.sources


def test_sdk_add_text_multiple_times_keeps_retrieval_stable(tmp_path):
    vector_store = FAISSVectorStore(index_path=str(tmp_path / "multi_index"), dimension=3)
    agent = PortfolioAgent(embedder=FakeEmbedder(), vector_store=vector_store)

    agent.add_text("Jane builds Python APIs.", source="first.txt", document_type="txt")
    agent.add_text("Jane works with FastAPI.", source="second.txt", document_type="txt")

    response = agent.query("What Python and FastAPI work is indexed?", session_id="multi")
    assert response.sources


def test_create_app_uses_supplied_agent(tmp_path):
    pytest.importorskip("fastapi", reason="FastAPI is required for API wrapper tests")
    from portfolio_agent.api.server import create_app

    vector_store = FAISSVectorStore(index_path=str(tmp_path / "app_index"), dimension=3)
    agent = PortfolioAgent(embedder=FakeEmbedder(), vector_store=vector_store)
    app = create_app(agent=agent)
    assert app.state.agent is agent
