# Quickstart

This repository is currently standardized around one public path: `PortfolioAgent`.

## 1. Install

From a fresh clone:

```bash
poetry install
```

Or install the package directly:

```bash
pip install portfolio-agent
```

## 2. Build an Agent

```python
from portfolio_agent import PortfolioAgent

agent = PortfolioAgent.from_settings()
```

By default the SDK uses:
- Hugging Face embeddings
- local FAISS indexing
- the built-in persona-grounded RAG pipeline

## 3. Ingest Content

### Raw text

```python
agent.add_text(
    "Jane builds Python APIs and retrieval systems.",
    source="profile.txt",
    document_type="txt",
)
```

### Local file

```python
agent.add_file("sample_docs/portfolio.txt")
```

### GitHub repo or website

```python
agent.add_github_repository("https://github.com/example/project")
agent.add_website("https://example.com")
```

## 4. Query

```python
result = agent.query("What does Jane specialize in?")

print(result.response)
print(result.sources)
```

## 5. Run the HTTP Wrapper

```python
from portfolio_agent import create_app

app = create_app(agent=agent)
```

Supported endpoints:
- `GET /api/v1/health`
- `POST /api/v1/query`
- `POST /api/v1/documents`
- `POST /api/v1/documents/file`

## 6. Use the CLI

```bash
portfolio-agent --add-file sample_docs/portfolio.txt --query "Summarize the portfolio"
portfolio-agent --interactive
portfolio-agent --serve
```

## 7. Verify Manually

Fastest smoke check:

```bash
python scripts/manual_e2e.py --mode smoke
```

Configured runtime check:

```bash
python scripts/manual_e2e.py --mode settings
```

See [MANUAL_E2E.md](MANUAL_E2E.md) for the full SDK, CLI, and API walkthrough.

## 8. Run The Benchmark

Fast deterministic benchmark:

```bash
python scripts/run_evaluation.py --mode smoke
```

Configured-runtime benchmark:

```bash
python scripts/run_evaluation.py --mode settings
```

See [EVALUATION.md](EVALUATION.md) for benchmark scope, metrics, and caveats.
