"""Phase 11.6A: applies a previously-generated legacy-invalidation proposal
by writing non-destructive sibling notice files and one directory-level
notice.

This module performs the ACTUAL WRITE step that
`promotion_gate.propose_invalidation()`/`write_invalidation_proposal()`
deliberately do not: those two functions only ever read a real record (to
capture its hash for the audit trail) and write to a caller-chosen
proposal-log path, never into the reviews tree itself.

Nothing in this module is invoked against the real
`data/ground_truth/reviews/` directory by any phase to date -- every test
uses a synthetic `tmp_path` fixture. Applying this module to the real 27
records is a separate, not-yet-authorized action.

Design constraints (Phase 11.6A brief):
- Validate the whole batch before writing anything (fail closed) --
  `validate_proposal_for_application` never writes and raises on the first
  violation found, rejecting the entire batch.
- Immediately before each individual write, re-verify the target's current
  SHA-256 against the hash captured in the proposal -- never trust the
  pre-flight validation alone.
- Never overwrite a target review record (never opened for writing, ever)
  or an existing notice (`O_CREAT | O_EXCL` -- the OS itself refuses to
  clobber an existing file, including one that is a symlink).
- Process records independently; a single failure must not abort the batch
  and must not roll back already-successful writes.
- Resume is idempotent only when an existing output's content exactly
  matches what would be written now; a mismatched existing output is a
  reported CONFLICT, never silently replaced.
- This operation is explicitly NOT atomic across its (up to) 28 outputs.
  See `apply_invalidation_notices`'s docstring for the documented recovery
  procedure and the one race condition this implementation cannot fully
  eliminate.

Phase 11.6C hardening (closing `docs/PHASE11_6B_EXECUTION_READINESS_AUDIT.md`'s
findings F1/F2/F4/F5; F3 is a test-coverage finding, closed in
`tests/test_phase11_6c_notice_writer_hardening.py`, not here):
- **F1**: a writer that loses the O_CREAT|O_EXCL creation race and then
  reads an UNPARSEABLE existing output (the signature of reading a file a
  concurrent winner has created but not yet finished writing) is now
  classified `CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE`, distinct from the
  permanent-looking `CONFLICT_EXISTING_OUTPUT_MISMATCH` used for content
  that was already present before this process ever attempted a write, or
  that is readable but genuinely different. This is a classification
  improvement only -- no-overwrite behavior is unchanged either way.
- **F2**: `load_and_verify_proposal()` binds application to the EXACT
  proposal file a human reviewed, by raw-byte SHA-256, supplied explicitly
  by the caller (never computed from whatever happens to be on disk) --
  see that function's docstring for the full rule and rationale.
- **F4**: notice content now carries the proposal's own
  `authorized_statement` verbatim and the `note` field explicitly states
  that the notice's existence is the applied marker, not independent proof
  of human authorization.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

EXPECTED_RECORD_COUNT = 27
REVIEW_FILE_SUFFIX = "_review.json"
NOTICE_SUFFIX = ".INVALIDATION_NOTICE.json"
DIRECTORY_NOTICE_NAME = "_INTEGRITY_NOTICE.md"

NOTICE_WRITE_STATUSES = (
    "WRITTEN",
    "SKIPPED_ALREADY_DONE_MATCHING",
    "CONFLICT_EXISTING_OUTPUT_MISMATCH",
    "CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE",
    "SKIPPED_TARGET_HASH_MISMATCH",
    "SKIPPED_TARGET_MISSING",
    "FAILED_WRITE_ERROR",
)

# Dry-run statuses. Kept disjoint from the applied statuses above so a plan
# can never be read as evidence that a notice was actually written.
NOTICE_PLAN_STATUSES = (
    "WOULD_WRITE",
    "WOULD_SKIP_ALREADY_DONE_MATCHING",
    "WOULD_SKIP_TARGET_HASH_MISMATCH",
    "WOULD_SKIP_TARGET_MISSING",
    "WOULD_CONFLICT_EXISTING_OUTPUT_MISMATCH",
    "WOULD_CONFLICT_EXISTING_UNREADABLE",
)

ALL_NOTICE_STATUSES = NOTICE_WRITE_STATUSES + NOTICE_PLAN_STATUSES

_REQUIRED_EVENT_FIELDS = (
    "event_id", "reason", "actor", "authorized_statement", "at_utc",
    "affected_record_path", "affected_record_sha256",
)


class NoticeWriterValidationError(Exception):
    """Raised before any file is written -- the whole batch is rejected,
    fail-closed, on the first schema/scope/path violation found."""


class ProposalBindingError(NoticeWriterValidationError):
    """Raised by `load_and_verify_proposal` when a proposal file's raw-byte
    content does not match the caller-supplied `expected_sha256` -- the
    file has changed, been regenerated, or been substituted since it was
    reviewed. Never written past this point; see that function's docstring.
    """


@dataclass
class NoticeWriteResult:
    event_id: str
    output_path: str
    status: str
    detail: str

    def __post_init__(self) -> None:
        if self.status not in ALL_NOTICE_STATUSES:
            raise ValueError(f"status must be one of {ALL_NOTICE_STATUSES}, got {self.status!r}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NoticeWriteReport:
    results: list[NoticeWriteResult]
    directory_notice_result: NoticeWriteResult
    started_at_utc: str
    finished_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self.results],
            "directory_notice_result": self.directory_notice_result.to_dict(),
            "started_at_utc": self.started_at_utc,
            "finished_at_utc": self.finished_at_utc,
        }

    def summary_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {s: 0 for s in ALL_NOTICE_STATUSES}
        for r in self.results:
            counts[r.status] += 1
        return counts


def _require_hex_sha256(value: str, *, where: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
        raise NoticeWriterValidationError(f"{where}: not a valid 64-character hex SHA-256: {value!r}")


def validate_proposal_for_application(
    proposal: dict[str, Any],
    *,
    reviews_root: Path,
    protected_roots: list[Path] | None = None,
    expected_count: int = EXPECTED_RECORD_COUNT,
) -> list[dict[str, Any]]:
    """Validates the WHOLE batch before any write is attempted. Returns a
    list of `{"event": dict, "target_path": Path, "output_path": Path}`
    (resolved, absolute paths) on success. Raises
    `NoticeWriterValidationError` on the first violation found and never
    writes anything, regardless of how many records would otherwise have
    been fine."""
    if not isinstance(proposal, dict) or "disposition_events" not in proposal:
        raise NoticeWriterValidationError("proposal must be a dict with a 'disposition_events' key")
    events = proposal["disposition_events"]
    if not isinstance(events, list):
        raise NoticeWriterValidationError("'disposition_events' must be a list")
    if len(events) != expected_count:
        raise NoticeWriterValidationError(
            f"expected exactly {expected_count} disposition_events, got {len(events)}"
        )

    reviews_root_resolved = reviews_root.resolve()
    protected_resolved = [p.resolve() for p in (protected_roots or [])]
    dir_notice_path_resolved = reviews_root_resolved / DIRECTORY_NOTICE_NAME

    seen_event_ids: set[str] = set()
    seen_targets: set[str] = set()
    seen_outputs: set[str] = set()
    validated: list[dict[str, Any]] = []

    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            raise NoticeWriterValidationError(f"event #{i} is not an object")
        for field_name in _REQUIRED_EVENT_FIELDS:
            value = ev.get(field_name)
            if not isinstance(value, str) or not value.strip():
                raise NoticeWriterValidationError(
                    f"event #{i} ({ev.get('event_id', '?')}) missing/blank required field {field_name!r}"
                )
        _require_hex_sha256(ev["affected_record_sha256"], where=f"event #{i} ({ev['event_id']})")

        if ev["event_id"] in seen_event_ids:
            raise NoticeWriterValidationError(f"duplicate event_id: {ev['event_id']}")
        seen_event_ids.add(ev["event_id"])

        raw_target = ev["affected_record_path"]
        if ".." in Path(raw_target).parts:
            raise NoticeWriterValidationError(
                f"event {ev['event_id']}: path traversal rejected in {raw_target!r}"
            )
        target_path = Path(raw_target)
        if target_path.is_absolute():
            raise NoticeWriterValidationError(
                f"event {ev['event_id']}: affected_record_path must be relative, got {raw_target!r}"
            )

        target_resolved = target_path.resolve()
        if not target_resolved.is_relative_to(reviews_root_resolved):
            raise NoticeWriterValidationError(
                f"event {ev['event_id']}: target {target_resolved} is not inside "
                f"reviews_root {reviews_root_resolved}"
            )
        for proot in protected_resolved:
            if target_resolved.is_relative_to(proot):
                raise NoticeWriterValidationError(
                    f"event {ev['event_id']}: target {target_resolved} falls under "
                    f"protected root {proot}"
                )
        if not target_path.name.endswith(REVIEW_FILE_SUFFIX):
            raise NoticeWriterValidationError(
                f"event {ev['event_id']}: target filename {target_path.name!r} does not "
                f"end with {REVIEW_FILE_SUFFIX!r}"
            )
        if target_resolved.parent.parent != reviews_root_resolved:
            raise NoticeWriterValidationError(
                f"event {ev['event_id']}: target {target_resolved} is not exactly one "
                f"cohort directory below reviews_root"
            )

        if str(target_resolved) in seen_targets:
            raise NoticeWriterValidationError(f"duplicate target path: {target_resolved}")
        seen_targets.add(str(target_resolved))

        output_path = target_resolved.parent / (target_path.stem + NOTICE_SUFFIX)

        if output_path == target_resolved:
            raise NoticeWriterValidationError(
                f"event {ev['event_id']}: output path collides with its own target"
            )
        if output_path == dir_notice_path_resolved:
            raise NoticeWriterValidationError(
                f"event {ev['event_id']}: output path collides with the directory-level notice path"
            )
        if str(output_path) in seen_outputs:
            raise NoticeWriterValidationError(f"duplicate output path: {output_path}")
        # Structurally unreachable given the mandatory REVIEW_FILE_SUFFIX
        # ("_review.json") / NOTICE_SUFFIX (".INVALIDATION_NOTICE.json")
        # patterns enforced above -- no string can end in both, so no valid
        # target can ever equal a derived output. Kept as a defensive
        # assertion (not dead-code-removed) so that if either suffix
        # constant is ever changed, this stops being vacuously true and
        # starts actually protecting something, rather than silently
        # reopening the gap. (Phase 11.6B Finding F5.)
        if str(output_path) in seen_targets:
            raise NoticeWriterValidationError(
                f"output path collides with another record's target: {output_path}"
            )
        seen_outputs.add(str(output_path))

        validated.append({"event": ev, "target_path": target_resolved, "output_path": output_path})

    return validated


def compute_proposal_sha256(proposal_path: Path) -> str:
    """Computes the RAW-BYTE SHA-256 of a proposal file exactly as it sits
    on disk -- not a canonical/semantic hash of its parsed content.

    This is a deliberate choice, not an oversight: `configs/frozen_experiment_v1.yaml`'s
    integrity is checked with a *canonical* (parsed, re-serialized)
    hash (`railway_detection.experiments.frozen_config.compute_canonical_config_hash`)
    because that config is allowed to be reformatted without changing its
    meaning. A legacy-invalidation proposal is different: a human reviewed
    this *exact* file -- including the precise wording of every `reason`
    and `authorized_statement` string -- as the dry-run plan. A canonical
    hash would accept any semantically-equivalent rewording or
    reformatting as "the same reviewed proposal," which is exactly what
    Finding F2 (`docs/PHASE11_6B_EXECUTION_READINESS_AUDIT.md`) identified
    as a gap: application should be bound to the literal artifact that was
    reviewed, not to "a proposal that means the same thing."
    """
    return hashlib.sha256(proposal_path.read_bytes()).hexdigest()


def load_and_verify_proposal(proposal_path: Path, *, expected_sha256: str) -> dict[str, Any]:
    """Reads a proposal file, verifies its raw-byte SHA-256 against
    `expected_sha256` (REQUIRED -- there is no default, deliberately: this
    function never computes "the hash of whatever happens to be on disk"
    and treats that as correct, which would make the check meaningless),
    and only then parses and returns it as JSON.

    Raises `ProposalBindingError` -- fail-closed, before any output is
    written -- if the file has changed, been regenerated, or been
    substituted since `expected_sha256` was recorded. The caller is
    responsible for then separately running `validate_proposal_for_application`
    on the returned dict (this function does not re-implement that
    structural check) before calling `apply_invalidation_notices`.

    **This hash check proves content integrity only -- it is NOT proof of
    human authorization.** `expected_sha256` being correct means "this is
    the exact file that was reviewed"; it says nothing about who reviewed
    it or whether they authorized acting on it. That authorization is the
    separate, human-completed record in
    `docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md` Section 6 (scope,
    mechanism, decision-maker, date) -- this function does not read or
    check that document, and a caller must not treat a passing hash check
    as substituting for it.
    """
    if not isinstance(expected_sha256, str) or not expected_sha256.strip():
        raise ProposalBindingError(
            "expected_sha256 must be a non-empty string supplied explicitly by the caller "
            "-- it is never computed from the proposal file itself"
        )
    _require_hex_sha256(expected_sha256, where="expected_sha256")

    raw_bytes = proposal_path.read_bytes()
    actual_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ProposalBindingError(
            f"proposal file {proposal_path} does not match the expected reviewed hash -- "
            f"expected {expected_sha256}, actual {actual_sha256}. The file has changed, been "
            f"regenerated, or been substituted since it was reviewed; refusing to apply it."
        )

    return json.loads(raw_bytes.decode("utf-8"))


def _atomic_exclusive_write(path: Path, content: str) -> None:
    """Writes `content` to `path` using O_CREAT|O_EXCL so the OS itself
    refuses to overwrite an existing file -- this is what eliminates the
    destination-overwrite race, even if something else creates the file in
    the gap between our existence check and this call."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)


def _build_notice_content(ev: dict[str, Any]) -> dict[str, Any]:
    """Pure function of the proposal event only -- deliberately does NOT
    embed a write-time wall-clock timestamp, so that re-running this
    against an already-written output produces byte-identical content and
    the idempotency check (exact equality) is meaningful across runs.

    Phase 11.6B Finding F4: the notice's own existence IS the applied,
    non-destructive invalidation marker (that is the entire point of the
    sibling-notice mechanism) -- but a notice being WRITTEN must never be
    read, by itself, as independent proof that a human formally authorized
    it. `authorized_statement` is now carried verbatim from the proposal so
    that claim is directly inspectable in the notice itself, and `note`
    says explicitly where the actual, separately-signed authorization
    record lives."""
    return {
        "notice_type": "LEGACY_REVIEW_INVALIDATION_NOTICE",
        "applies_to_file": ev["affected_record_path"],
        "applies_to_file_sha256_at_notice_time": ev["affected_record_sha256"],
        "disposition": "INVALIDATED",
        "proposed_by": ev["actor"],
        "proposed_at_utc": ev["at_utc"],
        "authorized_statement": ev["authorized_statement"],
        "reason": ev["reason"],
        "note": (
            "This notice IS the applied, non-destructive invalidation marker for the "
            "file named in 'applies_to_file' -- its existence implements the disposition. "
            "It does NOT, by itself, independently constitute or prove human authorization "
            "beyond the 'authorized_statement' recorded above; the full, separately-signed "
            "authorization record is docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md Section 6. "
            "This notice never modifies, moves, or deletes the file it describes -- that "
            "file's content is preserved exactly as it was, verified by the SHA-256 above "
            "at the moment this notice was written. See the full proposal log for the "
            "complete, tamper-evident disposition history."
        ),
    }


def _plan_one_record(ev: dict[str, Any], target_path: Path, output_path: Path) -> NoticeWriteResult:
    """Classify what `_process_one_record` would do, without writing anything.

    Mirrors the write path's decision order exactly -- target existence, then
    live target hash, then destination state -- so a dry run is a faithful
    preview rather than an independent approximation. Every status is prefixed
    `WOULD_` so a plan can never be mistaken for an applied result.
    """
    if not target_path.exists():
        return NoticeWriteResult(
            ev["event_id"], str(output_path), "WOULD_SKIP_TARGET_MISSING",
            f"target {target_path} does not exist",
        )
    actual_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()
    if actual_hash != ev["affected_record_sha256"]:
        return NoticeWriteResult(
            ev["event_id"], str(output_path), "WOULD_SKIP_TARGET_HASH_MISMATCH",
            f"expected {ev['affected_record_sha256']} but target currently hashes to {actual_hash}",
        )

    expected_content = _build_notice_content(ev)
    expected_json = json.dumps(expected_content, indent=2, sort_keys=True) + "\n"
    planned_sha256 = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()

    if output_path.exists():
        try:
            existing = output_path.read_text(encoding="utf-8")
        except OSError as exc:
            return NoticeWriteResult(
                ev["event_id"], str(output_path), "WOULD_CONFLICT_EXISTING_UNREADABLE", str(exc),
            )
        if existing == expected_json:
            return NoticeWriteResult(
                ev["event_id"], str(output_path), "WOULD_SKIP_ALREADY_DONE_MATCHING",
                f"notice already present and byte-identical (sha256 {planned_sha256})",
            )
        return NoticeWriteResult(
            ev["event_id"], str(output_path), "WOULD_CONFLICT_EXISTING_OUTPUT_MISMATCH",
            "a different notice already exists at this path; it would not be overwritten",
        )

    return NoticeWriteResult(
        ev["event_id"], str(output_path), "WOULD_WRITE",
        f"notice would be created with sha256 {planned_sha256}",
    )


def plan_invalidation_notices(
    proposal: dict[str, Any],
    *,
    reviews_root: Path,
    protected_roots: list[Path] | None = None,
    expected_count: int = EXPECTED_RECORD_COUNT,
    now_utc: datetime | None = None,
) -> NoticeWriteReport:
    """Dry-run companion to `apply_invalidation_notices`: writes nothing.

    Runs the same `validate_proposal_for_application` pre-flight and the same
    per-record integrity rechecks, then reports the action that would be taken
    for every record and for the directory notice. This function opens no file
    for writing and creates no directory, so it is safe to run against the real
    `data/ground_truth/reviews/` tree at any time, including before any
    execution authorization exists.

    It is a preview, not an authorization: a clean plan does not by itself
    permit execution.
    """
    validated = validate_proposal_for_application(
        proposal, reviews_root=reviews_root, protected_roots=protected_roots,
        expected_count=expected_count,
    )
    started = (
        (now_utc or datetime.now(UTC))
        .astimezone(UTC)
        .isoformat()
        .replace("+00:00", "Z")
    )

    results = [
        _plan_one_record(item["event"], item["target_path"], item["output_path"])
        for item in validated
    ]

    dir_notice_path = reviews_root.resolve() / DIRECTORY_NOTICE_NAME
    sorted_ids = sorted(item["event"]["event_id"] for item in validated)
    dir_content = _build_directory_notice_content(sorted_ids)
    if dir_notice_path.exists():
        try:
            existing = dir_notice_path.read_text(encoding="utf-8")
        except OSError as exc:
            dir_result = NoticeWriteResult(
                "<directory>", str(dir_notice_path), "WOULD_CONFLICT_EXISTING_UNREADABLE", str(exc),
            )
        else:
            dir_result = NoticeWriteResult(
                "<directory>", str(dir_notice_path),
                "WOULD_SKIP_ALREADY_DONE_MATCHING" if existing == dir_content
                else "WOULD_CONFLICT_EXISTING_OUTPUT_MISMATCH",
                "directory notice already present",
            )
    else:
        dir_result = NoticeWriteResult(
            "<directory>", str(dir_notice_path), "WOULD_WRITE",
            f"directory notice would be created covering {len(sorted_ids)} record(s)",
        )

    finished = (
        datetime.now(UTC).astimezone(UTC).isoformat().replace("+00:00", "Z")
    )
    return NoticeWriteReport(
        results=results, directory_notice_result=dir_result,
        started_at_utc=started, finished_at_utc=finished,
    )


def _process_one_record(ev: dict[str, Any], target_path: Path, output_path: Path) -> NoticeWriteResult:
    # Recheck immediately before writing -- never trust the pre-flight validation alone.
    if not target_path.exists():
        return NoticeWriteResult(
            ev["event_id"], str(output_path), "SKIPPED_TARGET_MISSING",
            f"target {target_path} does not exist at write time",
        )
    actual_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()
    if actual_hash != ev["affected_record_sha256"]:
        return NoticeWriteResult(
            ev["event_id"], str(output_path), "SKIPPED_TARGET_HASH_MISMATCH",
            f"expected {ev['affected_record_sha256']} but target currently hashes to {actual_hash}",
        )

    expected_content = _build_notice_content(ev)
    expected_json = json.dumps(expected_content, indent=2, sort_keys=True) + "\n"

    if output_path.exists():
        return _reconcile_existing(
            ev["event_id"], output_path, expected_content, is_json=True, came_from_race=False,
        )

    try:
        _atomic_exclusive_write(output_path, expected_json)
    except FileExistsError:
        # Lost a creation race in the gap between our .exists() check above
        # and the exclusive open -- classify exactly as the "already
        # exists" branch would, never silently proceed as if we had
        # written it ourselves. (Phase 11.6B F1 / Phase 11.6C correction:
        # the retryable-vs-permanent decision is based on what is actually
        # read, not on whether we got here via this branch or the upfront
        # .exists() check above -- see _reconcile_existing's docstring.)
        return _reconcile_existing(
            ev["event_id"], output_path, expected_content, is_json=True, came_from_race=True,
        )
    except OSError as exc:
        return NoticeWriteResult(ev["event_id"], str(output_path), "FAILED_WRITE_ERROR", str(exc))

    return NoticeWriteResult(ev["event_id"], str(output_path), "WRITTEN", "notice written successfully")


def _reconcile_existing(
    event_id: str, output_path: Path, expected_content: Any, *, is_json: bool, came_from_race: bool,
) -> NoticeWriteResult:
    """Classifies a pre-existing output.

    `came_from_race` records HOW we discovered the output already exists --
    `True` means we just lost an `O_CREAT|O_EXCL` creation attempt;
    `False` means our upfront `.exists()` check already found it there --
    and is used only for the human-readable `detail` wording, not for the
    retryable-vs-permanent decision below.

    Finding-F1 correction (Phase 11.6C): an earlier version of this
    function used `came_from_race` to DECIDE retryable-vs-permanent, on
    the premise that the `came_from_race=False` branch could only ever see
    content that was fully there before this call began. **That premise is
    false under genuine concurrency** -- a concurrent writer's in-progress,
    not-yet-complete file can just as easily be observed by the upfront
    `.exists()` check as by a lost `os.open()` race, confirmed empirically
    in this phase (a 3-thread stress test reproducing a
    `CONFLICT_EXISTING_OUTPUT_MISMATCH` for content that, moments later,
    was complete and correct). Classification is therefore now based
    purely on WHAT was read, not on which branch led here:
    - Nothing readable at all (`FileNotFoundError`) -- most plausibly a
      dangling symlink, since a genuine in-progress writer always leaves a
      real, if incomplete, file. This cannot resolve itself with a retry,
      so it is never classified retryable.
    - Readable but unparseable (`JSONDecodeError`) or an exact truncated
      prefix of the expected text -- consistent with a concurrent writer
      caught mid-write, classified `CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE`.
    - Readable, parseable, and genuinely different from what is expected --
      a real disagreement, classified `CONFLICT_EXISTING_OUTPUT_MISMATCH`.

    Limitation, documented rather than silently assumed away: if a race
    winner's write is interrupted such that the file contains VALID but
    incomplete JSON (plausible only for pathological buffering behavior,
    not observed in testing), this still correctly reports
    `CONFLICT_EXISTING_OUTPUT_MISMATCH` rather than the retryable status --
    safe (never overwrites) but not labeled retryable. No broader
    classification scheme (e.g. deep structural partial-content heuristics)
    is attempted."""
    try:
        existing_text = output_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        # Something answered "already exists" (either .exists() or a lost
        # O_EXCL race), yet nothing is actually readable at this path --
        # most plausibly a DANGLING symlink, not a concurrent winner
        # mid-write (a genuine in-progress writer leaves a real, if
        # incomplete, file; it does not leave nothing). Never retryable.
        return NoticeWriteResult(
            event_id, str(output_path), "CONFLICT_EXISTING_OUTPUT_MISMATCH",
            f"output path reports already-existing but nothing is actually readable there "
            f"-- likely a dangling symlink, not an in-progress concurrent write; left "
            f"untouched, requires human review, not a safe retry "
            f"(discovered via {'a lost creation race' if came_from_race else 'an upfront existence check'}): {exc}",
        )
    except OSError as exc:
        return NoticeWriteResult(
            event_id, str(output_path), "CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE",
            f"existing output is not yet readable, consistent with a concurrent writer still "
            f"producing it -- left untouched, not overwritten, safe to retry shortly "
            f"(discovered via {'a lost creation race' if came_from_race else 'an upfront existence check'}): {exc}",
        )

    if is_json:
        try:
            existing: Any = json.loads(existing_text)
        except json.JSONDecodeError as exc:
            return NoticeWriteResult(
                event_id, str(output_path), "CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE",
                f"existing output is not yet valid JSON, consistent with a concurrent writer "
                f"still producing it -- left untouched, not overwritten, safe to retry shortly "
                f"(discovered via {'a lost creation race' if came_from_race else 'an upfront existence check'}): {exc}",
            )
    else:
        existing = existing_text
        # Plain text always "parses", so there is no JSONDecodeError signal
        # to lean on here -- instead, a race-originated partial write looks
        # like a strict prefix of the full expected text, which is what a
        # sequential, not-yet-finished write naturally produces.
        if existing != expected_content and isinstance(expected_content, str) and expected_content.startswith(existing):
            return NoticeWriteResult(
                event_id, str(output_path), "CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE",
                f"existing output looks like a truncated prefix of the expected content, "
                f"consistent with a concurrent writer still producing it -- left untouched, "
                f"not overwritten, safe to retry shortly "
                f"(discovered via {'a lost creation race' if came_from_race else 'an upfront existence check'})",
            )

    if existing == expected_content:
        return NoticeWriteResult(
            event_id, str(output_path), "SKIPPED_ALREADY_DONE_MATCHING",
            "existing output content matches expected -- idempotent skip, nothing written",
        )
    return NoticeWriteResult(
        event_id, str(output_path), "CONFLICT_EXISTING_OUTPUT_MISMATCH",
        "existing output content differs from expected -- left untouched, not overwritten",
    )


def _build_directory_notice_content(sorted_event_ids: list[str]) -> str:
    return (
        "# INTEGRITY NOTICE — all records in this directory\n\n"
        f"Every review record in this directory ({len(sorted_event_ids)} total) is marked "
        "INVALIDATED. This file's existence, and each sibling notice's existence, IS the "
        "applied marker -- it does not independently prove human authorization. See the "
        "sibling `<event>_review.INVALIDATION_NOTICE.json` file next to each record for the "
        "specific evidence, disposition, and `authorized_statement` for that record, and "
        "docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md Section 6 for the full, separately-signed "
        "authorization record.\n\n"
        "These records must not be treated as evidence of genuine human review until "
        "superseded by a real Stage-2.1 record "
        "(src/railway_detection/annotation/stage2_1_schema.py).\n\n"
        "No file in this directory has been deleted or edited. Original content is "
        "preserved byte-for-byte.\n\n"
        "Covered events:\n" + "\n".join(f"- {e}" for e in sorted_event_ids) + "\n"
    )


def _process_directory_notice(output_path: Path, content: str) -> NoticeWriteResult:
    sentinel = "_DIRECTORY_NOTICE_"
    if output_path.exists():
        return _reconcile_existing(sentinel, output_path, content, is_json=False, came_from_race=False)
    try:
        _atomic_exclusive_write(output_path, content)
    except FileExistsError:
        return _reconcile_existing(sentinel, output_path, content, is_json=False, came_from_race=True)
    except OSError as exc:
        return NoticeWriteResult(sentinel, str(output_path), "FAILED_WRITE_ERROR", str(exc))
    return NoticeWriteResult(sentinel, str(output_path), "WRITTEN", "directory notice written successfully")


def apply_invalidation_notices(
    proposal: dict[str, Any],
    *,
    reviews_root: Path,
    protected_roots: list[Path] | None = None,
    expected_count: int = EXPECTED_RECORD_COUNT,
    now_utc: datetime | None = None,
) -> NoticeWriteReport:
    """Applies a previously-generated invalidation proposal (the
    `{"disposition_events": [...]}` structure produced by
    `promotion_gate.write_invalidation_proposal`) by writing one sibling
    notice per record plus one directory-level notice.

    **NOT ATOMIC across its outputs.** A failure partway through this
    function leaves every already-written notice in place (each is
    independently valid and non-destructive -- none depends on another)
    and every not-yet-attempted record unwritten. Re-running this function
    with the same proposal is the documented recovery procedure for an
    ordinary transient failure: already-written, matching notices are
    skipped as `SKIPPED_ALREADY_DONE_MATCHING`; unattempted or previously
    failed records are attempted again. A `FAILED_WRITE_ERROR` may leave a
    truncated or partial file at its output path (e.g. disk full mid-write)
    -- on retry this is detected as `CONFLICT_EXISTING_OUTPUT_MISMATCH`
    (never silently overwritten) and the documented recovery procedure is:
    a human inspects and removes that one specific partial file, then
    retries. No automatic cleanup of a partial file is attempted by this
    function.

    **Race condition this cannot fully eliminate:** the window between
    recomputing a target's hash and opening its sibling notice for
    exclusive creation is minimized (no other I/O happens in between) but
    not zero -- if the target review file were modified in that exact
    window, the notice would be written against a hash that was correct a
    moment earlier but is no longer current at the instant of writing. This
    implementation does not lock the target file (no cross-platform
    file-locking primitive is used), so this specific race is documented,
    not eliminated. In contrast, the destination-overwrite race (two
    callers racing to create the SAME notice file) IS fully eliminated by
    `O_CREAT | O_EXCL`, including when the destination is a pre-existing
    symlink (POSIX `O_EXCL` refuses to open through a symlink regardless of
    its target, verified empirically for this implementation in
    `docs/PHASE11_6B_EXECUTION_READINESS_AUDIT.md`).

    **Genuine concurrent execution** (two callers racing against the same
    `reviews_root`) can still produce a `CONFLICT_POSSIBLY_IN_PROGRESS_RETRYABLE`
    result for a record whose notice is mid-write by the other caller at
    the instant this one reads it -- this is a status-reporting nuance, not
    a safety gap: the underlying content is never corrupted and the
    original record is never at risk either way (Phase 11.6B Finding F1,
    closed in Phase 11.6C). This status means "safe to retry shortly," not
    "investigate a real conflict." `CONFLICT_EXISTING_OUTPUT_MISMATCH`
    remains reserved for output that was already present before this
    process attempted to create it, or that is readable but genuinely
    different -- that status does mean "a human should look at this."

    This function accepts an already-parsed `proposal: dict` and does not
    itself bind to a specific reviewed file -- for real (non-synthetic)
    use, load the proposal via `load_and_verify_proposal()` first (Finding
    F2), which fails closed on a changed/substituted file before this
    function, or anything else, ever runs.
    """
    validated = validate_proposal_for_application(
        proposal, reviews_root=reviews_root, protected_roots=protected_roots,
        expected_count=expected_count,
    )
    started = (now_utc or datetime.now(UTC)).astimezone(UTC).isoformat().replace("+00:00", "Z")

    results = [
        _process_one_record(item["event"], item["target_path"], item["output_path"])
        for item in validated
    ]

    dir_notice_path = reviews_root.resolve() / DIRECTORY_NOTICE_NAME
    sorted_ids = sorted(item["event"]["event_id"] for item in validated)
    dir_content = _build_directory_notice_content(sorted_ids)
    dir_result = _process_directory_notice(dir_notice_path, dir_content)

    finished = datetime.now(UTC).astimezone(UTC).isoformat().replace("+00:00", "Z")
    return NoticeWriteReport(
        results=results, directory_notice_result=dir_result,
        started_at_utc=started, finished_at_utc=finished,
    )
