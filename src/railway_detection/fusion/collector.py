"""Multimodal evidence collection, time alignment, and synchronized frame emission."""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

from railway_detection.data.sync import SyncAligner
from railway_detection.fusion.evidence import (
    EvidenceRecord,
    EvidenceStatus,
    Modality,
    OccupancyEvidence,
    classify_evidence_status,
)
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
    source_statuses: dict[str, str] = field(default_factory=dict)
    occupancy_records: tuple[OccupancyEvidence, ...] = ()

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
        *,
        event_id: str | None = None,
        allow_stale_detection_backfill: bool = False,
        max_stale_age_s: float | None = None,
    ) -> None:
        self.tracker = source_tracker if source_tracker is not None else SourceTracker()
        self.aligner = sync_aligner
        self.window_tolerance_s = float(window_tolerance_s)
        self.event_id = event_id
        self.allow_stale_detection_backfill = bool(allow_stale_detection_backfill)
        self.max_stale_age_s = float(max_stale_age_s) if max_stale_age_s is not None else None
        self._buffer: deque[tuple[float, EvidenceRecord]] = deque()
        self._occupancy_buffer: deque[tuple[float, OccupancyEvidence]] = deque()
        # Per-source last-ingested master timestamp, used to reject duplicate
        # and out-of-order observations at ingestion time (not merely at the
        # SourceTracker health-state layer). Keyed by source_id (or "occ::<id>").
        self._last_ingested_master_t: dict[str, float] = {}
        self._consumed_keys: set[tuple[str, str, float]] = set()
        self._consumed_occupancy_keys: set[tuple[str, float]] = set()
        # Registered initial sources (before any observations) for causal replay.
        self._registered_specs: dict[str, tuple[str, Modality, float, str | None, str | None]] = {
            src_id: (st.role, st.modality, st.timeout_s, st.camera_id, st.event_id)
            for src_id, st in self.tracker.sources.items()
            if st.registered
        }
        # Audit log of every rejected observation.
        self.rejected_observations: list[dict[str, object]] = []

    def reset(self, event_id: str | None = None) -> None:
        """Clear buffered evidence and tracker state to prevent cross-event leakage."""
        self.event_id = event_id
        self._buffer.clear()
        self._occupancy_buffer.clear()
        self._last_ingested_master_t.clear()
        self._consumed_keys.clear()
        self._consumed_occupancy_keys.clear()
        self.rejected_observations.clear()
        self.tracker = SourceTracker(
            default_timeout_s=self.tracker.default_timeout_s,
            confirmation_frames=self.tracker.confirmation_frames,
            recovery_hold_s=self.tracker.recovery_hold_s,
        )
        for src_id, (role, modality, timeout_s, cam_id, ev_id) in self._registered_specs.items():
            self.tracker.register_source(
                source_id=src_id,
                role=role,
                modality=modality,
                timeout_s=timeout_s,
                camera_id=cam_id,
                event_id=event_id if event_id is not None else ev_id,
            )

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

        Enforces:
        - Event-boundary isolation when ``self.event_id`` is configured.
        - R04 fail-closed dual-camera synchronization when an aligner is attached.
        - Per-source strictly increasing monotonic master-clock ordering.
        """
        if self.event_id is not None:
            meta_ev = record.metadata.get("event_id")
            if meta_ev is None and isinstance(record.metadata.get("provenance"), dict):
                meta_ev = record.metadata["provenance"].get("event_id")
            if meta_ev is not None and str(meta_ev) != self.event_id:
                self._reject(record, float(record.timestamp_s), "cross_event_leakage")
                return

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

        if not math.isfinite(master_t):
            raise ValueError(f"master timestamp must be finite, got {master_t!r}")

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

    def add_occupancy(self, occupancy: OccupancyEvidence) -> None:
        """Ingest a crossing occupancy observation with event and monotonic checks."""
        if self.event_id is not None:
            meta_ev = occupancy.metadata.get("event_id")
            if meta_ev is not None and str(meta_ev) != self.event_id:
                self.rejected_observations.append(
                    {
                        "source_id": occupancy.source_id,
                        "modality": "occupancy",
                        "local_timestamp_s": occupancy.timestamp_s,
                        "attempted_master_timestamp_s": occupancy.timestamp_s,
                        "reason": "cross_event_leakage",
                    }
                )
                return

        master_t = float(occupancy.timestamp_s)
        if not math.isfinite(master_t):
            raise ValueError(f"occupancy timestamp must be finite, got {master_t!r}")
        key = f"occ::{occupancy.source_id}"
        last_t = self._last_ingested_master_t.get(key)
        if last_t is not None:
            if abs(master_t - last_t) < 1e-9:
                self.rejected_observations.append(
                    {
                        "source_id": occupancy.source_id,
                        "modality": "occupancy",
                        "local_timestamp_s": occupancy.timestamp_s,
                        "attempted_master_timestamp_s": master_t,
                        "reason": "duplicate_observation",
                    }
                )
                return
            if master_t < last_t - 1e-9:
                self.rejected_observations.append(
                    {
                        "source_id": occupancy.source_id,
                        "modality": "occupancy",
                        "local_timestamp_s": occupancy.timestamp_s,
                        "attempted_master_timestamp_s": master_t,
                        "reason": "out_of_order_observation",
                    }
                )
                return
        self._last_ingested_master_t[key] = master_t
        self._occupancy_buffer.append((master_t, occupancy))

    def add_evidence_batch(
        self, records: list[EvidenceRecord], preserve_arrival_order: bool = False
    ) -> None:
        """Ingest a batch of records (sorted by default, or in arrival order when requested)."""
        ordered = list(records) if preserve_arrival_order else sorted(records, key=lambda r: r.timestamp_s)
        for rec in ordered:
            self.add_evidence(rec)

    def _assemble_snapshot(
        self,
        current_master_time_s: float,
        *,
        tracker: SourceTracker,
        consumed_keys: set[tuple[str, str, float]],
        consumed_occ_keys: set[tuple[str, float]],
        purge_older_than_s: float | None = None,
    ) -> MultimodalFrame:
        t_min = current_master_time_s - self.window_tolerance_s
        t_max = current_master_time_s + 1e-6

        vision_records: list[EvidenceRecord] = []
        audio_records: list[EvidenceRecord] = []
        occupancy_records: list[OccupancyEvidence] = []
        fresh_by_source: dict[str, EvidenceRecord] = {}

        if self.allow_stale_detection_backfill:
            for master_t, rec in self._buffer:
                if t_min <= master_t <= t_max:
                    fresh_by_source[rec.source_id] = rec
                    if rec.modality == Modality.VISION:
                        vision_records.append(rec)
                    elif rec.modality == Modality.AUDIO:
                        audio_records.append(rec)
            for master_t, occ in self._occupancy_buffer:
                if t_min <= master_t <= t_max:
                    occupancy_records.append(occ)
        else:
            latest_by_source_mod: dict[tuple[str, Modality], tuple[float, EvidenceRecord]] = {}
            for master_t, rec in self._buffer:
                if t_min <= master_t <= t_max:
                    key = (rec.source_id, rec.modality)
                    prev = latest_by_source_mod.get(key)
                    if prev is None or master_t > prev[0]:
                        latest_by_source_mod[key] = (master_t, rec)

            for (_, _), (master_t, rec) in sorted(
                latest_by_source_mod.items(), key=lambda item: (item[1][0], item[0][0])
            ):
                obs_key = (rec.source_id, rec.modality.value, round(master_t, 9))
                if obs_key in consumed_keys:
                    continue
                consumed_keys.add(obs_key)
                fresh_by_source[rec.source_id] = rec
                if rec.modality == Modality.VISION:
                    vision_records.append(rec)
                elif rec.modality == Modality.AUDIO:
                    audio_records.append(rec)

            latest_occ: dict[str, tuple[float, OccupancyEvidence]] = {}
            for master_t, occ in self._occupancy_buffer:
                if t_min <= master_t <= t_max:
                    prev_occ = latest_occ.get(occ.source_id)
                    if prev_occ is None or master_t > prev_occ[0]:
                        latest_occ[occ.source_id] = (master_t, occ)
            for src_id, (master_t, occ) in sorted(latest_occ.items(), key=lambda x: x[1][0]):
                occ_key = (src_id, round(master_t, 9))
                if occ_key in consumed_occ_keys:
                    continue
                consumed_occ_keys.add(occ_key)
                occupancy_records.append(occ)

        if purge_older_than_s is not None:
            cutoff = current_master_time_s - purge_older_than_s
            if self._buffer and any(mt < cutoff for mt, _ in self._buffer):
                self._buffer = deque(item for item in self._buffer if item[0] >= cutoff)
            if self._occupancy_buffer and any(mt < cutoff for mt, _ in self._occupancy_buffer):
                self._occupancy_buffer = deque(
                    item for item in self._occupancy_buffer if item[0] >= cutoff
                )

        availability = tracker.get_availability_map(current_master_time_s)
        health_map = tracker.get_health_map(current_master_time_s)
        reason_map = tracker.get_reason_map(current_master_time_s)
        age_map = tracker.get_age_map(current_master_time_s)
        active = tuple(src for src, avail in availability.items() if avail)
        missing = tuple(src for src, avail in availability.items() if not avail)

        stale_threshold = self.max_stale_age_s if self.max_stale_age_s is not None else tracker.default_timeout_s
        all_sources = set(availability) | set(fresh_by_source)
        status_map: dict[str, str] = {}
        for src in sorted(all_sources):
            fresh = fresh_by_source.get(src)
            contradictory = bool(fresh is not None and fresh.metadata.get("contradictory", False))
            status_map[src] = str(
                classify_evidence_status(
                    fresh_record=fresh,
                    health=health_map.get(src),
                    health_reason=reason_map.get(src),
                    age_s=age_map.get(src),
                    stale_after_s=stale_threshold,
                    contradictory=contradictory,
                ).value
            )

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
            source_statuses=status_map,
            occupancy_records=tuple(occupancy_records),
        )

    def collect_frame(
        self, current_master_time_s: float, purge_older_than_s: float = 5.0
    ) -> MultimodalFrame:
        """Assemble a MultimodalFrame aligned to current_master_time_s."""
        return self._assemble_snapshot(
            current_master_time_s,
            tracker=self.tracker,
            consumed_keys=self._consumed_keys,
            consumed_occ_keys=self._consumed_occupancy_keys,
            purge_older_than_s=purge_older_than_s,
        )

    def generate_frames_from_history(
        self,
        start_time_s: float,
        end_time_s: float,
        stride_s: float = 0.1,
    ) -> list[MultimodalFrame]:
        """Replay recorded buffer over [start_time_s, end_time_s] with fixed stride.

        When ``allow_stale_detection_backfill`` is False (default causal mode),
        ``SourceTracker`` state is replayed strictly chronologically up to each
        master tick ``t`` so future observations never mask earlier outages or
        mutate early health ages.
        """
        frames: list[MultimodalFrame] = []
        t = float(start_time_s)
        if self.allow_stale_detection_backfill:
            while t <= end_time_s + 1e-9:
                frame = self._build_frame_at(t)
                frames.append(frame)
                t += stride_s
            return frames

        replay_tracker = SourceTracker(
            default_timeout_s=self.tracker.default_timeout_s,
            confirmation_frames=self.tracker.confirmation_frames,
            recovery_hold_s=self.tracker.recovery_hold_s,
        )
        for src_id, (role, modality, timeout_s, cam_id, ev_id) in self._registered_specs.items():
            replay_tracker.register_source(
                source_id=src_id,
                role=role,
                modality=modality,
                timeout_s=timeout_s,
                camera_id=cam_id,
                event_id=self.event_id if self.event_id is not None else ev_id,
            )

        ordered = sorted(
            self._buffer,
            key=lambda item: (item[0], str(item[1].modality.value), item[1].source_id),
        )
        cursor = 0
        replay_consumed: set[tuple[str, str, float]] = set()
        replay_occ_consumed: set[tuple[str, float]] = set()
        while t <= end_time_s + 1e-9:
            while cursor < len(ordered) and ordered[cursor][0] <= t + 1e-6:
                mt, rec = ordered[cursor]
                replay_tracker.record_observation(
                    source_id=rec.source_id,
                    timestamp_s=mt,
                    available=rec.available,
                    detections=rec.detections,
                    metadata=rec.metadata,
                )
                cursor += 1
            frame = self._assemble_snapshot(
                t,
                tracker=replay_tracker,
                consumed_keys=replay_consumed,
                consumed_occ_keys=replay_occ_consumed,
                purge_older_than_s=None,
            )
            frames.append(frame)
            t += stride_s
        return frames

    def _build_frame_at(self, current_master_time_s: float) -> MultimodalFrame:
        return self._assemble_snapshot(
            current_master_time_s,
            tracker=self.tracker,
            consumed_keys=self._consumed_keys,
            consumed_occ_keys=self._consumed_occupancy_keys,
            purge_older_than_s=None,
        )
