"""Unit and regression tests for MultimodalDecisionEngine.

Validates normal operating cycles and safety invariants from EXPERIMENT_PROTOCOL_V2.md §9.
"""

from __future__ import annotations


from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.fusion.rules import CrossingState, GateState, RuleId


def _frame(
    t: float,
    v_dets=(),
    a_dets=(),
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
        source_availability={
            "camera_1": c1_avail,
            "camera_2": c2_avail,
            "audio_1": a_avail,
        },
    )


def test_normal_train_passage_full_cycle():
    """Verify complete normal crossing cycle from IDLE to GATE_CLOSING, OCCUPIED, CLEAR, and OPEN."""
    engine = MultimodalDecisionEngine(
        warning_dwell_s=2.0,
        gate_closing_s=3.0,
        gate_opening_s=3.0,
        clearance_dwell_s=3.0,
        confirm_frames=2,
    )
    engine.reset(0.0)

    # 1. Approach detected at t=1.0 (frame 1) -> TRAIN_APPROACHING
    rec = engine.evaluate_frame(_frame(1.0, v_dets=[Detection("front", 0.8)]))
    assert rec.resulting_state == CrossingState.TRAIN_APPROACHING.value
    assert rec.resulting_gate_state == GateState.OPEN.value

    # 2. Approach confirmed at t=1.1 (frame 2) -> WARNING
    rec = engine.evaluate_frame(_frame(1.1, v_dets=[Detection("front", 0.85)]))
    assert rec.resulting_state == CrossingState.WARNING.value
    assert rec.resulting_gate_state == GateState.OPEN.value

    # 3. Warning dwell elapses at t=3.2 -> GATE_CLOSING
    rec = engine.evaluate_frame(_frame(3.2, v_dets=[Detection("front", 0.8)]))
    assert rec.resulting_state == CrossingState.GATE_CLOSING.value
    assert rec.resulting_gate_state == GateState.CLOSING.value

    # 4. Gate closing time elapses at t=6.3 -> TRAIN_PRESENT, gate CLOSED
    rec = engine.evaluate_frame(_frame(6.3, v_dets=[Detection("front", 0.8)]))
    assert rec.resulting_state == CrossingState.TRAIN_PRESENT.value
    assert rec.resulting_gate_state == GateState.CLOSED.value

    # 5. Crossing occupied at t=7.0
    rec = engine.evaluate_frame(_frame(7.0, v_dets=[Detection("side", 0.9)]))
    assert rec.resulting_state == CrossingState.CROSSING_OCCUPIED.value
    assert rec.resulting_gate_state == GateState.CLOSED.value

    # 6. Train departing at t=10.0
    rec = engine.evaluate_frame(_frame(10.0, v_dets=[Detection("rear", 0.75)]))
    assert rec.resulting_state == CrossingState.TRAIN_DEPARTING.value
    assert rec.resulting_gate_state == GateState.CLOSED.value

    # 7. Rear confirmed at t=10.5
    rec = engine.evaluate_frame(_frame(10.5, v_dets=[Detection("rear", 0.8)]))
    assert rec.resulting_state == CrossingState.REAR_CONFIRMED.value
    assert rec.resulting_gate_state == GateState.CLOSED.value

    # 8. Train clears at t=11.0 (0 detections), clearance dwell begins
    rec = engine.evaluate_frame(_frame(11.0, v_dets=[]))
    assert rec.resulting_state == CrossingState.REAR_CONFIRMED.value

    # 9. Clearance dwell satisfies at t=14.1 (3.1s later) -> CROSSING_CLEAR
    rec = engine.evaluate_frame(_frame(14.1, v_dets=[]))
    assert rec.resulting_state == CrossingState.CROSSING_CLEAR.value

    # 10. Frame at t=14.2 initiates GATE_OPENING
    rec = engine.evaluate_frame(_frame(14.2, v_dets=[]))
    assert rec.resulting_state == CrossingState.GATE_OPENING.value
    assert rec.resulting_gate_state == GateState.OPENING.value

    # 11. Opening completes at t=17.3 (3.1s later) -> IDLE, OPEN
    rec = engine.evaluate_frame(_frame(17.3, v_dets=[]))
    assert rec.resulting_state == CrossingState.IDLE.value
    assert rec.resulting_gate_state == GateState.OPEN.value


def test_regression_audio_alone_never_closes_or_opens_in_idle():
    """Scenario 5: Audio train noise alone cannot actuate gate in IDLE."""
    engine = MultimodalDecisionEngine()
    engine.reset(0.0)

    rec = engine.evaluate_frame(_frame(1.0, a_dets=[Detection("train", 0.95)]))
    assert rec.resulting_state == CrossingState.IDLE.value
    assert rec.resulting_gate_state == GateState.OPEN.value
    assert rec.rule_id == RuleId.RULE_2_AUDIO_SUPPORT_ONLY.value


def test_regression_both_cameras_fail_triggers_fail_safe_clamp():
    """Scenario 4: If all vision sources drop out while gate is active, clamp CLOSED."""
    engine = MultimodalDecisionEngine()
    engine.reset(0.0)

    # Put into WARNING
    engine.evaluate_frame(_frame(1.0, v_dets=[Detection("front", 0.8)]))
    engine.evaluate_frame(_frame(1.1, v_dets=[Detection("front", 0.85)]))
    assert engine.current_state == CrossingState.WARNING

    # Complete vision blackout (both cameras fail)
    rec = engine.evaluate_frame(_frame(1.2, c1_avail=False, c2_avail=False))
    assert rec.resulting_state == CrossingState.FAULT_FAIL_SAFE.value
    assert rec.resulting_gate_state == GateState.CLOSED.value
    assert rec.rule_id == RuleId.RULE_4_FAIL_SAFE_CLAMP.value

    # Further frames cannot open the gate
    rec2 = engine.evaluate_frame(_frame(5.0, c1_avail=False, c2_avail=False))
    assert rec2.resulting_gate_state == GateState.CLOSED.value


def test_idle_dual_camera_failure_triggers_fail_safe_after_persistence():
    """Verify that sustained total vision blackout from IDLE clamps the gate closed."""
    engine = MultimodalDecisionEngine(confirm_frames=2)
    engine.reset(0.0)
    assert engine.current_state == CrossingState.IDLE

    # Frame 1 of blackout: transient filter keeps in IDLE
    rec1 = engine.evaluate_frame(_frame(0.2, c1_avail=False, c2_avail=False))
    assert rec1.resulting_state == CrossingState.IDLE.value
    assert rec1.resulting_gate_state == GateState.OPEN.value

    # Frame 2 of blackout: sustained loss triggers FAULT_FAIL_SAFE
    rec2 = engine.evaluate_frame(_frame(0.4, c1_avail=False, c2_avail=False))
    assert rec2.resulting_state == CrossingState.FAULT_FAIL_SAFE.value
    assert rec2.resulting_gate_state == GateState.CLOSED.value
    assert rec2.rule_id == RuleId.RULE_4_FAIL_SAFE_CLAMP.value


def test_idle_single_frame_glitch_does_not_clamp():
    """Verify that a single-frame vision glitch followed by sensor recovery does not clamp the gate."""
    engine = MultimodalDecisionEngine(confirm_frames=2)
    engine.reset(0.0)

    # 1 glitch frame
    rec1 = engine.evaluate_frame(_frame(0.2, c1_avail=False, c2_avail=False))
    assert rec1.resulting_state == CrossingState.IDLE.value
    assert rec1.resulting_gate_state == GateState.OPEN.value

    # Sensors recover
    rec2 = engine.evaluate_frame(_frame(0.4, c1_avail=True, c2_avail=True))
    assert rec2.resulting_state == CrossingState.IDLE.value
    assert engine.consecutive_vision_failure_count == 0


def test_regression_new_train_aborts_gate_opening():
    """Scenario 9: New train approach while gate is opening aborts back to CLOSING."""
    engine = MultimodalDecisionEngine(gate_opening_s=3.0)
    engine.reset(0.0)
    engine.current_state = CrossingState.GATE_OPENING
    engine.current_gate_state = GateState.OPENING
    engine.state_entry_time_s = 10.0

    # New train appears at t=11.0 during opening
    rec = engine.evaluate_frame(_frame(11.0, v_dets=[Detection("front", 0.9)]))
    assert rec.resulting_state == CrossingState.GATE_CLOSING.value
    assert rec.resulting_gate_state == GateState.CLOSING.value
    assert rec.rule_id == RuleId.RULE_7_NEW_TRAIN_INTERRUPT.value


def test_regression_audio_delays_clearance():
    """Scenario 8 / Rule 2: Strong audio train presence during clearance dwell delays opening."""
    engine = MultimodalDecisionEngine(clearance_dwell_s=2.0)
    engine.reset(0.0)
    engine.current_state = CrossingState.REAR_CONFIRMED
    engine.current_gate_state = GateState.CLOSED
    engine.clearance_started_at_s = 10.0

    # At t=11.0 (within dwell), train horn/rumble detected on audio
    rec = engine.evaluate_frame(_frame(11.0, a_dets=[Detection("train", 0.85)]))
    assert rec.resulting_state == CrossingState.REAR_CONFIRMED.value
    assert rec.rule_id == RuleId.RULE_2_AUDIO_SUPPORT_ONLY.value

    # Dwell timer was reset by audio presence, so at t=12.5 (only 1.5s after audio reset) not clear yet
    rec2 = engine.evaluate_frame(_frame(12.5))
    assert rec2.resulting_state == CrossingState.REAR_CONFIRMED.value

    # At t=13.5 (2.5s after audio reset) clearance dwell satisfied
    rec3 = engine.evaluate_frame(_frame(13.5))
    assert rec3.resulting_state == CrossingState.CROSSING_CLEAR.value


def test_regression_out_of_order_timestamps_rejected():
    """Scenario 11: Out-of-order timestamps must not reverse or corrupt state."""
    engine = MultimodalDecisionEngine()
    engine.reset(0.0)

    engine.evaluate_frame(_frame(10.0))
    rec = engine.evaluate_frame(_frame(5.0))  # 5.0 < 10.0
    assert rec.fault_status == "out_of_order"
    assert rec.rule_id == RuleId.RULE_8_OUT_OF_ORDER_REJECTION.value
