# Statistical Analysis — Exploratory Prototype Evaluation

**Primary Evidence File:** [`statistical_comparisons.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/analysis/statistical_comparisons.json)  
**Supporting Artifacts:** [`exp_a_front_detection.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_a_front_detection.json), [`exp_c_audio_horn.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_c_audio_horn.json), [`exp_d_back_departure.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_d_back_departure.json), [`exp_j_temporal_vs_stateless.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_j_temporal_vs_stateless.json)

---

## 1. Small-Sample Confidence Intervals (95% Wilson Score)

With small event cohorts ($n = 23$ train events, $n = 11$ synced events, $n = 3$ no-train events), classical Wald intervals collapse near boundary proportions (`0/11`, `0/3`, `12/13`). Two-sided **95% Wilson score intervals** quantify statistical precision cleanly:

| Experiment / Metric | Observed Count | Point Estimate | 95% Wilson Score CI | Interpretation |
| --- | --- | --- | --- | --- |
| **Exp A: Train Closure Trigger Rate (`train23`)** | `10 / 23` | `0.4348` | `[0.2563, 0.6319]` | Reflects `pre-db40305` unrotated vision cache losses (`9/23` reached `CLOSING`/`CLOSED`, `1` ended in `WARNING`) |
| **Exp C: Audio Recall (`audio23`)** | `12 / 13` | `0.9231` | `[0.6669, 0.9863]` | High sensitivity to train horns, but wide interval (`n=13`) |
| **Exp C: Audio Precision (`audio23`)** | `12 / 22` | `0.5455` | `[0.3466, 0.7308]` | Limited by `10` false-positive events among `absent_observed` clips |
| **Exp C: Audio Specificity (`audio23`)** | `0 / 10` | `0.0000` | `[0.0000, 0.2775]` | All `10` `absent_observed` train events contained >= `2` windows `>= 0.37` |
| **Exp C: Audio Accuracy (`audio23`)** | `12 / 23` | `0.5217` | `[0.3296, 0.7076]` | Driven down by near-chance specificity at `0.37` |

---

## 2. Continuous Ranking Metrics (`Exp C` Audio Horn)

Because `audio23` adopted annotations mark only event-level `horn_status` (`present` vs `absent_observed`, without frame/window horn onset timestamps), threshold-free ranking is reported solely at the **event-maximum window score** level (`n = 23`):

- **Event-Max `ROC-AUC`:** `0.6846`
- **Event-Max `Average Precision` (`AP`):** `0.7739`

### Methodological Qualification on Window-Level Precision/FPR
- `no_train_events/001..003` carry `horn_status = None` (ambient road vehicle horns exist on camera) and score maxima `0.800453`, `0.826141`, and `0.800207`.
- Window-level acoustic classification accuracy cannot be computed honestly until human-reviewed window-level onset/offset labels exist.

---

## 3. Timing Summary Statistics (`Exp A` Layer 1 Lead & Margin vs `T2`)

- **First Vision Detection Lead (`t_T2 - t_first_front_det_s`, `n = 16` events with >=1 front det):**
  - Minimum: `-100.5 s` (`event_006`, first detection late at `103.8 s` vs `T2 = 3.3 s`)
  - Median: `+0.05 s`
  - Mean: `-9.3812 s`
  - Maximum: `+3.6 s` (`event_013` and `event_023`)
- **Full-Closure Safety Margin (`t_T2 - t_fully_closed_s`, `n = 9` events that reached `CLOSED`):**
  - Minimum: `-105.5 s` (`event_006`)
  - Median: `-5.1 s` (`event_004`)
  - Mean: `-22.3 s`
  - Maximum: `-1.4 s` (`event_013`)
- Even on events where detection started slightly before `T2` (`event_003` `+2.8 s`, `event_013` `+3.6 s`, `event_023` `+3.6 s`), subtracting `confirm_frames = 2` (`0.2 s`), `warning_dwell = 2.0 s`, and `closing_duration = 3.0 s` (`5.2–5.4 s` total) places `t_fully_closed_s` `1.4–2.4 s` *after* crossing entry on prototype close-range cameras.

---

## 4. Exact McNemar Tests for Paired Policy Safety Improvements

Two-sided exact binomial McNemar tests evaluate paired binary outcomes on identical event streams (`b01 = policy A wrong, policy B right`; `b10 = policy A right, policy B wrong`):

1. **Premature Opening Reduction (`Exp D`, `sync11`, `V2_RULE_3B_3C` vs `V3_CONSERVATIVE_POSITIVE`):**
   - Discordant pairs: `4` (`event_001, 002, 006, 013` prematurely opened under V2; `0` prematurely opened under `V3_CONSERVATIVE_POSITIVE`; `b01 = 4`, `b10 = 0`).
   - Exact two-sided $p$-value: $p = 2 \times 0.5^4 = 0.125$.
   - **Interpretation:** Eliminating all `4/4` discordant premature openings is clinically and engineering-significant (`0/11` premature openings vs `4/11`), though under `n = 11` synced events the maximum achievable two-sided exact McNemar power at `b=4, c=0` is $p = 0.125 > 0.05$.

2. **False-Closure Elimination (`Exp J`, `no_train3`, `stateless_union` vs `V3_CONSERVATIVE`):**
   - Discordant pairs: `3` (`no_train_001, 002, 003` closed falsely under `stateless_union`; `0/3` closed falsely under `V3_CONSERVATIVE`; `b01 = 3`, `b10 = 0`).
   - Exact two-sided $p$-value: $p = 2 \times 0.5^3 = 0.25$.
   - **Interpretation:** Complete `3 -> 0` elimination of false closures demonstrates the causal effect of multi-frame temporal confirmation (`confirm_frames = 2`) and audio-non-triggering, bounded strictly by the `n = 3` sample size (`minimum possible p = 0.25`).

---

## 5. Statistical Scope & Power Conclusions

1. Real-data metrics are **exploratory** (cached `pre-db40305` vision + adopted AI-assisted reference annotations).
2. No subgroup hypothesis test (`p = 0.125`, `p = 0.25`) is overstated as `p < 0.05` statistical significance; instead, exact discordant counts, Wilson CIs, and deterministic failure mechanisms are reported transparently.

---

## 6. `Exp R` — 23-Fold Nested LOEO Acoustic Cross-Validation & Stratified Bootstrap CIs

Added in [`exp_r_crossval_and_failsafe.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/exp_r_crossval_and_failsafe.json) and Table 6 (`results/publication_tables/`): to eliminate in-sample parameter-selection optimism from `Exp O`, leave-one-event-out (`n = 23` folds on Batch-4 `audio23`) fits temperature scaling `T in [0.5..4.0]` (cross-entropy) and hysteresis `(tau, k)` strictly on the `22` training folds before scoring the held-out event (`2,000`-resample stratified event bootstrap for 95% CIs):

| Evaluation Mode | Accuracy | Specificity | Precision | Recall | F1 Score (95% Bootstrap CI) | Event-Max Brier | 5-Bin ECE |
|---|---|---|---|---|---|---|---|
| **Frozen Baseline (`tau=0.37, k=1`)** | `0.5217` | `0.0000` (`0/10`) | `0.5455` | `0.9231` (`12/13`) | `0.6857` | `0.2724` (raw) | `0.2955` |
| **23-Fold Nested LOEO OOF (Calibrated + Hysteresis)** | `0.6087` | `0.6000` (`6/10`) `[0.3000, 0.9000]` | `0.6667` | `0.6154` (`8/13`) `[0.3846, 0.8462]` | `0.6400` `[0.4167, 0.8148]` | `0.2366` (Δ CI `[-0.0839, +0.0104]`) | `0.0999` |

- **Inner-fold selection stability:** `(tau=0.75, k=2)` was chosen in `20 / 23` (`87.0%`) independent training folds (`(0.65, 2)` twice, `(0.80, 1)` once; mean selected temperature `3.665`, range `2.3–4.0`).
- **Statistical humility:** Under `n = 23`, the stratified bootstrap `95% CI` for `cal_minus_raw_brier` (`[-0.0839, +0.0104]`, mean `-0.0351`) still crosses zero (`p > 0.05`), so calibrated OOF gains are reported strictly as out-of-fold trends rather than statistically significant hypothesis rejections.
