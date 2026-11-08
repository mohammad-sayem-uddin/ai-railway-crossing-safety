"""Phase 10.1, Task 5: dedicated safety re-verification tests not already
covered by Phase 9/10's suites -- missing/invalid synchronization and gate
reopening conditions, re-checked for BOTH the frozen and candidate engines.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from railway_detection.experiments.diagnostic_trace import run_with_diagnostics
from railway_detection.experiments.frozen_config import TimingIntegrityError
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.decision_engine_v2_candidate import MultimodalDecisionEngineV2Candidate
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.fusion.rules import CrossingState
from railway_detection.fusion.rules_v2_candidate import (
    has_unambiguous_approach_label,
    has_unambiguous_departure_label,
)


@dataclass
class _CrossCameraSync:
    allow_unverified_zero_offset: bool = False


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
    cross_camera_sync: _CrossCameraSync = None

    def __post_init__(self):
        if self.cross_camera_sync is None:
            self.cross_camera_sync = _CrossCameraSync()


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


def _config_allowing_unverified_fusion() -> _Config:
    """For tests that exercise GATE mechanics with synthetic dual-camera
    evidence (already on a shared synthetic clock, no real offset to
    calibrate) rather than the sync-safety gate itself."""
    return _Config(
        timing=_Timing(cross_camera_sync=_CrossCameraSync(allow_unverified_zero_offset=True)),
        vision=_VisionCfg(), audio=_AudioCfg(),
    )


def _vision(source_id: str, t: float, label: str | None, conf: float = 0.8) -> EvidenceRecord:
    dets = (Detection(label=label, confidence=conf),) if label else ()
    return EvidenceRecord(timestamp_s=t, source_id=source_id, modality=Modality.VISION, available=True, detections=dets)


# --- Missing/invalid synchronization -------------------------------------

@pytest.mark.parametrize(
    "engine_factory,approach_fn,departure_fn",
    [
        (MultimodalDecisionEngine, None, None),
        (MultimodalDecisionEngineV2Candidate, has_unambiguous_approach_label, has_unambiguous_departure_label),
    ],
)
def test_unverified_cross_camera_fusion_blocked_for_both_policies(engine_factory, approach_fn, departure_fn) -> None:
    """Two vision sources, no sync_aligner, and a config that does not allow
    unverified zero-offset fusion (matching the real frozen config) must
    raise TimingIntegrityError before any decision is made -- for BOTH
    policies, since this gate lives in the shared replay facility, not in
    either engine. Found during Phase 10.1 to be a real, previously-unchecked
    gap: `run_with_diagnostics` built its collector directly and had no
    equivalent to `LayerBEventProcessor.build_multimodal_frames`'s R04 check
    at all; fixed in `experiments/diagnostic_trace.py` as part of this phase."""
    config = _config()
    recs = [_vision("camera_1", 0.0, "front"), _vision("camera_2", 0.0, "rear")]
    kwargs = dict(
        vision_records=recs, audio_records=[], duration_s=1.0, stride_s=0.2,
        event_id="e", condition="c", config=config, sync_aligner=None,
        engine_factory=engine_factory,
    )
    if approach_fn is not None:
        kwargs["approach_fn"] = approach_fn
        kwargs["departure_fn"] = departure_fn
    with pytest.raises(TimingIntegrityError):
        run_with_diagnostics(**kwargs)


def test_single_camera_evidence_never_blocked_by_sync_gate() -> None:
    """A single-camera topology (no cross-camera fusion at all) must never
    trigger the sync gate, regardless of `allow_unverified_zero_offset`."""
    config = _config()
    recs = [_vision("camera_1", 0.0, "front"), _vision("camera_1", 0.2, "front")]
    result = run_with_diagnostics(
        vision_records=recs, audio_records=[], duration_s=0.4, stride_s=0.2,
        event_id="e", condition="c", config=config, sync_aligner=None,
        engine_factory=MultimodalDecisionEngineV2Candidate,
        approach_fn=has_unambiguous_approach_label, departure_fn=has_unambiguous_departure_label,
    )
    assert result.ticks  # completed without raising


# --- Gate reopening conditions --------------------------------------------

def _to_clear_dual_camera():
    recs = []
    t = 0.0
    for _ in range(2):
        recs.append(_vision("camera_1", t, "front")); t += 0.2
    t = 2.1
    recs.append(_vision("camera_1", t, "front"))
    t += 3.1
    recs.append(_vision("camera_1", t, "front"))
    t += 0.2
    recs.append(_vision("camera_1", t, "front"))
    recs.append(_vision("camera_2", t, "front"))
    t += 0.2
    recs.append(_vision("camera_2", t, "rear"))
    t += 0.2
    recs.append(_vision("camera_2", t, "rear"))
    t_rear_confirmed = t
    tt = t_rear_confirmed + 0.2
    while tt <= t_rear_confirmed + 3.8:
        recs.append(_vision("camera_1", tt, None))
        recs.append(_vision("camera_2", tt, None))
        tt += 0.2
    return recs, tt


@pytest.mark.parametrize(
    "engine_factory,approach_fn,departure_fn",
    [
        (MultimodalDecisionEngine, None, None),
        (MultimodalDecisionEngineV2Candidate, has_unambiguous_approach_label, has_unambiguous_departure_label),
    ],
)
def test_gate_reopens_to_idle_after_clean_clearance(engine_factory, approach_fn, departure_fn) -> None:
    """GATE_OPENING -> IDLE must occur, for both policies, once clearance is
    verified and gate_opening_s elapses with no further approach evidence --
    confirms the candidate did not accidentally block normal gate reopening."""
    config = _config_allowing_unverified_fusion()
    recs, t_end = _to_clear_dual_camera()
    tt = t_end
    duration = t_end + 3.4
    while tt <= duration:
        recs.append(_vision("camera_1", tt, None))
        recs.append(_vision("camera_2", tt, None))
        tt += 0.2

    kwargs = dict(
        vision_records=recs, audio_records=[], duration_s=duration, stride_s=0.2,
        event_id="e", condition="c", config=config, engine_factory=engine_factory,
    )
    if approach_fn is not None:
        kwargs["approach_fn"] = approach_fn
        kwargs["departure_fn"] = departure_fn
    result = run_with_diagnostics(**kwargs)
    idle_after_clear = [
        t for t in result.ticks
        if t.resulting_state == CrossingState.IDLE.value and t.previous_state == CrossingState.GATE_OPENING.value
    ]
    assert idle_after_clear, "expected GATE_OPENING -> IDLE once gate_opening_s elapses after a clean clearance"


@pytest.mark.parametrize(
    "engine_factory,approach_fn,departure_fn",
    [
        (MultimodalDecisionEngine, None, None),
        (MultimodalDecisionEngineV2Candidate, has_unambiguous_approach_label, has_unambiguous_departure_label),
    ],
)
def test_gate_reopening_aborted_by_new_approach(engine_factory, approach_fn, departure_fn) -> None:
    """A genuine new approach during GATE_OPENING must abort the reopening
    back to GATE_CLOSING, for both policies -- the gate must never finish
    opening while a new train is approaching."""
    config = _config_allowing_unverified_fusion()
    recs, t_end = _to_clear_dual_camera()
    # Clean dwell completes; a new unambiguous "front" arrives right as
    # the gate starts opening.
    t_new = t_end + 0.4
    recs.append(_vision("camera_1", t_new, "front", conf=0.9))
    duration = t_new + 0.4

    kwargs = dict(
        vision_records=recs, audio_records=[], duration_s=duration, stride_s=0.2,
        event_id="e", condition="c", config=config, engine_factory=engine_factory,
    )
    if approach_fn is not None:
        kwargs["approach_fn"] = approach_fn
        kwargs["departure_fn"] = departure_fn
    result = run_with_diagnostics(**kwargs)
    abort_ticks = [
        t for t in result.ticks
        if t.previous_state == CrossingState.GATE_OPENING.value and t.resulting_state == CrossingState.GATE_CLOSING.value
    ]
    assert abort_ticks, "expected GATE_OPENING to abort to GATE_CLOSING on a new approach"
