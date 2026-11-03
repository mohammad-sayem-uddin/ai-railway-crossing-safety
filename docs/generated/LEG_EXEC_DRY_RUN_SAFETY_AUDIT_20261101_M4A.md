# LEG-EXEC Invalidation Notice Dry-Run & Non-Destructive Safety Audit (Mission 4A)

**Date:** 2026-11-01  
**Mission:** 4A — Governance Reconciliation, Authorization Integrity & Stage-2.1 Safety Verification  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Branch / HEAD:** `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Status:** VERIFIED SAFE (All 27 Sidecar Notices Valid; All 27 Legacy Review Records Byte-Intact; Re-Write Refused)

---

## 1. Executive Summary

Mission 4A Section 7 required auditing the `LEG-EXEC` legacy invalidation mechanism (`src/railway_detection/annotation/invalidation_notice_writer.py` and `src/railway_detection/annotation/notices.py`) against `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json` without executing any write operation against the repository.

Key verification results:
1. **Proposal Cryptographic Pin:** `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json` matches `PINNED_PROPOSAL_SHA256 = 41cbbba3e9d587b9972c3baca1b39f09d478d408d9c60fd538c249c4600113d4`.
2. **Dry-Run Planning (`plan_invalidation_notices`):** Plans exactly **27** sidecar `.INVALIDATION_NOTICE.json` files (`1` in `engine_events`, `3` in `no_train_events`, `23` in `train_events`) and **never** targets any `*_review.json` file or any file outside `data/ground_truth/reviews/`.
3. **Repository Sidecar State (`scan_notices`):** All **27** `.INVALIDATION_NOTICE.json` sidecar files are already present on disk from Phase 11.6 (`2026-04-16`), all **27** pass cryptographic SHA-256 verification against their paired `*_review.json` files (`invalid_notices = []`, `excused_legacy_records = 27`), and all **27** original `*_review.json` files remain byte-for-byte identical to the hashes recorded in `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json`.
4. **Fail-Closed Write Refusal:** Because all 27 `.INVALIDATION_NOTICE.json` files already exist on disk, any attempt to invoke `apply_invalidation_notices()` in write mode on the repository would immediately raise `ExistingNoticeCollisionError` before writing a single byte.

---

## 2. Cryptographic & Structural Audit of `invalidation_notice_writer.py` and `notices.py`

| Safeguard | Implementation Location | Verified Behavior |
|---|---|---|
| Proposal SHA-256 Pinning | `invalidation_notice_writer.py` (`EXPECTED_PROPOSAL_SHA256`) | Refuses (`ProposalBindingError`) if proposal file SHA-256 != `41cbbba3e9d587b9972c3baca1b39f09d478d408d9c60fd538c249c4600113d4` unless an explicit override hash is supplied for isolated `tmp_path` testing |
| Proposal Schema & Count Check | `load_and_verify_proposal()` | Requires `dry_run: true`, `execution_status: "NOT_EXECUTED"`, and non-empty `proposed_notices` list (`27` entries in canonical proposal) |
| Target Record Existence & Hash Check | `plan_invalidation_notices()` | Reads each `affected_record_path` (`data/ground_truth/reviews/<cohort>/event_XXX_review.json`) and verifies its live SHA-256 equals `affected_record_sha256`; raises `TargetRecordMismatchError` on missing file or hash mismatch |
| Sidecar Path Derivation & Confinement | `plan_invalidation_notices()` | Requires sidecar path to end in `_review.INVALIDATION_NOTICE.json` inside the same `data/ground_truth/reviews/<cohort>/` directory; never overwrites `*_review.json` |
| Existing Notice Collision Refusal | `plan_invalidation_notices()` / `apply_invalidation_notices()` | Raises `ExistingNoticeCollisionError` if any `.INVALIDATION_NOTICE.json` already exists on disk |
| Dry-Run Default | `apply_invalidation_notices(..., execute=False)` | Default `execute=False` performs zero filesystem writes |
| Sidecar Verification | `notices.py` (`scan_notices`, `invalid_notices`, `excused_legacy_records`) | Verifies `notice_schema_version == "1.0"`, `invalidation_status == "INVALIDATED_DO_NOT_PROMOTE"`, `superseded_by_protocol == "Stage-2.1"`, and live SHA-256 match between `target_file_sha256` and the paired `*_review.json` |

---

## 3. Repository Read-Only Dry-Run Verification Summary (27/27 Events)

| Cohort | Planned Sidecars | Existing Valid Sidecars on Disk | Invalid / Mismatched Sidecars | Original `*_review.json` Byte-Intact? |
|---|---:|---:|---:|---|
| `engine_events` (`event_001`) | `1` | `1` | `0` | Yes (`3493e125...1bca3edd`) |
| `no_train_events` (`event_001..003`) | `3` | `3` | `0` | Yes (all 3 SHA-256 digests match proposal) |
| `train_events` (`event_001..023`) | `23` | `23` | `0` | Yes (all 23 SHA-256 digests match proposal) |
| **Total** | **27** | **27** | **0** | **27 / 27 intact** |

---

## 4. Synthetic Fault-Injection Tests in `tmp_path`

Verified in `tests/unit/test_mission4a_governance_and_stage21_safety.py`:
- `test_leg_exec_dry_run_on_repository_is_non_destructive_and_all_27_notices_verify`:
  - Verifies `load_and_verify_proposal()` and `plan_invalidation_notices()` on the real repository in read-only mode, confirming all 27 `*_review.json` hashes and all 27 `.INVALIDATION_NOTICE.json` sidecar hashes before and after the check.
- `test_invalidation_notice_writer_fails_closed_on_tampering_in_tmp_path`:
  - Verifies in `tmp_path` that wrong proposal SHA-256 (`ProposalBindingError`), missing target review file (`ProposalBindingError`), tampered target review file hash (`ProposalBindingError`), existing sidecar notice collision (`ProposalBindingError`), and post-notice tampering of the review record (`invalid_notices` detection) all fail closed without corrupting any review record.
