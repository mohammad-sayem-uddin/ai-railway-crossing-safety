#!/usr/bin/env python3
"""Read-only zero-blocker verifier: cleanly separates technical checks from human/hardware gates.

Never touches raw media under data/raw/ and never fabricates human approvals.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from railway_detection.evaluation import governance  # noqa: E402
from railway_detection.evaluation.execution_gate import assess_official_phase12_readiness  # noqa: E402
from railway_detection.reproducibility.audit import run_reproducibility_audit  # noqa: E402
from railway_detection.safety import access_manifest as am  # noqa: E402
from railway_detection.safety.media_guard import CANONICAL_MEDIA_AUTH_RELATIVE  # noqa: E402


def collect_zero_blocker_status(root: Path = ROOT) -> dict[str, Any]:
    audit = run_reproducibility_audit(root)
    items = {item["id"]: item for item in audit["items"]}
    readiness = assess_official_phase12_readiness(root)
    manifest = am.load_manifest(root / am.MANIFEST_RELATIVE)
    manifest_problems = am.verify_manifest_against_tree(manifest, root)

    technical_checks = {
        "dependency_lock": items["dependency_lock"]["status"] == "PASS",
        "ultralytics_importable": items["ultralytics_importable"]["status"] == "PASS",
        "protocol_version_decided": items["protocol_version"]["status"] == "PASS",
        "r04_scope_decision_recorded": items["r04_scope_decision"]["status"] == "PASS",
        "model_checkpoint_fingerprints": items["model_checkpoint_fingerprints"]["status"] == "PASS",
        "config_and_policy_fingerprints": items["config_and_policy_fingerprints"]["status"] == "PASS",
        "dataset_manifests_intact": items["dataset_manifests"]["status"] == "PASS",
        "manuscript_claims_vs_evidence": items["manuscript_claims_vs_evidence"]["status"] == "PASS",
        "test_access_manifest_in_sync": len(manifest_problems) == 0,
        "all_test_files_classified": manifest["summary"]["total_test_files"] >= 175,
        "no_unexplained_unknown_classifications": all(
            bool(entry.get("spawns_child_process"))
            for entry in manifest["test_files"].values()
            if entry.get("category") == "UNKNOWN"
        ),
    }

    human_and_hardware_gates = {
        "auth_media_access_present": (root / CANONICAL_MEDIA_AUTH_RELATIVE).is_file(),
        "stage21_reviews_present_count": sum(1 for _ in (root / "data/ground_truth/reviews").glob("*_review.json")),
        "stage21_promotion_receipt_present": (root / governance.PROMOTION_RECEIPT_RELATIVE).is_file(),
        "event_split_decision_present": (root / governance.SPLIT_DECISION_RELATIVE).is_file(),
        "phase12_evaluation_inputs_present": (root / "data/manifests/phase12_evaluation_inputs.json").is_file(),
        "eval_authorization_present": (root / governance.EVAL_AUTH_RELATIVE).is_file(),
        "official_phase12_ready": readiness.ready,
        "remaining_official_blocker_codes": sorted(set(readiness.blocker_codes)),
    }

    return {
        "schema_version": "zero-blocker-readiness/1.0",
        "technical_checks": technical_checks,
        "all_technical_checks_passed": all(technical_checks.values()),
        "human_and_hardware_gates": human_and_hardware_gates,
    }


def main() -> int:
    status = collect_zero_blocker_status(ROOT)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["all_technical_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
