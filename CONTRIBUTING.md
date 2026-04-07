# Contributing

This repository is intentionally narrow.

The supported public surface is:
- `PortfolioAgent`
- local FAISS indexing
- ingest -> index -> query
- the thin FastAPI wrapper exposed by `create_app(...)`

Before opening a PR, please make sure changes align with that contract.

## Local Setup

```bash
poetry install
```

## Fastest Validation

```bash
python scripts/manual_e2e.py --mode smoke
python scripts/run_evaluation.py --mode smoke --fail-on-regression
pytest -q
```

## Release-Oriented Validation

```bash
python scripts/release_check.py
```

Optional heavier validation for environments that can load the configured embedding runtime:

```bash
python scripts/release_check.py --include-settings
```

Artifact install verification:

```bash
python scripts/verify_artifact_install.py --artifact both
```

## Scope Guidance

Good contributions:
- clearer SDK behavior
- better ingest/index/query reliability
- benchmark improvements tied to the canonical path
- docs and release hygiene improvements

Out of scope for normal contributions:
- reviving legacy platform surfaces
- broad enterprise claims
- new backend matrices without a strong reason
- speculative agent/framework abstractions

## Benchmark Notes

The benchmark is intentionally small and regression-focused.
If you add a benchmark case, prefer:
- a realistic canonical use case
- a readable version-controlled fixture
- a clear reason the case would catch a regression

Do not add large synthetic benchmarks just to increase the case count.
