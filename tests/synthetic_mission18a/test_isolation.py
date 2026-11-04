import builtins
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from railway_detection.synthetic.convention_b_pipeline import run_pipeline


def test_no_model_decoder_cli_or_split_imports():
    for name in (
        "torch",
        "cv2",
        "ultralytics",
        "railway_detection.cli.main",
        "railway_detection.data.split",
    ):
        assert name not in sys.modules


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
