"""Immutable intake contracts. References describe evidence; they do not verify it."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, fields, is_dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Protocol

from railway_detection.annotation.human_review_domain import Observation
from railway_detection.safety.constructed_authority import canonical as strict_canonical
from railway_detection.safety.constructed_authority import sha

SCHEMA = "REVIEW_GOVERNANCE/1"
FIXTURE = "CONSTRUCTED_REVIEW_FIXTURE"
CANDIDATE = "UNVERIFIED_EXTERNAL_INPUT"
RISKS = (
    "EXPLICIT_REVIEWER_FLAG",
    "UNCERTAIN_BOUNDARY",
    "ENGINE_T3_T4_INTERPRETATION",
    "FRONT_BACK_CONFLICT",
    "MEDIA_HASH_MISSING_OR_INCONSISTENT",
    "CORRECTED_FROM_CANDIDATE",
)
CANDIDATE_EVENTS = tuple(
    [f"train_events/event_{n:03}" for n in range(1, 24)]
    + [f"no_train_events/event_{n:03}" for n in range(1, 4)]
    + ["engine_events/event_001"]
)
R04_EVENTS = tuple(f"train_events/event_{n:03}" for n in (1, 2, 5, 6, 7, 9, 11, 12, 13, 14, 17))


class ReviewerStatus(StrEnum):
    MOCK = "MOCK_REVIEWER_FIXTURE"
    UNVERIFIED = "UNVERIFIED_REVIEWER"
    PENDING = "QUALIFICATION_EVIDENCE_PENDING"
    VERIFIED = "VERIFIED_REVIEWER"


class ReadinessStatus(StrEnum):
    CONSTRUCTED = "CONSTRUCTED_NON_PROMOTABLE"
    INCOMPLETE = "INCOMPLETE_REVIEW_BATCH"
    VERIFICATION = "REVIEW_COMPLETE_PENDING_VERIFICATION"
    AUTHORIZATION = "PROMOTION_ELIGIBLE_PENDING_AUTHORIZATION"
    PROMOTED = "PROMOTED_WITH_VALID_RECEIPT"


def canonical(value: object) -> str:
    def normalize(item):
        if isinstance(item, StrEnum):
            return item.value
        if isinstance(item, (list, tuple)):
            return [normalize(v) for v in item]
        if type(item) is dict:
            return {k: normalize(v) for k, v in item.items()}
        return item

    return strict_canonical(normalize(value))


def text(value: str) -> None:
    if type(value) is not str or not value.strip() or len(value) > 4096:
        raise ValueError("bounded nonempty reference/reason required")


def integer(value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError("exact nonnegative integer required")


def digest(value: object) -> str:
    return sha(
        canonical(asdict(value) if is_dataclass(value) and not isinstance(value, type) else value)
    )


def immutable(value: object) -> None:
    if type(value) is str:
        strict_canonical(value)
    elif is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            immutable(getattr(value, field.name))
    elif type(value) is tuple:
        for item in value:
            immutable(item)
    elif (
        value is not None and type(value) not in (str, int, bool) and not isinstance(value, StrEnum)
    ):
        raise ValueError("deep immutable metadata required; lists/maps/floats are not contracts")


def hex_digest(value: str) -> None:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("exact metadata SHA256 required; never read a source to invent it")


class EvidenceVerifier(Protocol):
    """Deployment-owned authenticated evidence service, never a user JSON flag.

    Must raise on invalid/revoked/expired evidence and verify subject digest,
    kind, principal, context and time at point of use. Return canonical physical
    principal identity for identity/independence checks. No implementation ships.
    """

    def verify(self, kind: str, subject_digest: str, reference: str, now: int) -> str: ...


@dataclass(frozen=True)
class Qualification:
    reference: str
    roles: tuple[str, ...]
    events: tuple[str, ...]
    valid_from: int
    expires: int
    verification_reference: str | None = None

    def validate(self, now: int, role: str, event: str) -> None:
        text(self.reference)
        integer(self.valid_from)
        integer(self.expires)
        integer(now)
        if not self.valid_from <= now < self.expires:
            raise ValueError("qualification missing/expired/not yet valid")
        if role not in self.roles or event not in self.events:
            raise ValueError("qualification outside role/event scope")


@dataclass(frozen=True)
class Reviewer:
    reviewer_id: str
    principal_reference: str
    status: ReviewerStatus
    qualification: Qualification | None
    identity_evidence: str | None
    conflicts: tuple[str, ...]
    independence_reference: str | None
    consent_reference: str | None

    def principal(
        self, *, event: str, role: str, now: int, fixture: bool, verifier: EvidenceVerifier | None
    ) -> str:
        immutable(self)
        text(self.reviewer_id)
        text(self.principal_reference)
        if not isinstance(self.status, ReviewerStatus):
            raise ValueError("typed reviewer status required; no automatic upgrade")
        if self.qualification is None:
            raise ValueError("qualification evidence missing")
        self.qualification.validate(now, role, event)
        if event in self.conflicts or self.independence_reference is None:
            raise ValueError("conflict or missing independence declaration")
        if self.consent_reference is None:
            raise ValueError("review procedure/participation consent evidence missing")
        if fixture:
            if self.status != ReviewerStatus.MOCK or not self.reviewer_id.startswith("synthetic:"):
                raise ValueError("constructed roster must remain MOCK_REVIEWER_FIXTURE")
            return self.principal_reference
        if any(
            v.startswith("synthetic:")
            for v in (self.reviewer_id, self.principal_reference, self.qualification.reference)
        ):
            raise PermissionError("constructed identity/qualification cannot become genuine")
        if self.status != ReviewerStatus.VERIFIED or verifier is None:
            raise PermissionError("genuine reviewer verification adapter/evidence unavailable")
        if not self.identity_evidence or not self.qualification.verification_reference:
            raise PermissionError("identity and authorized qualification verification required")
        principal = verifier.verify("REVIEWER_IDENTITY", digest(self), self.identity_evidence, now)
        for kind, ref in (
            ("QUALIFICATION", self.qualification.verification_reference),
            ("INDEPENDENCE", self.independence_reference),
            ("PARTICIPATION", self.consent_reference),
        ):
            if verifier.verify(kind, digest(self), ref, now) != principal:
                raise PermissionError("reviewer evidence principal mismatch")
        return principal


@dataclass(frozen=True)
class Permission:
    reference: str
    actor: str
    batch_digest: str
    events: tuple[str, ...]
    operations: tuple[str, ...]
    environment: str
    purpose: str
    valid_from: int
    expires: int
    revoked: bool = False

    def validate(self, *, actor: str, batch: str, event: str, operation: str, now: int) -> None:
        immutable(self)
        for v in (self.reference, self.actor, self.environment, self.purpose):
            text(v)
        for clock in (now, self.valid_from, self.expires):
            integer(clock)
        if type(self.revoked) is not bool or self.revoked:
            raise PermissionError("authorization revoked/invalid")
        if not self.valid_from <= now < self.expires:
            raise PermissionError("authorization expired/not yet valid")
        if (
            self.actor != actor
            or self.batch_digest != batch
            or event not in self.events
            or operation not in self.operations
        ):
            raise PermissionError("authorization actor/batch/event/operation scope mismatch")


@dataclass(frozen=True)
class Source:
    source_id: str
    event: str
    camera: str
    content_digest: str
    manifest_reference: str
    origin_us: int
    timebase: tuple[int, int]
    end_us: int
    verification_reference: str | None = None

    def validate(self) -> None:
        for v in (self.source_id, self.event, self.manifest_reference):
            text(v)
        hex_digest(self.content_digest)
        integer(self.origin_us)
        integer(self.end_us)
        if self.camera not in ("front", "back") or self.end_us < self.origin_us:
            raise ValueError("source camera/clock range invalid")
        if (
            type(self.timebase) is not tuple
            or len(self.timebase) != 2
            or any(type(v) is not int or v <= 0 for v in self.timebase)
        ):
            raise ValueError("exact positive source timebase required")


@dataclass(frozen=True)
class Batch:
    batch_id: str
    protocol_reference: str
    manifest_reference: str
    schema_reference: str
    boundary_version: str
    events: tuple[tuple[str, str], ...]
    sources: tuple[Source, ...]
    boundaries: tuple[str, ...]
    creation_reference: str
    classification: str
    lineage_digest: str
    approval_references: tuple[tuple[str, str], ...] = ()
    schema: str = SCHEMA

    def validate(self) -> None:
        immutable(self)
        for v in (
            self.batch_id,
            self.protocol_reference,
            self.manifest_reference,
            self.schema_reference,
            self.boundary_version,
            self.creation_reference,
        ):
            text(v)
        hex_digest(self.lineage_digest)
        if self.schema != SCHEMA or self.classification not in (FIXTURE, CANDIDATE):
            raise ValueError("unsupported batch schema/classification")
        if not self.events or len(self.events) != len(set(e for e, _ in self.events)):
            raise ValueError("missing/duplicate physical event")
        if (
            not self.boundaries
            or len(set(self.boundaries)) != len(self.boundaries)
            or not set(self.boundaries) <= {"T0", "T1", "T2", "T3", "T4", "SCENE_CLEAR"}
        ):
            raise ValueError("explicit unique boundary requirements required")
        if len(set(k for k, _ in self.approval_references)) != len(self.approval_references):
            raise ValueError("duplicate adoption references")
        for event, role in self.events:
            expected = (
                "TRAIN"
                if event.startswith("train_events/")
                else "CONTROL"
                if event.startswith("no_train_events/")
                else "CASE"
            )
            if self.classification == FIXTURE:
                if not event.startswith("synthetic:") or role not in ("TRAIN", "CONTROL", "CASE"):
                    raise ValueError("constructed event identity/role required")
            elif event not in CANDIDATE_EVENTS or role != expected:
                raise ValueError("event excluded or historical role substitution")
        if not self.sources or len(set(s.source_id for s in self.sources)) != len(self.sources):
            raise ValueError("missing/duplicate source identity")
        pairs = [(s.event, s.camera) for s in self.sources]
        if len(set(pairs)) != len(pairs):
            raise ValueError("duplicate event/camera source")
        for source in self.sources:
            source.validate()
            if (
                source.event not in dict(self.events)
                or source.manifest_reference != self.manifest_reference
            ):
                raise ValueError("source/event/manifest substitution")
        if set(s.event for s in self.sources) != set(dict(self.events)):
            raise ValueError("event source identity missing")


@dataclass(frozen=True)
class BoundaryObservation:
    observation_id: str
    reviewer_id: str
    source_id: str
    boundary_version: str
    observation: Observation
    previous: str | None = None
    correction_reason: str | None = None
    acoustic_shift_us: int = 0
    landmark_kind: str | None = None
    landmark_evidence: str | None = None
    human_statement_reference: str | None = None

    def validate(self, batch: Batch) -> Source:
        immutable(self)
        text(self.observation_id)
        self.observation.validate()
        sources = {s.source_id: s for s in batch.sources}
        if self.source_id not in sources:
            raise ValueError("observation source identity missing/substituted")
        source = sources[self.source_id]
        o = self.observation
        if (
            self.boundary_version != batch.boundary_version
            or o.boundary not in batch.boundaries
            or o.camera != source.camera
            or o.origin_us != source.origin_us
        ):
            raise ValueError("boundary/source clock contract mismatch")
        if type(self.acoustic_shift_us) is not int or self.acoustic_shift_us != 0:
            raise ValueError("acoustic offsets never shift human ground truth")
        if o.pts_ticks is not None:
            if o.timebase != source.timebase:
                raise ValueError("original frame timebase differs from source contract")
            frame_us = (
                Fraction(o.pts_ticks * source.timebase[0] * 1_000_000, source.timebase[1])
                + source.origin_us
            )
            if not source.origin_us <= frame_us <= source.end_us:
                raise ValueError("original PTS outside source contract")
        if o.value_us is not None:
            if o.pts_ticks is None or o.timebase != source.timebase:
                raise ValueError("exact source PTS contract required")
            if not source.origin_us <= o.value_us <= source.end_us:
                raise ValueError("timestamp outside source contract")
        if o.boundary == "T2" and o.state == "OBSERVABLE":
            if self.landmark_kind != "PHYSICAL_ROADWAY_ENTRY" or not self.landmark_evidence:
                raise ValueError(
                    "physical entry landmark deferred; lens-plane is not physical entry"
                )
        if bool(self.previous) != bool(self.correction_reason):
            raise ValueError("correction must link immutable parent and reason")
        return source
