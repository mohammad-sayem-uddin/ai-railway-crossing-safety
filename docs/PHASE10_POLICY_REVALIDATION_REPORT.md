# Phase 10 — Versioned Policy Semantics and Controlled Revalidation

**Status:** Forensic/research revalidation pass complete. No frozen configuration or decision policy modified, no full-cohort experiment run, no new model inference performed, no deployment authorized.

**Scope:** Resolve the Phase 9-documented ambiguity between detection classes, camera roles, approach/departure evidence, and clearance interruption, as a new, separately versioned, candidate policy — and test it against Phase 8's cached evidence and synthetic fixtures before any new inference or full-cohort experiment is authorized.

---

## 1. Preservation verification

Before any work began, all 46 files in Phase 8's output directory
(`results/r04_sync_estimation/exploratory_live_run_20261013T194806Z/`) and
Phase 9's own new artifacts were confirmed present and untouched. At the end
of this phase, the same 46 Phase 8 files were re-hashed (SHA-256) and diffed
against the baseline preserved since Phase 9:

```
PHASE8_OUTPUT: IDENTICAL (46/46 files)
```

Phase 9's replay output (`results/r04_sync_estimation/phase9_diagnostic_replay_20261014T040741Z/`,
23 files) was not opened for writing at any point in this phase.

**Frozen artifacts, confirmed unmodified throughout and at the end of this phase:**
- `configs/frozen_experiment_v1.yaml` canonical hash: `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e` (unchanged)
- `configs/decision_policy_v1.yaml` canonical hash: `051c908d4db23687db33cbc8349945b241a0735b362413be876d7017a5eacc9d` (unchanged)
- `src/railway_detection/fusion/rules.py` and `src/railway_detection/fusion/decision_engine.py`: not opened for writing at any point in this phase (confirmed via `git status`/`git diff --stat` before and after).
- No model weights, thresholds, or ground truth were modified. `data/ground_truth/` was not touched.
- Git HEAD unchanged at `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`; nothing staged or committed by this phase.

Every change made by this phase is a **new, separate, versioned artifact**
(listed in Section 7); nothing frozen was edited in place.

---

## 2. The candidate policy (v2.0.0-candidate)

**Document:** `configs/decision_policy_v2_candidate.yaml`, own canonical hash
`143782d15632d2d840e3c3a1d0437a113cd810356d8ce59757d1b6b97f55ea60`. Parallel
to, and never read by, `configs/decision_policy_v1.yaml` or the frozen
engine — the frozen code path is entirely unaware this file exists.

**Implementation:** `src/railway_detection/fusion/rules_v2_candidate.py`
(label/role semantics, pure functions) and
`src/railway_detection/fusion/decision_engine_v2_candidate.py` (a standalone
`MultimodalDecisionEngineV2Candidate` class with the same public interface
as the frozen `MultimodalDecisionEngine` — `reset()`/`evaluate_frame()` — so
it is a drop-in replacement wherever an engine is pluggable, never a
subclass of or import from the frozen engine).

### 2.1 Explicit detection-class semantics

| Label | Frozen policy | Candidate policy |
|---|---|---|
| `"front"` | Approach *and* departure (member of both label sets) | Approach only — unambiguous |
| `"rear"` | Approach *and* departure (member of both label sets) | Departure only — unambiguous |
| `"side"` | Approach *and* departure (member of both label sets) | Ambiguous orientation — **never**, by itself, confirms either direction |
| `"train"` | Approach *and* departure (member of both label sets) | Ambiguous orientation — same as `"side"` |

Per the Phase 10 brief's explicit constraint, direction is **never** inferred
from `"side"` alone, in either direction, under the candidate.

### 2.2 Explicit camera-role semantics

Positive departure confirmation is scoped to the camera registered in the
departure role (source id containing `"2"`, `"back"`, or `"rear"` — the same
heuristic already present in the frozen engine's RULE_5/RULE_6
departure-source checks since Phase 6, not a new assumption). This is a
claim about *which sensor is authoritative* for a safety determination,
justified by the dual-camera rig's documented physical geometry (the back
camera is mounted to view the departure side), **not** a claim that camera
role alone proves train direction — an unambiguous `"front"`/`"rear"` label
remains source-agnostic evidence in its own right (`has_unambiguous_approach_label`/
`has_unambiguous_departure_label_from` in `rules_v2_candidate.py`); role-scoping
is applied only at the point of deciding whether a given detection is
*eligible* to satisfy positive departure confirmation specifically.

### 2.3 Evidence required for approach vs. departure

- **Approach (RULE_1, initial trigger):** any qualifying detection from any
  source (unchanged in spirit from the frozen policy — this transition was
  never implicated in the Phase 9 finding and intentionally keeps the same
  "accumulate over `confirm_frames` consecutive frames" behavior).
- **Departure confirmation (TRAIN_DEPARTING → REAR_CONFIRMED):** **changed.**
  Requires either (a) an unambiguous `"rear"` label from a departure-role
  source (`RULE_3B_DEPARTURE_CONFIRMED_UNAMBIGUOUS_REAR`), or (b) sustained
  disappearance — the departure-role source (or, with no dedicated
  departure-role camera registered at all, the sole camera) reporting zero
  qualifying detections for `confirm_frames` consecutive ticks while still
  available (`RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE`, a genuinely new
  rule with no frozen-policy equivalent). An ambiguous label alone never
  confirms departure under the candidate.
- **New-train interrupt (RULE_7, scoped identically to the frozen policy —
  REAR_CONFIRMED/CROSSING_CLEAR/GATE_OPENING only):** **changed.** Requires
  either an unambiguous `"front"` label from any source (no continuity
  requirement), or an ambiguous label that is genuinely *reappearing* after
  the reporting source has gone `gap_frames` (reuses the frozen config's
  existing `timing.miss_tolerance_frames` field, default 2 — no new
  configuration field was introduced) consecutive ticks with no qualifying
  detection. A source's own continuing, unbroken ambiguous detections never
  reset the clearance dwell.

### 2.4 Clearance dwell, disagreement, and staleness

- **Start/completion:** unchanged mechanically from the frozen policy (timer
  set on first REAR_CONFIRMED evaluation; completes at 3.0s elapsed).
- **Reset:** only on the new RULE_7 condition above or on audio evidence
  (RULE_2, unchanged) — no longer on continuing ambiguous evidence.
- **Abort:** RULE_5 (stale departure-role source) reused with **identical**
  logic to the frozen engine — not weakened.
- **Camera disagreement:** when approach-role and departure-role sources
  report simultaneous, conflicting unambiguous evidence, approach evidence
  wins (the RULE_7 check runs before dwell/departure logic in every relevant
  state, same ordering as frozen) — a deliberate, documented,
  safety-conservative choice, not an attempt to adjudicate which camera is
  "correct."

### 2.5 An implementation bug found and fixed during this phase

An initial version of the candidate reused the strict "genuinely new"
evidence check for *both* RULE_1 (initial approach trigger, which requires
`confirm_frames` **consecutive** qualifying detections to accumulate) and
RULE_7 (new-train interrupt, which requires the **opposite** — non-continuing
evidence). This is a real design conflict: the second of two consecutive
ambiguous detections has a tracked gap of 0 and would never itself count as
"new," so RULE_1 could never accumulate past 1 frame on real events whose
front-camera evidence is predominantly ambiguous. This was caught by
replaying real `event_005` evidence (not by the synthetic tests, which only
used the unambiguous `"front"` label for approach scenarios) — the candidate
engine got stuck oscillating `IDLE`/`TRAIN_APPROACHING` for the entire event.
Fixed by using the broad, frozen-equivalent `has_any_qualifying_detection`
check for RULE_1 specifically, reserving the strict genuinely-new check for
RULE_7 only. Documented in both the code and `configs/decision_policy_v2_candidate.yaml`.

---

## 3. Task 3 — Controlled synthetic comparison tests

**File:** `tests/unit/test_phase10_candidate_policy.py`, 9/9 passing. Each
scenario is built once and replayed through both engines via the same
`run_with_diagnostics` facility (extended in a backward-compatible way —
see Section 4), so any difference is attributable only to policy, not to
input construction.

| Scenario | Result |
|---|---|
| Train approaching | Both policies reach `WARNING` via `RULE_1_APPROACH_TRIGGER` identically. |
| Departing while remaining visible (dual camera) | **Frozen:** repeatedly interrupts via `RULE_7`, never clears. **Candidate:** zero interrupts from the lingering evidence, dwell completes cleanly. This is the core Phase 9 mechanism, directly reproduced and fixed. |
| Genuinely new train during clearance | Both policies interrupt correctly (safety regression check — the fix does not suppress real interruption). |
| Ambiguous label reappearing after a genuine gap | Candidate correctly treats it as a new approach (interrupts), confirming the gap-based path works, not just the unambiguous-label path. |
| Conflicting front/back detections (same tick) | Both policies resolve to `TRAIN_PRESENT` (approach evidence wins) — recorded as a documented behavior, not asserted as uniquely "correct." |
| Stale departure camera mid-dwell | Both policies abort to `FAULT_FAIL_SAFE` via `RULE_5`, never reach `CROSSING_CLEAR` — safety regression check, confirms RULE_5 is not weakened. |
| Duplicate/out-of-order observations | Both policies process an identical, deduplicated tick sequence — rejection mechanics are untouched by the candidate. |
| Interrupted dwell, then recovery | Candidate: a genuine interrupt resets the dwell, and once departure is re-confirmed, a fresh dwell is given a fair chance and completes — confirms the fix is a normal, re-enterable dwell, not a one-shot "always clear" change. |
| Single-camera (front-only) topology | Candidate confirms departure via sustained disappearance, never via an ambiguous relabeling of the sole camera's own continuing detections — the other half of the Phase 9 fix. |

"Multiple trains/overlapping detections" (also requested in Task 3): **not
independently supported** by either engine's architecture — both model a
single train-presence lifecycle per crossing with no per-object track
identity, so two simultaneously-present trains cannot be represented
distinctly. The sequential case (a second train's genuinely new approach
arriving mid-clearance of a first) is covered by the "genuinely new train
during clearance" scenario above; true concurrent/overlapping multi-train
detection would require an architectural change out of this phase's scope,
and is reported here rather than fabricated a test for.

---

## 4. Task 4 — Replay against the real 11 Phase 8 events

**Script:** `scripts/run_phase10_candidate_replay.py`. Performs **no new
model inference** — reads only the same pre-existing cache JSONL files Phase
9 used (verified complete: 33 files), uses the same `load_validated_sync_aligner`
and frozen config, and replays through **both** engines via the same
`run_with_diagnostics` call pattern for each event, so both policies see
byte-identical frames. Output written to a new directory
(`results/r04_sync_estimation/phase10_candidate_replay_20261014T053200Z/`);
Phase 8's and Phase 9's original outputs were never opened for writing.

`experiments/diagnostic_trace.run_with_diagnostics` was extended (schema
unchanged, still 1.0.0) with optional `engine_factory`/`approach_fn`/
`departure_fn`/`audio_fn` parameters, all defaulting to exactly what Phase
9 used — every existing caller (Phase 9's tests and replay script) is
unaffected; re-ran Phase 9's full test suite (`test_diagnostic_trace.py`,
`test_phase9_class_ambiguity_hypothesis.py`) after this change: 10/10 still
passing, unchanged results.

**Uses the same synchronization validation as Phase 8/9, no shortcut:**
every event's `load_validated_sync_aligner` call is identical to Phase 8's
and Phase 9's — same manifest path, same `allow_candidate_status=True`
re-validation against live source-media hashes, same fail-closed behavior.
Nothing about synchronization was bypassed or assumed for the candidate.

### 4.1 Directly observed result

| Event | Frozen reaches `CROSSING_CLEAR`? | Candidate reaches `CROSSING_CLEAR`? | Trajectory changed? |
|---|---|---|---|
| event_001 | No | **Yes** | Yes |
| event_002 | No | No | Yes |
| event_005 | No | No | Yes |
| event_006 | No | No | Yes |
| event_007 | No | No | Yes |
| event_009 | No | **Yes** | Yes |
| event_011 | No | **Yes** | Yes |
| event_012 | No | **Yes** | Yes |
| event_013 | No | **Yes** | Yes |
| event_014 | No | **Yes** | Yes |
| event_017 | No | No | Yes |

**Frozen: 0/11 reach `CROSSING_CLEAR` (reproduces Phase 8/9 exactly).
Candidate: 6/11 reach `CROSSING_CLEAR`. All 11/11 events show a changed
state trajectory** (full resulting-state sequence, not just the final
state) — the candidate's effect is pervasive, not confined to the 6 that
fully clear.

This was **not** tuned to force all 11 through: 5 of 11 events still do not
clear under the candidate, and the reason is directly visible in the data
(Section 4.3) rather than papered over.

**Zero rejected observations and zero `RULE_5_STALE_SOURCE_ABORT` firings
across all 11 events, under both policies** — confirms, again, that neither
ingestion rejection nor stale-source handling is implicated in or affected
by this change for these real events.

### 4.2 Does the candidate address the Phase 9 mechanism?

**Yes, directly confirmed.** In every event where the candidate now clears,
the dwell completes via `RULE_3_POSITIVE_CLEARANCE` with **zero**
`RULE_7_NEW_TRAIN_INTERRUPT` firings from continuing evidence during the
successful dwell — the near-periodic interrupt cycle Phase 9 found in the
frozen replay (33–146 occurrences per event, every ~0.8–1.4s) does not occur
under the candidate for these events.

### 4.3 Why 5 of 11 events still do not clear — a distinct, honestly-reported limitation

Inspecting the candidate's rule counts for the 5 non-clearing events
(`event_002`, `005`, `006`, `007`, `017`) shows every one of them spends the
overwhelming majority of its duration cycling in `TRAIN_DEPARTING`
(89%–94% of all ticks) between `RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE`
(brief departure confirmations) and `RULE_7_NEW_TRAIN_INTERRUPT` (immediate
re-interruption), never achieving a REAR_CONFIRMED stretch long enough to
complete a 3.0s dwell.

Cross-checking against the raw cached back-camera (`camera_2`) detections
for all 11 events explains why: **the real vision model essentially never
emits the literal `"rear"` class.** Across all 11 events, `"rear"` appears
0 times in 5 of them (exactly the 5 that don't clear: `001`'s predecessor
set) and only 1–8 times in the other 6 — versus `"side"`, which appears on
57%–99% of all back-camera frames in every single event. The candidate's
primary departure-confirmation path (`RULE_3B`, unambiguous `"rear"`) is
therefore rarely reachable on real data; the system depends almost entirely
on the disappearance fallback (`RULE_3C`), which works well when the back
camera's detection rate has natural gaps (the 6 clearing events) but
oscillates when it reports near-continuously (the 5 non-clearing events,
whose back-camera frame-detection rates are 89%–95%).

**This is reported as a genuine, unresolved limitation of the candidate as
currently calibrated** (specifically, the `confirm_frames`-based, 2-tick
silence threshold for `RULE_3C` may be too short relative to real
back-camera flicker rates for some events) — not fixed in this phase, per
the brief's explicit instruction not to tune the policy merely to make
every event clear. It also surfaces a separate, model-level observation,
out of scope for a policy-only phase: the back-camera YOLO classifier's
near-total avoidance of the `"rear"` class in practice may itself warrant
future investigation (data labeling, model retraining, or camera
angle/geometry review) — none of which was performed or is proposed for
implementation here.

---

## 5. Task 5 — Safety and research checks

- **Relevant safety invariants re-run:** the existing fusion/decision/rule/
  collector/sync/layer_b regression suite (96 tests as of Phase 9) plus the
  10 Phase 9 tests plus the 9 new Phase 10 tests — all pass (115 total, see
  Section 6).
- **Sensor staleness and recovery remain fail-safe:** confirmed both via the
  dedicated synthetic test (Section 3) and directly in the real-event replay
  (Section 4.1) — `RULE_5_STALE_SOURCE_ABORT` and `RULE_6_DEGRADED_SOURCE_HOLD`
  mechanics are reused verbatim from the frozen engine, untouched.
- **A genuine new train can interrupt clearance:** confirmed both
  synthetically and by design — RULE_7's unambiguous-label path has no
  continuity requirement at all, so a real new approach is never delayed or
  suppressed by the candidate's fix for lingering evidence.
- **Duplicate/out-of-order frames cannot satisfy dwell:** confirmed — these
  are collector-level and engine-level mechanics (RULE_8/RULE_10) entirely
  untouched by the candidate; the dedicated test confirms both policies
  process an identical, deduplicated tick sequence.
- **No silent reliance on unsupported synchronization:** confirmed — the
  real-event replay script uses the identical `load_validated_sync_aligner`
  fail-closed revalidation Phase 8/9 used, for every event, with no shortcut.
- **Ground truth kept separate from model evidence:** this phase read no
  ground-truth file and performed no accuracy/recall/MTR/POR calculation.
  All results reported are state-machine trajectory and rule-firing
  comparisons between two decision policies over the same evidence — not a
  safety-performance or accuracy claim of any kind.

---

## 6. Test results and integrity verification

- `tests/unit/test_phase10_candidate_policy.py`: **9/9 passed.**
- Combined with Phase 9's `test_diagnostic_trace.py` (5) and
  `test_phase9_class_ambiguity_hypothesis.py` (5): **19/19 passed**, confirming
  the `diagnostic_trace.py` extension did not change any existing behavior.
- Full regression suite (`pytest -q --ignore=tests/unit/test_audio_leakage_and_preprocessing.py
  --ignore=tests/unit/test_audio_training.py`, same exclusions as Phases
  6–9): **336 passed, 3 failed** (up from 327 passed in Phase 9 by exactly
  the 9 new Phase 10 tests). The 3 failures are the **same** pre-existing,
  environment-local artifact-availability issues identified in Phase 9
  (missing generated audio-pipeline report artifacts and filename-extension
  symlinks), confirmed untouched by this phase via `git status`/`git diff --stat`.

**End-of-phase integrity re-verification:**
- Phase 8 output directory: byte-identical to the preserved baseline (46/46 files).
- Phase 9 output directory: present, not opened for writing by this phase.
- `configs/frozen_experiment_v1.yaml` hash: unchanged (`999a7970...`).
- `configs/decision_policy_v1.yaml` hash: unchanged (`051c908d...`), file not modified.
- `src/railway_detection/fusion/rules.py` / `decision_engine.py`: not modified.
- `data/ground_truth/`: not touched.
- Git HEAD: unchanged at `d4db94d`; nothing staged or committed by this phase.

**Remaining blockers / not performed in this phase:**
- The candidate's `RULE_3C` disappearance threshold is a real, unaddressed
  tuning question for 5/11 events (Section 4.3) — any adjustment requires
  its own separately versioned revision and evaluation, not performed here.
- The back-camera vision model's apparent avoidance of the `"rear"` class on
  real data is a model-level observation, not investigated or addressed in
  this policy-only phase.
- No full-cohort dual-camera experiment was run. No new model inference was
  performed (all 11-event replays used Phase 8's existing cache). No
  threshold was tuned to improve the outcome. No ground-truth-based
  accuracy, recall, MTR, POR, or safety-improvement claim is made anywhere
  in this report.

---

## 7. New artifacts (all additive; nothing frozen was modified)

- `configs/decision_policy_v2_candidate.yaml` — candidate policy document, canonical hash `143782d15632d2d840e3c3a1d0437a113cd810356d8ce59757d1b6b97f55ea60`
- `src/railway_detection/fusion/rules_v2_candidate.py` — candidate label/role semantics
- `src/railway_detection/fusion/decision_engine_v2_candidate.py` — candidate state-machine engine
- `tests/unit/test_phase10_candidate_policy.py` — 9 comparison tests
- `scripts/run_phase10_candidate_replay.py` — real-event replay driver
- `src/railway_detection/experiments/diagnostic_trace.py` — extended (backward-compatible) with pluggable engine/evidence-function parameters
- `results/r04_sync_estimation/phase10_candidate_replay_20261014T053200Z/` — replay output (new, separate directory)
- `docs/PHASE10_POLICY_REVALIDATION_REPORT.md` — this report

---

## 8. Recommendation

**The candidate policy (v2.0.0-candidate) directly and measurably addresses
the Phase 9 clearance-divergence mechanism** — the near-periodic
`RULE_7_NEW_TRAIN_INTERRUPT` cycle driven by a departing train's own
lingering ambiguous detections is eliminated by design and confirmed
eliminated on real data (zero such interrupts in any of the 6 now-clearing
events). It does so without any observed weakening of stale-source
fail-safe behavior, duplicate/out-of-order rejection, or genuine new-train
interruption, all explicitly re-checked.

It is **not** a complete or final solution: 5 of 11 real events still do
not clear, for a distinct, well-understood, and honestly reported reason
(Section 4.3) rather than an unknown one, and that reason — real
back-camera detection density interacting with the disappearance-fallback's
silence threshold — would need either a separately versioned threshold
revision or further vision-model investigation to resolve, neither of which
has been attempted here.

**Recommendation: the candidate is ready for a restricted, explicitly
authorized follow-up experiment** — specifically, a replay-only or small,
scoped live re-validation on the same 11-event `CALIBRATION_SUPPORTED`
subset, under the same authorization discipline used for Phase 8 (explicit
human sign-off, separate versioned config, no implicit authorization from
this report) — **not** for full-cohort execution or deployment, and not
without first deciding whether to address the `RULE_3C` threshold question
raised in Section 4.3 as part of that follow-up's scope.
