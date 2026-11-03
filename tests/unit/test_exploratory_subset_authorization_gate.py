"""Regression test for the exploratory dual-camera subset's execution gating.

Covers Task 5's authorization requirements: both the config file's own
`authorized_for_execution` flag AND an explicit CLI opt-in must be true
before `scripts/run_exploratory_dual_camera_subset.py` will execute
anything. Imports the actual script as a module rather than re-implementing
its logic, so this test tracks the real gate, not a description of it.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_exploratory_dual_camera_subset.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("run_exploratory_dual_camera_subset", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def script_module():
    return _load_script_module()


def test_both_flags_false_blocks(script_module) -> None:
    cfg = {"exploratory_metadata": {"authorized_for_execution": False}}
    with pytest.raises(PermissionError):
        script_module.gate_check_authorization(cfg, cli_authorized=False)


def test_config_true_cli_false_blocks(script_module) -> None:
    cfg = {"exploratory_metadata": {"authorized_for_execution": True}}
    with pytest.raises(PermissionError):
        script_module.gate_check_authorization(cfg, cli_authorized=False)


def test_config_false_cli_true_blocks(script_module) -> None:
    cfg = {"exploratory_metadata": {"authorized_for_execution": False}}
    with pytest.raises(PermissionError):
        script_module.gate_check_authorization(cfg, cli_authorized=True)


def test_both_true_passes(script_module) -> None:
    cfg = {"exploratory_metadata": {"authorized_for_execution": True}}
    script_module.gate_check_authorization(cfg, cli_authorized=True)  # must not raise


def test_shipped_config_is_not_authorized_by_default(script_module) -> None:
    """The actual, committed exploratory config file must ship with
    authorized_for_execution: false. If this test ever fails, someone
    flipped the flag -- that is a deliberate human act this test exists to
    make visible, not something to silently accept."""
    import yaml

    cfg = yaml.safe_load(script_module.EXPLORATORY_CONFIG_PATH.read_text(encoding="utf-8"))
    assert cfg["exploratory_metadata"]["authorized_for_execution"] is False


def test_dry_run_validates_all_eleven_events_against_live_manifest(script_module) -> None:
    """End-to-end dry-run against the REAL, committed candidate manifest and
    REAL source media hashes -- no inference, no model, no video decode."""
    cfg = script_module.yaml.safe_load(script_module.EXPLORATORY_CONFIG_PATH.read_text(encoding="utf-8"))
    validated = script_module.validate_all_included_events(cfg)
    assert len(validated) == 11
    for event_key, v in validated.items():
        assert v.verdict == "CALIBRATION_SUPPORTED"
