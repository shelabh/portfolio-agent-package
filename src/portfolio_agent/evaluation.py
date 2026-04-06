"""
Lightweight evaluation harness for the supported PortfolioAgent SDK path.

This module is intentionally small and repo-aligned. It measures retrieval,
grounding, abstention, and source transparency on a curated benchmark without
introducing a larger evaluation framework.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional

from .agents import RetrievalRequest, RerankingRequest, RerankingStrategy
from .config import settings
from .sdk import PortfolioAgent
from .text_matching import extract_terms
from .vector_stores import FAISSVectorStore
ABSTENTION_MARKERS = (
    "don't have enough source-backed information",
    "limited support in the indexed sources",
    "may be incomplete",
    "can't answer that confidently",
)


@dataclass
class BenchmarkDocument:
    source: str
    content: Optional[str] = None
    path: Optional[Path] = None
    document_type: str = "txt"
    ingest_via: str = "text"


@dataclass
class BenchmarkCase:
    id: str
    query: str
    expected_sources: List[str]
    required_term_groups: List[List[str]]
    expect_abstention: bool = False


@dataclass
class BenchmarkDefinition:
    name: str
    description: str
    documents: List[BenchmarkDocument]
    cases: List[BenchmarkCase]
    root: Path


@dataclass
class BenchmarkCaseResult:
    case_id: str
    query: str
    answer: str
    retrieved_sources: List[str]
    reranked_sources: List[str]
    answer_sources: List[str]
    expected_sources: List[str]
    evidence_strength: str
    source_recall_pass: bool
    grounded_pass: bool
    abstention_pass: bool
    source_transparency_pass: bool
    overall_pass: bool


@dataclass
class BenchmarkRun:
    benchmark: str
    mode: str
    summary: Dict[str, Any]
    cases: List[BenchmarkCaseResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "benchmark": self.benchmark,
            "mode": self.mode,
            "summary": self.summary,
            "cases": [asdict(case) for case in self.cases],
        }


class BenchmarkEmbedder:
    """Deterministic bag-of-words embedder for repeatable offline evaluation."""

    def __init__(self, vocabulary: List[str]):
        self.vocabulary = vocabulary
        self.index = {term: i for i, term in enumerate(vocabulary)}

    @classmethod
    def from_benchmark(cls, benchmark: BenchmarkDefinition) -> "BenchmarkEmbedder":
        terms = set()
        for document in benchmark.documents:
            terms.update(_tokenize(document.content))
        for case in benchmark.cases:
            terms.update(_tokenize(case.query))
            for group in case.required_term_groups:
                for term in group:
                    terms.update(_tokenize(term))
        vocabulary = sorted(terms)
        return cls(vocabulary)

    def embed_texts_sync(self, texts: Iterable[str]):
        return SimpleNamespace(embeddings=[self.embed_single_sync(text) for text in texts])

    def embed_single_sync(self, text: str) -> List[float]:
        counts = [0.0] * len(self.vocabulary)
        for term in _tokenize(text):
            idx = self.index.get(term)
            if idx is not None:
                counts[idx] += 1.0
        return counts

    def get_embedding_dimension(self) -> int:
        return len(self.vocabulary)


def load_benchmark(path: str | Path) -> BenchmarkDefinition:
    benchmark_path = Path(path).resolve()
    data = json.loads(benchmark_path.read_text(encoding="utf-8"))
    root = benchmark_path.parent

    documents = [
        BenchmarkDocument(
            source=item["source"],
            content=(root / item["path"]).read_text(encoding="utf-8").strip(),
            path=(root / item["path"]).resolve(),
            document_type=item.get("document_type", "txt"),
            ingest_via=item.get("ingest_via", "text"),
        )
        for item in data["documents"]
    ]
    cases = [
        BenchmarkCase(
            id=item["id"],
            query=item["query"],
            expected_sources=item.get("expected_sources", []),
            required_term_groups=item.get("required_term_groups", []),
            expect_abstention=item.get("expect_abstention", False),
        )
        for item in data["cases"]
    ]
    return BenchmarkDefinition(
        name=data["name"],
        description=data["description"],
        documents=documents,
        cases=cases,
        root=root,
    )


def run_benchmark(
    benchmark_path: str | Path,
    *,
    mode: str = "smoke",
    index_path: Optional[str] = None,
) -> BenchmarkRun:
    benchmark = load_benchmark(benchmark_path)

    if index_path is not None:
        agent = _build_agent(mode, benchmark, Path(index_path))
        return _run_cases(agent, benchmark, mode)

    with tempfile.TemporaryDirectory(prefix="portfolio-agent-benchmark-") as tmp_dir:
        agent = _build_agent(mode, benchmark, Path(tmp_dir) / "benchmark_index")
        return _run_cases(agent, benchmark, mode)


def format_run_summary(run: BenchmarkRun) -> str:
    summary = run.summary
    lines = [
        f"benchmark: {run.benchmark}",
        f"mode: {run.mode}",
        f"overall_pass_rate: {summary['overall_pass_rate']:.2f}",
        f"source_recall_rate: {summary['source_recall_rate']:.2f}",
        f"grounded_rate: {summary['grounded_rate']:.2f}",
        f"abstention_rate: {summary['abstention_rate']:.2f}",
        f"source_transparency_rate: {summary['source_transparency_rate']:.2f}",
        "",
        "cases:",
    ]
    for case in run.cases:
        lines.append(
            f"- {case.case_id}: overall={case.overall_pass} "
            f"retrieval={case.source_recall_pass} grounded={case.grounded_pass} "
            f"abstention={case.abstention_pass} transparency={case.source_transparency_pass}"
        )
        lines.append(f"  expected={case.expected_sources or '[]'}")
        lines.append(f"  retrieved={case.reranked_sources or case.answer_sources or []}")
        lines.append(f"  evidence_strength={case.evidence_strength}")
    return "\n".join(lines)


def _build_agent(mode: str, benchmark: BenchmarkDefinition, index_path: Path) -> PortfolioAgent:
    if mode == "settings":
        return PortfolioAgent.from_settings(index_path=str(index_path))

    embedder = BenchmarkEmbedder.from_benchmark(benchmark)
    vector_store = FAISSVectorStore(
        index_path=str(index_path),
        dimension=embedder.get_embedding_dimension(),
        index_type=settings.FAISS_INDEX_TYPE,
        metric=settings.FAISS_METRIC,
    )
    return PortfolioAgent(embedder=embedder, vector_store=vector_store)


def _run_cases(agent: PortfolioAgent, benchmark: BenchmarkDefinition, mode: str) -> BenchmarkRun:
    for document in benchmark.documents:
        if document.ingest_via == "file":
            if document.path is None:
                raise ValueError(f"Benchmark document `{document.source}` is missing a file path")
            agent.add_file(str(document.path), redact_pii=False)
            continue

        agent.add_text(
            document.content or "",
            source=document.source,
            document_type=document.document_type,
            redact_pii=False,
        )

    results: List[BenchmarkCaseResult] = []
    for case in benchmark.cases:
        retrieval = agent.retriever_agent.retrieve_documents(
            RetrievalRequest(query=case.query, k=settings.TOP_K_RETRIEVAL, include_metadata=True)
        )
        reranked = agent.reranker_agent.rerank_documents(
            RerankingRequest(
                documents=retrieval.documents,
                query=case.query,
                strategy=RerankingStrategy.HYBRID,
                max_results=min(settings.TOP_K_RERANK, settings.TOP_K_RETRIEVAL),
            )
        )
        response = agent.query(case.query, session_id=f"benchmark-{case.id}", include_sources=True)

        retrieved_sources = _source_labels(retrieval.documents)
        reranked_sources = _source_labels(reranked.documents)
        answer_sources = [
            _normalize_source_label(source.get("source") or source.get("id", ""))
            for source in response.sources
        ]
        answer_lower = response.response.lower()
        evidence_strength = response.metadata.get("response_metadata", {}).get("evidence_strength", "none")

        source_recall_pass = _expected_sources_present(case.expected_sources, reranked_sources or answer_sources)
        grounded_pass = _grounded_pass(case, answer_lower, evidence_strength, answer_sources)
        abstention_pass = _abstention_pass(case, answer_lower, evidence_strength, answer_sources)
        source_transparency_pass = _source_transparency_pass(case, response.response, answer_sources)
        overall_pass = all(
            [
                source_recall_pass,
                grounded_pass,
                abstention_pass,
                source_transparency_pass,
            ]
        )

        results.append(
            BenchmarkCaseResult(
                case_id=case.id,
                query=case.query,
                answer=response.response,
                retrieved_sources=retrieved_sources,
                reranked_sources=reranked_sources,
                answer_sources=answer_sources,
                expected_sources=case.expected_sources,
                evidence_strength=evidence_strength,
                source_recall_pass=source_recall_pass,
                grounded_pass=grounded_pass,
                abstention_pass=abstention_pass,
                source_transparency_pass=source_transparency_pass,
                overall_pass=overall_pass,
            )
        )

    summary = _summarize(results)
    return BenchmarkRun(benchmark=benchmark.name, mode=mode, summary=summary, cases=results)


def _source_labels(documents: List[Dict[str, Any]]) -> List[str]:
    labels: List[str] = []
    for doc in documents:
        metadata = doc.get("metadata", {})
        label = _normalize_source_label(metadata.get("source") or doc.get("id", ""))
        if label and label not in labels:
            labels.append(label)
    return labels


def _expected_sources_present(expected_sources: List[str], actual_sources: List[str]) -> bool:
    if not expected_sources:
        return True
    actual = set(actual_sources)
    return set(expected_sources).issubset(actual)


def _grounded_pass(
    case: BenchmarkCase,
    answer_lower: str,
    evidence_strength: str,
    answer_sources: List[str],
) -> bool:
    if case.expect_abstention:
        return evidence_strength in {"none", "weak"}
    if not _expected_sources_present(case.expected_sources, answer_sources):
        return False
    if evidence_strength not in {"moderate", "strong"}:
        return False
    for group in case.required_term_groups:
        if not any(term.lower() in answer_lower for term in group):
            return False
    return True


def _abstention_pass(
    case: BenchmarkCase,
    answer_lower: str,
    evidence_strength: str,
    answer_sources: List[str],
) -> bool:
    if not case.expect_abstention:
        return True
    if answer_sources:
        return False
    if evidence_strength not in {"none", "weak"}:
        return False
    return any(marker in answer_lower for marker in ABSTENTION_MARKERS)


def _source_transparency_pass(case: BenchmarkCase, answer: str, answer_sources: List[str]) -> bool:
    if case.expect_abstention:
        return not answer_sources
    if not answer_sources:
        return False

    answer_lower = answer.lower()
    expected_labels = case.expected_sources or answer_sources
    return any(label.lower() in answer_lower for label in expected_labels)


def _summarize(results: List[BenchmarkCaseResult]) -> Dict[str, Any]:
    total = len(results)
    supported = [case for case in results if case.expected_sources]
    abstention_cases = [case for case in results if not case.expected_sources]
    return {
        "total_cases": total,
        "supported_cases": len(supported),
        "abstention_cases": len(abstention_cases),
        "overall_pass_rate": _rate(sum(case.overall_pass for case in results), total),
        "source_recall_rate": _rate(sum(case.source_recall_pass for case in supported), len(supported)),
        "grounded_rate": _rate(sum(case.grounded_pass for case in supported), len(supported)),
        "abstention_rate": _rate(sum(case.abstention_pass for case in abstention_cases), len(abstention_cases)),
        "source_transparency_rate": _rate(
            sum(case.source_transparency_pass for case in supported),
            len(supported),
        ),
        "failed_cases": [case.case_id for case in results if not case.overall_pass],
    }


def _rate(passed: int, total: int) -> float:
    if total <= 0:
        return 1.0
    return passed / total


def _normalize_source_label(label: str) -> str:
    if not label:
        return ""
    return Path(label).name or label


def _tokenize(text: str) -> List[str]:
    return extract_terms(text)
