# Dataset & Ground-Truth Completion Plan

**Date:** 2026-10-29 UTC
**Status:** BLOCKED_BY_MISSING_EVIDENCE (human review required)

## 1. Dataset Inventory (Verified)

| Property | Value |
|---|---|
| Total events | 27 |
| train_events | 23 |
| no_train_events | 3 |
| engine_events | 1 |
| Capture sessions | 2 (2026-09-14: 20 events; 2026-10-04: 7 events) |
| Crossing | crossing_A, Bangladesh (single site) |
| Front camera | iPhone, 1920×1080, 29.97fps, HEVC |
| Back camera | iPad, 3840×2160, 59.94fps, HEVC |
| Audio | Front mic, 48kHz stereo AAC |
| Cache files | 108 JSONL (27 events × 2 cameras × 2 modalities) |

## 2. Annotation Status

| Stage | Count | Status |
|---|---|---|
| Candidate proposals generated | 61 files | Complete |
| Legacy review records (schema 6.0.0) | 27 | Invalidated |
| Invalidation notices | 27 | Verified |
| Active Stage-2.1 records (schema 8.1.0) | 0 | MISSING |
| Promotion receipt | 0 | MISSING |

## 3. Stage-2.1 Human Review Queue

### Required per event (27 total):

1. **Reviewer identity**: Must be on `data/ground_truth/authorized_reviewers.json` allowlist.
2. **Review duration**: ≥ 30 seconds per event (floor, not sufficiency proof).
3. **Model-independence attestation**: Explicit statement that labels were derived from
   visual/audio inspection, not model predictions.
4. **Reviewer-observed media hashes**: SHA-256 of front and back media files as observed
   during review.
5. **Four-state boundary adjudication** for each of T0–T4:
   - `OBSERVABLE`: value_s + reference_camera + frame_index + rationale
   - `UNOBSERVABLE_NOT_APPLICABLE`: rationale
   - `CENSORED`: rationale (e.g., left-censored T0, right-censored T4)
   - `UNCERTAIN`: rationale
6. **Adjudication history**: Append-only, starting with proposal review.
7. **Proposal binding**: Reference to the active proposal file and its hash.

### Priority Order:

| Priority | Cohort | Events | Rationale |
|---|---|---|---|
| 1 | train_events | 23 | Primary metric denominator |
| 2 | no_train_events | 3 | False-alarm evaluation |
| 3 | engine_events | 1 | Case study (isolated) |

### Known Boundary Issues:

| Event | Issue | Expected Resolution |
|---|---|---|
| train_events/event_005 | T1 unobservable (train present at start) | CENSORED |
| train_events/event_005 | T4 right-censored (recording ends mid-passage) | CENSORED |
| All train_events | T0 left-censored (train visible at t=0) | CENSORED or recording-relative |
| engine_events/event_001 | T3≡T4 (single locomotive) | Special handling |

## 4. Event Split Status

| Item | Status |
|---|---|
| Image-level split (705d388743ea) | EXISTS but leakage_risk=true, development_fallback |
| Event-level split decision | MISSING |
| Session metadata | 2 sessions documented |
| Crossing metadata | 1 crossing (crossing_A) |
| Group-disjoint split possible | NOT with current data (single crossing) |

### Split Options for Researcher:

1. **Full-cohort descriptive** (no split): All 27 events, no generalization claim.
2. **Two-session contrast**: Session 1 (20) vs Session 2 (7), confounded.
3. **Defer**: Wait for multi-crossing data.

## 5. R04 Synchronization Evidence

| Verdict | Count | Dual-camera eligible |
|---|---|---|
| CALIBRATION_SUPPORTED | 12 | Yes (with researcher acceptance) |
| PROVISIONAL | 7 | No (needs visual landmark verification) |
| AMBIGUOUS | 8 | No (insufficient diagnostic quality) |

### CALIBRATION_SUPPORTED Events:

```
engine_events/event_001 (offset=3.4964s, unc=0.15s)
train_events/event_001 (offset=3.4964s, unc=0.15s)
train_events/event_002 (offset=2.8123s, unc=0.12s)
train_events/event_005 (offset=4.1205s, unc=0.18s)
train_events/event_006 (offset=3.0847s, unc=0.11s)
train_events/event_007 (offset=2.9531s, unc=0.14s)
train_events/event_009 (offset=3.2187s, unc=0.13s)
train_events/event_010 (offset=3.5502s, unc=0.16s)
train_events/event_011 (offset=2.7643s, unc=0.10s)
train_events/event_012 (offset=3.8921s, unc=0.17s)
train_events/event_013 (offset=2.6314s, unc=0.12s)
train_events/event_014 (offset=3.1078s, unc=0.14s)
```

## 6. What the Researcher Must Do

1. **Review and adjudicate** 27 events using the Stage-2.1 workflow.
   Estimated time: 3–5 minutes per event = 80–135 minutes total.
2. **Select event split** or authorize descriptive-only mode.
3. **Accept R04 scope** for the 12 CALIBRATION_SUPPORTED events (or subset).
4. **Run promotion workflow** after reviews complete.

## 7. What the Agent Has Prepared

- Review queue with priority ordering.
- Boundary issue identification per event.
- Schema validation tools (existing).
- Promotion gate (existing, tested).
- Readiness CLI (existing, tested).
- All candidate proposals preserved and hash-bound.

