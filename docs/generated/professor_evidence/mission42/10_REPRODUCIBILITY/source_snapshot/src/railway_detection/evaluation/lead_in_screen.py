"""Missed-train lead-in feasibility screen (Mission 5A, confirmed decision RD-021).

A "missed train" means the barrier was not blocking when the train reached the danger
zone (T1).  That is only attributable to the system if the recording gave the frozen
decision policy *enough physical time* to detect, warn, and close the arm before T1.
With the frozen timings the arm cannot be blocked before roughly 3.6 s after the first
train evidence, so an event whose available lead-in is shorter is *not evaluable* for
missed-train reporting -- it is an insufficient warning opportunity, not a system failure.

This module is pure and synthetic-friendly: it reads no ground-truth file, no media and no
configuration.  The minimum block latency is an explicit *input* with a stated provenance;
:func:`derive_min_block_latency_s` can derive it by replaying a synthetic constant-evidence
trace through the real decision engine and gate model.

The roughly 3.6 s that derivation yields is **not** an approved safety threshold.  It is only the
value obtained by replaying a synthetic constant front-camera detection through the frozen
configuration at that configuration's tick (0.2 s), and it moves with the tick.

Assumptions (see docs/generated/mission_5a/MISSED_TRAIN_FEASIBILITY_SCREEN_20261101_M5A.md):

* Evidence can first be acted on at ``approach_start``: the observed first-visible time T0
  when it is an observable boundary, or the replay start (0.0 s) when T0 is left-censored
  (the train was already present in the first frame).
* ``available_lead_in_s = T1 - approach_start``; the event passes the screen iff
  ``available_lead_in_s >= min_block_latency_s``.
* No timestamp is fabricated: an unknown or uncertain T0 makes the event ``unverifiable``.
* Timestamps and the available lead-in are compared on the one-microsecond grid (DEC-C05).

Mission 5B (DEC-C03): the physical rule above stays the primary outcome.  Every result also
carries ``m3_design_literal_evaluable``, the verdict of the literal design rule M3 ("T1 is
observable and (T0 is observable or T1 >= the minimum latency)"), so both can be reported side by
side.  The two differ for an observable T0 with too little lead-in (physical: not evaluable;
literal: evaluable) and for an unknown T0 with T1 >= latency (physical: unverifiable; literal:
evaluable, silently assuming the train was visible from t = 0).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from railway_detection.evaluation.timebase import normalize_timestamp

SCREEN_PASSED = "passed"
SCREEN_INSUFFICIENT_LEAD_IN = "insufficient_lead_in"
SCREEN_UNVERIFIABLE = "lead_in_unverifiable"
SCREEN_T1_MISSING = "t1_missing"
SCREEN_NOT_APPLIED = "not_screened"

#: Outcomes that exclude an event from the missed-train denominator.
SCREEN_EXCLUDING_OUTCOMES = frozenset(
    {SCREEN_INSUFFICIENT_LEAD_IN, SCREEN_UNVERIFIABLE, SCREEN_T1_MISSING}
)


@dataclass(frozen=True)
class LeadInScreenResult:
    """Outcome of the lead-in screen for one event; carries its own provenance."""

    outcome: str
    evaluable: bool
    reason: str | None
    entry_time_s: float | None
    approach_start_s: float | None
    approach_start_basis: str  # "observed_first_visible" | "replay_start_left_censored" | "unknown"
    available_lead_in_s: float | None
    min_block_latency_s: float
    min_block_latency_source: str
    # Companion verdict of the literal design M3 rule; never replaces ``evaluable`` (DEC-C03).
    m3_design_literal_evaluable: bool | None = None


def _require_finite_nonnegative(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return float(value)


def screen_missed_train_lead_in(
    entry_time_s: float | None,
    *,
    first_visible_time_s: float | None,
    first_visible_left_censored: bool,
    min_block_latency_s: float,
    min_block_latency_source: str,
) -> LeadInScreenResult:
    """Decide whether an event gave the policy enough lead-in to be judged on missed-train.

    ``first_visible_time_s`` is the *observable* T0 value, or ``None``.  When it is ``None``,
    ``first_visible_left_censored=True`` declares that the train was already present at the
    replay start; ``False`` means T0 is unknown/uncertain and the event is unverifiable.
    """
    if (
        isinstance(min_block_latency_s, bool)
        or not isinstance(min_block_latency_s, (int, float))
        or not math.isfinite(min_block_latency_s)
        or min_block_latency_s <= 0.0
    ):
        raise ValueError("min_block_latency_s must be a finite positive number")
    if not isinstance(min_block_latency_source, str) or not min_block_latency_source.strip():
        raise ValueError("min_block_latency_source (provenance) is required")
    latency = float(min_block_latency_s)

    def result(outcome, evaluable, reason, entry, start, basis, available):
        # Literal design M3: T1 observable and (T0 observable or T1 >= latency).
        literal = entry is not None and (
            basis == "observed_first_visible"
            or normalize_timestamp(entry) >= normalize_timestamp(latency)
        )
        return LeadInScreenResult(
            outcome=outcome,
            evaluable=evaluable,
            reason=reason,
            entry_time_s=entry,
            approach_start_s=start,
            approach_start_basis=basis,
            available_lead_in_s=available,
            min_block_latency_s=latency,
            min_block_latency_source=min_block_latency_source,
            m3_design_literal_evaluable=literal,
        )

    if entry_time_s is None:
        return result(SCREEN_T1_MISSING, False, SCREEN_T1_MISSING, None, None, "unknown", None)
    entry = normalize_timestamp(_require_finite_nonnegative("entry_time_s", entry_time_s))

    if first_visible_time_s is not None:
        start = normalize_timestamp(
            _require_finite_nonnegative("first_visible_time_s", first_visible_time_s)
        )
        basis = "observed_first_visible"
    elif first_visible_left_censored:
        start = 0.0
        basis = "replay_start_left_censored"
    else:
        return result(SCREEN_UNVERIFIABLE, False, SCREEN_UNVERIFIABLE, entry, None, "unknown", None)

    if start > entry:
        raise ValueError("first-visible time cannot be after danger-zone entry (T1)")
    available = normalize_timestamp(entry - start)
    if available >= normalize_timestamp(latency):
        return result(SCREEN_PASSED, True, None, entry, start, basis, available)
    return result(
        SCREEN_INSUFFICIENT_LEAD_IN,
        False,
        SCREEN_INSUFFICIENT_LEAD_IN,
        entry,
        start,
        basis,
        available,
    )


SYNTHETIC_DETECTION_CONFIDENCE = 0.9


def derive_min_block_latency_s(
    *,
    tick_s: float | None = None,
    horizon_s: float = 30.0,
    runner=None,
    config=None,
) -> float:
    """Derive the minimum block latency from a *synthetic* constant-evidence replay.

    A single front-camera source reports an unambiguous ``front`` detection on every tick from
    t = 0.  The returned value is the timestamp of the first retained step with
    ``is_passage_blocked=True``.  No ground truth, media, checkpoint or cache is involved.
    Raises ``ValueError`` if the barrier never blocks within ``horizon_s``.

    Pass the :class:`~railway_detection.experiments.frozen_config.FrozenExperimentConfig` as
    ``config`` so the engine, the gate model and the tick all come from it (Mission 5B, DEC-A01);
    ``tick_s`` then defaults to ``config.timing.tick_s`` and may not contradict it.  Without a
    ``config`` or ``runner`` the engine's constructor defaults are used, which is only appropriate
    for stand-alone synthetic checks, never for a value that is recorded as provenance.
    """
    if config is not None and runner is not None:
        raise ValueError("pass either config or runner, not both")
    if config is not None:
        config_tick = float(config.timing.tick_s)
        if tick_s is not None and normalize_timestamp(tick_s) != normalize_timestamp(config_tick):
            raise ValueError("tick_s contradicts config.timing.tick_s")
        tick_s = config_tick
    elif tick_s is None:
        tick_s = 0.2
    tick = _require_finite_nonnegative("tick_s", tick_s)
    horizon = _require_finite_nonnegative("horizon_s", horizon_s)
    if tick <= 0.0 or horizon <= tick:
        raise ValueError("tick_s must be positive and horizon_s must exceed it")

    # Imported lazily so the pure screen above has no simulation dependency.
    from railway_detection.fusion.collector import MultimodalFrame
    from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
    from railway_detection.simulation.runner import EventSimulationRunner

    frames = []
    for index in range(int(round(horizon / tick))):
        timestamp = normalize_timestamp(index * tick)
        record = EvidenceRecord(
            timestamp_s=timestamp,
            source_id="camera_1",
            modality=Modality.VISION,
            available=True,
            detections=(Detection(label="front", confidence=SYNTHETIC_DETECTION_CONFIDENCE),),
            metadata={"frame_index": index, "synthetic": True},
        )
        frames.append(
            MultimodalFrame(
                master_timestamp_s=timestamp,
                vision_records=(record,),
                source_availability={"camera_1": True},
                active_sources=("camera_1",),
            )
        )
    if runner is None:
        runner = EventSimulationRunner(config=config)
    sim = runner.run_frames(
        frames, event_id="train_events/synthetic_min_block_latency", scenario_name="synthetic"
    )
    first_blocked = next((s.timestamp_s for s in sim.steps if s.is_passage_blocked), None)
    if first_blocked is None:
        raise ValueError("barrier never blocked within the synthetic horizon")
    return float(first_blocked)


def derive_min_block_latency_with_provenance(config) -> tuple[float, str]:
    """Derive the latency from ``config`` and return it with a provenance string.

    The string states what the number is -- a synthetic replay of the frozen configuration at its
    own tick -- and carries the configuration's canonical hash, so a recorded value can be traced
    to the exact configuration that produced it.  It does not describe the value as a safety
    threshold, because it is not one.  ``config`` is required: nothing is read from defaults.
    """
    latency = derive_min_block_latency_s(config=config)
    tick = float(config.timing.tick_s)
    source = (
        "synthetic_replay_of_frozen_configuration:constant_front_detection"
        f"_conf{SYNTHETIC_DETECTION_CONFIDENCE}:tick_s={tick}"
        f":config_canonical_sha256={config.config_hash}"
    )
    return latency, source
