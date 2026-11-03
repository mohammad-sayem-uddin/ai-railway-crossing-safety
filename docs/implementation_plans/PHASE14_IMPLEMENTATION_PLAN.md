# Phase 14 — Real-Time Optimization: Implementation Plan

**Status:** PLANNING ARTIFACT — not authorized, not implemented.

## 1. Objective and research justification

Profile and optimize the frozen baseline's inference and decision-engine latency to characterize real-time feasibility on target hardware, while preserving exact behavioral equivalence with the frozen baseline (no accuracy change, no threshold change). This is an engineering characterization study, not a redesign.

## 2. Verified starting state

Depends on Phase 12 (and optionally 13): baseline behavior is characterized; frozen config intact; approved ground truth available for regression testing. Current inference runs on CPU with YOLOv8n and CompactTrainHornCNN.

## 3. Dependencies and prerequisites

- Phase 12 baseline established.
- Researcher authorization for optimization scope.
- Target hardware specification (researcher-provided; if none, document assumed target).

## 4. Explicit authorization boundary

MAY profile, benchmark, and optimize inference pipelines (batching, quantization, operator fusion) PROVIDED behavioral equivalence is demonstrated on approved ground truth. MUST NOT change model weights, decision thresholds, timing parameters, or the frozen config. MUST NOT deploy on real railway hardware.

## 5. Files/modules to inspect

- `src/railway_detection/inference/` (vision/audio inference pipelines)
- `src/railway_detection/fusion/` (decision engine tick loop)
- `configs/frozen_experiment_v1.yaml` (timing constraints: tick_s=0.2, confirm_frames=2, etc.)
- `docs/EXPERIMENT_DESIGN_FINAL.md` §7 (real-time requirements if stated)
- Phase 5/8/10.1 tick logs (baseline timing reference)

## 6. Expected files to modify or create

Proposed: `src/railway_detection/optimization/profiler.py`; `src/railway_detection/optimization/latency_report.py`; `scripts/run_phase14_profiling.py`; `docs/PHASE14_REALTIME_OPTIMIZATION_REPORT.md`; outputs under `results/optimization/phase14_<timestamp>/`.

## 7. Detailed implementation tasks in dependency order

**Unit 1 (profiling):** instrument the existing inference + decision pipeline with per-stage timing (vision inference, audio inference, fusion tick, state machine transition). Profile on the current CPU setup. Establish baseline latency distribution per tick.
**Unit 2 (bottleneck identification):** from Unit 1 data, identify the dominant latency contributors. Document whether the 200ms tick budget is met, exceeded, or marginal.
**Unit 3 (optimization experiments):** if bottlenecks are identified, test bounded optimizations: ONNX export for vision model; batched audio windowing; vectorized state-machine transitions. Each optimization is tested for behavioral equivalence (same tick outputs on same inputs).
**Unit 4 (equivalence verification):** run the optimized pipeline on all approved events; compare tick logs byte-for-byte against Phase 12 baseline. Any divergence = optimization rejected.
**Unit 5 (report):** latency profiles, optimization results, equivalence evidence, hardware recommendations, and explicit statement that optimization does not change safety-relevant behavior.

## 8. Data, schema, and API changes

None to schema or config. New profiling/optimization modules.

## 9. Tests and acceptance criteria

- Profiling produces per-stage latency for every tick of every approved event.
- Behavioral equivalence: optimized pipeline tick logs are byte-identical to baseline for all approved events.
- No frozen config value changed (hash check).
- Report includes p50/p95/p99 latency per stage.

## 10. Negative tests and adversarial cases

- Optimized pipeline given a different frozen config → hash check refusal.
- Optimization that changes any tick output → flagged as equivalence failure, not silently accepted.
- Attempt to use Audio V2 in optimization → refusal.

## 11. Scientific-validity safeguards

Optimization is characterized, not claimed as improvement to the research contribution; latency numbers are engineering characterization, not safety evidence.

## 12. Safety invariants and prohibited shortcuts

No weight modification. No threshold change. No deployment on real hardware. No claim that optimized latency implies safety certification.

## 13. Expected outputs and report paths

`docs/PHASE14_REALTIME_OPTIMIZATION_REPORT.md`; profiling outputs; equivalence test results.

## 14. Rollback and recovery procedure

Optimization modules are additive; if equivalence fails, the optimization is simply not adopted. No production code is modified.

## 15. Integrity checks

Frozen config/checkpoint hashes unchanged; approved ground truth unchanged; Phase 12 outputs unchanged.

## 16. Definition of done

Latency profile complete; bottlenecks identified; optimizations tested (if any); equivalence verified; report delivered with hardware recommendations.

## 17. Stop conditions and escalation criteria

STOP if no optimization achieves equivalence (report the finding honestly); if profiling reveals the tick budget is fundamentally unachievable on available hardware (escalate — this is a design constraint finding, not a bug to fix).

## 18. Recommended implementation model

**Qwen 3.8 Max** (profiling instrumentation and equivalence testing are subtle); **Gemini 3.8 Flash** for report generation and figure creation.

**Minimum viable implementation:** Unit 1–2 (profiling + bottleneck ID). **Deferrable:** Unit 3 optimizations (only if bottlenecks are found and researcher authorizes). **Highest-risk failure mode:** an optimization that subtly changes rounding behavior, causing tick divergence (defeated by byte-for-byte comparison). **Cheapest verification:** run equivalence test on 3 events.
