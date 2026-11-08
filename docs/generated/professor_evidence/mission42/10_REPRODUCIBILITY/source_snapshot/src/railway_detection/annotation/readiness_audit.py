"""Read-only audit of ground-truth readiness (Phase 11).

Summarizes, from the repository's actual files only: legacy record counts and
schema versions, reviewer allowlist/blocklist matches, duplicated timestamps,
superseded proposal references, per-record promotion eligibility, record hashes,
cohort-level missing requirements, the promotion-receipt state, and a LEG-EXEC
(legacy invalidation) *preflight*.

Nothing here writes into the repository or promotes, invalidates, approves or
migrates anything. The preflight verifies that the inputs LEG-EXEC would act on are
the pinned, reviewed ones and reports whether the current repository contains a
valid operation-specific authorization. It contains no path to execution.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from railway_detection.annotation import receipt as receipt_module
from railway_detection.annotation.invalidation_notice_writer import (
    EXPECTED_RECORD_COUNT,
    NoticeWriterValidationError,
    compute_proposal_sha256,
    load_and_verify_proposal,
    plan_invalidation_notices,
)
from railway_detection.annotation.legacy_reconciliation import reconcile_legacy_reviews
from railway_detection.annotation.promotion_gate import (
    AuthorizedReviewersLoadError,
    load_authorized_reviewers,
)
from railway_detection.annotation.schemas import SchemaValidationError
from railway_detection.annotation.stage2_1_schema import (
    REVIEWER_ID_BLOCKLIST,
    STAGE_2_1_SCHEMA_VERSION,
    build_stage2_1_record_from_dict,
)

COHORTS = ("train_events", "no_train_events", "engine_events")
AUDIT_SCHEMA = "ground-truth-readiness-audit/1"

LEG_EXEC_PROPOSAL_RELATIVE = Path("docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json")
# Raw-byte SHA-256 of the reviewed dry-run proposal, as pinned in
# docs/PHASE11_6D_FINAL_EXECUTION_AUTHORIZATION_PACKAGE.md.
LEG_EXEC_PINNED_PROPOSAL_SHA256 = (
    "41cbbba3e9d587b9972c3baca1b39f09d478d408d9c60fd538c249c4600113d4"
)
LEG_EXEC_EXPECTED_OUTPUTS = EXPECTED_RECORD_COUNT + 1  # 27 notices + 1 directory notice


def leg_exec_preflight(root: Path | str) -> dict[str, Any]:
    """Verify (never perform) the legacy-invalidation inputs.

    ``execution_authorized`` reflects the current recorded LEG-EXEC authorization;
    it is verified independently from the read-only plan and never causes a write.
    A general project authorization is insufficient: the recorded statement must name
    the pinned hash, the 27 sources, the 28 output targets and the write operation.
    """
    base = Path(root).resolve()
    proposal_path = base / LEG_EXEC_PROPOSAL_RELATIVE
    result: dict[str, Any] = {
        "operation": "LEG-EXEC",
        "execution_authorized": False,
        "authorization_basis": (
            "none recorded: LEG-EXEC needs its own operation-specific authorization naming the "
            "pinned proposal hash, exactly 27 sources, exactly 28 outputs and the write operation"
        ),
        "pinned_proposal_sha256": LEG_EXEC_PINNED_PROPOSAL_SHA256,
        "expected_source_records": EXPECTED_RECORD_COUNT,
        "expected_output_targets": LEG_EXEC_EXPECTED_OUTPUTS,
        "inputs_verified": False,
    }
    if not proposal_path.is_file():
        result["input_error"] = f"proposal missing: {LEG_EXEC_PROPOSAL_RELATIVE}"
        return result
    actual = compute_proposal_sha256(proposal_path)
    result["actual_proposal_sha256"] = actual
    result["proposal_hash_matches_pin"] = actual == LEG_EXEC_PINNED_PROPOSAL_SHA256
    try:
        from railway_detection.annotation.leg_exec import working_directory

        proposal = load_and_verify_proposal(
            proposal_path, expected_sha256=LEG_EXEC_PINNED_PROPOSAL_SHA256
        )
        with working_directory(base):  # the proposal stores repo-relative paths
            plan = plan_invalidation_notices(
                proposal, reviews_root=base / receipt_module.DEFAULT_REVIEWS_RELATIVE
            )
    except (NoticeWriterValidationError, OSError, ValueError, json.JSONDecodeError) as exc:
        result["input_error"] = f"{type(exc).__name__}: {exc}"
        return result
    statuses = Counter(item.status for item in plan.results)
    try:
        from railway_detection.annotation.leg_exec import LegExecError, verify_authorization

        record = verify_authorization(base)
        result["execution_authorized"] = True
        result["authorization_basis"] = (
            "recorded unsigned researcher statement bound to the pinned hash, the 27 sources "
            f"and the 28 outputs (record {record['record_sha256'][:12]}…)"
        )
    except LegExecError as exc:
        result["authorization_error"] = f"{exc.code}: {exc.detail}"
    result.update(
        {
            "inputs_verified": all(
                item.status in {"WOULD_WRITE", "WOULD_SKIP_ALREADY_DONE_MATCHING"}
                for item in [*plan.results, plan.directory_notice_result]
            ),
            "planned_source_records": len(plan.results),
            "planned_output_targets": len(plan.results) + 1,
            "planned_statuses": dict(sorted(statuses.items())),
            "directory_notice_status": plan.directory_notice_result.status,
            "writes_performed": 0,
        }
    )
    return result


def _record_rows(root: Path, allowlist: frozenset[str] | None) -> list[dict[str, Any]]:
    reviews = root / receipt_module.DEFAULT_REVIEWS_RELATIVE
    rows: list[dict[str, Any]] = []
    for path in sorted(reviews.rglob("*_review.json")) if reviews.is_dir() else []:
        relative = path.relative_to(reviews).as_posix()
        digest = receipt_module.sha256_file(path)
        try:
            record = json.loads(path.read_bytes())
        except json.JSONDecodeError as exc:
            rows.append({"path": relative, "sha256": digest, "readable": False, "error": str(exc)})
            continue
        record = record if isinstance(record, dict) else {}
        reviewer_meta = record.get("reviewer_metadata")
        reviewer = (
            reviewer_meta.get("reviewer_id")
            if isinstance(reviewer_meta, dict)
            else record.get("reviewer_id")
        )
        reasons: list[str] = []
        schema_valid = False
        if record.get("schema_version") != STAGE_2_1_SCHEMA_VERSION:
            reasons.append("LEGACY_OR_UNKNOWN_SCHEMA")
        else:
            try:
                built = build_stage2_1_record_from_dict(record)
                schema_valid = True
                if built.adjudication_status != "APPROVED":
                    reasons.append(f"NOT_APPROVED:{built.adjudication_status}")
            except (SchemaValidationError, TypeError, AttributeError, ValueError) as exc:
                reasons.append(f"SCHEMA_INVALID:{exc}")
        if isinstance(reviewer, str) and reviewer.strip().lower() in REVIEWER_ID_BLOCKLIST:
            reasons.append("REVIEWER_BLOCKLISTED")
        if allowlist is not None and reviewer not in allowlist:
            reasons.append("REVIEWER_NOT_ON_ALLOWLIST")
        rows.append(
            {
                "path": relative,
                "sha256": digest,
                "readable": True,
                "cohort": record.get("cohort") or path.parent.name,
                "event_id": record.get("event_id"),
                "schema_version": record.get("schema_version"),
                "adjudication_status": record.get("adjudication_status"),
                "reviewer_id": reviewer,
                "stage21_schema_valid": schema_valid,
                "promotion_eligible_pending_media_rehash": not reasons,
                "ineligibility_reasons": reasons,
            }
        )
    return rows


def audit_ground_truth_readiness(root: Path | str) -> dict[str, Any]:
    """Build the machine-readable audit. Pure function of repository files."""
    base = Path(root).resolve()
    try:
        allowlist: frozenset[str] | None = load_authorized_reviewers(
            base / receipt_module.DEFAULT_ALLOWLIST_RELATIVE
        )
        allowlist_error = None
    except AuthorizedReviewersLoadError as exc:
        allowlist, allowlist_error = None, str(exc)

    rows = _record_rows(base, allowlist)
    legacy = reconcile_legacy_reviews(base)
    eligible = [r for r in rows if r.get("promotion_eligible_pending_media_rehash")]
    per_cohort: dict[str, Any] = {}
    for cohort in COHORTS:
        in_cohort = [r for r in rows if r.get("cohort") == cohort]
        per_cohort[cohort] = {
            "records": len(in_cohort),
            "stage21_records": sum(1 for r in in_cohort if r.get("stage21_schema_valid")),
            "eligible_pending_media_rehash": sum(
                1 for r in in_cohort if r.get("promotion_eligible_pending_media_rehash")
            ),
            "missing_requirement": (
                None
                if any(r.get("promotion_eligible_pending_media_rehash") for r in in_cohort)
                else "at least one approved, valid Stage-2.1 record with an allowlisted reviewer"
            ),
        }

    timestamps = Counter(
        entry["review_date_utc"] for entry in legacy["records"] if entry["review_date_utc"]
    )
    receipt_state: dict[str, Any]
    try:
        from railway_detection.evaluation import governance

        verified = governance.verify_promotion_receipt(
            base,
            review_record_sha256={r["path"]: r["sha256"] for r in rows},
            live_inputs=receipt_module.live_receipt_inputs(
                inventory=base / receipt_module.DEFAULT_INVENTORY_RELATIVE,
                proposals_dir=base / receipt_module.DEFAULT_PROPOSALS_RELATIVE,
                allowlist=base / receipt_module.DEFAULT_ALLOWLIST_RELATIVE,
            ),
        )
        receipt_state = {"status": "valid", "sha256": verified.sha256}
    except Exception as exc:  # noqa: BLE001 - reported, not raised
        receipt_state = {
            "status": "absent_or_invalid",
            "code": getattr(exc, "code", type(exc).__name__),
            "detail": getattr(exc, "detail", str(exc)),
        }

    identities = Counter((r.get("cohort"), r.get("event_id")) for r in rows)
    return {
        "schema_version": AUDIT_SCHEMA,
        "read_only": True,
        "summary": {
            "record_count": len(rows),
            "schema_versions": dict(Counter(str(r.get("schema_version")) for r in rows)),
            "stage21_records": sum(1 for r in rows if r.get("stage21_schema_valid")),
            "promotion_eligible_pending_media_rehash": len(eligible),
            "bare_event_ids_shared_across_cohorts": sorted(
                {
                    str(event)
                    for event, n in Counter(r.get("event_id") for r in rows).items()
                    if n > 1
                }
            ),
            "duplicate_cohort_event_identities": sorted(
                f"{c}/{e}" for (c, e), n in identities.items() if n > 1
            ),
        },
        "reviewer_allowlist": {
            "loaded": allowlist is not None,
            "error": allowlist_error,
            "entries": sorted(allowlist) if allowlist else [],
            "records_with_blocklisted_reviewer": sum(
                1 for r in rows if "REVIEWER_BLOCKLISTED" in r.get("ineligibility_reasons", [])
            ),
            "records_with_reviewer_not_on_allowlist": sum(
                1
                for r in rows
                if "REVIEWER_NOT_ON_ALLOWLIST" in r.get("ineligibility_reasons", [])
            ),
        },
        "legacy": {
            "summary": legacy["summary"],
            "duplicate_review_timestamps": {
                stamp: count for stamp, count in sorted(timestamps.items()) if count > 1
            },
            "superseded_proposal_references": sum(
                1 for e in legacy["records"] if e["recorded_proposal_matches_active"] is False
            ),
        },
        "cohorts": per_cohort,
        "promotion_receipt": receipt_state,
        "records": rows,
        "leg_exec_preflight": leg_exec_preflight(base),
        "notes": [
            "Eligibility is metadata-only: live media re-hashing (Decision 4) is performed only "
            "by the readiness CLI, never here.",
            "No record is promoted, invalidated, approved or migrated by this audit.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Readable summary of ``audit_ground_truth_readiness`` output."""
    summary = report["summary"]
    allow = report["reviewer_allowlist"]
    receipt = report["promotion_receipt"]
    pre = report["leg_exec_preflight"]
    legacy = report["legacy"]
    receipt_extra = (
        f" ({receipt.get('code')}: {receipt.get('detail')})"
        if receipt["status"] != "valid"
        else ""
    )
    lines = [
        "# Ground-Truth Readiness Audit (read-only)",
        "",
        "Generated from repository files only; nothing was written to evidence trees.",
        "",
        "## Summary",
        f"- Review records: **{summary['record_count']}**; "
        f"schema versions: {summary['schema_versions']}",
        f"- Valid Stage-2.1 records: **{summary['stage21_records']}**",
        "- Promotion-eligible (pending live media re-hash): "
        f"**{summary['promotion_eligible_pending_media_rehash']}**",
        "- Bare event ids shared across cohorts: "
        f"{summary['bare_event_ids_shared_across_cohorts']}",
        "- Duplicate cohort/event identities: "
        f"{summary['duplicate_cohort_event_identities'] or 'none'}",
        "",
        "## Reviewer allowlist",
        f"- Loaded: {allow['loaded']} (entries: {allow['entries']})",
        f"- Records with blocklisted reviewer id: {allow['records_with_blocklisted_reviewer']}",
        "- Records with reviewer not on allowlist: "
        f"{allow['records_with_reviewer_not_on_allowlist']}",
        "",
        "## Legacy records",
        f"- {legacy['summary']['record_count']} legacy-shaped records; "
        f"{legacy['superseded_proposal_references']} reference a superseded proposal",
        f"- Shared review timestamps: {legacy['duplicate_review_timestamps'] or 'none'}",
        "",
        "## Cohort requirements",
        "| Cohort | Records | Stage-2.1 | Eligible | Missing |",
        "|---|---:|---:|---:|---|",
    ]
    for cohort, row in report["cohorts"].items():
        lines.append(
            f"| {cohort} | {row['records']} | {row['stage21_records']} | "
            f"{row['eligible_pending_media_rehash']} | {row['missing_requirement'] or '—'} |"
        )
    lines += [
        "",
        "## Promotion receipt",
        f"- Status: **{receipt['status']}**{receipt_extra}",
        "",
        "## LEG-EXEC preflight (verification only)",
        f"- Execution authorized: **{pre['execution_authorized']}** — {pre['authorization_basis']}",
        f"- Pinned proposal hash: `{pre['pinned_proposal_sha256']}`; "
        f"matches file: {pre.get('proposal_hash_matches_pin')}",
        f"- Inputs verified: {pre['inputs_verified']}; planned sources/outputs: "
        f"{pre.get('planned_source_records')}/{pre.get('planned_output_targets')} "
        f"(expected {pre['expected_source_records']}/{pre['expected_output_targets']}); "
        f"writes performed: {pre.get('writes_performed', 0)}",
        "",
        "## Notes",
    ]
    lines += [f"- {note}" for note in report["notes"]]
    return "\n".join(lines) + "\n"
