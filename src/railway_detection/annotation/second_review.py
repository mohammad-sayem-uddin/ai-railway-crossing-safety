"""Mission 10, WP10.4: RD-043 second-review enforcement on real Stage-2.1 records.

Metadata only: this module reads review-record dictionaries, the allowlist and (optionally) the
immutable proposal JSON a record is bound to. It never opens media and never writes anything.

Trigger set (the *proposed* GOV-REVIEW-SECOND-REVIEW-TRIGGERS policy, still PENDING a researcher
adoption; enforcing it is stricter than not enforcing it, so it is applied fail-closed):

1. ``EXPLICIT_REVIEWER_FLAG``  -- status ``DISPUTED`` or ``NEEDS_SECOND_REVIEW``
2. ``UNCERTAIN_BOUNDARY``      -- any boundary adjudicated ``UNCERTAIN``
3. ``ENGINE_T3_T4_INTERPRETATION`` -- engine cohort with an interpreted T3/T4 boundary
4. ``FRONT_BACK_CONFLICT``     -- NOT mechanically detectable (the schema has no structured
   conflict field); a reviewer who sees one must set ``NEEDS_SECOND_REVIEW`` (trigger 1)
5. ``MEDIA_HASH_MISSING_OR_INCONSISTENT`` -- the reviewer-observed hashes are absent from, or differ
   from, the independently verified inventory registry
6. ``CORRECTED_FROM_CANDIDATE`` -- a boundary differs from the bound AI proposal's candidate
   (or the bound proposal cannot be verified)

``CENSORED`` alone and ``UNOBSERVABLE_NOT_APPLICABLE`` alone are NOT triggers. There is no timestamp
tolerance (RD-012 is deferred): two reviews agree only when states, reference cameras and
1-microsecond-normalized values are identical. The review-duration floor (RD-046 deferred) stays
what it already is -- a schema plausibility rejection, not a trigger.

Agreement between two reviews never replaces adjudication: the primary record's own human
``APPROVED`` status is unchanged, and agreement only satisfies the *precondition* that an
independent second review exists. A disagreement stays unresolved (the event is effectively
``UNCERTAIN``) because the format of a recorded researcher adjudication (RD-045) has not been
adopted; no code path here can clear it.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from railway_detection.annotation.schemas import CANONICAL_TIMESTAMPS, LEGACY_TIMESTAMP_ALIASES

TRIGGER_EXPLICIT_FLAG = "EXPLICIT_REVIEWER_FLAG"
TRIGGER_UNCERTAIN_BOUNDARY = "UNCERTAIN_BOUNDARY"
TRIGGER_ENGINE_T3_T4 = "ENGINE_T3_T4_INTERPRETATION"
TRIGGER_MEDIA_HASH = "MEDIA_HASH_MISSING_OR_INCONSISTENT"
TRIGGER_CORRECTED = "CORRECTED_FROM_CANDIDATE"

#: Triggers the code evaluates mechanically.
EVALUATED_TRIGGERS = (
    TRIGGER_EXPLICIT_FLAG,
    TRIGGER_UNCERTAIN_BOUNDARY,
    TRIGGER_ENGINE_T3_T4,
    TRIGGER_MEDIA_HASH,
    TRIGGER_CORRECTED,
)
#: Triggers that exist in the proposal but cannot be evaluated from a record (disclosed limitation).
NOT_MECHANICALLY_EVALUABLE = ("FRONT_BACK_CONFLICT",)

_FLAG_STATUSES = frozenset({"DISPUTED", "NEEDS_SECOND_REVIEW"})
_ENGINE_BOUNDARIES = ("T3_locomotive_unit_clearance", "T4_tail_clearance")
_ENGINE_COHORT = "engine_events"
#: Boundary states that count as an *interpretation* for the engine T3/T4 trigger.
_INTERPRETED_STATES = frozenset({"OBSERVABLE", "CENSORED", "UNCERTAIN"})


@dataclass(frozen=True)
class SecondReviewFinding:
    """One blocker produced by second-review enforcement."""

    code: str
    event_key: str
    detail: str


@dataclass(frozen=True)
class TriggerEvaluation:
    triggers: tuple[str, ...]
    details: tuple[str, ...]

    @property
    def requires_second_review(self) -> bool:
        return bool(self.triggers)


def normalize_timestamp(value: Any) -> float:
    """The shared 1-microsecond grid (imported lazily: ``railway_detection.evaluation`` imports
    the annotation package, so a module-level import would be circular)."""
    from railway_detection.evaluation.timebase import normalize_timestamp as _normalize

    return _normalize(value)


def event_key(record: Mapping[str, Any]) -> str:
    return f"{record.get('cohort')}/{record.get('event_id')}"


def _reviewer_id(record: Mapping[str, Any]) -> str:
    meta = record.get("reviewer_metadata")
    if isinstance(meta, Mapping):
        return str(meta.get("reviewer_id", "")).strip()
    return ""


def _boundary_signature(boundary: Mapping[str, Any]) -> tuple[Any, Any, Any]:
    value = boundary.get("value_s")
    return (
        boundary.get("state"),
        boundary.get("reference_camera"),
        None if value is None else normalize_timestamp(value),
    )


def load_candidate_values(
    record: Mapping[str, Any], *, repository_root: Path
) -> tuple[dict[str, tuple[bool, float | None]] | None, str | None]:
    """Read the candidate boundaries of the proposal a record is bound to.

    Returns ``(candidates, None)`` or ``(None, reason)``. The proposal file must lie inside the
    repository, exist and match the record's ``proposal_sha256``; otherwise the binding is
    unverifiable and the caller treats that as a trigger.
    """
    ref = record.get("proposal_reference")
    if not isinstance(ref, Mapping):
        return None, "record has no proposal_reference"
    rel, claimed = ref.get("proposal_file"), ref.get("proposal_sha256")
    if not isinstance(rel, str) or not isinstance(claimed, str):
        return None, "proposal_reference is malformed"
    root = repository_root.resolve()
    path = (root / rel).resolve()
    if root not in path.parents:
        return None, f"proposal file {rel!r} is outside the repository"
    if not path.is_file():
        return None, f"proposal file {rel!r} does not exist"
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != claimed:
        return None, f"proposal file {rel!r} does not match the record's proposal_sha256"
    try:
        proposal = json.loads(raw.decode("utf-8"))
        stamps = proposal["proposed_timestamps"]
    except (ValueError, KeyError, TypeError):
        return None, f"proposal file {rel!r} has no readable proposed_timestamps"
    if not isinstance(stamps, Mapping):
        return None, f"proposal file {rel!r} has malformed proposed_timestamps"
    candidates: dict[str, tuple[bool, float | None]] = {}
    for key, entry in stamps.items():
        canonical = LEGACY_TIMESTAMP_ALIASES.get(key, key)
        if not isinstance(entry, Mapping):
            continue
        value = entry.get("value_s")
        observable = entry.get("candidate_observable") is True and value is not None
        candidates[canonical] = (observable, float(value) if observable else None)
    return candidates, None


def evaluate_record_triggers(
    record: Mapping[str, Any],
    *,
    candidates: Mapping[str, tuple[bool, float | None]] | None,
    candidate_problem: str | None,
    media_registry_entry: Mapping[str, str] | None,
) -> TriggerEvaluation:
    """Evaluate the mechanically checkable RD-043 triggers on one record."""
    triggers: list[str] = []
    details: list[str] = []

    def fire(code: str, detail: str) -> None:
        if code not in triggers:
            triggers.append(code)
        details.append(f"{code}: {detail}")

    status = record.get("adjudication_status")
    if status in _FLAG_STATUSES:
        fire(TRIGGER_EXPLICIT_FLAG, f"adjudication_status={status}")

    boundaries = record.get("boundary_adjudications")
    boundaries = boundaries if isinstance(boundaries, Mapping) else {}
    for name in CANONICAL_TIMESTAMPS:
        entry = boundaries.get(name)
        if isinstance(entry, Mapping) and entry.get("state") == "UNCERTAIN":
            fire(TRIGGER_UNCERTAIN_BOUNDARY, f"{name} is UNCERTAIN")

    if record.get("cohort") == _ENGINE_COHORT:
        for name in _ENGINE_BOUNDARIES:
            entry = boundaries.get(name)
            if isinstance(entry, Mapping) and entry.get("state") in _INTERPRETED_STATES:
                fire(TRIGGER_ENGINE_T3_T4, f"engine-cohort {name} is {entry.get('state')}")

    observed = record.get("reviewer_observed_media_hashes")
    if media_registry_entry is None:
        fire(TRIGGER_MEDIA_HASH, "no independently verified registry entry for this event")
    elif not isinstance(observed, Mapping):
        fire(TRIGGER_MEDIA_HASH, "record carries no reviewer-observed media hashes")
    else:
        for side in ("front", "back"):
            if observed.get(f"{side}_sha256") != media_registry_entry.get(side):
                fire(TRIGGER_MEDIA_HASH, f"{side} hash differs from the verified registry")

    if candidates is None and candidate_problem is None:
        pass  # no repository root supplied: trigger 6 is not evaluated (disclosed in evidence)
    elif candidates is None:
        fire(TRIGGER_CORRECTED, candidate_problem or "bound proposal could not be verified")
    else:
        for name in CANONICAL_TIMESTAMPS:
            entry = boundaries.get(name)
            if not isinstance(entry, Mapping):
                continue
            cand_observable, cand_value = candidates.get(name, (False, None))
            recorded_observable = entry.get("state") == "OBSERVABLE"
            if cand_observable != recorded_observable:
                fire(TRIGGER_CORRECTED, f"{name}: observability differs from the candidate")
            elif (
                recorded_observable
                and cand_value is not None
                and (normalize_timestamp(entry.get("value_s")) != normalize_timestamp(cand_value))
            ):
                fire(TRIGGER_CORRECTED, f"{name}: value differs from the candidate")

    return TriggerEvaluation(tuple(triggers), tuple(details))


def _compare_reviews(primary: Mapping[str, Any], second: Mapping[str, Any]) -> list[str]:
    diffs: list[str] = []
    p_b = primary.get("boundary_adjudications") or {}
    s_b = second.get("boundary_adjudications") or {}
    for name in CANONICAL_TIMESTAMPS:
        pe, se = p_b.get(name), s_b.get(name)
        if not isinstance(pe, Mapping) or not isinstance(se, Mapping):
            diffs.append(f"{name}: missing in one review")
        elif _boundary_signature(pe) != _boundary_signature(se):
            diffs.append(f"{name}: {_boundary_signature(pe)} != {_boundary_signature(se)}")
    return diffs


def assess_second_reviews(
    records: Iterable[Mapping[str, Any]],
    *,
    authorized_reviewers: frozenset[str],
    repository_root: Path | None,
    media_sha256_registry: Mapping[str, Mapping[str, str]] | None,
) -> tuple[list[SecondReviewFinding], list[str]]:
    """Enforce RD-043 across a corpus of *schema-valid* Stage-2.1 record dicts.

    Returns ``(findings, evidence)``. A finding is a blocker. ``records`` must already have passed
    ``build_stage2_1_record_from_dict``; this function re-reads the dictionaries and trusts no
    field it can recompute.
    """
    all_records = [r for r in records if isinstance(r, Mapping)]
    primaries = [r for r in all_records if not r.get("second_review_of")]
    seconds_by_target: dict[str, list[Mapping[str, Any]]] = {}
    for rec in all_records:
        target = rec.get("second_review_of")
        if isinstance(target, str) and target.strip():
            seconds_by_target.setdefault(target.strip(), []).append(rec)
    known_ids = {str(r.get("review_id")) for r in all_records}

    findings: list[SecondReviewFinding] = []
    evidence: list[str] = []
    not_evaluated: set[str] = set()

    for orphan_target, orphans in sorted(seconds_by_target.items()):
        if orphan_target not in known_ids:
            for rec in orphans:
                findings.append(
                    SecondReviewFinding(
                        "SECOND_REVIEW_TARGET_MISSING",
                        event_key(rec),
                        f"second_review_of={orphan_target!r} matches no review record",
                    )
                )

    for primary in primaries:
        key = event_key(primary)
        registry_entry = None
        if media_sha256_registry is not None:
            registry_entry = media_sha256_registry.get(key) or media_sha256_registry.get(
                str(primary.get("event_id"))
            )
        candidates: dict[str, tuple[bool, float | None]] | None = None
        problem: str | None = None
        if repository_root is not None:
            candidates, problem = load_candidate_values(primary, repository_root=repository_root)
        elif key not in not_evaluated:
            not_evaluated.add(key)
        evaluation = evaluate_record_triggers(
            primary,
            candidates=candidates,
            candidate_problem=problem,
            media_registry_entry=registry_entry,
        )
        if not evaluation.requires_second_review:
            evidence.append(f"{key}: no RD-043 trigger fired; single review sufficient")
            continue

        companions = seconds_by_target.get(str(primary.get("review_id")), [])
        primary_reviewer = _reviewer_id(primary).lower()
        independent = [
            c
            for c in companions
            if _reviewer_id(c) in authorized_reviewers
            and _reviewer_id(c).lower() != primary_reviewer
            and event_key(c) == key
            and c.get("adjudication_status") == "APPROVED"
        ]
        if not independent:
            findings.append(
                SecondReviewFinding(
                    "INDEPENDENT_SECOND_REVIEW_MISSING",
                    key,
                    "RD-043 triggers fired (" + "; ".join(evaluation.details) + ") but no "
                    "APPROVED record by a distinct allowlisted reviewer references this review "
                    "via second_review_of. A missing independent reviewer is a blocker.",
                )
            )
            continue
        disagreements = [d for c in independent for d in _compare_reviews(primary, c)]
        if disagreements:
            findings.append(
                SecondReviewFinding(
                    "SECOND_REVIEW_DISAGREEMENT_UNRESOLVED",
                    key,
                    "independent reviews differ (no tolerance applied; event stays UNCERTAIN): "
                    + "; ".join(disagreements[:6]),
                )
            )
            continue
        evidence.append(
            f"{key}: RD-043 triggers {list(evaluation.triggers)} satisfied by an independent "
            "agreeing second review (agreement does not replace researcher adjudication)"
        )
    if not_evaluated:
        evidence.append(
            f"{TRIGGER_CORRECTED} not evaluated for {len(not_evaluated)} event(s): no "
            "repository_root was supplied (the canonical CLI and execution gate always supply it)"
        )
    return findings, evidence
