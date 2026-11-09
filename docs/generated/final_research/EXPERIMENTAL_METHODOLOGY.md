# Experimental Methodology

## Research question (authoritative, Protocol V2, 2026-08-13)

On synchronized, event-labeled recordings from held-out crossings, does a
predefined two-camera, audio-assisted, temporal state policy **change**
event-level missed-train and premature-opening outcomes relative to fair
single-camera and vision-only baselines?

Execution reality, disclosed rather than smoothed over: the available data
is one crossing, so "held-out crossings" is unattainable; the programme
executes the within-dataset paired comparisons the data supports and says
so (see LIMITATIONS).

## Evidence layers and their rules

1. **Perception layer (executed, Mission 43).** Frozen vision checkpoint
   and frozen Audio V3 (threshold 0.37, loader-enforced) run over all 54
   camera sources and 27 event audio extractions. Outputs are hash-bound
   caches; agreement is measured against the adopted references at event
   level only (the only level the references support).
2. **Decision layer — synthetic (ungated, EXECUTED 2026-11-08/09).** Both
   engines were driven through identical constructed MultimodalFrame
   streams (`scripts/run_m3_synthetic_battery.py`, 13 scenarios) covering
   nominal departure, disappearance, failure injection, staleness,
   contradictory evidence, single-camera topology, fault recovery,
   reopening interruption, duplicate/out-of-order rejection, and
   audio-delayed clearance. Final run: **46/46 checks passed**
   (`results/m3_synthetic_battery_r2/`). Synthetic results validate
   behaviour only.
3. **Decision layer — real caches (gated).** Replay goes exclusively
   through `CacheOnlyReplayEngine` (SHA-256 hash gate, media blacklist,
   deterministic run ids) under the descriptive-execution gate; the full
   multimodal conditions additionally require the back-stream extension and
   a validated SyncAligner (fail-closed for dual-vision conditions;
   dual-camera claims restricted to the 11 CALIBRATION_SUPPORTED events,
   other events evaluated in independent-camera mode with shared-timeline
   metrics marked not_evaluable).

## Fairness rules for every comparison

- Identical inputs: same caches, same manifest, same frozen config
  (`999a7970…a42e`), same thresholds (0.35 / 0.35 / 0.37), same stride
  (0.2 s), same frame windows. Only the named factor varies (policy version,
  stream set, or temporal ablation).
- Thresholds are frozen before execution and never tuned on evaluation
  data; the audio operating point 0.37 in particular is never adjusted to
  improve metrics.
- Durations and windows are computed on the sync-corrected master timeline
  (the naive raw-timestamp computation used by Phase 8–10 scripts is a
  known defect; Phase 10.1's correction is the reference behaviour).
- Missing evidence stays missing: unaligned/unpaired frames (2,717 of
  6,614 in the Mission 43 assembly lack paired audio) are absent inputs,
  not zeros; censored boundaries make dependent metrics not_evaluable.

## Metrics

The frozen descriptive scope (9 metrics: blocked_seconds,
clearance_latency_s, closure_episodes, excess_closed_duration_s,
exposure_s, missed_train, premature_opening, total_closed_s,
warning_lead_time_s) with per-metric evaluable denominators;
premature_opening computed under the researcher's recorded definition
(**decided 2026-11-09: M4 primary, v9 as sensitivity on the 11
sync-supported events**). Analysis and reporting conventions are in
STATISTICAL_ANALYSIS.md.

## Governance

Every real-data decision execution requires the AUTH-DESCRIPTIVE-EVAL-EXEC
record bound to live promotion-receipt, manifest, protocol, metric-scope
and model-config hashes; official evaluation additionally requires the
Stage-2.1 promotion chain and EVAL-AUTH. The chain, its current state, and
the exact researcher acts that complete it are documented in the completion
report and the professor handoff. No gate was bypassed, patched, or routed
around at any point in this programme.
