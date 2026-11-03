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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Mission 12 extends the static tripwire to research scripts and image readers.
# These are operation-boundary checks, not an OS sandbox.
RESEARCH_READER_ALLOWLIST: dict[str, str] = {}

#: ``"<relative path>::<function>"`` -> why this function cannot open raw media.
REVIEWED_METADATA_ONLY: dict[str, str] = {
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
    "src/railway_detection/evaluation/input_contracts.py::load_evaluation_input_manifest": "reads the evidence manifest JSON",
    "src/railway_detection/experiments/frozen_config.py::compute_file_sha256": "hashes the frozen config and model checkpoints (weights, not media)",
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


def _scan() -> dict[str, str]:
    found: dict[str, str] = {}
    files = (
        sorted((ROOT / "src").rglob("*.py"))
        + sorted((ROOT / "scripts").glob("*.py"))
        + sorted((ROOT / "research").rglob("*.py"))
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
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            text = ast.get_source_segment(source, node) or ""
            if "require_media_authorization(" in text or "frame_generator(" in text:
                continue
            reasons = []
            if "VideoCapture(" in text:
                reasons.append("cv2.VideoCapture")
            if "Image.open(" in text or "cv2.imread(" in text:
                reasons.append("image reader")
            if "wave.open(" in text and ('"rb"' in text or "'rb'" in text):
                reasons.append("wave.open rb")
            if "subprocess" in text and any(
                t in text for t in ('"ffmpeg"', '"ffprobe"', "'ffmpeg'", "'ffprobe'")
            ):
                reasons.append("ffmpeg/ffprobe subprocess")
            calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
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
                reasons.append("raw-byte hash")
            if "image reader" in reasons and "require_media_authorization(" not in text:
                found[f"{rel}::{node.name}"] = ",".join(reasons)
            if reasons:
                found[f"{rel}::{node.name}"] = ",".join(reasons)
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
