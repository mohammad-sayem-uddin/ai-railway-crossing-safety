"""LEG-EXEC: authorization binding, exact outputs, idempotency, interruption, adversarial cases.

The pinned proposal embeds repo-relative paths, so each test executes against a faithful COPY of
the proposal, the 27 legacy records and the allowlist under a tmp root. The real repository is
never written to by these tests (asserted at the end).
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from railway_detection.annotation import invalidation_notice_writer as writer
from railway_detection.annotation.leg_exec import (
    LEG_EXEC_AUTH_RELATIVE,
    PINNED_PROPOSAL_SHA256,
    PROPOSAL_RELATIVE,
    LegExecError,
    build_authorization_record,
    execute_leg_exec,
    verify_authorization,
)
from railway_detection.annotation.notices import (
    excused_legacy_records,
    invalid_notices,
    scan_notices,
    verify_invalidation_notice,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 12, 1, tzinfo=UTC)
RESEARCHER = "raihankabirrahu@gmail.com"
STATEMENT = "Synthetic-test statement of authorization (not a real authorization)."


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): _sha(p) for p in sorted(root.rglob("*")) if p.is_file()}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / PROPOSAL_RELATIVE, root / PROPOSAL_RELATIVE)
    shutil.copytree(
        REPO_ROOT / "data/ground_truth/reviews",
        root / "data/ground_truth/reviews",
        ignore=shutil.ignore_patterns("*INVALIDATION_NOTICE*", "_INTEGRITY_NOTICE.md", "*.md"),
    )
    shutil.copyfile(
        REPO_ROOT / "data/ground_truth/authorized_reviewers.json",
        root / "data/ground_truth/authorized_reviewers.json",
    )
    return root


def _authorize(root: Path, *, by: str = RESEARCHER, **overrides) -> dict:
    record = build_authorization_record(
        root=root,
        authorized_by=by,
        authorized_at_utc="2026-10-16T00:00:00Z",
        statement=STATEMENT,
        recorded_by={
            "kind": "agent_transcription",
            "identity": "test",
            "transcription_source": "unit test",
        },
    )
    record.update(overrides)
    if "record_sha256" not in overrides:
        from railway_detection.annotation.leg_exec import _record_sha

        record["record_sha256"] = _record_sha(record)
    path = root / LEG_EXEC_AUTH_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def _originals(root: Path) -> dict[str, str]:
    reviews = root / "data/ground_truth/reviews"
    return {k: v for k, v in _tree(reviews).items() if k.endswith("_review.json")}


# ------------------------------------------------------------------------- success path


def test_execution_writes_exactly_28_notices_and_leaves_originals_untouched(repo: Path):
    _authorize(repo)
    originals = _originals(repo)
    assert len(originals) == 27
    before = _tree(repo)
    report = execute_leg_exec(repo, now=NOW)
    after = _tree(repo)

    assert report["completed"] is True and report["originals_byte_identical"] is True
    assert report["authorization_attestation"] == "recorded_statement_unsigned"
    assert report["ground_truth_created"] is False
    assert _originals(repo) == originals
    new = sorted(set(after) - set(before))
    assert len(new) == 28 == len(report["expected_output_inventory"])
    assert new == sorted(
        f"data/ground_truth/reviews/{n}" for n in report["expected_output_inventory"]
    )
    assert sum(1 for n in new if n.endswith(".INVALIDATION_NOTICE.json")) == 27
    assert any(n.endswith("_INTEGRITY_NOTICE.md") for n in new)
    # nothing else changed anywhere in the tree
    assert {k: v for k, v in after.items() if k in before} == before
    assert set(report["output_sha256"]) == set(report["expected_output_inventory"])
    assert report["source_record_sha256"] and len(report["source_record_sha256"]) == 27


def test_every_notice_verifies_against_its_unchanged_legacy_record(repo: Path):
    _authorize(repo)
    execute_leg_exec(repo, now=NOW)
    reviews = repo / "data/ground_truth/reviews"
    notices = scan_notices(reviews)
    assert len(notices) == 27 and all(n.valid for n in notices)
    assert len(excused_legacy_records(reviews)) == 27 and invalid_notices(reviews) == []


def test_invalidation_creates_no_stage21_record_and_approves_nothing(repo: Path):
    _authorize(repo)
    execute_leg_exec(repo, now=NOW)
    reviews = repo / "data/ground_truth/reviews"
    schemas = {
        json.loads(p.read_text()).get("schema_version") for p in reviews.rglob("*_review.json")
    }
    assert schemas == {"6.0.0"}
    assert not (repo / "data/ground_truth/approved").exists()


def test_repeat_execution_is_idempotent(repo: Path):
    _authorize(repo)
    first = execute_leg_exec(repo, now=NOW)
    snapshot = _tree(repo)
    second = execute_leg_exec(repo, now=NOW)
    assert second["completed"] and second["new_files_this_run"] == []
    assert _tree(repo) == snapshot
    assert {r["status"] for r in second["result_statuses"]["records"]} == {
        "SKIPPED_ALREADY_DONE_MATCHING"
    }
    assert second["output_sha256"] == first["output_sha256"]


def test_interrupted_execution_resumes_without_duplicating_or_overwriting(repo: Path, monkeypatch):
    _authorize(repo)
    original = writer._process_one_record
    calls = {"n": 0}

    def flaky(ev, target, output):
        calls["n"] += 1
        if calls["n"] == 11:
            raise OSError("disk full (injected)")
        return original(ev, target, output)

    monkeypatch.setattr(writer, "_process_one_record", flaky)
    try:
        partial = execute_leg_exec(repo, now=NOW)
    except Exception as exc:  # the writer may surface the failure either way; both are safe
        partial = {"completed": False, "error": str(exc)}
    assert partial["completed"] is False
    written = [p for p in (repo / "data/ground_truth/reviews").rglob("*INVALIDATION_NOTICE.json")]
    assert 0 < len(written) < 27
    first_hashes = {p: _sha(p) for p in written}
    monkeypatch.setattr(writer, "_process_one_record", original)
    resumed = execute_leg_exec(repo, now=NOW)
    assert resumed["completed"] is True
    assert all(_sha(p) == h for p, h in first_hashes.items())  # earlier notices untouched
    assert len(list((repo / "data/ground_truth/reviews").rglob("*INVALIDATION_NOTICE.json"))) == 27


# ------------------------------------------------------------------------ authorization


def test_no_authorization_means_nothing_is_written(repo: Path):
    before = _tree(repo)
    with pytest.raises(LegExecError) as info:
        execute_leg_exec(repo, now=NOW)
    assert info.value.code == "LEG_EXEC_NOT_AUTHORIZED"
    assert _tree(repo) == before


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda r: r.update(authorization_statement="edited"), "LEG_EXEC_AUTH_INVALID"),
        (lambda r: r.update(authorized_by="someone@else.org"), "LEG_EXEC_AUTH_INVALID"),
        (lambda r: r.update(ready=True), "LEG_EXEC_AUTH_INVALID"),
        (
            lambda r: r.update(attestation={"type": "ED25519", "signature": "AAAA"}),
            "LEG_EXEC_AUTH_INVALID",
        ),
        (lambda r: r.update(authorized_at_utc="2999-01-01T00:00:00Z"), "LEG_EXEC_AUTH_INVALID"),
        (lambda r: r.update(authorization_statement=" "), "LEG_EXEC_AUTH_INVALID"),
        (
            lambda r: r.update(recorded_by={"kind": "agent_transcription", "identity": "x"}),
            "LEG_EXEC_AUTH_INVALID",
        ),
        (lambda r: r["scope"].update(output_target_count=27), "LEG_EXEC_AUTH_SCOPE_MISMATCH"),
        (
            lambda r: r["scope"].update(pinned_proposal_sha256="0" * 64),
            "LEG_EXEC_AUTH_SCOPE_MISMATCH",
        ),
        (
            lambda r: r["scope"].update(write_operation="delete originals"),
            "LEG_EXEC_AUTH_SCOPE_MISMATCH",
        ),
    ],
)
def test_forged_or_edited_authorizations_never_execute(repo: Path, mutate, code):
    record = _authorize(repo)
    broken = json.loads(json.dumps(record))
    mutate(broken)
    path = repo / LEG_EXEC_AUTH_RELATIVE
    # Re-derive the self-hash for scope edits so only the scope check can catch them.
    if code == "LEG_EXEC_AUTH_SCOPE_MISMATCH":
        from railway_detection.annotation.leg_exec import _record_sha

        broken["record_sha256"] = _record_sha(broken)
    path.write_text(json.dumps(broken), encoding="utf-8")
    before = _tree(repo)
    with pytest.raises(LegExecError) as info:
        execute_leg_exec(repo, now=NOW)
    assert info.value.code == code
    assert _tree(repo) == before


def test_authorization_is_voided_by_a_changed_source_record(repo: Path):
    _authorize(repo)
    victim = next((repo / "data/ground_truth/reviews").rglob("*_review.json"))
    victim.write_bytes(victim.read_bytes() + b"\n")
    before = _tree(repo)
    with pytest.raises(LegExecError) as info:
        execute_leg_exec(repo, now=NOW)
    assert info.value.code in {
        "LEG_EXEC_SOURCES_CHANGED",
        "LEG_EXEC_PREFLIGHT_FAILED",
        "LEG_EXEC_PLAN_NOT_CLEAN",
    }
    assert _tree(repo) == before


def test_authorization_is_voided_by_an_edited_proposal(repo: Path):
    _authorize(repo)
    proposal = repo / PROPOSAL_RELATIVE
    proposal.write_bytes(proposal.read_bytes() + b" ")
    before = _tree(repo)
    with pytest.raises(LegExecError) as info:
        execute_leg_exec(repo, now=NOW)
    assert info.value.code == "LEG_EXEC_PROPOSAL_CHANGED"
    assert _tree(repo) == before


def test_missing_source_record_aborts_before_any_write(repo: Path):
    _authorize(repo)
    next((repo / "data/ground_truth/reviews").rglob("*_review.json")).unlink()
    before = _tree(repo)
    with pytest.raises(LegExecError):
        execute_leg_exec(repo, now=NOW)
    assert _tree(repo) == before


def test_a_pre_existing_conflicting_output_aborts_the_run(repo: Path):
    _authorize(repo)
    target = next((repo / "data/ground_truth/reviews").rglob("*_review.json"))
    squatter = target.with_name(target.name.replace(".json", ".INVALIDATION_NOTICE.json"))
    squatter.write_text('{"someone else\'s file": true}')
    before = _tree(repo)
    with pytest.raises(LegExecError) as info:
        execute_leg_exec(repo, now=NOW)
    assert info.value.code == "LEG_EXEC_PLAN_NOT_CLEAN"
    assert _tree(repo) == before  # nothing written, nothing overwritten


def test_an_unexpected_extra_output_is_detected(repo: Path, monkeypatch):
    _authorize(repo)
    original = writer.apply_invalidation_notices

    def with_stray(*args, **kwargs):
        report = original(*args, **kwargs)
        (repo / "data/ground_truth/reviews/STRAY.json").write_text("{}")
        return report

    monkeypatch.setattr(
        "railway_detection.annotation.leg_exec.apply_invalidation_notices", with_stray
    )
    with pytest.raises(LegExecError) as info:
        execute_leg_exec(repo, now=NOW)
    assert info.value.code == "UNEXPECTED_OUTPUT"


def test_an_original_changing_during_the_run_is_detected(repo: Path, monkeypatch):
    _authorize(repo)
    original = writer.apply_invalidation_notices

    def tampering(*args, **kwargs):
        report = original(*args, **kwargs)
        victim = next((repo / "data/ground_truth/reviews").rglob("*_review.json"))
        victim.write_bytes(victim.read_bytes() + b" ")
        return report

    monkeypatch.setattr(
        "railway_detection.annotation.leg_exec.apply_invalidation_notices", tampering
    )
    with pytest.raises(LegExecError) as info:
        execute_leg_exec(repo, now=NOW)
    assert info.value.code == "ORIGINALS_CHANGED"


# ------------------------------------------------------------------------- notices


def test_notice_verification_rejects_every_kind_of_inconsistency(repo: Path):
    _authorize(repo)
    execute_leg_exec(repo, now=NOW)
    reviews = repo / "data/ground_truth/reviews"
    notice = next(reviews.rglob("*.INVALIDATION_NOTICE.json"))
    record = notice.with_name(notice.name.replace(".INVALIDATION_NOTICE.json", ".json"))
    pristine = record.read_bytes()
    assert verify_invalidation_notice(notice, reviews).valid

    record.write_bytes(pristine + b"\n")  # record changed after the notice
    assert "changed after" in verify_invalidation_notice(notice, reviews).problem
    record.write_bytes(pristine)

    data = json.loads(notice.read_text())
    notice.write_text(json.dumps({**data, "disposition": "OK"}))
    assert not verify_invalidation_notice(notice, reviews).valid
    notice.write_text(json.dumps({**data, "applies_to_file": "somewhere/else_review.json"}))
    assert "does not name" in verify_invalidation_notice(notice, reviews).problem
    notice.write_text("{broken")
    assert "unreadable" in verify_invalidation_notice(notice, reviews).problem
    notice.write_text(json.dumps(data))
    record.unlink()
    assert "missing" in verify_invalidation_notice(notice, reviews).problem
    record.write_bytes(pristine)

    stage21 = json.loads(pristine)
    stage21["schema_version"] = "8.1.0-stage2.1"
    forged = json.dumps(stage21).encode()
    record.write_bytes(forged)
    notice.write_text(
        json.dumps(
            {**data, "applies_to_file_sha256_at_notice_time": hashlib.sha256(forged).hexdigest()}
        )
    )
    assert (
        "cannot invalidate or excuse a Stage-2.1"
        in verify_invalidation_notice(notice, reviews).problem
    )


# ------------------------------------------------------------- the real repository


def test_real_repository_state_is_consistent_whether_or_not_leg_exec_has_run():
    reviews = REPO_ROOT / "data/ground_truth/reviews"
    originals = list(reviews.rglob("*_review.json"))
    assert len(originals) == 27
    notices = list(reviews.rglob("*.INVALIDATION_NOTICE.json"))
    assert len(notices) in (0, 27)
    if notices:
        assert all(n.valid for n in scan_notices(reviews))
        assert (reviews / "_INTEGRITY_NOTICE.md").is_file()
        assert verify_authorization(REPO_ROOT)["operation"] == "LEG-EXEC"
    assert _sha(REPO_ROOT / PROPOSAL_RELATIVE) == PINNED_PROPOSAL_SHA256


# ------------------------------------------- gates after invalidation (notice-aware loading)

import sys  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

from official_workspace import build_workspace  # noqa: E402

from railway_detection.annotation.evaluation_readiness_gate import evaluate_readiness  # noqa: E402
from railway_detection.evaluation.execution_gate import (  # noqa: E402
    assess_official_phase12_readiness,
)
from railway_detection.evaluation.ground_truth_loader import (  # noqa: E402
    CandidateProposalRefused,
    load_approved_ground_truth_with_hashes,
)


def test_gates_stop_reporting_invalidated_legacy_records_as_pending_problems(repo: Path):
    before = assess_official_phase12_readiness(repo, now=NOW)
    assert sum(b.code == "LEGACY_OR_UNKNOWN_GROUND_TRUTH_SCHEMA" for b in before.blockers) == 27
    _authorize(repo)
    execute_leg_exec(repo, now=NOW)
    after = assess_official_phase12_readiness(repo, now=NOW)
    assert "LEGACY_OR_UNKNOWN_GROUND_TRUTH_SCHEMA" not in after.blocker_codes
    stage21 = next(b for b in after.blockers if b.code == "STAGE21_RECORDS_MISSING")
    assert "27 legacy record(s) are invalidated" in stage21.detail
    assert any("27 legacy review record(s) excluded" in e for e in after.evidence)
    assert "COHORT_APPROVAL_MISSING" in after.blocker_codes  # approval is still absent
    assert "STAGE21_RECORDS_MISSING" in after.blocker_codes


def test_loader_and_media_gate_accept_verified_notices_but_not_forged_ones(repo: Path):
    _authorize(repo)
    execute_leg_exec(repo, now=NOW)
    reviews = repo / "data/ground_truth/reviews"
    truths, hashes = load_approved_ground_truth_with_hashes(reviews, qualify_event_ids=True)
    assert truths == [] and hashes == {}  # legacy records are neither loaded nor refused
    verdict = evaluate_readiness(
        reviews_dir=reviews,
        active_proposal_sha256_by_event={},
        media_sha256_registry={},
        allowlist_path=repo / "data/ground_truth/authorized_reviewers.json",
        media_file_paths={},
    )
    assert not verdict.ready and any("NO_RECORDS" in b for b in verdict.blockers)
    assert not any("LEGACY" in b for b in verdict.blockers)

    notice = next(reviews.rglob("*.INVALIDATION_NOTICE.json"))
    notice.write_text("{broken")
    with pytest.raises(CandidateProposalRefused):
        load_approved_ground_truth_with_hashes(reviews)
    verdict = evaluate_readiness(
        reviews_dir=reviews,
        active_proposal_sha256_by_event={},
        media_sha256_registry={},
        allowlist_path=repo / "data/ground_truth/authorized_reviewers.json",
        media_file_paths={},
    )
    assert any("REVIEWS_LOAD_FAILED" in b for b in verdict.blockers)
    assert (
        "INVALIDATION_NOTICE_INVALID"
        in assess_official_phase12_readiness(repo, now=NOW).blocker_codes
    )


def test_unnotified_legacy_records_alongside_valid_records_still_block(tmp_path, monkeypatch):
    ws = build_workspace(tmp_path, monkeypatch)
    assert ws.assess().ready
    root = ws.root
    (root / "docs").mkdir(exist_ok=True)
    shutil.copyfile(REPO_ROOT / PROPOSAL_RELATIVE, root / PROPOSAL_RELATIVE)
    for cohort_dir in (REPO_ROOT / "data/ground_truth/reviews").iterdir():
        if cohort_dir.is_dir():
            for file in cohort_dir.glob("*_review.json"):
                target = root / "data/ground_truth/reviews" / cohort_dir.name / file.name
                shutil.copyfile(file, target)
    blocked = ws.assess()
    assert not blocked.ready
    assert "LEGACY_OR_UNKNOWN_GROUND_TRUTH_SCHEMA" in blocked.blocker_codes

    _authorize(root, by="pilot.reviewer@synthetic.example.com")
    execute_leg_exec(root, now=NOW)
    # Invalidated legacy history no longer blocks; the genuine records, receipt and
    # authorization (which bind only active records) are still valid.
    assert ws.assess().ready, ws.assess().blockers
