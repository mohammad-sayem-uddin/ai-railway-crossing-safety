"""Phase 11.12: fail-closed evaluation-readiness gate.

Decides -- with evidence -- whether any named evaluation stage is justified.
Default verdict is NOT_READY; there is no override flag, no env-var bypass,
and no "force" parameter. The gate RECOMPUTES every condition from the
records themselves; it never trusts a caller claim that something was
"already validated" (mutation (f) in the Phase 11.12 plan).

Ground-truth approval remains a researcher signature, not a return value of
this function: READY only means the mechanical conditions hold, and starting
Phase 12 still requires a separate EVAL-AUTH.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from railway_detection.annotation.integrity_safeguard import check_review_batch_integrity
from railway_detection.annotation.promotion_gate import (
    AuthorizedReviewersLoadError,
    _is_real_repository_ground_truth_path,
    load_authorized_reviewers,
    validate_for_promotion,
)
from railway_detection.annotation.schemas import SchemaValidationError
from railway_detection.annotation.second_review import assess_second_reviews
from railway_detection.annotation.stage2_1_schema import (
    STAGE_2_1_SCHEMA_VERSION,
    build_stage2_1_record_from_dict,
)

# A READY verdict reports mechanical validity only. Promoting records into
# research ground truth remains a human researcher signature (EVAL-AUTH).
GROUND_TRUTH_APPROVAL_AUTHORITY = "human_researcher_only"


@dataclass(frozen=True)
class ReadinessBlocker:
    """One machine-readable reason readiness was refused."""

    code: str
    event_id: str | None
    detail: str

    def as_text(self) -> str:
        """Render the legacy single-string form used by report consumers."""
        base = f"{self.code}:{self.event_id}" if self.event_id else self.code
        return f"{base}: {self.detail}" if self.detail else base

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "event_id": self.event_id, "detail": self.detail}


@dataclass(frozen=True)
class ReadinessVerdict:
    ready: bool
    stage: str | None
    evidence: tuple[str, ...] = field(default_factory=tuple)
    blockers: tuple[str, ...] = field(default_factory=tuple)
    blocker_details: tuple[ReadinessBlocker, ...] = field(default_factory=tuple)

    @property
    def blocker_codes(self) -> tuple[str, ...]:
        """Distinct blocker codes, sorted, for programmatic dispatch."""
        return tuple(sorted({b.code for b in self.blocker_details}))

    @property
    def mechanically_valid(self) -> bool:
        """True when every mechanical check passed.

        This is deliberately distinct from researcher-approved ground truth:
        a mechanically valid corpus is still not approved evidence until a
        human researcher authorises evaluation.
        """
        return self.ready

    def to_dict(self) -> dict[str, Any]:
        """Serialize a machine-readable blocker report."""
        return {
            "ready": self.ready,
            "stage": self.stage,
            "mechanically_valid": self.mechanically_valid,
            "ground_truth_approval_authority": GROUND_TRUTH_APPROVAL_AUTHORITY,
            "researcher_approval_still_required": True,
            "evidence": list(self.evidence),
            "blockers": [b.to_dict() for b in self.blocker_details],
            "blocker_codes": list(self.blocker_codes),
            "blocker_count": len(self.blocker_details),
        }


def _verdict_not_ready(
    blockers: list[ReadinessBlocker],
    *,
    stage: str | None = None,
    evidence: list[str] | tuple[str, ...] = (),
) -> ReadinessVerdict:
    return ReadinessVerdict(
        ready=False,
        stage=stage,
        evidence=tuple(evidence),
        blockers=tuple(b.as_text() for b in blockers),
        blocker_details=tuple(blockers),
    )


def _not_ready(
    blockers: list[str], *, stage: str | None = None, evidence: list[str] | tuple[str, ...] = ()
) -> ReadinessVerdict:
    """Build a NOT_READY verdict from pre-rendered ``CODE: detail`` strings."""
    structured: list[ReadinessBlocker] = []
    for text in blockers:
        code, _, detail = text.partition(":")
        structured.append(ReadinessBlocker(code=code.strip(), event_id=None, detail=detail.strip()))
    return ReadinessVerdict(
        ready=False,
        stage=stage,
        evidence=tuple(evidence),
        blockers=tuple(blockers),
        blocker_details=tuple(structured),
    )


def _load_review_records(reviews_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Load only active ``*_review.json`` records; reject mixed JSON sources.

    Verified invalidation notices are allowed (they describe legacy records that are then
    excluded); an unverifiable notice or any other non-review JSON is refused.
    Returns ``(records, excused_record_paths)``.
    """
    from railway_detection.annotation.notices import (
        excused_legacy_records,
        invalid_notices,
        is_notice_path,
    )

    if not reviews_dir.exists() or not reviews_dir.is_dir():
        raise ValueError(f"reviews directory does not exist or is not a directory: {reviews_dir}")
    bad_notices = invalid_notices(reviews_dir)
    if bad_notices:
        raise ValueError(
            f"invalidation notice {bad_notices[0].notice} failed verification: "
            f"{bad_notices[0].problem}"
        )
    excused = excused_legacy_records(reviews_dir)
    all_json = sorted(reviews_dir.rglob("*.json"))
    review_paths = [p for p in all_json if p.name.endswith("_review.json")]
    unexpected = [p for p in all_json if p not in review_paths and not is_notice_path(p)]
    if unexpected:
        raise ValueError(f"non-review JSON found in reviews directory: {unexpected[0]}")
    records: list[dict[str, Any]] = []
    for path in review_paths:
        if path.relative_to(reviews_dir).as_posix() in excused:
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"could not read review record {path}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"review record {path} must contain a JSON object")
        records.append(value)
    return records, sorted(excused)


def evaluate_readiness(
    *,
    records: list[dict[str, Any]] | None = None,
    reviews_dir: Path | None = None,
    active_proposal_sha256_by_event: dict[str, str],
    media_sha256_registry: dict[str, dict[str, str]],
    allowlist_path: Path,
    media_file_paths: dict[str, dict[str, str]],
    required_cohorts: tuple[str, ...] = ("train_events", "no_train_events", "engine_events"),
    stage: str = "stage3_single_camera_baseline",
    disallow_synthetic_identifiers: bool = False,
    repository_root: Path | None = None,
) -> ReadinessVerdict:
    """Evaluate whether evaluation may start for a specific stage.

    ``records`` and ``reviews_dir`` are mutually exclusive; the directory form
    is the documented Phase 11.12 API and is loaded fail-closed.

    Conditions (ALL required):
      1. >= 1 APPROVED, resolved record per required cohort subset.
      2. Every in-scope record passes full schema validation.
      3. Every in-scope record passes full `validate_for_promotion`
         with real registry/allowlist/paths (live media re-hash).
      4. No DISPUTED / NEEDS_SECOND_REVIEW record in scope.
      5. No duplicate APPROVED record for the same event.
      6. The APPROVED set passes `check_review_batch_integrity`, so the
         short-burst batch pattern Phase 11.1 found in the 27 legacy records
         cannot reach evaluation through a schema-valid corpus.
      7. Every RD-043 second-review trigger on an APPROVED primary record is
         satisfied by an agreeing APPROVED record from a distinct allowlisted
         reviewer (`second_review.py`; Mission 10). A second-review record
         (``second_review_of`` set) is not a duplicate of its primary.

    Returns NOT_READY with every blocker enumerated if any condition fails.
    A READY verdict means the mechanical conditions hold; it is not a
    researcher approval of ground truth.
    """
    blockers: list[ReadinessBlocker] = []
    evidence: list[str] = []

    if not isinstance(stage, str) or not stage.strip():
        return _not_ready(["INVALID_STAGE: stage must be a non-empty string"])
    if records is not None and reviews_dir is not None:
        return _not_ready(
            ["MULTIPLE_RECORD_SOURCES: provide records or reviews_dir, not both"],
            stage=stage.strip(),
        )
    if reviews_dir is not None:
        try:
            records, excused_paths = _load_review_records(Path(reviews_dir))
        except (OSError, ValueError) as exc:
            return _not_ready([f"REVIEWS_LOAD_FAILED: {exc}"], stage=stage.strip())
        if excused_paths:
            evidence.append(
                f"{len(excused_paths)} legacy record(s) excluded: each has a verified "
                "invalidation notice (never promoted, never ground truth)"
            )
    if records is None:
        records = []

    # Allowlist must load fail-closed before anything else.
    try:
        authorized_reviewers = load_authorized_reviewers(allowlist_path)
    except AuthorizedReviewersLoadError as exc:
        return _not_ready([f"ALLOWLIST_LOAD_FAILED: {exc}"])

    if not records:
        # Keep the exclusion evidence: a corpus containing only verified,
        # invalidated legacy records is materially different from an empty
        # input directory, and the distinction belongs in the blocker report.
        return _not_ready(
            ["NO_RECORDS: zero in-scope records supplied"],
            stage=stage.strip(),
            evidence=evidence,
        )

    # Condition 2 + status extraction (recomputed, never trusted).
    resolved: list[dict[str, Any]] = []
    for rec in records:
        event_id = rec.get("event_id", "<unknown>") if isinstance(rec, dict) else "<non-object>"
        if not isinstance(rec, dict):
            blockers.append(
                ReadinessBlocker(
                    "SCHEMA_VALIDATION_FAILED", event_id, "record must be a JSON object"
                )
            )
            continue
        if rec.get("schema_version") != STAGE_2_1_SCHEMA_VERSION:
            blockers.append(
                ReadinessBlocker(
                    "LEGACY_OR_UNKNOWN_SCHEMA",
                    event_id,
                    f"schema_version={rec.get('schema_version')!r}",
                )
            )
            continue
        try:
            built = build_stage2_1_record_from_dict(rec)
        except (SchemaValidationError, TypeError, AttributeError, ValueError) as exc:
            blockers.append(ReadinessBlocker("SCHEMA_VALIDATION_FAILED", event_id, str(exc)))
            continue
        if not built.is_resolved:
            blockers.append(ReadinessBlocker("UNRESOLVED_DISAGREEMENT", event_id, ""))
            continue
        resolved.append(rec)
        if built.adjudication_status != "APPROVED":
            blockers.append(ReadinessBlocker("NOT_APPROVED", event_id, ""))

    # Condition 5: duplicate detection applies to approved ground truth.
    approved = [r for r in resolved if r.get("adjudication_status") == "APPROVED"]
    seen: dict[tuple[str | None, str], int] = {}
    for rec in approved:
        if rec.get("second_review_of"):
            continue  # an independent second review is not a duplicate primary
        # Identity is cohort-qualified: ``event_001`` legitimately exists in several cohorts.
        key = (rec.get("cohort"), rec.get("event_id", "<unknown>"))
        seen[key] = seen.get(key, 0) + 1
    for (cohort, eid), count in sorted(seen.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
        if count > 1:
            blockers.append(
                ReadinessBlocker("DUPLICATE_APPROVED_RECORD", eid, f"cohort={cohort} count={count}")
            )

    # Condition 1: cohort coverage by APPROVED records only.
    cohorts_covered = {r.get("cohort") for r in approved}
    for cohort in required_cohorts:
        if cohort not in cohorts_covered:
            blockers.append(ReadinessBlocker("MISSING_COHORT_APPROVAL", cohort, ""))

    # Condition 6: batch-level integrity. Phase 11.1 found 27 records sharing
    # one timestamp with no duration evidence; a schema-valid corpus with the
    # same signature must not reach evaluation.
    if approved:
        try:
            integrity_violations = check_review_batch_integrity(approved)
        except (TypeError, AttributeError, ValueError) as exc:
            blockers.append(
                ReadinessBlocker("BATCH_INTEGRITY_CHECK_FAILED", None, str(exc))
            )
        else:
            for violation in integrity_violations:
                blockers.append(
                    ReadinessBlocker(
                        f"BATCH_INTEGRITY:{violation.code}",
                        violation.event_id,
                        violation.message,
                    )
                )

    # Condition 3: full promotion validation on every APPROVED record.
    enforce_non_synthetic = disallow_synthetic_identifiers or (
        reviews_dir is not None and _is_real_repository_ground_truth_path(Path(reviews_dir))
    )
    for rec in approved:
        eid = rec.get("event_id", "<unknown>")
        try:
            violations = validate_for_promotion(
                rec,
                active_proposal_sha256_by_event=active_proposal_sha256_by_event,
                media_sha256_registry=media_sha256_registry,
                authorized_reviewers=authorized_reviewers,
                media_file_paths=media_file_paths,
                disallow_synthetic_identifiers=enforce_non_synthetic,
            )
        except (SchemaValidationError, TypeError, AttributeError, ValueError, OSError) as exc:
            blockers.append(
                ReadinessBlocker("PROMOTION_FAILED", eid, f"VALIDATION_ERROR ({exc})")
            )
            continue
        if violations:
            blockers.append(
                ReadinessBlocker("PROMOTION_FAILED", eid, "; ".join(v.code for v in violations))
            )
        else:
            evidence.append(f"{eid}: passes full promotion validation")

    # Condition 7: RD-043 second review, enforced on the actual records (never on caller outcomes).
    second_findings, second_evidence = assess_second_reviews(
        approved,
        authorized_reviewers=authorized_reviewers,
        repository_root=repository_root,
        media_sha256_registry=media_sha256_registry,
    )
    for finding in second_findings:
        blockers.append(
            ReadinessBlocker(finding.code, finding.event_key, finding.detail)
        )
    evidence.extend(second_evidence)

    if blockers:
        return _verdict_not_ready(blockers, stage=stage.strip(), evidence=evidence)

    evidence.append(f"approved_record_count={len(approved)}")
    evidence.append("batch integrity checks passed for the approved set")
    evidence.append(
        "mechanical checks only; ground-truth approval remains a researcher signature"
    )
    return ReadinessVerdict(
        ready=True,
        stage=stage.strip(),
        evidence=tuple(evidence),
    )