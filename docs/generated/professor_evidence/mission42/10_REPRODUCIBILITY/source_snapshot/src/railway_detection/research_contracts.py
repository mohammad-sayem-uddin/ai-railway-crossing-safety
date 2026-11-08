"""Non-executing research contracts for Phases 12–16.

These helpers validate supplied metadata only. They are not authorization
systems and are not wired to evaluation, ablation, profiling, field-capture,
or publication runners. In particular, caller-supplied approval flags do not
constitute researcher or site authorization. File existence establishes only
path traceability; it does not establish semantic evidence support or
authorization.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Mapping, Sequence


class ResearchContractError(ValueError):
    """Raised when supplied metadata violates a predeclared phase contract."""


def _validate_boolean_flags(values: Sequence[tuple[str, bool]]) -> None:
    """Reject truthy non-booleans instead of letting them satisfy a checklist."""
    for name, value in values:
        if not isinstance(value, bool):
            raise ResearchContractError(f"prerequisite {name!r} must be a boolean assertion")


def validate_event_level_split(partitions: Mapping[str, Sequence[str]]) -> None:
    """Require nonempty, disjoint train/val/test partitions of event IDs.

    This checks mechanical leakage properties only. It does not approve a
    split or make any existing image/frame-level split suitable for evaluation.
    """
    if not isinstance(partitions, Mapping):
        raise ResearchContractError("split partitions must be a mapping")
    required = {"train", "val", "test"}
    if set(partitions) != required:
        raise ResearchContractError(
            "split roles must be exactly ['test', 'train', 'val']; "
            f"got {sorted(map(repr, partitions))}"
        )

    seen: dict[str, str] = {}
    for role in sorted(required):
        event_ids = partitions[role]
        if isinstance(event_ids, (str, bytes)) or not isinstance(event_ids, Sequence):
            raise ResearchContractError(f"split role {role!r} must be a sequence of event IDs")
        if not event_ids:
            raise ResearchContractError(f"split role {role!r} must not be empty")
        local: set[str] = set()
        for event_id in event_ids:
            if (
                not isinstance(event_id, str)
                or not event_id.strip()
                or event_id != event_id.strip()
            ):
                raise ResearchContractError(f"split role {role!r} contains an invalid event ID")
            if event_id in local:
                raise ResearchContractError(
                    f"duplicate event ID {event_id!r} within split role {role!r}"
                )
            local.add(event_id)
            previous = seen.get(event_id)
            if previous is not None:
                raise ResearchContractError(
                    f"event {event_id!r} occurs in both {previous!r} and {role!r}"
                )
            seen[event_id] = role


def validate_camera_scope(
    event_modes: Mapping[str, str],
    *,
    accepted_sync_events: set[str] | frozenset[str],
) -> None:
    """Reject dual-camera scope unless that event is listed as sync-accepted.

    ``independent_camera`` means separate media-local runs, not a merged clock.
    ``accepted_sync_events`` is a caller-supplied assertion only: this function
    does not load or verify calibration evidence, establish researcher approval,
    or decide which supported events are in the evaluation scope. It enforces
    only that declared dual-camera events appear in that supplied set.
    """
    if not isinstance(event_modes, Mapping):
        raise ResearchContractError("camera scope must be a mapping")
    if not event_modes:
        raise ResearchContractError("camera scope must declare at least one event")
    if not isinstance(accepted_sync_events, (set, frozenset)):
        raise ResearchContractError("accepted_sync_events must be a set of event IDs")
    for event_id in event_modes:
        if not isinstance(event_id, str) or not event_id.strip() or event_id != event_id.strip():
            raise ResearchContractError(f"invalid event ID in camera scope: {event_id!r}")
    if any(
        not isinstance(event_id, str) or not event_id.strip() or event_id != event_id.strip()
        for event_id in accepted_sync_events
    ):
        raise ResearchContractError("accepted_sync_events contains an invalid event ID")
    undeclared_sync_events = accepted_sync_events.difference(event_modes)
    if undeclared_sync_events:
        raise ResearchContractError(
            "accepted_sync_events contains undeclared events: "
            f"{sorted(undeclared_sync_events)!r}"
        )
    allowed_modes = {"single_camera", "independent_camera", "dual_camera"}
    for event_id, mode in event_modes.items():
        if not isinstance(mode, str) or mode not in allowed_modes:
            raise ResearchContractError(f"unknown camera mode {mode!r} for {event_id!r}")
        if mode == "dual_camera" and event_id not in accepted_sync_events:
            raise ResearchContractError(
                f"dual-camera scope refused for {event_id!r}: accepted synchronization required"
            )


def missing_phase12_prerequisites(
    *,
    readiness_gate_passed: bool = False,
    eval_auth_granted: bool = False,
    event_split_decided: bool = False,
    r04_scope_decided: bool = False,
    approved_stage21_records_available: bool = False,
) -> tuple[str, ...]:
    """List Phase 12 blockers; this checklist does not establish authorization."""
    values = (
        ("readiness_gate_passed", readiness_gate_passed),
        ("eval_auth_granted", eval_auth_granted),
        ("event_split_decided", event_split_decided),
        ("r04_scope_decided", r04_scope_decided),
        ("approved_stage21_records_available", approved_stage21_records_available),
    )
    _validate_boolean_flags(values)
    return tuple(name for name, present in values if not present)


def missing_phase13_prerequisites(
    *,
    phase12_baseline_complete: bool = False,
    approved_ground_truth_available: bool = False,
    frozen_config_hash_verified: bool = False,
    researcher_scope_authorized: bool = False,
) -> tuple[str, ...]:
    """List Phase 13 blockers without launching ablations or perturbations."""
    values = (
        ("phase12_baseline_complete", phase12_baseline_complete),
        ("approved_ground_truth_available", approved_ground_truth_available),
        ("frozen_config_hash_verified", frozen_config_hash_verified),
        ("researcher_scope_authorized", researcher_scope_authorized),
    )
    _validate_boolean_flags(values)
    return tuple(name for name, present in values if not present)


def missing_phase14_prerequisites(
    *,
    phase12_baseline_complete: bool = False,
    researcher_scope_authorized: bool = False,
    target_hardware_specified: bool = False,
) -> tuple[str, ...]:
    """List Phase 14 blockers; no profiling or optimization is performed."""
    values = (
        ("phase12_baseline_complete", phase12_baseline_complete),
        ("researcher_scope_authorized", researcher_scope_authorized),
        ("target_hardware_specified", target_hardware_specified),
    )
    _validate_boolean_flags(values)
    return tuple(name for name, present in values if not present)


@dataclass(frozen=True)
class AblationConditionContract:
    """Description of a proposed condition; contains no executable transform."""

    condition_id: str
    baseline_config_sha256: str
    changed_factors: tuple[str, ...]
    condition_type: str = "ablation"
    is_baseline: bool = False
    uses_audio_v2: bool = False
    applies_to_ground_truth: bool = False


def validate_ablation_condition_contracts(
    conditions: Sequence[AblationConditionContract],
    *,
    frozen_config_sha256: str,
) -> None:
    """Check one-factor descriptions and frozen-config identity without running them."""
    if not isinstance(frozen_config_sha256, str) or not re.fullmatch(
        r"[0-9a-f]{64}", frozen_config_sha256
    ):
        raise ResearchContractError("frozen config SHA-256 must be 64 lowercase hex characters")
    if isinstance(conditions, (str, bytes)) or not isinstance(conditions, Sequence):
        raise ResearchContractError("conditions must be a sequence of condition contracts")
    if not conditions:
        raise ResearchContractError("at least one proposed ablation condition is required")

    seen: set[str] = set()
    baseline_count = 0
    for condition in conditions:
        if not isinstance(condition, AblationConditionContract):
            raise ResearchContractError("each condition must be an AblationConditionContract")
        if (
            not isinstance(condition.condition_id, str)
            or not condition.condition_id.strip()
            or condition.condition_id != condition.condition_id.strip()
            or condition.condition_id in seen
        ):
            raise ResearchContractError(
                f"empty or duplicate condition ID: {condition.condition_id!r}"
            )
        seen.add(condition.condition_id)
        if not isinstance(condition.baseline_config_sha256, str) or not re.fullmatch(
            r"[0-9a-f]{64}", condition.baseline_config_sha256
        ):
            raise ResearchContractError(
                f"condition {condition.condition_id!r} has an invalid config SHA-256"
            )
        if condition.baseline_config_sha256 != frozen_config_sha256:
            raise ResearchContractError(
                f"condition {condition.condition_id!r} does not retain the frozen config hash"
            )
        if (
            not isinstance(condition.changed_factors, tuple)
            or any(
                not isinstance(factor, str)
                or not factor.strip()
                or factor != factor.strip()
                for factor in condition.changed_factors
            )
            or len(set(condition.changed_factors)) != len(condition.changed_factors)
        ):
            raise ResearchContractError(
                f"condition {condition.condition_id!r} has malformed or duplicate changed factors"
            )
        for flag_name in ("is_baseline", "uses_audio_v2", "applies_to_ground_truth"):
            if not isinstance(getattr(condition, flag_name), bool):
                raise ResearchContractError(
                    f"condition {condition.condition_id!r} flag {flag_name!r} must be boolean"
                )
        if not isinstance(condition.condition_type, str) or condition.condition_type not in {
            "ablation",
            "perturbation",
        }:
            raise ResearchContractError(
                f"condition {condition.condition_id!r} has unknown type "
                f"{condition.condition_type!r}"
            )
        if condition.is_baseline:
            baseline_count += 1
            if condition.changed_factors or condition.condition_type != "ablation":
                raise ResearchContractError("baseline condition must not change any factor")
        elif condition.condition_type == "ablation" and (
            len(condition.changed_factors) != 1
            or not all(factor.strip() for factor in condition.changed_factors)
        ):
            raise ResearchContractError(
                f"condition {condition.condition_id!r} must describe exactly one changed factor"
            )
        elif condition.condition_type == "perturbation" and (
            not condition.changed_factors
            or not all(factor.strip() for factor in condition.changed_factors)
        ):
            raise ResearchContractError(
                f"perturbation {condition.condition_id!r} must name its injected factor(s)"
            )
        if condition.applies_to_ground_truth:
            raise ResearchContractError(
                f"condition {condition.condition_id!r} must not perturb approved ground truth"
            )
        if condition.uses_audio_v2:
            raise ResearchContractError(
                f"condition {condition.condition_id!r} references prohibited Audio V2"
            )
    if baseline_count != 1:
        raise ResearchContractError("exactly one unchanged baseline condition is required")


def require_identical_tick_log_bytes(baseline: bytes, candidate: bytes) -> None:
    """Raise unless two already-produced tick logs are byte-identical.

    This comparator performs no replay, timing, parsing, or performance analysis.
    """
    if not isinstance(baseline, bytes) or not isinstance(candidate, bytes):
        raise TypeError("tick logs must be supplied as bytes")
    if not baseline or not candidate:
        raise ResearchContractError("tick logs must be nonempty; missing/empty logs are not evidence")
    if baseline != candidate:
        raise ResearchContractError("tick-log byte-equivalence check failed")


def missing_phase15_prerequisites(
    *,
    phases_12_14_complete: bool = False,
    researcher_authorized: bool = False,
    site_access_authorized: bool = False,
    safety_case_approved: bool = False,
) -> tuple[str, ...]:
    """List absent Phase 15 prerequisites; never performs or authorizes activity.

    The booleans are caller assertions for a checklist only and are not evidence
    of authorization. The Phase 15 plan's conditional hardware prerequisite is
    intentionally omitted because hardware may not be applicable.
    """
    values = (
        ("phases_12_14_complete", phases_12_14_complete),
        ("researcher_authorized", researcher_authorized),
        ("site_access_authorized", site_access_authorized),
        ("safety_case_approved", safety_case_approved),
    )
    _validate_boolean_flags(values)
    return tuple(name for name, present in values if not present)


def missing_phase16_prerequisites(
    *,
    required_phase_evidence_complete: bool = False,
    publication_scope_decided: bool = False,
) -> tuple[str, ...]:
    """List Phase 16 blockers; a complete checklist is not publication approval."""
    values = (
        ("required_phase_evidence_complete", required_phase_evidence_complete),
        ("publication_scope_decided", publication_scope_decided),
    )
    _validate_boolean_flags(values)
    return tuple(name for name, present in values if not present)


_RAW_MEDIA_SUFFIXES = {".avi", ".m4a", ".mkv", ".mov", ".mp3", ".mp4", ".wav"}
_FORBIDDEN_EVIDENCE_SUFFIX = "models/audio/best_checkpoint.pt"


def _contains_data_raw_component(path: str) -> bool:
    """Recognize a data/raw segment after normalizing separators and case."""
    parts = [part for part in path.replace("\\", "/").lower().split("/") if part not in {"", "."}]
    return any(left == "data" and right == "raw" for left, right in zip(parts, parts[1:]))


def audit_evidence_references(
    repository_root: Path,
    claim_references: Mapping[str, Sequence[str]],
) -> None:
    """Check that claim references resolve inside the repo and avoid raw media.

    Passing this check establishes only path traceability—not that an artifact
    actually supports a claim. Human/researcher review remains necessary.
    """
    try:
        root = Path(repository_root).resolve(strict=True)
    except (OSError, RuntimeError, TypeError) as exc:
        raise ResearchContractError("repository root must resolve to an existing directory") from exc
    if not root.is_dir():
        raise ResearchContractError(f"repository root is not a directory: {root}")
    if not isinstance(claim_references, Mapping) or not claim_references:
        raise ResearchContractError("evidence audit must contain at least one claim")

    for claim_id, references in claim_references.items():
        if not isinstance(claim_id, str) or not claim_id.strip():
            raise ResearchContractError("claim IDs must be nonempty strings")
        if isinstance(references, (str, bytes)) or not isinstance(references, Sequence):
            raise ResearchContractError(f"claim {claim_id!r} references must be a sequence")
        if not references:
            raise ResearchContractError(f"claim {claim_id!r} has no evidence references")
        for reference in references:
            if not isinstance(reference, str) or not reference.strip():
                raise ResearchContractError(f"claim {claim_id!r} has an empty reference")
            normalized = reference.replace("\\", "/").strip()
            windows_path = PureWindowsPath(reference)
            if (
                "\x00" in reference
                or Path(normalized).is_absolute()
                or windows_path.is_absolute()
                or bool(windows_path.drive)
            ):
                raise ResearchContractError("evidence references must be repository-relative")
            normalized = normalized.lstrip("/")
            normalized_lower = normalized.lower()
            if (
                _contains_data_raw_component(normalized_lower)
                or Path(normalized_lower).suffix in _RAW_MEDIA_SUFFIXES
            ):
                raise ResearchContractError(
                    f"raw media cannot be cited as a public evidence reference: {reference!r}"
                )
            if normalized_lower.endswith(_FORBIDDEN_EVIDENCE_SUFFIX):
                raise ResearchContractError("Audio V2 checkpoint is prohibited as valid-model evidence")
            try:
                resolved = (root / Path(normalized)).resolve(strict=True)
            except (OSError, RuntimeError, ValueError) as exc:
                raise ResearchContractError(
                    f"evidence reference does not resolve: {reference!r}"
                ) from exc
            if not resolved.is_relative_to(root):
                raise ResearchContractError(
                    f"evidence reference escapes repository root: {reference!r}"
                )
            resolved_relative = resolved.relative_to(root).as_posix().lower()
            if _contains_data_raw_component(resolved_relative) or Path(
                resolved_relative
            ).suffix in _RAW_MEDIA_SUFFIXES:
                raise ResearchContractError(
                    f"raw media cannot be cited as a public evidence reference: {reference!r}"
                )
            if resolved_relative.endswith(_FORBIDDEN_EVIDENCE_SUFFIX):
                raise ResearchContractError("Audio V2 checkpoint is prohibited as valid-model evidence")
            if not resolved.is_file():
                raise ResearchContractError(
                    f"evidence reference is not a file: {reference!r}"
                )
