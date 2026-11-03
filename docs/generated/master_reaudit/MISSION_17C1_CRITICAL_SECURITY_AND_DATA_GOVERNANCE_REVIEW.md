# Mission 17C-1 — Critical security and data governance review

Date: 2026-11-03. Baseline: `b51568f763955acf311c932b5d112fd18e2c35c6`. Status: research decision preparation only. No new security mechanism, identity, role, grant or dataset role is adopted.

The three C0 critical groups identify valid prospective blockers. Their severity concerns unauthorized protected operations and invalid research conclusions if the designs are relied on. No attack was executed and no active compromise or observed evaluation-to-training transfer is asserted. F01 and F02 share trust-boundary dependencies; F06 overlaps F05/F08–F10. Their labels are not independent incident counts. See [the complete claim ledger](MISSION_17C1_INDEPENDENT_CHALLENGE_OF_17C0.md) and [all 24 defect dispositions](MISSION_17C1_CORRECTION_COMPLETENESS_AUDIT.md).

## 1. Distinguish the guarantees before choosing architecture

| Property | What must be established | What inspected mechanisms actually establish |
|---|---|---|
| Authentication | Who controls this session/credential and how enrollment is verified | Reviewer-handle membership is a string test, not proof of a human identity. |
| Authorization | This authenticated actor may perform this operation on these resources for this purpose | Current guards check structured recorded scope; the proposed tiers do not exist as an enforced schema. |
| Integrity | Bytes match a trusted expected version | A live digest can detect a mismatch to a trusted external expectation; hashing whatever is present proves no approval. |
| Authenticity | A trusted issuer attested to those exact bytes | An unkeyed record digest or recomputable chain is insufficient; governance explicitly disclaims signature validation. |
| Revocation | A grant/role remains valid when used | Startup-only acceptance is insufficient; protected authority and freshness/availability policy are needed. |
| Replay prevention | A grant cannot create another unauthorized operation/session | Requires authoritative durable reservation state and recovery rules; a copied local ledger can restore apparent availability. |
| Concurrency protection | Two workers cannot reserve/use one grant concurrently | A stable-inode full-transaction lock can coordinate cooperating writers; it cannot stop a process ignoring/replacing the ledger. |
| Point-of-use enforcement | Every protected operation passes a current check | CLI preflight misses alternate paths and later changes. Rechecking mutable disk bytes still does not authenticate loaded code. |
| OS isolation | Direct local-user/process access is prevented by an independent boundary | media_guard explicitly is not an OS sandbox. No host isolation is demonstrated. |
| Administrative approval | The researcher made a particular scope/science/design choice | A draft or technical recommendation is not an applicable canonical execution record. |

Evidence: `src/railway_detection/safety/media_guard.py:48-54`; `src/railway_detection/safety/media_guard.py:389-418`; `src/railway_detection/safety/media_guard.py:439-466`; `src/railway_detection/safety/media_guard.py:530-546`; `src/railway_detection/evaluation/governance.py:487-501`; `src/railway_detection/annotation/promotion_gate.py:66-140`. C0's HEAD/index and runtime-hash criticisms are supported. Its broader implication that locking has no useful atomicity, or that every original lock statement promised malicious-user resistance, needs qualification (C014).

## 2. Critical A: concrete source-derived threat scenarios

These are counterexamples under explicit attacker capabilities, not tested exploits. An ordinary cooperating-process bug and a malicious same-user writer require different controls. If the latter is outside the accepted threat model, state that limitation instead of promising resistance.

| Scenario / attacker capability | Failure trace if the proposed control is used alone | Required decision/control and remaining limit |
|---|---|---|
| Reused token; actor can copy an accepted record | Same token opens a second session before close if consumption is only recorded on close; a constant example nonce cannot identify a unique grant. | Reserve before first protected use, scope to session/actor/resources/bindings, deny new sessions after reservation; define within-session operations separately from one-use grant reservation. |
| Concurrent consumption; two cooperating workers | Both read unused, then each appends consumed, if only append is locked. | Lock check/reserve/flush on the same stable authoritative state; atomic winner and durable commit before access. Specify filesystem semantics. No same-user replacement protection follows. |
| Ledger rollback; actor can restore an earlier local copy | Restore a pre-consumption state, then pass the same check and reserve again. | Independent monotonic authority or protected committed head/length/state and freshness checks. Local chaining plus flock alone does not detect restoration. |
| Ledger tampering; actor can edit local JSONL | Rewrite observation and recompute every later digest, or truncate an acknowledged suffix while retaining a valid chain from trusted genesis. | Canonical bytes, stable record/session IDs, sequence and links, protected committed head **and length**, authenticated actor attestations, authorized corrections and recovery. Trusted genesis alone does not prevent suffix truncation. |
| Source modification after preflight; actor can edit imported code | Hash at start, then replace source/dependency or mutate loaded objects before an operation. A point-of-use disk hash may inspect bytes other than the loaded object. | Approved expected code/config/dependency version, trusted validator, protected immutable execution inputs, relevant operation checks and explicit residual same-user risk. No claim of immediate runtime detection. |
| Working-tree modification after authorization; actor can change tracked/ignored inputs | HEAD stays the same while unstaged code or ignored modules change; an index digest remains unchanged. | Bind the actual permitted execution inputs and provenance, not only HEAD/index; keep them protected through use. Content binding is integrity, not issuer authentication. |
| Alternate code path; actor can invoke a decoder/player directly | Approved CLI refuses but another process opens the resource without calling the Python guard. | Inventory/enforce every cooperating call site; for malicious-local-user resistance choose a separate OS/account/service boundary. Current source alone cannot provide that isolation. |
| Revoked/expired active session; cached preflight result | Session continues after role/grant revocation or expiration. | Fresh checks before protected operations, defined revocation authority, lease/failure policy and auditable stop. Current evaluation records and media leases have different contracts; do not silently promise a unified implemented scheme. |
| Rater onboarding expands issuer trust | Add an appointed rater to the shared reviewer list; media guard also accepts this list for authorized_by. | Separate reviewer/rater role from grant issuer/PI role before onboarding. This is source-observed role coupling, not proof that a new rater has issued a grant. |

Original lock/lifecycle: `docs/generated/master_reaudit/MISSION_17B_HUMAN_REVIEW_CLI_TECHNICAL_SPEC.md:230-241`; `docs/generated/master_reaudit/MISSION_17B_HUMAN_REVIEW_CLI_TECHNICAL_SPEC.md:326-328`. C0 corrected lifecycle: `docs/generated/master_reaudit/MISSION_17B_HUMAN_REVIEW_CLI_TECHNICAL_SPEC.md:394-400`. Its reservation/ACTIVE/COMPLETED concept is useful, but “previously consumed authorizations are denied” and “resume same session” need distinct meanings: reservation denies a **new** session; authenticated recovery may continue the **same** reserved session if still valid. Define RESERVED/ACTIVE/COMPLETED/ABORTED, crash-before/after durable acknowledgement, idempotency, exclusive ownership/fencing, revocation and terminal-state behavior. Whether a protected external operation can be made exactly-once across a crash also needs a stated transaction/idempotency boundary; logging alone cannot guarantee it. Do not approve any token implementation from this sketch.

## 3. Critical B: identity, observation lifecycle and promotion

### Role-specific authority

The active reviewer loader accepts a set of strings; it does not carry role permissions (`src/railway_detection/annotation/promotion_gate.py:66-140`). media_guard loads that same ground-truth reviewer file as the authorization issuer allowlist (`src/railway_detection/safety/media_guard.py:449-456`). Evaluation validation also tests authorized_by against its supplied allowlist (`src/railway_detection/evaluation/governance.py:442-445`). This creates a concrete onboarding dependency omitted from C0's generic role recommendation. Do not change the list during this mission.

| Role | Evidence/control required before appointment/use | Capability that must not be inferred |
|---|---|---|
| First-pass reviewer | Researcher appointment, verified identity/authentication, training/competence evidence, independent session attestation | Issuing grants, changing protocols, adjudicating own disagreements or publishing GT |
| Second reviewer | Same plus independence/conflict declaration and trigger coverage | Universal-review policy adoption or automatic resolution by agreement |
| Adjudicator | Explicit researcher-appointed authority and separate evidence-linked resolution | Overwriting original observations or forcing a definite label |
| Promoter | Scoped batch authority and vetted adapter/write boundary | Media read/hash permission or evaluation execution |
| Grant issuer / PI | Independently established issuer role and trusted attestation mechanism | Every allowlisted rater being an issuer |
| Evaluator | Approved profile/inputs and separate execution record | Training/tuning on the evaluation cases or access to unrelated models/caches |
| Maintainer | Bounded source/design authority | Researcher scientific approval or raw-media execution permission |

Only one string is currently listed (`data/ground_truth/authorized_reviewers.json:1-6`). This supports “no verified appointed second reviewer is established here,” not “the existing person is unqualified” or “RD-042 is contradicted.” RD-042 says external audit reviewer if appointable and keep the list unchanged (`docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:49`). Risk-triggered second review exists (`src/railway_detection/annotation/second_review.py:6-28`; `src/railway_detection/annotation/second_review.py:284-328`); a universal 27-event two-rater rule needs a new researcher choice. If a mandatory trigger is reached without an appointed independent reviewer, that record cannot pass the trigger by naming an invented reviewer.

### Observation-to-promotion contract

1. Preserve camera-local first-pass observations, clock/timebase/frame/PTS and typed observed/censored/uncertain/deferred states. Blinding requires neutral inputs and separate comparison/adjudication phases, with logs and queues included. A shared unrestricted OS account limits enforceability.
2. Store originals append-only by policy, with authenticated source/session evidence and a protected anchor; separate correction entries reference exact original IDs/digests. Hash chains establish relative integrity only against trusted committed state. They do not authenticate observations or make timestamps physically correct.
3. Adjudicate in a new entry referencing both observations and rationale. Preserve unresolved UNCERTAIN. Ban automatic averaging; allow a genuine independently observed frame even if its time coincides with the numerical midpoint. Do not substitute agreement for an adjudication record where the policy requires one.
4. A promotion adapter must bind source observations, corrections, reviewer/adjudicator roles, protocol/schema version and exact protocol digest, qualified physical-event/media identities, applicable risk review and current batch authority. A final record hash cannot substitute for those links.
5. Enforce the policy at the actual publication boundary, including create-only outputs, cohort-qualified keys, atomic batch/partial-failure policy and links to protected source anchors. Current promotion accepts one record plus caller-supplied conditions and writes event_id.json with write_text; it can overwrite and can collide across cohorts in a shared directory. This is an inspected API limitation, not an executed overwrite.

Evidence: `docs/generated/master_reaudit/MISSION_17B_HUMAN_REVIEW_CLI_TECHNICAL_SPEC.md:273-296`; `src/railway_detection/annotation/stage2_1_schema.py:279-350`; `src/railway_detection/annotation/promotion_gate.py:253-310`; `src/railway_detection/annotation/promotion_gate.py:540-567`; `docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:52`. Explicit PI promotion approval is a required future boundary; the current promoter does not cryptographically verify AUTH-PROMOTION or a JSONL chain. No single local ledger, string allowlist or call-site guard supplies the whole trust boundary.

## 4. Critical C: dataset roles and leakage boundaries

Safe inventory metadata contains 23 train-category events,3 no-train-category events and 1 engine-only event. “Train” in train_events describes a railway event category; it does not grant model-training eligibility. Canonical IDs are train_events/event_001…023, no_train_events/event_001…003 and engine_events/event_001. The latter is one physical case even when versions/duplicate artifacts exist. train_events/event_021 is not the engine. Metadata counts are verified; physical content/identity and formal inventory sign-off are not newly certified.

Evidence: `data/manifests/layer_b_v2_annotation_inventory.json:920-928`; `data/manifests/layer_b_v2_annotation_inventory.json:1060-1067`; `data/manifests/layer_b_v2_annotation_inventory.json:1198-1205`; `docs/generated/phase2/EXPERIMENT_DESIGN_CONSOLIDATED.md:24-29`. V1 Roboflow still images and V2 event videos have different provenance (`data/metadata/vision_v1_metadata.json:1-28`). No trustworthy development-image-to-physical-event join was found. Do not infer this join from file numerals or move V2 footage into a training CV design.

| Role | Meaning / allowable dependence in a future approved design | Assignment supported at this baseline |
|---|---|---|
| Training | Fit model parameters; all descendants of one physical event remain one group | V1 is described as development material; a new verified event-grouped training corpus is not established. No V2 event is newly assigned here. |
| Training-fold validation | Select stopping/checkpoints inside the outer training subset | Must be separate from outer evaluation by physical group; not fully specified. |
| Hyperparameter selection | Select architecture, thresholds, preprocessing or model settings | Inner grouped validation or a prospectively frozen rule; outer folds cannot retain independent evaluation status if used for this. |
| Calibration | Fit decision thresholds/score calibration | Prospectively separate or explicitly disclose reuse; the three final no-train controls cannot silently serve both purposes. |
| Development | Explore/debug/design; exposure affects later unseen claims | V1 provenance is distinct from V2. Prior pretrained/checkpoint exposure needs evidence before any held-out claim. |
| Final evaluation | Frozen protocol/model/thresholds applied after decisions | V2 is a full-cohort descriptive evaluation design, subject to human GT and execution approval. It is not evidence of model-unseen evaluation. |
| Held-out evaluation | Cases never used for the relevant development/tuning/training choices | No official V2 split or approved held-out partition exists. Final evaluation is not automatically held-out. |
| Case studies | Descriptive separate reporting, with no pooled or generalization claim | Engine-only case is separate; one physical pass/versions cannot inflate N. |
| No-train controls | Confirmed train-free event-level nuisance/exposure analysis | Three candidate control events; human confirmation pending, no FAR/hour or permanent train-free guarantee. |
| Engine-only cases | Separate railway-event category; T3=T4 when validly observed | One engine case; excluded from pooled M4/M5/occupancy/train-event aggregates. Detector-training eligibility is a separate corpus-specific choice. |

### Required RD reconciliation

| Direction | What is recorded | What C0 gets right / must be qualified |
|---|---|---|
| RD-024 (`docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:31`) | Engine excluded from pooled train-event outcomes | Correctly rejects misidentified engine and new detector-training prohibition. It does not authorize engine training or an unseen zero-shot claim. |
| RD-025 (`docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:32`) | Event-level/exposure controls; no train-free claim yet | Correctly rejects unapproved hourly rate and silently reused calibration. A design ambiguity is not proof contamination has already occurred. |
| RD-035 (`docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:42`) | B0–B2 plus back-stream paper conditions, design only | Correctly preserves independent back option. Names/audio availability/software remain pending; this is no execution authorization. |
| RD-039 (`docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:46`) | Full-cohort descriptive scope; real pathway requires approval | Correctly rejects interpreting full cohort as a training/CV permit. No official V2 split is created. |
| RD-041 (`docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:48`) |27=23+3+1, engine one event with versions | Count is independently supported by metadata. That does not certify physical labels, version identity or final eligibility. |

### CV design limits that remain

The old summary stores1,315 source-name groups/3,157 image IDs with 2218/467/472 partitions and zero same-source-name cross-partition matches. Its leakage_risk flag remains a warning; it does not prove temporal independence, near-duplicate leakage or memorization (`data/splits/705d388743ea/split_summary.json:3179-3190`; `data/splits/705d388743ea/split_summary.json:4496-4503`; `src/railway_detection/data/manifest.py:183-209`; `src/railway_detection/data/split.py:93-119`). No media hashes were computed.

Use pairwise role disjointness, complete lineage joins/derivative grouping and exactly-once outer evaluation coverage. Grouping does not establish cross-site independence. Five-fold joint environmental balance is **not verified**, rather than proven impossible: none of weather/lighting/direction is a top-level field in the 27-entry inventory; V1 summary lacks the required per-event mapping. K distinct groups per stratum is necessary only if that stratum must appear in every fold. Approximate stratification may permit absent rare strata; the scientific coverage claim must then be limited. Feasibility needs reliable labels and an approved objective, not an invented label assignment or ungrouped fallback.

Before implementation acceptance, specify deterministic aligned allocation, tie breaks/weighting, proper JSON Schema and a canonical assignment payload/digest. If timestamps/receipts are excluded from the reproducible payload, retain their independent integrity/provenance binding. Do not silently exclude scientific provenance from all verification. Fresh partitions cannot undo a model's prior exposure to evaluation cases (`docs/generated/master_reaudit/MISSION_17B_GROUPED_CV_SPLIT_DESIGN.md:296-308`).

## 5. Disposition and dependencies

F01: VERIFIED for incompatible current token example, missing HEAD architecture and false OS-boundary description; prospective critical priority. F02: PARTIALLY VERIFIED as a composite because overwrite/identity/rollback gaps hold, while some original locking language promised only cooperative atomicity; prospective critical priority. F06: VERIFIED for V1/V2 conflation and false one-group explanation; prospective critical priority. None is a completed remediation.

Researcher must choose protocol/camera/corpus/reviewer/evaluation scope. Technical owners then need a bounded security/ledger/role and CV acceptance contract. A later separately authorized implementation may use purely synthetic inputs; final protocol promotion and human-data receipts need not block every reversible synthetic engineering task. Protected execution always needs its own applicable approval/operation scope. This mission authorizes none of that work. Exact pending choices and execution records appear in [the final PI decision packet](MISSION_17C1_FINAL_PI_DECISION_PACKET.md).
