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
