# Mission 10 Upright (`db40305`) 27-Event Multimodal Evaluation & Baseline Comparison

**Qualification:** `Exploratory evaluation against researcher-adopted AI-assisted reference annotations.`
**Orientation Policy Applied:** `orthogonal_display_matrix_rotation_v1` (`54/54` streams verified)
**Audio Log-Mel Fresh Extraction Max Score Delta vs Baseline Cache:** `0.0` across `27` events

## 1. Pre-`db40305` Baseline vs Upright (`db40305`) Ablation Comparison (`23` Train vs `3` No-Train; `engine_001` Separate)

| Configuration | Base TP/23 | Upright TP/23 | Delta TP | Base NT FP/3 | Upright NT FP/3 | Base F1 | Upright F1 | Eng001 Base->Up | McNemar p (Base vs Up) | Recovered Trains |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| Vision: Front-Only Stateless (k>=1) | 16 | 23 | +7 | 2 | 3 | 78.0% | 93.9% | N->Y | 0.0703 | event_005, event_008, event_009, event_012, event_015, event_017, event_020 |
| Vision: Front-Only L1 Causal (confirm>=2) [B0_front] | 10 | 23 | +13 | 0 | 1 | 60.6% | 97.9% | N->Y | 0.0018 | event_002, event_005, event_008, event_009, event_010, event_011, event_012, event_014, event_015, event_016, event_017, event_019, event_020 |
| Vision: Back-Only Stateless (k>=1) | 17 | 23 | +6 | 2 | 2 | 81.0% | 95.8% | Y->Y | 0.0312 | event_005, event_009, event_010, event_011, event_015, event_019 |
| Vision: Back-Only Confirm2 (All Classes) | 9 | 23 | +14 | 2 | 2 | 52.9% | 95.8% | Y->Y | 0.0001 | event_003, event_005, event_008, event_009, event_010, event_011, event_012, event_013, event_014, event_015, event_017, event_018, event_019, event_020 |
| Vision: Back-Only Confirm2 (Side/Rear Filtered) | 9 | 23 | +14 | 0 | 0 | 56.2% | 100.0% | N->N | 0.0001 | event_003, event_005, event_008, event_009, event_010, event_011, event_012, event_013, event_014, event_015, event_017, event_018, event_019, event_020 |
| Vision: Side-Class Proxy (Front+Back side>=1) | 14 | 23 | +9 | 0 | 1 | 75.7% | 97.9% | N->Y | 0.0215 | event_005, event_008, event_009, event_010, event_011, event_012, event_015, event_019, event_020 |
| Vision: Dual-Vision Confirm2 (All Classes) | 12 | 23 | +11 | 2 | 3 | 64.9% | 93.9% | Y->Y | 0.0063 | event_005, event_008, event_009, event_010, event_011, event_012, event_014, event_015, event_017, event_019, event_020 |
| Vision: Dual-Vision Causal (Front L1 OR Back Side/Rear L1) | 12 | 23 | +11 | 0 | 1 | 68.6% | 97.9% | N->Y | 0.0063 | event_005, event_008, event_009, event_010, event_011, event_012, event_014, event_015, event_017, event_019, event_020 |
| Audio-Only: Frozen tau=0.37, k=1 [B1_audio] | 22 | 22 | +0 | 3 | 3 | 91.7% | 91.7% | N->N | 1.0000 | — |
| Audio-Only: tau=0.37, k=2 consecutive | 17 | 17 | +0 | 3 | 3 | 79.1% | 79.1% | N->N | 1.0000 | — |
| Audio-Only: Hysteresis tau=0.75, k=2 consecutive | 9 | 9 | +0 | 0 | 0 | 56.2% | 56.2% | N->N | 1.0000 | — |
| Fusion F1: Stateless Union (Front>=1 OR Audio>=0.37) | 23 | 23 | +0 | 3 | 3 | 93.9% | 93.9% | N->Y | 1.0000 | — |
| Fusion F2: V3 Default B2/B4 (Front L1 + Advisory Audio) | 10 | 23 | +13 | 0 | 1 | 60.6% | 97.9% | N->Y | 0.0018 | event_002, event_005, event_008, event_009, event_010, event_011, event_012, event_014, event_015, event_016, event_017, event_019, event_020 |
| Fusion F3: Front L1 OR (Weak Front>=1 & Audio 0.75 k=2) | 11 | 23 | +12 | 0 | 1 | 64.7% | 97.9% | N->Y | 0.0034 | event_005, event_008, event_009, event_010, event_011, event_012, event_014, event_015, event_016, event_017, event_019, event_020 |
| Fusion F4: Front L1 OR Audio Hysteresis (0.75, k=2) | 14 | 23 | +9 | 0 | 1 | 75.7% | 97.9% | N->Y | 0.0215 | event_008, event_009, event_010, event_011, event_014, event_015, event_016, event_019, event_020 |
| Fusion F5: Dual-Vision Side/Rear + Advisory Audio [B7] | 12 | 23 | +11 | 0 | 1 | 68.6% | 97.9% | N->Y | 0.0063 | event_005, event_008, event_009, event_010, event_011, event_012, event_014, event_015, event_017, event_019, event_020 |
| Fusion F6: Full Multimodal (Front L1 OR Back SR L1 OR Audio 0.75 k=2) | 15 | 23 | +8 | 0 | 1 | 79.0% | 97.9% | N->Y | 0.0391 | event_008, event_009, event_010, event_011, event_014, event_015, event_019, event_020 |
| Fusion F7: Exploratory 2-of-3 Optical + Back SR + Audio 0.75 k=2 | 17 | 23 | +6 | 0 | 1 | 85.0% | 97.9% | N->Y | 0.1250 | event_009, event_010, event_011, event_015, event_019, event_020 |

## 2. Recovery of the 8 Previously Failed (`pre-db40305` F6-Missed) Train Events

| Event ID | Rot F/B | Front DF Base->Up (mc) | Back DF Base->Up (sr_c) | Upright V2 | Upright F6 | Upright F7 | Diagnosis |
|---|---|---:|---:|---|---|---|---|
| `train_events/event_008` | -90/-90 | 0->295 (295) | 2->303 (292) | YES | YES | YES | Detected cleanly by Front L1 (295 consec frames) |
| `train_events/event_009` | -90/-90 | 0->212 (211) | 0->149 (139) | YES | YES | YES | Detected cleanly by Front L1 (211 consec frames) |
| `train_events/event_010` | -90/-90 | 1->100 (69) | 0->107 (99) | YES | YES | YES | Detected cleanly by Front L1 (69 consec frames) |
| `train_events/event_011` | -90/-90 | 2->181 (176) | 0->130 (38) | YES | YES | YES | Detected cleanly by Front L1 (176 consec frames) |
| `train_events/event_014` | -90/-90 | 4->193 (47) | 2->252 (68) | YES | YES | YES | Detected cleanly by Front L1 (47 consec frames) |
| `train_events/event_015` | -90/-90 | 0->109 (59) | 0->67 (61) | YES | YES | YES | Detected cleanly by Front L1 (59 consec frames) |
| `train_events/event_019` | -90/-90 | 1->286 (213) | 0->246 (234) | YES | YES | YES | Detected cleanly by Front L1 (213 consec frames) |
| `train_events/event_020` | -90/-90 | 0->79 (44) | 3->142 (137) | YES | YES | YES | Detected cleanly by Front L1 (44 consec frames) |

## 3. Causal FSM Gate Timing Comparison (Baseline vs Upright)

| FSM Architecture | Trig B->U | Full Closed B->U | Warn<=T2 B->U | Cmd<=T2 B->U | Full<=T2 B->U | NT FP B->U | Eng001 B->U | Reopen B->U |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `FSM_V2_Front_L1` | 10->23 | 9->23 | 4->22 | 3->22 | 0->1 | 0->1 | N->Y | 0->0 |
| `FSM_F2_V3_Default_B4` | 10->23 | 9->23 | 4->22 | 3->22 | 0->1 | 0->1 | N->Y | 0->0 |
| `FSM_F3_WeakFront_Plus_Audio` | 11->23 | 10->23 | 5->22 | 3->22 | 0->1 | 0->1 | N->Y | 0->0 |
| `FSM_F4_Front_Or_Audio075k2` | 14->23 | 13->23 | 6->22 | 3->22 | 0->1 | 0->1 | N->Y | 0->0 |
| `FSM_F5_Dual_Vision_Sync11` | 5->11 | 5->11 | 1->10 | 1->10 | 0->1 | 0->0 | N->N | 0->0 |
| `FSM_F6_Full_MM_Sync11` | 8->11 | 8->11 | 2->10 | 1->10 | 0->1 | 0->0 | N->N | 0->0 |
| `FSM_F6_Full_MM_Bounded27` | 15->23 | 15->23 | 6->22 | 3->22 | 0->1 | 0->1 | N->Y | 0->0 |
| `FSM_F7_Exploratory_2of3_Bounded27` | 17->23 | 17->23 | 8->22 | 4->22 | 0->1 | 0->1 | N->Y | 0->0 |

## 4. Exploratory Multimodal Quorum (`F8` / `F9`): Eliminating Upright Single-Camera False Positives vs Lead-Time Trade-off

After orientation correction, single-camera `V2` (and OR-fusion `F6`) triggers `1/3` false positive on `no_train_events/event_002` (`front_max_consec=20`, `back_sr=0`, `A3=False`) and triggers `engine_events/event_001`.

| Exploratory Quorum Rule | Base TP/23 | Up TP/23 | Up NT FP/3 | Up Eng001 | Up Prec | Up Rec | Up F1 | Causal Confirm<=T2 | Causal Est Cmd<=T2 |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| `F8_Exploratory_Strong_2of3_Quorum` (>=2 of V2,V5,A3) | 10 | **23** | **0** | no | 100.0% | 100.0% | 100.0% | 11/22 (vs V2 22/22) | 2/22 |
| `F9_Exploratory_Dual_Camera_And` (V2 AND V5) | 7 | **23** | **0** | no | 100.0% | 100.0% | 100.0% | — | — |

## 5. Upright Back-Camera Departure Tracking (`M2` vs `gt_T4_s`)

- Across `22/22` `T4`-annotated trains, upright `back_last_det_s - T4` error has mean `1.4958s`, median `1.2033s`, range `[-1.1867s, 5.8033s]`, with `20/22` non-premature (`>=0s`).
