"""Verify this selected suite does not import production entrypoints or do IO."""

import builtins
import socket
import subprocess
import sys
from pathlib import Path

import pytest


def test_production_modules_and_model_decoders_not_imported():
    for module in ("railway_detection.cli.main", "railway_detection.simulation.runner",
                   "railway_detection.data.split", "torch", "cv2", "ultralytics"):
        assert module not in sys.modules


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
