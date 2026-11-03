"""Registry path injection and tracked-artifact isolation.

Guards the defect where CLI tests appended mock records to the tracked
``results/experiment_registry.jsonl`` research artifact.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from railway_detection.cli.main import (
    DEFAULT_EXPERIMENT_REGISTRY,
    EXPERIMENT_REGISTRY_ENV,
    resolve_registry_path,
)
from railway_detection.config.exceptions import ConfigError


def test_default_registry_path_is_the_tracked_research_artifact(monkeypatch):
    monkeypatch.delenv(EXPERIMENT_REGISTRY_ENV, raising=False)
    assert resolve_registry_path() == DEFAULT_EXPERIMENT_REGISTRY
    assert DEFAULT_EXPERIMENT_REGISTRY == Path("results/experiment_registry.jsonl")


def test_explicit_override_wins_over_environment(monkeypatch, tmp_path):
    monkeypatch.setenv(EXPERIMENT_REGISTRY_ENV, str(tmp_path / "from_env.jsonl"))
    explicit = tmp_path / "explicit.jsonl"
    assert resolve_registry_path(explicit) == explicit


def test_environment_override_is_used_when_no_explicit_path(monkeypatch, tmp_path):
    target = tmp_path / "from_env.jsonl"
    monkeypatch.setenv(EXPERIMENT_REGISTRY_ENV, str(target))
    assert resolve_registry_path() == target


def test_empty_environment_override_fails_closed(monkeypatch):
    monkeypatch.setenv(EXPERIMENT_REGISTRY_ENV, "   ")
    with pytest.raises(ConfigError, match=EXPERIMENT_REGISTRY_ENV):
        resolve_registry_path()


def test_empty_explicit_override_fails_closed(monkeypatch):
    monkeypatch.delenv(EXPERIMENT_REGISTRY_ENV, raising=False)
    with pytest.raises(ConfigError, match="registry path override is empty"):
        resolve_registry_path("")


def test_autouse_fixture_redirects_registry_away_from_tracked_file(
    isolated_experiment_registry,
):
    """The session-wide fixture must not resolve to the tracked artifact."""
    resolved = resolve_registry_path()
    assert resolved == isolated_experiment_registry
    assert resolved != DEFAULT_EXPERIMENT_REGISTRY


def test_records_land_in_the_redirected_registry(isolated_experiment_registry):
    from railway_detection.utils.reproducibility import append_registry_record

    append_registry_record({"command": "unit test", "mock_data": True}, resolve_registry_path())
    lines = isolated_experiment_registry.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["mock_data"] is True
