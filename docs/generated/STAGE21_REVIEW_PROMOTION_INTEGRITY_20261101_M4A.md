# Stage-2.1 Review-to-Promotion Integrity Verification Report (Mission 4A)

**Date:** 2026-11-01  
**Mission:** 4A — Governance Reconciliation, Authorization Integrity & Stage-2.1 Safety Verification  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Branch / HEAD:** `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Status:** VERIFIED & HARDENED (Zero Unverified Promotion Paths; Zero Real Promotions Executed)

---

## 1. Executive Summary

Mission 4A Section 8 required a comprehensive security and scientific-integrity audit of the Stage-2.1 human-review schema, promotion gate, readiness gate, and cryptographic promotion-receipt verifier (`stage2_1_schema.py`, `promotion_gate.py`, `evaluation_readiness_gate.py`, `receipt.py`, and `governance.py`).

All tests were conducted using synthetic fixtures in isolated `tmp_path` directories. No real Stage-2.1 reviews were created, no ground truth was promoted, and `data/ground_truth/approved/PROMOTION_RECEIPT.json` remains absent.

---

## 2. Verification of the 9 Required Integrity Domains

### 2.1 Reviewer Allowlist & Blocklist (`promotion_gate.py` & `stage2_1_schema.py`)
- **Missing or Empty Allowlist:** `load_authorized_reviewers()` raises `AuthorizedReviewersLoadError` if `data/ground_truth/authorized_reviewers.json` is missing, unreadable, malformed JSON, or has an empty `authorized_reviewers` list.
- **Blocklist Enforcement:** `REVIEWER_ID_BLOCKLIST` (`"human_researcher_lead"`, `"human_annotator"`, `"annotator"`, `"reviewer"`, `"unknown"`, `"system"`, `"ai"`, `"assistant"`, `"human"`, `"researcher"`, `"n/a"`, `"na"`, `"tbd"`, `""`) is enforced at three independent layers:
  1. `load_authorized_reviewers()` rejects any allowlist containing a blocklisted string.
  2. `ReviewerMetadata.__post_init__()` rejects any `reviewer_id` in `REVIEWER_ID_BLOCKLIST`.
  3. `AdjudicationHistoryEntry.__post_init__()` (hardened in Mission 4A) rejects any `by` actor in `REVIEWER_ID_BLOCKLIST`.
- **Duplicate & Revoked/Inactive Reviewer Detection (Hardened in Mission 4A):**
  - `load_authorized_reviewers()` rejects duplicate entries in `authorized_reviewers` and fails closed (`AuthorizedReviewersLoadError`) if `revoked_reviewers` or `inactive_reviewers` is malformed or overlaps with `authorized_reviewers`.

### 2.2 Minimum Review Duration Floor (`30.0s`)
- `MIN_PLAUSIBLE_REVIEW_DURATION_S = 30.0` in `stage2_1_schema.py`.
- `ReviewerMetadata.__post_init__()` computes elapsed duration directly from `(review_end_utc - review_start_utc).total_seconds()`, **ignoring** any caller-supplied `review_duration_s` field if it disagrees by more than `1e-3s` (`SchemaValidationError`), and rejects any review shorter than `30.0s`.

### 2.3 Model-Independence Attestation
- `ModelIndependenceAttestation.__post_init__()` requires `attested is True`, a non-empty `statement` of at least `20` characters, and a valid timezone-aware UTC `attested_at_utc` timestamp.

### 2.4 Proposal Hash Binding & Active Proposal Currency
- `ProposalBinding.__post_init__()` validates `proposal_file` and 64-hex `proposal_sha256`.
- `validate_for_promotion()` checks the record's `proposal_binding.proposal_sha256` against `active_proposal_hashes[event_id]`, emitting `STALE_OR_MISMATCHED_PROPOSAL_HASH` or `MISSING_ACTIVE_PROPOSAL` on any mismatch.

### 2.5 Dual-Layer Media Hash Binding (`Registry` + `Live Disk`)
- `ReviewerObservedMediaHashes` requires 64-hex SHA-256 digests for both `front_camera_sha256` and `back_camera_sha256`.
- At promotion time (`validate_for_promotion`), `promotion_gate.py` verifies:
  1. Record's observed hashes match `media_hash_registry` (`MEDIA_HASH_MISMATCH_AT_REVIEW`).
  2. Live files on disk (`media_file_paths`) exist and their live SHA-256 matches both `media_hash_registry` (`MEDIA_HASH_CHANGED_SINCE_REGISTRY`) and `reviewer_observed_media_hashes` (`MEDIA_HASH_CHANGED_SINCE_REVIEW`).

### 2.6 Boundary State Taxonomy (`OBSERVABLE`, `UNOBSERVABLE_NOT_APPLICABLE`, `CENSORED`, `UNCERTAIN`)
- `Stage21ReviewRecord.__post_init__()` requires all 6 canonical boundaries (`T0_first_visible`, `T1_danger_zone_entry`, `T2_crossing_occupancy_start`, `T3_locomotive_unit_clearance`, `T4_tail_clearance`, `T_scene_clear`) to be explicitly adjudicated:
  - `OBSERVABLE`: requires finite non-negative `value_s`, `reference_camera in ("front", "back", "both")`, and non-negative integer `frame_index`.
  - `UNOBSERVABLE_NOT_APPLICABLE`, `CENSORED`, `UNCERTAIN`: requires `value_s is None` and `frame_index is None`, plus a non-empty `rationale` (`>= 10` characters).
  - Enforces temporal monotonicity (`T0 <= T1 <= T2 <= T3 <= T4 <= T_scene_clear`) across all observable timestamps.

### 2.7 Adjudication Status & Dispute Resolution (`Stage21ReviewRecord` & `promotion_gate.py`)
- Only `adjudication_status == "APPROVED"` is eligible for promotion; `"REJECTED"`, `"NEEDS_SECOND_REVIEW"`, and `"DISPUTED"` are refused (`STATUS_NOT_PROMOTABLE`).
- If `adjudication_history` contains `"dispute_opened"`, it must be followed by a later `"dispute_resolved"` entry with a non-empty `resolution_note`; otherwise `Stage21ReviewRecord` raises `SchemaValidationError` and `promotion_gate.py` emits `UNRESOLVED_DISPUTE_HISTORY`.

### 2.8 Adjudication History & Second-Review Independence (Hardened in Mission 4A)
- **Single-Record History Hardening (`stage2_1_schema.py`):**
  - Rejects duplicate `(event, by, at_utc, resolution_note)` entries in `adjudication_history`.
  - Rejects self-referential `second_review_of == review_id`.
  - Rejects any record claiming `second_review_of` or a `"second_review"` / `"dispute_resolved"` history step where all history entries belong to the same `by` reviewer.
- **Cross-Record Batch Hardening (`promotion_gate.py`):**
  - `validate_batch_for_promotion()` builds an index of `review_id -> reviewer_id` across the batch and emits `BATCH_SAME_REVIEWER_SECOND_REVIEW` if a record references `second_review_of` pointing to a record reviewed by the same `reviewer_id`.

### 2.9 Cryptographic Promotion Receipt Verification (`receipt.py` & `governance.py`)
- `verify_promotion_receipt(repo_root)` in `src/railway_detection/evaluation/governance.py` requires:
  1. `data/ground_truth/approved/PROMOTION_RECEIPT.json` exists.
  2. `schema_version == "stage2.1-promotion-receipt-v1"` and `produced_by == "railway_detection.annotation.evaluation_readiness_gate"`.
  3. `receipt_sha256` equals `receipt_body_sha256(receipt)`.
  4. All 27 inventory events are listed in `promoted_events`, and every promoted file on disk under `data/ground_truth/` matches its recorded `promoted_file_sha256`, `review_sha256`, and `proposal_sha256`.

---

## 3. Regression Test Coverage

Verified in `tests/unit/test_mission4a_governance_and_stage21_safety.py`:
- `test_allowlist_rejects_missing_empty_blocklisted_duplicate_and_revoked_entries`
- `test_stage21_schema_rejects_short_duration_forged_duration_and_bad_history`
- `test_promotion_gate_and_receipt_detect_media_tampering_disputes_and_batch_collisions`
