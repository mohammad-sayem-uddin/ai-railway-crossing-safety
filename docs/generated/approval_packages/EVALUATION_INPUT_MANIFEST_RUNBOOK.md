# Evaluation Input Manifest Preparation Runbook (`phase12-evaluation-inputs/1`)

- **Output Destination (Post-Approval Only):** `data/manifests/phase12_evaluation_inputs.json`
- **Why Not Built Pre-Approval:** `manifest_builder.build_evaluation_input_manifest(repository_root, event_sources, output_path)` requires one verified `phase12-replay-evidence/1` source JSON (under `data/manifests/` with `evidence_classification = 'real'`) per split event. No synthetic fixtures, Mission 39 exploratory caches, or pre-`AUTH-MEDIA-ACCESS` caches under `data/cache/` may be substituted (`input_contracts.py` rejects non-real/unverified sources).

## Exact Post-Stage-2.1 Execution Workflow
1. Complete Stage-2.1 ground-truth reviews (valid `AUTH-MEDIA-ACCESS.json` active) and generate `data/governance/stage21_promotion_receipt.json`.
2. Produce real per-event `phase12-replay-evidence/1` evidence files under `data/manifests/` using `RealEventReplayProducer` / authorized raw-media feature extraction against the Stage-2.1 ground truth and validated camera calibration.
3. Invoke `railway_detection.evaluation.manifest_builder.build_evaluation_input_manifest(repository_root=Path('.'), event_sources=..., output_path=Path('data/manifests/phase12_evaluation_inputs.json'))`.
4. Verify live readiness status with:
```bash
PYTHONPATH=src .venv/bin/python -m railway_detection evaluation status
```
Wait until ONLY `EVAL_AUTH_NOT_GRANTED` remains before computing the final `eval_authorization.json`.
