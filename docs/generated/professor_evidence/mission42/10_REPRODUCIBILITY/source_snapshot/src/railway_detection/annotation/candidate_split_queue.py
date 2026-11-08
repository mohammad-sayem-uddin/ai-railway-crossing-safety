"""Read-only candidate event split and Stage-2.1 review queue reports.

This module deliberately stops short of making a research decision.  It reads
the independently-produced event inventory, the active *candidate* proposal
for each event, and review records, then emits deterministic reports that a
researcher can inspect.  It never writes below ``data/ground_truth`` and never
turns a proposal (or a legacy review) into a label.

The event identity used throughout is ``<cohort>/<event_id>``.  Bare event
ids are unsafe here because ``event_001`` occurs in all three Layer-B cohorts.
All hashes in the reports are SHA-256 hashes of the exact bytes read, or of a
canonical JSON representation for derived report identifiers.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from railway_detection.annotation.notices import verify_invalidation_notice
from railway_detection.annotation.stage2_1_schema import (
    STAGE_2_1_SCHEMA_VERSION,
    build_stage2_1_record_from_dict,
)
from railway_detection.safety.media_guard import require_media_authorization

REPORT_VERSION = "candidate-event-split-and-stage21-queue/4"
SPLIT_REPORT_VERSION = "candidate-event-split-proposal/4"
QUEUE_REPORT_VERSION = "stage21-review-queue/4"
COHORTS = ("train_events", "no_train_events", "engine_events")
DEFAULT_RATIOS = {"train": 0.6, "val": 0.2, "test": 0.2}
_PROPOSAL_RE = re.compile(r"^(?P<event>.+?)_proposal(?:_v(?P<version>[0-9]+))?$")
_CANONICAL_BOUNDARIES = (
    "T0_first_visible",
    "T1_danger_zone_entry",
    "T2_crossing_occupancy_start",
    "T3_locomotive_unit_clearance",
    "T4_tail_clearance",
    "T_scene_clear",
)
_BOUNDARY_ALIASES = {"T3_locomotive_exit": "T3_locomotive_unit_clearance"}
_STAGE21_REQUIRED_FIELDS = (
    "schema_version",
    "review_id",
    "event_id",
    "cohort",
    "proposal_reference.proposal_file",
    "proposal_reference.proposal_sha256",
    "reviewer_metadata.reviewer_id",
    "reviewer_metadata.review_session_id",
    "reviewer_metadata.review_start_utc",
    "reviewer_metadata.review_end_utc",
    "reviewer_metadata.inspection_tool",
    "model_independence_attestation.attested",
    "model_independence_attestation.statement",
    "model_independence_attestation.attested_at_utc",
    "reviewer_observed_media_hashes.front_sha256",
    "reviewer_observed_media_hashes.back_sha256",
    "reviewer_observed_media_hashes.observed_at_utc",
    *(f"boundary_adjudications.{name}" for name in _CANONICAL_BOUNDARIES),
    "adjudication_status",
    "adjudication_history",
)


class CandidateReportError(ValueError):
    """Raised when report inputs are malformed or unsafe."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    require_media_authorization(path, "HASH_RAW_MEDIA")
    return _sha256_bytes(path.read_bytes())


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _derived_hash(value: Any) -> str:
    return _sha256_bytes(_canonical(value))


def _read_json(path: Path) -> tuple[Any, str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CandidateReportError(f"could not read {path}: {exc}") from exc
    try:
        return json.loads(raw), _sha256_bytes(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateReportError(f"invalid JSON in {path}: {exc}") from exc


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _identity(cohort: str, event_id: str) -> str:
    if not cohort or not event_id:
        raise CandidateReportError("cohort and event_id must be non-empty")
    return f"{cohort}/{event_id}"


def _inventory_entries(inventory: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(inventory, Mapping):
        raise CandidateReportError("event inventory must be a JSON object")
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for key in sorted(inventory):
        raw = inventory[key]
        if not isinstance(raw, Mapping):
            raise CandidateReportError(f"inventory entry {key!r} must be an object")
        parts = str(key).split("/", 1)
        cohort = str(raw.get("category") or (parts[0] if len(parts) == 2 else ""))
        event_id = str(raw.get("event_id") or (parts[1] if len(parts) == 2 else ""))
        event_key = _identity(cohort, event_id)
        if event_key in seen:
            raise CandidateReportError(f"duplicate cohort-qualified event identity: {event_key}")
        seen.add(event_key)
        entries.append(
            {
                "event_key": event_key,
                "cohort": cohort,
                "event_id": event_id,
                "inventory": dict(raw),
            }
        )
    if not entries:
        raise CandidateReportError("event inventory contains no events")
    return entries


def _proposal_candidates(proposals_dir: Path) -> dict[str, list[tuple[int, Path]]]:
    found: dict[str, list[tuple[int, Path]]] = {}
    if not proposals_dir.is_dir():
        return found
    for path in sorted(proposals_dir.rglob("*.json")):
        match = _PROPOSAL_RE.match(path.stem)
        if not match or path.parent.name not in COHORTS:
            continue
        version = int(match.group("version") or 1)
        key = _identity(path.parent.name, match.group("event"))
        found.setdefault(key, []).append((version, path))
    return found


def _active_proposals(proposals_dir: Path) -> dict[str, tuple[int, Path, str, Any]]:
    active: dict[str, tuple[int, Path, str, Any]] = {}
    for key, options in _proposal_candidates(proposals_dir).items():
        version, path = max(options, key=lambda pair: (pair[0], pair[1].name))
        try:
            value, digest = _read_json(path)
        except CandidateReportError:
            # Preserve the active path and hash where possible; queue generation
            # reports malformed proposals rather than silently selecting an older one.
            digest = _sha256_file(path)
            value = None
        active[key] = (version, path, digest, value)
    return active


def _validate_ratios(ratios: Mapping[str, float]) -> dict[str, float]:
    if set(ratios) != {"train", "val", "test"}:
        raise CandidateReportError("ratios must contain exactly train, val, and test")
    result = {name: float(ratios[name]) for name in ("train", "val", "test")}
    if any(value <= 0 or value >= 1 for value in result.values()) or abs(sum(result.values()) - 1.0) > 1e-9:
        raise CandidateReportError("ratios must be positive and sum to 1")
    return result


def _candidate_boundary_evidence(proposal: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Describe candidate boundary states without converting them into labels."""
    timestamps = proposal.get("proposed_timestamps", {}) if proposal else {}
    if not isinstance(timestamps, Mapping):
        timestamps = {}
    normalized = {_BOUNDARY_ALIASES.get(str(key), str(key)): value for key, value in timestamps.items()}
    result: dict[str, dict[str, Any]] = {}
    for name in _CANONICAL_BOUNDARIES:
        raw = normalized.get(name)
        if not isinstance(raw, Mapping):
            result[name] = {
                "candidate_status": "CANDIDATE_FIELD_MISSING",
                "value_s": None,
                "reference_camera": None,
                "rationale": "No canonical candidate field exists; researcher must adjudicate from source evidence.",
            }
            continue
        rationale = str(raw.get("rationale", ""))
        rationale_lower = rationale.lower()
        value = raw.get("value_s")
        if raw.get("applicable") is False:
            status = "CANDIDATE_NOT_APPLICABLE"
        elif value is None:
            if any(token in rationale_lower for token in ("left-censor", "left censor")):
                status = "CANDIDATE_CENSORED_LEFT"
            elif any(token in rationale_lower for token in ("right-censor", "right censor", "recording terminates", "still visible")):
                status = "CANDIDATE_CENSORED_RIGHT"
            else:
                status = "CANDIDATE_UNOBSERVABLE_OR_UNRESOLVED"
        elif raw.get("ambiguity_flag"):
            status = "CANDIDATE_AMBIGUOUS"
        elif raw.get("candidate_observable") is False:
            status = "CANDIDATE_UNOBSERVABLE_OR_UNRESOLVED"
        else:
            status = "CANDIDATE_OBSERVABLE_UNAPPROVED"
        result[name] = {
            "candidate_status": status,
            "value_s": value,
            "reference_camera": raw.get("reference_camera"),
            "rationale": rationale,
        }
    return result


def _partition_counts(total: int, ratios: Mapping[str, float]) -> dict[str, int]:
    if total < 3:
        raise CandidateReportError("at least three events are required for train/val/test")
    names = ("train", "val", "test")
    raw = {name: total * ratios[name] for name in names}
    counts = {name: max(1, int(raw[name])) for name in names}
    while sum(counts.values()) > total:
        candidate = max((name for name in names if counts[name] > 1), key=lambda n: raw[n] - int(raw[n]))
        counts[candidate] -= 1
    while sum(counts.values()) < total:
        candidate = max(names, key=lambda n: raw[n] - counts[n])
        counts[candidate] += 1
    return counts


def build_candidate_event_split(
    inventory: Mapping[str, Any],
    *,
    proposals_dir: Path | str | None = None,
    root: Path | str = ".",
    ratios: Mapping[str, float] | None = None,
    inventory_path: Path | str | None = None,
) -> dict[str, Any]:
    """Build a deterministic, explicitly unapproved event split proposal.

    Assignment is based on a SHA-256 ordering of cohort-qualified event ids;
    no random state or wall-clock value is used.  Existing grouping metadata is
    reported, but when one crossing/session spans roles the proposal is marked
    ``leakage_safe: false`` rather than pretending a group-disjoint split exists.
    """
    root_path = Path(root).resolve()
    entries = _inventory_entries(inventory)
    selected_ratios = _validate_ratios(ratios or DEFAULT_RATIOS)
    proposals = _active_proposals(Path(proposals_dir)) if proposals_dir else {}
    enriched: list[dict[str, Any]] = []
    for entry in entries:
        key = entry["event_key"]
        active = proposals.get(key)
        proposal_value = active[3] if active else None
        site = proposal_value.get("proposed_site_metadata", {}) if isinstance(proposal_value, Mapping) else {}
        crossing = site.get("crossing_id") if isinstance(site, Mapping) else None
        session = site.get("recording_session_id") if isinstance(site, Mapping) else None
        group = crossing or session
        enriched.append(
            {
                "event_key": key,
                "cohort": entry["cohort"],
                "event_id": entry["event_id"],
                "group_id": group,
                "group_field": "crossing_id" if crossing else ("recording_session_id" if session else None),
                "active_proposal": (
                    {
                        "path": _relative(root_path, active[1]),
                        "sha256": active[2],
                        "version": active[0],
                    }
                    if active
                    else None
                ),
            }
        )
    ordered = sorted(
        enriched,
        key=lambda item: (_derived_hash(item["event_key"]), item["event_key"]),
    )
    counts = _partition_counts(len(ordered), selected_ratios)
    partitions: dict[str, list[str]] = {name: [] for name in ("train", "val", "test")}
    cursor = 0
    for role in partitions:
        selected = ordered[cursor : cursor + counts[role]]
        partitions[role] = sorted(item["event_key"] for item in selected)
        cursor += counts[role]
    event_roles = {
        event_key: role for role, ids in partitions.items() for event_key in ids
    }
    grouping_checks: dict[str, dict[str, Any]] = {}
    grouping_metadata_missing: dict[str, list[str]] = {}
    for field in ("crossing_id", "recording_session_id"):
        group_roles: dict[str, set[str]] = {}
        group_events: dict[str, list[str]] = {}
        missing_groups: list[str] = []
        for item in enriched:
            active = proposals.get(item["event_key"])
            proposal_value = active[3] if active else None
            site = proposal_value.get("proposed_site_metadata", {}) if isinstance(proposal_value, Mapping) else {}
            value = site.get(field) if isinstance(site, Mapping) else None
            if not isinstance(value, str) or not value.strip():
                missing_groups.append(item["event_key"])
                continue
            group_events.setdefault(value, []).append(item["event_key"])
            group_roles.setdefault(value, set()).add(event_roles[item["event_key"]])
        overlapping = {
            group: {
                "roles": sorted(roles),
                "events_by_role": {
                    role: sorted(key for key in group_events[group] if event_roles[key] == role)
                    for role in sorted(roles)
                },
            }
            for group, roles in group_roles.items()
            if len(roles) > 1
        }
        grouping_checks[field] = {
            "overlapping_groups": overlapping,
            "events_missing_group_metadata": sorted(missing_groups),
            "leakage_safe": not overlapping and not missing_groups,
        }
        grouping_metadata_missing[field] = sorted(missing_groups)
    events_missing_any_group_metadata = sorted(
        set().union(*(set(keys) for keys in grouping_metadata_missing.values()))
    )
    all_grouping_safe = all(check["leakage_safe"] for check in grouping_checks.values())
    body: dict[str, Any] = {
        "schema_version": SPLIT_REPORT_VERSION,
        "status": "CANDIDATE_ONLY",
        "approval_status": "NOT_APPROVED",
        "purpose": "Deterministic event-level split proposal for researcher review; not an execution decision.",
        "ratios": selected_ratios,
        "algorithm": "sha256(cohort/event_id) ordering with largest-remainder counts",
        "source_inventory": {
            "path": (_relative(root_path, Path(inventory_path)) if inventory_path else None),
            # When called with a parsed mapping, this canonical digest still
            # binds the exact values supplied. The CLI additionally supplies
            # the raw-file path so its byte hash is used.
            "sha256": (
                _sha256_file(Path(inventory_path))
                if inventory_path and Path(inventory_path).is_file()
                else _derived_hash(inventory)
            ),
        },
        "events": enriched,
        "partitions": partitions,
        "grouping": {
            "checks_by_field": grouping_checks,
            "events_missing_any_group_metadata": events_missing_any_group_metadata,
            "leakage_safe": all_grouping_safe,
            "warning": (
                "At least one crossing_id or recording_session_id group spans roles, or group metadata is missing; this candidate is not leakage-safe."
                if not all_grouping_safe
                else None
            ),
        },
        "researcher_decision": None,
    }
    body["proposal_id"] = "candidate-split-" + _derived_hash(body)[:16]
    body["proposal_sha256"] = _derived_hash(body)
    return body


def _source(root: Path, path: Path | None, kind: str) -> dict[str, Any]:
    if path is None:
        return {"kind": kind, "path": None, "sha256": None}
    rel = _relative(root, path)
    if not path.is_file():
        return {"kind": kind, "path": rel, "sha256": None}
    return {"kind": kind, "path": rel, "sha256": _sha256_file(path)}


def _queue_category(reasons: list[str], *, has_review: bool) -> str:
    if any(code.startswith(("INVALID", "LEGACY", "RECORD_INVALIDATED", "REVIEW_JSON")) for code in reasons):
        return "INVALID"
    if any(code.startswith(("CONFLICT", "STALE", "UNRESOLVED", "FINAL_REJECTION")) for code in reasons):
        return "CONFLICT"
    if not has_review:
        return "MISSING"
    if reasons:
        return "INCOMPLETE"
    return "COMPLETE"


def build_stage21_review_queue(
    root: Path | str = ".",
    *,
    inventory_path: Path | str = "data/manifests/layer_b_v2_annotation_inventory.json",
    proposals_dir: Path | str = "data/ground_truth/proposals",
    reviews_dir: Path | str = "data/ground_truth/reviews",
) -> dict[str, Any]:
    """Build a deterministic queue of records needing genuine Stage-2.1 review."""
    root_path = Path(root).resolve()
    inventory_file = Path(inventory_path)
    if not inventory_file.is_absolute():
        inventory_file = root_path / inventory_file
    proposal_root = Path(proposals_dir)
    if not proposal_root.is_absolute():
        proposal_root = root_path / proposal_root
    reviews_root = Path(reviews_dir)
    if not reviews_root.is_absolute():
        reviews_root = root_path / reviews_root
    inventory, inventory_hash = _read_json(inventory_file)
    entries = _inventory_entries(inventory)
    active = _active_proposals(proposal_root)
    items: list[dict[str, Any]] = []
    for entry in entries:
        key, cohort, event_id = entry["event_key"], entry["cohort"], entry["event_id"]
        review_path = reviews_root / cohort / f"{event_id}_review.json"
        notice_path = reviews_root / cohort / f"{event_id}_review.INVALIDATION_NOTICE.json"
        active_entry = active.get(key)
        reasons: list[str] = []
        details: list[str] = []
        review_value: Any = None
        review_hash: str | None = None
        has_review = review_path.is_file()
        if not has_review:
            reasons.append("MISSING_REVIEW_RECORD")
            details.append("No review JSON exists at the cohort-qualified expected path.")
        if active_entry and not isinstance(active_entry[3], Mapping):
            reasons.append("INVALID_ACTIVE_PROPOSAL")
            details.append("Active candidate proposal could not be parsed as a JSON object.")
        if has_review:
            try:
                review_value, review_hash = _read_json(review_path)
            except CandidateReportError as exc:
                reasons.append("REVIEW_JSON_UNREADABLE")
                details.append(str(exc))
        notice_verification = None
        if notice_path.is_file():
            notice_verification = verify_invalidation_notice(notice_path, reviews_root)
            if notice_verification.valid:
                reasons.append("RECORD_INVALIDATED")
                details.append("A verified legacy invalidation notice applies; record remains untouched and unusable.")
            else:
                reasons.append("INVALIDATION_NOTICE_INVALID")
                details.append(notice_verification.problem or "invalidation notice failed verification")
        if isinstance(review_value, Mapping):
            if review_value.get("event_id") != event_id or review_value.get("cohort") not in (None, cohort):
                reasons.append("CONFLICT_RECORD_IDENTITY")
                details.append("Review event/cohort identity does not match its cohort-qualified path.")
            if review_value.get("schema_version") != STAGE_2_1_SCHEMA_VERSION:
                reasons.append("LEGACY_SCHEMA" if review_value.get("schema_version") else "INVALID_SCHEMA")
                details.append(f"schema_version is {review_value.get('schema_version')!r}, not Stage-2.1.")
            else:
                try:
                    built = build_stage2_1_record_from_dict(dict(review_value))
                except Exception as exc:  # schema errors are intentionally summarized in the queue
                    text = str(exc)
                    code = "INCOMPLETE_STAGE21_RECORD" if any(
                        token in text.lower() for token in ("missing", "required", "non-empty")
                    ) else "INVALID_STAGE21_RECORD"
                    reasons.append(code)
                    details.append(text)
                else:
                    if built.adjudication_status in {"NEEDS_SECOND_REVIEW", "DISPUTED"}:
                        reasons.append("UNRESOLVED_ADJUDICATION")
                        details.append(f"adjudication_status is {built.adjudication_status}.")
                    elif built.adjudication_status == "REJECTED":
                        reasons.append("FINAL_REJECTION_NOT_APPROVED")
                        details.append("Record is resolved as REJECTED and cannot serve as approved ground truth.")
            reference = review_value.get("proposal_reference") or {}
            if active_entry and isinstance(reference, Mapping):
                if reference.get("proposal_sha256") != active_entry[2]:
                    reasons.append("STALE_PROPOSAL_REFERENCE")
                    details.append("Review references a proposal hash different from the active candidate proposal.")
            elif not active_entry:
                reasons.append("MISSING_ACTIVE_PROPOSAL")
                details.append("No candidate proposal was found for this cohort-qualified event.")
        # Compare candidate input-media hashes to the independent inventory,
        # but never infer or fill an annotation value from either source.
        if active_entry and isinstance(active_entry[3], Mapping):
            proposed_media = ((active_entry[3].get("ai_assistant_metadata") or {}).get("input_media_files") or [])
            expected_media = {
                "camera_front.mov": (entry["inventory"].get("front") or {}).get("sha256"),
                "camera_back.mov": (entry["inventory"].get("back") or {}).get("sha256"),
            }
            for media in proposed_media if isinstance(proposed_media, list) else []:
                if (
                    isinstance(media, Mapping)
                    and media.get("file_name") in expected_media
                    and media.get("sha256") != expected_media[media["file_name"]]
                ):
                    reasons.append("CONFLICT_PROPOSAL_MEDIA_HASH")
                    details.append(
                        f"Active proposal media hash disagrees with inventory for {media.get('file_name')}."
                    )
        elif has_review and review_value is not None:
            reasons.append("INVALID_REVIEW_SHAPE")
            details.append("Review JSON top level is not an object.")
        category = _queue_category(reasons, has_review=has_review)
        valid_stage21_record = (
            isinstance(review_value, Mapping)
            and review_value.get("schema_version") == STAGE_2_1_SCHEMA_VERSION
            and "INVALID_STAGE21_RECORD" not in reasons
            and "INCOMPLETE_STAGE21_RECORD" not in reasons
        )
        proposal_value = active_entry[3] if active_entry and isinstance(active_entry[3], Mapping) else None
        media_sources = {
            camera: {
                "path": (entry["inventory"].get(camera) or {}).get("path"),
                "sha256": (entry["inventory"].get(camera) or {}).get("sha256"),
            }
            for camera in ("front", "back")
        }
        review_fields = [] if valid_stage21_record else list(_STAGE21_REQUIRED_FIELDS)
        if proposal_value is None:
            details.append("No usable active proposal is available; researcher must inspect source media and document every required boundary independently.")
        human_actions = [
            "Do not edit or migrate the invalidated legacy review; create a new genuine Stage-2.1 review through the researcher-operated workflow.",
            "Independently inspect the cohort-qualified front and back source media and adjudicate all six canonical boundary states, including censoring, uncertainty, or not-applicable status where evidence supports it.",
            "Inspect the active candidate proposal as a navigation aid only; verify or correct every candidate value from source evidence, not model predictions.",
            "Complete the required human audio/listening check for train-horn evidence when applicable, then record the actually observed result.",
            "Record individually attributable reviewer/session metadata, model-independence attestation, and reviewer-observed live media hashes in the Stage-2.1 workflow.",
            "Resolve any required second review/adjudication under the researcher-approved D1/D3 workflow before promotion.",
        ]
        workflow_prerequisites = [
            {
                "decision": "D1 review-duration thresholds",
                "status": "PENDING_RESEARCHER_DECISION",
                "action": "Run a genuine review pilot and let the researcher set the hard floor and fast-session upper threshold from observed timings; do not invent numeric thresholds.",
                "source": "docs/PHASE11_3_RESEARCHER_DECISIONS.md",
            },
            {
                "decision": "D3(a) second-review trigger",
                "status": "PENDING_RESEARCHER_DECISION",
                "action": "Researcher selects when an independent second review is mandatory before formal production review.",
                "source": "docs/PHASE11_3_RESEARCHER_DECISIONS.md",
            },
            {
                "decision": "D3(c) clear-boundary audit",
                "status": "PENDING_RESEARCHER_DECISION",
                "action": "Researcher specifies the audit mechanism and frequency for boundaries marked clear.",
                "source": "docs/PHASE11_3_RESEARCHER_DECISIONS.md",
            },
            {
                "decision": "ADJ-AUTH / production review authorization",
                "status": "NOT_RECORDED",
                "action": "Obtain explicit researcher authorization for genuine Stage-2.1 review/adjudication before producing real records.",
                "source": "docs/PHASE11_12_ADJUDICATION_CLOSURE_REPORT.md",
            },
        ]
        sources = [
            _source(root_path, inventory_file, "event_inventory"),
            _source(root_path, active_entry[1] if active_entry else None, "active_candidate_proposal"),
            _source(root_path, review_path if review_path.is_file() else None, "review_record"),
            _source(root_path, notice_path if notice_path.is_file() else None, "invalidation_notice"),
        ]
        # A fully valid approved record is intentionally represented in the
        # report for auditability, but is not a review task.
        queue_id = "stage21-review-" + _derived_hash({"event_key": key, "category": category, "reasons": sorted(set(reasons)), "sources": sources})[:20]
        items.append({
            "queue_id": queue_id,
            "event_key": key,
            "cohort": cohort,
            "event_id": event_id,
            "queue_category": category,
            "needs_human_action": category != "COMPLETE",
            "reason_codes": sorted(set(reasons)),
            "details": sorted(set(details)),
            "active_candidate_proposal": (
                {"path": _relative(root_path, active_entry[1]), "version": active_entry[0], "sha256": active_entry[2]}
                if active_entry else None
            ),
            "review_record_sha256": review_hash,
            "stage21_review_status": (
                "VALID_STAGE21_RECORD_PRESENT" if valid_stage21_record else "NEW_STAGE21_RECORD_REQUIRED"
            ),
            "missing_fields": review_fields,
            "required_human_actions": human_actions,
            "workflow_prerequisites": workflow_prerequisites,
            "candidate_boundary_evidence": _candidate_boundary_evidence(proposal_value),
            "source_media": media_sources,
            "inventory_media_sha256": {
                "front": (entry["inventory"].get("front") or {}).get("sha256"),
                "back": (entry["inventory"].get("back") or {}).get("sha256"),
            },
            "sources": sources,
        })
    items.sort(key=lambda item: item["event_key"])
    counts = Counter(item["queue_category"] for item in items)
    body: dict[str, Any] = {
        "schema_version": QUEUE_REPORT_VERSION,
        "status": "CANDIDATE_ONLY",
        "approval_status": "NOT_APPROVED",
        "purpose": "Deterministic read-only queue for researcher review; lists missing Stage-2.1 fields, source bindings, candidate-only boundary evidence, and required human actions.",
        "source_inventory": {"path": _relative(root_path, inventory_file), "sha256": inventory_hash},
        "items": items,
        "summary": {
            "total_events": len(items),
            "counts_by_category": {name: counts.get(name, 0) for name in ("MISSING", "INVALID", "CONFLICT", "INCOMPLETE", "COMPLETE")},
            "actionable_events": sum(1 for item in items if item["needs_human_action"]),
        },
        "provenance_note": "Hashes bind observed source bytes; no proposal value is promoted or fabricated as a label.",
    }
    body["queue_sha256"] = _derived_hash(body)
    return body


def _write_report(report: Mapping[str, Any], output_path: Path | str, root: Path | str) -> Path:
    destination = Path(output_path).resolve()
    root_path = Path(root).resolve()
    protected = [root_path / "data" / "ground_truth", root_path / "data" / "raw"]
    if any(destination == path.resolve() or path.resolve() in destination.parents for path in protected):
        raise CandidateReportError(f"refusing to write candidate report inside protected evidence path: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def write_candidate_event_split(path: Path | str, report: Mapping[str, Any], *, root: Path | str = ".") -> Path:
    return _write_report(report, path, root)


def write_stage21_review_queue(path: Path | str, report: Mapping[str, Any], *, root: Path | str = ".") -> Path:
    return _write_report(report, path, root)


def render_stage21_review_queue_markdown(report: Mapping[str, Any]) -> str:
    """Render an actionable human queue while keeping candidate evidence unapproved."""
    summary = report.get("summary", {})
    lines = [
        "# Stage-2.1 Human Review Queue",
        "",
        "> **Candidate review aid only — not an annotation, approval, promotion receipt, or authorization.**",
        "",
        f"- Status: `{report.get('status', 'UNKNOWN')}` / `{report.get('approval_status', 'UNKNOWN')}`",
        f"- Events: {summary.get('total_events', 0)}; human action required: {summary.get('actionable_events', 0)}",
        f"- Inventory: `{(report.get('source_inventory') or {}).get('path')}` SHA-256 `{(report.get('source_inventory') or {}).get('sha256')}`",
        "- Every entry below requires a new genuine Stage-2.1 record. Invalidated legacy records are not migrated or edited.",
        "",
    ]
    for item in report.get("items", []):
        lines.extend(
            [
                f"## {item['event_key']}",
                "",
                f"- Cohort: `{item['cohort']}`; queue: `{item['queue_category']}`; Stage-2.1: `{item.get('stage21_review_status')}`",
                f"- Reasons: {', '.join(f'`{code}`' for code in item.get('reason_codes', [])) or 'none'}",
                f"- Active candidate proposal: `{(item.get('active_candidate_proposal') or {}).get('path')}` SHA-256 `{(item.get('active_candidate_proposal') or {}).get('sha256')}`",
                "- Source media:",
            ]
        )
        for camera, media in sorted((item.get("source_media") or {}).items()):
            lines.append(f"  - {camera}: `{media.get('path')}` SHA-256 `{media.get('sha256')}`")
        lines.extend(["- Missing Stage-2.1 fields:"])
        lines.extend(f"  - `{field}`" for field in item.get("missing_fields", []))
        lines.extend(["- Candidate boundary evidence (unapproved):"])
        for name, evidence in sorted((item.get("candidate_boundary_evidence") or {}).items()):
            lines.append(
                f"  - `{name}`: `{evidence.get('candidate_status')}`, value `{evidence.get('value_s')}`, "
                f"camera `{evidence.get('reference_camera')}`; {evidence.get('rationale') or 'No proposal rationale.'}"
            )
        lines.extend(["- Required human actions:"])
        lines.extend(f"  - {action}" for action in item.get("required_human_actions", []))
        lines.extend(["- Workflow prerequisites (not resolved by this queue):"])
        for prerequisite in item.get("workflow_prerequisites", []):
            lines.append(
                f"  - `{prerequisite['decision']}`: `{prerequisite['status']}` — "
                f"{prerequisite['action']} Source: `{prerequisite['source']}`."
            )
        lines.extend([""])
    return "\n".join(lines)


def write_stage21_review_queue_markdown(path: Path | str, report: Mapping[str, Any], *, root: Path | str = ".") -> Path:
    destination = Path(path).resolve()
    root_path = Path(root).resolve()
    protected = [root_path / "data" / "ground_truth", root_path / "data" / "raw"]
    if any(destination == guard.resolve() or guard.resolve() in destination.parents for guard in protected):
        raise CandidateReportError(f"refusing to write candidate report inside protected evidence path: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_stage21_review_queue_markdown(report), encoding="utf-8")
    return destination


# Descriptive aliases for callers and scripts that use "proposal"/"report"
# terminology.  Keeping these as aliases avoids a second implementation path.
build_candidate_split_proposal = build_candidate_event_split
build_candidate_event_split_proposal = build_candidate_event_split
build_review_queue = build_stage21_review_queue
build_stage21_review_queue_report = build_stage21_review_queue
write_candidate_split_report = write_candidate_event_split
write_candidate_event_split_proposal = write_candidate_event_split
write_review_queue_report = write_stage21_review_queue
