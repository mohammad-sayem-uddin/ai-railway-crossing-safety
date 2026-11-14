# Professor Handoff Guide — Exploratory Execution & Root-Cause Audit

**Mandatory Governance & Evaluation Disclosure:**
> **Exploratory evaluation against researcher-adopted AI-assisted reference annotations.**  
> **Stage-2.1 Canonical Benchmark Status:** **NOT EXECUTED.** Zero Stage-2.1 human reviews, digital sign-offs, or `AUTH_MEDIA_ACCESS_GRANTED` tokens exist in the repository. Raw `.mov`/`.wav` access, canonical `ExecutionGate`, and `scripts/run_stage21_review.py` remain locked/untouched. Root [`docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`](../../../PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md) is hash-locked (`03444930...`) for baseline CI compliance; our completed exploratory manuscript draft lives at [`PAPER_DRAFT_EXPLORATORY_EXECUTION.md`](PAPER_DRAFT_EXPLORATORY_EXECUTION.md).

---

## 1. Executive Navigation Map

| Artifact | Purpose & Audience |
|---|---|
| [`FINAL_RESEARCH_COMPLETION_REPORT.md`](FINAL_RESEARCH_COMPLETION_REPORT.md) | Complete scientific answer to Protocol V2's RQ, ablation outcomes, root causes, stress results, and Stage-2.1 unblock path. |
| [`PAPER_DRAFT_EXPLORATORY_EXECUTION.md`](PAPER_DRAFT_EXPLORATORY_EXECUTION.md) | Full populated IEEE/Safety manuscript draft with Tables 1–5, embedded figures, and explicit exploratory disclaimers. |
| [`ARCHITECTURE_FINAL_STATUS.md`](ARCHITECTURE_FINAL_STATUS.md) | Perception-to-gate architecture, M44 `DISPLAYMATRIX` decode root cause on Nov 7–8 caches, `MultimodalEvidenceCollector` backfill & availability defects. |
| [`DATASET_AND_GROUND_TRUTH_REPORT.md`](DATASET_AND_GROUND_TRUTH_REPORT.md) | 27-event cohort taxonomy, left-censoring ($T_0 \le 0.0\text{ s}$, $T_1 \in [2.1, 5.8]\text{ s}$), R04 11-vs-16 sync scope, post-$T_4$ tail censoring. |
| [`EXPERIMENTAL_METHODOLOGY.md`](EXPERIMENTAL_METHODOLOGY.md) | Cache-only replay harness, Conditions `B0`–`B7`, V1/V2/Stateless policies, Convention A/B, M4 vs Legacy V9, `EXP-G/H/I/K` injections. |
| [`STATISTICAL_ANALYSIS.md`](STATISTICAL_ANALYSIS.md) | Two-sided 95% Wilson CIs, exact two-sided McNemar contrasts (`p = 0.000244`..`1.0`), Convention B vs A identity verification. |
| [`ERROR_ANALYSIS.md`](ERROR_ANALYSIS.md) | Mechanistic failure trace breakdown: left-censored misses, `RULE_3C` sparse-cache premature opening (`M4 = 7/9`), and single-frame backfill false closures. |
| [`SOFTWARE_TESTING_REPORT.md`](SOFTWARE_TESTING_REPORT.md) | Exact post-edit pytest audit (`3,807` passed / `33` preexisting triaged failures out of `3,840`), AST compliance, 8 new pipeline unit/integration tests. |
| [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) | Exact SHA-256 bindings (`FILE_HASH_MANIFEST.sha256`), Python `.venv` environment, and bit-for-bit verification (`344/344` files identical). |
| [`LIMITATIONS_AND_UNRESOLVED_ISSUES.md`](LIMITATIONS_AND_UNRESOLVED_ISSUES.md) | Exhaustive inventory of unresolved upstream defects, sample-size bounds, and concrete prerequisites for Stage-2.1 canonical completion. |

---

## 2. Headline Research Findings (Exploratory Cache-Only Suite)

1. **Primary Research Question (`B7` Dual+Audio+V2 vs `B0` Front-Only+V2 on `N = 11` Calibrated Sync Events):**
   - **Missed Train (`T_block <= T_1`):** `10/10` (`100%`, Wilson 95% CI `[0.7225, 1.0000]`) across both `B0__v2` and `DUAL_VISION_AUDIO__v2` (`event_005` excluded with `T1 = null`). Because all train events are left-censored ($T_1 \in [2.1, 5.8]\text{ s}$) and minimum V2 warning-to-blocked actuation latency is `3.4–3.6 s`, pre-entry closure is physically unachievable on this cohort under either configuration.
   - **Zero-Protection Failure (`closed_duration == 0.0 s`):** Halved from `4/11` (`36.36%`, CI `[0.1517, 0.6462]`) under `B0__v2` (`event_005, 009, 012, 017`) to `2/11` (`18.18%`, CI `[0.0514, 0.4770]`) under `DUAL_VISION_AUDIO__v2` (`event_005, 009` only; exact McNemar $p = 0.50$). Mean Convention-A closed duration increased by `+11.53 s` (`10.71 s -> 22.24 s`).
   - **Audio Incremental Effect (`DUAL_VISION__v2` vs `DUAL_VISION_AUDIO__v2`):** Identical binary event outcomes on `11` sync events (`zero_protection = 2/11`, `M4 = 7/9`, `reached_clear = 8/11`, all McNemar $p = 1.0$), adding `+1.33 s` mean closed duration (`20.91 s -> 22.24 s`) via `RULE_2` hold delays while maintaining `0.0 s` false actuation under `AUDIO_ONLY__v2` (`RULE_2` invariant preserved).
   - **Temporal State Policy vs Stateless Thresholds (`EXP-E`):** On `B7` (`N = 11`), `Stateless RULE_2` leaves `10/11` (`90.91%`) unprotected (`8` discordant pairs favored `V2`, exact McNemar $p = 0.007812$); across all `N = 23` front-camera events, `V2` rescues `13` unprotected events relative to `Stateless RULE_2` (`20/23` vs `7/23`, exact McNemar $p = 0.000244$). Meanwhile `Stateless OR-Union` drops `V2` audio gating and fails `3/3` (`16` episodes, `13.8 s`) on negative controls vs `0/3` (`0.0 s`) under `Stateless RULE_2`.
2. **Critical Pipeline Defects Uncovered During Execution:**
   - **Root Cause of Sparse Nov 7–8 Caches (Mission 39/43 vs Oct 13 Phase 10.1):** Both runs used the identical frozen YOLOv8n (`3f5bb5b2...`) and CompactTrainHornCNN V3 (`ea1bb81d...`) checkpoints, but Mission 37/38 switched decode to PyAV `source_pts=True`, which dropped `DISPLAYMATRIX` orthogonal rotation on `44/54` video sources (`24 front, 20 back`) prior to Mission 39/43 inference. Mission 44 (`db40305`) repaired `video.py` without re-running raw inference, leaving Nov 7–8 JSONL caches sparsely populated (`329` front + `1,020` back detections across `13,092` records).
   - **Premature Opening Mechanism (`M4 = 7/9` on `B7__v2` vs `4/8` on `V1`):** Policy V2's `RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE` interprets brief vision absence over sparse unrotated back-camera caches (`0.76%–5.07%` qualifying frame density on `9/10` events with `T4`) as full train departure, clearing `14.58 s` to `38.67 s` before `T4` (`event_002` clears before `T4` without unblocking before EOF). `event_011` (`+6.33 s` post-`T4`) is the sole sync event with sufficient post-`T4` recording tail (`7.73 s > 4.6 s`); `9/10` other `T4` events end `0.82 s–2.32 s` after `T4`.
   - **Collector `window_tolerance_s = 0.50 > stride_s = 0.20` Backfill & Availability Leak:** Re-emitting a single isolated YOLO detection across 3 consecutive `0.2 s` ticks bypasses `confirm_frames = 2`, causing `2/3` false closures (`14.2 s`) on `no_train_events/event_001` & `event_003` under `B0`. Tightening to `0.25 s` eliminates `no_train` single-frame backfill but doubles `B7__v2` zero-protection (`2/11 -> 4/11`) and cuts clearances (`8/11 -> 5/11`). Separately, `generate_frames_from_history` in [`collector.py`](../../../../src/railway_detection/fusion/collector.py) reads end-of-buffer `tracker.get_availability_map(t)`, leaking terminal `available=False` backward onto initial frames unless assembled sequentially.
3. **Fail-Safe Integrity & Reproducibility:** Across `202` perturbation runs (`EXP-G/H/I/K`), `0` runs transitioned directly from fault to `OPEN`; `11/11` out-of-order streams were rejected; `8/8` multi-train interrupts re-closed (`RULE_7`). End-to-end exploratory outputs (`344/344` files) verified bit-for-bit identical in `15.34 s`.

---

## 3. Visualizations

- [`fig1_ablation_rates_wilson_ci.png`](figures/fig1_ablation_rates_wilson_ci.png) — Ablation zero-protection, M4 premature opening, and blocked fraction with 95% Wilson CIs (`sync11` and `all23 + no_train`).
- [`fig2_sync11_event_timeline_outcomes.png`](figures/fig2_sync11_event_timeline_outcomes.png) — Per-event closed duration vs $T_4$ and `tol=0.25 s` sensitivity across all `11` calibrated events.
- [`fig3_departure_premature_opening_margins.png`](figures/fig3_departure_premature_opening_margins.png) — M4 premature-opening margins vs `RULE_3C` count, back-camera detection density, and post-$T_4$ recording margins.
- [`fig4_failure_injection_and_sensitivity.png`](figures/fig4_failure_injection_and_sensitivity.png) — All `21` failure-injection/recovery stress scenarios (`0/202` direct fault-to-open violations) and `window_tolerance_s` sensitivity.

---

## 4. Machine-Readable CSV Tables (`docs/generated/final_research/`)

- `BASELINE_COMPARISON.csv` | `MULTIMODAL_EVALUATION.csv` | `ABLATION_MATRIX.csv`
- `EVENT_LEVEL_RESULTS.csv` (`336` unperturbed runs) | `DEPARTURE_REOPENING_ANALYSIS.csv` (`11` sync events)
- `FAILURE_INJECTION_RESULTS.csv` (`21` scenarios) | `FAIL_SAFE_TRANSITION_RESULTS.csv` (`202` runs)
- `MISSED_TRAIN_ANALYSIS.csv` (`23` train events) | `PREMATURE_OPENING_ANALYSIS.csv` (`18` sync rows) | `WARNING_LEAD_TIME_ANALYSIS.csv` (`23` train events)
- `EXPERIMENT_REGISTRY.csv` (`9` families) | `ORIGINAL_RESEARCH_OBJECTIVES_STATUS.csv` (`10` objectives) | `FILE_HASH_MANIFEST.sha256`
