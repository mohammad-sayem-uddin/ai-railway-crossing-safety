# Researcher Action Package — Genuine Review and Evaluation Readiness

**Version:** 1.0  
**Prepared:** 2026-10-19 14:56 UTC  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Status:** ACTION REQUIRED — no new authorization, research decision, label, pilot record, or evaluation artifact was created.  
**Live gate:** `ready: false`; 9 blocker instances / 7 codes. The three cohort-approval rows are derived from the missing Stage-2.1 records, not three extra decisions.

This package starts from the 2026-10-19 readiness reports and the live repository. It corrects one important provenance statement in the earlier split discussion: the proposals assign one session ID to all 27 events, but source-video metadata and the independent media audit identify **two capture dates/sessions**, not one. Both sessions still share the same proposed crossing identity, and the present 16/6/5 allocation mixes sessions across partitions. Exact evidence and hashes are in the companion report `docs/RESEARCHER_READINESS_VERIFICATION_20261019T1456Z.md`.

## 1. Current gate output and independent prerequisites

Command:

```text
PYTHONPATH=src venv/bin/python -m railway_detection evaluation status \
  --repository-root /Users/sayemuddin/Desktop/Train_automation
```

Exit **3**; `ready: false`; **9 blockers / 7 codes**. Current `live_bindings`: frozen config `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e` and policy `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575` are present; event split, manifest, protocol profile, R04 decision, and promotion receipt are `null`.

| Exact gate blocker ID | Current live gate output | What evidence already establishes | Unknown / exact next action | Options and consequences | Dependencies and validation / recording |
|---|---|---|---|---|---|
| `STAGE21_RECORDS_MISSING` | No active Stage-2.1 records; **0** schema `8.1.0-stage2.1`; the 27 legacy records are excluded by verified notices. | 27 original v6 records are preserved unchanged; source/proposal hashes are in the queue; the schema and promotion gate exist. The adjudication runner in `src/railway_detection/annotation/adjudication_session.py` explicitly accepts synthetic IDs and temporary paths only. The Phase 11.9 pilot used synthetic data only. | First authorize a bounded **non-evaluative timing pilot** naming event(s), allowlisted reviewer(s), original-media use, output location outside official reviews, and no approval/promotion. Engineering must then provide and test a real-media, human-only pilot interaction before the reviewer uses it. After timing evidence and remaining decisions, authorize formal Stage-2.1 review separately. | (A) Timing-only pilot: yields genuine timing observations but creates no official labels. (B) Defer: leaves D1 numeric thresholds unresolved. Do not use the synthetic runner or manually copy proposal values into records. | Separate pilot authorization path proposed below; after a future pilot, validate media hashes, visible boundary fields, identity/times, append-only history and non-approval status. Official records require a distinct formal workflow and explicit ADJ-AUTH. Promotion/readiness must re-hash original media and issue a receipt only on READY. The resulting approved record set is what clears this blocker and the three derived cohort rows. |
| D1 numeric threshold (upstream of genuine-review readiness; not a separate Phase-12 gate code) | `STAGE21_RECORDS_MISSING` remains; official gate reports no Stage-2.1 records. | D1 mechanism D was selected 2026-10-14; the 30.0s flat schema floor is only a sanity check. Synthetic 600s pilot timing is expressly not human review duration. | After an authorized real timing pilot, researcher chooses and records a hard floor and fast-band upper threshold from observed durations, or explicitly defers final numbers. | (A) Set values from the real timing observations and route the fast-but-passing band to second review per D1. (B) Defer numbers; existing 30.0s floor remains only as current mechanical check and does not implement the selected band. No numeric recommendation is made here. | Record values and rationale as a numbered update to D1 in `docs/PHASE11_3_RESEARCHER_DECISIONS.md`; engineering then implements the recorded values and adds boundary tests. No pilot duration is usable unless it is a genuine human session. |
| `COHORT_APPROVAL_MISSING` ×3 (`engine_events`, `no_train_events`, `train_events`) | One derived diagnostic per cohort: no approved valid Stage-2.1 record. | These are not independent decisions; each follows from `STAGE21_RECORDS_MISSING`. | No separate researcher decision. Create valid, genuinely reviewed and approved records per required cohort under the approved process. | No separate option. Do not create one placeholder record per cohort. | Clears automatically with valid records plus successful media-hash readiness/receipt. |
| `EVENT_SPLIT_DECISION_MISSING` | `data/splits/phase12_event_split_decision.json` absent. Candidate `CANDIDATE_EVENT_SPLIT_PROPOSAL.json` is `CANDIDATE_ONLY` / `NOT_APPROVED`. | The 27 event/video pairs have live hashes matching the Layer-B inventory. Source metadata supports two capture sessions (20 events on 2026-09-14; 7 events on 2026-10-04), one candidate crossing, and the current 16/6/5 candidate random allocation overlaps both sessions among roles. | Decide the intended generalization claim and partition/design. Do **not** approve the existing random split as leakage-safe. Decide whether a two-session sensitivity analysis is useful, or whether new independent crossing/session data is required for train/validation/test. | (A) Retain random event partitions only for explicitly descriptive within-dataset development; no independent-session generalization claim. (B) Hold out the 2026-10-04 session against 2026-09-14 for a limited session-shift sensitivity analysis; this provides only two groups, no group-disjoint third validation partition, and the date/device/night/cohort differences are confounded. (C) Collect additional independently documented crossings/sessions for a group-disjoint train/validation/test design. None is selected here. | Record a researcher-authored decision envelope at this exact path using schema `phase12-event-split-decision/1`, with `partitions` containing cohort-qualified event keys, plus the common decision fields (`decision_status`, `decision_id`, `decided_by`, `decided_at_utc`, `researcher_statement`). Current verifier checks event-level IDs are nonempty and nonoverlapping; it does not establish group independence. Before acceptance, verify every capture source, all split groups, no adjacent/duplicate scene leakage, and the intended claim. Bind the final live decision hash in later artifacts. |
| `PREMATURE_OPENING_DEFINITION_UNDECIDED` | No `choices.premature_opening_window` in `data/manifests/phase12_protocol_decision.json`; v9/M4 both implemented, neither selected. | The current comparison document defines both predicates and code behavior. T0 physical arrival is left-censored when already present at recording start; true T0 is `≤ 0`, not an observed numeric point. T4 missing/right-censored means the primary clearance endpoint is unavailable. | Researcher must select exactly one implemented choice: `t1_entry_to_t4_clearance` (v9) or `first_blocked_to_t4_clearance` (M4), and record rationale and consequences. | **v9:** opening during `[T1,T4)`; requires approved observable T1/T4 on a compatible common timeline; excludes pre-T1 opening and missing/ambiguous/censored T1 or T4. Implemented per-sample flag additionally requires OPEN/OPENING and `not is_passage_blocked`. **M4:** first blocked replay tick is `t_blocked`; opening command or blocked→unblocked during `(t_blocked,T4)` is failure; T1 is not needed, but a back-clock T4 and replay trace are. A never-blocked-before-T4 event is M5/never-protected and excluded from M4 denominator, not a success. Neither treats left-censored T0 as a point time. | Record in `data/manifests/phase12_protocol_decision.json`, schema `phase12-protocol-decision/1`, `choices.premature_opening_window`, common decision envelope, statement and rationale. Validate against `protocol_choices.validate_protocol_choices`; confirm effective profile hash from the live readiness gate. Downstream: manifest/effective protocol binding and EVAL-AUTH. |
| `R04_SCOPE_DECISION_MISSING` | `data/manifests/phase12_r04_scope_decision.json` absent. | Evidence JSON is bound to live source files. Diagnostics: 11 `CALIBRATION_SUPPORTED`, 9 `AMBIGUOUS`, 7 `PROVISIONAL`. These are candidate calibration statuses, not approved clock fusion, labels, scope, or metric eligibility. | Choose a camera mode for **each** decided event and the accepted synchronization subset, if any. Resolve or exclude non-supported calibration events from dual-camera scope; decide independently whether independent-camera replay is in scope. | (A) `independent_camera` where appropriate: separate media-local clocks, no fused timing claims. (B) `dual_camera` only for researcher-accepted and calibration-supported events; this does not validate boundaries. (C) `single_camera` if deliberately selected and supported by the evaluation design. Combinations are possible per event. No mode/event set is selected here. | Write `data/manifests/phase12_r04_scope_decision.json`, schema `phase12-r04-scope-decision/1`, with `event_modes` covering exactly all split events and `accepted_sync_events`, plus the common decision envelope. Validate with `governance.check_r04_body`; verify accepted events against live calibration evidence. The manifest builder and replay producer depend on this. |
| `MANIFEST_MISSING` | `data/manifests/phase12_evaluation_inputs.json` absent. | `src/railway_detection/evaluation/manifest_builder.py` exists and refuses missing/invalid split and R04 records, mismatched event inputs, and overwrites. | Engineering supplies real inference/replay source payloads and runs the builder only after upstream decisions, eligible approved labels/receipt, and payloads exist. | No researcher choice to ask; this is a derived artifact. Do not create a placeholder manifest. | Build after Stage-2.1 readiness, accepted split, R04 scope, protocol choice and real payloads. Verify every source SHA-256 and that derived hashes match the decision artifacts. This manifest supplies one of seven later EVAL-AUTH bindings. |
| `EVAL_AUTH_NOT_GRANTED` | `data/governance/eval_authorization.json` absent; 5 required live bindings remain null. | Verifier requires an allowlisted researcher statement and seven live hashes; it explicitly does not accept a chat statement as a record and cannot grant field/physical authority. | Request only after all upstream records/receipt/manifest are live and verified. Researcher then explicitly authorizes the named evaluation stage and its exact scope. | Authorize that specific evaluation, or decline/defer. No evaluation runs if absent/invalid. Do not create it now. | Record using `phase12-eval-authorization/1`, bind policy, split, frozen config, manifest, protocol profile, R04 scope, and promotion-receipt hashes exactly as printed by live `evaluation status`. Validate record digest and all live bindings; rerun readiness. |

## 2. Researcher decisions already on record — do not re-decide them

The authoritative register `docs/PHASE11_3_RESEARCHER_DECISIONS.md` records, dated 2026-10-14:

- **D1 mechanism:** option D (fast-but-passing band routed to second review) is selected. **The hard floor and upper-band numeric threshold remain pending** because they are to be based on genuine human review timing, not synthetic timing.
- **D2:** mandatory reviewer allowlist (B) is selected and implemented. The live file contains only `raihankabirrahu@gmail.com`; no second reviewer is registered. Adding an identity requires that person's explicit authorization from the researcher.
- **D3(a):** second review for a first-reviewer UNCERTAIN boundary **plus** a fixed subset is selected (B+C). **D3(b):** no numeric disagreement tolerance (A) is selected. The current `docs/PHASE11_6_OPEN_ISSUE_REGISTER.csv` has 23 open unresolved boundary rows across nine event keys: `train_events/event_004`, `006`, `007`, `009`, `011`, `013`, `015`, `018`, `021`. The exact binding fixed-row set still needs a numbered clarification: the Phase 11.3 register points to a fixed subset but does not enumerate it there, and Phase 11.10 says its authority must be confirmed before implementation. Confirm/reconcile the exact row IDs using these authoritative records; do not re-decide B+C/no-tolerance or infer a subset from this report. The trigger logic is not implemented.
- **D3(c):** the requirement to audit boundaries marked clear is selected; the **audit method and frequency remain undecided**. Researcher must specify these before any clear-only boundary can be treated as final/promoted. Options recorded in the decision package include a declared spot-check percentage/frequency or a documented lightweight check of every clear boundary; no option is selected.
- **D4:** reviewer-observed hashes at review plus live media re-hash at promotion (B+C) is selected and implemented in schema `8.1.0-stage2.1` and `promotion_gate.py`.
- **LEG-EXEC:** full disposition and sibling-notice mechanism were selected and separately authorized/executed. The live operation report confirms 27/27 originals byte-identical, 28/28 notices present, zero failures/missing outputs, `ground_truth_created: false`. Do not request LEG-EXEC again.

## 3. Exact authorization request — timing pilot only

**Current state:** no genuine-review authorization artifact exists. The synthetic-only runner cannot be repurposed. The following is a request for a separate, narrow authorization; it is not itself an authorization and must not be transcribed as one until the researcher explicitly adopts it and fills the exact scope.

> **Researcher action:** authorize or decline a bounded Stage-2.1 human-review timing pilot. If authorizing, personally specify (1) exact cohort-qualified event key(s), (2) which already-allowlisted reviewer identity/identities may participate, (3) the timing-only purpose, (4) that original source media may be opened locally for human review, (5) the output directory `data/ground_truth/review_pilots/`, and (6) that pilot records are not labels, are never approved ground truth, are not promotable, do not satisfy official cohort approval, and confer no EVAL-AUTH or field authority. State that the reviewer must not consult model outputs or candidate timestamp values, and that live source/proposal hashes must match before and after inspection. This pilot is solely to collect genuine review-duration observations for D1; it does not decide D1 thresholds or the D3(c) audit frequency.

The eventual operation-specific authorization artifact (not created now) should bind:

```text
schema_version: stage21-human-review-pilot-authorization/1
authorization_id: researcher-supplied unique ID
authorized_by: allowlisted researcher identity
authorized_at_utc: actual time of authorization
authorization_statement: researcher-authored statement with the restrictions above
scope.operation: stage21_human_review_timing_pilot
scope.purpose: genuine_review_timing_pilot
scope.event_keys: exact researcher-selected cohort/event keys
scope.reviewer_ids: exact researcher-authorized, allowlisted identities
scope.output_directory: data/ground_truth/review_pilots
scope.source_inventory_sha256: live inventory hash
scope.media_sha256_by_event: live front/back source hashes for each selected event
scope.active_proposal_sha256_by_event: live active-proposal hash per event (binding only; candidate values are not presented)
scope.no_official_approval: true
attestation: recorded unsigned researcher statement (signature null; not cryptographic)
recorded_by: accurate researcher or agent-transcription provenance
record_sha256: deterministic hash of the completed record
```

### Authorization statement requested from the researcher (fill and affirm explicitly)

This is a **request/template only**. Bracketed fields must be completed by the researcher; its presence here does not grant permission. Do not transcribe this text into an authorization record unless the researcher explicitly affirms the completed statement.

```text
I explicitly authorize preparation of the bounded, non-evaluative Stage-2.1
genuine-media review timing pilot identified by authorization ID
[RESEARCHER-SUPPLIED ID].
This authorization does not permit media opening or review until I have
reviewed the released pilot workflow version/hash and have
explicitly activated this authorization in a dated, hash-bound addendum.
The exact cohort-qualified event keys are [RESEARCHER LIST]; the only authorized
reviewer identity/identities are [RESEARCHER LIST OF ALLOWLISTED IDENTITIES].
The only purpose is to observe genuine human review-session durations for the
D1 pilot. For those exact events, each named reviewer may open and inspect the
original front/back source video files whose current SHA-256 hashes are bound in
the authorization record. Active proposal hashes are bound for provenance only;
the proposal text and candidate values must not be shown to the reviewer. No
model prediction, model output, candidate timestamp, candidate label, or prior
evaluation result may be shown or used to determine a boundary. The permitted
output location is data/ground_truth/review_pilots/ only. Any resulting record
must be labeled HUMAN_REVIEW_COMPLETED_UNAPPROVED_PILOT, must have
ground_truth_eligible=false, must not be written as *_review.json, must not be
promoted or loaded as ground truth, and does not approve any label, protocol,
event split, R04 scope, official evaluation, field activity, or physical railway
operation. Stop without writing if identity, authorization scope, inventory,
source/proposal hash, media visibility, or activation state is uncertain or
mismatched. I understand this is a recorded unsigned statement, not a cryptographic signature
or authenticated access-control guarantee.
```

The structured example above includes `scope.active_proposal_sha256_by_event` in addition to the explicit source-media binding fields. The authorization verifier must bind these active proposal hashes as provenance without displaying proposal content to the reviewer. Before media can be opened, a separate activation addendum must bind the tested workflow version/source hash, confirm that the researcher reviewed that workflow, and confirm the exact event/reviewer/output scope remains unchanged. (No pilot authorization or activation is present or implied by this template.)

Required researcher-supplied artifact fields after that explicit affirmation: exact event keys; exact allowlisted reviewer identities; current inventory hash; live front/back source hashes and active-proposal hashes per event; exact output path; actual UTC authorization time; authorization ID; identity/provenance; and a content hash. Before any source video opens, require the later activation addendum to bind the tested workflow source/version hash and verify it against the released implementation. Do not create an authorization or activation record from this template without the researcher's explicit adoption.

**Engineering boundary:** no production pilot path was retained in this milestone. After the researcher authorizes engineering preparation, engineering must first complete and test a dedicated human-only pilot path; the researcher must inspect and activate it by the hash-bound addendum before any live media is opened. Do not remove the synthetic-only guard on `adjudication_session.py`. The pilot path must present original hashed media, keep proposal/model candidates off screen, collect the six human boundary fields and explicit visibility confirmation, measure monotonic review duration, validate chronology only on same-camera clocks, retain uncertainty/censoring, append tamper-evident audit history, write only non-approved pilot artifacts outside `*_review.json`, and fail closed on any binding/identity/authorization mismatch. Any ambiguity or schema gap stops the session. A pilot record can inform timing policy but cannot approve labels or satisfy official Stage-2.1 readiness. Formal adjudication requires a separate later authorization and workflow release.

## 4. Split and independent-data recommendation

### Verified grouping evidence

- The current event proposals all say `crossing_id: crossing_A` and `recording_session_id: session_20260914_morning`; those identical session IDs are stale for at least the later recordings.
- `docs/INDEPENDENT_MASTER_AUDIT.md` §2.5, current QuickTime metadata, and `data/manifests/real_world_v2_video_manifest.jsonl` together support **20 active events recorded 2026-09-14** (train events 001–020) and **7 active events recorded 2026-10-04** (train events 021–023, 3 no-train controls, 1 engine-only event). All 56 video-manifest entries, including the two historical duplicate streams, were re-hashed and matched their manifest hashes. The active 54 also match the Layer-B inventory.
- The same audited source says one crossing, but the active candidate crossing ID is proposal metadata, not a geodetic/site-survey record. Treat “one crossing” as the current documented evidence boundary; verify crossing identity with source custody/site records before making a broader claim.
- Two additional `Unseen_Video/` screen recordings have no event/camera/session/source-manifest mapping. They cannot be added to an evaluation partition without provenance. Two `event_historical_duplicate_010` streams are explicitly historical and evaluation-excluded.
- The active sessions differ in camera hardware and cohort mix: the back camera changes from iPhone 15 Pro Max (train events 001–020) to iPad 10th-generation (events 021–023, negatives, engine). Date/session effects therefore cannot be separated cleanly from device, night-visibility, and class-composition effects in a two-session comparison.

### Design consequences

Event-level random splitting is insufficient for a held-out generalization claim: related events can share the physical crossing, background, camera placement, device, session conditions, and capture workflow. Adjacent frames/crops, repeated scenes, and paired front/back views of one event are even closer dependencies and must never cross partitions.

The current 16/6/5 candidate split gives September 14: 13 train / 5 validation / 2 test; October 4: 3 train / 1 validation / 3 test. It leaks both sessions across all roles. There are two supportable **session groups**, not three; assigning one session to train and one to test could support only a small, explicitly exploratory session-shift sensitivity analysis, with no independent validation group and strong date/device/cohort confounding. It cannot support unseen-crossing generalization. No such alternative is approved here.

For an independent three-way design, collect provenance-verified events from multiple crossings and sessions, then assign the highest relevant independent group (crossing/site, with all its sessions/events/streams/frames) wholly to one partition. A minimal mechanical design requires at least one independent group per partition; a credible estimate requires multiple test crossings and enough sessions/events to show between-group uncertainty rather than treating one crossing as a population. The researcher/statistician should predeclare the required number from the intended claim and power/precision objective. Preserve stable crossing/site IDs, capture-session IDs, original source paths and hashes, device/camera identifiers, timestamps/timezone, event pairing evidence, edits/trims, and custody/consent records. Verify independence from provenance and duplicate/near-duplicate scene checks before splitting.

Claims supportable now are limited to implementation/software behavior, descriptive replay results on specifically named observed events after all review/authorization gates are satisfied, and a clearly labeled exploratory two-session contrast. The data do not support claims of generalization to unseen crossings, broad operating conditions, or safety assurance. Field collection itself requires separate site permission, safety planning, consent/privacy review, and researcher go/no-go; this package authorizes none of those activities.

## 5. R04: evidence-backed candidate scope, not a decision

Raw evidence artifact: `docs/generated/final_readiness_20261019/r04/R04_EVENT_EVIDENCE.json` (SHA-256 in the companion verification report). Its four declared source hashes were rechecked against live bytes.

| Candidate calibration class | Events | Current interpretation / additional evidence |
|---|---|---|
| `CALIBRATION_SUPPORTED` (11) | `train_events/event_001`, `event_002`, `event_005`, `event_006`, `event_007`, `event_009`, `event_011`, `event_012`, `event_013`, `event_014`, `event_017` | Diagnostics meet the candidate calibration rule. Still require researcher acceptance, actual event-specific clock evidence and review. `event_005` has candidate T1 unobservable and T4 right-censored despite the calibration status; its candidate T1/T4 pair is not evaluable. Other candidate values remain unapproved. |
| `AMBIGUOUS` (9) | `no_train_events/event_001`, `no_train_events/event_002`, `train_events/event_004`, `event_008`, `event_010`, `event_015`, `event_020`, `event_022`, `event_023` | No accepted sync from current diagnostic. Need the ambiguity-specific calibration evidence or else retain independent-camera mode/exclude fused claims. Boundary candidates are not labels. |
| `PROVISIONAL` (7) | `engine_events/event_001`, `no_train_events/event_003`, `train_events/event_003`, `event_016`, `event_018`, `event_019`, `event_021` | Calibration does not meet supported criteria; additional independently validated synchronization evidence is needed before any fused scope. |

Across all classes, boundary visibility in a proposal is not an approved label; nor does a label alone establish evaluator metric eligibility. For the 11 supported candidates, event-specific candidate T1/T4 pairs exist for ten; the remaining event 005 has neither a candidate-observable T1 nor T4. **Official evaluable count remains zero**: accepted scope, approved labels, and a replay trace are absent. R04 scope record format is `phase12-r04-scope-decision/1`: the researcher supplies `event_modes` for exactly the split events and `accepted_sync_events`. The gate checks internal consistency and supported-event membership, not the scientific wisdom of the selected scope.

## 6. Premature-opening choice: exact record consequences

The required record is `data/manifests/phase12_protocol_decision.json`, with schema `phase12-protocol-decision/1` and `choices.premature_opening_window` exactly one of:

| Choice | Predicate and event requirements | Missing/censored/unobservable handling and consequences |
|---|---|---|
| `t1_entry_to_t4_clearance` (v9) | Opening flagged by implemented replay predicate during `[T1,T4)`; predicate requires OPEN/OPENING and not physically passage-blocked. Needs approved T1 and T4 on a compatible common timeline (front T1/back T4; R04 must be accepted for fusion). | Any unavailable/ambiguous/unobservable T1 or T4 makes the event not evaluable for this endpoint; retain reason, exclude from denominator. An opening before T1 is outside this metric. T0 is not part of the interval. |
| `first_blocked_to_t4_clearance` (M4) | First blocked tick is `t_blocked`; opening command or blocked→unblocked in strict interval `(t_blocked,T4)` is failure. Implemented `m4_premature_opening` uses a replay trace and back-local T4; T1 and cross-camera fusion are not intrinsically required. | Missing/ambiguous/unobservable/right-censored T4 is not evaluable, never M5. If no blocked tick strictly before T4, record M5 `never_protected`, not an M4 success; exclude from M4 denominator and report M5 separately. T0 and T1 are not inputs. |

Common censoring rules: a train already visible at recording start has physical `T0 ≤ 0`; do not substitute recording-relative zero as true physical onset or include it in physical detection-latency point estimates. `T4` is final-vehicle clearance, not T3. For engine-only events, `T3 ≡ T4` only under the existing engine rule and only when independently adjudicated; never substitute T3 when T4 is censored. No-train events are not applicable to this train-boundary endpoint. A boundary marked uncertain/unobservable is never silently imputed or scored as a favorable zero. No candidate is selected by this package.

## 7. Research protocol and adjudication prerequisites — exact current state

| Item | Authoritative state | Missing action/evidence | Downstream effect |
|---|---|---|---|
| D1 numeric thresholds | D1 option D already selected; pilot-derived hard floor and band upper bound remain unset. Synthetic 600s fixture timing is not human timing. | Authorized genuine timing pilot; capture real session durations; researcher records chosen floor/band threshold and rationale. Until the band can be implemented, current schema still enforces only its existing 30.0s sanity floor. | D1 band routing and any threshold-dependent second-review logic; do not present the floor as sufficiency. |
| D3(a)/(b) | B+C second-review triggers and no numeric tolerance are already selected. | Before coding, reconcile the exact fixed-row IDs. The Phase 11.3 entry points to a fixed subset, while Phase 11.10 says the authoritative subset must be confirmed; the current issue register has 23 open rows across nine events. Record a numbered clarification naming exact CSV row IDs/hash. Then implement B+C; require an allowlisted independent reviewer before assignment. Preserve disagreements as DISPUTED; no automated tie-break. | Records in confirmed fixed rows or with uncertainty cannot be final without required second review/adjudication. |
| D3(c) | Clear-boundary audit requirement is selected; mechanism/frequency not selected. | Researcher specifies what is audited, by whom, and how often/which sample rule. | Before a clear-only boundary can be treated as final or promotion-ready. |
| D2 reviewer identity | Mandatory allowlist is selected/implemented; one identity is currently listed. | If independent review is required, researcher must explicitly authorize/register the actual second reviewer. The agent must not invent an identity. | D3 second review and records authored by that reviewer. |
| ADJ-AUTH | Not recorded. Existing Phase 11.11 protocol says NOT GRANTED. | Researcher separately authorizes formal Stage-2.1 adjudication, exact scope/cohorts/events, authorized reviewers, boundaries, period, write location, independent-review rules, no model exposure, stop conditions, and withdrawal. This differs from LEG-EXEC and EVAL-AUTH. | Formal human records under `data/ground_truth/reviews/`; later promotion/readiness. |
| Workflow capability | Existing `adjudication_session.py` is deliberately synthetic-only; no production-human-media workflow was built in this milestone. | After the narrow pilot authorization, engineering must separately implement and validate a human-controlled real-media pilot. Formal workflow release must follow its own review and ADJ-AUTH. | No genuine review can be claimed before the workflow exists and is actually used. |
| LEG-EXEC, D4, D2, prior choices | Already resolved as documented above. | No researcher action to repeat. | Preserve the original and notice files and live allowlist. |

### Engineering tasks — not researcher decisions

These are implementable only after their stated inputs are available; they must not be disguised as further researcher choices:

1. After the timing-pilot authorization, design and test a human-controlled pilot path separate from the synthetic-only runner. Do not enable real-media opening before the authorization and tests pass.
2. Reconcile the D3(a) fixed-row subset before implementation. The selected B+C rule is established, but the Phase 11.10 package says the exact fixed subset must be confirmed, and the current issue register has 23 open boundary rows (nine events). Record a numbered clarification with exact row IDs and the source CSV hash; do not assume every open row is the selected subset or guess a smaller subset. Then implement the UNCERTAIN + confirmed fixed-row triggers. Preserve no tolerance/no automated tie-break. Test every bound row and nonmembers.
3. After D3(c) audit method/frequency is recorded, implement its audit selection and make promotion/readiness fail closed when required audit evidence is absent.
4. After source-group evidence and a researcher-authored split decision exist, mechanically validate the exact partition, group disjointness for the declared claim, and source-manifest/hash bindings. The current split contract validates nonempty train/val/test and disjoint event IDs only; a green structural check alone does not establish group independence.
5. After approved records/decisions and real payloads exist, run the existing evaluation manifest builder; do not add a placeholder-manifest route.

### Separate external/researcher authorization boundaries

- **Timing-pilot authorization:** the explicit request/template in §3; bounded only to timing observations and the separately authorized, non-approved pilot output.
- **Formal ADJ-AUTH:** a distinct later action for human Stage-2.1 review/adjudication; it must name event scope, reviewers, protocol, outputs and stop conditions. Timing-pilot approval is not ADJ-AUTH.
- **R-SPLIT, protocol choice, and R04 scope:** these are separate researcher-authored scientific decision records, not authorizations implied by this package.
- **EVAL-AUTH:** a later, exact-hash-bound authorization for one named official evaluation; not available until upstream artifacts and Stage-2.1 receipt exist.
- **New data/field activity:** any collection requires separate crossing/site permission, safety and privacy/consent review, and researcher go/no-go. This package authorizes no field or railway operation.

### ADJ-AUTH request (separate from timing-pilot authorization)

After the pilot, D1/D3 process requirements, reviewer allowlist, and production workflow are settled, request a **new, separate** explicit researcher statement that names: the exact Stage-2.1 operation; event/cohort scope; each reviewer identity; boundaries/protocol version; second-review obligations; source-media inventory/hash; allowed output path; minimum/fast-band duration rules; clear-boundary audit rule; model-independence requirement; record state/approval limits; stop/withdrawal rules; and the fact that no evaluation, field work, or physical railway operation is authorized. Record the actual statement in its reviewed authorization record and validate it against live hashes. Do not infer ADJ-AUTH from engineering permission, this package, EVAL-AUTH, or LEG-EXEC.

## 8. Manifest and EVAL-AUTH sequence (not currently eligible)

1. Complete genuine reviews; resolve required second review and D3(c) audit; run the media-hashing Stage-2.1 readiness CLI. Only on READY can its real promotion receipt be issued.
2. Researcher records accepted event split and R04 per-event camera scope, and records v9 or M4 in the protocol decision.
3. Engineering supplies actual approved-scope replay/inference JSON source payloads and invokes the existing `build_evaluation_input_manifest`. It must bind decision hashes and raw source hashes; do not hand-author or pre-create it.
4. Rerun `railway_detection evaluation status`; only when all seven EVAL-AUTH bindings are non-null and upstream artifacts validate may the researcher record EVAL-AUTH. The authorization is for the named official evaluation only and not field/safety work.

## 9. Next readiness milestone

**Next milestone:** researcher explicitly authorizes **engineering preparation only** of the timing pilot for an exact event/reviewer scope. Engineering delivers a focused-tested genuine-media pilot workflow. The researcher then reviews the released version/hash and explicitly activates media use by a separate hash-bound addendum. Only after that activation may the reviewer complete the non-approved pilot. The researcher records D1 numbers from genuine timing observations. In parallel/next, record D3(c) audit policy and implement the already-selected D3(a) trigger. Then issue distinct formal ADJ-AUTH, conduct genuine Stage-2.1 review, decide data/split/R04/protocol, build the derived manifest, and issue EVAL-AUTH last.

Do not run the official gate expecting fewer blockers before the relevant prerequisites change. The artifact is expected to remain `ready: false` until evidence and decisions are genuinely present.