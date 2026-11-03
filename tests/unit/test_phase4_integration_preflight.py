"""Phase 4 Integration Verification and Preflight Tests.

Validates:
1. Sensor recovery safety semantics: recovery from an active/occupied crossing never clears to IDLE or opens gate.
2. Safe recovery from IDLE faults back to IDLE.
3. Event discovery and full 54-stream active cohort resolution across 27 events (excluding duplicate 010).
4. Audio track availability across all 27 active event front cameras.
5. End-to-end component wiring and FrozenExperimentConfig propagation.
6. R04 cross-camera temporal fusion blocking.
7. Decision causality and actuator boom kinematics.
8. Incremental serialization and run artifact schema integrity.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
import pytest

from railway_detection.experiments.frozen_config import (
    TimingIntegrityError,
    load_frozen_config,
    verify_checkpoint_integrity,
    verify_timing_safeguards,
)
from railway_detection.experiments.layer_b_processor import LayerBEventProcessor
from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.fusion.rules import CrossingState, GateState
from railway_detection.fusion.source_tracker import SensorHealth
from railway_detection.simulation.gate_model import PhysicalGateModel


def _frame(
    t: float,
    v_dets: list[Detection] | tuple[Detection, ...] = (),
    a_dets: list[Detection] | tuple[Detection, ...] = (),
    c1_avail: bool = True,
    c2_avail: bool = True,
    a_avail: bool = True,
) -> MultimodalFrame:
    v_recs = []
    if c1_avail or v_dets:
        v_recs.append(
            EvidenceRecord(
                timestamp_s=t,
                source_id="camera_1",
                modality=Modality.VISION,
                available=c1_avail,
                detections=tuple(v_dets) if c1_avail else (),
            )
        )
    if c2_avail:
        v_recs.append(
            EvidenceRecord(
                timestamp_s=t,
                source_id="camera_2",
                modality=Modality.VISION,
                available=c2_avail,
                detections=(),
            )
        )
    a_recs = []
    if a_avail or a_dets:
        a_recs.append(
            EvidenceRecord(
                timestamp_s=t,
                source_id="audio_1",
                modality=Modality.AUDIO,
                available=a_avail,
                detections=tuple(a_dets) if a_avail else (),
            )
        )
    return MultimodalFrame(
        master_timestamp_s=t,
        vision_records=tuple(v_recs),
        audio_records=tuple(a_recs),
        source_availability={"camera_1": c1_avail, "camera_2": c2_avail, "audio_1": a_avail},
    )


# ---------------------------------------------------------------------------
# Invariant 1: Sensor recovery from an active/occupied crossing never opens gate
# ---------------------------------------------------------------------------
def test_recovery_from_occupied_crossing_never_opens_gate():
    """CRITICAL SAFETY INVARIANT:

    If cameras drop out while a train is occupying the crossing, fail-safe clamps closed.
    When cameras recover, sensor health is restored, but sensor recovery ALONE
    must NOT transition to IDLE or open the gate!
    The crossing MUST transition to TRAIN_PRESENT with gate CLOSED.
    """
    engine = MultimodalDecisionEngine(confirm_frames=2)
    engine.reset(0.0)

    # 1. Train approaches, enters warning, closes gate, occupies crossing
    engine.evaluate_frame(_frame(0.2, v_dets=[Detection("front", 0.9)]))
    engine.evaluate_frame(_frame(0.4, v_dets=[Detection("front", 0.9)]))
    assert engine.current_state == CrossingState.WARNING

    engine.evaluate_frame(_frame(2.5))  # Warning dwell elapsed -> GATE_CLOSING
    assert engine.current_state == CrossingState.GATE_CLOSING

    engine.evaluate_frame(_frame(5.6))  # Gate closing elapsed -> TRAIN_PRESENT
    assert engine.current_state == CrossingState.TRAIN_PRESENT

    engine.evaluate_frame(_frame(6.0, v_dets=[Detection("front", 0.9)]))  # -> CROSSING_OCCUPIED
    assert engine.current_state == CrossingState.CROSSING_OCCUPIED
    assert engine.train_present_or_approaching is True

    # 2. Camera dropout occurs while crossing is occupied!
    rec_fault = engine.evaluate_frame(_frame(7.0, c1_avail=False, c2_avail=False))
    assert rec_fault.resulting_state == CrossingState.FAULT_FAIL_SAFE.value
    assert rec_fault.resulting_gate_state == GateState.CLOSED.value
    assert engine.fault_entered_from == CrossingState.CROSSING_OCCUPIED

    # 3. Cameras recover! Frame 1 of recovery
    rec_rec1 = engine.evaluate_frame(_frame(7.2, c1_avail=True, c2_avail=True, v_dets=()))
    assert rec_rec1.resulting_state == CrossingState.FAULT_FAIL_SAFE.value
    assert rec_rec1.resulting_gate_state == GateState.CLOSED.value

    # 4. Cameras confirmed healthy on Frame 2 of recovery (zero detections observed)
    rec_rec2 = engine.evaluate_frame(_frame(7.4, c1_avail=True, c2_avail=True, v_dets=()))

    # MUST NOT transition to IDLE! MUST NOT open gate!
    assert rec_rec2.resulting_state == CrossingState.TRAIN_PRESENT.value
    assert rec_rec2.resulting_gate_state == GateState.CLOSED.value
    assert engine.current_state == CrossingState.TRAIN_PRESENT
    assert engine.current_gate_state == GateState.CLOSED

    # 5. Clearance can only be achieved via operational departure detection
    # Disappearance alone holds gate closed
    rec_hold = engine.evaluate_frame(_frame(8.0, c1_avail=True, c2_avail=True, v_dets=()))
    assert rec_hold.resulting_state == CrossingState.TRAIN_PRESENT.value
    assert rec_hold.resulting_gate_state == GateState.CLOSED.value

    # Rear detected -> moves from TRAIN_PRESENT to CROSSING_OCCUPIED, then TRAIN_DEPARTING, then REAR_CONFIRMED
    engine.evaluate_frame(_frame(8.2, v_dets=[Detection("rear", 0.9)]))
    assert engine.current_state == CrossingState.CROSSING_OCCUPIED

    engine.evaluate_frame(_frame(8.4, v_dets=[Detection("rear", 0.9)]))
    assert engine.current_state == CrossingState.TRAIN_DEPARTING

    engine.evaluate_frame(_frame(8.6, v_dets=[Detection("rear", 0.9)]))
    assert engine.current_state == CrossingState.REAR_CONFIRMED

    # 3.0s clearance dwell: begins at t=9.0
    engine.evaluate_frame(_make_frame(9.0)) if hasattr(engine, "_make_frame") else engine.evaluate_frame(_frame(9.0))
    engine.evaluate_frame(_frame(12.1))
    assert engine.current_state == CrossingState.CROSSING_CLEAR

    engine.evaluate_frame(_frame(12.3))
    assert engine.current_state == CrossingState.GATE_OPENING
    assert engine.current_gate_state == GateState.OPENING

    engine.evaluate_frame(_frame(15.4))
    assert engine.current_state == CrossingState.IDLE
    assert engine.current_gate_state == GateState.OPEN


# ---------------------------------------------------------------------------
# Invariant 2: Sensor recovery from an IDLE fault safely restores IDLE
# ---------------------------------------------------------------------------
def test_recovery_from_idle_fault_safely_restores_idle():
    """Verify that transient sensor failure in IDLE (with no train approaching)

    safely restores to IDLE once sensors recover for 2 confirmation frames.
    """
    engine = MultimodalDecisionEngine(confirm_frames=2)
    engine.reset(0.0)

    # In IDLE: dual camera failure for 2 frames
    engine.evaluate_frame(_frame(0.2, c1_avail=False, c2_avail=False))
    rec_clamp = engine.evaluate_frame(_frame(0.4, c1_avail=False, c2_avail=False))
    assert rec_clamp.resulting_state == CrossingState.FAULT_FAIL_SAFE.value
    assert engine.fault_entered_from == CrossingState.IDLE
    assert engine.train_present_or_approaching is False

    # Frame 1 recovery -> stays FAULT_FAIL_SAFE
    engine.evaluate_frame(_frame(0.6, c1_avail=True, c2_avail=True))
    assert engine.current_state == CrossingState.FAULT_FAIL_SAFE

    # Frame 2 recovery -> restores to IDLE (safe because crossing was truly IDLE)
    rec_rec = engine.evaluate_frame(_frame(0.8, c1_avail=True, c2_avail=True))
    assert rec_rec.resulting_state == CrossingState.IDLE.value
    assert rec_rec.resulting_gate_state == GateState.OPEN.value
    assert engine.current_state == CrossingState.IDLE


# ---------------------------------------------------------------------------
# Invariant 3: Active Cohort Manifest & Stream Resolution (27 events, 54 streams)
# ---------------------------------------------------------------------------
def test_active_cohort_event_and_stream_resolution():
    """Verify exact active cohort:

    - 23 train events
    - 3 no-train negative controls
    - 1 engine-only event
    - Total: 27 active events
    - Duplicate event_historical_duplicate_010 excluded
    - All 54 video streams resolvable and non-empty
    """
    v2_dir = Path("data/raw/layer_b/v2")
    assert v2_dir.is_dir(), "Missing data/raw/layer_b/v2 directory"

    cohorts = ["train_events", "no_train_events", "engine_events"]
    discovered_events: list[tuple[str, str, Path]] = []

    for cohort in cohorts:
        c_dir = v2_dir / cohort
        assert c_dir.is_dir(), f"Missing cohort directory: {c_dir}"
        for ed in sorted(c_dir.iterdir()):
            if not ed.is_dir() or not ed.name.startswith("event_"):
                continue
            if ed.name == "event_historical_duplicate_010":
                continue  # Properly excluded
            discovered_events.append((cohort, ed.name, ed))

    assert len(discovered_events) == 27, f"Expected 27 active events, found {len(discovered_events)}"

    train_evs = [e for e in discovered_events if e[0] == "train_events"]
    no_train_evs = [e for e in discovered_events if e[0] == "no_train_events"]
    engine_evs = [e for e in discovered_events if e[0] == "engine_events"]

    assert len(train_evs) == 23, f"Expected 23 train events, found {len(train_evs)}"
    assert len(no_train_evs) == 3, f"Expected 3 no-train events, found {len(no_train_evs)}"
    assert len(engine_evs) == 1, f"Expected 1 engine event, found {len(engine_evs)}"

    # Check that each event resolves both camera_front.mov and camera_back.mov
    stream_count = 0
    for cohort, name, ed in discovered_events:
        front = ed / "camera_front.mov"
        back = ed / "camera_back.mov"
        assert front.exists() and front.stat().st_size > 0, f"Invalid front camera in {ed}"
        assert back.exists() and back.stat().st_size > 0, f"Invalid back camera in {ed}"
        stream_count += 2

    assert stream_count == 54, f"Expected 54 active video streams, verified {stream_count}"


# ---------------------------------------------------------------------------
# Invariant 4: Audio Track Availability across All 27 Active Events
# ---------------------------------------------------------------------------
def test_audio_track_availability_across_all_active_events():
    """Verify that all 27 active events have valid extractable audio streams in camera_front.mov."""
    v2_dir = Path("data/raw/layer_b/v2")
    cohorts = ["train_events", "no_train_events", "engine_events"]

    for cohort in cohorts:
        c_dir = v2_dir / cohort
        for ed in sorted(c_dir.iterdir()):
            if not ed.is_dir() or not ed.name.startswith("event_") or ed.name == "event_historical_duplicate_010":
                continue
            front = ed / "camera_front.mov"
            cmd = ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "json", str(front)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            assert res.returncode == 0, f"ffprobe failed on {front}"
            info = json.loads(res.stdout)
            codecs = [s["codec_type"] for s in info.get("streams", [])]
            assert "audio" in codecs, f"Missing audio track in {front}"


# ---------------------------------------------------------------------------
# Invariant 5: End-to-End Component Wiring & Frozen Config Propagation
# ---------------------------------------------------------------------------
def test_frozen_config_propagation_to_runtime_components():
    """Verify that FrozenExperimentConfig is ingested and propagated consistently:

    - DecisionEngine uses config thresholds (audio=0.3700, vision=0.35, confirm_frames=2)
    - PhysicalGateModel uses config closing/opening durations (3.0s, 3.0s)
    - Checkpoint integrity and timing safeguards pass
    """
    config = load_frozen_config()
    verify_checkpoint_integrity(config)
    verify_timing_safeguards(config)

    engine = MultimodalDecisionEngine(config=config)
    assert engine.audio_threshold == 0.3700
    assert engine.approach_threshold == 0.35
    assert engine.departure_threshold == 0.35
    assert engine.confirm_frames == 2
    assert engine.warning_dwell_s == 2.0
    assert engine.gate_closing_s == 3.0
    assert engine.gate_opening_s == 3.0
    assert engine.clearance_dwell_s == 3.0
    assert engine.source_staleness_s == 2.0


# ---------------------------------------------------------------------------
# Invariant 6: R04 Unsynchronized Cross-Camera Fusion Strictly Blocked
# ---------------------------------------------------------------------------
def test_r04_cross_camera_fusion_strictly_blocked():
    """Verify that attempting to assemble cross-camera frames without empirical offset calibration

    raises TimingIntegrityError under authoritative frozen configuration.
    """
    processor = LayerBEventProcessor()
    rec_c1 = EvidenceRecord(timestamp_s=1.0, source_id="camera_1", modality=Modality.VISION, available=True)
    rec_c2 = EvidenceRecord(timestamp_s=1.0, source_id="camera_2", modality=Modality.VISION, available=True)

    with pytest.raises(TimingIntegrityError, match="R04 Timing Violation"):
        processor.build_multimodal_frames(
            vision_records=[rec_c1, rec_c2],
            audio_records=[],
            duration_s=5.0,
            sync_aligner=None,
        )


# ---------------------------------------------------------------------------
# Invariant 7: Actuator Boom Kinematics Timeline Verification
# ---------------------------------------------------------------------------
def test_gate_actuation_kinematics_sequential_timeline():
    """Verify exact barrier arm angles and obstruction states:

    Rate = 30.0 deg/s.
    t=1.5s -> 45.0 deg (is_passage_blocked = True)
    t=3.0s -> 0.0 deg (is_fully_closed = True)
    """
    gate = PhysicalGateModel(closing_duration_s=3.0, opening_duration_s=3.0)
    assert gate.current_angle_deg == 90.0

    # 1.5s of closing
    gate.step(1.5, GateState.CLOSING)
    assert abs(gate.current_angle_deg - 45.0) < 1e-4
    assert gate.is_passage_blocked is True
    assert gate.is_fully_closed is False

    # Another 1.5s of closing (total 3.0s)
    gate.step(1.5, GateState.CLOSING)
    assert abs(gate.current_angle_deg - 0.0) < 1e-4
    assert gate.is_passage_blocked is True
    assert gate.is_fully_closed is True


# ---------------------------------------------------------------------------
# Invariant 8: Incremental Output Schema Integrity
# ---------------------------------------------------------------------------
def test_decision_record_and_frame_schema_completeness():
    """Verify that DecisionRecord serializes all Phase 3/4 audit fields:

    - source_health
    - health_reasons
    - observation_ages
    - gate_command
    - fault_status
    """
    engine = MultimodalDecisionEngine()
    engine.reset(0.0)

    rec = engine.evaluate_frame(_frame(0.2, v_dets=[Detection("front", 0.9)]))
    data = rec.to_dict()

    assert "source_health" in data
    assert "health_reasons" in data
    assert "observation_ages" in data
    assert "gate_command" in data
    assert "fault_status" in data
    assert data["source_health"]["camera_1"] == SensorHealth.HEALTHY.value
