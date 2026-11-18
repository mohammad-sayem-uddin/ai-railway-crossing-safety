# Project State Reconstruction (`d4db94d` -> `d103275` -> `62191ef`)

**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Audit Baseline Commit:** `62191ef6d8047e204f439c5cd3cc24f526fd04f8` (`exp/four-layer-completion`)  
**Main Branch HEAD:** `d1032756de80963130e1cbd3d2334cb32139b996` (`main`)  
**Historical Reference Baseline Cited in Prompt:** `d4db94d` (2026-10-29 snapshot in [`RESEARCHER_DECISIONS_AND_EVIDENCE_PACKAGE_20261029.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/RESEARCHER_DECISIONS_AND_EVIDENCE_PACKAGE_20261029.md))  
**Verification Mode:** Live repository telemetry + read-only metadata/cache inspection (raw media under `data/raw/` untouched per [`media_guard.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/safety/media_guard.py)).

---

## 1. Chronological State Transition (`2026-10-29` to `2026-11-14`)

A central finding of this reconstruction is that the project has evolved substantially beyond the `2026-10-29` `d4db94d` historical baseline often referenced in earlier handoff prompts:

| Milestone / Commit | Date | State Summary | Governance Blockers | Key Engineering / Research Additions |
|---|---|---|---|---|
| `d4db94d` (Historical snapshot) | 2026-10-29 | Pre-decision exploratory audit baseline | `ready: false`, `blocker_count: 9`, D1–D4 all undecided | Historical `118` + `149` test subsets documented; official Phase 12 blocked |
| `544b63c`, `6aa7fd1`, `25bab63` | 2026-11-08 | Repository cleanup & `README.md` rebuild | Official evaluation blocked (`AUTH-MEDIA-ACCESS` absent) | `.gitignore` hardening; superseded legacy YAML configs removed from active claims |
| `d62cc05`, `c35d133` | 2026-11-09 | Researcher governance decisions recorded | `blocker_count` reduced `9 -> 7` (`M4` + `R04` + `elaf85777` added) | Recorded [`phase12_protocol_decision.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/phase12_protocol_decision.json) (`M4` primary + `v9` sensitivity), [`phase12_r04_scope_decision.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/phase12_r04_scope_decision.json) (`11` dual / `16` independent), [`POLICY_ADOPTION_V2_20261109.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/research_decisions/POLICY_ADOPTION_V2_20261109.md), [`SPLIT_DECISION_OPTION_A_20261109.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/research_decisions/SPLIT_DECISION_OPTION_A_20261109.md), second reviewer [`authorized_reviewers.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/authorized_reviewers.json), [`run_stage21_review.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/run_stage21_review.py) |
| `45c84aa` – `d103275` (`main`) | 2026-11-10..13 | Exploratory V1/V2 multimodal completion | Same `7` official blockers (`0` Stage-2.1 reviews) | 27-event exploratory replay, synthetic fault tests, `docs/generated/final_research/` |
| `0ce8620` – `62191ef` (`exp/four-layer-completion`) | 2026-11-13..14 | **V3 Four-Layer Causal Prototype** | Same `7` official blockers (`0` Stage-2.1 reviews) | Fixed 7-angle display rotation normalization, removed default stale-detection backfill (`collector.py`), implemented Layers 1–4 + `OccupancyVerifier` ([`decision_engine_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/decision_engine_v3_four_layer.py)), executed `Exp A–N` + 23 SHA-256 bit-identical artifacts (`results/exploratory_v2/`), `docs/generated/final_research_v2/` (`fig01`–`fig10`), `3,819 passed / 41 pre-existing failed` |

---

## 2. Live Verification Snapshot (`62191ef`)

### 2.1 Official Evaluation Gate (`cli.main evaluation status`)
Executed directly via `.venv/bin/python -m railway_detection.cli.main evaluation status`:
- **`ready`:** `false` (`blocker_count: 7`)
- **`blocker_codes`:** `["COHORT_APPROVAL_MISSING", "EVAL_AUTH_NOT_GRANTED", "EVENT_SPLIT_DECISION_MISSING", "MANIFEST_MISSING", "STAGE21_RECORDS_MISSING"]` (total 7 blocker entries across required promotion/auth checks)
- **Live SHA-256 bindings verified:**
  - `protocol_profile_sha256`: `6b5edb4852fc0d16a10ac1975f3f18d6feb98...` (`6b5edb4852fc0d16a10ac1975f3f18d6feb28fe91638971da7d3761a7a6d42ca`)
  - `r04_scope_decision_sha256`: `f6eabebaab9a925628c119feb9638ba108b7e0c3fbcb942efdf890c2d6e5fc08`
- **Hard Media Firewall:** `data/governance/AUTH-MEDIA-ACCESS.json` is **absent**. Opening raw media in `data/raw/` is blocked by [`media_guard.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/safety/media_guard.py).

### 2.2 Reproducibility Audit (`cli.main audit reproducibility`)
Executed directly via `run_reproducibility_audit()`:
- **Counts:** `{"FAIL": 1, "NOT_AVAILABLE": 2, "PASS": 6, "UNRESOLVED": 4}`
- **PASS (6):** `dataset_manifests`, `r04_scope_decision`, `model_checkpoint_fingerprints`, `config_and_policy_fingerprints`, `ultralytics_importable`, `manuscript_claims_vs_evidence` (`0` unsupported claims across `PHASE16_*`)
- **UNRESOLVED (4):** `approved_ground_truth` (`0` Stage-2.1 records; `27` retired schema `6.0.0`), `protocol_version` *(stale code bug: ignores live `phase12_protocol_decision.json`)*, `event_split_decision` (Option A descriptive mode cannot encode `train/val/test`), `unresolved_decisions` register
- **FAIL (1):** `dependency_lock` (`11` package minor-version mismatches vs `requirements.lock` inside `.venv`, e.g., `anyio`, `fsspec`, `charset-normalizer`, `filelock`)
- **NOT_AVAILABLE (2):** `evaluation_result_provenance`, `experiment_manifest_completeness` (no official Phase 12/13 result exists)
- **Historical Archive Check:** `historical_claim_audit_status: FAIL` (`9` preserved findings on archival `.docx`, disposition `preserved_with_findings`).

### 2.3 Pre-Existing Software Architecture & Environment Telemetry
- **Virtualenv `.venv`:** Python `3.11.15`, `torch 2.13.0`, `ultralytics 8.4.121`, `av 18.1.0`, `opencv-python 5.0.0.93`, `numpy 2.4.6`, `PyYAML 6.0.3`, `Pillow 12.3.0`. Missing from `.venv`: `onnx`, `onnxruntime`, `scipy`, `librosa`, `sklearn` (`scipy` and editable `railway-detection` reside in `venv/`).
- **Test Collection Behavior:** `tests/` contains `172` test files including **4 duplicate module basenames** (`test_cli.py`, `test_contracts.py`, `test_isolation.py`, `test_manifest.py`), causing `pytest tests` without `--import-mode=importlib` to abort collection on `tests/synthetic_mission18a/test_isolation.py` colliding with `tests/synthetic_mission17d/test_isolation.py`. With `--import-mode=importlib`, `final_research_v2` observed `3,819 passed, 41 pre-existing failed` (`139.55s`).

---

## 3. Forensic Reconstruction of Actual Data & Checkpoints

### 3.1 Vision V1 (`baler.v1i.yolov8`) — Verified Reality vs Planned Claims
- **Planned vs Actual:** The `"~4,000 train images"` phrasing in [`RESEARCH_CONCEPT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/archive/RESEARCH_CONCEPT.md#L241) was a *planned* target across ~24 crossings; the `"104 rainy-condition train images"` claim found in some external project notes does **not appear anywhere** in `Train_automation` documents or manifests (`NOT FOUND`).
- **Actual verified corpus ([`dataset_manifest.jsonl`](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_validation/dataset_manifest.jsonl)):** **`3,157` images** (`640x640`, `3,267` bounding boxes: `front: 1,761`, `side: 805`, `rear: 701` (`rare`=`rear`), `0` negative background images), derived from **`1,315` unique source images** (`921` sources × `3` Roboflow offline augmentations + `394` unaugmented).
- **Newly Discovered Critical Leakage in Active Vision Split (`705d388743ea`) & Original Roboflow Folders:**
  1. Split [`705d388743ea`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/705d388743ea/split_summary.json) is flagged `"split_type": "development_fallback"`, `"leakage_risk": true`, `"allow_ungrouped_fallback": true`.
  2. **`87.1%` (`411 / 472`) of `705d/test`** (and `405 / 467` of `705d/val`) are drawn from Roboflow `train/` **3×-augmented** images!
  3. Grouping only by exact source filename left consecutive burst frames (e.g., `Screenshot-2026-05-23-at-14-00-50_png`, `IMG_20251204_105453_460_jpg`, `1764911995523_jpg`) scattered across `train`/`val`/`test`: across all `3,077` timestamped images (`1,283` unique sources spanning `13` dates), clustering at a conservative `10-minute` (`600 s`) capture-session gap yields **`29` discrete sessions**, of which **`27 / 29` (`93.1%`) cross splits** in `705d388743ea`, placing **`447 / 447` (`100.0%`)** of timestamped `705d/test` images (and `127 / 127` in original Roboflow `test/`) into the same capture sessions as `train`.
- **Consequence:** Frozen `YOLOv8n` checkpoint `39f402dfe460` (`92` epochs trained, `24.49 MB` unstripped file containing optimizer/EMA state vs `6.04 MB` FP16 weights) achieved **`0.9946` mAP@50** and **`1.000` `rear` F1** on leaked `705d/test`, but only `10/23` (`43.48%`) front trigger rate and `30` sparse `rear` / `0` `last_carriage` detections on Layer B crossing streams.

### 3.2 Audio V3 (`CompactTrainHornCNN`) — Verified Reality
- **Checkpoint ([`best.pt`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt)):** `329,497` bytes (`0.33 MB`), `25,989` parameters (`103,972` weight bytes), trained on natural `log(mel_spec + eps)` (`[64, 61]`), frozen operating threshold `0.37`.
- **Clean ESC-50 Negatives, Multi-Segment Positive Stem Leakage ([`dataset_split.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/audio/v3/dataset_split.json)):** `172` recordings (`86` train horns from `57` canonical stems [`66` unnormalized raw variants]; `86` ESC-50 non-horn negatives). ESC-50 negatives are strictly fold-isolated across splits, **but `5 / 57` unique YouTube stems (`28 / 86 = 32.56%` of positive recordings)** cross between `train`/`val`/`test`.
- **Layer B Domain Gap (`Exp C`):** Test window Acc `0.8956`, F1 `0.869`, ROC-AUC `0.9613`, ECE `0.0817` (recording ECE `0.1839`, Spec `0.6923`) collapses on field `audio23` to **Recall `0.9231`, Precision `0.5455`, Specificity `0.0000` (`10/10` FP)**, with road vehicle horns in `no_train_events` scoring `0.800–0.826`.

### 3.3 Layer B Field Video Corpus (`27` Active Events + `1` Excluded Duplicate)
- **Physical Streams:** `54` active `.mov` containers (`48` at `1920x1080`, `8` at `3840x2160` UHD, HEVC `~29.97` fps, 48kHz stereo AAC; plus `2` historical duplicate streams excluded).
- **Session Confound & AI Proposal Metadata Bug Discovered in Active Proposals:** Metadata reconstruction ([`results/dataset_audit/layer_b_split_audit_and_collection_plan.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_audit/layer_b_split_audit_and_collection_plan.json)) confirms that all `27` active schema-`7.0.0` events come from one crossing (`crossing_A`) across **two physical sessions**: Session 1 (`2026-09-14 14:13–17:26 +06:00`, daytime, `train_events/001..020`) and Session 2 (`2026-10-04 19:22–19:59 +06:00`, dusk/night, `train_events/021..023` [`night_video_lowlight`] + `3/3` `no_train_events` + `1/1` `engine_events`). Automated proposals mis-tagged `27/27` with `session_20260914_morning` and mis-labeled `021..023` as `lighting: "day"` (`7` inconsistent Session 2 metadata records). Because `100%` of controls come from Session 2 dusk/night at `crossing_A`, no leakage-safe 3-way train/val/test split exists (`leakage_safe = false`).
- **Missing Sensor Hardware in Collected Corpus:** `0/27` events have a dedicated side camera, `0/27` have a physical crossing occupancy sensor (`1/27` has proposal `T_scene_clear`), and only `11/23` have R04 candidate sync offsets.

---

## 4. Remaining Authentic Technical Gaps Targeted in This Mission

Since `exp/four-layer-completion` (`0ce8620`) already implemented V3 Four-Layer FSM fusion (`Exp A–N`), the highest-value unresolved engineering and scientific gaps are:
1. **Reproducibility Audit Consistency:** Fix [`audit.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/reproducibility/audit.py) so `protocol_version` reflects live verified [`phase12_protocol_decision.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/phase12_protocol_decision.json) rather than falsely flagging `premature_opening_window` `UNRESOLVED`.
2. **Leakage-Free Vision V1 & Audio V3 Splits:** Quantify burst/session/stem leakage algorithmically and emit verified, non-destructive session-grouped (`Vision`) and stem-grouped (`Audio`) split manifests ready for leakage-free retraining.
3. **Post-Hoc Acoustic Hysteresis & Calibration Study (`Exp O`):** Quantify temperature scaling / Platt calibration and `(k, tau)` consecutive-window hysteresis on the `2,600` field audio window scores + `no_train`/`engine` window caches.
4. **CPU Inference Optimization & Raspberry Pi Edge Readiness Profiling (`Exp P`):** Benchmark real CPU `YOLOv8n` + `CompactTrainHornCNN` + V3 engine stages (`640/416/320`, TorchScript, stripped weights vs optimizer-laden `.pt`, INT8 quantization behavior on CNN/MLP), peak RSS, and analytical event-triggered duty-cycle savings.
5. **Adverse Weather / Low-Visibility & Intrusion Stress Suite (`Exp Q`):** Controlled synthetic simulation quantifying V3 availability/safety under confidence attenuation (`rain/fog/night`), burst frame dropout, stopped obstacle interlocking, and multi-train reopening interruption.
6. **Unified Literature-Grounded IEEE Manuscript, Full 13-Report Audit Suite, Figures, and Synchronized `README.md`.**
