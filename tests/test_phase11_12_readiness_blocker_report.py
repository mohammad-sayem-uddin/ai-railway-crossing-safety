"""Phase 11.12: machine-readable blocker reports and batch-integrity wiring.

Covers the two gaps closed in this phase:
  * the gate now reports structured, machine-readable blockers alongside the
    legacy text form;
  * the gate now runs `check_review_batch_integrity` over the APPROVED set, so
    the short-burst batch signature Phase 11.1 found in the 27 legacy records
    cannot reach evaluation through an otherwise schema-valid corpus.

All fixtures are synthetic and live under pytest's temporary directory. No
production review record is read, promoted, or modified.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from railway_detection.annotation.evaluation_readiness_gate import (
    GROUND_TRUTH_APPROVAL_AUTHORITY,
    ReadinessBlocker,
    evaluate_readiness,
)
from test_phase11_12_readiness_gate import _allowlist, _gate, _three_records


def test_blocker_detail_renders_the_legacy_text_form():
    blocker = ReadinessBlocker("NOT_APPROVED", "event_001", "")
    assert blocker.as_text() == "NOT_APPROVED:event_001"
    detailed = ReadinessBlocker("SCHEMA_VALIDATION_FAILED", "event_002", "missing field")
    assert detailed.as_text() == "SCHEMA_VALIDATION_FAILED:event_002: missing field"
    headline = ReadinessBlocker("NO_RECORDS", None, "zero in-scope records supplied")
    assert headline.as_text() == "NO_RECORDS: zero in-scope records supplied"


def test_structured_blockers_accompany_every_text_blocker(tmp_path: Path):
    verdict = evaluate_readiness(
        records=[],
        active_proposal_sha256_by_event={},
        media_sha256_registry={},
        allowlist_path=_allowlist(tmp_path),
        media_file_paths={},
    )
    assert not verdict.ready
    assert len(verdict.blocker_details) == len(verdict.blockers)
    assert verdict.blocker_codes == ("NO_RECORDS",)
    assert verdict.blocker_details[0].code == "NO_RECORDS"


def test_verdict_report_is_json_serializable_and_names_approval_authority(tmp_path: Path):
    records, active, registry, paths = _three_records(tmp_path)
    records[0]["adjudication_status"] = "DISPUTED"
    records[0]["adjudication_history"][-1]["status_set"] = "DISPUTED"
    report = _gate(tmp_path, records, active, registry, paths).to_dict()

    round_tripped = json.loads(json.dumps(report))
    assert round_tripped["ready"] is False
    assert round_tripped["blocker_count"] == len(round_tripped["blockers"])
    assert "UNRESOLVED_DISAGREEMENT" in round_tripped["blocker_codes"]
    for blocker in round_tripped["blockers"]:
        assert set(blocker) == {"code", "event_id", "detail"}


def test_ready_verdict_still_defers_ground_truth_approval_to_the_researcher(tmp_path: Path):
    records, active, registry, paths = _three_records(tmp_path)
    verdict = _gate(tmp_path, records, active, registry, paths)
    assert verdict.ready
    report = verdict.to_dict()
    assert report["mechanically_valid"] is True
    assert report["researcher_approval_still_required"] is True
    assert report["ground_truth_approval_authority"] == GROUND_TRUTH_APPROVAL_AUTHORITY
    assert GROUND_TRUTH_APPROVAL_AUTHORITY == "human_researcher_only"
    assert any("researcher signature" in item for item in verdict.evidence)


def _overlap_one_reviewer(records: list[dict]) -> None:
    """Make every record claim the same reviewer and the same review window.

    Each window stays individually schema-plausible, so this is only caught by
    the batch-level overlap check, not by per-record schema validation.
    """
    window = records[0]["reviewer_metadata"]
    for record in records:
        record["reviewer_metadata"]["reviewer_id"] = window["reviewer_id"]
        record["reviewer_metadata"]["review_start_utc"] = window["review_start_utc"]
        record["reviewer_metadata"]["review_end_utc"] = window["review_end_utc"]


def test_overlapping_sessions_for_one_reviewer_block_readiness(tmp_path: Path):
    """Schema-valid records are still refused when one reviewer's windows overlap."""
    records, active, registry, paths = _three_records(tmp_path)
    _overlap_one_reviewer(records)

    verdict = _gate(tmp_path, records, active, registry, paths)
    assert not verdict.ready
    assert any(code.startswith("BATCH_INTEGRITY:") for code in verdict.blocker_codes)


def test_batch_integrity_blockers_carry_their_underlying_code(tmp_path: Path):
    records, active, registry, paths = _three_records(tmp_path)
    _overlap_one_reviewer(records)

    verdict = _gate(tmp_path, records, active, registry, paths)
    integrity = [b for b in verdict.blocker_details if b.code.startswith("BATCH_INTEGRITY:")]
    assert integrity, "expected at least one batch-integrity blocker"
    assert all(b.event_id for b in integrity)
    assert any("OVERLAPPING_REVIEW_SESSIONS" in b.code for b in integrity)


def test_sequential_sessions_for_one_reviewer_are_accepted(tmp_path: Path):
    """The overlap check must not reject genuinely sequential reviews."""
    records, active, registry, paths = _three_records(tmp_path)
    verdict = _gate(tmp_path, records, active, registry, paths)
    assert verdict.ready
    assert not any(code.startswith("BATCH_INTEGRITY:") for code in verdict.blocker_codes)
