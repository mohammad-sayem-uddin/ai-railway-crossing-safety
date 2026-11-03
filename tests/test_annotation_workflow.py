"""Unit tests for AI-Assisted Railway Annotation Workflow.

Authoritative Specification: docs/FINAL_GROUND_TRUTH_PROTOCOL.md v5.0.0
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from railway_detection.annotation.gemini_annotator import GeminiAnnotator
from railway_detection.annotation.review_reporter import ReviewReporter
from railway_detection.annotation.schemas import (
    AIAssistantMetadata,
    InputMediaFile,
    ProposalDocument,
    ProposedBoundaryTimestamp,
    ProposedCameraAlignmentMarkers,
    ProposedEnvironmentalConditions,
    ProposedSiteMetadata,
    ProposedTrainMetadata,
    SchemaValidationError,
    assert_proposal_approval_firewall,
    validate_sha256,
)

MOCK_HASH_1 = "1111111111111111111111111111111111111111111111111111111111111111"
MOCK_HASH_2 = "2222222222222222222222222222222222222222222222222222222222222222"
MOCK_HASH_PROMPT = "3333333333333333333333333333333333333333333333333333333333333333"


def test_sha256_validation_passes_valid_hex() -> None:
    valid_hash = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    assert validate_sha256(valid_hash) == valid_hash


@pytest.mark.parametrize(
    "invalid_hash,error_snippet",
    [
        ("a1b2c3...", "placeholder/ellipsis"),
        ("<sha256>", "placeholder/ellipsis"),
        ("123456", "not a valid 64-char"),
        ("", "not a valid 64-char"),
        ("ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789", "not a valid 64-char"),  # uppercase
        ("111111111111111111111111111111111111111111111111111111111111111g", "not a valid 64-char"),  # non-hex
    ],
)
def test_sha256_validation_rejects_invalid(invalid_hash: str, error_snippet: str) -> None:
    with pytest.raises(SchemaValidationError, match=error_snippet):
        validate_sha256(invalid_hash)


def test_prompt_template_sha256_dynamic_computation() -> None:
    annotator = GeminiAnnotator()
    h = annotator._prompt_template_sha256
    assert len(h) == 64
    assert validate_sha256(h) == h


def test_full_train_event_proposal_schema(tmp_path: Path) -> None:
    ai_meta = AIAssistantMetadata(
        model_name="gemini-3.8-flash",
        prompt_template_version="v1.0.0",
        prompt_template_sha256=MOCK_HASH_PROMPT,
        input_media_files=[
            InputMediaFile("camera_front.mov", 45.2, MOCK_HASH_1),
            InputMediaFile("camera_back.mov", 44.8, MOCK_HASH_2),
        ],
    )
    site_meta = ProposedSiteMetadata("crossing_A", "session_001")
    env = ProposedEnvironmentalConditions("day", "clear")
    train = ProposedTrainMetadata(
        train_present=True,
        train_direction="left_to_right",
        train_type="passenger",
        trailing_cars_count=5,
        horn_status="present",
        horn_onset_s=3.5,
        horn_uncertainty_s=0.2,
    )

    timestamps = {
        "T0_first_visible": ProposedBoundaryTimestamp(True, True, 4.1, 123, "front", 29.97, "Visible"),
        "T1_danger_zone_entry": ProposedBoundaryTimestamp(True, True, 10.5, 315, "front", 29.97, "Entry"),
        "T2_crossing_occupancy_start": ProposedBoundaryTimestamp(True, True, 10.5, 315, "front", 29.97, "Occupancy"),
        "T3_locomotive_exit": ProposedBoundaryTimestamp(True, True, 16.2, 486, "back", 30.0, "Loco exit"),
        "T4_tail_clearance": ProposedBoundaryTimestamp(True, True, 38.8, 1164, "back", 30.0, "Tail clear"),
        "T_scene_clear": ProposedBoundaryTimestamp(True, True, 41.2, 1236, "back", 30.0, "Scene clear"),
    }
    alignment = ProposedCameraAlignmentMarkers("Marker front", "Marker back", 1.45)

    doc = ProposalDocument(
        proposal_id="proposal_event_001_v1",
        event_id="event_001",
        event_type="REAL_WORLD_TRAIN_EVENT",
        proposal_timestamp_utc="2026-10-09T08:00:00Z",
        schema_version="5.0.0",
        ai_assistant_metadata=ai_meta,
        proposed_site_metadata=site_meta,
        proposed_environmental_conditions=env,
        proposed_train_metadata=train,
        proposed_timestamps=timestamps,
        proposed_camera_alignment_markers=alignment,
    )

    d = doc.to_dict()
    assert d["schema_version"] == "5.0.0"
    assert d["event_type"] == "REAL_WORLD_TRAIN_EVENT"
    assert d["proposed_train_metadata"]["trailing_cars_count"] == 5
    assert d["proposed_timestamps"]["T4_tail_clearance"]["value_s"] == 38.8


def test_full_train_rejects_t4_less_than_t3() -> None:
    ai_meta = AIAssistantMetadata("gemini-3.8-flash", "v1.0.0", MOCK_HASH_PROMPT)
    site_meta = ProposedSiteMetadata("crossing_A", "session_001")
    env = ProposedEnvironmentalConditions("day", "clear")
    train = ProposedTrainMetadata(
        train_present=True,
        train_type="passenger",
        trailing_cars_count=5,
        horn_status="absent_observed",
    )
    # Invalid: T4 earlier than T3 despite 5 trailing cars
    timestamps = {
        "T0_first_visible": ProposedBoundaryTimestamp(True, True, 4.1, 123, "front", 30.0),
        "T1_danger_zone_entry": ProposedBoundaryTimestamp(True, True, 10.0, 300, "front", 30.0),
        "T2_crossing_occupancy_start": ProposedBoundaryTimestamp(True, True, 10.0, 300, "front", 30.0),
        "T3_locomotive_exit": ProposedBoundaryTimestamp(True, True, 20.0, 600, "back", 30.0),
        "T4_tail_clearance": ProposedBoundaryTimestamp(True, True, 15.0, 450, "back", 30.0),
        "T_scene_clear": ProposedBoundaryTimestamp(True, True, 25.0, 750, "back", 30.0),
    }
    alignment = ProposedCameraAlignmentMarkers()

    with pytest.raises(SchemaValidationError, match="T4 .* must be greater than T3"):
        ProposalDocument(
            proposal_id="proposal_event_001_v1",
            event_id="event_001",
            event_type="REAL_WORLD_TRAIN_EVENT",
            proposal_timestamp_utc="2026-10-09T08:00:00Z",
            schema_version="5.0.0",
            ai_assistant_metadata=ai_meta,
            proposed_site_metadata=site_meta,
            proposed_environmental_conditions=env,
            proposed_train_metadata=train,
            proposed_timestamps=timestamps,
            proposed_camera_alignment_markers=alignment,
        )


def test_engine_only_coincidence_rule() -> None:
    ai_meta = AIAssistantMetadata("gemini-3.8-flash", "v1.0.0", MOCK_HASH_PROMPT)
    site_meta = ProposedSiteMetadata("crossing_A", "session_001")
    env = ProposedEnvironmentalConditions("day", "clear")
    train = ProposedTrainMetadata(
        train_present=True,
        train_type="engine_only",
        trailing_cars_count=0,
        horn_status="unobservable",
        horn_reason="Audio degraded",
    )
    # T3 != T4 should fail for engine-only
    timestamps_invalid = {
        "T0_first_visible": ProposedBoundaryTimestamp(True, True, 1.0, 30, "front", 30.0),
        "T1_danger_zone_entry": ProposedBoundaryTimestamp(True, True, 3.0, 90, "front", 30.0),
        "T2_crossing_occupancy_start": ProposedBoundaryTimestamp(True, True, 3.0, 90, "front", 30.0),
        "T3_locomotive_exit": ProposedBoundaryTimestamp(True, True, 5.0, 150, "back", 30.0),
        "T4_tail_clearance": ProposedBoundaryTimestamp(True, True, 8.0, 240, "back", 30.0),  # Not coincident!
        "T_scene_clear": ProposedBoundaryTimestamp(True, True, 10.0, 300, "back", 30.0),
    }
    alignment = ProposedCameraAlignmentMarkers()

    with pytest.raises(SchemaValidationError, match="T3 .* and T4 .* must coincide"):
        ProposalDocument(
            proposal_id="proposal_event_engine_001_v1",
            event_id="event_engine_001",
            event_type="REAL_WORLD_ENGINE_ONLY",
            proposal_timestamp_utc="2026-10-09T08:00:00Z",
            schema_version="5.0.0",
            ai_assistant_metadata=ai_meta,
            proposed_site_metadata=site_meta,
            proposed_environmental_conditions=env,
            proposed_train_metadata=train,
            proposed_timestamps=timestamps_invalid,
            proposed_camera_alignment_markers=alignment,
        )

    # Valid coincident T3 == T4
    timestamps_valid = {
        **timestamps_invalid,
        "T4_tail_clearance": ProposedBoundaryTimestamp(True, True, 5.0, 150, "back", 30.0),
    }
    doc_engine = ProposalDocument(
        proposal_id="proposal_event_engine_001_v1",
        event_id="event_engine_001",
        event_type="REAL_WORLD_ENGINE_ONLY",
        proposal_timestamp_utc="2026-10-09T08:00:00Z",
        schema_version="5.0.0",
        ai_assistant_metadata=ai_meta,
        proposed_site_metadata=site_meta,
        proposed_environmental_conditions=env,
        proposed_train_metadata=train,
        proposed_timestamps=timestamps_valid,
        proposed_camera_alignment_markers=alignment,
    )
    assert doc_engine.proposed_timestamps["T3_locomotive_exit"].value_s == doc_engine.proposed_timestamps["T4_tail_clearance"].value_s


def test_no_train_event_rules() -> None:
    ai_meta = AIAssistantMetadata("gemini-3.8-flash", "v1.0.0", MOCK_HASH_PROMPT)
    site_meta = ProposedSiteMetadata("crossing_A", "session_001")
    env = ProposedEnvironmentalConditions("day", "clear")
    train = ProposedTrainMetadata(
        train_present=False,
        horn_status=None,
    )
    timestamps = {
        ts: ProposedBoundaryTimestamp(applicable=False, candidate_observable=False, value_s=None)
        for ts in (
            "T0_first_visible",
            "T1_danger_zone_entry",
            "T2_crossing_occupancy_start",
            "T3_locomotive_exit",
            "T4_tail_clearance",
            "T_scene_clear",
        )
    }
    alignment = ProposedCameraAlignmentMarkers()

    doc_no_train = ProposalDocument(
        proposal_id="proposal_event_no_train_001_v1",
        event_id="event_no_train_001",
        event_type="REAL_WORLD_NO_TRAIN",
        proposal_timestamp_utc="2026-10-09T08:00:00Z",
        schema_version="5.0.0",
        ai_assistant_metadata=ai_meta,
        proposed_site_metadata=site_meta,
        proposed_environmental_conditions=env,
        proposed_train_metadata=train,
        proposed_timestamps=timestamps,
        proposed_camera_alignment_markers=alignment,
    )
    assert doc_no_train.proposed_train_metadata.train_present is False
    assert doc_no_train.proposed_timestamps["T0_first_visible"].applicable is False


def test_horn_states_validation() -> None:
    # Invalid horn status name
    with pytest.raises(SchemaValidationError, match="horn_status must be one of"):
        ProposedTrainMetadata(train_present=True, horn_status="horn_blown")

    # Present without onset_s
    with pytest.raises(SchemaValidationError, match="horn_onset_s must be provided"):
        ProposedTrainMetadata(train_present=True, horn_status="present", horn_onset_s=None)

    # Unobservable without reason
    with pytest.raises(SchemaValidationError, match="horn_reason must explain"):
        ProposedTrainMetadata(train_present=True, horn_status="unobservable", horn_reason=None)


def test_immutable_proposal_storage(tmp_path: Path) -> None:
    annotator = GeminiAnnotator(base_proposal_dir=tmp_path / "proposals")
    ai_meta = AIAssistantMetadata("gemini-3.8-flash", "v1.0.0", MOCK_HASH_PROMPT)
    site_meta = ProposedSiteMetadata("crossing_A", "session_001")
    env = ProposedEnvironmentalConditions("day", "clear")
    train = ProposedTrainMetadata(train_present=False)
    timestamps = {
        ts: ProposedBoundaryTimestamp(False, False, None)
        for ts in (
            "T0_first_visible",
            "T1_danger_zone_entry",
            "T2_crossing_occupancy_start",
            "T3_locomotive_exit",
            "T4_tail_clearance",
            "T_scene_clear",
        )
    }
    alignment = ProposedCameraAlignmentMarkers()

    doc_v1 = ProposalDocument(
        proposal_id="proposal_event_001_v1",
        event_id="event_001",
        event_type="REAL_WORLD_NO_TRAIN",
        proposal_timestamp_utc="2026-10-09T08:00:00Z",
        schema_version="5.0.0",
        ai_assistant_metadata=ai_meta,
        proposed_site_metadata=site_meta,
        proposed_environmental_conditions=env,
        proposed_train_metadata=train,
        proposed_timestamps=timestamps,
        proposed_camera_alignment_markers=alignment,
    )

    p1 = annotator.save_proposal(doc_v1, "no_train_events")
    assert p1.name == "event_001_proposal.json"
    assert p1.exists()

    # Second save of same event without overwrite should create v2
    doc_v2 = ProposalDocument(
        proposal_id="proposal_event_001_v1",
        event_id="event_001",
        event_type="REAL_WORLD_NO_TRAIN",
        proposal_timestamp_utc="2026-10-09T08:10:00Z",
        schema_version="5.0.0",
        ai_assistant_metadata=ai_meta,
        proposed_site_metadata=site_meta,
        proposed_environmental_conditions=env,
        proposed_train_metadata=train,
        proposed_timestamps=timestamps,
        proposed_camera_alignment_markers=alignment,
    )
    p2 = annotator.save_proposal(doc_v2, "no_train_events")
    assert p2.name == "event_001_proposal_v2.json"
    assert p2.exists()

    # Original v1 file must remain intact
    with open(p1) as f:
        d1 = json.load(f)
    assert d1["proposal_id"] == "proposal_event_001_v1"

    with open(p2) as f:
        d2 = json.load(f)
    assert d2["proposal_id"] == "proposal_event_001_v2"
    assert d2["prior_proposal_ref"] == str(p1)


def test_mandatory_approval_firewall() -> None:
    # 1. Attempt to write into approved directory
    prohibited_path = Path("/Users/sayemuddin/Desktop/Train_automation/data/ground_truth/train_events/event_001.json")
    with pytest.raises(SchemaValidationError, match="FIREWALL VIOLATION: Proposal write attempted into approved"):
        assert_proposal_approval_firewall(prohibited_path, {})

    # 2. Attempt to mark proposal as APPROVED
    proposal_path = Path("/Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/event_001_proposal.json")
    with pytest.raises(SchemaValidationError, match="FIREWALL VIOLATION: AI candidate proposal cannot be marked 'approval_status: APPROVED'"):
        assert_proposal_approval_firewall(proposal_path, {"approval_status": "APPROVED"})


def test_review_reporter_generation(tmp_path: Path) -> None:
    ai_meta = AIAssistantMetadata("gemini-3.8-flash", "v1.0.0", MOCK_HASH_PROMPT)
    site_meta = ProposedSiteMetadata("crossing_A", "session_001")
    env = ProposedEnvironmentalConditions("day", "clear")
    train = ProposedTrainMetadata(
        train_present=True,
        train_type="passenger",
        trailing_cars_count=7,
        horn_status="absent_observed",
    )
    timestamps = {
        "T0_first_visible": ProposedBoundaryTimestamp(True, True, 0.0, 0, "front", 29.97, "Visible"),
        "T1_danger_zone_entry": ProposedBoundaryTimestamp(True, True, 5.8, 174, "front", 29.97, "Entry"),
        "T2_crossing_occupancy_start": ProposedBoundaryTimestamp(True, True, 6.5, 195, "front", 29.97, "Occupancy"),
        "T3_locomotive_exit": ProposedBoundaryTimestamp(True, True, 3.6, 216, "back", 59.94, "Exit"),
        "T4_tail_clearance": ProposedBoundaryTimestamp(True, True, 45.0, 2697, "back", 59.94, "Tail clear"),
        "T_scene_clear": ProposedBoundaryTimestamp(True, False, None, None, "back", 59.94, "Receding", ambiguity_flag=True),
    }
    alignment = ProposedCameraAlignmentMarkers()

    doc = ProposalDocument(
        proposal_id="proposal_event_001_v1",
        event_id="event_001",
        event_type="REAL_WORLD_TRAIN_EVENT",
        proposal_timestamp_utc="2026-10-09T08:00:00Z",
        schema_version="5.0.0",
        ai_assistant_metadata=ai_meta,
        proposed_site_metadata=site_meta,
        proposed_environmental_conditions=env,
        proposed_train_metadata=train,
        proposed_timestamps=timestamps,
        proposed_camera_alignment_markers=alignment,
    )

    md = ReviewReporter.generate_review_markdown(doc, event_raw_dir="/data/raw/event_001")
    assert "MANDATORY APPROVAL FIREWALL NOTICE" in md
    assert "event_001" in md
    assert "absent_observed" in md
    assert "T4_tail_clearance" in md
    assert "Prerequisite R03 Status: RETIRED (Operational Danger-Zone Convention Applied)" in md
    assert "Prerequisite R04 Status: UNRESOLVED (Camera Synchronization Limitation)" in md
    assert "120.788s" in md
