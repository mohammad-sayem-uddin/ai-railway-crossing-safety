# Raspberry Pi & Edge Compute Readiness Report (`Exp P` + Standalone Thread Scaling)

**Primary Benchmark Evidence:** [`exp_p_cpu_edge_benchmark.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/exp_p_cpu_edge_benchmark.json) & [`host_edge_scaling_benchmark.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/host_edge_scaling_benchmark.json) (`SYNTHETIC_ONLY` tensors, produced by [`rpi_edge_benchmark.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/rpi_edge_benchmark.py))  
**Installation Architecture Reference:** [`REAL_WORLD_INSTALLATION_CONCEPT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/REAL_WORLD_INSTALLATION_CONCEPT.md)  
**Visual Breakdown:** [`fig13_cpu_edge_benchmark_and_duty_cycle.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/figures/fig13_cpu_edge_benchmark_and_duty_cycle.png)  
**Hardware Verification Disclosure:** **`physical_raspberry_pi_tested = false`**. All inference latencies and RSS were measured on an **Apple M1 CPU (`arm64`, `macOS-26.6.2`, `torch 2.13.0`, `python 3.11.15`)**. Raspberry Pi 4B / Pi 5 figures remain explicitly labeled **`ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE`** until `scripts/rpi_edge_benchmark.py` is executed directly on physical SBC hardware.

---

## 1. Latest Measured Host Stage Benchmarks (`Apple M1`, `SYNTHETIC_ONLY`)

### 1.1 Model Size & Standalone Edge Bundle Export
- **Vision Checkpoint Stripping (`exp_p`):** Raw training checkpoint is **`24,493,159 B` (`24.49 MB`)**. Stripping optimizer/EMA reduces disk size to **`6,145,232 B` (`6.15 MB`) in FP16 (`-74.91%`)** or **`12,188,432 B` (`12.19 MB`) in FP32**.
- **Standalone TorchScript & Stripped Bundle Sizes (`rpi_edge_benchmark.py`):** `vision_416_torchscript = 12,602,738 B` (`max_abs_diff = 0.0`), `vision_320_torchscript = 12,578,214 B` (`max_abs_diff = 0.0`), `vision_stripped_fp16 = 6,154,766 B`, `audio_torchscript = 131,596 B` (`max_abs_diff = 0.0`).
- **Peak Process Memory:** `364.67 MB` (standalone TorchScript benchmark) to `504.30 MB` (full ultralytics + quantization suite).

### 1.2 Measured Per-Stage Latency & Thread Scaling (`1 / 2 / 4` Threads)

Latest `Exp P` (`4` threads, `exp_p_cpu_edge_benchmark.json`) + standalone `rpi_edge_benchmark.py` (`host_edge_scaling_benchmark.json`):
- **Ultralytics `YOLO.predict` E2E (`Exp P`):** `640px` mean **`44.557 ms` (`p95=47.255 ms`, `22.44 FPS`)** -> `416px` mean **`21.597 ms` (`p95=22.843 ms`, `46.30 FPS`, `2.06×` speedup)**; Audio `log_mel` (`0.410 ms`) + `CNN TS` (`0.468 ms`) = `0.878 ms/window`; `V3 FSM` = `4.613 ms / 121 ticks` (**`0.0381 ms/tick`, `26,247 Hz`**).
- **Standalone TorchScript CPU Thread Scaling (`host_edge_scaling_benchmark.json`):**

| Threads | Vision `416px` TS (`mean_ms` / `FPS`) | Vision `320px` TS (`mean_ms` / `FPS`) | Audio `TS` (`mean_ms` / `win/s`) | `log_mel` (`mean_ms`) |
|---|---|---|---|---|
| `1` thread | `28.790 ms` (`34.73 FPS`) | `17.860 ms` (`55.99 FPS`) | `0.456 ms` (`2,193.5/s`) | `0.430 ms` |
| `2` threads | `20.729 ms` (`48.24 FPS`) | `13.402 ms` (`74.62 FPS`) | `0.414 ms` (`2,414.3/s`) | `0.414 ms` |
| **`4` threads** | **`17.361 ms` (`57.60 FPS`)** | **`11.787 ms` (`84.84 FPS`)** | **`0.388 ms` (`2,579.0/s`)** | `0.422 ms` |

*(Note: Dynamic INT8 Linear on the tiny 25.7k-param Audio CNN adds quantization overhead without speeding up over TorchScript `0.471 ms` while introducing `0.0601` probability shift; TorchScript FP32 is strictly preferred for Audio. `onnx` / `onnxruntime` are not installed in `.venv`.)*

---

## 2. Continuous `24/7` vs Event-Triggered Duty-Cycle Analysis (`ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE`)

Running two `640px` vision cameras (`front` + `back`) continuously at `5 FPS` requires `10 inferences/s = 864,000 frames/day`. Applying conservative SBC single-core slowdown factors (`5.5×` Apple M1 for **Raspberry Pi 4B Cortex-A72**; `2.4×` for **Raspberry Pi 5 Cortex-A76**):

- **Event-Triggered Architecture:** Run continuous `0.878 ms` audio / low-cost external wakeup (`2 Hz`) + `0.033 Hz` (`30 s`) health watchdog frames (`5,760 frames/day`), switching both cameras to `5 FPS` only for `60 s` around active events (`600 frames/train`).

| Resolution | Daily Regime | Vision Frames/Day | Reduction | RPi 4B Projected Vision (`ms`) | RPi 4B Projected Cores Used | RPi 5 Projected Cores Used |
|---|---|---|---|---|---|---|
| `640px` E2E | Continuous `24/7` (`5 FPS`) | `864,000` | baseline | `245.06 ms` *(cannot hit 10 FPS)* | **`2.4603` / 4 cores** *(thermally heavy)* | `1.0736` / 4 cores |
| `640px` E2E | Event-Triggered (`10 / 20 / 40` trains/d) | `11,760 / 17,760 / 29,760` | `-98.64%` to `-96.56%` | `245.06 ms` *(active ~4.1 FPS/cam cap)* | `0.0430 / 0.0600 / 0.0941` cores | `0.0188 / 0.0262 / 0.0410` cores |
| **`416px` E2E** | Continuous `24/7` (`5 FPS`) | `864,000` | baseline | `118.78 ms` *(misses 100 ms)* | `1.1975` / 4 cores | `0.5225` / 4 cores |
| **`416px` E2E** | **Event-Triggered (`10 / 20 / 40` trains/d)** | **`11,760 / 17,760 / 29,760`** | **`-98.64%` to `-96.56%`** | **`118.78 ms` (`~8.4 Hz` single-stream, `~4.2 Hz`/cam dual)** | **`0.0258 / 0.0341 / 0.0506` cores** | **`0.0113 / 0.0149 / 0.0221` cores** |

---

## 3. Edge Deployment Readiness Verdict & Remaining SBC Hardware Gaps

1. **Verdict:** **Software stack ready for host/prototype CPU; Raspberry Pi 4B requires `416px` (or `ONNX`/`NCNN` `INT8` export) + event-triggered gating + external upstream approach wakeup.** Continuous `24/7` dual-camera `640px` inference is projected to saturate `~75%` of all four Pi 4B cores (`3.02` cores) and cannot meet a `100 ms` dual-camera budget without NPU/Coral TPU or NCNN/ONNX INT8 compilation.
2. **Unmeasured Physical Hardware Items (`NOT OBTAINED`):** Physical RPi 4B/5 thermal throttling under `40°C` Bangladesh roadside enclosure conditions, DC solar/battery wattage (`W`), camera RTSP/USB decode jitter overhead, and physical fail-closed relay watchdog circuit response.
3. **Important Upstream Wakeup Caveat:** Because road horns cause false audio triggers (`Exp O`) and optical visibility attenuation can miss low-confidence trains (`Exp Q`), an event-triggered camera wakeup should pair acoustic monitoring with an ultra-low-power **upstream vibration / Doppler radar / magnetic rail sensor** rather than relying solely on acoustic waking or `30 s` camera polls.
