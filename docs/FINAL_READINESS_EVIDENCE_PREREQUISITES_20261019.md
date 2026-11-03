# Final Readiness Workstream — Evidence and Prerequisite Closure

**Generated:** 2026-10-19  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Disposition:** evidence packages and engineering report corrections completed; official evaluation remains **NOT READY**.

## Verified status

The live command

```text
venv/bin/python -m railway_detection evaluation status --repository-root /Users/sayemuddin/Desktop/Train_automation
```

returned exit **3**, `ready: false`, and **9 blocker instances across 7 codes**. The instances are three derived cohort-approval diagnostics and six independent prerequisites. Readiness was re-run after engineering changes and remained unchanged.

The live reproducibility command

```text
venv/bin/python scripts/audit_reproducibility.py --json /tmp/reproducibility-audit-workstream-20261019.json --md /tmp/reproducibility-audit-workstream-20261019.md
```

reported **PASS 6, FAIL 0, UNRESOLVED 5, NOT_AVAILABLE 2**. The nine historical manuscript findings remain in the archival ledger and are not active-manuscript failures.

No official evaluation, result, Phase 13 real-data experiment, approval, external authorization, or safety result was generated. The EVAL-AUTH record was not created because its live bindings depend on missing upstream decisions, approved records, receipt, protocol profile and manifest.

## Dependency map: nine live blocker instances

The gate reports all nine instances below. Rows 1–3 are derived from row 9 and are not separate decisions.

| # | Live instance | Class | Authoritative prerequisite / evidence | Required action and dependency |
|---:|---|---|---|---|
| 1 | `COHORT_APPROVAL_MISSING` — `engine_events` | Derived | Valid approved Stage-2.1 record for the cohort at `data/ground_truth/reviews/engine_events/`; source media and active proposal recorded in the review queue | Clears automatically when genuine record/adjudication and promotion prerequisites are satisfied. |
| 2 | `COHORT_APPROVAL_MISSING` — `no_train_events` | Derived | Same, under `data/ground_truth/reviews/no_train_events/` | Clears automatically with genuine records; not an independent decision. |
| 3 | `COHORT_APPROVAL_MISSING` — `train_events` | Derived | Same, under `data/ground_truth/reviews/train_events/` | Clears automatically with genuine records; not an independent decision. |
| 4 | `EVAL_AUTH_NOT_GRANTED` | Authorization | `data/governance/eval_authorization.json`; verifier binds the exact split, manifest, protocol profile, R04 decision, promotion receipt, frozen config and policy hashes printed as `live_bindings` | Researcher records EVAL-AUTH only after all bindings are non-null and prerequisites are verified. Does not grant field/safety authority. |
| 5 | `EVENT_SPLIT_DECISION_MISSING` | Researcher decision | `data/splits/phase12_event_split_decision.json`; candidate proposal in `docs/generated/final_readiness_20261019/CANDIDATE_EVENT_SPLIT_PROPOSAL.json` | Researcher decides whether a split is scientifically valid given one crossing/session, leakage, cohort composition and intended evaluation. Candidate SHA ordering is not approval. |
| 6 | `MANIFEST_MISSING` | Derived evidence artifact | `data/manifests/phase12_evaluation_inputs.json`; `src/railway_detection/evaluation/manifest_builder.py`; depends on approved split and R04 decisions, real source payloads, approved test records | Engineering builds only after valid researcher decisions and review evidence exist; not manufactured now. |
| 7 | `PREMATURE_OPENING_DEFINITION_UNDECIDED` | Researcher decision | `data/manifests/phase12_protocol_decision.json`; `docs/PREMATURE_OPENING_DECISION_EVIDENCE.md`; generated comparison under `docs/generated/final_readiness_20261019/r04/PREMATURE_OPENING_V9_M4_COMPARISON.md` | Researcher chooses v9 (`T1 ≤ t < T4`, implemented) or M4 (`t_blocked < t < T4`, implemented). No default selected. |
| 8 | `R04_SCOPE_DECISION_MISSING` | Researcher decision | `data/manifests/phase12_r04_scope_decision.json`; active event evidence in `docs/generated/final_readiness_20261019/r04/` | Researcher selects camera modes/accepted-sync events. Calibration-supported means candidate diagnostics only; no clock fusion or scope approval is inferred. |
| 9 | `STAGE21_RECORDS_MISSING` | Human evidence | `data/ground_truth/reviews/**/*_review.json`, schema `8.1.0-stage2.1`; active proposals and source-media hashes in the Stage-2.1 queue | Researcher must authorize and perform genuine review/adjudication through an operationally authorized workflow, resolve D1/D3 prerequisites, then promotion/readiness tools verify live media and issue a receipt. Legacy v6 records cannot be migrated. |

### Six independent prerequisites (not nine decisions)

1. Genuine Stage-2.1 review/adjudication, with all required workflow governance satisfied; its three cohort diagnostics are derived.
2. Researcher-authored event split decision.
3. Researcher-authored premature-opening protocol choice.
4. Researcher-authored R04 camera-scope decision.
5. Derived hash-bound evaluation input manifest, after items 1–4 and real payloads are available.
6. Evidence-bound EVAL-AUTH, last, once every binding is live and verified.

The separate reproducibility items `evaluation_result_provenance` and `experiment_manifest_completeness` are **NOT_AVAILABLE**, not hidden infrastructure work: no official Phase 12 result or official Phase 13 experiment exists. They become resolvable only after the relevant authorized executions.

## Stage-2.1 human review package

Generated artifacts:

- `docs/generated/final_readiness_20261019/STAGE21_REVIEW_QUEUE.json`
- `docs/generated/final_readiness_20261019/STAGE21_REVIEW_QUEUE.md`

The queue contains 27 cohort-qualified events, all `INVALID` because each legacy record is covered by a verified invalidation notice, all 27 requiring a new record. Each item identifies:

- current active proposal path/version/SHA-256;
- front and back source-video paths and inventory SHA-256 values;
- all 25 required Stage-2.1 top-level/nested/boundary fields;
- the six boundary candidate states, values, cameras and rationales, explicitly unapproved;
- required human actions (independent media inspection, boundary adjudication, listening check when applicable, live observed media hashes, reviewer attribution and no model-output exposure);
- D1 pilot-derived review-duration thresholds, D3 second-review/audit decisions, and missing ADJ-AUTH as separate upstream workflow prerequisites.

The queue does not edit or migrate legacy records, write under `data/ground_truth`, or convert proposal values into labels. **A material workflow limitation was confirmed during final review:** `src/railway_detection/annotation/adjudication_session.py` explicitly accepts only synthetic IDs and temporary paths; it cannot create genuine records for these real events. `review_session.build_review_record()` is a low-level constructor, not an operational interaction that demonstrates that a human inspected the media. ADJ-AUTH alone would not turn either code path into a legitimate real-data review process. A separately authorized, operationally appropriate, human-controlled workflow must be designed/approved before recording real Stage-2.1 reviews; no real record was written here.

The maintained allowlist currently contains one researcher identity. D3(a) requests independent second reviews for uncertainty-triggered and fixed-subset cases, but a second eligible reviewer is not listed. The researcher must explicitly authorize and register an independent reviewer before assigning such a review; no identity or review was invented. This is a distinct prerequisite from EVAL-AUTH and from the Stage-2.1 schema’s acceptance of a reviewer ID.

## Event split candidate and leakage analysis

Generated artifact: `docs/generated/final_readiness_20261019/CANDIDATE_EVENT_SPLIT_PROPOSAL.json`.

- Algorithm: SHA-256 of cohort-qualified event identities, deterministic ordering, largest-remainder counts; default candidate allocation is 16 train / 6 validation / 5 test.
- The report binds the Layer-B inventory bytes and every selected active proposal file. It is `CANDIDATE_ONLY`, `NOT_APPROVED`, and records no researcher decision.
- All 27 events share `crossing_id: crossing_A`; all share `recording_session_id: session_20260914_morning`.
- Both group-disjointness checks fail: the single crossing and single session each span train, validation and test. The exact event lists by role appear under `grouping.checks_by_field`.
- Therefore this ratio proposal is **not leakage-safe**. It is not defensible as an approved independent held-out split merely because the hash allocation is reproducible. Researcher must decide whether a different design/data acquisition is required.

## R04 event report and scope package

Generated under `docs/generated/final_readiness_20261019/r04/`:

- `R04_EVENT_EVIDENCE.json`
- `R04_EVENT_SCOPE_REPORT.md`
- `PREMATURE_OPENING_V9_M4_COMPARISON.md`

The evidence JSON retains all 27 events and binds the current active proposal (highest numeric version), the snapshot reference/hash, calibration diagnostics, source video hashes and candidate boundary values/states. The R04 inputs remain the calibration verdicts, frozen candidate snapshot, candidate sync manifest and independent Layer-B inventory (their source SHA-256 values are inside the report).

There are 11 `CALIBRATION_SUPPORTED` candidate events (all in the train cohort), 9 `AMBIGUOUS`, and 7 `PROVISIONAL`; the candidate manifest is still `CANDIDATE_UNVALIDATED_DO_NOT_MERGE`, and human review is `NOT REVIEWED`. The report does not fuse unsynchronized clocks. M4 candidate evaluability is always false until an actual replay trace and `t_blocked` exist. The coverage diagnostics report 10/11 candidate T1+T4 pairs for v9 and 22/24 candidate T4 values for train/engine events for M4, while explicitly stating official evaluable count **0** for both. These are availability counts, not metric denominators/results.

The v9/M4 review package records exact interval boundaries, command/state semantics, required clocks and labels, censoring, missing T1/T4, T0/T2/T3 roles, engine/no-train cases, blocked and never-protected M5 cases, trace sampling limitations, and the implications for metric inclusion. No choice is recommended or selected.

## EVAL-AUTH prerequisite review

Verifier contract: `src/railway_detection/evaluation/governance.py::verify_eval_authorization`.

The record is an allowlisted researcher statement, unsigned/non-cryptographic, with exact scope and a self-consistent record digest. It must bind **seven live SHA-256 values**: decision policy; event-split decision; frozen config; evaluation input manifest; effective protocol profile; R04 scope decision; Stage-2.1 promotion receipt. It cannot authorize field or physical railway operations.

Presently only the frozen config and policy bindings are available; split, manifest, protocol, R04 and promotion-receipt bindings are null. In addition, there are no active Stage-2.1 records or promotion receipt. Creating EVAL-AUTH now would necessarily use nonexistent bindings or invent authorization, so it was correctly not created. General engineering authorization, chat statements, LEG-EXEC authorization, and candidate report hashes are not EVAL-AUTH.

## Engineering work and evidence corrections

Updated the candidate-only reporting boundary in:

- `src/railway_detection/annotation/candidate_split_queue.py`
- `scripts/build_candidate_split_and_review_queue.py`
- `src/railway_detection/data/r04_evidence.py`
- `tests/test_candidate_split_queue.py`
- `tests/unit/test_r04_evidence.py`
- `docs/CANDIDATE_SPLIT_AND_STAGE21_QUEUE.md`

The changes add versioned per-event missing-field/source/action details, explicit field-by-field crossing/session leakage results and missing-group union, reviewer-facing Markdown, and R04 current-active-proposal provenance. They also correct the R04 report not to fill missing active-proposal boundaries from a historical snapshot, and prevent M4/v9 candidate availability from being mislabeled as evaluability without replay/scope/ground truth. No readiness predicate or researcher decision semantics were changed.

## Validation

- Focused tests after changes: **90 passed** across candidate split/queue, R04 evidence, Phase 12 governance and documented metrics.
- `ruff check` passed for `src/railway_detection/data/r04_evidence.py`; Ruff `UP` checks passed for the changed queue/tool/tests. The queue module/script and pre-existing test file contain long-line E501 findings outside the newly added code; no broad cleanup was made.
- `compileall` passed for changed Python modules/scripts/tests.
- `git diff --check` passed for changed tracked/text paths.
- `venv/bin/python -m pip check` passed: no broken requirements.
- Live readiness remains exit 3 / not ready / 9 instances / 7 codes.
- Reproducibility audit remains 6 PASS / 0 FAIL / 5 UNRESOLVED / 2 NOT_AVAILABLE.
- Final full-suite, full compile/lint/dependency and LEG-EXEC integrity re-verification are recorded in `docs/FINAL_READINESS_WORKSTREAM_REPORT_20261019.md`.

## Smallest defensible route to official evaluation readiness

1. Resolve the Stage-2.1 workflow prerequisites: D1 thresholds from real pilot timing data, D3(a) second-review trigger, D3(c) clear-boundary audit mechanism/frequency, and explicit ADJ-AUTH. Before any real review, provide a production-appropriate, human-controlled workflow (the existing session runner is synthetic-only) and an allowlisted independent reviewer where required. Do not start review until these conditions are met.
2. Qualified, authorized researchers perform new independent, media-grounded reviews for the needed population; resolve disagreements and required second reviews; create genuine Stage-2.1 records. Never edit/migrate the invalidated legacy files. Run promotion/readiness with live media re-hashing and issue a valid promotion receipt only after READY.
3. Researcher resolves the split design in light of single crossing/session leakage; acquire new independent groups if a leakage-safe held-out split is scientifically required. Record the actual accepted decision, not this SHA proposal.
4. Researcher records the premature-opening choice and R04 per-event camera scope. Do not infer approval from calibration diagnostics.
5. Engineering builds the input manifest from those verified decisions and real inference payloads; verify all live sources and hashes.
6. Researcher records EVAL-AUTH against the exact now-live bindings. Re-run readiness; run official evaluation only if the live gate says ready and EVAL-AUTH verifies.
7. Phase 13 official experiment/result provenance remains its own later authorization and execution gate.

HEAD remained unchanged and existing dirty-worktree content was preserved. Nothing was staged, committed, reset, cleaned or broadly reverted.