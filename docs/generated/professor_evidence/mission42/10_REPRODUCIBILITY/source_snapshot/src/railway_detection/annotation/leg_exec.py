"""LEG-EXEC: apply the pinned legacy-invalidation proposal under a recorded authorization.

The operation writes **only** sibling notices (27 ``*_review.INVALIDATION_NOTICE.json`` files
and one ``_INTEGRITY_NOTICE.md``) and never modifies, moves or deletes an original record.
It is separate from ground-truth approval: invalidating legacy reviews creates no Stage-2.1
record and approves nothing.

Execution requires an operation-specific authorization record
(``data/governance/leg_exec_authorization.json``, schema ``leg-exec-authorization/1``) that
carries the researcher's statement verbatim and is bound to the exact pinned proposal hash,
the exact 27 source records (by digest of their current hashes), the 28 output count and the
write operation. It is a *recorded, unsigned statement*, like EVAL-AUTH; nothing here is a
cryptographic attestation. Any change to the proposal or a source record after the statement
was recorded voids it.

Order of operations (every step fails closed before anything is written):

1. verify the authorization record against the live repository;
2. load the proposal bound to the pinned SHA-256;
3. dry-run the plan: every output must be ``WOULD_WRITE`` or an already-matching notice;
4. apply (resumable; the writer is not atomic across outputs);
5. re-hash all originals (must be byte-identical), verify the exact output inventory and
   that no other file appeared.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from railway_detection.annotation import receipt as receipt_module
from railway_detection.annotation.invalidation_notice_writer import (
    DIRECTORY_NOTICE_NAME,
    EXPECTED_RECORD_COUNT,
    NoticeWriterValidationError,
    apply_invalidation_notices,
    compute_proposal_sha256,
    load_and_verify_proposal,
    plan_invalidation_notices,
)
from railway_detection.annotation.notices import verify_invalidation_notice
from railway_detection.annotation.promotion_gate import (
    AuthorizedReviewersLoadError,
    load_authorized_reviewers,
)

LEG_EXEC_AUTH_SCHEMA = "leg-exec-authorization/1"
LEG_EXEC_AUTH_RELATIVE = Path("data/governance/leg_exec_authorization.json")
PROPOSAL_RELATIVE = Path("docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json")
PINNED_PROPOSAL_SHA256 = "41cbbba3e9d587b9972c3baca1b39f09d478d408d9c60fd538c249c4600113d4"
WRITE_OPERATION = (
    "create one sibling invalidation notice per legacy review record and one directory notice; "
    "never modify, move or delete an original record"
)
ACCEPTABLE_PLAN_STATUSES = {"WOULD_WRITE", "WOULD_SKIP_ALREADY_DONE_MATCHING"}

_AUTH_KEYS = {
    "schema_version",
    "operation",
    "authorized_by",
    "authorized_at_utc",
    "authorization_statement",
    "attestation",
    "recorded_by",
    "scope",
    "record_sha256",
}
_SCOPE_KEYS = {
    "pinned_proposal_sha256",
    "source_record_count",
    "output_target_count",
    "source_records_digest",
    "write_operation",
}


class LegExecError(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@contextlib.contextmanager
def working_directory(path: Path) -> Iterator[None]:
    """The proposal stores repo-relative record paths, so the writer must run at the root."""
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _record_sha(record: dict[str, Any]) -> str:
    body = {k: v for k, v in record.items() if k != "record_sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def source_records_digest(proposal: dict[str, Any], root: Path) -> tuple[str, dict[str, str]]:
    """Digest of the *current* hashes of exactly the records the proposal names."""
    current: dict[str, str] = {}
    for event in proposal["disposition_events"]:
        path = root / event["affected_record_path"]
        if not path.is_file():
            raise LegExecError("SOURCE_RECORD_MISSING", str(event["affected_record_path"]))
        current[event["affected_record_path"]] = receipt_module.sha256_file(path)
    return receipt_module.mapping_digest(current), current


def build_authorization_record(
    *,
    root: Path,
    authorized_by: str,
    authorized_at_utc: str,
    statement: str,
    recorded_by: dict[str, str],
) -> dict[str, Any]:
    """Transcribe a researcher's statement into a bound, unsigned record (does not write it)."""
    with working_directory(root):
        proposal = load_and_verify_proposal(
            root / PROPOSAL_RELATIVE, expected_sha256=PINNED_PROPOSAL_SHA256
        )
        digest, _ = source_records_digest(proposal, root)
    record: dict[str, Any] = {
        "schema_version": LEG_EXEC_AUTH_SCHEMA,
        "operation": "LEG-EXEC",
        "authorized_by": authorized_by,
        "authorized_at_utc": authorized_at_utc,
        "authorization_statement": statement,
        "attestation": {"type": "RECORDED_RESEARCHER_STATEMENT", "signature": None},
        "recorded_by": recorded_by,
        "scope": {
            "pinned_proposal_sha256": PINNED_PROPOSAL_SHA256,
            "source_record_count": EXPECTED_RECORD_COUNT,
            "output_target_count": EXPECTED_RECORD_COUNT + 1,
            "source_records_digest": digest,
            "write_operation": WRITE_OPERATION,
        },
    }
    record["record_sha256"] = _record_sha(record)
    return record


def verify_authorization(root: Path, *, now: datetime | None = None) -> dict[str, Any]:
    """Verify the recorded authorization against the live repository; raise ``LegExecError``."""
    now = now or datetime.now(UTC)
    path = root / LEG_EXEC_AUTH_RELATIVE
    if not path.is_file():
        raise LegExecError("LEG_EXEC_NOT_AUTHORIZED", f"no recorded authorization at {path}")
    try:
        record = json.loads(path.read_bytes())
    except json.JSONDecodeError as exc:
        raise LegExecError("LEG_EXEC_AUTH_INVALID", f"unreadable: {exc}") from exc
    if not isinstance(record, dict) or set(record) != _AUTH_KEYS:
        raise LegExecError(
            "LEG_EXEC_AUTH_INVALID",
            f"fields must be exactly {sorted(_AUTH_KEYS)}; flags are never honored",
        )
    if record["schema_version"] != LEG_EXEC_AUTH_SCHEMA or record["operation"] != "LEG-EXEC":
        raise LegExecError("LEG_EXEC_AUTH_INVALID", "wrong schema or operation")
    if record["record_sha256"] != _record_sha(record):
        raise LegExecError("LEG_EXEC_AUTH_INVALID", "record_sha256 does not match the record")
    try:
        allowlist = load_authorized_reviewers(root / receipt_module.DEFAULT_ALLOWLIST_RELATIVE)
    except AuthorizedReviewersLoadError as exc:
        raise LegExecError("AUTHORITY_ALLOWLIST_UNAVAILABLE", str(exc)) from exc
    if record["authorized_by"] not in allowlist:
        raise LegExecError("LEG_EXEC_AUTH_INVALID", "authorized_by is not on the allowlist")
    if (
        not isinstance(record["authorization_statement"], str)
        or not record["authorization_statement"].strip()
    ):
        raise LegExecError("LEG_EXEC_AUTH_INVALID", "the verbatim statement is required")
    try:
        when = datetime.fromisoformat(record["authorized_at_utc"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise LegExecError("LEG_EXEC_AUTH_INVALID", "authorized_at_utc invalid") from exc
    if when.tzinfo is None or when.astimezone(UTC) > now:
        raise LegExecError("LEG_EXEC_AUTH_INVALID", "authorized_at_utc must be a past UTC time")
    recorded_by = record["recorded_by"]
    if (
        not isinstance(recorded_by, dict)
        or recorded_by.get("kind") not in {"researcher", "agent_transcription"}
        or not str(recorded_by.get("identity", "")).strip()
        or (
            recorded_by.get("kind") == "agent_transcription"
            and not str(recorded_by.get("transcription_source", "")).strip()
        )
    ):
        raise LegExecError(
            "LEG_EXEC_AUTH_INVALID",
            "recorded_by needs a kind, an identity and (for transcriptions) a source",
        )
    attestation = record["attestation"]
    if attestation != {"type": "RECORDED_RESEARCHER_STATEMENT", "signature": None}:
        raise LegExecError(
            "LEG_EXEC_AUTH_INVALID", "only an unsigned recorded statement is verifiable here"
        )
    scope = record["scope"]
    if not isinstance(scope, dict) or set(scope) != _SCOPE_KEYS:
        raise LegExecError("LEG_EXEC_AUTH_INVALID", f"scope must be exactly {sorted(_SCOPE_KEYS)}")
    if (
        scope["pinned_proposal_sha256"] != PINNED_PROPOSAL_SHA256
        or scope["source_record_count"] != EXPECTED_RECORD_COUNT
        or scope["output_target_count"] != EXPECTED_RECORD_COUNT + 1
        or scope["write_operation"] != WRITE_OPERATION
    ):
        raise LegExecError(
            "LEG_EXEC_AUTH_SCOPE_MISMATCH", "scope differs from the pinned operation"
        )
    proposal_path = root / PROPOSAL_RELATIVE
    if compute_proposal_sha256(proposal_path) != scope["pinned_proposal_sha256"]:
        raise LegExecError("LEG_EXEC_PROPOSAL_CHANGED", "the proposal no longer matches the pin")
    return record


def _snapshot(reviews: Path) -> dict[str, str]:
    return {
        p.relative_to(reviews).as_posix(): receipt_module.sha256_file(p)
        for p in sorted(reviews.rglob("*"))
        if p.is_file()
    }


def execute_leg_exec(root: Path | str, *, now: datetime | None = None) -> dict[str, Any]:
    """Run LEG-EXEC. Raises ``LegExecError`` before writing anything unless every check holds."""
    base = Path(root).resolve()
    now = now or datetime.now(UTC)
    reviews = base / receipt_module.DEFAULT_REVIEWS_RELATIVE
    authorization = verify_authorization(base, now=now)
    with working_directory(base):
        try:
            proposal = load_and_verify_proposal(
                base / PROPOSAL_RELATIVE,
                expected_sha256=authorization["scope"]["pinned_proposal_sha256"],
            )
            digest, source_hashes = source_records_digest(proposal, base)
            if digest != authorization["scope"]["source_records_digest"]:
                raise LegExecError(
                    "LEG_EXEC_SOURCES_CHANGED",
                    "the source records differ from those the authorization was recorded for",
                )
            plan = plan_invalidation_notices(proposal, reviews_root=reviews, now_utc=now)
        except NoticeWriterValidationError as exc:
            raise LegExecError("LEG_EXEC_PREFLIGHT_FAILED", f"{type(exc).__name__}: {exc}") from exc
        bad = [
            f"{r.event_id}: {r.status}"
            for r in [*plan.results, plan.directory_notice_result]
            if r.status not in ACCEPTABLE_PLAN_STATUSES
        ]
        if bad or len(plan.results) != EXPECTED_RECORD_COUNT:
            raise LegExecError("LEG_EXEC_PLAN_NOT_CLEAN", f"unexpected plan outcome: {bad[:5]}")
        expected_outputs = sorted(
            [Path(r.output_path).relative_to(reviews).as_posix() for r in plan.results]
            + [DIRECTORY_NOTICE_NAME]
        )
        before = _snapshot(reviews)
        report = apply_invalidation_notices(proposal, reviews_root=reviews, now_utc=now)
        after = _snapshot(reviews)

    originals_before = {k: v for k, v in before.items() if k.endswith("_review.json")}
    originals_after = {k: v for k, v in after.items() if k.endswith("_review.json")}
    if originals_before != originals_after:
        raise LegExecError("ORIGINALS_CHANGED", "an original record changed during LEG-EXEC")
    new_files = sorted(set(after) - set(before))
    unexpected = sorted(set(new_files) - set(expected_outputs))
    if unexpected:
        raise LegExecError("UNEXPECTED_OUTPUT", f"files outside the expected set: {unexpected}")
    failures = [
        f"{r.event_id}: {r.status}"
        for r in [*report.results, report.directory_notice_result]
        if r.status not in {"WRITTEN", "SKIPPED_ALREADY_DONE_MATCHING"}
    ]
    missing_outputs = sorted(set(expected_outputs) - set(after))
    notice_checks = [
        verify_invalidation_notice(reviews / out, reviews)
        for out in expected_outputs
        if out.endswith(".json")
    ]
    invalid = [n for n in notice_checks if not n.valid]
    complete = not failures and not missing_outputs and not invalid
    return {
        "schema_version": "leg-exec-operation-report/1",
        "operation": "LEG-EXEC",
        "completed": complete,
        "executed_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authorization_record_sha256": authorization["record_sha256"],
        "authorized_by": authorization["authorized_by"],
        "authorization_attestation": "recorded_statement_unsigned",
        "pinned_proposal_sha256": authorization["scope"]["pinned_proposal_sha256"],
        "source_record_count": len(source_hashes),
        "source_record_sha256": dict(sorted(source_hashes.items())),
        "originals_byte_identical": True,
        "expected_output_inventory": expected_outputs,
        "output_sha256": {k: after[k] for k in expected_outputs if k in after},
        "new_files_this_run": new_files,
        "result_statuses": {
            "records": [r.to_dict() for r in report.results],
            "directory_notice": report.directory_notice_result.to_dict(),
        },
        "failures": failures,
        "missing_outputs": missing_outputs,
        "invalid_notices": [n.problem for n in invalid],
        "ground_truth_created": False,
        "note": "Invalidation notices are not Stage-2.1 records and approve nothing.",
    }
