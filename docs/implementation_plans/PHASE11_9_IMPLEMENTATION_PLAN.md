# Phase 11.9 — Synthetic Pilot and Workflow Audit: Implementation Plan

**Status:** PLANNING ARTIFACT — not authorized, not implemented.

## 1. Objective and research justification

Exercise the complete Phase 11.8 workflow end-to-end with synthetic records and synthetic media, before any real event is reviewed. Purpose: find workflow defects, measure usability, collect session-duration observations that will inform the researcher's D1 decision, and verify append-only history, media integrity, reviewer attribution, and recovery behavior — without creating a single real adjudication record.

## 2. Verified starting state

Depends on Phase 11.8 completion: `review_session.py` exists and passes its suite; environment repaired; baseline re-verified. Legacy records and `data/ground_truth/reviews/` untouched.

## 3. Dependencies and prerequisites

Phase 11.8 done + reviewed. Synthetic media fixtures (small generated video/audio files) — must be created under a clearly named synthetic directory, never under `data/raw/`.

## 4. Explicit authorization boundary

MAY create synthetic fixtures, pilot scripts, and a pilot report in a dedicated `scratch/` or `experiments/synthetic_pilot/` area (path confirmed before implementation). MUST NOT create real adjudication records, touch `data/ground_truth/reviews/`, run real-event media through the pilot, or promote anything.

## 5. Files/modules to inspect

- `src/railway_detection/annotation/review_session.py`, `promotion_gate.py`, `stage2_1_schema.py`, `integrity_safeguard.py`
- `tests/test_phase11_8_review_workflow_integration.py`
- `docs/PHASE11_3_ANNOTATION_REVIEW_WORKFLOW.md`

## 6. Expected files to modify or create

Proposed: `tests/test_phase11_9_synthetic_pilot.py`; synthetic fixture generator script (deterministic, seeded); `docs/PHASE11_9_SYNTHETIC_PILOT_REPORT.md`. No production source changes expected — if the pilot reveals a defect, it is fixed in a bounded follow-up unit with its own review checkpoint, not silently patched mid-pilot.

## 7. Detailed implementation tasks in dependency order

**Unit 1 (fixtures):** deterministic synthetic media (2 small files with distinct content per synthetic event) + a synthetic event registry with per-event media paths and precomputed hashes.
**Unit 2 (happy-path pilot):** run the full workflow for 3 synthetic events: authorize reviewer → observe media hashes → construct record → validate → dry-run promotion. Record wall-clock durations.
**Unit 3 (failure-mode pilot):** intentionally induce: wrong media swapped in after hashing; unauthorized reviewer; session interruption/resume; duplicate session id; out-of-order history append. Verify each is rejected and that no partial record survives (recovery behavior).
**Unit 4 (audit report):** usability findings, duration statistics (input for D1, explicitly labeled pilot evidence, not a decision), defect register.

Units 1→2→3 sequential; Unit 4 after all.

## 8. Data, schema, and API changes

None.

## 9. Tests and acceptance criteria

- Happy path: 3/3 synthetic records pass dry-run promotion with zero violations; durations logged per event.
- Failure modes: each induced failure returns the exact expected rejection code and leaves zero written artifacts (verified by directory listing/hash).
- Append-only: an attempted history overwrite raises; verified by test.
- Attribution: every pilot record's `reviewer_id` matches the synthetic authorized reviewer; no record carries a blocklisted or empty id.

## 10. Negative tests and adversarial cases

Swapped media content after observation; registry hash tampering; replaying one event's hashes against another event; session resumed with a tampered start time; allowlist modified between review and promotion.

## 11. Scientific-validity safeguards

All pilot outputs are labeled synthetic in-file and in the report; duration statistics are explicitly marked "pilot evidence for D1 — not a threshold decision".

## 12. Safety invariants and prohibited shortcuts

No real event ids in pilot records. No promotion writes. No reuse of real media paths. Pilot fixtures must not be placed where production loaders could ingest them.

## 13. Expected outputs and report paths

`docs/PHASE11_9_SYNTHETIC_PILOT_REPORT.md` including: usability findings, duration observations, defect register with severity, and an explicit readiness statement for Phase 11.11.

## 14. Rollback and recovery procedure

Pilot artifacts live in one dedicated directory; rollback = delete directory. No production files depend on pilot output.

## 15. Integrity checks

Pre/post sha256 of the 27 legacy records; frozen config/checkpoint hashes; `git status` delta limited to the pilot directory + new test/report files.

## 16. Definition of done

All acceptance criteria in §9 met; report written; researcher-readable summary of D1-relevant duration evidence delivered; zero real records created (asserted by a `find` on `data/ground_truth/reviews/` count remaining 27).

## 17. Stop conditions and escalation criteria

Stop if the pilot reveals a defect that requires schema or promotion-gate changes (escalate — that is a design decision); stop if any pilot artifact is found outside the designated directory.

## 18. Recommended implementation model

**Gemini 3.8 Flash** (bounded, well-specified test/fixture work) with **Opus review** of the defect register and the D1 evidence summary. If the Gemini pilot reveals scope creep, reassign Unit 3 to Qwen Max.

**Minimum viable implementation:** Units 1–2 + §10 items 1–2. **Deferrable:** interruption/resume ergonomics. **Highest-risk failure mode:** pilot accidentally writing into production paths (defeated by §12 directory checks). **Cheapest verification:** run the pilot test file + `find data/ground_truth/reviews -name '*.json' | wc -l` == 27.
