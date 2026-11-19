# Mission 13 — Complete Vision (`YOLOv8n`) & Audio (`CompactTrainHornCNN`) Overfitting, Underfitting, Leakage & Generalization Audit

**Project:** Train Gate Automation (`exp/four-layer-completion`)  
**Research Owner:** Mohammad Raihan Kabir (`raihankabirrahu@gmail.com`)  
**Audit Role:** Autonomous Principal Machine-Learning Research Engineer (Mission 13)  
**Preservation Guarantee:** Mission 11 frozen checkpoints (`39f402dfe460` `sha256: 3f5bb5b2...` and `RUN_20261008_AUDIO_V3_ESC50` `sha256: ea1bb81d...`), Mission 11–12 upright 27-event results (`results/upright_*`), gated raw media (`data/raw/`), and owner media authorization (`data/governance/AUTH-MEDIA-ACCESS.json`) remain **completely untouched**. Zero gated `data/raw/layer_b` media was uploaded to Kaggle; only the non-gated Roboflow `baler.v1i.yolov8` vision files were staged privately (`allfaz/railway-baler-v1-m13-yolo`) for GPU ablation training.

---

## Executive Diagnosis & Priority 10 Model Health Verdict

Neither production model is **underfitted** on its training corpus (`YOLOv8n` hits `mAP@0.50 = 0.9950`, `mAP@0.50:0.95 = 0.9055` on Train; `CompactTrainHornCNN` hits `F1 = 0.9848`, `PR-AUC = 0.9981` on clean Train). However, **both frozen models suffer from substantial dataset/selection leakage that masked real Train-to-Val/Test overfitting gaps and concealed severe domain-shift failure on field `crossing_A` footage**:

| Model / Experiment Scope | Underfitting? | Overfitting? | Split / Selection Leakage? | Independently Generalizing? | Primary Empirical Evidence | Impact on Fusion & Manuscript |
|---|---|---|---|---|---|---|
| **Frozen Vision: `YOLOv8n` (`39f402dfe460`, leaked `705d388743ea`)** | **No** (`Train mAP@50=0.9950, mAP@50-95=0.9055`) | **Moderate** (`-13.71 pp` Train->Val `mAP@50-95`; `val/cls` rises after Ep 72; `Ep93->97` degrades `-1.10 pp`) | **Severe** (`100%` eval frames `<=600s` & same calendar day as train; `2.37x–2.38x` aug copies in eval; `dHash<=5`: `42` val / `28` test) | **Unproven cross-crossing; Single-domain limited** (`-5.83 pp` to `-6.83 pp` `mAP@50-95` on unseen-to-`39f` subsets; `60/60` bridge FP on `no_train_002`) | [vision_baseline_39f402_audit.json](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_baseline_39f402_audit.json), [vision_39f402_on_clean_splits.json](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_39f402_on_clean_splits.json) | Checked-in `evaluator.py` `0.855` `mAP@50-95` must **not** be reported as generalization; explain `evaluator.py` bug (`0.8035` COCO) & single-crossing boundary. |
| **Clean Vision Ablations: `session_grouped_base` / `day_grouped_base` / `day_grouped_reg` (Kaggle T4, `100` ep)** | **No** (`Train mAP@50-95 = 0.8876–0.9008`) | **Moderate-to-High** (`-18.95 pp` Train->Test `mAP@50-95` on `session_grouped`; `-12.30 pp` on `day_grouped_base` with `+16.2%` `val/cls` rise Ep73->100) | **Controlled / Zero** (`0%` source/600s/day overlap in `day_grouped`, min gap `>= 44.8h`) | **Single-crossing Day-Disjoint: Yes (`mAP@50=0.9810, mAP@50-95=0.7731`); Cross-crossing / Hard-Neg: No (`60/60` `no_train_002` bridge FP persists)** | [vision_kaggle_clean_retrain_audit.json](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_kaggle_clean_retrain_audit.json), [vision_clean_vs_frozen_field_diagnostics.json](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_clean_vs_frozen_field_diagnostics.json) | Confirms regularization (`day_grouped_reg`) cuts held-out FPs `15->4` & raises small-box recall `0.873->0.916`, while proving `no_train_002` bridge FP stems from missing negative training images. |
| **Frozen Audio: `CompactTrainHornCNN` (`RUN_20261008_AUDIO_V3_ESC50`)** | **No** (`Train F1=0.9848, ROC-AUC=0.9986`) | **Moderate-to-Severe** (`Val F1=0.9942 -> Test F1=0.8690` [`-12.52 pp`]; `Rec Spec=0.6923`; `ECE 0.033->0.082`; BatchNorm spikes) | **Severe** (`5` pos stems = `59.3%` [`51/86`] of Val pos wins & `35.4%` [`23/65`] of Test pos wins leaked from Train; `50%` overlap cos-sim `0.7919`) | **No (Fails threshold transfer on `crossing_A`)** (`T*=0.37`: `13/13` FPs [`10/10` hornless trains + `3/3` no-train controls], `Spec=0.0`, `PR-AUC 0.9415 -> 0.7290`) | [audio_audit_summary.json](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/audio_audit_summary.json), [fig_m13_a2_roc_pr_confusion_calibration.png](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_a2_roc_pr_confusion_calibration.png) | Justifies strictly non-gating / hysteresis (`0.75, k=2`) role of audio inside `V3` fusion; explains why `T*=0.37` over-triggers in field acoustics. |
| **Clean Audio Ablations (`5`-seed stem-grouped + `5`-fold CV + `GroupNorm` + `SpecAug`)** | **Data-Limited, Not Capacity-Underfit** (Learning curve rises `0.7614 -> 0.8588` F1 across `20%–100%` data) | **Moderate + Seed/BN Variance** (`Train 0.9411 -> Test 0.8413 +- 0.0221`; `4.4 +- 2.3` `val_loss` spikes >`0.20`) | **Zero (`audio_v3_stem_grouped` + Fold-5-disjoint)** | **In-domain stem-disjoint: Moderate (`5`-fold CV `0.8638 +- 0.0565`, `PR-AUC 0.9261`); External `crossing_A`: Weak (`PR-AUC 0.6897 +- 0.0433`)** | [audio_audit_summary.json](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/audio_audit_summary.json), [fig_m13_a3_errors_cv_and_learning_curve.png](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_a3_errors_cv_and_learning_curve.png) | Proves `V3`'s `0.9942` Val F1 was a leakage artifact; true clean Test F1 is `~0.84–0.86` and needs real field negative acoustics. |

---

## 1. Checkpoint & Training Provenance Audit (Priority 1)

### 1.1 Vision Checkpoints (`YOLOv8n`)

- **Frozen Production Checkpoint:** [`experiments/vision/39f402dfe460/checkpoints/weights/best.pt`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/vision/39f402dfe460/checkpoints/weights/best.pt)  
  - `best.pt` SHA-256: `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` (selected at **Epoch 93** by Ultralytics fitness `0.1*mAP50 + 0.9*mAP50-95`).
  - `last.pt` SHA-256: `4be539fae0c798869e49b14193d80d0654d1ac24f6979c9bdd6162a612fc08b7` (**Epoch 97** — logged 97/100 configured epochs after `22,637.3 s = 6.29 h` on Apple M1 MPS; truncated 3 epochs early).
  - Exact Split Descriptors: `experiments/vision/39f402dfe460/descriptor/{train,val,test}.txt` are **100% set-identical** to `data/splits/705d388743ea` (`2,218 train / 467 val / 472 test` = `3,157` Roboflow `.jpg`s across `1,315` unique source stems).
  - Sibling Vision Runs Checked: `189a3afc9809`, `3052da735dc2`, and `8765e507b2e6` (dry-runs); `e1204e5c9790` (CPU 1-epoch test); `d9dfa4e34d02` (CPU aborted at Epoch 2).
- **Clean Mission 13 Kaggle T4 Retrains (`allfaz/m13-yolo-clean-generalization-retrain`, `Tesla T4`, `100` epochs, `batch=16`, `imgsz=640`, COCO-pretrained `yolov8n.pt`):**
  1. `session_grouped_base`: `1,377.1 s`, best fitness Ep `95`, `best.pt` SHA-256 `aabf506872fb2c477ab6c5682c2bb79d1fe2f8fc72ed22b4f8765bef5ee6b962`.
  2. `day_grouped_base`: `1,523.25 s`, best fitness Ep `77`, `best.pt` SHA-256 `1e3dd9eb1a405e141663ff517b06eceaa81f37d5ec65ae2889cb1bd9b57e275f`.
  3. `day_grouped_reg` (`cos_lr=True`, `dropout=0.10`, `weight_decay=0.002`, `mixup=0.10`, `copy_paste=0.10`, `hsv_v=0.50`, `close_mosaic=15`, `patience=25`): `1,553.21 s`, best fitness Ep `95`, `best.pt` SHA-256 `d18bcf9f4b62ba1d3cdae9e937fae980bac4db29ab45cb25aa0e7811e5b5ab23`.

### 1.2 Audio Checkpoints (`CompactTrainHornCNN`)

- **Frozen Production Checkpoint:** [`experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt)  
  - `best.pt` SHA-256: `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782`.
  - Exact verified trainable parameter count: **`25,697`** (`src/railway_detection/audio/model.py` docstring erroneously states `26,081`), operating on `64 x 32` natural log-Mel spectrograms (`log(mel + 1e-10)`), locked z-score normalization (`mean = -1.600999355316162`, `std = 5.1239728927612305`), selected at **Epoch 34** with validation-calibrated threshold **`T* = 0.3700`**.
  - Manifest: [`data/manifests/audio_training_dataset_v3.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/audio_training_dataset_v3.json) (`871 train / 203 val / 182 test` 1.0 s windows at 0.5 s hop across `120 / 26 / 26` clips).
- **Historical Audio Progression Audited:**
  - `V1` (`RUN_20260923_AUDIO_001`, `models/audio/best_checkpoint.pt`, `sha256: 59b0785f...`): incompatible `log10`/legacy feature scale (`mean=-4.66, std=23.72`), Test Window `F1 = 0.6971`.
  - `V2` (`RUN_20261008_AUDIO_V2`, `sha256: ddab244f...`): switched to natural log-Mel + identical-condition custom field negatives, yielding spurious **`1.0000` Val/Test F1** by learning background recording conditions instead of horn acoustics.
  - `V3` (`RUN_20261008_AUDIO_V3_ESC50`): replaced custom negatives with ESC-50 Fold 1–5 distractors (`11` categories), eliminating background overfitting *against clean ESC-50*, yet introducing stem-level positive leakage and domain mismatch relative to `crossing_A`.

---

## 2. Dataset Split & Multi-Tier Leakage Audit (Priority 2)

### 2.1 Vision Split Forensics (`baler.v1i.yolov8`)

Exact cross-split overlap and timestamp proximity (`within_600s_of_train`, `same_calendar_day_as_train`, Roboflow augmentation multiplier, and overlap with frozen `39f402` training images) are preserved in [`vision_split_leakage_comparison.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_split_leakage_comparison.json) and archived in [`clean_splits/`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/clean_splits/):

| Split Scheme | Partition | Images | Unique Sources | AugMult | `<= 600 s` of Train | `<= 3600 s` of Train | Same Calendar Day | Min Gap to Train | Seen in `39f402` Train | Boxes (`F / R / S`) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **`leaked_705d388743ea`** (`39f402`) | Train | 2,218 | 920 | 2.41x | - | - | - | - | 2,218 (100%) | `1230 / 512 / 555` |
| **`leaked_705d388743ea`** (`39f402`) | Val | 467 | 197 | **2.37x** | **426/426 (100%)** | **426/426 (100%)** | **426/426 (100%)** | **0.0 s** (`med 10s`) | 0 (100% same sessions) | `266 / 101 / 116` |
| **`leaked_705d388743ea`** (`39f402`) | Test | 472 | 198 | **2.38x** | **416/416 (100%)** | **416/416 (100%)** | **416/416 (100%)** | **0.0 s** (`med 11s`) | 0 (100% same sessions) | `265 / 88 / 134` |
| **`session_grouped`** (M11 canonical) | Train | 1,776 | 738 | 2.41x | - | - | - | - | 1,239 (69.8%) | `1016 / 388 / 445` |
| **`session_grouped`** (M11 canonical) | Val | 336 | 336 | **1.00x** | **0/260 (0%)** | 81/260 (31.2%) | 81/260 (31.2%) | 1,181 s (`19.7m`) | 228/336 (67.9%) | `196 / 49 / 97` |
| **`session_grouped`** (M11 canonical) | Test | 241 | 241 | **1.00x** | **0/241 (0%)** | **156/241 (64.7%)** | **156/241 (64.7%)** | 779 s (`13.0m`) | **177/241 (73.4%)** | `117 / 82 / 51` |
| **`day_grouped`** (M13 strictly disjoint) | Train | 2,154 | 894 | 2.41x | - | - | - | - | 1,485 (68.9%) | `1359 / 371 / 506` |
| **`day_grouped`** (M13 strictly disjoint) | Val | 157 | 157 | **1.00x** | **0/157 (0%)** | **0/157 (0%)** | **0/157 (0%)** | **179,187 s (`49.8h`)** | 117/157 (74.5%) | `57 / 54 / 46` |
| **`day_grouped`** (M13 strictly disjoint) | Test (`2026-05-23`) | 264 | 264 | **1.00x** | **0/264 (0%)** | **0/264 (0%)** | **0/264 (0%)** | **161,242 s (`44.8h`)** | **180/264 (68.2%)** | `113 / 82 / 79` |

\*All `416` (`IMG + Screenshot + image`) timestamped test images in `705d388743ea` (and `426/426` val) fall within `<=600 s` (`median 10–11 s`) of training frames, while **`dHash <= 5`** independently confirms **`42/467`** val (`16 <= 2`) and **`28/472`** test (`12 <= 2`) pixel near-duplicates (vs `0 <= 2` under grouped canonical splits), plus triple-counted augmented copies in `705d/test`. Notice also two deeper structural findings exposed by our audit:
1. Even `vision_v1_session_grouped` placed `session_019` (`156/241` test frames on `2026-07-08`) only `13.0 min` (`779 s`) away from training sessions `018`/`020`. Constructing strictly calendar-day-disjoint `day_grouped` (`8` training dates, `3` val dates `2026-05-28/29/07-11`, strictly held-out test date `2026-05-23`) removes **all** same-day lighting/camera/weather proximity (`>= 44.8 h` separation).
2. `baler.v1i.yolov8` contains **zero empty-background / non-train images** — all `3,157` files carry positive bounding boxes (`2,297 + 483 + 487 = 3,267` instances across `705d`), leaving any model trained solely on `baler.v1i.yolov8` without hard negative rejection of static railway structures.

### 2.2 Audio Split Forensics (`audio_training_dataset_v3.json` vs `audio_v3_stem_grouped`)

- **`audio_training_dataset_v3.json` (Frozen `V3`):** `871 train / 203 val / 182 test` windows (`120 / 26 / 26` clips; `331 / 86 / 65` positive windows; `540 / 117 / 117` negative windows). Forensics confirm:
  1. **Positive-Stem Leakage:** **`5` unique YouTube horn stems** (`28/86 = 32.56%` positive clips) were split across train/val/test, contaminating **`7/13` (`53.8%`) of Val positive recordings (`51/86 = 59.3%` of Val positive windows)** and **`5/13` (`38.5%`) of Test positive recordings (`23/65 = 35.4%` of Test positive windows)**.
  2. **Overlapping Window Redundancy:** Adjacent 1.0 s windows at 0.5 s hop exhibit high feature autocorrelation (**lag-1 cosine similarity = `0.7919`**, **lag-2 = `0.7698`**).
  3. **Stratification:** Clean stem-grouped split [`data/splits/audio_v3_stem_grouped/dataset_split.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/audio_v3_stem_grouped/dataset_split.json) (`867 train / 183 val / 206 test` windows across `120 / 26 / 26` clips; `327 / 66 / 89` positive windows; zero shared stems across partitions) fixes stem leakage cleanly.

---

## 3. Vision (`YOLOv8n`) Forensic Analysis & Clean Retraining (Priorities 3, 5, 7, 8)

![Frozen YOLOv8n Training History](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_v1_39f402_training_curves.png)

### 3.1 Frozen `39f402dfe460` Training Dynamics & Overfitting Signals

From [`vision_baseline_39f402_audit.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_baseline_39f402_audit.json):
- **Train vs. Leaked-Val Gap:** On Epoch 93 (`best.pt`), Ultralytics COCO `mAP@0.50:0.95` reached **`0.90547`** on Train vs **`0.76842`** on Val (**`-13.71 pp` drop** even with 100% session-leaked validation).
- **Late-Epoch Validation Loss Creep & Post-Mosaic Memorization:** `val/cls_loss` bottomed at **Epoch 72 (`0.41057`)** and `val/box_loss` at **Epoch 78 (`0.81682`)**, after which classification loss climbed slowly to `0.43114` at Epoch 97 (`+0.02057`). Turning mosaic off at **Epoch 91 (`close_mosaic=10`)** triggered an immediate training memorization drop (`train/cls_loss`: `0.36315` at Ep 90 -> `0.22837` at Ep 97, **`-0.13478`**) accompanied by **`-0.01096` Val `mAP@0.50:0.95` degradation** (`0.76841` at Ep 93 -> `0.75745` at Ep 97).
- **`evaluator.py` Bug Reconciliation:** Checked-in `evaluation/metrics.json` reported `mAP@0.50 = 0.9946, mAP@0.50:0.95 = 0.8550` on `705d/test`, whereas official Ultralytics COCO evaluation on `best_ep93` measures **`mAP@0.50 = 0.98535, mAP@0.50:0.95 = 0.80351`** (`P=0.99100, R=0.97033`). Direct code audit and unit proof ([`test_mission13_synthetic.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_mission13_synthetic.py)) verified two causes in [`src/railway_detection/vision/evaluator.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/vision/evaluator.py):
  1. `confusion_matrix` and `total_fp` iterate over **unfiltered** `pred_boxes` instead of applying `confidence_threshold=0.5`, producing `total_fp = 94` background false positives while `per_class_precision` filters at `>=0.5`.
  2. `evaluator.py` computes AP via 101-point numpy trapezoidal interpolation (`~+0.0515` higher `mAP@0.50:0.95` than standard COCO evaluation).

### 3.2 Unseen-Subset Collapse of Frozen `39f402` & Test Error Stratification

Evaluating frozen `39f402` (`best_ep93` & `last_ep97`) on clean splits in [`vision_39f402_on_clean_splits.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_39f402_on_clean_splits.json) provides direct proof of frame memorization:
- On **`session_grouped/test`** (`n=241`), `best_ep93` scores `mAP@0.50:0.95 = 0.87438` overall (`177` images were in `39f402`'s own training set!), but drops **`-6.83 pp` to `0.80613`** on the **`64` images unseen during `39f402` training** (`front` `0.8550 -> 0.7704`, `side` `0.8978 -> 0.8124`), with `last_ep97` dropping further to **`0.79498`** (`-1.12 pp`).
- On **`day_grouped/test`** (`n=264`), `best_ep93` scores `0.88246` overall (`180` in `39f402` train), dropping **`-5.83 pp` to `0.82418`** on the **`84` unseen-to-`39f402` images** (`last_ep97 = 0.81369`, `-1.05 pp`).
- Stratifying `705d/test` @ `conf=0.35` shows scale and camera fragility even before removing leakage: recall falls from `0.9820` (`218/222`, large `>=16%`) -> `0.9737` (`148/152`, medium) -> **`0.9646` (`109/113`, small `<4%`)**, while the **`epoch_ms`** mobile camera subset drops to **`0.8710` recall (`27/31`) / `0.9000` precision**. Representative TP, small/blurry FN, and boundary-confusion cases (`front->rear`, `front->side`) are rendered in [`fig_m13_vision_examples.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_vision_examples.png).

![YOLOv8n Leakage Audit vs Clean Retrains](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_v2_leakage_and_clean_retrain.png)
![YOLOv8n Confusion and Field Comparison](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_v3_confusion_and_pr_comparison.png)

### 3.3 Clean Session-Grouped & Calendar-Day-Grouped Retrains (Kaggle Tesla T4)

| Model (`best.pt`, `100` ep, `batch=16`) | Eval Split (`0` overlap for clean runs) | Train `mAP@50-95` | Val `mAP@50` / `mAP@50-95` | `last` Val `mAP@50-95` | Test `P` / `R` | Test `mAP@50` | Test `mAP@50-95` (`Train->Test` Gap) | Test `@0.35` (`264` day-test `TP/FP/FN` & `Small` R) |
|---|---|---:|---:|---:|---:|---:|---:|---|
| **`Frozen 39f402`** (`705d` Leaked) | `705d/test` (`n=472`) | 0.9055 | 0.9652 / 0.7684 | 0.7583 | 0.991 / 0.970 | 0.9854 | 0.8035 (`-10.2 pp`) | *(On day-test: `273/7/1`, `68%` memorized)* |
| **`session_grouped_base`** | `session_grouped/test` (`n=241`) | 0.9008 | 0.9717 / 0.7622 | 0.7604 | 0.919 / 0.921 | 0.9645 | **0.7113 (`-18.95 pp`)** | On day-test: `253/4/21`, Small R `0.8732` |
| **`day_grouped_base`** | Held-out `2026-05-23` (`n=264`) | 0.8876 | 0.9718 / 0.7696 | 0.7564 | 0.952 / 0.960 | 0.9807 | **0.7646 (`-12.30 pp`)** | On day-test: `254/15/20`, Small R `0.8732` |
| **`day_grouped_reg`** (`MixUp+CP+WD+cosLR`) | Held-out `2026-05-23` (`n=264`) | 0.8938 | 0.9583 / 0.7505 | 0.7527 | **0.982 / 0.966** | **0.9810** | **0.7731 (`-12.07 pp`)** | On day-test: **`257/4/17`, Small R `0.9155`** |

Key takeaways from [`vision_kaggle_clean_retrain_audit.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_kaggle_clean_retrain_audit.json) and [`vision_clean_vs_frozen_field_diagnostics.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_clean_vs_frozen_field_diagnostics.json):
1. **True Clean Overfitting Signature Unmasked:** Without same-day leakage (`day_grouped_base`), `val/cls_loss` bottoms at **Ep 73 (`0.4121`)** and climbs **`+16.2%` to `0.4789`** by Ep 100 (`3.2x` steeper than leaked `39f402`'s `+0.0206`), selecting `best.pt` early at **Ep 77** while `last` (`Ep 100`) falls `-1.32 pp` in `mAP@50-95`. On unseen sessions (`session_grouped_base`), `mAP@50-95` plunges **`-18.95 pp`** (`0.9008 -> 0.7113`), proving leaked evaluation concealed nearly `10–19 pp` of box localization & boundary fragility (`front` AP@50-95 stays lowest across clean tests at `0.6955–0.7190` vs `side` `0.8064–0.8179`).
2. **Controlled Regularization Works on Held-Out Days:** `day_grouped_reg` lifts held-out day `Precision` by `+3.07 pp` (`0.9516 -> 0.9823`), raises `mAP@0.50:0.95` to `0.7731`, eliminates `side` FNs (`79/79` true boxes recovered in Ultralytics CM), cuts `@0.35` FPs by **`73%` (`15 -> 4`)**, and lifts small-object recall (`<4%` area) from `0.8732` to **`0.9155`** (`+4.23 pp`).
3. **Why Clean Retraining Alone Cannot Fix `no_train_002` Overhead Bridge False Positives:** Evaluating all 4 models on upright `crossing_A` field controls (`conf=0.35`, `frame_generator(..., source_pts=True)`) demonstrates that `no_train_events/event_002_front` triggers **`60/60`** frames under `frozen_39f402` (`max_conf=0.8606`, `median_ycen=0.1619`), **`59/60`** under `session_grouped_base` (`max_conf=0.9081`, `0.1919`), **`60/60`** under `day_grouped_base` (`max_conf=0.8468`, `0.2042`), and **`60/60`** under `day_grouped_reg` (`max_conf=0.9051`, `0.1980`). Simultaneously, `day_grouped_reg` improves true solitary locomotive sensitivity (`engine_events/event_001_front`: `8/40 -> 22/40` frames, `max_consec 7 -> 15`) and curbs transient noise on `no_train_003_back` (`15 -> 4` frames). Because `baler.v1i.yolov8` has **0 empty-scene images**, static horizontal structures resembling rail cars can only be fixed by adding empty-track / overhead-bridge hard negatives and multi-crossing training footage (or temporary crossing-specific ROI masking explicitly labeled as post-hoc geometry tuning).

---

## 4. Audio (`CompactTrainHornCNN`) Forensic Analysis & Clean Retraining (Priorities 4, 5, 7, 8)

![CompactTrainHornCNN Training & Instability](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_a1_training_and_instability.png)
![CompactTrainHornCNN ROC PR Calibration](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_a2_roc_pr_confusion_calibration.png)
![CompactTrainHornCNN Errors CV & Learning Curve](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/fig_m13_a3_errors_cv_and_learning_curve.png)

### 4.1 Frozen `V3` Evaluation Across Splits & Validation-Leakage Inflation

All metrics below are taken directly from [`audio_audit_summary.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/audio_audit_summary.json):

| Evaluation Cohort (Frozen `V3`, `ea1bb81d`) | `n` (`pos/neg`) | Threshold | Accuracy | Precision | Recall `[95% CI]` | Specificity `[95% CI]` | F1 | ROC-AUC | PR-AUC | Brier / ECE |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|---|
| **Clean Train (Unaugmented)** | 871 (`331/540`) | 0.37 | 0.9885 | 0.9908 | 0.9789 `[.957,.990]` | 0.9944 `[.984,.998]` | **0.9848** | 0.9986 | 0.9981 | `0.0128 / 0.0330` |
| **Leaked Val** (`59.3%` pos leaked) | 203 (`86/117`) | 0.37 | 0.9951 | 0.9885 | **1.0000** | 0.9915 | **0.9942** | 0.9999 | 0.9999 | `0.0119 / 0.0538` |
| **Locked Test (Windows)** | 182 (`65/117`) | 0.37 | 0.8956 | **0.7875** | 0.9692 `[.895,.992]` | **0.8547** `[.780,.907]` | **0.8690** | 0.9613 | 0.9415 | **`0.0820 / 0.0817`** |
| **Locked Test @ `0.50` (`No Cal`)** | 182 (`65/117`) | 0.50 | 0.8956 | 0.8026 | 0.9385 `[.852,.976]` | 0.8718 `[.799,.921]` | 0.8652 | 0.9613 | 0.9415 | `0.0820 / 0.0817` |
| **Locked Test (Recording-Max)** | 26 (`13/13`) | 0.37 | 0.8462 | 0.7647 | 1.0000 `[.772,1.0]` | **0.6923** `[.424,.873]` | 0.8667 | 0.9408 | 0.9447 | **`0.1253 / 0.1839`** |
| **External `crossing_A` Field (`T*=0.37`)** | 26 (`13/13`) | 0.37 | 0.4615 | **0.4800** | 0.9231 (`12/13`) | **0.0000 (`0/13`!)** | **0.6316** | **0.6805** | **0.7290** | `(10/10 + 3/3 FP)` |
| **External `crossing_A` (`Hyst 0.75, k=2`)** | 26 (`13/13`) | `(0.75, k=2)` | 0.7692 | 0.8889 | 0.6154 (`8/13`) | **0.9231 (`12/13`)** | 0.7273 | *(0.6805)* | *(0.7290)* | `(1/10 + 0/3 FP)` |

Notice the complete diagnostic chain:
- **Calibration Illusion:** Because `51/86` (`59.3%`) validation positive windows came from **training stems** (mean prob `0.9770`) and negatives came cleanly from ESC-50 Fold 4, Val `F1` hit an artificial **`0.9942`**, pulling calibrated `T*` down to **`0.3700`** (higher specificity on uncontaminated negatives masked true boundary overlap).
- **Test Collapse (`-12.52 pp` F1):** On ESC-50 Fold 5 test negatives, **only `3` acoustic categories** drove all `17/117` window FPs (`4/13` test recordings): **`engine` (`9/18` = `50.0%`, `max_p = 0.9309`), `church_bells` (`7/18` = `38.9%`, `max_p = 0.9822`), and `siren` (`1/9` = `11.1%`, `max_p = 0.9406`)**, while `car_horn` contained only `1` recording (`9` windows, `max_p = 0.0892`). Brier error jumped `6.9x` (`0.0119 -> 0.0820`) and recording ECE jumped `3.4x` (`0.0538 -> 0.1839`).
- **External `crossing_A` Domain Shift:** In continuous field crossings (`n=26` annotated + `1` solitary engine=`0`), ambient road/rail rumble + crossing noise pushes max window probabilities above `0.37` on **`13/13` horn-free recordings (`10/10` horn-absent trains + `3/3` no-train controls, `0.0000` specificity!)**, while ranking discriminability drops to **`PR-AUC = 0.7290` / `ROC-AUC = 0.6805`**. Hysteresis `(0.75, k=2)` restores `0.9231` specificity (`12/13`) at a `-30.8 pp` horn recall penalty (`12/13 -> 8/13`).

### 4.2 Clean Stem-Grouped 5-Seed Ablations, 5-Fold CV & Sample-Size Learning Curve

| Experiment (`5` seeds `[42,101,202,303,404]` unless noted) | Clean Train `F1` | Clean Val `F1` | Clean Test `F1 (cal)` | Test `PR-AUC` / `ROC-AUC` | Test `Spec` / `Rec-F1` | Val Spikes `>0.20` | External `crossing_A` `PR-AUC` |
|---|---:|---:|---:|---:|---:|---:|---:|
| **`stem_grouped_v3_recipe`** (`BN`, `drop=0.30, wd=1e-4`) | `0.9411 +- .0268` | `0.8843 +- .0164` | **`0.8413 +- .0221`** | `0.9285 / 0.9447` | `0.8308 / 0.8787` | **`4.4 +- 2.3`** | `0.6897 +- .0433` |
| **`stem_grouped_specaug_strongreg`** (`drop=0.45, wd=1e-3, SpecAug, clip=1.0`) | `0.9239 +- .0352` | **`0.9020 +- .0238`** | **`0.8486 +- .0174`** | `0.9244 / 0.9416` | `0.8017 / 0.8787` | `3.6 +- 2.1` | `0.6641 +- .0144` |
| **`stem_grouped_groupnorm_specaug`** (`GroupNorm+LN`, `drop=0.40, SpecAug`) | `0.8568 +- .0301` | `0.8175 +- .0163` | `0.7999 +- .0347` | `0.9089 / 0.9223` | `0.7675 / 0.8711` | **`2.4 +- 1.1`** | `0.6903 +- .0332` |
| **`5-Fold Stem+Fold CV` (`v3_recipe`)** | - | - | **`0.8638 +- .0565`** (`[0.772..0.912]`) | `0.9261 / 0.9584` | `mean RecF1 0.8950` | - | - |
| **`5-Fold Stem+Fold CV` (`GroupNorm+SpecAug`)** | - | - | `0.8346 +- .0717` (`[0.730..0.915]`) | `0.9100 / 0.9405` | `mean RecF1 0.8816` | - | - |

- **Training Instability Explained:** Replacing `BatchNorm2d` with `GroupNorm` (`GroupNormTrainHornCNN`) cuts validation loss spikes (`>0.20`) nearly in half (**`4.4 -> 2.4` spikes/run**), proving batch-normalization variance over tiny `~867`-window minibatches causes the jagged `val_loss` spikes (`max 0.965`), though on clean splits `GroupNorm` loses `-4.14 pp` Test F1 (`0.8413 -> 0.7999`). SpecAugment + stronger regularization reduces seed-to-seed Test F1 variance (`std 0.0221 -> 0.0174`) and slightly improves Test F1 (`0.8486`).
- **Learning Curve Proves Sample Scarcity:** Across `20% -> 40% -> 60% -> 80% -> 100%` of clean training clusters (`mean 168.3 -> 867.0` windows), clean Test `F1` rises monotonically **`0.7614 +- 0.0559 -> 0.8133 -> 0.8043 -> 0.8412 -> 0.8588 +- 0.0253`** (`PR-AUC`: **`0.6899 -> 0.7893 -> 0.8927 -> 0.9121 -> 0.9086`**) with zero plateau, demonstrating that **`120` clean training recordings (`~172` total corpus) are still data-starved**, especially on tonal harmonic distractors (`engine`, `church_bells`, road horns).

---

## 5. Priority 6 Synthesis & Actionable Mitigation Roadmap (Priority 9)

1. **Why Frozen Metrics Looked "Perfect" Yet Failed Operational Transfer:**  
   - **Vision:** Random frame splitting (`705d388743ea`) leaked `100%` of capture sessions (`0 s` min gap, `10–11 s` median gap) and multiple Roboflow augmented variants across train/val/test, inflating COCO `mAP@0.50:0.95` from `0.711–0.773` (clean) up to `0.804` (`0.855` under buggy `evaluator.py`). Simultaneously, having **`0` negative-only images** left every retrained model vulnerable to overhead bridge textures (`no_train_002`).
   - **Audio:** Leaked stems (`59.3%` val positive windows) compressed calibrated threshold `T*` down to `0.37`, overfitting ESC-50 lab cleanliness and failing at `0%` recording specificity on real `crossing_A` ambient noise (`engine`, road vehicles, rail rumble).
2. **Concrete Non-Speculative Engineering Next Steps for Future Data Collections (`Option C`):**
   - **Vision:** Retain `day_grouped_reg` (`MixUp + CopyPaste + cos_lr + dropout + weight_decay`) as the baseline recipe; collect **multi-crossing** images (`Option C`) explicitly including **20–30% empty crossing / bridge / glare / night hard-negative frames**, and preserve native aspect ratio (`letterbox`, not squashed Roboflow 1:1 `640x640`).
   - **Audio:** Expand beyond `172` clips (`learning curve` still rising at `100%`); replace/augment ESC-50 negatives with **real `crossing_A`/`crossing_B` ambient trackside negatives** (road trucks, diesels, auto-rickshaws, warning bells, wind), maintain strict stem/recording grouping, and decouple `(0.75, k=2)` confirmation hysteresis until domain-matched calibration lowers false triggers without sacrificing horn recall.

---

## Index of Reproducible Audit Artifacts

- Scripts: [`run_mission13_vision_baseline_audit.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/run_mission13_vision_baseline_audit.py), [`run_mission13_audio_audit.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/run_mission13_audio_audit.py), [`generate_mission13_figures.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/generate_mission13_figures.py)
- JSON Results: [`audio_audit_summary.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/audio_audit_summary.json), [`vision_baseline_39f402_audit.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_baseline_39f402_audit.json), [`vision_split_leakage_comparison.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_split_leakage_comparison.json), [`vision_39f402_on_clean_splits.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_39f402_on_clean_splits.json), [`vision_kaggle_clean_retrain_audit.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_kaggle_clean_retrain_audit.json), [`vision_clean_vs_frozen_field_diagnostics.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/model_generalization_audit/vision_clean_vs_frozen_field_diagnostics.json)
- Figures: `fig_m13_a1..a3`, `fig_m13_v1..v3`, `fig_m13_vision_examples` under [`docs/generated/model_generalization_audit/figures/`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/model_generalization_audit/figures/)
- Synthetic Forensic Unit Tests: [`tests/unit/test_mission13_synthetic.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_mission13_synthetic.py)
