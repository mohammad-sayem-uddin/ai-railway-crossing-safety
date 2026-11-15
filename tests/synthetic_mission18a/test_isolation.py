import builtins
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from railway_detection.synthetic.convention_b_pipeline import run_pipeline

_REAL_POPEN = subprocess.Popen


def _assert_fresh_interpreter_has_no_production_imports() -> None:
    """Check the no-import contract in a clean child process after loading mission18a modules."""
    code = (
        "import importlib, sys; "
        "mods = ("
        "'railway_detection.synthetic',"
        "'railway_detection.synthetic.convention_b',"
        "'railway_detection.synthetic.convention_b_pipeline',"
        "'railway_detection.synthetic.integration_contracts',"
        "'railway_detection.synthetic.integration_fixture',"
        "'railway_detection.synthetic.integration_workflow',"
        "'tests.synthetic_mission18a.conftest',"
        "'tests.synthetic_mission18a.test_convention_b_integration'"
        "); "
        "[importlib.import_module(m) for m in mods]; "
        "names = ("
        "'torch','cv2','ultralytics','railway_detection.cli.main',"
        "'railway_detection.data.split'); "
        "leaked = [name for name in names if name in sys.modules]; "
        "sys.stderr.write(','.join(leaked)) if leaked else None; "
        "sys.exit(1 if leaked else 0)"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(("src", ".", env.get("PYTHONPATH", "")))
    proc = _REAL_POPEN([sys.executable, "-c", code], env=env)
    assert proc.wait(timeout=10) == 0


def test_no_model_decoder_cli_or_split_imports():
    _assert_fresh_interpreter_has_no_production_imports()


@pytest.mark.parametrize(
    "attempt",
    [
        lambda: builtins.open("/never", "rb"),
        lambda: Path("/never").read_bytes(),
        lambda: socket.socket(),
        lambda: subprocess.Popen(["never"]),
    ],
)
def test_isolation_guards(attempt):
    with pytest.raises(AssertionError, match="attempted file/network/process IO"):
        attempt()


def test_ordinary_frames_cannot_enter_pipeline():
    with pytest.raises(ValueError, match="constructed integration request"):
        run_pipeline([])
