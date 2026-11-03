"""Phase 11.11 WP2: Synthetic-only adjudication session runner tests.

All fixtures are deterministic and synthetic. No real event IDs are used.
No writes to data/ground_truth/reviews/. All output goes to tmp_path.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, UTC
from pathlib import Path

import pytest

from railway_detection.annotation.adjudication_session import (
    DuplicateRecordError,
    AdjudicationSessionError,
    EventNotInManifestError,
    MediaHashMismatchError,
    ModelFirewallViolationError,
    ProposalHashMismatchError,
    ResearcherNotConfirmedError,
    ReviewDurationTooShortError,
    SessionNotStartedError,
    StopConditionTriggeredError,
    create_session_from_inventory,
    load_event_from_inventory,
)
from railway_detection.annotation.review_session import ReviewerNotAuthorizedError
from railway_detection.annotation.stage2_1_schema import (
    STAGE_2_1_SCHEMA_VERSION,
    build_stage2_1_record_from_dict,
)

# --- Constants ---

SYNTHETIC_REVIEWER = "synthetic.reviewer@test.example.com"
SYNTHETIC_ALLOWLIST = frozenset({SYNTHETIC_REVIEWER})
T0 = datetime(2026, 10, 15, 10, 0, 0, tzinfo=UTC)


def _make_clock(start: datetime = T0, step_s: float = 45.0):
    """Return a callable time_source that advances by step_s on each call."""
    calls = {"n": 0}
    def clock() -> datetime:
        t = start + timedelta(seconds=calls["n"] * step_s)
        calls["n"] += 1
        return t
    return clock


def _make_monotonic(step_s: float = 45.0):
    calls = {"n": 0}
    def clock() -> float:
        value = calls["n"] * step_s
        calls["n"] += 1
        return value
    return clock


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _make_synthetic_media(tmp_path: Path, event_id: str) -> dict[str, Path]:
    """Create deterministic synthetic media files and return their paths."""
    front = tmp_path / f"{event_id}_front.mov"
    back = tmp_path / f"{event_id}_back.mov"
    front.write_bytes(f"SYNTHETIC_FRONT_{event_id}".encode() * 50)
    back.write_bytes(f"SYNTHETIC_BACK_{event_id}".encode() * 50)
    return {"front": front, "back": back}


def _make_inventory(tmp_path: Path, event_id: str, cohort: str = "train_events") -> dict:
    """Build a synthetic inventory dict for one event."""
    media = _make_synthetic_media(tmp_path, event_id)
    front_sha = _sha256(media["front"].read_bytes())
    back_sha = _sha256(media["back"].read_bytes())
    proposal_path = tmp_path / f"{event_id}_synthetic_proposal.json"
    proposal_path.write_text(json.dumps({"synthetic": True, "event_id": event_id}), encoding="utf-8")
    proposal_sha = _sha256(proposal_path.read_bytes())
    return {
        "total_events": 1,
        "events": {
            f"{cohort}/{event_id}": {
                "cohort": cohort,
                "event_id": event_id,
                "raw_media": {
                    "front": {"path": str(media["front"]), "sha256": front_sha, "duration_s": 10.0},
                    "back": {"path": str(media["back"]), "sha256": back_sha, "duration_s": 10.0},
                },
                "active_proposal_file": str(proposal_path),
                "active_proposal_sha256": proposal_sha,
            }
        },
    }


def _boundary_set_simple() -> dict[str, dict]:
    return {
        "T0_first_visible": {"state": "OBSERVABLE", "rationale": "Synthetic: visible at frame 0", "value_s": 0.0, "reference_camera": "front"},
        "T1_danger_zone_entry": {"state": "OBSERVABLE", "rationale": "Synthetic: cowcatcher at landmark", "value_s": 5.8, "reference_camera": "front"},
        "T2_crossing_occupancy_start": {"state": "OBSERVABLE", "rationale": "Synthetic: pilot crosses plane", "value_s": 6.5, "reference_camera": "front"},
        "T3_locomotive_unit_clearance": {"state": "OBSERVABLE", "rationale": "Synthetic: rear coupler clears", "value_s": 3.6, "reference_camera": "back"},
        "T4_tail_clearance": {"state": "OBSERVABLE", "rationale": "Synthetic: final coach clears", "value_s": 45.0, "reference_camera": "back"},
        "T_scene_clear": {"state": "CENSORED", "rationale": "Synthetic: recording ends while train still visible", "value_s": None, "reference_camera": None},
    }


def _run_full_session(tmp_path: Path, event_id: str = "synthetic_adj_001") -> Path:
    """Helper: run a complete happy-path session, return output file path."""
    inventory = _make_inventory(tmp_path, event_id)
    event_key = f"train_events/{event_id}"
    output_dir = tmp_path / "output"
    clock = _make_clock()
    monotonic_clock = _make_monotonic()
    session = create_session_from_inventory(
        inventory, event_key, SYNTHETIC_REVIEWER, SYNTHETIC_ALLOWLIST,
        output_dir=output_dir, time_source=clock, monotonic_source=monotonic_clock,
    )
    session.start()
    session.submit_boundaries(_boundary_set_simple())
    preview = session.preview(
        adjudication_status="APPROVED",
        attestation_statement=(
        "I, the synthetic test reviewer, confirm that all boundary adjudications "
        "were made independently from visual inspection of the media files, "
        "without reference to any model output."
        ),
    )
    session.confirm(confirmed=True, preview_sha256=session.preview_sha256)
    return session.finalize()


# --- Happy path ---


class TestHappyPath:
    def test_full_lifecycle_produces_valid_record(self, tmp_path: Path) -> None:
        output_path = _run_full_session(tmp_path)
        assert output_path.exists()
        record = json.loads(output_path.read_text())
        assert record["schema_version"] == STAGE_2_1_SCHEMA_VERSION
        assert record["event_id"] == "synthetic_adj_001"
        assert record["cohort"] == "train_events"
        assert record["adjudication_status"] == "APPROVED"
        # Validate through the schema validator
        build_stage2_1_record_from_dict(record)

    def test_media_hashes_in_record_match_files(self, tmp_path: Path) -> None:
        output_path = _run_full_session(tmp_path, "synthetic_adj_002")
        record = json.loads(output_path.read_text())
        media_hashes = record["reviewer_observed_media_hashes"]
        front_path = tmp_path / "synthetic_adj_002_front.mov"
        back_path = tmp_path / "synthetic_adj_002_back.mov"
        assert media_hashes["front_sha256"] == _sha256(front_path.read_bytes())
        assert media_hashes["back_sha256"] == _sha256(back_path.read_bytes())

    def test_session_log_records_all_events(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_003")
        event_key = "train_events/synthetic_adj_003"
        output_dir = tmp_path / "output"
        clock = _make_clock()
        monotonic_clock = _make_monotonic()
        session = create_session_from_inventory(
            inventory, event_key, SYNTHETIC_REVIEWER, SYNTHETIC_ALLOWLIST,
            output_dir=output_dir, time_source=clock, monotonic_source=monotonic_clock,
        )
        session.start()
        session.submit_boundaries(_boundary_set_simple())
        preview = session.preview(
            adjudication_status="APPROVED",
            attestation_statement="Synthetic reviewer independently inspected synthetic media only.",
        )
        session.confirm(confirmed=True, preview_sha256=session.preview_sha256)
        session.finalize()
        events = [e["event"] for e in session.log.entries]
        assert "session_start_attempt" in events
        assert "session_started" in events
        assert "boundaries_submitted" in events
        assert "researcher_confirmed" in events
        assert "record_written" in events

    def test_no_partial_files_on_success(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        _run_full_session(tmp_path, "synthetic_adj_004")
        # Only the final JSON should exist (no .tmp files)
        files = list(output_dir.iterdir())
        assert len(files) == 1
        assert files[0].suffix == ".json"


# --- Failure modes ---


class TestFailureModes:
    def test_unauthorized_reviewer_rejected(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_010")
        event_key = "train_events/synthetic_adj_010"
        with pytest.raises(ReviewerNotAuthorizedError):
            create_session_from_inventory(
                inventory, event_key, "unauthorized@evil.com",
                SYNTHETIC_ALLOWLIST, output_dir=tmp_path / "output",
            )

    def test_unknown_event_rejected(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_011")
        with pytest.raises(EventNotInManifestError):
            load_event_from_inventory(inventory, "train_events/nonexistent_event")

    def test_non_synthetic_event_is_rejected(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "event_001")
        with pytest.raises(EventNotInManifestError, match="Synthetic-only"):
            create_session_from_inventory(
                inventory, "train_events/event_001", SYNTHETIC_REVIEWER,
                SYNTHETIC_ALLOWLIST, output_dir=tmp_path / "output",
            )

    def test_non_temp_output_is_rejected(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_outside")
        with pytest.raises(AdjudicationSessionError, match="SYNTHETIC_ONLY_PATH_REQUIRED"):
            create_session_from_inventory(
                inventory, "train_events/synthetic_adj_outside", SYNTHETIC_REVIEWER,
                SYNTHETIC_ALLOWLIST, output_dir=Path.cwd() / "unsafe_output",
            )

    def test_media_hash_mismatch_aborts(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_012")
        # Corrupt the expected hash
        event_key = "train_events/synthetic_adj_012"
        inventory["events"][event_key]["raw_media"]["front"]["sha256"] = "b" * 64
        clock = _make_clock()
        monotonic_clock = _make_monotonic()
        session = create_session_from_inventory(
            inventory, event_key, SYNTHETIC_REVIEWER, SYNTHETIC_ALLOWLIST,
            output_dir=tmp_path / "output", time_source=clock,
            monotonic_source=monotonic_clock,
        )
        with pytest.raises(MediaHashMismatchError):
            session.start()
        assert not session.is_active
        # No output file should exist
        assert not (tmp_path / "output").exists() or not any((tmp_path / "output").iterdir())

    def test_media_change_after_review_aborts_preview_and_write(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_media_changed")
        event_key = "train_events/synthetic_adj_media_changed"
        clock = _make_clock()
        monotonic_clock = _make_monotonic()
        session = create_session_from_inventory(
            inventory, event_key, SYNTHETIC_REVIEWER, SYNTHETIC_ALLOWLIST,
            output_dir=tmp_path / "output", time_source=clock,
            monotonic_source=monotonic_clock,
        )
        session.start()
        session.submit_boundaries(_boundary_set_simple())
        (tmp_path / "synthetic_adj_media_changed_front.mov").write_bytes(b"changed")
        with pytest.raises(MediaHashMismatchError, match="pre_preview"):
            session.preview(
                adjudication_status="APPROVED",
                attestation_statement="Synthetic reviewer inspected synthetic media only.",
            )
        assert not session.is_active
        assert not (tmp_path / "output").exists()

    def test_short_monotonic_duration_rejected(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_too_fast")
        counter = {"value": 0.0}
        def fast_clock() -> float:
            counter["value"] += 1.0
            return counter["value"]
        session = create_session_from_inventory(
            inventory, "train_events/synthetic_adj_too_fast", SYNTHETIC_REVIEWER,
            SYNTHETIC_ALLOWLIST, output_dir=tmp_path / "output",
            time_source=_make_clock(step_s=1.0), monotonic_source=fast_clock,
        )
        session.start()
        session.submit_boundaries(_boundary_set_simple())
        with pytest.raises(ReviewDurationTooShortError):
            session.preview(
                adjudication_status="APPROVED",
                attestation_statement="Synthetic reviewer inspected synthetic media only.",
            )

    def test_confirmation_requires_affirmative_flag_and_matching_preview(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_confirmation")
        session = create_session_from_inventory(
            inventory, "train_events/synthetic_adj_confirmation", SYNTHETIC_REVIEWER,
            SYNTHETIC_ALLOWLIST, output_dir=tmp_path / "output",
            time_source=_make_clock(), monotonic_source=_make_monotonic(),
        )
        session.start()
        session.submit_boundaries(_boundary_set_simple())
        session.preview(
            adjudication_status="APPROVED",
            attestation_statement="Synthetic reviewer inspected synthetic media only.",
        )
        with pytest.raises(ResearcherNotConfirmedError, match="affirmative"):
            session.confirm(confirmed=False, preview_sha256=session.preview_sha256)
        with pytest.raises(ResearcherNotConfirmedError, match="does not match"):
            session.confirm(confirmed=True, preview_sha256="0" * 64)

    def test_existing_record_is_never_overwritten(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_existing")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        target = output_dir / "synthetic_adj_existing_stage2_1_review.json"
        target.write_text("preserve-existing", encoding="utf-8")
        session = create_session_from_inventory(
            inventory, "train_events/synthetic_adj_existing", SYNTHETIC_REVIEWER,
            SYNTHETIC_ALLOWLIST, output_dir=output_dir,
            time_source=_make_clock(), monotonic_source=_make_monotonic(),
        )
        session.start()
        session.submit_boundaries(_boundary_set_simple())
        session.preview(
            adjudication_status="APPROVED",
            attestation_statement="Synthetic reviewer inspected synthetic media only.",
        )
        session.confirm(confirmed=True, preview_sha256=session.preview_sha256)
        with pytest.raises(DuplicateRecordError, match="Refusing to overwrite"):
            session.finalize()
        assert target.read_text(encoding="utf-8") == "preserve-existing"

    def test_atomic_create_race_preserves_concurrent_record(self, tmp_path: Path, monkeypatch) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_race")
        output_dir = tmp_path / "output"
        target = output_dir / "synthetic_adj_race_stage2_1_review.json"
        session = create_session_from_inventory(
            inventory, "train_events/synthetic_adj_race", SYNTHETIC_REVIEWER,
            SYNTHETIC_ALLOWLIST, output_dir=output_dir,
            time_source=_make_clock(), monotonic_source=_make_monotonic(),
        )
        session.start()
        session.submit_boundaries(_boundary_set_simple())
        session.preview(
            adjudication_status="APPROVED",
            attestation_statement="Synthetic reviewer inspected synthetic media only.",
        )
        session.confirm(confirmed=True, preview_sha256=session.preview_sha256)

        real_link = os.link
        def concurrent_create(source, destination, *args, **kwargs):
            Path(destination).write_text("concurrent winner", encoding="utf-8")
            return real_link(source, destination, *args, **kwargs)
        monkeypatch.setattr(os, "link", concurrent_create)

        with pytest.raises(DuplicateRecordError, match="created concurrently"):
            session.finalize()
        assert target.read_text(encoding="utf-8") == "concurrent winner"
        assert sorted(p.name for p in output_dir.iterdir()) == [target.name]

    def test_media_changed_during_staging_prevents_atomic_create(self, tmp_path: Path, monkeypatch) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_staging_change")
        output_dir = tmp_path / "output"
        session = create_session_from_inventory(
            inventory, "train_events/synthetic_adj_staging_change", SYNTHETIC_REVIEWER,
            SYNTHETIC_ALLOWLIST, output_dir=output_dir,
            time_source=_make_clock(), monotonic_source=_make_monotonic(),
        )
        session.start()
        session.submit_boundaries(_boundary_set_simple())
        session.preview(
            adjudication_status="APPROVED",
            attestation_statement="Synthetic reviewer inspected synthetic media only.",
        )
        session.confirm(confirmed=True, preview_sha256=session.preview_sha256)

        real_fsync = os.fsync
        def mutate_after_staging(fd):
            result = real_fsync(fd)
            (tmp_path / "synthetic_adj_staging_change_front.mov").write_bytes(b"changed while staging")
            return result
        monkeypatch.setattr(os, "fsync", mutate_after_staging)

        with pytest.raises(MediaHashMismatchError, match="immediately before"):
            session.finalize()
        assert not any(output_dir.glob("*_stage2_1_review.json"))
        assert not list(output_dir.glob("*.tmp"))

    def test_proposal_change_before_preview_fails_closed(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_proposal_preview")
        proposal = Path(inventory["events"]["train_events/synthetic_adj_proposal_preview"]["active_proposal_file"])
        session = create_session_from_inventory(
            inventory, "train_events/synthetic_adj_proposal_preview", SYNTHETIC_REVIEWER,
            SYNTHETIC_ALLOWLIST, output_dir=tmp_path / "output",
            time_source=_make_clock(), monotonic_source=_make_monotonic(),
        )
        session.start()
        session.submit_boundaries(_boundary_set_simple())
        proposal.write_text('{"synthetic":true,"tampered":true}', encoding="utf-8")
        with pytest.raises(ProposalHashMismatchError, match="pre_preview"):
            session.preview(
                adjudication_status="APPROVED",
                attestation_statement="Synthetic reviewer inspected synthetic media only.",
            )
        assert not session.is_active
        assert not (tmp_path / "output").exists()

    def test_proposal_change_after_preview_prevents_write(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_proposal_write")
        proposal = Path(inventory["events"]["train_events/synthetic_adj_proposal_write"]["active_proposal_file"])
        output_dir = tmp_path / "output"
        session = create_session_from_inventory(
            inventory, "train_events/synthetic_adj_proposal_write", SYNTHETIC_REVIEWER,
            SYNTHETIC_ALLOWLIST, output_dir=output_dir,
            time_source=_make_clock(), monotonic_source=_make_monotonic(),
        )
        session.start()
        session.submit_boundaries(_boundary_set_simple())
        session.preview(
            adjudication_status="APPROVED",
            attestation_statement="Synthetic reviewer inspected synthetic media only.",
        )
        session.confirm(confirmed=True, preview_sha256=session.preview_sha256)
        proposal.write_text('{"synthetic":true,"tampered":true}', encoding="utf-8")
        with pytest.raises(ProposalHashMismatchError, match="pre_write"):
            session.finalize()
        assert not any(output_dir.glob("*_stage2_1_review.json"))

    def test_proposal_change_during_staging_prevents_atomic_create(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_proposal_staging")
        proposal = Path(inventory["events"]["train_events/synthetic_adj_proposal_staging"]["active_proposal_file"])
        output_dir = tmp_path / "output"
        session = create_session_from_inventory(
            inventory, "train_events/synthetic_adj_proposal_staging", SYNTHETIC_REVIEWER,
            SYNTHETIC_ALLOWLIST, output_dir=output_dir,
            time_source=_make_clock(), monotonic_source=_make_monotonic(),
        )
        session.start()
        session.submit_boundaries(_boundary_set_simple())
        session.preview(
            adjudication_status="APPROVED",
            attestation_statement="Synthetic reviewer inspected synthetic media only.",
        )
        session.confirm(confirmed=True, preview_sha256=session.preview_sha256)

        real_fsync = os.fsync

        def mutate_proposal_after_staging(fd):
            result = real_fsync(fd)
            proposal.write_text('{"synthetic":true,"changed_during_staging":true}', encoding="utf-8")
            return result

        monkeypatch.setattr(os, "fsync", mutate_proposal_after_staging)
        with pytest.raises(ProposalHashMismatchError, match="immediately_pre_write"):
            session.finalize()
        assert not any(output_dir.glob("*_stage2_1_review.json"))
        assert not list(output_dir.glob("*.tmp"))

    def test_media_symlink_escape_after_session_creation_is_rejected(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_symlink_escape")
        event = inventory["events"]["train_events/synthetic_adj_symlink_escape"]
        front = Path(event["raw_media"]["front"]["path"])
        session = create_session_from_inventory(
            inventory, "train_events/synthetic_adj_symlink_escape", SYNTHETIC_REVIEWER,
            SYNTHETIC_ALLOWLIST, output_dir=tmp_path / "output",
            time_source=_make_clock(), monotonic_source=_make_monotonic(),
        )
        # Point at an existing read-only system file outside tempfile storage;
        # the runner must reject its resolved path before reading it.
        outside_media = Path("/etc/hosts")
        front.unlink()
        front.symlink_to(outside_media)
        with pytest.raises(MediaHashMismatchError, match="Synthetic-only media path check"):
            session.start()
        assert not session.is_active
        front.unlink()

    def test_model_firewall_blocks_model_paths(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_013")
        event_key = "train_events/synthetic_adj_013"
        # Inject a model-output path
        inventory["events"][event_key]["raw_media"]["front"]["path"] = "results/yolo/best.pt"
        with pytest.raises(ModelFirewallViolationError):
            create_session_from_inventory(
                inventory, event_key, SYNTHETIC_REVIEWER, SYNTHETIC_ALLOWLIST,
                output_dir=tmp_path / "output",
            )

    def test_stop_condition_uncertain_majority(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_014")
        event_key = "train_events/synthetic_adj_014"
        clock = _make_clock()
        session = create_session_from_inventory(
            inventory, event_key, SYNTHETIC_REVIEWER, SYNTHETIC_ALLOWLIST,
            output_dir=tmp_path / "output", time_source=clock,
        )
        session.start()
        # 4 out of 6 boundaries UNCERTAIN (>50%)
        boundaries = {}
        for i, ts in enumerate([
            "T0_first_visible", "T1_danger_zone_entry",
            "T2_crossing_occupancy_start", "T3_locomotive_unit_clearance",
            "T4_tail_clearance", "T_scene_clear",
        ]):
            if i < 4:
                boundaries[ts] = {"state": "UNCERTAIN", "rationale": "Cannot determine", "value_s": None, "reference_camera": None}
            else:
                boundaries[ts] = {"state": "OBSERVABLE", "rationale": "Clearly visible", "value_s": float(i), "reference_camera": "front"}
        with pytest.raises(StopConditionTriggeredError):
            session.submit_boundaries(boundaries)
        assert not session.is_active

    def test_finalize_without_confirmation_rejected(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_015")
        event_key = "train_events/synthetic_adj_015"
        clock = _make_clock()
        session = create_session_from_inventory(
            inventory, event_key, SYNTHETIC_REVIEWER, SYNTHETIC_ALLOWLIST,
            output_dir=tmp_path / "output", time_source=clock,
        )
        session.start()
        session.submit_boundaries(_boundary_set_simple())
        with pytest.raises(ResearcherNotConfirmedError):
            session.finalize()

    def test_duplicate_write_rejected(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_016")
        event_key = "train_events/synthetic_adj_016"
        clock = _make_clock()
        monotonic_clock = _make_monotonic()
        session = create_session_from_inventory(
            inventory, event_key, SYNTHETIC_REVIEWER, SYNTHETIC_ALLOWLIST,
            output_dir=tmp_path / "output", time_source=clock,
            monotonic_source=monotonic_clock,
        )
        session.start()
        session.submit_boundaries(_boundary_set_simple())
        session.preview(
            adjudication_status="APPROVED",
            attestation_statement="Synthetic reviewer independently inspected synthetic media only.",
        )
        session.confirm(confirmed=True, preview_sha256=session.preview_sha256)
        session.finalize()
        # Session is now inactive; cannot finalize again
        with pytest.raises(SessionNotStartedError):
            session.finalize()

    def test_submit_boundaries_before_start_rejected(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_017")
        event_key = "train_events/synthetic_adj_017"
        clock = _make_clock()
        session = create_session_from_inventory(
            inventory, event_key, SYNTHETIC_REVIEWER, SYNTHETIC_ALLOWLIST,
            output_dir=tmp_path / "output", time_source=clock,
        )
        with pytest.raises(SessionNotStartedError):
            session.submit_boundaries(_boundary_set_simple())

    def test_boilerplate_attestation_rejected(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_018")
        event_key = "train_events/synthetic_adj_018"
        clock = _make_clock()
        session = create_session_from_inventory(
            inventory, event_key, SYNTHETIC_REVIEWER, SYNTHETIC_ALLOWLIST,
            output_dir=tmp_path / "output", time_source=clock,
        )
        session.start()
        session.submit_boundaries(_boundary_set_simple())
        with pytest.raises(ValueError, match="specific model-independence"):
            session.preview(adjudication_status="APPROVED", attestation_statement="ok")

    def test_withdrawal_produces_no_artifacts(self, tmp_path: Path) -> None:
        inventory = _make_inventory(tmp_path, "synthetic_adj_019")
        event_key = "train_events/synthetic_adj_019"
        output_dir = tmp_path / "output"
        clock = _make_clock()
        session = create_session_from_inventory(
            inventory, event_key, SYNTHETIC_REVIEWER, SYNTHETIC_ALLOWLIST,
            output_dir=output_dir, time_source=clock,
        )
        session.start()
        session.withdraw("Researcher withdrew for testing purposes.")
        assert not session.is_active
        assert not output_dir.exists() or not any(output_dir.iterdir())
        # Log records the withdrawal
        events = [e["event"] for e in session.log.entries]
        assert "session_withdrawn" in events
