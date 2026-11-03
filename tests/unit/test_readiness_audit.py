"""Read-only audit, LEG-EXEC preflight, and adversarial readiness cases."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from official_workspace import build_workspace

from railway_detection.annotation.readiness_audit import (
    LEG_EXEC_EXPECTED_OUTPUTS,
    LEG_EXEC_PINNED_PROPOSAL_SHA256,
    LEG_EXEC_PROPOSAL_RELATIVE,
    audit_ground_truth_readiness,
    leg_exec_preflight,
    render_markdown,
)
from railway_detection.evaluation import governance
from railway_detection.evaluation.execution_gate import assess_official_phase12_readiness

REPO_ROOT = Path(__file__).resolve().parents[2]


def _tree_digest(root: Path, *relative: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in relative:
        base = root / item
        for path in sorted(base.rglob("*")) if base.is_dir() else [base]:
            if path.is_file():
                out[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


# ------------------------------------------------------------------ the real repository


def test_real_audit_summarizes_the_legacy_corpus_without_touching_it():
    watched = ("data/ground_truth", "docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json")
    before = _tree_digest(REPO_ROOT, *watched)
    report = audit_ground_truth_readiness(REPO_ROOT)
    assert _tree_digest(REPO_ROOT, *watched) == before
    assert report["read_only"] is True
    summary = report["summary"]
    assert summary["record_count"] == 27
    assert summary["schema_versions"] == {"6.0.0": 27}
    assert summary["stage21_records"] == 0
    assert summary["promotion_eligible_pending_media_rehash"] == 0
    assert summary["bare_event_ids_shared_across_cohorts"] == [
        "event_001", "event_002", "event_003",
    ]
    assert summary["duplicate_cohort_event_identities"] == []
    assert report["reviewer_allowlist"]["records_with_blocklisted_reviewer"] == 27
    assert report["legacy"]["duplicate_review_timestamps"] == {"2026-10-12T16:51:21Z": 27}
    assert report["legacy"]["superseded_proposal_references"] == 27
    for cohort, row in report["cohorts"].items():
        assert row["missing_requirement"], cohort
    assert all(len(r["sha256"]) == 64 for r in report["records"])
    assert all(not r["promotion_eligible_pending_media_rehash"] for r in report["records"])
    assert report["promotion_receipt"]["status"] == "absent_or_invalid"
    assert "Execution authorized: **True**" in render_markdown(report)


def test_audit_is_deterministic():
    first = json.dumps(audit_ground_truth_readiness(REPO_ROOT), sort_keys=True)
    second = json.dumps(audit_ground_truth_readiness(REPO_ROOT), sort_keys=True)
    assert first == second


def test_leg_exec_preflight_verifies_inputs_and_never_writes():
    reviews = ("data/ground_truth/reviews",)
    before = _tree_digest(REPO_ROOT, *reviews)
    pre = leg_exec_preflight(REPO_ROOT)
    assert _tree_digest(REPO_ROOT, *reviews) == before
    assert pre["execution_authorized"] is True
    assert pre["inputs_verified"] is True and pre["proposal_hash_matches_pin"] is True
    assert pre["planned_source_records"] == 27
    assert pre["planned_output_targets"] == LEG_EXEC_EXPECTED_OUTPUTS == 28
    assert pre["writes_performed"] == 0
    assert set(pre["planned_statuses"]) == {"WOULD_SKIP_ALREADY_DONE_MATCHING"}
    assert pre["directory_notice_status"] == "WOULD_SKIP_ALREADY_DONE_MATCHING"
    assert len(
        list((REPO_ROOT / "data/ground_truth/reviews").rglob("*.INVALIDATION_NOTICE.json"))
    ) == 27
    assert (REPO_ROOT / "data/ground_truth/reviews/_INTEGRITY_NOTICE.md").exists()


def _copy_leg_exec_inputs(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / LEG_EXEC_PROPOSAL_RELATIVE, root / LEG_EXEC_PROPOSAL_RELATIVE)
    shutil.copytree(
        REPO_ROOT / "data/ground_truth/reviews",
        root / "data/ground_truth/reviews",
        ignore=shutil.ignore_patterns("*.md"),
    )
    return root


def test_leg_exec_preflight_verifies_a_faithful_copy_and_rejects_a_changed_source(tmp_path):
    """The preflight runs at the given root, so a byte-faithful copy verifies; a changed
    source record voids it."""
    root = _copy_leg_exec_inputs(tmp_path)
    pre = leg_exec_preflight(root)
    assert pre["inputs_verified"] is True and pre["planned_source_records"] == 27
    assert pre["execution_authorized"] is False  # no recorded authorization in the copy
    victim = next((root / "data/ground_truth/reviews").rglob("*_review.json"))
    victim.write_bytes(victim.read_bytes() + b"\n")
    changed = leg_exec_preflight(root)
    assert changed["inputs_verified"] is False and changed["execution_authorized"] is False


def test_leg_exec_preflight_rejects_an_edited_proposal(tmp_path):
    root = _copy_leg_exec_inputs(tmp_path)
    proposal = root / LEG_EXEC_PROPOSAL_RELATIVE
    proposal.write_bytes(proposal.read_bytes() + b" ")  # one byte
    pre = leg_exec_preflight(root)
    assert pre["inputs_verified"] is False
    assert pre["proposal_hash_matches_pin"] is False
    assert pre["actual_proposal_sha256"] != LEG_EXEC_PINNED_PROPOSAL_SHA256
    assert "ProposalBindingError" in pre["input_error"]
    assert pre["execution_authorized"] is False


def test_leg_exec_preflight_reports_a_missing_proposal(tmp_path):
    pre = leg_exec_preflight(tmp_path)
    assert pre["inputs_verified"] is False and "proposal missing" in pre["input_error"]


def test_a_general_authorization_never_flips_leg_exec(tmp_path, monkeypatch):
    """Even a fully authorized Phase 12 workspace carries no LEG-EXEC authorization."""
    ws = build_workspace(tmp_path, monkeypatch)
    assert ws.assess().ready
    assert leg_exec_preflight(ws.root)["execution_authorized"] is False


# --------------------------------------------------------------- synthetic valid corpus


def test_audit_recognizes_a_valid_synthetic_corpus_and_its_receipt(tmp_path, monkeypatch):
    ws = build_workspace(tmp_path, monkeypatch)
    report = audit_ground_truth_readiness(ws.root)
    # three primary records plus the independent second review RD-043 requires for the engine event
    assert report["summary"]["stage21_records"] == 4
    assert report["summary"]["promotion_eligible_pending_media_rehash"] == 4
    assert all(row["missing_requirement"] is None for row in report["cohorts"].values())
    assert report["promotion_receipt"]["status"] == "valid"
    assert report["reviewer_allowlist"]["records_with_blocklisted_reviewer"] == 0


def test_audit_flags_a_record_changed_after_the_receipt(tmp_path, monkeypatch):
    ws = build_workspace(tmp_path, monkeypatch)
    victim = next((ws.root / "data/ground_truth/reviews").rglob("*_review.json"))
    record = json.loads(victim.read_text())
    record["general_review_notes"] = "edited after issue"
    victim.write_text(json.dumps(record), encoding="utf-8")
    report = audit_ground_truth_readiness(ws.root)
    assert report["promotion_receipt"]["status"] == "absent_or_invalid"
    assert report["promotion_receipt"]["code"] == "STAGE21_PROMOTION_RECEIPT_INVALID"


def test_audit_marks_unallowlisted_reviewers_ineligible(tmp_path, monkeypatch):
    ws = build_workspace(tmp_path, monkeypatch)
    allowlist = ws.root / "data/ground_truth/authorized_reviewers.json"
    allowlist.write_text(json.dumps({"authorized_reviewers": ["someone.else@example.org"]}))
    report = audit_ground_truth_readiness(ws.root)
    assert report["summary"]["promotion_eligible_pending_media_rehash"] == 0
    assert report["reviewer_allowlist"]["records_with_reviewer_not_on_allowlist"] == 4


def test_audit_survives_an_unusable_allowlist(tmp_path, monkeypatch):
    ws = build_workspace(tmp_path, monkeypatch)
    (ws.root / "data/ground_truth/authorized_reviewers.json").write_text("{not json")
    report = audit_ground_truth_readiness(ws.root)
    assert report["reviewer_allowlist"]["loaded"] is False
    assert report["reviewer_allowlist"]["error"]


# ------------------------------------------------------------------- adversarial gate cases


def test_forged_manifest_approvals_cannot_clear_cohort_or_stage21_blockers(tmp_path):
    root = tmp_path / "repo"
    manifest = root / "data/manifests/phase12_evaluation_inputs.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "phase12-evaluation-inputs/1",
                "evidence_classification": "real",
                "approval_status": "APPROVED",
                "cohort_approved": True,
                "stage21_status": "VALID",
                "eval_auth": True,
                "partitions": {"train": ["a"], "val": ["b"], "test": ["c"]},
                "events": [],
            }
        )
    )
    verdict = assess_official_phase12_readiness(root)
    assert not verdict.ready
    assert {"STAGE21_RECORDS_MISSING", "COHORT_APPROVAL_MISSING", "EVAL_AUTH_NOT_GRANTED"} <= set(
        verdict.blocker_codes
    )


def test_legacy_records_with_forged_stage21_version_string_are_rejected(tmp_path):
    root = tmp_path / "repo"
    reviews = root / "data/ground_truth/reviews/train_events"
    reviews.mkdir(parents=True)
    source = next((REPO_ROOT / "data/ground_truth/reviews/train_events").glob("*_review.json"))
    legacy = json.loads(source.read_text())
    legacy["schema_version"] = "8.1.0-stage2.1"  # relabelled, still a legacy body
    (reviews / "event_001_review.json").write_text(json.dumps(legacy))
    verdict = assess_official_phase12_readiness(root)
    assert "GROUND_TRUTH_SCHEMA_INVALID" in verdict.blocker_codes
    assert "COHORT_APPROVAL_MISSING" in verdict.blocker_codes
    report = audit_ground_truth_readiness(root)
    assert report["summary"]["promotion_eligible_pending_media_rehash"] == 0


def test_allowlist_containing_a_blocklisted_identity_is_untrustworthy(tmp_path, monkeypatch):
    ws = build_workspace(tmp_path, monkeypatch)
    allowlist = ws.root / governance.ALLOWLIST_RELATIVE
    allowlist.write_text(json.dumps({"authorized_reviewers": ["human_researcher_lead"]}))
    assert "AUTHORITY_ALLOWLIST_UNAVAILABLE" in ws.assess().blocker_codes


@pytest.mark.parametrize("reviewer", ["", "reviewer", "unknown", "human_researcher_lead"])
def test_blocklisted_reviewer_ids_never_reach_eligibility(reviewer):
    from railway_detection.annotation.stage2_1_schema import REVIEWER_ID_BLOCKLIST

    assert reviewer.strip().lower() in REVIEWER_ID_BLOCKLIST
