"""Independent re-derivation of the ten R04 Phase 6 safety invariants.

Each test is constructed from first principles by tracing the ACTUAL
current `MultimodalDecisionEngine`, `SourceTracker`, and
`MultimodalEvidenceCollector` implementations (read in full for this pass,
not assumed from prior reports or from the existing, separately-maintained
Phase 3/4 test suites). Where this file's findings rely on an existing test
elsewhere, that is stated explicitly rather than silently re-asserted.
"""

from __future__ import annotations

from railway_detection.fusion.collector import MultimodalEvidenceCollector, MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.fusion.rules import CrossingState, GateState
from railway_detection.fusion.source_tracker import HealthReason, SensorHealth, SourceTracker


def _frame(
    t: float,
    front_detections: tuple[Detection, ...] = (),
    back_detections: tuple[Detection, ...] = (),
    audio_detections: tuple[Detection, ...] = (),
    front_available: bool = True,
    back_available: bool = True,
    audio_available: bool = True,
    include_front: bool = True,
    include_back: bool = True,
    include_audio: bool = True,
) -> MultimodalFrame:
    vision = []
    if include_front:
        vision.append(
            EvidenceRecord(
                timestamp_s=t, source_id="camera_1", modality=Modality.VISION,
                available=front_available, detections=front_detections if front_available else (),
            )
        )
    if include_back:
        vision.append(
            EvidenceRecord(
                timestamp_s=t, source_id="camera_2", modality=Modality.VISION,
                available=back_available, detections=back_detections if back_available else (),
            )
        )
    audio = []
    if include_audio:
        audio.append(
            EvidenceRecord(
                timestamp_s=t, source_id="audio_1", modality=Modality.AUDIO,
                available=audio_available, detections=audio_detections if audio_available else (),
            )
        )
    avail = {}
    if include_front:
        avail["camera_1"] = front_available
    if include_back:
        avail["camera_2"] = back_available
    if include_audio:
        avail["audio_1"] = audio_available
    return MultimodalFrame(
        master_timestamp_s=t,
        vision_records=tuple(vision),
        audio_records=tuple(audio),
        source_availability=avail,
    )


FRONT = (Detection(label="front", confidence=0.8),)
REAR = (Detection(label="rear", confidence=0.8),)
HORN = (Detection(label="train_horn", confidence=0.9),)


# ---------------------------------------------------------------- Invariant 1
def test_invariant_1_zero_detections_valid_frame_is_negative_evidence_not_failure() -> None:
    """A valid, available frame with zero detections must NOT be treated as
    a sensor failure: the source stays HEALTHY, the engine stays IDLE, and
    the gate never actuates."""
    engine = MultimodalDecisionEngine(confirm_frames=2)
    t = 0.0
    for _ in range(10):
        rec = engine.evaluate_frame(_frame(t, front_detections=(), back_detections=()))
        assert rec.resulting_state == CrossingState.IDLE.value
        assert rec.resulting_gate_state == GateState.OPEN.value
        assert rec.fault_status == "none"
        t += 0.2
    health = engine.source_tracker.get_health("camera_1", t)
    assert health == SensorHealth.HEALTHY, f"expected HEALTHY, got {health}"
    reason = engine.source_tracker.get_reason("camera_1")
    assert reason == HealthReason.OBSERVATION_NO_DETECTIONS


# ---------------------------------------------------------------- Invariant 2
def test_invariant_2_low_audio_score_is_negative_evidence_not_failure() -> None:
    """An available audio record below threshold (so it carries zero
    Detection objects, exactly as has_audio_train_presence expects) must
    not be treated as audio sensor failure, and must not actuate the gate."""
    engine = MultimodalDecisionEngine(confirm_frames=2)
    t = 0.0
    for _ in range(10):
        rec = engine.evaluate_frame(_frame(t, audio_detections=()))  # available, no detections (below threshold)
        assert rec.resulting_state == CrossingState.IDLE.value
        assert rec.resulting_gate_state == GateState.OPEN.value
        t += 0.2
    assert engine.source_tracker.get_health("audio_1", t) == SensorHealth.HEALTHY


# ---------------------------------------------------------------- Invariant 3
def test_invariant_3_stale_source_cannot_establish_clear_crossing() -> None:
    """Drive the engine to REAR_CONFIRMED (full passage with positive rear
    evidence), then let the departure camera go silent (no observations at
    all, not even an explicit unavailable record) past the staleness
    timeout. The crossing must NOT reach CROSSING_CLEAR; it must instead
    fail safe to FAULT_FAIL_SAFE with the gate held CLOSED. Mere absence of
    new observations -- staleness -- must never be interpreted as a clear
    crossing."""
    engine = MultimodalDecisionEngine(confirm_frames=2, clearance_dwell_s=3.0)
    t = 0.0
    # Reach WARNING -> GATE_CLOSING -> TRAIN_PRESENT -> CROSSING_OCCUPIED -> TRAIN_DEPARTING -> REAR_CONFIRMED
    for _ in range(2):
        engine.evaluate_frame(_frame(t, front_detections=FRONT)); t += 0.2
    assert engine.current_state == CrossingState.WARNING
    t = engine.state_entry_time_s + engine.warning_dwell_s + 0.1
    engine.evaluate_frame(_frame(t, front_detections=FRONT))
    assert engine.current_state == CrossingState.GATE_CLOSING
    t = engine.state_entry_time_s + engine.gate_closing_s + 0.1
    engine.evaluate_frame(_frame(t, front_detections=FRONT))
    assert engine.current_state == CrossingState.TRAIN_PRESENT
    t += 0.2
    engine.evaluate_frame(_frame(t, front_detections=FRONT, back_detections=FRONT))
    assert engine.current_state == CrossingState.CROSSING_OCCUPIED
    t += 0.2
    engine.evaluate_frame(_frame(t, back_detections=REAR))  # CROSSING_OCCUPIED -> TRAIN_DEPARTING
    assert engine.current_state == CrossingState.TRAIN_DEPARTING
    t += 0.2
    engine.evaluate_frame(_frame(t, back_detections=REAR))  # TRAIN_DEPARTING -> REAR_CONFIRMED
    assert engine.current_state == CrossingState.REAR_CONFIRMED

    # Now the departure (back) camera goes silent: no record at all for it.
    # Advance time well past the 2.0s staleness timeout without ever
    # sending a camera_2 observation again.
    t += 2.5
    rec = engine.evaluate_frame(_frame(t, include_back=False))
    assert rec.resulting_state != CrossingState.CROSSING_CLEAR.value, (
        "a stale departure camera must never be interpreted as clearance"
    )
    assert rec.resulting_state == CrossingState.FAULT_FAIL_SAFE.value
    assert rec.resulting_gate_state == GateState.CLOSED.value


# ---------------------------------------------------------------- Invariant 4
def test_invariant_4_fault_during_train_presence_cannot_recover_directly_to_open() -> None:
    """A fault that occurs while a train is present/approaching must, on
    sensor recovery, land in TRAIN_PRESENT with the gate held CLOSED --
    never directly back to IDLE/OPEN."""
    engine = MultimodalDecisionEngine(confirm_frames=2)
    t = 0.0
    for _ in range(2):
        engine.evaluate_frame(_frame(t, front_detections=FRONT)); t += 0.2
    t = engine.state_entry_time_s + engine.warning_dwell_s + 0.1
    engine.evaluate_frame(_frame(t, front_detections=FRONT))
    t = engine.state_entry_time_s + engine.gate_closing_s + 0.1
    rec = engine.evaluate_frame(_frame(t, front_detections=FRONT))
    assert rec.resulting_state == CrossingState.TRAIN_PRESENT.value

    # Both vision sources vanish entirely (total vision loss while active).
    # A single missed tick (0.2s) is within the 2.0s staleness grace period
    # by design (one dropped frame must not instantly fault-trip the
    # system); advance past the staleness timeout before the source is
    # actually considered failed, matching invariant 3's timing exactly.
    t += 2.2
    rec = engine.evaluate_frame(_frame(t, include_front=False, include_back=False))
    assert rec.resulting_state == CrossingState.FAULT_FAIL_SAFE.value
    assert rec.resulting_gate_state == GateState.CLOSED.value

    # Sensors recover: confirm_frames consecutive clean, train-absent
    # observations (no approach/departure evidence -- simulating the train
    # having physically left the camera's field of view while sensors were
    # down, which is exactly the dangerous case this invariant guards).
    for _ in range(2):
        t += 0.2
        rec = engine.evaluate_frame(_frame(t))
    assert rec.resulting_state == CrossingState.TRAIN_PRESENT.value, (
        "recovery from a fault that began during an active crossing must land in "
        "TRAIN_PRESENT, never directly in IDLE"
    )
    assert rec.resulting_gate_state == GateState.CLOSED.value, (
        "the gate must remain CLOSED on this recovery path -- it must not auto-open"
    )


# ---------------------------------------------------------------- Invariant 5
def test_invariant_5_reopening_requires_departure_evidence_and_uninterrupted_dwell() -> None:
    """Reaching CROSSING_CLEAR (and therefore eventually GATE_OPENING) must
    require (a) positive rear/departure evidence was seen, and (b) an
    UNINTERRUPTED clearance dwell with no conflicting audio evidence --
    conflicting audio must restart the dwell, not merely pause it."""
    engine = MultimodalDecisionEngine(confirm_frames=2, clearance_dwell_s=3.0)
    t = 0.0
    for _ in range(2):
        engine.evaluate_frame(_frame(t, front_detections=FRONT)); t += 0.2
    t = engine.state_entry_time_s + engine.warning_dwell_s + 0.1
    engine.evaluate_frame(_frame(t, front_detections=FRONT))
    t = engine.state_entry_time_s + engine.gate_closing_s + 0.1
    engine.evaluate_frame(_frame(t, front_detections=FRONT))
    t += 0.2
    engine.evaluate_frame(_frame(t, front_detections=FRONT, back_detections=FRONT))
    t += 0.2
    engine.evaluate_frame(_frame(t, back_detections=REAR))  # CROSSING_OCCUPIED -> TRAIN_DEPARTING
    assert engine.current_state == CrossingState.TRAIN_DEPARTING
    t += 0.2
    rec = engine.evaluate_frame(_frame(t, back_detections=REAR))  # TRAIN_DEPARTING -> REAR_CONFIRMED
    assert rec.resulting_state == CrossingState.REAR_CONFIRMED.value

    # 1.5s of clean dwell elapses...
    t += 1.5
    engine.evaluate_frame(_frame(t))
    assert engine.current_state == CrossingState.REAR_CONFIRMED

    # ...then audio train evidence appears, which MUST restart the dwell.
    t += 0.2
    engine.evaluate_frame(_frame(t, audio_detections=HORN))
    assert engine.current_state == CrossingState.REAR_CONFIRMED
    restarted_at = engine.clearance_started_at_s
    assert restarted_at == t, "audio evidence must restart (not merely pause) the clearance dwell"

    # Another 1.5s clean -- still short of the FULL 3.0s dwell measured from
    # the restart point -- must NOT yet reach CROSSING_CLEAR.
    t += 1.5
    rec = engine.evaluate_frame(_frame(t))
    assert rec.resulting_state == CrossingState.REAR_CONFIRMED.value, (
        "must not clear before a full, uninterrupted dwell measured from the restart"
    )

    # Completing the full dwell from the restart point (3.0s total) clears.
    t = restarted_at + 3.0 + 0.1
    rec = engine.evaluate_frame(_frame(t))
    assert rec.resulting_state == CrossingState.CROSSING_CLEAR.value


# ---------------------------------------------------------------- Invariant 6
def test_invariant_6_audio_alone_cannot_trigger_unsafe_gate_transition() -> None:
    """From IDLE, audio train evidence with NO corroborating vision approach
    must never actuate the gate or leave IDLE, for an extended period."""
    engine = MultimodalDecisionEngine(confirm_frames=2)
    t = 0.0
    for _ in range(50):
        rec = engine.evaluate_frame(_frame(t, audio_detections=HORN))
        assert rec.resulting_state == CrossingState.IDLE.value
        assert rec.resulting_gate_state == GateState.OPEN.value
        t += 0.2


# ---------------------------------------------------------------- Invariant 7
def test_invariant_7_invalid_cross_camera_timing_cannot_be_synchronized() -> None:
    """Re-confirms, at the fusion-collector layer exercised directly by the
    decision engine's own evidence path, that an unregistered dual-camera
    source cannot silently enter a frame at an unvalidated zero offset.
    (Full manifest-level coverage is in test_validated_sync_aligner.py and
    test_production_dual_camera_integration.py; this test adds the
    decision-engine-facing angle: a frame built from an incompletely
    registered aligner must never reach evaluate_frame at all.)"""
    from railway_detection.data.sync import SyncAligner

    aligner = SyncAligner()
    aligner.add_source("camera_1", offset_s=0.0, uncertainty_s=0.0)
    # camera_2 deliberately unregistered.
    collector = MultimodalEvidenceCollector(sync_aligner=aligner)
    collector.add_evidence(
        EvidenceRecord(timestamp_s=1.0, source_id="camera_1", modality=Modality.VISION, available=True)
    )
    try:
        collector.add_evidence(
            EvidenceRecord(timestamp_s=1.0, source_id="camera_2", modality=Modality.VISION, available=True)
        )
        raised = False
    except ValueError:
        raised = True
    assert raised, "an unregistered vision source must never silently enter the evidence buffer"


# ---------------------------------------------------------------- Invariant 8
def test_invariant_8_sensor_recovery_and_train_presence_state_remain_distinct() -> None:
    """SensorHealth and CrossingState are independent axes: a sensor
    transitioning through MISSING -> RECOVERING -> HEALTHY must not, by
    itself, move the crossing state machine -- only the engine's explicit
    rule branches (traced in invariant 4) may do that."""
    tracker = SourceTracker(default_timeout_s=2.0, confirmation_frames=2)
    tracker.register_source("camera_1", modality=Modality.VISION)

    tracker.record_observation("camera_1", timestamp_s=0.0, available=True, detections=())
    assert tracker.get_health("camera_1") == SensorHealth.HEALTHY

    tracker.record_observation("camera_1", timestamp_s=1.0, available=False)
    assert tracker.get_health("camera_1") == SensorHealth.MISSING

    tracker.record_observation("camera_1", timestamp_s=2.0, available=True, detections=())
    assert tracker.get_health("camera_1") == SensorHealth.RECOVERING

    tracker.record_observation("camera_1", timestamp_s=2.2, available=True, detections=())
    assert tracker.get_health("camera_1") == SensorHealth.HEALTHY

    # None of this touched any CrossingState or GateState concept at all --
    # SourceTracker has no such field, by construction. The engine-level
    # distinctness (recovery alone never implies clearance) is the subject
    # of invariant 4 above.


# ---------------------------------------------------------------- Invariant 9
def test_invariant_9a_duplicate_frames_cannot_satisfy_dwell_faster_than_real_time() -> None:
    """Re-delivering the SAME frame (identical master timestamp) repeatedly
    must not advance the clearance dwell timer at all -- dwell is measured
    in elapsed master-clock time, and a duplicate frame, being rejected
    before any state mutation, contributes zero elapsed time."""
    engine = MultimodalDecisionEngine(confirm_frames=2, clearance_dwell_s=3.0)
    t = 0.0
    for _ in range(2):
        engine.evaluate_frame(_frame(t, front_detections=FRONT)); t += 0.2
    t = engine.state_entry_time_s + engine.warning_dwell_s + 0.1
    engine.evaluate_frame(_frame(t, front_detections=FRONT))
    t = engine.state_entry_time_s + engine.gate_closing_s + 0.1
    engine.evaluate_frame(_frame(t, front_detections=FRONT))
    t += 0.2
    engine.evaluate_frame(_frame(t, front_detections=FRONT, back_detections=FRONT))
    t += 0.2
    engine.evaluate_frame(_frame(t, back_detections=REAR))  # CROSSING_OCCUPIED -> TRAIN_DEPARTING
    assert engine.current_state == CrossingState.TRAIN_DEPARTING
    t += 0.2
    engine.evaluate_frame(_frame(t, back_detections=REAR))  # TRAIN_DEPARTING -> REAR_CONFIRMED
    assert engine.current_state == CrossingState.REAR_CONFIRMED
    clearance_start = engine.clearance_started_at_s

    # Re-deliver the exact same frame (same t) one hundred times.
    for _ in range(100):
        rec = engine.evaluate_frame(_frame(t))
        assert rec.fault_status == "duplicate_frame"
        assert rec.resulting_state == CrossingState.REAR_CONFIRMED.value
    assert engine.clearance_started_at_s == clearance_start, (
        "duplicate-frame replay must not touch the dwell timer at all"
    )
    assert engine.current_state == CrossingState.REAR_CONFIRMED, (
        "one hundred duplicate deliveries of the same instant must not advance the state "
        "machine even one step -- only real elapsed master-clock time may do that"
    )


def test_invariant_9b_out_of_order_frame_rejected_without_mutating_clearance_timer() -> None:
    engine = MultimodalDecisionEngine(confirm_frames=2, clearance_dwell_s=3.0)
    t = 0.0
    for _ in range(2):
        engine.evaluate_frame(_frame(t, front_detections=FRONT)); t += 0.2
    t = engine.state_entry_time_s + engine.warning_dwell_s + 0.1
    engine.evaluate_frame(_frame(t, front_detections=FRONT))
    t = engine.state_entry_time_s + engine.gate_closing_s + 0.1
    engine.evaluate_frame(_frame(t, front_detections=FRONT))
    t += 0.2
    engine.evaluate_frame(_frame(t, front_detections=FRONT, back_detections=FRONT))
    t += 0.2
    engine.evaluate_frame(_frame(t, back_detections=REAR))  # CROSSING_OCCUPIED -> TRAIN_DEPARTING
    assert engine.current_state == CrossingState.TRAIN_DEPARTING
    t += 0.2
    engine.evaluate_frame(_frame(t, back_detections=REAR))  # TRAIN_DEPARTING -> REAR_CONFIRMED
    assert engine.current_state == CrossingState.REAR_CONFIRMED
    clearance_start = engine.clearance_started_at_s

    stale_t = t - 1.0  # strictly in the past
    rec = engine.evaluate_frame(_frame(stale_t))
    assert rec.fault_status == "out_of_order"
    assert rec.resulting_state == CrossingState.REAR_CONFIRMED.value
    assert engine.clearance_started_at_s == clearance_start


# ---------------------------------------------------------------- Invariant 10
def test_invariant_10_fresh_collector_per_event_prevents_cross_event_mixing() -> None:
    """`LayerBEventProcessor.build_multimodal_frames` constructs a brand new
    `MultimodalEvidenceCollector` on every call (verified by reading the
    production source for this pass). This test proves the consequence
    directly at the collector level: two independently-constructed
    collectors fed overlapping/identical local timestamps for the SAME
    source_id never share state, so two events processed as two separate
    calls (the only pattern the production scripts use) cannot leak
    evidence into each other. `EvidenceRecord` carries no event_id field,
    so this isolation is structural (fresh object per call) rather than
    enforced by a same-object identity check -- documented as a known
    reliance on caller discipline in docs/R04_IMPLEMENTATION_AND_UNBLOCK_REPORT.md."""
    collector_event_a = MultimodalEvidenceCollector()
    collector_event_b = MultimodalEvidenceCollector()

    collector_event_a.add_evidence(
        EvidenceRecord(
            timestamp_s=5.0, source_id="camera_1", modality=Modality.VISION,
            available=True, detections=(Detection(label="front", confidence=0.9),),
        )
    )
    # Event B's camera_1 at the SAME local timestamp carries DIFFERENT
    # evidence (no detections) -- if state leaked between collectors this
    # would be contaminated by event A's detection.
    collector_event_b.add_evidence(
        EvidenceRecord(
            timestamp_s=5.0, source_id="camera_1", modality=Modality.VISION,
            available=True, detections=(),
        )
    )

    frame_a = collector_event_a.collect_frame(5.0, purge_older_than_s=100.0)
    frame_b = collector_event_b.collect_frame(5.0, purge_older_than_s=100.0)

    assert any(r.detections for r in frame_a.vision_records), "event A must see its own detection"
    assert not any(r.detections for r in frame_b.vision_records), (
        "event B must NOT see event A's detection -- collectors must not share state"
    )
