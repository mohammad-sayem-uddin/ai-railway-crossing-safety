# R04 Eleven-versus-Twelve Reconciliation

**Date:** 2026-11-01  
**Mission:** 4D — Scientific Governance Integrity Remediation  
**Status:** RECONCILED (metadata-only; no media inspected; no scope changed)

## Discrepancy Summary

| Artifact | Count | Source |
|---|---:|---|
| `data/manifests/camera_sync_offsets_candidate.yaml` CALIBRATION_SUPPORTED | 12 | Candidate manifest v0.2.0_CANDIDATE |
| `configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml` included events | 11 | Authorized exploratory config |
| `governance.documented_r04_candidates()` consistency check | `consistent: False` | Code-level detection |

## Exact Event Discrepancy

**Event present in manifest (12) but NOT in exploratory config (11):**

- `train_events/event_010`

**Event present in exploratory config (11) but NOT in manifest (12):**

- None

## Root Cause Analysis

`train_events/event_010` was promoted to `CALIBRATION_SUPPORTED` via verified visual landmark corroboration by the Lead Researcher (Raihan Kabir Rahu) under `ADMINISTRATIVE_DISPOSITION_R04_READ_ONLY_UNBLOCK_20261025`. The manifest `human_review_status` field records this as `REVIEWED_WITH_CORROBORATION`.

However, the exploratory dual-camera configuration (`exploratory_dual_camera_v1_supported_subset.yaml` v1.0.0, later authorized as v1.1.0) was created BEFORE this promotion. The 11-event list was frozen at authorization time (2026-10-13) and was never updated to include the subsequently promoted event.

The exploratory config's `included_events_calibration_supported` list contains exactly 11 events, all of which are also in the manifest's 12-event CALIBRATION_SUPPORTED set. The manifest has one additional event (`train_events/event_010`) that was promoted after the exploratory config was frozen.

## Manifest Details for Discrepancy Event

| Field | Value |
|---|---|
| Event | `train_events/event_010` |
| Calibration verdict | `CALIBRATION_SUPPORTED` |
| Cohort | `train_events` |
| PSR | 2.14 |
| SNR | 22.34 |
| Window range | 0.0001 |
| Corroboration source | `visual_landmark` |
| Corroboration verified | `True` |
| Reviewer | `Raihan_Kabir_Rahu` |
| Candidate offset | 2.7158s |
| Delta | 0.000s (within 0.10s tolerance) |

## Classification

This is a **temporal scope discrepancy**, not a classification logic error. The manifest correctly reflects the current state (12 supported events including the visually corroborated event_010). The exploratory config correctly reflects its authorization-time state (11 events). Neither artifact is incorrect for its own purpose.

## What Was NOT Changed

- The candidate manifest was NOT modified.
- The exploratory configuration was NOT modified.
- No R04 scope decision was made.
- No synchronization acceptance was claimed.
- No media was inspected.

## Unresolved Researcher Decision

The researcher must decide whether:
1. The exploratory scope should be updated to include `train_events/event_010` (requires new authorization).
2. The current 11-event exploratory scope remains as-is.
3. A separate R04 scope decision (`phase12_r04_scope_decision.json`) should be created covering a different set of events.

This decision is recorded as `GOV-D4-R04-SYNCHRONIZATION` = `PENDING_RESEARCHER_DECISION`.

## Affected Artifacts (Read-Only Inspection)

- `data/manifests/camera_sync_offsets_candidate.yaml` (not modified)
- `configs/exploratory_dual_camera_v1_supported_subset.yaml` (not modified)
- `configs/exploratory_dual_camera_v1.1.0_authorized_20261013.yaml` (not modified)
- `src/railway_detection/evaluation/governance.py` (`documented_r04_candidates()`, not modified)
