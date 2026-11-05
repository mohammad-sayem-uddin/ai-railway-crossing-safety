"""Exact-operation readiness state machine. No opener, grant issuer or executor.

Unsigned documentary metadata and constructed predicates cannot authenticate
rights or human evidence. Genuine ports are absent in the shipped application.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from railway_detection.annotation.evidence_review.contracts import (
    EvidenceVerifier,
    digest,
    hex_digest,
    immutable,
    integer,
    text,
)
from railway_detection.application.contracts import closed_json

SCHEMA = "RESEARCH_PREFLIGHT/1"
FIXTURE = "CONSTRUCTED_PREFLIGHT_FIXTURE"
DOCUMENTARY = "UNVERIFIED_DOCUMENTARY_INPUT"
KINDS = (
    "SOURCE_IDENTITY",
    "RESOURCE_RIGHTS",
    "ACTOR_IDENTITY",
    "ROLE",
    "PURPOSE",
    "ENVIRONMENT",
    "PERMISSION_BASIS",
    "VALIDITY",
    "REVOCATION",
    "TECHNICAL",
    "HUMAN",
    "PROTOCOL",
    "DATA_SCHEMA",
    "PROVENANCE",
    "LOGGING",
    "OUTPUT",
)


class State(StrEnum):
    NOT_STARTED = "PREFLIGHT_NOT_STARTED"
    BLOCKED = "PREFLIGHT_BLOCKED"
    READY = "PREFLIGHT_READY_FOR_AUTHORIZATION_REVIEW"
    PENDING = "AUTHORIZATION_REVIEW_PENDING"
    AUTHORIZED = "AUTHORIZED_NOT_EXECUTED"
    PROHIBITED = "EXECUTION_NOT_PERMITTED"
    COMPLETED = "EXECUTION_COMPLETED_WITH_VALID_RECEIPT"


@dataclass(frozen=True)
class Request:
    request_id: str
    operation: str
    resource_id: str
    resource_identity: str
    actor: str | None
    role: str | None
    purpose: str | None
    environment: str | None
    protocol: str | None
    data_schema: str | None
    output_destination: str | None
    audit_log: str | None
    provenance_parents: tuple[str, ...]
    boundaries: tuple[str, ...] = ()
    landmark_kind: str | None = None
    acoustic_shift_us: int = 0
    classification: str = DOCUMENTARY
    schema: str = SCHEMA

    def validate(self):
        immutable(self)
        for value in (self.request_id, self.operation, self.resource_id):
            text(value)
        hex_digest(self.resource_identity)
        if self.schema != SCHEMA or self.classification not in (FIXTURE, DOCUMENTARY):
            raise ValueError("unsupported preflight schema/classification")
        if self.classification == FIXTURE and not self.resource_id.startswith("synthetic:"):
            raise ValueError("constructed input requires an explicit synthetic resource identity")
        if self.classification == DOCUMENTARY and (
            self.resource_id.startswith("synthetic:")
            or (self.actor is not None and self.actor.startswith("synthetic:"))
        ):
            raise ValueError("constructed resource/actor cannot become documentary genuine input")
        if type(self.acoustic_shift_us) is not int:
            raise ValueError("exact acoustic-offset metadata required")


@dataclass(frozen=True)
class Claim:
    kind: str
    reference: str
    request_digest: str
    valid_from: int
    expires: int
    revoked: bool
    facts_json: str
    classification: str


@dataclass(frozen=True)
class Issue:
    classification: str
    boundary: str
    reason: str


@dataclass(frozen=True)
class Readiness:
    state: State
    request_digest: str
    catalog_digest: str
    evaluated_at: int
    classification: str
    issues: tuple[Issue, ...]
    schema: str = SCHEMA
    execution_permitted: bool = False
    grant_issued: bool = False


@dataclass(frozen=True)
class ExternalReceipt:
    receipt_id: str
    request_digest: str
    catalog_digest: str
    authorization_digest: str | None
    valid_from: int
    expires: int
    revoked: bool
    canonical_schema_reference: str
    external_verification_reference: str
    classification: str


class PreflightEngine:
    def __init__(
        self,
        *,
        catalog_digest: str,
        decisions: tuple[tuple[str, str], ...],
        resources: tuple[tuple[str, str], ...],
        purposes: tuple[tuple[str, str], ...],
        parents: tuple[tuple[str, tuple[str, ...]], ...],
        verifier: EvidenceVerifier | None = None,
    ):
        hex_digest(catalog_digest)
        if (
            len(decisions) != 27
            or len(set(k for k, _ in decisions)) != 27
            or {k for k, _ in decisions} != {f"M19-PERM-{n:02}" for n in range(1, 28)}
            or any(v not in ("A", "B") for _, v in decisions)
            or sum(v == "A" for _, v in decisions) != 21
            or {k for k, v in decisions if v == "B"}
            != {f"M19-PERM-{n:02}" for n in (12, 13, 16, 18, 24, 25)}
        ):
            raise ValueError("exact preserved27-operation selection required")
        self.catalog_digest, self.decisions, self.verifier = catalog_digest, decisions, verifier
        if len(dict(resources)) != len(resources) or not resources:
            raise ValueError("independently retained unique resource identities required")
        for resource, identity in resources:
            text(resource)
            hex_digest(identity)
        self.resources = tuple(resources)
        if set(dict(purposes)) != set(dict(decisions)) or len(dict(purposes)) != len(purposes):
            raise ValueError("exact per-operation purpose bindings required")
        self.purposes = tuple(purposes)
        if len(dict(parents)) != len(parents) or set(dict(parents)) != set(dict(resources)):
            raise ValueError("complete independently retained provenance registry required")
        self.parents = tuple(parents)
        self._requests: dict[str, str] = {}
        self._authorizations: dict[str, ExternalReceipt] = {}
        self._executions: dict[str, str] = {}

    @staticmethod
    def initial_state() -> State:
        return State.NOT_STARTED

    def _claim(self, request: Request, claim: Claim, now: int) -> dict:
        immutable(claim)
        integer(claim.valid_from)
        integer(claim.expires)
        if (
            claim.kind not in KINDS
            or type(claim.revoked) is not bool
            or claim.revoked
            or not claim.valid_from <= now < claim.expires
        ):
            raise PermissionError("claim expired/revoked/invalid")
        if claim.request_digest != digest(request):
            raise PermissionError("claim resource/actor/operation/context binding mismatch")
        text(claim.reference)
        facts = closed_json(claim.facts_json)
        if type(facts) is not dict:
            raise ValueError("typed evidence fact object required")
        if request.classification == FIXTURE:
            if claim.classification != FIXTURE or not claim.reference.startswith("synthetic:"):
                raise PermissionError("constructed claims cannot change evidence class")
        else:
            if (
                claim.classification != DOCUMENTARY
                or self.verifier is None
                or claim.reference.startswith("synthetic:")
            ):
                raise PermissionError("genuine independently verified evidence unavailable")
            principal = self.verifier.verify(claim.kind, digest(claim), claim.reference, now)
            text(principal)
            if principal.startswith("synthetic:"):
                raise PermissionError("mock signer cannot verify real evidence")
            if (
                claim.kind in ("ACTOR_IDENTITY", "ROLE", "PERMISSION_BASIS")
                and principal != request.actor
            ):
                raise PermissionError("evidence signer is not the named operation actor")
        return facts

    def check(self, request: Request, claims: tuple[Claim, ...], *, now: int) -> Readiness:
        request.validate()
        integer(now)
        if request.operation not in dict(self.decisions):
            raise ValueError("explicit known operation required")
        if dict(self.decisions)[request.operation] == "B":
            return Readiness(
                State.PROHIBITED,
                digest(request),
                self.catalog_digest,
                now,
                request.classification,
                (Issue("DENIED_OR_DEFERRED", "OPERATION", "Existing B selection retained"),),
            )
        issues = []

        def missing(code, boundary, reason):
            issues.append(Issue(code, boundary, reason))

        if dict(self.resources).get(request.resource_id) != request.resource_identity:
            missing(
                "MISSING_RESOURCE_IDENTITY",
                "SOURCE_IDENTITY",
                "Resource differs from independently retained catalog identity",
            )
        if (
            request.purpose is not None
            and request.purpose != dict(self.purposes)[request.operation]
        ):
            missing(
                "UNKNOWN_REQUIRES_VERIFICATION",
                "PURPOSE",
                "Purpose differs from preserved exact-operation scope",
            )
        for name, code in (
            ("actor", "MISSING_ACTOR_OR_ROLE"),
            ("role", "MISSING_ACTOR_OR_ROLE"),
            ("purpose", "UNKNOWN_REQUIRES_VERIFICATION"),
            ("environment", "MISSING_TECHNICAL_PREREQUISITE"),
            ("protocol", "MISSING_TECHNICAL_PREREQUISITE"),
            ("data_schema", "MISSING_TECHNICAL_PREREQUISITE"),
            ("output_destination", "MISSING_TECHNICAL_PREREQUISITE"),
            ("audit_log", "MISSING_TECHNICAL_PREREQUISITE"),
        ):
            value = getattr(request, name)
            if type(value) is not str or not value.strip():
                missing(code, name.upper(), "Exact " + name + " absent")
        if (
            request.provenance_parents != dict(self.parents).get(request.resource_id)
            or not request.provenance_parents
            or len(set(request.provenance_parents)) != len(request.provenance_parents)
        ):
            missing(
                "MISSING_RESOURCE_IDENTITY",
                "PROVENANCE",
                "Exact unique provenance parents required",
            )
        if request.acoustic_shift_us != 0:
            missing("MISSING_HUMAN_EVIDENCE", "BOUNDARY", "Acoustic offsets never shift GT")
        if (
            set(request.boundaries) & {"T2", "T_OCC_START"}
            and request.landmark_kind != "PHYSICAL_ROADWAY_ENTRY"
        ):
            missing(
                "MISSING_HUMAN_EVIDENCE",
                "LANDMARK",
                "Physical entry deferred; lens-plane cannot substitute",
            )
        by_kind = {c.kind: c for c in claims}
        if len(by_kind) != len(claims) or not set(by_kind) <= set(KINDS):
            missing(
                "UNKNOWN_REQUIRES_VERIFICATION",
                "CLAIMS",
                "Duplicate/conflicting/unknown evidence kinds",
            )
        facts_by_kind = {}
        for kind in KINDS:
            if kind not in by_kind:
                missing(
                    {
                        "SOURCE_IDENTITY": "MISSING_RESOURCE_IDENTITY",
                        "RESOURCE_RIGHTS": "MISSING_RIGHTS_EVIDENCE",
                        "ACTOR_IDENTITY": "MISSING_ACTOR_OR_ROLE",
                        "ROLE": "MISSING_ACTOR_OR_ROLE",
                        "HUMAN": "MISSING_HUMAN_EVIDENCE",
                    }.get(kind, "MISSING_TECHNICAL_PREREQUISITE"),
                    kind,
                    "Evidence absent",
                )
                continue
            try:
                facts_by_kind[kind] = self._claim(request, by_kind[kind], now)
            except (ValueError, PermissionError, TypeError) as error:
                missing("UNKNOWN_REQUIRES_VERIFICATION", kind, str(error))
        for kind, facts in facts_by_kind.items():
            expectations: dict[str, dict] = {
                "SOURCE_IDENTITY": {
                    "resource_id": request.resource_id,
                    "identity": request.resource_identity,
                },
                "ACTOR_IDENTITY": {"actor": request.actor},
                "ROLE": {"role": request.role},
                "PURPOSE": {"purpose": request.purpose},
                "ENVIRONMENT": {"environment": request.environment},
                "PROTOCOL": {"protocol": request.protocol},
                "DATA_SCHEMA": {"schema": request.data_schema},
                "LOGGING": {"audit_log": request.audit_log},
                "OUTPUT": {"destination": request.output_destination},
                "PROVENANCE": {"parents": list(request.provenance_parents)},
            }
            expected = expectations.get(kind, {})
            if any(facts.get(k) != v for k, v in expected.items()) or not expected and not facts:
                missing(
                    "MISSING_TECHNICAL_PREREQUISITE", kind, "Evidence facts inconsistent/incomplete"
                )
        rights = facts_by_kind.get("RESOURCE_RIGHTS", {})
        if (
            not rights.get("owner_or_license_reference")
            or rights.get("operation") != request.operation
        ):
            missing(
                "MISSING_RIGHTS_EVIDENCE",
                "RESOURCE_RIGHTS",
                "Actual owner/license and exact operation rights required",
            )
        licenses = rights.get("conflicting_license_records", [])
        if (
            type(licenses) is not list
            or any(type(v) is not str for v in licenses)
            or len(set(licenses)) > 1
        ):
            missing(
                "MISSING_RIGHTS_EVIDENCE",
                "RESOURCE_RIGHTS",
                "Conflicting license records unresolved",
            )
        tech = facts_by_kind.get("TECHNICAL", {})
        if tech.get("prerequisites_complete") is not True:
            missing(
                "MISSING_TECHNICAL_PREREQUISITE",
                "TECHNICAL",
                "Required technical bindings incomplete",
            )
        external = tech.get("external_applicability")
        if external not in ("APPLICABLE_AND_EVIDENCED", "NOT_APPLICABLE_WITH_EVIDENCE"):
            missing(
                "MISSING_EXTERNAL_APPROVAL"
                if external == "APPLICABLE_PENDING_EVIDENCE"
                else "UNKNOWN_REQUIRES_VERIFICATION",
                "EXTERNAL",
                "Actual scoped applicability/evidence required; no universal approval assumed",
            )
        human = facts_by_kind.get("HUMAN", {})
        review_required = request.operation in {
            f"M19-PERM-{n:02}" for n in (15, 19, 20, 21, 26, 27)
        }
        if (
            human.get("qualified") is not True
            or review_required
            and (
                human.get("independent") is not True or human.get("conflicts_resolved") is not True
            )
        ):
            missing(
                "MISSING_HUMAN_EVIDENCE",
                "HUMAN",
                "Qualification/independence/conflict/batch evidence incomplete",
            )
        if (
            request.operation in ("M19-PERM-15", "M19-PERM-21")
            and human.get("batch_complete") is not True
        ):
            missing(
                "MISSING_HUMAN_EVIDENCE",
                "HUMAN",
                "Complete actual GT batch required for evaluation/promotion",
            )
        if request.operation == "M19-PERM-20" and human.get("review_parents_complete") is not True:
            missing(
                "MISSING_HUMAN_EVIDENCE",
                "HUMAN",
                "Exact independent review parents required for adjudication",
            )
        if (
            request.classification != FIXTURE
            and human.get("classification") != "GENUINE_VERIFIED_BY_EXTERNAL_SERVICE"
        ):
            missing(
                "MISSING_HUMAN_EVIDENCE",
                "HUMAN",
                "Constructed review cannot satisfy genuine evidence",
            )
        if (
            set(request.boundaries) & {"T2", "T_OCC_START"}
            and human.get("physical_landmark_verified") is not True
        ):
            missing("MISSING_HUMAN_EVIDENCE", "LANDMARK", "Physical landmark evidence absent")
        canonical_timing_required = (
            request.operation in ("M19-PERM-15", "M19-PERM-21")
            or request.data_schema == "8.1.0-stage2.1"
        )
        if (
            canonical_timing_required
            and facts_by_kind.get("DATA_SCHEMA", {}).get("duration_compatibility")
            != "CANONICAL_SCHEMA_TIMING_COMPATIBLE"
        ) or (
            not canonical_timing_required
            and facts_by_kind.get("DATA_SCHEMA", {}).get("duration_compatibility")
            not in ("CANONICAL_SCHEMA_TIMING_COMPATIBLE", "NOT_APPLICABLE_NO_REVIEW_RECORD")
        ):
            missing(
                "MISSING_TECHNICAL_PREREQUISITE",
                "DURATION_SCHEMA",
                "Canonical duration/schema compatibility absent",
            )
        for kind in ("PERMISSION_BASIS", "VALIDITY", "REVOCATION"):
            facts = facts_by_kind.get(kind, {})
            if (
                facts.get("operation") != request.operation
                or facts.get("resource_identity") != request.resource_identity
                or facts.get("current") is not True
            ):
                missing(
                    "UNKNOWN_REQUIRES_VERIFICATION",
                    kind,
                    "Current exact-operation basis/state absent",
                )
        return Readiness(
            State.BLOCKED if issues else State.READY,
            digest(request),
            self.catalog_digest,
            now,
            request.classification,
            tuple(issues),
        )

    def _fresh(self, request: Request, readiness: Readiness, claims: tuple[Claim, ...], now: int):
        current = self.check(request, claims, now=now)
        if readiness != current or current.state != State.READY:
            raise PermissionError(
                "stale/incomplete/substituted readiness; recheck current prerequisites"
            )

    def submit_authorization_review(
        self, request: Request, readiness: Readiness, claims: tuple[Claim, ...], *, now: int
    ) -> State:
        self._fresh(request, readiness, claims, now)
        binding = digest(request)
        previous = self._requests.get(request.request_id)
        if previous and previous != binding:
            raise ValueError("duplicate authorization request substitution")
        self._requests[request.request_id] = binding
        return State.PENDING

    def _external(self, request: Request, receipt: ExternalReceipt, kind: str, now: int):
        immutable(receipt)
        integer(receipt.valid_from)
        integer(receipt.expires)
        if (
            request.classification == FIXTURE
            or receipt.classification != DOCUMENTARY
            or self.verifier is None
        ):
            raise PermissionError("constructed preflight never becomes genuine authority/execution")
        if (
            receipt.revoked is not False
            or not receipt.valid_from <= now < receipt.expires
            or receipt.request_digest != digest(request)
            or receipt.catalog_digest != self.catalog_digest
        ):
            raise PermissionError("external receipt expired/revoked/substituted")
        text(receipt.canonical_schema_reference)
        text(receipt.external_verification_reference)
        signer = self.verifier.verify(
            kind, digest(receipt), receipt.external_verification_reference, now
        )
        text(signer)
        if signer.startswith("synthetic:"):
            raise PermissionError("mock external receipt")

    def record_authorization(
        self,
        request: Request,
        readiness: Readiness,
        claims: tuple[Claim, ...],
        receipt: ExternalReceipt,
        *,
        now: int,
    ) -> State:
        self._fresh(request, readiness, claims, now)
        if (
            self._requests.get(request.request_id) != digest(request)
            or receipt.authorization_digest is not None
        ):
            raise PermissionError("exact pending authorization review required")
        self._external(request, receipt, "EXISTING_CANONICAL_OPERATION_AUTHORIZATION", now)
        old = self._authorizations.get(request.request_id)
        if old and old != receipt:
            raise ValueError("authorization receipt substitution")
        self._authorizations[request.request_id] = receipt
        return State.AUTHORIZED

    def record_execution(self, request: Request, receipt: ExternalReceipt, *, now: int) -> State:
        integer(now)
        self._external(request, receipt, "EXISTING_OPERATION_EXECUTION_RECEIPT", now)
        authorization = self._authorizations.get(request.request_id)
        if (
            self._requests.get(request.request_id) != digest(request)
            or dict(self.decisions).get(request.operation) != "A"
            or authorization is None
            or receipt.authorization_digest != digest(authorization)
        ):
            raise PermissionError("execution receipt missing exact request/authorization parent")
        self._external(request, authorization, "EXISTING_CANONICAL_OPERATION_AUTHORIZATION", now)
        old = self._executions.get(request.request_id)
        if old and old != digest(receipt):
            raise ValueError("execution receipt substitution")
        self._executions[request.request_id] = digest(receipt)
        return State.COMPLETED

    @staticmethod
    def require_execution():
        raise PermissionError(
            "EXECUTION_NOT_PERMITTED: metadata preflight has no executor; "
            "use separately authorized guarded service"
        )


def duration_compatibility(
    *, reviewer_id: str, session_id: str, start: str, end: str, tool: str
) -> dict:
    """Use active schema unchanged. This never builds a review/GT record or touches media."""
    from railway_detection.annotation.stage2_1_schema import (
        STAGE_2_1_SCHEMA_VERSION,
        ReviewerMetadata,
        SchemaValidationError,
    )

    try:
        value = ReviewerMetadata(reviewer_id, session_id, start, end, tool)
    except (SchemaValidationError, ValueError, TypeError) as error:
        return {
            "status": "INCOMPATIBLE_DURATION_SCHEMA",
            "reason": str(error),
            "genuine_review_proven": False,
            "schema": STAGE_2_1_SCHEMA_VERSION,
        }
    return {
        "status": "CANONICAL_SCHEMA_TIMING_COMPATIBLE",
        "duration_seconds_derived": str(value.review_duration_s),
        "schema": STAGE_2_1_SCHEMA_VERSION,
        "genuine_review_proven": False,
        "scientific_duration_floor": "DEFERRED",
        "record_created": False,
    }
