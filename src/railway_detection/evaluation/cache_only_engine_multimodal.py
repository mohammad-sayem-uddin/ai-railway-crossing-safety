"""Mission 3 extension: full-multimodal cache-only replay (back camera).

The frozen :class:`CacheOnlyReplayEngine` supports only the front streams
(conditions B0/B1/B2). This subclass adds the back-camera stream and the
full-multimodal conditions without modifying the frozen module, so the
original B0-B2 behaviour stays byte-identical for reproducibility:

  BACK_VISION        back vision only                     (Protocol V2 B1)
  DUAL_VISION        front + back vision                  (Protocol V2 B2,
                                                           vision component)
  DUAL_VISION_AUDIO  front + back vision + front audio    (Protocol V2 B7)

(For clarity: the frozen engine's own labels map to Protocol V2 as
B0->B0, B1->B3 (audio only), B2->B4 (front vision + audio).)

Rules enforced here, mirroring the frozen engine's fail-closed posture:

* Back records are validated at load; two serializations are accepted and
  normalized -- the raw detector schema used for front caches
  (``frame_index``/``timestamp_sec``/``camera_id == "camera_back"``) and the
  EvidenceRecord serialization produced by the Mission 39 back run
  (``timestamp_s``/``source_id == "camera_2"``/``modality == "vision"``).
  Where PTS metadata is present, the PTS/timestamp identity proof applied
  to front records is applied identically.
* DUAL_* conditions refuse to run without a SyncAligner that registers BOTH
  cameras (R04: never silently assume a zero offset for a real source).
* The frame-generation window is computed on MASTER (aligned) timestamps,
  fixing the truncation defect in which evidence shifted by a camera offset
  fell outside the raw-timestamp window (same family as the Phase 10.1
  naive-duration defect).
* The descriptive-execution gate is invoked exactly as in the frozen
  engine, with the requested condition passed through; nothing here weakens
  or bypasses it.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace
from fractions import Fraction
from typing import Any

from railway_detection.data.sync import SyncAligner
from railway_detection.evaluation import cache_only_engine as _base
from railway_detection.evaluation.cache_only_engine import (
    CacheIntegrityError,
    CacheOnlyReplayEngine,
    CacheReplayRefusal,
    ReplayOutput,
)
from railway_detection.fusion.collector import MultimodalEvidenceCollector
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.simulation.runner import EventSimulationRunner

BACK_SOURCE_ID = "camera_2"

MM_SOURCE_IDS: dict[str, str] = {**_base.SOURCE_IDS, "back_vision": BACK_SOURCE_ID}

MM_CONDITION_STREAMS: dict[str, frozenset[str]] = {
    **_base.CONDITION_STREAMS,
    "BACK_VISION": frozenset({"back_vision"}),
    "DUAL_VISION": frozenset({"front_vision", "back_vision"}),
    "DUAL_VISION_AUDIO": frozenset({"front_vision", "back_vision", "front_audio"}),
}

MM_SUPPORTED_CONDITIONS = frozenset(MM_CONDITION_STREAMS)

#: New condition name -> Protocol V2 baseline it realizes.
PROTOCOL_V2_CONDITION = {
    "BACK_VISION": "B1",
    "DUAL_VISION": "B2",
    "DUAL_VISION_AUDIO": "B7",
}

DUAL_CONDITIONS = frozenset({"DUAL_VISION", "DUAL_VISION_AUDIO"})


def _validate_detections(detections_raw: Any, index: int, frame_index: int) -> list[Detection]:
    """Validate a detections list in either cache serialization."""
    if not isinstance(detections_raw, list):
        raise CacheReplayRefusal(
            f"Back visual record [{index}]: detections must be a list", code="RECORD_INVALID"
        )
    detections: list[Detection] = []
    for det_idx, det in enumerate(detections_raw):
        if not isinstance(det, dict):
            raise CacheReplayRefusal(
                f"Back visual record [{index}].detections[{det_idx}]: not a dict",
                code="RECORD_INVALID",
            )
        label = det.get("label", det.get("class_name"))
        if not isinstance(label, str) or not label.strip():
            raise CacheReplayRefusal(
                f"Back visual record [{index}].detections[{det_idx}]: "
                "label/class_name must be a non-empty string",
                code="RECORD_INVALID_CLASS",
            )
        confidence = det.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise CacheReplayRefusal(
                f"Back visual record [{index}].detections[{det_idx}]: confidence must be numeric",
                code="RECORD_INVALID",
            )
        confidence = float(confidence)
        if not math.isfinite(confidence) or confidence < 0.0 or confidence > 1.0:
            raise CacheReplayRefusal(
                f"Back visual record [{index}].detections[{det_idx}]: confidence must be in [0,1]",
                code="RECORD_INVALID_CONFIDENCE",
            )
        bbox = det.get("bbox_xyxy")
        bbox_tuple: tuple[float, float, float, float] | None = None
        if bbox is not None:
            if not isinstance(bbox, list) or len(bbox) != 4 or any(
                isinstance(c, bool) or not isinstance(c, (int, float)) or not math.isfinite(c)
                for c in bbox
            ):
                raise CacheReplayRefusal(
                    f"Back visual record [{index}].detections[{det_idx}]: "
                    "bbox_xyxy must be 4 finite numbers",
                    code="RECORD_INVALID",
                )
            bbox_tuple = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
        det_meta: dict[str, Any] = {"frame_index": frame_index}
        if isinstance(det.get("class_id"), int) and not isinstance(det.get("class_id"), bool):
            det_meta["class_id"] = det["class_id"]
        detections.append(
            Detection(label=label, confidence=confidence, bbox_xyxy=bbox_tuple, metadata=det_meta)
        )
    return detections


def _check_pts_identity(clock: Any, timestamp: float, frame_index: int, index: int) -> dict[str, Any]:
    """Mirror the frozen engine's PTS/timestamp identity proof for back records."""
    metadata: dict[str, Any] = {}
    if isinstance(clock, dict) and clock.get("timestamp_basis") == "source_pts":
        pts, tb, stream = clock.get("pts_ticks"), clock.get("timebase"), clock.get("stream_index")
        if (
            type(pts) is not int
            or pts < 0
            or not isinstance(tb, list)
            or len(tb) != 2
            or any(type(x) is not int or x <= 0 for x in tb)
            or type(stream) is not int
            or stream < 0
        ):
            raise CacheReplayRefusal("invalid original PTS metadata", code="RECORD_INVALID")
        if float(pts * Fraction(*tb)) != timestamp:
            raise CacheReplayRefusal("PTS/timestamp mismatch", code="RECORD_INVALID_TIMESTAMP")
        if (
            clock.get("stream_start_pts") is not None
            and type(clock["stream_start_pts"]) is not int
        ) or clock.get("frame_index", frame_index) != frame_index:
            raise CacheReplayRefusal("PTS/frame identity mismatch", code="RECORD_INVALID")
        metadata.update(
            {
                key: clock.get(key)
                for key in (
                    "timestamp_basis",
                    "pts_ticks",
                    "timebase",
                    "stream_index",
                    "stream_start_pts",
                )
            }
        )
    return metadata


def _validate_back_visual_record(record: Any, index: int) -> EvidenceRecord:
    """Validate a back-camera cache record in either serialization."""
    if not isinstance(record, dict):
        raise CacheReplayRefusal(f"Back visual record [{index}] is not a dict", code="RECORD_INVALID")

    if "timestamp_s" in record or "source_id" in record:
        # EvidenceRecord serialization (Mission 39 back run).
        required = {"timestamp_s", "source_id", "modality", "available", "detections"}
        missing = required - set(record)
        if missing:
            raise CacheReplayRefusal(
                f"Back visual record [{index}] missing required fields: {sorted(missing)}",
                code="RECORD_MISSING_FIELDS",
            )
        if record["source_id"] != BACK_SOURCE_ID:
            raise CacheReplayRefusal(
                f"Back visual record [{index}]: unsupported source_id {record['source_id']!r}; "
                "back cache records must declare camera_2",
                code="RECORD_INVALID_SOURCE",
            )
        if record["modality"] != "vision":
            raise CacheReplayRefusal(
                f"Back visual record [{index}]: modality must be 'vision'", code="RECORD_INVALID"
            )
        timestamp = record["timestamp_s"]
        available = record["available"]
        clock = record.get("metadata", {})
        frame_index_raw = clock.get("frame_index", index) if isinstance(clock, dict) else index
        record_format = "evidence_record"
    elif "timestamp_sec" in record or "camera_id" in record:
        # Raw detector serialization (same family as the front caches).
        required = {"frame_index", "timestamp_sec", "camera_id", "detections"}
        missing = required - set(record)
        if missing:
            raise CacheReplayRefusal(
                f"Back visual record [{index}] missing required fields: {sorted(missing)}",
                code="RECORD_MISSING_FIELDS",
            )
        if record["camera_id"] != "camera_back":
            raise CacheReplayRefusal(
                f"Back visual record [{index}]: unsupported camera_id {record['camera_id']!r}; "
                "back cache records must declare camera_back",
                code="RECORD_INVALID_SOURCE",
            )
        timestamp = record["timestamp_sec"]
        available = True
        clock = record.get("metadata", {})
        frame_index_raw = record["frame_index"]
        record_format = "raw_detector"
    else:
        raise CacheReplayRefusal(
            f"Back visual record [{index}]: unrecognized serialization "
            "(neither EvidenceRecord nor raw detector schema)",
            code="RECORD_MISSING_FIELDS",
        )

    if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
        raise CacheReplayRefusal(
            f"Back visual record [{index}]: timestamp must be numeric", code="RECORD_INVALID"
        )
    timestamp = float(timestamp)
    if not math.isfinite(timestamp) or timestamp < 0.0:
        raise CacheReplayRefusal(
            f"Back visual record [{index}]: timestamp must be finite and non-negative",
            code="RECORD_INVALID_TIMESTAMP",
        )
    if not isinstance(available, bool):
        raise CacheReplayRefusal(
            f"Back visual record [{index}]: available must be boolean", code="RECORD_INVALID"
        )
    if isinstance(frame_index_raw, bool) or not isinstance(frame_index_raw, int) or frame_index_raw < 0:
        raise CacheReplayRefusal(
            f"Back visual record [{index}]: frame_index must be a non-negative integer",
            code="RECORD_INVALID",
        )
    frame_index = int(frame_index_raw)

    detections = _validate_detections(record["detections"], index, frame_index)
    if not available and detections:
        raise CacheReplayRefusal(
            f"Back visual record [{index}]: unavailable record carries detections",
            code="RECORD_INVALID",
        )

    metadata: dict[str, Any] = {
        "camera_id": "camera_back",
        "frame_index": frame_index,
        "record_format": record_format,
    }
    metadata.update(_check_pts_identity(clock, timestamp, frame_index, index))
    return EvidenceRecord(
        timestamp_s=timestamp,
        source_id=BACK_SOURCE_ID,
        modality=Modality.VISION,
        available=available,
        detections=tuple(detections),
        metadata=metadata,
    )


class MultimodalCacheOnlyReplayEngine(CacheOnlyReplayEngine):
    """Cache-only replay with the back-camera stream and DUAL_* conditions."""

    def _validate_event_entry(self, event_key: str, event_entry: Any) -> None:
        super()._validate_event_entry(event_key, event_entry)
        if isinstance(event_entry, dict) and "back_vision_cache" in event_entry:
            cache_info = event_entry["back_vision_cache"]
            if not isinstance(cache_info, dict):
                raise CacheIntegrityError(
                    f"Event '{event_key}'.back_vision_cache must be a JSON object",
                    code="MANIFEST_INVALID_CACHE_ENTRY",
                )
            for field in ("path", "sha256", "line_count", "byte_size"):
                if field not in cache_info:
                    raise CacheIntegrityError(
                        f"Event '{event_key}'.back_vision_cache missing field: {field}",
                        code="MANIFEST_INVALID_CACHE_ENTRY",
                    )

    def load_back_visual_records(self, event_id: str) -> list[EvidenceRecord]:
        """Load validated back-camera evidence records for an event."""
        entry = self._get_event_entry(event_id)
        if "back_vision_cache" not in entry:
            raise CacheReplayRefusal(
                "selected condition requires an actual back-vision cache",
                code="CONDITION_STREAM_MISSING",
                event_id=event_id,
            )
        cache_info = entry["back_vision_cache"]
        raw_records = self._load_cache_stream(cache_info, event_id, "back_vision")
        provenance = {
            "event_id": event_id,
            "stream": "back_vision",
            "artifact_path": cache_info["path"],
            "artifact_sha256": cache_info["sha256"],
        }
        records = [
            _validate_back_visual_record(raw, idx) for idx, raw in enumerate(raw_records)
        ]
        return [
            replace(record, metadata={**record.metadata, "provenance": provenance})
            for record in records
        ]

    def execute_replay(
        self,
        event_id: str,
        condition: str,
        *,
        decision_engine: MultimodalDecisionEngine | None = None,
        sync_aligner: SyncAligner | None = None,
        frame_stride_s: float = 0.2,
    ) -> ReplayOutput:
        """Execute a deterministic cache-only replay, incl. DUAL_* conditions."""
        if condition in _base.SUPPORTED_CONDITIONS:
            return super().execute_replay(
                event_id,
                condition,
                decision_engine=decision_engine,
                sync_aligner=sync_aligner,
                frame_stride_s=frame_stride_s,
            )
        if condition not in MM_SUPPORTED_CONDITIONS:
            raise CacheReplayRefusal(
                f"Condition '{condition}' not supported. Must be one of "
                f"{sorted(MM_SUPPORTED_CONDITIONS)}",
                code="UNSUPPORTED_CONDITION",
                event_id=event_id,
            )

        # Operation-boundary gate: identical to the frozen engine; the
        # requested condition is passed through unchanged.
        from railway_detection.evaluation.descriptive_exec_gate import (
            require_descriptive_authorization_for_engine,
        )

        require_descriptive_authorization_for_engine(
            self.repo_root,
            condition=condition,
            event_id=event_id,
            manifest_sha256=self._manifest_sha256,
        )

        if isinstance(frame_stride_s, bool) or not isinstance(frame_stride_s, (int, float)):
            raise CacheReplayRefusal(
                "frame_stride_s must be numeric and positive",
                code="INVALID_FRAME_STRIDE",
                event_id=event_id,
            )
        frame_stride_s = float(frame_stride_s)
        if not math.isfinite(frame_stride_s) or frame_stride_s <= 0.0:
            raise CacheReplayRefusal(
                "frame_stride_s must be finite and positive",
                code="INVALID_FRAME_STRIDE",
                event_id=event_id,
            )

        if condition in DUAL_CONDITIONS:
            registered = set(sync_aligner.offsets_s) if sync_aligner is not None else set()
            if not {_base.SOURCE_IDS["front_vision"], BACK_SOURCE_ID} <= registered:
                raise CacheReplayRefusal(
                    f"Condition '{condition}' requires a SyncAligner registering both "
                    "camera_1 and camera_2 (R04 fail-closed: no assumed zero offset)",
                    code="SYNC_ALIGNMENT_REQUIRED",
                    event_id=event_id,
                )

        required_streams = MM_CONDITION_STREAMS[condition]
        all_records: list[EvidenceRecord] = []

        if "front_vision" in required_streams:
            vision_records = self.load_visual_records(event_id)
            if not vision_records:
                raise CacheReplayRefusal(
                    f"Event '{event_id}' has no valid visual records",
                    code="EMPTY_EVIDENCE",
                    event_id=event_id,
                )
            all_records.extend(vision_records)

        if "back_vision" in required_streams:
            back_records = self.load_back_visual_records(event_id)
            if not back_records:
                raise CacheReplayRefusal(
                    f"Event '{event_id}' has no valid back visual records",
                    code="EMPTY_EVIDENCE",
                    event_id=event_id,
                )
            all_records.extend(back_records)

        if "front_audio" in required_streams:
            audio_records = self.load_audio_records(event_id)
            if not audio_records:
                raise CacheReplayRefusal(
                    f"Event '{event_id}' has no valid audio records",
                    code="EMPTY_EVIDENCE",
                    event_id=event_id,
                )
            all_records.extend(audio_records)

        if not all_records:
            raise CacheReplayRefusal(
                f"Event '{event_id}' produced no evidence records for condition {condition}",
                code="EMPTY_EVIDENCE",
                event_id=event_id,
            )

        all_records = self._deterministic_sort(all_records)

        collector = MultimodalEvidenceCollector(
            sync_aligner=sync_aligner, window_tolerance_s=0.5
        )
        for record in all_records:
            collector.add_evidence(record)

        # Master-time window: records shifted by a camera offset must remain
        # inside the generated frame range (frozen engine used raw bounds).
        master_times = [
            sync_aligner.to_master(r.source_id, r.timestamp_s)
            if (sync_aligner is not None and r.source_id in sync_aligner.offsets_s)
            else r.timestamp_s
            for r in all_records
        ]
        t_start, t_end = min(master_times), max(master_times)

        frames = collector.generate_frames_from_history(
            start_time_s=t_start, end_time_s=t_end, stride_s=frame_stride_s
        )
        if not frames:
            raise CacheReplayRefusal(
                f"Event '{event_id}' produced no frames for condition {condition}",
                code="NO_FRAMES_GENERATED",
                event_id=event_id,
            )

        if decision_engine is None:
            decision_engine = MultimodalDecisionEngine()

        runner = EventSimulationRunner(decision_engine=decision_engine)
        result = runner.run_frames(
            frames=frames,
            event_id=event_id,
            scenario_name=f"cache_only_{condition}",
        )

        sync_summary = sync_aligner.alignment_summary() if sync_aligner else None
        replay_config = {
            "condition": condition,
            "frame_stride_s": frame_stride_s,
            "window_tolerance_s": 0.5,
            "sync": sync_summary,
        }
        config_bytes = json.dumps(replay_config, sort_keys=True, separators=(",", ":")).encode()
        deterministic_run_id = hashlib.sha256(
            self._manifest_sha256.encode() + b":" + event_id.encode() + b":" + config_bytes
        ).hexdigest()[:16]

        return ReplayOutput(
            event_id=event_id,
            condition=condition,
            result=result,
            frames_produced=len(frames),
            evidence_records_loaded=len(all_records),
            manifest_sha256=self._manifest_sha256,
            deterministic_run_id=deterministic_run_id,
            provenance={
                "manifest_sha256": self._manifest_sha256,
                "condition": condition,
                "protocol_v2_condition": PROTOCOL_V2_CONDITION.get(condition),
                "frame_stride_s": frame_stride_s,
                "sync": sync_summary,
                "cache_paths": {
                    stream: self._get_event_entry(event_id)[f"{stream}_cache"]["path"]
                    for stream in required_streams
                },
            },
        )
