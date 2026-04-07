"""
Canonical SDK for portfolio-agent.

This module defines the supported public toolkit surface: ingest content into a
vector store and query it through the persona-grounded RAG pipeline.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from .agents import MemoryManager, PersonaAgent, PersonaType, RerankerAgent, RetrieverAgent, RouterAgent
from .config import settings
from .ingestion import GenericIngestor, GitHubIngestor, ResumeIngestor, TextChunker, WebsiteIngestor, pii_redactor
from .rag_pipeline import RAGPipeline, RAGRequest, RAGResponse
from .vector_stores import FAISSVectorStore

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Summary for a single ingestion/indexing operation."""

    document_id: str
    chunks_created: int
    source: str
    metadata: Dict[str, Any]


class PortfolioAgent:
    """Supported high-level SDK for ingesting and querying personal knowledge."""

    def __init__(
        self,
        *,
        embedder: Any,
        vector_store: Optional[FAISSVectorStore] = None,
        router_agent: Optional[RouterAgent] = None,
        reranker_agent: Optional[RerankerAgent] = None,
        persona_agent: Optional[PersonaAgent] = None,
        memory_manager: Optional[MemoryManager] = None,
    ):
        self.embedder = embedder
        self.vector_store = vector_store or FAISSVectorStore(
            index_path=settings.FAISS_INDEX_PATH,
            dimension=self._embedding_dimension(embedder),
            index_type=settings.FAISS_INDEX_TYPE,
            metric=settings.FAISS_METRIC,
        )
        self.router_agent = router_agent or RouterAgent()
        self.retriever_agent = RetrieverAgent(
            vector_store=self.vector_store,
            embedder=self.embedder,
            default_k=settings.TOP_K_RETRIEVAL,
            min_score_threshold=settings.SIMILARITY_THRESHOLD,
        )
        self.reranker_agent = reranker_agent or RerankerAgent()
        self.persona_agent = persona_agent or PersonaAgent()
        self.memory_manager = memory_manager or MemoryManager(
            max_turns=10,
            max_context_length=4000,
            persistence_enabled=False,
        )
        self.pipeline = RAGPipeline(
            router_agent=self.router_agent,
            retriever_agent=self.retriever_agent,
            reranker_agent=self.reranker_agent,
            persona_agent=self.persona_agent,
            memory_manager=self.memory_manager,
        )

    @classmethod
    def from_settings(cls, *, index_path: Optional[str] = None) -> "PortfolioAgent":
        """Construct the supported local toolkit from repo settings."""
        try:
            if settings.EMBEDDING_PROVIDER == "openai":
                from .embeddings import OpenAIEmbedder

                embedder = OpenAIEmbedder(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.EMBEDDING_MODEL,
                    batch_size=settings.EMBEDDING_BATCH_SIZE,
                )
            else:
                from .embeddings import HuggingFaceEmbedder

                embedder = HuggingFaceEmbedder(
                    model_name=settings.EMBEDDING_MODEL,
                    use_sentence_transformers=settings.HF_USE_SENTENCE_TRANSFORMERS,
                    device=settings.EMBEDDING_DEVICE,
                    batch_size=settings.EMBEDDING_BATCH_SIZE,
                )

            vector_store = FAISSVectorStore(
                index_path=index_path or settings.FAISS_INDEX_PATH,
                dimension=cls._embedding_dimension(embedder),
                index_type=settings.FAISS_INDEX_TYPE,
                metric=settings.FAISS_METRIC,
            )

            return cls(embedder=embedder, vector_store=vector_store)
        except Exception as exc:
            provider = settings.EMBEDDING_PROVIDER
            if provider == "hf":
                raise RuntimeError(
                    "Failed to initialize the default local embedding runtime. "
                    "Verify that the Hugging Face embedding dependencies are installed, that the model can be "
                    f"loaded (`{settings.EMBEDDING_MODEL}`), and that `FAISS_INDEX_PATH` does not point to an "
                    "incompatible old index. For a fast repository verification, run "
                    "`python scripts/manual_e2e.py --mode smoke`."
                ) from exc

            raise RuntimeError(
                "Failed to initialize the OpenAI embedding runtime. "
                "Verify `OPENAI_API_KEY`, `EMBEDDING_MODEL`, and `FAISS_INDEX_PATH`."
            ) from exc

    def add_text(
        self,
        content: str,
        *,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
        document_type: str = "text",
        redact_pii: Optional[bool] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> IngestionResult:
        """Chunk and index raw text into the configured vector store."""

        redact = settings.REDACT_PII if redact_pii is None else redact_pii
        processed_content = content
        pii_stats: Dict[str, int] = {}
        if redact:
            processed_content, pii_stats = pii_redactor.redact_pii(content)

        document_id = str(uuid.uuid4())
        chunker = TextChunker(
            chunk_size=chunk_size or settings.CHUNK_SIZE,
            chunk_overlap=chunk_overlap or settings.CHUNK_OVERLAP,
        )
        chunk_metadata = {
            "document_id": document_id,
            "source": source,
            "document_type": document_type,
            "pii_redacted": redact,
            "pii_redactions": sum(pii_stats.values()),
            **(metadata or {}),
        }
        chunks = chunker.chunk_text(processed_content, chunk_metadata)
        normalized_chunks = self._assign_document_id(chunks, document_id, source_label=source)
        self._index_chunks(normalized_chunks)
        self._save_index()

        return IngestionResult(
            document_id=document_id,
            chunks_created=len(normalized_chunks),
            source=source,
            metadata=chunk_metadata,
        )

    def add_file(self, file_path: str, *, redact_pii: Optional[bool] = None) -> IngestionResult:
        """Ingest and index a local file."""

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix.lower() == ".pdf":
            ingestor = ResumeIngestor(redact_pii=settings.REDACT_PII if redact_pii is None else redact_pii)
            chunks = ingestor.ingest(str(path))
        else:
            ingestor = GenericIngestor(max_file_size_mb=settings.MAX_FILE_SIZE_MB)
            chunks = ingestor.ingest(str(path), redact_pii=settings.REDACT_PII if redact_pii is None else redact_pii)
        document_id = str(uuid.uuid4())
        normalized_chunks = self._assign_document_id(
            chunks,
            document_id,
            source_label=path.name,
            source_path=str(path),
        )
        self._index_chunks(normalized_chunks)
        self._save_index()

        return IngestionResult(
            document_id=document_id,
            chunks_created=len(normalized_chunks),
            source=path.name,
            metadata={"source": path.name, "file_path": str(path), "document_type": path.suffix.lstrip(".")},
        )

    def add_github_repository(self, repo_url: str, *, redact_pii: Optional[bool] = None) -> IngestionResult:
        """Ingest and index repository content from GitHub."""

        ingestor = GitHubIngestor(max_files=50)
        chunks = ingestor.ingest(repo_url, redact_pii=settings.REDACT_PII if redact_pii is None else redact_pii)
        document_id = str(uuid.uuid4())
        normalized_chunks = self._assign_document_id(chunks, document_id, source_label=repo_url)
        self._index_chunks(normalized_chunks)
        self._save_index()

        return IngestionResult(
            document_id=document_id,
            chunks_created=len(normalized_chunks),
            source=repo_url,
            metadata={"source": repo_url, "document_type": "github"},
        )

    def add_website(self, url: str, *, redact_pii: Optional[bool] = None) -> IngestionResult:
        """Ingest and index public website content."""

        ingestor = WebsiteIngestor(max_pages=10, max_depth=2)
        chunks = ingestor.ingest(url, redact_pii=settings.REDACT_PII if redact_pii is None else redact_pii)
        document_id = str(uuid.uuid4())
        normalized_chunks = self._assign_document_id(chunks, document_id, source_label=url)
        self._index_chunks(normalized_chunks)
        self._save_index()

        return IngestionResult(
            document_id=document_id,
            chunks_created=len(normalized_chunks),
            source=url,
            metadata={"source": url, "document_type": "website"},
        )

    def add_source(self, source: str, *, redact_pii: Optional[bool] = None) -> IngestionResult:
        """Route a source to the appropriate supported ingestion path."""

        parsed = urlparse(source)
        if parsed.scheme in {"http", "https"}:
            if parsed.netloc == "github.com":
                return self.add_github_repository(source, redact_pii=redact_pii)
            return self.add_website(source, redact_pii=redact_pii)
        return self.add_file(source, redact_pii=redact_pii)

    def query(
        self,
        query: str,
        *,
        session_id: str = "default",
        persona_type: PersonaType = PersonaType.PROFESSIONAL,
        max_documents: Optional[int] = None,
        include_sources: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> RAGResponse:
        """Query the indexed corpus through the canonical pipeline."""

        request = RAGRequest(
            query=query,
            session_id=session_id,
            persona_type=persona_type,
            max_documents=max_documents or settings.TOP_K_RETRIEVAL,
            include_sources=include_sources,
            context=context,
        )
        return self.pipeline.process_query(request)

    def stats(self) -> Dict[str, Any]:
        """Return a small set of SDK/runtime stats."""

        return {
            "vector_store": self.vector_store.get_stats(),
            "pipeline": self.pipeline.get_pipeline_stats(),
        }

    def _index_chunks(self, chunks: Iterable[Dict[str, Any]]) -> None:
        chunk_list = list(chunks)
        if not chunk_list:
            return

        texts = [chunk["content"] for chunk in chunk_list]
        vectors = self._embed_texts(texts)
        metadatas = [chunk["metadata"] for chunk in chunk_list]
        ids = [chunk["id"] for chunk in chunk_list]
        self.vector_store.add_texts(texts=texts, vectors=vectors, metadatas=metadatas, ids=ids)

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        if hasattr(self.embedder, "embed_texts_sync"):
            result = self.embedder.embed_texts_sync(texts)
        else:
            result = self.embedder.embed_texts(texts)
            if inspect.isawaitable(result):
                try:
                    asyncio.get_running_loop()
                except RuntimeError:
                    result = asyncio.run(result)
                else:
                    raise RuntimeError(
                        "The configured embedder only exposes async APIs. "
                        "Use an embedder with a sync interface for the supported SDK path."
                    )

        return result.embeddings if hasattr(result, "embeddings") else result

    def _save_index(self) -> None:
        if hasattr(self.vector_store, "save"):
            self.vector_store.save()

    @staticmethod
    def _assign_document_id(
        chunks: List[Dict[str, Any]],
        document_id: str,
        *,
        source_label: Optional[str] = None,
        source_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for idx, chunk in enumerate(chunks):
            metadata = dict(chunk.get("metadata", {}))
            metadata["document_id"] = document_id
            if source_label:
                metadata["source"] = source_label
            if source_path:
                metadata["file_path"] = source_path
            normalized.append(
                {
                    "id": f"{document_id}_chunk_{idx}",
                    "content": chunk["content"],
                    "metadata": metadata,
                }
            )
        return normalized

    @staticmethod
    def _embedding_dimension(embedder: Any) -> int:
        if hasattr(embedder, "get_embedding_dimension"):
            return int(embedder.get_embedding_dimension())
        return settings.EMBEDDING_DIMENSION
