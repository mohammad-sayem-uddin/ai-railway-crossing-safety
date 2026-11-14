# Reproducibility & Verification Receipt

**Verification Verdict:** **`verified_bit_identical = True`** across **`344/344` exploratory files** (`336` per-run trace JSONs + `8` summary/analysis JSON & CSV files; `0` mismatches, `0` missing/extra files; wall time `15.335 s`), verified by [`scripts/verify_exploratory_reproducibility.py`](../../../../scripts/verify_exploratory_reproducibility.py).

---

## 1. Environment & Repository Pin

- **Baseline Commit Prior to Deliverable Sync:** `c35d133f0a7e2b514cf5f34ef415342634b6c929` (branch `main`)
- **Python Environment:** Python `3.11` in repository `.venv` (`PYTHONPATH=src:.`)
- **Canonical Baseline Hash Preservation:** [`tests/unit/test_phase2_protocol_consolidation.py`](../../../../tests/unit/test_phase2_protocol_consolidation.py) verifies `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md` (`03444930...`) and frozen configs remain byte-identical.

---

## 2. Cryptographic Input & Code Bindings (`SHA-256`)

| Artifact | Verified SHA-256 |
|---|---|
| `configs/frozen_experiment_v1.yaml` | `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a` |
| `configs/decision_policy_v2_candidate.yaml` | `d90828b2ec37169d663c72ab7de7d86600728c0db170ebef3934b9565abaf07f` |
| `data/manifests/camera_sync_offsets_candidate.yaml` | `aaac453b7047ff5302592203114bdc4fc13de1d149669ad4590f074fa4110dcc` |
| `data/manifests/m3_multimodal_replay_manifest.json` | `3c720167ea06b67141beb7cf33bd02ce325db62a3e100819f8aa4ad213d5bbbb` |
| `src/railway_detection/fusion/decision_engine.py` | `3f5e3521e5b0b78e4ea2090855712cd36c0d91420ec125c09001382b1f0fcf40` |
| `src/railway_detection/fusion/decision_engine_v2_candidate.py` | `41063a75a001df291f45a00edb8bb3eaf9d1a3e6bf57fc4b3aa8f9db2ebef1a6` |
| `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` | `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` |
| `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` | `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782` |
| `scripts/exploratory_common.py` | `9cc842dd3829bcf9884fa13a50f789fa96ed31f7e3da477b1743b3eb11858e1c` |
| `scripts/run_exploratory_replay.py` | `6465c499e3a4637f1cc8def6b1f13d0d816b1fdecd6d16f5f29f061e59ccb70c` |
| `scripts/run_failure_injection_replays.py` | `68a8ea8bf077a4c7be2e117c831556143e55965803020ace8df65f2fdefb6289` |
| `scripts/evaluate_departure_reopening.py` | `ed18f1e4367edad59d9ffe3ea77274e3ad4259ed16325bb56d5546c070875d1c` |
| `scripts/compute_safety_metrics.py` | `9bbb3af3049e9142ae54991d414d79967025db57c7d040e0f6588e86eb814f03` |
| `scripts/compute_ablation_matrix.py` | `7d450e526a9110104f11c0d32019233a8546147b5fdc51094de2c22e798ef64b` |
| `scripts/verify_exploratory_reproducibility.py` | `3e1920df339fba6718f7793dd86815a50b10962cba8e13d6ade88e86eb814f03` |
| `scripts/generate_exploratory_figures.py` | `40dc4c82351bb740587427b14424d9a0dcf9e8caf339f7097395d2409216e858` |
| `scripts/build_final_research_deliverables.py` | `d7a0649b7928b3833dc870b7d74ffa6dcc0fa834769fa413bd438e7678ad5edd` |
| `tests/unit/test_exploratory_pipeline.py` | `2eea582048d65f41966403ee8888a0d16c706cad8d94d2b8a6b213cc40e19fde` |

See [`FILE_HASH_MANIFEST.sha256`](FILE_HASH_MANIFEST.sha256) for complete SHA-256 verification of all deliverables, figures, scripts, and analysis outputs (`shasum -a 256 -c docs/generated/final_research/FILE_HASH_MANIFEST.sha256`).

---

## 3. Verified Output File Hashes (`reproducibility_verification.json`)

- `replays/replay_summary.json`: `ce90cc13d91cefe1d1cef527b4a5311bbb16e4dfb4b81a371ce6aadada6c3be5`
- `failure_injection/stress_and_recovery_results.json`: `865725f549dfa67694ed67efa9d1687643acc1657881b13579e655a09283841b`
- `analysis/ablation_matrix.csv`: `9b130ffdbedeb87e03449af2eddc522aac320511c514776305b46c00bda43d47`
- `analysis/ablation_matrix.json`: `9c3005686716259444663c750dffe879c59ff0c8d25205016134ec404d3e95df`
- `analysis/departure_reopening_analysis.csv`: `1f8313f349c3aea91974bd97b40ec07c945a4f786a529fe3cdc871f1d304f487`
- `analysis/departure_reopening_analysis.json`: `8ba45d0ae828a09962344b745fc351e56a0979b2e7caf1c51da841189d1b1b62`
- `analysis/event_level_safety_metrics.csv`: `83de851ae1d215dc720cc22a8ea2fff214e8cc8b848076ac97e7c48a7c722f2d`
- `analysis/safety_metrics_summary.json`: `0763572cae37a811d2ca6a59a51746a0e7a3e7d2f00794a4834cc79e4f1fec7c`

---

## 4. Zero-Media Reproduction Command Sequence

```bash
PYTHONPATH=src:. .venv/bin/python scripts/verify_exploratory_reproducibility.py
.venv/bin/python scripts/generate_exploratory_figures.py
.venv/bin/python scripts/build_final_research_deliverables.py
PYTHONPATH=src:. .venv/bin/python -m pytest tests/unit/test_exploratory_pipeline.py tests/unit/test_access_classification_tools.py -q
```
