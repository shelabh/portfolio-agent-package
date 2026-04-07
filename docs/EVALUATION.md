# Evaluation

This repository includes a small, version-controlled benchmark for the supported SDK path:

`PortfolioAgent` -> ingest -> FAISS index -> query

The benchmark is intentionally small. It is meant to catch regressions in the canonical product flow, not to claim broad model-quality coverage.

## What The Benchmark Covers

- retrieval of expected source documents for portfolio/profile-style questions
- grounded answer behavior for supported questions
- abstention behavior for unsupported questions
- source-label transparency in the generated answer
- one synthesis case that expects evidence from multiple documents

## What It Does Not Cover

- broad semantic QA quality across many domains
- latency or throughput benchmarking
- cost benchmarking
- real-world evaluation of every embedding model
- website or GitHub ingestion quality
- long-conversation memory quality

## Benchmark Data

The current benchmark lives in:

- `benchmarks/canonical_portfolio/benchmark.json`
- `benchmarks/canonical_portfolio/documents/`

It includes:
- profile knowledge
- project/toolkit knowledge
- experience/mentoring knowledge
- collaboration/product knowledge
- markdown file ingestion coverage
- unsupported question coverage

PDF support exists in the SDK file-ingestion path, but PDF is not part of the core benchmark yet.
That omission is intentional: the current release benchmark is optimized for small, readable, version-controlled fixtures and low-friction regression review.
PDF should only be added to the core benchmark once a stable, trustworthy fixture and parsing expectations are curated.

## Run The Benchmark

Fast deterministic evaluation:

```bash
python scripts/run_evaluation.py --mode smoke
```

Fail the command if any case regresses:

```bash
python scripts/run_evaluation.py --mode smoke --fail-on-regression
```

Write a JSON report:

```bash
python scripts/run_evaluation.py --mode smoke --output benchmark-report.json
```

## Run Against The Real Configured Runtime

If your environment can load the configured embedding runtime:

```bash
python scripts/run_evaluation.py --mode settings
```

Optional automated settings-based benchmark check:

```bash
PORTFOLIO_AGENT_RUN_SETTINGS_EVALUATION=1 pytest -q tests/test_settings_evaluation_integration.py
```

## Reading The Metrics

- `overall_pass_rate`: all checks across all benchmark cases
- `source_recall_rate`: supported cases where expected source documents are present in the reranked/used evidence
- `grounded_rate`: supported cases where the answer reflects expected evidence terms and the pipeline reports moderate/strong evidence
- `abstention_rate`: unsupported cases where the system avoids overclaiming and reports weak/no evidence
- `source_transparency_rate`: supported cases where source labels remain visible in the answer

## Truthful Quality Claims

Reasonable claims from this benchmark:
- the canonical SDK path has a repeatable regression check for retrieval, groundedness, abstention, and source labels
- the project can be evaluated locally without external services in smoke mode
- the settings-based path can be benchmarked explicitly when the environment supports it

Claims this benchmark does not justify:
- state-of-the-art RAG quality
- universal portfolio/document QA accuracy
- production-grade evaluation coverage across all ingestion types and corpora
