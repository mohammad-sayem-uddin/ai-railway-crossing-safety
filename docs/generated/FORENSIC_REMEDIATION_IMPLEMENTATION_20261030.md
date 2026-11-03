# Forensic Remediation Implementation — 2026-10-30

## Scope decision

No source remediation was applied in this mission. Source inspection confirms several historical
findings, but fixing them safely would either alter frozen diagnostic semantics or require an
approved compatibility/provenance contract. The right outcome is a documented recovery boundary,
not a speculative refactor.

## Confirmed source findings

1. **Ground-truth unsafe diagnostic path:** `ExperimentRunner.run_condition()` hard-codes
`has_train_ground_truth=True` and `premature_opening_window="t1_entry_to_t4_clearance"` for its
legacy B0–B7 diagnostic path (`src/railway_detection/experiments/runner.py:110-141`). This explains
why historical diagnostic summaries cannot support approved GT/M4 claims. Changing it would alter
historical semantics; no change made.
2. **Cache provenance gap:** `LayerBEventProcessor.run_vision_inference()` and
`run_audio_inference()` key cache filenames by cohort/event/source/modality, omitting checkpoint,
configuration, and injector identity. New cache namespace/provenance changes require a governed
schema; historical caches were not rewritten.
3. **B7e implementation gap:** `FailureMode.STALE_TIMESTAMPS` is scheduled in the runner but no
corresponding injector branch is present. This is a confirmed source defect, but choosing the exact
stale-timestamp transformation is part of the frozen scientific condition; no guess was made.
4. **B7d ordering semantics:** injector swaps frames, while `EventSimulationRunner` sorts frames
before processing (`simulation/runner.py:163-165`), so disorder may be erased before decision logic.
Changing injection order requires a contract decision about delivery-layer semantics; not changed.
5. **B6b historical defect:** prior forensic audit records IDLE fail-safe failure and corrected
outputs in `results/experiments/corrected_run/B6b`; no historical output changed and no rerun made.
6. **B7b/B7f historical defect:** prior forensic audit records the original 100% drop bug and
corrected isolated outputs; no historical output changed or rerun made.

## Why no code fix was made

- Cache schema/provenance extension could break consumers and needs an explicit contract.
- B7e/B7d exact perturbation semantics are unresolved scientific choices.
- Diagnostic runner GT/profile behavior is historical and changing it would silently redefine
stored results.
- Governance/official contracts are protected.

## Historical artifact impact

All existing summaries, caches, checkpoints, figures, statistical JSON, proposals, reviews, and
corrected namespaces remain untouched. A source fix would not retroactively validate historical
results; real reruns require operational authorization.
