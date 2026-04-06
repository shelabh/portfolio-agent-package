# Manual E2E Verification

This repository supports one canonical path:

`PortfolioAgent` -> ingest -> FAISS index -> query -> optional FastAPI wrapper

Use this guide when validating a fresh clone manually.

## 1. Install From Source

```bash
poetry install
```

If you prefer not to use Poetry:

```bash
pip install -e .
```

## 2. Optional Environment File

For the supported local path, copy the example file:

```bash
cp env.example .env
```

The default configuration uses:
- local Hugging Face embeddings
- local FAISS indexes
- no external database requirement

Recommended real-runtime prerequisites:
- `sentence-transformers`
- `torch`
- network access on the first run if the model is not already cached locally

## 3. Fastest Smoke Test

For a quick offline verification of the SDK and API mechanics, run:

```bash
python scripts/manual_e2e.py --mode smoke
```

This uses a deterministic local smoke embedder so you can verify:
- SDK ingestion
- file ingestion
- grounded querying with sources
- API document ingestion
- API querying

Expected result:
- the script exits successfully
- it prints SDK and API responses
- each response includes at least one source

## 4. Real Local-Embedding Verification

To test the actual default runtime path:

```bash
python scripts/manual_e2e.py --mode settings
```

Notes:
- the first run may download the configured Hugging Face model
- model startup is slower than the smoke path
- `PortfolioAgent.from_settings()` now fails fast with a clearer error if the embedding runtime is unavailable or the FAISS index path points to an incompatible old index
- if you prefer OpenAI embeddings, set `EMBEDDING_PROVIDER=openai` and `OPENAI_API_KEY`
- if local startup is failing, try `EMBEDDING_DEVICE=cpu`

## 5. Manual SDK Flow

```python
from portfolio_agent import PortfolioAgent

agent = PortfolioAgent.from_settings()
agent.add_text(
    "Jane builds Python APIs with FastAPI and retrieval systems.",
    source="inline.txt",
    document_type="txt",
)
agent.add_file("sample_docs/portfolio.txt")

result = agent.query("What Python and FastAPI work is indexed?")
print(result.response)
print(result.sources)
```

What to verify:
- the response mentions indexed content rather than generic filler
- `result.sources` is non-empty
- the listed sources include the ingested file or inline source
- the response text itself references source-backed evidence instead of purely generic phrasing

## 6. Manual CLI Flow

```bash
portfolio-agent --add-file sample_docs/portfolio.txt --query "What are the key skills?"
```

What to verify:
- the file is indexed successfully
- the response includes a `Sources:` section
- if the CLI fails during real runtime startup, the error should mention either embedding dependencies, model loading, or incompatible FAISS index files

## 7. Manual API Flow

Start the server:

```bash
portfolio-agent --add-file sample_docs/portfolio.txt --serve
```

In another terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What are the key skills?","session_id":"manual"}'
```

Optional raw-text ingestion via API:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -d '{
        "content":"Jane also works on retrieval systems and backend architecture.",
        "document_type":"txt",
        "source":"api-note.txt"
      }'
```

What to verify:
- `/api/v1/health` returns healthy after startup
- `/api/v1/query` returns a response with sources
- `/api/v1/documents` accepts raw text and affects later query results
- the response body reflects retrieved evidence rather than only generic assistant language

## 8. Optional Integration Test For The Real Runtime

If you want a real automated check for the settings-based path and your environment can download/load the configured model, run:

```bash
PORTFOLIO_AGENT_RUN_SETTINGS_INTEGRATION=1 pytest -q tests/test_settings_runtime_integration.py
```

This launches the real `python scripts/manual_e2e.py --mode settings` flow in a subprocess and is intentionally opt-in.

## 9. Troubleshooting

- If the smoke path works but `--mode settings` fails, the issue is likely the local embedding environment rather than the SDK/API contract.
- If Hugging Face model loading is too slow or fails on first run, retry after the model download completes or switch to OpenAI embeddings.
- If the error mentions an incompatible FAISS index, point `FAISS_INDEX_PATH` at a fresh location or remove the old index files.
- If responses are generic and sources are empty, verify that ingestion succeeded before querying.
- If you generated local index files during testing, they are ignored by `.gitignore`.

## 10. Benchmark The Canonical Path

For a repeatable retrieval/grounding benchmark on the supported SDK path:

```bash
python scripts/run_evaluation.py --mode smoke
```

If your environment supports the configured local embedding runtime:

```bash
python scripts/run_evaluation.py --mode settings
```

See [EVALUATION.md](EVALUATION.md) for benchmark scope and interpretation.
