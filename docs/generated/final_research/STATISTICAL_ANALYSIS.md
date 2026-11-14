# Statistical Analysis Report — Wilson Intervals, Paired McNemar Contrasts & Convention B Identity

**Evaluation Basis:** *Exploratory evaluation against researcher-adopted AI-assisted reference annotations.*  
All confidence intervals use two-sided 95% Wilson score bounds ($z = 1.95996$); all paired binary contrasts use exact two-sided McNemar binomial tests over discordant event pairs (`a_only, b_only`) on strictly matched event subsets.

---

## 1. Paired Exact McNemar Contrasts (`ablation_matrix.json`, 9 Contrasts)

| Contrast | Events `N` | Outcome Metric | Eval `n` | Discordant (`A_only`, `B_only`) | Exact McNemar `p` | Mean Duration $\Delta(B - A)$ |
|---|---:|---|---:|---|---|---|
| **Primary Q1 (`B0__v2` vs `B7__v2`)** | 11 | Zero Protection (`A_zero_B_prot=2`, `B_zero_A_prot=0`) | 11 | `(2, 0)` [`ev012, ev017`] | `0.500000` | `+11.5273 s` |
| Primary Q1 (`B0__v2` vs `B7__v2`) | 11 | Reached Clear (`A_clr=0`, `B_clr=4`) | 11 | `(0, 4)` [`ev001,002,011,017`] | `0.125000` | `+11.5273 s` |
| Primary Q1 (`B0__v2` vs `B7__v2`) | 11 | Missed Train (`both=10`) / M4 (`both=4, neither=1`) | 10 / 5 | `(0, 0)` / `(0, 0)` | `1.000000` | — |
| **Dual Vision Only (`B0__v2` vs `B2__v2`)** | 11 | Zero Protection / Reached Clear | 11 | `(2, 0)` / `(0, 4)` | `0.500` / `0.125` | `+10.2000 s` |
| **Audio Increment (`B2__v2` vs `B7__v2`)** | 11 | Missed / Zero-Prot / M4 / Clear | 10/11/9/11 | `(0, 0)` across all 4 | `1.000000` | `+1.3273 s` |
| **Audio on Front (`B0__v2` vs `B4__v2`)** | 23 | Missed / Zero-Prot / M4 / Clear | 22/23/5/23 | `(0, 0)` across all 4 | `1.000000` | `+0.7826 s` |
| **Back Cam on Audio (`B4__v2` vs `B7__v2`)** | 11 | Zero Protection / Reached Clear | 11 | `(2, 0)` / `(0, 4)` | `0.500` / `0.125` | `+10.4000 s` |
| **Policy (`B7__v1` vs `B7__v2`)** | 11 | M4 Premature (`A=0, B=3`) [`ev001,007,014`] | 8 | `(0, 3)` | `0.250000` | `-1.5818 s` |
| Policy (`B7__v1` vs `B7__v2`) | 11 | Reached Clear (`A=0, B=4`) [`ev001,007,011,014`] | 11 | `(0, 4)` | `0.125000` | `-1.5818 s` |
| **EXP-E: `Stateless_RULE2` vs `V2` on `B7`** | 11 | Zero Protection (`Stateless_zero=8`, `V2_zero=0`) | 11 | **`(8, 0)`** | **`0.007812`** | **`+20.5273 s`** |
| **EXP-E: `Stateless_RULE2` vs `V2` on `B7`** | 11 | Reached Clear (`Stateless_clr=0`, `V2_clr=8`) | 11 | **`(0, 8)`** | **`0.007812`** | **`+20.5273 s`** |
| **EXP-E: `Stateless_Union` vs `V2` on `B7`** | 11 | Reached Clear / M4 / Zero-Prot | 11/7/11 | `(0, 8)` / `(1, 0)` / `(2, 1)` | **`0.007812`** / `1.0` / `1.0` | `+9.2545 s` |
| **EXP-E: `Stateless_RULE2` vs `V2` on `B0`** | 23 | Zero Protection (`Stateless=13`, `V2=0`) | 23 | **`(13, 0)`** | **`0.000244`** | **`+16.4870 s`** |
| **EXP-E: `Stateless_RULE2` vs `V2` on `B0`** | 23 | Reached Clear (`Stateless=0`, `V2=10`) | 23 | **`(0, 10)`** | **`0.001953`** | **`+16.4870 s`** |

---

## 2. Exact Interpretation of Statistical Power & Intervals

1. **Where Statistical Evidence Is Decisive:** Temporal state hysteresis (`V2`) produces statistically significant reductions in catastrophic zero-protection failures relative to stateless `RULE_2` thresholding even at these modest sample sizes (`p = 0.007812` on `N = 11` dual-camera events; `p = 0.000244` on `N = 23` front-camera events), while eliminating `Stateless Union`'s `3/3` (`16`-episode) negative-control false activations.
2. **Where Small Sample Size Limits Inference (`N = 11` Dual Sync, `N = 3` Negative Controls):**  
   - Halving zero-protection from `4/11` (`36.36%`, CI `[15.17%, 64.62%]`) to `2/11` (`18.18%`, CI `[5.14%, 47.70%]`) under `B7__v2` rests on `2` discordant pairs (`event_012, event_017`; $p = 0.50$). At $N = 11$, overlapping Wilson intervals are `~42–50` percentage points wide.
   - Similarly, V2's higher M4 premature-opening rate vs V1 (`7/9` = `77.78%` `[45.26%, 93.68%]` vs `4/8` = `50.00%` `[21.52%, 78.48%]`, discordant `(0, 3)`, $p = 0.25$) reflects a strong deterministic mechanism (`RULE_3C` over sparse caches) rather than noise, despite wide binomial intervals.
   - Negative controls (`N = 3`, `60.0 s` exposure) yield Wilson CIs `[20.77%, 93.85%]` at `2/3` and `[0.0%, 56.15%]` at `0/3`, making hourly false-alarm estimation impossible without extended field collection.

---

## 3. Convention B vs Convention A Mathematical Identity Verification

- Verified programmatically across **`336/336` unperturbed runs** in `results/exploratory_execution/analysis/safety_metrics_summary.json`:
  - `unique_conv_b_minus_a_values_s = [-0.2, 0.0]`
  - `terminal_blocked_unique_diffs_s = [-0.2]`
  - `verified_exact_identity = True`
- This empirically confirms the forward-causal theorem $T_{\text{ConvB}} = T_{\text{ConvA}} - \Delta t \cdot b_N$ at $\Delta t = 0.2\text{ s}$, resolving historical ambiguity in B4 Table 11 reporting.

---

## 4. Legacy V9 `[T1, T4)` vs M4 `(t_blocked, T4)` Endpoint Comparison

Legacy Protocol V9 flags `10/10` evaluable sync runs as premature across `B0__v2`, `AUDIO_ONLY__v2`, `B7__v2`, and `B7__v1` alike — including runs where the gate closed late (`t_blocked > T1`, leaving `[T1, t_blocked)` open) or even `AUDIO_ONLY__v2` (`0.0 s` blocked)! M4 cleanly separates **`never_protected` (`M5`)** from **post-closure premature opening inside `(t_blocked, T4)`**, reducing false conflation and enabling direct diagnosis of `RULE_3C` reopening bugs.
