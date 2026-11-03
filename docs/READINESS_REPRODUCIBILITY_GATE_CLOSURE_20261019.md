# Readiness and Reproducibility Gate Closure Report

**Generated:** 2026-10-19 06:34 EDT (2026-10-19T10:34Z)  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**HEAD at start and end:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Disposition:** reproducibility engineering defect corrected; official evaluation remains **NOT READY**.

## Executive result

The previous reproducibility result was **reported, not reverified**. Live verification on
2026-10-19 reproduced the reported readiness and LEG-EXEC facts, and reproduced the sole
reproducibility failure. The failure was an audit-scope defect: the active manuscript scan
treated an immutable historical DOCX as the current manuscript even though a separate,
evidence-limited correction exists. The correction itself also exposed a negation-recognition
gap in the claim scanner.

The audit now checks the active draft and correction independently, retains all nine findings
against the historical DOCX in a separate archival ledger, and distinguishes the archival
finding from the current-manuscript gate. No historical document was rewritten and no claim
criteria were suppressed or weakened.

| Gate | Final live result |
|---|---|
| Reproducibility audit | **PASS 6, FAIL 0, UNRESOLVED 5, NOT_AVAILABLE 2** |
| Active manuscript claims | **PASS**, no findings in draft or correction |
| Historical source audit | **FAIL (archival only)**, 9 findings retained: 8 overclaims and 1 unsupported number |
| Official evaluation readiness | **NOT READY**, 9 blocker instances, 7 unique codes; command exit 3 |
| Stage-2.1 readiness CLI | **NOT READY**, `NO_RECORDS`, exit 2 |
| LEG-EXEC | Authorization valid; 27 originals and 28 outputs verified; repeat run wrote 0 files |
| Full test suite | **1204 passed**, exit 0, no warning |
| Compileall / targeted Ruff / dependency check | Passed / passed / passed |

No official evaluation, Phase 13 official experiment, field session, target-hardware result,
safety result, or official readiness is claimed.

## Verified starting and ending repository state

- HEAD remained `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`.
- Starting worktree, before this task's edits: 16 tracked modified paths, 10,192 untracked
  paths, 0 staged paths. The unusually large dirty state pre-existed; it was preserved.
- Ending worktree: 18 tracked modified paths, 10,193 untracked paths, 0 staged paths. The
  extra untracked path is this report. No stage, commit, push, reset, clean, or broad revert
  was performed.
- Two historical report copies remain byte-identical:
  `Railway_Crossing_Automation_Research_Report.docx` and
  `results/Railway_Crossing_Automation_Research_Report.docx`, each SHA-256
  `f35b157f42370b8308fb691bb5e2d3b0a20e7da10fef96e0c948df462eaef761`.
- Current active manuscript inputs were fingerprinted during the audit. The protocol/design,
  candidate split, Stage-2.1 queue, R04 evidence, and synthetic benchmark fingerprints and
  their timestamps are recorded in the verification notes below.

## Reproducibility failure: evidence and remediation

### Exact original failure

- **Check:** `manuscript_claims_vs_evidence`.
- **Original status:** `FAIL`.
- **Evidence:** nine findings all came from
  `Railway_Crossing_Automation_Research_Report.docx`: eight `OVERCLAIM_LANGUAGE` findings
  and one `UNSUPPORTED_EMPIRICAL_NUMBER` finding. The active
  `docs/PHASE16_MANUSCRIPT_DRAFT.md` had no findings. The separate
  `docs/PHASE16_MANUSCRIPT_CORRECTION_v1.md` explicitly retired unsupported safety language
  and constrained Layer-A metrics to their still-image evidence, but was not in the default
  audit target list.
- **Severity:** genuine claim-integrity problem in a historical source; not a contradiction
  in current active copy, but important because the historical DOCX could be reused.
- **Root cause:** the audit conflated an immutable historical artifact with the current
  manuscript after an additive correction had been authored. A second scanner defect caused
  it to misread the correction's “did not establish …” disclaimer when the clause was split
  across lines.

### Engineering fix

1. Active default scan now includes the current draft and versioned correction.
2. Historical DOCX is scanned by the same unchanged claim rules into
   `historical_claim_findings`, with `historical_claim_audit_status: FAIL` and
   `historical_source_disposition: preserved_with_findings`. Markdown renders a distinct
   historical section. All nine original findings remain visible and traceable.
3. Added `did not` to the explicit negation vocabulary and regression coverage for historical
   disclaimers.
4. Added regression assertions for current-manuscript PASS, archival finding counts/codes,
   and rendered archival findings.
5. Clarified the Phase 12 and Phase 14 status documents so historical snapshots are not
   presented as current implementation status. Phase 14's synthetic benchmark is explicitly
   not target-hardware or official evaluation evidence.

**Verified live report:** `/tmp/reproducibility-audit-final-20261019.json`  
**Generated:** `2026-10-19T10:22:00Z`  
**Report SHA-256:** `0727009220c60e14fcd3380cd88f40c69a05f71fffb125b64e8985295c3190da`  
The CLI deliberately refuses to write audit outputs under `docs/`; the machine-readable live
report and Markdown were therefore generated under `/tmp`, and their verified results are
captured here.

## All unresolved and unavailable reproducibility checks

Evidence freshness refers to the live audit at `2026-10-19T10:22:00Z`, the live readiness gate
at approximately `2026-10-19T10:22Z`, and the listed input file fingerprints. “Autonomous” asks
whether engineering can supply the missing scientific/human fact without inventing evidence.

| Check ID / description | Current evidence and freshness | Why unresolved / unavailable; exact missing prerequisite | Engineering can resolve autonomously? | Implemented remediation / verification | Remaining human decision or external dependency |
|---|---|---|---|---|---|
| `approved_ground_truth` — approved Stage-2.1 labels | Ground-truth audit generated live 2026-10-19: 27 records, all schema `6.0.0`; 0 Stage-2.1, 0 eligible; receipt absent/invalid. Current notices verify all legacy records as invalidated. | Legacy records are not labels. Missing genuine, individually attributable Stage-2.1 review/adjudication records for the intended evaluation population; after review, a valid promotion receipt must be issued. | **No** for labels, adjudication, or approval. Software supports the workflow and can verify a genuinely completed record. | Confirmed no current Stage-2.1 records and that the queue has 27 `INVALID` items; did not migrate or manufacture labels. | Researcher must conduct/authorize genuine reviews and adjudication; any receipt follows only after valid approved records and live media checks. D1 duration thresholds and D3(c) clear-boundary audit decisions also remain open in the project register. |
| `protocol_version` — premature-opening definition | Protocol v9 SHA-256 `7c183b323970591b68f0db692e70413e54dcacfc4bf78a358c28f1b1ed68734c`; design SHA-256 `2e906c1e19426d2fa406fe626858b0b308fc6abb38510afd660768e954fbb407`; decision evidence is `docs/PREMATURE_OPENING_DECISION_EVIDENCE.md`. | v9 (`T1 ≤ t < T4`) and design M4 (`t_blocked < t < T4`) conflict; no researcher-attributed acceptance exists. Missing `data/manifests/phase12_protocol_decision.json` with the selected `choices.premature_opening_window`. | **No** for choosing a scientific endpoint. If M4 is selected, engineering must implement and test it before it is usable. | Searched authoritative decision records; preserved the no-default fail-closed implementation. No choice fabricated. | Researcher chooses v9 or M4 (and accepts its implications); engineering implements M4 only if that is the recorded choice. |
| `event_split_decision` — event-level train/validation/test split | Candidate proposal SHA-256 `43f11a559366cd1d1f9e21fe198d87526e3f39bbd9ff8c64d559b2f00f476cad`; mtime 2026-10-19 04:44 local; marked `CANDIDATE_ONLY` / `NOT_APPROVED`. | Candidate partition is not approval and grouping/leakage constraints remain relevant. Missing researcher-authored `data/splits/phase12_event_split_decision.json` with cohort-qualified partitions and verified provenance. | **No** for split allocation or leakage acceptance. Mechanical validation and manifest building are engineering actions after approval. | Verified candidate artifact was not consumed as an approved decision; did not promote it or choose a partition. | Researcher records R-SPLIT and accepts the event-level allocation / grouping policy. |
| `r04_scope_decision` — accepted camera synchronization scope | `R04_EVENT_EVIDENCE.json` SHA-256 `95f9dd2082cc0b9051b97cdd3749dde852fc1c0b3fdad61bfeb09050fac7dabf`, mtime 2026-10-19 04:44 local; candidate evidence reports 11 calibration-supported candidates, 9 ambiguous, 7 provisional, and full-cohort dual-camera scope blocked. | Evidence is expressly not a decision. Missing researcher-authored `data/manifests/phase12_r04_scope_decision.json`, including `accepted_sync_events`. | **No** for deciding eligible camera scope. Engineering can validate the record and enforce supported-event constraints after choice. | Searched calibration and exploratory authorization records; retained them as evidence only. | Researcher chooses and records the accepted-sync event set/scope; no automatic approval. |
| `unresolved_decisions` — consolidated research/authorization register | Live register reports EVAL-AUTH not recorded, premature-opening choice unresolved, split unresolved, R04 unresolved, Stage-2.1 not obtained, D1 thresholds unresolved, D3(c) audit unresolved; LEG-EXEC is verified authorized. | This is a roll-up, not one artifact defect. Exact missing artifacts/decisions are in the preceding rows plus `data/governance/eval_authorization.json`, D1's numeric threshold decision based on real review-duration evidence, and D3(c)'s researcher-selected audit mechanism/frequency. | **Partly.** Engineering can construct/verify records after real decisions and evidence; it cannot sign, attribute a researcher choice, supply missing observations, or approve field activity. | Read authoritative records and current file presence; corrected audit scope without changing this register's truth. | Researcher supplies the decisions and EVAL-AUTH statement. Any site/safety authority approval is external and not established here. |
| `evaluation_result_provenance` — official event-evaluation result | Live gate and audit: no official result directory/run manifest; no approved truth, split, R04 scope, protocol choice, input manifest, or EVAL-AUTH. | `NOT_AVAILABLE` because no valid authorized official run has occurred. Missing prerequisite is a fully verified live evidence package plus EVAL-AUTH, followed by an actual successful `evaluation run` and its provenance manifest. | **Not now.** Runner and verification are integrated; running now is correctly blocked. After prerequisites and authorization exist, engineering can execute the command under that scope. | Verified the official CLI refuses before execution with live blockers; no result or output was created. | Researcher decisions/approval and genuine data first; EVAL-AUTH explicitly bound to current hashes; then authorized official run. |
| `experiment_manifest_completeness` — Phase 13 experiment manifest | Live audit finds no Phase 13 experiment manifest. Phase 13 engine code/tests are present but restrict execution to synthetic data; the available benchmark artifact is Phase 14 synthetic, not a Phase 13 official experiment. | `NOT_AVAILABLE` because no official Phase 13 experiment exists. Missing prerequisite is Phase 12 baseline/result, a specified/authorized Phase 13 scope and an actual run manifest. | **No** for creating an official result or inventing a scientific run. Engineering may run separately authorized synthetic software tests, which are not this evidence. | Verified Phase 13 engine's synthetic-only safeguards, checkpoint/resume and manifest tests; did not produce an experiment. | Researcher authorization/scope and Phase 12 prerequisites; if meant to study real data, it also needs eligible evidence and official approval. |

### Evidence classifications retained

- Synthetic tests and the Phase 13 engine's synthetic runs establish software behavior only.
- Phase 14's `phase14-benchmark-report/2` artifact is synthetic development-host timing:
  `fingerprints_verified: true`, `real_time_claim_permitted: false`,
  `is_target_hardware_evidence: false`; it does not establish target-hardware performance.
- Layer-A still-image detector metrics are not Layer-B event evaluation.
- Official event evaluation, controlled field validation, safety, and deployment evidence are
  not obtained.

## Nine official-readiness blocker instances reconciled

Live command: `venv/bin/python -m railway_detection evaluation status --repository-root /Users/sayemuddin/Desktop/Train_automation`  
Exit: **3** · `ready: false` · **9 instances / 7 unique codes**.

| # | Blocker / classification | Evidence and reproducibility mapping | Independent or derived? | Resolution / exact next action |
|---:|---|---|---|---|
| 1 | `COHORT_APPROVAL_MISSING` — `engine_events` (`DERIVED`) | 0 approved Stage-2.1 records; maps to `approved_ground_truth`. | Derived diagnostic; depends on missing Stage-2.1 approvals. | Clears automatically when a genuine approved record exists for the cohort. |
| 2 | `COHORT_APPROVAL_MISSING` — `no_train_events` (`DERIVED`) | Same evidence; maps to `approved_ground_truth`. | Derived diagnostic. | Same; do not invent approval. |
| 3 | `COHORT_APPROVAL_MISSING` — `train_events` (`DERIVED`) | Same evidence; maps to `approved_ground_truth`. | Derived diagnostic. | Same; do not invent approval. |
| 4 | `EVAL_AUTH_NOT_GRANTED` (`AUTHORIZATION`) | `data/governance/eval_authorization.json` absent; maps to `unresolved_decisions`. `live_bindings` has null split, manifest, protocol, R04, and promotion-receipt hashes. | Separate authorization blocker (its valid binding depends on upstream artifacts). | Researcher records EVAL-AUTH only after all evidence hashes are ready; no authorization inferred from chat or general authorization. |
| 5 | `EVENT_SPLIT_DECISION_MISSING` (`MISSING_RESEARCH_DECISION`) | `data/splits/phase12_event_split_decision.json` absent; candidate proposal is unapproved. Maps to `event_split_decision`. | Researcher decision; not a duplicate. | Researcher authors R-SPLIT; engineering validates/builds derived manifest afterward. |
| 6 | `MANIFEST_MISSING` (`MISSING_HUMAN_EVIDENCE`) | `data/manifests/phase12_evaluation_inputs.json` absent. Maps to `evaluation_result_provenance` / missing official input package; depends on decisions and approved truth. | Downstream artifact blocker; formally a separate gate instance, semantically dependent on prerequisites. | Build from verified approved split/scope and authorized inputs; do not generate a fake manifest. |
| 7 | `PREMATURE_OPENING_DEFINITION_UNDECIDED` (`MISSING_RESEARCH_DECISION`) | `data/manifests/phase12_protocol_decision.json` absent; v9/M4 evidence and hashes above. Maps to `protocol_version`. | Researcher decision; not a duplicate. | Researcher selects and records the endpoint; implement M4 only if selected. |
| 8 | `R04_SCOPE_DECISION_MISSING` (`MISSING_RESEARCH_DECISION`) | `data/manifests/phase12_r04_scope_decision.json` absent; R04 candidate report is not approval. Maps to `r04_scope_decision`. | Researcher decision; not a duplicate. | Researcher records accepted synchronization scope. |
| 9 | `STAGE21_RECORDS_MISSING` (`MISSING_HUMAN_EVIDENCE`) | No active Stage-2.1 records; 27 verified-invalidated legacy records are excluded. Maps to `approved_ground_truth`. | Independent root evidence blocker. | Genuine researcher review/adjudication; legacy records must not be migrated. |

Thus the nine instances are **not nine independent root causes**: three are explicit derived
cohort diagnostics; the remaining six are distinct gate prerequisites, although manifest and
authorization are downstream of some decisions/evidence. No gate semantics or blocker count
was altered.

## LEG-EXEC authorization and integrity

The live operation-specific authorization at
`data/governance/leg_exec_authorization.json` validated against the pinned proposal, current
source digest, exactly 27 source records, exactly 28 outputs, and the stated write operation.
It is an explicitly **unsigned recorded researcher statement**, not a cryptographic signature.

- Authorization record body SHA-256: `d4002a0a1367e7cd18cfb007eb89c3937583247f77804ff410d650d54a688363`.
- Pinned/actual proposal SHA-256: `41cbbba3e9d587b9972c3baca1b39f09d478d408d9c60fd538c249c4600113d4`.
- Authorized source-record digest: `b9d10de45dd0849b321e4136ef1a0807e0240f4e4a41efadc90333619786ab0d`.
- Live repeat operation report: `/tmp/LEG_EXEC_OPERATION_REPORT_FINAL.json`; SHA-256
  `ec01404f47635ba273309c6098a21bf695117aaa9b1eb2478c4582b3c9aeb90a`.
- Live repeat: `completed: true`, 27 sources, `originals_byte_identical: true`, 0 new files,
  0 failures, 0 missing outputs, 0 invalid notices. All 27 record operations and the directory
  operation were `SKIPPED_ALREADY_DONE_MATCHING`.
- Independently recomputed all 27 source SHA-256 values and compared them to the operation
  report: all matched. The full exact path/hash ledger is in the live operation report; the
  record path set is precisely the 27 `*_review.json` inputs named by the pinned proposal.
- Recomputed the output inventory from the reviews tree: exactly the 27 sibling notice paths
  and the directory notice below, no missing or additional notice outputs; all 28 live output
  hashes matched the live report. All 27 sibling notices passed `verify_invalidation_notice()`.
- The per-record source path/hash ledger is reproduced below so protected-source verification
  does not depend on retaining the temporary JSON report.

### Per-record original SHA-256 ledger

| Original review record | SHA-256 |
|---|---|
| `data/ground_truth/reviews/engine_events/event_001_review.json` | `3493e125e86c7642d47dca13ddfe3a91fad926b6e6d0fd9e9662968d1bca3edd` |
| `data/ground_truth/reviews/no_train_events/event_001_review.json` | `7387acbf17e6ca2eda6b814e3d9f30683aecffe863b14637cc4ff4bf51015243` |
| `data/ground_truth/reviews/no_train_events/event_002_review.json` | `619efd3ec467f0f23f0b70ef885fd7771fb84dcd052b1175c4c9fca4745ace95` |
| `data/ground_truth/reviews/no_train_events/event_003_review.json` | `8f163c525e32ddf4623718093b2909bcaf1b20b320d8a75985fd7310ee19ce2b` |
| `data/ground_truth/reviews/train_events/event_001_review.json` | `a0edd4a670e1706391309392661559e93a310d5c9f39d17cf094173cfb5e1cc6` |
| `data/ground_truth/reviews/train_events/event_002_review.json` | `437e0d2dec08179aa5194633bcca56bb2cb37c464048566fbe09b2745dcaa239` |
| `data/ground_truth/reviews/train_events/event_003_review.json` | `308d22669e2bee899c3d621c66388e4753e0c0ba5d656a56d497ddf23944ab5b` |
| `data/ground_truth/reviews/train_events/event_004_review.json` | `d47aabda3fa81f7c530e1603a89f8c5fb26ffe8103edd33ead00bfe7bd237f4d` |
| `data/ground_truth/reviews/train_events/event_005_review.json` | `d79c5a4b4a3d6e0139ce300e6de4a6d34250fdef1495a69c3c60badc3d829af9` |
| `data/ground_truth/reviews/train_events/event_006_review.json` | `d7f1d5594d4d1d6d8675e9f97140139d8a400d7081d315832a5b15c6195a6b5e` |
| `data/ground_truth/reviews/train_events/event_007_review.json` | `ba40869a4abc7d9db8295782a15c5bd2c380f8d9c31afa9bfc3e07dfddb8a536` |
| `data/ground_truth/reviews/train_events/event_008_review.json` | `d97bcc8d68630d9e886e34577c3622b83f5115c682c0d8dc5edfc5521cbf54cf` |
| `data/ground_truth/reviews/train_events/event_009_review.json` | `06660001cfa9299eb5d299b64089413c96df99284171648e0d0e0f43b0dd860e` |
| `data/ground_truth/reviews/train_events/event_010_review.json` | `f64bbe72f11b17910f3d3cc98d08a7303b77ef37cdf2a2ca9b97509aae6c85b4` |
| `data/ground_truth/reviews/train_events/event_011_review.json` | `28fcf1f5c8824a42782d964e012552e46e245bce67fb64c72a421276ef6ebb4c` |
| `data/ground_truth/reviews/train_events/event_012_review.json` | `b369f6863f00212cbc9a988c5d42035fe540f150793f60b058731abeaf69eeba` |
| `data/ground_truth/reviews/train_events/event_013_review.json` | `8d5dfc1f03b7bc2dd9bbc42199fda6c2935e60c9c1292de19d5df31bab7cce76` |
| `data/ground_truth/reviews/train_events/event_014_review.json` | `2717a61b0a6d328ab6977aa9320a2c78990d76f4b6887203e675445844ab7d5a` |
| `data/ground_truth/reviews/train_events/event_015_review.json` | `9a90a1a6ed1eb77801b1250d2368ee6916508c38c08fb86f951682cf55bd9c8a` |
| `data/ground_truth/reviews/train_events/event_016_review.json` | `c25a8e4bb4f9667927a2c2e88d76aa40e09612baffd75a8bb8171ff4381db1af` |
| `data/ground_truth/reviews/train_events/event_017_review.json` | `f2ee23c67348984283e30f18735d57feb1cedbd822056bfec12a5466eee8d859` |
| `data/ground_truth/reviews/train_events/event_018_review.json` | `a954c637fc7430ba5fcaf1de98c3407f6f8a9f2cd984f7cb5fadaeef3e60efaf` |
| `data/ground_truth/reviews/train_events/event_019_review.json` | `278b49f9c241b10189274c19a9634e58a5c8dfc4e45530239d2778f662fe29f2` |
| `data/ground_truth/reviews/train_events/event_020_review.json` | `b98c257804fd2ba0acb21a10de90c9dc4595fc3a898ce1c41a86beedc3ccf9e9` |
| `data/ground_truth/reviews/train_events/event_021_review.json` | `c6e689b00b5001191660b4b71c8df43d205b84f1b7d23af066298152d85b563f` |
| `data/ground_truth/reviews/train_events/event_022_review.json` | `30f0ec6c8f2825a6644bebe3ce8ab97a9352cfeabb8a721da30a235403f134c4` |
| `data/ground_truth/reviews/train_events/event_023_review.json` | `e19f917c28920161535e9322a984fa35fecd8fba552557a017062b727b3854d6` |

Exact output inventory (the first 4 are the single engine record and 3 no-train records; the
remaining 23 correspond to train events 001–023):

```text
_INTEGRITY_NOTICE.md
engine_events/event_001_review.INVALIDATION_NOTICE.json
no_train_events/event_001_review.INVALIDATION_NOTICE.json
no_train_events/event_002_review.INVALIDATION_NOTICE.json
no_train_events/event_003_review.INVALIDATION_NOTICE.json
train_events/event_001_review.INVALIDATION_NOTICE.json
train_events/event_002_review.INVALIDATION_NOTICE.json
train_events/event_003_review.INVALIDATION_NOTICE.json
train_events/event_004_review.INVALIDATION_NOTICE.json
train_events/event_005_review.INVALIDATION_NOTICE.json
train_events/event_006_review.INVALIDATION_NOTICE.json
train_events/event_007_review.INVALIDATION_NOTICE.json
train_events/event_008_review.INVALIDATION_NOTICE.json
train_events/event_009_review.INVALIDATION_NOTICE.json
train_events/event_010_review.INVALIDATION_NOTICE.json
train_events/event_011_review.INVALIDATION_NOTICE.json
train_events/event_012_review.INVALIDATION_NOTICE.json
train_events/event_013_review.INVALIDATION_NOTICE.json
train_events/event_014_review.INVALIDATION_NOTICE.json
train_events/event_015_review.INVALIDATION_NOTICE.json
train_events/event_016_review.INVALIDATION_NOTICE.json
train_events/event_017_review.INVALIDATION_NOTICE.json
train_events/event_018_review.INVALIDATION_NOTICE.json
train_events/event_019_review.INVALIDATION_NOTICE.json
train_events/event_020_review.INVALIDATION_NOTICE.json
train_events/event_021_review.INVALIDATION_NOTICE.json
train_events/event_022_review.INVALIDATION_NOTICE.json
train_events/event_023_review.INVALIDATION_NOTICE.json
```

The notices are historical disposition markers. They create no Stage-2.1 ground truth,
approval, evaluation authorization, or field authorization.

## Deliverable integration and scope review (Phases 12–16)

| Phase | Verified implementation/output | Integration and current boundary |
|---|---|---|
| 12 — official evaluation | Evidence-derived readiness and execution gate, manifest builder, replay producer, metric/report pipeline, governance, provenance tests. | Integrated into `python -m railway_detection evaluation status/run`; live run refuses at the gate. No official output exists. Corrected stale historical wording in `docs/PHASE12_EVALUATION_REPORT.md`. |
| 13 — ablations/robustness | Synthetic-only experiment engine has atomic per-cell checkpoints, resume/retry, input fingerprints and complete-grid comparisons; focused tests exist. | These are software/development mechanisms only, not a completed official Phase 13 experiment. No official Phase 13 manifest/result exists. No scientific authorization or real-data path was enabled. |
| 14 — profiling/benchmark | Reproducible benchmark suite, fingerprint and equivalence checking; existing report is `docs/generated/PHASE14_SYNTHETIC_BENCHMARK_20261016.json`. | Integrated `python -m railway_detection benchmark run`; current artifact explicitly denies target-hardware/real-time claim permission. Corrected stale wording in `docs/PHASE14_REALTIME_OPTIMIZATION_REPORT.md`. No target device or acceptance criterion exists. |
| 15 — controlled validation | Capture-session v2 schema/validator, chain-of-custody verifier, canonical deterministic manifest/preflight, tests. | Metadata tooling only. It cannot verify site permission or safety-case soundness (`external_authorization_verified: false`); no field session or capture manifest exists. No field workflow or authority approval is inferred or added. |
| 16 — manuscript/environment | Current draft plus evidence-limited versioned correction, reproducibility CLI/module, environment record. | Audit is invoked via `scripts/audit_reproducibility.py` and top-level `audit reproducibility`; active draft and correction pass. Historical DOCX findings remain separately archived. Environment uses verified `venv`, not the drifting `.venv`. |

No phase output was elevated from smoke/synthetic/development evidence to official evaluation or
validated target-hardware performance.

## Warning, tests, lint, and compilation

### Warning investigation and engineering fix

The reported suite warning was reproduced: importing `src/railway_detection/demo/server.py`
imported deprecated stdlib `cgi` (`DeprecationWarning`, slated for removal in Python 3.13).
The dashboard's upload and image-prediction endpoints used `cgi.FieldStorage`. Replaced this
with a binary-safe standard-library MIME parser, length-checked request-body reader, duplicate
field rejection, malformed-request handling, and focused parser plus HTTP upload tests. This
preserves binary upload bytes and removes the deprecated import. Full final suite emitted no
warning.

### Final validation

- Focused regression/integration tests (audit, correction, dashboard multipart, Phase 12–15):
  **250 passed**.
- Full suite after all changes: `venv/bin/python -m pytest -q` — **1204 passed in 92.24s**,
  exit 0, no warning.
- `venv/bin/python -m compileall -q src scripts` — passed.
- Targeted Ruff on changed application/test modules and relevant Phase 12–16 modules — passed,
  “All checks passed!”.
- `venv/bin/python -m pip check` — “No broken requirements found.”
- `git diff --check` on this task's changed tracked/text paths — passed. A repository-wide diff
  check reports trailing whitespace in unrelated pre-existing dirty protocol/test files; they
  were not edited to avoid broad cleanup.
- A broader Ruff probe including the untouched
  `src/railway_detection/annotation/readiness_cli.py` reports a pre-existing E501 at line 224;
  that file was not changed. Targeted Ruff for changed modules is clean.
- `venv` Python 3.11.15, pytest 9.1.1, Ruff 0.17.0; pip dependency graph clean.

## Smallest remaining actions for official evaluation readiness

1. Researcher conducts genuine Stage-2.1 review/adjudication; do not reuse the invalidated
   legacy records. Resolve D1/D3(c) where required by that workflow.
2. Researcher records the premature-opening endpoint choice (v9 or M4; M4 requires an
   engineering implementation/test before official use).
3. Researcher authors R-SPLIT and R-R04SCOPE, using the current candidate/evidence reports as
   inputs, not approvals.
4. Engineering runs the validated promotion/readiness flow, constructs the input manifest
   from approved decisions, and checks all live media/provenance bindings.
5. Researcher records EVAL-AUTH bound to the exact live hashes reported by `evaluation status`.
6. Rerun `evaluation status`; only if it reports ready should the researcher authorize and
   request `evaluation run`. Keep Phase 13, target-hardware measurement, field validation, and
   safety authorization as separate later gates.

## Commands and evidence locations

```text
venv/bin/python -m pytest -q
venv/bin/python -m compileall -q src scripts
venv/bin/ruff check <changed and relevant Phase 12–16 files>
venv/bin/python scripts/audit_reproducibility.py --json /tmp/reproducibility-audit-final-20261019.json --md /tmp/reproducibility-audit-final-20261019.md
venv/bin/python -m railway_detection evaluation status --repository-root /Users/sayemuddin/Desktop/Train_automation
venv/bin/python scripts/audit_ground_truth_readiness.py --json /tmp/ground-truth-readiness-final-20261019.json --md /tmp/ground-truth-readiness-final-20261019.md
venv/bin/python -m railway_detection.annotation.readiness_cli --report-path /tmp/stage21-gate-final-20261019.json --markdown-path /tmp/stage21-gate-final-20261019.md
venv/bin/python scripts/run_leg_exec.py execute --report /tmp/LEG_EXEC_OPERATION_REPORT_FINAL.json
```

The live machine-readable reports were written to `/tmp` to respect CLI output protections and
avoid altering generated/historical evidence files. This closure report records their results;
the archival reports dated 2026-10-19 were not overwritten.