# Phase 16 — Manuscript Draft (Skeleton)

**Status:** BLOCKED. Depends on Phases 12–15 results.
**Date:** 2026-10-15.

---

## 1. Summary

This is a structural skeleton for the future manuscript. No claims are made. No numbers are presented. The manuscript cannot be written until evaluation results exist.

## 2. Planned Structure

1. **Introduction:** Railway crossing safety; automated detection research question.
2. **Related Work:** Audio-visual fusion for event detection; railway safety systems.
3. **Dataset:** 27-event inventory; three cohorts; media description; annotation protocol.
4. **Method:** YOLOv8n vision; CompactTrainHornCNN audio; temporal fusion; decision engine.
5. **Experiments:** Phase 12 baseline; Phase 13 ablations; Phase 14 latency.
6. **Results:** (BLOCKED — no approved ground truth exists).
7. **Limitations:** R04 unresolved; small n; domain shift; no safety certification.
8. **Conclusion:** Summary of findings and future work.

## 3. Preliminary Evidence Inventory (Not a Completed Audit)

This is only a list of candidate source locations and known gaps. It does not
verify that each artifact supports a claim, establish citation accuracy, or
authorize publication. Any claim not semantically checked against its source
must be removed or marked unresolved.

| Section | Required Evidence | Status |
|---|---|---|
| Dataset description | Inventory and media-hash manifests; semantic audit outstanding | Candidate sources only |
| Method | Source and frozen config; exact analyzed version/hashes to record | Candidate sources only |
| Results | Phase 12 outputs | ❌ Not produced; no claims permitted |
| Ablations | Phase 13 outputs | ❌ Not produced; no claims permitted |
| Latency | Phase 14 outputs | ❌ Not produced; no claims permitted |

## 4. Reproducibility Statement (Unfilled Template)

When results are produced:
- Config hash: **not recorded for a manuscript run**
- Checkpoint hashes: **must be verified and recorded for the exact run; no run is asserted here**
- Seed: **verify against the exact run manifest**
- Device: **verify against the exact run manifest**
- Commands: **not recorded; no Phase 12–14 result run is claimed**

## 5. Safety Language Requirements

- ❌ No safety certification claims.
- ❌ No overclaim beyond evidence.
- ❌ No Audio V2 references as valid model.
- ❌ No raw video in public release without explicit decision.
- ✅ Simulated gate behavior labeled as simulation.
- ✅ R04 unresolved status disclosed.
- ✅ Small-n findings with appropriate CIs.

## 6. Blocked Operations

All Phase 16 content is blocked pending Phases 12–15 results and researcher publication decisions.


---

## Status update — 2026-10-16 (methods, test status and reproducibility record)

This update keeps the skeleton's rule: **no empirical claim is made, because no official or real-data result exists.** It records only what the repository can substantiate.

### A. Methods as implemented (software facts, not results)

| Component | Implemented fact | Source |
|---|---|---|
| Vision | YOLOv8n checkpoint `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` (SHA-256 `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`) | `configs/frozen_experiment_v1.yaml` |
| Audio | CompactTrainHornCNN V3, `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` (SHA-256 `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`), operating threshold 0.3700. The Audio V2 checkpoint is prohibited in the frozen config and is not described or used | same |
| Decision policy | Tick 0.2 s; confirmation 2 ticks; miss tolerance 2; warning dwell 2.0 s; gate closing 3.0 s; clearance dwell 3.0 s; vision confidence 0.35 (approach/departure). Audio has no clearance authority (INV-1). Whether audio may *start* a warning is documented inconsistently (protocol v9 section 12.1 says yes; `OPEN_DECISIONS_AND_BLOCKERS.md` D-5/IMA-20 says the code treats audio as supporting only) and is unresolved. Barrier timing is **simulated** | frozen config; protocol v9 section 12.1; D-5 |
| Frozen configuration identity | canonical SHA-256 `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`; decision policy file SHA-256 `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575` | verified by `evaluation status` |
| Evaluation | Event-level evaluator (`evaluation/metrics.py`, `evaluation_runner.py`, clock-aware `clock_aware.py`): missed-train, premature-opening (the v9 T1 <= t < T4 predicate is the only one implemented and is **not yet a decided definition**), warning lead time, excess closure, clearance latency, no-train nuisance seconds/episodes; Wilson 95% intervals; censored/uncertain boundaries excluded with stated reasons | `docs/PHASE12_EVALUATION_REPORT.md` |
| Ablation / perturbation | Single-factor plans, seeded confidence noise, sensor dropout, timing jitter; synthetic-only engine | `docs/PHASE13_ROBUSTNESS_ABLATION_REPORT.md` |
| Profiling | Stage profiler and claim-free benchmark harness | `docs/PHASE14_PROFILING_INFRASTRUCTURE.md` |

### B. Software verification status (synthetic only)

At repository HEAD `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` plus the uncommitted working tree, the full suite reported **862 passed, 3 failed**. The three failures are pre-existing, unrelated to this work and caused by missing artifacts: two audio-report tests (`test_audio_v2_pipeline`, `test_audio_v3_pipeline`) and one dataset-inventory test (`test_audio_extension_anomaly_tracking`). Passing synthetic tests demonstrate that the code behaves as specified on fabricated fixtures. They are **not** evidence about railway performance and must not be cited as results.

### C. What is unresolved and must appear in the paper

- **No approved ground truth exists.** The 27 legacy review files are invalid, were disowned by the researcher, and are refused by every loader; zero valid Stage-2.1 records exist. Candidate annotations are machine-proposed and unapproved.
- **No official evaluation, ablation, or latency/target-hardware measurement has been run.** Section 6 (Results), the ablation results, and latency claims are therefore empty by design.
- Open researcher decisions (`docs/APPROVAL_RECONCILIATION_REPORT.md` section 7): event-level split; R04 camera-scope record; premature-opening window (protocol v9 vs design M4, pending `[D-10]`; neither has a researcher-attributed acceptance, so the evaluator has no default and an official run is blocked until it is chosen); EVAL-AUTH recording; D1 thresholds; D3(c) audit; D-5 audio warning authority; adjudication and legacy-disposition authorizations.
- R04 camera synchronization is unresolved for 16 of 27 events; the exploratory 11-event dual-camera run is not a validation of hardware synchronization.
- Scope limits to state: one site; two sessions; handheld devices; recordings begin after the train is visible (0/23 train events support true detection latency); the decision policy was revised after a pilot on the same recordings; ground truth is single-annotator unless a second annotator is added; barrier behavior is simulated; negative exposure is about 120.8 camera-stream-seconds, so no per-hour false-alarm rate is stated.
- No safety, SIL or standards-compliance claim is supported by this study.

### D. Reproducibility statement (what can be stated now)

- Environment: Python 3.11.15 in the repository's `.venv`; dependency pins in `requirements.lock` (not independently audited here).
- Verifiable now: frozen-config canonical hash, policy file hash and the two checkpoint hashes above; deterministic canonical-JSON serialization for run manifests; seeds recorded per run manifest.
- **Not yet existing, and therefore not asserted:** a run manifest for any official result, the exact commands that produced results, the device/seed of a result run, or a claim that any number in this paper is reproducible. These must be filled from the actual run manifest when one exists.
- Raw video and audio are not part of any public release without an explicit researcher decision (R-PUB).

---

## Evidence-class ledger and audit — 2026-10-16 (overnight)

Every statement in a manuscript derived from this project must belong to exactly one of these classes. The reproducibility audit (`python -m railway_detection audit reproducibility --json <out> --md <out>`, read-only) checks the repository against this ledger and scans manuscript text for statements the repository cannot support.

| Evidence class | Status today | What may be said |
|---|---|---|
| Implemented software | present | Describe methods as implemented, citing source and tests. |
| Synthetic tests | present (1151 passed, 0 failed on the working tree at the time of this update) | Software behaves as specified on fabricated fixtures. Never railway performance. |
| Layer A perception evaluation (still images) | present: `experiments/vision/39f402dfe460/evaluation/` | Per-image detector metrics on the held-out image split, as recorded there; not system behavior. |
| Real-data event evaluation | NOT OBTAINED | Nothing. No approved Stage-2.1 ground truth exists. |
| Target-hardware measurement | NOT OBTAINED | Nothing. No target platform is declared and no acceptance criterion is documented; development-host timings are labelled as such and make no claim. |
| Controlled validation | NOT OBTAINED | Nothing. No field session has occurred or is authorized. |
| Open decisions | UNRESOLVED | Premature-opening window, event split, R04 scope, EVAL-AUTH record, D1/D3(c), LEG-EXEC. |

The audit currently **fails** the earlier progress report `Railway_Crossing_Automation_Research_Report.docx` (2026-08-31) on overreaching language about system behavior ("eliminating catastrophic premature opening risks", "Guarantees train clearance…", "Flawless…", "successfully … validated", "state-of-the-art") and one unsupported derived figure; its Layer A mAP figures are backed by the vision evaluation artifacts. Those sentences must be rewritten or tagged with `[evidence: <path>]` that resolves before any reuse. This draft itself is audit-clean.
