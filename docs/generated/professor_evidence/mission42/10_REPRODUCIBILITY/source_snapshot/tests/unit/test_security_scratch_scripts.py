"""Mission 14 (WP14.5): the git-ignored ``scratch/`` scripts that launch FFmpeg are guarded.

The scripts run work at import time (they open manifests, create folders, loop over events), so
they are *not* imported.  Instead:

* a static AST check proves every ``subprocess`` launch and every ``wave.open`` in ``scratch/`` is
  immediately preceded by the matching authorization call on the same command/path; and
* the real function bodies are extracted from the script source and executed in a namespace with a
  recording stand-in for ``subprocess`` -- proving the refusal happens before any launch.

Everything runs against a synthetic fake repository; no FFmpeg is ever started.
"""

from __future__ import annotations

import ast
import sys
import wave
from pathlib import Path
from typing import Any

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from security_support import make_fake_repo, outside_dir  # noqa: E402

from railway_detection.safety.media_guard import (  # noqa: E402
    MediaAccessAuthorizationError,
    require_media_authorization,
    require_media_command_authorization,
)

SCRATCH = Path(__file__).resolve().parents[2] / "scratch"
FFMPEG_SCRIPTS = [
    "analyze_train_events.py",
    "analyze_forensic_results.py",
    "analyze_audio.py",
    "extract_frames.py",
    "forensic_event_auditor.py",
    "measure_ground_truth_v7.py",
    "run_phase2_verification.py",
]
LAUNCHERS = {"run", "Popen", "call", "check_call", "check_output"}

pytestmark = pytest.mark.skipif(
    not SCRATCH.is_dir(), reason="scratch/ is git-ignored and absent from this checkout"
)


def parse(name: str) -> ast.Module:
    return ast.parse((SCRATCH / name).read_text(encoding="utf-8"))


def find_calls(node: ast.AST, *, module: str, names: set[str]) -> list[ast.Call]:
    out = []
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and isinstance(child.func.value, ast.Name)
            and child.func.value.id == module
            and child.func.attr in names
        ):
            out.append(child)
    return out


def bodies(tree: ast.AST):
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if isinstance(block, list) and block and isinstance(block[0], ast.stmt):
                yield block


def is_guard_call(stmt: ast.stmt, guard: str) -> ast.Call | None:
    if (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Call)
        and isinstance(stmt.value.func, ast.Name)
        and stmt.value.func.id == guard
    ):
        return stmt.value
    return None


def contains(stmt: ast.stmt, call: ast.Call) -> bool:
    return any(node is call for node in ast.walk(stmt))


def preceding_guard(tree: ast.AST, call: ast.Call, guard: str) -> ast.Call | None:
    """The guard call that is the statement immediately before the statement holding ``call``."""
    for block in bodies(tree):
        for index, stmt in enumerate(block):
            if contains(stmt, call) and not any(
                contains(inner, call)
                for inner in ast.walk(stmt)
                if isinstance(inner, ast.stmt) and inner is not stmt
            ):
                return is_guard_call(block[index - 1], guard) if index else None
    return None


def first_arg_name(call: ast.Call) -> str | None:
    return call.args[0].id if call.args and isinstance(call.args[0], ast.Name) else None


# ------------------------------------------------------------------ static coverage


def test_the_seven_ffmpeg_scripts_are_present():
    missing = [name for name in FFMPEG_SCRIPTS if not (SCRATCH / name).is_file()]
    assert missing == []


@pytest.mark.parametrize("name", FFMPEG_SCRIPTS)
def test_every_subprocess_launch_is_immediately_preceded_by_the_command_guard(name):
    tree = parse(name)
    launches = find_calls(tree, module="subprocess", names=LAUNCHERS)
    assert launches, f"{name} no longer launches a subprocess; update the inventory"
    for launch in launches:
        guard = preceding_guard(tree, launch, "require_media_command_authorization")
        assert guard is not None, f"{name}:{launch.lineno} launches a process without a guard"
        assert first_arg_name(guard) == first_arg_name(launch), (
            f"{name}:{launch.lineno} guards a different command than it launches"
        )


def test_every_wave_open_in_scratch_is_preceded_by_a_media_guard():
    seen = 0
    for path in sorted(SCRATCH.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for call in find_calls(tree, module="wave", names={"open"}):
            seen += 1
            assert preceding_guard(tree, call, "require_media_authorization") is not None, (
                f"{path.name}:{call.lineno} opens audio without a guard"
            )
    assert seen >= 1


def test_no_scratch_script_launches_a_process_without_a_guard():
    for path in sorted(SCRATCH.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for launch in find_calls(tree, module="subprocess", names=LAUNCHERS):
            assert preceding_guard(tree, launch, "require_media_command_authorization"), (
                f"{path.name}:{launch.lineno}"
            )


@pytest.mark.parametrize("name", FFMPEG_SCRIPTS)
def test_scripts_import_the_repository_guard_not_a_local_copy(name):
    imports = [
        node
        for node in ast.walk(parse(name))
        if isinstance(node, ast.ImportFrom)
        and node.module == "railway_detection.safety.media_guard"
    ]
    assert imports, f"{name} does not import the shared guard"
    imported = {alias.name for node in imports for alias in node.names}
    assert "require_media_command_authorization" in imported


# ------------------------------------------------------------------ dynamic refusal


class RecordingSubprocess:
    PIPE = -1
    DEVNULL = -3

    def __init__(self) -> None:
        self.launches: list[list[str]] = []

    def _record(self, cmd, *_a, **_k):
        self.launches.append([str(x) for x in cmd])
        raise AssertionError("a subprocess was launched")

    run = Popen = _record  # noqa: N815


def load_function(script: str, function: str, **extra: Any):
    source = (SCRATCH / script).read_text(encoding="utf-8")
    node = next(
        n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == function
    )
    namespace: dict[str, Any] = {
        "Path": Path,
        "Any": Any,
        "np": np,
        "wave": wave,
        "require_media_authorization": require_media_authorization,
        "require_media_command_authorization": require_media_command_authorization,
        **extra,
    }
    exec(compile(ast.Module(body=[node], type_ignores=[]), script, "exec"), namespace)  # noqa: S102
    return namespace[function]


@pytest.fixture
def repo(tmp_path_factory, monkeypatch):
    return make_fake_repo(tmp_path_factory, monkeypatch)


def test_frame_extractor_refuses_before_launching_ffmpeg(repo):
    recorder = RecordingSubprocess()
    extract = load_function("forensic_event_auditor.py", "extract_frame_at", subprocess=recorder)
    with pytest.raises(MediaAccessAuthorizationError) as info:
        extract(repo.video, 3.0, repo.root / "scratch" / "frame.jpg")
    assert info.value.code == "AUTH_MEDIA_ACCESS_NOT_GRANTED"
    assert recorder.launches == []


def test_frame_extractor_refuses_an_alias_with_an_innocent_name(repo, tmp_path_factory):
    recorder = RecordingSubprocess()
    extract = load_function("forensic_event_auditor.py", "extract_frame_at", subprocess=recorder)
    alias = outside_dir(tmp_path_factory, "alias") / "notes.txt"
    alias.symlink_to(repo.video)
    with pytest.raises(MediaAccessAuthorizationError):
        extract(alias, 1.0, repo.root / "scratch" / "frame.jpg")
    assert recorder.launches == []


def test_frame_extractor_refuses_to_write_into_evidence_trees_even_for_synthetic_input(
    repo, tmp_path_factory
):
    recorder = RecordingSubprocess()
    extract = load_function("forensic_event_auditor.py", "extract_frame_at", subprocess=recorder)
    clip = outside_dir(tmp_path_factory, "synthetic_in") / "clip.mov"
    clip.write_bytes(b"x")
    with pytest.raises(MediaAccessAuthorizationError) as info:
        extract(clip, 1.0, repo.root / "data" / "ground_truth" / "overwrite.jpg")
    assert info.value.code == "PROTECTED_OUTPUT_REFUSED"
    assert recorder.launches == []


def test_frame_extractor_launches_for_synthetic_input_and_scratch_output(repo, tmp_path_factory):
    recorder = RecordingSubprocess()
    extract = load_function("forensic_event_auditor.py", "extract_frame_at", subprocess=recorder)
    clip = outside_dir(tmp_path_factory, "synthetic_ok") / "clip.mov"
    clip.write_bytes(b"x")
    with pytest.raises(AssertionError, match="launched"):  # the stand-in blocks the real launch
        extract(clip, 1.0, repo.root / "scratch" / "frame.jpg")
    assert len(recorder.launches) == 1 and str(clip) in recorder.launches[0]


def test_audio_snr_extractor_refuses_before_launching(repo):
    recorder = RecordingSubprocess()
    extract = load_function("run_phase2_verification.py", "extract_audio_snr", subprocess=recorder)
    with pytest.raises(MediaAccessAuthorizationError):
        extract(repo.video)
    assert recorder.launches == []


def test_wav_analysis_refuses_before_opening_audio(repo, monkeypatch):
    analyze = load_function("analyze_audio.py", "analyze_wav")
    wav = repo.root / "scratch" / "front_audio.wav"
    wav.write_bytes(b"RIFF....WAVE")
    monkeypatch.setattr(
        wave, "open", lambda *a, **k: (_ for _ in ()).throw(AssertionError("opened"))
    )
    with pytest.raises(MediaAccessAuthorizationError):
        analyze(wav)


def test_environment_cannot_bypass_the_scratch_guard(repo, monkeypatch):
    for key in ("AUTH_MEDIA_ACCESS", "RAILWAY_ALLOW_MEDIA", "SKIP_MEDIA_GUARD", "CI"):
        monkeypatch.setenv(key, "1")
    recorder = RecordingSubprocess()
    extract = load_function("forensic_event_auditor.py", "extract_frame_at", subprocess=recorder)
    with pytest.raises(MediaAccessAuthorizationError):
        extract(repo.video, 0.0, repo.root / "scratch" / "f.jpg")
    assert recorder.launches == []
