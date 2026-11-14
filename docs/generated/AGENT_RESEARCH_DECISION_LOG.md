# Agent Research Decision Log (9-Step Framework)

Maintained in `docs/generated/AGENT_RESEARCH_DECISION_LOG.md` across all autonomous engineering and experimental decisions in this mission. Consolidated archival governance decisions appear in `docs/generated/RESEARCH_DECISION_LOG.md`.

---

## Decision D-01: Reconcile `reproducibility/audit.py` with Verified `phase12_protocol_decision.json`
1. **Problem Statement:** `railway_detection.reproducibility.audit.run_reproducibility_audit()` reported `protocol_version` and `unresolved_decisions.register["premature_opening_window"]` as `UNRESOLVED`, directly contradicting `railway_detection.evaluation.governance.verify_protocol_override()` and live `evaluation status` output (`protocol_profile_sha256` bound since `2026-11-09` commit `d62cc05`).
2. **Existing Design / Data:** [`audit.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/reproducibility/audit.py#L399-L518) called `protocol_choices.unresolved_decisions(None)` and returned a static literal string `"UNRESOLVED (v9 vs M4; no researcher-attributed acceptance)"`.
3. **Why Existing Was Insufficient:** Two official repository CLI commands (`evaluation status` vs `audit reproducibility`) reported mutually contradictory governance states for the identical repository snapshot.
4. **Alternatives Evaluated:**
   - *Option A:* Leave `audit.py` untouched and only note the bug in Markdown reports.
   - *Option B:* Update `audit.py` to inspect `data/manifests/phase12_protocol_decision.json` via [`verify_protocol_override`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/governance.py#L273-L303) while defaulting safely to `UNRESOLVED` whenever the decision JSON is absent (e.g., synthetic isolated tmp workspaces) and `FAIL` if malformed/unlisted.
5. **Selected Choice:** Option B, plus updating stale Oct-29 assertions in [`test_reproducibility_audit.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_reproducibility_audit.py) while adding explicit negative tests confirming `UNRESOLVED` when decision artifacts are absent.
6. **Justification:** Preserves strict fail-closed governance while eliminating live CLI state contradiction without weakening any synthetic governance boundary.
7. **Expected Effect:** `audit reproducibility` transitions `protocol_version` from `UNRESOLVED` -> `PASS` on live `HEAD`, reduces `UNRESOLVED` items cleanly from `4` -> `3` (`approved_ground_truth`, `event_split_decision`, `unresolved_decisions`), and aligns `audit` with `evaluation status`.
8. **Measured Result:** **Verified.** [`audit reproducibility`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/cli/main.py) transitioned to `{"FAIL": 1, "NOT_AVAILABLE": 2, "PASS": 7, "UNRESOLVED": 3}` (`protocol_version = PASS`, `premature_opening_window = recorded (M4 / v9 sensitivity)`); `test_reproducibility_audit.py` passes **`23/23`** including `test_protocol_version_fails_closed_when_override_tampered`.
9. **Limitations:** Does not modify `approved_ground_truth`, `event_split_decision` (`Option A`), or `EVAL_AUTH_NOT_GRANTED`; official evaluation remains strictly `ready: false`.

---

## Decision D-02: Non-Destructive Session-Grouped Vision V1 & Stem-Grouped Audio V3 Split Engineering
1. **Problem Statement:** Forensic inspection revealed two serious data-leakage mechanisms hidden beneath prior accuracy figures: (a) Vision split `705d388743ea` placed `87.1%` (`411/472`) of `test` images from Roboflow offline-augmented `train/` and split `27/29` (`93.1%`) 10-minute timestamp capture sessions across `train`/`val`/`test` (`447/447` timestamped test images shared sessions with `train`); (b) Audio V3 split `32.56%` (`28/86`) of positive train-horn recordings across `5/57` unique YouTube stems spanning `train`/`val`/`test`.
2. **Existing Design / Data:** [`split.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/data/split.py) grouped Vision V1 only by immediate source filename (`split_group_id`), ignoring temporal burst correlation (`Screenshot-YYYY-MM-DD-at-HH-MM-SS`, `IMG_YYYYMMDD_HHMMSS`, 13-digit epoch ms, ISO timestamps) and mixed Roboflow offline-augmented `train` images into `val`/`test`. Audio V3 grouped ESC-50 negatives by fold but split YouTube positive clips individually.
3. **Why Existing Was Insufficient:** Reported `99.46% mAP@50` (`39f402dfe460`) and `0.8956` Audio V3 window accuracy suffered cross-split correlation, failing to generalize on Layer B (`43.48%` front closure trigger, `0.00%` field audio specificity).
4. **Alternatives Evaluated:**
   - *Option A:* Overwrite `705d388743ea` and `data/splits/audio/v3/dataset_split.json`. *(Rejected: destroys provenance of frozen checkpoints).*
   - *Option B:* Create non-destructive session/stem-grouped manifest & audit module + clean candidate splits under `data/splits/vision_v1_session_grouped/` and `data/splits/audio_v3_stem_grouped/`, proving `0%` cross-split burst/session/stem/augmentation overlap via automated invariant tests. *(Selected).*
5. **Selected Choice:** Option B. (Retraining models on the raw `.jpg`/`.wav` assets is explicitly deferred until `AUTH-MEDIA-ACCESS.json` is granted).
6. **Justification:** Preserves frozen checkpoint provenance (`sha256` unchanged), establishes exact quantitative shrinkage (`1,315` unique sources, `29` timestamp sessions -> leakage-free partitions), and supplies turnkey split manifests for valid post-authorization retraining.
7. **Expected Effect:** Zero cross-split session overlap (`gap <= 600 s`), zero Roboflow `train/` augmented images in `val`/`test`, zero cross-split YouTube stems or ESC-50 folds.
8. **Measured Result:** **Verified (`vision_audio_leakage_audit.json`).** Candidate `vision_v1_session_grouped` yields `train=1,776 (738 unique)`, `val=336`, `test=241` with `0/29` crossing sessions up to `gap=600 s`, `0` multi-split groups, and `804` eval augmentation duplicates excluded; candidate `audio_v3_stem_grouped` yields `60/60`, `13/13`, `13/13` with `0/57` cross-split positive stems and `0` cross-split ESC-50 folds. `test_leakage_free_splits.py` passes **`4/4`**.
9. **Limitations:** Original checkpoints cannot be retrained under the current fail-closed raw-media boundary (`AUTH-MEDIA-ACCESS.json` absent). Also, `gap >= 1800 s` merges continuous `2026-07-08` multi-hour screenshots (`2` session crossings at `1800 s`).

---

## Decision D-03: Exploratory Post-Hoc Audio Calibration & Consecutive-Window Hysteresis Study (`Exp O`)
1. **Problem Statement:** Frozen Audio V3 (`T* = 0.37`) yields `92.31%` recall but `0.00%` specificity (`10/10` FP on absent-horn train clips) and `0.800–0.826` max score across `11–16` windows per `no_train` clip.
2. **Existing Design / Data:** Single-window threshold check `score >= 0.37` evaluated per `1.0 s` window (`0.5 s` hop) across `2,600` train windows (`ALL_AUDIO_WINDOW_SCORES.csv`) + `130` `no_train`/`engine` windows (`results/experiments/cache/*_audio_1_audio.jsonl`).
3. **Why Existing Was Insufficient:** No quantitative analysis existed showing whether higher threshold `tau`, consecutive-window persistence (`k-of-k`), or temperature scaling separates real locomotive horns from road horns or transient artifacts.
4. **Alternatives Evaluated:**
   - *Option A:* Retrain Audio V3 with road-horn negative supervision. *(Blocked: requires raw `.wav` decoding under `AUTH-MEDIA-ACCESS`).*
   - *Option B:* Run exact reproducible sensitivity sweep across `(tau, k_consecutive)` and post-hoc temperature/Platt calibration across all `27` events' real cached scores. *(Selected).*
5. **Selected Choice:** Option B (strictly labeled post-hoc exploratory diagnostic).
6. **Justification:** Separates resolvable post-processing false triggers (isolated spikes) from structural acoustic feature overlap (sustained `0.80+` road-vehicle horns), empirically settling threshold hypotheses without touching raw media.
7. **Expected Effect:** Maps exact Recall/Specificity/F1/`no_train` FP Pareto frontier on field data.
8. **Measured Result:** **Verified (`exp_o_audio_calibration_hysteresis.json`).** Proved all `3` `no_train` clips sustain runs of `3, 5, 9` windows `>=0.37` (defeating `k>=2` at `0.37`) yet drop to `longest_run_ge_0_75 = 1`. Raising threshold+hysteresis to **`(tau=0.75, k=2)`** achieves **`0/3` `no_train` FP, `0/1` `engine` FP, `Spec=0.9000` (`9/10`), `Prec=0.8889`, `Acc=0.7391`, `F1=0.7273`** (`Rec=0.6154`); temperature scaling `T=3.0` drops 5-bin ECE `0.2955 -> 0.0709` (`Brier 0.2724 -> 0.2246`).
9. **Limitations:** Event-level reference labels lack sub-event horn timestamps; high specificity gains at high threshold trade away `5/13` genuine horns.

---

## Decision D-04: CPU Stage Profiling, Weight Stripping, TorchScript & Quantization + Duty-Cycle Modeling (`Exp P`)
1. **Problem Statement:** `24.49 MB` unstripped `YOLOv8n` checkpoint (`best.pt`), TorchScript/quantization speedups, per-stage CPU latency, peak RSS, and continuous `24/7` vs event-triggered Raspberry Pi feasibility have never been measured in the repository.
2. **Existing Design / Data:** [`optimization/benchmark_cli.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/optimization/benchmark_cli.py) existed cleanly on disk but had zero recorded execution artifacts for real neural models on CPU.
3. **Why Existing Was Insufficient:** Hardware readiness (`RASPBERRY_PI_READINESS_REPORT.md`) cannot rely on guesswork or unmeasured claims about FPS or memory bounds.
4. **Alternatives Evaluated:**
   - *Option A:* Qualitative estimate only. *(Rejected: violates evidence discipline).*
   - *Option B:* Deterministic CPU profiling script in `scripts/run_optimization_and_robustness_suite.py` using real `YOLOv8n` + `CompactTrainHornCNN` weights on synthetic tensors (`INPUT_CLASSIFICATIONS: SYNTHETIC_ONLY`), comparing stripped weights, FP32 (`640`, `416`, `320`), TorchScript trace, dynamic INT8 Linear quantization on CNN, peak RSS, V3 FSM tick time, and analytical Raspberry Pi 4B / Pi 5 duty-cycle scaling. *(Selected).*
5. **Selected Choice:** Option B, explicitly separating **measured macOS ARM64 host telemetry** from **analytical Pi 4B/Pi 5 projections** and **unmeasured physical SBC hardware**.
6. **Justification:** Delivers reproducible numeric memory/latency gains while maintaining total empirical honesty (`onnx` / `onnxruntime` unavailable in `.venv`).
7. **Expected Effect:** Establishes exact FPS/RSS envelopes and quantifies duty-cycle compute savings from acoustic/vibration event-gating vs continuous dual-camera 5-FPS vision.
8. **Measured Result:** **Verified (`exp_p_cpu_edge_benchmark.json`).** Weight stripping shrinks Vision `best.pt` **`24,493,159 -> 6,145,232 B` FP16 (`-74.91%`)**; peak RSS **`491.52 MB`**; E2E `YOLO.predict` speeds up **`2.32×`** from `54.658 ms` (`640px`, `18.30 FPS`) -> **`23.605 ms` (`416px`, `42.36 FPS`)**; `log_mel + TorchScript CNN` = **`0.881 ms/window`** (`0.0` drift); V3 FSM `121` ticks = **`4.737 ms` (`0.0391 ms/tick`, `25,575 Hz`)**; event-triggered duty cycle cuts daily vision frames `864,000 -> 11,760–29,760` (`-96.56% to -98.64%`), lowering projected RPi 4B load at `416px` (`5.5×`) from `1.308` -> **`0.0274–0.0544` cores**.
9. **Limitations:** Physical Raspberry Pi thermal throttling, power draw (`W`), and NEON throughput remain unmeasured on target hardware (`physical_raspberry_pi_tested = false`).

---

## Decision D-05: Synthetic Adverse-Weather / Visibility & Crossing-Fault Stress Matrix (`Exp Q`)
1. **Problem Statement:** All `23` real train proposals come from one single `day/overcast` morning session at `crossing_A`, leaving rain/fog/night confidence attenuation combined with burst dropouts, stalled crossing obstacles, and multi-train interruption untested quantitatively across parameter sweeps.
2. **Existing Design / Data:** `Exp L` (`18` point scenarios) checked binary pass/fail safety invariants under fixed faults, but did not sweep continuous degradation (`alpha_conf` x `p_drop`) or measure closure failure vs fail-safe rate.
3. **Why Existing Was Insufficient:** Safety vs availability trade-offs under tropical monsoon rain/fog (`Bangladesh` operating target) must be quantified transparently.
4. **Alternatives Evaluated:** Controlled closed-loop synthetic sweep over attenuation factor `alpha` (representing rain/fog/night confidence decay), burst packet drop probability `p_drop`, stalled crossing obstacle dwell, and multi-train reopening interruption through `MultimodalDecisionEngineV3FourLayer` + `PhysicalGateModel`.
5. **Selected Choice:** Implement `Exp Q` inside `optimization_and_stress.py` (`INPUT_CLASSIFICATIONS: SYNTHETIC_ONLY`).
6. **Justification:** Strictly obeys `media_guard.py`, complements fixed-fault `Exp L`, and explicitly distinguishes synthetic stress curves from unseen field weather data.
7. **Expected Effect:** Characterizes exact transition point where attenuated confidence shifts V3 from clean nominal actuation -> failsafe lock -> zero unsafe openings (`0` insecure opens across all grids).
8. **Measured Result:** **Verified (`exp_q_weather_and_interlocking_stress.json`).** Across all **`100`** grid runs: **`0` unsafe openings, `100%` legal FSM transitions**; `100%` closure for `alpha >= 0.45` (`eff_conf >= 0.396`) and sharp cliff to `0%` closure / `0%` failsafe at `alpha = 0.35` (`eff_conf = 0.308 < 0.35`, because healthy empty frames do not trigger heartbeat staleness). Stalled obstacle safely holds closed until `22.6 s`; multi-train interrupt safely reverses `GATE_OPENING -> GATE_CLOSING` at `14.8 s`. (`test_optimization_and_stress_suite.py` passes **`3/3`**.)
9. **Limitations:** Parametric attenuation is an analytical proxy for image rain/fog blur, not field optical measurement.
