# ruff: noqa: E501
"""Static detection of unguarded raw-media openers (Mission 10, WP10.2).

A heuristic AST scan over ``src/`` and ``scripts/``: any function that decodes video, reads a WAV
in binary mode, runs ``ffmpeg``/``ffprobe`` through ``subprocess``, or hashes raw bytes must call
``require_media_authorization`` -- unless it is on the reviewed allowlist below, each entry of which
states why it can only ever touch metadata. The scan is a tripwire for *new* openers, not a proof:
it cannot see a library that opens media indirectly (see the limitations in ``media_guard``).
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Mission 12 extends the static tripwire to research scripts and image readers; Mission 14 adds
# guard-before-reader ordering, ``predict(source=path)``, full-path ffmpeg names, module-level
# code and the git-ignored ``scratch/`` scripts.  These are operation-boundary checks, not an OS
# sandbox.
RESEARCH_READER_ALLOWLIST: dict[str, str] = {}

#: ``"<relative path>::<function>"`` -> why this function cannot open raw media.
REVIEWED_METADATA_ONLY: dict[str, str] = {
    "src/railway_detection/safety/resource_free_acceptance.py::bindings": "hashes only explicit src/scripts/test Python and config metadata families after protected-root and source/config symlink refusal; no research artifact trees",
    "src/railway_detection/synthetic/integration_workflow.py::verify_completed": "hashes only closed-name constructed demo JSON/docs/source artifacts after protected-root and parent-first symlink rejection",
    "src/railway_detection/synthetic/integration_workflow.py::run_demo": "hashes only its own named constructed artifacts and snapshot, after protected-root and parent-first symlink rejection; never media/cache/checkpoint paths",
    "src/railway_detection/annotation/batch_multimodal_annotator.py::_compute_prompt_hash": "hashes the prompt template text file",
    "src/railway_detection/annotation/candidate_split_queue.py::_read_json": "reads JSON manifests",
    "src/railway_detection/annotation/gemini_annotator.py::_load_prompt_template_hash": "hashes the prompt template text file",
    "src/railway_detection/annotation/invalidation_notice_writer.py::compute_proposal_sha256": "hashes a proposal JSON",
    "src/railway_detection/annotation/invalidation_notice_writer.py::load_and_verify_proposal": "reads a proposal JSON",
    "src/railway_detection/annotation/invalidation_notice_writer.py::_plan_one_record": "hashes review-record JSON",
    "src/railway_detection/annotation/invalidation_notice_writer.py::_process_one_record": "hashes review-record JSON",
    "src/railway_detection/annotation/leg_exec.py::verify_authorization": "reads the LEG-EXEC authorization JSON",
    "src/railway_detection/annotation/legacy_reconciliation.py::_sha256": "hashes review-record JSON",
    "src/railway_detection/annotation/legacy_reconciliation.py::reconcile_legacy_reviews": "reads review-record JSON",
    "src/railway_detection/annotation/notices.py::verify_invalidation_notice": "reads notice and record JSON",
    "src/railway_detection/annotation/promotion_gate.py::propose_invalidation": "hashes a review-record JSON",
    "src/railway_detection/annotation/readiness_audit.py::_record_rows": "reads review-record JSON",
    "src/railway_detection/annotation/second_review.py::load_candidate_values": "reads a proposal JSON bound by hash",
    "src/railway_detection/annotation/stage21_timing_pilot.py::verify_release_manifest": "hashes release-manifest metadata files",
    "src/railway_detection/annotation/stage21_timing_pilot.py::_metadata_bindings": "hashes inventory/proposal metadata",
    "src/railway_detection/annotation/stage21_timing_pilot.py::write_unapproved_draft": "re-reads draft JSON it wrote",
    "src/railway_detection/annotation/stage21_timing_pilot.py::create_release_artifacts": "hashes release metadata",
    "src/railway_detection/evaluation/descriptive_exec_gate.py::verify_descriptive_authorization": "reads the AUTH-DESCRIPTIVE-EVAL-EXEC JSON record",
    "src/railway_detection/evaluation/execution_gate.py::_read_repository_records": "reads review-record JSON",
    "src/railway_detection/evaluation/governance.py::sha256_small_file": "hashes governance JSON",
    "src/railway_detection/evaluation/governance.py::_read_json_object": "reads governance JSON",
    "src/railway_detection/evaluation/ground_truth_loader.py::load_approved_ground_truth_with_hashes": "reads review-record JSON",
    "src/railway_detection/experiments/frozen_config.py::compute_file_sha256": "hashes the frozen config and model checkpoints (weights, not media)",
    "scratch/run_phase2_verification.py::compute_sha256": "hashes proposal JSON files (the media step is guarded separately)",
    "src/railway_detection/safety/access_manifest.py::sha256_of": "hashes test source files for the classification manifest",
    "src/railway_detection/simulation/runner.py::_profile_metadata": "hashes this package's own source files",
}


def _is_binary_read(call: ast.Call, *, mode_index: int) -> bool:
    candidates = list(call.args[mode_index : mode_index + 1]) + [
        k.value for k in call.keywords if k.arg == "mode"
    ]
    return any(
        isinstance(c, ast.Constant)
        and isinstance(c.value, str)
        and "r" in c.value
        and "b" in c.value
        for c in candidates
    )


_PATH_PREDICT = re.compile(r"\.predict\([^)]*?source=(?:str\(|Path\(|[A-Za-z_]*path\b|p\b)", re.S)
_GUARDS = (
    "require_media_authorization(",
    "require_media_command_authorization(",
    "frame_generator(",
)
_FFMPEG_NAMES = (
    '"ffmpeg"',
    '"ffprobe"',
    "'ffmpeg'",
    "'ffprobe'",
    'ffmpeg"',
    'ffprobe"',
    "ffmpeg'",
    "ffprobe'",
)


def _reader_tokens(text: str, calls: list[ast.Call]) -> list[tuple[int, str]]:
    """(offset, reason) of each media-reading construct in ``text``."""
    found: list[tuple[int, str]] = []

    def add(token: str, reason: str) -> None:
        index = text.find(token)
        if index != -1:
            found.append((index, reason))

    add("VideoCapture(", "cv2.VideoCapture")
    add("Image.open(", "image reader")
    add("cv2.imread(", "image reader")
    if "wave.open(" in text and ('"rb"' in text or "'rb'" in text):
        add("wave.open(", "wave.open rb")
    if "subprocess" in text and any(token in text for token in _FFMPEG_NAMES):
        for launcher in ("subprocess.run(", "subprocess.Popen(", "subprocess.check_output("):
            add(launcher, "ffmpeg/ffprobe subprocess")
    # Mission 14 (F13-13): ultralytics reads the file itself when ``source`` is a path.
    match = _PATH_PREDICT.search(text)
    if match:
        found.append((match.start(), "predict(source=path)"))
    raw = any(
        (isinstance(c.func, ast.Attribute) and c.func.attr == "read_bytes")
        or (
            isinstance(c.func, ast.Name)
            and c.func.id == "open"
            and _is_binary_read(c, mode_index=1)
        )
        or (
            isinstance(c.func, ast.Attribute)
            and c.func.attr == "open"
            and _is_binary_read(c, mode_index=0)
        )
        for c in calls
    )
    if raw and ("sha256" in text or "hashlib" in text):
        offsets = [text.find(t) for t in ("read_bytes(", "open(") if t in text]
        found.append((min(offsets), "raw-byte hash"))
    return found


def _scopes(tree: ast.Module):
    """Every function, plus the module body itself (scripts run work at import time)."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node.name, node
    module_level = ast.Module(
        body=[
            n
            for n in tree.body
            if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ],
        type_ignores=[],
    )
    yield "<module>", module_level


def _scan() -> dict[str, str]:
    found: dict[str, str] = {}
    files = (
        sorted((ROOT / "src").rglob("*.py"))
        + sorted((ROOT / "scripts").glob("*.py"))
        + sorted((ROOT / "research").rglob("*.py"))
        + sorted((ROOT / "scratch").glob("*.py"))
    )
    for path in files:
        if path.name == "media_guard.py":
            continue
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        rel = path.relative_to(ROOT).as_posix()
        for name, node in _scopes(tree):
            text = (
                ast.get_source_segment(source, node)
                if not isinstance(node, ast.Module)
                else ("\n".join(ast.get_source_segment(source, n) or "" for n in node.body))
            )
            text = text or ""
            calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
            readers = _reader_tokens(text, calls)
            if not readers:
                continue
            first_reader = min(index for index, _ in readers)
            guard_positions = [text.find(g) for g in _GUARDS if g in text]
            reasons = ",".join(sorted({reason for _, reason in readers}))
            if not guard_positions:
                found[f"{rel}::{name}"] = reasons
            elif min(guard_positions) > first_reader and not name.startswith("<"):
                # Mission 14 (F13-13): a guard that appears *after* the reader does not protect it.
                found[f"{rel}::{name}"] = f"guard after reader ({reasons})"
    return found


def test_every_media_opener_is_guarded_or_reviewed_metadata_only():
    unguarded = {k: v for k, v in _scan().items() if k not in REVIEWED_METADATA_ONLY}
    assert not unguarded, (
        "unguarded raw-media openers (add require_media_authorization at the opener, or review and "
        f"allowlist with a reason): {unguarded}"
    )


def test_allowlist_has_no_stale_entries():
    stale = sorted(set(REVIEWED_METADATA_ONLY) - set(_scan()))
    assert not stale, f"allowlist entries that no longer match an opener: {stale}"


def test_allowlist_reasons_are_specific():
    assert all(len(reason) > 12 for reason in REVIEWED_METADATA_ONLY.values())


def test_scan_detects_a_new_unguarded_opener(tmp_path: Path, monkeypatch):
    """The detector itself is exercised on a synthetic offender."""
    fake_src = tmp_path / "src"
    (fake_src / "pkg").mkdir(parents=True)
    (fake_src / "pkg" / "bad.py").write_text(
        "import cv2\n\ndef open_it(p):\n    return cv2.VideoCapture(p)\n", encoding="utf-8"
    )
    (tmp_path / "scripts").mkdir()
    monkeypatch.setattr(sys.modules[__name__], "ROOT", tmp_path)
    assert "src/pkg/bad.py::open_it" in _scan()


def _scan_offender(tmp_path: Path, monkeypatch, filename: str, body: str) -> dict[str, str]:
    fake_src = tmp_path / "src" / "pkg"
    fake_src.mkdir(parents=True)
    (fake_src / filename).write_text(body, encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    monkeypatch.setattr(sys.modules[__name__], "ROOT", tmp_path)
    return _scan()


def test_scan_detects_a_guard_that_comes_after_the_reader(tmp_path: Path, monkeypatch):
    body = (
        "import cv2\n"
        "from railway_detection.safety.media_guard import require_media_authorization\n\n"
        "def late(p):\n    cap = cv2.VideoCapture(p)\n"
        "    require_media_authorization(p, 'READ_RAW_MEDIA')\n    return cap\n\n"
        "def early(p):\n    require_media_authorization(p, 'READ_RAW_MEDIA')\n"
        "    return cv2.VideoCapture(p)\n"
    )
    hits = _scan_offender(tmp_path, monkeypatch, "late.py", body)
    assert "guard after reader" in hits["src/pkg/late.py::late"]
    assert "src/pkg/late.py::early" not in hits


def test_scan_detects_path_predict_full_path_ffmpeg_and_module_level_readers(
    tmp_path: Path, monkeypatch
):
    body = (
        "import subprocess\n\n"
        "def run_model(model, p):\n    return model.predict(source=str(p), conf=0.3)\n\n"
        "def in_memory(model, frames):\n    return model.predict(source=frames)\n\n"
        "def launch(path):\n"
        "    cmd = ['/opt/homebrew/bin/ffmpeg', '-i', str(path), 'out.jpg']\n"
        "    return subprocess.run(cmd)\n\n"
        "subprocess.Popen(['ffmpeg', '-i', 'x.mov', '-'])\n"
    )
    hits = _scan_offender(tmp_path, monkeypatch, "readers.py", body)
    assert "predict(source=path)" in hits["src/pkg/readers.py::run_model"]
    assert "src/pkg/readers.py::in_memory" not in hits
    assert "ffmpeg/ffprobe subprocess" in hits["src/pkg/readers.py::launch"]
    assert "src/pkg/readers.py::<module>" in hits


def test_scan_covers_the_git_ignored_scratch_directory(tmp_path: Path, monkeypatch):
    (tmp_path / "src").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scratch").mkdir()
    (tmp_path / "scratch" / "tool.py").write_text(
        "import subprocess\nsubprocess.run(['ffmpeg', '-i', 'a.mov', 'b.jpg'])\n", encoding="utf-8"
    )
    monkeypatch.setattr(sys.modules[__name__], "ROOT", tmp_path)
    assert "scratch/tool.py::<module>" in _scan()


def test_the_evaluation_input_loader_is_no_longer_allowlisted():
    """Mission 13 F13-01: its old 'reads the evidence manifest JSON' reason hid source reads."""
    assert not any("input_contracts.py" in key for key in REVIEWED_METADATA_ONLY)
