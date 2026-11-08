# Reproduction and operation boundaries

Starting Git HEAD:8d03ba5e10f2defb71f2a54ddf46955a29e7185e; tracking origin/main:fc3c29a761deaa9e36eca1e5eea4e0205b1f9a74. No push. Actual visual/audio manifests record real run IDs, start/end times, invocation SHA, model/config identities, environment versions, original-source/annotation hashes, logs and per-event outcomes. Because the new invocation files were not yet committed at run time, their exact file hashes supplement the baseline Git revision; the containing final commit anchors their delivered bytes.

Executed entrypoints (from repository root, using the existing environment):

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. .venv/bin/python docs/generated/professor_evidence/mission43/invocations/run_full_validation.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/reconcile_annotations.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/record_researcher_adoption.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/verify_sources.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/run_vision.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/run_metadata_integration.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/run_audio.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/analyze_results.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/validate_actual_outputs.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/crosscheck_metrics.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/generated/professor_evidence/mission43/invocations/plot_results.py
```

Exact pytest/ffprobe/ffmpeg commands are recorded in their execution receipts/manifests; full inference/analysis stdout/stderr is retained in logs/. Source snapshots/configs/dependency references are included with byte-identical identities in COPIED_EVIDENCE_SOURCE_MAP.json. New output filenames are immutable on reuse; old predictions are hash-checked and reused instead of repeated. Plot layout was refined after visual inspection without rerunning inference or changing numerical inputs.

The actual Mission43 request authorizes the expanded ordinary inference work; previously confirmed authority identity is retained. Each original-operation phase uses the existing real-root AUTH-MEDIA-ACCESS schema, exact27 event IDs/54 paths, actual current issue/expiry/scope hash and unsigned recorded-statement provenance. Issued/closed records are retained in operations/; the canonical raw-media slot is returned to absence. No allowlist or guard change, fake GT promotion, temporary-root real replay or expired grant reuse. B2 remains separately blocked.

These are recorded commands, not authority to re-run now: the transcribed phase scopes were closed and scripts may issue their run-scoped records when intentionally executed. Reproduction requires the actual researcher direction, exact original/model assets, compatible packages and current relevant operation authority; do not treat a copied historical approval or edited JSON as new permission. Ordinary verification of this evidence uses `python3 verify_package.py` **from this package folder** and reads package files only.

Raw videos/audio/PCM, checkpoint binaries, private runtime caches, credentials and absent manual notes are not included. Reused evidence and adopted originals are copied byte-for-byte; original repository references remain documentary pointers. Package verification resolves those references to included copies through the source map, so it does not open raw assets. Source clock stability is not physical camera identity or synchronization. Timings vary by host/load and are not deployment profiling.
