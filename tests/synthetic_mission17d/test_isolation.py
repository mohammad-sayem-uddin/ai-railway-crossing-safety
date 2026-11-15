"""Verify this selected suite does not import production entrypoints or do IO."""

import builtins
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

_REAL_POPEN = subprocess.Popen


def _assert_fresh_interpreter_has_no_production_imports() -> None:
    """Check import isolation in a fresh interpreter, not pytest's shared process.

    The selected synthetic tests deliberately run with an IO-denying fixture.  A
    same-process ``sys.modules`` assertion is order-dependent when the complete
    repository suite is run, so the security property is checked in a child that
    starts with an empty module graph.  The real ``Popen`` is captured before the
    fixture installs its denial hook.
    """
    code = (
        "import importlib, sys; "
        "mods = ("
        "'railway_detection.synthetic',"
        "'railway_detection.synthetic.convention_b',"
        "'railway_detection.synthetic.grouped_cv',"
        "'railway_detection.experiments.provenance_registry',"
        "'tests.synthetic_mission17d.conftest',"
        "'tests.synthetic_mission17d.test_convention_b',"
        "'tests.synthetic_mission17d.test_grouped_cv',"
        "'tests.synthetic_mission17d.test_mission17f_regressions',"
        "'tests.synthetic_mission17d.test_mission17g_hardening'"
        "); "
        "[importlib.import_module(m) for m in mods]; "
        "names = ("
        "'railway_detection.cli.main','railway_detection.simulation.runner',"
        "'railway_detection.data.split','torch','cv2','ultralytics'); "
        "leaked = [name for name in names if name in sys.modules]; "
        "sys.stderr.write(','.join(leaked)) if leaked else None; "
        "sys.exit(1 if leaked else 0)"
    )
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = os.pathsep.join(("src", ".", env.get("PYTHONPATH", "")))
    proc = _REAL_POPEN([sys.executable, "-B", "-c", code], env=env)
    assert proc.wait(timeout=15) == 0


def test_production_modules_and_model_decoders_not_imported():
    _assert_fresh_interpreter_has_no_production_imports()


@pytest.mark.parametrize("attempt", [
    lambda: builtins.open("/synthetic-denied", "rb"),
    lambda: Path("/synthetic-denied").read_bytes(),
    lambda: Path("/synthetic-denied").write_text("never written"),
    lambda: socket.socket(),
    lambda: subprocess.Popen(["synthetic-never-spawned"]),
])
def test_fixture_guard_denies_file_network_and_process_calls(attempt):
    with pytest.raises(AssertionError, match="attempted file/network/process IO"):
        attempt()
