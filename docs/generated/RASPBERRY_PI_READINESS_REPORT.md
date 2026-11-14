# Raspberry Pi & Edge Compute Readiness Report (`Exp P`)

**Primary Benchmark Evidence:** [`exp_p_cpu_edge_benchmark.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/optimization_and_stress/exp_p_cpu_edge_benchmark.json) (`SYNTHETIC_ONLY` tensors)  
**Installation Architecture Reference:** [`REAL_WORLD_INSTALLATION_CONCEPT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/REAL_WORLD_INSTALLATION_CONCEPT.md)  
**Visual Breakdown:** [`fig13_cpu_edge_benchmark_and_duty_cycle.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/figures/fig13_cpu_edge_benchmark_and_duty_cycle.png)  
**Hardware Verification Disclosure:** **`physical_raspberry_pi_tested = false`**. All inference latencies and RSS were measured on an **Apple M1 CPU (`arm64`, `macOS-26.6.2`, `torch 2.13.0`, `4` threads)**. Raspberry Pi 4B / Pi 5 figures are explicitly labeled **`ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE`**.

---

## 1. Measured Host Stage Benchmarks (`Apple M1`, `4` Threads, `SYNTHETIC_ONLY`)

### 1.1 Model Size & Weight Optimization
- **Vision Checkpoint Stripping ([`best.pt`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/vision/39f402dfe460/checkpoints/weights/best.pt)):** Raw training checkpoint is **`24,493,159 B` (`24.49 MB`)** because it bundles `optimizer` and `ema` states (`3,011,433` parameters). Stripping optimizer/EMA reduces disk size to **`6,145,232 B` (`6.15 MB`) in FP16 (`-74.91%`)** or **`12,188,432 B` (`12.19 MB`) in FP32**.
- **Audio V3 Checkpoint ([`best.pt`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt)):** `329,497 B` raw; TorchScript FP32 **`134,358 B`**; dynamic INT8 Linear **`109,005 B`** (`25,697` module params).
- **Peak Process Memory:** **`491.52 MB` peak RSS** across combined Ultralytics/TorchScript/FSM execution (comfortably fits `2 GB` / `4 GB` / `8 GB` SBC RAM envelopes when not co-resident with heavy desktop UIs).

### 1.2 Measured Per-Stage Latency & Throughput

| Stage / Export Mode | Input Size / Workload | Mean Latency (`ms`) | p50 (`ms`) | p95 (`ms`) | Throughput | Numerical Drift |
|---|---|---|---|---|---|---|
| `YOLOv8n` Eager FP32 forward | `1x3x640x640` | `39.938` | `39.607` | `42.780` | `25.04 FPS` | baseline |
| `YOLOv8n` TorchScript FP32 | `1x3x640x640` | `38.603` | `37.630` | `43.765` | `25.90 FPS` | `0.0` |
| `YOLOv8n` Eager FP32 forward | `1x3x416x416` | `19.141` | `18.860` | `20.243` | `52.24 FPS` | baseline |
| `YOLOv8n` TorchScript FP32 | `1x3x416x416` | `18.253` | `17.321` | `22.900` | `54.79 FPS` | `0.0` |
| `YOLOv8n` TorchScript FP32 | `1x3x320x320` | `13.155` | `12.265` | `16.595` | `76.02 FPS` | `0.0` |
| **Ultralytics `YOLO.predict` E2E** | **`640px` numpy RGB** | **`54.658`** | `50.017` | `72.785` | **`18.30 FPS`** | — |
| **Ultralytics `YOLO.predict` E2E** | **`416px` numpy RGB** | **`23.605`** | `22.409` | `28.017` | **`42.36 FPS`** | **`2.32×` E2E speedup** |
| Audio `log_mel_1s_numpy` | `1 s @ 16 kHz -> [64, 61]` | `0.410` | `0.406` | `0.446` | `2,436 win/s` | exact |
| Audio `CNN` TorchScript FP32 | `[1, 1, 64, 61]` | `0.471` | `0.472` | `0.527` | `2,123 win/s` | `0.0` |
| Audio `CNN` Dynamic INT8 (`Linear`) | `[1, 1, 64, 61]` (`qnnpack`) | `0.563` | `0.575` | `0.660` | `1,776 win/s` | `0.0601` |
| **V3 FSM + Collector + Gate** | `121`-tick closed loop | **`4.737` total (`0.0391/tick`)** | `4.704` | `4.919` | **`25,575 Hz`** | deterministic |

*(Note: Dynamic INT8 Linear on the tiny 25.7k-param Audio CNN adds quantization overhead without speeding up over TorchScript `0.471 ms` while introducing `0.0601` probability shift; TorchScript FP32 is strictly preferred for Audio. `onnx` / `onnxruntime` are not installed in `.venv`.)*

---

## 2. Continuous `24/7` vs Event-Triggered Duty-Cycle Analysis (`ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE`)

Running two `640px` vision cameras (`front` + `back`) continuously at `5 FPS` requires `10 inferences/s = 864,000 frames/day`. Applying conservative SBC single-core slowdown factors (`5.5×` Apple M1 for **Raspberry Pi 4B Cortex-A72**; `2.4×` for **Raspberry Pi 5 Cortex-A76**):

- **Event-Triggered Architecture:** Run continuous `0.881 ms` audio / low-cost external wakeup (`2 Hz`) + `0.033 Hz` (`30 s`) health watchdog frames (`5,760 frames/day`), switching both cameras to `5 FPS` only for `60 s` around active events (`600 frames/train`).

| Resolution | Daily Regime | Vision Frames/Day | Reduction | RPi 4B Projected Vision (`ms`) | RPi 4B Projected Cores Used | RPi 5 Projected Cores Used |
|---|---|---|---|---|---|---|
| `640px` E2E | Continuous `24/7` (`5 FPS`) | `864,000` | baseline | `300.62 ms` *(cannot hit 10 FPS)* | **`3.0159` / 4 cores** *(thermally unsafe)* | `1.3160` / 4 cores |
| `640px` E2E | Event-Triggered (`10 / 20 / 40` trains/d) | `11,760 / 17,760 / 29,760` | `-98.64%` to `-96.56%` | `300.62 ms` *(active ~3.3 FPS/cam cap)* | `0.0506 / 0.0715 / 0.1132` cores | `0.0221 / 0.0312 / 0.0494` cores |
| **`416px` E2E** | Continuous `24/7` (`5 FPS`) | `864,000` | baseline | `129.83 ms` *(misses 100 ms)* | `1.3080` / 4 cores | `0.5707` / 4 cores |
| **`416px` E2E** | **Event-Triggered (`10 / 20 / 40` trains/d)** | **`11,760 / 17,760 / 29,760`** | **`-98.64%` to `-96.56%`** | **`129.83 ms` (`~7.7 Hz` single-stream, `~3.85 Hz`/cam dual)** | **`0.0274 / 0.0364 / 0.0544` cores** | **`0.0119 / 0.0159 / 0.0237` cores** |

---

## 3. Edge Deployment Readiness Verdict & Remaining SBC Hardware Gaps

1. **Verdict:** **Software stack ready for host/prototype CPU; Raspberry Pi 4B requires `416px` (or `ONNX`/`NCNN` `INT8` export) + event-triggered gating + external upstream approach wakeup.** Continuous `24/7` dual-camera `640px` inference is projected to saturate `~75%` of all four Pi 4B cores (`3.02` cores) and cannot meet a `100 ms` dual-camera budget without NPU/Coral TPU or NCNN/ONNX INT8 compilation.
2. **Unmeasured Physical Hardware Items (`NOT OBTAINED`):** Physical RPi 4B/5 thermal throttling under `40°C` Bangladesh roadside enclosure conditions, DC solar/battery wattage (`W`), camera RTSP/USB decode jitter overhead, and physical fail-closed relay watchdog circuit response.
3. **Important Upstream Wakeup Caveat:** Because road horns cause false audio triggers (`Exp O`) and optical visibility attenuation can miss low-confidence trains (`Exp Q`), an event-triggered camera wakeup should pair acoustic monitoring with an ultra-low-power **upstream vibration / Doppler radar / magnetic rail sensor** rather than relying solely on acoustic waking or `30 s` camera polls.
