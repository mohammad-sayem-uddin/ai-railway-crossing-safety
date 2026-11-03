"""Evidence-derived official execution readiness checks for Phase 12/13.

This module never accepts caller-supplied readiness booleans. It inspects the
repository's real review records, researcher decision artifacts, promotion
receipt, policy/config identity, checkpoint hashes, input manifest and the
recorded EVAL-AUTH statement. It reads only small metadata files: it never
opens, decodes or hashes source media.

Every blocker carries a category, the artifact that would clear it and the
remedy, so a blocked report distinguishes *missing human evidence* from
*invalid evidence* and from blockers that are merely *derived* from another.

EVAL-AUTH is a recorded researcher statement bound by SHA-256 to the live
evidence (see ``governance``). It is explicitly **not** a cryptographic
attestation; readiness reports state its attestation level.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from railway_detection.annotation import notices as notices_module
from railway_detection.annotation import readiness_cli
from railway_detection.annotation import receipt as receipt_module
from railway_detection.annotation.schemas import SchemaValidationError
from railway_detection.annotation.second_review import assess_second_reviews
from railway_detection.annotation.stage2_1_schema import (
    REVIEWER_ID_BLOCKLIST,
    STAGE_2_1_SCHEMA_VERSION,
    build_stage2_1_record_from_dict,
)
from railway_detection.evaluation import governance, protocol_choices
from railway_detection.evaluation.input_contracts import (
    EvaluationInputError,
    load_evaluation_input_manifest,
)
from railway_detection.experiments.frozen_config import (
    CheckpointIntegrityError,
    ConfigurationIntegrityError,
    load_frozen_config,
    verify_checkpoint_integrity,
    verify_timing_safeguards,
)

# Categories
MISSING_HUMAN_EVIDENCE = "MISSING_HUMAN_EVIDENCE"
MISSING_RESEARCH_DECISION = "MISSING_RESEARCH_DECISION"
INVALID_EVIDENCE = "INVALID_EVIDENCE"
INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
DERIVED = "DERIVED"
NOT_OFFICIAL_EVIDENCE = "NOT_OFFICIAL_EVIDENCE"
AUTHORIZATION = "AUTHORIZATION"
UNCLASSIFIED = "UNCLASSIFIED"

_STAGE21_PRODUCER = (
    "researcher runs the Stage-2.1 review/adjudication workflow "
    "(annotation.review_session / adjudication_session)"
)

# code -> (category, artifact that clears it, remedy)
BLOCKER_CATALOGUE: dict[str, tuple[str, str, str]] = {
    "STAGE21_RECORDS_MISSING": (
        MISSING_HUMAN_EVIDENCE,
        "data/ground_truth/reviews/**/*_review.json with schema_version 8.1.0-stage2.1",
        f"Genuine Stage-2.1 records: {_STAGE21_PRODUCER}. A statement that annotations "
        "were approved is not a record; legacy 6.0.0 files cannot be migrated.",
    ),
    "COHORT_APPROVAL_MISSING": (
        DERIVED,
        "an APPROVED Stage-2.1 record in each of train_events, no_train_events, engine_events",
        "Clears automatically once STAGE21_RECORDS_MISSING is resolved for that cohort.",
    ),
    "LEGACY_OR_UNKNOWN_GROUND_TRUTH_SCHEMA": (
        INVALID_EVIDENCE,
        "a replacement Stage-2.1 record for this event",
        "Legacy records are preserved byte-for-byte and never evaluated against. "
        "Resolved per event by a genuine Stage-2.1 record; see "
        "docs/LEGACY_REVIEW_RECONCILIATION.json.",
    ),
    "GROUND_TRUTH_RECORD_INVALID": (
        INTEGRITY_FAILURE,
        "a readable JSON object review record",
        "Repair the file from its preserved original; do not hand-edit approvals.",
    ),
    "GROUND_TRUTH_SCHEMA_INVALID": (
        INVALID_EVIDENCE,
        "a schema-valid Stage-2.1 record",
        "Re-run the review workflow for the event; the schema error names the field.",
    ),
    "GROUND_TRUTH_NOT_APPROVED": (
        MISSING_HUMAN_EVIDENCE,
        "adjudication_status APPROVED on a valid Stage-2.1 record",
        "Complete adjudication in the review workflow.",
    ),
    "STAGE21_PROMOTION_RECEIPT_MISSING": (
        MISSING_HUMAN_EVIDENCE,
        "data/governance/stage21_promotion_receipt.json",
        "Run `python -m railway_detection.annotation.readiness_cli --receipt-path "
        "data/governance/stage21_promotion_receipt.json` once the media-hashing "
        "readiness gate reports READY (the execution gate itself never hashes media).",
    ),
    "STAGE21_PROMOTION_RECEIPT_INVALID": (
        INVALID_EVIDENCE,
        "a receipt bound to the current review records and allowlist",
        "Re-run the readiness CLI after any record or allowlist change.",
    ),
    "INVALIDATION_NOTICE_INVALID": (
        INTEGRITY_FAILURE,
        "an invalidation notice whose sibling legacy record is present, unchanged, legacy-schema",
        "Do not edit notices or the legacy records they describe; investigate the named problem.",
    ),
    "AUTHORITY_ALLOWLIST_UNAVAILABLE": (
        INTEGRITY_FAILURE,
        "data/ground_truth/authorized_reviewers.json",
        "The maintained allowlist must load; it is edited only by the researcher.",
    ),
    "EVENT_SPLIT_DECISION_MISSING": (
        MISSING_RESEARCH_DECISION,
        "data/splits/phase12_event_split_decision.json",
        "Researcher-authored event-level train/val/test split decision (R-SPLIT).",
    ),
    "EVENT_SPLIT_DECISION_INVALID": (
        INVALID_EVIDENCE,
        "data/splits/phase12_event_split_decision.json",
        "Fix the named field; decided_by must be on the allowlist.",
    ),
    "R04_SCOPE_DECISION_MISSING": (
        MISSING_RESEARCH_DECISION,
        "data/manifests/phase12_r04_scope_decision.json",
        "Researcher-authored camera-scope decision naming accepted-sync events (R-R04SCOPE).",
    ),
    "R04_SCOPE_DECISION_INVALID": (
        INVALID_EVIDENCE,
        "data/manifests/phase12_r04_scope_decision.json",
        "Fix the named field; decided_by must be on the allowlist.",
    ),
    "R04_ACCEPTED_EVENT_NOT_SUPPORTED": (
        INVALID_EVIDENCE,
        "a CALIBRATION_SUPPORTED entry for each accepted-sync event",
        "Accepted synchronization must be backed by calibration evidence; unsupported events "
        "run on independent camera clocks.",
    ),
    "PREMATURE_OPENING_DEFINITION_UNDECIDED": (
        MISSING_RESEARCH_DECISION,
        "data/manifests/phase12_protocol_decision.json with choices.premature_opening_window",
        "Choose the premature-opening window: protocol v9 't1_entry_to_t4_clearance' or M4 "
        "'first_blocked_to_t4_clearance'. Both are implemented and selectable; neither is a "
        "default. Evidence: docs/PREMATURE_OPENING_DECISION_EVIDENCE.md.",
    ),
    "PROTOCOL_DECISION_INVALID": (
        INVALID_EVIDENCE,
        "data/manifests/phase12_protocol_decision.json (optional override)",
        "Fix or remove the override; without it the documented protocol profile applies.",
    ),
    "PROTOCOL_CHOICE_NOT_IMPLEMENTED": (
        INVALID_EVIDENCE,
        "an evaluator implementation of the chosen definition",
        "Choose an implemented option, or implement and test the definition first "
        "(e.g. design-document M4 premature-opening window).",
    ),
    "MANIFEST_MISSING": (
        MISSING_HUMAN_EVIDENCE,
        "data/manifests/phase12_evaluation_inputs.json",
        "Hash-bound event input manifest built from the approved split; "
        "see evaluation.manifest_builder. Depends on the split decision.",
    ),
    "ANNOTATION_INVENTORY_MISSING": (
        MISSING_HUMAN_EVIDENCE,
        "data/manifests/layer_b_v2_annotation_inventory.json",
        "The independent annotation/media inventory must be present; a manifest cannot "
        "vouch for its own events.",
    ),
    "MANIFEST_EVENT_NOT_IN_INVENTORY": (
        INVALID_EVIDENCE,
        "manifest event ids equal to cohort-qualified inventory keys (cohort/event_id)",
        "Rebuild the manifest from the decided split using inventory identities.",
    ),
    "MANIFEST_COHORT_MISMATCH": (
        INTEGRITY_FAILURE,
        "manifest cohorts equal to the inventory category",
        "A manifest may not relabel an event's cohort.",
    ),
    "MANIFEST_TEST_EVENT_WITHOUT_APPROVED_RECORD": (
        INVALID_EVIDENCE,
        "an approved, valid Stage-2.1 record for every test-split event",
        "Only events with approved ground truth can be in the test split.",
    ),
    "MANIFEST_INVALID": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "MANIFEST_SCHEMA_INVALID": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "EVIDENCE_CLASSIFICATION_INVALID": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "SPLIT_INVALID": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "SPLIT_DUPLICATE_EVENT": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "SPLIT_LEAKAGE": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "EVENTS_MISSING": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "EVENT_RECORD_INVALID": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "DUPLICATE_EVENT_ID": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "EVENT_SPLIT_MISMATCH": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "SOURCE_HASH_INVALID": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "SOURCE_PATH_AMBIGUOUS": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "SOURCE_PATH_ESCAPE": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "SOURCE_MEDIA_ACCESS_DENIED": (
        INVALID_EVIDENCE,
        "a manifest whose sources are JSON replay-evidence payloads, never raw media",
        "Rebuild the manifest from verified JSON evidence; raw media is read only under a "
        "recorded AUTH-MEDIA-ACCESS, never by the evaluation input loader.",
    ),
    "SOURCE_SYMLINK_UNEXPECTED": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "DUPLICATE_SOURCE_IDENTITY": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "CAMERA_SCOPE_INVALID": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "SYNC_SCOPE_INVALID": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "INPUT_MISSING": (
        INVALID_EVIDENCE,
        "a valid data/manifests/phase12_evaluation_inputs.json (phase12-evaluation-inputs/1)",
        "Rebuild the manifest with evaluation.manifest_builder from the verified decisions.",
    ),
    "SOURCE_HASH_MISMATCH": (
        INTEGRITY_FAILURE,
        "an event source whose bytes equal the manifest's declared SHA-256",
        "The source changed after the manifest was pinned; re-pin and re-authorize, never edit "
        "the hash to match.",
    ),
    "EVENT_INPUT_INVALID": (
        INVALID_EVIDENCE,
        "an event source that is a JSON object",
        "Repair or regenerate the evidence payload, then rebuild and re-pin the manifest.",
    ),
    "SYNTHETIC_INPUTS_NOT_OFFICIAL": (
        NOT_OFFICIAL_EVIDENCE,
        "a manifest with evidence_classification 'real'",
        "Synthetic manifests can never satisfy official readiness.",
    ),
    "INPUT_MANIFEST_DECISION_MISMATCH": (
        INTEGRITY_FAILURE,
        "an input manifest whose split and camera scope equal the researcher decisions",
        "Rebuild the manifest from the decision artifacts; do not edit decisions to fit it.",
    ),
    "POLICY_CONFIG_OR_CHECKPOINT_INVALID": (
        INTEGRITY_FAILURE,
        "configs/frozen_experiment_v1.yaml, configs/decision_policy_v1.yaml, checkpoints",
        "Frozen artifacts must verify; they are never modified to pass.",
    ),
    "EVAL_AUTH_NOT_GRANTED": (
        AUTHORIZATION,
        "data/governance/eval_authorization.json",
        "A recorded EVAL-AUTH bound to the current evidence hashes. "
        "`python -m railway_detection evaluation status` prints live_bindings to bind. "
        "Chat statements and documents are recorded in docs but cannot be verified here.",
    ),
    "EVAL_AUTH_INVALID": (
        AUTHORIZATION,
        "data/governance/eval_authorization.json",
        "Fix the named field. Unknown keys such as 'ready' or 'approved' are refused.",
    ),
    "EVAL_AUTH_ATTESTATION_UNSUPPORTED": (
        AUTHORIZATION,
        "attestation.type RECORDED_RESEARCHER_STATEMENT with signature null",
        "No key infrastructure exists; signature-style attestations are not trusted.",
    ),
    "EVAL_AUTH_BINDING_MISMATCH": (
        AUTHORIZATION,
        "an EVAL-AUTH re-recorded against the current evidence",
        "Evidence changed after the statement was recorded; the authorization no longer applies.",
    ),
    "EVAL_AUTH_BINDING_UNVERIFIABLE": (
        DERIVED,
        "the missing or invalid prerequisite artifact",
        "Clears once the prerequisite blocker is resolved.",
    ),
}


# Category -> what kind of gap it is (a verifier defect is never expressed as a blocker: defects
# are fixed in code and listed in the implementation reports).
CAUSE_CLASS: dict[str, str] = {
    MISSING_HUMAN_EVIDENCE: "missing_artifact",
    MISSING_RESEARCH_DECISION: "undecided_decision",
    INVALID_EVIDENCE: "invalid_artifact",
    INTEGRITY_FAILURE: "integrity_failure",
    DERIVED: "derived",
    NOT_OFFICIAL_EVIDENCE: "non_official_evidence",
    AUTHORIZATION: "authorization_gap",
    UNCLASSIFIED: "unclassified",
}

_INSUFFICIENT_BY_CATEGORY: dict[str, str] = {
    MISSING_HUMAN_EVIDENCE: (
        "the required artifact does not exist; no chat statement or document can substitute "
        "for a machine-verifiable record"
    ),
    MISSING_RESEARCH_DECISION: (
        "no researcher-attributed decision record exists, and the software will not choose a "
        "scientific definition or assignment on the researcher's behalf"
    ),
    INVALID_EVIDENCE: (
        "the artifact exists but fails the documented verification rule in the evidence"
    ),
    INTEGRITY_FAILURE: "an integrity binding (hash, identity or cross-check) did not hold",
    DERIVED: "this follows from another blocker and cannot be cleared on its own",
    NOT_OFFICIAL_EVIDENCE: (
        "the evidence is classified as non-official and can never satisfy the gate"
    ),
    AUTHORIZATION: "no valid, evidence-bound recorded authorization exists for the current state",
}

_INSUFFICIENT_BY_CODE: dict[str, str] = {
    "LEGACY_OR_UNKNOWN_GROUND_TRUTH_SCHEMA": (
        "schema 6.0.0, blocklisted reviewer id, shared timestamp and superseded proposal: not a "
        "Stage-2.1 record, and the researcher disowned and ordered the invalidation of these files"
    ),
    "STAGE21_RECORDS_MISSING": (
        "zero 8.1.0-stage2.1 records exist; the researcher's statement that annotations were "
        "approved has no corresponding artifact"
    ),
    "EVAL_AUTH_NOT_GRANTED": (
        "the general authorization was given in conversation; a bindable record needs the split, "
        "R04, receipt and manifest that do not exist yet"
    ),
    "PREMATURE_OPENING_DEFINITION_UNDECIDED": (
        "protocol v9 and design M4 conflict and neither has a researcher-attributed acceptance"
    ),
}


@dataclass(frozen=True)
class ExecutionBlocker:
    code: str
    detail: str

    @property
    def cause_class(self) -> str:
        return CAUSE_CLASS[self.category]

    @property
    def insufficient_because(self) -> str:
        return _INSUFFICIENT_BY_CODE.get(
            self.code, _INSUFFICIENT_BY_CATEGORY.get(self.category, "unclassified blocker")
        )

    @property
    def category(self) -> str:
        return BLOCKER_CATALOGUE.get(self.code, (UNCLASSIFIED, "", ""))[0]

    @property
    def required_artifact(self) -> str:
        return BLOCKER_CATALOGUE.get(self.code, (UNCLASSIFIED, "", ""))[1]

    @property
    def remedy(self) -> str:
        return BLOCKER_CATALOGUE.get(self.code, (UNCLASSIFIED, "", ""))[2]

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "detail": self.detail,
            "verification_evidence": self.detail,
            "category": self.category,
            "cause_class": self.cause_class,
            "insufficient_because": self.insufficient_because,
            "required_artifact": self.required_artifact,
            "remedy": self.remedy,
        }


@dataclass(frozen=True)
class OfficialExecutionReadiness:
    ready: bool
    blockers: tuple[ExecutionBlocker, ...]
    evidence: tuple[str, ...] = ()
    authorization_attestation_level: str | None = None
    authorization_sha256: str | None = None
    live_bindings: dict[str, str | None] = field(default_factory=dict)
    # The protocol definitions an official run would apply (None until fully decided).
    protocol_profile: dict[str, str] | None = None
    # Review-record digests observed during this assessment (relative path -> SHA-256).
    review_record_sha256: dict[str, str] = field(default_factory=dict)

    @property
    def blocker_codes(self) -> tuple[str, ...]:
        return tuple(sorted({blocker.code for blocker in self.blockers}))

    @property
    def authorization_verified(self) -> bool:
        return self.authorization_attestation_level is not None

    def blockers_by_category(self) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = {}
        for blocker in self.blockers:
            grouped.setdefault(blocker.category, []).append(blocker.code)
        return {key: sorted(set(value)) for key, value in sorted(grouped.items())}

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "blockers": [blocker.to_dict() for blocker in self.blockers],
            "blocker_codes": list(self.blocker_codes),
            "blocker_count": len(self.blockers),
            "blockers_by_category": self.blockers_by_category(),
            "evidence": list(self.evidence),
            "authorization_verification_available": True,
            "authorization_verified": self.authorization_verified,
            "authorization_attestation_level": self.authorization_attestation_level,
            "authorization_is_cryptographic": False,
            "live_bindings": dict(sorted(self.live_bindings.items())),
            "protocol_profile": dict(sorted(self.protocol_profile.items()))
            if self.protocol_profile
            else None,
        }


@dataclass(frozen=True)
class _LoadedRecord:
    relative: str
    sha256: str
    data: dict[str, Any]


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _reviewer_of(record: dict[str, Any]) -> str:
    meta = record.get("reviewer_metadata")
    if isinstance(meta, dict) and isinstance(meta.get("reviewer_id"), str):
        return meta["reviewer_id"]
    value = record.get("reviewer_id")
    return value if isinstance(value, str) else "<none>"


def _read_repository_records(
    root: Path,
) -> tuple[list[_LoadedRecord], list[ExecutionBlocker]]:
    reviews_dir = root / "data/ground_truth/reviews"
    if not reviews_dir.is_dir():
        return [], [ExecutionBlocker("STAGE21_RECORDS_MISSING", f"missing {reviews_dir}")]
    records: list[_LoadedRecord] = []
    blockers: list[ExecutionBlocker] = []
    excused = notices_module.excused_legacy_records(reviews_dir)
    for bad in notices_module.invalid_notices(reviews_dir):
        blockers.append(
            ExecutionBlocker(
                "INVALIDATION_NOTICE_INVALID", f"{bad.notice}: {bad.problem}"
            )
        )
    record_paths = [
        p
        for p in sorted(reviews_dir.rglob("*_review.json"))
        if p.relative_to(reviews_dir).as_posix() not in excused
    ]
    if not record_paths:
        note = (
            f"; {len(excused)} legacy record(s) are invalidated by verified notices and are "
            "not counted"
            if excused
            else ""
        )
        blockers.append(
            ExecutionBlocker("STAGE21_RECORDS_MISSING", f"no active review records found{note}")
        )
    for path in record_paths:
        relative = path.relative_to(reviews_dir).as_posix()
        try:
            raw = path.read_bytes()
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError("must contain a JSON object")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            blockers.append(ExecutionBlocker("GROUND_TRUTH_RECORD_INVALID", f"{relative}: {exc}"))
            continue
        records.append(_LoadedRecord(relative, governance.sha256_bytes(raw), value))
    stage21 = [r for r in records if r.data.get("schema_version") == STAGE_2_1_SCHEMA_VERSION]
    if records and not stage21:
        versions: dict[str, int] = {}
        reviewers: set[str] = set()
        for item in records:
            version = str(item.data.get("schema_version"))
            versions[version] = versions.get(version, 0) + 1
            reviewers.add(_reviewer_of(item.data))
        blocked = sorted(r for r in reviewers if r.strip().lower() in REVIEWER_ID_BLOCKLIST)
        blockers.append(
            ExecutionBlocker(
                "STAGE21_RECORDS_MISSING",
                f"no {STAGE_2_1_SCHEMA_VERSION} records; found {len(records)} review "
                f"record(s) by schema_version {dict(sorted(versions.items()))}; "
                f"reviewer ids {sorted(reviewers)}"
                + (f" (blocklisted: {blocked})" if blocked else ""),
            )
        )
    return records, blockers


def _verify_decision_file(
    root: Path,
    relative: Path,
    *,
    schema: str,
    missing_code: str,
    invalid_code: str,
    allowlist: frozenset[str] | None,
    now: datetime,
    check_body: Any,
) -> tuple[dict[str, Any] | None, str | None, ExecutionBlocker | None]:
    if allowlist is None:
        # AUTHORITY_ALLOWLIST_UNAVAILABLE is reported once for all artifacts; an
        # absent artifact is still reported as missing.
        if not (root / relative).is_file():
            return None, None, ExecutionBlocker(missing_code, str(root / relative))
        return None, None, None
    try:
        verified = governance.verify_decision_file(
            root,
            relative,
            schema=schema,
            missing_code=missing_code,
            invalid_code=invalid_code,
            allowlist=allowlist,
            now=now,
            check_body=check_body,
        )
    except governance.GovernanceError as exc:
        return None, None, ExecutionBlocker(exc.code, exc.detail)
    return verified.payload, verified.sha256, None


def _policy_file_sha256(policy_file: Path) -> str:
    return governance.sha256_small_file(policy_file)


def _manifest_identity_blockers(
    root: Path, inputs: Any, approved_keys: set[str]
) -> list[ExecutionBlocker]:
    """A manifest may not vouch for its own identity, cohort or approval.

    ``evidence_classification: real`` is a self-declared label. What makes the events
    real is independent evidence: each manifest event must be a (cohort-qualified)
    entry of the annotation inventory with the same cohort, and each test-split event
    must have an approved, valid Stage-2.1 record for that identity.
    """
    found: list[ExecutionBlocker] = []
    inventory_path = root / receipt_module.DEFAULT_INVENTORY_RELATIVE
    inventory: dict[str, Any] | None = None
    try:
        raw = json.loads(inventory_path.read_text(encoding="utf-8"))
        inventory = raw if isinstance(raw, dict) else None
    except (OSError, json.JSONDecodeError):
        inventory = None
    if inventory is None:
        return [
            ExecutionBlocker(
                "ANNOTATION_INVENTORY_MISSING",
                f"{receipt_module.DEFAULT_INVENTORY_RELATIVE} is absent or unreadable; the "
                "manifest's event identities and cohorts cannot be checked independently",
            )
        ]
    unknown: list[str] = []
    wrong_cohort: list[str] = []
    for item in inputs.events:
        entry = inventory.get(item.event_id)
        if not isinstance(entry, dict):
            unknown.append(item.event_id)
        elif entry.get("category") != item.cohort or f"{item.cohort}/{entry.get('event_id')}" != (
            item.event_id
        ):
            wrong_cohort.append(item.event_id)
    if unknown:
        found.append(
            ExecutionBlocker(
                "MANIFEST_EVENT_NOT_IN_INVENTORY",
                f"{len(unknown)} manifest event(s) are not cohort-qualified inventory "
                f"entries: {sorted(unknown)[:5]}",
            )
        )
    if wrong_cohort:
        found.append(
            ExecutionBlocker(
                "MANIFEST_COHORT_MISMATCH",
                f"manifest cohort differs from the inventory for {sorted(wrong_cohort)[:5]}",
            )
        )
    if approved_keys:
        unapproved = sorted(set(inputs.partitions["test"]) - approved_keys)
        if unapproved:
            found.append(
                ExecutionBlocker(
                    "MANIFEST_TEST_EVENT_WITHOUT_APPROVED_RECORD",
                    f"test-split events without an approved Stage-2.1 record: {unapproved[:5]}",
                )
            )
    return found


def assess_official_phase12_readiness(
    repository_root: Path | str,
    *,
    config_path: Path | str = "configs/frozen_experiment_v1.yaml",
    policy_path: Path | str = "configs/decision_policy_v1.yaml",
    input_manifest_path: Path | str = "data/manifests/phase12_evaluation_inputs.json",
    now: datetime | None = None,
) -> OfficialExecutionReadiness:
    """Assess actual repository evidence; never accept asserted readiness flags."""
    root = Path(repository_root).resolve()
    now = now or datetime.now(UTC)
    blockers: list[ExecutionBlocker] = []
    evidence: list[str] = []
    bindings: dict[str, str | None] = dict.fromkeys(governance.EVAL_AUTH_BINDING_KEYS)

    try:
        allowlist: frozenset[str] | None = governance.load_allowlist(root)
    except governance.GovernanceError as exc:
        allowlist = None
        blockers.append(ExecutionBlocker(exc.code, exc.detail))

    # ---- Stage-2.1 ground truth -------------------------------------------------
    records, record_blockers = _read_repository_records(root)
    blockers.extend(record_blockers)
    excused_records = notices_module.excused_legacy_records(root / "data/ground_truth/reviews")
    if excused_records:
        evidence.append(
            f"{len(excused_records)} legacy review record(s) excluded: each has a verified "
            "invalidation notice (record unchanged, legacy schema); they are history, not "
            "ground truth, and satisfy no Stage-2.1 requirement"
        )
    # Parse and validate Stage-2.1 records without promotion-time validation,
    # which intentionally opens raw media. Promotion validation remains the
    # separately authorized readiness workflow; its outcome is consumed here
    # only through the hash-bound promotion receipt.
    approved_by_cohort: dict[str, int] = {}
    approved_keys: set[str] = set()
    approved_records: list[dict[str, Any]] = []
    record_level_problem = False
    for item in records:
        record = item.data
        event_id = str(record.get("event_id", "<unknown>"))
        if record.get("schema_version") != STAGE_2_1_SCHEMA_VERSION:
            record_level_problem = True
            reviewer = _reviewer_of(record)
            note = " [reviewer id is on REVIEWER_ID_BLOCKLIST]" if (
                reviewer.strip().lower() in REVIEWER_ID_BLOCKLIST
            ) else ""
            blockers.append(
                ExecutionBlocker(
                    "LEGACY_OR_UNKNOWN_GROUND_TRUTH_SCHEMA",
                    f"{item.relative} ({event_id}): schema_version "
                    f"{record.get('schema_version')!r}, reviewer {reviewer!r}{note}",
                )
            )
            continue
        try:
            built = build_stage2_1_record_from_dict(record)
        except (SchemaValidationError, TypeError, AttributeError, ValueError) as exc:
            record_level_problem = True
            blockers.append(
                ExecutionBlocker("GROUND_TRUTH_SCHEMA_INVALID", f"{item.relative}: {exc}")
            )
            continue
        if built.adjudication_status != "APPROVED":
            record_level_problem = True
            blockers.append(
                ExecutionBlocker(
                    "GROUND_TRUTH_NOT_APPROVED",
                    f"{item.relative}: {built.adjudication_status}",
                )
            )
            continue
        approved_records.append(record)
        if built.second_review_of is None:  # an independent second review is not a second event
            approved_by_cohort[built.cohort] = approved_by_cohort.get(built.cohort, 0) + 1
        approved_keys.add(f"{built.cohort}/{built.event_id}")
    # Mission 10 (WP10.1): the consumer repeats RD-043 second-review enforcement on the actual
    # records instead of trusting that the receipt producer did it. Metadata only.
    if approved_records and allowlist is not None:
        try:
            second_registry: dict[str, dict[str, str]] | None = readiness_cli.load_media_context(
                root / receipt_module.DEFAULT_INVENTORY_RELATIVE
            )[0]
        except readiness_cli.ReadinessCliError:
            second_registry = None
        second_findings, second_evidence = assess_second_reviews(
            approved_records,
            authorized_reviewers=allowlist,
            repository_root=root,
            media_sha256_registry=second_registry,
        )
        for finding in second_findings:
            blockers.append(
                ExecutionBlocker(finding.code, f"{finding.event_key}: {finding.detail}")
            )
        evidence.extend(second_evidence)
    for cohort, count in sorted(approved_by_cohort.items()):
        evidence.append(f"approved_stage21_records[{cohort}]={count}")
    for cohort in ("train_events", "no_train_events", "engine_events"):
        if approved_by_cohort.get(cohort, 0) == 0:
            blockers.append(
                ExecutionBlocker("COHORT_APPROVAL_MISSING", f"no approved {cohort} record")
            )

    receipt_sha: str | None = None
    receipt_stage: str | None = None
    if records and not record_level_problem and allowlist is not None:
        record_hashes = {item.relative: item.sha256 for item in records}
        try:
            receipt = governance.verify_promotion_receipt(
                root,
                review_record_sha256=record_hashes,
                live_inputs=receipt_module.live_receipt_inputs(
                    inventory=root / receipt_module.DEFAULT_INVENTORY_RELATIVE,
                    proposals_dir=root / receipt_module.DEFAULT_PROPOSALS_RELATIVE,
                    allowlist=root / receipt_module.DEFAULT_ALLOWLIST_RELATIVE,
                ),
                now=now,
            )
            receipt_sha = receipt.sha256
            receipt_stage = str(receipt.payload["stage"])
            evidence.append(f"stage2.1 promotion receipt verified: {receipt.sha256}")
        except governance.GovernanceError as exc:
            blockers.append(ExecutionBlocker(exc.code, exc.detail))
    bindings["stage21_promotion_receipt_sha256"] = receipt_sha

    # ---- Researcher decision artifacts ------------------------------------------
    split_payload, split_sha, split_blocker = _verify_decision_file(
        root,
        governance.SPLIT_DECISION_RELATIVE,
        schema=governance.SPLIT_DECISION_SCHEMA,
        missing_code="EVENT_SPLIT_DECISION_MISSING",
        invalid_code="EVENT_SPLIT_DECISION_INVALID",
        allowlist=allowlist,
        now=now,
        check_body=governance.check_split_body,
    )
    if split_blocker:
        blockers.append(split_blocker)
    bindings["event_split_decision_sha256"] = split_sha

    r04_payload, r04_sha, r04_blocker = _verify_decision_file(
        root,
        governance.R04_DECISION_RELATIVE,
        schema=governance.R04_DECISION_SCHEMA,
        missing_code="R04_SCOPE_DECISION_MISSING",
        invalid_code="R04_SCOPE_DECISION_INVALID",
        allowlist=allowlist,
        now=now,
        check_body=governance.check_r04_body,
    )
    if r04_blocker:
        blockers.append(r04_blocker)
    bindings["r04_scope_decision_sha256"] = r04_sha
    if r04_payload is not None and r04_payload["accepted_sync_events"]:
        supported = governance.calibration_supported_events(root)
        unsupported = sorted(
            set(r04_payload["accepted_sync_events"]) - (supported or set())
        )
        if unsupported:
            blockers.append(
                ExecutionBlocker(
                    "R04_ACCEPTED_EVENT_NOT_SUPPORTED",
                    "accepted_sync_events without a CALIBRATION_SUPPORTED entry in "
                    f"{governance.CALIBRATION_MANIFEST_RELATIVE}: {unsupported[:5]}",
                )
            )

    # The documented protocol profile applies unless the researcher recorded a valid,
    # implementable override. The binding is the digest of what will actually run.
    protocol_profile_digest: str | None = None
    effective: dict[str, str] | None = None
    overrides: dict[str, Any] | None = None
    override_ok = True
    if allowlist is not None:
        try:
            override = governance.verify_protocol_override(root, allowlist=allowlist, now=now)
            overrides = override.payload["choices"] if override is not None else None
        except governance.GovernanceError as exc:
            override_ok = False
            blockers.append(ExecutionBlocker(exc.code, exc.detail))
    elif (root / governance.PROTOCOL_DECISION_RELATIVE).is_file():
        override_ok = False  # AUTHORITY_ALLOWLIST_UNAVAILABLE already explains this
    if override_ok:
        try:
            profile = protocol_choices.effective_profile(overrides)
            effective = profile
            protocol_profile_digest = protocol_choices.profile_sha256(profile)
            evidence.append(
                "protocol profile "
                + ("(researcher override)" if overrides else "(documented, no override)")
                + f": {protocol_profile_digest}"
            )
        except protocol_choices.ProtocolChoiceError as exc:
            blockers.append(ExecutionBlocker(exc.code, exc.detail))
    bindings["protocol_profile_sha256"] = protocol_profile_digest

    # ---- Frozen configuration, policy, checkpoints ------------------------------
    try:
        config_file = Path(config_path)
        if not config_file.is_absolute():
            config_file = root / config_file
        config = load_frozen_config(config_file)
        verify_checkpoint_integrity(config, repo_root=root)
        verify_timing_safeguards(config)
        policy_file = Path(policy_path)
        if not policy_file.is_absolute():
            policy_file = root / policy_file
        policy = yaml.safe_load(policy_file.read_text(encoding="utf-8"))
        if not isinstance(policy, dict) or not isinstance(policy.get("policy_metadata"), dict):
            raise ValueError("decision policy metadata is missing")
        policy_metadata = policy["policy_metadata"]
        declared = policy_metadata.get("reference_frozen_config_sha256")
        if declared != config.config_hash:
            raise ValueError(
                "decision policy frozen-config reference mismatch: "
                f"expected {config.config_hash}, got {declared!r}"
            )
        if not re.fullmatch(r"[0-9a-f]{64}", config.config_hash):
            raise ValueError("computed frozen config hash is invalid")
        bindings["frozen_config_sha256"] = config.config_hash
        bindings["decision_policy_sha256"] = _policy_file_sha256(policy_file)
        evidence.append(f"frozen config canonical SHA-256 verified: {config.config_hash}")
        evidence.append(f"decision policy SHA-256: {bindings['decision_policy_sha256']}")
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        ConfigurationIntegrityError,
        CheckpointIntegrityError,
    ) as exc:
        blockers.append(ExecutionBlocker("POLICY_CONFIG_OR_CHECKPOINT_INVALID", str(exc)))

    # ---- Input manifest (metadata only) -----------------------------------------
    try:
        manifest_path = Path(input_manifest_path)
        if not manifest_path.is_absolute():
            manifest_path = root / manifest_path
        inputs = load_evaluation_input_manifest(manifest_path, verify_sources=False)
        if inputs.evidence_classification.value != "real":
            blockers.append(
                ExecutionBlocker(
                    "SYNTHETIC_INPUTS_NOT_OFFICIAL",
                    "synthetic input manifest cannot satisfy official readiness",
                )
            )
        else:
            bindings["input_manifest_sha256"] = inputs.manifest_sha256
            blockers.extend(_manifest_identity_blockers(root, inputs, approved_keys))
        evidence.append(f"real input manifest hash verified: {inputs.manifest_sha256}")
        if split_payload is not None:
            decided = {
                role: tuple(ids) for role, ids in split_payload["partitions"].items()
            }
            if decided != inputs.partitions:
                blockers.append(
                    ExecutionBlocker(
                        "INPUT_MANIFEST_DECISION_MISMATCH",
                        "manifest partitions differ from the researcher's split decision",
                    )
                )
        if r04_payload is not None:
            if (
                dict(inputs.camera_scope_by_event) != dict(r04_payload["event_modes"])
                or set(inputs.accepted_sync_events) != set(r04_payload["accepted_sync_events"])
            ):
                blockers.append(
                    ExecutionBlocker(
                        "INPUT_MANIFEST_DECISION_MISMATCH",
                        "manifest camera scope differs from the researcher's R04 decision",
                    )
                )
    except EvaluationInputError as exc:
        blockers.append(ExecutionBlocker(exc.code, exc.detail))

    # ---- EVAL-AUTH ---------------------------------------------------------------
    attestation_level: str | None = None
    authorization_sha: str | None = None
    if allowlist is None:
        # The allowlist blocker explains why a present record cannot be verified;
        # an absent record is still reported as not granted.
        if not (root / governance.EVAL_AUTH_RELATIVE).is_file():
            blockers.append(
                ExecutionBlocker(
                    "EVAL_AUTH_NOT_GRANTED",
                    f"no recorded EVAL-AUTH at {governance.EVAL_AUTH_RELATIVE}",
                )
            )
    else:
        try:
            verified = governance.verify_eval_authorization(
                root,
                allowlist=allowlist,
                live_bindings=bindings,
                promotion_stage=receipt_stage,
                now=now,
            )
            attestation_level = verified.attestation_level
            authorization_sha = verified.artifact.sha256
            evidence.append(
                "EVAL-AUTH verified as a "
                f"{verified.attestation_level} (recorded_by={verified.recorded_by_kind}); "
                "not a cryptographic attestation"
            )
        except governance.GovernanceError as exc:
            blockers.append(ExecutionBlocker(exc.code, exc.detail))

    unique: dict[tuple[str, str], ExecutionBlocker] = {
        (item.code, item.detail): item for item in blockers
    }
    ordered = tuple(sorted(unique.values(), key=lambda item: (item.code, item.detail)))
    ready = not ordered
    return OfficialExecutionReadiness(
        ready=ready,
        blockers=ordered,
        evidence=tuple(sorted(evidence)),
        authorization_attestation_level=attestation_level,
        authorization_sha256=authorization_sha,
        live_bindings=bindings,
        protocol_profile=effective,
        review_record_sha256={item.relative: item.sha256 for item in records},
    )
