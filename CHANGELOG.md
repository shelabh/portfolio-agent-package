# Changelog

This project follows a pragmatic `0.x` versioning approach.

During `0.x` releases:
- the canonical SDK-first product direction is expected to remain stable
- package internals and supporting heuristics may still evolve quickly
- release notes should prefer truthfulness over completeness

## 0.3.0rc1 - 2026-04-06

First public release candidate for the narrowed SDK-first package.

Highlights:
- standardized public surface around `PortfolioAgent`
- canonical ingest -> index -> query workflow
- smoke and settings-based manual E2E validation paths
- lightweight benchmark for retrieval, grounding, abstention, and source transparency
- release checklist, release-candidate handoff docs, and dry-run release validation flow
- built-wheel verification plus source-distribution archive inspection

Notable scope boundaries:
- local FAISS is the supported vector store path
- the FastAPI layer is a thin wrapper, not a broader platform surface
- benchmark coverage is intentionally small and regression-focused
- legacy modules remain isolated and unsupported

Known acceptable limitations for this release candidate:
- settings-based validation is heavier and still optional in routine local runs
- the default local validation path proves wheel usability, not a full online dependency-resolution install
- sdist is archive-verified by default; real sdist install remains an explicit extra check
