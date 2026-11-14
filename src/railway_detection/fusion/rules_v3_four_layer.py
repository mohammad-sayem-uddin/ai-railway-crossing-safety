"""Four-layer multimodal rule identifiers, evaluators, and Layer-2 movement tracking."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.evidence import Detection, EvidenceRecord, EvidenceStatus
from railway_detection.fusion.rules import AUDIO_TRAIN_LABELS

FRONT_APPROACH_LABELS = frozenset({"front", "train_front"})
REAR_DEPARTURE_LABELS = frozenset({"rear", "train_rear"})
HORN_LABELS = AUDIO_TRAIN_LABELS

SIDE_PRESENCE_LABELS = frozenset({"side", "train_body", "carriage", "locomotive", "train_side"})
LAST_CARRIAGE_LABELS = frozenset({"last_carriage", "train_tail", "tail", "end_of_train"})


class DeparturePolicyMode(StrEnum):
    """Controls how Layer 4 interprets back-camera clearance."""

    CONSERVATIVE_POSITIVE = "conservative_positive"
    GUARDED_DISAPPEARANCE = "guarded_disappearance"


class RuleIdV3(StrEnum):
    """Explicit rule identifiers across all four operational layers and fail-safes."""

    RULE_L1_FRONT_APPROACH_TRIGGER = "L1_FRONT_APPROACH_TRIGGER"
    RULE_L1_APPROACH_UNCONFIRMED_RESET = "L1_APPROACH_UNCONFIRMED_RESET"
    RULE_L2_SIDE_MOVEMENT_CONFIRMED = "L2_SIDE_MOVEMENT_CONFIRMED"
    RULE_L2_SIDE_STOPPED_HOLD = "L2_SIDE_STOPPED_HOLD"
    RULE_L2_SIDE_SINGLE_FRAME_HOLD = "L2_SIDE_SINGLE_FRAME_HOLD"
    RULE_L3_AUDIO_SUPPORT_ONLY = "L3_AUDIO_SUPPORT_ONLY"
    RULE_L3_AUDIO_DWELL_HOLD = "L3_AUDIO_DWELL_HOLD"
    RULE_L4_BACK_POSITIVE_DEPARTURE = "L4_BACK_POSITIVE_DEPARTURE"
    RULE_L4_BACK_LAST_CARRIAGE_CONFIRMED = "L4_BACK_LAST_CARRIAGE_CONFIRMED"
    RULE_L4_BACK_GUARDED_DISAPPEARANCE = "L4_BACK_GUARDED_DISAPPEARANCE"
    RULE_L4_BACK_SPARSE_DROPOUT_HOLD = "L4_BACK_SPARSE_DROPOUT_HOLD"
    RULE_L4_REVERSAL_HOLD = "L4_REVERSAL_HOLD"
    RULE_L5_OCCUPANCY_CLEAR_VERIFIED = "L5_OCCUPANCY_CLEAR_VERIFIED"
    RULE_L5_OCCUPANCY_HOLD_UNKNOWN_OR_MISSING = "L5_OCCUPANCY_HOLD_UNKNOWN_OR_MISSING"
    RULE_L5_OCCUPANCY_CONTRADICTION_ABORT = "L5_OCCUPANCY_CONTRADICTION_ABORT"
    RULE_L5_REOPEN_AUTHORIZED = "L5_REOPEN_AUTHORIZED"
    RULE_L5_MULTI_TRAIN_INTERRUPT = "L5_MULTI_TRAIN_INTERRUPT"
    RULE_TIMEOUT_FAIL_SAFE = "L5_INFERENCE_TIMEOUT_FAIL_SAFE"


def _is_front_source(source_id: str) -> bool:
    s = source_id.lower()
    if _is_side_source(s) or _is_back_source(s):
        return False
    return any(tok in s for tok in ("camera_1", "cam_1", "front", "approach")) or s == "camera"


def _is_side_source(source_id: str) -> bool:
    s = source_id.lower()
    return any(tok in s for tok in ("side", "camera_3", "cam_3", "cam_side"))


def _is_back_source(source_id: str) -> bool:
    s = source_id.lower()
    return any(tok in s for tok in ("camera_2", "cam_2", "back", "rear", "departure"))


def classify_vision_sources(source_ids: Iterable[str] | set[str]) -> dict[str, list[str]]:
    """Group known vision source IDs by operational role (front, side, back)."""
    roles: dict[str, list[str]] = {"front": [], "side": [], "back": []}
    for src in sorted(source_ids):
        if _is_side_source(src):
            roles["side"].append(src)
        elif _is_back_source(src):
            roles["back"].append(src)
        elif _is_front_source(src) or "camera" in src.lower() or "vision" in src.lower():
            roles["front"].append(src)
    return roles


@dataclass(frozen=True)
class Layer1FrontEvidence:
    detected: bool
    max_confidence: float
    qualifying_labels: tuple[str, ...]
    source_ids: tuple[str, ...]
    approach_only_labels: bool


def extract_layer1_front_evidence(
    frame: MultimodalFrame,
    threshold: float = 0.35,
    *,
    allow_any_front_camera_label: bool = True,
) -> Layer1FrontEvidence:
    """Layer 1: Inspect front approach camera without waiting for side, audio, or back.

    In Layer B v2 front videos, rotated frames often fired ``side`` or ``rear`` proxy
    classes alongside ``front``. When ``allow_any_front_camera_label=True`` (matching
    V1/V2 approach semantics on ``camera_1``), any qualifying train class on a front
    approach camera triggers Layer 1; when False, strictly requires ``FRONT_APPROACH_LABELS``.
    """
    max_conf = 0.0
    labels: list[str] = []
    sources: list[str] = []
    strict_front_labels = False

    for rec in frame.vision_records:
        if not rec.available or not _is_front_source(rec.source_id):
            continue
        for det in rec.detections:
            lbl = det.label.lower()
            if float(det.confidence) < threshold:
                continue
            is_strict_front = lbl in FRONT_APPROACH_LABELS
            is_train_label = is_strict_front or (
                allow_any_front_camera_label and lbl in (SIDE_PRESENCE_LABELS | REAR_DEPARTURE_LABELS)
            )
            if is_train_label:
                max_conf = max(max_conf, float(det.confidence))
                labels.append(det.label)
                if rec.source_id not in sources:
                    sources.append(rec.source_id)
                if is_strict_front:
                    strict_front_labels = True

    return Layer1FrontEvidence(
        detected=bool(labels),
        max_confidence=max_conf,
        qualifying_labels=tuple(labels),
        source_ids=tuple(sources),
        approach_only_labels=strict_front_labels,
    )


@dataclass(frozen=True)
class Layer2SideEvidence:
    present: bool
    dedicated_side_source_present: bool
    movement_state: str  # "MOVING", "STOPPED", "SINGLE_FRAME", "UNOBSERVED"
    consecutive_observations: int
    displacement_px: float | None
    max_confidence: float
    source_ids: tuple[str, ...]


class SideMovementTracker:
    """Layer 2 tracker separating persistent movement from isolated frames and stops."""

    def __init__(
        self,
        *,
        presence_threshold: float = 0.35,
        min_persistence_frames: int = 2,
        stopped_displacement_px_per_s: float = 2.0,
        stopped_min_duration_s: float = 2.0,
    ) -> None:
        self.presence_threshold = float(presence_threshold)
        self.min_persistence_frames = int(min_persistence_frames)
        self.stopped_displacement_px_per_s = float(stopped_displacement_px_per_s)
        self.stopped_min_duration_s = float(stopped_min_duration_s)
        self._consecutive_obs: int = 0
        self._last_centroid: tuple[float, float] | None = None
        self._last_bbox_area: float | None = None
        self._last_obs_t: float | None = None
        self._stationary_since_t: float | None = None

    def reset(self) -> None:
        self._consecutive_obs = 0
        self._last_centroid = None
        self._last_bbox_area = None
        self._last_obs_t = None
        self._stationary_since_t = None

    @staticmethod
    def _largest_bbox_stats(dets: list[Detection]) -> tuple[tuple[float, float] | None, float | None]:
        best_area = -1.0
        best_centroid: tuple[float, float] | None = None
        for det in dets:
            if det.bbox_xyxy is None or len(det.bbox_xyxy) != 4:
                continue
            x1, y1, x2, y2 = det.bbox_xyxy
            w = max(0.0, float(x2) - float(x1))
            h = max(0.0, float(y2) - float(y1))
            area = w * h
            if area > best_area:
                best_area = area
                best_centroid = ((float(x1) + float(x2)) / 2.0, (float(y1) + float(y2)) / 2.0)
        return (best_centroid, best_area) if best_area >= 0.0 else (None, None)

    def update(self, frame: MultimodalFrame) -> Layer2SideEvidence:
        t = float(frame.master_timestamp_s)
        qualifying: list[Detection] = []
        sources: list[str] = []
        dedicated_side = False
        max_conf = 0.0

        for rec in frame.vision_records:
            if not rec.available:
                continue
            is_side_src = _is_side_source(rec.source_id)
            for det in rec.detections:
                if float(det.confidence) < self.presence_threshold:
                    continue
                lbl = det.label.lower()
                if is_side_src or lbl in SIDE_PRESENCE_LABELS:
                    qualifying.append(det)
                    max_conf = max(max_conf, float(det.confidence))
                    if rec.source_id not in sources:
                        sources.append(rec.source_id)
                    if is_side_src:
                        dedicated_side = True

        # Determine whether any registered dedicated side camera actively ran this tick
        side_src_refreshed = any(_is_side_source(r.source_id) for r in frame.vision_records)
        if not qualifying:
            if side_src_refreshed:
                self._consecutive_obs = 0
                self._last_centroid = None
                self._last_bbox_area = None
                self._last_obs_t = None
                self._stationary_since_t = None
            return Layer2SideEvidence(
                present=False,
                dedicated_side_source_present=False,
                movement_state="UNOBSERVED",
                consecutive_observations=self._consecutive_obs,
                displacement_px=None,
                max_confidence=0.0,
                source_ids=(),
            )

        self._consecutive_obs += 1
        centroid, area = self._largest_bbox_stats(qualifying)
        disp: float | None = None
        movement_state = (
            "SINGLE_FRAME" if self._consecutive_obs < self.min_persistence_frames else "MOVING"
        )

        # Explicitly allow synthetic/annotated stationary flags when bbox absent
        explicit_stopped = any(bool(d.metadata.get("stopped", False)) for d in qualifying)
        if explicit_stopped:
            movement_state = "STOPPED"
            if self._stationary_since_t is None:
                self._stationary_since_t = t
        elif (
            centroid is not None
            and self._last_centroid is not None
            and self._last_obs_t is not None
            and (t - self._last_obs_t) > 1e-6
        ):
            dt = t - self._last_obs_t
            dx = centroid[0] - self._last_centroid[0]
            dy = centroid[1] - self._last_centroid[1]
            disp = (dx * dx + dy * dy) ** 0.5
            area_delta = (
                abs(area - self._last_bbox_area) / max(self._last_bbox_area, 1.0)
                if area is not None and self._last_bbox_area is not None
                else 0.0
            )
            speed_px_s = disp / dt
            if speed_px_s < self.stopped_displacement_px_per_s and area_delta < 0.03:
                if self._stationary_since_t is None:
                    self._stationary_since_t = t
                if (t - self._stationary_since_t) >= self.stopped_min_duration_s:
                    movement_state = "STOPPED"
            else:
                self._stationary_since_t = None

        if centroid is not None:
            self._last_centroid = centroid
            self._last_bbox_area = area
            self._last_obs_t = t

        return Layer2SideEvidence(
            present=True,
            dedicated_side_source_present=dedicated_side,
            movement_state=movement_state,
            consecutive_observations=self._consecutive_obs,
            displacement_px=disp,
            max_confidence=max_conf,
            source_ids=tuple(sources),
        )


@dataclass(frozen=True)
class Layer3AudioEvidence:
    horn_detected: bool
    max_confidence: float
    source_ids: tuple[str, ...]
    available: bool


def extract_layer3_audio_evidence(
    frame: MultimodalFrame, threshold: float = 0.37
) -> Layer3AudioEvidence:
    """Layer 3: Evaluate audio horn evidence strictly as supporting presence."""
    max_conf = 0.0
    sources: list[str] = []
    any_available = any(r.available for r in frame.audio_records)
    for rec in frame.audio_records:
        if not rec.available:
            continue
        for det in rec.detections:
            if det.label.lower() in HORN_LABELS and float(det.confidence) >= threshold:
                max_conf = max(max_conf, float(det.confidence))
                if rec.source_id not in sources:
                    sources.append(rec.source_id)
    return Layer3AudioEvidence(
        horn_detected=bool(sources),
        max_confidence=max_conf,
        source_ids=tuple(sources),
        available=any_available,
    )


@dataclass(frozen=True)
class Layer4DepartureAssessment:
    back_present: bool
    positive_rear: bool
    last_carriage_confirmed: bool
    reversing_detected: bool
    back_source_refreshed: bool
    back_source_healthy: bool
    max_confidence: float
    source_ids: tuple[str, ...]
    labels: tuple[str, ...]


def extract_layer4_departure_evidence(
    frame: MultimodalFrame,
    *,
    rear_threshold: float = 0.35,
    back_sources: Iterable[str] = (),
) -> Layer4DepartureAssessment:
    """Layer 4: Separate positive rear/last-carriage confirmation from generic presence."""
    max_conf = 0.0
    src_ids: list[str] = []
    labels: list[str] = []
    pos_rear = False
    last_carriage = False
    reversing = False
    any_back_present = False
    back_refreshed = False

    for rec in frame.vision_records:
        is_back = _is_back_source(rec.source_id)
        if is_back:
            back_refreshed = True
        if not rec.available:
            continue
        for det in rec.detections:
            conf = float(det.confidence)
            if conf < rear_threshold:
                continue
            lbl = det.label.lower()
            if det.metadata.get("reversing") or str(det.metadata.get("direction", "")).lower() == "reverse":
                reversing = True
            if lbl in LAST_CARRIAGE_LABELS or bool(det.metadata.get("last_carriage", False)):
                last_carriage = True
                pos_rear = True
                any_back_present = True
                max_conf = max(max_conf, conf)
                labels.append(det.label)
                if rec.source_id not in src_ids:
                    src_ids.append(rec.source_id)
            elif is_back and lbl in (REAR_DEPARTURE_LABELS | SIDE_PRESENCE_LABELS):
                any_back_present = True
                if lbl in REAR_DEPARTURE_LABELS:
                    pos_rear = True
                max_conf = max(max_conf, conf)
                labels.append(det.label)
                if rec.source_id not in src_ids:
                    src_ids.append(rec.source_id)
            elif not is_back and lbl in REAR_DEPARTURE_LABELS:
                pos_rear = True
                any_back_present = True
                max_conf = max(max_conf, conf)
                labels.append(det.label)
                if rec.source_id not in src_ids:
                    src_ids.append(rec.source_id)

    back_list = list(back_sources)
    healthy = True
    if back_list:
        healthy = all(
            frame.source_availability.get(src, True)
            and frame.source_statuses.get(src, EvidenceStatus.UNKNOWN.value)
            not in {
                EvidenceStatus.MISSING.value,
                EvidenceStatus.STALE.value,
                EvidenceStatus.UNAVAILABLE.value,
            }
            for src in back_list
        )

    return Layer4DepartureAssessment(
        back_present=any_back_present,
        positive_rear=pos_rear,
        last_carriage_confirmed=last_carriage,
        reversing_detected=reversing,
        back_source_refreshed=back_refreshed,
        back_source_healthy=healthy,
        max_confidence=max_conf,
        source_ids=tuple(src_ids),
        labels=tuple(labels),
    )
