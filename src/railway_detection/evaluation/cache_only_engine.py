"""Fail-Closed Cache-Only Replay Engine for Train Gate Automation.

Implements the architecture specified in ``docs/CACHE_ONLY_REPLAY_DESIGN.md``.
Consumes only pre-computed JSONL cache artifacts referenced by a hash-bound
manifest. Never opens, decodes, or references raw media files.

Safety invariants enforced:
- ``INV-CACHE-1`` (Zero Fallback): no references to cv2, av, ffmpeg.
- ``INV-CACHE-2`` (Extension Blacklisting): media extensions trigger refusal.
- ``INV-CACHE-3`` (Hash Gate): SHA-256 verified before any record is parsed.
- ``INV-CACHE-4`` (Isolated Outputs): writes only to the designated output dir.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from dataclasses import dataclass, field, replace
from fractions import Fraction
from pathlib import Path
from typing import Any

from railway_detection.data.sync import SyncAligner
from railway_detection.fusion.collector import MultimodalEvidenceCollector
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.safety import path_identity as pid
from railway_detection.simulation.runner import EventSimulationRunner


# JSON object parser that refuses duplicate keys rather than silently keeping
# the last value. Duplicate keys can otherwise hide conflicting identifiers or
# integrity metadata in a supposedly hash-bound artifact.
def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


class CacheIntegrityError(Exception):
    """Cache file missing, corrupt, or fails hash verification."""

    def __init__(self, message: str, *, code: str = "CACHE_INTEGRITY_ERROR") -> None:
        self.code = code
        super().__init__(message)


class MediaAccessViolationError(Exception):
    """Attempt to ingest, reference, or decode raw media files."""

    def __init__(self, message: str, *, code: str = "MEDIA_ACCESS_VIOLATION") -> None:
        self.code = code
        super().__init__(message)


class CacheReplayRefusal(Exception):
    """Structured refusal for invalid inputs that cannot produce evidence."""

    def __init__(self, message: str, *, code: str, event_id: str | None = None) -> None:
        self.code = code
        self.event_id = event_id
        super().__init__(message)


PROHIBITED_EXTENSIONS = frozenset({
    ".mov", ".mp4", ".avi", ".mkv", ".wav", ".aac", ".flac",
    ".m4a", ".mp3", ".ogg", ".webm", ".wmv", ".flv",
})

ALLOWED_CACHE_EXTENSIONS = frozenset({".jsonl"})
MANIFEST_SCHEMA_VERSION = "1.0.0"
SUPPORTED_CONDITIONS = frozenset({"B0", "B1", "B2"})

CONDITION_STREAMS: dict[str, frozenset[str]] = {
    "B0": frozenset({"front_vision"}),
    "B1": frozenset({"front_audio"}),
    "B2": frozenset({"front_vision", "front_audio"}),
}

SOURCE_IDS: dict[str, str] = {
    "front_vision": "camera_1",
    "front_audio": "audio_1",
}


def _validate_cache_path(path_str: str, repo_root: Path) -> Path:
    """Validate a cache artifact path against the repository boundary.

    Rejects absolute paths, traversal components, paths that resolve outside
    repo_root (symlink escape), prohibited media extensions, and disallowed
    cache extensions.
    """
    if not isinstance(path_str, str) or not path_str.strip():
        raise CacheReplayRefusal(
            "Cache path must be a non-empty string", code="INVALID_CACHE_PATH"
        )

    path_obj = Path(path_str)
    if path_obj.is_absolute():
        raise CacheReplayRefusal(
            f"Absolute cache path rejected: {path_str}", code="ABSOLUTE_PATH_REJECTED"
        )
    if ".." in path_obj.parts:
        raise CacheReplayRefusal(
            f"Path traversal rejected: {path_str}", code="PATH_TRAVERSAL_REJECTED"
        )

    suffix = path_obj.suffix.lower()
    if suffix in PROHIBITED_EXTENSIONS:
        raise MediaAccessViolationError(
            f"Media Access Violation: prohibited extension '{suffix}' in cache path: {path_str}"
        )
    if suffix not in ALLOWED_CACHE_EXTENSIONS:
        raise CacheReplayRefusal(
            f"Disallowed cache file extension '{suffix}': {path_str}",
            code="DISALLOWED_EXTENSION",
        )

    try:
        resolved = pid.canonical_path(Path(repo_root) / path_obj)
        inside = pid.is_within(resolved, repo_root, include_root=False)
    except pid.PathIdentityError as exc:
        raise CacheReplayRefusal(
            f"Cache path could not be canonicalised: {path_str}", code="PATH_ESCAPE_REJECTED"
        ) from exc
    # ``canonical_path`` has already resolved every symlink, so a link that points out of the root
    # lands outside it here; containment is judged by filesystem identity (case-insensitive safe).
    if not inside:
        raise CacheReplayRefusal(
            f"Cache path escapes repository root: {path_str}", code="PATH_ESCAPE_REJECTED"
        )

    return resolved


def _assert_no_media_references(data: Any, context: str = "manifest") -> None:
    """Recursively scan data structures for prohibited media references."""
    if isinstance(data, str):
        lower_str = data.lower()
        for ext in PROHIBITED_EXTENSIONS:
            if lower_str.endswith(ext) or f"{ext}." in lower_str:
                raise MediaAccessViolationError(
                    f"Media Access Violation in {context}: prohibited media reference "
                    f"detected: '{data}'. Replay must consume feature cache files only."
                )
    elif isinstance(data, dict):
        for key, value in data.items():
            _assert_no_media_references(key, context)
            _assert_no_media_references(value, context)
    elif isinstance(data, list | tuple):
        for item in data:
            _assert_no_media_references(item, context)


def _validate_visual_record(record: Any, index: int) -> EvidenceRecord:
    """Validate a visual detection cache record and produce an EvidenceRecord."""
    if not isinstance(record, dict):
        raise CacheReplayRefusal(
            f"Visual record [{index}] is not a dict", code="RECORD_INVALID"
        )

    required = {"frame_index", "timestamp_sec", "camera_id", "detections"}
    missing = required - set(record)
    if missing:
        raise CacheReplayRefusal(
            f"Visual record [{index}] missing required fields: {sorted(missing)}",
            code="RECORD_MISSING_FIELDS",
        )

    frame_index = record["frame_index"]
    if isinstance(frame_index, bool) or not isinstance(frame_index, int) or frame_index < 0:
        raise CacheReplayRefusal(
            f"Visual record [{index}]: frame_index must be non-negative integer",
            code="RECORD_INVALID",
        )

    timestamp = record["timestamp_sec"]
    if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
        raise CacheReplayRefusal(
            f"Visual record [{index}]: timestamp_sec must be numeric",
            code="RECORD_INVALID",
        )
    timestamp = float(timestamp)
    if not math.isfinite(timestamp) or timestamp < 0.0:
        raise CacheReplayRefusal(
            f"Visual record [{index}]: timestamp_sec must be finite and non-negative",
            code="RECORD_INVALID_TIMESTAMP",
        )

    camera_id = record["camera_id"]
    if camera_id != "camera_front":
        raise CacheReplayRefusal(
            f"Visual record [{index}]: unsupported camera_id {camera_id!r}; "
            "front cache records must declare camera_front",
            code="RECORD_INVALID_SOURCE",
        )

    detections_raw = record["detections"]
    if not isinstance(detections_raw, list):
        raise CacheReplayRefusal(
            f"Visual record [{index}]: detections must be a list",
            code="RECORD_INVALID",
        )

    detections: list[Detection] = []
    for det_idx, det in enumerate(detections_raw):
        if not isinstance(det, dict):
            raise CacheReplayRefusal(
                f"Visual record [{index}].detections[{det_idx}]: not a dict",
                code="RECORD_INVALID",
            )
        det_required = {"class_id", "class_name", "confidence", "bbox_xyxy"}
        det_missing = det_required - set(det)
        if det_missing:
            raise CacheReplayRefusal(
                f"Visual record [{index}].detections[{det_idx}] missing: {sorted(det_missing)}",
                code="RECORD_MISSING_FIELDS",
            )
        confidence = det["confidence"]
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise CacheReplayRefusal(
                f"Visual record [{index}].detections[{det_idx}]: confidence must be numeric",
                code="RECORD_INVALID",
            )
        confidence = float(confidence)
        if not math.isfinite(confidence) or confidence < 0.0 or confidence > 1.0:
            raise CacheReplayRefusal(
                f"Visual record [{index}].detections[{det_idx}]: confidence must be in [0,1]",
                code="RECORD_INVALID_CONFIDENCE",
            )
        bbox = det["bbox_xyxy"]
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise CacheReplayRefusal(
                f"Visual record [{index}].detections[{det_idx}]: bbox_xyxy must have 4 elements",
                code="RECORD_INVALID",
            )
        for coord in bbox:
            is_bad_coord = (
                isinstance(coord, bool)
                or not isinstance(coord, (int, float))
                or not math.isfinite(coord)
            )
            if is_bad_coord:
                raise CacheReplayRefusal(
                    f"Visual record [{index}].detections[{det_idx}]: "
                    "bbox coordinates must be finite",
                    code="RECORD_INVALID",
                )

        class_id = det["class_id"]
        class_name = det["class_name"]
        if isinstance(class_id, bool) or not isinstance(class_id, int) or class_id < 0:
            raise CacheReplayRefusal(
                f"Visual record [{index}].detections[{det_idx}]: "
                "class_id must be non-negative integer",
                code="RECORD_INVALID_CLASS",
            )
        if not isinstance(class_name, str) or not class_name.strip():
            raise CacheReplayRefusal(
                f"Visual record [{index}].detections[{det_idx}]: "
                "class_name must be non-empty string",
                code="RECORD_INVALID_CLASS",
            )

        detections.append(Detection(
            label=class_name,
            confidence=confidence,
            bbox_xyxy=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
            metadata={"class_id": class_id, "frame_index": frame_index},
        ))

    metadata: dict[str, Any] = {"camera_id": camera_id, "frame_index": frame_index}
    clock = record.get("metadata", {})
    if isinstance(clock, dict) and clock.get("timestamp_basis") == "source_pts":
        pts, tb, stream = clock.get("pts_ticks"), clock.get("timebase"), clock.get("stream_index")
        if (
            type(pts) is not int or pts < 0
            or not isinstance(tb, list) or len(tb) != 2
            or any(type(x) is not int or x <= 0 for x in tb)
            or type(stream) is not int or stream < 0
        ):
            raise CacheReplayRefusal("invalid original PTS metadata", code="RECORD_INVALID")
        if float(pts * Fraction(*tb)) != timestamp:
            raise CacheReplayRefusal("PTS/timestamp mismatch", code="RECORD_INVALID_TIMESTAMP")
        if (
            (clock.get("stream_start_pts") is not None
             and type(clock["stream_start_pts"]) is not int)
            or clock.get("frame_index", frame_index) != frame_index
        ):
            raise CacheReplayRefusal("PTS/frame identity mismatch", code="RECORD_INVALID")
        metadata.update({key: clock.get(key) for key in (
            "timestamp_basis", "pts_ticks", "timebase", "stream_index", "stream_start_pts"
        )})
    return EvidenceRecord(
        timestamp_s=timestamp,
        source_id=SOURCE_IDS["front_vision"],
        modality=Modality.VISION,
        available=True,
        detections=tuple(detections),
        metadata=metadata,
    )


def _validate_audio_record(record: Any, index: int) -> EvidenceRecord:
    """Validate an audio detection cache record and produce an EvidenceRecord."""
    if not isinstance(record, dict):
        raise CacheReplayRefusal(
            f"Audio record [{index}] is not a dict", code="RECORD_INVALID"
        )

    required = {"window_index", "start_sec", "end_sec", "horn_confidence", "is_horn_detected"}
    missing = required - set(record)
    if missing:
        raise CacheReplayRefusal(
            f"Audio record [{index}] missing required fields: {sorted(missing)}",
            code="RECORD_MISSING_FIELDS",
        )

    window_index = record["window_index"]
    if isinstance(window_index, bool) or not isinstance(window_index, int) or window_index < 0:
        raise CacheReplayRefusal(
            f"Audio record [{index}]: window_index must be non-negative integer",
            code="RECORD_INVALID",
        )

    start_sec = record["start_sec"]
    end_sec = record["end_sec"]
    for name, val in (("start_sec", start_sec), ("end_sec", end_sec)):
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise CacheReplayRefusal(
                f"Audio record [{index}]: {name} must be numeric", code="RECORD_INVALID"
            )
    start_sec = float(start_sec)
    end_sec = float(end_sec)
    if not math.isfinite(start_sec) or start_sec < 0.0:
        raise CacheReplayRefusal(
            f"Audio record [{index}]: start_sec must be finite and non-negative",
            code="RECORD_INVALID_TIMESTAMP",
        )
    if not math.isfinite(end_sec) or end_sec < 0.0:
        raise CacheReplayRefusal(
            f"Audio record [{index}]: end_sec must be finite and non-negative",
            code="RECORD_INVALID_TIMESTAMP",
        )
    if end_sec < start_sec:
        raise CacheReplayRefusal(
            f"Audio record [{index}]: end_sec < start_sec", code="RECORD_INVALID_TIMESTAMP"
        )

    horn_confidence = record["horn_confidence"]
    if isinstance(horn_confidence, bool) or not isinstance(horn_confidence, (int, float)):
        raise CacheReplayRefusal(
            f"Audio record [{index}]: horn_confidence must be numeric", code="RECORD_INVALID"
        )
    horn_confidence = float(horn_confidence)
    if not math.isfinite(horn_confidence) or horn_confidence < 0.0 or horn_confidence > 1.0:
        raise CacheReplayRefusal(
            f"Audio record [{index}]: horn_confidence must be in [0,1]",
            code="RECORD_INVALID_CONFIDENCE",
        )

    is_horn_detected = record["is_horn_detected"]
    if not isinstance(is_horn_detected, bool):
        raise CacheReplayRefusal(
            f"Audio record [{index}]: is_horn_detected must be boolean", code="RECORD_INVALID"
        )

    detections: tuple[Detection, ...] = ()
    if is_horn_detected and horn_confidence > 0.0:
        detections = (Detection(
            label="train_horn",
            confidence=horn_confidence,
            metadata={"window_index": window_index, "start_sec": start_sec},
        ),)

    return EvidenceRecord(
        timestamp_s=end_sec,
        source_id=SOURCE_IDS["front_audio"],
        modality=Modality.AUDIO,
        available=True,
        detections=detections,
        metadata={
            "window_index": window_index,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "is_horn_detected": is_horn_detected,
        },
    )


@dataclass(frozen=True)
class ReplayOutput:
    """Structured output from a successful cache-only replay."""

    event_id: str
    condition: str
    result: Any
    frames_produced: int
    evidence_records_loaded: int
    manifest_sha256: str
    deterministic_run_id: str
    provenance: dict[str, Any] = field(default_factory=dict)
    refusals: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReplayRefusalRecord:
    """Structured refusal when replay cannot proceed."""

    event_id: str
    condition: str
    code: str
    detail: str
    stage: str


class CacheOnlyReplayEngine:
    """Executes B0/B1/B2 replays strictly from pre-computed cache artifacts."""

    def __init__(
        self,
        manifest_path: Path | str,
        repo_root: Path | str = ".",
        output_base_dir: Path | str = "results/replays",
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.manifest_path = Path(manifest_path)
        if not self.manifest_path.is_absolute():
            self.manifest_path = self.repo_root / self.manifest_path
        self.manifest_path = self.manifest_path.resolve()

        try:
            self.manifest_path.relative_to(self.repo_root)
        except ValueError as exc:
            raise CacheReplayRefusal(
                "Cache manifest must be within the repository root",
                code="MANIFEST_PATH_ESCAPE",
            ) from exc

        self.output_base_dir = Path(output_base_dir)
        if not self.output_base_dir.is_absolute():
            self.output_base_dir = self.repo_root / self.output_base_dir
        self.output_base_dir = self.output_base_dir.resolve()
        replay_root = (self.repo_root / "results" / "replays").resolve()
        try:
            self.output_base_dir.relative_to(replay_root)
        except ValueError as exc:
            raise CacheReplayRefusal(
                "output_base_dir must remain beneath repository results/replays",
                code="OUTPUT_DIR_PROTECTED",
            ) from exc

        self._manifest_sha256 = ""
        self._manifest_data: dict[str, Any] = self._load_and_validate_manifest()

    @staticmethod
    def _read_snapshot(file_path: Path) -> bytes:
        """Read one stable descriptor snapshot without following the final symlink."""
        try:
            fd = os.open(file_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        except OSError as exc:
            raise CacheIntegrityError(
                f"Cache file unreadable: {file_path}: {exc}", code="CACHE_UNREADABLE"
            ) from exc
        try:
            with os.fdopen(fd, "rb") as stream:
                return stream.read()
        except OSError as exc:
            raise CacheIntegrityError(
                f"Cache file unreadable: {file_path}: {exc}", code="CACHE_UNREADABLE"
            ) from exc

    @classmethod
    def _read_verified_snapshot(
        cls,
        file_path: Path,
        *,
        expected_sha256: str | None = None,
        expected_byte_size: int | None = None,
    ) -> bytes:
        """Return bytes whose size/hash were verified, before any parsing."""
        data = cls._read_snapshot(file_path)
        if expected_byte_size is not None and len(data) != expected_byte_size:
            raise CacheIntegrityError(
                f"Byte size mismatch for {file_path.name}: expected "
                f"{expected_byte_size}, found {len(data)}",
                code="CACHE_SIZE_MISMATCH",
            )
        actual_hash = hashlib.sha256(data).hexdigest()
        if expected_sha256 is not None and actual_hash != expected_sha256.lower():
            raise CacheIntegrityError(
                f"Cryptographic hash mismatch for {file_path.name}!\n"
                f"Expected: {expected_sha256}\nActual:   {actual_hash}",
                code="CACHE_HASH_MISMATCH",
            )
        return data

    def _load_and_validate_manifest(self) -> dict[str, Any]:
        """Load and validate the cache manifest. Fail-closed on any error."""
        if not self.manifest_path.exists():
            raise CacheIntegrityError(
                f"Cache manifest not found: {self.manifest_path}", code="MANIFEST_MISSING"
            )
        if not self.manifest_path.is_file():
            raise CacheIntegrityError(
                f"Cache manifest is not a file: {self.manifest_path}", code="MANIFEST_NOT_FILE"
            )

        try:
            raw_bytes = self._read_snapshot(self.manifest_path)
        except CacheIntegrityError as exc:
            raise CacheIntegrityError(
                f"Cache manifest unreadable: {self.manifest_path}: {exc}",
                code="MANIFEST_UNREADABLE",
            ) from exc

        if not raw_bytes:
            raise CacheIntegrityError(
                f"Cache manifest is empty: {self.manifest_path}", code="MANIFEST_EMPTY"
            )

        self._manifest_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        try:
            data = json.loads(
                raw_bytes.decode("utf-8"), object_pairs_hook=_reject_duplicate_json_keys
            )
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            raise CacheIntegrityError(
                f"Cache manifest is malformed JSON: {exc}", code="MANIFEST_MALFORMED"
            ) from exc

        if not isinstance(data, dict):
            raise CacheIntegrityError(
                "Cache manifest root must be a JSON object",
                code="MANIFEST_INVALID_STRUCTURE",
            )

        required_fields = {"manifest_version", "created_at", "cohort", "events"}
        missing = required_fields - set(data)
        if missing:
            raise CacheIntegrityError(
                f"Cache manifest missing required fields: {sorted(missing)}",
                code="MANIFEST_MISSING_FIELDS",
            )

        if data["manifest_version"] != MANIFEST_SCHEMA_VERSION:
            raise CacheIntegrityError(
                f"Unsupported manifest_version: {data['manifest_version']!r}. "
                f"Expected {MANIFEST_SCHEMA_VERSION!r}",
                code="MANIFEST_VERSION_MISMATCH",
            )

        if not isinstance(data["cohort"], str) or not data["cohort"].strip():
            raise CacheIntegrityError(
                "Cache manifest 'cohort' must be a non-empty string",
                code="MANIFEST_INVALID_COHORT",
            )

        events = data["events"]
        if not isinstance(events, dict):
            raise CacheIntegrityError(
                "Cache manifest 'events' must be a JSON object",
                code="MANIFEST_INVALID_EVENTS",
            )

        for event_key, event_entry in events.items():
            self._validate_event_entry(event_key, event_entry)

        _assert_no_media_references(data, "manifest")
        return data

    def _validate_event_entry(self, event_key: str, event_entry: Any) -> None:
        """Validate a single event entry in the manifest."""
        if not isinstance(event_entry, dict):
            raise CacheIntegrityError(
                f"Event '{event_key}' entry must be a JSON object",
                code="MANIFEST_INVALID_EVENT",
            )
        event_required = {"event_id", "front_vision_cache"}
        event_missing = event_required - set(event_entry)
        if event_missing:
            raise CacheIntegrityError(
                f"Event '{event_key}' missing required fields: {sorted(event_missing)}",
                code="MANIFEST_EVENT_MISSING_FIELDS",
            )

        for cache_key in ("front_vision_cache", "front_audio_cache"):
            if cache_key not in event_entry:
                continue
            cache_info = event_entry[cache_key]
            if not isinstance(cache_info, dict):
                raise CacheIntegrityError(
                    f"Event '{event_key}'.{cache_key} must be a JSON object",
                    code="MANIFEST_INVALID_CACHE_ENTRY",
                )
            cache_required = {"path", "sha256", "line_count", "byte_size"}
            cache_missing = cache_required - set(cache_info)
            if cache_missing:
                raise CacheIntegrityError(
                    f"Event '{event_key}'.{cache_key} missing: {sorted(cache_missing)}",
                    code="MANIFEST_CACHE_MISSING_FIELDS",
                )

            sha = cache_info["sha256"]
            if not isinstance(sha, str) or len(sha) != 64 or not all(
                c in "0123456789abcdef" for c in sha.lower()
            ):
                raise CacheIntegrityError(
                    f"Event '{event_key}'.{cache_key}.sha256 must be 64 hex chars",
                    code="MANIFEST_INVALID_SHA256",
                )

            line_count = cache_info["line_count"]
            if isinstance(line_count, bool) or not isinstance(line_count, int) or line_count < 1:
                raise CacheIntegrityError(
                    f"Event '{event_key}'.{cache_key}.line_count must be positive integer",
                    code="MANIFEST_INVALID_LINE_COUNT",
                )

            byte_size = cache_info["byte_size"]
            if isinstance(byte_size, bool) or not isinstance(byte_size, int) or byte_size < 1:
                raise CacheIntegrityError(
                    f"Event '{event_key}'.{cache_key}.byte_size must be positive integer",
                    code="MANIFEST_INVALID_BYTE_SIZE",
                )

            _validate_cache_path(cache_info["path"], self.repo_root)

        if event_entry["event_id"] != event_key:
            raise CacheIntegrityError(
                f"Event key '{event_key}' differs from declared event_id "
                f"{event_entry['event_id']!r}",
                code="MANIFEST_EVENT_ID_MISMATCH",
            )

    def _verify_cache_file(
        self, cache_path: Path, expected_sha256: str, expected_byte_size: int
    ) -> bytes:
        """Verify and return one descriptor snapshot before any parsing."""
        if not cache_path.exists():
            raise CacheIntegrityError(
                f"FATAL: Cache file does not exist: {cache_path}. "
                f"Silent fallthrough to raw media decoding is strictly prohibited.",
                code="CACHE_FILE_MISSING",
            )
        if not cache_path.is_file():
            raise CacheIntegrityError(
                f"Cache path is not a regular file: {cache_path}", code="CACHE_NOT_FILE"
            )
        return self._read_verified_snapshot(
            cache_path,
            expected_sha256=expected_sha256,
            expected_byte_size=expected_byte_size,
        )

    def _get_event_entry(self, event_id: str) -> dict[str, Any]:
        events = self._manifest_data.get("events", {})
        entry = events.get(event_id)
        if entry is None:
            raise CacheReplayRefusal(
                f"Event ID '{event_id}' not registered in cache manifest.",
                code="EVENT_NOT_IN_MANIFEST",
                event_id=event_id,
            )
        return entry

    def _load_cache_stream(
        self, cache_info: dict[str, Any], event_id: str, stream_name: str
    ) -> list[dict[str, Any]]:
        """Load and validate a JSONL cache file, returning parsed records."""
        from railway_detection.evaluation.descriptive_exec_gate import (
            require_descriptive_authorization_for_engine,
        )

        # Lowest-level cache reader: direct load_*_records() calls meet the gate too.
        require_descriptive_authorization_for_engine(
            self.repo_root, condition=None, event_id=event_id, manifest_sha256=self._manifest_sha256
        )
        path_str = cache_info["path"]
        cache_path = _validate_cache_path(path_str, self.repo_root)
        verified_bytes = self._verify_cache_file(
            cache_path, cache_info["sha256"], cache_info["byte_size"]
        )
        try:
            raw_content = verified_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CacheIntegrityError(
                f"Cache file unreadable: {cache_path}: {exc}", code="CACHE_UNREADABLE"
            ) from exc

        lines = [line for line in raw_content.splitlines() if line.strip()]
        if len(lines) != cache_info["line_count"]:
            raise CacheIntegrityError(
                f"Line count mismatch in {cache_path.name}: "
                f"expected {cache_info['line_count']}, found {len(lines)}",
                code="CACHE_LINE_COUNT_MISMATCH",
            )

        records: list[dict[str, Any]] = []
        for line_idx, line in enumerate(lines):
            try:
                record = json.loads(
                    line, object_pairs_hook=_reject_duplicate_json_keys
                )
            except (json.JSONDecodeError, ValueError) as exc:
                raise CacheIntegrityError(
                    f"Malformed JSON at line {line_idx + 1} in {cache_path.name}: {exc}",
                    code="CACHE_MALFORMED_RECORD",
                ) from exc
            if not isinstance(record, dict):
                raise CacheIntegrityError(
                    f"Record at line {line_idx + 1} in {cache_path.name} is not a JSON object",
                    code="CACHE_RECORD_NOT_OBJECT",
                )
            records.append(record)
        return records

    def load_visual_records(self, event_id: str) -> list[EvidenceRecord]:
        """Load validated visual evidence records for an event."""
        entry = self._get_event_entry(event_id)
        cache_info = entry["front_vision_cache"]
        raw_records = self._load_cache_stream(cache_info, event_id, "front_vision")
        provenance = {
            "event_id": event_id,
            "stream": "front_vision",
            "artifact_path": cache_info["path"],
            "artifact_sha256": cache_info["sha256"],
        }
        records = [_validate_visual_record(raw, idx) for idx, raw in enumerate(raw_records)]
        return [
            replace(record, metadata={**record.metadata, "provenance": provenance})
            for record in records
        ]

    def load_audio_records(self, event_id: str) -> list[EvidenceRecord]:
        """Load validated audio evidence records for an event."""
        entry = self._get_event_entry(event_id)
        if "front_audio_cache" not in entry:
            raise CacheReplayRefusal(
                "selected condition requires an actual audio cache",
                code="CONDITION_STREAM_MISSING", event_id=event_id,
            )
        cache_info = entry["front_audio_cache"]
        raw_records = self._load_cache_stream(cache_info, event_id, "front_audio")
        provenance = {
            "event_id": event_id,
            "stream": "front_audio",
            "artifact_path": cache_info["path"],
            "artifact_sha256": cache_info["sha256"],
        }
        records = [_validate_audio_record(raw, idx) for idx, raw in enumerate(raw_records)]
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
        """Execute a deterministic cache-only replay for the given event and condition."""
        # Operation-boundary gate: replaying real-data caches needs AUTH-DESCRIPTIVE-EVAL-EXEC.
        # (Imported lazily: the gate imports the execution gate, which imports this package.)
        from railway_detection.evaluation.descriptive_exec_gate import (
            require_descriptive_authorization_for_engine,
        )

        require_descriptive_authorization_for_engine(
            self.repo_root,
            condition=condition,
            event_id=event_id,
            manifest_sha256=self._manifest_sha256,
        )
        if condition not in SUPPORTED_CONDITIONS:
            raise CacheReplayRefusal(
                f"Condition '{condition}' not supported. Must be one of "
                f"{sorted(SUPPORTED_CONDITIONS)}",
                code="UNSUPPORTED_CONDITION",
                event_id=event_id,
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

        required_streams = CONDITION_STREAMS[condition]
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

        timestamps = [r.timestamp_s for r in all_records]
        t_start = min(timestamps)
        t_end = max(timestamps)

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
                "frame_stride_s": frame_stride_s,
                "sync": sync_summary,
                "cache_paths": {
                    stream: self._get_event_entry(event_id)[f"{stream}_cache"]["path"]
                    for stream in required_streams
                },
            },
        )

    def replay_all_events(
        self, condition: str, **kwargs: Any
    ) -> dict[str, ReplayOutput | ReplayRefusalRecord]:
        """Replay all events in the manifest. Records per-event failures as refusals."""
        results: dict[str, ReplayOutput | ReplayRefusalRecord] = {}
        events = self._manifest_data.get("events", {})

        for event_id in sorted(events.keys()):
            try:
                results[event_id] = self.execute_replay(event_id, condition, **kwargs)
            except Exception as exc:  # noqa: BLE001 - batch API must record every refusal
                code = getattr(exc, "code", "REPLAY_ERROR")
                results[event_id] = ReplayRefusalRecord(
                    event_id=event_id,
                    condition=condition,
                    code=code,
                    detail=str(exc),
                    stage="replay",
                )
        return results

    @staticmethod
    def _deterministic_sort(records: list[EvidenceRecord]) -> list[EvidenceRecord]:
        """Sort records deterministically by timestamp, source, and index."""

        def sort_key(record: EvidenceRecord) -> tuple[float, str, int]:
            ts = record.timestamp_s
            src = record.source_id
            idx = record.metadata.get("frame_index", record.metadata.get("window_index", 0))
            if not isinstance(idx, int):
                idx = 0
            return (ts, src, idx)

        return sorted(records, key=sort_key)

    @property
    def manifest_data(self) -> dict[str, Any]:
        """Return a deep copy of the validated manifest data."""
        return copy.deepcopy(self._manifest_data)

    @property
    def manifest_sha256(self) -> str:
        """Return the SHA-256 of the manifest file itself."""
        return self._manifest_sha256

    def list_events(self) -> list[str]:
        """Return sorted list of event IDs in the manifest."""
        return sorted(self._manifest_data.get("events", {}).keys())
