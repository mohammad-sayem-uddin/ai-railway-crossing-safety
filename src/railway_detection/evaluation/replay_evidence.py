"""Per-event replay-evidence payloads for the Phase 12 official replay.

An evidence payload is the *input* to the decision-engine replay: serialized
``EvidenceRecord`` streams (vision detections, audio windows) that frozen models
already produced, plus the provenance needed to prove which frozen
configuration, checkpoints and media produced them. It deliberately has **no
field for annotation labels or boundary times**: the replay never sees ground
truth, and model outputs can never flow into labels.

The payload is the ``source`` file named in the hash-bound input manifest, so
its bytes are pinned by the manifest digest that EVAL-AUTH binds.

Stream/scope contract (``camera_mode`` must equal the manifest's camera scope):

================== ===================================== ====================
mode               required streams                      forbidden streams
================== ===================================== ====================
single_camera      front_vision                          back_vision
independent_camera front_vision, back_vision             (none)
dual_camera        front_vision, back_vision             (none)
================== ===================================== ====================

``front_audio`` is optional in every mode (audio is taken from the front track).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from railway_detection.experiments.frozen_config import FrozenExperimentConfig
from railway_detection.experiments.layer_b_processor import (
    deserialize_evidence_record,
    serialize_evidence_record,
)
from railway_detection.fusion.evidence import EvidenceRecord, Modality

REPLAY_EVIDENCE_SCHEMA = "phase12-replay-evidence/1"

STREAM_SPEC: dict[str, tuple[str, Modality]] = {
    "front_vision": ("camera_1", Modality.VISION),
    "back_vision": ("camera_2", Modality.VISION),
    "front_audio": ("audio_1", Modality.AUDIO),
}
MODE_REQUIRED: dict[str, frozenset[str]] = {
    "single_camera": frozenset({"front_vision"}),
    "independent_camera": frozenset({"front_vision", "back_vision"}),
    "dual_camera": frozenset({"front_vision", "back_vision"}),
}
MODE_FORBIDDEN: dict[str, frozenset[str]] = {
    "single_camera": frozenset({"back_vision"}),
    "independent_camera": frozenset(),
    "dual_camera": frozenset(),
}

_PAYLOAD_KEYS = frozenset(
    {"schema_version", "event_id", "cohort", "camera_mode", "streams", "provenance"}
)
_PROVENANCE_KEYS = frozenset(
    {
        "frozen_config_canonical_sha256",
        "checkpoint_sha256",
        "vision_confidence_threshold",
        "audio_operating_threshold",
        "media_sha256",
        "inference_run_id",
        "annotation_labels_used",
        "generated_by",
    }
)


class ReplayInputError(ValueError):
    """An evidence payload is malformed, mis-scoped, or mis-attributed."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class ReplayEvidence:
    event_id: str
    cohort: str
    camera_mode: str
    streams: dict[str, tuple[EvidenceRecord, ...]]
    provenance: dict[str, Any]


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _check_provenance(provenance: Any, config: FrozenExperimentConfig) -> dict[str, Any]:
    if not isinstance(provenance, dict) or set(provenance) != _PROVENANCE_KEYS:
        raise ReplayInputError(
            "PROVENANCE_INVALID", f"provenance must have exactly {sorted(_PROVENANCE_KEYS)}"
        )
    if provenance["annotation_labels_used"] is not False:
        raise ReplayInputError(
            "LABEL_LEAKAGE", "annotation_labels_used must be exactly false"
        )
    for key in ("inference_run_id", "generated_by"):
        if not isinstance(provenance[key], str) or not provenance[key].strip():
            raise ReplayInputError("PROVENANCE_INVALID", f"{key} is required")
    if provenance["frozen_config_canonical_sha256"] != config.canonical_hash:
        raise ReplayInputError(
            "PROVENANCE_MISMATCH", "evidence was not produced under the live frozen configuration"
        )
    checkpoints = provenance["checkpoint_sha256"]
    if not isinstance(checkpoints, dict) or set(checkpoints) != {"vision", "audio_v3"}:
        raise ReplayInputError(
            "PROVENANCE_INVALID", "checkpoint_sha256 must name exactly vision and audio_v3"
        )
    if checkpoints["audio_v3"] == config.checkpoints.prohibited_audio_v2.sha256 or any(
        value == config.checkpoints.prohibited_audio_v2.sha256 for value in checkpoints.values()
    ):
        raise ReplayInputError(
            "PROHIBITED_CHECKPOINT", "evidence was produced with the prohibited Audio V2 checkpoint"
        )
    if (
        checkpoints["vision"] != config.checkpoints.vision.expected_sha256
        or checkpoints["audio_v3"] != config.checkpoints.audio_v3.expected_sha256
    ):
        raise ReplayInputError(
            "PROVENANCE_MISMATCH", "checkpoint hashes differ from the frozen configuration"
        )
    if (
        provenance["vision_confidence_threshold"] != config.vision.confidence_threshold_approach
        or provenance["audio_operating_threshold"] != config.audio.operating_threshold
    ):
        raise ReplayInputError(
            "PROVENANCE_MISMATCH", "recorded inference thresholds differ from the frozen values"
        )
    media = provenance["media_sha256"]
    if (
        not isinstance(media, dict)
        or not media
        or set(media) - {"front", "back"}
        or not all(_is_sha256(value) for value in media.values())
    ):
        raise ReplayInputError("PROVENANCE_INVALID", "media_sha256 must map front/back to SHA-256")
    return provenance


def _parse_stream(name: str, raw: Any) -> tuple[EvidenceRecord, ...]:
    source_id, modality = STREAM_SPEC[name]
    if not isinstance(raw, dict) or set(raw) != {"source_id", "records"}:
        raise ReplayInputError("STREAM_INVALID", f"{name} must have exactly source_id and records")
    if raw["source_id"] != source_id:
        raise ReplayInputError(
            "STREAM_INVALID", f"{name}.source_id must be {source_id!r}, got {raw['source_id']!r}"
        )
    if not isinstance(raw["records"], list) or not raw["records"]:
        raise ReplayInputError("STREAM_INVALID", f"{name}.records must be a nonempty list")
    records: list[EvidenceRecord] = []
    for index, item in enumerate(raw["records"]):
        try:
            record = deserialize_evidence_record(item)
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ReplayInputError("RECORD_INVALID", f"{name}[{index}]: {exc}") from exc
        if record.source_id != source_id or record.modality is not modality:
            raise ReplayInputError(
                "RECORD_INVALID", f"{name}[{index}]: source/modality differs from the stream"
            )
        if not math.isfinite(record.timestamp_s) or record.timestamp_s < 0:
            raise ReplayInputError("RECORD_INVALID", f"{name}[{index}]: invalid timestamp")
        for detection in record.detections:
            if not math.isfinite(detection.confidence) or not 0.0 <= detection.confidence <= 1.0:
                raise ReplayInputError(
                    "RECORD_INVALID", f"{name}[{index}]: confidence outside [0, 1]"
                )
        records.append(record)
    return tuple(records)


def parse_replay_evidence(
    payload: Mapping[str, Any],
    *,
    expected_event_id: str,
    expected_cohort: str,
    expected_camera_mode: str,
    config: FrozenExperimentConfig,
) -> ReplayEvidence:
    """Validate one payload against its manifest identity, scope and the frozen config."""
    if not isinstance(payload, Mapping) or set(payload) != _PAYLOAD_KEYS:
        extra = sorted(set(payload) - _PAYLOAD_KEYS) if isinstance(payload, Mapping) else []
        raise ReplayInputError(
            "PAYLOAD_INVALID",
            f"payload must have exactly {sorted(_PAYLOAD_KEYS)}; unexpected={extra} "
            "(label or boundary fields are never accepted)",
        )
    if payload["schema_version"] != REPLAY_EVIDENCE_SCHEMA:
        raise ReplayInputError(
            "PAYLOAD_INVALID", f"unsupported schema_version {payload['schema_version']!r}"
        )
    if payload["event_id"] != expected_event_id or payload["cohort"] != expected_cohort:
        raise ReplayInputError(
            "IDENTITY_MISMATCH",
            f"payload identity {payload['cohort']!r}/{payload['event_id']!r} differs from the "
            f"manifest's {expected_cohort!r}/{expected_event_id!r}",
        )
    mode = payload["camera_mode"]
    if mode != expected_camera_mode:
        raise ReplayInputError(
            "SCOPE_MISMATCH",
            f"payload camera_mode {mode!r} differs from the decided scope "
            f"{expected_camera_mode!r}",
        )
    if mode not in MODE_REQUIRED:
        raise ReplayInputError("SCOPE_MISMATCH", f"unknown camera mode {mode!r}")
    raw_streams = payload["streams"]
    if not isinstance(raw_streams, dict) or set(raw_streams) - set(STREAM_SPEC):
        raise ReplayInputError(
            "STREAM_INVALID", f"streams may only contain {sorted(STREAM_SPEC)}"
        )
    present = set(raw_streams)
    forbidden = present & MODE_FORBIDDEN[mode]
    if forbidden:
        raise ReplayInputError(
            "SCOPE_VIOLATION", f"{mode} forbids stream(s) {sorted(forbidden)}"
        )
    missing = MODE_REQUIRED[mode] - present
    if missing:
        raise ReplayInputError("STREAM_INVALID", f"{mode} requires stream(s) {sorted(missing)}")
    provenance = _check_provenance(payload["provenance"], config)
    needed_media = {"front"} | ({"back"} if "back_vision" in present else set())
    if set(provenance["media_sha256"]) != needed_media:
        raise ReplayInputError(
            "PROVENANCE_INVALID", f"media_sha256 must cover exactly {sorted(needed_media)}"
        )
    streams = {name: _parse_stream(name, raw_streams[name]) for name in sorted(raw_streams)}
    return ReplayEvidence(
        event_id=expected_event_id,
        cohort=expected_cohort,
        camera_mode=mode,
        streams=streams,
        provenance=dict(provenance),
    )


def build_replay_evidence_payload(
    *,
    event_id: str,
    cohort: str,
    camera_mode: str,
    streams: Mapping[str, list[EvidenceRecord]],
    provenance: Mapping[str, Any],
) -> dict[str, Any]:
    """Package already-produced inference records into a payload (no model is run).

    The result is validated by ``parse_replay_evidence`` at replay time; this helper
    performs no check of its own so a mispackaged payload fails where it is used.
    """
    return {
        "schema_version": REPLAY_EVIDENCE_SCHEMA,
        "event_id": event_id,
        "cohort": cohort,
        "camera_mode": camera_mode,
        "streams": {
            name: {
                "source_id": STREAM_SPEC[name][0],
                "records": [serialize_evidence_record(record) for record in records],
            }
            for name, records in streams.items()
        },
        "provenance": dict(provenance),
    }
