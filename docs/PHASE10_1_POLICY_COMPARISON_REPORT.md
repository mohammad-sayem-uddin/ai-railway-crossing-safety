# Phase 10.1 — Restricted Candidate-Policy Experiment

**Status:** Restricted, authorized comparison complete, strictly scoped to the 11 existing `CALIBRATION_SUPPORTED` events. No full-cohort B3/B4/B6/B7 execution. No deployment authorized. No new model inference performed.

**Scope:** Prepare, verify preconditions for, and execute a restricted comparison of the frozen policy and `configs/decision_policy_v2_candidate.yaml` on exactly the 11 authorized events, with the diagnostic observability and safety re-verification the Phase 10.1 brief specifies, and a precise, per-event explanation for every event that still does not reach `CROSSING_CLEAR`.

---

## 1. Preserve research integrity

**Preconditions verified before any replay ran** (`scripts/run_phase10_1_candidate_comparison.py`'s `_verify_preconditions`, which aborts with a clear message rather than proceeding if any check fails):

- All 33 expected Phase 8 cache files (11 events × {front vision, back vision, audio}) present.
- `configs/decision_policy_v2_candidate.yaml`'s canonical hash re-verified **at execution time** against the hash recorded in the Phase 10 report: `143782d15632d2d840e3c3a1d0437a113cd810356d8ce59757d1b6b97f55ea60` — **match confirmed**, proving the candidate had not changed since Phase 10.
- Phase 9's and Phase 10's output directories present (needed for the cross-validation in Section 6).

**Preserved and re-verified at the end of this phase:**
- Phase 8 output (46 files): byte-identical to the baseline preserved since Phase 9.
- Phase 9 output directory (23 files) and Phase 10 output directory (45 files): present, never opened for writing by this phase.
- `configs/frozen_experiment_v1.yaml` hash: `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e` (unchanged).
- `configs/decision_policy_v1.yaml` hash: `051c908d4db23687db33cbc8349945b241a0735b362413be876d7017a5eacc9d` (unchanged, not modified).
- `configs/decision_policy_v2_candidate.yaml` hash: `143782d15632d2d840e3c3a1d0437a113cd810356d8ce59757d1b6b97f55ea60` (unchanged).
- No model weights or thresholds modified. `data/ground_truth/` not touched; no ground-truth file read or written anywhere in this phase.
- Git HEAD unchanged at `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`; nothing staged or committed.

Output written to a new, unique directory:
`results/r04_sync_estimation/phase10_1_restricted_comparison_20261014T054615Z/`.

---

## 2. A fair comparison, confirmed

Both policies, for every event, were replayed from **byte-identical inputs**: the same cached vision/audio evidence (no new model inference — same `LayerBEventProcessor` cache-hit path Phase 9/10 used), the same `load_validated_sync_aligner`-validated offset, the same frozen `FrozenExperimentConfig` timing/threshold values, the same stride, and the same replay facility (`run_with_diagnostics`), differing only in `engine_factory` (and the evidence-annotation functions, which never feed back into either engine's decisions). The run manifest records the exact frozen config hash, candidate policy hash, and candidate policy version for the run, and confirms **exactly the 11 authorized events** were processed (`"exactly_11_events": true`).

**Cross-validation against prior phases, performed automatically by the script and confirmed:**
- `frozen_reproduces_phase9_naive_duration: true` — the frozen policy's `CROSSING_CLEAR` outcome, under the same (naive) duration computation Phase 9 used, matches Phase 9's results for all 11 events exactly.
- `candidate_reproduces_phase10_naive_duration: true` — the candidate policy's outcome, under the same duration, matches Phase 10's results for all 11 events exactly.

This confirms both policies behave deterministically and reproducibly across independent runs, and that nothing about either engine changed between Phase 10 and this phase (other than the diagnostic facility's new sync-safety gate, Section 5, which does not affect any of these 11 events since all have valid aligners).

---

## 3. Diagnostic observability added

Every event/policy/duration combination's full tick-by-tick trace (`*_diagnostic_ticks.jsonl`) already carries, per Phase 9/10's `DiagnosticTick` schema (unchanged, still version 1.0.0): state transitions and timestamps, rule IDs and explanations, clearance-dwell start/elapsed, source health/observation-age, and per-tick evidence references. This phase's run manifest adds, per event and per policy/duration combination, exactly what the brief requested and was previously only reconstructable by hand:

- **Detection counts by camera and class** (`detection_counts_by_camera_and_class`), computed once per event directly from the cached vision records, independent of either policy.
- **New-train interruption events**: an explicit list of every `RULE_7`-equivalent firing with its timestamp and the state it interrupted (`new_train_interrupt_events`), plus a count.
- **Duplicate/out-of-order rejection counts**: `rejected_observations` and `rejections_by_reason` (unchanged mechanism from Phase 9, now in the per-run summary rather than only the raw JSONL).
- **Stale-source abort counts** (`stale_source_abort_count`).
- **Gate commands/states**: already per-tick in the diagnostic ticks (`gate_command`, `resulting_gate_state`, `gate_angle_deg`, `is_passage_blocked`).
- **Errors/rejected evidence**: the rejection summary; no exceptions occurred during this run (all 11 events processed cleanly).

Raw cached evidence was read, never modified — confirmed by the preservation checks in Section 1.

---

## 4. The five unresolved events: exact, individually-diagnosed reasons

Phase 10's report attributed all 5 non-clearing events (`002`, `005`, `006`, `007`, `017`) to one blanket mechanism ("back camera's near-continuous detection density prevents disappearance confirmation"). This phase's deeper investigation found that is **only part of the picture**, and gives each event its own precise, individually-confirmed reason.

### 4.1 A real, previously-undetected artifact: naive duration truncates the replay window

Investigating the cached predictions directly surfaced a defect in how `duration_s` has been computed since **Phase 8's original script** (inherited unchanged into Phase 9's and Phase 10's replay drivers): it takes `max()` across **raw, unaligned local timestamps** from different cameras, which start their local clocks at different real times. Since the back camera's local clock needs its own validated offset (`back_offset_s`, 3.3–9.4s across these events) added to land on the shared master timeline, the naive computation silently **truncates the replay window by 1.1–5.1 seconds** for every one of the 11 events — always truncating exactly the back camera's latest, most-recent evidence.

| Event | back_offset_s | Naive duration (s) | Corrected duration (s) | Truncated by (s) |
|---|---|---|---|---|
| event_001 | 7.41 | 49.64 | 53.44 | 3.80 |
| event_002 | 4.19 | 32.42 | 34.19 | 1.77 |
| event_005 | 6.04 | 79.50 | 84.04 | 4.54 |
| event_006 | 4.51 | 126.81 | 131.32 | 4.51 |
| event_007 | 8.88 | 38.23 | 43.28 | 5.06 |
| event_009 | 9.40 | 42.83 | 46.81 | 3.98 |
| event_011 | 5.27 | 37.63 | 42.47 | 4.85 |
| event_012 | 5.57 | 75.05 | 76.17 | 1.12 |
| event_013 | 3.28 | 73.65 | 76.32 | 2.66 |
| event_014 | 4.08 | 55.00 | 57.49 | 2.49 |
| event_017 | 4.57 | 83.61 | 88.17 | 4.57 |

This affects **both policies identically** (same shared replay infrastructure, same inputs) — it is a replay-instrumentation artifact, not a frozen-vs-candidate asymmetry, so every comparison in Phase 10's report remains a fair, apples-to-apples comparison between the two policies. It does, however, mean Phase 10's per-event "did it clear" results were each evaluated on a slightly incomplete evidence window. This phase re-ran every event under **both** the naive (Phase 9/10-matching) and a corrected (sync-offset-aware) duration for full rigor; corrected-duration results use only the already-cached evidence, no new inference.

**Result of the correction: it changes nothing about which events clear.** Both the naive and corrected replays give identical `CROSSING_CLEAR` outcomes for all 11 events under both policies. The missing evidence window, while real, was not by itself the reason any event failed to clear — except where noted in Section 4.2.

### 4.2 Per-event diagnosis

| Event | Exact reason for not reaching `CROSSING_CLEAR` |
|---|---|
| **event_002** | **Insufficient recording length, not oscillation.** Departure *is* genuinely confirmed via `RULE_3B_DEPARTURE_CONFIRMED_UNAMBIGUOUS_REAR` at corrected master time t=33.2s — the back camera's one real cluster of `"rear"` labels (6 detections, local t=29.0–30.0s) becomes visible on the master timeline only once the offset-correction is applied (it falls entirely outside the naive, truncated window). But the cached recording ends at t=34.0s — only **0.8s** after confirmation, far short of the ~3.2–3.6s a dwell needs (Section 2 of the Phase 9 report). Confirmed via a controlled synthetic fixture (`test_recording_ends_shortly_after_late_departure_confirmation_cannot_complete_dwell`) reproducing exactly this 0.8s-margin scenario: departure confirms, dwell starts, recording ends before it can complete. **This is a data/recording-length limitation, not a policy or model defect.** |
| **event_006** | **Same mechanism as event_002, more marginal.** Last departure-confirmation attempt (`RULE_3C`, disappearance) at t=128.4s; recording ends at t=131.2s — **2.8s** margin, still short of the ~3.2–3.6s needed, but closer to sufficient than event_002. |
| **event_005** | **Density-prevented disappearance confirmation**, with ample remaining time. Last confirmation attempt at t=12.4s; the recording continues to t=84.0s (71.6s of unused margin), but the back camera's `"side"`-labeled detections (93% of its frames) never again leave a genuine ≥2-consecutive-tick silence gap for the entire remaining duration. |
| **event_007** | Same density mechanism as event_005. Last confirmation attempt at t=20.2s; 23.0s of remaining margin, never used. |
| **event_017** | Same density mechanism. Last confirmation attempt at t=47.8s; 40.2s of remaining margin, never used. |

For `event_005`/`007`/`017`, the mechanism was isolated and confirmed in a minimal, controlled synthetic fixture
(`test_near_continuous_ambiguous_detection_density_prevents_disappearance_confirmation`, `tests/unit/test_phase10_1_unresolved_events_investigation.py`): a departure camera reporting an ambiguous label on every tick except isolated single-tick gaps never confirms departure, for as long as that density continues, regardless of how much extra time is available — matching the real events' measured 89–95% back-camera detection rates. A contrast test
(`test_two_consecutive_silent_ticks_is_sufficient_to_confirm_despite_high_density`) confirms the SAME setup DOES confirm departure once a genuine silence gap is present, proving the mechanism is specifically about gap length, not about `"side"` labels being categorically unconfirmable.

**A further calibration detail found while building that contrast test:** the collector's `window_tolerance_s=0.25` frame-matching backfills a literal 2-tick (0.4s) gap in the raw evidence with the nearest neighboring detection, so the *effective* silence threshold `RULE_3C` needs in practice is closer to ~0.7–1.0s than the nominal `confirm_frames * tick_s = 0.4s`. This does not change any conclusion above (both the real events and the synthetic reproduction already exceed this effective threshold) but is recorded here for anyone reasoning about the exact numbers later.

### 4.3 Does the departure camera's viewpoint and role justify the current fallback?

Directly inspected: one frame each from `event_005`'s front and back camera footage (`data/raw/layer_b/v2/train_events/event_005/camera_front.mov`, `camera_back.mov`). **Both cameras are lateral, trackside cameras positioned at different points along the route — neither is an axial camera looking down the track from in front of or behind the train.** Both frames show the train almost entirely in side profile. No camera geometry or site-survey documentation exists anywhere in this repository to formally specify viewing angles (confirmed absent in `docs/R04_CALIBRATION_VALIDATION_REPORT.md`, which explicitly notes no site survey was ever performed); this direct visual inspection is the only available evidence.

This has two consequences for the candidate's design:
1. **The near-universal `"side"` classification on the back camera is the physically correct description of what that camera sees for almost the entire time a train is in its frame** — not a model defect, and not inherently a directional signal in either direction, confirming the Phase 10 label-semantics design choice.
2. **"Departure role" is justified as a positional claim (this camera is further along the track, toward the departure side) but NOT as a claim that this camera would, by viewing geometry, predominantly produce an axial `"rear"` view.** Checking exactly when the rare real `"rear"` detections occur (6/11 events had any at all, 1–8 occurrences each) shows they cluster tightly in the final 1–2 seconds of several events (`event_002`: local t=29.0–30.0 of a 30.0s clip; `event_013`: t=71.6–73.0 of 73.0s) — consistent with the train's true rear becoming visible at an oblique angle only as the last car exits the lateral camera's effective frame, not a model error. **`"rear"` is a real, physically meaningful, but necessarily rare and necessarily late signal given this camera geometry.**

**Conclusion: the departure camera's physical viewpoint justifies using it as the authoritative sensor for departure confirmation (a positional/role claim), but does NOT justify expecting an unambiguous `"rear"` label to be the primary confirmation pathway (an orientation claim the geometry does not support).** This means `RULE_3C` (sustained disappearance) is not merely a fallback for sparse data — given this camera's actual geometry, it is the **necessarily primary** mechanism, with `RULE_3B` (unambiguous `"rear"`) correctly understood as a rare, late-arriving bonus confirmation rather than the main pathway. This reframes, but does not reverse, Phase 10's framing of `RULE_3B` vs `RULE_3C`.

No threshold was lowered and no directional evidence was invented anywhere in this investigation to increase the clearance count, per the brief's explicit instruction.

---

## 5. Safety requirements re-verified

| Check | Result |
|---|---|
| Stale-source fail-safe behavior | Re-confirmed via Phase 10's existing dedicated test and directly in this phase's real-event replay: zero `RULE_5_STALE_SOURCE_ABORT` firings across all 11 events for both policies (genuinely no stale-source scenario occurred in real data); the synthetic test confirms both policies still correctly clamp to `FAULT_FAIL_SAFE` when one is injected. |
| Duplicate and out-of-order observations | Zero rejected observations across all 11 real events for both policies; Phase 10's dedicated test re-confirms both policies process an identical, deduplicated tick sequence from synthetic duplicate/out-of-order input. |
| Genuine new-train interruption | Re-confirmed via Phase 10's dedicated test (both policies interrupt on a genuinely new unambiguous approach) and directly observable in the real replay's `new_train_interrupt_events` lists for every event. |
| Interrupted clearance dwell | Re-confirmed via Phase 10's dedicated "interrupted dwell, then recovery" test — a genuine interrupt resets the dwell, and a subsequent genuine re-confirmation is given a fair chance to complete. |
| Missing or invalid synchronization | **A real, previously-unchecked gap found and fixed in this phase**: `experiments/diagnostic_trace.run_with_diagnostics` built its `MultimodalEvidenceCollector` directly and had no equivalent to `LayerBEventProcessor.build_multimodal_frames`'s R04 cross-camera-sync safety gate at all — `MultimodalEvidenceCollector` itself never enforces this invariant; only the production wrapper did. Every real caller of this facility (Phase 9's and Phase 10's replay scripts) always passed a validated `sync_aligner`, so this gap was never actually exercised with bad data in practice, but it was a genuine structural gap for any future caller. **Fixed**: the same check (raising `TimingIntegrityError` when ≥2 vision sources are present with no `sync_aligner`, unless the config explicitly allows unverified zero-offset fusion) is now enforced in `run_with_diagnostics` itself, bringing it to parity with the production path. New dedicated test (`test_unverified_cross_camera_fusion_blocked_for_both_policies`) confirms it fires correctly for both engines; re-ran all of Phase 9's and Phase 10's existing tests afterward (19/19 still passing) to confirm no regression from adding this check. |
| Gate reopening conditions | Two new dedicated tests confirm, for both policies: `GATE_OPENING → IDLE` occurs once `gate_opening_s` elapses after a clean clearance, and `GATE_OPENING → GATE_CLOSING` (reopening aborted) occurs on a genuine new approach during opening. |

**No safety invariant was violated by either policy.** The comparison was not stopped.

---

## 6. Validation (per Task 6)

- **Exactly the 11 authorized events were included**: confirmed programmatically (`"exactly_11_events": true`).
- **The frozen policy reproduces its expected cached-evidence behavior**: confirmed — identical to Phase 9's results under the naive duration (`"frozen_reproduces_phase9_naive_duration": true`, zero mismatches).
- **The candidate policy reproduces the expected replay behavior unless a documented implementation difference explains otherwise**: confirmed identical to Phase 10's results under the naive duration (`"candidate_reproduces_phase10_naive_duration": true`, zero mismatches); the only implementation difference since Phase 10 is the additive sync-safety gate (Section 5), which does not affect any of these 11 events.
- **Both conditions use identical evidence**: confirmed by construction — the same `all_v_recs`/`front_a_recs` lists and the same `sync_aligner` are passed to both engine calls for every event/duration combination.
- **No ground-truth performance metrics are reported**: confirmed — every result in this report is a state-machine trajectory / rule-firing comparison between two decision policies over the same cached evidence. No accuracy, recall, MTR, POR, or safety-improvement claim is made anywhere.

---

## 7. Overall results

| Event | Naive: frozen clear | Naive: candidate clear | Corrected: frozen clear | Corrected: candidate clear |
|---|---|---|---|---|
| event_001 | No | Yes | No | Yes |
| event_002 | No | No | No | No |
| event_005 | No | No | No | No |
| event_006 | No | No | No | No |
| event_007 | No | No | No | No |
| event_009 | No | Yes | No | Yes |
| event_011 | No | Yes | No | Yes |
| event_012 | No | Yes | No | Yes |
| event_013 | No | Yes | No | Yes |
| event_014 | No | Yes | No | Yes |
| event_017 | No | No | No | No |

**Frozen: 0/11 under both duration settings (reproduces Phase 8/9/10 exactly). Candidate: 6/11 under both duration settings** — the duration correction changes no event's outcome. Gate commands remained clean (one close, no premature reopen prior to a confirmed clearance or genuine interrupt) in every event under both policies, matching Phase 8's original observation.

---

## 8. Test results

- `tests/unit/test_phase10_1_safety_checks.py`: 7/7 passed (missing/invalid synchronization × 2 policies + 1 single-camera control, gate reopening × 2 policies, gate-reopening-abort × 2 policies).
- `tests/unit/test_phase10_1_unresolved_events_investigation.py`: 3/3 passed (density-prevents-confirmation, contrast gap-confirms, insufficient-recording-length).
- Combined with Phase 9's 10 tests and Phase 10's 9 tests: **29/29 passed**.
- Full regression suite (`pytest -q --ignore=tests/unit/test_audio_leakage_and_preprocessing.py --ignore=tests/unit/test_audio_training.py`): **346 passed, 3 failed** (up from 336 in Phase 10 by exactly the 10 new tests). The 3 failures are the same pre-existing, environment-local artifact-availability issues identified in Phase 9 and reconfirmed in Phase 10, confirmed untouched by this phase.

---

## 9. Hashes, reconfirmed

- `configs/frozen_experiment_v1.yaml`: `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`
- `configs/decision_policy_v1.yaml`: `051c908d4db23687db33cbc8349945b241a0735b362413be876d7017a5eacc9d`
- `configs/decision_policy_v2_candidate.yaml`: `143782d15632d2d840e3c3a1d0437a113cd810356d8ce59757d1b6b97f55ea60` (unchanged since Phase 10, verified by the run itself before executing)
- Checkpoint hashes: unchanged (enforced by `config.verify_all_safeguards()`, which this script calls before any replay).
- `data/ground_truth/`: untouched.
- Git HEAD: `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`, unchanged; nothing staged or committed.

---

## 10. Remaining limitations

- The duration-truncation artifact (Section 4.1), while confirmed not to change any outcome for these 11 events, is a real, previously-undetected defect inherited from Phase 8's original script and silently present through Phase 9 and Phase 10. It was corrected only inside this phase's own replay script (`scripts/run_phase10_1_candidate_comparison.py`); Phase 8's, 9's, and 10's original scripts/outputs were deliberately left untouched (preservation requirement) and still carry the naive computation. Any future replay work should use the corrected computation.
- `event_002` and `event_006`'s non-clearance is now understood to be substantially a recording-length limitation (0.8s and 2.8s of margin respectively, against a ~3.2–3.6s need) rather than a policy defect — no amount of policy revision can fix a recording that ends before the dwell could possibly complete.
- `event_005`/`007`/`017`'s non-clearance is a genuine, confirmed density/threshold interaction (Section 4.2–4.3): given the back camera's actual viewing geometry and detection rate, `RULE_3C`'s 2-consecutive-tick (effectively ~0.7–1.0s, Section 4.2) silence threshold may be too short relative to real flicker rates for some events — an open, unresolved tuning question, not addressed in this phase per the brief's explicit instruction not to tune the policy merely to increase the clearance count.
- No full-cohort dual-camera experiment was run. No new model inference was performed. No ground-truth-based accuracy, recall, MTR, POR, or safety-improvement claim is made anywhere in this report. No deployment is authorized by this report.

**This restricted experiment does not change the Phase 10 recommendation**: the candidate policy directly and measurably addresses the Phase 9 mechanism with no observed safety regression, remains an incomplete solution for a now much more precisely understood set of reasons, and remains appropriate only for further restricted, explicitly authorized evaluation on this same 11-event subset — not for full-cohort execution or deployment.
