"""Typed review-service port over the existing atomic constructed service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from railway_detection.annotation.human_review_domain import Observation, ReviewWorkflow
from railway_detection.annotation.human_review_service import (
    SCHEMA as SERVICE_SCHEMA,
)
from railway_detection.annotation.human_review_service import (
    ConstructedReviewService,
    ReviewScope,
    _value,
)
from railway_detection.application.contracts import (
    EvidenceClass,
    canonical,
    closed_json,
    synthetic_id,
)


class ReviewOperation(StrEnum):
    SEAL = "SEAL"
    COMPARE = "COMPARE"
    CORRECT = "CORRECT"
    ADJUDICATE = "ADJUDICATE"


@dataclass(frozen=True)
class ReviewRequest:
    scope: ReviewScope
    operation: ReviewOperation
    event: str
    request_id: str
    arguments_json: str
    classification: EvidenceClass = EvidenceClass.REVIEW
    schema: str = "TYPED_REVIEW_REQUEST/1"

    def arguments(self):
        if (
            self.schema != "TYPED_REVIEW_REQUEST/1"
            or self.classification != EvidenceClass.REVIEW
            or type(self.classification) is not EvidenceClass
        ):
            raise ValueError("constructed review fixture request required")
        if type(self.scope) is not ReviewScope or type(self.operation) is not ReviewOperation:
            raise ValueError("typed operation/session context required")
        self.scope.current()
        synthetic_id(self.event)
        synthetic_id(self.request_id)
        args = closed_json(self.arguments_json)
        expected = {
            ReviewOperation.SEAL: {"observations"},
            ReviewOperation.COMPARE: {"risk_inputs"},
            ReviewOperation.CORRECT: {"observations", "reason"},
            ReviewOperation.ADJUDICATE: {"source_digests", "state", "rationale"},
        }[self.operation]
        if type(args) is not dict or set(args) != expected:
            raise ValueError("closed versioned operation arguments required")
        if "observations" in args:
            rows = []
            for raw in args["observations"]:
                raw = dict(raw)
                if raw.get("timebase") is not None:
                    raw["timebase"] = tuple(raw["timebase"])
                rows.append(Observation(**raw))
            args["observations"] = tuple(rows)
            ReviewWorkflow._body(args["observations"])
        if "risk_inputs" in args:
            args["risk_inputs"] = tuple(tuple(p) for p in args["risk_inputs"])
        if "source_digests" in args:
            args["source_digests"] = tuple(args["source_digests"])
        return args


@dataclass(frozen=True)
class ReviewResponse:
    request_id: str
    event: str
    operation: ReviewOperation
    canonical_result: str
    schema: str = "TYPED_REVIEW_RESPONSE/1"
    classification: EvidenceClass = EvidenceClass.REVIEW
    genuine_evidence: bool = False

    def __post_init__(self):
        if (
            self.genuine_evidence is not False
            or self.classification != EvidenceClass.REVIEW
            or self.schema != "TYPED_REVIEW_RESPONSE/1"
        ):
            raise ValueError("only fixture review responses are available")


@dataclass(frozen=True)
class ReviewReadiness:
    fixture_history_available: bool
    genuine_complete: bool = False
    missing: tuple[str, ...] = (
        "genuine appointments/qualification/consent",
        "source-bound human observations",
        "independent required review",
        "real human batch judgment",
        "protected source grants",
    )
    schema: str = "REVIEW_SERVICE_READINESS/1"

    def __post_init__(self):
        if self.genuine_complete is not False or self.schema != "REVIEW_SERVICE_READINESS/1":
            raise ValueError("fixture readiness cannot complete genuine review")


class ReviewServicePort(Protocol):
    def perform(self, request: ReviewRequest) -> ReviewResponse: ...


class TypedConstructedReviewService:
    """No independent transaction or role database; legacy delegate owns both journals."""

    def __init__(self, authority, store):
        self.delegate = ConstructedReviewService(authority, store)
        self.events: tuple[ReviewResponse, ...] = ()

    def perform(self, request: ReviewRequest) -> ReviewResponse:
        if type(request) is not ReviewRequest:
            raise ValueError("typed review service request required")
        args = request.arguments()
        result = self.delegate.execute(
            request.scope,
            request.operation.value,
            request.event,
            request_id=request.request_id,
            **args,
        )
        if (
            result.get("classification") != EvidenceClass.REVIEW
            or result.get("real_human_evidence") is not False
        ):
            raise ValueError("fixture service cannot emit genuine evidence")
        response = ReviewResponse(
            request.request_id, request.event, request.operation, canonical(result)
        )
        prior = tuple(
            e for e in self.events if (e.event, e.request_id) == (request.event, request.request_id)
        )
        if prior and prior != (response,):
            raise ValueError("typed response substitution")
        if not prior:
            self.events += (response,)
        return response

    def execute(self, scope, operation, event, *, request_id, **args):
        # Compatibility adapter only: every call becomes a closed typed request.
        request = ReviewRequest(
            scope, ReviewOperation(operation), event, request_id, canonical(_value(args))
        )
        return json.loads(self.perform(request).canonical_result)

    def readiness(self, scope: ReviewScope, event: str) -> ReviewReadiness:
        if type(scope) is not ReviewScope:
            raise ValueError("typed current review scope required before metadata access")
        a = self.delegate.authority
        with a._transaction():
            if a.db.execute("SELECT version FROM constructed_review_service").fetchall() != [
                (SERVICE_SCHEMA,)
            ]:
                raise ValueError("review service schema changed")
            _, grant = a._session(scope.session, scope.fence, **scope.current())
            if grant["event"] != event:
                raise ValueError("review readiness event mismatch")
            self.delegate.store._restore()
        return ReviewReadiness(self.delegate.store.anchor[0] > 0)

    def require_genuine_complete_record(self, envelope) -> None:
        raise PermissionError(
            "Constructed review records never satisfy genuine complete-record validation"
        )
