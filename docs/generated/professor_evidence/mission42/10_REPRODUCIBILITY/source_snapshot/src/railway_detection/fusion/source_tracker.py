"""Sensor source health, timeout monitoring, and availability tracking.

Implements Phase 3 deterministic sensor health state machine:
- HEALTHY: Sensor is active, observations arrive within 2.0s timeout, valid data.
  CRITICAL: 0 detections on a valid frame/window is HEALTHY negative evidence, NOT a failure!
- DEGRADED: Observation received but degraded in quality, resolution, or integrity.
- STALE: Elapsed time since last valid observation exceeds timeout (2.0s).
- MISSING: Sensor stream missing, disconnected, or unobserved.
- RECOVERING: Sensor resumed emission but awaiting confirmation frames (2 frames).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from railway_detection.fusion.evidence import Modality
from railway_detection.utils.logging import get_logger

logger = get_logger("fusion.source_tracker")


class SensorHealth(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    STALE = "stale"
    MISSING = "missing"
    RECOVERING = "recovering"
    FAILED = "failed"  # Alias for backwards compatibility with legacy tests


class HealthReason(StrEnum):
    OBSERVATION_HEALTHY = "observation_healthy"
    OBSERVATION_NO_DETECTIONS = "observation_no_detections"
    OBSERVATION_DEGRADED = "observation_degraded"
    OBSERVATION_CORRUPTED = "observation_corrupted"
    TIMEOUT_STALE = "timeout_stale"
    INPUT_MISSING = "input_missing"
    OUT_OF_ORDER = "out_of_order"
    RECOVERY_PENDING = "recovery_pending"
    FLAPPING_INSTABILITY = "flapping_instability"
    INITIALIZING = "initializing"


@dataclass
class SourceStatus:
    source_id: str
    modality: Modality
    role: str = "primary"
    timeout_s: float = 2.0
    camera_id: str | None = None
    event_id: str | None = None
    last_timestamp_s: float = 0.0
    last_valid_timestamp_s: float = 0.0
    last_sequence_num: int = -1
    health: SensorHealth = SensorHealth.HEALTHY
    health_reason: HealthReason = HealthReason.INITIALIZING
    last_available: bool = False
    registered: bool = True
    consecutive_valid_observations: int = 0
    consecutive_missing_observations: int = 0
    flapping_count: int = 0
    recovery_start_time_s: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SourceTracker:
    """Tracks availability, health states, and failure monitoring for evidence sources.

    Maintains heartbeats and enforces fail-safe detection when primary or secondary
    sensors drop frames, disconnect, or time out.
    """

    def __init__(
        self,
        default_timeout_s: float = 2.0,
        confirmation_frames: int = 2,
        recovery_hold_s: float = 3.0,
    ) -> None:
        self.default_timeout_s = float(default_timeout_s)
        self.confirmation_frames = int(confirmation_frames)
        self.recovery_hold_s = float(recovery_hold_s)
        self.sources: dict[str, SourceStatus] = {}

    def register_source(
        self,
        source_id: str,
        role: str = "primary",
        modality: Modality = Modality.VISION,
        timeout_s: float | None = None,
        camera_id: str | None = None,
        event_id: str | None = None,
    ) -> None:
        """Register an expected sensor stream."""
        timeout = float(timeout_s) if timeout_s is not None else self.default_timeout_s
        cam_id = camera_id
        if cam_id is None and modality == Modality.VISION:
            cam_id = source_id

        self.sources[source_id] = SourceStatus(
            source_id=source_id,
            modality=modality,
            role=role,
            timeout_s=timeout,
            camera_id=cam_id,
            event_id=event_id,
            last_timestamp_s=0.0,
            last_valid_timestamp_s=0.0,
            last_sequence_num=-1,
            health=SensorHealth.HEALTHY,
            health_reason=HealthReason.INITIALIZING,
            last_available=False,
            registered=True,
            consecutive_valid_observations=0,
            consecutive_missing_observations=0,
            flapping_count=0,
        )

    def record_heartbeat(
        self, source_id: str, timestamp_s: float, available: bool = True
    ) -> None:
        """Record heartbeat (backwards-compatible API wrapper)."""
        self.record_observation(
            source_id=source_id,
            timestamp_s=timestamp_s,
            available=available,
            detections=(),
        )

    def record_observation(
        self,
        source_id: str,
        timestamp_s: float,
        available: bool = True,
        detections: tuple[Any, ...] | list[Any] = (),
        sequence_num: int = -1,
        is_degraded: bool = False,
        latency_s: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> SensorHealth:
        """Ingest observation and deterministically evaluate source health state.

        Core invariant:
        `available=True` with `detections=()` is a valid, healthy negative observation.
        """
        if source_id not in self.sources:
            modality = Modality.AUDIO if ("audio" in source_id or "mic" in source_id) else Modality.VISION
            self.register_source(source_id, modality=modality)

        status = self.sources[source_id]
        t = float(timestamp_s)
        meta = metadata or {}

        # 1. Out-of-order rejection
        if status.last_timestamp_s > 0.0 and t < status.last_timestamp_s - 1e-9:
            logger.warning(
                "Source %s out-of-order timestamp: %f < %f",
                source_id,
                t,
                status.last_timestamp_s,
            )
            status.health_reason = HealthReason.OUT_OF_ORDER
            return status.health

        # 2. Duplicate observation idempotence
        if status.last_timestamp_s > 0.0 and abs(t - status.last_timestamp_s) < 1e-9:
            return status.health

        status.last_timestamp_s = t
        if sequence_num >= 0:
            status.last_sequence_num = sequence_num
        status.metadata.update(meta)
        if latency_s > 0:
            status.metadata["processing_latency_s"] = latency_s

        prev_health = status.health

        # 3. Observation evaluation
        if available and not is_degraded:
            status.last_valid_timestamp_s = t
            status.consecutive_missing_observations = 0

            # Was the source previously failing or stale?
            if prev_health in (SensorHealth.STALE, SensorHealth.MISSING, SensorHealth.FAILED):
                # Transition to RECOVERING
                status.health = SensorHealth.RECOVERING
                status.health_reason = HealthReason.RECOVERY_PENDING
                status.consecutive_valid_observations = 1
                status.flapping_count += 1
                status.recovery_start_time_s = t
                status.last_available = False

                # If confirmation frames is 1, recover immediately
                if status.consecutive_valid_observations >= self.confirmation_frames:
                    status.health = SensorHealth.HEALTHY
                    status.health_reason = (
                        HealthReason.OBSERVATION_NO_DETECTIONS
                        if len(detections) == 0
                        else HealthReason.OBSERVATION_HEALTHY
                    )
                    status.last_available = True

            elif prev_health == SensorHealth.RECOVERING:
                status.consecutive_valid_observations += 1
                if status.consecutive_valid_observations >= self.confirmation_frames:
                    status.health = SensorHealth.HEALTHY
                    status.health_reason = (
                        HealthReason.OBSERVATION_NO_DETECTIONS
                        if len(detections) == 0
                        else HealthReason.OBSERVATION_HEALTHY
                    )
                    status.last_available = True
                else:
                    status.health = SensorHealth.RECOVERING
                    status.health_reason = HealthReason.RECOVERY_PENDING
                    status.last_available = False

            else:
                # Already HEALTHY or INITIALIZING
                status.health = SensorHealth.HEALTHY
                status.health_reason = (
                    HealthReason.OBSERVATION_NO_DETECTIONS
                    if len(detections) == 0
                    else HealthReason.OBSERVATION_HEALTHY
                )
                status.consecutive_valid_observations += 1
                status.last_available = True

        elif is_degraded:
            status.health = SensorHealth.DEGRADED
            status.health_reason = HealthReason.OBSERVATION_DEGRADED
            status.last_available = False
            status.consecutive_valid_observations = 0
            status.consecutive_missing_observations += 1

        else:
            # available == False
            status.health = SensorHealth.MISSING
            status.health_reason = HealthReason.INPUT_MISSING
            status.last_available = False
            status.consecutive_valid_observations = 0
            status.consecutive_missing_observations += 1

        return status.health

    def evaluate_staleness(self, source_id: str, current_time_s: float) -> SensorHealth:
        """Check observation age against configured timeout (e.g. 2.0s).

        Boundary behavior:
        age_s <= timeout_s: fresh.
        age_s > timeout_s: STALE.
        """
        if source_id not in self.sources:
            return SensorHealth.MISSING

        status = self.sources[source_id]
        t = float(current_time_s)

        # Unobserved source check
        if status.last_valid_timestamp_s == 0.0 and status.last_timestamp_s == 0.0:
            if t > status.timeout_s:
                status.health = SensorHealth.MISSING
                status.health_reason = HealthReason.INPUT_MISSING
                status.last_available = False
            return status.health

        age_s = t - status.last_valid_timestamp_s
        if age_s > status.timeout_s:
            status.health = SensorHealth.STALE
            status.health_reason = HealthReason.TIMEOUT_STALE
            status.last_available = False

        return status.health

    def is_available(self, source_id: str, current_time_s: float | None = None) -> bool:
        """Check whether a specific source is currently considered available.

        A source is available if and only if it is HEALTHY.
        """
        if source_id not in self.sources:
            return False

        if current_time_s is not None:
            self.evaluate_staleness(source_id, current_time_s)

        status = self.sources[source_id]
        return status.health == SensorHealth.HEALTHY and status.last_available

    def is_healthy(self, source_id: str, current_time_s: float | None = None) -> bool:
        """Check if source is strictly in HEALTHY state."""
        return self.is_available(source_id, current_time_s)

    def get_health(self, source_id: str, current_time_s: float | None = None) -> SensorHealth:
        if source_id not in self.sources:
            return SensorHealth.MISSING
        if current_time_s is not None:
            self.evaluate_staleness(source_id, current_time_s)
        return self.sources[source_id].health

    def get_reason(self, source_id: str) -> HealthReason:
        if source_id not in self.sources:
            return HealthReason.INPUT_MISSING
        return self.sources[source_id].health_reason

    def get_age(self, source_id: str, current_time_s: float) -> float:
        if source_id not in self.sources:
            return float("inf")
        status = self.sources[source_id]
        if status.last_valid_timestamp_s <= 0.0:
            return float("inf")
        return max(0.0, float(current_time_s) - status.last_valid_timestamp_s)

    def get_availability_map(
        self, current_time_s: float | None = None
    ) -> dict[str, bool]:
        """Return dict of {source_id: is_available}."""
        return {
            src_id: self.is_available(src_id, current_time_s)
            for src_id in self.sources
        }

    def get_health_map(
        self, current_time_s: float | None = None
    ) -> dict[str, str]:
        """Return dict of {source_id: health_state}."""
        return {
            src_id: str(self.get_health(src_id, current_time_s).value)
            for src_id in self.sources
        }

    def get_reason_map(
        self, current_time_s: float | None = None
    ) -> dict[str, str]:
        """Return dict of {source_id: health_reason}."""
        if current_time_s is not None:
            for s in self.sources:
                self.evaluate_staleness(s, current_time_s)
        return {
            src_id: str(self.sources[src_id].health_reason.value)
            for src_id in self.sources
        }

    def get_age_map(self, current_time_s: float) -> dict[str, float]:
        """Return dict of {source_id: age_seconds}."""
        return {
            src_id: self.get_age(src_id, current_time_s)
            for src_id in self.sources
        }

    def get_vision_sources(self) -> list[str]:
        return [
            src_id
            for src_id, s in self.sources.items()
            if s.modality == Modality.VISION
        ]

    def get_audio_sources(self) -> list[str]:
        return [
            src_id
            for src_id, s in self.sources.items()
            if s.modality == Modality.AUDIO
        ]

    def vision_health_summary(
        self, current_time_s: float | None = None
    ) -> tuple[int, int, str]:
        """Return (healthy_count, total_count, status_label)."""
        vision_sources = self.get_vision_sources()
        total_vision = len(vision_sources)
        healthy_vision = sum(
            1 for s in vision_sources if self.is_available(s, current_time_s)
        )

        if total_vision == 0:
            status = "no_vision_sources"
        elif healthy_vision == total_vision and total_vision >= 2:
            status = "dual_vision_healthy"
        elif healthy_vision == total_vision and total_vision == 1:
            status = "single_vision_healthy"
        elif healthy_vision > 0:
            status = "single_vision_degraded"
        else:
            status = "all_vision_failed"

        return healthy_vision, total_vision, status

    def is_audio_available(self, current_time_s: float | None = None) -> bool:
        """Check if at least one audio source is currently active and healthy."""
        audio_sources = self.get_audio_sources()
        return any(self.is_available(s, current_time_s) for s in audio_sources)

    def reset(self, initial_time_s: float = 0.0) -> None:
        """Reset tracker states."""
        for s in self.sources.values():
            s.last_timestamp_s = float(initial_time_s)
            s.last_valid_timestamp_s = float(initial_time_s)
            s.last_sequence_num = -1
            s.health = SensorHealth.HEALTHY
            s.health_reason = HealthReason.INITIALIZING
            s.last_available = False
            s.consecutive_valid_observations = 0
            s.consecutive_missing_observations = 0
            s.flapping_count = 0
            s.recovery_start_time_s = None
