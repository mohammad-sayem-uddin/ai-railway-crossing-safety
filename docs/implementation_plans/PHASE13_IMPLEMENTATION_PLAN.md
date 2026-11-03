# Phase 13 — Robustness and Ablation Studies: Implementation Plan

**Status:** PLANNING ARTIFACT — not authorized, not implemented.

## 1. Objective and research justification

Quantify the frozen baseline's sensitivity to perturbations (sensor dropout, noise injection, timing jitter, threshold sensitivity) and ablate individual contributions (audio-only vs vision-only vs fusion; confirmation frames; miss tolerance) — all against approved ground truth from Phase 12. This produces the evidence for which components matter, under what conditions, and how fragile the system is.

## 2. Verified starting state

Depends on Phase 12 completion: baseline metrics exist against approved ground truth; event-level split is fixed; frozen config is intact. No ablation or robustness experiment has been run in any prior phase.

## 3. Dependencies and prerequisites

- Phase 12 baseline metrics computed and reported.
- Approved ground truth available (from 11.11/11.12).
- Frozen config hashes verified unchanged.
- Researcher authorization for ablation scope.

## 4. Explicit authorization boundary

MAY run ablation variants and perturbation experiments against the frozen baseline using approved ground truth. MUST NOT modify the frozen config, checkpoints, or decision policy; MUST NOT retune thresholds based on ablation results; MUST NOT use Audio V2; MUST NOT claim safety conclusions from ablation findings.

## 5. Files/modules to inspect

- `configs/frozen_experiment_v1.yaml`, `configs/decision_policy_v1.yaml`
- `src/railway_detection/evaluation/` (ground_truth_loader, event_metrics from Phase 12)
- `src/railway_detection/fusion/` (decision engine, evidence, state machine)
- `docs/FINAL_ABLATION_MATRIX.md` (pre-planned ablation conditions)
- `docs/EXPERIMENT_DESIGN_FINAL.md` §6 (robustness design)
- Phase 12 outputs (baseline tick logs, metrics)

## 6. Expected files to modify or create

Proposed: `src/railway_detection/evaluation/ablation_runner.py`; `src/railway_detection/evaluation/perturbation.py` (sensor dropout simulation, noise injection, timing jitter); `scripts/run_phase13_ablations.py`; `docs/PHASE13_ROBUSTNESS_ABLATION_REPORT.md`; outputs under `results/experiments/phase13_<timestamp>/`.

## 7. Detailed implementation tasks in dependency order

**Unit 1 (ablation matrix execution):** run the pre-planned ablation conditions from `FINAL_ABLATION_MATRIX.md`: vision-only, audio-only, fusion; confirmation=1/2/3; miss_tolerance=0/1/2/3. Each is a replay variant with one parameter changed, all others frozen. Record full tick logs.
**Unit 2 (perturbation suite):** sensor dropout (drop camera_1 for N ticks, camera_2 for N ticks, audio for N ticks); Gaussian noise on detection confidences; timing jitter (±1 frame on event boundaries in ground truth, to test metric sensitivity). All perturbations are applied at replay time, never to the frozen config or raw data.
**Unit 3 (analysis):** per-condition metric tables with deltas from baseline; identify which components contribute most; identify failure modes under perturbation; compute sensitivity indices where n permits.
**Unit 4 (report):** full ablation report with pre-registered hypotheses (stated before running), results, limitations, and explicit statement that ablation findings do not authorize threshold changes.

## 8. Data, schema, and API changes

None.

## 9. Tests and acceptance criteria

- Each ablation condition produces a complete tick log for every approved event.
- Perturbation parameters are logged per-run in a manifest.
- Baseline condition reproduces Phase 12 numbers exactly (determinism check).
- No frozen config value differs across conditions (verified by hash).

## 10. Negative tests and adversarial cases

- Ablation runner given a modified frozen config → refusal (hash check).
- Perturbation applied to ground truth instead of predictions → refusal.
- Attempt to run ablation on unapproved events → loader refusal.

## 11. Scientific-validity safeguards

Pre-register hypotheses before running; report all conditions including null results; never cherry-pick; small-n CIs; R04 restriction applies to every condition identically.

## 12. Safety invariants and prohibited shortcuts

No Audio V2. No frozen-config modification. No post-hoc threshold adjustment based on ablation results. No safety claims from simulation.

## 13. Expected outputs and report paths

`docs/PHASE13_ROBUSTNESS_ABLATION_REPORT.md`; `results/experiments/phase13_<timestamp>/`; registry entries.

## 14. Rollback and recovery procedure

Outputs in fresh timestamped directory; rollback = delete directory + truncate registry lines.

## 15. Integrity checks

Frozen config/checkpoint hashes unchanged; approved ground truth unchanged; Phase 12 outputs unchanged.

## 16. Definition of done

All pre-planned ablation conditions executed; perturbation suite complete; report with deltas, sensitivity analysis, and limitations delivered; baseline reproduction verified.

## 17. Stop conditions and escalation criteria

STOP if baseline reproduction fails (indicates environment drift); if a perturbation reveals a previously unknown failure mode that invalidates Phase 12 claims (escalate to researcher before continuing).

## 18. Recommended implementation model

**Gemini 3.8 Flash** for bounded replay scripting (Units 1–2); **Qwen 3.8 Max** for perturbation logic and failure-injection design (Unit 2 complex cases); **Opus** reviews the report for overclaim.

**Minimum viable implementation:** Unit 1 (core ablation matrix). **Deferrable:** timing jitter sensitivity (Unit 2 partial). **Highest-risk failure mode:** accidentally modifying the frozen config for one condition (defeated by hash check). **Cheapest verification:** baseline condition reproduces Phase 12 numbers.
