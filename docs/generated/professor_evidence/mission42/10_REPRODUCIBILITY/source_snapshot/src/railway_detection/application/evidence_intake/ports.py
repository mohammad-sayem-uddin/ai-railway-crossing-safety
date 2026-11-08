"""Deployment contracts only. Absent services keep genuine review inactive."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from railway_detection.annotation.evidence_review.contracts import EvidenceVerifier
from railway_detection.application.preflight.engine import Request

from .intake import DocumentaryVerifier


class HumanIdentityProvider(Protocol):
    """Authenticate actual physical person; verify sessions, expiry and revocation."""

    def authenticate(self, session_reference: str, now: int) -> str: ...


class BlindSourcePlayer(Protocol):
    """Canonical guarded source use only; hide prior values and preserve local PTS.

    Production acceptance must bind exact resource/actor/operation/time/output,
    recheck the canonical point-of-use grant and audit blinding/exposure events.
    This interface supplies no playback implementation.
    """

    def present(self, request: Request, canonical_authorization: str, now: int) -> str: ...


class HumanObservationStore(Protocol):
    """Authenticate human submissions and atomically bind all review/WP04 parents.

    Implement current identity, assignment, independent second-review parents,
    separate adjudication parents, idempotent create-only writes, retained anchors,
    revocation, audit export and immutable corrections. Never generate judgments.
    """

    def commit_human_submission(
        self,
        human_submission_reference: str,
        expected_head: str,
        canonical_authorization: str,
        now: int,
    ) -> str: ...


class CanonicalPublisher(Protocol):
    """Validate complete active-schema batch and existing promotion receipt.

    This is not a grant issuer. Export must honor exact recipients/output scope.
    """

    def export_verified_batch(
        self,
        batch_digest: str,
        canonical_authorization: str,
        destination: str,
        now: int,
    ) -> str: ...


@dataclass(frozen=True)
class ActivationPorts:
    identity: HumanIdentityProvider | None = None
    documentary_verifier: DocumentaryVerifier | None = None
    review_verifier: EvidenceVerifier | None = None
    player: BlindSourcePlayer | None = None
    observation_store: HumanObservationStore | None = None
    publisher: CanonicalPublisher | None = None

    def missing(self) -> tuple[str, ...]:
        return tuple(name for name in self.__dataclass_fields__ if getattr(self, name) is None)

    def require_genuine_activation(self) -> None:
        # Availability is insufficient: real integrations need separate acceptance,
        # genuine evidence and operation-specific current canonical authorization.
        raise PermissionError(
            "Genuine review inactive; deployment acceptance and canonical grants required; "
            "missing services: " + ", ".join(self.missing())
        )
