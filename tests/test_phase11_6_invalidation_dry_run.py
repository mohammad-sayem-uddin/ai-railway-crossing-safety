"""Phase 11.6: dry-run planning for legacy-invalidation notices.

Synthetic fixtures only (`tmp_path`, with cwd chdir'd into it). These tests
never construct a path under the real `data/ground_truth/reviews/` tree and
never use the real 27 records as a fixture.

The dry run must be a faithful preview of the write path and must itself
write nothing, so the central assertions are (a) plan statuses correspond to
the applied statuses, and (b) the filesystem is byte-identical before and
after planning.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from railway_detection.annotation.invalidation_notice_writer import (
    DIRECTORY_NOTICE_NAME,
    NOTICE_PLAN_STATUSES,
    NOTICE_SUFFIX,
    NOTICE_WRITE_STATUSES,
    apply_invalidation_notices,
    plan_invalidation_notices,
)
from test_phase11_6a_invalidation_notice_writer import _make_fixture


def _tree_fingerprint(root: Path) -> dict[str, str]:
    """Hash every file under root, so any write at all is detectable."""
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_plan_statuses_are_disjoint_from_applied_statuses():
    """A plan result can never be mistaken for an applied result."""
    assert not set(NOTICE_PLAN_STATUSES) & set(NOTICE_WRITE_STATUSES)
    assert all(status.startswith("WOULD_") for status in NOTICE_PLAN_STATUSES)


def test_dry_run_writes_nothing_at_all(tmp_path: Path, monkeypatch):
    reviews_root, proposal, _targets = _make_fixture(tmp_path, monkeypatch, n=3)
    before = _tree_fingerprint(tmp_path)

    report = plan_invalidation_notices(
        proposal, reviews_root=reviews_root, expected_count=3
    )

    assert _tree_fingerprint(tmp_path) == before
    assert not list(reviews_root.rglob(f"*{NOTICE_SUFFIX}"))
    assert not (reviews_root / DIRECTORY_NOTICE_NAME).exists()
    assert all(r.status == "WOULD_WRITE" for r in report.results)
    assert report.directory_notice_result.status == "WOULD_WRITE"


def test_dry_run_predicts_the_applied_outcome(tmp_path: Path, monkeypatch):
    """Every WOULD_WRITE must become WRITTEN when the writer actually runs."""
    reviews_root, proposal, _targets = _make_fixture(tmp_path, monkeypatch, n=3)

    planned = plan_invalidation_notices(proposal, reviews_root=reviews_root, expected_count=3)
    applied = apply_invalidation_notices(proposal, reviews_root=reviews_root, expected_count=3)

    planned_by_event = {r.event_id: r for r in planned.results}
    for result in applied.results:
        prediction = planned_by_event[result.event_id]
        assert prediction.status == "WOULD_WRITE"
        assert result.status == "WRITTEN"
        assert prediction.output_path == result.output_path


def test_dry_run_after_application_reports_already_done(tmp_path: Path, monkeypatch):
    reviews_root, proposal, _targets = _make_fixture(tmp_path, monkeypatch, n=2)
    apply_invalidation_notices(proposal, reviews_root=reviews_root, expected_count=2)

    after = _tree_fingerprint(tmp_path)
    report = plan_invalidation_notices(proposal, reviews_root=reviews_root, expected_count=2)

    assert _tree_fingerprint(tmp_path) == after
    assert all(r.status == "WOULD_SKIP_ALREADY_DONE_MATCHING" for r in report.results)
    assert report.directory_notice_result.status == "WOULD_SKIP_ALREADY_DONE_MATCHING"


def test_dry_run_flags_a_target_whose_hash_changed(tmp_path: Path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=2)
    targets[0].write_text(json.dumps({"tampered": True}), encoding="utf-8")

    report = plan_invalidation_notices(proposal, reviews_root=reviews_root, expected_count=2)

    statuses = {r.event_id: r.status for r in report.results}
    assert "WOULD_SKIP_TARGET_HASH_MISMATCH" in statuses.values()
    assert not list(reviews_root.rglob(f"*{NOTICE_SUFFIX}"))


def test_dry_run_flags_a_missing_target(tmp_path: Path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=2)
    targets[0].unlink()

    report = plan_invalidation_notices(proposal, reviews_root=reviews_root, expected_count=2)

    assert "WOULD_SKIP_TARGET_MISSING" in {r.status for r in report.results}


def test_dry_run_flags_a_conflicting_existing_notice(tmp_path: Path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=2)
    conflicting = targets[0].resolve().parent / (targets[0].stem + NOTICE_SUFFIX)
    conflicting.write_text(json.dumps({"notice_type": "SOMETHING_ELSE"}), encoding="utf-8")
    before = _tree_fingerprint(tmp_path)

    report = plan_invalidation_notices(proposal, reviews_root=reviews_root, expected_count=2)

    assert "WOULD_CONFLICT_EXISTING_OUTPUT_MISMATCH" in {r.status for r in report.results}
    assert _tree_fingerprint(tmp_path) == before


def test_dry_run_enforces_the_same_expected_count_preflight(tmp_path: Path, monkeypatch):
    """The dry run must not be a way to bypass the proposal pre-flight."""
    import pytest

    from railway_detection.annotation.invalidation_notice_writer import (
        NoticeWriterValidationError,
    )

    reviews_root, proposal, _targets = _make_fixture(tmp_path, monkeypatch, n=2)
    with pytest.raises(NoticeWriterValidationError):
        plan_invalidation_notices(proposal, reviews_root=reviews_root, expected_count=27)
