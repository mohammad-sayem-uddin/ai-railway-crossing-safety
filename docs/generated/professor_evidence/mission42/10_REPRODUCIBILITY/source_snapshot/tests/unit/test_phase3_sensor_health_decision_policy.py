"""Phase 3 Comprehensive Regression Tests: Sensor Health, Staleness, and Decision Policy.

Validates the 20 targeted safety and sensor-health scenarios specified in Phase 3:
 1. Healthy camera with valid frames but zero detections.
 2. Healthy audio stream with consistently low probabilities.
 3. Missing video input.
 4. Missing audio input.
 5. Staleness exactly at and around configured timeout (2.0s).
 6. Temporary inference latency without source-data loss.
 7. Out-of-order frames and invalid timestamps.
 8. Duplicate observations.
 9. Front-camera staleness while back-camera observations continue.
10. Back-camera staleness while front-camera observations continue.
11. Independent camera timestamps that must not be compared.
12. Attempted unsynchronized cross-camera fusion operation (R04).
13. Train presence followed by a brief detection dropout.
14. Stale data attempting to trigger a clear or open decision.
15. Video termination while crossing remains occupied.
16. Recovery after a source resumes.
17. Repeated health-state oscillation (flapping).
18. Gate-command timing versus simulated gate movement kinematics.
19. Engine-only traversal.
20. No-train audio confounders with no valid visual train evidence.
"""

from __future__ import annotations

import pytest

from railway_detection.experiments.frozen_config import (
    TimingIntegrityError,
)
from railway_detection.experiments.layer_b_processor import LayerBEventProcessor
from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.fusion.rules import CrossingState, GateState, RuleId
from railway_detection.fusion.source_tracker import (
    HealthReason,
    SensorHealth,
    SourceTracker,
)
from railway_detection.simulation.gate_model import PhysicalGateModel


def _make_frame(
    t: float,
    v_dets: list[Detection] | tuple[Detection, ...] = (),
    a_dets: list[Detection] | tuple[Detection, ...] = (),
    c1_avail: bool = True,
    c2_avail: bool = True,
    a_avail: bool = True,
    c1_dets: list[Detection] | tuple[Detection, ...] | None = None,
    c2_dets: list[Detection] | tuple[Detection, ...] | None = None,
) -> MultimodalFrame:
    """Helper creating a MultimodalFrame with explicit source records."""
    cam1_dets = tuple(c1_dets if c1_dets is not None else v_dets)
    cam2_dets = tuple(c2_dets if c2_dets is not None else ())

    v_recs: list[EvidenceRecord] = []
    if c1_avail or cam1_dets:
        v_recs.append(
            EvidenceRecord(
                timestamp_s=t,
                source_id="camera_1",
                modality=Modality.VISION,
                available=c1_avail,
                detections=cam1_dets if c1_avail else (),
            )
        )
    if c2_avail or cam2_dets:
        v_recs.append(
            EvidenceRecord(
                timestamp_s=t,
                source_id="camera_2",
                modality=Modality.VISION,
                available=c2_avail,
                detections=cam2_dets if c2_avail else (),
            )
        )

    a_recs: list[EvidenceRecord] = []
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
# Test 1: Healthy camera with valid frames but zero detections
# ---------------------------------------------------------------------------
def test_scenario_01_healthy_camera_with_zero_detections():
    tracker = SourceTracker(default_timeout_s=2.0)
    tracker.register_source("camera_1", modality=Modality.VISION)

    # Valid frame received with zero detections
    health = tracker.record_observation(
        source_id="camera_1",
        timestamp_s=0.2,
        available=True,
        detections=(),
    )

    assert health == SensorHealth.HEALTHY
    assert tracker.get_reason("camera_1") == HealthReason.OBSERVATION_NO_DETECTIONS
    assert tracker.is_healthy("camera_1", 0.2)
    assert tracker.is_available("camera_1", 0.2)

    # Decision engine processes this frame
    engine = MultimodalDecisionEngine()
    rec = engine.evaluate_frame(_frame_at_t := _make_frame(0.2, v_dets=()))
    assert rec.resulting_state == CrossingState.IDLE.value
    assert rec.resulting_gate_state == GateState.OPEN.value
    assert rec.fault_status == "none"
    assert rec.source_health["camera_1"] == SensorHealth.HEALTHY.value
    assert rec.health_reasons["camera_1"] == HealthReason.OBSERVATION_NO_DETECTIONS.value


# ---------------------------------------------------------------------------
# Test 2: Healthy audio stream with consistently low probabilities
# ---------------------------------------------------------------------------
def test_scenario_02_healthy_audio_stream_with_low_probabilities():
    engine = MultimodalDecisionEngine(audio_threshold=0.3700)
    low_audio_det = [Detection("train_horn", 0.12)]  # Far below 0.3700

    for t in (0.5, 1.0, 1.5, 2.0):
        frame = _make_frame(t, a_dets=low_audio_det)
        rec = engine.evaluate_frame(frame)
        assert rec.resulting_state == CrossingState.IDLE.value
        assert rec.resulting_gate_state == GateState.OPEN.value
        assert rec.fault_status == "none"
        assert rec.source_health["audio_1"] == SensorHealth.HEALTHY.value


# ---------------------------------------------------------------------------
# Test 3: Missing video input
# ---------------------------------------------------------------------------
def test_scenario_03_missing_video_input():
    engine = MultimodalDecisionEngine(confirm_frames=2)
    engine.reset(0.0)

    # Approach detected on frame 1
    engine.evaluate_frame(_make_frame(0.2, v_dets=[Detection("front", 0.85)]))
    # Approach confirmed on frame 2 -> WARNING
    rec_warn = engine.evaluate_frame(_make_frame(0.4, v_dets=[Detection("front", 0.85)]))
    assert rec_warn.resulting_state == CrossingState.WARNING.value

    # Video stream drops entirely while crossing active
    rec_drop = engine.evaluate_frame(_make_frame(0.6, c1_avail=False, c2_avail=False))
    assert rec_drop.resulting_state == CrossingState.FAULT_FAIL_SAFE.value
    assert rec_drop.resulting_gate_state == GateState.CLOSED.value
    assert rec_drop.rule_id == RuleId.RULE_4_FAIL_SAFE_CLAMP.value
    assert rec_drop.source_health["camera_1"] == SensorHealth.MISSING.value


# ---------------------------------------------------------------------------
# Test 4: Missing audio input
# ---------------------------------------------------------------------------
def test_scenario_04_missing_audio_input_does_not_prevent_vision_safety():
    engine = MultimodalDecisionEngine(confirm_frames=2)
    engine.reset(0.0)

    # Audio input missing from the beginning
    frame1 = _make_frame(0.2, v_dets=[Detection("front", 0.85)], a_avail=False)
    frame2 = _make_frame(0.4, v_dets=[Detection("front", 0.85)], a_avail=False)

    engine.evaluate_frame(frame1)
    rec2 = engine.evaluate_frame(frame2)

    # Approach confirmation still functions safely based on vision
    assert rec2.resulting_state == CrossingState.WARNING.value
    assert rec2.source_health["audio_1"] == SensorHealth.MISSING.value
    assert rec2.source_health["camera_1"] == SensorHealth.HEALTHY.value


# ---------------------------------------------------------------------------
# Test 5: Staleness exactly at and around configured timeout (2.0s)
# ---------------------------------------------------------------------------
def test_scenario_05_staleness_boundary_at_2_0_seconds():
    tracker = SourceTracker(default_timeout_s=2.0)
    tracker.register_source("camera_1", modality=Modality.VISION)

    # Observation at t = 1.0s
    tracker.record_observation("camera_1", timestamp_s=1.0, available=True)

    # At age = 1.9s (t = 2.9s): Fresh
    assert tracker.evaluate_staleness("camera_1", 2.9) == SensorHealth.HEALTHY
    assert tracker.is_healthy("camera_1", 2.9) is True

    # At age = 2.0s (t = 3.0s): Boundary edge is fresh (<= 2.0s)
    assert tracker.evaluate_staleness("camera_1", 3.0) == SensorHealth.HEALTHY
    assert tracker.is_healthy("camera_1", 3.0) is True

    # At age = 2.01s (t = 3.01s): Stale (> 2.0s)
    assert tracker.evaluate_staleness("camera_1", 3.01) == SensorHealth.STALE
    assert tracker.is_healthy("camera_1", 3.01) is False
    assert tracker.get_reason("camera_1") == HealthReason.TIMEOUT_STALE


# ---------------------------------------------------------------------------
# Test 6: Temporary inference latency without source-data loss
# ---------------------------------------------------------------------------
def test_scenario_06_inference_latency_without_source_data_loss():
    tracker = SourceTracker(default_timeout_s=2.0)
    tracker.register_source("camera_1", modality=Modality.VISION)

    # Frame sampled at t=0.2s with 0.8s inference delay
    health = tracker.record_observation(
        source_id="camera_1",
        timestamp_s=0.2,
        available=True,
        latency_s=0.8,
    )

    assert health == SensorHealth.HEALTHY
    status = tracker.sources["camera_1"]
    assert status.metadata.get("processing_latency_s") == 0.8
    # Media timestamp is 0.2, age at media time 1.0 is 0.8s <= 2.0s -> healthy
    assert tracker.evaluate_staleness("camera_1", 1.0) == SensorHealth.HEALTHY


# ---------------------------------------------------------------------------
# Test 7: Out-of-order frames and invalid timestamps
# ---------------------------------------------------------------------------
def test_scenario_07_out_of_order_frames_rejected():
    engine = MultimodalDecisionEngine()
    engine.reset(0.0)

    # Ingest t=5.0s
    engine.evaluate_frame(_make_frame(5.0))

    # Attempt to ingest t=4.8s (out of order)
    rec_ooo = engine.evaluate_frame(_make_frame(4.8))
    assert rec_ooo.rule_id == RuleId.RULE_8_OUT_OF_ORDER_REJECTION.value
    assert rec_ooo.fault_status == "out_of_order"


# ---------------------------------------------------------------------------
# Test 8: Duplicate observations
# ---------------------------------------------------------------------------
def test_scenario_08_duplicate_observations_idempotence():
    tracker = SourceTracker(default_timeout_s=2.0)
    tracker.register_source("camera_1", modality=Modality.VISION)

    h1 = tracker.record_observation("camera_1", timestamp_s=2.0, available=True)
    valid_count_1 = tracker.sources["camera_1"].consecutive_valid_observations

    # Duplicate observation at t=2.0s
    h2 = tracker.record_observation("camera_1", timestamp_s=2.0, available=True)
    valid_count_2 = tracker.sources["camera_1"].consecutive_valid_observations

    assert h1 == h2 == SensorHealth.HEALTHY
    assert valid_count_1 == valid_count_2  # No duplicate increment


# ---------------------------------------------------------------------------
# Test 9: Front-camera staleness while back-camera observations continue
# ---------------------------------------------------------------------------
def test_scenario_09_front_camera_staleness_with_healthy_back_camera():
    engine = MultimodalDecisionEngine(confirm_frames=2)
    engine.reset(0.0)

    # Both active at t=0.2s
    engine.evaluate_frame(_make_frame(0.2, c1_avail=True, c2_avail=True))

    # At t=2.5s, front camera drops out (stale > 2.0s), back camera emits
    frame_t25 = MultimodalFrame(
        master_timestamp_s=2.5,
        vision_records=(
            EvidenceRecord(
                timestamp_s=2.5,
                source_id="camera_2",
                modality=Modality.VISION,
                available=True,
                detections=(),
            ),
        ),
        source_availability={"camera_1": False, "camera_2": True},
    )
    rec = engine.evaluate_frame(frame_t25)

    assert rec.source_health["camera_1"] in (SensorHealth.STALE.value, SensorHealth.MISSING.value)
    assert rec.source_health["camera_2"] == SensorHealth.HEALTHY.value
    # Does not fail-safe clamp because camera_2 is still healthy
    assert rec.resulting_state == CrossingState.IDLE.value


# ---------------------------------------------------------------------------
# Test 10: Back-camera staleness while front-camera observations continue
# ---------------------------------------------------------------------------
def test_scenario_10_back_camera_staleness_holds_departure_state():
    engine = MultimodalDecisionEngine()
    engine.reset(0.0)
    engine.current_state = CrossingState.TRAIN_DEPARTING
    engine.current_gate_state = GateState.CLOSED

    # Front camera healthy, but departure camera (camera_2) is stale / unavailable
    frame = MultimodalFrame(
        master_timestamp_s=5.0,
        vision_records=(
            EvidenceRecord(
                timestamp_s=5.0,
                source_id="camera_1",
                modality=Modality.VISION,
                available=True,
                detections=(),
            ),
        ),
        source_availability={"camera_1": True, "camera_2": False},
    )
    rec = engine.evaluate_frame(frame)

    # Rule 6 holds the gate closed and does not allow clearance
    assert rec.resulting_state == CrossingState.TRAIN_DEPARTING.value
    assert rec.resulting_gate_state == GateState.CLOSED.value
    assert rec.rule_id == RuleId.RULE_6_DEGRADED_SOURCE_HOLD.value


# ---------------------------------------------------------------------------
# Test 11: Independent camera timestamps must not be compared
# ---------------------------------------------------------------------------
def test_scenario_11_independent_camera_timelines_isolated():
    tracker = SourceTracker()
    tracker.register_source("camera_front", camera_id="front_01")
    tracker.register_source("camera_back", camera_id="back_01")

    # Ingest front camera at front-local media time 10.0s
    tracker.record_observation("camera_front", timestamp_s=10.0, available=True)
    # Ingest back camera at back-local media time 5.0s (independent timeline)
    tracker.record_observation("camera_back", timestamp_s=5.0, available=True)

    # Both must retain their own independent last valid timestamps
    assert tracker.sources["camera_front"].last_valid_timestamp_s == 10.0
    assert tracker.sources["camera_back"].last_valid_timestamp_s == 5.0
    # Evaluate staleness against their respective timelines
    assert tracker.evaluate_staleness("camera_front", 11.0) == SensorHealth.HEALTHY
    assert tracker.evaluate_staleness("camera_back", 6.0) == SensorHealth.HEALTHY


# ---------------------------------------------------------------------------
# Test 12: Attempted unsynchronized cross-camera fusion operation (R04)
# ---------------------------------------------------------------------------
def test_scenario_12_unverified_cross_camera_fusion_rejected():
    processor = LayerBEventProcessor()
    # Attempting to assemble multimodal stream with multiple cameras and no SyncAligner
    rec_cam1 = EvidenceRecord(0.0, "camera_1", Modality.VISION, True)
    rec_cam2 = EvidenceRecord(0.0, "camera_2", Modality.VISION, True)

    with pytest.raises(TimingIntegrityError, match="R04 Timing Violation"):
        processor.build_multimodal_frames(
            vision_records=[rec_cam1, rec_cam2],
            audio_records=[],
            duration_s=5.0,
            sync_aligner=None,
        )


# ---------------------------------------------------------------------------
# Test 13: Train presence followed by a brief detection dropout
# ---------------------------------------------------------------------------
def test_scenario_13_detection_dropout_does_not_clear_crossing():
    engine = MultimodalDecisionEngine()
    engine.reset(0.0)
    engine.current_state = CrossingState.TRAIN_PRESENT
    engine.current_gate_state = GateState.CLOSED

    # Valid camera frames arrive with zero detections (brief dropout)
    rec1 = engine.evaluate_frame(_make_frame(10.0, v_dets=()))
    rec2 = engine.evaluate_frame(_make_frame(10.2, v_dets=()))

    # Gate remains CLOSED; does not clear or open without confirmed rear departure
    assert rec1.resulting_state == CrossingState.TRAIN_PRESENT.value
    assert rec2.resulting_state == CrossingState.TRAIN_PRESENT.value
    assert rec2.resulting_gate_state == GateState.CLOSED.value


# ---------------------------------------------------------------------------
# Test 14: Stale data attempting to trigger a clear or open decision
# ---------------------------------------------------------------------------
def test_scenario_14_stale_data_aborts_clearance_and_clamps_gate():
    engine = MultimodalDecisionEngine(clearance_dwell_s=3.0)
    engine.reset(0.0)
    engine.current_state = CrossingState.REAR_CONFIRMED
    engine.current_gate_state = GateState.CLOSED
    engine.state_entry_time_s = 10.0
    engine.clearance_started_at_s = 10.0

    # Clearance dwell progressing at t=11.0s
    rec_progress = engine.evaluate_frame(_make_frame(11.0, c1_avail=True, c2_avail=True))
    assert rec_progress.resulting_state == CrossingState.REAR_CONFIRMED.value

    # At t=12.0s, camera stream goes stale/missing while clearance is in progress
    rec_stale = engine.evaluate_frame(_make_frame(12.0, c1_avail=False, c2_avail=False))

    # Rule 5 MUST abort clearance immediately and clamp closed into FAULT_FAIL_SAFE
    assert rec_stale.resulting_state == CrossingState.FAULT_FAIL_SAFE.value
    assert rec_stale.resulting_gate_state == GateState.CLOSED.value
    assert rec_stale.rule_id == RuleId.RULE_5_STALE_SOURCE_ABORT.value


# ---------------------------------------------------------------------------
# Test 15: Video termination while crossing remains occupied
# ---------------------------------------------------------------------------
def test_scenario_15_video_termination_while_occupied_holds_closed():
    engine = MultimodalDecisionEngine()
    engine.reset(0.0)
    engine.current_state = CrossingState.CROSSING_OCCUPIED
    engine.current_gate_state = GateState.CLOSED

    # Stream terminates -> time advances with no new frames (sources missing)
    rec = engine.evaluate_frame(_make_frame(20.0, c1_avail=False, c2_avail=False))

    # Crossing remains clamped closed in FAULT_FAIL_SAFE
    assert rec.resulting_state == CrossingState.FAULT_FAIL_SAFE.value
    assert rec.resulting_gate_state == GateState.CLOSED.value


# ---------------------------------------------------------------------------
# Test 16: Recovery after a source resumes
# ---------------------------------------------------------------------------
def test_scenario_16_sensor_recovery_requires_confirmation_frames():
    tracker = SourceTracker(confirmation_frames=2)
    tracker.register_source("camera_1", modality=Modality.VISION)

    # Initial failure
    tracker.record_observation("camera_1", timestamp_s=1.0, available=False)
    assert tracker.get_health("camera_1") == SensorHealth.MISSING

    # Observation resumes: Frame 1 -> RECOVERING
    h1 = tracker.record_observation("camera_1", timestamp_s=1.2, available=True)
    assert h1 == SensorHealth.RECOVERING
    assert tracker.is_available("camera_1") is False

    # Observation continues: Frame 2 -> HEALTHY
    h2 = tracker.record_observation("camera_1", timestamp_s=1.4, available=True)
    assert h2 == SensorHealth.HEALTHY
    assert tracker.is_available("camera_1") is True


# ---------------------------------------------------------------------------
# Test 17: Repeated health-state oscillation (flapping)
# ---------------------------------------------------------------------------
def test_scenario_17_repeated_health_oscillation_flapping_tracked():
    tracker = SourceTracker(confirmation_frames=2)
    tracker.register_source("camera_1", modality=Modality.VISION)

    # Healthy -> Fail -> Recover attempt -> Fail -> Recover attempt
    tracker.record_observation("camera_1", 1.0, available=True)
    tracker.record_observation("camera_1", 1.2, available=False)
    tracker.record_observation("camera_1", 1.4, available=True)  # Flap 1
    tracker.record_observation("camera_1", 1.6, available=False)
    tracker.record_observation("camera_1", 1.8, available=True)  # Flap 2

    assert tracker.sources["camera_1"].flapping_count >= 2
    # Sensor must still be in RECOVERING, not HEALTHY
    assert tracker.get_health("camera_1") == SensorHealth.RECOVERING


# ---------------------------------------------------------------------------
# Test 18: Gate-command timing versus simulated gate movement kinematics
# ---------------------------------------------------------------------------
def test_scenario_18_gate_command_timing_vs_physical_kinematics():
    gate = PhysicalGateModel(closing_duration_s=3.0, opening_duration_s=3.0)
    assert gate.current_angle_deg == 90.0
    assert gate.is_fully_open is True

    # Closing commanded
    # After 1.5s (45 deg): passage is blocked
    angle_15 = gate.step(1.5, GateState.CLOSING)
    assert abs(angle_15 - 45.0) < 1e-3
    assert gate.is_passage_blocked is True
    assert gate.is_fully_closed is False

    # After another 1.5s (total 3.0s): fully closed (0 deg)
    angle_30 = gate.step(1.5, GateState.CLOSING)
    assert abs(angle_30 - 0.0) < 1e-3
    assert gate.is_fully_closed is True


# ---------------------------------------------------------------------------
# Test 19: Engine-only traversal
# ---------------------------------------------------------------------------
def test_scenario_19_engine_only_traversal():
    engine = MultimodalDecisionEngine(
        warning_dwell_s=2.0,
        gate_closing_s=3.0,
        clearance_dwell_s=3.0,
        gate_opening_s=3.0,
        confirm_frames=2,
    )
    engine.reset(0.0)

    # 1. Approach detected & confirmed
    engine.evaluate_frame(_make_frame(0.2, v_dets=[Detection("front", 0.9)]))
    engine.evaluate_frame(_make_frame(0.4, v_dets=[Detection("front", 0.9)]))
    assert engine.current_state == CrossingState.WARNING

    # 2. Warning dwell (2.0s) -> GATE_CLOSING
    engine.evaluate_frame(_make_frame(2.5))
    assert engine.current_state == CrossingState.GATE_CLOSING

    # 3. Gate closing (3.0s) -> TRAIN_PRESENT
    engine.evaluate_frame(_make_frame(5.6))
    assert engine.current_state == CrossingState.TRAIN_PRESENT

    # 4. Engine occupies crossing
    engine.evaluate_frame(_make_frame(6.0, v_dets=[Detection("front", 0.9)]))
    assert engine.current_state == CrossingState.CROSSING_OCCUPIED

    # 5. Rear immediately detected (no trailing cars)
    engine.evaluate_frame(_make_frame(7.0, c2_dets=[Detection("rear", 0.9)]))
    assert engine.current_state == CrossingState.TRAIN_DEPARTING

    engine.evaluate_frame(_make_frame(7.2, c2_dets=[Detection("rear", 0.9)]))
    assert engine.current_state == CrossingState.REAR_CONFIRMED

    # 6. Clearance dwell (3.0s): begins at t=8.0
    engine.evaluate_frame(_make_frame(8.0))
    engine.evaluate_frame(_make_frame(11.1))
    assert engine.current_state == CrossingState.CROSSING_CLEAR

    # 7. Gate opening (3.0s) -> IDLE
    engine.evaluate_frame(_make_frame(11.3))
    assert engine.current_state == CrossingState.GATE_OPENING

    engine.evaluate_frame(_make_frame(14.4))
    assert engine.current_state == CrossingState.IDLE
    assert engine.current_gate_state == GateState.OPEN


# ---------------------------------------------------------------------------
# Test 20: No-train audio confounders with no valid visual train evidence
# ---------------------------------------------------------------------------
def test_scenario_20_audio_confounder_without_vision_does_not_close_gate():
    engine = MultimodalDecisionEngine(audio_threshold=0.3700)
    engine.reset(0.0)

    # Loud horn / noise confounder with high audio confidence (0.95 > 0.37)
    # Cameras are healthy but report 0 train detections
    confounder_dets = [Detection("train_horn", 0.95)]
    frame = _make_frame(1.0, a_dets=confounder_dets, v_dets=())

    rec = engine.evaluate_frame(frame)

    # Rule 2: Audio is supportive only; cannot trigger warning or close gate in IDLE
    assert rec.resulting_state == CrossingState.IDLE.value
    assert rec.resulting_gate_state == GateState.OPEN.value
    assert rec.rule_id == RuleId.RULE_2_AUDIO_SUPPORT_ONLY.value
