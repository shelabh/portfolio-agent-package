import os
import subprocess
import sys
from pathlib import Path

import pytest


RUN_SETTINGS_RUNTIME_INTEGRATION = os.getenv("PORTFOLIO_AGENT_RUN_SETTINGS_INTEGRATION") == "1"
REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.integration
@pytest.mark.skipif(
    not RUN_SETTINGS_RUNTIME_INTEGRATION,
    reason="Set PORTFOLIO_AGENT_RUN_SETTINGS_INTEGRATION=1 to run the real settings-based runtime check.",
)
def test_settings_runtime_manual_e2e():
    env = os.environ.copy()
    env.setdefault("EMBEDDING_PROVIDER", "hf")
    env.setdefault("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    result = subprocess.run(
        [sys.executable, "scripts/manual_e2e.py", "--mode", "settings"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
    )

    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
