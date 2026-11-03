"""Phase 11.9: Synthetic Pilot and Workflow Audit.

Exercises the complete Phase 11.8 workflow end-to-end with synthetic records
and synthetic media. All fixtures are deterministic and synthetic. No real
event IDs are used. No writes to data/ground_truth/reviews/.

Units:
1. Fixtures: deterministic synthetic media + event registry.
2. Happy-path pilot: 3 synthetic events through full workflow.
3. Failure-mode pilot: induced failures are rejected; no partial artifacts.
4. Audit: duration statistics, defect register, append-only verification.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta, UTC
from pathlib import Path

import pytest

from railway_detection.annotation.promotion_gate import (
    PromotionRejected,
    promote_record,
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

# --- Constants ---

PILOT_REVIEWER = "pilot.reviewer@synthetic.example.com"
PILOT_ALLOWLIST = frozenset({PILOT_REVIEWER})
VALID_PROPOSAL_SHA = "d" * 64
T0 = datetime(2026, 11, 20, 9, 0, 0, tzinfo=UTC)
# Idle gap between consecutive synthetic review sessions.
SESSION_GAP_S = 120.0

SYNTHETIC_EVENTS = [
    {"event_id": "synthetic_pilot_event_001", "cohort": "train_events", "complexity": "simple"},
    {"event_id": "synthetic_pilot_event_002", "cohort": "no_train_events", "complexity": "negative_control"},
    {"event_id": "synthetic_pilot_event_003", "cohort": "engine_events", "complexity": "single_camera"},
]


def _ts(offset_s: float) -> str:
    return (T0 + timedelta(seconds=offset_s)).isoformat().replace("+00:00", "Z")


def _boundary_set_simple() -> dict[str, dict]:
    return {
        "T0_first_visible": {"state": "OBSERVABLE", "rationale": "Visible at frame 0", "value_s": 0.0, "reference_camera": "front"},
        "T1_danger_zone_entry": {"state": "OBSERVABLE", "rationale": "Cowcatcher at landmark", "value_s": 5.8, "reference_camera": "front"},
        "T2_crossing_occupancy_start": {"state": "OBSERVABLE", "rationale": "Pilot crosses plane", "value_s": 6.5, "reference_camera": "front"},
        "T3_locomotive_unit_clearance": {"state": "OBSERVABLE", "rationale": "Rear coupler clears", "value_s": 3.6, "reference_camera": "back"},
        "T4_tail_clearance": {"state": "OBSERVABLE", "rationale": "Final coach clears", "value_s": 45.0, "reference_camera": "back"},
        "T_scene_clear": {"state": "CENSORED", "rationale": "Recording ends while train still visible", "value_s": None, "reference_camera": None},
    }


def _boundary_set_negative() -> dict[str, dict]:
    """No-train event: all boundaries UNOBSERVABLE_NOT_APPLICABLE."""
    return {
        "T0_first_visible": {"state": "UNOBSERVABLE_NOT_APPLICABLE", "rationale": "No train present in this event", "value_s": None, "reference_camera": None},
        "T1_danger_zone_entry": {"state": "UNOBSERVABLE_NOT_APPLICABLE", "rationale": "No train present in this event", "value_s": None, "reference_camera": None},
        "T2_crossing_occupancy_start": {"state": "UNOBSERVABLE_NOT_APPLICABLE", "rationale": "No train present in this event", "value_s": None, "reference_camera": None},
        "T3_locomotive_unit_clearance": {"state": "UNOBSERVABLE_NOT_APPLICABLE", "rationale": "No train present in this event", "value_s": None, "reference_camera": None},
        "T4_tail_clearance": {"state": "UNOBSERVABLE_NOT_APPLICABLE", "rationale": "No train present in this event", "value_s": None, "reference_camera": None},
        "T_scene_clear": {"state": "OBSERVABLE", "rationale": "Scene clear confirmed at end of recording", "value_s": 120.0, "reference_camera": "front"},
    }


def _make_media(tmp_path: Path, event_id: str, *, seed: int = 42) -> dict[str, str]:
    """Create deterministic synthetic media files."""
    front = tmp_path / f"{event_id}_front.mov"
    back = tmp_path / f"{event_id}_back.mov"
    # Deterministic content based on event_id and seed
    front_content = f"SYNTHETIC_FRONT_{event_id}_seed{seed}".encode() * 100
    back_content = f"SYNTHETIC_BACK_{event_id}_seed{seed}".encode() * 100
    front.write_bytes(front_content)
    back.write_bytes(back_content)
    return {"front": str(front), "back": str(back)}


def _build_pilot_record(tmp_path: Path, event: dict, *, session_duration_s: float = 600.0) -> dict:
    """Build a pilot record for one synthetic event."""
    event_id = event["event_id"]
    cohort = event["cohort"]
    media = _make_media(tmp_path, event_id)

    if cohort == "no_train_events":
        boundaries = _boundary_set_negative()
    else:
        boundaries = _boundary_set_simple()

    # One reviewer cannot review two events at once, so each synthetic session
    # follows the previous one instead of sharing a window with it.
    session_index = next(
        (i for i, e in enumerate(SYNTHETIC_EVENTS) if e["event_id"] == event_id),
        0,
    )
    start_offset = session_index * (session_duration_s + SESSION_GAP_S)
    end_offset = start_offset + session_duration_s

    return build_review_record(
        event_id=event_id,
        cohort=cohort,
        reviewer_id=PILOT_REVIEWER,
        authorized_reviewers=PILOT_ALLOWLIST,
        front_media_path=media["front"],
        back_media_path=media["back"],
        proposal_file=f"data/ground_truth/proposals/{cohort}/{event_id}_proposal_v1.json",
        proposal_sha256=VALID_PROPOSAL_SHA,
        review_session_id=f"pilot-session-{event_id}",
        review_start_utc=_ts(start_offset),
        review_end_utc=_ts(end_offset),
        inspection_tool="synthetic pilot: ffmpeg frame-by-frame + scipy spectral audit",
        attestation_statement=f"Synthetic pilot review of {event_id}: I reviewed only the raw video/audio and did not consult any model prediction.",
        attested_at_utc=_ts(end_offset + 1),
        observed_at_utc=_ts(start_offset),
        boundary_adjudications=boundaries,
        adjudication_status="APPROVED",
    )


def _promo_ctx(tmp_path: Path, event: dict, record: dict) -> dict:
    event_id = event["event_id"]
    return {
        "active_proposal_sha256_by_event": {event_id: VALID_PROPOSAL_SHA},
        "media_sha256_registry": {event_id: {
            "front": record["reviewer_observed_media_hashes"]["front_sha256"],
            "back": record["reviewer_observed_media_hashes"]["back_sha256"],
        }},
        "authorized_reviewers": PILOT_ALLOWLIST,
        "media_file_paths": {event_id: {
            "front": str(tmp_path / f"{event_id}_front.mov"),
            "back": str(tmp_path / f"{event_id}_back.mov"),
        }},
    }


# --- Unit 1: fixtures ---

def test_synthetic_media_deterministic_and_distinct(tmp_path):
    m1 = _make_media(tmp_path, "synthetic_pilot_event_001")
    h1 = hashlib.sha256(Path(m1["front"]).read_bytes()).hexdigest()
    m2 = _make_media(tmp_path, "synthetic_pilot_event_002")
    h2 = hashlib.sha256(Path(m2["front"]).read_bytes()).hexdigest()
    assert h1 != h2  # distinct per event
    # deterministic: same event + seed reproduces the same content
    again = tmp_path / "again_front.mov"
    again.write_bytes(f"SYNTHETIC_FRONT_synthetic_pilot_event_001_seed42".encode() * 100)
    assert hashlib.sha256(again.read_bytes()).hexdigest() == h1


def test_event_registry_covers_three_distinct_events():
    ids = [e["event_id"] for e in SYNTHETIC_EVENTS]
    assert len(ids) == 3 and len(set(ids)) == 3
    assert {e["cohort"] for e in SYNTHETIC_EVENTS} == {"train_events", "no_train_events", "engine_events"}


# --- Unit 2: happy-path pilot ---

def test_three_events_pass_full_workflow_with_zero_violations(tmp_path):
    for event in SYNTHETIC_EVENTS:
        record = _build_pilot_record(tmp_path, event)
        built = build_stage2_1_record_from_dict(record)
        assert built.is_resolved
        assert record["reviewer_metadata"]["reviewer_id"] == PILOT_REVIEWER
        violations = validate_for_promotion(record, **_promo_ctx(tmp_path, event, record))
        assert violations == [], f"{event['event_id']}: {[v.code for v in violations]}"


def test_pilot_writes_nothing_to_production_review_directory(tmp_path):
    for event in SYNTHETIC_EVENTS:
        _build_pilot_record(tmp_path, event)
    count = sum(1 for _ in Path("data/ground_truth/reviews").rglob("*_review.json"))
    assert count == 27  # exactly the 27 legacy records, nothing added


# --- Unit 3: failure modes ---

def test_media_swapped_after_observation_detected(tmp_path):
    event = SYNTHETIC_EVENTS[0]
    record = _build_pilot_record(tmp_path, event)
    ctx = _promo_ctx(tmp_path, event, record)
    Path(ctx["media_file_paths"][event["event_id"]]["front"]).write_bytes(b"SWAPPED")
    codes = {v.code for v in validate_for_promotion(record, **ctx)}
    assert "MEDIA_HASH_CHANGED_SINCE_REVIEW" in codes


def test_unauthorized_reviewer_rejected_in_pilot(tmp_path):
    media = _make_media(tmp_path, "synthetic_pilot_event_001")
    with pytest.raises(ReviewerNotAuthorizedError):
        build_review_record(
            event_id="synthetic_pilot_event_001", cohort="train_events",
            reviewer_id="intruder@example.com", authorized_reviewers=PILOT_ALLOWLIST,
            front_media_path=media["front"], back_media_path=media["back"],
            proposal_file="data/ground_truth/proposals/train_events/synthetic_pilot_event_001_proposal_v1.json",
            proposal_sha256=VALID_PROPOSAL_SHA, review_session_id="pilot-session-intruder",
            review_start_utc=_ts(0.0), review_end_utc=_ts(600.0),
            inspection_tool="synthetic pilot",
            attestation_statement="Synthetic pilot: I reviewed only the raw media, no model outputs.",
            attested_at_utc=_ts(601.0), observed_at_utc=_ts(0.0),
            boundary_adjudications=_boundary_set_simple(), adjudication_status="APPROVED",
        )


def test_interrupted_sub_30s_session_rejected(tmp_path):
    event = SYNTHETIC_EVENTS[0]
    media = _make_media(tmp_path, event["event_id"])
    with pytest.raises(SchemaValidationError):
        build_review_record(
            event_id=event["event_id"], cohort=event["cohort"],
            reviewer_id=PILOT_REVIEWER, authorized_reviewers=PILOT_ALLOWLIST,
            front_media_path=media["front"], back_media_path=media["back"],
            proposal_file=f"data/ground_truth/proposals/train_events/{event['event_id']}_proposal_v1.json",
            proposal_sha256=VALID_PROPOSAL_SHA, review_session_id="pilot-session-interrupted",
            review_start_utc=_ts(0.0), review_end_utc=_ts(10.0),
            inspection_tool="synthetic pilot",
            attestation_statement="Synthetic pilot: I reviewed only the raw media, no model outputs.",
            attested_at_utc=_ts(11.0), observed_at_utc=_ts(0.0),
            boundary_adjudications=_boundary_set_simple(), adjudication_status="APPROVED",
        )


# --- Unit 3 (continued): adversarial failure modes ---

def test_registry_hash_tampering_rejected(tmp_path):
    """Adversarial: tampering the registry hash between review and promotion is rejected."""
    event = SYNTHETIC_EVENTS[0]
    record = _build_pilot_record(tmp_path, event)
    ctx = _promo_ctx(tmp_path, event, record)
    ctx["media_sha256_registry"][event["event_id"]]["front"] = "f" * 64
    codes = {v.code for v in validate_for_promotion(record, **ctx)}
    assert "MEDIA_HASH_CHANGED_SINCE_REGISTRY" in codes


def test_allowlist_modified_between_review_and_promotion(tmp_path):
    """Adversarial: allowlist shrunk after review -> reviewer no longer authorized."""
    event = SYNTHETIC_EVENTS[0]
    record = _build_pilot_record(tmp_path, event)
    ctx = _promo_ctx(tmp_path, event, record)
    ctx["authorized_reviewers"] = frozenset({"replacement.reviewer@example.com"})
    codes = {v.code for v in validate_for_promotion(record, **ctx)}
    assert "REVIEWER_NOT_AUTHORIZED" in codes


def test_promote_record_refuses_tampered_media_and_writes_nothing(tmp_path):
    """promote_record raises PromotionRejected and writes no file on violation."""
    event = SYNTHETIC_EVENTS[0]
    record = _build_pilot_record(tmp_path, event)
    ctx = _promo_ctx(tmp_path, event, record)
    Path(ctx["media_file_paths"][event["event_id"]]["front"]).write_bytes(b"EVIL SWAP")
    out = tmp_path / "promotion_out"
    with pytest.raises(PromotionRejected):
        promote_record(record, output_dir=out, **ctx)
    assert not (out / f"{event['event_id']}.json").exists()


def test_promote_record_writes_valid_synthetic_record(tmp_path):
    """promote_record succeeds for a fully valid synthetic record (synthetic out dir only)."""
    event = SYNTHETIC_EVENTS[0]
    record = _build_pilot_record(tmp_path, event)
    ctx = _promo_ctx(tmp_path, event, record)
    out = tmp_path / "promotion_out_valid"
    path = promote_record(record, output_dir=out, **ctx)
    assert path.exists() and path.name == f"{event['event_id']}.json"
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["schema_version"] == STAGE_2_1_SCHEMA_VERSION


# --- Unit 4: audit / attribution ---

def test_every_pilot_record_attributes_synthetic_reviewer(tmp_path):
    for event in SYNTHETIC_EVENTS:
        record = _build_pilot_record(tmp_path, event)
        assert record["reviewer_metadata"]["reviewer_id"] == PILOT_REVIEWER
        assert record["reviewer_metadata"]["reviewer_id"] != ""
        assert record["model_independence_attestation"]["attested"] is True


def test_pilot_duration_observations_recorded(tmp_path):
    """Wall-clock observations per event (D1 pilot evidence; synthetic, not a threshold)."""
    durations = {}
    for event in SYNTHETIC_EVENTS:
        t0 = time.monotonic()
        record = _build_pilot_record(tmp_path, event)
        durations[event["event_id"]] = time.monotonic() - t0
        built = build_stage2_1_record_from_dict(record)
        assert abs(built.reviewer_metadata.review_duration_s - 600.0) < 1.0
    assert len(durations) == 3 and all(d < 5.0 for d in durations.values())