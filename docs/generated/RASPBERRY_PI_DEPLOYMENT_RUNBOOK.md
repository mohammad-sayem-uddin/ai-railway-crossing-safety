# Raspberry Pi 4B / 5 Installation, Export & Edge Benchmark Runbook

> **Physical Hardware Boundary:** `physical_raspberry_pi_tested = false` on the development host (`Darwin arm64`, Apple M1). Every physical Raspberry Pi figure below marked **`ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE`** is an unmeasured scaling estimate (`5.5×` for Pi 4B Cortex-A72; `2.4×` for Pi 5 Cortex-A76), **NOT** a physical SBC measurement. Physical deployment claims MUST only be updated after running [`scripts/rpi_edge_benchmark.py`](../../scripts/rpi_edge_benchmark.py) directly on Raspberry Pi hardware where `/proc/device-tree/model` confirms `"Raspberry Pi"`.

---

## 1. Target Operating System & Python 3.11+ Environment Setup

Recommended OS: **Raspberry Pi OS 64-bit (`aarch64`, Debian 12 Bookworm or Debian 13 Trixie)**. Ensure swap (`>= 2048 MB`) is enabled on 2–4 GB RAM boards before tracing TorchScript bundles.

```bash
sudo apt-get update && sudo apt-get install -y --no-install-recommends \
  python3.11 python3.11-venv python3.11-dev build-essential git \
  ffmpeg libavcodec-dev libavformat-dev libswscale-dev \
  libgl1 libglib2.0-0 libgomp1 v4l-utils libcamera-apps

python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

### Verified Python Runtime Stack (`requirements.lock` Reference)
- `torch==2.13.0` (`aarch64` CPU wheel)
- `ultralytics==8.4.121`
- `opencv-python==5.0.0.93` (or `opencv-python-headless==5.0.0.93` on headless Raspberry Pi OS without X11)
- `av==18.1.0` (`PyAV` for PTS-ordered decode and container display rotation extraction)
- `numpy==2.4.6`
- Install local package into `.venv`:
```bash
PYTHONPATH=src .venv/bin/pip install --no-deps -e .
```
- **Note on ONNX Runtime:** `onnx` and `onnxruntime` are NOT installed in [`requirements.lock`](../../requirements.lock). The verified edge format in this repository is **TorchScript (`.ts`)** plus **stripped FP16 weights (`.pt`)**.

---

## 2. Camera Input & Mandatory Display-Rotation Normalization

Mission 44 (`db40305`) documented that portrait/side-mounted `.mov` streams carried container `DISPLAYMATRIX` rotations (`±90°` on `44/54` Layer-B sources) causing severe `YOLOv8n` recall losses when decoded unrotated. On Raspberry Pi cameras:

1. **CSI (`libcamera`/`rpicam-vid`), USB UVC (`V4L2` `/dev/video*`), or RTSP Streams:** Fix sensor rotation in camera/stream config where supported, and normalize every decoded BGR frame through [`normalize_orthogonal_rotation`](../../src/railway_detection/vision/video.py) and [`apply_display_rotation`](../../src/railway_detection/vision/video.py) (`orthogonal_display_matrix_rotation_v1`) before inference.
2. **In-Memory OpenCV Preprocess Timing ([`pi_telemetry.py`](../../src/railway_detection/optimization/pi_telemetry.py)):** Measures `1920×1080` JPEG decode + `cv2.ROTATE_90_CLOCKWISE` + bilinear resize to `416×416` (`SYNTHETIC_ONLY`) so decode/rotation CPU overhead is accounted for explicitly alongside model forward latency (`mean 16.980 ms`, `p50 16.994 ms`, `p95 17.029 ms` measured on Apple M1 host).

---

## 3. Stripped FP16 & TorchScript Edge Bundle Export

[`scripts/rpi_edge_benchmark.py`](../../scripts/rpi_edge_benchmark.py) deterministically exports edge bundles (`--export-dir`, defaulting to a temp dir) with `max_abs_diff = 0.0` verified vs eager FP32 on CPU:

- **Vision YOLOv8n Stripped FP16:** `best.pt` (`24,493,159 B` with optimizer + EMA states) -> `6,154,766 B` (`-74.87%`)
- **Vision YOLOv8n TorchScript `416px` (`yolo_v8n_416_ts.pt`):** `12,603,058 B` (`max_abs_diff = 0.0`)
- **Vision YOLOv8n TorchScript `320px` (`yolo_v8n_320_ts.pt`):** `12,578,470 B` (`max_abs_diff = 0.0`)
- **Audio `CompactTrainHornCNN` V3 TorchScript (`audio_cnn_ts.pt`):** `131,596 B` (`max_abs_diff = 0.0`)

---

## 4. Running the Physical Raspberry Pi Benchmark & Thread Control

[`scripts/rpi_edge_benchmark.py`](../../scripts/rpi_edge_benchmark.py) internally sweeps `1`, `2`, and `4` `torch.set_num_threads(...)` settings while protecting `data/`, `configs/`, `models/`, `experiments/`, `src/`, and `tests/`. On physical Raspberry Pi hardware:

```bash
# Inspect active cpufreq governor (optionally set 'performance' during bench)
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
# echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONPATH=src:. .venv/bin/python scripts/rpi_edge_benchmark.py \
  --iters 15 \
  --export-dir /tmp/edge_bundles \
  --output /tmp/rpi_hardware_benchmark.json
```

**Important:** Write physical Pi results to a hardware-specific path (`/tmp/rpi_hardware_benchmark.json` or a new dedicated filename), NOT over [`host_edge_scaling_benchmark.json`](../../results/exploratory_v2/optimization_and_stress/host_edge_scaling_benchmark.json), and confirm `"physical_raspberry_pi_tested": true` (`hardware.device_tree_model` populated).

---

## 5. Telemetry Capture: Peak RSS (`VmHWM`) & SoC Thermal Monitoring

[`pi_telemetry.py`](../../src/railway_detection/optimization/pi_telemetry.py) records `telemetry_pre` and `telemetry_post` around the `1/2/4`-thread benchmark:
- **`vmhwm_mb` (`/proc/self/status` `VmHWM`):** Linux high-water mark RSS in MB (also combined via `max(...)` with `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` on Linux).
- **`soc_temp_c` (`/sys/class/thermal/thermal_zone0/temp`):** Pre- and post-sweep SoC temperature (`deg C`); inspect thermal rise to verify passive/active cooling prevents `>= 80–85 °C` Raspberry Pi thermal throttling.
- **`cpu_governor` (`/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor`):** Captures active frequency scaling policy.

---

## 6. Measured Host Baseline (`rpi-edge-benchmark/1.1`) vs Analytical Projections

| Workload | Measured Apple M1 Host (`15` iters TS / `20` audio; `physical_raspberry_pi_tested=false`) | Analytical Pi 5 (`2.4×`, **UNMEASURED**) | Analytical Pi 4B (`5.5×`, **UNMEASURED**) |
|---|---|---|---|
| **Vision `416px` TS (`1T / 2T / 4T`)** | `28.025 / 20.921 / 16.839 ms` (`4T`: **`59.39 FPS`**, p50 `16.515`, p95 `18.276`) | ~`40.4 ms` (`4T`, ~`24.7 FPS`) | ~`92.6 ms` (`4T`, ~`10.8 FPS`) |
| **Vision `320px` TS (`1T / 2T / 4T`)** | `17.150 / 13.537 / 11.523 ms` (`4T`: **`86.78 FPS`**, p50 `11.351`, p95 `12.268`) | ~`27.7 ms` (`4T`, ~`36.2 FPS`) | ~`63.4 ms` (`4T`, ~`15.8 FPS`) |
| **OpenCV `1080p->Rotate90->416px`** | Mean `16.980 ms` (`p50 16.994`, `p95 17.029`) | Unmeasured on target ARM | Unmeasured on target ARM |
| **Audio `log_mel + TS` (`4T`)** | `0.405 + 0.384 = 0.789 ms/window` (`Audio TS 2,602.27 FPS_eq`) | ~`1.9 ms/win` | ~`4.3 ms/win` |
| **V3 FSM + Gate (`Exp P`)** | `0.0381–0.0391 ms/tick` (`> 25,000 Hz`) | `< 0.15 ms/tick` | `< 0.30 ms/tick` |
| **Peak Process RSS** | `452.45 MB` (`rpi-edge-benchmark/1.1` incl. OpenCV 1080p prep; `Exp P` eager `491.52 MB`) | Expected `350–500 MB` | Expected `350–500 MB` |
| **Duty-Cycle Daily Frames (`Exp P`)** | `11,760–29,760/d` (`10–40` trains/d) vs `864,000/d` continuous (`-96.56%` to `-98.64%`) | `0.012–0.024` avg cores (`416px`) | `0.027–0.054` avg cores (`416px`) |

---

## 7. Expected Output JSON Schema (`rpi-edge-benchmark/1.1`)

```json
{
  "schema_version": "rpi-edge-benchmark/1.1",
  "input_classification": "SYNTHETIC_ONLY",
  "hardware": {
    "system": "Linux",
    "release": "...",
    "machine": "aarch64",
    "python_version": "3.11.x",
    "torch_version": "2.13.0",
    "device_tree_model": "Raspberry Pi 4 Model B ...",
    "is_physical_raspberry_pi": true,
    "cpu_count": 4,
    "os": "Linux",
    "platform": "Linux-..."
  },
  "physical_raspberry_pi_tested": true,
  "peak_process_rss_mb": 452.5,
  "telemetry_pre": {"vmhwm_mb": 340.0, "soc_temp_c": 48.2, "cpu_governor": "performance"},
  "telemetry_post": {"vmhwm_mb": 452.5, "soc_temp_c": 57.1, "cpu_governor": "performance"},
  "synthetic_opencv_preprocess_416px": {
    "available": true,
    "input_classification": "SYNTHETIC_ONLY",
    "src_shape": [1920, 1080],
    "rotation_applied": "ROTATE_90_CLOCKWISE",
    "dst_size": 416,
    "n_iters": 10,
    "mean_ms": 0.0,
    "p50_ms": 0.0,
    "p95_ms": 0.0
  },
  "exported_bundles": {
    "audio_torchscript_bytes": 131596,
    "audio_torchscript_max_abs_diff": 0.0,
    "vision_320_torchscript_bytes": 12578470,
    "vision_320_torchscript_max_abs_diff": 0.0,
    "vision_416_torchscript_bytes": 12603058,
    "vision_416_torchscript_max_abs_diff": 0.0,
    "vision_stripped_fp16_bytes": 6154766
  },
  "thread_scaling_ms": {
    "threads_1": {"audio_ts_ms": {}, "log_mel_ms": {}, "vision_320_ts_ms": {}, "vision_416_ts_ms": {}},
    "threads_2": {"audio_ts_ms": {}, "log_mel_ms": {}, "vision_320_ts_ms": {}, "vision_416_ts_ms": {}},
    "threads_4": {"audio_ts_ms": {}, "log_mel_ms": {}, "vision_320_ts_ms": {}, "vision_416_ts_ms": {}}
  }
}
```
