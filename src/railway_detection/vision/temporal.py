"""Temporal evidence engine.

Maintains a sliding per-source buffer of detections and applies configurable
confidence smoothing, consecutive-frame confirmation, detection persistence,
miss tolerance, and evidence expiry. This layer emits evidence only; it never
makes gate open/close decisions.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from railway_detection.fusion.evidence import EvidenceRecord
from railway_detection.utils.logging import get_logger

logger = get_logger("vision.temporal")


@dataclass
class TemporalConfig:
    confirm_frames: int = 3
    confirm_window_s: float = 0.5
    miss_tolerance_frames: int = 2
    evidence_expiry_s: float = 3.0
    smoothing_alpha: float = 0.5


@dataclass
class LabelState:
    smoothed_confidence: float = 0.0
    consecutive_frames: int = 0
    missed_frames: int = 0
    first_seen_s: float = -1.0
    last_seen_s: float = -1.0
    confirmed: bool = False

    @property
    def active(self) -> bool:
        return self.consecutive_frames > 0 or self.missed_frames > 0


@dataclass
class SourceState:
    labels: dict[str, LabelState] = field(default_factory=dict)
    last_timestamp_s: float | None = None

    def ensure_label(self, name: str) -> LabelState:
        if name not in self.labels:
            self.labels[name] = LabelState()
        return self.labels[name]


class TemporalEvidenceBuffer:
    """Sliding-window temporal filter over per-source detections."""

    def __init__(self, config: TemporalConfig | None = None) -> None:
        self.config = config or TemporalConfig()
        self._sources: dict[str, SourceState] = {}
        self._history: dict[str, deque[tuple[float, list[tuple[str, float]]]]] = (
            defaultdict(deque)
        )

    def process(
        self, record: EvidenceRecord
    ) -> EvidenceRecord:
        """Process one evidence record and emit the temporally filtered version."""
        if record.timestamp_s < 0:
            raise ValueError("timestamp_s must be non-negative")

        source = self._sources.setdefault(record.source_id, SourceState())
        if source.last_timestamp_s is not None:
            if record.timestamp_s < source.last_timestamp_s:
                raise ValueError(
                    f"out-of-order timestamp for {record.source_id}: "
                    f"{record.timestamp_s} < {source.last_timestamp_s}"
                )
        source.last_timestamp_s = record.timestamp_s

        if not record.available:
            self._expire_all(source, record.timestamp_s)
            return EvidenceRecord(
                timestamp_s=record.timestamp_s,
                source_id=record.source_id,
                modality=record.modality,
                available=False,
                metadata={**record.metadata, "temporal_status": "unavailable"},
            )

        detections_by_label: dict[str, float] = {}
        for detection in record.detections:
            current = detections_by_label.get(detection.label)
            if current is None or detection.confidence > current:
                detections_by_label[detection.label] = detection.confidence

        filtered: list[Any] = []
        now = record.timestamp_s
        for label, confidence in detections_by_label.items():
            state = source.ensure_label(label)
            if state.last_seen_s < 0 or state.consecutive_frames == 0:
                state.first_seen_s = now
            state.smoothed_confidence = (
                self.config.smoothing_alpha * confidence
                + (1.0 - self.config.smoothing_alpha) * state.smoothed_confidence
                if state.last_seen_s >= 0
                else confidence
            )
            state.consecutive_frames += 1
            state.missed_frames = 0
            state.last_seen_s = now
            if (
                state.consecutive_frames >= self.config.confirm_frames
                or (
                    state.first_seen_s >= 0
                    and now - state.first_seen_s >= self.config.confirm_window_s
                )
            ):
                state.confirmed = True

        for label in list(source.labels.keys()):
            state = source.labels[label]
            if label in detections_by_label:
                continue
            if not state.active:
                continue
            if now - state.last_seen_s > self.config.evidence_expiry_s:
                state.consecutive_frames = 0
                state.confirmed = False
                state.smoothed_confidence = 0.0
                state.missed_frames = 0
                continue
            state.missed_frames += 1
            if state.missed_frames <= self.config.miss_tolerance_frames:
                # persistence: retain the previous state for a short gap
                filtered.append(
                    self._evidence_entry(
                        label, state.smoothed_confidence, state.confirmed
                    )
                )
            else:
                state.consecutive_frames = 0
                state.confirmed = False

        for label in detections_by_label:
            state = source.ensure_label(label)
            filtered.append(
                self._evidence_entry(
                    label, state.smoothed_confidence, state.confirmed
                )
            )

        return EvidenceRecord(
            timestamp_s=record.timestamp_s,
            source_id=record.source_id,
            modality=record.modality,
            available=True,
            detections=tuple(
                entry for entry in filtered
            ),
            metadata={**record.metadata, "temporal_status": "processed"},
        )

    def _evidence_entry(
        self, label: str, confidence: float, confirmed: bool
    ) -> Any:
        from railway_detection.fusion.evidence import Detection

        return Detection(
            label=label,
            confidence=confidence,
            metadata={"temporal_confirmed": confirmed},
        )

    def _expire_all(self, source: SourceState, now: float) -> None:
        for state in source.labels.values():
            if now - state.last_seen_s > self.config.evidence_expiry_s:
                state.consecutive_frames = 0
                state.confirmed = False
                state.smoothed_confidence = 0.0
                state.missed_frames = 0
