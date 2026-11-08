"""Phase 11.5: researcher field-level adjudication records.

These records document a specific, narrow thing: the researcher personally
reviewing a Phase 11.4 audit finding (video evidence already extracted and
composited) and confirming, for one boundary on one event, that the
candidate proposal's classification is wrong and what the correct
classification is.

This is explicitly NOT a complete Stage-2.1 review record
(`stage2_1_schema.py`, Phase 11.2) -- a full Stage-2.1 record requires a
timed review session (>= 30s, independently plausible), a model-independence
attestation, and an adjudication decision for every boundary on the event,
none of which a single confirmed finding provides. `FieldAdjudicationRecord`
is a separate, smaller artifact type for exactly this purpose: recording a
researcher's confirmed correction to one specific audit finding, pending
eventual incorporation into a full per-event Stage-2.1 re-review.

Nothing in this module writes to, modifies, or promotes any file under
`data/ground_truth/{proposals,reviews,train_events,no_train_events,
engine_events}/`. It is not wired into `promotion_gate.py` and a
`FieldAdjudicationRecord`, by itself, is not sufficient for Stage 3
eligibility.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
from typing import Any

# Deliberately a SEPARATE, smaller vocabulary from stage2_1_schema.py's
# ADJUDICATION_STATUSES (APPROVED/REJECTED/NEEDS_SECOND_REVIEW/DISPUTED),
# which describes the status of a COMPLETE Stage-2.1 review record, not a
# single field-level correction. Reusing that enum's values here would
# misrepresent a field-level finding as record-level approval/rejection.
FIELD_ADJUDICATION_STATUSES = (
    "FLAGGED_BY_AUDIT",             # Phase 11.4-style: a discrepancy was found and recorded, not yet reviewed by the researcher
    "DISPUTED",                      # the legacy proposal's classification is now actively contested (repository term, reused deliberately)
    "RESEARCHER_CONFIRMED_CORRECTION",  # the researcher reviewed the evidence and confirmed the audit finding
    "RESEARCHER_CONFIRMED_ACCEPTED",    # the researcher reviewed the evidence and confirmed the ORIGINAL proposal was correct after all
    "UNRESOLVED",                    # neither confirmed nor rejected; still open
)


@dataclass
class FieldAdjudicationHistoryEntry:
    event: str
    by: str
    at_utc: str
    status: str

    def __post_init__(self) -> None:
        if self.status not in FIELD_ADJUDICATION_STATUSES:
            raise ValueError(f"status must be one of {FIELD_ADJUDICATION_STATUSES}, got '{self.status}'")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FieldAdjudicationRecord:
    """One researcher-confirmed (or still-open) correction to a single
    boundary on a single event. `legacy_proposal_*` fields describe the
    UNCHANGED candidate proposal being disputed -- this record never
    modifies that file. `adjudication_history` is append-only: new events
    are added, never replacing or removing prior entries."""

    adjudication_id: str
    event_id: str
    boundary: str
    source_video_path: str
    source_video_sha256: str
    legacy_proposal_file: str
    legacy_proposal_version: str
    legacy_claimed_value_s: float | None
    legacy_claimed_classification: str
    legacy_claimed_rationale: str
    phase_11_4_finding_outcome: str
    phase_11_4_finding_evidence: str
    adjudication_history: list[FieldAdjudicationHistoryEntry] = field(default_factory=list)
    current_status: str = "UNRESOLVED"
    corrected_classification: str | None = None
    corrected_value_s: float | None = None
    corrected_rationale: str | None = None
    legacy_record_disposition_note: str = (
        "The legacy candidate proposal and the invalidated Stage-2 review (if any) "
        "referencing this event remain unmodified on disk. This record does NOT "
        "constitute formal invalidation of any legacy approval -- that is a separate, "
        "explicitly researcher-authorized action per docs/PHASE11_3_RESEARCHER_DECISIONS.md "
        "Section 3, not executed by this record."
    )
    stage_2_1_completeness_note: str = (
        "This is a field-level adjudication, not a complete Stage-2.1 review record. "
        "It does not satisfy promotion_gate.py's requirements and is not, by itself, "
        "sufficient for Stage 3 eligibility."
    )

    def __post_init__(self) -> None:
        if self.current_status not in FIELD_ADJUDICATION_STATUSES:
            raise ValueError(f"current_status must be one of {FIELD_ADJUDICATION_STATUSES}")

    def append_event(self, *, by: str, status: str, now_utc: datetime | None = None) -> None:
        ts = (now_utc or datetime.now(UTC)).astimezone(UTC).isoformat().replace("+00:00", "Z")
        entry = FieldAdjudicationHistoryEntry(
            event=f"status_set_to_{status.lower()}", by=by, at_utc=ts, status=status,
        )
        self.adjudication_history.append(entry)
        self.current_status = status

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["adjudication_history"] = [e.to_dict() for e in self.adjudication_history]
        return d
