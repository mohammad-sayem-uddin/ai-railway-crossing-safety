"""Phase 9, Task 5: minimal synthetic tests probing the class-ambiguity
hypothesis for the Phase 8 clearance divergence (B0 front-only baseline
reached CROSSING_CLEAR 3/11 times; the dual-camera fused condition reached
it 0/11 times for the same 11 events).

Each test pins down one concrete, reproducible behavior of the FROZEN,
UNMODIFIED decision engine (`fusion/decision_engine.py`) and rule functions
(`fusion/rules.py`) using the diagnostic replay facility from Task 4
(`experiments/diagnostic_trace.run_with_diagnostics`). No policy code is
changed here; these tests only characterize what the existing, frozen
policy already does.
"""

from __future__ import annotations

from dataclasses import dataclass

from railway_detection.experiments.diagnostic_trace import run_with_diagnostics
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.fusion.rules import CrossingState, RuleId


@dataclass
class _Timing:
    tick_s: float = 0.2
    confirm_frames: int = 2
    miss_tolerance_frames: int = 2
    warning_dwell_s: float = 2.0
    gate_closing_s: float = 3.0
    gate_opening_s: float = 3.0
    clearance_dwell_s: float = 3.0
    source_staleness_s: float = 2.0
    fault_confirmation_frames: int = 2
    fault_recovery_hold_s: float = 3.0


@dataclass
class _VisionCfg:
    confidence_threshold_approach: float = 0.35
    confidence_threshold_departure: float = 0.35


@dataclass
class _AudioCfg:
    operating_threshold: float = 0.3700


@dataclass
class _Config:
    timing: _Timing
    vision: _VisionCfg
    audio: _AudioCfg


def _config() -> _Config:
    return _Config(timing=_Timing(), vision=_VisionCfg(), audio=_AudioCfg())


def _vision(source_id: str, t: float, label: str | None, conf: float = 0.8) -> EvidenceRecord:
    dets = (Detection(label=label, confidence=conf),) if label else ()
    return EvidenceRecord(timestamp_s=t, source_id=source_id, modality=Modality.VISION, available=True, detections=dets)


def _to_occupied(camera: str = "camera_1") -> tuple[list[EvidenceRecord], float]:
    """Minimal approach -> warning -> closing -> occupied sequence using a
    SINGLE camera, matching the Phase 8 B0 baseline's single front-camera
    topology. Returns (records, t_reached_occupied)."""
    recs: list[EvidenceRecord] = []
    t = 0.0
    for _ in range(2):
        recs.append(_vision(camera, t, "front"))
        t += 0.2
    t = 2.0 + 0.1
    recs.append(_vision(camera, t, "front"))
    t = recs[-1].timestamp_s + 3.0 + 0.1
    recs.append(_vision(camera, t, "front"))
    t += 0.2
    recs.append(_vision(camera, t, "front"))  # TRAIN_PRESENT -> CROSSING_OCCUPIED
    return recs, t


def test_valid_departure_from_dedicated_rear_camera_is_unambiguous() -> None:
    """Baseline/control case: a dedicated rear camera (source id containing
    "2"/"back"/"rear") reporting the literal "rear" label produces a clean,
    unambiguous RULE_3_POSITIVE_CLEARANCE transition into REAR_CONFIRMED.
    This is the case the frozen policy was designed for."""
    config = _config()
    recs, t_occupied = _to_occupied("camera_1")
    t = t_occupied + 0.2
    recs.append(_vision("camera_2", t, "rear"))
    t += 0.2
    recs.append(_vision("camera_2", t, "rear"))
    duration = t + 0.2

    result = run_with_diagnostics(
        vision_records=recs, audio_records=[], duration_s=duration, stride_s=0.2,
        event_id="synthetic_event", condition="valid_departure", config=config,
    )
    rear_confirm_ticks = [tk for tk in result.ticks if tk.resulting_state == CrossingState.REAR_CONFIRMED.value]
    assert rear_confirm_ticks, "expected a clean REAR_CONFIRMED transition from dedicated rear-camera evidence"
    tick = rear_confirm_ticks[0]
    assert tick.rule_id == RuleId.RULE_3_POSITIVE_CLEARANCE.value
    assert tick.departure_detected is True


def test_front_only_camera_can_satisfy_departure_without_any_rear_evidence() -> None:
    """DIRECTLY TESTS THE CLASS-AMBIGUITY HYPOTHESIS: with only ONE camera
    registered (no dedicated rear/back camera at all, matching Phase 8's B0
    front-only baseline topology), the SAME front camera emitting the
    ambiguous "train" label -- which is a member of both APPROACH_LABELS
    and DEPARTURE_LABELS in fusion/rules.py -- is enough to satisfy
    `has_qualified_departure` and drive CROSSING_OCCUPIED -> TRAIN_DEPARTING
    -> REAR_CONFIRMED. No rear-facing camera, and no "rear"-labeled
    detection, was ever observed. This demonstrates the frozen policy's
    departure rules are camera-viewpoint-agnostic: they inspect only the
    detection LABEL, never `record.source_id`, so a single ambiguous-label
    camera can impersonate rear clearance evidence."""
    config = _config()
    recs, t_occupied = _to_occupied("camera_1")
    t = t_occupied + 0.2
    recs.append(_vision("camera_1", t, "train"))  # TRAIN_DEPARTING
    t += 0.2
    recs.append(_vision("camera_1", t, "train"))  # REAR_CONFIRMED
    duration = t + 0.2

    result = run_with_diagnostics(
        vision_records=recs, audio_records=[], duration_s=duration, stride_s=0.2,
        event_id="synthetic_event", condition="front_only_ambiguous", config=config,
    )
    rear_confirm_ticks = [tk for tk in result.ticks if tk.resulting_state == CrossingState.REAR_CONFIRMED.value]
    assert rear_confirm_ticks, (
        "expected the engine to reach REAR_CONFIRMED from front-camera-only ambiguous 'train' "
        "labels, with no rear camera registered at all and no 'rear' label ever observed"
    )
    tick = rear_confirm_ticks[0]
    assert tick.rule_id == RuleId.RULE_3_POSITIVE_CLEARANCE.value
    # Every evidence reference up to this point is from camera_1 -- the
    # single front camera -- never a dedicated rear/back source.
    assert all(ref.startswith("camera_1:") for tk in result.ticks[: rear_confirm_ticks[0].tick_index + 1] for ref in tk.evidence_references)


def test_lingering_side_label_from_departure_camera_resets_dwell_as_new_train_interrupt() -> None:
    """The departure camera that JUST confirmed rear clearance continuing to
    emit the ambiguous "side" label during the clearance dwell -- plausibly
    still observing the same departing train's receding silhouette, not a
    genuinely new train -- is indistinguishable, under the frozen rule set,
    from a brand new approaching train: both satisfy `has_qualified_approach`
    via the same "side" label in APPROACH_LABELS, so RULE_7_NEW_TRAIN_INTERRUPT
    fires and the dwell resets, even though the SAME camera and SAME physical
    train produced both the rear-confirmation and the 'interrupting' evidence."""
    config = _config()
    recs, t_occupied = _to_occupied("camera_1")
    t = t_occupied + 0.2
    recs.append(_vision("camera_2", t, "rear"))
    t += 0.2
    recs.append(_vision("camera_2", t, "rear"))
    t_rear_confirmed = t

    t_lingering = t_rear_confirmed + 0.4
    recs.append(_vision("camera_2", t_lingering, "side"))  # same departure camera, lingering/uncertain label
    duration = t_lingering + 0.4

    result = run_with_diagnostics(
        vision_records=recs, audio_records=[], duration_s=duration, stride_s=0.2,
        event_id="synthetic_event", condition="lingering_side", config=config,
    )
    interrupt_ticks = [
        tk for tk in result.ticks
        if abs(tk.timestamp_s - t_lingering) < 0.15 and tk.rule_id == RuleId.RULE_7_NEW_TRAIN_INTERRUPT.value
    ]
    assert interrupt_ticks, (
        "expected the departure camera's own lingering 'side' label to trigger "
        "RULE_7_NEW_TRAIN_INTERRUPT even though it is the same camera/train that just confirmed departure"
    )
    tick = interrupt_ticks[0]
    assert tick.previous_state == CrossingState.REAR_CONFIRMED.value
    assert tick.resulting_state == CrossingState.TRAIN_PRESENT.value
    # Confirm the evidence that triggered the interrupt came from the SAME
    # source that had just confirmed rear clearance, not a different camera.
    assert any(ref.startswith("camera_2:") for ref in tick.evidence_references)


def test_camera_disagreement_simultaneous_front_approach_and_rear_departure_labels() -> None:
    """Simultaneous, conflicting evidence at the same tick during
    CROSSING_OCCUPIED: the front camera reports "front" (approach-only,
    not in DEPARTURE_LABELS) while the rear camera reports "rear"
    (departure-only) at the identical timestamp. The frozen rules resolve
    this by OR-ing departure evidence across ALL sources with no
    disagreement-detection step: `has_qualified_departure` returns True
    the moment ANY source reports a departure-qualifying label, regardless
    of what any OTHER source simultaneously reports. The transition is
    driven purely by departure evidence being present somewhere, not by an
    examination of agreement between cameras."""
    config = _config()
    recs, t_occupied = _to_occupied("camera_1")
    # `t_occupied` is the tick whose evaluation drives GATE_CLOSING ->
    # TRAIN_PRESENT; reaching CROSSING_OCCUPIED itself needs one further
    # tick evaluated while already in TRAIN_PRESENT. Settle into
    # CROSSING_OCCUPIED with unambiguous approach-only evidence first, so
    # the disagreement injected afterwards is evaluated with
    # previous_state already CROSSING_OCCUPIED (verified via a standalone
    # replay trace), not conflated with the TRAIN_PRESENT->OCCUPIED step.
    t_settle = t_occupied + 0.2
    recs.append(_vision("camera_1", t_settle, "front"))
    t_disagree = t_settle + 0.2
    recs.append(_vision("camera_1", t_disagree, "front"))  # approach-only label, front camera
    recs.append(_vision("camera_2", t_disagree, "rear"))  # departure-only label, rear camera, SAME tick
    duration = t_disagree + 0.4

    result = run_with_diagnostics(
        vision_records=recs, audio_records=[], duration_s=duration, stride_s=0.2,
        event_id="synthetic_event", condition="camera_disagreement", config=config,
    )
    disagreement_ticks = [tk for tk in result.ticks if abs(tk.timestamp_s - t_disagree) < 0.15]
    assert disagreement_ticks, "expected a tick at the disagreement timestamp"
    tick = disagreement_ticks[0]
    assert tick.approach_detected is True
    assert tick.departure_detected is True
    assert tick.previous_state == CrossingState.CROSSING_OCCUPIED.value
    assert tick.resulting_state == CrossingState.TRAIN_DEPARTING.value, (
        "expected departure evidence to win the transition despite simultaneous, "
        "conflicting approach evidence from a different camera at the same tick"
    )


def test_stale_departure_camera_during_clearance_dwell_triggers_fail_safe_abort() -> None:
    """If the departure (rear/back) camera goes stale/missing during the
    REAR_CONFIRMED clearance dwell -- e.g. it stops emitting frames for
    longer than `source_staleness_s` -- RULE_5_STALE_SOURCE_ABORT fires and
    the crossing is clamped to FAULT_FAIL_SAFE instead of ever reaching
    CROSSING_CLEAR, even if the approach camera remains perfectly healthy.
    This is a directly plausible, saved-log-visible explanation for why a
    dual-camera fused run could fail to reach CROSSING_CLEAR where a
    front-only baseline (with no second camera to go stale) would not hit
    this failure mode at all."""
    config = _config()
    recs, t_occupied = _to_occupied("camera_1")
    t = t_occupied + 0.2
    recs.append(_vision("camera_2", t, "rear"))
    t += 0.2
    recs.append(_vision("camera_2", t, "rear"))
    t_rear_confirmed = t

    # Keep the APPROACH camera healthy throughout, but never emit another
    # observation from camera_2 (the departure camera) after rear
    # confirmation -- it goes stale after source_staleness_s (2.0s).
    tt = t_rear_confirmed + 0.2
    duration = t_rear_confirmed + 3.0
    while tt <= duration:
        recs.append(_vision("camera_1", tt, None))
        tt += 0.2

    result = run_with_diagnostics(
        vision_records=recs, audio_records=[], duration_s=duration, stride_s=0.2,
        event_id="synthetic_event", condition="stale_departure_camera", config=config,
    )
    abort_ticks = [tk for tk in result.ticks if tk.rule_id == RuleId.RULE_5_STALE_SOURCE_ABORT.value]
    assert abort_ticks, "expected RULE_5_STALE_SOURCE_ABORT once the departure camera goes stale during the dwell"
    tick = abort_ticks[0]
    assert tick.previous_state == CrossingState.REAR_CONFIRMED.value
    assert tick.resulting_state == CrossingState.FAULT_FAIL_SAFE.value
    assert tick.source_health.get("camera_2") in ("stale", "missing")
    clear_ticks = [tk for tk in result.ticks if tk.resulting_state == CrossingState.CROSSING_CLEAR.value]
    assert not clear_ticks, "must never reach CROSSING_CLEAR once the departure camera has gone stale mid-dwell"
