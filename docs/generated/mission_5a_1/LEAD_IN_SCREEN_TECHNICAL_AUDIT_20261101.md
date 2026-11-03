# Missed-Train Lead-In Screen — Technical Audit (Mission 5A.1)

> The screen was **not** executed on real events, **not** wired into the official runner, and the 3.6 s value is **not** an approved threshold. The M3 question below is left to the researcher.

## 1. The 3.6-second value
* **Derivation (verified by re-running):** `derive_min_block_latency_s()` replays a synthetic constant `front` detection (confidence 0.9, one source) through `EventSimulationRunner` and returns the first blocked step. Results (3 repetitions each): **3.6 s at ticks 0.1 and 0.2**; **3.5 s at ticks 0.25 and 0.5**. It is deterministic but **tick-quantized — not a universal constant**.
* **Which engine/configuration?** `derive_min_block_latency_s` constructs `EventSimulationRunner()` **without a configuration**, i.e. the constructor defaults, *not* the frozen configuration. For the frozen values in this repository (`timing.tick_s 0.2`, warning 2.0, closing 3.0, confirm 2, vision threshold 0.35) the result with `EventSimulationRunner(config=load_frozen_config(...))` is identical (3.6 s), verified. The Mission 5A documents' wording "the real decision engine and gate model … frozen" is therefore true by coincidence of defaults, not by construction (F-07). Recommendation: when wiring is ever approved, pass the configuration explicitly and record its canonical hash in `min_block_latency_source`.
* Provenance: the screen requires a non-empty `min_block_latency_source` (enforced; tested), but nothing verifies the string describes how the number was obtained.

## 2. Behaviour (verified)
| Question | Finding |
|---|---|
| Insufficient lead-in → ? | `missed_train=None`, `missed_train_screen="insufficient_lead_in"`, `metric_exclusions["missed_train"]="insufficient_lead_in"`: **not evaluable, not a failure**. |
| Unknown/uncertain T0 | `lead_in_unverifiable` (not evaluable). T1 missing → `t1_missing`. T0 after T1 → `ValueError`. |
| Disabled by default? | Yes: `lead_in_min_block_latency_s=None` → `missed_train_screen="not_screened"`, behaviour identical to before. No environment/config switch exists. |
| Unwired from the official runner? | Yes (verified by search and test): the only `src/` files mentioning `lead_in_min_block_latency_s` / `screen_missed_train_lead_in` are `metrics.py` and `lead_in_screen.py`; `clock_aware.py`, `evaluation_runner.py` and `experiments/runner.py` do not pass it. |
| Accidental activation? | Only by explicitly passing the keyword. If someone enables it without T0 information, every event becomes `lead_in_unverifiable` (fail-closed, tested). Engine/no-train/GT-unverified early returns never run it. |
| Counts | `missed_train_insufficient_lead_in_count`, `missed_train_screen_excluded_count` in the summary; screened-out events are outside `missed_train_evaluable_count`. |

## 3. Relationship to the design document's M3 (not resolved here)
Implemented rule: `available = T1 − (T0 if observable else 0)`; pass iff `available ≥ latency`.
Design M3: evaluable iff `T0 ok` **or** `T1 ≥ R_block`.
| Situation | Design M3 | Implemented | Effect |
|---|---|---|---|
| T0 observable, `T1 − T0 < latency` | evaluable (may be counted as a miss) | **insufficient_lead_in** | implemented rule is stricter, physically motivated |
| T0 left-censored, `T1 ≥ latency` | evaluable | passed | same |
| T0 left-censored, `T1 < latency` | not evaluable | insufficient | same |
| T0 unknown/uncertain, `T1 ≥ latency` | evaluable | **lead_in_unverifiable** | implemented rule is stricter: the train might have appeared later than the replay start |
So the implemented screen **changes the meaning of M3** in two cells. `RD-021` asked for a feasibility screen distinguishing insufficient opportunity from failure; it did not say which cell semantics. **Technical recommendation (not a decision):** keep the physical rule for reporting, but publish both variants side by side in any descriptive table until the researcher chooses; keep `lead_in_unverifiable` as its own category; do not call 3.6 s a threshold—report it as "derived from synthetic replay of the frozen policy at tick 0.2 s".

## 4. Not done / not claimed
No wiring; no use on real events; no approval of 3.6 s; no change to M3.
