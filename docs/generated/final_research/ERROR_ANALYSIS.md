# Error Analysis

Errors are grouped by layer. Every item names its evidence source; no error
is attributed to a cause the evidence does not support.

## 1. Audio perception errors (Mission 43, adopted-reference comparison)

Frozen rule: event = horn-present iff any 0.5 s-hop window scores ≥ 0.37
(threshold never retuned). Over the 23 train events with adopted horn status:
TP 12, FP 10, FN 1, TN 0.

- **All 10 horn-absent train events false-alarmed.** The max-window
  aggregation is brittle by construction: one spurious window anywhere in an
  event flips the event label. Specificity on this subset is 0%. This is an
  *aggregation-rule* finding as much as a model finding — the window-level
  scores may be mostly correct while the event rule still fails — but
  window-level ground truth does not exist (0 window labels), so the split
  between model error and aggregation error cannot be quantified. The
  per-window review candidates are preserved in the Mission 43 package
  (`AUDIO_ERROR_REVIEW_WINDOWS.csv`, `FAILURE_REVIEW_CANDIDATES.csv`).
- **Sole false negative: event_001** (max window probability 0.2475, below
  the 0.37 operating point). No threshold adjustment is permitted on the
  evaluation data; the miss is reported, not tuned away.
- Descriptive ranking quality is modest (ROC-AUC 0.6846, AP 0.7739 over the
  same 23 events): the audio model is weak event-level evidence, consistent
  with its architectural role — supporting evidence only (RULE_2), never an
  actuation source.

## 2. Decision-policy errors (Phase 10.1, identical cached inputs, 11 events)

- **v1 systematic self-interruption (design defect).** The departing train's
  own `side` detections satisfy v1's approach predicate, firing
  RULE_7_NEW_TRAIN_INTERRUPT repeatedly during the clearance dwell.
  Result: 0/11 events ever reach CROSSING_CLEAR. This is a specification
  error in the frozen label sets (overlap + no role scoping), reproduced
  from source in Mission 3 (Blocker A) and targeted by synthetic scenario S1.
- **v2 residual non-clearances are data/geometry interactions, not logic
  errors:** events 002/006 — recordings end before the dwell can complete
  (0.8 s / 2.8 s margins); events 005/007/017 — back-camera detection density
  (89–95% of ticks) never leaves the ≥2-tick silence RULE_3C requires.
  Isolated in controlled fixtures by Phase 10.1; mirrored in battery
  scenarios S1/S2 design assumptions.

## 3. Instrumentation and assembly errors

- **Naive duration truncation (Phase 8–10 scripts).** Replay duration was
  computed as max over raw, unaligned per-camera timestamps, silently
  truncating 1.1–5.1 s of back-camera tail evidence per event. Found and
  corrected inside Phase 10.1's own script only; historical outputs were
  preserved uncorrected (and Phase 10.1 verified the correction changes no
  clearance outcome on the 11 events).
- **Same defect family in the governed replay engine (Mission 3).**
  `CacheOnlyReplayEngine.execute_replay` bounds frame generation by raw
  record timestamps while the collector aligns to master time — with a sync
  aligner attached, aligned tail evidence can fall outside the generated
  window. **Fixed in the Mission 3 subclass**
  (`cache_only_engine_multimodal.py`, master-time bounds) with regression
  tests (8/8 pass, including a frame-generation probe beyond the raw
  bound); the frozen engine module is untouched.
- **Collector backfill shortens effective silence.** The 0.25 s window
  tolerance backfills a literal 2-tick gap with the neighbouring detection,
  so RULE_3C's effective silence requirement is ~0.7–1.0 s rather than the
  nominal 0.4 s (Phase 10.1 §4.2). Reported so the number is not misread.
- **Event_010 frame-count discrepancy (+1)** in the Mission 43 assembly was
  reconciled to an extra query frame; recorded in the Mission 43 report.

## 4. What is NOT an error

- The gates refusing execution (Missions 40–43, and the present programme)
  is governance working as designed, not a malfunction; no refusal was
  circumvented.
- v1 never opening the gate in single-camera disappearance scenarios (S6)
  is the frozen policy's stated semantics (positive evidence only) — safe
  but non-functional for departure. The researchers decided the policy
  question on 2026-11-09: v2 adopted as canonical experimental policy with
  the RULE_3C deviation recorded; v1 retained as the frozen baseline.
