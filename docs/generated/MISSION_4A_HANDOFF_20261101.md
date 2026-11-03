# Mission 4A Handoff & Stage-2.1 Human-Review Execution Guide

**Date:** 2026-11-01  
**Mission:** 4A — Governance Reconciliation, Authorization Integrity & Stage-2.1 Safety Verification  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Branch / HEAD:** `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Status:** COMPLETE — Ready for Researcher Governance Sign-Off & Stage-2.1 Human Review

---

## 1. Mission 4A Accomplishments Summary

1. **Governance Decision Register Reconciled (`preflight_validator.py` & `GOVERNANCE_DECISION_RECONCILIATION_20261101_M4A.md`):**
   - Established the 17-entry `CANONICAL_DECISION_REGISTER` and `HISTORICAL_DECISION_ALIASES` using the 6 strictly permitted status tokens (`DECISION_STATUSES`).
   - Restored historical `D1` (`GOV-D1-PROTOCOL-AUTHORITY`) and `D2` (`GOV-D2-EVALUATION-PROFILE`) to their exact Mission 1/2 definitions and separated them from `EXP-OPERATING-THRESHOLDS` and `EXP-ROI-GEOMETRY` in both documentation and `preflight_validator.py`.
   - Explicitly separated `D3` (`GOV-D3-DESCRIPTIVE-MODE`, approved) from `D3_SPLIT` (`AUTH-EVENT-SPLIT`, pending).
2. **Engine-Event Scope Reconciled (`ENGINE_EVENT_SCOPE_RECONCILIATION_20261101_M4A.md`):**
   - Proved across all manifests, proposals, reviews, invalidation notices, and `STAGE21_REVIEW_QUEUE.json` that the repository contains **1** engine event (`engine_events/event_001`, which has 3 proposal version files `event_001_proposal_v1..v3.json`), **3** no-train events (`no_train_events/event_001..003`), and **23** train events (`train_events/event_001..023`) = **27** total events.
3. **Stage-2.1 Synthetic ID Guard Audited & Hardened (`stage2_1_schema.py`, `promotion_gate.py`, `evaluation_readiness_gate.py`):**
   - Verified `adjudication_session.py` and `stage21_timing_pilot.py` enforce `synthetic_` prefixes and non-canonical output directories during dry-run preparation.
   - Added `validate_non_synthetic_record()` and `disallow_synthetic_identifiers` (auto-enabled on real repository `data/ground_truth` paths) to `promotion_gate.py` and `evaluation_readiness_gate.py` so synthetic records (`synthetic_*` IDs, `@synthetic.` domains, or temp-dir media paths) can **never** be promoted as canonical ground truth.
4. **LEG-EXEC Dry-Run & Non-Destructive Safety Verified (`LEG_EXEC_DRY_RUN_SAFETY_AUDIT_20261101_M4A.md`):**
   - Verified in read-only mode that all 27 `.INVALIDATION_NOTICE.json` sidecar files on disk pass `scan_notices()`, all 27 legacy `*_review.json` files remain byte-intact, and any attempt to re-execute `apply_invalidation_notices()` in write mode is refused by `ExistingNoticeCollisionError`.
5. **Stage-2.1 Review-to-Promotion Pipeline Hardened (`STAGE21_REVIEW_PROMOTION_INTEGRITY_20261101_M4A.md`):**
   - Hardened `load_authorized_reviewers()` against `revoked_reviewers` / `inactive_reviewers` overlaps.
   - Hardened `Stage21ReviewRecord` and `AdjudicationHistoryEntry` against blocklisted history actors, duplicate history entries, self-referential `second_review_of`, and same-reviewer second-review history claims.
   - Added cross-record `BATCH_SAME_REVIEWER_SECOND_REVIEW` detection to `validate_batch_for_promotion()`.
6. **Controlled Cache & Readiness Gates Verified (`1,409` passing tests):**
   - Verified end-to-end integration of `controlled-cache-v1` across `cache_provenance.py`, `layer_b_processor.py`, `runner.py`, `descriptive_only.py`, and `preflight_validator.py`.
   - Confirmed all official evaluation gates (`evaluation_readiness_gate.py`, `execution_gate.py`, `governance.py`, `evaluation_runner.py`, `preflight_validator.py`) fail closed (`ready_for_official_evaluation = False`).

---

## 2. Researcher Action Checklist for the Next Stage (Human-Review & Governance Phase)

The software pipeline is fully verified and fail-closed. The next steps require **human researcher action** and cannot be automated by an AI agent:

### Step 1: Populate the Reviewer Allowlist (`AUTH-STAGE21-ALLOWLIST`)
Create `data/ground_truth/authorized_reviewers.json` with real, individually attributable human reviewer identifiers (none from `REVIEWER_ID_BLOCKLIST` and none starting with `synthetic_`):
```json
{
  "authorized_reviewers": [
    "<primary_reviewer_email_or_orcid>",
    "<second_reviewer_email_or_orcid>"
  ],
  "revoked_reviewers": [],
  "inactive_reviewers": []
}
```

### Step 2: Execute the 3-Event Stage-2.1 Timing Calibration Pilot (`AUTH-PILOT-EXEC`)
Perform real frame-by-frame visual and spectral-audio inspection (`>= 30.0s` per event, without consulting model predictions) on the 3 pilot events (`train_events/event_001`, `no_train_events/event_001`, `engine_events/event_001`) using `build_review_record()` in `src/railway_detection/annotation/review_session.py`.

### Step 3: Complete All 27 Stage-2.1 Human Reviews & Promote Ground Truth (`AUTH-PROMOTE-EXEC`)
1. Complete `8.1.0-stage2.1` review records for all 27 events (`23` `train_events`, `3` `no_train_events`, `1` `engine_events`).
2. Run the readiness check in dry-run mode:
   ```bash
   PYTHONPATH=src .venv/bin/python -m railway_detection.annotation.readiness_cli --check-only
   ```
3. Once `ready_for_promotion: true` is reported with `0` violations, execute promotion to write canonical ground truth and `data/ground_truth/approved/PROMOTION_RECEIPT.json`:
   ```bash
   PYTHONPATH=src .venv/bin/python -m railway_detection.annotation.readiness_cli --promote
   ```

### Step 4: Record Pending Scientific Decisions Before Official Phase 12 Evaluation (`AUTH-EVAL-OFFICIAL`)
Record explicit researcher sign-off for:
- `GOV-D1-PROTOCOL-AUTHORITY` (`D1`): Protocol authority reconciliation (`EXPERIMENT_PROTOCOL_V2.md` v9.0.0 vs `GROUND_TRUTH_DESIGN_DOCUMENT.md` v1.0.0).
- `GOV-D2-EVALUATION-PROFILE` (`D2`): Premature-opening window (`v9` vs `M4` vs `dual_report`).
- `AUTH-EVENT-SPLIT` (`D3_SPLIT`): Calibration-pilot vs held-out evaluation split across the 23 `train_events`.
- `GOV-D4-R04-SYNCHRONIZATION` (`D4`): Dual-camera clock policy (`independent_camera_clocks` vs measured offset).
- `EXP-OPERATING-THRESHOLDS` & `EXP-ROI-GEOMETRY`: Post-pilot operating thresholds and ROI polygon coordinates.
- `AUTH-EVAL-OFFICIAL` (`EVAL-AUTH`): Authorization to generate `controlled-cache-v1` caches and run official B0–B7 evaluation.
