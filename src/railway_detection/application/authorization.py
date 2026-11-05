"""Typed point-of-use fixture access over the existing transactional broker."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from railway_detection.application.contracts import EvidenceClass, canonical, synthetic_id
from railway_detection.safety.constructed_broker import ConstructedResourceBroker


class FixtureOperation(StrEnum):
    READ = "READ"
    PROBE = "PROBE"
    HASH = "HASH"


@dataclass(frozen=True)
class ResourceUseRequest:
    session: str
    transaction: str
    fence: int
    actor: str
    operation: FixtureOperation
    resource: str
    context: str
    purpose: str
    now: int
    expected_resource_digest: str
    classification: EvidenceClass = EvidenceClass.SYNTHETIC
    schema: str = "TYPED_FIXTURE_ACCESS/1"

    def validate(self):
        if (
            self.schema != "TYPED_FIXTURE_ACCESS/1"
            or type(self.classification) is not EvidenceClass
            or self.classification != EvidenceClass.SYNTHETIC
        ):
            raise ValueError("fixture access cannot accept external or genuine resource claims")
        for value in (self.session, self.transaction, self.actor, self.resource):
            synthetic_id(value)
        if type(self.operation) is not FixtureOperation:
            raise ValueError("closed constructed READ/PROBE/HASH operation required")
        if (
            type(self.fence) is not int
            or self.fence < 1
            or type(self.now) is not int
            or self.now < 0
        ):
            raise ValueError("exact fence and mock integer time required")
        if (
            not self.context
            or not self.purpose
            or type(self.expected_resource_digest) is not str
            or not re.fullmatch("[0-9a-f]{64}", self.expected_resource_digest)
        ):
            raise ValueError("exact runtime/purpose/resource version binding required")


@dataclass(frozen=True)
class ResourceUseResponse:
    session: str
    transaction: str
    payload_json: str
    receipt_json: str
    classification: EvidenceClass = EvidenceClass.SYNTHETIC
    schema: str = "TYPED_FIXTURE_ACCESS_RESPONSE/1"


class ResourceAccessPort(Protocol):
    def perform(self, request: ResourceUseRequest) -> ResourceUseResponse: ...


class TypedConstructedResourceBroker:
    def __init__(self, authority, *, resources, expected_registry_digest):
        self.delegate = ConstructedResourceBroker(
            authority, resources=resources, expected_registry_digest=expected_registry_digest
        )
        self.events: tuple[ResourceUseResponse, ...] = ()
        self._receipts = {}

    def perform(self, request: ResourceUseRequest) -> ResourceUseResponse:
        if type(request) is not ResourceUseRequest:
            raise ValueError("typed point-of-use request required")
        request.validate()
        payload, receipt = self.delegate.use(
            request.session,
            request.transaction,
            fence=request.fence,
            actor=request.actor,
            operation=request.operation.value,
            resource=request.resource,
            context=request.context,
            purpose=request.purpose,
            now=request.now,
            expected_resource_digest=request.expected_resource_digest,
        )
        from dataclasses import asdict

        response = ResourceUseResponse(
            request.session, request.transaction, canonical(payload), canonical(asdict(receipt))
        )
        prior = tuple(
            e
            for e in self.events
            if (e.session, e.transaction) == (request.session, request.transaction)
        )
        if prior and prior != (response,):
            raise ValueError("point-of-use response substitution")
        if not prior:
            self.events += (response,)
        self._receipts[request.session, request.transaction] = receipt
        return response

    def use(
        self,
        session,
        transaction,
        *,
        fence,
        actor,
        operation,
        resource,
        context,
        purpose,
        now,
        expected_resource_digest,
    ):
        import json

        request = ResourceUseRequest(
            session,
            transaction,
            fence,
            actor,
            FixtureOperation(operation),
            resource,
            context,
            purpose,
            now,
            expected_resource_digest,
        )
        response = self.perform(request)
        return json.loads(response.payload_json), self._receipts[session, transaction]
