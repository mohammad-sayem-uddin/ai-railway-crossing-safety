"""AUTH-DESCRIPTIVE-EVAL-EXEC: the gate for descriptive execution on real-data caches (Mission 10).

Distinct from AUTH-MEDIA-ACCESS (which governs raw media bytes) and from EVAL-AUTH (which governs
the *official* Phase 12 run). This record governs cache-only replays of real events whose results
would be reported descriptively. It is verified from disk on every call and is bound to the live
state of everything it vouches for:

* ``promotion_receipt_sha256`` -- the verified Stage-2.1 promotion receipt (so second-review
  enforcement and live media-hash attestation are part of what was authorized);
* ``evaluation_manifest_sha256`` -- the cache manifest being replayed;
* ``protocol_sha256`` -- the effective protocol profile;
* ``metric_scope_sha256`` -- the exact metric set the evaluation code computes (changing the metric
  set voids the authorization);
* ``model_config_provenance_sha256`` -- the frozen experiment configuration, which pins the model
  checkpoint hashes.

Like every record in this repository it is an unsigned, tamper-evident researcher statement; nothing
here creates one, and its absence blocks execution.

The gate applies when the engine's repository root *is* the real repository
(``media_guard.REAL_REPO_ROOT``). A synthetic tree under the system temp directory is not real data.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from railway_detection.evaluation import governance
from railway_detection.safety import media_guard
from railway_detection.safety import path_identity as pid

DESCRIPTIVE_AUTH_RELATIVE = Path("data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json")
DESCRIPTIVE_AUTH_SCHEMA = "phase5-descriptive-eval-execution-authorization/1"
AUTHORIZATION_CLASS = "AUTH-DESCRIPTIVE-EVAL-EXEC"
DESCRIPTIVE_OPERATION = "descriptive_cache_only_replay"

#: Metric fields computed by ``evaluation.metrics.SingleEventEvaluation``: the bound scope.
DESCRIPTIVE_METRIC_SCOPE = (
    "blocked_seconds",
    "clearance_latency_s",
    "closure_episodes",
    "excess_closed_duration_s",
    "exposure_s",
    "missed_train",
    "premature_opening",
    "total_closed_s",
    "warning_lead_time_s",
)

BINDING_KEYS = (
    "evaluation_manifest_sha256",
    "metric_scope_sha256",
    "model_config_provenance_sha256",
    "promotion_receipt_sha256",
    "protocol_sha256",
)
_KEYS = frozenset(
    {
        "schema_version",
        "authorization_id",
        "authorization_class",
        "status",
        "authorized_by",
        "authorized_at_utc",
        "expires_at_utc",
        "revoked",
        "authorization_statement",
        "attestation",
        "recorded_by",
        "scope",
        "bindings",
        "record_sha256",
    }
)
_SCOPE_KEYS = frozenset(
    {
        "operation",
        "conditions",
        "events",
        "metric_scope",
        "purpose",
        "field_or_physical_operations_authorized",
    }
)
_SHA256 = re.compile(r"[0-9a-f]{64}")
ALL_MANIFEST_EVENTS = "ALL_MANIFEST_EVENTS"


class DescriptiveExecutionNotAuthorized(PermissionError):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"[{code}] {detail}")


@dataclass(frozen=True)
class VerifiedDescriptiveAuthorization:
    authorization_id: str
    record_sha256: str
    bindings: dict[str, str]


def metric_scope_sha256() -> str:
    raw = json.dumps(list(DESCRIPTIVE_METRIC_SCOPE), separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def live_bindings(root: Path, *, manifest_sha256: str) -> dict[str, str | None]:
    """Recompute every binding from the repository as it is now (None = cannot be verified)."""
    from railway_detection.evaluation.execution_gate import assess_official_phase12_readiness

    readiness = assess_official_phase12_readiness(root)
    live = readiness.live_bindings
    return {
        "evaluation_manifest_sha256": manifest_sha256,
        "metric_scope_sha256": metric_scope_sha256(),
        "model_config_provenance_sha256": live.get("frozen_config_sha256"),
        "promotion_receipt_sha256": live.get("stage21_promotion_receipt_sha256"),
        "protocol_sha256": live.get("protocol_profile_sha256"),
    }


def verify_descriptive_authorization(
    root: Path,
    *,
    condition: str | None,
    event_id: str | None,
    manifest_sha256: str,
    now: datetime | None = None,
    live: dict[str, str | None] | None = None,
) -> VerifiedDescriptiveAuthorization:
    """Verify the on-disk record for one replay. Never consults a caller flag or environment."""
    now = now or datetime.now(UTC)
    path = root / DESCRIPTIVE_AUTH_RELATIVE
    if not path.is_file():
        raise DescriptiveExecutionNotAuthorized(
            "AUTH_DESCRIPTIVE_EVAL_EXEC_NOT_GRANTED",
            f"no recorded AUTH-DESCRIPTIVE-EVAL-EXEC at {DESCRIPTIVE_AUTH_RELATIVE}; descriptive "
            "execution on real-data caches is blocked until a researcher records one.",
        )
    try:
        payload = json.loads(path.read_bytes())
    except (OSError, ValueError) as exc:
        raise DescriptiveExecutionNotAuthorized(
            "AUTH_DESCRIPTIVE_EVAL_EXEC_MALFORMED", f"cannot parse {path}: {exc}"
        ) from exc
    try:
        allowlist = governance.load_allowlist(root)
        _validate(payload, allowlist=allowlist, condition=condition, event_id=event_id, now=now)
        live = live if live is not None else live_bindings(root, manifest_sha256=manifest_sha256)
        declared = payload["bindings"]
        for key in BINDING_KEYS:
            actual = live.get(key)
            if actual is None:
                raise ValueError(
                    f"binding {key} cannot be verified: the live artifact is missing or invalid"
                )
            if declared[key] != actual:
                raise ValueError(
                    f"binding {key} no longer matches the live artifact "
                    f"(recorded {declared[key][:12]}…, live {actual[:12]}…)"
                )
    except (ValueError, governance.GovernanceError) as exc:
        raise DescriptiveExecutionNotAuthorized(
            "AUTH_DESCRIPTIVE_EVAL_EXEC_INVALID", str(exc)
        ) from exc
    return VerifiedDescriptiveAuthorization(
        authorization_id=payload["authorization_id"],
        record_sha256=payload["record_sha256"],
        bindings=dict(declared),
    )


def _validate(
    payload: Any,
    *,
    allowlist: frozenset[str],
    condition: str | None,
    event_id: str | None,
    now: datetime,
) -> None:
    if not isinstance(payload, dict):
        raise ValueError("the record must be a JSON object")
    if set(payload) - _KEYS or _KEYS - set(payload):
        raise ValueError(
            f"fields must be exactly {sorted(_KEYS)}; unexpected {sorted(set(payload) - _KEYS)}, "
            f"missing {sorted(_KEYS - set(payload))}"
        )
    if payload["schema_version"] != DESCRIPTIVE_AUTH_SCHEMA:
        raise ValueError(f"unsupported schema_version {payload['schema_version']!r}")
    if payload["authorization_class"] != AUTHORIZATION_CLASS:
        raise ValueError(f"authorization_class must be {AUTHORIZATION_CLASS!r}")
    for key in ("authorization_id", "authorized_by", "authorization_statement"):
        if not isinstance(payload[key], str) or not payload[key].strip():
            raise ValueError(f"{key} is required")
    if payload["status"] != "APPROVED":
        raise ValueError(f"status is {payload['status']!r}; it must be 'APPROVED'")
    if payload["revoked"] is not False:
        raise ValueError("revoked must be the boolean false")
    if payload["authorized_by"] not in allowlist:
        raise ValueError(f"signer {payload['authorized_by']!r} is not on the authority allowlist")
    attestation = payload["attestation"]
    if (
        not isinstance(attestation, dict)
        or set(attestation) != {"type", "signature"}
        or attestation["type"] != governance.ATTESTATION_RECORDED_STATEMENT
        or attestation["signature"] is not None
    ):
        raise ValueError("attestation must be a recorded researcher statement with signature: null")
    recorded_by = payload["recorded_by"]
    if (
        not isinstance(recorded_by, dict)
        or set(recorded_by) - {"kind", "identity", "transcription_source"}
        or recorded_by.get("kind") not in {"researcher", "agent_transcription"}
        or not isinstance(recorded_by.get("identity"), str)
        or not recorded_by["identity"].strip()
    ):
        raise ValueError("recorded_by must name a kind and an identity")
    if recorded_by["kind"] == "agent_transcription" and not (
        isinstance(recorded_by.get("transcription_source"), str)
        and recorded_by["transcription_source"].strip()
    ):
        raise ValueError("agent_transcription requires transcription_source")
    if payload["record_sha256"] != governance.canonical_record_sha256(payload):
        raise ValueError("record_sha256 does not match the record content")

    issued = media_guard._utc(payload["authorized_at_utc"], "authorized_at_utc")
    expires = media_guard._utc(payload["expires_at_utc"], "expires_at_utc")
    if issued > now:
        raise ValueError("authorized_at_utc is in the future")
    if expires <= issued:
        raise ValueError("expires_at_utc must be after authorized_at_utc")
    if now >= expires:
        raise ValueError(f"the authorization expired at {expires.isoformat()}")

    scope = payload["scope"]
    if not isinstance(scope, dict) or set(scope) != _SCOPE_KEYS:
        raise ValueError(f"scope must declare exactly {sorted(_SCOPE_KEYS)}")
    if scope["operation"] != DESCRIPTIVE_OPERATION:
        raise ValueError(f"scope.operation must be {DESCRIPTIVE_OPERATION!r}")
    if scope["field_or_physical_operations_authorized"] is not False:
        raise ValueError("field or physical railway operations can never be authorized here")
    if not isinstance(scope["purpose"], str) or len(scope["purpose"].strip()) < 10:
        raise ValueError("scope.purpose must state a specific purpose")
    conditions = media_guard._string_list(scope["conditions"], "scope.conditions")
    events = media_guard._string_list(scope["events"], "scope.events")
    metric_scope = media_guard._string_list(scope["metric_scope"], "scope.metric_scope")
    if sorted(metric_scope) != sorted(DESCRIPTIVE_METRIC_SCOPE):
        raise ValueError(
            "scope.metric_scope must equal the metric set the evaluation code computes"
        )
    if condition is not None and condition not in conditions:
        raise ValueError(f"condition {condition!r} is not authorized; authorized {conditions}")
    if events != [ALL_MANIFEST_EVENTS] and (event_id is None or event_id not in events):
        raise ValueError(f"event {event_id!r} is outside the authorized events")

    bindings = payload["bindings"]
    if not isinstance(bindings, dict) or set(bindings) != set(BINDING_KEYS):
        raise ValueError(f"bindings must be exactly {list(BINDING_KEYS)}")
    for key in BINDING_KEYS:
        if not isinstance(bindings[key], str) or not _SHA256.fullmatch(bindings[key]):
            raise ValueError(f"binding {key} is not a SHA-256")


def require_descriptive_authorization_for_engine(
    repo_root: Path, *, condition: str | None, event_id: str, manifest_sha256: str
) -> None:
    """Called by the cache-only replay engine at the operation boundary."""
    if not _touches_real_repository(repo_root):
        return  # a disjoint synthetic tree is not real data
    verify_descriptive_authorization(
        Path(media_guard.REAL_REPO_ROOT),
        condition=condition,
        event_id=event_id,
        manifest_sha256=manifest_sha256,
    )


def _touches_real_repository(repo_root: Path) -> bool:
    """True unless ``repo_root`` is provably a tree disjoint from the real repository.

    Decided by filesystem identity, not by spelling (Mission 14, F13-04): a case-variant or alias
    of the real checkout, the checkout's parent, or any directory inside it all count as the real
    repository.  A path that cannot be canonicalised is treated as real (fail closed).
    """
    real = Path(media_guard.REAL_REPO_ROOT)
    try:
        return pid.is_within(repo_root, real) or pid.is_within(real, repo_root)
    except pid.PathIdentityError:
        return True


__all__ = [
    "BINDING_KEYS",
    "DESCRIPTIVE_AUTH_RELATIVE",
    "DESCRIPTIVE_AUTH_SCHEMA",
    "DESCRIPTIVE_METRIC_SCOPE",
    "DescriptiveExecutionNotAuthorized",
    "VerifiedDescriptiveAuthorization",
    "live_bindings",
    "metric_scope_sha256",
    "require_descriptive_authorization_for_engine",
    "verify_descriptive_authorization",
]
