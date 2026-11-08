"""Safety policy rules, crossing states, and multimodal decision invariants."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from railway_detection.fusion.collector import MultimodalFrame


class CrossingState(StrEnum):
    """Discrete operational states of the level-crossing safety controller."""

    IDLE = "IDLE"
    TRAIN_APPROACHING = "TRAIN_APPROACHING"
    WARNING = "WARNING"
    GATE_CLOSING = "GATE_CLOSING"
    TRAIN_PRESENT = "TRAIN_PRESENT"
    CROSSING_OCCUPIED = "CROSSING_OCCUPIED"
    TRAIN_DEPARTING = "TRAIN_DEPARTING"
    REAR_CONFIRMED = "REAR_CONFIRMED"
    CROSSING_CLEAR = "CROSSING_CLEAR"
    GATE_OPENING = "GATE_OPENING"
    FAULT_FAIL_SAFE = "FAULT_FAIL_SAFE"


class GateState(StrEnum):
    """Physical barrier arm states."""

    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    OPENING = "OPENING"


class RuleId(StrEnum):
    """Identifies deterministic safety rules commanding state transitions."""

    RULE_1_APPROACH_TRIGGER = "RULE_1_APPROACH_TRIGGER"
    RULE_2_AUDIO_SUPPORT_ONLY = "RULE_2_AUDIO_SUPPORT_ONLY"
    RULE_3_POSITIVE_CLEARANCE = "RULE_3_POSITIVE_CLEARANCE"
    RULE_4_FAIL_SAFE_CLAMP = "RULE_4_FAIL_SAFE_CLAMP"
    RULE_5_STALE_SOURCE_ABORT = "RULE_5_STALE_SOURCE_ABORT"
    RULE_6_DEGRADED_SOURCE_HOLD = "RULE_6_DEGRADED_SOURCE_HOLD"
    RULE_7_NEW_TRAIN_INTERRUPT = "RULE_7_NEW_TRAIN_INTERRUPT"
    RULE_8_OUT_OF_ORDER_REJECTION = "RULE_8_OUT_OF_ORDER_REJECTION"
    RULE_9_SENSOR_RECOVERY = "RULE_9_SENSOR_RECOVERY"
    # RULE_10 is an ingestion-safety mechanism, not a dwell/decision rule from
    # configs/decision_policy_v1.yaml's frozen rule set (RULE_1-9). It is added
    # here, in code only, to give duplicate-frame rejection its own auditable
    # identity distinct from RULE_8 (disordered timestamp). It does not alter,
    # and is never referenced by, the frozen policy document or its canonical
    # hash. See docs/R04_IMPLEMENTATION_AND_UNBLOCK_REPORT.md Task 2.
    RULE_10_DUPLICATE_FRAME_REJECTION = "RULE_10_DUPLICATE_FRAME_REJECTION"


APPROACH_LABELS = frozenset({"front", "side", "train"})
DEPARTURE_LABELS = frozenset({"rear", "side", "train"})
AUDIO_TRAIN_LABELS = frozenset({"train", "horn", "rail", "train_horn"})


def has_qualified_approach(frame: MultimodalFrame, threshold: float = 0.35) -> bool:
    """Checks whether any available vision source reports a qualified approach detection."""
    for record in frame.vision_records:
        if not record.available:
            continue
        for det in record.detections:
            if det.label.lower() in APPROACH_LABELS and det.confidence >= threshold:
                return True
    return False


def has_qualified_departure(frame: MultimodalFrame, threshold: float = 0.35) -> bool:
    """Checks whether any available vision source reports a qualified departure detection."""
    for record in frame.vision_records:
        if not record.available:
            continue
        for det in record.detections:
            if det.label.lower() in DEPARTURE_LABELS and det.confidence >= threshold:
                return True
    return False


def has_audio_train_presence(frame: MultimodalFrame, threshold: float = 0.3700) -> bool:
    """Checks whether any available audio source reports train acoustic presence."""
    for record in frame.audio_records:
        if not record.available:
            continue
        for det in record.detections:
            label = det.label.lower()
            if (label in AUDIO_TRAIN_LABELS or "train" in label) and det.confidence >= threshold:
                return True
    return False
