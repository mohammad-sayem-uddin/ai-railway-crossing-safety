# Dataset, Ground Truth & Leakage Audit Report

**Audit Evidence:** [`vision_audio_leakage_audit.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_audit/vision_audio_leakage_audit.json), [`dataset_manifest.jsonl`](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_validation/dataset_manifest.jsonl), [`RESEARCHER_ANNOTATION_ADOPTION.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/professor_evidence/mission43/RESEARCHER_ANNOTATION_ADOPTION.json), [`real_world_v2_video_manifest.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/professor_evidence/mission43/real_world_v2_video_manifest.json), [`PUBLICATION_TABLES.md`](file:///Users/sayemuddin/Desktop/Train_automation/results/publication_tables/PUBLICATION_TABLES.md)  
**Visual Comparison:** [`fig11_dataset_leakage_comparison.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/figures/fig11_dataset_leakage_comparison.png)  
**Raw Media Boundary:** `raw_media_accessed: false` (`AUTH-MEDIA-ACCESS.json` absent; zero raw images, audio, or `.mov` frames decoded).

---

## 1. Planned Target vs Actual Verified Corpora (Fact Check)

| Claim / Corpus | Documented Target / Claim | Actual Verified Repository Fact |
|---|---|---|
| Vision V1 (`baler.v1i.yolov8`) Size | `~4,000` train images planned across `~24` crossings ([`RESEARCH_CONCEPT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/archive/RESEARCH_CONCEPT.md#L241)) | **`3,157` manifest entries** (`640x640`), derived from **`1,315` unique source images** (`921` sources × `3` Roboflow aug copies + `394` unaugmented); `3,267` boxes (`front: 1,761`, `side: 805`, `rear: 701`); **`0` negative background images**. |
| `"104 rainy-condition train images"` | Occasionally cited in external notes | **`NOT FOUND`** anywhere in repository code, manifests, or documents. |
| Audio V3 (`TrainHorn + ESC-50`) | Balanced train horn vs non-horn corpus | **`172` clips**: `86` positive train horn segments from **`57` canonical stems** (`66` raw stem variants before normalization); `86` ESC-50 non-horn negatives across `5` folds. |
| Layer B Field Video (`real_world_v2`) | Multi-condition field crossing evaluation | **`27` active events** (`23` `train_events`, `3` `no_train_events`, `1` `engine_events`) + `1` excluded duplicate (`54` active `.mov` containers: `48` at `1920x1080`, `8` at `3840x2160` total incl. duplicate manifest; `29.97` fps HEVC, `48 kHz` stereo AAC). |

---

## 2. Critical Data Leakage Uncovered & Remediated (`leakage_audit.py`)

### 2.1 Vision V1 Split Leakage (`705d388743ea` vs Roboflow vs Candidate Clean)
Filename timestamps across `3,077` of `3,157` images (`1,283` unique sources spanning `13` dates from `2025-11-13` to `2026-07-11`: `Screenshot-YYYY-MM-DD-at-HH-MM-SS` `949` groups / `2,255` imgs; `IMG_YYYYMMDD_HHMMSS` `233` / `559`; 13-digit `epoch_ms` `76` / `202`; ISO `image` `25` / `61`; `unparsed` `32` / `80`) cluster into **`29` capture sessions** at a `10-minute` (`gap <= 600 s`) threshold:

1. **Roboflow Original Folders (`2,763 / 263 / 131`):** Even before re-splitting, **`27 / 29` (`93.1%`)** capture sessions crossed between `train`, `valid`, and `test`, placing **`127 / 127` (`100%`)** of timestamped `test` images in the same 10-minute session bursts as `train`.
2. **Active Split `705d388743ea` (`2,218 / 467 / 472`):** Marked `"split_type": "development_fallback"`, `"leakage_risk": true`, `"allow_ungrouped_fallback": true`. Worse than Roboflow:
   - **`87.1%` (`411 / 472`) of `705d/test`** (and `405 / 467` of `705d/val`) originated from Roboflow **`train/` offline-augmented** exports (`3×` duplicates sharing visual composition with `train`).
   - **`27 / 29` (`93.1%`)** sessions crossed splits at `gap = 600 s`, putting **`447 / 447` (`100.0%`)** of timestamped `test` images and **`458 / 458` (`100.0%`)** of timestamped `val` images inside `train` capture sessions!
3. **Remediated Candidate Split [`vision_v1_session_grouped`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/vision_v1_session_grouped/split_summary.json):**
   - Groups all timestamped sources at `gap <= 600 s` strictly into disjoint partitions (`unparsed` confined to `train`), and strips `804` evaluation augmentation duplicates from `val`/`test`.
   - Resulting split: **`train = 1,776` (`738` unique sources; boxes: `front=1016, rear=388, side=445`), `val = 336` (`336` unique; `front=196, rear=49, side=97`), `test = 241` (`241` unique; `front=117, rear=82, side=51`)**.
   - **Verified Leakage (`test_leakage_free_splits.py`):** **`0 / 29`** crossing sessions for `gap <= 120 s`, `300 s`, and **`600 s`**, **`0 / 241`** test overlap with `train`, **`0`** multi-split source groups, and **`0`** augmentation duplicates in `val`/`test`. *(Remaining limitation: continuous multi-hour `2026-07-08` macOS screenshots merge across `gap >= 1800 s`, yielding `2` session crossings at `1800 s` because intra-day recording gaps vary).*

### 2.2 Audio V3 Split Leakage (`audio/v3` vs Candidate Clean)
- **Original [`audio/v3/dataset_split.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/audio/v3/dataset_split.json) (`120 / 26 / 26`):** ESC-50 negatives strictly respect 5-fold isolation (Folds `1–3` train `60`, Fold `4` val `13`, Fold `5` test `13`, **`0` cross-split folds**). However, **`5 / 57` unique positive YouTube stems (`28 / 86 = 32.56%` of positive recordings)** cross between `train`, `val`, and `test` (`"19"`, `"Horn of Bangladesh Train"`, `"Train horn sound effect ...#short"`, `"Train whistle of Bangladesh Railway Broad Gauge ... 60 61 63 64 & 65"`, `"Whistle of New EMD Locomotive ..."`).
- **Remediated Candidate [`audio_v3_stem_grouped`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/audio_v3_stem_grouped/split_summary.json):**
  - Uses greedy bin-packing over stem counts while keeping ESC-50 folds untouched.
  - Yields exact balanced counts (**`train: 60/60 (120)`, `val: 13/13 (26)`, `test: 13/13 (26)`**) with **`0 / 57` cross-split positive stems (`0.00%` stem leakage)** and **`0` cross-split ESC-50 folds**.

---

## 3. Ground Truth Governance & Layer B Field Corpus Audit
1. **Environmental-Class Confounding (`100%` Coupled):** Every single `23/23` `train_events` proposal in [`RESEARCHER_ANNOTATION_ADOPTION.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/professor_evidence/mission43/RESEARCHER_ANNOTATION_ADOPTION.json) carries `{crossing_id: "crossing_A", session_id: "session_20260914_morning", lighting: "day", weather: "overcast"}`, whereas all `3/3` `no_train_events` and `1/1` `engine_events` carry `{lighting: "night", weather: "clear"}`. Real `train` vs `no_train` comparisons are therefore completely confounded with `day/overcast` vs `night/clear`!
2. **Annotation Provenance (`Stage 2.1` Absent):** `0` Stage-2.1 human-reviewed records exist; `27` retired schema-`6.0.0` manifests fail closed. Only the `27` researcher-adopted AI-assisted `7.0.0` proposals support **exploratory** replay (`DATASET_AND_REFERENCE_ANNOTATIONS.md`).
3. **Hardware Coverage Gaps:** `0 / 27` events have a side camera (`side` YOLO labels only appear on `cam_1`/`cam_2`); `0 / 27` have occupancy sensors (`1/27` has `T_scene_clear = 32.5 s` on `event_011`); `0 / 27` back streams yield a `last_carriage` YOLO detection (`30` sparse `rear` boxes total); `11 / 23` train events (`sync11`) have candidate manual sync offsets.
4. **Root Cause of Real Vision Misses (`13/23` un-triggered approach):** Frozen `pre-db40305` vision JSONLs lack upright rotation for `-90°` `.mov` containers (`7` zero-detection events: `005, 008, 009, 012, 015, 017, 020`), while causal `confirm_frames=2` removes `5` sparse single-frame gaps (`002, 010, 014, 016, 019`) that previously passed via stale backfill (`Exp I`).
