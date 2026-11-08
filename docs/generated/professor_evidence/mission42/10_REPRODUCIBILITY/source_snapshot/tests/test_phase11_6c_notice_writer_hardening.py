"""Phase 11.6C: regression tests closing findings F1/F2/F3/F4 from
`docs/PHASE11_6B_EXECUTION_READINESS_AUDIT.md`.

Synthetic fixtures only (`tmp_path`, `monkeypatch.chdir`'d into it), same
discipline as `tests/test_phase11_6a_invalidation_notice_writer.py`. NEVER
constructs a path under the real `data/ground_truth/reviews/` and never
calls the writer or its application function with a real target path.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import asdict
from datetime import datetime, UTC
from pathlib import Path

import pytest

from railway_detection.annotation.invalidation_notice_writer import (
    DIRECTORY_NOTICE_NAME,
    NOTICE_SUFFIX,
    NoticeWriterValidationError,
    ProposalBindingError,
    apply_invalidation_notices,
    compute_proposal_sha256,
    load_and_verify_proposal,
    validate_proposal_for_application,
)
import railway_detection.annotation.invalidation_notice_writer as mod
from railway_detection.annotation.promotion_gate import propose_invalidation

NOW = datetime(2026, 10, 14, 23, 0, 0, tzinfo=UTC)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_fixture(tmp_path: Path, monkeypatch, n: int = 3) -> tuple[Path, dict, list[Path]]:
    monkeypatch.chdir(tmp_path)
    reviews_root = Path("data/ground_truth/reviews")
    for i in range(n):
        d = reviews_root / "train_events"
        d.mkdir(parents=True, exist_ok=True)
        t = d / f"event_{i:03d}_review.json"
        t.write_text(json.dumps({"schema_version": "7.0.0", "event_id": f"event_{i:03d}"}), encoding="utf-8")
    targets = [reviews_root / "train_events" / f"event_{i:03d}_review.json" for i in range(n)]
    events = []
    for t, i in zip(targets, range(n)):
        ev = propose_invalidation(
            event_id=f"train_events/event_{i:03d}", reason="r", actor="a",
            authorized_statement="s", affected_record_path=t, now_utc=NOW,
        )
        events.append(asdict(ev))
    proposal = {"disposition_events": events}
    return reviews_root, proposal, targets


def _apply(reviews_root, proposal, n, **kwargs):
    return apply_invalidation_notices(proposal, reviews_root=reviews_root, expected_count=n, now_utc=NOW, **kwargs)


def _notice_path(target: Path) -> Path:
    return target.resolve().parent / (target.stem + NOTICE_SUFFIX)


# =============================================================================
# F1 -- concurrency / race classification
# =============================================================================

def test_race_matching_content_classified_skipped_not_retryable(tmp_path, monkeypatch):
    """Deterministic (no real threads): force the exclusive-create attempt
    to lose a race against a winner who wrote MATCHING content, via a
    monkeypatched Path.exists that lies about the output not existing yet
    (forcing control past the upfront check into the FileExistsError path).
    """
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    t = targets[0]
    before_hash = _sha256(t)
    out = _notice_path(t)

    ev = proposal["disposition_events"][0]
    expected = mod._build_notice_content(ev)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    real_exists = Path.exists

    def lying_exists(self):
        return False if self == out else real_exists(self)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(Path, "exists", lying_exists)
        result = mod._process_one_record(ev, t.resolve(), out)

    assert result.status == "SKIPPED_ALREADY_DONE_MATCHING"
    assert _sha256(t) == before_hash


def test_race_unparseable_content_classified_retryable_via_lost_open(tmp_path, monkeypatch):
    """The original F1 scenario: lose the O_CREAT|O_EXCL attempt itself
    (FileExistsError), and the winner hasn't finished writing yet (empty
    file) -- must be the retryable status, not a permanent mismatch."""
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    t = targets[0]
    before_hash = _sha256(t)
    out = _notice_path(t)
    ev = proposal["disposition_events"][0]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("", encoding="utf-8")  # empty -- "in progress"

    real_exists = Path.exists

    def lying_exists(self):
        return False if self == out else real_exists(self)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(Path, "exists", lying_exists)
        result = mod._process_one_record(ev, t.resolve(), out)

    assert result.status == "CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE"
    assert _sha256(t) == before_hash
    assert out.read_text(encoding="utf-8") == ""  # left untouched, not overwritten


def test_race_unparseable_content_classified_retryable_via_upfront_exists(tmp_path, monkeypatch):
    """Phase 11.6C correction: the SAME retryable classification must apply
    when the unparseable content is discovered via the upfront .exists()
    check (came_from_race=False), not only via a lost O_EXCL race -- a
    genuine concurrent writer's in-progress file can be observed either
    way. A 3-thread stress test caught this as a real bug during this
    phase's development (a false CONFLICT_EXISTING_OUTPUT_MISMATCH for
    content that was complete and correct moments later); this test pins
    the fix deterministically."""
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    t = targets[0]
    before_hash = _sha256(t)
    out = _notice_path(t)
    ev = proposal["disposition_events"][0]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('{"notice_type": "LEGACY_REVIEW', encoding="utf-8")  # truncated mid-write

    result = mod._process_one_record(ev, t.resolve(), out)  # output_path.exists() is genuinely True here

    assert result.status == "CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE"
    assert _sha256(t) == before_hash
    assert out.read_text(encoding="utf-8") == '{"notice_type": "LEGACY_REVIEW'


def test_race_conflicting_but_parseable_content_remains_permanent_mismatch(tmp_path, monkeypatch):
    """A race winner who already finished writing DIFFERENT, valid content
    is a genuine disagreement, not an in-progress artifact -- must stay the
    permanent-looking status regardless of which branch discovers it."""
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    t = targets[0]
    out = _notice_path(t)
    ev = proposal["disposition_events"][0]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"totally": "different", "but": "valid"}), encoding="utf-8")

    result = mod._process_one_record(ev, t.resolve(), out)
    assert result.status == "CONFLICT_EXISTING_OUTPUT_MISMATCH"


def test_directory_notice_truncated_prefix_classified_retryable(tmp_path, monkeypatch):
    """Same F1 fix, applied to the text-content directory notice path."""
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=2)
    dir_notice = reviews_root / DIRECTORY_NOTICE_NAME
    sorted_ids = sorted(e["event_id"] for e in proposal["disposition_events"])
    full_content = mod._build_directory_notice_content(sorted_ids)
    dir_notice.parent.mkdir(parents=True, exist_ok=True)
    dir_notice.write_text(full_content[:20], encoding="utf-8")  # a strict prefix -- "in progress"

    result = mod._process_directory_notice(dir_notice.resolve(), full_content)
    assert result.status == "CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE"
    assert dir_notice.read_text(encoding="utf-8") == full_content[:20]


def test_dangling_symlink_at_output_never_classified_retryable(tmp_path, monkeypatch):
    """A dangling symlink is NOT a transient in-progress artifact -- a
    retry will never resolve it, so it must stay a permanent conflict even
    though it is discovered via the same FileExistsError race path."""
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    t = targets[0]
    before_hash = _sha256(t)
    out = _notice_path(t)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.symlink_to(tmp_path / "nowhere" / "nonexistent.json")

    report = _apply(reviews_root, proposal, n=1)
    result = report.results[0]
    assert result.status == "CONFLICT_EXISTING_OUTPUT_MISMATCH"
    assert "dangling symlink" in result.detail
    assert _sha256(t) == before_hash
    assert out.is_symlink() and not out.exists()  # untouched


def test_genuine_concurrent_threads_never_produce_permanent_mismatch(tmp_path, monkeypatch):
    """Real OS threads (not mocked), racing against the identical proposal
    -- content is deterministic, so any genuine disagreement would be a
    real bug. Not a timing-dependent correctness assertion (no fixed count
    of WRITTEN vs retryable is asserted, since that varies by run), only
    the invariants that must always hold regardless of interleaving."""
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=12)
    before_hashes = {str(t): _sha256(t) for t in targets}

    reports = [None, None, None]

    def worker(idx):
        reports[idx] = _apply(reviews_root, proposal, n=12)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    total_mismatch = sum(r.summary_counts()["CONFLICT_EXISTING_OUTPUT_MISMATCH"] for r in reports)
    total_written = sum(r.summary_counts()["WRITTEN"] for r in reports)
    total_skipped = sum(r.summary_counts()["SKIPPED_ALREADY_DONE_MATCHING"] for r in reports)
    total_retryable = sum(r.summary_counts()["CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE"] for r in reports)

    assert total_mismatch == 0, "identical-content concurrent writers must never produce a permanent conflict"
    assert total_written + total_skipped + total_retryable == 12 * 3

    after_hashes = {str(t): _sha256(t) for t in targets}
    assert before_hashes == after_hashes

    for t in targets:
        content = json.loads(_notice_path(t).read_text(encoding="utf-8"))
        assert content["disposition"] == "INVALIDATED"


# =============================================================================
# F3 -- symlink escapes (low-level primitive + public API)
# =============================================================================

def test_symlink_output_to_source_record_itself_refused_low_level(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    t = targets[0]
    before_hash = _sha256(t)
    before_content = t.read_text(encoding="utf-8")
    out = _notice_path(t)
    out.symlink_to(t.resolve())

    with pytest.raises(FileExistsError):
        mod._atomic_exclusive_write(out, "would-be notice content\n")

    assert _sha256(t) == before_hash
    assert t.read_text(encoding="utf-8") == before_content


def test_symlink_output_to_source_record_itself_refused_full_api(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    t = targets[0]
    before_content = t.read_text(encoding="utf-8")
    before_hash = _sha256(t)
    out = _notice_path(t)
    out.symlink_to(t.resolve())

    report = _apply(reviews_root, proposal, n=1)

    assert report.results[0].status == "CONFLICT_EXISTING_OUTPUT_MISMATCH"
    assert _sha256(t) == before_hash
    assert t.read_text(encoding="utf-8") == before_content
    assert out.is_symlink()
    assert out.resolve() == t.resolve()  # symlink itself also untouched


def test_symlink_output_to_different_protected_file_refused(tmp_path, monkeypatch):
    """Output path symlinked to a DIFFERENT file (not its own target) that
    stands in for a protected artifact (e.g. a proposal file) -- must
    never be modified."""
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=2)
    victim = Path("data/ground_truth/proposals/train_events/event_000_proposal_v2.json")
    victim.parent.mkdir(parents=True, exist_ok=True)
    victim.write_text(json.dumps({"precious": "proposal content"}), encoding="utf-8")
    victim_hash_before = _sha256(victim)

    out0 = _notice_path(targets[0])
    out0.symlink_to(victim.resolve())

    report = _apply(reviews_root, proposal, n=2)
    result0 = next(r for r in report.results if r.event_id == proposal["disposition_events"][0]["event_id"])
    assert result0.status == "CONFLICT_EXISTING_OUTPUT_MISMATCH"
    assert _sha256(victim) == victim_hash_before
    assert out0.is_symlink() and out0.resolve() == victim.resolve()
    # the other, unaffected record still proceeds normally
    assert report.summary_counts()["WRITTEN"] == 1


def test_symlink_target_outside_permitted_output_tree_refused(tmp_path, monkeypatch):
    """Output path symlinked to somewhere entirely outside reviews_root."""
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    outside = tmp_path / "outside_reviews_root.json"
    outside.write_text(json.dumps({"i am": "outside the permitted tree"}), encoding="utf-8")
    outside_hash_before = _sha256(outside)

    out = _notice_path(targets[0])
    out.symlink_to(outside)

    report = _apply(reviews_root, proposal, n=1)
    assert report.results[0].status == "CONFLICT_EXISTING_OUTPUT_MISMATCH"
    assert _sha256(outside) == outside_hash_before
    assert out.is_symlink() and out.resolve() == outside.resolve()


def test_dangling_output_symlink_refused(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    out = _notice_path(targets[0])
    out.symlink_to(tmp_path / "this_file_does_not_exist.json")

    report = _apply(reviews_root, proposal, n=1)
    assert report.results[0].status == "CONFLICT_EXISTING_OUTPUT_MISMATCH"
    assert "dangling symlink" in report.results[0].detail
    assert out.is_symlink() and not out.exists()


def test_symlink_scenarios_never_modify_any_protected_target(tmp_path, monkeypatch):
    """Consolidated proof across several symlink scenarios in one batch:
    assert every candidate 'protected' file's hash is identical before and
    after, not just that SOME record succeeded."""
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=4)

    # Valid JSON but different from any expected notice content, so these
    # two exercise the "readable, parseable, genuinely different" path
    # (permanent mismatch) rather than the "unparseable, possibly
    # in-progress" path (retryable) -- see the dedicated malformed-content
    # tests above for that other, equally-covered case.
    victim = Path("data/ground_truth/proposals/decoy.json")
    victim.parent.mkdir(parents=True, exist_ok=True)
    victim.write_text(json.dumps({"precious": "decoy json content"}), encoding="utf-8")
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps({"precious": "outside json content"}), encoding="utf-8")

    _notice_path(targets[0]).symlink_to(targets[0].resolve())       # -> own source record
    _notice_path(targets[1]).symlink_to(victim.resolve())            # -> different protected file
    _notice_path(targets[2]).symlink_to(outside)                     # -> outside permitted tree
    _notice_path(targets[3]).symlink_to(tmp_path / "dangling.json")  # -> dangling

    before = {
        "targets": {str(t): _sha256(t) for t in targets},
        "victim": victim.read_text(encoding="utf-8"),
        "outside": outside.read_text(encoding="utf-8"),
    }

    report = _apply(reviews_root, proposal, n=4)
    assert report.summary_counts()["CONFLICT_EXISTING_OUTPUT_MISMATCH"] == 4

    after = {
        "targets": {str(t): _sha256(t) for t in targets},
        "victim": victim.read_text(encoding="utf-8"),
        "outside": outside.read_text(encoding="utf-8"),
    }
    assert before == after


# =============================================================================
# F3 -- existing symlinks / malformed / unreadable (non-symlink)
# =============================================================================

def test_unreadable_existing_output_real_permission_denied(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    out = _notice_path(targets[0])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("irrelevant", encoding="utf-8")
    os.chmod(out, 0o000)
    try:
        report = _apply(reviews_root, proposal, n=1)
        status = report.results[0].status
        assert status in ("CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE", "CONFLICT_EXISTING_OUTPUT_MISMATCH")
    finally:
        os.chmod(out, 0o644)  # restore so pytest's tmp_path cleanup can remove it


# =============================================================================
# F2 -- reviewed-proposal binding
# =============================================================================

def _write_real_proposal_file(tmp_path: Path, monkeypatch, n: int = 2) -> tuple[Path, Path, dict, list[Path]]:
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=n)
    proposal_path = Path("proposal.json")
    proposal_path.write_text(json.dumps(proposal, indent=2), encoding="utf-8")
    return proposal_path, reviews_root, proposal, targets


def test_load_and_verify_proposal_matching_hash_succeeds(tmp_path, monkeypatch):
    proposal_path, reviews_root, proposal, targets = _write_real_proposal_file(tmp_path, monkeypatch)
    expected_hash = compute_proposal_sha256(proposal_path)

    loaded = load_and_verify_proposal(proposal_path, expected_sha256=expected_hash)
    assert loaded == proposal

    # and the loaded dict is still subject to full structural validation downstream
    validated = validate_proposal_for_application(loaded, reviews_root=reviews_root, expected_count=2)
    assert len(validated) == 2


def test_load_and_verify_proposal_modified_content_rejected(tmp_path, monkeypatch):
    proposal_path, reviews_root, proposal, targets = _write_real_proposal_file(tmp_path, monkeypatch)
    expected_hash = compute_proposal_sha256(proposal_path)

    mutated = dict(proposal)
    mutated["disposition_events"][0]["reason"] = "a silently changed reason"
    proposal_path.write_text(json.dumps(mutated, indent=2), encoding="utf-8")

    with pytest.raises(ProposalBindingError, match="does not match"):
        load_and_verify_proposal(proposal_path, expected_sha256=expected_hash)


def test_load_and_verify_proposal_substituted_file_rejected(tmp_path, monkeypatch):
    proposal_path, reviews_root, proposal, targets = _write_real_proposal_file(tmp_path, monkeypatch)
    expected_hash = compute_proposal_sha256(proposal_path)

    proposal_path.write_text(json.dumps({"disposition_events": []}), encoding="utf-8")  # totally different file

    with pytest.raises(ProposalBindingError):
        load_and_verify_proposal(proposal_path, expected_sha256=expected_hash)


def test_load_and_verify_proposal_altered_scope_rejected(tmp_path, monkeypatch):
    proposal_path, reviews_root, proposal, targets = _write_real_proposal_file(tmp_path, monkeypatch, n=2)
    expected_hash = compute_proposal_sha256(proposal_path)

    extra = dict(proposal)
    third_target = targets[0]  # reuse a path for simplicity; content difference alone changes the hash
    extra["disposition_events"] = extra["disposition_events"] + [dict(extra["disposition_events"][0])]
    proposal_path.write_text(json.dumps(extra, indent=2), encoding="utf-8")

    with pytest.raises(ProposalBindingError):
        load_and_verify_proposal(proposal_path, expected_sha256=expected_hash)


def test_load_and_verify_proposal_failure_writes_nothing(tmp_path, monkeypatch):
    proposal_path, reviews_root, proposal, targets = _write_real_proposal_file(tmp_path, monkeypatch)
    wrong_hash = "0" * 64

    before_files = set(p for p in Path(".").rglob("*") if p.is_file())
    with pytest.raises(ProposalBindingError):
        load_and_verify_proposal(proposal_path, expected_sha256=wrong_hash)
    after_files = set(p for p in Path(".").rglob("*") if p.is_file())
    assert before_files == after_files  # nothing written anywhere


def test_load_and_verify_proposal_requires_non_blank_expected_hash(tmp_path, monkeypatch):
    proposal_path, reviews_root, proposal, targets = _write_real_proposal_file(tmp_path, monkeypatch)
    with pytest.raises(ProposalBindingError, match="non-empty"):
        load_and_verify_proposal(proposal_path, expected_sha256="")


def test_load_and_verify_proposal_rejects_malformed_hash_format(tmp_path, monkeypatch):
    proposal_path, reviews_root, proposal, targets = _write_real_proposal_file(tmp_path, monkeypatch)
    # _require_hex_sha256 raises the shared NoticeWriterValidationError
    # (ProposalBindingError is a subclass of it, not the reverse).
    with pytest.raises(NoticeWriterValidationError, match="SHA-256"):
        load_and_verify_proposal(proposal_path, expected_sha256="not-a-real-hash")


def test_load_and_verify_proposal_never_defaults_to_computed_hash(tmp_path, monkeypatch):
    """No default exists for expected_sha256 -- calling without it is a
    TypeError, never a silent pass."""
    proposal_path, reviews_root, proposal, targets = _write_real_proposal_file(tmp_path, monkeypatch)
    with pytest.raises(TypeError):
        load_and_verify_proposal(proposal_path)  # type: ignore[call-arg]


# =============================================================================
# F4 -- notice content wording
# =============================================================================

def test_notice_content_includes_authorized_statement(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    report = _apply(reviews_root, proposal, n=1)
    assert report.results[0].status == "WRITTEN"

    content = json.loads(_notice_path(targets[0]).read_text(encoding="utf-8"))
    assert content["authorized_statement"] == proposal["disposition_events"][0]["authorized_statement"]


def test_notice_wording_clarifies_not_independent_proof_of_authorization(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    _apply(reviews_root, proposal, n=1)
    content = json.loads(_notice_path(targets[0]).read_text(encoding="utf-8"))
    assert "does not" in content["note"] or "does NOT" in content["note"]
    assert "authorization" in content["note"].lower()
    assert "PHASE11_6_LEGACY_RECORD_DISPOSITION" in content["note"]


def test_directory_notice_wording_clarifies_not_independent_proof_of_authorization(tmp_path, monkeypatch):
    reviews_root, proposal, targets = _make_fixture(tmp_path, monkeypatch, n=1)
    _apply(reviews_root, proposal, n=1)
    text = (reviews_root / DIRECTORY_NOTICE_NAME).read_text(encoding="utf-8")
    assert "does not independently prove" in text
    assert "PHASE11_6_LEGACY_RECORD_DISPOSITION" in text
