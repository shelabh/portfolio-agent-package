#!/usr/bin/env python3
"""Verify that built distribution artifacts are usable and reviewable.

Wheel validation performs a real install into a temporary virtual environment.
sdist validation inspects archive contents by default and can optionally attempt
an actual install when the build backend is available.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import tarfile
import zipfile
from pathlib import Path
from email.parser import Parser

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "dist"

SMOKE_CHECK = r"""
from pathlib import Path
from types import SimpleNamespace
import tempfile

from portfolio_agent import PortfolioAgent, create_app
from portfolio_agent.vector_stores import FAISSVectorStore

class ArtifactSmokeEmbedder:
    KEYWORDS = ["python", "fastapi", "retrieval", "backend"]

    def embed_texts_sync(self, texts):
        return SimpleNamespace(embeddings=[self.embed_single_sync(text) for text in texts])

    def embed_single_sync(self, text):
        lowered = text.lower()
        return [1.0 if keyword in lowered else 0.0 for keyword in self.KEYWORDS]

    def get_embedding_dimension(self):
        return len(self.KEYWORDS)

with tempfile.TemporaryDirectory(prefix="portfolio-agent-artifact-") as tmp_dir:
    index_path = Path(tmp_dir) / "artifact_index"
    embedder = ArtifactSmokeEmbedder()
    vector_store = FAISSVectorStore(index_path=str(index_path), dimension=embedder.get_embedding_dimension())
    agent = PortfolioAgent(embedder=embedder, vector_store=vector_store)
    agent.add_text(
        "Jane builds Python APIs with FastAPI and retrieval systems.",
        source="artifact.txt",
        document_type="txt",
        redact_pii=False,
    )
    result = agent.query("What Python and FastAPI work is indexed?", session_id="artifact")
    assert result.sources, "expected sources from installed artifact smoke check"
    assert "Python" in result.response or "FastAPI" in result.response
    app = create_app(agent=agent)
    assert app is not None

print("artifact-import-sdk-cli-ok")
"""


def latest_artifact(pattern: str) -> Path:
    matches = sorted(DIST_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No artifact found for pattern: {pattern}. Run `poetry build` first.")
    return matches[-1]


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    completed = subprocess.run(cmd, cwd=REPO_ROOT, env=env, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def inspect_wheel_metadata(artifact: Path) -> dict[str, object]:
    with zipfile.ZipFile(artifact) as archive:
        metadata_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        entry_points_name = next(name for name in archive.namelist() if name.endswith(".dist-info/entry_points.txt"))
        metadata = Parser().parsestr(archive.read(metadata_name).decode("utf-8", "ignore"))
        entry_points = archive.read(entry_points_name).decode("utf-8", "ignore")

    project_urls = metadata.get_all("Project-URL", [])
    summary = {
        "name": metadata.get("Name"),
        "version": metadata.get("Version"),
        "summary": metadata.get("Summary"),
        "requires_python": metadata.get("Requires-Python"),
        "license": metadata.get("License"),
        "project_urls": project_urls,
        "has_console_script": "portfolio-agent=portfolio_agent.cli:main" in entry_points,
    }

    required_fields = {
        "name": summary["name"] == "portfolio-agent",
        "version": bool(summary["version"]),
        "summary": bool(summary["summary"]),
        "requires_python": summary["requires_python"] == ">=3.12,<3.14",
        "license": summary["license"] == "Apache-2.0",
        "project_urls": len(project_urls) >= 3,
        "console_script": summary["has_console_script"],
    }
    summary["checks"] = required_fields
    summary["passed"] = all(required_fields.values())
    return summary


def verify_wheel_install(artifact: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="portfolio-agent-artifact-install-") as tmp_dir:
        venv_dir = Path(tmp_dir) / "venv"
        run([sys.executable, "-m", "venv", "--system-site-packages", str(venv_dir)])

        bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
        python = bin_dir / "python"
        cli = bin_dir / "portfolio-agent"

        install_cmd = [str(python), "-m", "pip", "install", "--no-deps", "--force-reinstall", str(artifact)]
        run(install_cmd)

        run([str(python), "-c", "from portfolio_agent import PortfolioAgent, create_app; print('import-ok')"])
        run([str(python), "-c", SMOKE_CHECK])
        run([str(cli), "--help"])

    return {
        "artifact": artifact.name,
        "venv_mode": "temporary-system-site-packages",
        "install_verified": True,
        "import_verified": True,
        "sdk_smoke_verified": True,
        "cli_help_verified": True,
    }


def inspect_sdist(artifact: Path) -> dict[str, object]:
    expected_entries = {
        "LICENSE",
        "README.md",
        "CHANGELOG.md",
        "pyproject.toml",
        "src/portfolio_agent/__init__.py",
        "src/portfolio_agent/sdk.py",
        "src/portfolio_agent/cli.py",
    }
    with tarfile.open(artifact, "r:gz") as archive:
        names = set(archive.getnames())
        root_prefix = f"{artifact.stem.replace('.tar', '')}/"
        missing = [
            entry for entry in expected_entries
            if f"{root_prefix}{entry}" not in names
        ]
    if missing:
        raise SystemExit(f"sdist inspection failed, missing entries: {missing}")
    return {
        "artifact": artifact.name,
        "archive_inspected": True,
        "expected_entries_verified": sorted(expected_entries),
        "install_verified": False,
    }


def verify_sdist_install(artifact: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="portfolio-agent-sdist-install-") as tmp_dir:
        venv_dir = Path(tmp_dir) / "venv"
        run([sys.executable, "-m", "venv", "--system-site-packages", str(venv_dir)])

        bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
        python = bin_dir / "python"
        cli = bin_dir / "portfolio-agent"

        run([str(python), "-m", "pip", "install", "--no-deps", "--force-reinstall", "--no-build-isolation", str(artifact)])
        run([str(python), "-c", "from portfolio_agent import PortfolioAgent, create_app; print('import-ok')"])
        run([str(python), "-c", SMOKE_CHECK])
        run([str(cli), "--help"])
    return {
        "artifact": artifact.name,
        "venv_mode": "temporary-system-site-packages",
        "install_verified": True,
        "import_verified": True,
        "sdk_smoke_verified": True,
        "cli_help_verified": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify installation from built portfolio-agent artifacts.")
    parser.add_argument(
        "--artifact",
        choices=["wheel", "sdist", "both"],
        default="both",
        help="Which built artifact(s) to verify.",
    )
    parser.add_argument(
        "--install-sdist",
        action="store_true",
        help="Attempt a real sdist install in addition to archive inspection. Requires `poetry-core` to be available to pip.",
    )
    parser.add_argument(
        "--report",
        help="Optional path to write a JSON verification report.",
    )
    args = parser.parse_args()

    report: dict[str, object] = {
        "mode": "offline-local-artifact-verification",
        "notes": [
            "Wheel install is verified in a temporary virtual environment that can see locally available site packages.",
            "sdist is inspected by default and may be install-verified explicitly with --install-sdist.",
            "This is a pre-publish confidence check, not a simulation of an online package index upload or resolver run.",
        ],
    }

    print("portfolio-agent artifact verification")
    if args.artifact in {"wheel", "both"}:
        wheel = latest_artifact("*.whl")
        print(f"- verifying wheel install: {wheel.name}")
        report["wheel_metadata"] = inspect_wheel_metadata(wheel)
        if not report["wheel_metadata"]["passed"]:
            raise SystemExit("wheel metadata inspection failed")
        report["wheel_install"] = verify_wheel_install(wheel)

    if args.artifact in {"sdist", "both"}:
        sdist = latest_artifact("*.tar.gz")
        print(f"- inspecting sdist: {sdist.name}")
        report["sdist_archive"] = inspect_sdist(sdist)
        if args.install_sdist:
            print(f"- verifying sdist install: {sdist.name}")
            report["sdist_install"] = verify_sdist_install(sdist)
        else:
            print("- skipped real sdist install; use --install-sdist when the build backend is available.")
            report["sdist_install"] = {
                "artifact": sdist.name,
                "install_verified": False,
                "skipped": True,
                "reason": "real sdist install requires the build backend to be available to pip",
            }

    if args.report:
        report_path = Path(args.report)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"- wrote verification report: {report_path}")

    print("Artifact verification completed successfully.")


if __name__ == "__main__":
    main()
