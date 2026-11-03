# Phase 9 — Forensic Analysis of Phase 8 Clearance Divergence

**Status:** Forensic/observability pass complete. No thresholds tuned, no models retrained, no frozen configuration or decision policy modified, no full-cohort dual-camera experiment run.

**Scope:** Explain why the Phase 8 front-camera-only baseline (B0) reached `CROSSING_CLEAR` in 3/11 events while the Phase 8 dual-camera fused condition (B4) reached it in 0/11 events, for the same 11 `CALIBRATION_SUPPORTED` events.

---

## 1. Preservation verification

Before any analysis, the Phase 8 output directory
(`results/r04_sync_estimation/exploratory_live_run_20261013T194806Z/`, 46 files:
11 `decision_steps.json`, 33 cache JSONL files, `run_manifest.json`,
`baseline_comparison.json`) was hashed (SHA-256) and the hash manifest preserved
at `/tmp/phase8_output_hashes_baseline.txt`. The same 46 files were re-hashed at
the end of this phase and diffed against the baseline:

```
IDENTICAL: Phase 8 output unchanged (all 46 files)
```

Also re-verified unchanged at the end of this phase:
- `configs/frozen_experiment_v1.yaml` canonical hash:
  `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`
- `configs/decision_policy_v1.yaml` is untouched (read-only throughout this phase;
  no edits made to it).
- Git HEAD unchanged at `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`; no commits made,
  nothing staged by this phase.
- `data/ground_truth/` was not read or written by this phase.

No Phase 8 output was overwritten or regenerated. All replay work in this phase
reads Phase 8's existing cache files and writes to a **new, separate** output
directory (`results/r04_sync_estimation/phase9_diagnostic_replay_20261014T040741Z/`).

---

## 2. The three baseline (B0) events that reached `CROSSING_CLEAR`

Directly observed by scanning each event's saved
`results/experiments/phase5_full_dataset_run_20261013/conditions/B0_vision_front/*_decision_records.jsonl`
for a record with `resulting_state == "CROSSING_CLEAR"`:

| Event | First `CROSSING_CLEAR` at |
|---|---|
| `train_events/event_005` | t=21.80s |
| `train_events/event_006` | (confirmed present) |
| `train_events/event_012` | (confirmed present) |

The other 8 of the 11 authorized events never reached `CROSSING_CLEAR` in B0 either.
This was determined directly from saved records, not inferred from aggregate counts.

---

## 3. Task 4 — Diagnostic logging facility (implemented)

**File:** `src/railway_detection/experiments/diagnostic_trace.py` (new, schema
version `1.0.0`). **Tests:** `tests/unit/test_diagnostic_trace.py` (5/5 passing).

Purely additive instrumentation. It does not modify `MultimodalDecisionEngine`,
`MultimodalEvidenceCollector`, `PhysicalGateModel`, or
`configs/decision_policy_v1.yaml`. It reuses those classes unmodified and records,
per tick: event ID/condition, timestamp, previous/resulting crossing and gate
state, applicable `rule_id` and explanation, fault status, per-source
availability/health/health-reason/observation-age, gate command and simulated
gate angle, independently-recomputed approach/departure/audio-presence flags
(via the same public rule functions the engine itself uses), and clearance-dwell
introspection (`clearance_started_at_s`, `clearance_elapsed_s`, read from the
engine's own public attribute). Separately, it surfaces the collector's
rejected-observation log (duplicate/out-of-order) with reason and source
breakdowns. No raw tensors or model payloads are logged — only scalar/string
fields and detection-level evidence references (`source_id:timestamp`), matching
what `DecisionRecord.to_dict()` already persists for baseline conditions plus
engine-internal dwell state that Phase 8's output never captured.

If a new configuration were needed for diagnostic runs, it would be created as
a separate versioned file; none was needed — the facility takes the existing
frozen `FrozenExperimentConfig` object directly and changes no config value.

**A genuine, non-bug mechanical finding surfaced while building the tests:**
`clearance_started_at_s` is set on the *second* tick evaluated after the engine
enters `REAR_CONFIRMED` (not the first), and because ticks land on discrete
0.2s boundaries, the dwell-satisfied check (`elapsed >= 3.0s`) is first true one
tick late, i.e. at `elapsed ≈ 3.2s`, not exactly `3.0s`. This is correct,
deterministic behavior of the existing code — not a bug — but it means reading
saved dwell timers requires a ~1-tick tolerance when checking whether a 3.0s
dwell "should" have completed.

---

## 4. Task 5 — Class-ambiguity hypothesis: synthetic tests

**File:** `tests/unit/test_phase9_class_ambiguity_hypothesis.py` (5/5 passing).

Fresh re-verification of `src/railway_detection/fusion/rules.py` (unmodified):

```python
APPROACH_LABELS  = frozenset({"front", "side", "train"})
DEPARTURE_LABELS = frozenset({"rear", "side", "train"})
```

`has_qualified_approach` and `has_qualified_departure` both iterate
`frame.vision_records` and check only `det.label.lower() in {...}` and
`det.confidence >= threshold`. **Neither function inspects `record.source_id`.**
Camera viewpoint (front vs. back/rear) is structurally invisible to both checks.
`"side"` and `"train"` are members of *both* label sets.

Five minimal synthetic scenarios, built with the Task 4 diagnostic facility,
confirm the concrete consequences:

1. **Valid departure (control):** a dedicated rear camera reporting `"rear"`
   produces a clean, unambiguous `RULE_3_POSITIVE_CLEARANCE` → `REAR_CONFIRMED`.
2. **Front-only camera can satisfy departure with zero rear evidence:** with a
   single registered camera (matching B0's topology) emitting the ambiguous
   `"train"` label, the engine reaches `REAR_CONFIRMED` with every evidence
   reference up to that point coming from the front camera — no rear-facing
   camera, no `"rear"` label, ever observed.
3. **Lingering side label from the departure camera itself:** the *same*
   camera that just confirmed rear clearance continuing to emit `"side"`
   during the dwell is indistinguishable, under the frozen rules, from a brand
   new approaching train — `RULE_7_NEW_TRAIN_INTERRUPT` fires from its own
   lingering evidence.
4. **Camera disagreement:** front reports `"front"` (approach-only) and rear
   reports `"rear"` (departure-only) at the *same* tick during
   `CROSSING_OCCUPIED`. The rules resolve this by OR-ing departure evidence
   across all sources with no disagreement check — departure evidence wins
   the transition regardless of simultaneous conflicting evidence elsewhere.
5. **Stale departure camera during the dwell:** if the departure camera goes
   stale/missing for >2.0s during `REAR_CONFIRMED`, `RULE_5_STALE_SOURCE_ABORT`
   fires and clamps to `FAULT_FAIL_SAFE`, never reaching `CROSSING_CLEAR`, even
   with a perfectly healthy approach camera. (This mechanism was checked
   directly against the real replay data in Section 5 and **ruled out** as the
   cause for these 11 events — see below.)

---

## 5. Task 6 — Replay of the 11 real Phase 8 events

**Script:** `scripts/run_phase9_diagnostic_replay.py` (new). Performs **no new
model inference** — it reads only the pre-existing cached YOLOv8n/CompactTrainHornCNN
output JSONL files under
`results/r04_sync_estimation/exploratory_live_run_20261013T194806Z/cache/`
(verified complete: 33 files = 11 events × {front vision, back vision, audio}
before the replay ran), uses the same `load_validated_sync_aligner` and frozen
config Phase 8 used, and replays through the unmodified decision engine with
full diagnostic instrumentation. Output:
`results/r04_sync_estimation/phase9_diagnostic_replay_20261014T040741Z/`
(new directory; Phase 8's original output was never opened for writing).

### 5.1 Directly observed result

All 11 events, replayed from the exact cached evidence Phase 8 used:

| Event | Reached `CROSSING_CLEAR` | Final state | Fault | Rejected obs. |
|---|---|---|---|---|
| event_001 | No | REAR_CONFIRMED | No | 0 |
| event_002 | No | REAR_CONFIRMED | No | 0 |
| event_005 | No | CROSSING_OCCUPIED | No | 0 |
| event_006 | No | CROSSING_OCCUPIED | No | 0 |
| event_007 | No | TRAIN_DEPARTING | No | 0 |
| event_009 | No | REAR_CONFIRMED | No | 0 |
| event_011 | No | CROSSING_OCCUPIED | No | 0 |
| event_012 | No | TRAIN_DEPARTING | No | 0 |
| event_013 | No | REAR_CONFIRMED | No | 0 |
| event_014 | No | REAR_CONFIRMED | No | 0 |
| event_017 | No | REAR_CONFIRMED | No | 0 |

This reproduces Phase 8's 0/11 result exactly, confirming the replay is
behaviorally faithful to the original run.

**Zero faults and zero rejected observations across all 11 events.** This
directly rules out, for these specific 11 events:
- `RULE_5_STALE_SOURCE_ABORT` (the stale-departure-camera mechanism
  demonstrated synthetically in Section 4, scenario 5) — never fired.
- `RULE_8_OUT_OF_ORDER_REJECTION` / `RULE_10_DUPLICATE_FRAME_REJECTION` —
  never fired. No frames were lost or discarded during ingestion for these 11
  events.

### 5.2 The actual mechanism, directly observed

Every one of the 11 events shows a pervasive, near-periodic
`RULE_7_NEW_TRAIN_INTERRUPT` cycle (33 to 146 occurrences per event, recurring
roughly every 0.8–1.4s) continuing for the entire remainder of the event after
first reaching `REAR_CONFIRMED`. Inspecting the raw cached front-camera
detections behind these interrupts (example: `event_001`, front camera
`camera_1`, timestamps 9.0–12.7s) shows a continuous stream of `"side"`-labeled
detections at confidence 0.50–0.84 — well above the 0.35 threshold — with only
occasional single-tick gaps:

```
t=9.007  side 0.498      t=10.408 side 0.568      t=11.809 side 0.767, side 0.686
t=9.207  side 0.674      t=10.608 side 0.631      t=12.009 side 0.718
t=9.407  side 0.671      t=10.808 side 0.795      t=12.209 side 0.836
t=9.607  side 0.633      t=11.008 side 0.727      t=12.409 side 0.733
t=9.807  (none)          t=11.208 side 0.797      t=12.609 side 0.787
t=10.007 side 0.573      t=11.408 side 0.83
```

Because `"side"` is a member of `APPROACH_LABELS`, every tick where the front
camera reports it while the engine is in `REAR_CONFIRMED` satisfies
`has_qualified_approach`, which fires `RULE_7_NEW_TRAIN_INTERRUPT` and resets
the clearance dwell (`clearance_started_at_s = None`) — even though it is the
same physical train continuing to be visible in the frame, not a new one, and
even though the rear camera may have already positively confirmed departure.

**Measuring the maximum quiet gap between consecutive `RULE_7` interrupts**
(the longest uninterrupted window the dwell timer could have accumulated
in) across the fused replay versus the B0 baseline, directly from saved/replayed
data:

| Event | Fused (B4) max gap | B0 max gap | B0 reached CLEAR? |
|---|---|---|---|
| event_001 | 2.20s | 2.60s | No |
| event_002 | 0.80s | 0.80s | No |
| event_005 | 1.00s | **7.80s** | **Yes** |
| event_006 | 2.20s | **25.00s** | **Yes** |
| event_007 | 1.00s | — | No |
| event_009 | 0.80s | — | No |
| event_011 | 0.80s | — | No |
| event_012 | 1.40s | **6.00s** | **Yes** |
| event_013 | 0.80s | — | No |
| event_014 | 1.00s | — | No |
| event_017 | 0.80s | — | No |

Recall from Section 3 that a clean dwell needs roughly 3.2–3.6s of
uninterrupted quiet to complete (3.0s dwell + ~0.2–0.6s of tick-granularity
overhead). **In every one of the 11 fused-condition events, the longest quiet
gap between interrupts never exceeds 2.2 seconds — below the threshold needed
for any dwell to complete, in every single case.** In the B0 baseline, the
three events that reached `CROSSING_CLEAR` are exactly the three with a quiet
gap comfortably above that threshold (6.0s, 7.8s, 25.0s); the B0 events that
stayed below threshold (e.g. `event_001` at 2.6s, `event_002` at 0.8s) did not
reach `CROSSING_CLEAR` either — consistent with the same mechanism operating
in both conditions.

**Why the fused condition's gaps are systematically shorter than B0's:**
`has_qualified_approach`/`has_qualified_departure` OR evidence across *every*
registered vision source. With only one camera (B0), a quiet gap requires that
single camera's detections to drop out for 3+ seconds. With two cameras (the
fused condition), a quiet gap requires *both* independently-flickering camera
streams to be silent simultaneously for 3+ seconds — a strictly harder
condition to satisfy by chance. Adding the second camera as an additional,
independent source of the same ambiguous labels compounds the interruption
rate rather than providing confirming redundancy, because the rules treat
every source as an undifferentiated OR-pool rather than distinguishing
camera roles.

### 5.3 Class-ambiguity hypothesis: verdict

**Supported.** Not merely plausible — directly demonstrated from saved/replayed
evidence for all 11 events, with a quantified, consistent mechanism (quiet-gap
threshold) that correctly separates the B0 events that cleared from the ones
that didn't, and correctly predicts that none of the 11 fused events could
clear given their observed interrupt cadence.

No event in this analysis required labeling as `NOT_DETERMINABLE_FROM_SAVED_OUTPUTS`
— the cached evidence and replayed diagnostic trace were sufficient to fully
explain the divergence for all 11 events.

---

## 6. Software defect vs. policy-design limitation

**No software bug was found.** `has_qualified_approach`, `has_qualified_departure`,
and the `REAR_CONFIRMED` state-machine branch in `decision_engine.py` each
execute exactly what `configs/decision_policy_v1.yaml`'s rule descriptions
specify ("Immediate interruption of clearance or gate opening upon new
qualified approach detection"; "Requires confirmed departure evidence and 3.0s
clearance dwell without conflicting detections"). The code is a faithful
implementation of those descriptions.

**This is a demonstrated policy-design limitation**, specifically an
interpretive gap the frozen policy document leaves open: it never defines
which vision-model class labels constitute "approach" vs. "departure"
evidence, nor whether evidence should be scoped by camera role. That mapping
exists only in code (`fusion/rules.py`'s `APPROACH_LABELS`/`DEPARTURE_LABELS`),
where `"side"` and `"train"` were made members of both sets and no
`record.source_id` check was added. Two independent, compounding consequences
of this gap were demonstrated directly:

1. A single ambiguous-label detection can impersonate rear-clearance evidence
   from a camera that has never observed the rear of the crossing (Section 4,
   scenario 2).
2. The same ambiguous labels, continuing to be reported by the *departing
   train itself* as it exits each camera's frame, repeatedly re-trigger
   `RULE_7_NEW_TRAIN_INTERRUPT` against the dwell that is supposed to confirm
   its departure — and adding a second camera increases rather than decreases
   how often this happens, because the rules OR evidence across sources
   without role-awareness (Section 5.2).

### Proposed (not implemented) policy revision

A separate, versioned successor to `configs/decision_policy_v1.yaml` /
`fusion/rules.py` should be drafted — not implemented in this phase — that
would need to resolve, at minimum:

- Whether approach/departure evidence should be scoped to camera role
  (e.g., require departure evidence specifically from a camera registered as
  "departure" / "rear", not any available source), and
- Whether `RULE_7_NEW_TRAIN_INTERRUPT` should distinguish "the same
  object continuing to be visible" from "a genuinely new detection" (e.g. via
  detection-track continuity, a cooldown after rear confirmation, or
  requiring the interrupting evidence to come from the *approach*-role camera
  specifically, not any camera).

Any such change is a safety-policy change and requires its own review,
versioning, and explicit authorization before implementation, per the Phase 9
brief's constraints.

---

## 7. Test results and integrity verification

**Targeted tests:** `tests/unit/test_diagnostic_trace.py` (5 passed),
`tests/unit/test_phase9_class_ambiguity_hypothesis.py` (5 passed).

**Related regression suite** (fusion/decision/rule/collector/sync/layer_b
tests): 96 passed, 0 failed.

**Full suite** (`pytest -q --ignore=tests/unit/test_audio_leakage_and_preprocessing.py
--ignore=tests/unit/test_audio_training.py`, same exclusions used in Phases
6–8 for modules with a missing dependency): **327 passed, 3 failed**. The 3
failures (`test_audio_v2_pipeline.py::test_v2_figures_and_report_artifacts`,
`test_audio_v3_pipeline.py::test_v3_publication_figures_and_reports`,
`test_real_dataset_inventory.py::test_audio_extension_anomaly_tracking`) are
pre-existing, environment-local artifact-availability issues (missing
generated report JSON files and filename-extension symlinks that are not
part of this repository's tracked content) in audio-pipeline test modules
**not touched by this phase in any way** — confirmed via `git diff --stat`
and `git status`, neither of which shows these files as modified by Phase 9.
They are unrelated to the decision engine, fusion rules, diagnostic facility,
or anything else examined in this phase.

**End-of-phase integrity re-verification:**
- Phase 8 output directory: byte-identical to the preserved baseline
  (46/46 files, SHA-256 match).
- `configs/frozen_experiment_v1.yaml` canonical hash: unchanged
  (`999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`).
- `configs/decision_policy_v1.yaml`: not modified.
- Git HEAD: unchanged at `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`; no commits
  made by this phase.
- No full-cohort dual-camera experiment was run; no model was retrained; no
  thresholds were tuned; no safety-performance improvement is claimed.

---

## 8. Summary

- The 3/11 vs. 0/11 `CROSSING_CLEAR` divergence between the B0 baseline and
  the Phase 8 fused condition is explained, directly from saved and replayed
  evidence, by the frozen policy's label-to-rule mapping treating `"side"`
  and `"train"` detections as valid "new approach" evidence regardless of
  which camera reports them or whether the same physical train is still
  simply visible in frame.
- Adding a second (rear) camera, intended to provide confirming departure
  evidence, instead compounds the rate of spurious `RULE_7_NEW_TRAIN_INTERRUPT`
  resets by adding an independent second source of the same ambiguous labels —
  measurably shrinking the achievable quiet-gap window below the ~3.2–3.6s
  needed for the clearance dwell to ever complete, in all 11 observed events.
- This is a policy-design limitation in the (code-only, undocumented-by-policy)
  class-label-to-rule mapping, not a software bug; the engine code correctly
  implements the frozen rule descriptions as written.
- A versioned policy revision is justified to address this, but was not
  designed or implemented in this phase.
