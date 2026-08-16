"""Reproducibility utilities: run manifests and experiment registry."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def generate_run_id() -> str:
    return uuid.uuid4().hex[:12]


def git_revision(project_root: Path | None = None) -> str | None:
    """Return the current git commit hash, or None if unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root or Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def capture_environment() -> dict[str, Any]:
    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "os": platform.system(),
        "machine": platform.machine(),
        "executable": sys.executable,
    }


def build_run_manifest(
    *,
    command: str,
    config: dict[str, Any] | None = None,
    project_root: Path | None = None,
    run_id: str | None = None,
    output_dir: str | Path | None = None,
    seed: int | None = None,
    dataset_identity: str | None = None,
    mock_data: bool = False,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "run_id": run_id or generate_run_id(),
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "command": command,
        "environment": capture_environment(),
        "git_commit": git_revision(project_root),
        "seed": seed,
        "dataset_identity": dataset_identity,
        "mock_data": mock_data,
        "output_dir": str(output_dir) if output_dir is not None else None,
        "config": config,
    }
    if extra:
        manifest.update(extra)
    return manifest


def write_run_manifest(manifest: dict[str, Any], output_dir: str | Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def append_registry_record(record: dict[str, Any], registry_path: str | Path) -> Path:
    registry_path = Path(registry_path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with registry_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return registry_path
