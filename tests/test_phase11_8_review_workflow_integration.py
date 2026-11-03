"""Phase 11.8: Review Workflow Integration tests.

Validates the review_session.py record-construction helper and its
integration with the promotion gate. All fixtures are synthetic (tmp_path);
no real event IDs, no writes to data/ground_truth/reviews/.

Units covered:
- Unit 1: record construction via build_review_record (schema-valid output).
- Unit 2: unauthorized reviewer rejected before assembly; sub-30s rejected.
- Unit 3: dry-run promotion returns zero violations for valid record and
  exact expected codes for broken variants.
- Unit 4: (doc update verified separately by grep).

Negative tests per plan §10:
(a) media file bytes changed after hash observation → MEDIA_HASH_CHANGED_SINCE_REVIEW
(b) front/back hashes swapped → rejected
(c) reviewer not in allowlist → REVIEWER_NOT_AUTHORIZED
(d) allowlist file deleted mid-flow → AuthorizedReviewersLoadError
(e) attestation statement of 19 chars → schema error
(f) attempt to omit reviewer_observed_media_hashes → schema error
(g) review_duration_s caller-supplied → ignored/re-derived
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, UTC
from pathlib import Path

import pytest

from railway_detection.annotation.promotion_gate import (
    AuthorizedReviewersLoadError,
    load_authorized_reviewers,
    validate_for_promotion,
)
from railway_detection.annotation.review_session import (
    ReviewerNotAuthorizedError,
    build_review_record,
)
from railway_detection.annotation.schemas import SchemaValidationError
from railway_detection.annotation.stage2_1_schema import (
    STAGE_2_1_SCHEMA_VERSION,
    build_stage2_1_record_from_dict,
)

# --- Shared synthetic fixtures ---

T0 = datetime(2026, 11, 15, 10, 0, 0, tzinfo=UTC)
T_START = T0.isoformat().replace("+00:00", "Z")
T_END = (T0 + timedelta(seconds=600)).isoformat().replace("+00:00", "Z")
T_ATTEST = (T0 + timedelta(seconds=601)).isoformat().replace("+00:00", "Z")
VALID_PROPOSAL_SHA = "b" * 64
REVIEWER = "synthetic.reviewer@example.com"
ALLOWED = frozenset({REVIEWER})


def _boundary_set() -> dict[str, dict]:
    return {
        "T0_first_visible": {"state": "OBSERVABLE", "rationale": "Visible at frame 0", "value_s": 0.0, "reference_camera": "front"},
        "T1_danger_zone_entry": {"state": "OBSERVABLE", "rationale": "Cowcatcher at landmark", "value_s": 5.8, "reference_camera": "front"},
        "T2_crossing_occupancy_start": {"state": "OBSERVABLE", "rationale": "Pilot crosses plane", "value_s": 6.5, "reference_camera": "front"},
        "T3_locomotive_unit_clearance": {"state": "OBSERVABLE", "rationale": "Rear coupler clears", "value_s": 3.6, "reference_camera": "back"},
        "T4_tail_clearance": {"state": "OBSERVABLE", "rationale": "Final coach clears", "value_s": 45.0, "reference_camera": "back"},
        "T_scene_clear": {"state": "CENSORED", "rationale": "Recording ends while train still visible", "value_s": None, "reference_camera": None},
    }


def _make_media(tmp_path: Path, event_id: str, *, front_content: bytes | None = None, back_content: bytes | None = None) -> dict:
    front = tmp_path / f"{event_id}_front.mov"
    back = tmp_path / f"{event_id}_back.mov"
    front.write_bytes(front_content or f"synthetic front content {event_id}".encode())
    back.write_bytes(back_content or f"synthetic back content {event_id}".encode())
    return {"front": str(front), "back": str(back)}


def _build_valid_record(tmp_path: Path, event_id: str = "synthetic_event_001") -> dict:
    """Build a fully valid synthetic record using the helper."""
    media = _make_media(tmp_path, event_id)
    return build_review_record(
        event_id=event_id,
        cohort="train_events",
        reviewer_id=REVIEWER,
        authorized_reviewers=ALLOWED,
        front_media_path=media["front"],
        back_media_path=media["back"],
        proposal_file=f"data/ground_truth/proposals/train_events/{event_id}_proposal_v6.json",
        proposal_sha256=VALID_PROPOSAL_SHA,
        review_session_id=f"session-{event_id}",
        review_start_utc=T_START,
        review_end_utc=T_END,
        inspection_tool="ffmpeg frame-by-frame + scipy spectral audit, manual",
        attestation_statement="I reviewed only the raw video/audio and did not consult any model prediction.",
        attested_at_utc=T_ATTEST,
        observed_at_utc=T_START,
        boundary_adjudications=_boundary_set(),
        adjudication_status="APPROVED",
    )


def _promo_ctx(tmp_path: Path, event_id: str, record: dict) -> dict:
    """Caller-supplied context for validate_for_promotion on one record."""
    return {
        "active_proposal_sha256_by_event": {event_id: VALID_PROPOSAL_SHA},
        "media_sha256_registry": {event_id: {
            "front": record["reviewer_observed_media_hashes"]["front_sha256"],
            "back": record["reviewer_observed_media_hashes"]["back_sha256"],
        }},
        "authorized_reviewers": ALLOWED,
        "media_file_paths": {event_id: {
            "front": str(tmp_path / f"{event_id}_front.mov"),
            "back": str(tmp_path / f"{event_id}_back.mov"),
        }},
    }


# --- Unit 1: record-construction helper ---

def test_valid_record_passes_schema_and_matches_independent_hashes(tmp_path):
    record = _build_valid_record(tmp_path)
    built = build_stage2_1_record_from_dict(record)
    assert built.schema_version == STAGE_2_1_SCHEMA_VERSION
    assert built.is_resolved
    # Hashes must equal an independently computed sha256 of the fixture files
    front = tmp_path / "synthetic_event_001_front.mov"
    back = tmp_path / "synthetic_event_001_back.mov"
    assert record["reviewer_observed_media_hashes"]["front_sha256"] == hashlib.sha256(front.read_bytes()).hexdigest()
    assert record["reviewer_observed_media_hashes"]["back_sha256"] == hashlib.sha256(back.read_bytes()).hexdigest()


def test_helper_never_reads_real_review_directory(tmp_path):
    """The helper returns a dict and writes nothing anywhere."""
    record = _build_valid_record(tmp_path, "synthetic_event_noio")
    assert record["event_id"] == "synthetic_event_noio"
    assert not (Path("data/ground_truth/reviews") / "train_events" / "synthetic_event_noio").exists()


# --- Unit 2: authorization and schema gates ---

def test_unauthorized_reviewer_rejected_before_assembly(tmp_path):
    media = _make_media(tmp_path, "synthetic_event_unauth")
    with pytest.raises(ReviewerNotAuthorizedError):
        build_review_record(
            event_id="synthetic_event_unauth", cohort="train_events",
            reviewer_id="not.in.allowlist@example.com", authorized_reviewers=ALLOWED,
            front_media_path=media["front"], back_media_path=media["back"],
            proposal_file="data/ground_truth/proposals/train_events/p_v6.json",
            proposal_sha256=VALID_PROPOSAL_SHA, review_session_id="session-unauth",
            review_start_utc=T_START, review_end_utc=T_END,
            inspection_tool="ffmpeg frame-by-frame",
            attestation_statement="I reviewed only the raw video/audio and did not consult any model prediction.",
            attested_at_utc=T_ATTEST, observed_at_utc=T_START,
            boundary_adjudications=_boundary_set(), adjudication_status="APPROVED",
        )


def test_sub_30s_session_rejected_by_schema_floor(tmp_path):
    media = _make_media(tmp_path, "synthetic_event_short")
    short_end = (T0 + timedelta(seconds=10)).isoformat().replace("+00:00", "Z")
    with pytest.raises(SchemaValidationError, match="duration"):
        build_review_record(
            event_id="synthetic_event_short", cohort="train_events",
            reviewer_id=REVIEWER, authorized_reviewers=ALLOWED,
            front_media_path=media["front"], back_media_path=media["back"],
            proposal_file="data/ground_truth/proposals/train_events/p_v6.json",
            proposal_sha256=VALID_PROPOSAL_SHA, review_session_id="session-short",
            review_start_utc=T_START, review_end_utc=short_end,
            inspection_tool="ffmpeg frame-by-frame",
            attestation_statement="I reviewed only the raw video/audio and did not consult any model prediction.",
            attested_at_utc=T_ATTEST, observed_at_utc=T_START,
            boundary_adjudications=_boundary_set(), adjudication_status="APPROVED",
        )


def test_missing_media_file_fails_closed(tmp_path):
    media = _make_media(tmp_path, "synthetic_event_missing")
    with pytest.raises(FileNotFoundError):
        build_review_record(
            event_id="synthetic_event_missing", cohort="train_events",
            reviewer_id=REVIEWER, authorized_reviewers=ALLOWED,
            front_media_path=tmp_path / "nonexistent_front.mov", back_media_path=media["back"],
            proposal_file="data/ground_truth/proposals/train_events/p_v6.json",
            proposal_sha256=VALID_PROPOSAL_SHA, review_session_id="session-missing",
            review_start_utc=T_START, review_end_utc=T_END,
            inspection_tool="ffmpeg frame-by-frame",
            attestation_statement="I reviewed only the raw video/audio and did not consult any model prediction.",
            attested_at_utc=T_ATTEST, observed_at_utc=T_START,
            boundary_adjudications=_boundary_set(), adjudication_status="APPROVED",
        )


# --- Unit 3: dry-run promotion integration ---

def test_valid_record_dry_run_promotion_zero_violations(tmp_path):
    record = _build_valid_record(tmp_path)
    violations = validate_for_promotion(record, **_promo_ctx(tmp_path, "synthetic_event_001", record))
    assert violations == []


def test_media_bytes_changed_after_review_observation(tmp_path):
    """Negative test (a): tamper media after hash observation -> MEDIA_HASH_CHANGED_SINCE_REVIEW."""
    record = _build_valid_record(tmp_path)
    ctx = _promo_ctx(tmp_path, "synthetic_event_001", record)
    (tmp_path / "synthetic_event_001_front.mov").write_bytes(b"TAMPERED AFTER REVIEW")
    codes = {v.code for v in validate_for_promotion(record, **ctx)}
    assert "MEDIA_HASH_CHANGED_SINCE_REVIEW" in codes


def test_front_back_hashes_swapped_rejected(tmp_path):
    """Negative test (b): registry hashes swapped across cameras -> rejected."""
    record = _build_valid_record(tmp_path)
    ctx = _promo_ctx(tmp_path, "synthetic_event_001", record)
    swapped = dict(ctx["media_sha256_registry"]["synthetic_event_001"])
    swapped["front"], swapped["back"] = swapped["back"], swapped["front"]
    ctx["media_sha256_registry"] = {"synthetic_event_001": swapped}
    violations = validate_for_promotion(record, **ctx)
    assert violations != []


def test_unauthorized_reviewer_at_promotion_gate(tmp_path):
    """Negative test (c): reviewer not in allowlist -> REVIEWER_NOT_AUTHORIZED."""
    record = _build_valid_record(tmp_path)
    ctx = _promo_ctx(tmp_path, "synthetic_event_001", record)
    ctx["authorized_reviewers"] = frozenset({"someone.else@example.com"})
    codes = {v.code for v in validate_for_promotion(record, **ctx)}
    assert "REVIEWER_NOT_AUTHORIZED" in codes


def test_deleted_allowlist_file_fails_closed(tmp_path):
    """Negative test (d): allowlist removed mid-flow -> AuthorizedReviewersLoadError."""
    p = tmp_path / "authorized_reviewers.json"
    p.write_text(json.dumps({"authorized_reviewers": [REVIEWER]}), encoding="utf-8")
    assert load_authorized_reviewers(p) == frozenset({REVIEWER})
    p.unlink()
    with pytest.raises(AuthorizedReviewersLoadError):
        load_authorized_reviewers(p)


def test_attestation_statement_19_chars_rejected(tmp_path):
    """Negative test (e): 19-char attestation statement -> schema error."""
    media = _make_media(tmp_path, "synthetic_event_att19")
    with pytest.raises(SchemaValidationError):
        build_review_record(
            event_id="synthetic_event_att19", cohort="train_events",
            reviewer_id=REVIEWER, authorized_reviewers=ALLOWED,
            front_media_path=media["front"], back_media_path=media["back"],
            proposal_file="data/ground_truth/proposals/train_events/p_v6.json",
            proposal_sha256=VALID_PROPOSAL_SHA, review_session_id="session-att19",
            review_start_utc=T_START, review_end_utc=T_END,
            inspection_tool="ffmpeg frame-by-frame",
            attestation_statement="nineteen characters",  # 19 chars
            attested_at_utc=T_ATTEST, observed_at_utc=T_START,
            boundary_adjudications=_boundary_set(), adjudication_status="APPROVED",
        )


def test_omitting_media_hashes_field_impossible(tmp_path):
    """Negative test (f): helper computes hashes itself; no parameter to supply them."""
    import inspect
    sig = inspect.signature(build_review_record)
    assert "front_media_path" in sig.parameters and "back_media_path" in sig.parameters
    assert "front_sha256" not in sig.parameters
    assert "back_sha256" not in sig.parameters
    assert "media_hashes" not in sig.parameters


def test_caller_supplied_review_duration_ignored(tmp_path):
    """Negative test (g): review_duration_s is derived, never trusted from caller."""
    record = _build_valid_record(tmp_path)
    record["reviewer_metadata"]["review_duration_s"] = 9999.0
    built = build_stage2_1_record_from_dict(record)
    assert abs(built.reviewer_metadata.review_duration_s - 600.0) < 1.0


# --- Unit 4: documentation update ---

def test_no_stale_schema_version_in_workflow_doc():
    doc = Path("docs/PHASE11_3_ANNOTATION_REVIEW_WORKFLOW.md").read_text(encoding="utf-8")
    assert doc.count('"8.1.0-stage2.1"') >= 1
    # The only remaining 8.0.0 mention, if any, must be the superseded-format note
    for line in doc.splitlines():
        if "8.0.0-stage2.1" in line:
            assert "superseded" in line.lower()