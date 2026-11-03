# Diagnostic Harness & Execution Scripts: Static Safety Audit

**Document Version:** 1.0.0  
**Audit Type:** Static Code Safety & Side-Effect Audit (Zero Execution)  
**Governing Scripts & Modules:**  
- `scripts/run_real_world_experiments.py`
- `scripts/run_phase5_full_inference.py`
- `src/railway_detection/experiments/layer_b_processor.py`
- `src/railway_detection/data/audio_extractor.py`
- `src/railway_detection/vision/video.py`
- `src/railway_detection/evaluation/replay_producer.py`
**Active Policies Evaluated:**  
- Media Access Hold ([`docs/MEDIA_ACCESS_HOLD_RESOLUTION_PLAN.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/MEDIA_ACCESS_HOLD_RESOLUTION_PLAN.md))  
- Research Evaluation Authorization Policy ([`docs/RESEARCHER_DECISION_BRIEF.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/RESEARCHER_DECISION_BRIEF.md))  

---

## 1. Executive Summary

This audit performs a strict, static inspection of the control flow, input dependencies, subprocess invocations, filesystem side-effects, and governance checks in the repository's diagnostic execution scripts: `scripts/run_real_world_experiments.py` and `scripts/run_phase5_full_inference.py`.

### Critical Finding:
Neither script is safe to execute under the current Media Access Hold. 
1. `scripts/run_phase5_full_inference.py` has **`use_cache=False` hardcoded** across lines 324, 343, and 361. Invoking this script immediately launches video decoding and audio extraction on all 54 active media files.
2. `scripts/run_real_world_experiments.py` contains a **silent fallback to raw media decoding**: if any cache file in `results/experiments/cache/` is absent, corrupted, or zero bytes, control flow automatically falls through to opening raw `.mov` video files without raising an error.
3. Both scripts bypass formal split governance, ground-truth authorization (`ADJ-AUTH`), and evaluation authorization (`EVAL-AUTH`), and `run_real_world_experiments.py` overwrites existing documentation files upon execution.

---

## 2. Potential Raw-Media Read Paths

### 2.1 Video Decoding Invocations
In `src/railway_detection/experiments/layer_b_processor.py` (`run_vision_inference`, lines 172–239):
```python
cache_file = self.cache_dir / f"{cohort}_{video_path.parent.name}_{video_path.stem}_{source_id}_vision.jsonl"
if use_cache and cache_file.exists():
    # Reads pre-computed JSONL
    return records

# FALLTHROUGH HAZARD:
if not video_path.exists():
    return []
yolo = self._get_yolo_model(checkpoint_path)
for frame in frame_generator(video_path, target_fps=target_fps, source_id=source_id): # OPENS RAW VIDEO!
    preds = yolo.predict(frame.image, conf=conf, verbose=False)
```
- **Hazard Mechanism:** When `cache_file.exists()` evaluates to `False`, the function does NOT abort. Instead, it imports and calls `frame_generator(video_path)` from `src/railway_detection/vision/video.py`, which opens the video container using OpenCV / PyAV, decoding raw RGB pixel arrays.
- **Affected Invocations:**
  - `front_video = event_dir / "camera_front.mov"` (lines 358, 362)
  - `back_video = event_dir / "camera_back.mov"` (lines 359, 371)
- **Hardcoded Bypass in Phase 5 Script:**
  In `scripts/run_phase5_full_inference.py`:
  - Line 324: `front_v_recs = processor.run_vision_inference(..., use_cache=False)`
  - Line 361: `back_v_recs = processor.run_vision_inference(..., use_cache=False)`
  Because `use_cache=False` is hardcoded, every execution opens and decodes all 54 `.mov` files regardless of whether cache files exist.

### 2.2 Audio Extraction Subprocesses
In `src/railway_detection/experiments/layer_b_processor.py` (`extract_audio`, lines 135–170):
```python
if front_video.exists():
    if not front_wav.exists() or front_wav.stat().st_size == 0:
        extracted["front"] = extract_audio_from_video(
            front_video, front_wav, sample_rate=16000, channels=1
        )
```
- **Hazard Mechanism:** In `src/railway_detection/data/audio_extractor.py`, `extract_audio_from_video()` executes an external `ffmpeg` subprocess:
  ```bash
  ffmpeg -y -i <camera_front.mov> -vn -ar 16000 -ac 1 -f wav <camera_front.wav>
  ```
  This reads raw QuickTime audio samples and transcodes them to linear PCM WAV.
- **Audio Inference Fallthrough:**
  In `layer_b_processor.py` (`run_audio_inference`, lines 241–288):
  If `use_cache=False` or cache JSONL is absent, it calls `pipeline.process_file(wav_path)`, which opens and reads `.wav` bytes into memory for STFT computation.

---

## 3. Complete Filesystem Side-Effect Mapping

Executing `scripts/run_real_world_experiments.py` writes to the following repository locations:

| Target Directory / File | Written Artifacts | Modification Type | Impact / Risk |
| :--- | :--- | :--- | :--- |
| `data/processed/layer_b/audio/` | `camera_front.wav`, `camera_back.wav` | Creates / Overwrites | Modifies data tree; demuxes raw media. |
| `results/experiments/cache/` | `*_vision.jsonl`, `*_audio.jsonl` | Creates / Overwrites | Writes unverified inference cache files. |
| `results/experiments/{B0..B7}/` | `summary.json`, `single_events.json` | **Overwrites** | Overwrites diagnostic results for 17 scenario runs. |
| `results/experiments/B4/timelines/` | `{event_id}_timeline.json`, `.csv` | Creates / Overwrites | Writes 27 timeline files. |
| `results/experiments/statistical_analysis/` | `comprehensive_statistics.json` | **Overwrites** | Generates unapproved paired statistics and Wilson CIs. |
| `results/experiments/figures/` | `fig01_*.png` through `fig20_*.png` | Overwrites 20 figures | Modifies results directory with 300 DPI plots. |
| `results/experiments/tables/` | `table01_*.md`, `.csv`, `.tex` (12 tables) | Overwrites 36 files | Modifies results directory with formatted tables. |
| `docs/REAL_WORLD_EXPERIMENT_REPORT.md` | **Markdown Research Report** | **DIRECT OVERWRITE** | Overwrites documentation file at lines 234–236, 393. |

Executing `scripts/run_phase5_full_inference.py` writes:
- `data/predictions/phase5_raw/{cohort}_{event_id}_*.jsonl` (raw prediction streams).
- `data/simulations/phase5_{B0,B1,B2,Back_Independent}/` (state-machine simulation steps).
- `data/manifests/phase5_inference_manifest.json` (summary manifest).

---

## 4. Governance & Safeguard Analysis

### 4.1 Present Governance Checks
The following checks are statically implemented in `scripts/run_real_world_experiments.py`:
1. **Checkpoint Immutability:** Verifies YOLO and Audio V3 SHA-256 hashes against frozen constants (`run_all_leakage_checks`, line 66).
2. **Runtime Parameter Freeze:** Verifies 16 frozen parameters against `configs/frozen_experiment_v1.yaml`.
3. **Historical Duplicate Exclusion:** Line 81 explicitly skips `event_historical_duplicate_010`.
4. **Audio Safety Role Invariant:** `layer_b_processor.py` (line 280) asserts `r.metadata.get("audio_safety_role") == "supporting_only"`.

### 4.2 Missing & Bypassed Governance Checks
The following mandatory governance controls are entirely absent:
1. **No Media Access Hold Check:** Zero verification that source media access is permitted.
2. **Split Contract Bypass:** Discovers all 27 events from raw directory tree and evaluates them in a single batch without verifying `data/splits/phase12_event_split_decision.json`.
3. **Ground-Truth Authorization Bypass:** Does not load `data/ground_truth/phase12_ground_truth.json` or verify `ADJ-AUTH` approval status.
4. **Cross-Camera Synchronization Bypass:** In line 394 of `layer_b_processor.py`:
   `all_v_records = v1_records + v2_records`
   `sync_aligner` is passed as `None`. In `build_multimodal_frames()` (lines 301–316), this triggers a fatal `TimingIntegrityError` unless `allow_unverified_zero_offset: true` is set in config.

---

## 5. Why Cache-Only Configuration Is Insufficient for Safety

A superficial attempt to make `run_real_world_experiments.py` safe by passing `--use-cache` (or omitting `--no-cache`) is **statically insufficient**:

1. **Silent Fallthrough Architecture:**
   In `layer_b_processor.py` (lines 184–200), the condition is:
   ```python
   if use_cache and cache_file.exists():
       return records
   # If cache_file does not exist, IT SILENTLY PROCEEDS TO OPEN THE RAW VIDEO!
   ```
   If even a single cache file out of the 54 streams is missing, corrupted, or misspelled, the code does not raise an exception; it silently opens `camera_front.mov` or `camera_back.mov` and decodes video frames.
2. **Hardcoded Overrides in Other Entrypoints:**
   In `scripts/run_phase5_full_inference.py` (lines 324, 343, 361), `use_cache=False` is hardcoded in the function call arguments, ignoring any global cache configuration.
3. **Destructive Side Effects on Documentation:**
   Even if every cache file existed, running `run_real_world_experiments.py` directly overwrites `docs/REAL_WORLD_EXPERIMENT_REPORT.md` and replaces results in `results/experiments/`.

---

## 6. Pre-Requisites for Safe Future Execution

Before any execution of diagnostic or inference scripts can be authorized:
1. **Fail-Closed Cache Architecture:**
   The ingestion functions (`run_vision_inference`, `run_audio_inference`, `extract_audio`) must be modified or wrapped in a dedicated cache-only replay interface that strictly enforces:
   ```python
   if not cache_file.exists():
       raise CacheMissingError(f"Cache missing for {event_id}. Falling back to raw media is strictly prohibited.")
   ```
2. **Media-Path Disconnection:**
   The replay harness must accept pre-computed prediction JSONLs directly, with no reference to `.mov` or `.wav` file paths in its input schemas.
3. **Isolated Output Directory:**
   Outputs must be directed to an isolated, non-authoritative scratch directory (e.g., `results/scratch/diagnostic_run/`) rather than overwriting tracked reports or official results.
4. **Formal Governance Ratification:**
   The researcher must formally resolve the Media Access Hold and issue explicit execution authorization (`EVAL-AUTH`).
