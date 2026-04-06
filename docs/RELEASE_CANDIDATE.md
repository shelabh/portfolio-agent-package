# Release Candidate Flow

This document is the final pre-publish handoff for `portfolio-agent`.

Current release candidate target: `0.3.0rc1`

It is intentionally written for a narrow `0.x` release:
- one canonical SDK surface
- one supported ingest -> index -> query path
- one benchmark/regression story
- one dry-run release process

## 1. Choose The Version

For a first public candidate, keep the release small and explicit.

Update:
- `pyproject.toml`
- `CHANGELOG.md`

The changelog should describe:
- what changed
- what is supported
- what is intentionally still evolving

## 2. Run The Release Candidate Checks

Primary dry run:

```bash
python scripts/release_check.py
```

This validates:
- smoke manual E2E
- smoke benchmark
- full test suite
- package build
- wheel install verification
- sdist archive inspection

Optional heavier runtime validation:

```bash
python scripts/release_check.py --include-settings
```

Optional stronger sdist check:

```bash
python scripts/verify_artifact_install.py --artifact sdist --install-sdist
```

## 3. Review The Outputs

Review:
- `release-benchmark-smoke.json`
- `dist/portfolio_agent-<version>-py3-none-any.whl`
- `dist/portfolio_agent-<version>.tar.gz`

What to confirm:
- benchmark has no failed cases
- artifact version matches the intended release version
- wheel metadata looks correct
- changelog entry matches the package version

## 4. Know What Is Proven Locally

Locally validated:
- source-tree behavior on the canonical path
- smoke benchmark regression behavior
- build success
- built wheel usability
- sdist archive completeness

Not fully proven until a real upload/install path:
- package index rendering on PyPI
- dependency resolution in a truly fresh online environment
- final install experience for every downstream system

## 5. Publish Handoff

After this checklist is complete, the next step is intentionally simple:

1. decide the final version string
2. commit the version/changelog updates
3. create the tag for the release candidate or release
4. publish manually using your chosen package/release workflow

If anything in the release candidate run feels ambiguous, prefer delaying the publish and tightening the docs or validation first.
