"""Crossing occupancy verification interface and conservative clearance arbiter.

Distinguishes dedicated crossing-zone occupancy state (OCCUPIED, CLEAR, UNKNOWN,
MISSING, CONTRADICTORY) from back-camera train departure and audio horn signals.
Missing, stale, contradictory, or unverified occupancy always resolves fail-closed
and never permits automated gate reopening.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.evidence import Detection, EvidenceStatus, OccupancyEvidence, OccupancyState


@dataclass(frozen=True)
class OccupancyAssessment:
    """Evaluated occupancy verdict at master timestamp t."""

    state: OccupancyState
    confidence: float | None
    reason: str
    active_sources: tuple[str, ...] = ()
    contradictory_signals: tuple[str, ...] = ()
    healthy: bool = False
    fresh: bool = False
    verified_clear: bool = False


class OccupancyVerifier:
    """Evaluates whether the level crossing zone is affirmatively OCCUPIED or CLEAR.

    Design invariants:
    - Never infers CLEAR solely from the absence of detections when no healthy,
      fresh occupancy verifier covers the crossing zone.
    - Treats disagreement between occupancy sources or between CLEAR occupancy
      and active train/horn evidence as CONTRADICTORY.
    - Treats missing, stale, or unavailable occupancy observations as UNKNOWN or
      MISSING rather than CLEAR.
    """

    def __init__(
        self,
        *,
        require_dedicated_sensor: bool = True,
        max_occupancy_age_s: float = 2.0,
        min_clear_confidence: float = 0.5,
        presence_threshold: float = 0.35,
        audio_presence_threshold: float = 0.37,
    ) -> None:
        self.require_dedicated_sensor = bool(require_dedicated_sensor)
        self.max_occupancy_age_s = float(max_occupancy_age_s)
        self.min_clear_confidence = float(min_clear_confidence)
        self.presence_threshold = float(presence_threshold)
        self.audio_presence_threshold = float(audio_presence_threshold)
        self._last_valid_occupancy_t: float | None = None
        self._ever_observed_occupancy: bool = False

    def reset(self) -> None:
        self._last_valid_occupancy_t = None
        self._ever_observed_occupancy = False

    def _active_train_signals(
        self, frame: MultimodalFrame
    ) -> tuple[list[str], list[str], list[str]]:
        """Collect crossing-zone vision signals, all vision signals, and audio horn signals."""
        crossing_vision_signals: list[str] = []
        vision_signals: list[str] = []
        audio_signals: list[str] = []
        for rec in frame.vision_records:
            if not rec.available:
                continue
            src_low = rec.source_id.lower()
            is_crossing_cam = "side" in src_low or "back" in src_low or "camera_2" in src_low or "crossing" in src_low
            for det in rec.detections:
                if float(det.confidence) >= self.presence_threshold:
                    sig = f"{rec.source_id}:{det.label}({det.confidence:.2f})"
                    vision_signals.append(sig)
                    lbl = det.label.lower()
                    if (
                        is_crossing_cam
                        or bool(det.metadata.get("in_crossing_zone", False))
                        or lbl in {"side", "rear", "last_carriage"}
                    ):
                        crossing_vision_signals.append(sig)
        for rec in frame.audio_records:
            if not rec.available:
                continue
            for det in rec.detections:
                if float(det.confidence) >= self.audio_presence_threshold:
                    audio_signals.append(f"{rec.source_id}:{det.label}({det.confidence:.2f})")
        return crossing_vision_signals, vision_signals, audio_signals

    @staticmethod
    def _crossing_zone_occupied_from_metadata(detections: Iterable[Detection]) -> bool:
        for det in detections:
            if bool(det.metadata.get("in_crossing_zone", False)):
                return True
        return False

    def evaluate(
        self,
        frame: MultimodalFrame,
        *,
        extra_occupancy: tuple[OccupancyEvidence, ...] = (),
        active_crossing_expected: bool = True,
    ) -> OccupancyAssessment:
        t = float(frame.master_timestamp_s)
        crossing_signals, vision_signals, audio_signals = self._active_train_signals(frame)
        all_occ_records = list(frame.occupancy_records) + list(extra_occupancy)

        # Any explicit crossing-zone visual detection forces OCCUPIED immediately,
        # even before inspecting dedicated occupancy sensors.
        in_zone_from_vision = any(
            self._crossing_zone_occupied_from_metadata(r.detections)
            for r in frame.vision_records
            if r.available
        )

        if all_occ_records:
            self._ever_observed_occupancy = True
            valid_records: list[OccupancyEvidence] = []
            unavailable_sources: list[str] = []
            stale_sources: list[str] = []

            for occ in all_occ_records:
                age_s = t - float(occ.timestamp_s)
                if not occ.available or occ.evidence_status == EvidenceStatus.UNAVAILABLE:
                    unavailable_sources.append(occ.source_id)
                    continue
                if age_s > self.max_occupancy_age_s or occ.evidence_status == EvidenceStatus.STALE:
                    stale_sources.append(occ.source_id)
                    continue
                valid_records.append(occ)

            if valid_records:
                self._last_valid_occupancy_t = t

            states = {r.state for r in valid_records}
            active_src = tuple(sorted({r.source_id for r in valid_records}))

            if OccupancyState.CONTRADICTORY in states or (
                OccupancyState.OCCUPIED in states and OccupancyState.CLEAR in states
            ):
                return OccupancyAssessment(
                    state=OccupancyState.CONTRADICTORY,
                    confidence=None,
                    reason="Conflicting or explicitly CONTRADICTORY occupancy sensor readings",
                    active_sources=active_src,
                    contradictory_signals=tuple(
                        f"{r.source_id}:{r.state.value}" for r in valid_records
                    ),
                    healthy=False,
                    fresh=bool(valid_records),
                    verified_clear=False,
                )

            if OccupancyState.OCCUPIED in states or in_zone_from_vision:
                confs = [
                    float(r.confidence)
                    for r in valid_records
                    if r.state == OccupancyState.OCCUPIED and r.confidence is not None
                ]
                return OccupancyAssessment(
                    state=OccupancyState.OCCUPIED,
                    confidence=max(confs) if confs else None,
                    reason="Crossing occupancy sensor or zone geometry reports OCCUPIED",
                    active_sources=active_src,
                    healthy=bool(valid_records),
                    fresh=bool(valid_records),
                    verified_clear=False,
                )

            if OccupancyState.CLEAR in states:
                # Contradiction guard: occupancy sensor says CLEAR while crossing-zone
                # cameras/labels report active train presence inside the crossing.
                if crossing_signals:
                    return OccupancyAssessment(
                        state=OccupancyState.CONTRADICTORY,
                        confidence=None,
                        reason=(
                            "Occupancy reports CLEAR while active vision/audio train signals exist"
                        ),
                        active_sources=active_src,
                        contradictory_signals=tuple(crossing_signals),
                        healthy=False,
                        fresh=True,
                        verified_clear=False,
                    )
                if unavailable_sources or stale_sources:
                    return OccupancyAssessment(
                        state=OccupancyState.UNKNOWN,
                        confidence=None,
                        reason="Partial occupancy clearance negated by stale/unavailable occupancy source",
                        active_sources=active_src,
                        healthy=False,
                        fresh=False,
                        verified_clear=False,
                    )
                clear_confs = [
                    float(r.confidence)
                    for r in valid_records
                    if r.state == OccupancyState.CLEAR and r.confidence is not None
                ]
                min_conf = min(clear_confs) if clear_confs else 1.0
                if min_conf < self.min_clear_confidence:
                    return OccupancyAssessment(
                        state=OccupancyState.UNKNOWN,
                        confidence=min_conf,
                        reason=(
                            f"Occupancy CLEAR confidence {min_conf:.2f} below threshold "
                            f"{self.min_clear_confidence:.2f}"
                        ),
                        active_sources=active_src,
                        healthy=True,
                        fresh=True,
                        verified_clear=False,
                    )
                return OccupancyAssessment(
                    state=OccupancyState.CLEAR,
                    confidence=min_conf,
                    reason="Healthy, fresh occupancy verification confirms crossing is CLEAR",
                    active_sources=active_src,
                    healthy=True,
                    fresh=True,
                    verified_clear=True,
                )

            if OccupancyState.UNKNOWN in states:
                return OccupancyAssessment(
                    state=OccupancyState.UNKNOWN,
                    confidence=None,
                    reason="Occupancy verifier explicitly reports UNKNOWN state",
                    active_sources=active_src,
                    healthy=True,
                    fresh=True,
                    verified_clear=False,
                )

            return OccupancyAssessment(
                state=OccupancyState.MISSING,
                confidence=None,
                reason="Occupancy sensor records are stale or unavailable",
                active_sources=active_src,
                healthy=False,
                fresh=False,
                verified_clear=False,
            )

        # No occupancy records attached on this tick
        if vision_signals or in_zone_from_vision or audio_signals:
            return OccupancyAssessment(
                state=OccupancyState.OCCUPIED,
                confidence=None,
                reason="Active visual/audio train evidence implies crossing may still be OCCUPIED",
                active_sources=tuple(sorted(set(vision_signals + audio_signals))),
                healthy=False,
                fresh=False,
                verified_clear=False,
            )

        if self._ever_observed_occupancy and (
            self._last_valid_occupancy_t is None
            or (t - self._last_valid_occupancy_t) > self.max_occupancy_age_s
        ):
            return OccupancyAssessment(
                state=OccupancyState.MISSING,
                confidence=None,
                reason="Previously active occupancy verifier stopped reporting (MISSING)",
                healthy=False,
                fresh=False,
                verified_clear=False,
            )

        if not self.require_dedicated_sensor and not active_crossing_expected:
            return OccupancyAssessment(
                state=OccupancyState.UNKNOWN,
                confidence=None,
                reason="No dedicated crossing occupancy sensor configured; state remains UNKNOWN",
                healthy=False,
                fresh=False,
                verified_clear=False,
            )

        return OccupancyAssessment(
            state=OccupancyState.UNKNOWN,
            confidence=None,
            reason="No fresh crossing-zone occupancy sensor observation available",
            healthy=False,
            fresh=False,
            verified_clear=False,
        )
