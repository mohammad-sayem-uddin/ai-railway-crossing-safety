#!/usr/bin/env python3
"""Hash the Mission 10 deliverables so an auditor can verify exactly what was reviewed.

Reads only source, test and document files (never media; the media guard is applied to every
hash). Output is deterministic JSON. Hashes change with any edit -- regenerate, don't hand-copy.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402

PATHS = """
src/railway_detection/annotation/second_review.py
src/railway_detection/annotation/phase5_review_tooling.py
src/railway_detection/annotation/media_authorization.py
src/railway_detection/annotation/evaluation_readiness_gate.py
src/railway_detection/annotation/readiness_cli.py
src/railway_detection/annotation/promotion_gate.py
src/railway_detection/annotation/receipt.py
src/railway_detection/evaluation/execution_gate.py
src/railway_detection/evaluation/ground_truth_loader.py
src/railway_detection/evaluation/descriptive_exec_gate.py
src/railway_detection/evaluation/cache_only_engine.py
src/railway_detection/safety/__init__.py
src/railway_detection/safety/media_guard.py
src/railway_detection/safety/access_guard_plugin.py
src/railway_detection/safety/access_manifest.py
scripts/classify_test_access.py
scripts/run_synthetic_tests.py
scripts/mission10_artifact_manifest.py
tests/test_access_classification.yaml
tests/second_review_support.py
tests/test_mission10_second_review.py
tests/unit/test_phase5_review_tooling.py
tests/unit/test_media_authorization.py
tests/unit/test_media_opener_coverage.py
tests/unit/test_descriptive_exec_gate.py
tests/unit/test_access_classification_tools.py
tests/unit/test_mission10_m4_m5_differential.py
tests/unit/test_mission10_back_stream_scope.py
docs/generated/phase5/MISSION_10_FINDING_REGISTER.md
docs/generated/phase5/MISSION_10_RECOVERY_REPORT.md
docs/generated/phase5/MISSION_10_TEST_CLASSIFICATION_AND_SAFE_RUNNER.md
docs/generated/phase5/MISSION_10_DOCUMENT_RECONCILIATION.md
docs/generated/phase5/MISSION_10_CONDITION_MAPPING.md
docs/generated/phase5/MISSION_10_REBUILD_READINESS.md
docs/generated/phase5/MISSION_10_ADVERSARIAL_SELF_AUDIT.md
""".split()
UNCHANGED_BY_MISSION_10 = """
docs/generated/phase5/SONNET_PHASE5_INDEPENDENT_AUDIT_REPORT.md
docs/generated/phase5/SONNET_PHASE5_REMEDIATION_REAUDIT_REPORT.md
docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md
docs/FINAL_GROUND_TRUTH_PROTOCOL.md
configs/decision_policy_v1.yaml
configs/frozen_experiment_v1.yaml
data/ground_truth/authorized_reviewers.json
data/governance/leg_exec_authorization.json
""".split()


def digest(rel: str) -> dict[str, object]:
    path = REPO_ROOT / rel
    if not path.is_file():
        return {"path": rel, "sha256": None, "bytes": None}
    require_media_authorization(path, "HASH_RAW_MEDIA")  # no-op for non-media files
    raw = path.read_bytes()
    return {"path": rel, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def main() -> int:
    manifest = {
        "schema": "mission10-artifact-manifest/1",
        "note": "hashes are of the working tree at generation time; nothing here is committed",
        "mission10_artifacts": [digest(p) for p in PATHS],
        "preserved_inputs_expected_unchanged": [digest(p) for p in UNCHANGED_BY_MISSION_10],
    }
    out = REPO_ROOT / "docs/generated/phase5/MISSION_10_ARTIFACT_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    missing = [e["path"] for e in manifest["mission10_artifacts"] if e["sha256"] is None]
    print(f"wrote {out.relative_to(REPO_ROOT)}; missing: {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
