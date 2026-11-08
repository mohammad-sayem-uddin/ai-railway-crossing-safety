"""Verifiers for the governance artifacts that gate official Phase 12 execution.

Every artifact here is a *recorded* statement bound to the repository's real
files by SHA-256. None of them is a cryptographic attestation: the repository
has no key infrastructure, and this module never pretends otherwise. What the
verifiers establish is deliberately narrow:

* the named authority is on the maintained allowlist
  (``data/ground_truth/authorized_reviewers.json``);
* the record has exactly the documented fields (unknown keys such as
  ``ready``/``approved`` are refused, so a forged flag can never matter);
* the record's content hash is self-consistent;
* every binding still equals the live artifact it names, so changing any
  evidence after the statement was recorded invalidates it.

What they cannot establish is *who actually typed the file*. Provenance is
therefore carried as an explicit ``attestation_level`` and surfaced in every
readiness report, so no consumer can mistake a recorded statement for an
external or cryptographic signature.

The module opens only small JSON/YAML metadata files. It never opens, decodes
or hashes source media.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from railway_detection.annotation.promotion_gate import (
    AuthorizedReviewersLoadError,
    load_authorized_reviewers,
)
from railway_detection.annotation.receipt import (
    PROMOTION_RECEIPT_PRODUCER,
    PROMOTION_RECEIPT_SCHEMA,
    receipt_body_sha256,
)
from railway_detection.evaluation.output_contracts import canonical_json_bytes
from railway_detection.evaluation.protocol_choices import (
    PROTOCOL_CHOICE_KEYS,
    ProtocolChoiceError,
    validate_protocol_choices,
)
from railway_detection.research_contracts import validate_camera_scope, validate_event_level_split

ALLOWLIST_RELATIVE = Path("data/ground_truth/authorized_reviewers.json")
SPLIT_DECISION_RELATIVE = Path("data/splits/phase12_event_split_decision.json")
R04_DECISION_RELATIVE = Path("data/manifests/phase12_r04_scope_decision.json")
PROTOCOL_DECISION_RELATIVE = Path("data/manifests/phase12_protocol_decision.json")
PROMOTION_RECEIPT_RELATIVE = Path("data/governance/stage21_promotion_receipt.json")
EVAL_AUTH_RELATIVE = Path("data/governance/eval_authorization.json")

SPLIT_DECISION_SCHEMA = "phase12-event-split-decision/1"
R04_DECISION_SCHEMA = "phase12-r04-scope-decision/1"
PROTOCOL_DECISION_SCHEMA = "phase12-protocol-decision/1"
EVAL_AUTH_SCHEMA = "phase12-eval-authorization/1"

ATTESTATION_RECORDED_STATEMENT = "RECORDED_RESEARCHER_STATEMENT"
ATTESTATION_LEVEL_UNSIGNED = "recorded_statement_unsigned"
AUTHORIZED_OPERATION = "phase12_official_evaluation"

EVAL_AUTH_BINDING_KEYS = (
    "decision_policy_sha256",
    "event_split_decision_sha256",
    "frozen_config_sha256",
    "input_manifest_sha256",
    "protocol_profile_sha256",
    "r04_scope_decision_sha256",
    "stage21_promotion_receipt_sha256",
)

_SHA256 = re.compile(r"[0-9a-f]{64}")


class GovernanceError(ValueError):
    """A governance artifact is missing, malformed, forged or unbound."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class VerifiedArtifact:
    path: Path
    sha256: str
    payload: dict[str, Any]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_small_file(path: Path) -> str:
    """Hash a governance metadata file (never media)."""
    return sha256_bytes(path.read_bytes())


def canonical_record_sha256(record: dict[str, Any], *, exclude: str = "record_sha256") -> str:
    """Hash a record's canonical JSON with its own digest field removed."""
    body = {key: value for key, value in record.items() if key != exclude}
    return sha256_bytes(canonical_json_bytes(body))


def load_allowlist(root: Path) -> frozenset[str]:
    try:
        return load_authorized_reviewers(root / ALLOWLIST_RELATIVE)
    except AuthorizedReviewersLoadError as exc:
        raise GovernanceError("AUTHORITY_ALLOWLIST_UNAVAILABLE", str(exc)) from exc


def _read_json_object(path: Path, *, missing_code: str) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        raise GovernanceError(missing_code, str(path))
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        invalid = missing_code.replace("_MISSING", "_INVALID")
        raise GovernanceError(invalid, f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GovernanceError(
            missing_code.replace("_MISSING", "_INVALID"), f"{path} must contain a JSON object"
        )
    return value, sha256_bytes(raw)


def _parse_utc(value: Any, field: str, *, now: datetime) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must carry a UTC offset")
    if parsed.astimezone(UTC) > now:
        raise ValueError(f"{field} is in the future")
    return parsed


def verify_decision_envelope(
    payload: dict[str, Any],
    *,
    schema_version: str,
    allowlist: frozenset[str],
    now: datetime,
) -> None:
    """Check the common researcher-decision envelope; raise ``ValueError``.

    A decision artifact must name an allowlisted authority and carry the
    researcher's statement verbatim. Presence of ``decision_status: APPROVED``
    alone proves nothing and is never sufficient.
    """
    if payload.get("schema_version") != schema_version:
        raise ValueError(f"unsupported schema_version {payload.get('schema_version')!r}")
    if payload.get("decision_status") != "APPROVED":
        raise ValueError("decision_status must be APPROVED")
    for key in ("decision_id", "decided_by", "researcher_statement"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} is required")
    if payload["decided_by"] not in allowlist:
        raise ValueError(
            f"decided_by {payload['decided_by']!r} is not on the maintained authority allowlist"
        )
    _parse_utc(payload.get("decided_at_utc"), "decided_at_utc", now=now)


def check_split_body(payload: dict[str, Any]) -> None:
    partitions = payload.get("partitions")
    if not isinstance(partitions, dict):
        raise ValueError("partitions is required")
    validate_event_level_split(partitions)


def check_r04_body(payload: dict[str, Any]) -> None:
    modes = payload.get("event_modes")
    accepted = payload.get("accepted_sync_events")
    if not isinstance(modes, dict) or not isinstance(accepted, list):
        raise ValueError("event_modes and accepted_sync_events are required")
    validate_camera_scope(modes, accepted_sync_events=set(accepted))


def verify_decision_file(
    root: Path,
    relative: Path,
    *,
    schema: str,
    missing_code: str,
    invalid_code: str,
    allowlist: frozenset[str],
    now: datetime,
    check_body: Any,
) -> VerifiedArtifact:
    """Load and verify one researcher decision artifact; raise ``GovernanceError``."""
    path = root / relative
    payload, digest = _read_json_object(path, missing_code=missing_code)
    try:
        verify_decision_envelope(payload, schema_version=schema, allowlist=allowlist, now=now)
        check_body(payload)
    except (ValueError, TypeError) as exc:
        raise GovernanceError(invalid_code, f"{relative}: {exc}") from exc
    return VerifiedArtifact(path=path, sha256=digest, payload=payload)


CALIBRATION_MANIFEST_RELATIVE = Path("data/manifests/camera_sync_offsets_candidate.yaml")
EXPLORATORY_AUTHORIZED_RELATIVE = Path(
    "configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml"
)


def _load_yaml_mapping(path: Path) -> dict[str, Any] | None:
    import yaml

    if not path.is_file():
        return None
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def calibration_supported_events(root: Path) -> set[str] | None:
    """Event keys (``cohort/event``) whose calibration verdict is CALIBRATION_SUPPORTED.

    Metadata only: reads the calibration manifest, never media. ``None`` when the
    manifest is absent or malformed.
    """
    manifest = _load_yaml_mapping(root / CALIBRATION_MANIFEST_RELATIVE)
    events = manifest.get("events") if manifest else None
    if not isinstance(events, dict):
        return None
    return {
        str(key)
        for key, entry in events.items()
        if isinstance(entry, dict) and entry.get("calibration_verdict") == "CALIBRATION_SUPPORTED"
    }


def documented_r04_candidates(root: Path) -> dict[str, Any]:
    """What the repository's existing records say about dual-camera scope. NOT a decision.

    Combines the calibration verdicts with the researcher's 2026-10-13 authorization of an
    exploratory dual-camera run. The exploratory authorization explicitly did not extend to
    any other use, so this is evidence for the researcher's R04 scope decision, never a
    substitute for it.
    """
    supported = calibration_supported_events(root)
    exploratory = _load_yaml_mapping(root / EXPLORATORY_AUTHORIZED_RELATIVE)
    authorized = (
        sorted(exploratory.get("included_events_calibration_supported", []))
        if exploratory
        else None
    )
    return {
        "is_decision": False,
        "calibration_supported": sorted(supported) if supported is not None else None,
        "phase8_authorized_exploratory": authorized,
        "consistent": (
            supported is not None and authorized is not None and set(authorized) == supported
        ),
        "note": (
            "Evidence only. The Phase 8 authorization covers the exploratory ablation, not "
            "the official evaluation scope; recording accepted_sync_events is the "
            "researcher's act."
        ),
    }


def verify_protocol_override(
    root: Path, *, allowlist: frozenset[str], now: datetime | None = None
) -> VerifiedArtifact | None:
    """Verify the *optional* researcher override of the documented protocol profile.

    Returns ``None`` when no override file exists (the documented profile then
    applies). A present but invalid or unimplementable override raises, so it can
    never degrade silently to the documented profile.
    """
    now = now or datetime.now(UTC)
    path = root / PROTOCOL_DECISION_RELATIVE
    if not path.is_file():
        return None
    payload, digest = _read_json_object(path, missing_code="PROTOCOL_DECISION_MISSING")
    try:
        verify_decision_envelope(
            payload, schema_version=PROTOCOL_DECISION_SCHEMA, allowlist=allowlist, now=now
        )
        choices = payload.get("choices")
        if not isinstance(choices, dict):
            raise ValueError("choices is required")
        unexpected = sorted(set(payload) - _PROTOCOL_ENVELOPE_KEYS)
        if unexpected:
            raise ValueError(f"unexpected fields {unexpected}")
        validate_protocol_choices(choices)
    except ProtocolChoiceError as exc:
        raise GovernanceError(exc.code, exc.detail) from exc
    except ValueError as exc:
        raise GovernanceError("PROTOCOL_DECISION_INVALID", str(exc)) from exc
    return VerifiedArtifact(path=path, sha256=digest, payload=payload)


_PROTOCOL_ENVELOPE_KEYS = frozenset(
    {
        "schema_version",
        "decision_status",
        "decision_id",
        "decided_by",
        "decided_at_utc",
        "researcher_statement",
        "choices",
        "notes",
    }
)


def verify_promotion_receipt(
    root: Path,
    *,
    review_record_sha256: dict[str, str],
    live_inputs: dict[str, str | None],
    now: datetime | None = None,
) -> VerifiedArtifact:
    """Verify the Stage-2.1 promotion receipt against the live repository metadata.

    The receipt is produced by ``railway_detection.annotation.readiness_cli``
    (``--receipt-path``) after the media-hashing readiness gate returns READY.
    The execution gate must not open media itself, so it checks that the receipt
    reports READY, is self-consistent, and is bound to the exact current record bytes
    and to the current allowlist, annotation inventory and active proposals. A receipt
    issued for any other state of those inputs is stale and refused. It is
    tamper-evident, not tamper-proof: it cannot prove the CLI was actually run.
    """
    now = now or datetime.now(UTC)
    path = root / PROMOTION_RECEIPT_RELATIVE
    payload, digest = _read_json_object(path, missing_code="STAGE21_PROMOTION_RECEIPT_MISSING")
    try:
        if payload.get("schema_version") != PROMOTION_RECEIPT_SCHEMA:
            raise ValueError(f"unsupported schema_version {payload.get('schema_version')!r}")
        if payload.get("produced_by") != PROMOTION_RECEIPT_PRODUCER:
            raise ValueError(f"produced_by must be {PROMOTION_RECEIPT_PRODUCER!r}")
        if payload.get("receipt_sha256") != receipt_body_sha256(payload):
            raise ValueError("receipt_sha256 does not match the receipt content")
        _parse_utc(payload.get("produced_at_utc"), "produced_at_utc", now=now)
        verdict = payload.get("verdict")
        if (
            not isinstance(verdict, dict)
            or verdict.get("ready") is not True
            or verdict.get("blocker_count") != 0
        ):
            raise ValueError("receipt does not record a READY verdict with zero blockers")
        if payload.get("media_hashes_verified_live") is not True:
            raise ValueError("receipt does not attest live media hashing")
        if not isinstance(payload.get("stage"), str) or not payload["stage"].strip():
            raise ValueError("stage is required")
        recorded = payload.get("review_record_sha256")
        if not isinstance(recorded, dict) or not recorded:
            raise ValueError("review_record_sha256 is required")
        if any(not isinstance(v, str) or not _SHA256.fullmatch(v) for v in recorded.values()):
            raise ValueError("review_record_sha256 contains an invalid digest")
        if recorded != review_record_sha256:
            changed = sorted(
                key
                for key in set(recorded) | set(review_record_sha256)
                if recorded.get(key) != review_record_sha256.get(key)
            )
            raise ValueError(f"review records differ from the receipt: {changed[:5]}")
        inputs = payload.get("inputs")
        if not isinstance(inputs, dict) or set(inputs) != set(live_inputs):
            raise ValueError(f"inputs must bind exactly {sorted(live_inputs)}")
        for key, live in sorted(live_inputs.items()):
            if live is None:
                raise ValueError(f"cannot check {key}: the live input is missing")
            if inputs[key] != live:
                raise ValueError(f"{key} differs from the receipt (inputs changed after issue)")
    except ValueError as exc:
        raise GovernanceError("STAGE21_PROMOTION_RECEIPT_INVALID", str(exc)) from exc
    return VerifiedArtifact(path=path, sha256=digest, payload=payload)


_EVAL_AUTH_KEYS = frozenset(
    {
        "schema_version",
        "authorization_id",
        "stage",
        "authorized_by",
        "authorized_at_utc",
        "authorization_statement",
        "attestation",
        "recorded_by",
        "scope",
        "bindings",
        "record_sha256",
    }
)


@dataclass(frozen=True)
class VerifiedAuthorization:
    artifact: VerifiedArtifact
    attestation_level: str
    recorded_by_kind: str


def verify_eval_authorization(
    root: Path,
    *,
    allowlist: frozenset[str],
    live_bindings: dict[str, str | None],
    promotion_stage: str | None,
    now: datetime | None = None,
) -> VerifiedAuthorization:
    """Verify EVAL-AUTH: a recorded researcher statement bound to live evidence.

    Raises ``GovernanceError`` with ``EVAL_AUTH_NOT_GRANTED`` when no record
    exists and ``EVAL_AUTH_INVALID``/``EVAL_AUTH_ATTESTATION_UNSUPPORTED``/
    ``EVAL_AUTH_BINDING_*`` otherwise. Never consults any caller flag.
    """
    now = now or datetime.now(UTC)
    path = root / EVAL_AUTH_RELATIVE
    if not path.is_file():
        raise GovernanceError(
            "EVAL_AUTH_NOT_GRANTED",
            f"no recorded EVAL-AUTH at {EVAL_AUTH_RELATIVE}; no authorization can be "
            "verified from chat statements or documents",
        )
    payload, digest = _read_json_object(path, missing_code="EVAL_AUTH_MISSING")
    try:
        unexpected = sorted(set(payload) - _EVAL_AUTH_KEYS)
        if unexpected:
            raise ValueError(f"unexpected fields {unexpected}; flags are never honored")
        missing = sorted(_EVAL_AUTH_KEYS - set(payload))
        if missing:
            raise ValueError(f"missing fields {missing}")
        if payload["schema_version"] != EVAL_AUTH_SCHEMA:
            raise ValueError(f"unsupported schema_version {payload['schema_version']!r}")
        for key in ("authorization_id", "stage", "authorized_by", "authorization_statement"):
            if not isinstance(payload[key], str) or not payload[key].strip():
                raise ValueError(f"{key} is required")
        if payload["authorized_by"] not in allowlist:
            raise ValueError(
                f"authorized_by {payload['authorized_by']!r} is not on the authority allowlist"
            )
        _parse_utc(payload["authorized_at_utc"], "authorized_at_utc", now=now)

        scope = payload["scope"]
        if not isinstance(scope, dict) or set(scope) != {
            "operation",
            "stage",
            "field_or_physical_operations_authorized",
        }:
            raise ValueError("scope must declare exactly operation, stage and physical flag")
        if scope["operation"] != AUTHORIZED_OPERATION:
            raise ValueError(f"scope.operation must be {AUTHORIZED_OPERATION!r}")
        if scope["stage"] != payload["stage"]:
            raise ValueError("scope.stage differs from stage")
        if scope["field_or_physical_operations_authorized"] is not False:
            raise ValueError("field or physical railway operations can never be authorized here")
        if promotion_stage is not None and payload["stage"] != promotion_stage:
            raise ValueError(
                f"stage {payload['stage']!r} differs from the promotion receipt stage "
                f"{promotion_stage!r}"
            )

        recorded_by = payload["recorded_by"]
        if not isinstance(recorded_by, dict) or set(recorded_by) - {
            "kind",
            "identity",
            "transcription_source",
        }:
            raise ValueError("recorded_by has unsupported fields")
        kind = recorded_by.get("kind")
        if kind not in {"researcher", "agent_transcription"}:
            raise ValueError("recorded_by.kind must be 'researcher' or 'agent_transcription'")
        if not isinstance(recorded_by.get("identity"), str) or not recorded_by["identity"].strip():
            raise ValueError("recorded_by.identity is required")
        if kind == "agent_transcription" and not (
            isinstance(recorded_by.get("transcription_source"), str)
            and recorded_by["transcription_source"].strip()
        ):
            raise ValueError("agent_transcription requires transcription_source")
    except ValueError as exc:
        raise GovernanceError("EVAL_AUTH_INVALID", str(exc)) from exc

    attestation = payload["attestation"]
    if (
        not isinstance(attestation, dict)
        or attestation.get("type") != ATTESTATION_RECORDED_STATEMENT
    ):
        raise GovernanceError(
            "EVAL_AUTH_ATTESTATION_UNSUPPORTED",
            f"only {ATTESTATION_RECORDED_STATEMENT!r} is verifiable; this repository has no "
            "signature or key infrastructure, so signature-style attestations are refused",
        )
    if set(attestation) != {"type", "signature"} or attestation["signature"] is not None:
        raise GovernanceError(
            "EVAL_AUTH_ATTESTATION_UNSUPPORTED",
            "a recorded statement must declare signature: null; unverifiable signature "
            "material is refused rather than trusted",
        )

    if payload["record_sha256"] != canonical_record_sha256(payload):
        raise GovernanceError(
            "EVAL_AUTH_INVALID", "record_sha256 does not match the record content"
        )

    bindings = payload["bindings"]
    if not isinstance(bindings, dict) or set(bindings) != set(EVAL_AUTH_BINDING_KEYS):
        raise GovernanceError(
            "EVAL_AUTH_INVALID", f"bindings must be exactly {list(EVAL_AUTH_BINDING_KEYS)}"
        )
    for key in EVAL_AUTH_BINDING_KEYS:
        declared = bindings[key]
        if not isinstance(declared, str) or not _SHA256.fullmatch(declared):
            raise GovernanceError("EVAL_AUTH_INVALID", f"binding {key} is not a SHA-256")
        live = live_bindings.get(key)
        if live is None:
            raise GovernanceError(
                "EVAL_AUTH_BINDING_UNVERIFIABLE",
                f"binding {key} cannot be checked: the live artifact is missing or invalid",
            )
        if declared != live:
            raise GovernanceError(
                "EVAL_AUTH_BINDING_MISMATCH",
                f"binding {key} no longer matches the live artifact "
                f"(recorded {declared[:12]}…, live {live[:12]}…)",
            )
    return VerifiedAuthorization(
        artifact=VerifiedArtifact(path=path, sha256=digest, payload=payload),
        attestation_level=ATTESTATION_LEVEL_UNSIGNED,
        recorded_by_kind=kind,
    )


__all__ = [
    "ATTESTATION_LEVEL_UNSIGNED",
    "ATTESTATION_RECORDED_STATEMENT",
    "AUTHORIZED_OPERATION",
    "EVAL_AUTH_BINDING_KEYS",
    "EVAL_AUTH_RELATIVE",
    "EVAL_AUTH_SCHEMA",
    "GovernanceError",
    "PROMOTION_RECEIPT_PRODUCER",
    "PROMOTION_RECEIPT_RELATIVE",
    "PROMOTION_RECEIPT_SCHEMA",
    "PROTOCOL_CHOICE_KEYS",
    "PROTOCOL_DECISION_RELATIVE",
    "R04_DECISION_RELATIVE",
    "R04_DECISION_SCHEMA",
    "SPLIT_DECISION_RELATIVE",
    "SPLIT_DECISION_SCHEMA",
    "VerifiedArtifact",
    "VerifiedAuthorization",
    "calibration_supported_events",
    "canonical_record_sha256",
    "check_r04_body",
    "check_split_body",
    "documented_r04_candidates",
    "load_allowlist",
    "sha256_bytes",
    "sha256_small_file",
    "verify_decision_envelope",
    "verify_decision_file",
    "verify_eval_authorization",
    "verify_promotion_receipt",
    "verify_protocol_override",
]
