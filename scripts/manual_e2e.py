#!/usr/bin/env python3
"""Manual end-to-end verification helper for the supported SDK path."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable, List

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from portfolio_agent import PortfolioAgent, create_app
from portfolio_agent.config import settings
from portfolio_agent.vector_stores import FAISSVectorStore


class SmokeTestEmbedder:
    """Deterministic embedder for fast offline smoke verification."""

    KEYWORDS = [
        "python",
        "fastapi",
        "retrieval",
        "langgraph",
        "react",
        "node",
        "aws",
        "docker",
        "kubernetes",
        "machine learning",
    ]

    def embed_texts_sync(self, texts: Iterable[str]):
        return SimpleNamespace(embeddings=[self.embed_single_sync(text) for text in texts])

    def embed_single_sync(self, text: str) -> List[float]:
        lowered = text.lower()
        return [1.0 if keyword in lowered else 0.0 for keyword in self.KEYWORDS]

    def get_embedding_dimension(self) -> int:
        return len(self.KEYWORDS)


def build_agent(mode: str, index_path: Path) -> PortfolioAgent:
    if mode == "settings":
        print("Using PortfolioAgent.from_settings() with the configured embedding provider.")
        return PortfolioAgent.from_settings(index_path=str(index_path))

    print("Using deterministic smoke-test embedder for fast offline verification.")
    embedder = SmokeTestEmbedder()
    vector_store = FAISSVectorStore(
        index_path=str(index_path),
        dimension=embedder.get_embedding_dimension(),
        index_type=settings.FAISS_INDEX_TYPE,
        metric=settings.FAISS_METRIC,
    )
    return PortfolioAgent(embedder=embedder, vector_store=vector_store)


def verify_sdk_flow(agent: PortfolioAgent, sample_file: Path) -> None:
    print("\n[SDK] Indexing inline text...")
    agent.add_text(
        "Jane builds Python APIs with FastAPI and retrieval systems.",
        source="manual-inline.txt",
        document_type="txt",
    )

    print(f"[SDK] Indexing file: {sample_file}")
    agent.add_file(str(sample_file))

    result = agent.query("What Python and FastAPI work is indexed?", session_id="manual-sdk")
    print("[SDK] Response:", result.response)
    print("[SDK] Sources:", json.dumps(result.sources, indent=2))

    if not result.sources:
        raise SystemExit("SDK verification failed: expected grounded sources in the response.")


def verify_api_flow(agent: PortfolioAgent, sample_file: Path) -> None:
    print("\n[API] Exercising SDK-backed HTTP wrapper with TestClient...")
    app = create_app(agent=agent)

    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        if health.status_code != 200:
            raise SystemExit(f"Health endpoint failed with {health.status_code}: {health.text}")

        raw_doc = client.post(
            "/api/v1/documents",
            json={
                "content": "Jane also mentors teams on backend architecture and retrieval systems.",
                "document_type": "txt",
                "source": "api-note.txt",
            },
        )
        if raw_doc.status_code != 200:
            raise SystemExit(f"Raw document ingestion failed: {raw_doc.status_code} {raw_doc.text}")

        with sample_file.open("rb") as handle:
            uploaded = client.post(
                "/api/v1/documents/file",
                files={"file": (sample_file.name, handle, "text/plain")},
            )
        if uploaded.status_code != 200:
            raise SystemExit(f"File upload failed: {uploaded.status_code} {uploaded.text}")

        query = client.post(
            "/api/v1/query",
            json={
                "query": "What backend and retrieval work has been indexed?",
                "session_id": "manual-api",
                "include_sources": True,
            },
        )
        if query.status_code != 200:
            raise SystemExit(f"Query failed: {query.status_code} {query.text}")

        payload = query.json()
        print("[API] Response:", payload["response"])
        print("[API] Sources:", json.dumps(payload["sources"], indent=2))
        if not payload["sources"]:
            raise SystemExit("API verification failed: expected grounded sources in the response.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manual E2E verifier for the supported PortfolioAgent path")
    parser.add_argument(
        "--mode",
        choices=["smoke", "settings"],
        default="smoke",
        help="Use 'smoke' for a fast offline check or 'settings' for the configured runtime.",
    )
    parser.add_argument(
        "--sample-file",
        default=str(REPO_ROOT / "sample_docs" / "portfolio.txt"),
        help="Sample file to ingest during verification.",
    )
    args = parser.parse_args()

    sample_file = Path(args.sample_file).resolve()
    if not sample_file.exists():
        raise SystemExit(f"Sample file not found: {sample_file}")

    print("portfolio-agent manual verification")
    print(f"Mode: {args.mode}")
    print(f"Sample file: {sample_file}")

    with tempfile.TemporaryDirectory(prefix="portfolio-agent-manual-") as tmp_dir:
        index_path = Path(tmp_dir) / "manual_e2e_index"
        print(f"Using temporary FAISS index: {index_path}")

        agent = build_agent(args.mode, index_path)
        verify_sdk_flow(agent, sample_file)
        verify_api_flow(agent, sample_file)

    print("\nVerification completed successfully.")
    print("For an actual server run, start: portfolio-agent --add-file sample_docs/portfolio.txt --serve")


if __name__ == "__main__":
    main()
