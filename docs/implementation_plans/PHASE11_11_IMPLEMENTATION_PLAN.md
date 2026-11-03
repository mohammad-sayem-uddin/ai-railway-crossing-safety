# Phase 11.11 — Formal Stage 2.1 Adjudication: Implementation Plan

**Status:** PLANNING ARTIFACT — not authorized, not implemented. Adjudication does NOT start automatically under any circumstance.

## 1. Objective and research justification

Define and prepare a controlled, researcher-led review of the actual 27-event inventory that produces genuine Stage-2.1 records — the first researcher-approved ground truth this project has ever had. Every record is created by the researcher's own judgment against raw media, never from model output.

## 2. Verified starting state

Workflow integrated (Phase 11.8) and pilot-audited (11.9); decisions D1/D3(a) either closed by researcher or explicitly deferred-with-interim-floor documented (11.10); 27 legacy records present and untouched; zero Stage-2.1 records exist.

## 3. Dependencies and prerequisites

- 11.8 + 11.9 complete; 11.10 decision record exists.
- Researcher's explicit ADJ-AUTH authorization naming the review scope (which events, which boundaries).
- Legacy disposition decision (LEG-EXEC executed or explicitly declined) if new records are to carry `supersedes` fields.

## 4. Explicit authorization boundary

Tooling MAY be built to support review sessions. NO adjudication starts without ADJ-AUTH. No model of any kind may draft boundary values for the researcher to "confirm" — proposals may be opened by the researcher as Stage-1 evidence only, per the existing firewall, and the workflow must log that model outputs were not consulted.

## 5. Files/modules to inspect

- `src/railway_detection/annotation/review_session.py`, `stage2_1_schema.py`, `promotion_gate.py`
- `docs/PHASE11_3_REVIEW_INVENTORY.json` (27 events, media paths/hashes, active proposals)
- `docs/PHASE11_4_FINAL_VIDEO_ANNOTATION_AUDIT_REPORT.md`, `docs/PHASE11_5_ADJUDICATION_REPORT.md`, `docs/PHASE11_6_OPEN_ISSUE_REGISTER.csv` (known unresolved rows)
- `docs/PHASE11_GROUND_TRUTH_PROTOCOL.md` §2 taxonomy

## 6. Expected files to modify or create

Proposed: `src/railway_detection/annotation/adjudication_session.py` (researcher-facing session runner, no autonomous decisions); `docs/PHASE11_11_ADJUDICATION_PROTOCOL.md`; review-order manifest (proposed path: `data/ground_truth/adjudication_plan.json`, created only under ADJ-AUTH); `docs/PHASE11_11_REPORT.md` (per-batch appendices). Confirmed: records would live under `data/ground_truth/reviews/...` ONLY when the researcher personally completes a session.

## 7. Detailed implementation tasks in dependency order

**Unit 1 (protocol doc):** review sequence (recommended: engine_events/event_001 first as the simplest single-camera-shaped case, then no_train_events as negative controls, then train_events shortest-to-longest), reviewer responsibilities, per-boundary four-state decision procedure, evidence capture format (frame index + rationale), and stop conditions.
**Unit 2 (session runner):** interactive (human-in-the-loop) runner: loads one event from the inventory, verifies media hashes live, starts/stops the session clock, collects boundary adjudications keyed by the researcher, builds the record via Phase 11.8 helpers, writes ONLY after the researcher confirms; every write is one record per event, individually timestamped.
**Unit 3 (uncertainty + provenance):** enforce the four-state taxonomy per boundary; require rationale; record censoring direction; bind `reviewer_observed_media_hashes` from the exact files reviewed.
**Unit 4 (disagreement workflow):** implement the researcher's D3(a)-selected second-review flow (`NEEDS_SECOND_REVIEW`/`DISPUTED` states, `second_review_of` linkage) exactly as decided in 11.10 — no invented tolerance.
**Unit 5 (batch review under ADJ-AUTH):** researcher reviews events in the planned order; implementer's role is tooling support and integrity logging only.

## 8. Data, schema, and API changes

None to schema. New session-runner API. Records written per-event under existing `data/ground_truth/reviews/` layout ONLY by researcher action.

## 9. Tests and acceptance criteria

- Session runner constructs only schema-valid records (property test over synthetic inputs).
- Every written record passes `validate_for_promotion` dry-run with real registry/allowlist/paths.
- Review-order manifest covers exactly 27 event ids, no duplicates.
- Per completed session: duration >= enforced floor; attestation non-boilerplate; hashes match independent `sha256sum`.

## 10. Negative tests and adversarial cases

- Attempt to start a session for an event not in the manifest → refused.
- Attempt to write two records for one event in one session → refused (one session, one record).
- Attempt to import a model-output file path into a session → refused + logged.
- Sub-30s confirmation → schema rejection.
- Reviewer id not in allowlist → refusal before session start.

## 11. Scientific-validity safeguards

Model firewall enforced in tooling (no prediction files opened by the runner); left-censored T0 recorded per protocol §2.3, never fabricated; UNCERTAIN retained where footage is insufficient (the 14 site-survey-blocked rows are expected to stay UNCERTAIN/CENSORED).

## 12. Safety invariants and prohibited shortcuts

No auto-approval; no batch stamping; no copying a value from a proposal without the researcher's own frame-level observation; legacy records never edited; no promotion writes in this phase (promotion is 11.12's gate).

## 13. Expected outputs and report paths

Protocol doc, session runner, per-batch report appendices in `docs/PHASE11_11_REPORT.md`, and (researcher-produced) Stage-2.1 records.

## 14. Rollback and recovery procedure

A defective record is never edited in place: it is handled via the append-only `adjudication_history`/invalidation mechanisms only. Session runner writes are atomic (write-temp + rename) with a pre-write backup of the target path if one exists.

## 15. Integrity checks

Before/after each batch: 27 legacy records sha256 unchanged; media files unchanged (re-hash sample); frozen artifacts unchanged; review count increments by exactly the number of completed sessions.

## 16. Definition of done

All events in the authorized scope have either a researcher-completed Stage-2.1 record or a documented stop-condition entry; every record passes dry-run promotion; report written.

## 17. Stop conditions and escalation criteria

STOP if: media hash mismatch is detected mid-review (integrity incident); the researcher invokes uncertainty on >50% of boundaries in a batch (protocol may be wrong); any tooling defect could have allowed a model output into a session; researcher withdraws authorization. Escalate rather than improvise.

## 18. Recommended implementation model

Protocol (Unit 1) and disagreement design (Unit 4): **Claude Opus 4.8**. Session runner (Units 2–3): **Qwen 3.8 Max** (high-consequence write path). Batch support (Unit 5): **Gemini 3.8 Flash** for logging/integrity bookkeeping. The researcher executes the reviews personally.

**Minimum viable implementation:** Units 1–2 for a first 3-event batch. **Deferrable:** Unit 4 until D3(a) is closed. **Highest-risk failure mode:** automation creep — any helper that pre-fills a boundary value (defeated by §10 import-refusal test and Opus diff review). **Cheapest verification:** dry-run promotion on the first completed record + integrity hash block.
