# Official Readiness & Authorization Matrix (Mission 4A)

**Date:** 2026-11-01  
**Mission:** 4A — Governance Reconciliation, Authorization Integrity & Stage-2.1 Safety Verification  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Branch / HEAD:** `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Status:** FAIL-CLOSED VERIFIED (`ready_for_promotion = False`, `ready_for_official_evaluation = False`)

---

## 1. Executive Summary

Mission 4A Section 10 required inspecting and cross-checking all seven readiness, governance, manifest, and execution-gate modules to verify that no inconsistent readiness state can exist across the repository and that official Phase 12 B0–B7 evaluation (`EVAL-AUTH`) fails closed until every human-review, promotion, cache-provenance, and researcher-decision prerequisite is satisfied.

---

## 2. Module-by-Module Gate Audit

| Module | Primary Entrypoint | Enforced Prerequisites | Current Live Repository Verdict |
|---|---|---|---|
| `src/railway_detection/annotation/evaluation_readiness_gate.py` | `evaluate_readiness()` | 1. Valid `authorized_reviewers.json` allowlist<br>2. `0` invalid `.INVALIDATION_NOTICE.json` sidecars<br>3. All `27` inventory events (`23` train, `3` no-train, `1` engine) have valid `8.1.0-stage2.1` `APPROVED` reviews<br>4. Live media hashes match registry & review<br>5. Active proposal hashes match review bindings<br>6. Zero `synthetic_` identifiers in canonical directories | `ready_for_promotion = False`<br>(`ALLOWLIST_LOAD_FAILED` + `27/27` legacy `7.0.0` reviews invalidated/unpromoted) |
| `src/railway_detection/annotation/readiness_cli.py` | `main()` (`--check-only` default) | Wraps `evaluate_readiness()` and only writes `PROMOTION_RECEIPT.json` if `--promote` is explicitly passed **and** `ready_for_promotion is True` | Exits non-zero (`ready_for_promotion = False`) |
| `src/railway_detection/evaluation/governance.py` | `verify_promotion_receipt(repo_root)` | Requires `data/ground_truth/approved/PROMOTION_RECEIPT.json` with valid `receipt_sha256` and all 27 promoted files matching recorded SHA-256 digests | Raises `GovernanceError` (`PROMOTION_RECEIPT.json` does not exist) |
| `src/railway_detection/evaluation/execution_gate.py` | `assess_official_phase12_readiness(repo_root)` | Checks `verify_promotion_receipt(repo_root)`, `authorized_reviewers.json`, Stage-2.1 review completeness (`27/27`), and Phase 12 manifest readiness | `ready_for_official_evaluation = False` (`PROMOTION_RECEIPT_INVALID_OR_MISSING`, `ALLOWLIST_MISSING_OR_INVALID`, `PROMOTED_GROUND_TRUTH_INCOMPLETE`) |
| `src/railway_detection/evaluation/manifest_builder.py` | `build_phase12_manifest()` | Requires verified `PROMOTION_RECEIPT.json` and 27 promoted Stage-2.1 ground-truth records before emitting an official Phase 12 evaluation manifest | Refuses to build official manifest until promotion receipt exists |
| `src/railway_detection/evaluation/evaluation_runner.py` | `Phase12EvaluationRunner.run()` | Calls `verify_promotion_receipt(repo_root)` and `assess_official_phase12_readiness(repo_root)` before executing any B0–B7 evaluation scenario | Raises `EvaluationRefused` |
| `src/railway_detection/evaluation/research_contracts.py` | Contract validators | Separates `DESCRIPTIVE_ONLY` historical outputs (`official_evaluation_eligible=False`) from official inferential evaluation contracts | Enforces `official_evaluation_eligible = False` on all pre-Stage-2.1 artifacts |
| `src/railway_detection/experiments/preflight_validator.py` | `run_experiment_preflight()` | Checks all of the above **plus** controlled cache provenance (`controlled-cache-v1`), 64-hex checkpoint SHA-256 resolution, and canonical researcher decisions (`GOV-D1-PROTOCOL-AUTHORITY`, `GOV-D2-EVALUATION-PROFILE`, `EXP-OPERATING-THRESHOLDS`, `EXP-ROI-GEOMETRY`, `GOV-D4-R04-SYNCHRONIZATION`, `AUTH-EVENT-SPLIT`, `AUTH-EVAL-OFFICIAL`) | `ready_for_controlled_execution = False`<br>`ready_for_official_evaluation = False` |

---

## 3. Master Pipeline Operation Authorization Matrix

| Pipeline Operation | Currently Permitted? | Blocking Gate(s) | Required Preconditions to Unlock |
|---|---|---|---|
| **1. Synthetic unit & regression testing (`pytest` in `tmp_path`)** | **YES (PERMITTED)** | None (isolated to `tmp_path`, zero raw media access) | Already active (`1,409` passing tests) |
| **2. Historical 27-event descriptive-only reporting (`DESCRIPTIVE_ONLY`)** | **YES (PERMITTED — Non-Inferential Only)** | `descriptive_only.py` (`official_evaluation_eligible=False`) | Approved under `GOV-D3-DESCRIPTIVE-MODE` (`D3`); must carry explicit caveats and never claim inferential B0–B7 validity |
| **3. `LEG-EXEC` dry-run / notice verification (`scan_notices`)** | **YES (PERMITTED — Read-Only)** | `invalidation_notice_writer.py` (`execute=False`) | All 27 `.INVALIDATION_NOTICE.json` sidecars already written in Phase 11.6 and verified; write mode is permanently blocked by `ExistingNoticeCollisionError` |
| **4. Synthetic Stage-2.1 session & timing-pilot dry-runs (`synthetic_*` IDs in `tmp_path`)** | **YES (PERMITTED — Non-Canonical Only)** | `adjudication_session.py`, `stage21_timing_pilot.py`, `promotion_gate.py` (`SYNTHETIC_RECORD_NOT_PROMOTABLE`) | Permitted only outside `data/ground_truth/`; cannot be promoted |
| **5. Real Stage-2.1 3-event timing calibration pilot (`PILOT-EXEC`)** | **BLOCKED (Requires Human Action)** | `AUTH-STAGE21-ALLOWLIST`, `AUTH-PILOT-EXEC` | Researcher must populate `data/ground_truth/authorized_reviewers.json` with real human reviewer IDs and perform independent frame-by-frame review (`>= 30.0s` per event) |
| **6. Full 27-event Stage-2.1 human review & adjudication** | **BLOCKED (Requires Human Action)** | `evaluation_readiness_gate.py` (`0/27` Stage-2.1 reviews on disk) | Researcher / authorized human reviewers must complete and attest `8.1.0-stage2.1` reviews for all 27 events (`23` train, `3` no-train, `1` engine) |
| **7. Ground-truth promotion & `PROMOTION_RECEIPT.json` creation (`PROMOTE-EXEC`)** | **BLOCKED** | `promotion_gate.py`, `evaluation_readiness_gate.py`, `AUTH-PROMOTE-EXEC` | Requires `27/27` `APPROVED` Stage-2.1 reviews, zero unresolved disputes, live media hash match, active proposal hash match, and explicit researcher execution of `readiness_cli.py --promote` |
| **8. Controlled cache generation from raw `.mov`/`.wav` corpus** | **BLOCKED** | Raw media safety boundary + `EXP-OPERATING-THRESHOLDS` + `EXP-ROI-GEOMETRY` | Requires explicit researcher authorization to access raw media, pinned 64-hex checkpoint SHA-256 digests (excluding prohibited `v2/audio_pretrained.pt`), and approved ROI/threshold config |
| **9. Official Phase 12 B0–B7 inferential evaluation (`EVAL-AUTH`)** | **BLOCKED** | `execution_gate.py`, `evaluation_runner.py`, `preflight_validator.py`, `AUTH-EVAL-OFFICIAL` | Requires verified `PROMOTION_RECEIPT.json`, verified `controlled-cache-v1` caches, and researcher sign-off on `D1` (`GOV-D1-PROTOCOL-AUTHORITY`), `D2` (`GOV-D2-EVALUATION-PROFILE`), `D3_SPLIT` (`AUTH-EVENT-SPLIT`), `D4` (`GOV-D4-R04-SYNCHRONIZATION`), `EXP-OPERATING-THRESHOLDS`, `EXP-ROI-GEOMETRY`, and `EVAL-AUTH` |
