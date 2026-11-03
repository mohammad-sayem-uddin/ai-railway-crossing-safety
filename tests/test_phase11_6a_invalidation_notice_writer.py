"""Phase 11.6A: tests for the legacy-invalidation notice writer.

Synthetic fixtures only (`tmp_path`, with cwd chdir'd into it). NEVER
constructs a path under the real `data/ground_truth/reviews/` and never
imports or references the real 27 records as a write-operation fixture,
per the Phase 11.6A authorization boundary: implementation and testing
only, no real record may be touched.

`affected_record_path` is deliberately a REPO-RELATIVE string in the real
proposal format (`promotion_gate.propose_invalidation` stores whatever
`Path` it is given, and in real use that is always repo-relative) -- so
each test chdir's into its own `tmp_path` and builds relative paths there,
mirroring exactly how the real proposal was constructed in Phase 11.6.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, UTC
from pathlib import Path

import pytest

from railway_detection.annotation.invalidation_notice_writer import (
    DIRECTORY_NOTICE_NAME,
    NOTICE_SUFFIX,
    NoticeWriterValidationError,
    apply_invalidation_notices,
    validate_proposal_for_application,
)
from railway_detection.annotation.promotion_gate import propose_invalidation

NOW = datetime(2026, 10, 14, 22, 0, 0, tzinfo=UTC)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_fixture(tmp_path: Path, monkeypatch, n: int = 3) -> tuple[Path, dict, list[Path]]:
    """Chdir's into tmp_path and builds a synthetic reviews/ tree with n
    legacy review records (alternating cohorts), plus a sibling proposals/
    directory (never targeted) to prove protected-artifact separation.
    Returns (reviews_root, proposal_dict, [target_paths]) -- all relative
    to the now-current working directory (tmp_path)."""
    monkeypatch.chdir(tmp_path)
    reviews_root = Path("data/ground_truth/reviews")
    proposals_root = Path("data/ground_truth/proposals")
    (proposals_root / "train_events").mkdir(parents=True)
    (proposals_root / "train_events" / "event_001_proposal_v2.json").write_text("{}", encoding="utf-8")

    targets: list[Path] = []
    events = []
    for i in range(n):
        cohort = "train_events" if i % 2 == 0 else "no_train_events"
        cohort_dir = reviews_root / cohort
        cohort_dir.mkdir(parents=True, exist_ok=True)
        target = cohort_dir / f"event_{i:03d}_review.json"
        target.write_text(json.dumps({"schema_version": "7.0.0", "event_id": f"event_{i:03d}"}), encoding="utf-8")
        targets.append(target)

        ev = propose_invalidation(
            event_id=f"{cohort}/event_{i:03d}",
            reason="synthetic test reason -- process integrity defect",
            actor="test_researcher@example.com",
            authorized_statement="synthetic test authorization statement",
            affected_record_path=target,
            now_utc=NOW,
        )
        events.append(asdict(ev))

    proposal = {"disposition_events": events}
    return reviews_root, proposal, targets


def _apply(reviews_root, proposal, n, **kwargs):
    return apply_invalidation_notices(
        proposal, reviews_root=reviews_root, expected_count=n, now_utc=NOW, **kwargs
    )


# ---------------------------------------------------------------------------
# 1. All expected notices generated for synthetic records
# ---------------------------------------------------------------------------

def test_all_expected_notices_generated(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=3)
    before_hashes = [_sha256(t) for t in targets]

    report = _apply(reviews_root, proposal, n=3)

    assert report.summary_counts()["WRITTEN"] == 3
    assert report.directory_notice_result.status == "WRITTEN"

    for t in targets:
        notice_path = t.parent / (t.stem + NOTICE_SUFFIX)
        assert notice_path.exists()
        content = json.loads(notice_path.read_text(encoding="utf-8"))
        assert content["disposition"] == "INVALIDATED"
        assert content["applies_to_file_sha256_at_notice_time"] == _sha256(t)

    dir_notice = reviews_root / DIRECTORY_NOTICE_NAME
    assert dir_notice.exists()
    assert "3 total" in dir_notice.read_text(encoding="utf-8")

    after_hashes = [_sha256(t) for t in targets]
    assert before_hashes == after_hashes


# ---------------------------------------------------------------------------
# 2. Target hash mismatch and missing target
# ---------------------------------------------------------------------------

def test_target_hash_mismatch_skipped(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=3)
    targets[1].write_text(json.dumps({"schema_version": "7.0.0", "tampered": True}), encoding="utf-8")
    mutated_hash = _sha256(targets[1])

    report = _apply(reviews_root, proposal, n=3)
    counts = report.summary_counts()
    assert counts["SKIPPED_TARGET_HASH_MISMATCH"] == 1
    assert counts["WRITTEN"] == 2

    notice_path = targets[1].parent / (targets[1].stem + NOTICE_SUFFIX)
    assert not notice_path.exists()
    assert _sha256(targets[1]) == mutated_hash  # writer never touched the target itself


def test_missing_target_skipped(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=3)
    targets[2].unlink()

    report = _apply(reviews_root, proposal, n=3)
    counts = report.summary_counts()
    assert counts["SKIPPED_TARGET_MISSING"] == 1
    assert counts["WRITTEN"] == 2

    notice_path = targets[2].parent / (targets[2].stem + NOTICE_SUFFIX)
    assert not notice_path.exists()


# ---------------------------------------------------------------------------
# 3. Existing matching output and conflicting output
# ---------------------------------------------------------------------------

def test_existing_matching_output_is_idempotent_resume(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=3)

    first = _apply(reviews_root, proposal, n=3)
    assert first.summary_counts()["WRITTEN"] == 3

    second = _apply(reviews_root, proposal, n=3)
    counts = second.summary_counts()
    assert counts["SKIPPED_ALREADY_DONE_MATCHING"] == 3
    assert counts["WRITTEN"] == 0
    assert second.directory_notice_result.status == "SKIPPED_ALREADY_DONE_MATCHING"


def test_existing_conflicting_output_reported_not_overwritten(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=3)
    notice_path = targets[0].parent / (targets[0].stem + NOTICE_SUFFIX)
    notice_path.parent.mkdir(parents=True, exist_ok=True)
    notice_path.write_text(json.dumps({"disposition": "SOMETHING_ELSE_ENTIRELY"}), encoding="utf-8")

    report = _apply(reviews_root, proposal, n=3)
    counts = report.summary_counts()
    assert counts["CONFLICT_EXISTING_OUTPUT_MISMATCH"] == 1
    assert counts["WRITTEN"] == 2
    assert json.loads(notice_path.read_text(encoding="utf-8")) == {"disposition": "SOMETHING_ELSE_ENTIRELY"}


def test_directory_level_notice_conflict(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=2)
    dir_notice = reviews_root / DIRECTORY_NOTICE_NAME
    dir_notice.write_text("# pre-existing unrelated content\n", encoding="utf-8")

    report = _apply(reviews_root, proposal, n=2)
    assert report.directory_notice_result.status == "CONFLICT_EXISTING_OUTPUT_MISMATCH"
    assert report.summary_counts()["WRITTEN"] == 2  # per-record notices still proceed independently
    assert dir_notice.read_text(encoding="utf-8") == "# pre-existing unrelated content\n"


# ---------------------------------------------------------------------------
# 4. Duplicate paths and path traversal
# ---------------------------------------------------------------------------

def test_duplicate_target_paths_rejected_and_nothing_written(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=2)
    proposal["disposition_events"].append(dict(proposal["disposition_events"][0]))

    with pytest.raises(NoticeWriterValidationError, match="duplicate"):
        validate_proposal_for_application(proposal, reviews_root=reviews_root, expected_count=3)

    assert not any(reviews_root.rglob(f"*{NOTICE_SUFFIX}"))
    assert not (reviews_root / DIRECTORY_NOTICE_NAME).exists()


def test_path_traversal_rejected(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    proposal["disposition_events"][0]["affected_record_path"] = "data/ground_truth/reviews/../../../etc/passwd"

    with pytest.raises(NoticeWriterValidationError, match="traversal"):
        validate_proposal_for_application(proposal, reviews_root=reviews_root, expected_count=1)

    assert not any(reviews_root.rglob(f"*{NOTICE_SUFFIX}"))


def test_absolute_target_path_rejected(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    proposal["disposition_events"][0]["affected_record_path"] = str(targets[0].resolve())

    with pytest.raises(NoticeWriterValidationError, match="relative"):
        validate_proposal_for_application(proposal, reviews_root=reviews_root, expected_count=1)


# ---------------------------------------------------------------------------
# 5. Partial failures and resume after partial completion
# ---------------------------------------------------------------------------

def test_partial_failure_then_resume(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=3)
    failing_target = targets[1]
    # validate_proposal_for_application resolves to absolute paths internally,
    # so the output_path _atomic_exclusive_write actually receives is absolute.
    failing_output = failing_target.resolve().parent / (failing_target.stem + NOTICE_SUFFIX)

    import railway_detection.annotation.invalidation_notice_writer as mod
    real_write = mod._atomic_exclusive_write

    def flaky_write(path, content):
        if path == failing_output:
            raise OSError("simulated transient disk error")
        return real_write(path, content)

    monkeypatch.setattr(mod, "_atomic_exclusive_write", flaky_write)

    report = _apply(reviews_root, proposal, n=3)
    counts = report.summary_counts()
    assert counts["WRITTEN"] == 2
    assert counts["FAILED_WRITE_ERROR"] == 1
    assert not failing_output.exists()

    monkeypatch.setattr(mod, "_atomic_exclusive_write", real_write)

    resumed = _apply(reviews_root, proposal, n=3)
    resumed_counts = resumed.summary_counts()
    assert resumed_counts["SKIPPED_ALREADY_DONE_MATCHING"] == 2
    assert resumed_counts["WRITTEN"] == 1
    assert failing_output.exists()


def test_batch_continues_after_one_ordinary_failure_not_aborted(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=4)
    targets[0].unlink()

    report = _apply(reviews_root, proposal, n=4)
    counts = report.summary_counts()
    assert counts["SKIPPED_TARGET_MISSING"] == 1
    assert counts["WRITTEN"] == 3


# ---------------------------------------------------------------------------
# 6. Expected scope / schema validation
# ---------------------------------------------------------------------------

def test_expected_count_mismatch_rejected(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=2)
    with pytest.raises(NoticeWriterValidationError, match="expected exactly"):
        validate_proposal_for_application(proposal, reviews_root=reviews_root, expected_count=27)


def test_missing_required_field_rejected(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    del proposal["disposition_events"][0]["affected_record_sha256"]
    with pytest.raises(NoticeWriterValidationError, match="missing/blank"):
        validate_proposal_for_application(proposal, reviews_root=reviews_root, expected_count=1)


def test_malformed_sha256_rejected(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    proposal["disposition_events"][0]["affected_record_sha256"] = "not-a-real-hash"
    with pytest.raises(NoticeWriterValidationError, match="SHA-256"):
        validate_proposal_for_application(proposal, reviews_root=reviews_root, expected_count=1)


def test_protected_root_rejected_even_if_also_inside_reviews_root(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    with pytest.raises(NoticeWriterValidationError, match="protected root"):
        validate_proposal_for_application(
            proposal, reviews_root=reviews_root, protected_roots=[reviews_root], expected_count=1,
        )


def test_target_not_ending_in_review_json_suffix_rejected(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    bad_target = targets[0].parent / "not_a_review_file.json"
    targets[0].rename(bad_target)
    proposal["disposition_events"][0]["affected_record_path"] = str(bad_target)
    proposal["disposition_events"][0]["affected_record_sha256"] = _sha256(bad_target)
    with pytest.raises(NoticeWriterValidationError, match="_review.json"):
        validate_proposal_for_application(proposal, reviews_root=reviews_root, expected_count=1)


# ---------------------------------------------------------------------------
# 7. Proof originals remain byte-identical; proof nothing written outside fixture
# ---------------------------------------------------------------------------

def test_originals_byte_identical_through_mixed_outcomes(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=3)
    before = {str(t): _sha256(t) for t in targets}

    notice_path = targets[0].parent / (targets[0].stem + NOTICE_SUFFIX)
    notice_path.write_text(json.dumps({"disposition": "WRONG"}), encoding="utf-8")

    _apply(reviews_root, proposal, n=3)

    after = {str(t): _sha256(t) for t in targets}
    assert before == after


def test_no_path_written_outside_fixture_root(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=3)
    before_files = set(p for p in Path(".").rglob("*") if p.is_file())

    _apply(reviews_root, proposal, n=3)

    after_files = set(p for p in Path(".").rglob("*") if p.is_file())
    new_files = after_files - before_files

    expected_new = {t.parent / (t.stem + NOTICE_SUFFIX) for t in targets}
    expected_new.add(reviews_root / DIRECTORY_NOTICE_NAME)
    assert new_files == expected_new

    proposals_files_after = list(Path("data/ground_truth/proposals").rglob("*"))
    assert not any(str(p).endswith(NOTICE_SUFFIX) for p in proposals_files_after)
