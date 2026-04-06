from unittest.mock import Mock

from fastapi.testclient import TestClient

from portfolio_agent import PortfolioAgent, create_app
from portfolio_agent.vector_stores import FAISSVectorStore


class FakeEmbedder:
    def embed_texts_sync(self, texts):
        return Mock(embeddings=[self.embed_single_sync(text) for text in texts])

    def embed_single_sync(self, text):
        text = text.lower()
        return [
            1.0 if "python" in text else 0.0,
            1.0 if "fastapi" in text else 0.0,
            1.0 if "retrieval" in text else 0.0,
            1.0 if "backend" in text else 0.0,
        ]

    def get_embedding_dimension(self):
        return 4


def build_client(tmp_path):
    vector_store = FAISSVectorStore(index_path=str(tmp_path / "api_index"), dimension=4)
    agent = PortfolioAgent(embedder=FakeEmbedder(), vector_store=vector_store)
    app = create_app(agent=agent)
    return TestClient(app)


def test_health_endpoint_reports_ready(tmp_path):
    with build_client(tmp_path) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"


def test_documents_and_query_round_trip(tmp_path):
    with build_client(tmp_path) as client:
        ingest = client.post(
            "/api/v1/documents",
            json={
                "content": "Jane builds Python APIs with FastAPI and retrieval systems.",
                "document_type": "txt",
                "source": "inline.txt",
            },
        )
        assert ingest.status_code == 200

        query = client.post(
            "/api/v1/query",
            json={
                "query": "What Python and FastAPI work is indexed?",
                "session_id": "api-test",
                "include_sources": True,
            },
        )

    assert query.status_code == 200
    payload = query.json()
    assert payload["sources"]
    assert "Python" in payload["response"] or "FastAPI" in payload["response"]


def test_file_upload_and_query_round_trip(tmp_path):
    sample_file = tmp_path / "profile.txt"
    sample_file.write_text("Jane works on backend retrieval systems with Python and FastAPI.")

    with build_client(tmp_path) as client:
        with sample_file.open("rb") as handle:
            upload = client.post(
                "/api/v1/documents/file",
                files={"file": ("profile.txt", handle, "text/plain")},
            )
        assert upload.status_code == 200

        query = client.post(
            "/api/v1/query",
            json={
                "query": "What backend retrieval work is indexed?",
                "session_id": "api-file-test",
            },
        )

    assert query.status_code == 200
    payload = query.json()
    assert payload["sources"]
