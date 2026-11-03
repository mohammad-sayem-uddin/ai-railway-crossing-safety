# Core Pipeline Implementation Handoff — 2026-10-30

## Implemented in this mission

- B7d delivery-order preservation option: `EventSimulationRunner.run_frames(..., preserve_arrival_order=True)`; B7d runner path requests it. The default remains sorted for all other paths.
- B7e explicit delayed-timestamp injection: `FailureMode.STALE_TIMESTAMPS` now requires finite positive `delay_s` and nonempty `target_source`; current evidence records are timestamp-shifted without changing detection/content.
- Legacy diagnostic runner no longer silently selects a premature-opening profile for new `run_condition` evaluations; it passes `premature_opening_window=None` and uses explicit ground-truth presence (`bool(event.labels)`). Existing tests now assert undecided profile semantics.
- Synthetic regressions cover B7d delivery behavior, B7e required parameters/content preservation/determinism, and legacy runner profile non-selection.

## Deliberately not implemented

- No numerical B7e delay default, camera scope, rejection threshold, or expected state outcome was invented.
- No cache namespace migration/provenance rewrite was performed.
- No D1/D2/D4 selection was made.
- No historical output was rewritten or retroactively validated.

## Contract boundary

The official Phase 12 runner, split validator, input manifest contract, readiness gate, frozen
policy, metrics definitions, ground truth, and EVAL-AUTH remain unchanged.
