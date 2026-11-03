# Engine-Event Scope Reconciliation Report (Mission 4A)

**Date:** 2026-11-01  
**Mission:** 4A — Governance Reconciliation, Authorization Integrity & Stage-2.1 Safety Verification  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Branch / HEAD:** `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Status:** VERIFIED & RECONCILED (`1` Engine Event, `3` No-Train Events, `23` Train Events = `27` Total Events)

---

## 1. Executive Summary

Earlier mission narratives contained an occasional discrepancy where engine-only events were referred to in prose as `engine_events/event_001..003` (3 events), whereas the repository manifests, review directories, and Stage-2.1 queue contain **1** engine event (`engine_events/event_001`), **3** negative-control no-train events (`no_train_events/event_001..003`), and **23** train-passage events (`train_events/event_001..023`), totaling **27** events.

Mission 4A inspected all repository manifests, proposal directories, review directories, invalidation sidecars, Stage-2.1 review queue items, and metric calculators (without opening or hashing any `.mov`, `.mp4`, or `.wav` files) and established both the **authoritative cohort counts** and the **exact root cause** of the historical prose confusion.

---

## 2. Authoritative Repository Cohort Inventory (27 Total Events)

| Cohort | Event Count | Canonical Event IDs | Event Type in Proposal Schema | Official Evaluation Role |
|---|---:|---|---|---|
| `train_events` | **23** | `train_events/event_001` .. `train_events/event_023` | `REAL_WORLD_TRAIN_EVENT` | Eligible for train-passage sensitivity / missed-train / premature-opening / lead-time metrics (subject to calibration-vs-test split `AUTH-EVENT-SPLIT` and Stage-2.1 promotion) |
| `no_train_events` | **3** | `no_train_events/event_001` .. `no_train_events/event_003` | `REAL_WORLD_NO_TRAIN` | Negative-control safe baseline cohort (`false_alarm_count`, `false_alarm_blocked_seconds`, `false_alarm_closure_episodes`) |
| `engine_events` | **1** | `engine_events/event_001` | `REAL_WORLD_ENGINE_ONLY` | Isolated case-study cohort (`GOV-ENGINE-ISOLATION`); strictly excluded from train-passage sensitivity and negative-control false-alarm denominators |
| **Total** | **27** | **27 canonical events** | — | — |

---

## 3. Forensic Root Cause of the Historical `1` vs `3` Engine-Event Prose Confusion

Inspection of the filesystem metadata under `data/ground_truth/proposals/` revealed why an earlier narrative confused `engine_events` with 3 files:

1. **Three Proposal Version Files for a Single Engine Event:**
   - Inside `data/ground_truth/proposals/engine_events/`, there are **3 JSON files**, all belonging to the **single event** `engine_events/event_001`:
     - `data/ground_truth/proposals/engine_events/event_001_proposal_v1.json`
     - `data/ground_truth/proposals/engine_events/event_001_proposal_v2.json`
     - `data/ground_truth/proposals/engine_events/event_001_proposal_v3.json` (active candidate proposal, `sha256: aa0d94d83e16975fc6930bbd27cd874c7394959e4343c8c8ce02674d771f648a`)
   - There has **never** been an `engine_events/event_002` or `engine_events/event_003` in the repository.
2. **Conflation with `no_train_events/event_001..003`:**
   - `no_train_events` has 3 distinct events (`event_001`, `event_002`, `event_003`).
   - A superficial file count of `data/ground_truth/proposals/engine_events/*.json` (`3` version files for `event_001`) combined with `no_train_events/event_001..003` led an earlier narrative summary to write `engine_events/event_001..003`.

---

## 4. Cross-Artifact Verification Matrix

Every authoritative artifact in the repository agrees on `1` engine event (`engine_events/event_001`), `3` no-train events (`no_train_events/event_001..003`), and `23` train events (`train_events/event_001..023`):

| Repository Artifact / Module | `engine_events` | `no_train_events` | `train_events` | Total Events | Verification Result |
|---|---:|---:|---:|---:|---|
| `data/manifests/layer_b_v2_annotation_inventory.json` | `1` (`event_001`) | `3` (`event_001..003`) | `23` (`event_001..023`) | `27` | Exact match |
| `data/ground_truth/proposals/` (distinct `event_id`s) | `1` (`event_001`, versions `v1..v3`) | `3` (`event_001..003`, versions `v1..v2`) | `23` (`event_001..023`, versions `v1..v2`) | `27` | Exact match |
| `data/ground_truth/reviews/*/*_review.json` | `1` (`event_001_review.json`) | `3` (`event_001..003_review.json`) | `23` (`event_001..023_review.json`) | `27` | Exact match |
| `data/ground_truth/reviews/*/*.INVALIDATION_NOTICE.json` | `1` (`event_001`) | `3` (`event_001..003`) | `23` (`event_001..023`) | `27` | Exact match |
| `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json` | `1` (`engine_events/event_001`) | `3` (`no_train_events/event_001..003`) | `23` (`train_events/event_001..023`) | `27` | Exact match |
| `docs/generated/STAGE21_REVIEW_QUEUE.json` | `1` (`engine_events/event_001`) | `3` (`no_train_events/event_001..003`) | `23` (`train_events/event_001..023`) | `27` | Exact match |
| `EventMetricsCalculator.aggregate_cohort` (`metrics.py`) | Isolates any `engine_events/*` or `notes=="engine_event_excluded"` into `summary.engine_events` | Isolates `no_train_events/*` into `summary.no_train_events` | Aggregates `train_events/*` into `summary.eligible_events` | Dynamic (`1 + 3 + 23 = 27` on corpus) | Verified in unit tests |
| `aggregate_descriptive_only` (`descriptive_only.py`) | Records `engine_case_study_ids = ("engine_events/event_001",)` and `summary.engine_events = 1` | `summary.no_train_events = 3` | `summary.eligible_events = 23` | `27` | Verified in unit tests |

---

## 5. Regression Test Coverage

- `tests/unit/test_mission4a_governance_and_stage21_safety.py`:
  - `test_repository_engine_event_scope_is_exactly_one_event`: Verifies `data/manifests/layer_b_v2_annotation_inventory.json`, `data/ground_truth/proposals/`, `data/ground_truth/reviews/`, and `docs/generated/STAGE21_REVIEW_QUEUE.json` all contain exactly `1` engine event (`engine_events/event_001`), `3` no-train events, and `23` train events.
  - `test_single_engine_event_isolated_from_train_and_negative_control_denominators`: Verifies `EventMetricsCalculator.aggregate_cohort` and `aggregate_descriptive_only` isolate `engine_events/event_001` from both `missed_train_count` (train sensitivity denominator) and `false_alarm_count` (negative-control denominator).
