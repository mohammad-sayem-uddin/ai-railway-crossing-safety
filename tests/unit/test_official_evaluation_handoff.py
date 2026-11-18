"""Tests for Task 2/6 approval-package validation and fail-closed official evaluation handoff."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from railway_detection.evaluation.official_handoff import (
    OfficialHandoffError,
    run_post_approval_official_evaluation,
    run_post_approval_option_a_descriptive_evaluation,
    validate_approval_package_bundle,
)
from railway_detection.safety import media_guard

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from prepare_and_execute_official_evaluation import main as handoff_cli_main  # noqa: E402


def test_validate_approval_package_bundle_succeeds_across_all_12_docs() -> None:
    report = validate_approval_package_bundle(REPO_ROOT)
    assert report["validated_file_count"] == 12
    assert report["events_verified"] == 27
    assert report["zero_fabricated_approvals"] is True
    assert report["official_phase12_ready"] is False
    assert report["option_a_descriptive_ready"] is False
    assert set(report["official_blocker_codes"]) == {
        "COHORT_APPROVAL_MISSING",
        "EVAL_AUTH_NOT_GRANTED",
        "EVENT_SPLIT_DECISION_MISSING",
        "MANIFEST_MISSING",
        "STAGE21_RECORDS_MISSING",
    }


def test_post_approval_execution_refuses_when_auth_media_missing(tmp_path: Path) -> None:
    with pytest.raises(OfficialHandoffError, match="AUTH_MEDIA_ACCESS_NOT_GRANTED"):
        run_post_approval_official_evaluation(REPO_ROOT, output_dir=tmp_path / "official_out")
    with pytest.raises(OfficialHandoffError, match="STAGE21_PROMOTION_RECEIPT_MISSING"):
        run_post_approval_option_a_descriptive_evaluation(
            REPO_ROOT, output_dir=tmp_path / "option_a_out"
        )


def test_post_approval_execution_refuses_in_temp_repo_without_stage21_and_eval_auth(
    tmp_path: Path,
) -> None:
    fake_repo = tmp_path / "fake_repo"
    (fake_repo / "data/ground_truth").mkdir(parents=True)
    (fake_repo / "data/governance").mkdir(parents=True)
    (fake_repo / "docs").mkdir(parents=True)
    (fake_repo / "configs").mkdir(parents=True)

    (fake_repo / "data/ground_truth/authorized_reviewers.json").write_text(
        (REPO_ROOT / "data/ground_truth/authorized_reviewers.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (fake_repo / "docs/FINAL_GROUND_TRUTH_PROTOCOL.md").write_text(
        (REPO_ROOT / "docs/FINAL_GROUND_TRUTH_PROTOCOL.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (fake_repo / "configs/frozen_experiment_v1.yaml").write_text(
        (REPO_ROOT / "configs/frozen_experiment_v1.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (fake_repo / "configs/decision_policy_v1.yaml").write_text(
        (REPO_ROOT / "configs/decision_policy_v1.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    tmpl = json.loads(
        (REPO_ROOT / "docs/generated/approval_packages/AUTH_MEDIA_ACCESS.template.json").read_text(
            encoding="utf-8"
        )
    )
    now = datetime.now(UTC)
    signer = "raihankabirrahu@gmail.com"
    tmpl["authorization_id"] = "AUTH-MEDIA-ACCESS-TMP"
    tmpl["status"] = "APPROVED"
    tmpl["authorized_by"] = signer
    tmpl["authorized_at_utc"] = (now - timedelta(hours=1)).isoformat()
    tmpl["expires_at_utc"] = (now + timedelta(days=2)).isoformat()
    tmpl["authorization_statement"] = "Synthetic temp-tree gate test."
    tmpl["recorded_by"] = {"kind": "researcher", "identity": signer}
    tmpl["record_sha256"] = media_guard._canonical_sha256(tmpl)
    (fake_repo / media_guard.CANONICAL_MEDIA_AUTH_RELATIVE).write_text(
        json.dumps(tmpl, indent=2), encoding="utf-8"
    )

    with pytest.raises(OfficialHandoffError, match="OFFICIAL_PHASE12_BLOCKED"):
        run_post_approval_official_evaluation(fake_repo, output_dir=tmp_path / "official_out")


def test_handoff_cli_preflight_passes_and_execute_refuses(tmp_path: Path, capsys) -> None:
    rc_pre = handoff_cli_main(["--mode", "preflight-check", "--root", str(REPO_ROOT)])
    out_pre = json.loads(capsys.readouterr().out)
    assert rc_pre == 0
    assert out_pre["validated_file_count"] == 12
    assert out_pre["official_phase12_ready"] is False
    assert out_pre["option_a_descriptive_ready"] is False

    rc_exec = handoff_cli_main(
        [
            "--mode",
            "execute-after-approval",
            "--root",
            str(REPO_ROOT),
            "--output-dir",
            str(tmp_path / "official_out"),
        ]
    )
    out_exec = json.loads(capsys.readouterr().out)
    assert rc_exec == 3
    assert out_exec["status"] == "BLOCKED"
    assert out_exec["code"] == "AUTH_MEDIA_ACCESS_NOT_GRANTED"

    rc_opt_a = handoff_cli_main(
        [
            "--mode",
            "execute-option-a-descriptive",
            "--root",
            str(REPO_ROOT),
            "--output-dir",
            str(tmp_path / "option_a_out"),
        ]
    )
    out_opt_a = json.loads(capsys.readouterr().out)
    assert rc_opt_a == 3
    assert out_opt_a["status"] == "BLOCKED"
    assert out_opt_a["code"] == "STAGE21_PROMOTION_RECEIPT_MISSING"
