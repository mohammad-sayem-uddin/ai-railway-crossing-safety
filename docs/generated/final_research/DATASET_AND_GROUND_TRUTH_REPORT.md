# Dataset, Synchronization Scope & Reference Annotation Report

**Governance Disclosure:**  
> **Exploratory evaluation against researcher-adopted AI-assisted reference annotations.**  
> Official Stage-2.1 human adjudication (`data/ground_truth/reviews/`) contains **zero** valid approved records (`LEGACY_REVIEW_INVALIDATION_NOTICE` invalidated Oct 14, 2026 automated review burst). Exploratory evaluation uses `docs/generated/professor_evidence/mission43/RESEARCHER_ANNOTATION_ADOPTION.json` (`27` active schema `7.0.0` candidate proposals authorized solely for exploratory analysis).

---

## 1. Cohort Taxonomy (`N = 27` Events, Single Crossing `crossing_A`)

| Cohort | Count | Event IDs | Physical Characteristics & Benchmark Role |
|---|---:|---|---|
| **Train Events** | 23 | `train_events/event_001` .. `event_023` | Regional freight/intermodal passages (`12–88` railcars, daylight capture). All `23/23` exhibit **`t0_censored = True`** ($T_0 \le 0.0\text{ s}$); locomotive already approaching/entering frame at recording onset. |
| **No-Train Negative Controls** | 3 | `no_train_events/event_001` .. `event_003` | Nighttime negative controls (`event_001`: `24.6 s` front / `24.2 s` back; `event_002`: `11.8 s` / `13.2 s`; `event_003`: `23.6 s` / `22.6 s`; `60.0 s` cumulative front exposure on replay ticks). Roadway vehicles, farm traffic, pedestrians, wind. |
| **Engine-Only Anomaly** | 1 | `engine_events/event_001` | Isolated nighttime single locomotive (zero trailing cars; $T_1 = 0.0\text{ s}$ on front proposal). Analyzed solely in isolated descriptive reporting, excluded from train & negative-control denominators. |

---

## 2. Boundary Milestones & Left/Right Censoring Constraints

Reference timestamps record up to four event boundaries:
- $T_1$: Locomotive front enters approach warning zone / visual frame. On `22` evaluable train events, **`T1` spans `2.1 s` to `5.8 s`** (median `2.8 s`); `train_events/event_005` has **`T1 = null`** (Dining Car 1402 already occupying crossing at $t = 0.0\text{ s}$), capping `missed_train` denominator at **`N_eval <= 22`** (or `<= 10` in the `11`-event sync subset).
- $T_2, T_3, T_4$: Front/rear crossing centerline ($T_2, T_3$) and rear tail exit ($T_4$). Notice $T_4$ originates on `camera_back`; evaluating $T_4$ relative to replay state requires R04 master-clock alignment (`dual_sync11`) or local back-camera replay (`BACK_VISION`).
- **Severe Post-$T_4$ Right-Censoring (`departure_reopening_analysis.csv`):** Across the `10` calibrated sync train events with defined `T4_master_s`:
  - **`9/10` events end only `0.8199 s` (`event_007`) to `2.3220 s` (`event_013`) after $T_4$** (`event_001`: `0.994 s`, `002`: `1.013 s`, `006`: `0.888 s`, `009`: `0.996 s`, `012`: `1.232 s`, `014`: `2.119 s`, `017`: `0.935 s`). Because `T_clear = 3.0 s` plus `GATE_OPENING = 1.6 s` requires `>= 4.6 s` post-$T_4$ recording tail to legitimately clear and unblock **after** $T_4$, physical post-departure unblocking is **unobservable before EOF** on those `9` recordings unless premature clearance fires **before** $T_4$.
  - Only **`train_events/event_011`** (`t4_master_s = 34.6713 s`, `master_end_s = 42.4 s`, **`post_t4_recording_margin_s = 7.7287 s`**) provides a sufficiently long post-$T_4$ tail to observe legitimate post-departure clearance (`+6.3287 s`).

---

## 3. Hardware Cross-Camera Synchronization Scope (`phase12_r04_scope_decision.json`)

Cameras lacked genlock or NTP sync. Milestone R04 + `phase12_r04_scope_decision.json` enforce a **fail-closed scope boundary**:

- **Admitted for `DUAL_VISION` / `DUAL_VISION_AUDIO` (`11` `CALIBRATION_SUPPORTED` `accepted_sync_events`):**  
  `train_events/event_001`, `event_002`, `event_005`, `event_006`, `event_007`, `event_009`, `event_011`, `event_012`, `event_013`, `event_014`, `event_017`.
- **Fail-Closed Refused from `DUAL_*` (`16` events):**  
  - `train_events/event_010` (explicitly excluded by `phase12_r04_scope_decision.json` despite earlier candidate offset entry)
  - `12` train events without supported calibration (`event_003, 004, 008, 015, 016, 018–023`)
  - `3` negative controls (`no_train_events/event_001–003`) and `1` engine-only event (`engine_events/event_001`) -> `16` independent-camera events total (`10 + 1` in note: `16` = `1` excluded + `15` uncalibrated; evaluated strictly under single-camera `B0`, `AUDIO_ONLY`, `BACK_VISION`, and `FRONT_AUDIO` conditions).

---

## 4. Perceptual Cache Manifest Used (`m3_multimodal_replay_manifest.json`)

- **Manifest SHA-256:** `3c720167ea06b67141beb7cf33bd02ce325db62a3e100819f8aa4ad213d5bbbb`
- **Aggregate Cache Counts (`13,092` records):** `329` front vision detections, `1,020` back vision detections, `445/2,600` positive audio windows (`>= 0.37`).
- **Pre-Fix Rotation Caveat:** Vision caches reflect Mission 39/43 inference on pre-Mission-44 unrotated PyAV frames (`44/54` sources). Across the `10` sync events with $T_4$, `cam2_qualifying_density` (`conf >= 0.35`) is `0.00%` (`event_009, 011`), `0.76%` (`event_006`), `1.39%` (`event_014`), `1.57%` (`event_012`), `1.83%` (`event_013`), `2.72%` (`event_017`), `3.73%` (`event_001`), `5.07%` (`event_007`), and `43.86%` (`event_002`).
