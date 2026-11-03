# Researcher Readiness Verification — 2026-10-19 14:56 UTC

**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**HEAD before/after:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Disposition:** audit and researcher action package added; no workflow code retained; no researcher decision, human review, media write, evaluation manifest, or EVAL-AUTH created.  
**Companion action package:** `docs/RESEARCHER_ACTION_PACKAGE_v1_20261019.md`.

## 1. Verified live gate and reproducibility state

Live official command:

```text
PYTHONPATH=src venv/bin/python -m railway_detection evaluation status \
  --repository-root /Users/sayemuddin/Desktop/Train_automation
```

Exit **3**, `ready: false`, **9 blocker instances across 7 codes**:

- `COHORT_APPROVAL_MISSING` ×3 (derived from absent/invalid Stage-2.1 approval evidence).
- `EVAL_AUTH_NOT_GRANTED`.
- `EVENT_SPLIT_DECISION_MISSING`.
- `MANIFEST_MISSING`.
- `PREMATURE_OPENING_DEFINITION_UNDECIDED`.
- `R04_SCOPE_DECISION_MISSING`.
- `STAGE21_RECORDS_MISSING`.

Current `live_bindings`: policy `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575`; frozen config `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`; split, input manifest, protocol profile, R04 decision, and Stage-2.1 receipt are null. EVAL-AUTH was correctly not created.

Live reproducibility audit:

```text
venv/bin/python scripts/audit_reproducibility.py --root /Users/sayemuddin/Desktop/Train_automation \
  --json /tmp/current_repro.json --md /tmp/current_repro.md
```

**6 PASS / 0 FAIL / 5 UNRESOLVED / 2 NOT_AVAILABLE.** The two unavailable items correspond to official evaluation-result provenance and official Phase 13 experiment-manifest completeness; no such authorized run exists. Historical manuscript findings remain separately archived.

Live ground-truth readiness audit: **27** original review JSONs, all schema `6.0.0`; **0** valid Stage-2.1 records; **0** pending media-rehash eligible; promotion receipt missing. The maintained reviewer allowlist loads and contains one identity. The 27 originals have verified sibling invalidation notices; no record was migrated.

## 2. Live input and integrity checks

### Active Layer-B media

- Layer-B inventory SHA-256: `5585e22ecc7841e2cca4d8e56b9d61999e252e1efaf5dfa6e57d81471b809a56`.
- Video source manifest SHA-256: `bfd86e04b996d1edfe030a48689e99c423ba5bfeadd906dc33b03ba49fd54e7d`.
- Independent media-audit SHA-256: `213cbb1308363ebd92841e149d6479aa56638e867580a7be66a56d3134ea8bdf`.
- All **54 active** front/back source videos were independently re-hashed against the inventory: **54/54 match**, 0 mismatches. Reproducible path+content aggregate: `7468e415b383ebd93c5b44162dcacb7afee598d152b120395e8ae5204d37d93a` using SHA-256 over sorted `relative_path NUL file_sha256 LF` entries.
- The manifest has 56 video rows total. All **56/56** listed destinations match the row hashes, including two historical duplicate streams; those duplicate streams remain explicitly evaluation-excluded.
- The extra two `Unseen_Video/Screen Recording ... .mov` files do not appear as event/camera sources in the source manifest or active inventory; their event/session provenance is absent. They were not considered evaluation candidates.

### Capture-session evidence and correction to prior summaries

The active proposals all contain `proposed_site_metadata.crossing_id: crossing_A` and `recording_session_id: session_20260914_morning`. The live active event/proposal hashes match the candidate split proposal (27/27). However, these copied proposal session values conflict with independently inspected media metadata and the independent audit:

- `train_events/event_001` through `event_020`: **2026-09-14**, approximately 14:13–17:26 local.
- `train_events/event_021` through `event_023`, all three no-train events, and the engine-only event: **2026-10-04**, approximately 19:22–19:59 local.

The source-manifest identities/hashes and QuickTime recording tags support these two dates; the independent audit also notes device changes (iPhone 15 Pro Max back camera for events 001–020; iPad 10th-generation back camera for events 021–023/controls). These tags and devices establish a provenance conflict and a plausible two-session partition; they do **not** independently certify a crossing's geodetic identity or prove all event pairings are physically independent. The 27 active events therefore cannot honestly be described as one verified recording session. Conversely, the evidence does **not** establish three independent sessions or multiple independent crossings. All active proposals name only one candidate crossing ID; a separate site survey/custody record would be needed to validate that identity.

The previous readiness report's description of all 27 as one session was based on repeated proposal metadata, not a reconciliation against the source-video timestamps. That statement is superseded by this additive verification. Original candidate artifacts were not rewritten.

### Current candidate event split

Candidate split artifact SHA-256: `a2faad3e50aa693ace4608c252f8249e330feb25926608dd6c80942a5eb51ed0`; status remains `CANDIDATE_ONLY` / `NOT_APPROVED`. Its 16/6/5 partition distributes:

- 2026-09-14 group: train 13 / validation 5 / test 2.
- 2026-10-04 group: train 3 / validation 1 / test 3.

Thus both observed sessions cross all three candidate roles. It is not session-disjoint and cannot support independent-session testing. With only two observed session groups, one session could be reserved for a limited exploratory shift analysis, but there would be no third independent group for validation; the sessions also confound device, time of day, night conditions, and cohort composition. A held-out session does not provide an unseen-crossing claim. The evidence package is kept unapproved; no new split was produced.

### Candidate review and R04 artifacts

| Artifact | Live SHA-256 | Verification |
|---|---|---|
| `docs/generated/final_readiness_20261019/STAGE21_REVIEW_QUEUE.json` | `bf8fd7dc53a8bfa417766004bbf3fe9fcf36381ff1de9a705236ea364f97b034` | 27 cohort-qualified items, `CANDIDATE_ONLY` / `NOT_APPROVED`; all active proposal hashes checked 27/27. |
| `docs/generated/final_readiness_20261019/CANDIDATE_EVENT_SPLIT_PROPOSAL.json` | `a2faad3e50aa693ace4608c252f8249e330feb25926608dd6c80942a5eb51ed0` | 27 active proposal hashes checked 27/27; deterministic but not approved; does not group-disjoint by the two supported capture sessions. |
| `docs/generated/final_readiness_20261019/r04/R04_EVENT_EVIDENCE.json` | `9aa4d8490c824725179b68722e0babeab63551685fda82d168f71846ae3a47b8` | Four declared source hashes verified against live bytes; verdict counts 11 supported / 9 ambiguous / 7 provisional. |
| `docs/generated/final_readiness_20261019/r04/R04_EVENT_SCOPE_REPORT.md` | `96915453f3b99f327e2874b0b5582c464aadd4c80e48aed215fd6be362ab92c0` | Candidate evidence only. |
| `docs/generated/final_readiness_20261019/r04/PREMATURE_OPENING_V9_M4_COMPARISON.md` | `5660065a5346c221d1e349c5e15e1fda10c93c02d6ba53c8106f84e9481fb96e` | Comparison only; neither choice accepted. |

On the 11 `CALIBRATION_SUPPORTED` events, the R04 JSON labels ten candidate T1/T4 values as observable/unapproved and event 005's T1/T4 as unobservable/right-censored; candidate availability does not make these approved labels, accepted synchronization, replay events, or metric-evaluable examples. The five remaining ambiguous/provisional events are still outside supported synchronization. Nothing was fused or approved.

## 3. Stage-2.1 workflow and decision state

- `src/railway_detection/annotation/adjudication_session.py` still enforces `synthetic_` IDs and temporary-only paths; it never promotes. This is the correct safety boundary until a separate genuine-human workflow and its operation-specific authorization are ready.
- `docs/PHASE11_11_ADJUDICATION_PROTOCOL.md` marks ADJ-AUTH not granted. There is no `data/governance/stage21_human_review_pilot_authorization.json`; no formal ADJ-AUTH record exists either.
- No genuine review was performed in this task. No pilot record, boundary label, reviewer identity, signature, threshold, or approval was created.
- A pilot-workflow implementation was attempted and its focused test suite did not converge; the two newly introduced code/test files were removed. The final repository status matches its captured pre-document baseline. No failed prototype is being presented as a deliverable.
- The actionable package gives an exact, bounded timing-pilot authorization request, while keeping the official review namespace and current synthetic-only runner locked. Formal review requires a distinct authorization after the timing pilot and remaining D1/D3 prerequisites.
- D1 mechanism D, D2 mandatory allowlist, D3(a) B+C, D3(b) no numeric tolerance, D3(c) audit requirement, and D4 B+C were checked in the authoritative decision register. Do not re-ask the settled portions; exact remaining values/actions are listed in the action package.
- Existing `docs/PHASE11_6_OPEN_ISSUE_REGISTER.csv`: 23 open unresolved boundary rows across nine event keys. The Phase 11.3 decision says D3(a)'s fixed subset is named by this register, while the Phase 11.10 closure package says the subset's authority must be confirmed before implementation. I did not infer that all 23 rows, or a guessed smaller set, are the exact binding subset. A numbered researcher clarification identifying exact row IDs and the source-register hash is required; B+C and no tolerance remain the already-selected policy.

## 4. Premature-opening record semantics

No selection was made. Exact implementation semantics were verified from `protocol_choices.py`, `metrics.py`, the comparison report and protocols:

- **v9** `t1_entry_to_t4_clearance`: `[T1,T4)`; implemented replay flag additionally requires OPEN/OPENING and not physically passage-blocked. Requires approved observable T1 and T4 on a common accepted timeline. Missing/ambiguous/unobservable/right-censored T1 or T4 -> excluded with reason. Openings before T1 are outside v9. Physical left-censored T0 is never replaced by point time 0.
- **M4** `first_blocked_to_t4_clearance`: first blocked replay tick `t_blocked`; failure on opening command or blocked→unblocked strictly within `(t_blocked,T4)`. Requires replay trace and back-clock T4; not T1 or cross-clock fusion. Missing/censored T4 -> not evaluable. Never blocked before T4 -> separate M5 `never_protected`, not an M4 success, excluded from M4 denominator. T0 is not part of its predicate.
- T3 is locomotive-unit clearance, not tail clearance; it does not substitute for missing T4 except the documented engine-only identity rule after independent adjudication. No-train train-boundary metrics are not applicable. Censoring/unobservability is not a zero/favorable value.

The researcher records the choice in `data/manifests/phase12_protocol_decision.json`; the gate accepts only implemented option values and uses the resulting effective protocol profile hash.

## 5. Manifest and EVAL-AUTH remain blocked

No official split decision, protocol decision, R04 decision, approved Stage-2.1 records, promotion receipt, evaluation input manifest, or EVAL-AUTH exists. The existing manifest builder refuses missing/invalid researcher decisions, event-set mismatches, and overwrite. It should only run after genuine upstream records, decisions, and real inference/replay payloads are available. EVAL-AUTH has seven required live bindings; only frozen config and policy are currently populated. No signature or fake human authorization was generated.

## 6. LEG-EXEC, frozen artifacts, and worktree

- `docs/generated/LEG_EXEC_OPERATION_REPORT.json` SHA-256 `1345e2741408c9baab214cb3606a99680606961bdec2b64364e8f80da32d4f1f`; `data/governance/leg_exec_authorization.json` SHA-256 `77933986b42b44d340723227c8319a4fb90687a9d6dbe00133de39780bd9cb7e`.
- The report is completed with the operation-specific recorded statement, `ground_truth_created: false`, originals byte-identical, 27 sources, 28 expected outputs, zero failures, zero missing outputs. The directory has 27 sibling invalidation notices and one integrity notice. This operation does not approve labels or adjudication.
- A fresh hash of the sorted 27 original review files was saved outside the repository at `/tmp/reviews_before_next_milestone.sha256`; aggregate hash of that list file: `903833b4b2f03628fa934550b216c04853d3d2d4285e2fceb018ed276ef41786`. All 27 were independently re-hashed against on-disk bytes at task start; the original Stage-2.1 review records were never written.
- Frozen config, policy and vision checkpoint hashes match the previously verified values: config raw `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a`, canonical `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`; policy raw `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575`; vision checkpoint `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd`.
- The two attempted prototype files were removed; serialized `git status --porcelain -z` before docs equals the pre-task baseline snapshot: **18 tracked modified paths, 307 untracked paths, 0 staged**. HEAD unchanged. Existing user dirty contents remain untouched.

## 7. Validation and next milestone

**Final verification time:** 2026-10-19 14:56 UTC.

Final validation after the docs were written:
- Focused Stage-2.1, pending-decision, candidate-split/queue, R04, Phase-12 governance/documented metrics, ground-truth audit and blocker-report tests: **150 passed in 1.71s** (final run).
- Full suite `venv/bin/python -m pytest -q`: **1,206 passed in 28.71s**, exit 0 (final run).
- `venv/bin/python -m compileall -q src scripts`: passed.
- `venv/bin/python -m pip check`: **No broken requirements found**.
- Live reproducibility audit: **6 PASS / 0 FAIL / 5 UNRESOLVED / 2 NOT_AVAILABLE**.
- Live official gate: exit **3**, `ready: false`, 9 blockers / 7 codes; no binding changed.
- Docs structural check: both files parse as text, Markdown fences balance, all seven live blocker codes and requested decision terms appear. No code workflow remains from the failed prototype attempt.
- No official evaluation run was attempted. The readiness status command is read-only and remains blocked.

**Next milestone:** researcher first authorizes **engineering preparation only** of the timing pilot described in `docs/RESEARCHER_ACTION_PACKAGE_v1_20261019.md`; engineering implements/tests the human-only, hash-bound, non-approved workflow. The researcher then reviews its released version/hash and issues a separate activation addendum before any real-media use. After genuine timing data, the researcher records D1 numeric thresholds and D3(c) audit policy; engineering implements the already-selected D3(a) B+C trigger; the researcher issues separate formal ADJ-AUTH; genuine Stage-2.1 review and promotion/receipt follow. In parallel, the researcher resolves the session-aware analysis design, R04 scope and v9/M4 choice. Manifest, then EVAL-AUTH, come last.

No new genuine-review code is retained, because authorization is absent and the prototype did not pass its focused validation. The documented next step is therefore an authorization-bound engineering milestone, not a claim of review readiness. Official evaluation remains not ready and no blocker was artificially removed.