"""Validate restored local tool, including a deliberately rejected type defect."""

import importlib.metadata
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "package,expected",
    [
        ("mypy", "2.4.0"),
        ("mypy_extensions", "1.1.0"),
        ("typing_extensions", "4.16.0"),
        ("librt", "0.16.0"),
        ("ast_serialize", "0.13.0"),
        ("pathspec", "1.1.1"),
    ],
)
def test_exact_locked_tool_packages_have_complete_metadata(package, expected):
    distribution = importlib.metadata.distribution(package)
    assert distribution.version == expected
    assert distribution.metadata["Metadata-Version"]
    assert (package + "==" + expected) in (ROOT / "requirements.lock").read_text()


def test_typecheck_accepts_valid_code_and_rejects_real_defect(tmp_path):
    base = [
        sys.executable,
        "-m",
        "mypy",
        "--config-file",
        str(ROOT / "pyproject.toml"),
        "--no-incremental",
        "--cache-dir",
        str(tmp_path / "cache"),
    ]
    positive_source = tmp_path / "valid.py"
    positive_source.write_text("value: int = 1\n")
    positive = subprocess.run(base + [str(positive_source)], capture_output=True, text=True)
    assert positive.returncode == 0, positive.stdout + positive.stderr
    negative_source = tmp_path / "invalid.py"
    negative_source.write_text('value: int = "wrong"\n')
    negative = subprocess.run(base + [str(negative_source)], capture_output=True, text=True)
    assert negative.returncode == 1
    assert "[assignment]" in negative.stdout and "incompatible type" in negative.stdout.lower()


def test_cli_and_module_share_the_active_interpreter():
    module = subprocess.check_output([sys.executable, "-m", "mypy", "--version"], text=True)
    cli = subprocess.check_output([str(ROOT / ".venv/bin/mypy"), "--version"], text=True)
    assert module == cli and module.startswith("mypy 2.4.0")
