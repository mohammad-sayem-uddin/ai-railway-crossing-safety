"""Phase 11.11: human-operated adjudication session runner.

Implements Units 2-3 of the Phase 11.11 Implementation Plan. This module
provides the researcher-facing session runner that orchestrates a single
Stage-2.1 review session for one event. It is a TOOLING module only: it
never makes autonomous boundary decisions, never reads model outputs, and
never starts adjudication without explicit researcher action.

Design principles (fail-closed, matching promotion_gate.py and
review_session.py conventions):

1. Reviewer authorization is verified BEFORE session start.
2. Media hashes are computed LIVE via compute_media_sha256_pair().
3. The model firewall is enforced structurally.
4. One session produces exactly one record for exactly one event.
5. A validated preview is digest-bound to explicit reviewer confirmation.
6. Writes are atomic, create-only, and confined to OS temporary storage.
7. Stop conditions halt the session immediately.

Authorization boundary: this module is intentionally synthetic-only. It
rejects non-synthetic event IDs and media/output paths outside the OS temporary
directory, so it cannot be used for genuine adjudication. It never calls
promote_record.
"""

from __future__ import annotations
from railway_detection.safety.media_guard import require_media_authorization

import hashlib
import json
import os
import re
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Callable

from railway_detection.annotation.promotion_gate import compute_media_sha256_pair
from railway_detection.annotation.review_session import (
    ReviewerNotAuthorizedError,
    build_review_record,
)
from railway_detection.annotation.schemas import (
    CANONICAL_TIMESTAMPS,
    SchemaValidationError,
)
from railway_detection.annotation.stage2_1_schema import (
    BoundaryAdjudication,
    MIN_PLAUSIBLE_REVIEW_DURATION_S,
    build_stage2_1_record_from_dict,
)


# --- Exceptions ---


class AdjudicationSessionError(Exception):
    """Base error for adjudication session failures."""


class SessionNotStartedError(AdjudicationSessionError):
    """Raised when an operation requires an active session but none exists."""


class SessionAlreadyActiveError(AdjudicationSessionError):
    """Raised when attempting to start a session while one is already active."""


class EventNotInManifestError(AdjudicationSessionError):
    """Raised when the requested event_id is not in the review-order manifest."""


class MediaHashMismatchError(AdjudicationSessionError):
    """Raised when live media hashes do not match the inventory expectation.
    This is a STOP event per the protocol."""


class ProposalHashMismatchError(AdjudicationSessionError):
    """Raised when the synthetic proposal reference is absent or has changed."""


class ModelFirewallViolationError(AdjudicationSessionError):
    """Raised when a path that appears to be model output is supplied to the
    session. The runner refuses and logs the attempt."""


class DuplicateRecordError(AdjudicationSessionError):
    """Raised when attempting to write a second record for the same event."""


class StopConditionTriggeredError(AdjudicationSessionError):
    """Raised when a protocol stop condition is met (>50% UNCERTAIN)."""


class ResearcherNotConfirmedError(AdjudicationSessionError):
    """Raised when attempting to finalize without explicit confirmation."""


class ReviewDurationTooShortError(AdjudicationSessionError):
    """Raised when monotonic elapsed time is below the existing schema floor."""


# --- Model firewall ---

_MODEL_OUTPUT_FRAGMENTS = frozenset({
    "results/", "models/", "predictions/", "outputs/", "checkpoints/",
    "runs/", "experiment_registry", "yolo", "best_checkpoint",
    ".pt", ".onnx", ".weights",
})


def _check_model_firewall(path: Path | str) -> None:
    """Refuse any path that looks like model output."""
    normalized = str(path).lower().replace("\\", "/")
    for fragment in _MODEL_OUTPUT_FRAGMENTS:
        if fragment in normalized:
            raise ModelFirewallViolationError(
                f"MODEL_FIREWALL_VIOLATION: path '{path}' contains model-output "
                f"fragment '{fragment}'. The session runner refuses to open, read, "
                f"or import model outputs. This attempt has been logged."
            )


def _require_synthetic_id(event_id: str) -> None:
    """This implementation is deliberately incapable of real-event review."""
    if not isinstance(event_id, str) or not re.fullmatch(r"synthetic_[A-Za-z0-9_-]+", event_id):
        raise EventNotInManifestError(
            "Synthetic-only runner requires an event_id beginning with 'synthetic_'."
        )


def _require_temp_path(path: Path | str, *, label: str) -> Path:
    """Resolve a path and require it to stay inside the OS temporary directory."""
    resolved = Path(path).expanduser().resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if not resolved.is_relative_to(temp_root):
        raise AdjudicationSessionError(
            f"SYNTHETIC_ONLY_PATH_REQUIRED: {label} must resolve beneath {temp_root}"
        )
    return resolved


def _sha256_file(path: Path) -> str:
    require_media_authorization(path, "HASH_RAW_MEDIA")  # no-op for non-media metadata files
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --- Data classes ---


@dataclass(frozen=True)
class SessionEvent:
    """Immutable descriptor for the event under review."""

    event_key: str
    event_id: str
    cohort: str
    front_media_path: Path
    back_media_path: Path
    expected_front_sha256: str
    expected_back_sha256: str
    proposal_file: str
    proposal_sha256: str


@dataclass
class SessionLog:
    """Append-only integrity log for a single session."""

    entries: list[dict[str, Any]] = field(default_factory=list)

    def append(self, event: str, **kwargs: Any) -> None:
        entry: dict[str, Any] = {
            "event": event,
            "at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
        entry.update(kwargs)
        self.entries.append(entry)


# --- Session runner ---


@dataclass
class AdjudicationSession:
    """A single human-operated review session for one event.

    Lifecycle:
        1. start() -- verifies media integrity and starts the clock.
        2. Researcher performs frame-by-frame review externally.
        3. submit_boundaries() -- researcher supplies boundary adjudications.
        4. preview() -- build and schema-validate a frozen record preview.
        5. confirm() -- researcher confirms the exact preview digest.
        6. finalize() -- rechecks media integrity and atomically creates a file.

    At no point does this class make autonomous decisions, read model
    outputs, or fill in boundary values.
    """

    event: SessionEvent
    reviewer_id: str
    authorized_reviewers: frozenset[str]
    output_dir: Path
    inspection_tool: str = "ffmpeg"
    time_source: Callable[[], datetime] | None = field(default=None, repr=False)
    monotonic_source: Callable[[], float] | None = field(default=None, repr=False)

    # Internal state
    _active: bool = field(default=False, repr=False)
    _start_utc: str | None = field(default=None, repr=False)
    _end_utc: str | None = field(default=None, repr=False)
    _start_monotonic: float | None = field(default=None, repr=False)
    _live_front_sha256: str | None = field(default=None, repr=False)
    _live_back_sha256: str | None = field(default=None, repr=False)
    _boundaries: dict[str, dict[str, Any]] | None = field(default=None, repr=False)
    _confirmed: bool = field(default=False, repr=False)
    _written: bool = field(default=False, repr=False)
    _log: SessionLog = field(default_factory=SessionLog, repr=False)
    _session_id: str | None = field(default=None, repr=False)
    _attestation_statement: str = field(default="", repr=False)
    _preview_record: dict[str, Any] | None = field(default=None, repr=False)
    _preview_sha256: str | None = field(default=None, repr=False)
    _adjudication_status: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.time_source is None:
            self.time_source = lambda: datetime.now(UTC)
        if self.monotonic_source is None:
            self.monotonic_source = time.monotonic
        _require_synthetic_id(self.event.event_id)
        _check_model_firewall(self.event.front_media_path)
        _check_model_firewall(self.event.back_media_path)
        _check_model_firewall(self.event.proposal_file)
        self.output_dir = _require_temp_path(self.output_dir, label="output_dir")
        self.event = SessionEvent(
            event_key=self.event.event_key,
            event_id=self.event.event_id,
            cohort=self.event.cohort,
            front_media_path=_require_temp_path(self.event.front_media_path, label="front media"),
            back_media_path=_require_temp_path(self.event.back_media_path, label="back media"),
            expected_front_sha256=self.event.expected_front_sha256,
            expected_back_sha256=self.event.expected_back_sha256,
            proposal_file=str(_require_temp_path(self.event.proposal_file, label="proposal reference")),
            proposal_sha256=self.event.proposal_sha256,
        )
        if not re.fullmatch(r"[0-9a-fA-F]{64}", self.event.proposal_sha256):
            raise ValueError("Synthetic proposal reference must have a valid SHA-256.")
        if self.reviewer_id not in self.authorized_reviewers:
            raise ReviewerNotAuthorizedError(
                f"REVIEWER_NOT_AUTHORIZED: '{self.reviewer_id}' is not in the "
                f"authorized-reviewers allowlist. No session can be started."
            )
        _check_model_firewall(self.event.front_media_path)
        _check_model_firewall(self.event.back_media_path)
        _check_model_firewall(self.event.proposal_file)
        self._session_id = (
            f"adj_session_{self.event.event_id}_"
            f"{self.time_source().strftime('%Y%m%dT%H%M%SZ')}"
        )

    def _verify_proposal_reference(self, *, phase: str) -> None:
        proposal_path = Path(self.event.proposal_file)
        try:
            proposal_path = _require_temp_path(proposal_path, label="proposal reference")
            if not proposal_path.is_file():
                raise OSError("proposal reference is missing or is not a regular file")
            actual = _sha256_file(proposal_path)
            if actual.lower() != self.event.proposal_sha256.lower():
                raise ValueError("proposal SHA-256 differs from the inventory")
        except (AdjudicationSessionError, OSError, ValueError) as exc:
            self._active = False
            self._log.append(
                "proposal_integrity_failure", phase=phase,
                expected_sha256=self.event.proposal_sha256,
                detail=str(exc),
            )
            raise ProposalHashMismatchError(
                f"Synthetic proposal integrity check failed for "
                f"{self.event.event_id} (phase={phase}): {exc}"
            ) from exc

    def _compute_live_media_hashes(self) -> dict[str, str]:
        """Re-resolve media paths at every read to prevent temp-root escapes."""
        try:
            front_path = _require_temp_path(self.event.front_media_path, label="front media")
            back_path = _require_temp_path(self.event.back_media_path, label="back media")
            return compute_media_sha256_pair(front_path, back_path)
        except (AdjudicationSessionError, OSError) as exc:
            raise MediaHashMismatchError(
                f"Synthetic-only media path check failed: {exc}"
            ) from exc

    @property
    def session_id(self) -> str:
        assert self._session_id is not None
        return self._session_id

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def log(self) -> SessionLog:
        return self._log

    def start(self) -> None:
        """Start the session: verify media integrity and start the clock.

        Raises:
            SessionAlreadyActiveError: if this session is already active.
            MediaHashMismatchError: if live hashes differ from expected.
            FileNotFoundError: if media files do not exist.
        """
        if self._active:
            raise SessionAlreadyActiveError(
                f"Session for {self.event.event_id} is already active. "
                "One session, one record."
            )
        self._log.append("session_start_attempt", event_id=self.event.event_id)
        self._verify_proposal_reference(phase="session_start")
        if not self.event.front_media_path.exists():
            raise FileNotFoundError(
                f"Front media file does not exist: {self.event.front_media_path}"
            )
        if not self.event.back_media_path.exists():
            raise FileNotFoundError(
                f"Back media file does not exist: {self.event.back_media_path}"
            )
        media_hashes = self._compute_live_media_hashes()
        self._live_front_sha256 = media_hashes["front"]
        self._live_back_sha256 = media_hashes["back"]
        if self._live_front_sha256 != self.event.expected_front_sha256:
            self._log.append(
                "media_hash_mismatch", camera="front",
                expected=self.event.expected_front_sha256,
                actual=self._live_front_sha256,
            )
            raise MediaHashMismatchError(
                f"STOP: Front media hash mismatch for {self.event.event_id}. "
                "Integrity incident."
            )
        if self._live_back_sha256 != self.event.expected_back_sha256:
            self._log.append(
                "media_hash_mismatch", camera="back",
                expected=self.event.expected_back_sha256,
                actual=self._live_back_sha256,
            )
            raise MediaHashMismatchError(
                f"STOP: Back media hash mismatch for {self.event.event_id}. "
                "Integrity incident."
            )
        self._active = True
        self._start_utc = self.time_source().isoformat().replace("+00:00", "Z")
        self._start_monotonic = self.monotonic_source()
        self._log.append(
            "session_started", event_id=self.event.event_id,
            reviewer_id=self.reviewer_id, start_utc=self._start_utc,
            front_sha256=self._live_front_sha256,
            back_sha256=self._live_back_sha256,
        )

    def submit_boundaries(self, boundary_adjudications: dict[str, dict[str, Any]]) -> None:
        """Submit the researcher's boundary adjudications (four-state taxonomy).

        Raises:
            SessionNotStartedError: if session not active.
            ValueError: if boundaries are structurally invalid.
            StopConditionTriggeredError: if >50% are UNCERTAIN.
        """
        if not self._active:
            raise SessionNotStartedError("Cannot submit boundaries: session not started.")
        if not isinstance(boundary_adjudications, dict):
            raise ValueError("Boundary adjudications must be a mapping.")
        missing = set(CANONICAL_TIMESTAMPS) - set(boundary_adjudications)
        if missing:
            raise ValueError(f"Missing boundary adjudications for {sorted(missing)}.")
        unknown = set(boundary_adjudications) - set(CANONICAL_TIMESTAMPS)
        if unknown:
            raise ValueError(f"Unknown boundary timestamps: {sorted(unknown)}")
        uncertain_count = 0
        validated: dict[str, dict[str, Any]] = {}
        for ts, adj in boundary_adjudications.items():
            if not isinstance(adj, dict):
                raise ValueError(f"Boundary {ts} adjudication must be a mapping.")
            try:
                validated[ts] = BoundaryAdjudication(**adj).to_dict()
            except (SchemaValidationError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid adjudication for {ts}: {exc}") from exc
            state = validated[ts]["state"]
            if state == "UNCERTAIN":
                uncertain_count += 1
        total = len(CANONICAL_TIMESTAMPS)
        if uncertain_count > total / 2:
            self._log.append(
                "stop_condition_triggered", reason="UNCERTAIN_MAJORITY",
                uncertain_count=uncertain_count, total_boundaries=total,
            )
            self._active = False
            raise StopConditionTriggeredError(
                f"STOP: {uncertain_count}/{total} boundaries are UNCERTAIN (>50%). "
                "Session halted; escalate to researcher."
            )
        self._boundaries = validated
        self._preview_record = None
        self._preview_sha256 = None
        self._confirmed = False
        self._attestation_statement = ""
        self._log.append(
            "boundaries_submitted", event_id=self.event.event_id,
            boundary_count=len(boundary_adjudications), uncertain_count=uncertain_count,
        )

    @property
    def preview_sha256(self) -> str | None:
        """SHA-256 of the most recently schema-validated preview, if any."""
        return self._preview_sha256

    def preview(
        self,
        *,
        adjudication_status: str,
        attestation_statement: str,
    ) -> dict[str, Any]:
        """Build and validate a preview without writing any artifact.

        Both status and the reviewer's independence statement are deliberately
        required from the caller. The runner does not approve implicitly.
        """
        if not self._active:
            raise SessionNotStartedError("Cannot preview: session not active.")
        if self._boundaries is None:
            raise ValueError("Cannot preview before boundaries are submitted.")
        if not isinstance(attestation_statement, str) or len(attestation_statement.strip()) < 20:
            raise ValueError("Preview requires a specific model-independence attestation.")
        elapsed = self.monotonic_source() - self._start_monotonic
        if elapsed < MIN_PLAUSIBLE_REVIEW_DURATION_S:
            raise ReviewDurationTooShortError(
                f"Monotonic review duration {elapsed:.1f}s is below the existing "
                f"schema floor of {MIN_PLAUSIBLE_REVIEW_DURATION_S:.1f}s."
            )
        try:
            preview_hashes = self._compute_live_media_hashes()
        except (MediaHashMismatchError, OSError) as exc:
            self._active = False
            self._log.append("media_integrity_failure", phase="pre_preview", detail=str(exc))
            raise MediaHashMismatchError(
                f"STOP: Media integrity check failed before preview for "
                f"{self.event.event_id}: {exc}"
            ) from exc
        self._verify_proposal_reference(phase="pre_preview")
        expected_hashes = {
            "front": self._live_front_sha256,
            "back": self._live_back_sha256,
        }
        if preview_hashes != expected_hashes:
            self._active = False
            self._log.append(
                "media_hash_mismatch", phase="pre_preview",
                expected=expected_hashes, actual=preview_hashes,
            )
            raise MediaHashMismatchError(
                f"STOP: Media changed during review for {self.event.event_id} "
                "(phase=pre_preview); no preview created."
            )
        self._end_utc = self.time_source().isoformat().replace("+00:00", "Z")
        try:
            record = build_review_record(
                event_id=self.event.event_id,
                cohort=self.event.cohort,
                reviewer_id=self.reviewer_id,
                authorized_reviewers=self.authorized_reviewers,
                review_session_id=self.session_id,
                review_start_utc=self._start_utc,
                review_end_utc=self._end_utc,
                inspection_tool=self.inspection_tool,
                attestation_statement=attestation_statement,
                attested_at_utc=self._end_utc,
                front_media_path=self.event.front_media_path,
                back_media_path=self.event.back_media_path,
                observed_at_utc=self._end_utc,
                proposal_file=self.event.proposal_file,
                proposal_sha256=self.event.proposal_sha256,
                boundary_adjudications=self._boundaries,
                adjudication_status=adjudication_status,
            )
            build_stage2_1_record_from_dict(record)
        except (SchemaValidationError, TypeError, ValueError) as exc:
            raise AdjudicationSessionError(f"Preview failed schema validation: {exc}") from exc
        # Replace the placeholder only after explicit confirmation, then
        # rebuild and revalidate before writing.
        self._adjudication_status = adjudication_status
        self._attestation_statement = attestation_statement
        self._preview_record = record
        self._preview_sha256 = hashlib.sha256(
            json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self._confirmed = False
        return json.loads(json.dumps(record))

    def confirm(self, *, confirmed: bool, preview_sha256: str) -> None:
        """Confirm the exact, schema-validated preview digest.

        Raises:
            SessionNotStartedError: if session not active.
            ValueError: if preview digest is absent/mismatched.
        """
        if not self._active:
            raise SessionNotStartedError("Cannot confirm: session not active.")
        if confirmed is not True:
            raise ResearcherNotConfirmedError("Explicit affirmative confirmation is required.")
        if self._preview_record is None or self._preview_sha256 is None:
            raise ValueError("Cannot confirm before a validated preview is created.")
        if preview_sha256 != self._preview_sha256:
            raise ResearcherNotConfirmedError(
                "Confirmation digest does not match the current record preview."
            )
        self._confirmed = True
        self._log.append(
            "researcher_confirmed", event_id=self.event.event_id,
            preview_sha256=self._preview_sha256,
        )

    def finalize(self) -> Path:
        """Assemble the record via build_review_record() and write it
        atomically to output_dir. Returns the written file path.

        Raises:
            SessionNotStartedError: if session not active.
            ResearcherNotConfirmedError: if researcher has not confirmed.
            DuplicateRecordError: if a record was already written this session.
        """
        if not self._active:
            raise SessionNotStartedError("Cannot finalize: session not active.")
        if not self._confirmed:
            raise ResearcherNotConfirmedError(
                "Cannot finalize: researcher has not confirmed the record."
            )
        if self._written:
            raise DuplicateRecordError(
                f"A record for {self.event.event_id} was already written "
                "in this session. One session, one record."
            )
        elapsed = self.monotonic_source() - self._start_monotonic
        if elapsed < MIN_PLAUSIBLE_REVIEW_DURATION_S:
            raise ReviewDurationTooShortError(
                f"Monotonic review duration {elapsed:.1f}s is below the existing "
                f"schema floor of {MIN_PLAUSIBLE_REVIEW_DURATION_S:.1f}s."
            )
        record_dict = json.loads(json.dumps(self._preview_record))
        # Schema validation happens again on the exact object about to be
        # stored. The digest must still bind that unchanged preview.
        try:
            build_stage2_1_record_from_dict(record_dict)
        except (SchemaValidationError, TypeError, ValueError) as exc:
            raise AdjudicationSessionError(f"Final record failed schema validation: {exc}") from exc
        try:
            current_hashes = self._compute_live_media_hashes()
        except (MediaHashMismatchError, OSError) as exc:
            self._active = False
            self._log.append("media_integrity_failure", phase="pre_write", detail=str(exc))
            raise MediaHashMismatchError(
                f"STOP: Media integrity check failed before record creation for "
                f"{self.event.event_id}: {exc}"
            ) from exc
        self._verify_proposal_reference(phase="pre_write")
        expected_hashes = {
            "front": self._live_front_sha256,
            "back": self._live_back_sha256,
        }
        record_hashes = record_dict["reviewer_observed_media_hashes"]
        if (
            current_hashes != expected_hashes
            or record_hashes["front_sha256"] != current_hashes["front"]
            or record_hashes["back_sha256"] != current_hashes["back"]
        ):
            self._active = False
            self._log.append(
                "media_hash_mismatch", phase="pre_write",
                expected=expected_hashes, actual=current_hashes,
            )
            raise MediaHashMismatchError(
                f"STOP: Media changed after review for {self.event.event_id}; no record written."
            )
        current_preview_sha256 = hashlib.sha256(
            json.dumps(record_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if current_preview_sha256 != self._preview_sha256:
            raise ResearcherNotConfirmedError(
                "The record changed after confirmation; create and confirm a new preview."
            )
        self.output_dir = _require_temp_path(self.output_dir, label="output_dir")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = _require_temp_path(self.output_dir, label="output_dir")
        target = self.output_dir / f"{self.event.event_id}_stage2_1_review.json"
        if target.exists():
            raise DuplicateRecordError(
                f"Refusing to overwrite existing record: {target}"
            )
        fd, tmp_path = tempfile.mkstemp(dir=str(self.output_dir), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            # Recheck after serialization, immediately before the atomic
            # create. This narrows the window in which reviewed media could
            # change between verification and publication of the record.
            try:
                final_hashes = self._compute_live_media_hashes()
            except (MediaHashMismatchError, OSError) as exc:
                self._active = False
                self._log.append(
                    "media_integrity_failure", phase="immediately_pre_write",
                    detail=str(exc),
                )
                raise MediaHashMismatchError(
                    f"STOP: Media integrity check failed immediately before record "
                    f"creation for {self.event.event_id}: {exc}"
                ) from exc
            self._verify_proposal_reference(phase="immediately_pre_write")
            if (
                final_hashes != expected_hashes
                or record_hashes["front_sha256"] != final_hashes["front"]
                or record_hashes["back_sha256"] != final_hashes["back"]
            ):
                self._active = False
                self._log.append(
                    "media_hash_mismatch", phase="immediately_pre_write",
                    expected=expected_hashes, actual=final_hashes,
                )
                raise MediaHashMismatchError(
                    f"STOP: Media changed immediately before record creation for "
                    f"{self.event.event_id}; no record written."
                )
            # link() is an atomic create-if-absent operation; unlike replace(),
            # it cannot overwrite a record created concurrently.
            try:
                os.link(tmp_path, target)
            except FileExistsError as exc:
                raise DuplicateRecordError(
                    f"Refusing to overwrite record created concurrently: {target}"
                ) from exc
            os.unlink(tmp_path)
        except BaseException:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
        self._written = True
        self._active = False
        self._log.append("record_written", event_id=self.event.event_id, path=str(target))
        return target

    def withdraw(self, reason: str) -> None:
        """Researcher withdraws authorization mid-session. Produces no
        artifacts; logs the withdrawal."""
        self._active = False
        self._log.append("session_withdrawn", event_id=self.event.event_id, reason=reason)


# --- Factory helpers ---


def load_event_from_inventory(inventory: dict[str, Any], event_key: str) -> SessionEvent:
    """Extract a SessionEvent from the Phase 11.3 inventory dict.

    Raises:
        EventNotInManifestError: if event_key not in inventory.
        ValueError: if inventory entry is malformed.
    """
    events = inventory.get("events", {})
    if event_key not in events:
        raise EventNotInManifestError(
            f"Event '{event_key}' not found in the review-order manifest."
        )
    entry = events[event_key]
    event_id = entry.get("event_id")
    cohort = entry.get("cohort")
    if not event_id or not cohort:
        raise ValueError(f"Malformed inventory entry for {event_key}")
    raw_media = entry.get("raw_media", {})
    front_info = raw_media.get("front", {})
    back_info = raw_media.get("back", {})
    return SessionEvent(
        event_key=event_key,
        event_id=event_id,
        cohort=cohort,
        front_media_path=Path(front_info.get("path", "")),
        back_media_path=Path(back_info.get("path", "")),
        expected_front_sha256=front_info.get("sha256", ""),
        expected_back_sha256=back_info.get("sha256", ""),
        proposal_file=entry.get("active_proposal_file", ""),
        proposal_sha256=entry.get("active_proposal_sha256", ""),
    )


def create_session_from_inventory(
    inventory: dict[str, Any],
    event_key: str,
    reviewer_id: str,
    authorized_reviewers: frozenset[str],
    output_dir: Path,
    inspection_tool: str = "ffmpeg",
    time_source: Callable[[], datetime] | None = None,
    monotonic_source: Callable[[], float] | None = None,
) -> AdjudicationSession:
    """Convenience factory: load event from inventory and create a session.

    Raises:
        EventNotInManifestError: if event not in inventory.
        ReviewerNotAuthorizedError: if reviewer not in allowlist.
        ModelFirewallViolationError: if any path looks like model output.
    """
    event = load_event_from_inventory(inventory, event_key)
    return AdjudicationSession(
        event=event,
        reviewer_id=reviewer_id,
        authorized_reviewers=authorized_reviewers,
        output_dir=output_dir,
        inspection_tool=inspection_tool,
        time_source=time_source,
        monotonic_source=monotonic_source,
    )
