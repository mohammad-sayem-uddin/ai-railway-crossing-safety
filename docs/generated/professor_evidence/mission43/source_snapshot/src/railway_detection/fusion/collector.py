"""Multimodal evidence collection, time alignment, and synchronized frame emission."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from railway_detection.data.sync import SyncAligner
from railway_detection.fusion.evidence import EvidenceRecord, Modality
from railway_detection.fusion.source_tracker import SourceTracker
from railway_detection.utils.logging import get_logger

logger = get_logger("fusion.collector")


@dataclass(frozen=True)
class MultimodalFrame:
    """Time-synchronized snapshot of all sensor evidence at a master clock instant."""

    master_timestamp_s: float
    vision_records: tuple[EvidenceRecord, ...] = ()
    audio_records: tuple[EvidenceRecord, ...] = ()
    source_availability: dict[str, bool] = field(default_factory=dict)
    active_sources: tuple[str, ...] = ()
    missing_sources: tuple[str, ...] = ()
    source_health: dict[str, str] = field(default_factory=dict)
    health_reasons: dict[str, str] = field(default_factory=dict)
    observation_ages: dict[str, float] = field(default_factory=dict)

    @property
    def has_vision_evidence(self) -> bool:
        return any(bool(r.detections) for r in self.vision_records if r.available)

    @property
    def has_audio_evidence(self) -> bool:
        return any(bool(r.detections) for r in self.audio_records if r.available)

    @property
    def all_detections(self) -> list:
        dets = []
        for r in self.vision_records:
            if r.available:
                dets.extend(r.detections)
        for r in self.audio_records:
            if r.available:
                dets.extend(r.detections)
        return dets


class MultimodalEvidenceCollector:
    """Aggregates asynchronous evidence streams and produces master-time aligned frames."""

    def __init__(
        self,
        source_tracker: SourceTracker | None = None,
        sync_aligner: SyncAligner | None = None,
        window_tolerance_s: float = 0.5,
    ) -> None:
        self.tracker = source_tracker if source_tracker is not None else SourceTracker()
        self.aligner = sync_aligner
        self.window_tolerance_s = float(window_tolerance_s)
        self._buffer: deque[tuple[float, EvidenceRecord]] = deque()
        # Per-source last-ingested master timestamp, used to reject duplicate
        # and out-of-order observations at ingestion time (not merely at the
        # SourceTracker health-state layer, which only suppresses the health
        # update and still lets the duplicate/disordered record enter the
        # frame buffer). Keyed by source_id.
        self._last_ingested_master_t: dict[str, float] = {}
        # Audit log of every rejected observation: {source_id, modality,
        # local_timestamp_s, attempted_master_timestamp_s, reason}. Original
        # local timestamps are preserved here even though the record itself
        # is discarded, so a run manifest can report exactly what was
        # rejected and why.
        self.rejected_observations: list[dict[str, object]] = []

    def _reject(self, record: EvidenceRecord, master_t: float, reason: str) -> None:
        logger.warning(
            "Rejecting %s observation from source '%s': local_t=%f master_t=%f reason=%s",
            record.modality.value if hasattr(record.modality, "value") else record.modality,
            record.source_id,
            record.timestamp_s,
            master_t,
            reason,
        )
        self.rejected_observations.append(
            {
                "source_id": record.source_id,
                "modality": record.modality.value if hasattr(record.modality, "value") else str(record.modality),
                "local_timestamp_s": record.timestamp_s,
                "attempted_master_timestamp_s": master_t,
                "reason": reason,
            }
        )

    def add_evidence(self, record: EvidenceRecord) -> None:
        """Ingest a single evidence record from any modality.

        R04 safety fix: when an aligner IS attached to this collector, every
        vision source it observes must be explicitly registered in that
        aligner (including the reference camera, conventionally at
        offset_s=0.0). A vision source that is not registered is no longer
        silently treated as already being on the master clock (offset 0) --
        that was the exact defect that let unvalidated zero-offset fusion
        happen whenever a caller forgot to register one camera. Audio
        sources are exempt: they are evaluated against whichever vision
        camera's clock they were extracted from and are registered under
        that camera's own source_id upstream, not independently time-shifted
        here.
        """
        master_t = record.timestamp_s
        if self.aligner is not None:
            if record.source_id in self.aligner.offsets_s:
                master_t = self.aligner.to_master(record.source_id, record.timestamp_s)
            elif record.modality == Modality.VISION:
                raise ValueError(
                    f"R04 fail-closed violation: aligner is attached but vision source "
                    f"'{record.source_id}' is not registered in it. Register every fused "
                    f"vision source explicitly (including the reference camera at "
                    f"offset_s=0.0) before ingesting its evidence, or omit the aligner "
                    f"entirely to run this source in single-camera, media-local-time mode."
                )

        # Per-source duplicate/out-of-order rejection at ingestion time.
        # Stable identity here is (source_id, master timestamp): the master
        # clock is the right identity space because two records from the
        # SAME source can never legitimately share or regress a master
        # timestamp once synchronization (if any) has been applied -- a
        # single physical sensor produces observations in monotonic time
        # order. Rejecting here (not only inside SourceTracker, which only
        # suppresses the health-state update) prevents a duplicate record's
        # body from ever entering a MultimodalFrame at all, closing the gap
        # where two copies of the same detection could inflate evidence
        # references or, via two frames sharing a timestamp, double-count
        # toward decision-engine confirmation/dwell counters.
        last_t = self._last_ingested_master_t.get(record.source_id)
        if last_t is not None:
            if abs(master_t - last_t) < 1e-9:
                self._reject(record, master_t, "duplicate_observation")
                return
            if master_t < last_t - 1e-9:
                self._reject(record, master_t, "out_of_order_observation")
                return
        self._last_ingested_master_t[record.source_id] = master_t

        self.tracker.record_observation(
            source_id=record.source_id,
            timestamp_s=master_t,
            available=record.available,
            detections=record.detections,
            metadata=record.metadata,
        )
        self._buffer.append((master_t, record))

    def add_evidence_batch(
        self, records: list[EvidenceRecord], preserve_arrival_order: bool = False
    ) -> None:
        """Ingest a batch of records (sorted by default, or in arrival order when requested)."""
        ordered = list(records) if preserve_arrival_order else sorted(records, key=lambda r: r.timestamp_s)
        for rec in ordered:
            self.add_evidence(rec)

    def collect_frame(
        self, current_master_time_s: float, purge_older_than_s: float = 5.0
    ) -> MultimodalFrame:
        """Assemble a MultimodalFrame aligned to current_master_time_s."""
        t_min = current_master_time_s - self.window_tolerance_s
        t_max = current_master_time_s + 1e-6

        vision_records: list[EvidenceRecord] = []
        audio_records: list[EvidenceRecord] = []

        for master_t, rec in self._buffer:
            if t_min <= master_t <= t_max:
                if rec.modality == Modality.VISION:
                    vision_records.append(rec)
                elif rec.modality == Modality.AUDIO:
                    audio_records.append(rec)

        # Purge stale evidence older than current_master_time_s - purge_older_than_s.
        # Rebuilds the buffer by filtering rather than popping from the left
        # under the assumption the deque is globally time-sorted: when
        # multiple sources are ingested as separate contiguous batches (the
        # normal pattern here -- all vision, then all audio), the deque is
        # two sorted runs concatenated, not one globally sorted sequence, so
        # a front-popping purge can stop early and silently retain an
        # unbounded amount of genuinely-stale data from a later-ingested
        # source. This does not affect frame-assembly correctness (that scan
        # is already order-independent) but does affect whether purging
        # actually bounds memory as intended.
        cutoff = current_master_time_s - purge_older_than_s
        if self._buffer and self._buffer[0][0] < cutoff:
            self._buffer = deque(item for item in self._buffer if item[0] >= cutoff)

        availability = self.tracker.get_availability_map(current_master_time_s)
        health_map = self.tracker.get_health_map(current_master_time_s)
        reason_map = self.tracker.get_reason_map(current_master_time_s)
        age_map = self.tracker.get_age_map(current_master_time_s)
        active = tuple(src for src, avail in availability.items() if avail)
        missing = tuple(src for src, avail in availability.items() if not avail)

        return MultimodalFrame(
            master_timestamp_s=float(current_master_time_s),
            vision_records=tuple(vision_records),
            audio_records=tuple(audio_records),
            source_availability=availability,
            active_sources=active,
            missing_sources=missing,
            source_health=health_map,
            health_reasons=reason_map,
            observation_ages=age_map,
        )

    def generate_frames_from_history(
        self,
        start_time_s: float,
        end_time_s: float,
        stride_s: float = 0.1,
    ) -> list[MultimodalFrame]:
        """Replay entire recorded buffer over [start_time_s, end_time_s] with fixed stride."""
        frames: list[MultimodalFrame] = []
        t = float(start_time_s)
        while t <= end_time_s + 1e-9:
            # When batch generating from history, don't purge so all intervals see data
            frame = self._build_frame_at(t)
            frames.append(frame)
            t += stride_s
        return frames

    def _build_frame_at(self, current_master_time_s: float) -> MultimodalFrame:
        t_min = current_master_time_s - self.window_tolerance_s
        t_max = current_master_time_s + 1e-6

        vision_records: list[EvidenceRecord] = []
        audio_records: list[EvidenceRecord] = []

        for master_t, rec in self._buffer:
            if t_min <= master_t <= t_max:
                if rec.modality == Modality.VISION:
                    vision_records.append(rec)
                elif rec.modality == Modality.AUDIO:
                    audio_records.append(rec)

        availability = self.tracker.get_availability_map(current_master_time_s)
        health_map = self.tracker.get_health_map(current_master_time_s)
        reason_map = self.tracker.get_reason_map(current_master_time_s)
        age_map = self.tracker.get_age_map(current_master_time_s)
        active = tuple(src for src, avail in availability.items() if avail)
        missing = tuple(src for src, avail in availability.items() if not avail)

        return MultimodalFrame(
            master_timestamp_s=float(current_master_time_s),
            vision_records=tuple(vision_records),
            audio_records=tuple(audio_records),
            source_availability=availability,
            active_sources=active,
            missing_sources=missing,
            source_health=health_map,
            health_reasons=reason_map,
            observation_ages=age_map,
        )
