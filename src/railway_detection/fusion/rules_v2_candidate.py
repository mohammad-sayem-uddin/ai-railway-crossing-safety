"""Phase 10 candidate policy (v2.0.0-candidate): explicit detection-class
semantics, explicit camera-role semantics, and continuity-aware new-train
detection.

This module does NOT modify `fusion/rules.py` or `configs/decision_policy_v1.yaml`
in any way -- both remain the frozen, authorized policy. This is a separate,
versioned candidate under forensic/research review only (Phase 10); nothing
here is wired into the default/frozen execution path, and nothing here is
authorized for deployment.

Background (see docs/PHASE9_CLEARANCE_DIVERGENCE_REPORT.md): the frozen
policy's `APPROACH_LABELS`/`DEPARTURE_LABELS` both contain "side" and "train",
and neither `has_qualified_approach` nor `has_qualified_departure` inspects
`record.source_id`. This was demonstrated, directly from Phase 8's real
cached evidence, to cause a near-continuous `RULE_7_NEW_TRAIN_INTERRUPT`
cycle against the SAME departing train's own lingering "side" detections,
preventing the clearance dwell from ever completing in all 11 real events.

--- Detection-class semantics (explicit) ---

The underlying vision model emits four classes: "front", "rear", "side",
"train". Only "front" and "rear" encode orientation information specific
enough to support a directional safety inference on their own: a "front"
detection asserts the train's front face is toward the camera; a "rear"
detection asserts its rear is toward the camera. "side" and "train" do NOT
encode which way the train is facing or moving -- "side" literally means
"the train's lateral profile is in frame", which is equally consistent with
an approaching, departing, or simply passing train, and "train" is the
model's generic/unclassified-orientation fallback. Per the Phase 10 brief's
explicit constraint, this candidate policy does NOT infer direction from
"side" (or "train") alone, in either direction.

--- Camera-role semantics (explicit) ---

This candidate scopes DEPARTURE CONFIRMATION to the camera registered in the
departure role (source id containing "2", "back", or "rear" -- the SAME
heuristic already present in the frozen engine's RULE_5/RULE_6 departure-
source checks in `decision_engine.py`; this is not a new assumption
introduced here). This is justified by the dual-camera rig's documented
physical geometry (see docs/R04_CALIBRATION_VALIDATION_REPORT.md and the
Phase 8 report): the "back" camera is mounted to view the departure side of
the crossing, the "front" camera the approach side. This is a claim about
WHICH SENSOR is authoritative for a given safety determination, not a claim
that camera role alone proves train direction: an unambiguous "front" label
from the departure camera, or a "rear" label from the approach camera, is
still valid evidence under this module's label-level functions (see
`has_unambiguous_approach_label`/`has_unambiguous_departure_label` below,
which are source-agnostic); role-scoping is applied only at the point where
the engine decides whether a given detection is ELIGIBLE to satisfy positive
departure confirmation specifically, per Phase 10 Task 2's instruction not
to treat role as sufficient evidence of direction by itself.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from railway_detection.fusion.collector import MultimodalFrame

CANDIDATE_POLICY_VERSION = "2.0.0-candidate"

UNAMBIGUOUS_APPROACH_LABELS = frozenset({"front"})
UNAMBIGUOUS_DEPARTURE_LABELS = frozenset({"rear"})
AMBIGUOUS_ORIENTATION_LABELS = frozenset({"side", "train"})
ALL_QUALIFYING_VISION_LABELS = (
    UNAMBIGUOUS_APPROACH_LABELS | UNAMBIGUOUS_DEPARTURE_LABELS | AMBIGUOUS_ORIENTATION_LABELS
)
# Unchanged from the frozen policy: audio orientation is not at issue in the
# Phase 9 finding, so audio semantics are reused verbatim, not redefined.
AUDIO_TRAIN_LABELS = frozenset({"train", "horn", "rail", "train_horn"})


class RuleIdV2(StrEnum):
    """Candidate rule identifiers. IDs shared with the frozen `RuleId` enum
    (fusion/rules.py) denote UNCHANGED mechanics reused verbatim (out-of-order
    and duplicate-frame rejection, fail-safe clamps, sensor recovery, degraded-
    source hold, stale-source abort, audio-support-only, dwell completion).
    IDs with a V2-specific suffix denote genuinely new candidate-policy
    conditions that have no equivalent in the frozen policy."""

    RULE_1_APPROACH_TRIGGER = "RULE_1_APPROACH_TRIGGER"
    RULE_2_AUDIO_SUPPORT_ONLY = "RULE_2_AUDIO_SUPPORT_ONLY"
    RULE_3_POSITIVE_CLEARANCE = "RULE_3_POSITIVE_CLEARANCE"
    RULE_3B_DEPARTURE_CONFIRMED_UNAMBIGUOUS_REAR = "RULE_3B_DEPARTURE_CONFIRMED_UNAMBIGUOUS_REAR"
    RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE = "RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE"
    RULE_4_FAIL_SAFE_CLAMP = "RULE_4_FAIL_SAFE_CLAMP"
    RULE_5_STALE_SOURCE_ABORT = "RULE_5_STALE_SOURCE_ABORT"
    RULE_6_DEGRADED_SOURCE_HOLD = "RULE_6_DEGRADED_SOURCE_HOLD"
    RULE_7_NEW_TRAIN_INTERRUPT = "RULE_7_NEW_TRAIN_INTERRUPT"
    RULE_8_OUT_OF_ORDER_REJECTION = "RULE_8_OUT_OF_ORDER_REJECTION"
    RULE_9_SENSOR_RECOVERY = "RULE_9_SENSOR_RECOVERY"
    RULE_10_DUPLICATE_FRAME_REJECTION = "RULE_10_DUPLICATE_FRAME_REJECTION"


def is_departure_role_source(source_id: str) -> bool:
    """Same heuristic as the frozen engine's existing departure-source checks
    (decision_engine.py `departure_sources`/`dep_sources` computations).
    Not a new assumption; reused verbatim for consistency and auditability."""
    return "2" in source_id or "back" in source_id or "rear" in source_id


def is_approach_role_source(source_id: str) -> bool:
    return not is_departure_role_source(source_id)


def has_unambiguous_approach_label(frame: MultimodalFrame, threshold: float) -> bool:
    """True if ANY available vision source (any role) reports the unambiguous
    "front" label above threshold. Source-agnostic by design: an unambiguous
    orientation label is meaningful evidence regardless of which camera
    reports it (see module docstring's camera-role section)."""
    for record in frame.vision_records:
        if not record.available:
            continue
        for det in record.detections:
            if det.label.lower() in UNAMBIGUOUS_APPROACH_LABELS and det.confidence >= threshold:
                return True
    return False


def has_unambiguous_departure_label_from(
    frame: MultimodalFrame, eligible_source_ids: set[str], threshold: float
) -> bool:
    """True if one of `eligible_source_ids` reports the unambiguous "rear"
    label above threshold. Role-scoped: callers pass the departure-role
    source set so only the camera facing the departure side can satisfy
    positive departure confirmation via an unambiguous label."""
    for record in frame.vision_records:
        if not record.available or record.source_id not in eligible_source_ids:
            continue
        for det in record.detections:
            if det.label.lower() in UNAMBIGUOUS_DEPARTURE_LABELS and det.confidence >= threshold:
                return True
    return False


def has_unambiguous_departure_label(frame: MultimodalFrame, threshold: float) -> bool:
    """Source-agnostic convenience wrapper over `has_unambiguous_departure_label_from`
    for diagnostic/annotation display only (matches the 2-arg
    `(frame, threshold)` signature `experiments.diagnostic_trace.run_with_diagnostics`
    expects for its independently-recomputed `departure_detected` field). The
    engine itself always uses the role-scoped version for actual departure
    confirmation -- this wrapper is never used for a safety decision."""
    for record in frame.vision_records:
        if not record.available:
            continue
        for det in record.detections:
            if det.label.lower() in UNAMBIGUOUS_DEPARTURE_LABELS and det.confidence >= threshold:
                return True
    return False


def has_any_qualifying_detection(frame: MultimodalFrame, threshold: float) -> bool:
    """Broad "is a train visibly present" check across all four classes and
    all sources -- used only for the non-safety-critical early occupancy
    transitions (TRAIN_PRESENT -> CROSSING_OCCUPIED) where leniency is safe
    (it only ever keeps the gate closed), never for departure confirmation
    or new-train interruption, which require the stricter functions above
    and `has_genuinely_new_approach_evidence` below."""
    for record in frame.vision_records:
        if not record.available:
            continue
        for det in record.detections:
            if det.label.lower() in ALL_QUALIFYING_VISION_LABELS and det.confidence >= threshold:
                return True
    return False


def detection_sources_this_tick(frame: MultimodalFrame, threshold: float) -> set[str]:
    """Source IDs that reported at least one qualifying (any of the 4
    classes) detection above threshold this tick. Used by the engine to
    update its per-source continuity/gap tracking."""
    sources: set[str] = set()
    for record in frame.vision_records:
        if not record.available:
            continue
        for det in record.detections:
            if det.label.lower() in ALL_QUALIFYING_VISION_LABELS and det.confidence >= threshold:
                sources.add(record.source_id)
                break
    return sources


def has_genuinely_new_approach_evidence(
    frame: MultimodalFrame,
    ticks_since_last_detection: dict[str, int],
    threshold: float,
    gap_frames: int,
) -> bool:
    """The central candidate-policy fix: distinguishes a genuinely new train
    from continued observation of the same departing/passing train.

    - An unambiguous "front" label ALWAYS counts, from any source, regardless
      of continuity -- it is specific enough orientation evidence on its own
      (see module docstring).
    - An ambiguous "side"/"train" label counts ONLY if that source has gone
      at least `gap_frames` consecutive ticks with no qualifying detection
      immediately before this one, i.e. it is REAPPEARING after a genuine
      silence, not continuing an unbroken detection stream. `gap_frames`
      defaults to the sentinel used for a source with no detection history
      at all (see the engine's gap-state initialization), so the very first
      detection ever seen from a source always counts as "new" under this
      same rule.

    Used ONLY for RULE_7 (new-train interrupt, scoped to REAR_CONFIRMED/
    CROSSING_CLEAR/GATE_OPENING). It is deliberately NOT reused for RULE_1's
    initial approach confirmation: RULE_1 requires `confirm_frames`
    CONSECUTIVE qualifying detections to accumulate (the opposite continuity
    requirement from RULE_7), so the engine uses the broader
    `has_any_qualifying_detection` for that transition instead -- confirmed
    necessary by a real-event replay regression (event_005 got stuck
    oscillating IDLE/TRAIN_APPROACHING when this function was first, wrongly,
    reused there too, since a second consecutive ambiguous detection has
    gap=0 and would never itself count as "new").
    """
    for record in frame.vision_records:
        if not record.available:
            continue
        for det in record.detections:
            if det.confidence < threshold:
                continue
            label = det.label.lower()
            if label in UNAMBIGUOUS_APPROACH_LABELS:
                return True
            if label in AMBIGUOUS_ORIENTATION_LABELS:
                gap = ticks_since_last_detection.get(record.source_id, gap_frames)
                if gap >= gap_frames:
                    return True
    return False
