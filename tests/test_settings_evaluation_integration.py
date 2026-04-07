import os
import subprocess
import sys
from pathlib import Path

import pytest


RUN_SETTINGS_EVALUATION = os.getenv("PORTFOLIO_AGENT_RUN_SETTINGS_EVALUATION") == "1"
REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.integration
@pytest.mark.skipif(
    not RUN_SETTINGS_EVALUATION,
    reason="Set PORTFOLIO_AGENT_RUN_SETTINGS_EVALUATION=1 to run the settings-based benchmark check.",
)
def test_settings_runtime_benchmark():
    env = os.environ.copy()
    env.setdefault("EMBEDDING_PROVIDER", "hf")
    env.setdefault("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    result = subprocess.run(
        [sys.executable, "scripts/run_evaluation.py", "--mode", "settings", "--fail-on-regression"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=1200,
    )

    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
