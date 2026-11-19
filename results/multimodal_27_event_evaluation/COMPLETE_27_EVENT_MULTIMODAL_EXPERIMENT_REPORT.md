# Complete 27-Event Multimodal Experimental Evaluation & Fusion Verdict

**Qualification:** `Exploratory evaluation against researcher-adopted AI-assisted reference annotations.`
**Vision Data Provenance:** `Mission 39/43 Frozen YOLOv8n Actual Inference Caches (pre-db40305 unrotated container decoding; 6,613 front frames / 329 objects, 6,479 back frames / 1,020 objects)`
**Audio Data Provenance:** `Mission 39/43 Corrected Natural Log-Mel CompactTrainHornCNN Actual Inference Caches (2,600 windows of 1.0 s / 0.5 s hop)`
**Reference Labels:** `Researcher-adopted AI-assisted reference proposals (docs/generated/professor_evidence/mission43/RESEARCHER_ANNOTATION_ADOPTION.json)`
**Hardware / Sensor Scope:** `camera_1` (front) on 27/27 events; `camera_2` (back) on 27/27 events; `audio_1` (front microphone) on 27/27 events; **0/27** dedicated physical `camera_side` views; **0/27** track/occupancy sensors.
**Boundary Note on `engine_events/event_001`:** In its adopted proposal (`event_001_proposal_v3.json`), `engine_events/event_001` is a solitary light locomotive (`train_present = true`, `trailing_cars_count = 0`, `horn_status = absent_observed`) traversing `camera_back.mov`. Below we report BOTH **View 1** (`23` multi-car `train_events` vs `3` `no_train_events`, with `engine_events/001` in its own dedicated column) AND **View 2** (`23` `train_events` vs all `4` controls) & **View 3** (`24` rail vehicles vs `3` `no_train_events`).

## 1. Executive Answer: Does Multimodal Fusion Improve Performance?

| Architecture / Modality | Train TP/23 | Train FN/23 | No-Train FP/3 | Engine001 Det | Prec (V1) | Rec (V1) | NT Spec (V1) | F1 (V1) | Acc (26) | Rail24 Rec/F1 (V3) | McNemar p vs V2 (V1/V2) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Vision: Front-Only Any Frame (Stateless k>=1) | 16 | 7 | 2 | no | 88.9% | 69.6% | 33.3% | 78.0% | 65.4% | 16/24 (76.2%) | 0.2891 / 0.2891 |
| Vision: Front-Only L1 Causal (confirm>=2) [B0_front] | 10 | 13 | 0 | no | 100.0% | 43.5% | 100.0% | 60.6% | 50.0% | 10/24 (58.8%) | 1.0000 / 1.0000 |
| Vision: Back-Only Any Frame (Stateless k>=1) | 17 | 6 | 2 | YES | 89.5% | 73.9% | 33.3% | 81.0% | 69.2% | 18/24 (81.8%) | 0.1797 / 0.3438 |
| Vision: Back-Only Confirm2 (All Classes) | 9 | 14 | 2 | YES | 81.8% | 39.1% | 33.3% | 52.9% | 38.5% | 10/24 (55.6%) | 0.4531 / 0.2891 |
| Vision: Back-Only Confirm2 (Side/Rear Filtered) | 9 | 14 | 0 | no | 100.0% | 39.1% | 100.0% | 56.2% | 46.2% | 9/24 (54.5%) | 1.0000 / 1.0000 |
| Vision: Side-Class Proxy (Front+Back side>=1; 0 ded. cam) | 14 | 9 | 0 | no | 100.0% | 60.9% | 100.0% | 75.7% | 65.4% | 14/24 (73.7%) | 0.1250 / 0.1250 |
| Vision: Dual-Vision Causal (Front L1 OR Back Side/Rear L1) | 12 | 11 | 0 | no | 100.0% | 52.2% | 100.0% | 68.6% | 57.7% | 12/24 (66.7%) | 0.5000 / 0.5000 |
| Audio-Only: Frozen tau=0.37, k=1 [B1_audio] | 22 | 1 | 3 | no | 88.0% | 95.7% | 0.0% | 91.7% | 84.6% | 22/24 (89.8%) | 0.0490 / 0.0490 |
| Audio-Only: tau=0.37, k=2 consecutive | 17 | 6 | 3 | no | 85.0% | 73.9% | 0.0% | 79.1% | 65.4% | 17/24 (77.3%) | 0.4239 / 0.4239 |
| Audio-Only: Hysteresis tau=0.75, k=2 consecutive | 9 | 14 | 0 | no | 100.0% | 39.1% | 100.0% | 56.2% | 46.2% | 9/24 (54.5%) | 1.0000 / 1.0000 |
| Fusion F1: Stateless Union (Front>=1 OR Audio>=0.37) | 23 | 0 | 3 | no | 88.5% | 100.0% | 0.0% | 93.9% | 88.5% | 23/24 (92.0%) | 0.0213 / 0.0213 |
| Fusion F2: V3 Default B2/B4 (Front L1 + Advisory Audio) | 10 | 13 | 0 | no | 100.0% | 43.5% | 100.0% | 60.6% | 50.0% | 10/24 (58.8%) | 1.0000 / 1.0000 |
| Fusion F3: Front L1 OR (Weak Front>=1 & Audio 0.75 k=2) | 11 | 12 | 0 | no | 100.0% | 47.8% | 100.0% | 64.7% | 53.8% | 11/24 (62.9%) | 1.0000 / 1.0000 |
| Fusion F4: Front L1 OR Audio Hysteresis (0.75, k=2) | 14 | 9 | 0 | no | 100.0% | 60.9% | 100.0% | 75.7% | 65.4% | 14/24 (73.7%) | 0.1250 / 0.1250 |
| Fusion F5: Dual-Vision (Back Side/Rear) + Advisory Audio [B7] | 12 | 11 | 0 | no | 100.0% | 52.2% | 100.0% | 68.6% | 57.7% | 12/24 (66.7%) | 0.5000 / 0.5000 |
| Fusion F6: Full Multimodal (Front L1 OR Back Side/Rear L1 OR Audio 0.75 k=2) | 15 | 8 | 0 | no | 100.0% | 65.2% | 100.0% | 79.0% | 69.2% | 15/24 (76.9%) | 0.0625 / 0.0625 |

### Scientific Findings on Vision + Audio + Multi-Camera Fusion
1. **Default V3 Front+Audio Fusion (`F2` / `B2` / `B4`) gives +0.0% arrival recall gain over Front Vision Alone (`V2`):** Because audio at `tau=0.37` is strictly advisory (logs `L3_AUDIO_SUPPORT_ONLY` while IDLE on 20/27 events, never triggers closure), `V2` and `F2` achieve the exact same `10/23` (`43.5%`) train detection recall, `0/3` `no_train` false positives (`100.0%` precision/specificity), and `60.6%` F1. Because `0/27` real events have a physical occupancy sensor to authorize reopening under conservative V3, `L3_AUDIO_DWELL_HOLD` never fires on real B4 runs (reopening extension is verified only in synthetic suites).
2. **Naive Stateless Union Fusion (`F1`: `Vision>=1 OR Audio>=0.37`) maximizes recall to `23/23` (`100.0%`) at an unacceptable safety-false-positive cost:** `F1` triggers false closures on **`3/3` no-train controls** (`no_train_events/001..003`, `0.0%` no-train specificity) plus fails causal reopening stability in `exp_j`.
3. **Multi-Camera Spatial Fusion (`V8` / `F5`) improves detection recall from `43.5%` (`10/23`) to `52.2%` (`12/23`) with `0/3` `no_train` false positives — ONLY if `camera_2` is restricted to `side`/`rear` classes:** Raw `camera_2` `confirm>=2` across all classes (`V4`) generates false positives on `2/3` `no_train` controls (`001, 003`, `25`/`15` `front`-class hallucinations), even though it also detects the solitary locomotive in `engine_events/001` (`13` frames, `mean=0.805, max=0.899`, making View 3 `10/24` recall for `V4` alone). Filtering `camera_2` to `side`/`rear` classes (`V5` / `V8`) eliminates **all `2/3` `no_train` false positives (`FP=0/3`)** while recovering **`train_events/event_002`** (`43` back `side` objects, `42` frames) and **`train_events/event_016`** (`8` back `side` objects, `8` frames).
4. **Full Multimodal Fusion with High-Specificity Audio Hysteresis (`F6`: `Front L1 OR Back Side/Rear L1 OR Audio tau=0.75, k=2`) delivers the strongest zero-false-positive result (`+21.7 percentage points` recall, `+18.3 pp` F1):** Relative to Front-Only L1 (`10/23`, `43.5%` recall, `60.6%` F1), adding Back Side/Rear (`+2`: `event_002`, `event_016`) and high-specificity Audio Hysteresis (`+3` additional unique recoveries: `event_005` [completely dark `-90°` rotated night optical, `105` positive audio windows, `31` `>=0.75`, max `0.972`], `event_012` [`34` positive windows, `8` `>=0.75`, max `0.978`], `event_017` [nighttime, `21` positive windows, `8` `>=0.75`, max `0.986`]; plus overlapping confirmation on `event_002`, `event_004`, `event_006`, `event_007`, `event_013`, `event_018`) raises detection to **`15/23` (`65.2%`)** with **`0/3` `no_train` false positives (`100.0%` precision, `100.0%` specificity, `79.0%` F1, McNemar `p = 0.0625` vs `V2`)**.
   - *Methodological caveat:* This `tau=0.75, k=2` operating point was identified via `exp_o` hysteresis sweeping on the `27`-event cohort (in `exp_r` 23-fold LOEO, OOF audio metrics are `61.5%` recall / `60.0%` specificity / `64.0%` F1 against `horn_status`). Out-of-sample replication on a new session is required before promoting audio gating to production.
5. **Why `8/23` train events (`event_008, 009, 010, 011, 014, 015, 019, 020`) are STILL missed even under `F6`:** Unrotated `-90°` pre-`db40305` portrait video decoding crippled YOLOv8n (`0` or `1` scattered front frame; `0`–`4` scattered back `side`/`rear` frames below `confirm>=2`), AND `6` of those `8` events (`009, 010, 011, 014, 019, 020`) either had weak/brief horns (`maxA` `0.378`–`0.582`, `0` windows `>=0.75`) or had only single-window acoustic peaks (`event_008` max `0.811` `r75=1`, `event_015` max `0.840` `r75=1`, both failing `k=2`).

## 2. Complete 27-Event Perception Summary (Front Vision, Back Vision, Side Proxy, Audio & Ground Truth)

| Event ID | Cohort (Train/Rail GT) | Sess | Light | Sync | Front DF (c) [F/S/R] | Front Conf (mean/max) | Back DF (c/sr_c) [F/S/R] | Back Conf (mean/max) | Side Proxy (F+B / Tracker) | Aud >=0.37 (r37) | Aud >=0.75 (r75) | Aud Max@t | Adopted GT Horn |
|---|---|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|---|
| `train_events/event_001` | TRAIN (1/1) | Session 1 | day | sync11 | 6 (3) [1/5/0] | 0.47/0.64 | 7 (3/3) [0/7/0] | 0.52/0.69 | 12 (MOVING) | 0 (0) | 0 (0) | 0.247@3.0s | present (6.66s) |
| `train_events/event_002` | TRAIN (1/1) | Session 1 | day | sync11 | 1 (1) [1/0/0] | 0.72/0.72 | 42 (6/6) [0/43/0] | 0.57/0.80 | 43 (MOVING) | 3 (3) | 2 (2) | 0.983@3.5s | present (2.50s) |
| `train_events/event_003` | TRAIN (1/1) | Session 1 | day | indep | 58 (8) [7/52/0] | 0.62/0.86 | 1 (1/1) [0/0/1] | 0.60/0.60 | 52 (MOVING) | 8 (7) | 2 (1) | 0.914@4.5s | absent_observed (—) |
| `train_events/event_004` | TRAIN (1/1) | Session 1 | day | indep | 4 (2) [3/0/1] | 0.48/0.78 | 8 (3/3) [0/4/4] | 0.52/0.76 | 4 (UNOBSERVED) | 30 (10) | 5 (4) | 0.999@2.0s | present (0.96s) |
| `train_events/event_005` | TRAIN (1/1) | Session 1 | day | sync11 | 0 (0) [0/0/0] | — | 0 (0/0) [0/0/0] | — | 0 (UNOBSERVED) | 105 (32) | 31 (7) | 0.972@6.5s | present (1.28s) |
| `train_events/event_006` | TRAIN (1/1) | Session 1 | day | sync11 | 8 (3) [0/0/8] | 0.56/0.75 | 3 (3/3) [0/3/0] | 0.62/0.85 | 3 (MOVING) | 51 (7) | 6 (3) | 0.816@8.0s | present (121.28s) |
| `train_events/event_007` | TRAIN (1/1) | Session 1 | day | sync11 | 4 (2) [0/5/0] | 0.61/0.81 | 7 (4/4) [1/6/0] | 0.55/0.82 | 11 (MOVING) | 16 (5) | 5 (4) | 0.990@33.5s | absent_observed (—) |
| `train_events/event_008` | TRAIN (1/1) | Session 1 | day | indep | 0 (0) [0/0/0] | — | 2 (1/1) [0/0/2] | 0.43/0.50 | 0 (UNOBSERVED) | 13 (2) | 1 (1) | 0.811@27.0s | absent_observed (—) |
| `train_events/event_009` | TRAIN (1/1) | Session 1 | day | sync11 | 0 (0) [0/0/0] | — | 0 (0/0) [0/0/0] | — | 0 (UNOBSERVED) | 7 (2) | 0 (0) | 0.582@29.0s | absent_observed (—) |
| `train_events/event_010` | TRAIN (1/1) | Session 1 | day | indep | 1 (1) [1/0/0] | 0.74/0.74 | 0 (0/0) [0/0/0] | — | 0 (UNOBSERVED) | 2 (1) | 0 (0) | 0.447@15.0s | absent_observed (—) |
| `train_events/event_011` | TRAIN (1/1) | Session 1 | day | sync11 | 2 (1) [0/0/3] | 0.52/0.60 | 0 (0/0) [0/0/0] | — | 0 (UNOBSERVED) | 3 (1) | 0 (0) | 0.450@34.0s | absent_observed (—) |
| `train_events/event_012` | TRAIN (1/1) | Session 1 | day | sync11 | 0 (0) [0/0/0] | — | 2 (1/0) [2/0/0] | 0.39/0.40 | 0 (UNOBSERVED) | 34 (8) | 8 (3) | 0.978@37.0s | present (6.78s) |
| `train_events/event_013` | TRAIN (1/1) | Session 1 | day | sync11 | 6 (3) [5/0/1] | 0.66/0.84 | 3 (1/1) [0/3/0] | 0.41/0.47 | 3 (MOVING) | 32 (7) | 7 (2) | 0.914@1.5s | present (4.22s) |
| `train_events/event_014` | TRAIN (1/1) | Session 1 | day | sync11 | 4 (1) [3/1/0] | 0.50/0.54 | 2 (1/1) [0/2/0] | 0.50/0.59 | 3 (MOVING) | 5 (1) | 0 (0) | 0.517@24.0s | absent_observed (—) |
| `train_events/event_015` | TRAIN (1/1) | Session 1 | day | indep | 0 (0) [0/0/0] | — | 0 (0/0) [0/0/0] | — | 0 (UNOBSERVED) | 5 (3) | 1 (1) | 0.840@23.5s | present (14.85s) |
| `train_events/event_016` | TRAIN (1/1) | Session 1 | day | indep | 5 (1) [5/1/0] | 0.45/0.53 | 8 (5/5) [0/8/0] | 0.55/0.89 | 9 (SINGLE_FRAME) | 5 (2) | 0 (0) | 0.709@22.0s | absent_observed (—) |
| `train_events/event_017` | TRAIN (1/1) | Session 1 | day | sync11 | 0 (0) [0/0/0] | — | 4 (1/1) [0/4/0] | 0.42/0.49 | 4 (MOVING) | 21 (5) | 8 (3) | 0.986@66.0s | present (0.83s) |
| `train_events/event_018` | TRAIN (1/1) | Session 1 | day | indep | 4 (3) [4/0/0] | 0.48/0.67 | 1 (1/1) [0/1/0] | 0.40/0.40 | 1 (UNOBSERVED) | 34 (14) | 10 (3) | 0.998@6.5s | present (5.95s) |
| `train_events/event_019` | TRAIN (1/1) | Session 1 | day | indep | 1 (1) [0/0/1] | 0.36/0.36 | 0 (0/0) [0/0/0] | — | 0 (UNOBSERVED) | 6 (2) | 0 (0) | 0.550@18.5s | absent_observed (—) |
| `train_events/event_020` | TRAIN (1/1) | Session 1 | day | indep | 0 (0) [0/0/0] | — | 3 (1/0) [3/0/0] | 0.51/0.60 | 0 (UNOBSERVED) | 1 (1) | 0 (0) | 0.378@20.0s | present (0.58s) |
| `train_events/event_021` | TRAIN (1/1) | Session 2 | day | indep | 6 (3) [0/6/0] | 0.52/0.72 | 230 (69/69) [1/225/4] | 0.83/0.94 | 231 (MOVING) | 4 (2) | 0 (0) | 0.578@47.5s | present (51.39s) |
| `train_events/event_022` | TRAIN (1/1) | Session 2 | day | indep | 14 (4) [0/14/0] | 0.58/0.77 | 228 (219/189) [222/205/5] | 0.78/0.95 | 219 (MOVING) | 3 (1) | 0 (0) | 0.603@43.5s | present (2.37s) |
| `train_events/event_023` | TRAIN (1/1) | Session 2 | day | indep | 196 (136) [15/182/2] | 0.89/0.94 | 208 (111/111) [0/196/14] | 0.87/0.94 | 378 (MOVING) | 18 (11) | 1 (1) | 0.786@1.5s | absent_observed (—) |
| `no_train_events/event_001` | NO_TRN (0/0) | Session 2 | night | indep | 1 (1) [1/0/0] | 0.38/0.38 | 24 (4/0) [25/0/0] | 0.48/0.68 | 0 (UNOBSERVED) | 11 (3) | 1 (1) | 0.800@24.0s | None (—) |
| `no_train_events/event_002` | NO_TRN (0/0) | Session 2 | night | indep | 0 (0) [0/0/0] | — | 0 (0/0) [0/0/0] | — | 0 (UNOBSERVED) | 12 (5) | 2 (1) | 0.826@6.5s | None (—) |
| `no_train_events/event_003` | NO_TRN (0/0) | Session 2 | night | indep | 1 (1) [1/0/0] | 0.51/0.51 | 15 (3/0) [15/0/0] | 0.51/0.69 | 0 (UNOBSERVED) | 16 (9) | 1 (1) | 0.800@9.5s | None (—) |
| `engine_events/event_001` | ENGINE (0/1) | Session 2 | night | indep | 0 (0) [0/0/0] | — | 13 (12/0) [14/0/0] | 0.81/0.90 | 0 (UNOBSERVED) | 0 (0) | 0 (0) | 0.143@1.0s | absent_observed (—) |

## 3. Event-by-Event Modality & Fusion Predictions vs Ground Truth (All 27 Events)

| Event ID | GT | V1 Fr>=1 | V2 Fr L1 | V4 Bk All | V5 Bk SR | V6 Side>=1 | V8 Dual SR | A1 Aud.37 | A3 Aud.75k2 | F1 Union | F2 V3 Def | F3 Weak+A | F4 Fr+A75k2 | F6 Full MM | V3 Gate State | F6 Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `train_events/event_001` | POS | POS | POS | POS | POS | POS | POS | neg | neg | POS | POS | POS | POS | POS | WARNING/OPEN | BACK_SR_L1_SYNC |
| `train_events/event_002` | POS | POS | neg | POS | POS | POS | POS | POS | POS | POS | neg | POS | POS | POS | IDLE/OPEN | AUDIO_075_K2 |
| `train_events/event_003` | POS | POS | POS | neg | neg | POS | POS | POS | neg | POS | POS | POS | POS | POS | CROSSING_OCCUPIED/CLOSED | FRONT_L1 |
| `train_events/event_004` | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | TRAIN_DEPARTING/CLOSED | AUDIO_075_K2 |
| `train_events/event_005` | POS | neg | neg | neg | neg | neg | neg | POS | POS | POS | neg | neg | POS | POS | IDLE/OPEN | AUDIO_075_K2 |
| `train_events/event_006` | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | TRAIN_DEPARTING/CLOSED | AUDIO_075_K2 |
| `train_events/event_007` | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | POS | CROSSING_OCCUPIED/CLOSED | FRONT_L1 |
| `train_events/event_008` | POS | neg | neg | neg | neg | neg | neg | POS | neg | POS | neg | neg | neg | neg | IDLE/OPEN | NONE |
| `train_events/event_009` | POS | neg | neg | neg | neg | neg | neg | POS | neg | POS | neg | neg | neg | neg | IDLE/OPEN | NONE |
| `train_events/event_010` | POS | POS | neg | neg | neg | neg | neg | POS | neg | POS | neg | neg | neg | neg | IDLE/OPEN | NONE |
| `train_events/event_011` | POS | POS | neg | neg | neg | neg | neg | POS | neg | POS | neg | neg | neg | neg | IDLE/OPEN | NONE |
| `train_events/event_012` | POS | neg | neg | neg | neg | neg | neg | POS | POS | POS | neg | neg | POS | POS | IDLE/OPEN | AUDIO_075_K2 |
| `train_events/event_013` | POS | POS | POS | neg | neg | POS | POS | POS | POS | POS | POS | POS | POS | POS | TRAIN_DEPARTING/CLOSED | FRONT_L1 |
| `train_events/event_014` | POS | POS | neg | neg | neg | POS | neg | POS | neg | POS | neg | neg | neg | neg | IDLE/OPEN | NONE |
| `train_events/event_015` | POS | neg | neg | neg | neg | neg | neg | POS | neg | POS | neg | neg | neg | neg | IDLE/OPEN | NONE |
| `train_events/event_016` | POS | POS | neg | POS | POS | POS | POS | POS | neg | POS | neg | neg | neg | POS | IDLE/OPEN | BACK_SR_L1_LOCAL |
| `train_events/event_017` | POS | neg | neg | neg | neg | POS | neg | POS | POS | POS | neg | neg | POS | POS | IDLE/OPEN | AUDIO_075_K2 |
| `train_events/event_018` | POS | POS | POS | neg | neg | POS | POS | POS | POS | POS | POS | POS | POS | POS | CROSSING_OCCUPIED/CLOSED | AUDIO_075_K2 |
| `train_events/event_019` | POS | POS | neg | neg | neg | neg | neg | POS | neg | POS | neg | neg | neg | neg | IDLE/OPEN | NONE |
| `train_events/event_020` | POS | neg | neg | neg | neg | neg | neg | POS | neg | POS | neg | neg | neg | neg | IDLE/OPEN | NONE |
| `train_events/event_021` | POS | POS | POS | POS | POS | POS | POS | POS | neg | POS | POS | POS | POS | POS | CROSSING_OCCUPIED/CLOSED | BACK_SR_L1_LOCAL |
| `train_events/event_022` | POS | POS | POS | POS | POS | POS | POS | POS | neg | POS | POS | POS | POS | POS | CROSSING_OCCUPIED/CLOSED | FRONT_L1 |
| `train_events/event_023` | POS | POS | POS | POS | POS | POS | POS | POS | neg | POS | POS | POS | POS | POS | TRAIN_DEPARTING/CLOSED | FRONT_L1 |
| `no_train_events/event_001` | NEG | POS | neg | POS | neg | neg | neg | POS | neg | POS | neg | neg | neg | neg | IDLE/OPEN | NONE |
| `no_train_events/event_002` | NEG | neg | neg | neg | neg | neg | neg | POS | neg | POS | neg | neg | neg | neg | IDLE/OPEN | NONE |
| `no_train_events/event_003` | NEG | POS | neg | POS | neg | neg | neg | POS | neg | POS | neg | neg | neg | neg | IDLE/OPEN | NONE |
| `engine_events/event_001` | ENG | neg | neg | POS | neg | neg | neg | neg | neg | neg | neg | neg | neg | neg | IDLE/OPEN | NONE |

## 4. Crossing Decision Timestamps (Arrival, Warning, Closure, Clearance & Reopening)

| Event ID | GT T0/T2 (Front) | GT T4 | Fr First/L1 | B4 Warn/Cmd/Full | Margin vs T2 | Audio Dwell Hold? | M2 Back Last | M2 Err vs T4 | M3 Sync11 (Cons / Guarded) | F6 Trig@t | Diagnosis |
|---|---|---|---:|---:|---:|---|---:|---:|---|---|---|
| `train_events/event_001` | 0.00/6.50 | 52.41 | 26.82/49.80 | 49.80/—/— | — | no | 42.01 | -2.99s | SafeClosed / SafeClosed | BACK_SR_L1_SYNC@14.01s | Detected by Front L1 (3 consec), but late (26.82s vs T2=6.5s) |
| `train_events/event_002` | 0.00/3.60 | 32.99 | 3.60/— | —/—/— | — | SuppOnly_Idle | 27.80 | -1.00s | SafeClosed / SafeClosed | AUDIO_075_K2@3.50s | Missed by Front L1 (df=1, max_c=1); RECOVERED by Back side/rear L1 (6 consec) + Audio >=0.75 k=2 (run=2, max=0.9834) |
| `train_events/event_003` | 0.00/2.80 | 30.50 | 0.00/0.20 | 0.20/2.40/5.20 | -2.40s | no | 31.40 | 0.90s | uncal. | FRONT_L1@0.20s | Detected cleanly by Front L1 (8 consec frames) |
| `train_events/event_004` | 0.00/2.90 | 76.80 | 2.40/3.20 | 3.20/5.20/8.00 | -5.10s | SuppOnly_Idle | 78.01 | 1.21s | uncal. | AUDIO_075_K2@1.50s | Detected cleanly by Front L1 (2 consec frames) |
| `train_events/event_005` | 0.00/— | — | —/— | —/—/— | — | SuppOnly_Idle | — | — | SafeClosed / SafeClosed | AUDIO_075_K2@2.50s | Missed by Front L1 (df=0, max_c=0); RECOVERED by Audio >=0.75 k=2 (run=7, max=0.9715) |
| `train_events/event_006` | 0.00/3.30 | 130.31 | 103.61/104.00 | 104.00/106.00/108.80 | -105.50s | SuppOnly_Idle | 90.61 | -35.19s | SafeClosed / 114.4s (prem) | AUDIO_075_K2@8.50s | Detected by Front L1 (3 consec), but late (103.6083s vs T2=3.3s) |
| `train_events/event_007` | 0.00/3.40 | 42.38 | 16.01/16.40 | 16.40/18.60/21.40 | -18.00s | SuppOnly_Idle | 22.40 | -11.10s | SafeClosed / 38.2s (prem) | FRONT_L1@16.40s | Detected by Front L1 (2 consec), but late (16.0117s vs T2=3.4s) |
| `train_events/event_008` | 0.00/3.20 | 61.20 | —/— | —/—/— | — | SuppOnly_Idle | 22.20 | -39.00s | uncal. | NONE | Missed by Front L1 (df=0), Back side/rear L1 (c=1), & Audio >=0.75 k=2 (r75=1, maxA=0.8109) |
| `train_events/event_009` | 1.50/5.00 | 45.80 | —/— | —/—/— | — | SuppOnly_Idle | — | — | SafeClosed / SafeClosed | NONE | Missed by Front L1 (df=0), Back side/rear L1 (c=0), & Audio >=0.75 k=2 (r75=0, maxA=0.582) |
| `train_events/event_010` | 0.00/3.50 | 22.40 | 0.20/— | —/—/— | — | SuppOnly_Idle | — | — | uncal. | NONE | Missed by Front L1 (df=1), Back side/rear L1 (c=0), & Audio >=0.75 k=2 (r75=0, maxA=0.4473) |
| `train_events/event_011` | 0.00/3.60 | 34.67 | 28.22/— | —/—/— | — | SuppOnly_Idle | — | — | SafeClosed / SafeClosed | NONE | Missed by Front L1 (df=2), Back side/rear L1 (c=0), & Audio >=0.75 k=2 (r75=0, maxA=0.4502) |
| `train_events/event_012` | 0.00/3.90 | 74.77 | —/— | —/—/— | — | SuppOnly_Idle | 31.60 | -37.60s | SafeClosed / SafeClosed | AUDIO_075_K2@25.00s | Missed by Front L1 (df=0, max_c=0); RECOVERED by Audio >=0.75 k=2 (run=3, max=0.9779) |
| `train_events/event_013` | 0.00/4.00 | 74.08 | 0.40/0.60 | 0.60/2.60/5.40 | -1.40s | no | 70.60 | -0.20s | SafeClosed / 48.2s (prem) | FRONT_L1@0.60s | Detected cleanly by Front L1 (3 consec frames) |
| `train_events/event_014` | 0.00/3.40 | 55.28 | 1.80/— | —/—/— | — | SuppOnly_Idle | 19.40 | -31.80s | SafeClosed / SafeClosed | NONE | Missed by Front L1 (df=4), Back side/rear L1 (c=1), & Audio >=0.75 k=2 (r75=0, maxA=0.5166) |
| `train_events/event_015` | 1.50/5.00 | 19.50 | —/— | —/—/— | — | SuppOnly_Idle | — | — | uncal. | NONE | Missed by Front L1 (df=0), Back side/rear L1 (c=0), & Audio >=0.75 k=2 (r75=1, maxA=0.8402) |
| `train_events/event_016` | 1.50/5.00 | 44.10 | 2.00/— | —/—/— | — | SuppOnly_Idle | 41.40 | -2.70s | uncal. | BACK_SR_L1_LOCAL@13.20s | Missed by Front L1 (df=5, max_c=1); RECOVERED by Back side/rear L1 (5 consec) |
| `train_events/event_017` | 0.00/3.60 | 87.07 | —/— | —/—/— | — | SuppOnly_Idle | 81.01 | -1.49s | SafeClosed / SafeClosed | AUDIO_075_K2@22.00s | Missed by Front L1 (df=0, max_c=0); RECOVERED by Audio >=0.75 k=2 (run=3, max=0.9855) |
| `train_events/event_018` | 0.00/3.50 | 50.80 | 4.20/50.60 | 50.60/52.60/55.40 | -51.90s | SuppOnly_Idle | 44.00 | -6.80s | uncal. | AUDIO_075_K2@6.50s | Detected by Front L1 (3 consec), but late (4.2033s vs T2=3.5s) |
| `train_events/event_019` | 0.00/3.80 | 47.20 | 9.61/— | —/—/— | — | SuppOnly_Idle | — | — | uncal. | NONE | Missed by Front L1 (df=1), Back side/rear L1 (c=0), & Audio >=0.75 k=2 (r75=0, maxA=0.55) |
| `train_events/event_020` | 0.00/3.10 | 28.70 | —/— | —/—/— | — | SuppOnly_Idle | 7.60 | -21.10s | uncal. | NONE | Missed by Front L1 (df=0), Back side/rear L1 (c=0), & Audio >=0.75 k=2 (r75=0, maxA=0.378) |
| `train_events/event_021` | 0.00/4.10 | 60.10 | 6.81/9.60 | 9.60/11.80/14.60 | -10.50s | SuppOnly_Idle | 59.80 | -0.30s | uncal. | BACK_SR_L1_LOCAL@7.40s | Detected by Front L1 (3 consec), but late (6.8067s vs T2=4.1s) |
| `train_events/event_022` | 0.00/3.30 | 45.10 | 2.40/2.80 | 2.80/4.80/7.60 | -4.30s | no | 45.60 | 0.50s | uncal. | FRONT_L1@2.80s | Detected cleanly by Front L1 (4 consec frames) |
| `train_events/event_023` | 0.00/3.60 | 43.40 | 0.00/0.20 | 0.20/2.40/5.20 | -1.60s | no | 45.60 | 2.20s | uncal. | FRONT_L1@0.20s | Detected cleanly by Front L1 (136 consec frames) |
| `no_train_events/event_001` | —/— | — | 13.80/— | —/—/— | — | SuppOnly_Idle | 18.82 | — | uncal. | NONE | TN under V2/F5/F6; front=1f(max_c=1), back_false_front=25obj, audio_037=11w(r75=1) |
| `no_train_events/event_002` | —/— | — | —/— | —/—/— | — | SuppOnly_Idle | — | — | uncal. | NONE | TN under V2/F5/F6; audio_037=12w(r75=1) |
| `no_train_events/event_003` | —/— | — | 12.81/— | —/—/— | — | SuppOnly_Idle | 21.40 | — | uncal. | NONE | TN under V2/F5/F6; front=1f(max_c=1), back_false_front=15obj, audio_037=16w(r75=1) |
| `engine_events/event_001` | 0.00/0.00 | — | —/— | —/—/— | — | no | 9.60 | — | uncal. | NONE | Solitary light locomotive (train_present=True, 0 cars): front=0f, audio=0w(max=0.1428); back_cls_front=14obj(c=12, maxC=0.8995), 0 side/rear |

## 5. Subgroup Breakdown & Acoustic Horn Ground-Truth Check

### 5.1 Train Detection Stratification (Recording Session & Sync Calibration Scope; gt_is_train_event)
| Subgroup (F6 vs Front L1 V2) | Events (Train/Ctrl) | V2 Front L1 Recall | F6 Multimodal Recall | Gain | V2 Ctrl FP | F6 Ctrl FP |
|---|---:|---:|---:|---:|---:|---:|
| Session 1 (2026-09-14 Day Overcast) | 20 (20/0) | 7/20 (35.0%) | 12/20 (60.0%) | +5 | 0 | 0 |
| Session 2 (2026-10-04 Mixed Day/Night) | 7 (3/4) | 3/3 (100.0%) | 3/3 (100.0%) | +0 | 0 | 0 |
| Sync11 Calibrated Dual-Camera Subset | 11 (11/0) | 4/11 (36.4%) | 8/11 (72.7%) | +4 | 0 | 0 |
| Uncalibrated Independent-Camera Subset | 16 (12/4) | 6/12 (50.0%) | 7/12 (58.3%) | +1 | 0 | 0 |

### 5.2 Audio-Only Evaluated Against Adopted Horn Ground Truth (`horn_status == 'present'`)
| Audio Operating Rule | TP (Horn=Present) | FN | FP (Horn=Absent) | TN | Precision | Recall | Specificity | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Audio tau=0.37, k=1 (All 27: 13 horn+ / 14 horn-) | 12/13 | 1 | 13/14 | 1 | 48.0% | 92.3% | 7.1% | 63.2% |
| Audio tau=0.37, k=2 (All 27: 13 horn+ / 14 horn-) | 10/13 | 3 | 10/14 | 4 | 50.0% | 76.9% | 28.6% | 60.6% |
| Audio tau=0.75, k=2 Hysteresis (All 27: 13 horn+ / 14 horn-) | 8/13 | 5 | 1/14 | 13 | 88.9% | 61.5% | 92.9% | 72.7% |
| 23-Fold Nested LOEO Calibrated OOF (Train23: 13 horn+ / 10 horn-) | 8/13 | 5 | 4/10 | 6 | 66.7% | 61.5% | 60.0% | 64.0% |

## 6. Explicit Boundary: Metrics That Existing Data & Labels Cannot Establish

| Metric / Capability | Status on Current Dataset & Repository | Why / Blocking Evidence Gap |
|---|---|---|
| Layer B frame-level YOLO mAP / IoU / Precision-Recall curves | **CANNOT BE COMPUTED** | Proposals provide event-level `T0..T4` timestamps only; 0 frame-level bounding boxes exist. |
| Window-level audio horn F1 / frame-accurate horn offset error | **CANNOT BE COMPUTED** | Proposals provide `horn_status` + `horn_onset_s` only; 0 window-level horn offset timestamps exist. |
| Upright (`0°` / display-matrix rotated) YOLO evaluation on Layer B | **CANNOT BE EXECUTED WITHOUT MEDIA AUTH** | Cached detections come from pre-`db40305` unrotated container frames (`48/54` streams rotated `-90°` in metadata); `AUTH-MEDIA-ACCESS.json` is absent. |
| Physical dedicated side-camera evaluation | **0/27 EVENTS** | Hardware setup deployed `camera_1` (front) and `camera_2` (back) only; `side` relies on YOLO `side` proxy class. |
| Physical track/occupancy sensor gate reopening (`V3 CONSERVATIVE_POSITIVE`) | **0/27 REOPENINGS ON REAL FOOTAGE** | `0/27` track sensors collected; fail-closed conservative policy keeps gate safely closed until physical occupancy clearance (`0%` premature openings). |
| Millisecond-aligned cross-camera fusion on 16 non-`sync11` events | **BLOCKED BY R04 CLOCK UNCERTAINTY** | Only 11 events have `CALIBRATION_SUPPORTED` clock offsets (`phase12_r04_scope_decision.json`); the remaining 16 have `±1.0–2.0 s` QuickTime rounding or missing audio peaks. |

