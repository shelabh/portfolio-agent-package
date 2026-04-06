from pathlib import Path

import pytest

from portfolio_agent.evaluation import run_benchmark


BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "benchmarks" / "canonical_portfolio" / "benchmark.json"


def test_canonical_benchmark_smoke_passes():
    pytest.importorskip("faiss", reason="FAISS is required for the benchmark smoke test")
    run = run_benchmark(BENCHMARK_PATH, mode="smoke")

    assert run.summary["failed_cases"] == []
    assert run.summary["overall_pass_rate"] == 1.0
    assert run.summary["source_recall_rate"] == 1.0
    assert run.summary["grounded_rate"] == 1.0
    assert run.summary["source_transparency_rate"] == 1.0
