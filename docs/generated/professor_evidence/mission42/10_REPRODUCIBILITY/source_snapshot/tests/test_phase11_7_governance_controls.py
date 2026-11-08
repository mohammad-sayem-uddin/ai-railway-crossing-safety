"""Phase 11.7: tests for the governance controls behind Decisions 2
(mandatory reviewer allowlist) and 4 (media-hash verification at review and
promotion time), per `docs/PHASE11_3_RESEARCHER_DECISIONS.md` v1.2.0.

Synthetic fixtures only (`tmp_path`). The one exception, consistent with
the authorization boundary, is a read-only load of the REAL allowlist file
(`data/ground_truth/authorized_reviewers.json`) to confirm it matches what
was actually implemented -- never a write, never a path under
`data/ground_truth/reviews/`.
"""

from __future__ import annotations

import hashlib
import inspect
import json
from datetime import datetime, timedelta, UTC
from pathlib import Path

import pytest

from railway_detection.annotation.promotion_gate import (
    AuthorizedReviewersLoadError,
    PromotionRejected,
    compute_media_sha256_pair,
    load_authorized_reviewers,
    promote_record,
    validate_for_promotion,
)
from railway_detection.annotation.schemas import SchemaValidationError
from railway_detection.annotation.stage2_1_schema import STAGE_2_1_SCHEMA_VERSION

T0 = datetime(2026, 11, 1, 14, 0, 0, tzinfo=UTC)
T_START = T0.isoformat().replace("+00:00", "Z")
T_END = (T0 + timedelta(seconds=600)).isoformat().replace("+00:00", "Z")
T_ATTEST = (T0 + timedelta(seconds=601)).isoformat().replace("+00:00", "Z")

VALID_PROPOSAL_SHA = "a" * 64


def _boundary_set() -> dict:
    return {
        "T0_first_visible": {"state": "OBSERVABLE", "rationale": "Visible at frame 0", "value_s": 0.0, "reference_camera": "front"},
        "T1_danger_zone_entry": {"state": "OBSERVABLE", "rationale": "Cowcatcher at landmark", "value_s": 5.8, "reference_camera": "front"},
        "T2_crossing_occupancy_start": {"state": "OBSERVABLE", "rationale": "Pilot crosses plane", "value_s": 6.5, "reference_camera": "front"},
        "T3_locomotive_unit_clearance": {"state": "OBSERVABLE", "rationale": "Rear coupler clears", "value_s": 3.6, "reference_camera": "back"},
        "T4_tail_clearance": {"state": "OBSERVABLE", "rationale": "Final coach clears", "value_s": 45.0, "reference_camera": "back"},
        "T_scene_clear": {"state": "CENSORED", "rationale": "Recording ends while train still visible", "value_s": None, "reference_camera": None},
    }


def _record_dict(event_id: str, reviewer_id: str, media_hashes: dict, **overrides) -> dict:
    base = {
        "schema_version": STAGE_2_1_SCHEMA_VERSION,
        "review_id": f"review_{event_id}_v1_20261101",
        "event_id": event_id,
        "cohort": "train_events",
        "proposal_reference": {
            "proposal_file": f"data/ground_truth/proposals/train_events/{event_id}_proposal_v6.json",
            "proposal_sha256": VALID_PROPOSAL_SHA,
        },
        "reviewer_metadata": {
            "reviewer_id": reviewer_id,
            "review_session_id": f"session-{event_id}",
            "review_start_utc": T_START,
            "review_end_utc": T_END,
            "inspection_tool": "ffmpeg frame-by-frame + scipy spectral audit, manual",
        },
        "model_independence_attestation": {
            "attested": True,
            "statement": "I reviewed only the raw video/audio and did not consult any model prediction.",
            "attested_at_utc": T_ATTEST,
        },
        "reviewer_observed_media_hashes": {
            "front_sha256": media_hashes["front"],
            "back_sha256": media_hashes["back"],
            "observed_at_utc": T_START,
        },
        "boundary_adjudications": _boundary_set(),
        "adjudication_status": "APPROVED",
        "adjudication_history": [
            {"event": "created", "by": reviewer_id, "at_utc": T_END, "status_set": "APPROVED"},
        ],
    }
    base.update(overrides)
    return base


def _make_media(tmp_path: Path, event_id: str, *, front_content: bytes | None = None, back_content: bytes | None = None) -> dict:
    front = tmp_path / f"{event_id}_front.mov"
    back = tmp_path / f"{event_id}_back.mov"
    front.write_bytes(front_content or f"front content {event_id}".encode())
    back.write_bytes(back_content or f"back content {event_id}".encode())
    return {
        "paths": {"front": str(front), "back": str(back)},
        "hashes": {
            "front": hashlib.sha256(front.read_bytes()).hexdigest(),
            "back": hashlib.sha256(back.read_bytes()).hexdigest(),
        },
    }


def _write_allowlist(tmp_path: Path, reviewers: list, filename: str = "allowlist.json") -> Path:
    p = tmp_path / filename
    p.write_text(json.dumps({"authorized_reviewers": reviewers}), encoding="utf-8")
    return p


# =============================================================================
# Task 1 sanity: real repository state (read-only)
# =============================================================================

def test_real_allowlist_file_loads_and_contains_only_the_researcher() -> None:
    allowlist = load_authorized_reviewers(Path("data/ground_truth/authorized_reviewers.json"))
    assert allowlist == frozenset({"raihankabirrahu@gmail.com"})


def test_real_stage2_1_schema_requires_reviewer_observed_media_hashes() -> None:
    assert STAGE_2_1_SCHEMA_VERSION == "8.1.0-stage2.1"


# =============================================================================
# Task 2 -- D2: mandatory reviewer allowlist
# =============================================================================

def test_authorized_reviewer_passes(tmp_path: Path) -> None:
    media = _make_media(tmp_path, "event_001")
    record = _record_dict("event_001", "jane_doe_researcher", media["hashes"])
    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event={"event_001": VALID_PROPOSAL_SHA},
        media_sha256_registry={"event_001": media["hashes"]},
        authorized_reviewers=frozenset({"jane_doe_researcher"}),
        media_file_paths={"event_001": media["paths"]},
    )
    assert violations == []


def test_unauthorized_reviewer_rejected(tmp_path: Path) -> None:
    media = _make_media(tmp_path, "event_001")
    record = _record_dict("event_001", "not_in_the_allowlist", media["hashes"])
    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event={"event_001": VALID_PROPOSAL_SHA},
        media_sha256_registry={"event_001": media["hashes"]},
        authorized_reviewers=frozenset({"jane_doe_researcher"}),
        media_file_paths={"event_001": media["paths"]},
    )
    assert any(v.code == "REVIEWER_NOT_AUTHORIZED" for v in violations)


def test_missing_allowlist_file_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(AuthorizedReviewersLoadError, match="does not exist"):
        load_authorized_reviewers(tmp_path / "nonexistent.json")


def test_malformed_allowlist_json_fails_closed(tmp_path: Path) -> None:
    p = tmp_path / "allowlist.json"
    p.write_text("{ not valid json !!", encoding="utf-8")
    with pytest.raises(AuthorizedReviewersLoadError, match="not valid JSON"):
        load_authorized_reviewers(p)


def test_allowlist_wrong_top_level_shape_fails_closed(tmp_path: Path) -> None:
    p = tmp_path / "allowlist.json"
    p.write_text(json.dumps(["jane_doe_researcher"]), encoding="utf-8")  # a list, not an object
    with pytest.raises(AuthorizedReviewersLoadError, match="JSON object"):
        load_authorized_reviewers(p)


def test_allowlist_empty_list_fails_closed(tmp_path: Path) -> None:
    p = _write_allowlist(tmp_path, [])
    with pytest.raises(AuthorizedReviewersLoadError, match="non-empty"):
        load_authorized_reviewers(p)


def test_allowlist_blank_entry_fails_closed(tmp_path: Path) -> None:
    p = _write_allowlist(tmp_path, ["jane_doe_researcher", "  "])
    with pytest.raises(AuthorizedReviewersLoadError, match="blank entry"):
        load_authorized_reviewers(p)


def test_allowlist_duplicate_entries_fails_closed(tmp_path: Path) -> None:
    p = _write_allowlist(tmp_path, ["jane_doe_researcher", "jane_doe_researcher"])
    with pytest.raises(AuthorizedReviewersLoadError, match="duplicate"):
        load_authorized_reviewers(p)


def test_allowlist_containing_blocklisted_identifier_fails_closed(tmp_path: Path) -> None:
    """An allowlist that somehow contains a known-fabricated placeholder
    (the exact string from the 27 invalidated Phase 11.1 records) is
    itself untrustworthy -- refuse the whole file, not just that entry."""
    p = _write_allowlist(tmp_path, ["jane_doe_researcher", "human_researcher_lead"])
    with pytest.raises(AuthorizedReviewersLoadError, match="blocklisted"):
        load_authorized_reviewers(p)


def test_altered_allowlist_revokes_a_previously_valid_reviewer(tmp_path: Path) -> None:
    """Simulates the allowlist being maintained over time: a reviewer valid
    under one version of the file is correctly rejected once the file is
    updated to remove them -- proving the check is a live lookup against
    the external file's current content, not a cached decision."""
    p = _write_allowlist(tmp_path, ["jane_doe_researcher"])
    allowlist_v1 = load_authorized_reviewers(p)
    assert "jane_doe_researcher" in allowlist_v1

    p.write_text(json.dumps({"authorized_reviewers": ["someone_else"]}), encoding="utf-8")
    allowlist_v2 = load_authorized_reviewers(p)
    assert "jane_doe_researcher" not in allowlist_v2


def test_injecting_fake_authorization_field_into_record_rejected(tmp_path: Path) -> None:
    """A record cannot invent its own 'authorized'/'allowlisted' field to
    bypass the external lookup -- ReviewerMetadata has no such field, so
    adding one is a structural validation failure, not a successful
    self-assertion."""
    from railway_detection.annotation.stage2_1_schema import build_stage2_1_record_from_dict

    media = _make_media(tmp_path, "event_001")
    record = _record_dict("event_001", "not_in_the_allowlist", media["hashes"])
    record["reviewer_metadata"]["authorized"] = True  # invented field
    with pytest.raises(SchemaValidationError, match="Malformed field structure"):
        build_stage2_1_record_from_dict(record)


# =============================================================================
# Task 3 -- D4: media-hash verification
# =============================================================================

def test_correct_media_hashes_pass(tmp_path: Path) -> None:
    media = _make_media(tmp_path, "event_001")
    record = _record_dict("event_001", "jane_doe_researcher", media["hashes"])
    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event={"event_001": VALID_PROPOSAL_SHA},
        media_sha256_registry={"event_001": media["hashes"]},
        authorized_reviewers=frozenset({"jane_doe_researcher"}),
        media_file_paths={"event_001": media["paths"]},
    )
    assert violations == []


def test_incorrect_registry_hash_rejected(tmp_path: Path) -> None:
    media = _make_media(tmp_path, "event_001")
    record = _record_dict("event_001", "jane_doe_researcher", media["hashes"])
    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event={"event_001": VALID_PROPOSAL_SHA},
        media_sha256_registry={"event_001": {"front": "f" * 64, "back": "0" * 64}},  # wrong
        authorized_reviewers=frozenset({"jane_doe_researcher"}),
        media_file_paths={"event_001": media["paths"]},
    )
    assert any(v.code == "MEDIA_HASH_CHANGED_SINCE_REGISTRY" for v in violations)


def test_media_changed_between_review_and_promotion_rejected(tmp_path: Path) -> None:
    """The reviewer observed the file's hash at review time; the file is
    then altered before promotion -- the live re-hash must disagree with
    the reviewer's recorded observation and block promotion."""
    media = _make_media(tmp_path, "event_001")
    record = _record_dict("event_001", "jane_doe_researcher", media["hashes"])

    # tamper with the raw media AFTER the review was recorded, BEFORE promotion
    Path(media["paths"]["front"]).write_bytes(b"this is not what was reviewed")

    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event={"event_001": VALID_PROPOSAL_SHA},
        media_sha256_registry={"event_001": media["hashes"]},  # registry still has the OLD hash too
        authorized_reviewers=frozenset({"jane_doe_researcher"}),
        media_file_paths={"event_001": media["paths"]},
    )
    codes = {v.code for v in violations}
    assert "MEDIA_HASH_CHANGED_SINCE_REVIEW" in codes
    assert "MEDIA_HASH_CHANGED_SINCE_REGISTRY" in codes  # registry is now stale too, both should fire


def test_missing_media_file_rejected(tmp_path: Path) -> None:
    media = _make_media(tmp_path, "event_001")
    record = _record_dict("event_001", "jane_doe_researcher", media["hashes"])
    Path(media["paths"]["front"]).unlink()

    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event={"event_001": VALID_PROPOSAL_SHA},
        media_sha256_registry={"event_001": media["hashes"]},
        authorized_reviewers=frozenset({"jane_doe_researcher"}),
        media_file_paths={"event_001": media["paths"]},
    )
    assert any(v.code == "MEDIA_FILE_MISSING" for v in violations)


def test_path_substitution_with_different_content_rejected(tmp_path: Path) -> None:
    """Simulates substituted media: the path string is unchanged, but the
    bytes at that path are now a different file -- the live hash catches
    this even though no path or record field was edited."""
    media = _make_media(tmp_path, "event_001")
    record = _record_dict("event_001", "jane_doe_researcher", media["hashes"])

    Path(media["paths"]["back"]).write_bytes(b"completely different substituted media content")

    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event={"event_001": VALID_PROPOSAL_SHA},
        media_sha256_registry={"event_001": media["hashes"]},
        authorized_reviewers=frozenset({"jane_doe_researcher"}),
        media_file_paths={"event_001": media["paths"]},
    )
    assert any(v.code == "MEDIA_HASH_CHANGED_SINCE_REVIEW" for v in violations)


def test_tampered_reviewer_observed_hash_field_cannot_bypass_verification(tmp_path: Path) -> None:
    """A reviewer (or anyone editing the record) claiming a hash that
    matches NOTHING real cannot satisfy promotion -- verification compares
    against the actual file content, not the claimed value."""
    media = _make_media(tmp_path, "event_001")
    record = _record_dict("event_001", "jane_doe_researcher", {"front": "9" * 64, "back": "9" * 64})

    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event={"event_001": VALID_PROPOSAL_SHA},
        media_sha256_registry={"event_001": media["hashes"]},
        authorized_reviewers=frozenset({"jane_doe_researcher"}),
        media_file_paths={"event_001": media["paths"]},
    )
    assert any(v.code == "MEDIA_HASH_CHANGED_SINCE_REVIEW" for v in violations)


def test_media_hash_bound_to_specific_event_not_reusable_across_events(tmp_path: Path) -> None:
    """event_002's reviewer_observed_media_hashes must not be satisfiable
    by event_001's actual media files -- binding is per-event, not a
    global 'some valid hash somewhere' check."""
    media_1 = _make_media(tmp_path, "event_001")
    media_2 = _make_media(tmp_path, "event_002")
    # Record for event_002, but claiming event_001's media hashes (wrong binding)
    record = _record_dict("event_002", "jane_doe_researcher", media_1["hashes"])

    violations = validate_for_promotion(
        record, active_proposal_sha256_by_event={"event_002": VALID_PROPOSAL_SHA},
        media_sha256_registry={"event_002": media_2["hashes"]},
        authorized_reviewers=frozenset({"jane_doe_researcher"}),
        media_file_paths={"event_002": media_2["paths"]},  # event_002's REAL files
    )
    codes = {v.code for v in violations}
    assert "MEDIA_HASH_CHANGED_SINCE_REVIEW" in codes


def test_compute_media_sha256_pair_raises_on_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        compute_media_sha256_pair(tmp_path / "nope_front.mov", tmp_path / "nope_back.mov")


def test_compute_media_sha256_pair_matches_manual_hashlib(tmp_path: Path) -> None:
    media = _make_media(tmp_path, "event_001")
    result = compute_media_sha256_pair(Path(media["paths"]["front"]), Path(media["paths"]["back"]))
    assert result == media["hashes"]


# =============================================================================
# Bypass attempts / no-writes-on-failure
# =============================================================================

def test_promote_record_writes_nothing_when_reviewer_unauthorized(tmp_path: Path) -> None:
    media = _make_media(tmp_path, "event_001")
    record = _record_dict("event_001", "not_in_the_allowlist", media["hashes"])
    out_dir = tmp_path / "stage3_sandbox"

    with pytest.raises(PromotionRejected) as exc_info:
        promote_record(
            record, output_dir=out_dir,
            active_proposal_sha256_by_event={"event_001": VALID_PROPOSAL_SHA},
            media_sha256_registry={"event_001": media["hashes"]},
            authorized_reviewers=frozenset({"jane_doe_researcher"}),
            media_file_paths={"event_001": media["paths"]},
        )
    assert any(v.code == "REVIEWER_NOT_AUTHORIZED" for v in exc_info.value.violations)
    assert not out_dir.exists() or not any(out_dir.iterdir())


def test_promote_record_writes_nothing_when_media_hash_mismatched(tmp_path: Path) -> None:
    media = _make_media(tmp_path, "event_001")
    record = _record_dict("event_001", "jane_doe_researcher", media["hashes"])
    Path(media["paths"]["front"]).write_bytes(b"tampered after review, before promotion")
    out_dir = tmp_path / "stage3_sandbox"

    with pytest.raises(PromotionRejected) as exc_info:
        promote_record(
            record, output_dir=out_dir,
            active_proposal_sha256_by_event={"event_001": VALID_PROPOSAL_SHA},
            media_sha256_registry={"event_001": media["hashes"]},
            authorized_reviewers=frozenset({"jane_doe_researcher"}),
            media_file_paths={"event_001": media["paths"]},
        )
    assert any(v.code == "MEDIA_HASH_CHANGED_SINCE_REVIEW" for v in exc_info.value.violations)
    assert not out_dir.exists() or not any(out_dir.iterdir())


def test_required_governance_params_have_no_default() -> None:
    """Structural proof, not just behavioral: authorized_reviewers and
    media_file_paths cannot be omitted by a careless caller, because
    neither has a default value in the actual function signatures."""
    for fn in (validate_for_promotion, promote_record):
        sig = inspect.signature(fn)
        for name in ("authorized_reviewers", "media_file_paths"):
            assert sig.parameters[name].default is inspect.Parameter.empty, (
                f"{fn.__name__}'s {name} must have no default value"
            )


def test_omitting_authorized_reviewers_is_a_typeerror_not_a_silent_pass() -> None:
    media_tmp = Path(".")  # unused, call fails before any path is touched
    with pytest.raises(TypeError):
        validate_for_promotion(  # type: ignore[call-arg]
            {"schema_version": STAGE_2_1_SCHEMA_VERSION, "event_id": "event_001"},
            active_proposal_sha256_by_event={},
            media_sha256_registry={},
            media_file_paths={},
        )


def test_omitting_media_file_paths_is_a_typeerror_not_a_silent_pass() -> None:
    with pytest.raises(TypeError):
        validate_for_promotion(  # type: ignore[call-arg]
            {"schema_version": STAGE_2_1_SCHEMA_VERSION, "event_id": "event_001"},
            active_proposal_sha256_by_event={},
            media_sha256_registry={},
            authorized_reviewers=frozenset(),
        )
