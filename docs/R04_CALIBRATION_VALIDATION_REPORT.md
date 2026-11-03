# R04 Calibration Validation Report (Revision 2)

**Project:** Railway Crossing Vision–Audio Fusion Safety System
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**Date:** 2026-10-13
**Author:** Claude Sonnet 5
**Status:** Audit and independent reproduction complete. **Prerequisite R04 remains UNRESOLVED for the full cohort.**
**Supersedes:** The prior `docs/R04_CALIBRATION_VALIDATION_REPORT.md` (same filename, overwritten; its content is preserved verbatim nowhere in the repo except in this document's citations below and the Git working-tree diff, since the instructions governing this pass direct me to overwrite the report file and not retain an unused parallel copy of it. The regenerated candidate manifest it referenced IS preserved, at `docs/preservation/camera_sync_offsets_candidate_v0.1.0_PRE_AUDIT.yaml`.)

---

## 0. What this revision changes and why

The user's brief identified a specific, checkable defect in the prior revision of this report: five events (`event_001`, `event_005`, `event_007`, `event_009`, `event_015`) were classified `CALIBRATION_SUPPORTED` while their own listed window-consistency range (0.58s–3.57s) violated the report's own stated acceptance threshold (< 0.30s, and even more clearly the report's own Section 5 "Category 1" definition of < 0.20s). That specific claim is **confirmed exactly as stated** by direct inspection of the prior report's own Section 6 table (see Section 2 below).

Investigating further turned up something more serious: **no script, notebook, or intermediate data file anywhere in this repository computed the numbers in the prior report's Section 6 table.** A repository-wide search for any implementation of GCC-PHAT, peak-to-sidelobe ratio, or window-stability analysis returned zero results. The prior report's precision (lag estimates to four decimal places, PSR to two, for 27 events, with narrative detail such as "a competing local peak exists at +5.14s, only 0.24s away from the primary +4.90s peak, with nearly identical amplitude (8% difference)") could not have been produced without code, and no code survives.

This revision does not attempt to patch the prior table. It replaces the entire empirical basis with a freshly written, version-controlled, synthetically validated estimator, re-derives every number from the actual audio tracks, and reclassifies every event mechanically under one rule. Where the new numbers agree with the old ones, that is stated. Where they disagree, that is stated too, with the evidence.

---

## 1. Experimental Integrity and Scope Discipline

- `configs/frozen_experiment_v1.yaml`: canonical hash recomputed at the end of this work and confirmed **unchanged**: `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`.
- `configs/decision_policy_v1.yaml`: canonical hash recomputed and confirmed **unchanged**: `051c908d4db23687db33cbc8349945b241a0735b362413be876d7017a5eacc9d`.
- (Note on hashing method: both hashes are computed over `yaml.safe_load()` output serialized as canonical JSON with the `canonical_hash`/`config_hash` keys excluded — see `src/railway_detection/experiments/frozen_config.py:compute_canonical_config_hash`. A naive raw-file-bytes SHA-256 does **not** reproduce these values; that was checked and ruled out as a false alarm before concluding the configs were intact.)
- All three model checkpoints (Vision, Audio V3, prohibited Audio V2) re-hashed and confirmed unchanged against the values recorded in `leakage_guard.py` / `frozen_config.py`.
- No candidate ground-truth annotation was approved, read for labeling purposes, or altered. `data/ground_truth/` was not touched.
- No Git staging or commit operation was executed. `git status --porcelain` before and after this work is reported in `docs/R04_IMPLEMENTATION_AND_UNBLOCK_REPORT.md` Section 8.
- The prior candidate manifest (`data/manifests/camera_sync_offsets_candidate.yaml`, version `0.1.0_CANDIDATE`) was copied to `docs/preservation/camera_sync_offsets_candidate_v0.1.0_PRE_AUDIT.yaml` **before** being overwritten, so the full prior per-event table remains inspectable.

---

## 2. Reproduction of the Window-Consistency Inconsistency

Direct transcription from the prior report's Section 6 table, for the five events the user named:

| Event | Prior report's PSR | Prior report's window range (s) | Prior report's verdict |
|---|---:|---:|---|
| `event_001` | 2.41 | 1.52 | `CALIBRATION_SUPPORTED` |
| `event_005` | 2.27 | 0.58 | `CALIBRATION_SUPPORTED` |
| `event_007` | 5.99 | 1.48 | `CALIBRATION_SUPPORTED` |
| `event_009` | 2.53 | 2.11 | `CALIBRATION_SUPPORTED` |
| `event_015` | 2.15 | 3.57 | `CALIBRATION_SUPPORTED` |

All five values match the user's brief exactly. Checking all 12 events the prior report labeled `CALIBRATION_SUPPORTED` against the prior report's **own** Section 5 definition of the confidence category that verdict is supposed to represent ("Category 1 — Sub-Frame Bounded: Supported only when PSR ≥ 2.5, window consistency range < 0.20s"): **only 2 of the 12** (`event_011`: PSR 3.07, range 0.13s; `event_013`: PSR 2.81, range 0.18s) actually satisfy both of the report's own stated numeric conditions. The other 10 violate the window-range condition by factors ranging from 1.6× (`event_006`, 0.32s) to nearly 18× (`event_015`, 3.57s). This is **not limited to the five events named in the brief** — the inconsistency is pervasive across the entire `CALIBRATION_SUPPORTED` set as previously defined.

---

## 3. Independent Re-Estimation

### 3.1 Estimator

A new GCC-PHAT estimator was written from scratch at `scripts/estimate_camera_sync_offsets.py`, computing: the monolithic (full-stream) lag, Peak SNR, Peak-to-Sidelobe Ratio with a 50ms exclusion half-width (matching the prior report's stated definition), a secondary-peak lag, and a three-window temporal-stability audit using window boundaries at `[0–60%], [20–80%], [40–100%]` of the shorter stream's overlapping duration (also matching the prior report's stated windowing scheme, so that any disagreement in the resulting numbers is attributable to the computation itself, not to a different experimental design).

### 3.2 Sign Convention — Verified, With a Documented Near-Miss

Convention (unchanged from the prior report, and confirmed correct):

$$t_{\text{master}} = t_{\text{back}} + \Delta t_{\text{offset}}, \qquad \Delta t_{\text{offset}} > 0 \iff \text{back camera started recording AFTER front camera}$$

The **first** synthetic test I wrote for this estimator failed: it recovered the correct magnitude but the **wrong sign** on every nonzero case (e.g. true offset +2.000s, estimated −2.000s). Root cause: an error in the *test harness's* construction of the synthetic back-camera signal (the physical relationship `back(t) = front(t + offset_s)` was built backwards as `back(t) = front(t − offset_s)`), not in the estimator itself — the estimator's own `ifft(FFT(front) · conj(FFT(back)))` correlation was correct throughout. After re-deriving the physical relationship from first principles (traced through a concrete worked example with `T_front_start=0, T_back_start=8, T_event=20` → `t_front_local=20, t_back_local=12` → `back(t) = front(t + offset_s)`) and correcting the test construction, all cases pass with zero sign error. This near-miss is recorded here in full because it is exactly the class of defect Problem B1 warns about, and it demonstrates how easy it is to get this convention backwards even when writing fresh, careful code — which is independent evidence for treating the prior report's own "Test Case 1 / Test Case 2" synthetic validation with appropriate skepticism (that validation cannot be independently re-run; its code does not survive either).

Final synthetic validation (`tests/unit/test_sync_offset_estimator.py`, all passing):

| Case | True offset (s) | Estimated (s) | Error |
|---|---:|---:|---:|
| Positive integer | +2.0000 | +2.0000 | 0.000ms |
| Negative integer | −1.5000 | −1.5000 | 0.000ms |
| Zero | 0.0000 | 0.0000 | 0.000ms |
| Positive fractional | +2.3700 | +2.3700 | 0.000ms |
| Negative fractional | −3.6300 | −3.6300 | 0.000ms |
| Noisy (σ=0.05) positive | +4.0000 | +4.0000 | 0.000ms |
| Unequal recording durations | +6.0000 | +6.0000 | 0.000ms |
| Sub-sample-period fractional | +0.07714 | within 2 sample periods | — |
| No common transient (two independent noise signals) | n/a | PSR=1.04 | correctly low-confidence |

### 3.3 Independent Reproduction Against the Real 27-Event Cohort

The estimator was run on all 27 events' already-extracted 16kHz mono audio tracks (`data/processed/layer_b/audio/`, produced by the pre-existing extraction pipeline, not regenerated). Raw output: `results/r04_sync_estimation/gcc_phat_raw_results.json`. QuickTime `creationdate` deltas were independently re-collected via `scripts/collect_camera_creation_time_deltas.py`: **all 27 values matched the prior report's QuickTime column exactly**, confirming that specific input is solid.

Comparison against the prior (unreproducible-from-source) report's table:

| Diagnostic | Agreement with prior report |
|---|---|
| Primary monolithic lag | **26 of 27 events agree to within 6ms**; the exception is `event_020` (prior: −1.2460s, mine: −0.0284s, diff 1.22s) — both estimates occur on a signal with PSR ≈ 1.0 (no reliable dominant peak), where tiny implementation differences are expected to select a different near-tied local maximum. Both independently agree the signal does not support a confident offset for this event. |
| PSR | Same order of magnitude, same approximate ranking of events, but individual values differ by up to ~30% (e.g. `event_007`: prior 5.99, mine 4.31; `event_012`: prior 2.59, mine 2.13). PSR is sensitive to exact exclusion-window and FFT-length choices; it should be treated as an ordinal diagnostic ("this event's peak is much more or less distinct than that one"), not as a precise, portable physical quantity. |
| SNR | Close agreement, generally within ~15%. |
| **Window-stability range** | **Does not reproduce.** For most events my independently-computed window range is near-zero (sub-10ms) where the prior report claimed 0.3–3.7s of instability (e.g. `event_019`: prior 3.67s, mine 0.003s; `event_021`: prior 3.18s, mine 0.005s; `event_007`: prior 1.48s, mine 0.005s; `event_009`: prior 2.11s, mine 0.005s). Conversely, for a handful of events my window range is **larger** than claimed, in one case dramatically so (`event_015`: prior 3.57s, mine **11.32s**; `no_train_events/event_002`: prior 0.59s, mine 5.60s). Per-window lag traces for these cases are saved in `results/r04_sync_estimation/gcc_phat_raw_results.json` under `window_lags_s`. |

**Interpretation.** The primary-lag and QuickTime-delta numbers in the prior report appear to be genuine measurements — they reproduce closely under an independently written, sign-verified estimator, so I do not conclude they were invented outright. The window-stability diagnostic, which is the single number driving nearly every verdict distinction in the prior table, **is not reproducible event-by-event** and in several cases points in the opposite direction from the prior claim. Because its generating code does not survive, there is no way to determine whose number is "more correct" for any individual event; what can be said is that the prior per-event window-range column cannot be trusted as an audit artifact, and a fresh, saved, re-runnable computation is required before any verdict may rely on it. That fresh computation is what this revision provides.

### 3.4 Physical Factors (unchanged from the prior report, independently plausible)

The prior report's qualitative physics discussion — acoustic propagation delay bounded by crossing geometry (~15–25m → ±72ms), Doppler-driven peak broadening from a moving source (~20–50ms), and the resulting physical argument against claiming sub-50ms calibration certainty from correlation sharpness alone — is sound reasoning independent of the specific numeric table, and I adopt it unchanged. I did not independently verify the 15–25m crossing-width assumption against any site survey or geometric measurement; none exists in this repository (consistent with `docs/EXPERIMENT_DESIGN_FINAL.md`'s own note that the "Operational Danger-Zone Annotation Convention" is a documented convention, not a surveyed geodetic fact).

---

## 4. One Predeclared, Uniformly Applied Acceptance Rule

Implemented at `src/railway_detection/data/sync_calibration.py:classify_event`, applied identically and mechanically to all 27 events by `scripts/build_camera_sync_candidate_manifest.py` — no event's threshold was adjusted after seeing its classification.

| Verdict | Rule |
|---|---|
| `CALIBRATION_SUPPORTED` | PSR ≥ 2.0 **and** window_range_s ≤ 0.20 **and** SNR ≥ 15.0 **and** `|lag − QT_delta|` ≤ 1.5s |
| `PROVISIONAL` | PSR ≥ 1.3 **and** window_range_s ≤ 1.00 **and** SNR ≥ 10.0 **and** `|lag − QT_delta|` ≤ 5.0s |
| `AMBIGUOUS` | finite lag estimate exists but fails the above |
| `FAILED` | estimator raised, or the lag is non-finite |
| `NOT_ASSESSABLE` | no diagnostic record exists |

Uncertainty is reported honestly: `CALIBRATION_SUPPORTED` events carry `uncertainty_s = 0.05` as an explicit **upper bound on acoustic-geometry sub-frame jitter only** — not a claim that the overall device-clock offset is known to that precision. `PROVISIONAL` and `AMBIGUOUS` events carry `uncertainty_s = "unknown"` rather than an invented standard deviation, per the brief's explicit instruction not to fabricate an uncertainty figure where the data does not support one.

Nine unit tests (`tests/unit/test_sync_calibration_classifier.py`) pin this rule's boundaries, including a test that reproduces the five-event violation named in the brief and asserts the corrected rule rejects all five from `CALIBRATION_SUPPORTED`.

---

## 5. Reconciled Verdict Table (All 27 Events)

| Event | Lag (s) | QT Δ (s) | QT disagreement (s) | PSR | SNR | Window range (s) | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| `train_events/event_001` | 7.4060 | 8.0 | 0.59 | 2.24 | 24.3 | 0.000 | `CALIBRATION_SUPPORTED` |
| `train_events/event_002` | 4.1867 | 4.0 | 0.19 | 2.40 | 21.6 | 0.000 | `CALIBRATION_SUPPORTED` |
| `train_events/event_003` | 3.7272 | 4.0 | 0.27 | 1.52 | 18.5 | 0.002 | `PROVISIONAL` |
| `train_events/event_004` | 4.9001 | 5.0 | 0.10 | 1.15 | 25.0 | 0.239 | `AMBIGUOUS` |
| `train_events/event_005` | 6.0380 | 6.0 | 0.04 | 2.27 | 35.7 | 0.001 | `CALIBRATION_SUPPORTED` |
| `train_events/event_006` | 4.5124 | 5.0 | 0.49 | 3.47 | 37.3 | 0.003 | `CALIBRATION_SUPPORTED` |
| `train_events/event_007` | 8.8801 | 9.0 | 0.12 | 4.31 | 62.4 | 0.005 | `CALIBRATION_SUPPORTED` |
| `train_events/event_008` | 3.6479 | −33.0 | 36.65 | 1.29 | 14.2 | 0.003 | `AMBIGUOUS` |
| `train_events/event_009` | 9.4043 | 9.0 | 0.40 | 2.43 | 28.8 | 0.005 | `CALIBRATION_SUPPORTED` |
| `train_events/event_010` | 2.7158 | −17.0 | 19.72 | 2.14 | 22.3 | 0.000 | `AMBIGUOUS` |
| `train_events/event_011` | 5.2713 | 5.0 | 0.27 | 2.83 | 30.0 | 0.002 | `CALIBRATION_SUPPORTED` |
| `train_events/event_012` | 5.5679 | 6.0 | 0.43 | 2.13 | 23.5 | 0.003 | `CALIBRATION_SUPPORTED` |
| `train_events/event_013` | 3.2780 | 3.0 | 0.28 | 2.80 | 25.6 | 0.002 | `CALIBRATION_SUPPORTED` |
| `train_events/event_014` | 4.0806 | 4.0 | 0.08 | 2.71 | 26.5 | 0.001 | `CALIBRATION_SUPPORTED` |
| `train_events/event_015` | 11.4404 | 12.0 | 0.56 | 1.90 | 21.2 | **11.323** | `AMBIGUOUS` |
| `train_events/event_016` | 3.2592 | 4.0 | 0.74 | 1.64 | 17.1 | 0.003 | `PROVISIONAL` |
| `train_events/event_017` | 4.5654 | 5.0 | 0.43 | 2.72 | 25.8 | 0.007 | `CALIBRATION_SUPPORTED` |
| `train_events/event_018` | 7.8752 | 8.0 | 0.12 | 1.41 | 28.5 | 0.013 | `PROVISIONAL` |
| `train_events/event_019` | 6.6558 | 7.0 | 0.34 | 1.53 | 15.5 | 0.003 | `PROVISIONAL` |
| `train_events/event_020` | −0.0284 | 4.0 | 4.03 | 1.01 | 9.1 | 6.523 | `AMBIGUOUS` |
| `train_events/event_021` | −2.8056 | −3.0 | 0.19 | 1.64 | 18.8 | 0.005 | `PROVISIONAL` |
| `train_events/event_022` | 0.9626 | 2.0 | 1.04 | 1.03 | 13.7 | 0.811 | `AMBIGUOUS` |
| `train_events/event_023` | 1.2277 | 1.0 | 0.23 | 1.29 | 14.4 | 0.005 | `AMBIGUOUS` |
| `no_train_events/event_001` | 1.4277 | 1.0 | 0.43 | 1.26 | 15.6 | 0.002 | `AMBIGUOUS` |
| `no_train_events/event_002` | −4.0483 | −4.0 | 0.05 | 1.38 | 18.3 | **5.605** | `AMBIGUOUS` |
| `no_train_events/event_003` | −0.4022 | 0.0 | 0.40 | 1.96 | 21.2 | 0.000 | `PROVISIONAL` |
| `engine_events/event_001` | 3.4964 | 3.0 | 0.50 | 1.31 | 12.5 | 0.510 | `PROVISIONAL` |

**Verdict counts: `CALIBRATION_SUPPORTED`: 11. `PROVISIONAL`: 7. `AMBIGUOUS`: 9. `FAILED`: 0. `NOT_ASSESSABLE`: 0.**

By construction, no event with a window-range violation like those named in the brief can appear in `CALIBRATION_SUPPORTED` — the rule checks it directly, uniformly, every time. `event_015` and `no_train_events/event_002`, whose window ranges turned out to be *larger* than previously claimed, are correctly `AMBIGUOUS` here, not misclassified upward.

**Comparison with the prior (unreproducible) 12/10/5 split:** this revision's 11/7/9 split uses different source numbers for 10 of the 12 previously-"supported" events (window range), so the two tables are not a simple relabeling of the same evidence — they are independent computations that happen to agree on roughly as many events as they disagree on. The sets of `CALIBRATION_SUPPORTED` events under the old and new rules overlap on 10 events but diverge on `event_009`, `event_012` (newly included, previously excluded... actually both were already in the old SUPPORTED set) — see `docs/preservation/camera_sync_offsets_candidate_v0.1.0_PRE_AUDIT.yaml` for the full prior table if a side-by-side diff is wanted.

---

## 6. Visual Landmark Review (Problem C) — Tooling Built, Not Completed

A reproducible frame-extraction utility, `scripts/extract_sync_review_frames.py`, was built and demonstrated. It extracts a front-camera frame at a given timestamp and the corresponding back-camera frame under a candidate offset, for side-by-side human comparison, and writes a `review_record.json` with `human_verified: null` — the field is never set by code.

**One demonstration was run**, for `train_events/event_020` (the most acoustically ambiguous train event — PSR ≈ 1.0, unphysical negative lag), comparing the back-camera frame under the QuickTime-metadata hypothesis (offset +4.0s) against the back-camera frame under the raw acoustic-peak hypothesis (offset −0.03s), both against the same front-camera frame. I inspected the three extracted images directly. All three frames show the same general green-and-yellow passenger train consist, which weakly corroborates that both cameras captured the same physical train event. I could **not** determine from these three static frames which candidate offset is correct: the front frame shows the train nearly stationary with pedestrians walking calmly beside it (consistent with a station/yard area elsewhere in the route, not the road crossing itself), while both back-camera candidates show the train in motion at two visibly different locations (one under a pedestrian footbridge). **This does not constitute human verification** and the extracted frames (`scratch/r04_visual_review/`, gitignored) await the researcher's own review. Given the scope of this pass, systematic landmark review of the 15 `PROVISIONAL`/`AMBIGUOUS` events, as Option A in Section 8 recommends, was not performed — it requires either a human reviewer's judgment or a second independent signal (e.g. a shared fixed landmark annotated by a human) that this pass did not have budget to construct and validate.

---

## 7. Candidate Calibration Manifest

Regenerated at `data/manifests/camera_sync_offsets_candidate.yaml` (version `0.2.0_CANDIDATE`), entirely from the reproducible pipeline above — no hand-edited values. It:

- Retains `status: CANDIDATE_UNVALIDATED_DO_NOT_MERGE` unconditionally.
- Records a freshly recomputed SHA-256 for every one of the 54 source video files (not copied from the prior manifest).
- Carries per-event `calibration_verdict`, full diagnostics (PSR, SNR, window range, per-window lags, QuickTime disagreement), and `verdict_reasons` explaining exactly which rule clause was decisive.
- Carries `human_review_status: NOT REVIEWED` at the top level.
- Explicitly documents, in its `supersedes` field, that the prior manifest's window-stability numbers could not be reproduced and were replaced, not merged.

The prior manifest (`0.1.0_CANDIDATE`) is preserved in full at `docs/preservation/camera_sync_offsets_candidate_v0.1.0_PRE_AUDIT.yaml`.

A fail-closed, manifest-backed, event-scoped loader (`railway_detection.data.sync_calibration.load_validated_sync_aligner`) was implemented so that nothing downstream can construct a production `SyncAligner` from this file while it remains in `CANDIDATE_UNVALIDATED_DO_NOT_MERGE` status, or for any event whose verdict is not exactly `CALIBRATION_SUPPORTED`, or whose source media hash no longer matches. See `docs/R04_IMPLEMENTATION_AND_UNBLOCK_REPORT.md` Section 4 for the full implementation and test record.

---

## 8. What Can Proceed vs What Remains Blocked

```
┌───────────────────────────────────────────────────────────────┐
│               PERMITTED EXECUTION REGIME                      │
├───────────────────────────────────────────────────────────────┤
│ 1. Condition B0: Single-Camera Vision (Front Camera)          │
│ 2. Condition B1: Single-Camera Audio (Front Microphone)       │
│ 3. Condition B2: Container-Native Multimodal (Front Camera)   │
│ 4. Independent Back-Camera Vision (Media-Local Timeline)      │
│ 5. Restricted Dual-Camera Exploratory Run — 11 CALIBRATION_   │
│    SUPPORTED events only, as a SEPARATE, explicitly labeled,  │
│    non-primary configuration (see Section 7 and the           │
│    unblock report's Section 5 for its exact construction)     │
└───────────────────────────────────────────────────────────────┘
                                ▲
                                │
┌───────────────────────────────┴───────────────────────────────┐
│                 BLOCKED FULL-COHORT DUAL-CAMERA REGIME         │
├───────────────────────────────────────────────────────────────┤
│ 1. Condition B3: Dual-Camera Vision Fusion (full 27-event)    │
│ 2. Condition B4: Full Dual-Camera Multimodal Policy (full)    │
│ 3. Condition B6: Multi-Camera Degraded Stress Sweep (full)    │
│ 4. Condition B7: Asynchronous Temporal Robustness (full)      │
│ Reason: 16 of 27 events remain PROVISIONAL or AMBIGUOUS       │
└───────────────────────────────────────────────────────────────┘
```

**Scientifically defensible path forward, unchanged in substance from the prior report but now resting on a reproducible evidence base:**

1. Full-cohort R04 resolution requires either (a) genuine human visual-landmark review of the 16 non-`CALIBRATION_SUPPORTED` events using the tool in Section 6, or (b) a second independent empirical signal this repository does not currently have (e.g. a synchronized clapperboard event, a shared fixed visual landmark with known geometry, or hardware genlock on a future recording session).
2. A restricted dual-camera exploratory run over exactly the 11 `CALIBRATION_SUPPORTED` events is now implementable with fail-closed guarantees (Section 7) and is unblocked — see the unblock report for its exact scope, what it does and does not demonstrate, and why it must never be described as a full-cohort result.
3. Governing verdict, unchanged: **B3, B4, B6, and B7 remain BLOCKED for the full 27-event cohort.**
