"""Phase 11.2: the fail-closed Stage-2.1 -> Stage-3 promotion gate.

There is currently no Stage 3 implementation anywhere in this repository
(confirmed in `docs/PHASE11_1_ANNOTATION_INTEGRITY_AUDIT.md` Section 3.1).
This module builds only the smallest well-defined promotion interface
necessary to enforce the rules `docs/PHASE11_1_REMEDIATION_PLAN.md` Section
4 specifies -- not a full evaluation system.

`promote_record` is the ONLY function in this module that writes a file,
and it is a thin wrapper that ALWAYS calls `validate_for_promotion` first
and refuses to write anything if any violation is returned. There is no
second, faster, or "trusted caller" code path that skips validation --
this is what "enforced at the actual promotion boundary" means here: the
write and the validation are not separable.

`promote_record` takes `output_dir` as a required argument with no default
pointing at `data/ground_truth/`. No script in this repository calls it
against the real `data/ground_truth/reviews/` records in this phase --
doing so is explicitly out of scope (see Phase 11.2 brief, "Do not promote
any existing record to evaluation-ready status").
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from railway_detection.annotation.integrity_safeguard import check_review_batch_integrity
from railway_detection.annotation.schemas import SchemaValidationError
from railway_detection.annotation.stage2_1_schema import (
    REVIEWER_ID_BLOCKLIST,
    STAGE_2_1_SCHEMA_VERSION,
    build_stage2_1_record_from_dict,
)
from railway_detection.safety.media_guard import require_media_authorization

_REPO_GROUND_TRUTH_ROOT = (Path(__file__).resolve().parents[3] / "data" / "ground_truth").resolve()


def _is_real_repository_ground_truth_path(path: Path) -> bool:
    """Return True if ``path`` resolves inside the real repository's ``data/ground_truth`` tree."""
    try:
        resolved = path.resolve()
        temp_root = Path(tempfile.gettempdir()).resolve()
        if resolved == temp_root or temp_root in resolved.parents:
            return False
        return resolved == _REPO_GROUND_TRUTH_ROOT or _REPO_GROUND_TRUTH_ROOT in resolved.parents
    except OSError:
        return False

# --- Phase 11.7, Decision 2: mandatory reviewer allowlist ------------------


class AuthorizedReviewersLoadError(Exception):
    """Raised by `load_authorized_reviewers` for any missing, malformed, or
    internally-inconsistent allowlist file. There is no code path that
    returns a partially-trusted or empty-but-accepted set on failure --
    every failure mode here is fail-closed (raise), never fail-open."""


def load_authorized_reviewers(allowlist_path: Path) -> frozenset[str]:
    """Loads and validates the reviewer allowlist from
    `allowlist_path` (e.g. `data/ground_truth/authorized_reviewers.json`).

    Fails closed on: a missing file; invalid JSON; the wrong top-level
    shape; an empty list; a non-string or blank entry; a duplicate entry;
    or an entry that is itself on `REVIEWER_ID_BLOCKLIST` (a maintained
    allowlist that somehow contains a known-bad placeholder is itself
    evidence the file is not trustworthy, not something to silently
    tolerate). This function performs no normalization that could turn an
    invalid file into a usable one -- every failure raises, it never
    returns a best-effort subset.
    """
    if not allowlist_path.exists():
        raise AuthorizedReviewersLoadError(
            f"authorized-reviewers allowlist does not exist: {allowlist_path}"
        )
    try:
        raw = allowlist_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AuthorizedReviewersLoadError(f"authorized-reviewers allowlist unreadable: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AuthorizedReviewersLoadError(
            f"authorized-reviewers allowlist is not valid JSON: {exc}"
        ) from exc

    if not isinstance(data, dict) or "authorized_reviewers" not in data:
        raise AuthorizedReviewersLoadError(
            "authorized-reviewers allowlist must be a JSON object with an 'authorized_reviewers' list"
        )
    reviewers = data["authorized_reviewers"]
    if not isinstance(reviewers, list) or not reviewers:
        raise AuthorizedReviewersLoadError("'authorized_reviewers' must be a non-empty list")

    normalized: list[str] = []
    for entry in reviewers:
        if not isinstance(entry, str) or not entry.strip():
            raise AuthorizedReviewersLoadError(
                f"'authorized_reviewers' contains a non-string or blank entry: {entry!r}"
            )
        reviewer_id = entry.strip()
        if reviewer_id.lower() in REVIEWER_ID_BLOCKLIST:
            raise AuthorizedReviewersLoadError(
                f"'authorized_reviewers' contains a blocklisted identifier ({reviewer_id!r}) -- "
                "refusing to trust an allowlist that is internally inconsistent with the denylist."
            )
        normalized.append(reviewer_id)

    if len(set(normalized)) != len(normalized):
        raise AuthorizedReviewersLoadError("'authorized_reviewers' contains duplicate entries")

    for revoked_key in ("revoked_reviewers", "inactive_reviewers"):
        if revoked_key in data:
            revoked_raw = data[revoked_key]
            if not isinstance(revoked_raw, list):
                raise AuthorizedReviewersLoadError(
                    f"'{revoked_key}' must be a list of strings when present"
                )
            revoked_set: set[str] = set()
            for r_entry in revoked_raw:
                if not isinstance(r_entry, str) or not r_entry.strip():
                    raise AuthorizedReviewersLoadError(
                        f"'{revoked_key}' contains a non-string or blank entry: {r_entry!r}"
                    )
                revoked_set.add(r_entry.strip())
            overlap = sorted(set(normalized) & revoked_set)
            if overlap:
                raise AuthorizedReviewersLoadError(
                    f"'authorized_reviewers' overlaps with '{revoked_key}' ({overlap}) -- "
                    "refusing to trust an allowlist containing revoked or inactive reviewers."
                )

    return frozenset(normalized)


def validate_non_synthetic_record(
    record_dict: dict[str, Any],
    *,
    media_file_paths: dict[str, dict[str, str]] | None = None,
) -> list[PromotionViolation]:
    """Fail-closed check ensuring synthetic pilot/adjudication records can never be promoted as canonical ground truth."""
    event_id = str(record_dict.get("event_id", "<unknown>"))
    violations: list[PromotionViolation] = []
    reviewer_meta = record_dict.get("reviewer_metadata") or {}
    if not isinstance(reviewer_meta, dict):
        reviewer_meta = {}
    proposal_ref = record_dict.get("proposal_reference") or {}
    if not isinstance(proposal_ref, dict):
        proposal_ref = {}

    candidate_fields: list[tuple[str, str]] = [
        ("event_id", event_id),
        ("review_id", str(record_dict.get("review_id", ""))),
        ("reviewer_id", str(reviewer_meta.get("reviewer_id", ""))),
        ("review_session_id", str(reviewer_meta.get("review_session_id", ""))),
        ("proposal_file", str(proposal_ref.get("proposal_file", ""))),
    ]
    history = record_dict.get("adjudication_history")
    if isinstance(history, list):
        for idx, h_entry in enumerate(history):
            if isinstance(h_entry, dict):
                candidate_fields.append((f"adjudication_history[{idx}].by", str(h_entry.get("by", ""))))

    for field_name, val in candidate_fields:
        norm = val.strip().lower()
        if (
            norm.startswith("synthetic_")
            or "/synthetic_" in norm
            or "@synthetic." in norm
            or norm.endswith("@test.example.com")
        ):
            violations.append(
                PromotionViolation(
                    event_id,
                    "SYNTHETIC_RECORD_NOT_PROMOTABLE",
                    f"Field '{field_name}' carries synthetic identifier '{val}'; synthetic pilot/test "
                    "records are strictly isolated from canonical ground-truth promotion.",
                )
            )

    if media_file_paths is not None:
        file_paths = _lookup_by_identity(media_file_paths, record_dict, event_id)
        if isinstance(file_paths, dict):
            temp_root = Path(tempfile.gettempdir()).resolve()
            for cam in ("front", "back"):
                raw_p = file_paths.get(cam)
                if isinstance(raw_p, str) and raw_p.strip():
                    try:
                        resolved_p = Path(raw_p).resolve()
                        if (
                            resolved_p == temp_root
                            or temp_root in resolved_p.parents
                            or resolved_p.name.lower().startswith("synthetic_")
                        ):
                            violations.append(
                                PromotionViolation(
                                    event_id,
                                    "SYNTHETIC_RECORD_NOT_PROMOTABLE",
                                    f"Media path for '{cam}' ('{raw_p}') resolves to a temporary or "
                                    "synthetic fixture path; canonical promotion requires real corpus media.",
                                )
                            )
                    except OSError:
                        pass

    return violations


# --- Phase 11.7, Decision 4: full-file media-hash verification -------------


def compute_media_sha256_pair(front_path: Path, back_path: Path) -> dict[str, str]:
    """Computes the full-file SHA-256 of both camera streams. Used both at
    review time (to populate `reviewer_observed_media_hashes` when
    constructing a Stage-2.1 record) and at promotion time (to re-verify
    the live files, below). Raises `FileNotFoundError` -- never silently
    skips a missing file or substitutes a cached/previous value."""
    for path, label in ((front_path, "front"), (back_path, "back")):
        require_media_authorization(path, "HASH_RAW_MEDIA")
        if not path.exists():
            raise FileNotFoundError(f"{label} media file does not exist: {path}")
    return {
        "front": hashlib.sha256(front_path.read_bytes()).hexdigest(),
        "back": hashlib.sha256(back_path.read_bytes()).hexdigest(),
    }


@dataclass(frozen=True)
class PromotionViolation:
    event_id: str
    code: str
    message: str


class PromotionRejected(Exception):
    """Raised by `promote_record` when any violation is found. Carries the
    full violation list so callers can report every reason, not just the
    first one found."""

    def __init__(self, violations: list[PromotionViolation]) -> None:
        self.violations = violations
        summary = "; ".join(f"[{v.code}] {v.event_id}: {v.message}" for v in violations)
        super().__init__(f"Promotion rejected ({len(violations)} violation(s)): {summary}")


def _lookup_by_identity(
    mapping: dict[str, Any], record_dict: dict[str, Any], event_id: str
) -> Any:
    """Find a per-event entry by cohort-qualified identity, falling back to the bare id.

    ``event_id`` is only unique within a cohort (``event_001`` exists in three), so a
    mapping built from a real corpus must be keyed ``"<cohort>/<event_id>"``. A bare-id
    key is honored only when no qualified key exists, which keeps single-cohort callers
    working; it can never shadow a qualified entry.
    """
    cohort = record_dict.get("cohort")
    if isinstance(cohort, str):
        qualified = f"{cohort}/{event_id}"
        if qualified in mapping:
            return mapping[qualified]
    return mapping.get(event_id)


def validate_for_promotion(
    record_dict: dict[str, Any],
    *,
    active_proposal_sha256_by_event: dict[str, str],
    media_sha256_registry: dict[str, dict[str, str]],
    authorized_reviewers: frozenset[str],
    media_file_paths: dict[str, dict[str, str]],
    disallow_synthetic_identifiers: bool = False,
) -> list[PromotionViolation]:
    """Validates ONE record against every rejection rule. No caller may
    omit `authorized_reviewers` or `media_file_paths` -- both are required
    keyword arguments with no default, so Decisions 2 and 4 (Phase 11.7)
    cannot be silently bypassed by a caller that simply does not pass
    them. This function still performs no I/O of its own beyond the one
    live media re-hash below (`compute_media_sha256_pair`), which Decision
    4 explicitly requires ("verify the complete media file... at
    promotion"); every other check remains a pure comparison against
    caller-supplied state.

    `active_proposal_sha256_by_event`: {event_id: sha256 of the CURRENTLY
    active proposal file}, supplied by the caller (e.g. computed fresh from
    `data/ground_truth/proposals/` at promotion time) -- this module never
    reads that directory itself, so it cannot silently drift from whatever
    the caller considers authoritative.

    `media_sha256_registry`: {event_id: {"front": sha256, "back": sha256}},
    similarly caller-supplied (e.g. from
    `data/manifests/layer_b_v2_annotation_inventory.json`, independently
    verified in Phase 11) -- the PRE-COMPUTED, trusted-manifest hash.

    `authorized_reviewers`: the output of `load_authorized_reviewers()` (or
    an equivalent frozenset), caller-loaded so this function never reads
    the allowlist file itself and cannot silently fall back to a default
    path.

    `media_file_paths`: {event_id: {"front": path_str, "back": path_str}},
    the actual raw media file locations to LIVE re-hash at promotion time
    and cross-check against both `media_sha256_registry` and the record's
    own `reviewer_observed_media_hashes` -- this is what makes promotion
    actually re-verify the file, not merely re-trust a cached hash.
    """
    event_id = record_dict.get("event_id", "<unknown>")
    violations: list[PromotionViolation] = []

    if disallow_synthetic_identifiers:
        violations.extend(
            validate_non_synthetic_record(record_dict, media_file_paths=media_file_paths)
        )

    # 1. Legacy/unknown schema is rejected outright -- no partial validation
    # of a non-Stage-2.1 record is ever attempted. This is also how a
    # record using `approval_status` (the old field name) instead of
    # `adjudication_status` is caught: it will not match the Stage-2.1
    # schema_version and is rejected here before any field is even read.
    if record_dict.get("schema_version") != STAGE_2_1_SCHEMA_VERSION:
        return [
            *violations,
            PromotionViolation(
                event_id,
                "LEGACY_OR_UNKNOWN_SCHEMA",
                f"schema_version '{record_dict.get('schema_version')}' is not '{STAGE_2_1_SCHEMA_VERSION}'. "
                "Legacy records (including all 27 schema_version='7.0.0' records investigated in Phase 11.1) "
                "are never eligible for promotion regardless of their claimed adjudication_status.",
            ),
        ]

    # 2. Explicit invalidation marker, if present, blocks promotion
    # unconditionally, before any further check.
    if record_dict.get("invalidation") is not None:
        return [
            *violations,
            PromotionViolation(
                event_id,
                "RECORD_INVALIDATED",
                "Record carries an explicit invalidation marker and cannot be promoted.",
            ),
        ]

    # 3. Full schema validation (field presence, types, internal
    # consistency, minimum review duration, attestation, etc. -- see
    # stage2_1_schema.py). A record failing ANY of these is rejected
    # without attempting the remaining, provenance-level checks below,
    # since those checks assume a structurally valid record to compare
    # against.
    try:
        record = build_stage2_1_record_from_dict(record_dict)
    except SchemaValidationError as exc:
        return [*violations, PromotionViolation(event_id, "SCHEMA_VALIDATION_FAILED", str(exc))]

    # 3b. Reviewer allowlist (Decision 2). Being well-formed and not on the
    # BLOCKLIST (stage2_1_schema.py's ReviewerMetadata check) is necessary
    # but not sufficient -- the reviewer_id must also be explicitly present
    # in the caller-supplied, externally-maintained ALLOWLIST. A record
    # cannot make its own reviewer_id valid by any internal field change:
    # this check is a lookup against state the record does not control.
    if record.reviewer_metadata.reviewer_id not in authorized_reviewers:
        violations.append(PromotionViolation(
            event_id, "REVIEWER_NOT_AUTHORIZED",
            f"reviewer_id '{record.reviewer_metadata.reviewer_id}' is not present in the supplied "
            "authorized-reviewers allowlist. Passing schema validation and the blocklist check is not "
            "sufficient for promotion; the identity must also be explicitly authorized.",
        ))

    # 4. Stale proposal version.
    active_sha = _lookup_by_identity(active_proposal_sha256_by_event, record_dict, event_id)
    if active_sha is None:
        violations.append(PromotionViolation(
            event_id, "NO_ACTIVE_PROPOSAL_KNOWN",
            f"No active proposal sha256 supplied for event_id '{event_id}'; cannot verify currency.",
        ))
    elif record.proposal_reference.proposal_sha256 != active_sha:
        violations.append(PromotionViolation(
            event_id, "STALE_PROPOSAL_REFERENCE",
            f"Record references proposal sha256 '{record.proposal_reference.proposal_sha256}' but the "
            f"currently active proposal has sha256 '{active_sha}' -- this review does not certify the "
            "current candidate.",
        ))

    # 5. Missing or incomplete media identity.
    media = _lookup_by_identity(media_sha256_registry, record_dict, event_id)
    if media is None:
        violations.append(PromotionViolation(
            event_id, "MISSING_MEDIA_IDENTITY",
            f"No media sha256 registry entry supplied for event_id '{event_id}'.",
        ))
    else:
        missing_cams = [c for c in ("front", "back") if c not in media or not media[c]]
        if missing_cams:
            violations.append(PromotionViolation(
                event_id, "INCOMPLETE_MEDIA_IDENTITY",
                f"media_sha256_registry entry for '{event_id}' is missing camera(s): {missing_cams}.",
            ))

    # 5b. Live media re-verification at promotion time (Decision 4). Not a
    # second trust of the same cached registry value -- this re-reads the
    # actual files on disk right now and cross-checks the result against
    # BOTH the registry (did the file change since the manifest was built?)
    # AND the reviewer's own `reviewer_observed_media_hashes` (did the file
    # change since this specific review happened, or does the reviewer's
    # recorded observation simply not match the real file?). Either
    # disagreement blocks promotion; neither can be satisfied by editing a
    # path string, since both compare against freshly-computed content hashes.
    file_paths = _lookup_by_identity(media_file_paths, record_dict, event_id)
    if file_paths is None:
        violations.append(PromotionViolation(
            event_id, "MISSING_MEDIA_FILE_PATHS",
            f"No media_file_paths entry supplied for event_id '{event_id}' -- cannot perform the "
            "promotion-time live media re-verification Decision 4 requires.",
        ))
    else:
        missing_path_cams = [c for c in ("front", "back") if c not in file_paths or not file_paths[c]]
        if missing_path_cams:
            violations.append(PromotionViolation(
                event_id, "INCOMPLETE_MEDIA_FILE_PATHS",
                f"media_file_paths entry for '{event_id}' is missing camera(s): {missing_path_cams}.",
            ))
        else:
            front_path, back_path = Path(file_paths["front"]), Path(file_paths["back"])
            missing_files = [str(p) for p in (front_path, back_path) if not p.exists()]
            if missing_files:
                violations.append(PromotionViolation(
                    event_id, "MEDIA_FILE_MISSING",
                    f"Media file(s) do not exist at promotion time, cannot re-verify: {missing_files}.",
                ))
            else:
                live = compute_media_sha256_pair(front_path, back_path)
                if media is not None and "front" in media and "back" in media:
                    if live["front"] != media["front"] or live["back"] != media["back"]:
                        violations.append(PromotionViolation(
                            event_id, "MEDIA_HASH_CHANGED_SINCE_REGISTRY",
                            f"Live re-hash of the raw media for '{event_id}' does not match the "
                            "media_sha256_registry entry -- the file(s) were changed or substituted "
                            "after the registry was built.",
                        ))
                rom = record.reviewer_observed_media_hashes
                if live["front"] != rom.front_sha256 or live["back"] != rom.back_sha256:
                    violations.append(PromotionViolation(
                        event_id, "MEDIA_HASH_CHANGED_SINCE_REVIEW",
                        f"Live re-hash of the raw media for '{event_id}' does not match this record's own "
                        "reviewer_observed_media_hashes -- the media changed between review time and "
                        "promotion time, or the reviewer's recorded observation does not correspond to "
                        "the actual file.",
                    ))

    # 6. Unresolved disagreement.
    if not record.is_resolved:
        violations.append(PromotionViolation(
            event_id, "UNRESOLVED_DISAGREEMENT",
            f"adjudication_status is '{record.adjudication_status}', not a final resolved status. "
            "No automated tie-breaking is performed; a human must resolve this before promotion.",
        ))
    elif record.adjudication_status != "APPROVED":
        violations.append(PromotionViolation(
            event_id, "NOT_APPROVED",
            f"adjudication_status is '{record.adjudication_status}', not 'APPROVED'.",
        ))

    return violations


def validate_batch_for_promotion(
    record_dicts: list[dict[str, Any]],
    *,
    active_proposal_sha256_by_event: dict[str, str],
    media_sha256_registry: dict[str, dict[str, str]],
    authorized_reviewers: frozenset[str],
    media_file_paths: dict[str, dict[str, str]],
    disallow_synthetic_identifiers: bool = False,
) -> list[PromotionViolation]:
    """Validates a BATCH of records together, catching cross-record issues
    a per-record check cannot see (e.g. implausible identical timestamps
    across the batch, reusing Phase 11.1's `check_review_batch_integrity`,
    and same-reviewer second-review collisions) in addition to every
    per-record check above."""
    violations: list[PromotionViolation] = []
    for r in record_dicts:
        violations.extend(validate_for_promotion(
            r, active_proposal_sha256_by_event=active_proposal_sha256_by_event,
            media_sha256_registry=media_sha256_registry,
            authorized_reviewers=authorized_reviewers, media_file_paths=media_file_paths,
            disallow_synthetic_identifiers=disallow_synthetic_identifiers,
        ))

    # Only meaningful across records that at least passed individual schema
    # validation (legacy/malformed records already rejected above and
    # excluded here, since check_review_batch_integrity expects
    # well-formed adjudication_status/reviewer_metadata fields).
    well_formed = [r for r in record_dicts if r.get("schema_version") == STAGE_2_1_SCHEMA_VERSION]

    # Cross-record second-review reviewer separation check: if record B claims
    # second_review_of record A in the batch, B's reviewer_id must differ from A's.
    by_review_id: dict[str, dict[str, Any]] = {
        str(r.get("review_id", "")): r for r in well_formed if r.get("review_id")
    }
    for r in well_formed:
        second_of = r.get("second_review_of")
        if isinstance(second_of, str) and second_of.strip() in by_review_id:
            first_rec = by_review_id[second_of.strip()]
            first_reviewer = str((first_rec.get("reviewer_metadata") or {}).get("reviewer_id", "")).strip()
            second_reviewer = str((r.get("reviewer_metadata") or {}).get("reviewer_id", "")).strip()
            if first_reviewer and first_reviewer == second_reviewer:
                violations.append(
                    PromotionViolation(
                        str(r.get("event_id", "<unknown>")),
                        "BATCH_SAME_REVIEWER_SECOND_REVIEW",
                        f"Record '{r.get('review_id')}' claims second_review_of='{second_of}', "
                        f"but both reviews were performed by the same reviewer '{second_reviewer}'.",
                    )
                )

    batch_check_input = [
        {
            "event_id": r["event_id"],
            "adjudication_status": r.get("adjudication_status"),
            "reviewer_metadata": {
                "review_date_utc": r.get("reviewer_metadata", {}).get("review_start_utc"),
            },
            "review_duration_s": r.get("reviewer_metadata", {}).get("review_duration_s"),
            "review_session_id": r.get("reviewer_metadata", {}).get("review_session_id"),
        }
        for r in well_formed
    ]
    batch_violations = check_review_batch_integrity(batch_check_input)
    for v in batch_violations:
        violations.append(PromotionViolation(v.event_id, f"BATCH_{v.code}", v.message))

    return violations


def promote_record(
    record_dict: dict[str, Any],
    *,
    output_dir: Path,
    active_proposal_sha256_by_event: dict[str, str],
    media_sha256_registry: dict[str, dict[str, str]],
    authorized_reviewers: frozenset[str],
    media_file_paths: dict[str, dict[str, str]],
    disallow_synthetic_identifiers: bool = False,
) -> Path:
    """The only write path. Validates first; raises PromotionRejected and
    writes nothing if any violation is found. `output_dir` is a required
    argument supplied by the caller -- this function has no hardcoded
    default pointing at any real `data/ground_truth/` path, and no test or
    script in this repository calls it with one in this phase."""
    enforce_non_synthetic = disallow_synthetic_identifiers or _is_real_repository_ground_truth_path(output_dir)
    violations = validate_for_promotion(
        record_dict, active_proposal_sha256_by_event=active_proposal_sha256_by_event,
        media_sha256_registry=media_sha256_registry,
        authorized_reviewers=authorized_reviewers, media_file_paths=media_file_paths,
        disallow_synthetic_identifiers=enforce_non_synthetic,
    )
    if violations:
        raise PromotionRejected(violations)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{record_dict['event_id']}.json"
    out_path.write_text(json.dumps(record_dict, indent=2), encoding="utf-8")
    return out_path


# --- Researcher-controlled invalidation (Task 5) --------------------------


@dataclass(frozen=True)
class InvalidationEvent:
    """A PROPOSED disposition event for ONE record. Constructing this object
    never reads, writes, or modifies the affected record itself beyond
    hashing its current (unmodified) content for the audit trail.

    Authorization caveat, stated plainly: this repository has no real
    authentication or authorization system -- no user accounts, no
    cryptographic signing, no role-based access control. `actor` and
    `authorized_statement` are a DOCUMENTED CONVENTION recording who claims
    responsibility and why, not a security control. Anyone able to run
    this code can supply any string for either field. This function's
    output must be treated as a structured, auditable PROPOSAL requiring
    the researcher's own out-of-band confirmation (e.g. personally
    reviewing and then committing it), never as cryptographic or
    access-controlled proof that an authorized human actually approved it.
    """

    event_id: str
    reason: str
    actor: str
    authorized_statement: str
    at_utc: str
    affected_record_path: str
    affected_record_sha256: str


def propose_invalidation(
    *,
    event_id: str,
    reason: str,
    actor: str,
    authorized_statement: str,
    affected_record_path: Path,
    now_utc: datetime | None = None,
) -> InvalidationEvent:
    """Builds (does not apply) an invalidation disposition event. Reads
    `affected_record_path` ONLY to capture its current SHA-256 for the
    audit trail; never writes to it."""
    if not reason.strip():
        raise ValueError("reason must be a non-empty, specific explanation")
    if not actor.strip():
        raise ValueError("actor must be a non-empty, individually-attributable identifier")
    if not authorized_statement.strip():
        raise ValueError("authorized_statement must be a non-empty explicit authorization statement")
    if not affected_record_path.exists():
        raise ValueError(f"affected_record_path does not exist: {affected_record_path}")

    import hashlib
    content = affected_record_path.read_bytes()
    sha = hashlib.sha256(content).hexdigest()
    ts = (now_utc or datetime.now(UTC)).astimezone(UTC).isoformat().replace("+00:00", "Z")

    return InvalidationEvent(
        event_id=event_id, reason=reason, actor=actor, authorized_statement=authorized_statement,
        at_utc=ts, affected_record_path=str(affected_record_path), affected_record_sha256=sha,
    )


def write_invalidation_proposal(events: list[InvalidationEvent], output_path: Path) -> Path:
    """Appends the proposed disposition events to `output_path` (creating it
    if absent). Pure append: any existing `disposition_events` entries are
    preserved and extended, never replaced or removed -- this is the
    append-only audit history Task 5 requires, applied to the invalidation
    proposal log itself. Never writes to any path under
    `data/ground_truth/reviews/` -- `output_path` is caller-supplied and
    this function does not default or redirect it there."""
    existing: list[dict[str, Any]] = []
    if output_path.exists():
        existing = json.loads(output_path.read_text()).get("disposition_events", [])
    existing.extend(asdict(e) for e in events)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"disposition_events": existing}, indent=2), encoding="utf-8")
    return output_path
