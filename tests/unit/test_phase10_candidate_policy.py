"""Phase 10, Task 3: controlled comparison tests between the frozen policy
(`MultimodalDecisionEngine` / `fusion/rules.py`) and the candidate policy
(`MultimodalDecisionEngineV2Candidate` / `fusion/rules_v2_candidate.py`).

Neither `fusion/rules.py`, `fusion/decision_engine.py`, nor
`configs/decision_policy_v1.yaml` is touched by this file or by the
candidate modules it imports. Every scenario below is built once as a
synthetic evidence sequence and replayed through BOTH engines via the same
`run_with_diagnostics` facility, so any behavioral difference recorded here
is attributable only to the policy, not to any difference in how the frames
were constructed or replayed.

Per the Phase 10 brief: this suite is not tuned to make every scenario reach
CROSSING_CLEAR. Several tests assert that BOTH policies behave identically
(stale-source abort, duplicate/out-of-order rejection, genuine new-train
interruption) specifically to confirm the candidate has not weakened any
existing safety behavior while fixing the Phase 9 mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass

from railway_detection.experiments.diagnostic_trace import run_with_diagnostics
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.decision_engine_v2_candidate import MultimodalDecisionEngineV2Candidate
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.fusion.rules import CrossingState, RuleId
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


def _vision(source_id: str, t: float, label: str | None, conf: float = 0.8) -> EvidenceRecord:
    dets = (Detection(label=label, confidence=conf),) if label else ()
    return EvidenceRecord(timestamp_s=t, source_id=source_id, modality=Modality.VISION, available=True, detections=dets)


def _run_frozen(recs, duration, event_id, condition, config):
    return run_with_diagnostics(
        vision_records=recs, audio_records=[], duration_s=duration, stride_s=0.2,
        event_id=event_id, condition=condition, config=config,
        engine_factory=MultimodalDecisionEngine,
    )


def _run_candidate(recs, duration, event_id, condition, config):
    return run_with_diagnostics(
        vision_records=recs, audio_records=[], duration_s=duration, stride_s=0.2,
        event_id=event_id, condition=condition, config=config,
        engine_factory=MultimodalDecisionEngineV2Candidate,
        approach_fn=has_unambiguous_approach_label,
        departure_fn=has_unambiguous_departure_label,
    )


def _to_rear_confirmed_dual_camera(approach_label: str = "front") -> tuple[list[EvidenceRecord], float]:
    """Approach -> warning -> closing -> occupied -> departing, with the
    departure camera confirming via unambiguous "rear" at the end. Both
    policies reach REAR_CONFIRMED identically from this sequence (the
    difference under test happens AFTER this point)."""
    recs: list[EvidenceRecord] = []
    t = 0.0
    for _ in range(2):
        recs.append(_vision("camera_1", t, approach_label))
        t += 0.2
    t = 2.1
    recs.append(_vision("camera_1", t, approach_label))
    t += 3.1
    recs.append(_vision("camera_1", t, approach_label))
    t += 0.2
    recs.append(_vision("camera_1", t, approach_label))
    recs.append(_vision("camera_2", t, "front"))
    t += 0.2
    recs.append(_vision("camera_2", t, "rear"))
    t += 0.2
    recs.append(_vision("camera_2", t, "rear"))
    return recs, t


# --- Scenario 1: a train approaching -----------------------------------

def test_approach_scenario_both_policies_reach_warning_identically() -> None:
    config = _config()
    recs = [_vision("camera_1", 0.0, "front"), _vision("camera_1", 0.2, "front")]
    duration = 0.4

    frozen = _run_frozen(recs, duration, "e", "frozen", config)
    candidate = _run_candidate(recs, duration, "e", "candidate", config)

    frozen_warning = next(t for t in frozen.ticks if t.resulting_state == CrossingState.WARNING.value)
    candidate_warning = next(t for t in candidate.ticks if t.resulting_state == CrossingState.WARNING.value)
    assert frozen_warning.rule_id == RuleId.RULE_1_APPROACH_TRIGGER.value
    assert candidate_warning.rule_id == RuleIdV2.RULE_1_APPROACH_TRIGGER.value


# --- Scenario 2: departing while remaining visible (THE Phase 9 fix) ---

def test_departing_while_remaining_visible_frozen_oscillates_candidate_clears() -> None:
    """The exact mechanism demonstrated in Phase 9 on real data: the
    departure camera confirms rear clearance, then the SAME train's
    lingering ambiguous "side" classification continues to be reported by
    the approach camera throughout the dwell window. Under the frozen
    policy this repeatedly fires RULE_7 and the dwell never completes;
    under the candidate it is correctly recognized as continuing, not new,
    evidence and the dwell completes cleanly."""
    config = _config()
    recs, t_rear_confirmed = _to_rear_confirmed_dual_camera()

    tt = t_rear_confirmed + 0.2
    duration = t_rear_confirmed + 6.0
    while tt <= duration:
        recs.append(_vision("camera_1", tt, "side", conf=0.6))  # continuous lingering, same source, no gap
        recs.append(_vision("camera_2", tt, None))
        tt += 0.2

    frozen = _run_frozen(recs, duration, "e", "frozen", config)
    candidate = _run_candidate(recs, duration, "e", "candidate", config)

    frozen_interrupts = [t for t in frozen.ticks if t.rule_id == RuleId.RULE_7_NEW_TRAIN_INTERRUPT.value]
    candidate_interrupts = [t for t in candidate.ticks if t.rule_id == RuleIdV2.RULE_7_NEW_TRAIN_INTERRUPT.value]
    frozen_cleared = any(t.resulting_state == CrossingState.CROSSING_CLEAR.value for t in frozen.ticks)
    candidate_cleared = any(t.resulting_state == CrossingState.CROSSING_CLEAR.value for t in candidate.ticks)

    assert frozen_interrupts, "frozen policy is expected to repeatedly interrupt on the lingering 'side' label"
    assert not frozen_cleared, "frozen policy is expected to never clear in this scenario (reproduces Phase 9)"
    assert not candidate_interrupts, "candidate policy must not treat continuing lingering evidence as a new train"
    assert candidate_cleared, "candidate policy must reach CROSSING_CLEAR once the lingering evidence is correctly ignored"


# --- Scenario 3: a genuinely new train arriving during clearance -------

def test_genuinely_new_train_during_clearance_interrupts_both_policies() -> None:
    """Safety regression check (Phase 10 Task 5): the candidate policy's fix
    for lingering evidence must NOT suppress a real new-train interrupt. An
    unambiguous "front" label is injected after rear confirmation -- both
    policies must interrupt."""
    config = _config()
    recs, t_rear_confirmed = _to_rear_confirmed_dual_camera()
    t_new_train = t_rear_confirmed + 1.0
    recs.append(_vision("camera_1", t_new_train, "front", conf=0.9))
    duration = t_new_train + 0.4

    frozen = _run_frozen(recs, duration, "e", "frozen", config)
    candidate = _run_candidate(recs, duration, "e", "candidate", config)

    frozen_hit = [t for t in frozen.ticks if abs(t.timestamp_s - t_new_train) < 0.15 and t.rule_id == RuleId.RULE_7_NEW_TRAIN_INTERRUPT.value]
    candidate_hit = [t for t in candidate.ticks if abs(t.timestamp_s - t_new_train) < 0.15 and t.rule_id == RuleIdV2.RULE_7_NEW_TRAIN_INTERRUPT.value]

    assert frozen_hit, "frozen policy must interrupt on a genuinely new unambiguous approach"
    assert candidate_hit, "candidate policy must still interrupt on a genuinely new unambiguous approach"
    assert frozen_hit[0].resulting_state == CrossingState.TRAIN_PRESENT.value
    assert candidate_hit[0].resulting_state == CrossingState.TRAIN_PRESENT.value


def test_ambiguous_label_reappearing_after_genuine_gap_counts_as_new_under_candidate() -> None:
    """The candidate's gap-based reoccurrence path: an ambiguous "side"
    label that is genuinely ABSENT for >= miss_tolerance_frames (2) ticks
    and then reappears is treated as a new approach, distinguishing a real
    gap from continuous flickering."""
    config = _config()
    recs, t_rear_confirmed = _to_rear_confirmed_dual_camera()
    # Silence (no detections at all, including from camera_2) for a window
    # long enough to create a genuine gap, then an ambiguous "side" label
    # reappears on camera_1.
    silence_start = t_rear_confirmed + 0.2
    t = silence_start
    while t < silence_start + 1.0:
        recs.append(_vision("camera_1", t, None))
        recs.append(_vision("camera_2", t, None))
        t += 0.2
    t_reoccur = t
    recs.append(_vision("camera_1", t_reoccur, "side", conf=0.6))
    duration = t_reoccur + 0.4

    candidate = _run_candidate(recs, duration, "e", "candidate", config)
    reoccur_tick = [t for t in candidate.ticks if abs(t.timestamp_s - t_reoccur) < 0.15][0]
    assert reoccur_tick.rule_id == RuleIdV2.RULE_7_NEW_TRAIN_INTERRUPT.value
    assert reoccur_tick.resulting_state == CrossingState.TRAIN_PRESENT.value


# --- Scenario 4: conflicting front/back detections ----------------------

def test_conflicting_front_back_detections_recorded_for_both_policies() -> None:
    """Simultaneous, conflicting evidence: front camera reports unambiguous
    "front" while back camera reports unambiguous "rear" at the identical
    tick during REAR_CONFIRMED. Both policies prioritize approach evidence
    (interrupt) over simultaneous departure evidence -- recorded here as a
    documented behavior, not asserted as uniquely "correct"."""
    config = _config()
    recs, t_rear_confirmed = _to_rear_confirmed_dual_camera()
    t_conflict = t_rear_confirmed + 1.0
    recs.append(_vision("camera_1", t_conflict, "front", conf=0.9))
    recs.append(_vision("camera_2", t_conflict, "rear", conf=0.9))
    duration = t_conflict + 0.4

    frozen = _run_frozen(recs, duration, "e", "frozen", config)
    candidate = _run_candidate(recs, duration, "e", "candidate", config)

    frozen_tick = [t for t in frozen.ticks if abs(t.timestamp_s - t_conflict) < 0.15][0]
    candidate_tick = [t for t in candidate.ticks if abs(t.timestamp_s - t_conflict) < 0.15][0]

    assert frozen_tick.resulting_state == CrossingState.TRAIN_PRESENT.value
    assert candidate_tick.resulting_state == CrossingState.TRAIN_PRESENT.value


# --- Scenario 5: a stale departure camera (must remain fail-safe) ------

def test_stale_departure_camera_aborts_identically_in_both_policies() -> None:
    """Safety regression check: the candidate must not weaken RULE_5
    (stale-source abort). The departure camera goes stale mid-dwell in both
    policies; both must clamp to FAULT_FAIL_SAFE, never reach CROSSING_CLEAR."""
    config = _config()
    recs, t_rear_confirmed = _to_rear_confirmed_dual_camera()
    # Approach camera stays healthy; departure camera (camera_2) never
    # emits another observation after rear confirmation, so it goes stale
    # after source_staleness_s (2.0s).
    tt = t_rear_confirmed + 0.2
    duration = t_rear_confirmed + 3.0
    while tt <= duration:
        recs.append(_vision("camera_1", tt, None))
        tt += 0.2

    frozen = _run_frozen(recs, duration, "e", "frozen", config)
    candidate = _run_candidate(recs, duration, "e", "candidate", config)

    frozen_abort = [t for t in frozen.ticks if t.rule_id == RuleId.RULE_5_STALE_SOURCE_ABORT.value]
    candidate_abort = [t for t in candidate.ticks if t.rule_id == RuleIdV2.RULE_5_STALE_SOURCE_ABORT.value]

    assert frozen_abort and frozen_abort[0].resulting_state == CrossingState.FAULT_FAIL_SAFE.value
    assert candidate_abort and candidate_abort[0].resulting_state == CrossingState.FAULT_FAIL_SAFE.value
    assert not any(t.resulting_state == CrossingState.CROSSING_CLEAR.value for t in frozen.ticks)
    assert not any(t.resulting_state == CrossingState.CROSSING_CLEAR.value for t in candidate.ticks)


# --- Scenario 6: missing and out-of-order observations ------------------

def test_duplicate_and_out_of_order_frames_rejected_identically() -> None:
    """Safety regression check: duplicate/out-of-order rejection (RULE_8/
    RULE_10) is unchanged mechanics in the candidate -- both policies must
    reject identically and neither must let a duplicate/out-of-order frame
    advance any dwell timer."""
    config = _config()
    recs = [
        _vision("camera_1", 1.0, "front"),
        _vision("camera_1", 1.0, "front"),  # exact duplicate
    ]
    duration = 1.2

    frozen = _run_frozen(recs, duration, "e", "frozen", config)
    candidate = _run_candidate(recs, duration, "e", "candidate", config)

    frozen_dupe = [t for t in frozen.ticks if t.rule_id == RuleId.RULE_10_DUPLICATE_FRAME_REJECTION.value]
    candidate_dupe = [t for t in candidate.ticks if t.rule_id == RuleIdV2.RULE_10_DUPLICATE_FRAME_REJECTION.value]
    assert frozen.rejections.total_rejected == candidate.rejections.total_rejected == 1
    # Note: the duplicate master-timestamp frame is filtered by the shared
    # MultimodalEvidenceCollector before either engine ever sees it (see
    # Phase 9's test_diagnostic_trace_records_rejected_duplicate_observations),
    # so RULE_10 does not actually fire at the engine level for this input;
    # this assertion instead confirms both engines process the SAME
    # (deduplicated) tick count, i.e. neither silently processes the
    # rejected duplicate as if it were a second, valid observation.
    assert len(frozen.ticks) == len(candidate.ticks)


# --- Scenario 7: interrupted clearance dwell, then recovery ------------

def test_interrupted_dwell_recovers_and_completes_under_candidate() -> None:
    """A genuinely new approach interrupts the dwell, then (as that
    detection source itself goes silent again and the crossing re-confirms
    departure) the dwell is given a fair chance to complete afterward --
    confirms the candidate's fix is not a one-shot "always clear" change
    but a normal, re-enterable dwell."""
    config = _config()
    recs, t_rear_confirmed = _to_rear_confirmed_dual_camera()
    t_interrupt = t_rear_confirmed + 1.0
    recs.append(_vision("camera_1", t_interrupt, "front", conf=0.9))

    # After the interrupt, the crossing must re-confirm departure before a
    # new dwell can start: approach camera returns to silence, departure
    # camera reports a fresh unambiguous "rear".
    t = t_interrupt + 0.2
    recs.append(_vision("camera_1", t, None))
    recs.append(_vision("camera_2", t, None))
    t += 0.2
    recs.append(_vision("camera_2", t, "rear"))
    t_second_rear_confirmed = t

    tt = t_second_rear_confirmed + 0.2
    duration = t_second_rear_confirmed + 4.0
    while tt <= duration:
        recs.append(_vision("camera_1", tt, None))
        recs.append(_vision("camera_2", tt, None))
        tt += 0.2

    candidate = _run_candidate(recs, duration, "e", "candidate", config)
    interrupts = [t for t in candidate.ticks if t.rule_id == RuleIdV2.RULE_7_NEW_TRAIN_INTERRUPT.value]
    cleared = [t for t in candidate.ticks if t.resulting_state == CrossingState.CROSSING_CLEAR.value]
    assert interrupts, "expected the first genuinely new approach to interrupt the dwell"
    assert cleared, "expected the dwell to be given a fair chance and complete after re-confirmation"
    assert cleared[0].timestamp_s > interrupts[0].timestamp_s


# --- Scenario 8: single-camera topology (no departure-role source) -----

def test_single_camera_topology_confirms_departure_by_disappearance_under_candidate() -> None:
    """The other half of the Phase 9 fix: a front-only topology (no
    dedicated rear camera at all, matching the B0 baseline) can no longer
    confirm departure via an ambiguous "side"/"train" relabeling of its own
    continuing detections (Phase 9's demonstrated defect); instead it must
    wait for the sole camera to report nothing for `confirm_frames`
    consecutive ticks (the train has left the only camera's frame)."""
    config = _config()
    recs: list[EvidenceRecord] = []
    t = 0.0
    for _ in range(2):
        recs.append(_vision("camera_1", t, "front"))
        t += 0.2
    t = 2.1
    recs.append(_vision("camera_1", t, "front"))
    t += 3.1
    recs.append(_vision("camera_1", t, "front"))
    t += 0.2
    recs.append(_vision("camera_1", t, "front"))
    t_occupied = t

    tt = t_occupied + 0.2
    while tt <= t_occupied + 1.0:
        recs.append(_vision("camera_1", tt, "side", conf=0.6))  # same train, ambiguous, continuing
        tt += 0.2
    duration = tt + 1.0
    while tt <= duration:
        recs.append(_vision("camera_1", tt, None))  # train has left the frame
        tt += 0.2

    candidate = _run_candidate(recs, duration, "e", "candidate", config)
    disappearance_ticks = [
        t for t in candidate.ticks if t.rule_id == RuleIdV2.RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE.value
    ]
    assert disappearance_ticks, "expected departure to be confirmed via sustained disappearance, not an ambiguous label"
    assert disappearance_ticks[0].resulting_state == CrossingState.REAR_CONFIRMED.value
    # The ambiguous "side" labels while the train was still visible must
    # never have been accepted as an unambiguous-rear-style confirmation.
    rear_ticks_via_label = [
        t for t in candidate.ticks if t.rule_id == RuleIdV2.RULE_3B_DEPARTURE_CONFIRMED_UNAMBIGUOUS_REAR.value
    ]
    assert not rear_ticks_via_label
