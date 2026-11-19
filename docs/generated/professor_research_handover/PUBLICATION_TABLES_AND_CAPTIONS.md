# Publication-Ready Tables & Figure Captions

**Parent Document:** [`FINAL_PROFESSOR_RESEARCH_HANDOVER.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/FINAL_PROFESSOR_RESEARCH_HANDOVER.md)  
**Verified Cross-Check Status:** `12/12` consistency checks passed (`layer_b_split_audit_and_collection_plan.json` v1.3).

---

## Table I — Perception & Layer-B Dataset Audit Summary
*(Evidence: [`vision_audio_leakage_audit.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_audit/vision_audio_leakage_audit.json), [`ACTUAL_FULL_COHORT_RESULTS.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/professor_evidence/mission43/ACTUAL_FULL_COHORT_RESULTS.json), [`layer_b_split_audit_and_collection_plan.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_audit/layer_b_split_audit_and_collection_plan.json))*

| Dataset / Cohort | Scope / Split | Sample Counts | Verified Leakage / Confounding Finding | Remediated Status |
|---|---|---|---|---|
| **Vision V1 (`705d388743ea`)** | Train / Val / Test | `2,218 / 467 / 472` (`3,157` total; `3,267` boxes) | `27/29` (`93.1%`) `<=600 s` sessions cross splits; `447/447` test imgs share train sessions; `411/472` (`87.1%`) from RF `train/` aug exports | [`vision_v1_session_grouped`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/vision_v1_session_grouped/split_summary.json): `1,776 / 336 / 241`, **`0/29` cross-split sessions (`<=600 s`)** |
| **Audio V3 (`audio/v3`)** | Train / Val / Test | `120 / 26 / 26` (`172` clips; `50%` pos/neg) | `0` ESC-50 fold overlap, **`5/57` YouTube horn stems (`28/86 = 32.56%`)** cross splits | [`audio_v3_stem_grouped`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/audio_v3_stem_grouped/split_summary.json): `120 / 26 / 26`, **`0/57` cross-split stems** |
| **Layer B Field Corpus** | `train` / `no_train` / `engine` | `23 / 3 / 1` (`27` events, `54` streams, `2,600` audio wins) | Single site (`crossing_A`), `2` sessions (Session 1 day `20` trains; Session 2 night `3` trains + `3` nt + `1` eng), `0/27` occ sensors | `leakage_safe = false` for any 3-way split -> **Option A** descriptive (`27` events) or **Option C** (`235`/`271` multi-site) |

---

## Table II — Exploratory Approach Closure & Policy Comparison (`B4` All `27` & `sync11`)
*(Evidence: [`exp_a_front_detection.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_a_front_detection.json), [`exp_j_temporal_vs_stateless.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_j_temporal_vs_stateless.json), [`exp_d_back_departure.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_d_back_departure.json), [`statistical_comparisons.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/analysis/statistical_comparisons.json); basis: `pre-db40305` caches + adopted references)*

| Policy / Variant | `train23` Closures (`[Wilson 95% CI]`) | `no_train` FP (`0/3`) | `engine` FP (`0/1`) | Illegal B4 Events | `sync11` Premature Openings (`[95% CP UB]`) | `sync11` Completed Reopenings |
|---|---|---|---|---|---|---|
| `stateless_union` | `23/23` (`100%`) | **`3/3`** | `0/1` | `26/27` | `0/11` (never sustained closed) | `N/A` |
| `stateless_vision_rule2` | `16/23` (`69.57%`) | `2/3` | `0/1` | `18/27` | `0/11` | `N/A` |
| `V1` (`RULE_3` disappearance) | `9/23` (`39.13%`) | `0/3` | `0/1` | `0/27` | `2/11` | Disappearance-based |
| `V2` (`RULE_3B_3C` candidate) | `10/23` (`43.48%`) | `0/3` | `0/1` | `0/27` | `4/11` (`001,002,006,013`) | Disappearance-based |
| `V3_GUARDED_DISAPPEARANCE` | `10/23` (`43.48%`) | `0/3` | `0/1` | `0/27` | `3/11` | Disappearance-based |
| **`V3_CONSERVATIVE_POSITIVE`** | **`10/23` (`43.48%`, `[0.2563, 0.6319]`)** | **`0/3`** *(McNemar p=`0.25` vs union)* | **`0/1`** | **`0/27`** | **`0/11` (`<= 23.84%`)** *(McNemar p=`0.125` vs V2)* | **`0/11` (all held fail-closed EOF)** |

---

## Table III — Session Stratification & Autonomous Reopening Method Ablation (`Exp S`, `M1`–`M5`)
*(Evidence: [`layer_b_split_audit_and_collection_plan.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_audit/layer_b_split_audit_and_collection_plan.json) v1.3, [`exp_n_event_matrix.csv`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_n_event_matrix.csv))*

| Finding Dimension / Method | Subgroup or Mechanism | Measured Outcome | Interpretation / Engineering Implication |
|---|---|---|---|
| **Approach by Session (`Exp S`)** | Session 1 (`2026-09-14` day, `n=20`) vs Session 2 (`2026-10-04` night, `n=3`) | **`7/20` (`35.0%`, `[0.1812, 0.5671]`)** vs **`3/3` (`100%`, `[0.4385, 1.0000]`)** | `-90°` `.mov` rotation losses suppressed daytime Session 1; Session 2 held `824/967` (`85.21%`) side-proxy & `23/30` rear boxes |
| **`sync11` Terminal FSM State** | `11` calibrated clips (`Session 1` only) | `4` L1 closures, `5` EOF `RULE_4_FAIL_SAFE_CLAMP`, `2` `IDLE` | **`0/11` completed autonomous reopenings** (`43.203 s` max gap on `017`, `0/11` rear boxes, `0/27` occ sensors) |
| **`M1` Disappearance Timer** | `V2` / `V3_GUARDED_DISAPPEARANCE` | `V2=4/11` (`sync11`), `4` on `T4` corpus | Unsafe (`UNSAFE_REJECTED`) under optical dropouts |
| **`M2` Naive `>= 2` Rear Pair Only** | Unfiltered YOLO `rear` frames on `camera_2` | **`4/22` premature** (`008` `-39.0 s` before `T4`, `021`–`023` pre-`T4`) | Unsafe alone (`UNSAFE_ALONE_REJECTED`); mid-train false rear boxes fire early |
| **`M3` Monotonic Transit + Silence** | `>= 20` dets, gap `<= 3.5 s`, cessation + `1.5 s` silence | **`0/22` premature** (`021, 022, 023` clean exit) | Strongest vision layer (`STRONGEST_VISION_PREREQUISITE_LAYER`), still misses unlit stalls |
| **`M5` `V3 + M3 + Occ.CLEAR + >=15s`** | Real (`0/27` occ, `1.402 s` median tail) vs `SYNTHETIC_ONLY` | Real: `0/11` premature (closed); Synth CLEAR+8s: `OPEN`; no-occ or `1.4 s` tail: `CLOSED` | Required target architecture; demands physical occupancy + `>= 15 s` post-`T4` capture |

---

## Table IV — Acoustic Horn Classification, Hysteresis (`Exp O`) & Nested LOEO CV (`Exp R`)
*(Evidence: [`exp_c_audio_horn.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_c_audio_horn.json), [`exp_o_audio_calibration_hysteresis.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/exp_o_audio_calibration_hysteresis.json), [`exp_r_independent_validation.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/exp_r_independent_validation.json))*

| Evaluation Mode (`audio23` + `no_train3` + `engine1`) | Recall (`n=13`) | Specificity (`n=10`) | Precision | F1 | `5-bin ECE` | Brier Score (`Δ 95% CI`) | `no_train` FP (`n=3`) |
|---|---|---|---|---|---|---|---|
| **Baseline Frozen `(tau=0.37, k=1)`** | `0.9231` (`12/13`) | `0.0000` (`0/10`) | `0.5455` | `0.6857` | `0.2955` | `0.2724` | `3/3` (`3–9` wins `0.800–0.826`) |
| **`Exp O` In-Sample Grid Best `(0.75, k=2, T=3.0)`** | `0.6154` (`8/13`) | `0.9000` (`9/10`) | `0.8889` | `0.7273` | `0.0709` | `0.2246` | `0/3` (`0/1` engine FP) |
| **`Exp R` 23-Fold Nested LOEO OOF (`2,000` boot)** | **`0.6154`** (`[0.3552, 0.8229]`) | **`0.6000`** (`6/10`, `[0.3000, 0.9000]`) | `0.6667` | `0.6400` (`[0.4167, 0.8148]`) | **`0.0999`** | `0.2366` (**Δ CI `[-0.0839, +0.0104]`**) | Non-gating in V3 |

---

## Table V — Synthetic Weather-Dropout Stress (`Exp Q`), Faults (`Exp L`) & Optical Wakeup (`Exp R`)
*(Classification: strictly `SYNTHETIC_ONLY` — [`exp_l_fault_injection.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/failure_injection/exp_l_fault_injection.json), [`exp_q_weather_and_interlocking_stress.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/exp_q_weather_and_interlocking_stress.json), [`exp_r_crossval_and_failsafe.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/exp_r_crossval_and_failsafe.json))*

| Synthetic Suite | Design / Conditions | Unsafe Openings | Legal Transitions | Key Safety Outcome |
|---|---|---|---|---|
| **Exp L (18 Fault Scenarios)** | Nominal 4-layer cycle + single/multi-sensor faults + sparse dropouts | **`0/18`** | `100%` | `00_nominal` reopens at `14.6 s`; all fault runs latch `CLOSED`; `V2_RULE_3C` failed on sparse dropout |
| **Exp Q (100 Weather × Dropout Runs)** | `alpha in [1.0, 0.8, 0.6, 0.45, 0.35]` × `p_drop in [0.0..0.5]` × `5` seeds + interlocking cases | **`0/100`** | `100%` | `100%` closures (`80/80`) for `alpha >= 0.45`; **cliff to `0%` (`alpha=0.35`, `conf=0.308 < 0.35`)** while `SourceTracker` remains `HEALTHY`; stalled obstacle holds past `20.8 s` -> opens `22.6 s` |
| **`Exp R` Opt-In Wakeup (`RULE_L3`, default `False`)** | `optical_degraded` + sustained `audio >= 0.75` (`k >= 3`) | **`0`** | `100%` | Recovers synthetic `alpha=0.35` closure **`0% -> 100%`** (`trigger @ 4.0 s`) with **`0/2`** synthetic ambient/impulse FPs |

---

## Table VI — Apple M1 Edge CPU Profiling & Analytical SBC Projections (`Exp P`)
*(Hardware: Apple M1 macOS `arm64`, **`physical_raspberry_pi_tested = false`** — [`exp_p_cpu_edge_benchmark.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/exp_p_cpu_edge_benchmark.json), [`host_edge_scaling_benchmark.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/host_edge_scaling_benchmark.json))*

| Component / Mode | Host Measurement (`Apple M1`) | Unmeasured Analytical SBC Projection (`RPi 5` `2.4×` / `RPi 4B` `5.5×`) |
|---|---|---|
| **YOLOv8n Checkpoint Stripping** | `24.49 MB -> 6.15 MB` FP16 (`-74.91%`), `12.19 MB` FP32 | Storage/RAM load reduction only (host verified) |
| **YOLOv8n E2E `YOLO.predict` (`640 -> 416px`)** | `44.557 ms (22.44 FPS) -> 21.597 ms (46.30 FPS)` (**`2.06×`** speedup) | `51.83 ms` (`RPi 5`) / `118.78 ms` (`RPi 4B`) at `416px` *(unmeasured)* |
| **TorchScript FP32 + OpenCV Preprocess (`416px`)** | `16.839 ms` (`4T` TS, `59.39 FPS`, `0.0` drift) + `16.980 ms` (`1080p->rot90->416`) | Host RSS `452.45–504.3 MB` |
| **Audio Natural Log-Mel + CNN TorchScript + V3 FSM** | `0.410 + 0.468 = 0.878 ms/window`; FSM `4.613 ms / 121 ticks` (`0.0381 ms/tick`) | Real-time audio + interlocking control overhead `< 1 ms` on host |
| **Event-Triggered Duty Cycle (`10–40` trains/day)** | `864,000 -> 11,760–29,760` vision frames/day (**`-98.64%` to `-96.56%`**) | `416px` gated cores: `0.0258–0.0506` (`RPi 4B`), `0.0113–0.0221` (`RPi 5`) *(vs `2.4603` cont. @ 640px)* |

---

## Table VII — Reconciled Multi-Crossing `Option C` Collection & Power Design (`ICC` Sensitivity)
*(Evidence: [`layer_b_split_audit_and_collection_plan.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_audit/layer_b_split_audit_and_collection_plan.json) v1.3)*

| Tier / Scenario (`5` crossings, `>=10 s` pre-`T0`, `>=15 s` post-`T4`, occ sensor) | Train (`2` sites) | Val (`1` site) | Test (`2` unseen sites) | Total Events | Test Power & 95% Risk Bound (`p_01=0.005`) |
|---|---|---|---|---|---|
| **`3`-Crossing Structural Floor (Rejected)** | `~20` | `~10` | `12` train, `6` nt | `~36` (`6` sess) | `22.09%` (`0/12`) / `39.30%` (`0/6`) 95% UB; `1.87%` McNemar (`p_10=0.20`) |
| **`C1` Unclustered (`rho = 0.00`)** | `98` (`5` sess) | `43` (`3` sess) | `29+29+8 = 66` (`5` sess) | **`207`** (`13` sess) | `N_eff = 29.0`, `9.81%` CP UB, `49.23%` McNemar (`p_10=0.20`) |
| **`C2` Primary Cluster-Adjusted (`rho = 0.05`)** | **`98`** (`5` sess) | **`43`** (`3` sess) | **`43+43+8 = 94`** (`5` sess) | **`235`** (`13` sess) | `DEFF_actual=1.38`, `N_eff=31.16`, **`9.17% <= 10%` UB**, `98.79%` at `4/11` |
| **`C3` High Power McNemar (`rho = 0.05`)** | `98` (`5` sess) | `43` (`3` sess) | `62+60+8 = 130` (`6` sess) | **`271`** (`14` sess) | `DEFF_actual=1.4667`, `N_eff=42.27`, `6.84%` UB, **`81.59%` McNemar (`p_10=0.20`)** |

*ICC Sensitivity (`m = 10` per session, `(<=10% CP / >=80% McNemar p_10=0.20 / <=5% CP)`):* `rho=0.0` -> `29 / 42 / 59`; `rho=0.02` -> `35 / 50 / 70`; `rho=0.05` -> `43 / 61 / 86`; `rho=0.10` -> `56 / 80 / 113`; `rho=0.15` -> `69 / 99 / 139`.

---

## Table VIII — Complete 27-Event Modality & Vision+Audio Fusion Comparison
*(Evidence: [`COMPLETE_27_EVENT_MULTIMODAL_EXPERIMENT_REPORT.md`](file:///Users/sayemuddin/Desktop/Train_automation/results/multimodal_27_event_evaluation/COMPLETE_27_EVENT_MULTIMODAL_EXPERIMENT_REPORT.md), [`event_by_event_27_multimodal_evaluation.csv`](file:///Users/sayemuddin/Desktop/Train_automation/results/multimodal_27_event_evaluation/event_by_event_27_multimodal_evaluation.csv), [`modality_and_fusion_ablation_metrics.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/multimodal_27_event_evaluation/modality_and_fusion_ablation_metrics.json); View 1 = `23` trains vs `3` `no_train` with `engine_events/001` separate; View 3 = `24` rail vehicles vs `3` `no_train`)*

| Architecture / Modality | Train `TP/23` | `FN/23` | `no_train` `FP/3` | `engine_001` Det | Prec (`V1`) | Recall (`V1`) | Spec (`V1`) | F1 (`V1`) | Rail24 `Rec/F1` (`V3`) | McNemar `p` vs `V2` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Front-Only Stateless (`k>=1`)** (`V1`) | `16` | `7` | `2` | `no` | `88.9%` | `69.6%` | `33.3%` | `78.0%` | `16/24 (76.2%)` | `0.2891` |
| **Front-Only L1 Causal (`confirm>=2`)** (`V2`/`B0`) | `10` | `13` | `0` | `no` | `100.0%` | `43.5%` | `100.0%` | `60.6%` | `10/24 (58.8%)` | `1.0000` |
| **Back-Only `confirm>=2` (All Classes)** (`V4`) | `9` | `14` | `2` | `YES` | `81.8%` | `39.1%` | `33.3%` | `52.9%` | `10/24 (55.6%)` | `0.4531` |
| **Back-Only `confirm>=2` (Side/Rear Filtered)** (`V5`) | `9` | `14` | `0` | `no` | `100.0%` | `39.1%` | `100.0%` | `56.2%` | `9/24 (54.5%)` | `1.0000` |
| **Side-Class Proxy (`Front+Back side>=1`)** (`V6`) | `14` | `9` | `0` | `no` | `100.0%` | `60.9%` | `100.0%` | `75.7%` | `14/24 (73.7%)` | `0.1250` |
| **Dual-Vision (`Front L1 OR Back Side/Rear L1`)** (`V8`) | `12` | `11` | `0` | `no` | `100.0%` | `52.2%` | `100.0%` | `68.6%` | `12/24 (66.7%)` | `0.5000` |
| **Audio-Only (`tau=0.37, k=1`)** (`A1`/`B1`) | `22` | `1` | `3` | `no` | `88.0%` | `95.7%` | `0.0%` | `91.7%` | `22/24 (89.8%)` | `0.0490` |
| **Audio-Only Hysteresis (`tau=0.75, k=2`)** (`A3`) | `9` | `14` | `0` | `no` | `100.0%` | `39.1%` | `100.0%` | `56.2%` | `9/24 (54.5%)` | `1.0000` |
| **Fusion `F1`: Stateless Union (`V1 OR A1`)** | `23` | `0` | `3` | `no` | `88.5%` | `100.0%` | `0.0%` | `93.9%` | `23/24 (92.0%)` | `0.0213` |
| **Fusion `F2`: V3 Default (`B2/B4`, Adv. Audio)** | `10` | `13` | `0` | `no` | `100.0%` | `43.5%` | `100.0%` | `60.6%` | `10/24 (58.8%)` | `1.0000` |
| **Fusion `F3`: Front L1 OR (`V1 AND A3`)** | `11` | `12` | `0` | `no` | `100.0%` | `47.8%` | `100.0%` | `64.7%` | `11/24 (62.9%)` | `1.0000` |
| **Fusion `F4`: Front L1 OR Audio `(0.75, k=2)`** | `14` | `9` | `0` | `no` | `100.0%` | `60.9%` | `100.0%` | `75.7%` | `14/24 (73.7%)` | `0.1250` |
| **Fusion `F5`: Dual-Vision Side/Rear + Adv. Audio (`B7`)** | `12` | `11` | `0` | `no` | `100.0%` | `52.2%` | `100.0%` | `68.6%` | `12/24 (66.7%)` | `0.5000` |
| **Fusion `F6`: Full Multimodal (`V2 OR V5 OR A3`)** | **`15`** | **`8`** | **`0`** | `no` | **`100.0%`** | **`65.2%`** | **`100.0%`** | **`79.0%`** | `15/24 (76.9%)` | `0.0625` |
| **Fusion `F7`: Exploratory `2-of-3` (`Gap <= 0.45s`)** | **`17`** | **`6`** | **`0`** | `no` | **`100.0%`** | **`73.9%`** | **`100.0%`** | **`85.0%`** | `17/24 (82.9%)` | `0.0156` |

---

## Table IX — End-to-End Causal Gate-Control State Machine Integration (`V3 FSM + PhysicalGateModel`)
*(Evidence: [`causal_fsm_gate_timing_summary.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/multimodal_27_event_evaluation/causal_fsm_gate_timing_summary.json), [`failed_events_forensic_diagnosis.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/multimodal_27_event_evaluation/failed_events_forensic_diagnosis.json); `dt = 0.20 s`; requires `>=5.2 s` from first detection to `0 deg` closure while `21/22` `T2`-annotated clips begin `2.8-5.0 s` before `T2`)*

| Causal FSM Configuration | Train Triggered | Full Closure (`0°`) | Warn@EOF Only | `NT FP/3` | `Eng001` | `Warn <= T2` | `Cmd <= T2` | `Half <= T2` | `Full <= T2` | Reopen Cycles |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **FSM `V2`/`F2`: Front L1 / Default B4** (`FROZEN`, Front Clock) | `10/23` | `9/23` | `1` (`001`) | `0/3` | `no` | `4` | `3` | `1` | `0` | `0` |
| **FSM `F3`: Weak-Front & Audio `0.75 k=2`** (`EXPL.`, Front Clock) | `11/23` | `10/23` | `1` (`001`) | `0/3` | `no` | `5` | `3` | `1` | `0` | `0` |
| **FSM `F4`: Front L1 OR Audio `0.75 k=2`** (`EXPL.`, Front Clock) | `14/23` | `13/23` | `1` (`001`) | `0/3` | `no` | `6` | `3` | `1` | `0` | `0` |
| **FSM `F5`: Dual-Vision Side/Rear (`sync11` n=11 Calibrated)** | `5/11` | `5/11` | `0` | `N/A` | `N/A` | `1` | `1` | `1` | `0` | `0` |
| **FSM `F6`: Full Multimodal (`sync11` n=11 Calibrated)** | `8/11` | `8/11` | `0` | `N/A` | `N/A` | `2` | `1` | `1` | `0` | `0` |
| **FSM `F6`: Full Multimodal (`27` Bounded: `sync11` + Local `16`)** | `15/23` | `15/23` | `0` | `0/3` | `no` | `6` | `3` | `1` | `0` | `0` |
| **FSM `F7`: Exploratory `2-of-3` (`27` Bounded)** | `17/23` | `17/23` | `0` | `0/3` | `no` | `8` | `4` | `1` | `0` | `0` |

---

## Reproducible Figure Captions (`fig01`–`fig15`)

1. **Fig. 1 (`fig01`):** End-to-end Four-Layer + `OccupancyVerifier` V3 multimodal crossing protection architecture across trackside sensing, causal snapshot alignment, asymmetric decision engine, and fail-closed physical gate boom simulation. ([`fig01_system_architecture.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig01_system_architecture.png))
2. **Fig. 2 (`fig02`):** Layer-by-layer sensor ingestion and transition workflow showing non-gating Layer 3 audio reinforcement vs gated Layer 1/Layer 4 transitions. ([`fig02_four_layer_workflow.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig02_four_layer_workflow.png))
3. **Fig. 3 (`fig03`):** Nominal gate closure sequence timeline illustrating `confirm_frames = 2`, `2.0 s` warning, and `3.0 s` boom closure stroke (`90° -> 0°`, protected <= `45°`). ([`fig03_gate_closure_timeline.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig03_gate_closure_timeline.png))
4. **Fig. 4 (`fig04`):** Departure and clearance state flow comparing legacy disappearance timers (`M1`) against positive tail + `OccupancyState.CLEAR` AND-gating. ([`fig04_departure_and_clearance_workflow.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig04_departure_and_clearance_workflow.png))
5. **Fig. 5 (`fig05`):** Modality ablation (`Exp K`) on `sync11` real caches and closed-loop 4-layer synthetic nominal vs degraded runs. ([`fig05_modality_ablation.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig05_modality_ablation.png))
6. **Fig. 6 (`fig06`):** Approach closure and false-positive comparison (`Exp A, I, J`) contrasting stateless union, legacy backfill, and causal V3 across `train23`, `no_train3`, and `engine1`. ([`fig06_closure_performance.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig06_closure_performance.png))
7. **Fig. 7 (`fig07`):** Premature barrier reopening counts on `sync11` (`Exp D`: `V1=2/11`, `V2=4/11`, `V3_GUARDED=3/11`, `V3_CONSERVATIVE=0/11` via EOF fail-closed hold). ([`fig07_premature_opening_analysis.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig07_premature_opening_analysis.png))
8. **Fig. 8 (`fig08`):** Closed-loop state legality and unsafe-opening counts across `18` synthetic fault-injection scenarios (`Exp L`, `0` unsafe openings). ([`fig08_fault_injection_outcomes.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig08_fault_injection_outcomes.png))
9. **Fig. 9 (`fig09`):** Detection lead time vs `T2` arrival margins on close-range prototype videos highlighting `-90°` orientation misses and upstream distance shortfalls. ([`fig09_detection_and_actuation_timing.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig09_detection_and_actuation_timing.png))
10. **Fig. 10 (`fig10`):** Unvalidated upstream sensor geometry concept illustrating `84–211 m` baseline sighting distance scenarios for `40–100 km/h` (`7.6 s` closure budget). ([`fig10_real_world_installation_concept.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig10_real_world_installation_concept.png))
11. **Fig. 11 (`fig11`):** Forensic dataset leakage comparison across Vision V1 (`705d388743ea` vs `vision_v1_session_grouped`) and Audio V3 (`audio/v3` vs `audio_v3_stem_grouped`). ([`fig11_dataset_leakage_comparison.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/figures/fig11_dataset_leakage_comparison.png))
12. **Fig. 12 (`fig12`):** Trackside audio run-length distributions (`3–9` window `no_train` bursts >= `0.37` vs `1` window >= `0.75`), `(tau, k)` Pareto frontier, and temperature calibration (`Exp O`). ([`fig12_audio_hysteresis_and_calibration.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/figures/fig12_audio_hysteresis_and_calibration.png))
13. **Fig. 13 (`fig13`):** Apple M1 CPU stage latencies, TorchScript scaling, checkpoint stripping (`-74.91%`), and analytical daily duty-cycle frame reductions (`96.56%–98.64%`, `Exp P`). ([`fig13_cpu_edge_benchmark_and_duty_cycle.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/figures/fig13_cpu_edge_benchmark_and_duty_cycle.png))
14. **Fig. 14 (`fig14`):** Synthetic weather optical confidence attenuation × frame burst-dropout closure heatmap (`Exp Q`: `0/100` unsafe openings, `alpha = 0.35` healthy-empty-frame cliff). ([`fig14_weather_attenuation_stress_heatmap.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/figures/fig14_weather_attenuation_stress_heatmap.png))
15. **Fig. 15 (`fig15`):** `23`-fold nested LOEO acoustic CV trade-off (`Spec 0.00 -> 0.60`, `Recall 0.92 -> 0.62`, non-significant Brier Δ) and synthetic `RULE_L3` optical-degraded wakeup (`Exp R`). ([`fig15_exp_r_loeo_and_optical_wakeup.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/figures/fig15_exp_r_loeo_and_optical_wakeup.png))

<!-- MISSION11_UPRIGHT_TABLES_START -->
## Table X — Upright (`db40305`) Original-Media 27-Event Modality & Fusion vs `pre-db40305` Baseline
*(Evidence: [`UPRIGHT_INFERENCE_MANIFEST.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_inference_v2/UPRIGHT_INFERENCE_MANIFEST.json), [`baseline_vs_upright_comparison.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_27_event_evaluation/baseline_vs_upright_comparison.json), [`authoritative_27_event_results_table.csv`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_27_event_evaluation/authoritative_27_event_results_table.csv); `54/54` streams orientation-verified, audio max score delta vs cache = `0.0`)*

| Configuration | Base TP/23 | Upright TP/23 | ΔTP | NT FP/3 | Eng001 (B->U) | Upright Prec | Upright Recall [95% CI] | Upright Spec | Upright F1 | Rail24 F1 (V3) | McNemar p (Base vs Up) |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| `A1_Audio_Frozen_037_k1` | 22 | **22** | +0 | 3 | N->N | 88.0% | 95.7% [79.0-99.2%] | 0.0% | 91.7% | 22/24 (89.8%) | 1.0000 |
| `A2_Audio_037_k2` | 17 | **17** | +0 | 3 | N->N | 85.0% | 73.9% [53.5-87.5%] | 0.0% | 79.1% | 17/24 (77.3%) | 1.0000 |
| `A3_Audio_Hysteresis_075_k2` | 9 | **9** | +0 | 0 | N->N | 100.0% | 39.1% [22.2-59.2%] | 100.0% | 56.2% | 9/24 (54.5%) | 1.0000 |
| `F1_Stateless_Union_FrontAny_Or_Audio037` | 23 | **23** | +0 | 3 | N->Y | 88.5% | 100.0% [85.7-100.0%] | 0.0% | 93.9% | 24/24 (94.1%) | 1.0000 |
| `F2_V3_Default_Front_L1_Advisory_Audio` | 10 | **23** | +13 | 1 | N->Y | 95.8% | 100.0% [85.7-100.0%] | 66.7% | 97.9% | 24/24 (98.0%) | 0.0018 |
| `F3_Front_L1_Or_Corroborated_WeakFront_Audio075k2` | 11 | **23** | +12 | 1 | N->Y | 95.8% | 100.0% [85.7-100.0%] | 66.7% | 97.9% | 24/24 (98.0%) | 0.0034 |
| `F4_Front_L1_Or_Audio075k2` | 14 | **23** | +9 | 1 | N->Y | 95.8% | 100.0% [85.7-100.0%] | 66.7% | 97.9% | 24/24 (98.0%) | 0.0215 |
| `F5_Dual_Vision_SideRear_Advisory_Audio` | 12 | **23** | +11 | 1 | N->Y | 95.8% | 100.0% [85.7-100.0%] | 66.7% | 97.9% | 24/24 (98.0%) | 0.0063 |
| `F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2` | 15 | **23** | +8 | 1 | N->Y | 95.8% | 100.0% [85.7-100.0%] | 66.7% | 97.9% | 24/24 (98.0%) | 0.0391 |
| `F7_Exploratory_2of3_Multimodal` | 17 | **23** | +6 | 1 | N->Y | 95.8% | 100.0% [85.7-100.0%] | 66.7% | 97.9% | 24/24 (98.0%) | 0.1250 |
| `V1_Front_Any_Stateless` | 16 | **23** | +7 | 3 | N->Y | 88.5% | 100.0% [85.7-100.0%] | 0.0% | 93.9% | 24/24 (94.1%) | 0.0703 |
| `V2_Front_L1_Confirm2` | 10 | **23** | +13 | 1 | N->Y | 95.8% | 100.0% [85.7-100.0%] | 66.7% | 97.9% | 24/24 (98.0%) | 0.0018 |
| `V3_Back_Any_Stateless` | 17 | **23** | +6 | 2 | Y->Y | 92.0% | 100.0% [85.7-100.0%] | 33.3% | 95.8% | 24/24 (96.0%) | 0.0312 |
| `V4_Back_Confirm2_AllClasses` | 9 | **23** | +14 | 2 | Y->Y | 92.0% | 100.0% [85.7-100.0%] | 33.3% | 95.8% | 24/24 (96.0%) | 0.0001 |
| `V5_Back_Confirm2_SideRear` | 9 | **23** | +14 | 0 | N->N | 100.0% | 100.0% [85.7-100.0%] | 100.0% | 100.0% | 23/24 (97.9%) | 0.0001 |
| `V6_Side_Proxy_Any` | 14 | **23** | +9 | 1 | N->Y | 95.8% | 100.0% [85.7-100.0%] | 66.7% | 97.9% | 24/24 (98.0%) | 0.0215 |
| `V7_Dual_Vision_Confirm2_AllClasses` | 12 | **23** | +11 | 3 | Y->Y | 88.5% | 100.0% [85.7-100.0%] | 0.0% | 93.9% | 24/24 (94.1%) | 0.0063 |
| `V8_Dual_Vision_Confirm2_SideRear` | 12 | **23** | +11 | 1 | N->Y | 95.8% | 100.0% [85.7-100.0%] | 66.7% | 97.9% | 24/24 (98.0%) | 0.0063 |
| `F8_Exploratory_Strong_2of3_Quorum` (>=2 of V2,V5,A3) | 10 | **23** | +13 | 0 | N->N | 100.0% | 100.0% | 100.0% | 100.0% | 23/24 (97.9%) | 0.0002 |

## Table XI — Upright (`db40305`) Causal V3 FSM Gate-Control Replay & Previously Missed Event Recovery
*(Evidence: [`causal_fsm_gate_timing_summary.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_27_event_evaluation/causal_fsm_gate_timing_summary.json), [`COMPLETE_27_EVENT_UPRIGHT_MULTIMODAL_REPORT.md`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_27_event_evaluation/COMPLETE_27_EVENT_UPRIGHT_MULTIMODAL_REPORT.md))*

| Causal FSM Architecture | Train Trig/23 | Full Boom Closed/23 | Warn<=T2 | Cmd<=T2 | Half<=T2 | Full<=T2 | NT FP/3 | Eng001 | Reopen Cycles |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `FSM_V2_Front_L1` | 23/23 | 23/23 | 22 | 22 | 8 | 1 | 1/3 | YES | 0 |
| `FSM_F2_V3_Default_B4` | 23/23 | 23/23 | 22 | 22 | 8 | 1 | 1/3 | YES | 0 |
| `FSM_F3_WeakFront_Plus_Audio` | 23/23 | 23/23 | 22 | 22 | 8 | 1 | 1/3 | YES | 0 |
| `FSM_F4_Front_Or_Audio075k2` | 23/23 | 23/23 | 22 | 22 | 8 | 1 | 1/3 | YES | 0 |
| `FSM_F5_Dual_Vision_Sync11` | 11/11 | 11/11 | 10 | 10 | 4 | 1 | N/A | N/A | 0 |
| `FSM_F6_Full_MM_Sync11` | 11/11 | 11/11 | 10 | 10 | 4 | 1 | N/A | N/A | 0 |
| `FSM_F6_Full_MM_Bounded27` | 23/23 | 23/23 | 22 | 22 | 8 | 1 | 1/3 | YES | 0 |
| `FSM_F7_Exploratory_2of3_Bounded27` | 23/23 | 23/23 | 22 | 22 | 8 | 1 | 1/3 | YES | 0 |

## Table XII — Mission 12 Exploratory Overhead-Bridge ROI Filter, Locomotive Preservation, Passage Coverage & Dropout Stress
*(Evidence: [`mission12_scientific_analysis.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_27_event_evaluation/mission12_scientific_analysis.json), [`spatial_filters.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/spatial_filters.py); post-hoc `crossing_A` exploratory mitigations & labeled synthetic stress scenarios preserve frozen Mission 11 baselines unchanged.)*

| Rule / Exploratory Variant (Provenance) | Train TP/23 | NT FP/3 | Eng001 | View 1 F1 (23+3) | View 3 Rail24 TP | View 3 Rail24 F1 | Pre-T2 Confirm (/22) |
|---|---:|---:|---|---:|---:|---:|---:|
| `V2_Raw (Upright Baseline)` | 23/23 | 1/3 | YES | 97.9% | 24/24 | 98.0% | - |
| `V2_TrackROI (Exploratory Overhead Filter)` | 23/23 | 0/3 | YES | 100.0% | 24/24 | 100.0% | 22 |
| `V5_SideRear (Upright Back S/R)` | 23/23 | 0/3 | no | 100.0% | 23/24 | 97.9% | - |
| `V5_RailVehicle (Exploratory +Large Front)` | 23/23 | 0/3 | YES | 100.0% | 24/24 | 100.0% | - |
| `F6_Raw_Or (Upright Fusion Baseline)` | 23/23 | 1/3 | YES | 97.9% | 24/24 | 98.0% | - |
| `F8_Quorum_SideRear (Mission 11 2-of-3)` | 23/23 | 0/3 | no | 100.0% | 23/24 | 97.9% | 11 |
| `F10_TrackROI_Or_RailBack_Or_Audio (Exploratory Union)` | 23/23 | 0/3 | YES | 100.0% | 24/24 | 100.0% | 22 |
| `F11_RailVehicle_2of3_RawFront (Exploratory Quorum, No ROI)` | 23/23 | 0/3 | YES | 100.0% | 24/24 | 100.0% | 11 |

- **Recorded `[T0..T4]` Continuous Passage Coverage (`n=23`):** Front = `75.19%`, Back = `80.27%`, Dual (`Front|Back`) = **`95.67%`**, Multimodal (`F|B|Audio`) = `95.88%`; trains with `>=5.0 s` blind gap dropped **`8/23 -> 1/23`**. Low-Front subgroup (`<70%`, `n=8`): Front `48.35%` -> Dual **`90.64%`**, `A3` positive in `4/8`. Night Session 2 (`n=3`): Front `65.73%` -> Dual `94.67%` (all `3/3` night trains lost Front before `T4`: `-14.3s` to `-2.4s`).
- **`SYNTHETIC_PERTURBATION_STRESS_TEST` (Applied to Upright Streams):** Front blackout -> `V2_TrackROI=0/23`, **`F10=23/23`** (`11/22` pre-`T2`, `0/3` FP, `Eng001=True`); early `4 s` front glare -> `V2_TrackROI` pre-`T2` drops `3/22` vs **`F10=14/22`**; back blackout -> `V5_RailVehicle=0/23` vs **`F10=23/23` (`22/22` pre-`T2`)**; dual-camera blackout (audio only) -> **`A3=9/23`** (`3/22` pre-`T2`, `0/3` FP); `70%` random vision drop (seed 42) -> `V2_TrackROI` `15/22` vs `F10` `17/22`.

16. **Fig. 16 (`fig16`):** Pre-`db40305` sideways caches vs upright (`db40305`) original-media train recall, no-train FPs, and Session 1/Session 2 stratification across all modalities and fusion rules. ([`fig16_upright_vs_baseline_ablation.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/figures/fig16_upright_vs_baseline_ablation.png))
17. **Fig. 17 (`fig17`):** Per-event optical detection recovery across all 27 original recordings and causal V3 FSM gate-closure timing relative to `T2`. ([`fig17_upright_event_recovery_and_fsm_timing.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/figures/fig17_upright_event_recovery_and_fsm_timing.png))
18. **Fig. 18 (`fig18`):** Recorded `[T0..T4]` continuous dual-camera passage coverage across all 23 trains (`75.19% -> 95.67%`, blind gaps `>=5s`: `8 -> 1`), exploratory ROI/locomotive trade-offs, and synthetic blackout/glare stress recovery. ([`fig18_mission12_roi_dropout_and_fusion_value.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/figures/fig18_mission12_roi_dropout_and_fusion_value.png))

## Table XIII — Mission 13 Vision & Audio Overfitting, Leakage & Clean-Retrain Generalization Audit
*(Evidence: [`MODEL_GENERALIZATION_AND_OVERFITTING_REPORT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/MODEL_GENERALIZATION_AND_OVERFITTING_REPORT.md), [`vision_baseline_39f402_audit.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_baseline_39f402_audit.json), [`vision_kaggle_clean_retrain_audit.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_kaggle_clean_retrain_audit.json), [`vision_clean_vs_frozen_field_diagnostics.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_clean_vs_frozen_field_diagnostics.json), [`audio_audit_summary.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/audio_audit_summary.json).)*

| Modality / Experiment | Split Protocol & Leakage Status | Train Metric | Val Metric | Test Metric (Official) | External `crossing_A` Diagnostics | Overfitting / Leakage Diagnosis |
|---|---|---:|---:|---:|---|---|
| **Vision Frozen `39f402` (`best Ep93`)** | `705d388743ea`: `100% <=600s` (`426/426` val, `416/416` test), `2.38x` aug | `mAP50-95=0.9055` (`mAP50=0.9950`) | `0.7684` (`0.9652`) (`last 0.7583`) | `0.8035` COCO (`0.9854`); `evaluator.py` `0.855` | `no_train_002` bridge `60/60` (`max 0.861`); `Eng001` `8/14` fr/bk | **Severe split leakage + Ep91–97 overfitting** (`-13.71 pp` Train->Val; unseen subset drops `-5.83` to `-6.83 pp`) |
| **Vision Clean `session_grouped_base`** | `1.00x` canonical, `0 <=600s`, `64.7%` same-day test | `mAP50-95=0.9008` | `0.7622` (`0.9717`) (`last 0.7604`) | `0.7113` (`0.9645`) (`-18.95 pp` gap) | `no_train_002` `59/60`; day-test `@0.35`: `253/4/21` (`Small 0.8732`) | **High cross-session variance (`-18.95 pp`)** |
| **Vision Clean `day_grouped_base`** | Strictly day-disjoint (`0% <=3600s`/day, `>=44.8h`) | `mAP50-95=0.8876` | `0.7696` (`0.9718`) (`last 0.7564`) | `0.7646` (`0.9807`) (`-12.30 pp` gap) | `no_train_002` `60/60`; day-test `@0.35`: `254/15/20` (`Small 0.8732`) | **Unmasked Ep73->100 `val/cls` creep (`+16.2%`)** |
| **Vision Clean `day_grouped_reg`** | Day-disjoint + MixUp/CopyPaste/WD/Dropout/cosLR | `mAP50-95=0.8938` | `0.7505` (`0.9583`) (`last 0.7527`) | **`0.7731` (`0.9810`, `P=0.9823`)** | `no_train_002` `60/60` (needs hard-neg); **`257/4/17` (`Small 0.9155`)** | **Best clean vision recipe** (`-73%` test FP vs base); single-crossing domain limit remains |
| **Audio Frozen `V3` (`ea1bb81d`, `T*=0.37`)** | `5` pos stems leaked (`59.3%` Val, `35.4%` Test pos wins) | `Win F1=0.9848` (`PR-AUC=0.9981`) | **`0.9942`** (leakage-inflated) | `0.8690` (`PR=0.9415`, `Rec Spec=0.6923`) | `T*=0.37`: `13/13` FPs (`Spec=0.0`, `PR=0.729`); `(0.75,k=2)`: `1/13` FP (`R=8/13`) | **Severe selection leakage + Test `-12.52 pp` + external shift failure** |
| **Audio Clean `stem_grouped_v3_recipe` (`5` seeds)** | Zero stem overlap (`120/26/26` clips), Fold-5 disjoint | `Win F1=0.9411` (`+- .0268`) | `0.8843` (`+- .0164`) | **`0.8413 +- .0221`** (`PR=0.9285`) | External `PR-AUC=0.6897 +- .0433`; `2.8 +- 0.45` NT FPs | **Moderate overfitting (`~10 pp` Train->Test) + `4.4` BN spikes; `SpecAug` `0.8486 +- .0174`; `GroupNorm` `0.7999` (`2.4` spikes); `5`-fold CV `0.8638`** |

19. **Fig. 19 (`fig_m13_v1`):** Frozen `YOLOv8n` (`39f402dfe460`) Epochs 1–97 loss divergence, post-mosaic (`Ep91–97`) overfitting zoom, `-13.71 pp` Train->Val `mAP@0.50:0.95` gap, and `evaluator.py` vs Ultralytics COCO reconciliation. ([`fig_m13_v1_39f402_training_curves.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_v1_39f402_training_curves.png))
20. **Fig. 20 (`fig_m13_vision_examples`):** Genuine `39f402dfe460` test predictions (`@0.35`) illustrating clean TP localization, `epoch_ms` small/foggy misses, and `front->rear`/`front->side` boundary ambiguity. ([`fig_m13_vision_examples.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_vision_examples.png))
21. **Fig. 21 (`fig_m13_v2`):** Test-split temporal/day/augmentation contamination (`705d` vs `session_grouped` vs `day_grouped`), clean Kaggle T4 100-epoch learning curves, Train->Val->Test `mAP@0.50:0.95` gaps, and held-out `2026-05-23` object-scale recall. ([`fig_m13_v2_leakage_and_clean_retrain.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_v2_leakage_and_clean_retrain.png))
22. **Fig. 22 (`fig_m13_v3`):** Clean `session_grouped_base` and `day_grouped_reg` held-out test confusion matrices, per-class COCO `AP@0.50:0.95`, and upright `crossing_A` overhead-bridge FP (`no_train_002`) vs locomotive (`engine_001`) field diagnostics. ([`fig_m13_v3_confusion_and_pr_comparison.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_v3_confusion_and_pr_comparison.png))
23. **Fig. 23 (`fig_m13_a1`):** Audio V1/V2/V3 historical curves and BatchNorm vs GroupNorm validation-loss instability on clean stem-grouped splits. ([`fig_m13_a1_training_and_instability.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_a1_training_and_instability.png))
24. **Fig. 24 (`fig_m13_a2`):** Audio ROC, Precision-Recall, Split/Domain Confusion, and Calibration (`Brier`/`ECE`) curves across ESC-50 Splits and external `crossing_A`. ([`fig_m13_a2_roc_pr_confusion_calibration.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_a2_roc_pr_confusion_calibration.png))
25. **Fig. 25 (`fig_m13_a3`):** ESC-50 negative-category false positives (`engine`, `church_bells`, `siren`), 5-seed ablation comparison, 5-fold strict grouped CV, and 20%–100% learning curve diagnosing sample scarcity. ([`fig_m13_a3_errors_cv_and_learning_curve.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_a3_errors_cv_and_learning_curve.png))
<!-- MISSION11_UPRIGHT_TABLES_END -->
