# DRAFT — NOT APPROVED — NOT AUTHORIZATION

## Cache Production and Provenance Checklist

**Status:** DRAFT — NOT APPROVED — NOT AUTHORIZATION
**Execution:** NOT TO BE RUN DURING THIS AUDIT

### Cache artifacts

- [ ] Front vision JSONL records conform to the cache design schema.
- [ ] Front audio JSONL records conform to the cache design schema.
- [ ] B0/B1/B2 stream selection is explicit and preserves B1 audio-only semantics.
- [ ] Event/cohort identifiers match the approved event decision.
- [ ] Timestamps are finite, nonnegative, and ordered.
- [ ] Synchronization metadata is present only where the approved R04 scope permits it.

### Manifest

- [ ] `manifest_version: 1.0.0`.
- [ ] Correct cohort identity.
- [ ] Repository-bound relative `.jsonl` paths.
- [ ] SHA-256, byte size, and line count for every artifact.
- [ ] No raw-media path fields.
- [ ] Manifest bytes independently retained and hash-bound.

### Official provenance (required before official evidence)

- [ ] Frozen config canonical hash.
- [ ] Frozen decision-policy hash.
- [ ] Vision checkpoint hash.
- [ ] Audio V3 checkpoint hash.
- [ ] Frozen thresholds.
- [ ] Reviewed media SHA-256 values.
- [ ] Inference run ID and generator identity.
- [ ] `annotation_labels_used: false` for replay evidence.
- [ ] Researcher-approved protocol/split/R04 bindings.
- [ ] EVAL-AUTH binding to final live hashes.

Potential producers (`run_phase5_full_inference.py`, `run_real_world_experiments.py`,
`run_exploratory_dual_camera_subset.py`, `run_phase9_diagnostic_replay.py`) are
**NOT_TO_BE_RUN_PENDING_REVIEW** because static inspection shows possible raw-media access,
model inference, ffmpeg/OpenCV use, and repository writes.
