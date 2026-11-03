# Phase 15 — Controlled Validation and Hardware Integration: Implementation Plan

**Status:** PLANNING ARTIFACT — not authorized, not implemented. This phase is authorization-gated and safety-case-dependent.

## 1. Objective and research justification

Plan and prepare (but NOT execute without separate authorization) a controlled validation study that tests the system's detection and decision behavior against real-world observations at the study site, and characterize hardware integration requirements. This phase is primarily PLANNING and SAFETY-CASE DEVELOPMENT. No live railway control is authorized or planned.

## 2. Verified starting state

Depends on Phases 12–14: baseline metrics, ablation results, and latency characterization exist. Frozen config intact. No field deployment has occurred in any prior phase.

## 3. Dependencies and prerequisites

- Phases 12–14 complete.
- Researcher authorization for controlled validation scope.
- Site access authorization (external dependency — railway authority, land owner).
- Safety case draft approved by researcher.
- Hardware procurement complete (if applicable).

## 4. Explicit authorization boundary

MAY plan the validation protocol, draft the safety case, specify hardware requirements, and prepare data-collection scripts. MUST NOT deploy any system on or near a live railway. MUST NOT collect data without site authorization. MUST NOT make safety claims. MUST NOT connect any output to a physical gate or barrier.

## 5. Files/modules to inspect

- `docs/EXPERIMENT_DESIGN_FINAL.md` §8 (field validation design if present)
- `docs/OPEN_DECISIONS_AND_BLOCKERS.md` (site-survey dependency)
- Phase 12–14 reports (what needs validation)
- `configs/frozen_experiment_v1.yaml` (system parameters to validate)

## 6. Expected files to modify or create

Proposed: `docs/PHASE15_VALIDATION_PROTOCOL.md`; `docs/PHASE15_SAFETY_CASE_DRAFT.md`; `docs/PHASE15_HARDWARE_REQUIREMENTS.md`; `docs/PHASE15_REPORT.md`. No code changes expected unless data-collection tooling is needed (bounded, read-only sensors).

## 7. Detailed implementation tasks in dependency order

**Unit 1 (validation protocol design):** define what will be validated (detection accuracy, timing, false alarm rate), how (passive observation, no intervention), where, when, and with what equipment. Specify success criteria and stop conditions.
**Unit 2 (safety case draft):** document why the system, as characterized in Phases 12–14, is safe to observe (not to deploy) at the site. Identify hazards, mitigations, and residual risks. Explicitly state this is NOT a safety certification.
**Unit 3 (hardware requirements):** specify cameras, microphones, compute platform, power, connectivity needed for a passive observation study. Cost estimate. Procurement timeline.
**Unit 4 (data-collection preparation):** if authorized, write scripts for passive sensor data capture (no model inference, no decision output). Test in lab only.
**Unit 5 (report):** consolidate all planning artifacts; state readiness for researcher's go/no-go decision on actual field data collection.

## 8. Data, schema, and API changes

None.

## 9. Tests and acceptance criteria

- Validation protocol is complete and internally consistent.
- Safety case identifies all foreseeable hazards of passive observation.
- Hardware requirements are specific enough to procure.
- No code connects to any actuator or control system.

## 10. Negative tests and adversarial cases

- Code review: no GPIO, serial, network control, or actuator interface exists in any new file.
- Safety case explicitly lists what the system CANNOT do (control a gate, stop a train, etc.).

## 11. Scientific-validity safeguards

Field validation (if it happens) is observational only; it does not modify the frozen baseline or approved ground truth; findings are reported as supplementary evidence, not as replacing Phase 12 metrics.

## 12. Safety invariants and prohibited shortcuts

NO LIVE RAILWAY CONTROL. NO DEPLOYMENT WITHOUT SEPARATE AUTHORIZATION. NO SAFETY CERTIFICATION CLAIMS. The system under study is a research prototype, not a safety-critical product.

## 13. Expected outputs and report paths

`docs/PHASE15_VALIDATION_PROTOCOL.md`, `docs/PHASE15_SAFETY_CASE_DRAFT.md`, `docs/PHASE15_HARDWARE_REQUIREMENTS.md`, `docs/PHASE15_REPORT.md`.

## 14. Rollback and recovery procedure

All outputs are planning documents; rollback = delete files. No production system is modified.

## 15. Integrity checks

Frozen config/checkpoint hashes unchanged; no new code touches `data/ground_truth/` or `results/`.

## 16. Definition of done

All planning documents complete; safety case reviewed by researcher; go/no-go decision documented; no field activity has occurred.

## 17. Stop conditions and escalation criteria

STOP if site access is denied (document and close); if the safety case reveals an unacceptable risk for even passive observation; if the researcher declines to proceed.

## 18. Recommended implementation model

**Claude Opus 4.8** for the safety case and validation protocol (judgment-heavy, safety-critical language); **Gemini 3.8 Flash** for hardware requirements documentation.

**Minimum viable implementation:** Units 1–2 (protocol + safety case). **Deferrable:** Units 3–5 (only if researcher authorizes progression). **Highest-risk failure mode:** language in the safety case that could be misread as a safety certification (defeated by Opus review + explicit disclaimer). **Cheapest verification:** researcher reads the safety case draft.
