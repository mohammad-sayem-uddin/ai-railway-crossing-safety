"""Global test isolation for tracked research artifacts.

The CLI appends run records to ``results/experiment_registry.jsonl``, which is a
tracked research artifact. Earlier CLI test runs leaked mock records with pytest
tmpdir paths into it. These fixtures redirect the registry for every test and
fail the session if the tracked registry is mutated anyway.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from railway_detection.cli.main import EXPERIMENT_REGISTRY_ENV

REPO_ROOT = Path(__file__).resolve().parents[1]
TRACKED_REGISTRY = REPO_ROOT / "results" / "experiment_registry.jsonl"


def _registry_fingerprint() -> str | None:
    """Return a content hash for the tracked registry, or None if absent."""
    if not TRACKED_REGISTRY.exists():
        return None
    return hashlib.sha256(TRACKED_REGISTRY.read_bytes()).hexdigest()


@pytest.fixture(autouse=True)
def isolated_experiment_registry(tmp_path, monkeypatch):
    """Point every test's registry writes at a per-test temporary file."""
    redirect = tmp_path / "experiment_registry.jsonl"
    monkeypatch.setenv(EXPERIMENT_REGISTRY_ENV, str(redirect))
    yield redirect


@pytest.fixture(scope="session", autouse=True)
def _guard_tracked_registry():
    """Fail the session if the tracked experiment registry changed during tests."""
    before = _registry_fingerprint()
    yield
    after = _registry_fingerprint()
    if before != after:
        raise AssertionError(
            "tests mutated the tracked experiment registry "
            f"{TRACKED_REGISTRY}: {before} -> {after}. "
            f"Pass --registry-path or set {EXPERIMENT_REGISTRY_ENV}."
        )


def pytest_report_header() -> str:
    """Make the registry redirect visible in test output."""
    env = os.environ.get(EXPERIMENT_REGISTRY_ENV)
    return f"experiment registry redirect: {env or 'per-test tmp_path (autouse)'}"
