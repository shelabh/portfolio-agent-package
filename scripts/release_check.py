#!/usr/bin/env python3
"""Release validation helper for the supported PortfolioAgent path."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Step:
    name: str
    command: List[str]
    optional: bool = False
    env: Optional[Dict[str, str]] = None


def run_step(step: Step) -> None:
    print(f"\n[{step.name}]")
    print(" ".join(step.command))
    completed = subprocess.run(
        step.command,
        cwd=REPO_ROOT,
        env={**step.env} if step.env else None,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the minimum release validation flow for portfolio-agent.")
    parser.add_argument(
        "--include-settings",
        action="store_true",
        help="Also run the heavier settings-based validation steps.",
    )
    args = parser.parse_args()

    python = sys.executable
    steps = [
        Step("Smoke E2E", [python, "scripts/manual_e2e.py", "--mode", "smoke"]),
        Step(
            "Smoke Benchmark",
            [python, "scripts/run_evaluation.py", "--mode", "smoke", "--fail-on-regression", "--output", "release-benchmark-smoke.json"],
        ),
        Step("Test Suite", ["pytest", "-q"]),
        Step("Build", ["poetry", "build"]),
        Step(
            "Artifact Verification",
            [
                python,
                "scripts/verify_artifact_install.py",
                "--artifact",
                "both",
                "--report",
                "release-artifact-verification.json",
            ],
        ),
    ]

    optional_steps = [
        Step("Settings E2E", [python, "scripts/manual_e2e.py", "--mode", "settings"], optional=True),
        Step(
            "Settings Benchmark",
            [python, "scripts/run_evaluation.py", "--mode", "settings", "--fail-on-regression", "--output", "release-benchmark-settings.json"],
            optional=True,
        ),
    ]

    print("portfolio-agent release validation")
    print("Required steps:")
    for step in steps:
        print(f"- {step.name}")
    print("Optional settings-based steps:")
    for step in optional_steps:
        print(f"- {step.name}")

    for step in steps:
        run_step(step)

    if args.include_settings:
        for step in optional_steps:
            run_step(step)
    else:
        print("\n[Optional steps skipped]")
        print("Run `python scripts/release_check.py --include-settings` in a clean environment to validate the configured local embedding runtime.")

    print("\nRelease validation completed successfully.")


if __name__ == "__main__":
    main()
