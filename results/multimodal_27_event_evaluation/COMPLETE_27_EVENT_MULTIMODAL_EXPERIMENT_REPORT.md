# Complete 27-Event Multimodal Experimental Evaluation, Causal Gate Control & Failure Forensics

**Qualification:** `Exploratory evaluation against researcher-adopted AI-assisted reference annotations.`
**Vision Data Provenance:** `Mission 39/43 Frozen YOLOv8n Actual Inference Caches (pre-db40305 unrotated container decoding: 44/54 streams -90 deg rotated, 10/54 streams 0 deg upright; 6,613 front frames / 329 objects, 6,479 back frames / 1,020 objects)`
**Audio Data Provenance:** `Mission 39/43 Corrected Natural Log-Mel CompactTrainHornCNN Actual Inference Caches (2,600 windows of 1.0 s / 0.5 s hop; orientation-invariant)`
**Reference Labels:** `Researcher-adopted AI-assisted reference proposals (docs/generated/professor_evidence/mission43/RESEARCHER_ANNOTATION_ADOPTION.json; 0/27 independent Stage-2.1 human reviews)`
**Authorization & Re-Inference Readiness (Task 1):** `data/governance/AUTH-MEDIA-ACCESS.json` is `ABSENT` (`AUTH_MEDIA_ACCESS_NOT_GRANTED`). Pre-hashed owner template staged at `docs/generated/human_approval_templates/AUTH_MEDIA_ACCESS_MISSION9_READY.json`.

## 1. Original-Video Orientation Audit (`Display Matrix` `-90°` vs `0°` Upright)
- Across the `54` `.mov` recordings (`27` front + `27` back), **`44/54` (`81.5%`) carry `Display Matrix rotation = -90°`** (`24` front, `20` back) and **`10/54` (`18.5%`) are native `0°` upright** (`3` front: `train_023, no_train_001, no_train_003`; `7` back: `train_021..023, no_train_001..003, engine_001`).
- **`CompactTrainHornCNN` Audio (`27/27` events, `2,600` windows):** Already re-run cleanly with corrected natural log-Mel features (`orientation-invariant`).
- **`YOLOv8n` Upright Evidence Already Present (`4/4 = 100%` on `0°` train streams):** Every `0°` upright train video achieved dense continuous tracking (`train_023` front: `196` frames/`136` consec; `train_021` back: `230` frames/`69` consec; `train_022` back: `228` frames/`219` consec; `train_023` back: `208` frames/`111` consec). By contrast, **16/16 streams across all 8 failed events (`008, 009, 010, 011, 014, 015, 019, 020`) are `-90°` unrotated**, directly causing optical starvation (`0–5` scattered frames).

## 2. Vision vs Audio vs Rule-Based Late Fusion Comparison (All 27 Events)
All fusion variants evaluated here (`F1`–`F7`) are **rule-based late fusion** (`0` learned multimodal fusion weights). We explicitly label `FROZEN_PROTOCOL` baselines vs `EXPLORATORY_COHORT_SELECTED` thresholds.

| Configuration | Fusion Type / Thresholds | Train TP/23 | FN/23 | NT FP/3 | Eng001 Det | Prec (V1) | Rec (V1 [95% CI]) | Spec (V1) | F1 (V1) | Rail24 Rec/F1 (V3) | McNemar p vs V2 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Vision: Front-Only Stateless (k>=1) | Single-Modality / `FROZEN_PROTOCOL` | 16 | 7 | 2 | no | 88.9% | 69.6% [49.1–84.4%] | 33.3% | 78.0% | 16/24 (76.2%) | 0.2891 |
| Vision: Front-Only L1 Causal (confirm>=2) [B0_front] | Single-Modality / `FROZEN_PROTOCOL` | 10 | 13 | 0 | no | 100.0% | 43.5% [25.6–63.2%] | 100.0% | 60.6% | 10/24 (58.8%) | 1.0000 |
| Vision: Back-Only Stateless (k>=1) | Single-Modality / `FROZEN_PROTOCOL` | 17 | 6 | 2 | YES | 89.5% | 73.9% [53.5–87.5%] | 33.3% | 81.0% | 18/24 (81.8%) | 0.1797 |
| Vision: Back-Only Confirm2 (All Classes) | Single-Modality / `FROZEN_PROTOCOL` | 9 | 14 | 2 | YES | 81.8% | 39.1% [22.2–59.2%] | 33.3% | 52.9% | 10/24 (55.6%) | 0.4531 |
| Vision: Back-Only Confirm2 (Side/Rear Filtered) | Single-Modality / `EXPLORATORY_COHORT_SELECTED` | 9 | 14 | 0 | no | 100.0% | 39.1% [22.2–59.2%] | 100.0% | 56.2% | 9/24 (54.5%) | 1.0000 |
| Vision: Side-Class Proxy (Front+Back side>=1) | Single-Modality / `FROZEN_PROTOCOL` | 14 | 9 | 0 | no | 100.0% | 60.9% [40.8–77.8%] | 100.0% | 75.7% | 14/24 (73.7%) | 0.1250 |
| Vision: Dual-Vision Confirm2 (All Classes) | Rule-Based Late Fusion / `FROZEN_PROTOCOL` | 12 | 11 | 2 | YES | 85.7% | 52.2% [33.0–70.8%] | 33.3% | 64.9% | 13/24 (66.7%) | 1.0000 |
| Vision: Dual-Vision Causal (Front L1 OR Back Side/Rear L1) | Rule-Based Late Fusion / `EXPLORATORY_COHORT_SELECTED` | 12 | 11 | 0 | no | 100.0% | 52.2% [33.0–70.8%] | 100.0% | 68.6% | 12/24 (66.7%) | 0.5000 |
| Audio-Only: Frozen tau=0.37, k=1 [B1_audio] | Single-Modality / `FROZEN_PROTOCOL` | 22 | 1 | 3 | no | 88.0% | 95.7% [79.0–99.2%] | 0.0% | 91.7% | 22/24 (89.8%) | 0.0490 |
| Audio-Only: tau=0.37, k=2 consecutive | Single-Modality / `EXPLORATORY_COHORT_SELECTED` | 17 | 6 | 3 | no | 85.0% | 73.9% [53.5–87.5%] | 0.0% | 79.1% | 17/24 (77.3%) | 0.4239 |
| Audio-Only: Hysteresis tau=0.75, k=2 consecutive | Single-Modality / `EXPLORATORY_COHORT_SELECTED` | 9 | 14 | 0 | no | 100.0% | 39.1% [22.2–59.2%] | 100.0% | 56.2% | 9/24 (54.5%) | 1.0000 |
| Fusion F1: Stateless Union (Front>=1 OR Audio>=0.37) | Rule-Based Late Fusion / `FROZEN_PROTOCOL` | 23 | 0 | 3 | no | 88.5% | 100.0% [85.7–100.0%] | 0.0% | 93.9% | 23/24 (92.0%) | 0.0213 |
| Fusion F2: V3 Default B2/B4 (Front L1 + Advisory Audio) | Rule-Based Late Fusion / `FROZEN_PROTOCOL` | 10 | 13 | 0 | no | 100.0% | 43.5% [25.6–63.2%] | 100.0% | 60.6% | 10/24 (58.8%) | 1.0000 |
| Fusion F3: Front L1 OR (Weak Front>=1 & Audio 0.75 k=2) | Rule-Based Late Fusion / `EXPLORATORY_COHORT_SELECTED` | 11 | 12 | 0 | no | 100.0% | 47.8% [29.2–67.0%] | 100.0% | 64.7% | 11/24 (62.9%) | 1.0000 |
| Fusion F4: Front L1 OR Audio Hysteresis (0.75, k=2) | Rule-Based Late Fusion / `EXPLORATORY_COHORT_SELECTED` | 14 | 9 | 0 | no | 100.0% | 60.9% [40.8–77.8%] | 100.0% | 75.7% | 14/24 (73.7%) | 0.1250 |
| Fusion F5: Dual-Vision Side/Rear + Advisory Audio [B7] | Rule-Based Late Fusion / `EXPLORATORY_COHORT_SELECTED` | 12 | 11 | 0 | no | 100.0% | 52.2% [33.0–70.8%] | 100.0% | 68.6% | 12/24 (66.7%) | 0.5000 |
| Fusion F6: Full Multimodal (Front L1 OR Back SR L1 OR Audio 0.75 k=2) | Rule-Based Late Fusion / `EXPLORATORY_COHORT_SELECTED` | 15 | 8 | 0 | no | 100.0% | 65.2% [44.9–81.2%] | 100.0% | 79.0% | 15/24 (76.9%) | 0.0625 |
| Fusion F7: Exploratory 2-of-3 Optical + Back SR + Audio 0.75 k=2 | Rule-Based Late Fusion / `EXPLORATORY_COHORT_SELECTED` | 17 | 6 | 0 | no | 100.0% | 73.9% [53.5–87.5%] | 100.0% | 85.0% | 17/24 (82.9%) | 0.0156 |

## 3. What Does `CompactTrainHornCNN` Actually Detect? (Horn vs Train Presence)
`CompactTrainHornCNN` was trained to classify **train horns vs ambient/traffic sounds**, NOT general train wheel/engine rumble:
- Across all `27` events evaluated against **adopted `horn_status`** (`13` `horn_present` vs `14` `horn_absent`), frozen `(tau=0.37, k=1)` gets `TP=12/13 (92.3%)` with **`FP=13/14` (`7.1%` specificity)**, while exploratory `(tau=0.75, k=2)` gets **`TP=8/13 (61.5%)` with `FP=1/14` (`92.9%` specificity, `F1=72.7%`)** (`23`-fold LOEO OOF on `train23`: `61.5%` recall, `60.0%` specificity, `64.0%` F1).
- Consequently, audio hysteresis `(0.75, k=2)` recovers **`+3` silent-optical honking trains (`005, 012, 017`)** (`0/3` `no_train` FP), **cannot detect non-honking trains (`001, 008, 009, 010, 011, 014, 019`) or solitary `engine_001`** (`max=0.1428`), and emits `0.37–0.826` false positives on road horns in `3/3` `no_train` clips under `k=1`.

## 4. Causal Gate-Control State Machine Integration (`V3 FSM + PhysicalGateModel` @ `dt=0.20s`)
Closing the crossing physically requires **`confirm=2` (`0.2 s`) + `2.0 s` warning dwell + `3.0 s` boom closure = `>=5.2 s`**, whereas `21/22` `T2`-annotated recordings begin only **`2.8–5.0 s` before `T2`** (only `event_001` has `T2=6.5 s`).

| Causal FSM Architecture (Clock Basis) | Triggered / 23 | Full Boom Closed / 23 | Warn@EOF Only | Missed FN/23 | NT FP/3 | Eng001 | Warn <= T2 | CloseCmd <= T2 | HalfClosed <= T2 | FullClosed <= T2 | Reopen Cycles |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FSM V2 Front L1 (`B0`, Frozen, Front Clock) | 10/23 | 9/23 | 1 | 13 | 0/3 | no | 4 | 3 | 1 | 0 | 0 |
| FSM F2 Default V3 (`B4`, Frozen, Front Clock) | 10/23 | 9/23 | 1 | 13 | 0/3 | no | 4 | 3 | 1 | 0 | 0 |
| FSM F3 Weak-Front & Audio 0.75k2 (Expl., Front Clock) | 11/23 | 10/23 | 1 | 12 | 0/3 | no | 5 | 3 | 1 | 0 | 0 |
| FSM F4 Front L1 OR Audio 0.75k2 (Expl., Front Clock) | 14/23 | 13/23 | 1 | 9 | 0/3 | no | 6 | 3 | 1 | 0 | 0 |
| FSM F5 Dual-Vision Side/Rear (Strict Calibrated `sync11` n=11) | 5/11 | 5/11 | 0 | 6 | N/A (0 NT) | N/A | 1 | 1 | 1 | 0 | 0 |
| FSM F6 Full Multimodal (Strict Calibrated `sync11` n=11) | 8/11 | 8/11 | 0 | 3 | N/A (0 NT) | N/A | 2 | 1 | 1 | 0 | 0 |
| FSM F6 Full Multimodal (Calibrated `sync11` + Approx Local `16` = 27) | 15/23 | 15/23 | 0 | 8 | 0/3 | no | 6 | 3 | 1 | 0 | 0 |
| FSM F7 Exploratory `2-of-3` Dropout Multimodal (All 27 Bounded) | 17/23 | 17/23 | 0 | 6 | 0/3 | no | 8 | 4 | 1 | 0 | 0 |

## 5. Event-by-Event Results & Causal FSM Timing Summary (All 27 Events)

| Event ID | Cohort (Sess) | Rot F/B | GT T2 / Horn | Fr DF (mc) [F/S/R] MaxC | Bk DF (sr_c) [F/S/R] MaxC | Aud >=.37 / >=.75 (r75) MaxA | V2 / F4 / F6 / F7 | F6 FSM Trig (Rule) | F6 Warn/Cmd/Full (Marg vs T2) | Timing Class (`F6`) |
|---|---|---|---|---:|---:|---:|---|---|---|---|
| `train_events/event_001` | train (1) | -90/-90 | 6.50s / Y | 6(3) [1/5/0] 0.64 | 7(3) [0/7/0] 0.69 | 0/0(0) 0.247 | P/P/P/P | 14.20s (L4_BACK_SI) | 14.20/16.40/19.20 (-12.70s) | LATE_POST_T2_CLOSURE |
| `train_events/event_002` | train (1) | -90/-90 | 3.60s / Y | 1(1) [1/0/0] 0.72 | 42(6) [0/43/0] 0.80 | 3/2(2) 0.983 | -/P/P/P | 3.60s (L3_OPTICAL) | 3.60/5.60/8.40 (-4.80s) | PRE_T2_WARNING_LATE_CMD |
| `train_events/event_003` | train (1) | -90/-90 | 2.80s / N | 58(8) [7/52/0] 0.86 | 1(1) [0/0/1] 0.60 | 8/2(1) 0.914 | P/P/P/P | 0.20s (L1_FRONT_A) | 0.20/2.40/5.20 (-2.40s) | PRE_T2_CLOSE_CMD_LATE_BOOM |
| `train_events/event_004` | train (1) | -90/-90 | 2.90s / Y | 4(2) [3/0/1] 0.78 | 8(3) [0/4/4] 0.76 | 30/5(4) 0.999 | P/P/P/P | 1.60s (L3_OPTICAL) | 1.60/3.60/6.40 (-3.50s) | PRE_T2_WARNING_LATE_CMD |
| `train_events/event_005` | train (1) | -90/-90 | —s / Y | 0(0) [0/0/0] — | 0(0) [0/0/0] — | 105/31(7) 0.972 | -/P/P/P | 2.60s (L3_OPTICAL) | 2.60/4.60/7.40 (—) | CLOSED_NO_T2_REF |
| `train_events/event_006` | train (1) | -90/-90 | 3.30s / Y | 8(3) [0/0/8] 0.75 | 3(3) [0/3/0] 0.85 | 51/6(3) 0.816 | P/P/P/P | 8.60s (L3_OPTICAL) | 8.60/10.80/13.60 (-10.30s) | LATE_POST_T2_CLOSURE |
| `train_events/event_007` | train (1) | -90/-90 | 3.40s / N | 4(2) [0/5/0] 0.81 | 7(4) [1/6/0] 0.82 | 16/5(4) 0.990 | P/P/P/P | 16.40s (L1_FRONT_A) | 16.40/18.60/21.40 (-18.00s) | LATE_POST_T2_CLOSURE |
| `train_events/event_008` | train (1) | -90/-90 | 3.20s / N | 0(0) [0/0/0] — | 2(1) [0/0/2] 0.50 | 13/1(1) 0.811 | -/-/-/P | NONE | —/—/— (—) | MISSED_TRIGGER_EOF_FAIL_SAFE_CLAMP |
| `train_events/event_009` | train (1) | -90/-90 | 5.00s / N | 0(0) [0/0/0] — | 0(0) [0/0/0] — | 7/0(0) 0.582 | -/-/-/- | NONE | —/—/— (—) | MISSED_TRIGGER_EOF_FAIL_SAFE_CLAMP |
| `train_events/event_010` | train (1) | -90/-90 | 3.50s / N | 1(1) [1/0/0] 0.74 | 0(0) [0/0/0] — | 2/0(0) 0.447 | -/-/-/- | NONE | —/—/— (—) | MISSED_CLOSURE_FN |
| `train_events/event_011` | train (1) | -90/-90 | 3.60s / N | 2(1) [0/0/3] 0.60 | 0(0) [0/0/0] — | 3/0(0) 0.450 | -/-/-/- | NONE | —/—/— (—) | MISSED_TRIGGER_EOF_FAIL_SAFE_CLAMP |
| `train_events/event_012` | train (1) | -90/-90 | 3.90s / Y | 0(0) [0/0/0] — | 2(0) [2/0/0] 0.40 | 34/8(3) 0.978 | -/P/P/P | 25.00s (L3_OPTICAL) | 25.00/27.20/30.00 (-26.10s) | LATE_POST_T2_CLOSURE |
| `train_events/event_013` | train (1) | -90/-90 | 4.00s / Y | 6(3) [5/0/1] 0.84 | 3(1) [0/3/0] 0.47 | 32/7(2) 0.914 | P/P/P/P | 0.60s (L1_FRONT_A) | 0.60/2.60/5.40 (-1.40s) | PRE_T2_HALF_CLOSED_LATE_FULL |
| `train_events/event_014` | train (1) | -90/-90 | 3.40s / N | 4(1) [3/1/0] 0.54 | 2(1) [0/2/0] 0.59 | 5/0(0) 0.517 | -/-/-/P | NONE | —/—/— (—) | MISSED_TRIGGER_EOF_FAIL_SAFE_CLAMP |
| `train_events/event_015` | train (1) | -90/-90 | 5.00s / Y | 0(0) [0/0/0] — | 0(0) [0/0/0] — | 5/1(1) 0.840 | -/-/-/- | NONE | —/—/— (—) | MISSED_CLOSURE_FN |
| `train_events/event_016` | train (1) | -90/-90 | 5.00s / N | 5(1) [5/1/0] 0.53 | 8(5) [0/8/0] 0.89 | 5/0(0) 0.709 | -/-/P/P | 13.40s (L4_BACK_SI) | 13.40/15.60/18.40 (-13.40s) | LATE_POST_T2_CLOSURE |
| `train_events/event_017` | train (1) | -90/-90 | 3.60s / Y | 0(0) [0/0/0] — | 4(1) [0/4/0] 0.49 | 21/8(3) 0.986 | -/P/P/P | 22.00s (L3_OPTICAL) | 22.00/24.20/27.00 (-23.40s) | LATE_POST_T2_CLOSURE |
| `train_events/event_018` | train (1) | -90/-90 | 3.50s / Y | 4(3) [4/0/0] 0.67 | 1(1) [0/1/0] 0.40 | 34/10(3) 0.998 | P/P/P/P | 6.60s (L3_OPTICAL) | 6.60/8.80/11.60 (-8.10s) | LATE_POST_T2_CLOSURE |
| `train_events/event_019` | train (1) | -90/-90 | 3.80s / N | 1(1) [0/0/1] 0.36 | 0(0) [0/0/0] — | 6/0(0) 0.550 | -/-/-/- | NONE | —/—/— (—) | MISSED_CLOSURE_FN |
| `train_events/event_020` | train (1) | -90/-90 | 3.10s / Y | 0(0) [0/0/0] — | 3(0) [3/0/0] 0.60 | 1/0(0) 0.378 | -/-/-/- | NONE | —/—/— (—) | MISSED_CLOSURE_FN |
| `train_events/event_021` | train (2) | -90/0 | 4.10s / Y | 6(3) [0/6/0] 0.72 | 230(69) [1/225/4] 0.94 | 4/0(0) 0.578 | P/P/P/P | 8.00s (L4_BACK_SI) | 8.00/10.20/13.00 (-8.90s) | LATE_POST_T2_CLOSURE |
| `train_events/event_022` | train (2) | -90/0 | 3.30s / Y | 14(4) [0/14/0] 0.77 | 228(189) [222/205/5] 0.95 | 3/0(0) 0.603 | P/P/P/P | 2.80s (L1_FRONT_A) | 2.80/4.80/7.60 (-4.30s) | PRE_T2_WARNING_LATE_CMD |
| `train_events/event_023` | train (2) | 0/0 | 3.60s / N | 196(136) [15/182/2] 0.94 | 208(111) [0/196/14] 0.94 | 18/1(1) 0.786 | P/P/P/P | 0.20s (L1_FRONT_A) | 0.20/2.40/5.20 (-1.60s) | PRE_T2_CLOSE_CMD_LATE_BOOM |
| `no_train_events/event_001` | no (2) | 0/0 | —s / N | 1(1) [1/0/0] 0.38 | 24(0) [25/0/0] 0.68 | 11/1(1) 0.800 | -/-/-/- | NONE | —/—/— (—) | CORRECT_OPEN_TN |
| `no_train_events/event_002` | no (2) | -90/0 | —s / N | 0(0) [0/0/0] — | 0(0) [0/0/0] — | 12/2(1) 0.826 | -/-/-/- | NONE | —/—/— (—) | CORRECT_OPEN_TN |
| `no_train_events/event_003` | no (2) | 0/0 | —s / N | 1(1) [1/0/0] 0.51 | 15(0) [15/0/0] 0.69 | 16/1(1) 0.800 | -/-/-/- | NONE | —/—/— (—) | CORRECT_OPEN_TN |
| `engine_events/event_001` | engine (2) | -90/0 | 0.00s / N | 0(0) [0/0/0] — | 13(0) [14/0/0] 0.90 | 0/0(0) 0.143 | -/-/-/- | NONE | —/—/— (—) | CORRECT_OPEN_TN |

## 6. Forensic Diagnosis of All 8 `F6`-Missed Train Events (`failed_events_forensic_diagnosis.json`)

| Event ID | Rot F/B | Front Raw Dets | Back Raw Dets | Audio Top Score / Runs | Adopted Horn | Forensic Root Cause & Legitimate Recoverability |
|---|---|---|---|---|---|---|
| `train_events/event_008` | -90/-90 | 0 frames | 21.6017s:[{'label': 'rear', 'confidence': 0.4981}], 22.2017s:[{'label': 'rear', 'confidence': 0.366}] | max=0.8109@27.0s (p37=13, r75=1) | absent_observed | RECOVERABLE_BY_2OF3_DROPOUT_TOLERANCE_AND_LIKELY_UPRIGHT_ROTATION: Both streams were decoded sideways (-90 deg); existing detections already pair within <=0.60 s. |
| `train_events/event_009` | -90/-90 | 0 frames | 0 frames | max=0.582@29.0s (p37=7, r75=0) | absent_observed | ZERO_OPTICAL_AT_MINUS90_AND_ABSENT_HORN: Both cameras were -90 deg unrotated (0 optical frames) and no horn present; only upright video re-inference can recover without acoustic overfitting. |
| `train_events/event_010` | -90/-90 | 0.2s:[{'label': 'front', 'confidence': 0.7361}] | 0 frames | max=0.4473@15.0s (p37=2, r75=0) | absent_observed | SPARSE_UNROTATED_DETECTIONS_BELOW_RUN2: Both cameras were -90 deg unrotated, yielding only 1-4 scattered frames (gaps >=2.4 s) and quiet/absent horn; requires db40305 upright video re-inference. |
| `train_events/event_011` | -90/-90 | 28.22s:[{'label': 'rear', 'confidence': 0.4707}], 35.025s:[{'label': 'rear', 'confidence': 0.5971}, {'label': 'rear', 'confidence': 0.4906}] | 0 frames | max=0.4502@34.0s (p37=3, r75=0) | absent_observed | SPARSE_UNROTATED_DETECTIONS_BELOW_RUN2: Both cameras were -90 deg unrotated, yielding only 1-4 scattered frames (gaps >=2.4 s) and quiet/absent horn; requires db40305 upright video re-inference. |
| `train_events/event_014` | -90/-90 | 1.8017s:[{'label': 'front', 'confidence': 0.4263}], 2.2017s:[{'label': 'front', 'confidence': 0.535}], 3.4017s:[{'label': 'front', 'confidence': 0.5062}], 12.2083s:[{'label': 'side', 'confidence': 0.5242}] | 19.0017s:[{'label': 'side', 'confidence': 0.4115}], 19.4017s:[{'label': 'side', 'confidence': 0.5939}] | max=0.5166@24.0s (p37=5, r75=0) | absent_observed | RECOVERABLE_BY_2OF3_DROPOUT_TOLERANCE_AND_LIKELY_UPRIGHT_ROTATION: Both streams were decoded sideways (-90 deg); existing detections already pair within <=0.60 s. |
| `train_events/event_015` | -90/-90 | 0 frames | 0 frames | max=0.8402@23.5s (p37=5, r75=1) | present | SINGLE_WINDOW_AUDIO_NEAR_MISS_AND_UNROTATED_OPTICAL: Strong peak horn window (0.8402 followed by 0.7440; missed 0.75 k=2 by 0.0060), 0 optical frames at -90 deg; requires upright re-inference rather than overfitting threshold. |
| `train_events/event_019` | -90/-90 | 9.6067s:[{'label': 'rear', 'confidence': 0.3638}] | 0 frames | max=0.55@18.5s (p37=6, r75=0) | absent_observed | SPARSE_UNROTATED_DETECTIONS_BELOW_RUN2: Both cameras were -90 deg unrotated, yielding only 1-4 scattered frames (gaps >=2.4 s) and quiet/absent horn; requires db40305 upright video re-inference. |
| `train_events/event_020` | -90/-90 | 0 frames | 2.8s:[{'label': 'front', 'confidence': 0.5013}], 5.2s:[{'label': 'front', 'confidence': 0.4105}], 7.6s:[{'label': 'front', 'confidence': 0.6048}] | max=0.378@20.0s (p37=1, r75=0) | present | SPARSE_UNROTATED_DETECTIONS_BELOW_RUN2: Both cameras were -90 deg unrotated, yielding only 1-4 scattered frames (gaps >=2.4 s) and quiet/absent horn; requires db40305 upright video re-inference. |

## 7. Explicit Boundary: What Existing Recordings & Labels Cannot Prove

| Claim / Requirement | Status on Current 27 Events | Empirical Blocker |
|---|---|---|
| Pre-`T2` full `0°` barrier closure (`>=5.2 s` before arrival) | **0/23 EVENTS** | `21/22` `T2`-annotated recordings begin `2.8–5.0 s` before `T2` (`< 5.2 s` confirm+warn+stroke budget). |
| Complete gate close -> autonomous reopen cycle on real footage | **0/27 CYCLES** | `0/27` track occupancy sensors + `20/22` `T4`-annotated clips end `<3.5 s` after `T4` (`median 1.402 s`). |
| True upright `-90° -> 0°` YOLO recall across all 27 events | **PENDING OWNER `AUTH-MEDIA-ACCESS.json`** | `44/54` streams are `-90°` rotated in caches; `data/governance/AUTH-MEDIA-ACCESS.json` absent on disk. |
| Frame-level YOLO mAP/IoU or window-level audio offset error | **CANNOT BE COMPUTED** | Proposals supply event-level timestamps only (`0` bbox GT, `0` horn offset GT, `0` Stage-2.1 human reviews). |
| Generalization across crossings/sessions/unseen traffic | **BLOCKED (`leakage_safe = false`)** | Single crossing (`crossing_A`), 2 confounded sessions, `tau=0.75, k=2` & `2-of-3` gap selected exploratory on cohort. |

