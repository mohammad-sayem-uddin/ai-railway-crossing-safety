"""Document-reference intake with append-only lineage; no resource opener or grant issuer.

A retained head detects local history substitution. SQLite is cooperative storage,
not independently protected authority. Genuine attestation adapters do not ship.
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import date
from enum import StrEnum
from typing import Protocol

from railway_detection.annotation.evidence_review.contracts import (
    canonical,
    digest,
    hex_digest,
    immutable,
    integer,
    text,
)
from railway_detection.application.contracts import closed_json

SCHEMA = "DOCUMENTARY_EVIDENCE/1"
DOCUMENTARY = "UNVERIFIED_DOCUMENTARY_INPUT"
CONSTRUCTED = "CONSTRUCTED_DOCUMENTARY_FIXTURE"
EMPTY_HEAD = "0" * 64
KINDS = (
    "SOURCE_IDENTITY",
    "RIGHTS",
    "APPOINTMENT",
    "QUALIFICATION",
    "INDEPENDENCE",
    "PARTICIPATION",
    "EXTERNAL_DETERMINATION",
    "PROTOCOL_ADOPTION",
    "LANDMARK",
    "REVOCATION",
)
RIGHTS = (
    "RESEARCH_USE",
    "INTERNAL_STORAGE",
    "PROCESSING",
    "ANNOTATION",
    "TRAINING",
    "EVALUATION",
    "DERIVED_RESULTS_PUBLICATION",
    "DEIDENTIFIED_METADATA_SHARE",
    "ORIGINAL_REDISTRIBUTION",
    "PUBLIC_DATASET_RELEASE",
)


class Status(StrEnum):
    SUBMITTED = "SUBMITTED"
    PARSED = "PARSED"
    VALID = "STRUCTURALLY_VALID"
    ATTRIBUTABLE = "ATTRIBUTABLE"
    VERIFIED = "INDEPENDENTLY_VERIFIED"
    ACCEPTED = "ACCEPTED_FOR_SPECIFIC_PURPOSE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Scope:
    resource: str
    operation: str | None
    actor: str | None
    role: str | None
    purpose: str | None
    environment: str | None
    rights: tuple[str, ...] = ()

    def validate(self, *, complete: bool = False):
        immutable(self)
        text(self.resource)
        for value in (self.operation, self.actor, self.role, self.purpose, self.environment):
            if value is not None:
                text(value)
            elif complete:
                raise ValueError("complete exact-operation evidence scope required")
        if self.operation is not None and self.operation not in {
            f"M19-PERM-{n:02}" for n in range(1, 28)
        }:
            raise ValueError("exact known operation required")
        if len(set(self.rights)) != len(self.rights) or not set(self.rights) <= set(RIGHTS):
            raise ValueError("explicit unique rights dimensions required")


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    evidence_type: str
    subject: str
    source_reference: str
    issuing_authority: str | None
    scope: Scope
    documented_date: str | None = None
    valid_from: int | None = None
    expires: int | None = None
    expiry_not_applicable: bool = False
    parent_reference: str | None = None
    supersedes_reference: str | None = None
    revokes_reference: str | None = None
    unresolved_conflicts: tuple[str, ...] = ()
    classification: str = DOCUMENTARY
    schema: str = SCHEMA

    def validate(self):
        immutable(self)
        if type(self.scope) is not Scope or self.schema != SCHEMA:
            raise ValueError("typed evidence scope/known schema required")
        for value in (self.evidence_id, self.subject, self.source_reference):
            text(value)
        if self.evidence_type not in KINDS or self.classification not in (DOCUMENTARY, CONSTRUCTED):
            raise ValueError(
                "documentary evidence only; observations/signatures cannot be generated"
            )
        if self.issuing_authority is not None:
            text(self.issuing_authority)
        self.scope.validate()
        if self.documented_date is not None:
            date.fromisoformat(self.documented_date)
        if type(self.expiry_not_applicable) is not bool:
            raise ValueError("explicit expiry-applicability boolean required")
        if self.expiry_not_applicable and self.expires is not None:
            raise ValueError("conflicting expiry and no-fixed-expiry declaration")
        for clock in (self.valid_from, self.expires):
            if clock is not None:
                integer(clock)
        if self.valid_from is not None and self.expires is not None:
            if self.expires <= self.valid_from:
                raise ValueError("positive evidence validity interval required")
        for parent in (self.parent_reference, self.supersedes_reference, self.revokes_reference):
            if parent is not None:
                hex_digest(parent)
        for conflict in self.unresolved_conflicts:
            text(conflict)
        if self.revokes_reference is not None and self.evidence_type != "REVOCATION":
            raise ValueError("revocation requires explicit revocation evidence type")
        if self.classification == CONSTRUCTED:
            if not self.evidence_id.startswith("synthetic:"):
                raise ValueError("fixtures require synthetic evidence IDs")
        elif any(
            v is not None and v.startswith("synthetic:")
            for v in (
                self.evidence_id,
                self.subject,
                self.source_reference,
                self.issuing_authority,
                self.scope.resource,
                self.scope.actor,
            )
        ):
            raise ValueError("constructed evidence cannot be relabeled genuine")


def parse_evidence(body: str) -> Evidence:
    """Closed, duplicate-key rejecting parse. No reference is dereferenced."""
    if type(body) is not str or len(body.encode()) > 64 * 1024:
        raise ValueError("bounded UTF-8 evidence metadata required")
    value = closed_json(body)
    if type(value) is not dict or type(value.get("scope")) is not dict:
        raise ValueError("typed documentary object and scope required")
    scope = dict(value.pop("scope"))
    if type(scope.get("rights", [])) is not list:
        raise ValueError("rights array required")
    scope["rights"] = tuple(scope.get("rights", []))
    if type(value.get("unresolved_conflicts", [])) is not list:
        raise ValueError("conflicts array required")
    value["unresolved_conflicts"] = tuple(value.get("unresolved_conflicts", []))
    evidence = Evidence(scope=Scope(**scope), **value)
    evidence.validate()
    return evidence


@dataclass(frozen=True)
class Attestation:
    evidence_digest: str
    stage: str
    scope_digest: str
    issuer: str
    verifier_principal: str
    verification_reference: str
    valid_from: int
    expires: int
    revoked: bool
    classification: str


class DocumentaryVerifier(Protocol):
    """Trusted deployment service; authenticate originals/issuer/delegation independently.

    Bind exact evidence, scope and stage, check conflict resolutions and current
    validity/revocation, and return canonical physical verifier identity. A caller
    JSON assertion cannot implement this service. No genuine adapter ships.
    """

    def inspect(self, item: Evidence, stage: Status, now: int) -> Attestation: ...


NEXT = {
    Status.SUBMITTED: Status.PARSED,
    Status.PARSED: Status.VALID,
    Status.VALID: Status.ATTRIBUTABLE,
    Status.ATTRIBUTABLE: Status.VERIFIED,
    Status.VERIFIED: Status.ACCEPTED,
}
ATTESTED = {Status.ATTRIBUTABLE, Status.VERIFIED, Status.ACCEPTED}


class DocumentaryJournal:
    """Caller supplies connection and independently retained expected head per call.

    This ledger never supplies human observations, changes Mission26 decisions,
    authorizes access, or replaces WP04/WP03 transaction and point-of-use guards.
    """

    def __init__(self, connection: sqlite3.Connection, *, constructed: bool = False):
        if type(constructed) is not bool:
            raise ValueError("explicit fixture-mode boolean required")
        if connection.in_transaction:
            raise ValueError(
                "dedicated documentary connection required; owner transaction is active"
            )
        self.db = connection
        self.constructed = constructed
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS documentary_log "
            "(seq INTEGER PRIMARY KEY, request TEXT UNIQUE NOT NULL, "
            "body TEXT NOT NULL, previous TEXT NOT NULL, head TEXT NOT NULL)"
        )
        self.db.commit()

    def _history(self, expected_head: str) -> tuple[list[dict], dict[str, dict]]:
        hex_digest(expected_head)
        previous = EMPTY_HEAD
        history: list[dict] = []
        records: dict[str, dict] = {}
        evidence_digests: dict[str, str] = {}
        for n, (seq, request, body, parent, head) in enumerate(
            self.db.execute(
                "SELECT seq,request,body,previous,head FROM documentary_log ORDER BY seq"
            ),
            1,
        ):
            command = closed_json(body)
            if (
                seq != n
                or parent != previous
                or head
                != digest({"seq": seq, "request": request, "body": body, "previous": parent})
            ):
                raise ValueError("evidence audit lineage altered")
            if command["kind"] == "SUBMIT":
                item = parse_evidence(canonical(command["evidence"]))
                key = item.evidence_id
                if key in records or (item.classification == CONSTRUCTED) != self.constructed:
                    raise ValueError("duplicate identity or substituted evidence classification")
                for ref in (
                    item.parent_reference,
                    item.supersedes_reference,
                    item.revokes_reference,
                ):
                    if ref is not None and ref not in evidence_digests:
                        raise ValueError("missing/altered evidence parent")
                for ref in (item.supersedes_reference, item.revokes_reference):
                    if ref is not None:
                        other = records[evidence_digests[ref]]["item"]
                        if other.subject != item.subject or other.scope != item.scope:
                            raise ValueError("cross-subject/scope lineage substitution")
                records[key] = {"item": item, "status": Status.SUBMITTED, "attestation": None}
                evidence_digests[digest(item)] = key
            elif command["kind"] == "TRANSITION":
                key = command["evidence_id"]
                state = records[key]
                if command["evidence_digest"] != digest(state["item"]):
                    raise ValueError("altered transition evidence binding")
                target = Status(command["target"])
                self._allowed(state["status"], target)
                if target in ATTESTED and command["attestation"] is None:
                    raise ValueError("missing historical verification receipt")
                state["status"] = target
                state["attestation"] = command["attestation"]
                if target == Status.ACCEPTED and state["item"].revokes_reference:
                    revoked_id = evidence_digests[state["item"].revokes_reference]
                    records[revoked_id]["status"] = Status.REVOKED
            else:
                raise ValueError("unknown evidence audit command")
            history.append({"seq": seq, "request": request, "command": command, "head": head})
            previous = head
        if previous != expected_head:
            raise ValueError("retained evidence audit head mismatch; history truncated/substituted")
        return history, records

    @staticmethod
    def _allowed(current: Status, target: Status):
        if current in (Status.REVOKED, Status.REJECTED, Status.EXPIRED):
            raise ValueError("terminal evidence status; submit a new linked evidence item")
        if target not in (Status.REVOKED, Status.REJECTED, Status.EXPIRED):
            if NEXT.get(current) != target:
                raise ValueError("evidence stages cannot be skipped or inferred")

    def _append(self, request: str, command: dict, expected_head: str) -> str:
        # Caller holds BEGIN IMMEDIATE through validation and commit.
        body = canonical(command)
        prior = self.db.execute(
            "SELECT body,head FROM documentary_log WHERE request=?", (request,)
        ).fetchone()
        if prior:
            if prior[0] != body:
                raise ValueError("request identity substitution")
            return prior[1]
        seq = self.db.execute("SELECT count(*) FROM documentary_log").fetchone()[0] + 1
        head = digest({"seq": seq, "request": request, "body": body, "previous": expected_head})
        self.db.execute(
            "INSERT INTO documentary_log VALUES(?,?,?,?,?)",
            (seq, request, body, expected_head, head),
        )
        return head

    def submit(self, item: Evidence, *, request: str, expected_head: str) -> str:
        item.validate()
        text(request)
        if (item.classification == CONSTRUCTED) != self.constructed:
            raise PermissionError("constructed/genuine ledger separation required")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            _, records = self._history(expected_head)
            command = {"kind": "SUBMIT", "evidence": asdict(item)}
            prior = self.db.execute(
                "SELECT body,head FROM documentary_log WHERE request=?", (request,)
            ).fetchone()
            if prior:
                if prior[0] != canonical(command):
                    raise ValueError("duplicate request substitution")
                self.db.commit()
                return prior[1]
            if item.evidence_id in records:
                raise ValueError("duplicate evidence ID; corrections need a new linked ID")
            head = self._append(request, command, expected_head)
            self._history(head)  # Enforce existing parent/subject/scope before commit.
            self.db.commit()
            return head
        except BaseException:
            self.db.rollback()
            raise

    def _attest(
        self,
        item: Evidence,
        target: Status,
        now: int,
        verifier: DocumentaryVerifier | None,
    ) -> Attestation:
        if verifier is None:
            raise PermissionError("independent documentary verifier adapter unavailable")
        if not item.issuing_authority or item.unresolved_conflicts:
            raise PermissionError("missing issuer or unresolved conflicting evidence")
        item.scope.validate(complete=True)
        if item.evidence_type == "RIGHTS" and not item.scope.rights:
            raise PermissionError("rights evidence needs explicit purpose-specific dimensions")
        if item.expires is None and not item.expiry_not_applicable:
            raise PermissionError("unknown expiry cannot become permission")
        if item.valid_from is None and not item.expiry_not_applicable:
            raise PermissionError("unknown validity cannot become permission")
        if (item.valid_from is not None and now < item.valid_from) or (
            item.expires is not None and now >= item.expires
        ):
            raise PermissionError("evidence expired/not yet valid")
        a = verifier.inspect(item, target, now)
        immutable(a)
        if type(a) is not Attestation:
            raise PermissionError("typed independently verified attestation required")
        for clock in (a.valid_from, a.expires):
            integer(clock)
        for value in (a.issuer, a.verifier_principal, a.verification_reference):
            text(value)
        if (
            a.evidence_digest != digest(item)
            or a.scope_digest != digest(item.scope)
            or a.stage != target
            or a.issuer != item.issuing_authority
            or a.classification != item.classification
            or type(a.revoked) is not bool
            or a.revoked
            or not a.valid_from <= now < a.expires
            or a.verifier_principal in (item.issuing_authority, item.scope.actor, item.subject)
        ):
            raise PermissionError(
                "unverified, dependent, expired, revoked or substituted attestation"
            )
        if self.constructed:
            if not a.verifier_principal.startswith("synthetic:"):
                raise PermissionError("fixture verifier must remain constructed")
        elif any(
            v.startswith("synthetic:")
            for v in (
                a.issuer,
                a.verifier_principal,
                a.verification_reference,
            )
        ):
            raise PermissionError("constructed verifier cannot verify genuine evidence")
        return a

    def transition(
        self,
        evidence_id: str,
        target: Status,
        *,
        request: str,
        expected_head: str,
        now: int,
        reason: str,
        verifier: DocumentaryVerifier | None = None,
    ) -> str:
        text(request)
        text(reason)
        integer(now)
        if not isinstance(target, Status):
            raise ValueError("typed evidence stage required")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            _, records = self._history(expected_head)
            state = records[evidence_id]
            item = state["item"]
            # Exact retries retrieve a historical result without new verification/use.
            prior = self.db.execute(
                "SELECT body,head FROM documentary_log WHERE request=?", (request,)
            ).fetchone()
            if prior:
                old = closed_json(prior[0])
                if any(
                    old.get(k) != v
                    for k, v in {
                        "kind": "TRANSITION",
                        "evidence_id": evidence_id,
                        "target": target,
                        "now": now,
                        "reason": reason,
                        "evidence_digest": digest(item),
                    }.items()
                ):
                    raise ValueError("duplicate transition request substitution")
                self.db.commit()
                return prior[1]
            self._allowed(state["status"], target)
            if target == Status.EXPIRED:
                deadlines = [
                    value
                    for value in (item.expires, (state["attestation"] or {}).get("expires"))
                    if value is not None
                ]
                if not deadlines or now < min(deadlines):
                    raise ValueError("expiry cannot be inferred from missing dates")
            a = self._attest(item, target, now, verifier) if target in ATTESTED else None
            head = self._append(
                request,
                {
                    "kind": "TRANSITION",
                    "evidence_id": evidence_id,
                    "target": target,
                    "now": now,
                    "reason": reason,
                    "evidence_digest": digest(item),
                    "attestation": asdict(a) if a else None,
                },
                expected_head,
            )
            self._history(head)
            self.db.commit()
            return head
        except BaseException:
            self.db.rollback()
            raise

    def snapshot(self, *, expected_head: str, now: int) -> dict:
        integer(now)
        history, records = self._history(expected_head)
        rows = []
        for key, state in sorted(records.items()):
            item = state["item"]
            status = state["status"]
            attestation = state["attestation"]
            if status not in (Status.REVOKED, Status.REJECTED) and (
                (item.expires is not None and now >= item.expires)
                or (attestation is not None and now >= attestation["expires"])
            ):
                status = Status.EXPIRED
            rows.append(
                {
                    "evidence_id": key,
                    "item": asdict(item),
                    "recorded_status": state["status"],
                    "effective_status": status,
                    "attestation": state["attestation"],
                    "current_acceptance_reverification_required": True,
                    "currently_usable_for_operation": False,
                    "genuine_permission": False,
                    "human_observation": False,
                }
            )
        return {
            "schema": SCHEMA,
            "head": expected_head,
            "evaluated_at": now,
            "classification": CONSTRUCTED if self.constructed else DOCUMENTARY,
            "evidence": rows,
            "audit_history": history,
            "new_grants": 0,
            "authorized_operations": [],
            "executed_operations": [],
            "human_review_ready": False,
        }

    def accepted_for(
        self,
        evidence_id: str,
        scope: Scope,
        *,
        expected_head: str,
        now: int,
        verifier: DocumentaryVerifier | None = None,
    ) -> bool:
        integer(now)
        _, records = self._history(expected_head)
        state = records[evidence_id]
        if self.constructed or state["status"] != Status.ACCEPTED or scope != state["item"].scope:
            raise PermissionError("no current genuine exact-purpose acceptance")
        for other in records.values():
            if other["item"].supersedes_reference == digest(state["item"]):
                raise PermissionError("superseded evidence requires new verification")
            if other["item"].revokes_reference == digest(state["item"]):
                raise PermissionError("revocation evidence requires independent disposition")
        parent = state["item"].parent_reference
        if parent is not None:
            parents = [v["item"] for v in records.values() if digest(v["item"]) == parent]
            if len(parents) != 1:
                raise PermissionError("exact evidence parent unavailable")
            self.accepted_for(
                parents[0].evidence_id,
                parents[0].scope,
                expected_head=expected_head,
                now=now,
                verifier=verifier,
            )
        self._attest(state["item"], Status.ACCEPTED, now, verifier)
        return True  # Documentary acceptance only; canonical operation grant still required.
