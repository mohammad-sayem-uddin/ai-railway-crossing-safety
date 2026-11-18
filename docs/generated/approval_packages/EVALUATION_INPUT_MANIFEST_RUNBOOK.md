# Evaluation Input Manifest Preparation Runbook (`phase12-evaluation-inputs/1`)

- **Output Destination (Post-Approval Only):** `data/manifests/phase12_evaluation_inputs.json`
- **Why Not Built Pre-Approval:** `manifest_builder.build_evaluation_input_manifest(repository_root, event_sources, output_path)` requires one verified `phase12-replay-evidence/1` source JSON (inside `data/manifests/`, non-symlink, `annotation_labels_used: false`) per split event. No synthetic fixtures, Mission 39 exploratory caches, or pre-`AUTH-MEDIA-ACCESS` caches under `data/cache/` may be substituted (`cache_phase12_adapter.to_official_evidence_payload` refuses by design).

## Required `phase12-replay-evidence/1` Source Payload Contract
- Exact top-level keys (`replay_evidence.py`): `schema_version`, `event_id`, `cohort`, `camera_mode` (`dual_camera` | `independent_camera` | `single_camera`), `streams` (`front_vision`, `back_vision`, optional `front_audio`), `provenance` (`frozen_config_canonical_sha256`, `checkpoint_sha256` `{vision, audio_v3}`, `vision_confidence_threshold`, `audio_operating_threshold`, `media_sha256`, `inference_run_id`, `annotation_labels_used: false`, `generated_by`).

## Exact Post-Stage-2.1 Execution Workflow
1. Ensure `data/governance/AUTH-MEDIA-ACCESS.json`, all Stage-2.1 reviews, `data/governance/stage21_promotion_receipt.json`, and an explicit `data/splits/phase12_event_split_decision.json` exist.
2. After `AUTH-MEDIA-ACCESS` approval, extract upright `LayerBEventProcessor` `EvidenceRecord` streams (`camera_1`, `camera_2`, `audio_1`) into per-event `phase12-replay-evidence/1` JSON files under `data/manifests/phase12_replay_evidence/`.
3. Invoke `railway_detection.evaluation.manifest_builder.build_evaluation_input_manifest(repository_root=Path('.'), event_sources=..., output_path=Path('data/manifests/phase12_evaluation_inputs.json'))`.
4. Check readiness (`EVAL_AUTH_NOT_GRANTED` should remain alone), bind `live_bindings` into `data/governance/eval_authorization.json`, then run:
```bash
PYTHONPATH=src:. .venv/bin/python -m railway_detection evaluation status
PYTHONPATH=src:. .venv/bin/python scripts/prepare_and_execute_official_evaluation.py --mode execute-after-approval --output-dir <OUT_DIR_OUTSIDE_REPO_TREES>
```
