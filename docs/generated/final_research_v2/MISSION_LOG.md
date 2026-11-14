# Mission Log — Four-Layer Multimodal Railway Crossing Protection Prototype Completion

- **Baseline Commit:** `d1032756de80963130e1cbd3d2334cb32139b996` (`main`, matching `origin/main`)
- **Working Branch:** `exp/four-layer-completion`
- **Results Directory (New, Versioned):** `results/exploratory_v2/`
- **Documentation Directory (New, Versioned):** `docs/generated/final_research_v2/`
- **Preserved Prior Package:** `results/exploratory_execution/`, `docs/generated/final_research/`, frozen V1/V2 configs and engines, Mission 43/44 artifacts, and preexisting working-tree entries are kept intact.

## Phase Progress Checklist

| Phase | Scope | Status | Notes |
| --- | --- | --- | --- |
| Phase 0 | Branch setup, environment verification, SHA-256 baseline snapshot | COMPLETED | `BASELINE_SNAPSHOT.json` recorded; `AUTH-MEDIA-ACCESS.json` absent (`media_guard.py` preserved intact); Kaggle account `allfaz` has 0 Train Gate datasets |
| Phase 1A | Video decoder (`video.py`) + demo writer (`video_demo.py`) orientation hardening | COMPLETED | PyAV `np.rot90(..., k=(rotation // 90) % 4)` validated vs OpenCV `CAP_PROP_ORIENTATION_AUTO` across 7 orthogonal rotations + CPU `YOLOv8n`; `raw_coded_size` mocked-frame regression guard preserved |
| Phase 1B | Causal `MultimodalEvidenceCollector` + `OccupancyState` / `EvidenceStatus` semantics | COMPLETED | Causal default `allow_stale_detection_backfill=False`; explicit `allow_stale_detection_backfill=True` preserved in `exploratory_common.py` and `diagnostic_trace.py` for V1/V2 baselines |
| Phase 2 | V3 four-layer modules (`occupancy.py`, `rules_v3_four_layer.py`, `decision_engine_v3_four_layer.py`) | COMPLETED | Implemented Layers 1–4 + Occupancy gate + positive reopening + fail-safe state transitions across `state_machine.py`, `gate_model.py`, and `runner.py` |
| Phases 3–6 | Experiments A–N across real cohorts (`all27`, `sync11`, `audio23`, `no_train3`, `engine1`), synthetic L1–L4, 18 scenarios, 8 sensitivity sweeps | COMPLETED | `23` deterministic artifacts in `results/exploratory_v2/` verified bit-identical across 2 consecutive runs (`23/23 OK`) |
| Phase 7 | Comprehensive unit, causality, safety-invariant, synthetic-rotation, and regression tests + classification registry | COMPLETED | `20/20` V3 tests passing (`15` test functions); `94` safe files: `1,857` passed, `1` pre-existing `METADATA_ONLY` allowlist failure in `run_synthetic_tests.py` (`guard.blocked=0`, `violations=[]`); full `pytest tests/` `3,819 passed, 41 failed` (`0` regressions, `41` itemized pre-existing issues) |
| Phases 8–9 | Reproducibility hash manifest, 10 figures, 13 named reports, claim audit | COMPLETED | `fig01`–`fig10` visually inspected + `13` Markdown reports + `FILE_HASH_MANIFEST.sha256` verified in `docs/generated/final_research_v2/` |
| Phase 10 | Git verification & branch commit | COMPLETED | Preserved baseline frozen files verified zero-diff; intentional completion files committed cleanly on `exp/four-layer-completion` |

## Key Governance & Access Record
- `data/governance/leg_exec_authorization.json` present (`sha256: 77933986b42b44d340723227c8319a4fb90687a9d6dbe00133de39780bd9cb7e`).
- `data/governance/AUTH-MEDIA-ACCESS.json` not present on disk: `media_guard.py` enforces `[AUTH_MEDIA_ACCESS_NOT_GRANTED]` on raw `.mov` and `.wav` files under `data/`. No bypass attempted; real-data replay uses frozen Mission 43/39 JSONL caches (pre-`db40305` unrotated inference, explicitly qualified) and Mission 44 audio window CSVs, paired with full synthetic multi-orientation FFmpeg + YOLOv8n verification.
