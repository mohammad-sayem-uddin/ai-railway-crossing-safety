"""Versioned immutable application boundaries. Labels never authenticate evidence."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from enum import StrEnum

APPLICATION_SCHEMA = "CONSTRUCTED_APPLICATION/1"


class EvidenceClass(StrEnum):
    SYNTHETIC = "CONSTRUCTED_SYNTHETIC_INPUT"
    REVIEW = "CONSTRUCTED_REVIEW_FIXTURE"
    EXTERNAL = "UNVERIFIED_EXTERNAL_INPUT"
    PENDING = "GENUINE_EVIDENCE_PENDING"


def synthetic_id(value: str) -> None:
    if type(value) is not str or not value.startswith("synthetic:") or len(value) <= 10:
        raise ValueError("explicit constructed identity required")


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"


def closed_json(text: str):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate JSON field refused: " + key)
            result[key] = value
        return result

    def constant(value):
        raise ValueError("nonfinite JSON value refused: " + value)

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


@dataclass(frozen=True)
class EvidenceEnvelope:
    classification: EvidenceClass
    subject: str
    source: str
    schema: str = "EVIDENCE_ORIGIN/1"

    def require_constructed(self) -> None:
        if (
            type(self.classification) is not EvidenceClass
            or self.classification != EvidenceClass.SYNTHETIC
        ):
            raise ValueError("only CONSTRUCTED_SYNTHETIC_INPUT may enter this application")
        if self.schema != "EVIDENCE_ORIGIN/1":
            raise ValueError("unsupported evidence origin schema")
        synthetic_id(self.subject)
        synthetic_id(self.source)

    def require_genuine(self) -> None:
        raise PermissionError(
            "No genuine-evidence service is connected; labels cannot establish it"
        )


@dataclass(frozen=True)
class ApplicationRequest:
    event: str
    fixture: str
    seed: int
    code_identity: str
    crossing: str = "crossing_A"
    classification: EvidenceClass = EvidenceClass.SYNTHETIC
    schema: str = APPLICATION_SCHEMA

    def validate(self) -> None:
        if self.schema != APPLICATION_SCHEMA or self.crossing != "crossing_A":
            raise ValueError("application schema or crossing mismatch")
        EvidenceEnvelope(self.classification, self.event, self.fixture).require_constructed()
        if type(self.seed) is not int or not 0 <= self.seed <= 1_000_000:
            raise ValueError("bounded deterministic integer seed required")
        if type(self.code_identity) is not str or not re.fullmatch(
            "[0-9a-f]{40}", self.code_identity
        ):
            raise ValueError("exact producing Git identity required")
        if (
            self.event != f"synthetic:m22:s{self.seed}:event"
            or self.fixture != f"synthetic:m22:s{self.seed}:fixture"
        ):
            raise ValueError("event/fixture do not bind the declared deterministic input")

    @classmethod
    def constructed(cls, *, code_identity: str, seed: int = 22) -> ApplicationRequest:
        result = cls(
            f"synthetic:m22:s{seed}:event", f"synthetic:m22:s{seed}:fixture", seed, code_identity
        )
        result.validate()
        return result

    def to_json(self) -> str:
        self.validate()
        return canonical(asdict(self))

    @classmethod
    def from_json(cls, text: str) -> ApplicationRequest:
        value = closed_json(text)
        if type(value) is not dict or set(value) != {
            "event",
            "fixture",
            "seed",
            "code_identity",
            "crossing",
            "classification",
            "schema",
        }:
            raise ValueError("closed versioned application request required")
        value["classification"] = EvidenceClass(value["classification"])
        result = cls(**value)
        result.validate()
        return result


@dataclass(frozen=True)
class CameraContract:
    camera: str
    source: str
    event: str
    origin_us: int
    accepted_inputs: int
    controller_digest: str
    time_unit: str = "microseconds"

    def __post_init__(self):
        synthetic_id(self.event)
        if self.camera not in ("front", "back") or self.source != "camera_" + self.camera:
            raise ValueError("exact camera/source contract required")
        if (
            type(self.origin_us) is not int
            or self.origin_us < 0
            or self.time_unit != "microseconds"
        ):
            raise ValueError("exact local microsecond origin required")
        if type(self.accepted_inputs) is not int or not 0 < self.accepted_inputs <= 8192:
            raise ValueError("bounded nonempty accepted constructed stream required")
        if type(self.controller_digest) is not str or not re.fullmatch(
            "[0-9a-f]{64}", self.controller_digest
        ):
            raise ValueError("controller identity required")


@dataclass(frozen=True)
class MetricContract:
    camera: str
    premature_opening_m4: bool | None
    never_protected_m5: int | None
    empirical_result: bool = False
    reason: str | None = None

    def __post_init__(self):
        if self.premature_opening_m4 is not None and type(self.premature_opening_m4) is not bool:
            raise ValueError("M4 must remain boolean or unavailable")
        if self.never_protected_m5 is not None and (
            type(self.never_protected_m5) is not int or self.never_protected_m5 not in (0, 1)
        ):
            raise ValueError("NEVER_PROTECTED_M5 must remain integer0/1 or unavailable")
        if (self.premature_opening_m4 is None or self.never_protected_m5 is None) and not (
            type(self.reason) is str and self.reason.strip()
        ):
            raise ValueError("unavailable metric requires its explicit reason")
        if self.camera not in ("front", "back"):
            raise ValueError("known independent camera required for metric")
        if self.empirical_result is not False:
            raise ValueError("constructed metrics cannot become empirical results")


@dataclass(frozen=True)
class ServiceState:
    schema: str
    classification: str
    history_count: int
    genuine_evidence: bool = False
    promotion_available: bool = False

    def __post_init__(self):
        if self.genuine_evidence is not False or self.promotion_available is not False:
            raise ValueError(
                "constructed service state cannot establish genuine evidence/promotion"
            )
        if type(self.history_count) is not int or self.history_count < 0:
            raise ValueError("exact nonnegative history count required")
        if self.classification not in {"CONSTRUCTED_REVIEW_FIXTURE", "MOCK_PRINCIPAL_ONLY"}:
            raise ValueError("constructed service classification required")


@dataclass(frozen=True)
class ApplicationReceipt:
    schema: str
    request: ApplicationRequest
    cameras: tuple[CameraContract, ...]
    metric_contracts: tuple[MetricContract, ...]
    review: ServiceState
    authorization: ServiceState
    inactive_comparator_json: str
    lineage_digest: str
    workflow_execution_digest: str
    genuine_evidence: bool = False
    empirical_results: bool = False
    physical_deployment: bool = False

    def to_json(self) -> str:
        self.request.validate()
        if self.schema != APPLICATION_SCHEMA or any(
            x is not False
            for x in (self.genuine_evidence, self.empirical_results, self.physical_deployment)
        ):
            raise ValueError("constructed application cannot manufacture readiness")
        if tuple(c.camera for c in self.cameras) != ("front", "back"):
            raise ValueError("two explicitly independent cameras required")
        if any(
            c.source != "camera_" + c.camera or c.event != self.request.event for c in self.cameras
        ):
            raise ValueError("camera/event/source binding mismatch")
        if tuple(m.camera for m in self.metric_contracts) != ("front", "back"):
            raise ValueError("exact independent metric camera contracts required")
        if (
            self.review.classification != "CONSTRUCTED_REVIEW_FIXTURE"
            or self.authorization.classification != "MOCK_PRINCIPAL_ONLY"
        ):
            raise ValueError("review and authorization classifications must remain separate")
        for value in (self.lineage_digest, self.workflow_execution_digest):
            if type(value) is not str or not re.fullmatch("[0-9a-f]{64}", value):
                raise ValueError("exact lineage/workflow digest required")
        outcomes = closed_json(self.inactive_comparator_json)
        if (
            type(outcomes) is not list
            or not outcomes
            or any(
                type(o) is not dict
                or o.get("active") is not False
                or o.get("logical_command") is not None
                or o.get("applied_command") is not None
                or o.get("decision_id") != "M22-COMP-MAPPING"
                or o.get("observation", {}).get("event") != self.request.event
                for o in outcomes
            )
        ):
            raise ValueError("application cannot activate an unadopted comparator")
        return canonical(asdict(self))
