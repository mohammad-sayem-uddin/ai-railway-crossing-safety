import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "source_snapshot",
    Path(__file__).resolve().parents[2] / "scripts/prepare_researcher_snapshot.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture(tmp_path):
    root = tmp_path / "project"
    (root / "src").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "src/example.py").write_text("VALUE = 1\n")
    (root / "docs/note.md").write_text("# Local fixture\n")
    return root


def test_deterministic_explicit_source_only_with_protected_enumeration_tripwire(
    tmp_path, monkeypatch
):
    root = fixture(tmp_path)

    def denied(*args, **kwargs):
        raise AssertionError("tree enumeration is forbidden")

    monkeypatch.setattr(Path, "iterdir", denied)
    monkeypatch.setattr(Path, "rglob", denied)
    p = ("src/example.py", "docs/note.md")
    first = module.build_source_snapshot(root, p, code_identity="a" * 40)
    assert first == module.build_source_snapshot(root, p[::-1], code_identity="a" * 40)
    out = tmp_path / "snapshot"
    r = module.write_source_snapshot(root, p, destination=out, code_identity="a" * 40)
    assert r["files"] == 2
    assert (
        json.loads((out / "SOURCE_MANIFEST.json").read_text())["protected_resources_included"]
        is False
    )
    assert (out / "src/example.py").read_text() == "VALUE = 1\n"
    with pytest.raises(module.SnapshotError, match="DESTINATION_EXISTS"):
        module.write_source_snapshot(root, p, destination=out, code_identity="a" * 40)


@pytest.mark.parametrize(
    "path",
    [
        "data/raw/a.json",
        "data/processed/a.txt",
        "experiments/c.txt",
        "models/a.py",
        "results/cache/a.json",
        "docs/cache/a.json",
        "src/model.pt",
        "../a.py",
        "/tmp/a.py",
        "src/./a.py",
        "src//a.py",
        "src/../a.py",
        "src/a\n.py",
        "src\\a.py",
    ],
)
def test_denial_precedes_stat_read_or_enumeration(path, monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("denied path must never reach filesystem")

    monkeypatch.setattr(Path, "is_symlink", denied)
    monkeypatch.setattr(Path, "stat", denied)
    with pytest.raises(module.SnapshotError, match="SOURCE_PATH_REFUSED"):
        module.build_source_snapshot(Path("/unopened"), (path,), code_identity="a" * 40)


def test_symlink_directory_and_binary_disguised_as_text(tmp_path):
    root = fixture(tmp_path)
    (root / "docs/link.md").symlink_to(root / "docs/note.md")
    with pytest.raises(module.SnapshotError, match="SYMLINK"):
        module.build_source_snapshot(root, ("docs/link.md",), code_identity="a" * 40)
    (root / "src/binary.py").write_bytes(b"\xff\x00")
    with pytest.raises(module.SnapshotError, match="NOT_UTF8"):
        module.build_source_snapshot(root, ("src/binary.py",), code_identity="a" * 40)
    with pytest.raises(module.SnapshotError, match="INSIDE_PROJECT"):
        module.write_source_snapshot(
            root, ("src/example.py",), destination=root / "docs/snapshot", code_identity="a" * 40
        )


def test_input_selection_identity_and_changed_worktree(tmp_path):
    root = fixture(tmp_path)
    paths = ("src/example.py",)
    before, _ = module.build_source_snapshot(root, paths, code_identity="a" * 40)
    (root / "src/example.py").write_text("VALUE = 2\n")
    after, _ = module.build_source_snapshot(root, paths, code_identity="a" * 40)
    assert before != after
    for selection, code in [((), "a" * 40), (paths * 2, "a" * 40), (paths, "HEAD")]:
        with pytest.raises(module.SnapshotError):
            module.build_source_snapshot(root, selection, code_identity=code)


def test_nul_payload_refused(tmp_path):
    root = fixture(tmp_path)
    (root / "src/disguised.py").write_bytes(b"ASCII\x00binary")
    with pytest.raises(module.SnapshotError, match="NOT_TEXT"):
        module.build_source_snapshot(root, ("src/disguised.py",), code_identity="a" * 40)
