# Final Readiness Workstream — Completion Report

**Generated:** 2026-10-19 07:17 EDT (2026-10-19T11:17Z)  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**HEAD at start/end:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Disposition:** evidence-dependent engineering work completed; official evaluation remains **NOT READY**.

## Final live status

- Official readiness: **NOT READY**, exit **3**, 9 blocker instances / 7 codes.
- Reproducibility: **6 PASS, 0 FAIL, 5 UNRESOLVED, 2 NOT_AVAILABLE**.
- Active manuscript claim scan: PASS, zero active findings; 9 historical DOCX findings remain in the separate archival ledger.
- Ground truth: 27 legacy `6.0.0` records, 0 valid Stage-2.1 records, 0 promotion eligible; promotion receipt absent/invalid.
- Stage-2.1 readiness CLI: **NOT READY**, `NO_RECORDS`, exit **2**.
- EVAL-AUTH, split decision, R04 scope decision, protocol decision, evaluation input manifest and Stage-2.1 promotion receipt remain absent. They were not fabricated.

The nine blocker instances consist of **six independent prerequisites**—Stage-2.1 review evidence, event split decision, premature-opening decision, R04 scope decision, derived input manifest, and evidence-bound EVAL-AUTH—plus **three derived `COHORT_APPROVAL_MISSING` diagnostics** for engine/no-train/train cohorts. The cohort diagnostics clear only when genuine valid approved Stage-2.1 evidence exists; they are not independent decisions.

`live_bindings` at final assessment:

| Binding | SHA-256 |
|---|---|
| `decision_policy_sha256` | `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575` |
| `frozen_config_sha256` | `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e` |
| `event_split_decision_sha256` | **null — missing decision** |
| `input_manifest_sha256` | **null — missing derived manifest** |
| `protocol_profile_sha256` | **null — protocol choice unresolved** |
| `r04_scope_decision_sha256` | **null — scope decision missing** |
| `stage21_promotion_receipt_sha256` | **null — approved Stage-2.1 evidence/receipt missing** |

Therefore EVAL-AUTH was **not** recorded; general engineering authorization, LEG-EXEC authorization, chat statements or candidate hashes cannot replace this record.

## Blocker mapping and human actions

The full dependency map and sources are in `docs/FINAL_READINESS_EVIDENCE_PREREQUISITES_20261019.md`. In short:

1. **Stage-2.1 records:** Before real review, resolve D1 review-duration policy using genuine pilot timing data, D3(a) second-review trigger and D3(c) clear-boundary audit mechanism/frequency; obtain explicit ADJ-AUTH; provide a proper human-controlled real-data review workflow; and list any required independent second reviewer in the maintained allowlist. The existing `adjudication_session.py` is synthetic-only and cannot create real-event records. Nothing here authorizes real review or adjudication.
2. **Split:** Researcher decides a valid analysis design after considering the one-crossing/one-session leakage finding. The deterministic hash allocation is candidate only and not leakage-safe.
3. **Protocol:** Researcher selects v9 or M4. No default was selected.
4. **R04:** Researcher chooses per-event camera scope. Calibration diagnostics do not approve scope; no unsynchronized clocks were fused.
5. **Manifest:** Engineering builds from verified decisions and real output payloads only after those prerequisites exist.
6. **EVAL-AUTH:** Researcher records an exact-hash-bound authorization last, once all live evidence bindings exist. It cannot grant physical/field/safety authorization.

## Evidence packages generated

All new generated review artifacts are in `docs/generated/final_readiness_20261019/`, avoiding overwrites of pre-existing untracked reports.

### Stage-2.1 human review queue

- `STAGE21_REVIEW_QUEUE.json` — schema `stage21-review-queue/4`, 27 cohort-qualified actionable events, all 27 `INVALID` because verified invalidation notices apply to legacy records. Each includes active candidate proposal/hash, source video paths and inventory hashes, all **25 required Stage-2.1 fields**, six candidate boundary states/rationales, explicit human actions, and D1/D3/ADJ-AUTH prerequisites.
- `STAGE21_REVIEW_QUEUE.md` — reviewer-facing rendering with the same candidate-only boundary.
- Queue/report SHA-256: JSON `bf8fd7dc53a8bfa417766004bbf3fe9fcf36381ff1de9a705236ea364f97b034`; Markdown `4e056fe2da8e983808aaef53e8604bf7979c57ec703c99de3a30203b27b66e51`.

The package does not edit/migrate legacy records, promote proposals to labels, or create a Stage-2.1 record.

### Event split proposal

- `CANDIDATE_EVENT_SPLIT_PROPOSAL.json` — schema `candidate-event-split-proposal/4`, deterministic SHA-256 assignment, 16/6/5 candidate train/validation/test counts, inventory/proposal input hashes, and both crossing/session overlap inventories by role.
- All 27 events share `crossing_A` and `session_20260914_morning`; both groups span all three roles. `grouping.leakage_safe: false`; no group metadata is missing. This candidate is **not approved and is not leakage-safe**. Researcher must determine whether a different design/new independent recording groups are necessary.
- Artifact SHA-256: `a2faad3e50aa693ace4608c252f8249e330feb25926608dd6c80942a5eb51ed0`.

### R04 and protocol evidence

- `r04/R04_EVENT_EVIDENCE.json` — schema `r04-event-evidence/2`; 27 events; 11 calibration-supported candidates, 9 ambiguous, 7 provisional; source hashes and current proposal versions recorded. For engine event 001, active v3 SHA-256 `aa0d94d83e16975fc6930bbd27cd874c7394959e4343c8c8ce02674d771f648a` is distinguished from frozen snapshot v2 SHA-256 `c72f555b8a12ece3110d94dfc64eea50e234cf084bdfcd8cea22f156e02ff54d`; no snapshot timestamps are used to fill absent current-proposal values.
- Candidate coverage diagnostics: v9 has candidate T1+T4 values for 10/11 calibration-supported train events; M4 has candidate T4 values for 22/24 train/engine events. These are **not** approved-label denominators. There is no accepted scope, approved ground truth, replay trace or `t_blocked`; official evaluable counts are **0** for both. Candidate evaluability flags fail closed.
- `r04/R04_EVENT_SCOPE_REPORT.md` contains per-event active proposal/hash, R04 verdict, T1/T4 candidate values, states, reference cameras and decision status. Calibration availability is not scope approval.
- `r04/PREMATURE_OPENING_V9_M4_COMPARISON.md` gives exact definitions, half-open/strict boundary behavior, command-vs-physical-blocked semantics, T0–T4 roles, censoring/exclusion rules, clock compatibility, engine/no-train cases, M5 `never_protected`, trace sampling limits, and denominator implications. Decision remains UNRESOLVED.
- Artifact SHA-256 values: JSON `9aa4d8490c824725179b68722e0babeab63551685fda82d168f71846ae3a47b8`; scope Markdown `96915453f3b99f327e2874b0b5582c464aadd4c80e48aed215fd6be362ab92c0`; comparison Markdown `5660065a5346c221d1e349c5e15e1fda10c93c02d6ba53c8106f84e9481fb96e`.

The R04 source fingerprints are: Layer-B inventory `5585e22ecc7841e2cca4d8e56b9d61999e252e1efaf5dfa6e57d81471b809a56`; candidate snapshot `7eaa0c9bde777d4b36ead21d0654d511cc103255c5bf965e8bc50417a3b8e4e1`; calibration verdicts `46cbcb030305150c606fbbd882882530430d7873e2b5954adb409ffaa080738c`; calibration candidate manifest `2a2f3faa88ae9ffa3e49cd4fb26cf32f3e1595cf0e24422a1dd198102df51f69`.

## Engineering changes

Modified additive candidate reporting in:

- `src/railway_detection/annotation/candidate_split_queue.py`
- `scripts/build_candidate_split_and_review_queue.py`
- `src/railway_detection/data/r04_evidence.py`
- `tests/test_candidate_split_queue.py`
- `tests/unit/test_r04_evidence.py`
- `docs/CANDIDATE_SPLIT_AND_STAGE21_QUEUE.md`

Changes add per-event Stage-2.1 checklists and human-action review packages; explicit independent crossing/session leakage details; candidate-only Markdown; current active-proposal R04 provenance; and fail-closed candidate-vs-official evaluability semantics. No readiness predicate, approval state, human choice, annotation, authorization, input manifest, or official result was added or altered.

## Final verification

- Full suite: `venv/bin/python -m pytest -q` — **1,206 passed in 24.22s**, exit 0.
- Focused changed-surface regression: **90 passed** across candidate split/queue, R04 evidence, Phase 12 governance and documented metrics.
- `venv/bin/python -m compileall -q src scripts` — passed.
- Targeted Ruff with `--ignore E501` on the changed code/test set — passed. Ruff `UP` on the changed queue module/script/tests — passed. This avoids broad E501 cleanup of pre-existing long lines.
- `venv/bin/python -m pip check` — **No broken requirements found**.
- Changed-file `git diff --check` — passed.
- Reproducibility audit — **6 PASS / 0 FAIL / 5 UNRESOLVED / 2 NOT_AVAILABLE**; 0 active claim findings, 9 archival historical findings retained.
- Official readiness — exit 3; not ready; 9 instances / 7 codes.
- Stage-2.1 readiness — exit 2; `NO_RECORDS`; no promotion receipt.
- LEG-EXEC repeat — exit 0, completed, 27 original records byte-identical, 28/28 expected outputs present and verified, `ground_truth_created: false`, **0 new files**, 0 failures, 0 missing outputs.
- Live-media integrity: independently hashed all **54** front/back video files (**3,821,594,887 bytes**) against the Layer-B inventory; 0 mismatches.
- Deterministic artifact regeneration: all six generated artifacts above matched byte-for-byte in a separate `/tmp` output directory.
- Repository HEAD stayed `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`; 18 tracked dirty paths and 306 untracked paths remain; staged changes: 0. Existing dirty state was preserved; no stage/commit/reset/clean/broad revert occurred.

## Smallest defensible path forward

1. Resolve Stage-2.1 process prerequisites and authorize a legitimate real-data human review workflow; enlist/allowlist an independent reviewer if D3 requires one.
2. Conduct new media-grounded reviews and required independent review/adjudication. Obtain a valid promotion receipt only after the live media-hashing readiness workflow reports READY.
3. Researcher resolves a leakage-valid split/design; if the intended held-out design requires group independence, acquire independent crossing/session data rather than treating a random event partition as leakage-safe.
4. Researcher records the v9/M4 endpoint and R04 event-scope decisions; engineering must not infer either.
5. Build/verify the input manifest from approved decisions and real payloads.
6. Record EVAL-AUTH bound to the exact live hashes; rerun readiness. Only if the live gate reports ready may official evaluation be authorized/run.
7. Phase 13, field activity, target-hardware measurements, and safety authorization remain separate future gates.