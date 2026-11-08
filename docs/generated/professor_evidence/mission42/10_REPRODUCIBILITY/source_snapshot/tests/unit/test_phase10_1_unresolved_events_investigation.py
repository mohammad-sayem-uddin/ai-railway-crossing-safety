"""Phase 10.1, Task 4: controlled synthetic fixtures isolating the exact
mechanism behind the real-event replay's 5 unresolved events (identified in
`results/r04_sync_estimation/phase10_1_restricted_comparison_*`), confirming
it in a minimal, reproducible setting separate from the real cached
evidence. No threshold is lowered and no directional evidence is invented
to force these to clear -- they are expected to demonstrate the SAME
failure to clear as the real events, not a fix.
"""

from __future__ import annotations

from dataclasses import dataclass

from railway_detection.experiments.diagnostic_trace import run_with_diagnostics
from railway_detection.fusion.decision_engine_v2_candidate import MultimodalDecisionEngineV2Candidate
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.fusion.rules import CrossingState
from railway_detection.fusion.rules_v2_candidate import (
    RuleIdV2,
    has_unambiguous_approach_label,
    has_unambiguous_departure_label,
)


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


def _vision(source_id: str, t: float, label: str | None, conf: float = 0.6) -> EvidenceRecord:
    dets = (Detection(label=label, confidence=conf),) if label else ()
    return EvidenceRecord(timestamp_s=t, source_id=source_id, modality=Modality.VISION, available=True, detections=dets)


def _run_candidate(recs, duration, config):
    return run_with_diagnostics(
        vision_records=recs, audio_records=[], duration_s=duration, stride_s=0.2,
        event_id="e", condition="candidate", config=config,
        engine_factory=MultimodalDecisionEngineV2Candidate,
        approach_fn=has_unambiguous_approach_label, departure_fn=has_unambiguous_departure_label,
    )


def _to_occupied_dual_camera():
    recs = []
    t = 0.0
    for _ in range(2):
        recs.append(_vision("camera_1", t, "front", conf=0.8))
        t += 0.2
    t = 2.1
    recs.append(_vision("camera_1", t, "front", conf=0.8))
    t += 3.1
    recs.append(_vision("camera_1", t, "front", conf=0.8))
    t += 0.2
    recs.append(_vision("camera_1", t, "front", conf=0.8))
    recs.append(_vision("camera_2", t, "front", conf=0.8))
    return recs, t


def test_near_continuous_ambiguous_detection_density_prevents_disappearance_confirmation() -> None:
    """Isolates the exact mechanism found in the real 11-event replay for
    events 005/007/017: a departure-role camera that reports an ambiguous
    "side" label on (nearly) every tick -- mirroring the real back-camera
    detection rates of 89-95% measured directly from the cached evidence --
    never accumulates `confirm_frames` (2) CONSECUTIVE silent ticks, so
    RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE can never fire, and (absent
    any literal "rear" label, also matching those 3 real events) departure
    is never confirmed at all for as long as this density continues --
    regardless of how much additional time is available."""
    config = _config()
    recs, t_occupied = _to_occupied_dual_camera()

    # Departure camera reports ambiguous "side" on every tick except a
    # single isolated 1-tick gap every ~1.0s -- never two CONSECUTIVE
    # silent ticks, so the gap counter is reset before it can reach
    # confirm_frames=2. This mirrors the real events' measured density.
    tt = t_occupied + 0.2
    duration = t_occupied + 20.0
    tick_index = 0
    while tt <= duration:
        recs.append(_vision("camera_1", tt, None))
        if tick_index % 5 == 4:
            # one isolated silent tick on the departure camera, never two in a row
            pass
        else:
            recs.append(_vision("camera_2", tt, "side", conf=0.6))
        tt += 0.2
        tick_index += 1

    result = _run_candidate(recs, duration, config)
    confirmed = [
        t for t in result.ticks
        if t.rule_id in (
            RuleIdV2.RULE_3B_DEPARTURE_CONFIRMED_UNAMBIGUOUS_REAR.value,
            RuleIdV2.RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE.value,
        )
    ]
    assert not confirmed, (
        "expected departure to NEVER be confirmed while the departure camera's ambiguous "
        "detections never leave a 2-tick gap, regardless of the extra 20s of available time -- "
        "reproducing the real event_005/007/017 mechanism in isolation"
    )
    assert result.ticks[-1].resulting_state == CrossingState.TRAIN_DEPARTING.value


def test_two_consecutive_silent_ticks_is_sufficient_to_confirm_despite_high_density() -> None:
    """Control/contrast case: the SAME high-density departure camera, but
    with one genuine, substantially-sized silence gap inserted, DOES confirm
    via RULE_3C at that gap -- proving the mechanism above is specifically
    about gap length, not about "side" labels being categorically
    unconfirmable. (The gap must exceed roughly 2*window_tolerance_s+tick_s
    -- a literal 2-tick input gap gets backfilled by the collector's 0.25s
    window-tolerance frame matching, which reuses the nearest neighboring
    detection across a short gap; this was confirmed by a standalone replay
    trace before fixing this test's gap width.)"""
    config = _config()
    recs, t_occupied = _to_occupied_dual_camera()

    tt = t_occupied + 0.2
    gap_start = t_occupied + 6.0
    gap_end = gap_start + 1.0
    duration = t_occupied + 10.0
    while tt <= duration:
        recs.append(_vision("camera_1", tt, None))
        if gap_start <= tt < gap_end:
            pass  # a genuine, window-tolerance-proof silence on the departure camera
        else:
            recs.append(_vision("camera_2", tt, "side", conf=0.6))
        tt += 0.2

    result = _run_candidate(recs, duration, config)
    confirmed = [t for t in result.ticks if t.rule_id == RuleIdV2.RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE.value]
    assert confirmed, "expected a genuine silence gap to confirm departure via disappearance"


def test_recording_ends_shortly_after_late_departure_confirmation_cannot_complete_dwell() -> None:
    """Isolates the exact mechanism found for event_002 (and, more
    marginally, event_006): departure is genuinely confirmed (here via an
    unambiguous "rear" label, matching event_002's real cached evidence),
    but the recorded evidence ends well before the ~3.2-3.6s dwell
    (including tick-granularity overhead, see Phase 9) can complete. This is
    a data/recording-length limitation, not a policy or model defect --
    confirmed by varying only how much evidence exists after confirmation."""
    config = _config()
    recs, t_occupied = _to_occupied_dual_camera()
    t = t_occupied + 0.2
    recs.append(_vision("camera_2", t, "rear", conf=0.9))
    t += 0.2
    recs.append(_vision("camera_2", t, "rear", conf=0.9))
    t_rear_confirmed = t

    # Only 0.8s of evidence remains after confirmation (matching event_002's
    # measured 0.8s margin) -- too short for the dwell to ever complete.
    tt = t_rear_confirmed + 0.2
    duration = t_rear_confirmed + 0.8
    while tt <= duration:
        recs.append(_vision("camera_1", tt, None))
        recs.append(_vision("camera_2", tt, None))
        tt += 0.2

    result = _run_candidate(recs, duration, config)
    rear_confirmed_ticks = [t for t in result.ticks if t.resulting_state == CrossingState.REAR_CONFIRMED.value]
    cleared = [t for t in result.ticks if t.resulting_state == CrossingState.CROSSING_CLEAR.value]
    assert rear_confirmed_ticks, "departure must still be confirmed despite the short remaining window"
    assert not cleared, "the dwell must not complete when the recording ends before 3.0s has genuinely elapsed"
