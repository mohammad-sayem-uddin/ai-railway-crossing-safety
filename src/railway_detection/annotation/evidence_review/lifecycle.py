"""Metadata review lifecycle. No raw opener, human impersonation or receipt issuer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from types import MappingProxyType

from railway_detection.annotation.evidence_review.contracts import (
    FIXTURE,
    RISKS,
    Batch,
    BoundaryObservation,
    EvidenceVerifier,
    Permission,
    ReadinessStatus,
    Reviewer,
    canonical,
    digest,
    integer,
    text,
)


@dataclass(frozen=True)
class Assignment:
    assignment_id: str
    batch_digest: str
    event: str
    reviewer_id: str
    role: str
    source_ids: tuple[str, ...]
    permission_reference: str


@dataclass(frozen=True)
class Adjudication:
    adjudication_id: str
    event: str
    source_id: str
    boundary: str
    adjudicator: str
    contributors: tuple[str, ...]
    state: str
    reason: str
    resolution: BoundaryObservation | None = None
    human_statement_reference: str | None = None
    previous: str | None = None


@dataclass(frozen=True)
class Readiness:
    status: ReadinessStatus
    batch_digest: str
    history_digest: str
    reasons: tuple[str, ...]
    event_reasons: tuple[tuple[str, tuple[str, ...]], ...]
    genuine_evidence_accepted: bool = False


@dataclass(frozen=True)
class PromotionReceipt:
    receipt_id: str
    batch_digest: str
    history_digest: str
    lineage_digest: str
    object_digest: str
    issuer: str
    authorization_reference: str
    verification_reference: str


class ReviewLifecycle:
    """Caller supplies already-authorized metadata, never filenames or approvals.

    Genuine intake additionally requires a deployment-owned verifier. No such
    verifier ships; status strings and references alone never authenticate facts.
    Fixture operations exercise the same structural state machine, retaining
    their classification on every result. No automatic observation/adjudication.
    """

    def __init__(
        self,
        batch: Batch,
        reviewers: tuple[Reviewer, ...],
        *,
        verifier: EvidenceVerifier | None = None,
    ):
        batch.validate()
        if not reviewers or len(set(r.reviewer_id for r in reviewers)) != len(reviewers):
            raise ValueError("unique explicit reviewer roster required")
        self.batch, self.verifier = batch, verifier
        self.roster = MappingProxyType({r.reviewer_id: r for r in reviewers})
        self._assignments: dict[str, Assignment] = {}
        self._sessions: dict[str, str] = {}
        self._observations: dict[str, BoundaryObservation] = {}
        self._latest: dict[tuple[str, str, str], str] = {}
        self._completed: dict[str, tuple[tuple[str, bool], ...]] = {}
        self._adjudications: dict[str, Adjudication] = {}
        self._history: list[str] = []
        self._publications: dict[str, PromotionReceipt] = {}

    @property
    def fixture(self) -> bool:
        return self.batch.classification == FIXTURE

    @property
    def history(self) -> tuple[str, ...]:
        return tuple(self._history)

    @property
    def observations(self) -> tuple[BoundaryObservation, ...]:
        return tuple(self._observations.values())

    @property
    def assignments(self) -> tuple[Assignment, ...]:
        return tuple(self._assignments.values())

    def _record(self, kind: str, value: object) -> None:
        self._history.append(
            canonical(
                {
                    "kind": kind,
                    "record": asdict(value)
                    if is_dataclass(value) and not isinstance(value, type)
                    else value,
                    "classification": self.batch.classification,
                }
            )
        )

    def _verify(self, kind: str, value: object, reference: str | None, now: int) -> str:
        if (
            self.fixture
            or self.verifier is None
            or not reference
            or reference.startswith("synthetic:")
        ):
            raise PermissionError(kind + " requires genuine authenticated evidence")
        principal = self.verifier.verify(kind, digest(value), reference, now)
        text(principal)
        if principal.startswith("synthetic:"):
            raise PermissionError("mock verifier principal cannot authenticate genuine evidence")
        return principal

    def _verify_statement(
        self, kind: str, value: object, reference: str | None, principal: str, now: int
    ) -> None:
        if self._verify(kind, value, reference, now) != principal:
            raise PermissionError("human statement signer differs from assigned principal")

    def _verify_adjudication(self, record: Adjudication, principal: str, now: int) -> None:
        self._verify_statement(
            "HUMAN_ADJUDICATION", record, record.human_statement_reference, principal, now
        )
        resolution = record.resolution
        if (
            resolution is not None
            and resolution.observation.boundary == "T2"
            and resolution.observation.state == "OBSERVABLE"
        ):
            self._verify("PHYSICAL_ENTRY_LANDMARK", resolution, resolution.landmark_evidence, now)

    def _access(
        self, permission: Permission, actor: str, event: str, operation: str, now: int, role: str
    ) -> str:
        integer(now)
        permission.validate(
            actor=actor, batch=digest(self.batch), event=event, operation=operation, now=now
        )
        if event not in dict(self.batch.events) or actor not in self.roster:
            raise PermissionError("unknown batch event/reviewer")
        principal = self.roster[actor].principal(
            event=event, role=role, now=now, fixture=self.fixture, verifier=self.verifier
        )
        if not self.fixture:
            if self._verify("AUTHORIZATION", permission, permission.reference, now) != principal:
                raise PermissionError("permission principal mismatch")
        return principal

    def assign(self, assignment: Assignment, permission: Permission, *, now: int) -> str:
        from railway_detection.annotation.evidence_review.contracts import immutable

        immutable(assignment)
        text(assignment.assignment_id)
        if assignment.role not in ("REVIEWER", "ADJUDICATOR"):
            raise ValueError("explicit review/adjudication role required")
        self._access(
            permission, assignment.reviewer_id, assignment.event, "ASSIGN", now, assignment.role
        )
        if (
            assignment.batch_digest != digest(self.batch)
            or assignment.permission_reference != permission.reference
        ):
            raise ValueError("assignment batch/permission substitution")
        expected = {s.source_id for s in self.batch.sources if s.event == assignment.event}
        if not assignment.source_ids or set(assignment.source_ids) != expected:
            raise ValueError("exact event source assignment required")
        prior = self._assignments.get(assignment.assignment_id)
        if prior:
            if prior != assignment:
                raise ValueError("assignment identity substitution")
            return digest(prior)
        if any(
            (a.reviewer_id, a.event, a.role)
            == (assignment.reviewer_id, assignment.event, assignment.role)
            for a in self.assignments
        ):
            raise ValueError("duplicate assignment under another identity")
        self._assignments[assignment.assignment_id] = assignment
        self._record("ASSIGNMENT", assignment)
        return digest(assignment)

    def open_session(self, assignment_id: str, permission: Permission, *, now: int) -> str:
        a = self._assignment(assignment_id)
        if permission.reference != a.permission_reference:
            raise PermissionError("assignment authorization reference substitution")
        self._access(permission, a.reviewer_id, a.event, "OPEN_SESSION", now, a.role)
        session = digest({"assignment": asdict(a), "batch": digest(self.batch)})
        if assignment_id not in self._sessions:
            self._sessions[assignment_id] = session
            self._record("BLIND_SESSION", {"assignment": assignment_id, "session": session})
        return session

    def _assignment(self, assignment_id: str) -> Assignment:
        if assignment_id not in self._assignments:
            raise ValueError("assignment missing")
        return self._assignments[assignment_id]

    def submit(
        self, assignment_id: str, item: BoundaryObservation, permission: Permission, *, now: int
    ) -> str:
        a = self._assignment(assignment_id)
        if permission.reference != a.permission_reference:
            raise PermissionError("assignment authorization reference substitution")
        principal = self._access(permission, a.reviewer_id, a.event, "SUBMIT", now, "REVIEWER")
        if assignment_id not in self._sessions or a.role != "REVIEWER":
            raise ValueError("blind reviewer session required")
        source = item.validate(self.batch)
        if (
            item.reviewer_id != a.reviewer_id
            or source.event != a.event
            or source.source_id not in a.source_ids
        ):
            raise PermissionError("observation assignment/source scope mismatch")
        if not self.fixture:
            self._verify_statement(
                "HUMAN_OBSERVATION", item, item.human_statement_reference, principal, now
            )
            self._verify("SOURCE_IDENTITY", source, source.verification_reference, now)
            if item.observation.boundary == "T2" and item.observation.state == "OBSERVABLE":
                self._verify("PHYSICAL_ENTRY_LANDMARK", item, item.landmark_evidence, now)
        prior = self._observations.get(item.observation_id)
        if prior:
            if prior != item:
                raise ValueError("original observation cannot be overwritten")
            return digest(prior)
        key = (a.reviewer_id, source.source_id, item.observation.boundary)
        previous_id = self._latest.get(key)
        if previous_id:
            if (
                item.previous != digest(self._observations[previous_id])
                or not item.correction_reason
            ):
                raise ValueError("correction immutable parent/reason missing")
            if assignment_id not in self._completed:
                raise ValueError("first blind observation cannot be silently revised before seal")
        elif item.previous:
            raise ValueError("correction parent missing")
        elif assignment_id in self._completed:
            raise ValueError("completed blind session cannot gain original observations")
        self._observations[item.observation_id] = item
        self._latest[key] = item.observation_id
        self._record("INFORMED_CORRECTION" if previous_id else "BLIND_OBSERVATION", item)
        # A correction invalidates all earlier comparisons/resolutions through digest binding.
        return digest(item)

    def complete(
        self,
        assignment_id: str,
        risks: tuple[tuple[str, bool], ...],
        permission: Permission,
        *,
        now: int,
    ) -> str:
        a = self._assignment(assignment_id)
        if permission.reference != a.permission_reference:
            raise PermissionError("assignment authorization reference substitution")
        self._access(permission, a.reviewer_id, a.event, "COMPLETE", now, "REVIEWER")
        if assignment_id not in self._sessions or a.role != "REVIEWER":
            raise ValueError("reviewer session missing")
        if (
            len(risks) != len(RISKS)
            or set(dict(risks)) != set(RISKS)
            or any(type(v) is not bool for _, v in risks)
        ):
            raise ValueError("all explicit risk assessments required")
        for source in a.source_ids:
            for boundary in self.batch.boundaries:
                if (a.reviewer_id, source, boundary) not in self._latest:
                    raise ValueError("incomplete review boundary set")
        previous = self._completed.get(assignment_id)
        if previous and previous != risks:
            raise ValueError("completion risk record immutable; use new versioned batch")
        if not previous:
            self._completed[assignment_id] = risks
            self._record("REVIEW_COMPLETION", {"assignment": assignment_id, "risks": risks})
        return digest({"assignment": assignment_id, "risks": risks})

    def compare(self, event: str) -> dict:
        if event not in dict(self.batch.events):
            raise ValueError("event missing")
        completed = [
            a
            for a in self.assignments
            if a.event == event and a.assignment_id in self._completed and a.role == "REVIEWER"
        ]
        reasons = {k for a in completed for k, v in self._completed[a.assignment_id] if v}
        rows = [
            self._observations[self._latest[k]]
            for k in self._latest
            if self._observations[self._latest[k]].source_id
            in {s.source_id for s in self.batch.sources if s.event == event}
        ]
        if any(o.observation.state == "UNCERTAIN" for o in rows):
            reasons.add("UNCERTAIN_BOUNDARY")
        if any(o.previous for o in rows):
            reasons.add("CORRECTED_FROM_CANDIDATE")
        if dict(self.batch.events)[event] == "CASE":
            reasons.add("ENGINE_T3_T4_INTERPRETATION")
        disagreements = []
        for source in (s for s in self.batch.sources if s.event == event):
            for boundary in self.batch.boundaries:
                items = [
                    self._observations[self._latest[(a.reviewer_id, source.source_id, boundary)]]
                    for a in completed
                ]
                # Exact comparison, independently per camera. No inferred tolerance or averaging.
                signatures = {
                    canonical({k: v for k, v in asdict(o.observation).items() if k != "rationale"})
                    for o in items
                }
                if len(signatures) > 1:
                    disagreements.append(
                        {
                            "source_id": source.source_id,
                            "boundary": boundary,
                            "contributors": tuple(sorted(digest(o) for o in items)),
                            "state": "UNCERTAIN",
                        }
                    )
        return {
            "event": event,
            "required_second_review": bool(reasons or disagreements),
            "risk_reasons": sorted(reasons),
            "completed_assignments": len(completed),
            "disagreements": disagreements,
            "automatic_adjudication": False,
            "clear_boundary_audit": "RISK_BASED_NO_FIXED_PERCENTAGE",
        }

    def adjudicate(
        self, assignment_id: str, record: Adjudication, permission: Permission, *, now: int
    ) -> str:
        a = self._assignment(assignment_id)
        if permission.reference != a.permission_reference:
            raise PermissionError("assignment authorization reference substitution")
        principal = self._access(
            permission, a.reviewer_id, a.event, "ADJUDICATE", now, "ADJUDICATOR"
        )
        from railway_detection.annotation.evidence_review.contracts import immutable

        immutable(record)
        text(record.adjudication_id)
        text(record.reason)
        if (
            a.role != "ADJUDICATOR"
            or record.adjudicator != a.reviewer_id
            or record.event != a.event
            or assignment_id not in self._sessions
        ):
            raise PermissionError("qualified independent adjudicator session required")
        comparison = self.compare(a.event)
        matching = [
            d
            for d in comparison["disagreements"]
            if (d["source_id"], d["boundary"]) == (record.source_id, record.boundary)
        ]
        if (
            not matching
            or record.contributors != matching[0]["contributors"]
            or len(record.contributors) < 2
        ):
            raise ValueError("adjudication must bind all exact conflicting observation parents")
        contributors = [o for o in self.observations if digest(o) in record.contributors]
        for item in contributors:
            other = self.roster[item.reviewer_id].principal(
                event=a.event,
                role="REVIEWER",
                now=now,
                fixture=self.fixture,
                verifier=self.verifier,
            )
            if other == principal:
                raise PermissionError("adjudicator must be separate from conflicting reviewers")
        if record.state == "UNCERTAIN":
            if record.resolution is not None:
                raise ValueError("unresolved adjudication cannot invent a numeric value")
        elif record.state == "HUMAN_RESOLVED":
            if record.resolution is None:
                raise ValueError("human resolution observation missing")
            source = record.resolution.validate(self.batch)
            if record.resolution.previous is not None:
                raise ValueError(
                    "adjudication resolution cannot carry an orphan observation parent; "
                    "version the adjudication"
                )
            if record.resolution.observation_id in self._observations or any(
                other.adjudication_id != record.adjudication_id
                and other.resolution is not None
                and other.resolution.observation_id == record.resolution.observation_id
                for other in self._adjudications.values()
            ):
                raise ValueError(
                    "adjudication resolution identity duplicates an existing observation"
                )
            if (
                record.resolution.reviewer_id != a.reviewer_id
                or source.event != a.event
                or source.source_id != record.source_id
                or record.resolution.observation.boundary != record.boundary
            ):
                raise ValueError("adjudication resolution source/actor/boundary mismatch")
        else:
            raise ValueError("automatic adjudication forbidden")
        if not self.fixture:
            self._verify_adjudication(record, principal, now)
        prior = self._adjudications.get(record.adjudication_id)
        if prior:
            if prior != record:
                raise ValueError("adjudication original immutable")
            return digest(record)
        previous = [
            r
            for r in self._adjudications.values()
            if (r.event, r.source_id, r.boundary)
            == (record.event, record.source_id, record.boundary)
        ]
        if previous and record.previous != digest(previous[-1]):
            raise ValueError("adjudication correction parent missing")
        if not previous and record.previous is not None:
            raise ValueError("adjudication parent missing")
        self._adjudications[record.adjudication_id] = record
        self._record(
            "SEPARATE_ADJUDICATION_FIXTURE" if self.fixture else "HUMAN_ADJUDICATION", record
        )
        return digest(record)

    def readiness(self, *, now: int, permissions: tuple[Permission, ...] = ()) -> Readiness:
        integer(now)
        events = []
        verification = []
        for event, _role in self.batch.events:
            issues = []
            comparison = self.compare(event)
            completed = [
                a
                for a in self.assignments
                if a.event == event and a.assignment_id in self._completed
            ]
            if not completed:
                issues.append("NO_COMPLETE_REVIEW")
            principals = set()
            for a in completed:
                try:
                    p = next(
                        p for p in permissions if p.actor == a.reviewer_id and event in p.events
                    )
                    if p.reference != a.permission_reference:
                        raise PermissionError("assignment authorization reference changed")
                    principals.add(
                        self._access(p, a.reviewer_id, event, "COMPLETE", now, "REVIEWER")
                    )
                except (ValueError, PermissionError, StopIteration) as exc:
                    issues.append("REVIEWER_CURRENT_PERMISSION_OR_QUALIFICATION:" + str(exc))
            if comparison["required_second_review"] and len(principals) < 2:
                issues.append("INDEPENDENT_SECOND_REVIEW_REQUIRED")
            for d in comparison["disagreements"]:
                resolutions = [
                    r
                    for r in self._adjudications.values()
                    if r.event == event
                    and r.source_id == d["source_id"]
                    and r.boundary == d["boundary"]
                    and r.contributors == d["contributors"]
                ]
                if not resolutions or resolutions[-1].state != "HUMAN_RESOLVED":
                    issues.append("UNRESOLVED_DISAGREEMENT:" + d["source_id"] + ":" + d["boundary"])
                else:
                    resolution = resolutions[-1]
                    try:
                        p = next(
                            p
                            for p in permissions
                            if p.actor == resolution.adjudicator and event in p.events
                        )
                        principal = self._access(
                            p, resolution.adjudicator, event, "ADJUDICATE", now, "ADJUDICATOR"
                        )
                        if principal in principals:
                            raise PermissionError("adjudicator independence changed")
                        if not self.fixture:
                            self._verify_adjudication(resolution, principal, now)
                    except (ValueError, PermissionError, StopIteration) as exc:
                        issues.append("ADJUDICATION_CURRENT_EVIDENCE:" + str(exc))
            events.append((event, tuple(sorted(set(issues)))))
        if not self.fixture:
            checks = (
                "PROTOCOL_ADOPTION",
                "SCHEMA_ADOPTION",
                "BOUNDARY_ADOPTION",
                "CANONICAL_SCHEMA_ACCEPTANCE",
                "IMMUTABLE_HISTORY_ATTESTATION",
                "LINEAGE_VERIFICATION",
                "BATCH_SIGNOFF",
            )
            refs = dict(self.batch.approval_references)
            for kind in checks:
                try:
                    # History-sensitive evidence must bind the complete current batch/history.
                    self._verify(
                        kind,
                        {"batch": asdict(self.batch), "history": self.history},
                        refs.get(kind),
                        now,
                    )
                except (ValueError, PermissionError) as exc:
                    verification.append(kind + ":" + str(exc))
            for item in self.observations:
                try:
                    principal = self.roster[item.reviewer_id].principal(
                        event=next(
                            s.event for s in self.batch.sources if s.source_id == item.source_id
                        ),
                        role="REVIEWER",
                        now=now,
                        fixture=False,
                        verifier=self.verifier,
                    )
                    self._verify_statement(
                        "HUMAN_OBSERVATION", item, item.human_statement_reference, principal, now
                    )
                    if item.observation.boundary == "T2" and item.observation.state == "OBSERVABLE":
                        self._verify("PHYSICAL_ENTRY_LANDMARK", item, item.landmark_evidence, now)
                except (ValueError, PermissionError) as exc:
                    verification.append(item.observation_id + ":" + str(exc))
            for source in self.batch.sources:
                try:
                    self._verify("SOURCE_IDENTITY", source, source.verification_reference, now)
                except (ValueError, PermissionError) as exc:
                    verification.append(source.source_id + ":" + str(exc))
        reasons = [reason for _, issues in events for reason in issues] + verification
        if self.fixture:
            status = ReadinessStatus.CONSTRUCTED
            reasons.append("FIXTURE_NEVER_HUMAN_GROUND_TRUTH")
        elif any(issues for _, issues in events):
            status = ReadinessStatus.INCOMPLETE
        elif verification:
            status = ReadinessStatus.VERIFICATION
        else:
            status = ReadinessStatus.AUTHORIZATION
        return Readiness(
            status,
            digest(self.batch),
            digest(self.history),
            tuple(sorted(set(reasons))),
            tuple(events),
        )

    def occupancy_start(self, item: BoundaryObservation, *, now: int) -> tuple[int | None, str]:
        item.validate(self.batch)
        if item.observation.boundary != "T2":
            raise ValueError("T_OCC_START can only alias reconciled T2")
        if self.fixture or item.observation.state != "OBSERVABLE":
            return None, "PHYSICAL_ENTRY_DEFERRED_OR_CONSTRUCTED"
        self._verify("PHYSICAL_ENTRY_LANDMARK", item, item.landmark_evidence, now)
        self._verify(
            "BOUNDARY_ADOPTION",
            self.batch,
            dict(self.batch.approval_references).get("BOUNDARY_ADOPTION"),
            now,
        )
        return item.observation.value_us, "VERIFIED_PHYSICAL_T2_ALIAS"

    def validate_promotion_receipt(
        self,
        receipt: PromotionReceipt,
        permission: Permission,
        *,
        now: int,
        review_permissions: tuple[Permission, ...],
    ) -> Readiness:
        # Check current grant even for duplicates. Never issue a receipt here.
        permission.validate(
            actor=receipt.issuer,
            batch=digest(self.batch),
            event=self.batch.events[0][0],
            operation="PROMOTE_GT",
            now=now,
        )
        if set(permission.events) != set(dict(self.batch.events)):
            raise PermissionError("promotion must cover the exact complete batch")
        ready = self.readiness(now=now, permissions=review_permissions)
        if ready.status != ReadinessStatus.AUTHORIZATION:
            raise PermissionError("batch not promotion eligible: " + ";".join(ready.reasons))
        if (
            receipt.batch_digest != ready.batch_digest
            or receipt.history_digest != ready.history_digest
            or receipt.lineage_digest != self.batch.lineage_digest
            or receipt.object_digest
            != digest({"batch": asdict(self.batch), "history": self.history})
            or receipt.authorization_reference != permission.reference
        ):
            raise ValueError("promotion receipt complete-content binding mismatch")
        principal = self._verify("PROMOTION_AUTHORIZATION", permission, permission.reference, now)
        if (
            self._verify("PROMOTION_RECEIPT", receipt, receipt.verification_reference, now)
            != principal
        ):
            raise PermissionError("promotion issuer verification mismatch")
        text(receipt.receipt_id)
        prior = self._publications.get(receipt.receipt_id)
        if prior and prior != receipt:
            raise ValueError("duplicate promotion identity substitution")
        if self._publications and not prior:
            raise ValueError("batch already published; no duplicate receipt creation")
        self._publications[receipt.receipt_id] = receipt
        # Receipt validation does not mutate observation history or issue/publicize data.
        return Readiness(
            ReadinessStatus.PROMOTED,
            ready.batch_digest,
            ready.history_digest,
            (),
            ready.event_reasons,
            genuine_evidence_accepted=True,
        )

    def dashboard(self, *, now: int, permissions: tuple[Permission, ...] = ()) -> dict:
        if not self.fixture:
            raise PermissionError(
                "genuine dashboard requires authenticated blinding-aware view adapter"
            )
        return {
            "schema": self.batch.schema,
            "batch": asdict(self.batch),
            "assignments": [asdict(a) for a in self.assignments],
            "observations": [asdict(o) for o in self.observations],
            "adjudications": [asdict(a) for a in self._adjudications.values()],
            "comparisons": [self.compare(e) for e, _ in self.batch.events],
            "readiness": asdict(self.readiness(now=now, permissions=permissions)),
            "audit_history": self.history,
            "real_review_ui_enabled": False,
            "live_publisher_enabled": False,
        }
