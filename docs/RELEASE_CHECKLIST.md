# Release Checklist

Use this checklist before tagging a public version.

Current release candidate target: `0.3.0rc1`

## Minimum Release Gate

Run:

```bash
python scripts/release_check.py
```

This currently validates:
- smoke manual E2E
- smoke benchmark with fail-on-regression
- full test suite
- package build
- install-from-built-wheel verification
- source distribution archive inspection

Artifact verification uses a temporary virtual environment with available site packages so it can validate the built package without requiring network access during the dry run.

## Optional Clean-Environment Settings Validation

If you want confidence in the configured local embedding runtime from a fresh environment, run:

```bash
python scripts/release_check.py --include-settings
```

This adds:
- settings-based manual E2E
- settings-based benchmark

Because the settings path can require model download/cache setup, it is intentionally treated as heavier and optional for routine iteration.

## Review Checklist

- README still reflects the supported SDK-first scope
- `docs/MANUAL_E2E.md` and `docs/EVALUATION.md` still match the real commands
- benchmark output is inspectable and no cases regressed
- built wheel and sdist install successfully via `scripts/verify_artifact_install.py`
- no new public API was introduced accidentally
- no legacy module was moved back into the supported surface
- version number and changelog/tag notes are updated if needed

## Dry-Run Release Flow

1. Update version and `CHANGELOG.md`.
2. Run `python scripts/release_check.py`.
3. Inspect `release-benchmark-smoke.json`.
4. Inspect the artifact verification summary if you wrote one with `scripts/verify_artifact_install.py --report ...`.
5. Confirm `dist/` contains a wheel and sdist for the expected version.
6. If you want extra confidence in sdist installation itself, run `python scripts/verify_artifact_install.py --artifact sdist --install-sdist` in an environment where the build backend is available.
7. If you want extra confidence in the configured local embedding runtime, run `python scripts/release_check.py --include-settings`.

For the full maintainer handoff, see [RELEASE_CANDIDATE.md](RELEASE_CANDIDATE.md).

## Benchmark Artifacts

The release validation script writes:
- `release-benchmark-smoke.json`
- `release-benchmark-settings.json` when `--include-settings` is used

Review these if you want the full per-case output rather than the console summary.

## Current Truthful Public Claim

This repo is ready to be described as:

"A Python toolkit for turning documents, repositories, and web content into a citable, persona-aware assistant, with a small built-in benchmark for retrieval and grounding regressions."

It is not yet reasonable to claim:
- broad production evaluation coverage
- universal RAG quality guarantees
- exhaustive file-format benchmarking
