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
    cli_failure = subprocess.run(
        [str(ROOT / ".venv/bin/mypy"), *base[3:], str(negative_source)],
        capture_output=True,
        text=True,
    )
    assert cli_failure.returncode == 1 and "[assignment]" in cli_failure.stdout
    assert "[assignment]" in negative.stdout and "incompatible type" in negative.stdout.lower()


def test_cli_and_module_share_the_active_interpreter():
    module = subprocess.check_output([sys.executable, "-m", "mypy", "--version"], text=True)
    cli = subprocess.check_output([str(ROOT / ".venv/bin/mypy"), "--version"], text=True)
    assert module == cli and module.startswith("mypy 2.4.0")


@pytest.mark.parametrize(
    "package",
    ["mypy", "mypy_extensions", "typing_extensions", "librt", "ast_serialize", "pathspec"],
)
def test_repaired_package_record_contains_no_missing_files(package):
    distribution = importlib.metadata.distribution(package)
    assert distribution.files, "RECORD must enumerate the repaired installation"
    missing = [
        str(file) for file in distribution.files if not distribution.locate_file(file).is_file()
    ]
    assert missing == []


def test_mypy_record_entrypoints_match_active_cli_hashes():
    import base64
    import hashlib

    distribution = importlib.metadata.distribution("mypy")
    entries = [file for file in distribution.files if "/bin/" in str(file)]
    assert {Path(file).name for file in entries} == {
        "mypy",
        "dmypy",
        "mypyc",
        "stubgen",
        "stubtest",
    }
    for file in entries:
        actual = distribution.locate_file(file).resolve()
        assert actual == ROOT / ".venv/bin" / Path(file).name
        digest = (
            base64.urlsafe_b64encode(hashlib.sha256(actual.read_bytes()).digest())
            .decode()
            .rstrip("=")
        )
        assert file.hash.mode == "sha256" and file.hash.value == digest
