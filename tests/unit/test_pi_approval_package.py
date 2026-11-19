"""Tests for deterministic PI human-approval preparation packages (non-raw)."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from railway_detection.evaluation import descriptive_exec_gate, governance
from railway_detection.evaluation.cache_only_engine_multimodal import MM_SUPPORTED_CONDITIONS
from railway_detection.evaluation.execution_gate import assess_official_phase12_readiness
from railway_detection.safety import media_guard

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from prepare_pi_approval_package import HUMAN_PLACEHOLDER, build_pi_approval_packages  # noqa: E402


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_repo_has_zero_fabricated_approvals_or_reviews() -> None:
    assert not (REPO_ROOT / media_guard.CANONICAL_MEDIA_AUTH_RELATIVE).exists()
    assert not (REPO_ROOT / governance.PROMOTION_RECEIPT_RELATIVE).exists()
    assert not (REPO_ROOT / governance.SPLIT_DECISION_RELATIVE).exists()
    assert not (REPO_ROOT / governance.EVAL_AUTH_RELATIVE).exists()
    assert not (REPO_ROOT / descriptive_exec_gate.DESCRIPTIVE_AUTH_RELATIVE).exists()
    assert not (REPO_ROOT / "data/manifests/phase12_evaluation_inputs.json").exists()


def test_prepare_pi_approval_packages_matches_checked_in_artifacts_and_schemas(
    tmp_path: Path,
) -> None:
    out = tmp_path / "pkg"
    summary = build_pi_approval_packages(REPO_ROOT, out)
    assert summary["total_events_in_checklist"] == 27
    assert summary["authorized_reviewers"] == ["elaf85777@gmail.com", "raihankabirrahu@gmail.com"]

    checked_in = REPO_ROOT / "docs/generated/approval_packages"
    for fname in summary["files_written"]:
        assert (checked_in / fname).read_text(encoding="utf-8") == (out / fname).read_text(
            encoding="utf-8"
        ), f"Drift in checked-in approval package file: {fname}"

    checklist = _load(out / "STAGE21_27_EVENT_REVIEW_CHECKLIST.json")
    assert checklist["generated_without_raw_media_access"] is True
    assert checklist["total_events"] == 27
    assert len({e["event_key"] for e in checklist["events"]}) == 27

    cohorts = _load(out / "COHORT_APPROVAL_PACKAGES.json")
    assert cohorts["cohorts"]["train_events"]["total_events_in_cohort"] == 23
    assert cohorts["cohorts"]["no_train_events"]["total_events_in_cohort"] == 3
    assert cohorts["cohorts"]["engine_events"]["total_events_in_cohort"] == 1


def test_templates_pass_live_validators_when_human_placeholders_filled(tmp_path: Path) -> None:
    out = tmp_path / "pkg"
    build_pi_approval_packages(REPO_ROOT, out)

    signer = "raihankabirrahu@gmail.com"
    now = datetime(2026, 11, 15, 16, 0, tzinfo=UTC)

    # 1) AUTH_MEDIA_ACCESS template must pass media_guard.verify_authorization_record once filled
    auth_tmpl = _load(out / "AUTH_MEDIA_ACCESS.template.json")
    assert HUMAN_PLACEHOLDER in auth_tmpl["authorized_by"]
    assert "RESEARCH_OWNER" in auth_tmpl["authorized_by"]
    assert HUMAN_PLACEHOLDER in auth_tmpl["status"]
    auth_tmpl["authorization_id"] = "AUTH-MEDIA-ACCESS-TEST-01"
    auth_tmpl["status"] = "APPROVED"
    auth_tmpl["authorized_by"] = signer
    auth_tmpl["authorized_at_utc"] = (now - timedelta(hours=1)).isoformat()
    auth_tmpl["expires_at_utc"] = (now + timedelta(days=7)).isoformat()
    auth_tmpl["authorization_statement"] = "Test activation of template after placeholder replacement."
    auth_tmpl["recorded_by"] = {"kind": "researcher", "identity": signer}
    auth_tmpl["record_sha256"] = media_guard._canonical_sha256(auth_tmpl)

    fake_repo = tmp_path / "fake_repo"
    (fake_repo / "data/ground_truth").mkdir(parents=True)
    (fake_repo / "data/governance").mkdir(parents=True)
    (fake_repo / "docs").mkdir(parents=True)
    (fake_repo / "data/raw/layer_b/v2/train_events/event_001").mkdir(parents=True)
    (fake_repo / "data/ground_truth/authorized_reviewers.json").write_text(
        (REPO_ROOT / governance.ALLOWLIST_RELATIVE).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (fake_repo / "docs/FINAL_GROUND_TRUTH_PROTOCOL.md").write_text(
        (REPO_ROOT / "docs/FINAL_GROUND_TRUTH_PROTOCOL.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (fake_repo / media_guard.CANONICAL_MEDIA_AUTH_RELATIVE).write_text(
        json.dumps(auth_tmpl, indent=2), encoding="utf-8"
    )
    verified_media = media_guard.verify_authorization_record(
        fake_repo,
        operation="READ_RAW_MEDIA",
        media_path=fake_repo / "data/raw/layer_b/v2/train_events/event_001/camera_front.mov",
        event_id="train_events/event_001",
        now=now,
    )
    assert verified_media["status"] == "APPROVED"

    # 2) Event split template must pass governance.verify_decision_file once filled
    split_tmpl = _load(out / "phase12_event_split_decision.candidate.template.json")
    assert HUMAN_PLACEHOLDER in split_tmpl["decision_status"]
    split_tmpl["decision_status"] = "APPROVED"
    split_tmpl["decision_id"] = "PHASE12-EVENT-SPLIT-TEST-01"
    split_tmpl["decided_by"] = signer
    split_tmpl["decided_at_utc"] = now.isoformat()
    split_tmpl["researcher_statement"] = "Test superseding Option A for held-out Phase 12."
    split_tmpl["recorded_by"] = {"kind": "researcher", "identity": signer}
    split_path = fake_repo / governance.SPLIT_DECISION_RELATIVE
    split_path.parent.mkdir(parents=True, exist_ok=True)
    split_path.write_text(json.dumps(split_tmpl, indent=2), encoding="utf-8")
    allowlist = governance.load_authorized_reviewers(
        fake_repo / governance.ALLOWLIST_RELATIVE
    )
    verified_split = governance.verify_decision_file(
        fake_repo,
        governance.SPLIT_DECISION_RELATIVE,
        schema=governance.SPLIT_DECISION_SCHEMA,
        missing_code="EVENT_SPLIT_DECISION_MISSING",
        invalid_code="EVENT_SPLIT_DECISION_INVALID",
        allowlist=allowlist,
        now=now,
        check_body=governance.check_split_body,
    )
    assert verified_split.payload["schema_version"] == governance.SPLIT_DECISION_SCHEMA

    # 3) eval_authorization template must have exact allowed keyset & static live hashes
    eval_tmpl = _load(out / "eval_authorization.template.json")
    assert set(eval_tmpl) == set(governance._EVAL_AUTH_KEYS)
    live = assess_official_phase12_readiness(REPO_ROOT).live_bindings
    for key in (
        "decision_policy_sha256",
        "frozen_config_sha256",
        "protocol_profile_sha256",
        "r04_scope_decision_sha256",
    ):
        assert eval_tmpl["bindings"][key] == live[key]
    for dyn_key in (
        "stage21_promotion_receipt_sha256",
        "event_split_decision_sha256",
        "input_manifest_sha256",
    ):
        assert HUMAN_PLACEHOLDER in eval_tmpl["bindings"][dyn_key]

    # Fill remaining human placeholders on a copy and verify with verify_eval_authorization
    full_bindings = dict(live)
    full_bindings["stage21_promotion_receipt_sha256"] = "1" * 64
    full_bindings["event_split_decision_sha256"] = "2" * 64
    full_bindings["input_manifest_sha256"] = "3" * 64
    eval_tmpl["authorization_id"] = "EVAL-AUTH-TEST-01"
    eval_tmpl["authorized_by"] = signer
    eval_tmpl["authorized_at_utc"] = now.isoformat()
    eval_tmpl["authorization_statement"] = "Test activation of eval_authorization template."
    eval_tmpl["recorded_by"] = {"kind": "researcher", "identity": signer}
    eval_tmpl["bindings"] = full_bindings
    eval_tmpl["record_sha256"] = governance.canonical_record_sha256(eval_tmpl)
    (fake_repo / governance.EVAL_AUTH_RELATIVE).write_text(
        json.dumps(eval_tmpl, indent=2), encoding="utf-8"
    )
    verified_eval = governance.verify_eval_authorization(
        fake_repo,
        allowlist=allowlist,
        live_bindings=full_bindings,
        promotion_stage="stage3_single_camera_baseline",
        now=now,
    )
    assert verified_eval.artifact.payload["authorization_id"] == "EVAL-AUTH-TEST-01"

    # 4) AUTH_DESCRIPTIVE_EVAL_EXEC template must pass verify_descriptive_authorization once filled
    desc_tmpl = _load(out / "AUTH_DESCRIPTIVE_EVAL_EXEC.template.json")
    assert set(desc_tmpl) == set(descriptive_exec_gate._KEYS)
    assert desc_tmpl["scope"]["conditions"] == sorted(MM_SUPPORTED_CONDITIONS)
    assert desc_tmpl["bindings"]["metric_scope_sha256"] == descriptive_exec_gate.metric_scope_sha256()
    b2_manifest_sha = governance.sha256_small_file(
        REPO_ROOT / "docs/generated/professor_evidence/mission43/B2_EVALUATION_INPUT_MANIFEST.json"
    )
    assert desc_tmpl["bindings"]["evaluation_manifest_sha256"] == b2_manifest_sha
    desc_tmpl["authorization_id"] = "AUTH-DESCRIPTIVE-TEST-01"
    desc_tmpl["status"] = "APPROVED"
    desc_tmpl["authorized_by"] = signer
    desc_tmpl["authorized_at_utc"] = (now - timedelta(hours=1)).isoformat()
    desc_tmpl["expires_at_utc"] = (now + timedelta(days=7)).isoformat()
    desc_tmpl["authorization_statement"] = "Test activation of Option A descriptive execution template."
    desc_tmpl["recorded_by"] = {"kind": "researcher", "identity": signer}
    promo_sha = "5" * 64
    desc_tmpl["bindings"]["promotion_receipt_sha256"] = promo_sha
    desc_tmpl["record_sha256"] = governance.canonical_record_sha256(desc_tmpl)
    (fake_repo / descriptive_exec_gate.DESCRIPTIVE_AUTH_RELATIVE).write_text(
        json.dumps(desc_tmpl, indent=2), encoding="utf-8"
    )
    verified_desc = descriptive_exec_gate.verify_descriptive_authorization(
        fake_repo,
        condition="B2",
        event_id="train_events/event_001",
        manifest_sha256=b2_manifest_sha,
        now=now,
        live={
            "evaluation_manifest_sha256": b2_manifest_sha,
            "metric_scope_sha256": descriptive_exec_gate.metric_scope_sha256(),
            "model_config_provenance_sha256": live["frozen_config_sha256"],
            "promotion_receipt_sha256": promo_sha,
            "protocol_sha256": live["protocol_profile_sha256"],
        },
    )
    assert verified_desc.authorization_id == "AUTH-DESCRIPTIVE-TEST-01"
