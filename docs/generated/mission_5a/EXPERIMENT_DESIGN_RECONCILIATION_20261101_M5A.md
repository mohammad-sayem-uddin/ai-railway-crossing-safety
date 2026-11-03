# Experiment-Design Reconciliation (RD-001, 020, 023, 029–038, 035)

> **PROPOSED — NOT APPROVED — NO CONDITION EXECUTED.** `EXPERIMENT_DESIGN_FINAL.md` (untracked, unchanged) is a **non-binding reference** except for the items listed as ADOPTED below. v7 governs ground-truth boundaries; v9 governs system and metric definitions (RD-001).

## 1. Section-by-section disposition of `EXPERIMENT_DESIGN_FINAL.md`

| Design item | Disposition | Note |
|---|---|---|
| Unit of analysis = event; Wilson 95 % intervals; no hourly nuisance rate; N1 form (event-level + blocked seconds, episodes, per-stream exposure) | **ADOPTED** | consistent with v9 §11/§19 |
| Engine event: separate case study, never pooled | **ADOPTED** (and engine **excluded from M4/M5**) | the design table that lists "Train, engine" for M4/M5 is **superseded** by the approved isolation |
| M4 / M5 | **ADOPTED in the v9-style form** implemented in code, with the corrected incomplete-replay classification | design's "any opening command" wording is not used; the implemented predicate is |
| M3 + `insufficient_lead_in` feasibility screen | **ADOPTED (implemented)** — with the physical lead-in rule (see screen document) | |
| Independent-camera clock rule (front stream for T1-dependent, back stream for T4-dependent) | **ADOPTED** | RD-015, RD-028 |
| Censoring: exclude from point estimates, count by reason | **ADOPTED** | RD-011; design's "censored marker stores a bound" is exploratory only |
| M1, M2, M6, M7, M8, M9, M10, V1, F1, D1 | **UNIMPLEMENTED / OUT OF SCOPE** for this mission | not implemented; not required by RD-020 |
| McNemar, Wilcoxon, Holm, bootstrap contrasts, "primary contrasts" | **NOT ADOPTED / REMOVED** | RD-023: descriptive statistics only, no p-values |
| `T4 ± u` sensitivity | **DEFERRED** | tolerance `u` deferred (RD-012) |
| Fused analysis primary if ≥ 20/23 calibrate | **SUPERSEDED** | only 12 candidates calibrate; fused is exploratory; the criterion is **not** claimed met |
| Corrected policy §5 (ABS/REAR clearance, fault recovery), C×T×P×A matrix, EMA | **NOT ADOPTED** | RD-029: freeze `decision_policy_v1` |
| Audio may start a warning | **NOT ADOPTED** | RD-030: audio supporting only |
| Quarantined duplicate engine event deny-list | **IO** | inventory stays 27 = 23 + 3 + 1 |

## 2. Frozen policy and constants (RD-029–033)

- **Decision policy `decision_policy_v1` is frozen for the descriptive study.** Neither v2-candidate nor the design's corrected policy replaces it.
- **Known limitations, documented not fixed** (second-hand, from the design/decision documents): no implementation of "positive rear confirmation" for clearance; the fault state is documented as lacking an exit in the design's audit; the policy's behaviour on these 27 recordings was seen before freezing (pilot contamination — to be disclosed); barrier timings are simulated; `rear` detections are rare in the field outputs.
- **Constants (vision 0.35/0.35, audio 0.37, staleness 2.0 s, tick 0.2 s, confirm 2, miss 2, dwell/closing/opening/clearance 2/3/3/3 s, fault 2, recovery 3 s): exploratory/descriptive only; no scientific approval; no calibration or sensitivity run.** Two-tick confirmation, two-miss tolerance and no EMA are retained (RD-031). Audio is supporting only: it cannot independently start a warning or grant clearance (RD-030).
- **TF-06 tick conflict (documented):** `decision_policy_v1.yaml` has `tick_interval_s: 0.1`; `frozen_experiment_v1.yaml` has `timing.tick_s: 0.2`. A search of `src/` shows `tick_interval_s` is **not read by any code**; `timing.tick_s` governs. The policy file was **not edited** (it is the frozen policy). A synthetic derivation shows the first-block latency is 3.6 s at both tick sizes, so the choice does not change the lead-in screen.
- **ROI (RD-033):** no ROI-dependent official analysis; the frozen configuration has no ROI section; the danger zone is defined by ground-truth landmarks only.

## 3. Proposed experiment design (RD-035, RD-036, RD-038) — design only

| Condition set | Replay | Outcomes it can feed | Status |
|---|---|---|---|
| B0 vision, B1 audio, B2 front fusion (container-native) | front stream | MTR (with screen), warning lead time, closed-duration telemetry | proposed |
| Back-stream condition(s) *(names TBD by researcher)* | back stream | M4, M5, clearance latency | proposed — back-stream audio availability not verified |
| Fused (R04-supported subset) | fused | exploratory comparison only | exploratory, 11-event authorized scope, no official dual-camera scope |

- **No condition is executed**; controlled reruns require separate authorization (RD-036). Historical B0–B7f outputs are diagnostic only and are never cited as results.
- **Fault injection (B6/B7)** is a separate descriptive section; synthetic fault outcomes are never pooled with natural events (RD-038). **B7e numeric delay, source and acceptance criteria remain DEFERRED (RD-034)**; only the delayed-timestamp *mechanism* was previously selected. B7d remains delivery-layer disorder.
- **No additional recordings** in this study (RD-037); limitations and possible future collection are documented, not planned.
- **Population (RD-039–041):** descriptive full cohort, no official split; sessions reported separately where supported; per-metric evaluable denominators; inventory 27 = 23 + 3 + 1 (engine = one event with three proposal versions).
- **Real-data descriptive pathway** does not exist (the approved descriptive mode accepts only synthetic evidence in code) and needs separate governance approval and implementation.
