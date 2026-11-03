"""Authoritative proposal schema definitions and validation for AI-assisted ground truth.

Conforms strictly to Ground Truth Protocol v5.0.0 §6.0 and §6.1.
Enforces 64-character lowercase hexadecimal SHA-256 validation.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SHA256_REGEX = re.compile(r"^[0-9a-f]{64}$")

VALID_EVENT_TYPES = (
    "REAL_WORLD_TRAIN_EVENT",
    "REAL_WORLD_NO_TRAIN",
    "REAL_WORLD_ENGINE_ONLY",
)

VALID_HORN_STATUSES = (
    "present",
    "absent_observed",
    "unobservable",
)

CANONICAL_TIMESTAMPS = (
    "T0_first_visible",
    "T1_danger_zone_entry",
    "T2_crossing_occupancy_start",
    "T3_locomotive_unit_clearance",
    "T4_tail_clearance",
    "T_scene_clear",
)

# Backward-compatibility alias mappings for legacy draft proposals (v1-v4)
LEGACY_TIMESTAMP_ALIASES: dict[str, str] = {
    "T3_locomotive_exit": "T3_locomotive_unit_clearance",
}

# Authoritative human-readable canonical terminology (Protocol v6.0.0 §2.1)
CANONICAL_TIMESTAMP_NAMES: dict[str, str] = {
    "T0_first_visible": "First Visual Appearance",
    "T1_danger_zone_entry": "Danger Zone Entry",
    "T2_crossing_occupancy_start": "Crossing Occupancy Start",
    "T3_locomotive_unit_clearance": "Locomotive Unit Clearance (rear end exits danger zone)",
    "T4_tail_clearance": "Tail Clearance (final vehicle exits danger zone)",
    "T_scene_clear": "Scene Clear",
}


def normalize_timestamp_keys(timestamps: dict[str, Any]) -> dict[str, Any]:
    """Map legacy proposal keys (e.g., T3_locomotive_exit) to canonical keys for Stage 3 migration."""
    normalized: dict[str, Any] = {}
    for k, v in timestamps.items():
        canonical_k = LEGACY_TIMESTAMP_ALIASES.get(k, k)
        normalized[canonical_k] = v
    return normalized


class SchemaValidationError(ValueError):
    """Raised when a proposal or checksum fails schema validation."""


def validate_sha256(hash_str: str, field_name: str = "checksum") -> str:
    """Validate that a string is a 64-character lowercase hexadecimal SHA-256 hash.

    Raises:
        SchemaValidationError: If hash_str does not match ^[0-9a-f]{64}$.
    """
    if not isinstance(hash_str, str):
        raise SchemaValidationError(
            f"{field_name} must be a string, got {type(hash_str).__name__}"
        )
    if not SHA256_REGEX.match(hash_str):
        if "..." in hash_str or "<" in hash_str:
            raise SchemaValidationError(
                f"{field_name} contains placeholder/ellipsis: '{hash_str}'. "
                "Must be a full 64-character lowercase hex string."
            )
        raise SchemaValidationError(
            f"{field_name} is not a valid 64-char lowercase hex SHA-256: '{hash_str}' "
            f"(len={len(hash_str)})"
        )
    return hash_str


@dataclass
class InputMediaFile:
    file_name: str
    duration_s: float
    sha256: str

    def __post_init__(self) -> None:
        self.sha256 = validate_sha256(self.sha256, f"input_media_files[{self.file_name}].sha256")
        if self.duration_s <= 0:
            raise SchemaValidationError(f"duration_s must be positive, got {self.duration_s}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AIAssistantMetadata:
    model_name: str
    prompt_template_version: str
    prompt_template_sha256: str
    input_media_files: list[InputMediaFile] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.prompt_template_sha256 = validate_sha256(
            self.prompt_template_sha256, "prompt_template_sha256"
        )
        if not self.model_name:
            raise SchemaValidationError("model_name cannot be empty")
        if not self.prompt_template_version:
            raise SchemaValidationError("prompt_template_version cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "prompt_template_version": self.prompt_template_version,
            "prompt_template_sha256": self.prompt_template_sha256,
            "input_media_files": [f.to_dict() for f in self.input_media_files],
        }


@dataclass
class ProposedSiteMetadata:
    crossing_id: str
    recording_session_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProposedEnvironmentalConditions:
    lighting: str
    weather: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProposedTrainMetadata:
    train_present: bool
    train_direction: str | None = None
    train_type: str | None = None
    trailing_cars_count: int | None = None
    horn_status: str | None = None
    horn_onset_s: float | None = None
    horn_uncertainty_s: float | None = None
    horn_reason: str | None = None
    confidence_note: str | None = None

    def __post_init__(self) -> None:
        if self.train_present:
            if self.horn_status is not None and self.horn_status not in VALID_HORN_STATUSES:
                raise SchemaValidationError(
                    f"horn_status must be one of {VALID_HORN_STATUSES}, got '{self.horn_status}'"
                )
            if self.horn_status == "present" and self.horn_onset_s is None:
                raise SchemaValidationError(
                    "horn_onset_s must be provided when horn_status is 'present'"
                )
            if self.horn_status == "unobservable" and not self.horn_reason:
                raise SchemaValidationError(
                    "horn_reason must explain why horn is unobservable"
                )
        else:
            if self.horn_status is not None:
                raise SchemaValidationError(
                    "horn_status must be None for no-train events"
                )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProposedBoundaryTimestamp:
    applicable: bool
    candidate_observable: bool
    value_s: float | None = None
    frame_index: int | None = None
    reference_camera: str | None = None
    native_fps: float | None = None
    rationale: str | None = None
    ambiguity_flag: bool = False

    def __post_init__(self) -> None:
        if self.applicable and self.candidate_observable:
            if self.value_s is None:
                raise SchemaValidationError(
                    "value_s must be provided when applicable and candidate_observable are True"
                )
            if self.reference_camera not in ("front", "back"):
                raise SchemaValidationError(
                    f"reference_camera must be 'front' or 'back', got '{self.reference_camera}'"
                )
        if not self.applicable:
            if self.value_s is not None:
                raise SchemaValidationError(
                    "value_s must be None when timestamp is not applicable"
                )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProposedCameraAlignmentMarkers:
    candidate_front_marker: str | None = None
    candidate_back_marker: str | None = None
    candidate_offset_s: float | None = None
    requires_human_empirical_verification: bool = True
    audited_front_stream_exposure_s: float = 60.300
    audited_back_stream_exposure_s: float = 60.488
    audited_combined_camera_stream_exposure_s: float = 120.788
    stream_exposure_note: str = (
        "Combined camera-stream exposure (120.788s) represents summed stream-seconds "
        "and must NOT be treated as concurrent wall-clock exposure."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProposalDocument:
    proposal_id: str
    event_id: str
    event_type: str
    proposal_timestamp_utc: str
    schema_version: str
    ai_assistant_metadata: AIAssistantMetadata
    proposed_site_metadata: ProposedSiteMetadata
    proposed_environmental_conditions: ProposedEnvironmentalConditions
    proposed_train_metadata: ProposedTrainMetadata
    proposed_timestamps: dict[str, ProposedBoundaryTimestamp]
    proposed_camera_alignment_markers: ProposedCameraAlignmentMarkers
    raw_proposal_immutable: bool = True
    prior_proposal_ref: str | None = None
    activity_log: list[dict[str, Any]] = field(default_factory=list)
    schema_url: str = "https://json-schema.org/draft/2020-12/schema"

    def __post_init__(self) -> None:
        if self.event_type not in VALID_EVENT_TYPES:
            raise SchemaValidationError(
                f"event_type must be one of {VALID_EVENT_TYPES}, got '{self.event_type}'"
            )
        if self.schema_version not in ("5.0.0", "6.0.0", "7.0.0"):
            raise SchemaValidationError(
                f"schema_version must be '5.0.0', '6.0.0', or '7.0.0', got '{self.schema_version}'"
            )

        # Validate canonical timestamps presence (supporting legacy alias keys for v1-v4 proposals)
        for ts_key in CANONICAL_TIMESTAMPS:
            if ts_key not in self.proposed_timestamps:
                # Check if a legacy alias is present in proposed_timestamps
                alias_present = any(
                    legacy_k in self.proposed_timestamps
                    for legacy_k, canon_k in LEGACY_TIMESTAMP_ALIASES.items()
                    if canon_k == ts_key
                )
                if not alias_present:
                    raise SchemaValidationError(f"Missing canonical timestamp '{ts_key}' in proposal")

        def _get_t3() -> ProposedBoundaryTimestamp:
            if "T3_locomotive_unit_clearance" in self.proposed_timestamps:
                return self.proposed_timestamps["T3_locomotive_unit_clearance"]
            if "T3_locomotive_exit" in self.proposed_timestamps:
                return self.proposed_timestamps["T3_locomotive_exit"]
            raise SchemaValidationError("Missing T3 (Locomotive Unit Clearance) timestamp in proposal")

        # Event-type specific logic
        if self.event_type == "REAL_WORLD_TRAIN_EVENT":
            if not self.proposed_train_metadata.train_present:
                raise SchemaValidationError(
                    "train_present must be True for REAL_WORLD_TRAIN_EVENT"
                )
            t3 = _get_t3()
            t4 = self.proposed_timestamps["T4_tail_clearance"]
            trailing_cars = self.proposed_train_metadata.trailing_cars_count or 0
            if trailing_cars > 0 and t3.value_s is not None and t4.value_s is not None:
                if t4.value_s <= t3.value_s:
                    raise SchemaValidationError(
                        f"T4 ({t4.value_s}s) must be greater than T3 ({t3.value_s}s) "
                        f"when trailing cars are present ({trailing_cars})"
                    )

        elif self.event_type == "REAL_WORLD_ENGINE_ONLY":
            if not self.proposed_train_metadata.train_present:
                raise SchemaValidationError(
                    "train_present must be True for REAL_WORLD_ENGINE_ONLY"
                )
            t3 = _get_t3()
            t4 = self.proposed_timestamps["T4_tail_clearance"]
            if t3.candidate_observable and t4.candidate_observable:
                if t3.value_s != t4.value_s:
                    raise SchemaValidationError(
                        f"For engine-only events, T3 ({t3.value_s}s) and T4 ({t4.value_s}s) "
                        "must coincide (T3 == T4)"
                    )

        elif self.event_type == "REAL_WORLD_NO_TRAIN":
            if self.proposed_train_metadata.train_present:
                raise SchemaValidationError(
                    "train_present must be False for REAL_WORLD_NO_TRAIN"
                )
            for ts_name, ts in self.proposed_timestamps.items():
                if ts.applicable or ts.value_s is not None:
                    raise SchemaValidationError(
                        f"Timestamp '{ts_name}' must have applicable=False and value_s=None for no-train events"
                    )

    def to_dict(self) -> dict[str, Any]:
        data = {
            "$schema": self.schema_url,
            "proposal_id": self.proposal_id,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "proposal_timestamp_utc": self.proposal_timestamp_utc,
            "schema_version": self.schema_version,
            "ai_assistant_metadata": self.ai_assistant_metadata.to_dict(),
            "proposed_site_metadata": self.proposed_site_metadata.to_dict(),
            "proposed_environmental_conditions": self.proposed_environmental_conditions.to_dict(),
            "proposed_train_metadata": self.proposed_train_metadata.to_dict(),
            "proposed_timestamps": {
                k: v.to_dict() for k, v in self.proposed_timestamps.items()
            },
            "proposed_camera_alignment_markers": self.proposed_camera_alignment_markers.to_dict(),
            "raw_proposal_immutable": self.raw_proposal_immutable,
        }
        if self.prior_proposal_ref:
            data["prior_proposal_ref"] = self.prior_proposal_ref
        if self.activity_log:
            data["activity_log"] = self.activity_log
        return data


def assert_proposal_approval_firewall(output_path: Path, doc_dict: dict[str, Any]) -> None:
    """Enforce the mandatory approval firewall.

    Prohibits:
    1. Writing into approved ground truth directories.
    2. Setting approval_status to 'APPROVED' in candidate proposals.
    3. Missing proposal directory hierarchy.
    """
    resolved_path = output_path.resolve()
    path_str = str(resolved_path)

    # 1. Prohibit approved directories
    prohibited_approved_dirs = (
        "data/ground_truth/train_events",
        "data/ground_truth/no_train_events",
        "data/ground_truth/engine_events",
    )
    for bad_dir in prohibited_approved_dirs:
        if bad_dir in path_str and "proposals" not in path_str:
            raise SchemaValidationError(
                f"FIREWALL VIOLATION: Proposal write attempted into approved ground truth directory: {path_str}"
            )

    # 2. Must be under proposals/
    if "proposals" not in resolved_path.parts:
        raise SchemaValidationError(
            f"FIREWALL VIOLATION: Proposal must be saved under a 'proposals/' directory. Got: {path_str}"
        )

    # 3. Prohibit approval_status: APPROVED
    if "approval_status" in doc_dict and doc_dict["approval_status"] == "APPROVED":
        raise SchemaValidationError(
            "FIREWALL VIOLATION: AI candidate proposal cannot be marked 'approval_status: APPROVED'. "
            "Approval is strictly reserved for certified human review."
        )
