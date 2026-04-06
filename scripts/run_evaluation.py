#!/usr/bin/env python3
"""Run the canonical benchmark against the supported PortfolioAgent path."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from portfolio_agent.evaluation import format_run_summary, run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the canonical portfolio-agent benchmark")
    parser.add_argument(
        "--mode",
        choices=["smoke", "settings"],
        default="smoke",
        help="Use deterministic offline embeddings (`smoke`) or the configured runtime (`settings`).",
    )
    parser.add_argument(
        "--benchmark",
        default=str(REPO_ROOT / "benchmarks" / "canonical_portfolio" / "benchmark.json"),
        help="Path to the benchmark definition JSON file.",
    )
    parser.add_argument(
        "--output",
        help="Optional path to write the full benchmark results as JSON.",
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with status 1 if any benchmark case fails.",
    )
    args = parser.parse_args()

    run = run_benchmark(args.benchmark, mode=args.mode)
    print(format_run_summary(run))

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(run.to_dict(), indent=2), encoding="utf-8")
        print(f"\nWrote evaluation report to {output_path}")

    if args.fail_on_regression and run.summary["failed_cases"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
