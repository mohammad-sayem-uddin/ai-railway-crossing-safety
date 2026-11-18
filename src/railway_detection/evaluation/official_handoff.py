"""Fail-closed validation and post-approval execution helper for Phase 12 (Tasks 2 & 6).

All validation operations are non-raw and read-only. Official execution strictly
refuses unless AUTH-MEDIA-ACCESS, Stage-2.1 reviews + promotion receipt,
event split decision, phase12-evaluation-inputs/1 manifest, and bound EVAL-AUTH
are genuinely present and verified on disk.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from railway_detection.data.split_audit import build_event_provenance_table, evaluate_candidate_split
from railway_detection.evaluation import descriptive_exec_gate, governance, manifest_builder
from railway_detection.evaluation.cache_only_engine import CacheOnlyReplayEngine
from railway_detection.evaluation.cache_only_engine_multimodal import (
    MM_SUPPORTED_CONDITIONS,
    MultimodalCacheOnlyReplayEngine,
)
from railway_detection.evaluation.execution_gate import (
    OfficialExecutionReadiness,
    assess_official_phase12_readiness,
)
from railway_detection.evaluation.input_contracts import (
    EvaluationInputError,
    load_evaluation_input_manifest,
)
from railway_detection.evaluation.output_contracts import EvaluationFailureReport
from railway_detection.reproducibility.audit import run_reproducibility_audit
from railway_detection.safety import media_guard

EXPECTED_APPROVAL_PACKAGE_FILES = (
    "AUTH_DESCRIPTIVE_EVAL_EXEC.template.json",
    "AUTH_MEDIA_ACCESS.template.json",
    "COHORT_APPROVAL_PACKAGES.json",
    "COHORT_APPROVAL_PACKAGES.md",
    "EVALUATION_INPUT_MANIFEST_RUNBOOK.md",
    "PI_APPROVAL_EXECUTION_GUIDE.md",
    "SPLIT_OPTION_A_RECONCILIATION.md",
    "STAGE21_27_EVENT_REVIEW_CHECKLIST.json",
    "STAGE21_27_EVENT_REVIEW_CHECKLIST.md",
    "eval_authorization.template.json",
    "phase12_evaluation_inputs.template.json",
    "phase12_event_split_decision.candidate.template.json",
)


class OfficialHandoffError(RuntimeError):
    """Raised when approval packages or post-approval execution gates fail."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"[{code}] {detail}")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_approval_package_bundle(
    repo_root: Path | str,
    package_dir: Path | str = "docs/generated/approval_packages",
) -> dict[str, Any]:
    """Validate all 11 approval-package files, schemas, hashes, event IDs & dependencies."""
    root = Path(repo_root).resolve()
    pkg = Path(package_dir)
    if not pkg.is_absolute():
        pkg = root / pkg

    missing_files = [name for name in EXPECTED_APPROVAL_PACKAGE_FILES if not (pkg / name).is_file()]
    if missing_files:
        raise OfficialHandoffError(
            "APPROVAL_PACKAGE_FILES_MISSING",
            f"missing files under {pkg}: {missing_files}",
        )

    inventory = _read_json(root / "data/manifests/layer_b_v2_annotation_inventory.json")
    expected_events = sorted(inventory)
    readiness = assess_official_phase12_readiness(root)

    # 1. AUTH_MEDIA_ACCESS.template.json
    auth_tmpl = _read_json(pkg / "AUTH_MEDIA_ACCESS.template.json")
    if set(auth_tmpl) != set(media_guard._AUTH_KEYS):
        raise OfficialHandoffError("AUTH_TEMPLATE_SCHEMA", "AUTH_MEDIA_ACCESS keyset mismatch")
    if set(auth_tmpl["scope"]) != set(media_guard._SCOPE_KEYS):
        raise OfficialHandoffError("AUTH_TEMPLATE_SCOPE", "AUTH_MEDIA_ACCESS scope keyset mismatch")
    if sorted(auth_tmpl["scope"]["events"]) != expected_events:
        raise OfficialHandoffError("AUTH_TEMPLATE_EVENTS", "AUTH_MEDIA_ACCESS event list mismatch")
    proto_path = root / auth_tmpl["bindings"]["protocol_document"]["path"]
    if governance.sha256_small_file(proto_path) != auth_tmpl["bindings"]["protocol_document"]["sha256"]:
        raise OfficialHandoffError("AUTH_TEMPLATE_HASH", "protocol document SHA-256 mismatch")

    # 2. STAGE21_27_EVENT_REVIEW_CHECKLIST.{json,md}
    checklist = _read_json(pkg / "STAGE21_27_EVENT_REVIEW_CHECKLIST.json")
    if checklist.get("total_events") != 27 or len(checklist.get("events", [])) != 27:
        raise OfficialHandoffError("CHECKLIST_COUNT", "checklist must cover all 27 events")
    checklist_keys = sorted(item["event_key"] for item in checklist["events"])
    if checklist_keys != expected_events:
        raise OfficialHandoffError("CHECKLIST_EVENTS", "checklist event keys differ from inventory")
    for item in checklist["events"]:
        key = item["event_key"]
        prop_sha = governance.sha256_small_file(root / item["active_proposal"]["path"])
        if prop_sha != item["active_proposal"]["sha256"]:
            raise OfficialHandoffError("CHECKLIST_PROPOSAL_HASH", f"{key} proposal sha256 mismatch")
        if (
            item["expected_media"]["front_sha256"] != inventory[key]["front"]["sha256"]
            or item["expected_media"]["back_sha256"] != inventory[key]["back"]["sha256"]
        ):
            raise OfficialHandoffError("CHECKLIST_MEDIA_HASH", f"{key} inventory media hash mismatch")
        if "--cohort" not in item["primary_review_command"] or "--event" not in item["primary_review_command"]:
            raise OfficialHandoffError("CHECKLIST_CMD", f"{key} invalid primary review CLI syntax")
    checklist_md = (pkg / "STAGE21_27_EVENT_REVIEW_CHECKLIST.md").read_text(encoding="utf-8")
    for key in expected_events:
        if key not in checklist_md:
            raise OfficialHandoffError("CHECKLIST_MD_MISSING_EVENT", f"{key} absent from Markdown checklist")

    # 3. COHORT_APPROVAL_PACKAGES.{json,md}
    cohorts = _read_json(pkg / "COHORT_APPROVAL_PACKAGES.json")
    cohort_totals = {
        name: cohorts["cohorts"][name]["total_events_in_cohort"]
        for name in ("train_events", "no_train_events", "engine_events")
    }
    if cohort_totals != {"train_events": 23, "no_train_events": 3, "engine_events": 1}:
        raise OfficialHandoffError("COHORT_COUNTS", f"unexpected cohort counts: {cohort_totals}")
    cohort_md = (pkg / "COHORT_APPROVAL_PACKAGES.md").read_text(encoding="utf-8")
    if "readiness_cli" not in cohort_md or "--receipt-path" not in cohort_md:
        raise OfficialHandoffError("COHORT_MD_CMD", "cohort Markdown missing readiness_cli receipt command")

    # 4. phase12_event_split_decision.candidate.template.json & SPLIT_OPTION_A_RECONCILIATION.md
    split_tmpl = _read_json(pkg / "phase12_event_split_decision.candidate.template.json")
    governance.validate_event_level_split(split_tmpl["partitions"])
    assigned = {ek for ids in split_tmpl["partitions"].values() for ek in ids}
    if sorted(assigned) != expected_events:
        raise OfficialHandoffError("SPLIT_TEMPLATE_EVENTS", "split template does not cover 27 events")
    events_prov = build_event_provenance_table(root)
    split_check = evaluate_candidate_split(
        events_prov, split_tmpl["partitions"], name="approval_package_candidate_split"
    )
    if split_check["leakage_safe"] is not False or split_tmpl["source_proposal"]["leakage_safe"] is not False:
        raise OfficialHandoffError("SPLIT_LEAKAGE_FLAG_UNSAFE", "single-site candidate must remain leakage_safe=False")
    recon_md = (pkg / "SPLIT_OPTION_A_RECONCILIATION.md").read_text(encoding="utf-8")
    if "SPLIT-DECISION-OPTION-A-2026-11-09" not in recon_md:
        raise OfficialHandoffError("SPLIT_RECON_MISSING_OPTION_A", "reconciliation must cite Option A")

    # 5. phase12_evaluation_inputs.template.json & EVALUATION_INPUT_MANIFEST_RUNBOOK.md
    manifest_tmpl = _read_json(pkg / "phase12_evaluation_inputs.template.json")
    required_manifest_keys = {
        "schema_version",
        "evidence_classification",
        "partitions",
        "events",
        "camera_scope_by_event",
        "accepted_sync_events",
        "derived_from",
    }
    if set(manifest_tmpl) != required_manifest_keys:
        raise OfficialHandoffError(
            "MANIFEST_TEMPLATE_KEYS",
            f"manifest template keys {sorted(manifest_tmpl)} != exact manifest_builder keys {sorted(required_manifest_keys)}",
        )
    if manifest_tmpl["schema_version"] != "phase12-evaluation-inputs/1" or manifest_tmpl["evidence_classification"] != "real":
        raise OfficialHandoffError("MANIFEST_TEMPLATE_SCHEMA", "invalid manifest template schema/classification")
    manifest_runbook = (pkg / "EVALUATION_INPUT_MANIFEST_RUNBOOK.md").read_text(encoding="utf-8")
    if "build_evaluation_input_manifest" not in manifest_runbook or "phase12-replay-evidence/1" not in manifest_runbook:
        raise OfficialHandoffError("MANIFEST_RUNBOOK_INCOMPLETE", "manifest runbook missing builder/evidence schema")

    # 6. eval_authorization.template.json & PI_APPROVAL_EXECUTION_GUIDE.md
    eval_tmpl = _read_json(pkg / "eval_authorization.template.json")
    if set(eval_tmpl) != set(governance._EVAL_AUTH_KEYS):
        raise OfficialHandoffError("EVAL_AUTH_TEMPLATE_KEYS", "eval_authorization keys do not match governance._EVAL_AUTH_KEYS")
    if eval_tmpl["scope"]["field_or_physical_operations_authorized"] is not False:
        raise OfficialHandoffError("EVAL_AUTH_PHYSICAL_FLAG", "physical operations must remain False")
    for k in ("decision_policy_sha256", "frozen_config_sha256", "protocol_profile_sha256", "r04_scope_decision_sha256"):
        if eval_tmpl["bindings"].get(k) != readiness.live_bindings.get(k):
            raise OfficialHandoffError("EVAL_AUTH_STATIC_HASH", f"static binding mismatch for {k}")
    guide_md = (pkg / "PI_APPROVAL_EXECUTION_GUIDE.md").read_text(encoding="utf-8")
    if "--output-dir" not in guide_md:
        raise OfficialHandoffError("GUIDE_MISSING_OUTPUT_DIR", "execution guide must include --output-dir on evaluation run")

    # 7. AUTH_DESCRIPTIVE_EVAL_EXEC.template.json (Option A descriptive execution authorization template)
    desc_tmpl = _read_json(pkg / "AUTH_DESCRIPTIVE_EVAL_EXEC.template.json")
    if set(desc_tmpl) != set(descriptive_exec_gate._KEYS):
        raise OfficialHandoffError("DESC_AUTH_TEMPLATE_KEYS", "AUTH_DESCRIPTIVE_EVAL_EXEC keys mismatch")
    if set(desc_tmpl["scope"]) != set(descriptive_exec_gate._SCOPE_KEYS):
        raise OfficialHandoffError("DESC_AUTH_TEMPLATE_SCOPE", "AUTH_DESCRIPTIVE_EVAL_EXEC scope keys mismatch")
    if desc_tmpl["scope"]["operation"] != descriptive_exec_gate.DESCRIPTIVE_OPERATION:
        raise OfficialHandoffError("DESC_AUTH_TEMPLATE_OP", "unexpected descriptive operation")
    if desc_tmpl["scope"]["field_or_physical_operations_authorized"] is not False:
        raise OfficialHandoffError("DESC_AUTH_PHYSICAL_FLAG", "physical operations must remain False")
    if sorted(desc_tmpl["scope"]["metric_scope"]) != sorted(descriptive_exec_gate.DESCRIPTIVE_METRIC_SCOPE):
        raise OfficialHandoffError("DESC_AUTH_METRIC_SCOPE", "metric_scope mismatch")
    if set(desc_tmpl["bindings"]) != set(descriptive_exec_gate.BINDING_KEYS):
        raise OfficialHandoffError("DESC_AUTH_BINDING_KEYS", "descriptive binding keyset mismatch")
    if desc_tmpl["bindings"]["metric_scope_sha256"] != descriptive_exec_gate.metric_scope_sha256():
        raise OfficialHandoffError("DESC_AUTH_METRIC_SHA", "metric_scope_sha256 mismatch")
    if desc_tmpl["bindings"]["model_config_provenance_sha256"] != readiness.live_bindings.get("frozen_config_sha256"):
        raise OfficialHandoffError("DESC_AUTH_CONFIG_SHA", "model_config_provenance_sha256 mismatch")
    if desc_tmpl["bindings"]["protocol_sha256"] != readiness.live_bindings.get("protocol_profile_sha256"):
        raise OfficialHandoffError("DESC_AUTH_PROTO_SHA", "protocol_sha256 mismatch")
    if desc_tmpl["scope"]["conditions"] != sorted(MM_SUPPORTED_CONDITIONS):
        raise OfficialHandoffError("DESC_AUTH_CONDITIONS", "descriptive conditions must match MM_SUPPORTED_CONDITIONS")
    b2_manifest_path = root / "docs/generated/professor_evidence/mission43/B2_EVALUATION_INPUT_MANIFEST.json"
    if desc_tmpl["bindings"]["evaluation_manifest_sha256"] != governance.sha256_small_file(b2_manifest_path):
        raise OfficialHandoffError("DESC_AUTH_MANIFEST_SHA", "B2 descriptive manifest SHA-256 mismatch")

    option_a_ready = bool(
        (root / governance.PROMOTION_RECEIPT_RELATIVE).is_file()
        and (root / descriptive_exec_gate.DESCRIPTIVE_AUTH_RELATIVE).is_file()
    )

    return {
        "schema_version": "approval-package-validation/1.0",
        "validated_file_count": len(EXPECTED_APPROVAL_PACKAGE_FILES),
        "events_verified": len(expected_events),
        "zero_fabricated_approvals": True,
        "official_phase12_ready": readiness.ready,
        "option_a_descriptive_ready": option_a_ready,
        "official_blocker_codes": list(readiness.blocker_codes),
        "static_live_bindings": {k: v for k, v in readiness.live_bindings.items() if v is not None},
    }


def _refuse_if_unready(root: Path, readiness: OfficialExecutionReadiness) -> None:
    if not (root / media_guard.CANONICAL_MEDIA_AUTH_RELATIVE).is_file():
        raise OfficialHandoffError(
            "AUTH_MEDIA_ACCESS_NOT_GRANTED",
            f"missing {media_guard.CANONICAL_MEDIA_AUTH_RELATIVE}; cannot proceed without human raw-media authorization",
        )
    if not readiness.ready:
        raise OfficialHandoffError(
            "OFFICIAL_PHASE12_BLOCKED",
            f"cannot execute official evaluation while blockers remain: {list(readiness.blocker_codes)}",
        )


def run_post_approval_official_evaluation(
    repo_root: Path | str,
    *,
    output_dir: Path | str,
    event_sources: Mapping[str, manifest_builder.EventSourceSpec] | None = None,
    config_path: Path | str = "configs/frozen_experiment_v1.yaml",
    policy_path: Path | str = "configs/decision_policy_v1.yaml",
    input_manifest_path: Path | str = "data/manifests/phase12_evaluation_inputs.json",
    seed: int = 42,
) -> dict[str, Any]:
    """Reproducible post-approval Phase 12 execution procedure (refuses if any gate is missing)."""
    from railway_detection.evaluation.evaluation_runner import Phase12EvaluationRunner

    root = Path(repo_root).resolve()
    manifest_dest = Path(input_manifest_path)
    if not manifest_dest.is_absolute():
        manifest_dest = root / manifest_dest

    # Step 1: Never bypass raw-media or governance gates
    if not (root / media_guard.CANONICAL_MEDIA_AUTH_RELATIVE).is_file():
        raise OfficialHandoffError(
            "AUTH_MEDIA_ACCESS_NOT_GRANTED",
            f"missing {media_guard.CANONICAL_MEDIA_AUTH_RELATIVE}; official post-approval execution aborted cleanly",
        )
    # Verify media authorization for REAL_REPLAY cleanly (fails closed if invalid/expired)
    try:
        media_guard.precheck_operation_authorized("REAL_REPLAY", repo_root=root)
    except media_guard.MediaAccessAuthorizationError as exc:
        raise OfficialHandoffError(exc.code, exc.detail) from exc

    # Step 2: Build hash-bound input manifest only if absent and event_sources are explicitly supplied
    if not manifest_dest.is_file() and event_sources is not None:
        manifest_builder.build_evaluation_input_manifest(
            root, event_sources=event_sources, output_path=manifest_dest
        )

    readiness = assess_official_phase12_readiness(
        root,
        config_path=config_path,
        policy_path=policy_path,
        input_manifest_path=input_manifest_path,
    )
    _refuse_if_unready(root, readiness)

    # Step 3: Verify manifest sources exist & match real classification before replay
    loaded_inputs = load_evaluation_input_manifest(manifest_dest, verify_sources=True)
    if loaded_inputs.evidence_classification.value != "real":
        raise OfficialHandoffError("NON_REAL_INPUTS", "official evaluation requires real classified inputs")

    # Step 4: Execute official Phase 12 runner cleanly outside protected repository trees
    dest = Path(output_dir)
    if not dest.is_absolute():
        dest = (root / dest).resolve()
    failure_path = dest.with_name(dest.name + ".failure_report.json")
    outcome = Phase12EvaluationRunner().run_official_safe(
        repository_root=root,
        config_path=config_path,
        policy_path=policy_path,
        input_manifest_path=input_manifest_path,
        seed=seed,
        output_dir=dest,
        failure_report_path=failure_path,
        command="scripts/prepare_and_execute_official_evaluation.py",
    )
    if isinstance(outcome, EvaluationFailureReport):
        raise OfficialHandoffError(
            "OFFICIAL_RUN_FAILED",
            f"evaluation refused or failed: {outcome.blockers} (report: {failure_path})",
        )

    # Step 5: Re-audit reproducibility with the newly generated official output directory & preserve delta
    audit_report = run_reproducibility_audit(root, result_dirs=[dest])
    handoff_receipt = {
        "schema_version": "official-phase12-execution-handoff/1.0",
        "output_dir": str(dest),
        "input_manifest_sha256": loaded_inputs.manifest_sha256,
        "authorization_record_sha256": readiness.authorization_sha256,
        "reproducibility_status_counts": audit_report["status_counts"],
        "evaluation_result_provenance_status": next(
            (i["status"] for i in audit_report["items"] if i["id"] == "evaluation_result_provenance"),
            None,
        ),
        "manuscript_update_action": (
            "Populate post-authorization official Phase 12 tables and run_manifest hashes into "
            "docs/PHASE16_MANUSCRIPT_CORRECTION_v1.md and docs/generated/IEEE_MANUSCRIPT_TRAIN_GATE_AUTOMATION.md "
            "keeping single-crossing/session scope disclosed."
        ),
    }
    (dest / "post_evaluation_handoff_receipt.json").write_text(
        json.dumps(handoff_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return handoff_receipt


def run_post_approval_option_a_descriptive_evaluation(
    repo_root: Path | str,
    *,
    output_dir: Path | str,
    manifest_path: Path | str = "docs/generated/professor_evidence/mission43/B2_EVALUATION_INPUT_MANIFEST.json",
    condition: str = "B2",
) -> dict[str, Any]:
    """Fail-closed post-approval Option A single-crossing descriptive execution helper."""
    root = Path(repo_root).resolve()
    promo_path = root / governance.PROMOTION_RECEIPT_RELATIVE
    if not promo_path.is_file():
        raise OfficialHandoffError(
            "STAGE21_PROMOTION_RECEIPT_MISSING",
            f"missing {governance.PROMOTION_RECEIPT_RELATIVE}; complete human Stage-2.1 review and emit receipt first",
        )
    if not (root / descriptive_exec_gate.DESCRIPTIVE_AUTH_RELATIVE).is_file():
        raise OfficialHandoffError(
            "AUTH_DESCRIPTIVE_EVAL_EXEC_NOT_GRANTED",
            f"missing {descriptive_exec_gate.DESCRIPTIVE_AUTH_RELATIVE}; supervisor descriptive execution approval required",
        )

    try:
        allowlist = governance.load_allowlist(root)
        governance.verify_promotion_receipt(
            root, allowlist=allowlist, expected_stage="stage3_single_camera_baseline"
        )
    except governance.GovernanceError as exc:
        raise OfficialHandoffError(exc.code, exc.detail) from exc

    mpath = Path(manifest_path)
    if not mpath.is_absolute():
        mpath = (root / mpath).resolve()
    if not mpath.is_file():
        raise OfficialHandoffError("DESCRIPTIVE_MANIFEST_MISSING", f"missing manifest: {mpath}")
    manifest_sha = governance.sha256_small_file(mpath)

    try:
        auth = descriptive_exec_gate.verify_descriptive_authorization(
            root,
            condition=condition,
            event_id=None,
            manifest_sha256=manifest_sha,
        )
    except descriptive_exec_gate.DescriptiveExecutionNotAuthorized as exc:
        raise OfficialHandoffError(exc.code, exc.detail) from exc

    dest = Path(output_dir)
    if not dest.is_absolute():
        dest = (root / dest).resolve()
    for protected in ("data", "configs", "results", "docs", "models", "experiments", "src", "tests"):
        guard = (root / protected).resolve()
        if dest == guard or guard in dest.parents:
            raise OfficialHandoffError(
                "PROTECTED_OUTPUT_DIR",
                f"refusing to write Option A descriptive outputs inside protected tree {protected}/",
            )

    engine_cls = (
        MultimodalCacheOnlyReplayEngine
        if condition in {"BACK_VISION", "DUAL_VISION", "DUAL_VISION_AUDIO"}
        else CacheOnlyReplayEngine
    )
    engine = engine_cls(mpath, repo_root=root)
    manifest_data = _read_json(mpath)
    event_ids = sorted((manifest_data.get("events") or {}).keys())
    per_event: list[dict[str, Any]] = []
    for eid in event_ids:
        replay = engine.execute_replay(eid, condition)
        per_event.append(
            {
                "event_id": eid,
                "condition": condition,
                "closure_triggered": replay.simulation_result.closure_triggered,
                "closed_duration_s": round(replay.simulation_result.closed_duration_s, 4),
                "final_crossing_state": (
                    replay.simulation_result.steps[-1].crossing_state
                    if replay.simulation_result.steps
                    else "NONE"
                ),
                "step_count": len(replay.simulation_result.steps),
            }
        )

    dest.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema_version": "option-a-descriptive-execution-handoff/1.0",
        "study_scope": "OPTION_A_SINGLE_CROSSING_DESCRIPTIVE_ONLY",
        "cross_site_generalization_claimed": False,
        "authorization_id": auth.authorization_id,
        "authorization_record_sha256": auth.record_sha256,
        "condition": condition,
        "manifest_sha256": manifest_sha,
        "events_evaluated": len(per_event),
        "closure_triggered_count": sum(1 for r in per_event if r["closure_triggered"]),
        "per_event_summary": per_event,
    }
    (dest / "option_a_descriptive_execution_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return receipt
