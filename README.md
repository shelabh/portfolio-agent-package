# portfolio-agent

`portfolio-agent` is an open-source Python toolkit for turning a person's or team's documents, repositories, and web content into a citable, persona-aware assistant.

The repository is intentionally standardized around one supported path:
- ingest content with `PortfolioAgent`
- index it into the local `FAISSVectorStore`
- query it through the built-in persona-grounded `RAGPipeline`

## What Is Supported

- Python SDK via `PortfolioAgent`
- Local FAISS indexing
- File ingestion for text/markdown/html/json/pdf
- GitHub and website ingestion through the SDK
- Querying with citations and lightweight session memory
- Optional FastAPI wrapper via `create_app(...)`

## What Is Not the Supported Surface

- the old `build_graph()` entrypoint
- placeholder enterprise/platform claims
- legacy example scripts outside the portfolio demo
- unfinished HTTP endpoints for streaming, batch orchestration, admin, or security tooling

## Public Release Scope

This repository is preparing for a narrow, truthful first public tag.

Release-ready expectations:
- install from source or package
- run the smoke/manual path
- run the smoke benchmark
- inspect source-backed answers and benchmark output

Not promised in this release:
- broad production guarantees
- exhaustive benchmark coverage for every ingestion format
- automatic validation of every optional runtime in every environment

## Installation

When published as a package:

```bash
pip install portfolio-agent
```

From a fresh clone:

```bash
poetry install
```

From a locally built artifact:

```bash
poetry build
pip install dist/portfolio_agent-*.whl
```

For local embeddings, the package defaults to Hugging Face sentence-transformers. The first run may download the configured model.

## Manual Verification

The fastest supported end-to-end check from a fresh clone is:

```bash
python scripts/manual_e2e.py --mode smoke
```

For the actual configured runtime path:

```bash
python scripts/manual_e2e.py --mode settings
```

See [docs/MANUAL_E2E.md](docs/MANUAL_E2E.md) for the full SDK, CLI, and API verification flow.
If your environment can load the real local embedding runtime, you can also run the opt-in integration check documented there.

## Evaluation

The repo also includes a small benchmark for retrieval, grounding, abstention, and source-label quality on the canonical SDK path:

```bash
python scripts/run_evaluation.py --mode smoke
```

For the real configured runtime:

```bash
python scripts/run_evaluation.py --mode settings
```

See [docs/EVALUATION.md](docs/EVALUATION.md) for what the benchmark covers and what it does not.

## Release Validation

For a maintainer/reviewer release pass:

```bash
python scripts/release_check.py
```

For a heavier clean-environment review of the configured embedding runtime:

```bash
python scripts/release_check.py --include-settings
```

See [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md) for the minimum release gate and review notes.
The built-artifact dry run validates the wheel in a temporary virtual environment using available local site packages; it is meant to prove package usability, not to simulate a full online dependency-resolution install.
For the end-to-end maintainer handoff, see [docs/RELEASE_CANDIDATE.md](docs/RELEASE_CANDIDATE.md).

## Versioning

This project is currently using a pragmatic `0.x` release shape:
- the canonical `PortfolioAgent` SDK path is the supported contract
- internals and heuristics may still evolve between minor releases
- release notes and changelog entries should be read as the source of truth for what changed

Current release candidate: `0.3.0rc1`

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Quick Start

```python
from portfolio_agent import PortfolioAgent

agent = PortfolioAgent.from_settings()

agent.add_text(
    """
    Jane Doe is a backend engineer who works with Python, FastAPI, and retrieval systems.
    She has built developer tooling, API platforms, and AI product prototypes.
    """,
    source="profile.txt",
    document_type="txt",
)

result = agent.query("What does Jane work on?")
print(result.response)
print(result.sources)
```

### Ingest a File

```python
from portfolio_agent import PortfolioAgent

agent = PortfolioAgent.from_settings()
agent.add_file("sample_docs/portfolio.txt")

result = agent.query("Summarize the indexed portfolio")
print(result.response)
```

### Ingest a GitHub Repo or Website

```python
from portfolio_agent import PortfolioAgent

agent = PortfolioAgent.from_settings()
agent.add_github_repository("https://github.com/example/project")
agent.add_website("https://example.com")
```

## FastAPI App

```python
from portfolio_agent import PortfolioAgent, create_app

agent = PortfolioAgent.from_settings()
app = create_app(agent=agent)
```

Supported API endpoints:
- `GET /api/v1/health`
- `POST /api/v1/query`
- `POST /api/v1/documents`
- `POST /api/v1/documents/file`

## CLI

The package exposes a `portfolio-agent` CLI:

```bash
portfolio-agent --add-file sample_docs/portfolio.txt --query "What are the key skills?"
portfolio-agent --interactive
portfolio-agent --serve
```

If you are validating a fresh clone and want the quickest repeatable check, use `python scripts/manual_e2e.py --mode smoke` before using the heavier local-embedding runtime.

## Configuration

Key environment variables:

```bash
EMBEDDING_PROVIDER=hf
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=16
# EMBEDDING_DEVICE=cpu
FAISS_INDEX_PATH=./faiss_index
REDACT_PII=true
TOP_K_RETRIEVAL=5
```

If you want OpenAI embeddings instead of local embeddings:

```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=your-key
```

## Canonical Architecture

```text
Source -> Ingestor -> Chunker -> Embedder -> FAISSVectorStore
                                     |
Query -> RouterAgent -> RetrieverAgent -> RerankerAgent -> PersonaAgent -> Response
                                                             |
                                                        MemoryManager
```

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for a slightly more detailed walkthrough.
