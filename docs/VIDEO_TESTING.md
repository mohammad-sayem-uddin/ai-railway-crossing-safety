# Railway Crossing Train Detection — Video Testing & Demonstration Tool

**Document Version:** 1.0.0  
**Authority:** AI Railway Crossing Safety Research Project  
**Implementation Modules:** [`src/railway_detection/demo/video_demo.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/demo/video_demo.py) and [`scripts/demo_video.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/demo_video.py)

---

## 1. Overview & Purpose
The Video Testing / Demo Tool is an engineering utility designed to test trained YOLO object detection models on single video files (`.mp4`, `.mov`, `.avi`, `.mkv`). 

It performs frame-by-frame inference, draws high-contrast visual bounding boxes with canonical class labels, displays an interactive progress bar in the terminal, renders an annotated output MP4 video, and exports structured detection summaries (`summary.json` and `summary.md`).

> [!IMPORTANT]
> **Research & Validation Boundary**  
> This tool is strictly an engineering visual verification and demonstration utility. The generated statistics represent raw detection frequencies and confidence distributions across the video frames. **They do not compute or claim ground-truth metrics (such as mAP, precision, recall, or F1)** because arbitrary demo videos may lack ground-truth annotations.

---

## 2. Canonical Classes & Normalization
The demo tool always maps and renders the three canonical train viewpoint classes:

| Class ID | Canonical Name | Visualization Color (BGR) | Semantic Role |
|:---:|:---:|:---:|:---|
| `0` | **`FRONT`** | Amber / Orange (`0, 140, 255`) | Approaching locomotive / leading train cabin |
| `1` | **`REAR`** | Magenta / Purple (`180, 0, 220`) | Departing train tail / rear cabin |
| `2` | **`SIDE`** | Azure / Sky Blue (`255, 180, 0`) | Continuous train carriages / crossing passage |

*Note: The original Roboflow Dataset V1 contained the legacy typo `"rare"` for class 1; the demo tool automatically normalizes all occurrences to canonical **`rear`**.*

---

## 3. Quick Start & Execution

### Basic Interactive Run
Run the tool from the repository root without arguments:
```bash
python demo_video.py
```
*(or via `python scripts/demo_video.py`)*

When run without the `--input` argument, the tool automatically attempts:
1. **Option A (Native File Dialog):** On macOS, launches a native Finder file picker to select a video.
2. **Option B (Terminal Prompt):** If the file dialog is cancelled or unavailable (e.g. headless/remote), prompts interactively:
   ```text
   ============================================================
   AI RAILWAY CROSSING SAFETY — VIDEO SELECTOR
   ============================================================
   Supported formats: .avi, .mkv, .mov, .mp4
   Enter the path to the video file: path/to/sample_video.mp4
   ```

---

## 4. Command-Line Options

```text
usage: demo_video [-h] [-i INPUT_VIDEO] [-m MODEL_PATH] [-o OUTPUT_DIR]
                  [-c CONF_THRESHOLD] [--iou IOU_THRESHOLD]
                  [-d {auto,mps,cuda,cpu}] [-p] [-t]

AI Railway Crossing Safety — Video Inference & Demonstration Tool

options:
  -h, --help            show this help message and exit
  -i, --input INPUT_VIDEO
                        Path to input video (.mp4, .mov, .avi, .mkv). If omitted,
                        opens native picker or terminal prompt. (default: None)
  -m, --model MODEL_PATH
                        Path to trained YOLO weights file (.pt).
                        (default: experiments/vision/39f402dfe460/checkpoints/weights/best.pt)
  -o, --output-dir OUTPUT_DIR
                        Base directory for output runs (defaults to
                        outputs/video_tests/<name>_<timestamp>). (default: None)
  -c, --conf CONF_THRESHOLD
                        Confidence threshold for bounding box detection. (default: 0.25)
  --iou IOU_THRESHOLD   NMS IoU threshold. (default: 0.45)
  -d, --device {auto,mps,cuda,cpu}
                        Inference compute device. (default: auto)
  -p, --preview         Show live graphical preview window during processing
                        (press Q to stop early). (default: False)
  -t, --temporal        Apply optional temporal evidence smoothing buffer across
                        consecutive frames. (default: False)
```

---

## 5. Usage Examples

### 1. Run on a Specific Video File
```bash
python demo_video.py --input /path/to/train_passage.mp4
```

### 2. Run with Hardware Acceleration (Apple Silicon GPU)
```bash
python demo_video.py --input sample_video.mp4 --device mps
```

### 3. Use a Custom Trained Model Checkpoint
```bash
python demo_video.py \
    --input sample_video.mp4 \
    --model experiments/vision/39f402dfe460/checkpoints/weights/best.pt
```

### 4. Enable Live Graphical Preview (with early stop via 'Q')
```bash
python demo_video.py --input sample_video.mp4 --preview
```

### 5. Enable Optional Temporal Evidence Smoothing
```bash
python demo_video.py --input sample_video.mp4 --temporal
```

### 6. Adjust Detection Sensitivity
```bash
python demo_video.py --input sample_video.mp4 --conf 0.40 --iou 0.50
```

---

## 6. Output Artifacts

For each run, a unique timestamped directory is created under `outputs/video_tests/`:

```text
outputs/video_tests/
└── <video_stem>_<YYYYMMDD_HHMMSS>/
    ├── processed_video.mp4     # Annotated MP4 video with bounding boxes & badge labels
    ├── summary.json            # Machine-readable inference statistics
    └── summary.md              # Human-readable Markdown summary report
```

### Sample `summary.md` Output
```markdown
# Railway Crossing Video Inference Summary

> **Research & Validation Notice**  
> These results are inference statistics only and do not represent ground-truth evaluation metrics.

## 1. Video & Environment Metadata
- **Input Video:** `/data/videos/train_test.mp4`
- **Output Video:** `/outputs/video_tests/train_test_20260818_170000/processed_video.mp4`
- **Model Path:** `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`
- **Model Name:** `best.pt`
- **Compute Device Used:** `mps`
- **Resolution:** 1920 × 1080
- **Native Video FPS:** 30.00
- **Total Frames in Video:** 900
- **Successfully Processed Frames:** 900
- **Processing Duration:** 18.42 seconds
- **Average Inference Throughput:** 48.86 FPS
- **Confidence Threshold:** 0.25
- **IoU Threshold:** 0.45
- **Temporal Smoothing:** Disabled

## 2. Detection Overview
- **Total Detected Instances:** 1240
- **Frames with At Least One Detection:** 720 (80.0%)
- **Frames with No Detection:** 180

## 3. Class-Wise Detection Statistics

| Class | Frames Present | Total Detections | Avg Confidence | Max Confidence |
|:---:|:---:|:---:|:---:|:---:|
| **FRONT** | 180 | 185 | 0.9120 | 0.9650 |
| **REAR** | 120 | 120 | 0.9450 | 0.9820 |
| **SIDE** | 450 | 935 | 0.8870 | 0.9740 |

## 4. Audio Preservation Note
Processed output video is encoded via OpenCV MP4 container. Audio tracks (if present in source) are omitted during visual frame reconstruction.
```

---

## 7. Architecture & Integration
The video demo tool integrates directly with the existing codebase:
- Reuses [`Ultralytics YOLO`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/vision/yolo_adapter.py) backend.
- Reuses [`TemporalEvidenceBuffer`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/vision/temporal.py) and [`EvidenceRecord`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/evidence.py) when `--temporal` is specified.
- Reuses structured logging from [`railway_detection.utils.logging`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/utils/logging.py).
- Completely decoupled from the training, dataset splitting, and experiment registry orchestration pipelines.
