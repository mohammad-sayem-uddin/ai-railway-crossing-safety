"""Constructed metadata only; isolate from root conftest and production CLI.

Run with --confcutdir=tests/synthetic_mission18a, plugin autoload disabled and
cache/bytecode writes disabled. The IO guard below is test isolation, not a
production sandbox or authorization mechanism.
"""

import builtins
import io
import os
import socket
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def no_component_io(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("synthetic component attempted file/network/process IO")

    for owner, name in [
        (builtins, "open"),
        (io, "open"),
        (os, "open"),
        (Path, "open"),
        (Path, "read_bytes"),
        (Path, "read_text"),
        (Path, "write_bytes"),
        (Path, "write_text"),
        (socket, "socket"),
        (socket, "create_connection"),
        (subprocess, "Popen"),
    ]:
        monkeypatch.setattr(owner, name, denied)
