# Mission 17C-0 — Independent forensic re-audit of Missions 17A and 17B

Date: 2026-11-03, America/New_York. Auditor: Codex; agent-authored audit, **not researcher approval**.

## 1. Disposition and limits

**PASS WITH CORRECTIONS for the documentation-audit mission. IMPLEMENTATION / REAL-DATA EXECUTION: BLOCKED pending researcher review and applicable approvals.** This disposition does not certify 17A/17B designs, completed human review, approved ground truth or publication readiness. It means the authorized safe audit and documentation corrections were completed with stated limitations.

123 traceability claims checked: VERIFIED 10; PARTIALLY VERIFIED 51; CONTRADICTED 53; UNSUPPORTED 5; NOT VERIFIABLE 4.

24 material defect groups: 3 critical, 17 high, 4 medium. Critical findings are F01 (authorization/integrity guarantees), F02 (identity/ledger/promotion authenticity), and F06 (training/evaluation corpus conflation). High findings include wrong cohort identities/landmarks, missing independent-back alternative, invalid split invariants, unproven stratification, calibration/model-selection leakage risk, incomplete causal/numerical contracts, implied approvals and unsupported manuscript/pilot/empirical claims.

Original 17A dossier/register, Mission 16 reports, protocol files, manuscript, source/tests, data manifests and historical results were preserved. Only the four requested 17C-0 deliverables and four permitted 17B specifications changed. Original 17B bodies remain visible with a same-line status pointer; appended corrections supersede defective requirements. No researcher direction was changed. The missing standalone 17A/17B completion transcripts and unverified real-world facts remain explicit gaps.

## 2. Baseline, Git safety and scope

Repository: `/Users/sayemuddin/Desktop/Train_automation`; branch `main`; initial HEAD `e248bf8c84a781664b93c88e92b07d5256a37971`. Initial `git status --short` was empty (no staged, unstaged or untracked entries). `git rev-parse origin/main` and live `git ls-remote origin refs/heads/main` both returned `e248bf8c84a781664b93c88e92b07d5256a37971`. No baseline divergence or unexpected changes were found. No AGENTS.md was found in the repository or governing ancestor paths inspected.

Baseline command receipt:

```text
git rev-parse --show-toplevel -> /Users/sayemuddin/Desktop/Train_automation
git branch --show-current -> main
git rev-parse HEAD -> e248bf8c84a781664b93c88e92b07d5256a37971
git status --short -> [empty]
git rev-parse origin/main -> e248bf8c84a781664b93c88e92b07d5256a37971
git ls-remote origin refs/heads/main -> e248bf8c84a781664b93c88e92b07d5256a37971 refs/heads/main
```

`git show --stat e248bf8` identifies four documentation specifications added by 17B. The 17A dossier/register were first tracked in the repository-cleanup commit ad9e5c3; neither Git history nor these authored statements alone prove the prior uncommitted workspace, test commands or non-access history. 17A's “25 modified files” is historical narrative, not this baseline's state. No reset/clean/rebase/amend/force push or history rewrite is used.

Authorized scope: read safe source/text/reports/metadata and existing synthetic test definitions; independently derive mathematics; correct documentation. No implementation of 17C or new runtime module/test was performed. The user explicitly authorized exact-path staging, a documentation-only commit and normal push after validation; those Git actions are not research approval.

## 3. Independent method and evidence classification

- Read both complete 17A files and all four complete 17B specifications; inspect their original assertions rather than assuming their concluding assurances are true. Locate Mission 16 findings and compare the relevant claims to source code, config, safe inventory and preserved outputs.
- Diff all bytes between v7.0/v7.1.0 and v7.1.0/v7.1.1; hash only these plain-text protocols. Compare active schema constants/validators against the proposed token and observation formats. Check actual paths and canonical governance record existence; do not invoke token verifiers against real protected resources.
- Trace runner/controller/gate APIs and accumulation indexing statically. Use a standalone Decimal mathematical model with manually supplied command sequences, not real replay. Prove the lag lemma; challenge initial commands, complete/multiple cycles, irregular sampling and partial endpoints. Run 1,000 seeded uniform synthetic comparisons. No model or sensor data enters that model.
- Parse only existing historical B4 timeline timestamp and gate-state fields, matched to all 27 cohort-qualified IDs in B4/single_events.json. Sum existing blocked intervals with Decimal and compare to preserved Table 11/JSON; this is historical arithmetic, not inference/evaluation/replay. Do not use21 extra bare-name CSV aliases as independent events. No feature cache, raw media or checkpoint is read/hashed.
- Inspect V1 split source-name metadata, all 1315 group assignments and 3157 listed image IDs; count source-hint overlap using strings only. Do not open/hash images or assume names prove physical independence. Inspect safe v2 inventory counts and event-level label-key availability; do not generate an actual split.
- Run only the four existing pure synthetic split-unit tests after inspecting their complete definitions and imported package initialization. Bypass unrelated root conftest/CLI imports with pytest confcutdir; disable plugin autoload, pytest cache and bytecode writes. No production tests were changed. Other synthetic test plans were reviewed as design requirements, not executed suites.
- Consult primary COPE authorship policy and scikit-learn grouped-stratification documentation for narrow external checks. [COPE policy](https://doi.org/10.24318/cCVRZBms) supports no AI authorship and human responsibility; its publisher page was 403 when directly fetched, so only the primary indexed policy text was available. [scikit-learn StratifiedGroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html) describes approximate stratification subject to grouping constraints. Neither external source validates this dataset, the target venue or actual performance. No library installation/change occurred.

The verification matrix gives claim, exact path/line evidence, independent method, status, impact, required correction and PI need for all 68 technical rows and all 55 RD trace rows. NOT VERIFIABLE is not assumed false; UNSUPPORTED means evidence is inadequate. RD comparisons verify the available recorded direction, not private conversational provenance or human signatures. Static security inspection does not establish adversarial runtime enforcement.

## 4. Mission 17A: findings and corrections

### Protocol authority and residual contradictions

| Text file | Lines | Independently computed SHA-256 | Authority finding |
|---|---|---|---|
| docs/FINAL_GROUND_TRUTH_PROTOCOL.md | 847 | d100c1e6a63280c375f94e297416efb0cf7dd3c15c9aa8df076ede052d49ecf4 | In-place v7.0 text; formal authority approval not established |
| docs/generated/mission_5a/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md | 867 | d21a84fa5129c82d6d4202f34d539a4f3f24da4151df09912d53f0996e5cde22 | PROPOSED; not adopted or hash-bound |
| docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md | 877 | 23b383b89c57e97852f60e320c8e4feb25d99ac6492e399db281abb126b92a6d | PROPOSED; not adopted or hash-bound |

The v7.1.0 proposal corrects T1 to the approach frog/pedestrian line, T2 to physical leading-end roadway entry with deferred landmark, and premature-opening wording to M4/M5; it adds direction/blind-review/adjudication conventions and explicit CCA deferral. Historical obsolete wording stays marked non-normative. These are verified text differences, not adoption.

The complete v7.1.0→v7.1.1 diff adds a stronger no-approval/no-record banner and v9.1.1 companion reference, replaces one “EMA states” firewall phrase with “internal evidence states,” changes T4's role label to M4/M5, adds replay-evidence/comparison-grid references, T0 censor-direction treatment, further mock disclaimers and historical change-log delimiters. 17A's broad “eliminates obsolete EMA controller references” is limited to that one text-list replacement; it is not a controller-code change. Microsecond normalization is representation handling, not a calibrated review tolerance.

v7.1.1 still contains the offline AI-proposal lifecycle, legacy illustrative records using approval_status/adjudication_status and example timestamp semantics rather than a complete compatible human-ledger schema. Its banner correctly says mocks are not records; these examples must not be used as a production adapter. The active Stage21 schema is 8.1.0, while the inactive schema proposal is 8.2.0-stage2.1-proposed. T2, scientific tolerances and per-event human directions remain deferred. Thus “all conflicts resolved / technically ready” is too strong. 17B's blanket AI-proposal ban is also not an accurate description of the existing protocol's permitted offline candidate lifecycle; this audit's media/AI-annotation prohibition remains fully in force.

Canonical protocol/eval/promotion approval paths are defined at `src/railway_detection/evaluation/governance.py:52-76`. No applicable protocol adoption/binding, media authorization, promotion receipt or EVAL-AUTH file was found at these canonical paths. No authority was inferred from prose labels, a hash, a checkbox or the existing narrow legacy authorization. D-01 remains pending. 17A's v7.1.1 digest actually names v7.1.0; full correct digests above are informational only.

### Review architecture, security and calibration

Synthetic ID/temp-path safeguards are present at `src/railway_detection/annotation/adjudication_session.py:126-150` and used in construction and hashing paths. A separate human module is technically justified to keep these regression guards intact; it does not make the proposed interfaces correct by itself. 17A's review/ namespace, governance allowlist, fictitious manifest paths and REVIEW_RAW_MEDIA operation are not actual repository interfaces. The existing session is an API, not the claimed console runner.

HEAD only names committed content; write-tree names the staged index; clean status is useful evidence at one instant. None authenticates running code or prevents mutation after authorization. Existing media_guard binds protocol bytes, not HEAD; EVAL-AUTH uses seven artifact digests. New nonce/tier/checkpoint mechanisms are proposed, not implemented. Current unsigned recorded statements explicitly refuse signature claims. Runtime disk hashing cannot attest loaded bytecode or defeat a same-user attacker. A signed/anchored design or explicitly bounded trust model remains a researcher decision.

No appointed second rater, verified credentials, empirical tolerance or pilot execution was established. 17A expected spread ranges have no measurements behind them. Five cases can expose usability/operational issues but do not validate general scientific tolerances. Seconds are a valid comparison unit across frame rates; equating0.1 s with three frames everywhere is wrong, while varying fps alone does not prove that a tolerance in seconds is scientifically invalid. Use presentation timestamps/timebase where frame_idx/fps assumptions fail. The30 s schema floor remains a software plausibility check; RD046 defers scientific review-duration calibration. No new session cap is adopted.

RD043 is risk-based mandatory second review, not universal dual-review approval; the current single-record promoter cannot enforce a corpus-wide two-rater architecture by itself. RD045 is preserved: independent original observations, separate linked adjudication, unresolved UNCERTAIN, no automatic averaging. The invalid numerical ban on ever equaling a midpoint is corrected; independently observed evidence may coincide with it.

### Camera scope and research framing

The key omitted alternative is independent back-stream replay plus approved observable back-clock T4. It can support M4/M5 without cross-camera synchronization (`docs/generated/phase2/EXPERIMENT_DESIGN_CONSOLIDATED.md:31-47`; `src/railway_detection/evaluation/metrics.py:235-258`). The current front-only cache engine is an implementation limitation, not a proof that M4/M5 require fused R04 or must be dropped from V1. Approved T4/coverage and back-route engineering/authorization are still missing. Actual camera visibility was not visually rechecked; documented front scope cannot establish tail clearance from disappearance.

Option C remains pending and would amend affected directions; no amendment exists in this audit. RD015 back-primary, RD028 independent-primary/fused-secondary, RD035 back conditions and RD039 descriptive-full-cohort remain the recorded basis. 11-event R04 is an exploratory scope, not a newly certified official dual-camera set; event_010 cannot be silently added but is not barred from every future researcher-authorized amendment. RD027 prohibits shifting human camera-local GT by acoustic offsets. T2/full occupancy remain deferred; nominal metric names must not be changed to closed duration/safety buffer or expanded to M1–M3 by assumption.

The actual manuscript still lists an agent, while human-only authorship/disclosure is a pending correction, not completed work. Venue remains undecided; Q1/Q3 publication dates and definitive drift/100%-reproducibility claims lack evidence. Release direction allows future code/approved annotations after privacy review and excludes raw media.20/23 left censoring is candidate/report-derived and cannot be promoted to approved GT; existing proposals themselves have known reliability problems. MTR outcome is not its eligibility screen. Two-tick confirmation is not2 seconds;2s is the warning dwell; a0.1 s arithmetic subtraction is not a scientifically approved tolerance. The numerical3.6s latency is implementation/cadence/float dependent and must be re-derived for any new convention, not advertised as a safety standard.

## 5. Mission 17B: independent findings

### Human-review CLI

The token example cannot pass the active media /2 exact-key/nested contract. The observation dataclass omits cohort, per-boundary camera/clock, required states, media/protocol/schema bindings, reviewed duration and fields requested by its own gate-operation form. T3 is wrongly changed to locomotive-nose/island passage. Cross-camera numeric monotonicity can reject correct observations on unsynchronized local clocks. The five-event pilot and full 27 dual review are proposals.

First-pass blinding is only a UI rule unless proposal/prediction/prior-review data are excluded from process state, neutral queue metadata, logs and external tooling. Local file access outside a wrapped interface remains a disclosed boundary. Handle lookup cannot authenticate a reviewer or establish qualification. Existing promoter verifies Stage21 records/live media identity, not the new JSONL chain or PI cryptographic token, and its current write can overwrite an event JSON. No production fix was made.

Hash chaining alone permits entire-chain rewrite and tail truncation. Define canonical bytes, record IDs/sequences, trusted genesis/tail anchors, one serialized writer, lock scope, durable fsync acknowledgement, idempotence, torn-write quarantine and rollback detection. A local consumed-nonce file needs an atomic durable reservation before the first protected operation and clear ACTIVE/completed/aborted/resume semantics; consume-on-open and retirement-on-close must not disagree. Resume must recheck identity/bindings/expiry/revocation and cannot allow a second session. Same-user rollback/inode replacement and monkeypatches are outside the guarantee of flock/disk hashing. Corrected requirements are in the appended CLI history; security approval remains pending.

### Convention B and mathematical verification

Current runner computes u_k before advancing the preceding interval (`src/railway_detection/simulation/runner.py:185-233`). Gate commands CLOSED/CLOSING lower and OPEN/OPENING raise (`src/railway_detection/simulation/gate_model.py:47-71`). Convention B's core propagation with u_(k-1), then endpoint observation/decision, is forward causal. The pseudocode's6s actuator differs from frozen 3s, sorting hides arrival disorder, clamping prevents its negative-dt branch, watchdog behavior is absent, missing/nonfinite timestamps and explicit final horizon are not defined, and three angle predicates disagree. The active/issued command fields help but are not complete interval provenance.

For a uniform grid h, common initial state, identical fixed command sequence/dynamics F/classifier, and initial fixed-point condition F(theta0,u0,h)=theta0:

`theta_B[k] = theta_A[k-1]` by induction, hence `b_B[k] = b_A[k-1]`.

`T_B - T_A = h * sum(k=1..N, b_A[k-1]-b_A[k]) = h*(b_A[0]-b_A[N])`.

With initially open b_A[0]=0, this is `-h*b_A[N]`. The terminal indicator is explicitly Convention A's; the two terminal states can differ. Multiple blocked episodes telescope too; exactly one episode and symmetric actuator speeds are not necessary. u0=LOWER need not satisfy the initial condition; feedback changes can invalidate common-command equality. For irregular/partial grids use `sum(dt[k]*(b_B[k]-b_A[k]))`, with no terminal-only shortcut. An endpoint-weighted sum is not continuous threshold-crossing integration.

Independent Decimal counterexamples and corroborations (rate30°/s, initial 90°; commands0=hold/open-at-limit, -1=lower, +1=raise):

| Synthetic case | A sampled seconds | B sampled seconds | Delta | Finding |
|---|---|---|---|---|
| uniform_terminal | 4.6 | 4.4 | -0.2 | h=.2; u0 fixed; terminal blocked |
| uniform_complete | 8.0 | 8.0 | 0.0 | Full cycle ends open; boundary term0 |
| multiple_episodes | 10.6 | 10.4 | -0.2 | Multiple episodes; terminal term only |
| terminal_unblocked | 0.0 | 0.0 | 0.0 | No blockage; difference0 |
| partial_final | 0.7 | 0.5 | -0.2 | Lastdt=.1 but difference-.2, not-.1 |
| initial_lower | 4.6 | 4.6 | 0.0 | u0=LOWER; lag assumption fails |
| irregular_positive | 0 | 2 | 2 | dt=[1,2],u=[0,-1,+1]; one-sided bound fails |

1,000 additional seeded100-interval uniform mathematical cases passed the conditional telescoping identity exactly in Decimal. This validates the algebraic model, not a future implementation or physical gate. Explicit sequences and code are in §10. Rounding timestamps to microseconds does not imply microsecond physical blockage accuracy; right-endpoint credit can differ by interval-scale boundary error. A future watchdog must activate at an explicit timer event or at detection time, never retroactively over the missing interval. A media cutoff after the last observation needs an explicit no-new-observation propagation segment, not an invented frame or default dt.

### Event-grouped CV

The actual split has1315 source-image hint groups, not one crossing_id=1 group. Its flags disclose risk; they do not prove temporal duplicate leakage or memorization. Metadata-only source-hint comparison found0 cross-partition identical hints, which also does not prove no near-duplicates or same-event leakage. Historical evaluation artifact mAP50=.9946, not the specification's unreferenced.98; no re-evaluation was run.

The27-event v2 evaluation cohort is not the 3157-image V1 development corpus. Bare IDs collide; train021 is not the engine and train003/009/016 are not controls. Canonical engine/control identities and version/derivative grouping must be used. RD024 pooled-metric exclusion is not a detector-training prohibition. Splitting v2 videos into model training would require a new corpus/evaluation decision; it is not a factual “repair” to RD039.

Empty three-way intersection permits train/val leakage. Require pairwise role disjointness within an iteration, validation-fold group disjointness/coverage across iterations and complete image/annotation/derivative lineage checks. Training sets across CV iterations intentionally overlap. A fallback=True constructor must be rejected; the original merely skips the missing-ID error. Ambiguous or unavailable physical grouping must stop the splitter with no ungrouped random alternative.

No weather/lighting/direction event-top-level keys were found in the 27-entry safe inventory; V1 metadata is dataset-level, not a trustworthy per-image event/stratum join. This is a specific inspected-schema absence, not a claim that nobody has ever described weather in any document. If a required joint stratum must appear in all K folds, it needs at least K distinct groups; even that does not guarantee feasible balancing under other constraints.23/5 can yield5,5,5,4,4, but23 eligible development groups are not established. Allocation is an ellipsis, labels precede sorting, and the purported schema is only an instance with undefined self-hash.

Calibrating on controls and later claiming them unseen contaminates evaluation; the design does not specify separation. Keep calibration and outer evaluation disjoint or label reuse exploratory. Outer held-out folds must not select checkpoints/hyperparameters/thresholds; use inner grouped validation or prospectively fixed tuning, training-only preprocessing and recorded initialization/exposure provenance. Event grouping alone cannot undo prior model exposure or same-session/site dependence. No-train reporting remains event counts/blocked seconds/episodes/exposure, with no hourly-rate inference. Future manifest requirements and infeasibility/failure oracles are corrected in the CV appendix; no actual split was generated.

### Integrated dependencies

There are five conceptual tracks A–E, not four. Technical separability does not grant implementation permission. Existing “pre-approved/preserved-active/proven-ready” labels do not create formal governance artifacts. D-01..D-10 are pending. The integrated register misnames M4/M5, implies physical11-event R04 certification, misidentifies special cohorts and treats future security controls as current. Its gates omit schema/ledger adaptation and capability-specific read/hash/cache/promotion/eval requirements. Zero disagreements cannot force false consensus: unresolved values stay UNCERTAIN with metric-specific reasons. Gate labels do not prove scientific approval, human completion or publication readiness.

## 6. Historical Table 11 recheck and bounded derived values

Canonical selection: read the 27 event IDs in `results/experiments/B4/single_events.json`; for each read exactly `<event_id>_timeline.csv`. Parse timestamp_s with Decimal and gate_state as JSON; count rows, intervals, episodes and endpoint-weighted blocked duration. Match table rows by exact cohort-qualified underscore identifier. Gate-state data are historical outputs, not human GT.

All27 initial angles90°, final angles0°, blocked episode counts1, terminal intervals0.2. All6,710 intervals equal Decimal('0.2'); no duplicate/nonmonotonic interval; every sum equals Table 11 and matches its floating JSON within 1e-9. Totals6,737/6,710 contradict16H aggregate arithmetic, while corroborating its per-file ledger and grid/terminal findings.

The following final column is **an analytical fixed-command lag-model value, not a newly executed Convention B result or approved benchmark**. It assumes the common command/dynamics/initial-condition/classifier proof above; historical SimulationStep does not explicitly log issued/applied actuator commands. No claim is made that all future feedback-aware implementations or full media horizons have the same correction. 27 source CSV citations include complete line ranges to make origin/cutoff auditable.

| Event | Rows / intervals | Historical Table 11 seconds | Derived fixed-command seconds | Exact CSV path and line range |
|---|---|---|---|---|
| train_events_event_001 | 249 / 248 | 46.0 | 45.8 | `results/experiments/B4/timelines/train_events_event_001_timeline.csv:1-250` |
| train_events_event_002 | 163 / 162 | 28.8 | 28.6 | `results/experiments/B4/timelines/train_events_event_002_timeline.csv:1-164` |
| train_events_event_003 | 167 / 166 | 29.6 | 29.4 | `results/experiments/B4/timelines/train_events_event_003_timeline.csv:1-168` |
| train_events_event_004 | 391 / 390 | 74.4 | 74.2 | `results/experiments/B4/timelines/train_events_event_004_timeline.csv:1-392` |
| train_events_event_005 | 398 / 397 | 75.8 | 75.6 | `results/experiments/B4/timelines/train_events_event_005_timeline.csv:1-399` |
| train_events_event_006 | 635 / 634 | 122.4 | 122.2 | `results/experiments/B4/timelines/train_events_event_006_timeline.csv:1-636` |
| train_events_event_007 | 192 / 191 | 34.6 | 34.4 | `results/experiments/B4/timelines/train_events_event_007_timeline.csv:1-193` |
| train_events_event_008 | 314 / 313 | 59.0 | 58.8 | `results/experiments/B4/timelines/train_events_event_008_timeline.csv:1-315` |
| train_events_event_009 | 215 / 214 | 39.2 | 39.0 | `results/experiments/B4/timelines/train_events_event_009_timeline.csv:1-216` |
| train_events_event_010 | 120 / 119 | 20.2 | 20.0 | `results/experiments/B4/timelines/train_events_event_010_timeline.csv:1-121` |
| train_events_event_011 | 189 / 188 | 34.0 | 33.8 | `results/experiments/B4/timelines/train_events_event_011_timeline.csv:1-190` |
| train_events_event_012 | 376 / 375 | 71.4 | 71.2 | `results/experiments/B4/timelines/train_events_event_012_timeline.csv:1-377` |
| train_events_event_013 | 369 / 368 | 70.0 | 69.8 | `results/experiments/B4/timelines/train_events_event_013_timeline.csv:1-370` |
| train_events_event_014 | 275 / 274 | 51.2 | 51.0 | `results/experiments/B4/timelines/train_events_event_014_timeline.csv:1-276` |
| train_events_event_015 | 156 / 155 | 27.4 | 27.2 | `results/experiments/B4/timelines/train_events_event_015_timeline.csv:1-157` |
| train_events_event_016 | 235 / 234 | 43.2 | 43.0 | `results/experiments/B4/timelines/train_events_event_016_timeline.csv:1-236` |
| train_events_event_017 | 419 / 418 | 80.0 | 79.8 | `results/experiments/B4/timelines/train_events_event_017_timeline.csv:1-420` |
| train_events_event_018 | 295 / 294 | 55.2 | 55.0 | `results/experiments/B4/timelines/train_events_event_018_timeline.csv:1-296` |
| train_events_event_019 | 302 / 301 | 56.6 | 56.4 | `results/experiments/B4/timelines/train_events_event_019_timeline.csv:1-303` |
| train_events_event_020 | 150 / 149 | 26.2 | 26.0 | `results/experiments/B4/timelines/train_events_event_020_timeline.csv:1-151` |
| train_events_event_021 | 307 / 306 | 57.6 | 57.4 | `results/experiments/B4/timelines/train_events_event_021_timeline.csv:1-308` |
| train_events_event_022 | 232 / 231 | 42.6 | 42.4 | `results/experiments/B4/timelines/train_events_event_022_timeline.csv:1-233` |
| train_events_event_023 | 229 / 228 | 42.0 | 41.8 | `results/experiments/B4/timelines/train_events_event_023_timeline.csv:1-230` |
| no_train_events_event_001 | 124 / 123 | 18.8 | 18.6 | `results/experiments/B4/timelines/no_train_events_event_001_timeline.csv:1-125` |
| no_train_events_event_002 | 67 / 66 | 9.6 | 9.4 | `results/experiments/B4/timelines/no_train_events_event_002_timeline.csv:1-68` |
| no_train_events_event_003 | 119 / 118 | 10.6 | 10.4 | `results/experiments/B4/timelines/no_train_events_event_003_timeline.csv:1-120` |
| engine_events_event_001 | 49 / 48 | 5.0 | 4.8 | `results/experiments/B4/timelines/engine_events_event_001_timeline.csv:1-50` |

Historical tables, JSON summaries and timelines were not modified. The source commit of the original execution is not established by a later documentation baseline; frozen run metadata records cadence/hashes but does not bind the whole historical execution code. No missing command field or source commit is invented.

## 7. Severity-ranked defect register and verified corrections

| Defect | Severity | Finding | Verification rows | Applied documentation correction | Pending PI dependency |
|---|---|---|---|---|---|
| F01 | CRITICAL | Authorization and integrity guarantees exceed implementation | C010–C013, C025–C026 | Correct H/I descriptions and token/example status; require approved threat model, operation/resource separation and protected execution. | D-03 |
| F02 | CRITICAL | Authenticity, concurrency and immutable-storage gaps | C014–C016, C024 | Withdraw guarantees; specify durable transactional nonce/session lifecycle, authenticated actors, anchored logs, safe promotion adapter. | D-02/D-03 |
| F06 | CRITICAL | Development/evaluation dataset conflation | C034, C036 | Identify actual 1315 source hints; do not move evaluation footage into training; require reliable development lineage. | D-07 |
| F03 | HIGH | Review semantics and governance are incompatible | C017–C023 | Restore semantic/clock constraints; isolate blind pass; keep RD-045; require PI review-policy/schema adoption. | D-01/D-02/D-05 |
| F04 | HIGH | Camera/metric reconciliation creates a false dependency | C029–C032 | Restore independent back-clock alternative; retain T2 deferral and correct M4/M5; Option C remains pending. | D-06 |
| F05 | HIGH | Engine/control IDs and training direction invented | C037–C038 | Use cohort-qualified inventory identities and one physical group for all engine versions; separate training decision. | D-07 |
| F07 | HIGH | Leakage mechanism and metric cause overclaimed | C035 | Preserve diagnostic qualification; remove causal assertion; record actual artifact value as historical only. | D-07/D-08 |
| F08 | HIGH | Split-disjointness and fail-closed checks insufficient | C039–C040 | Pairwise within-fold disjointness, complete eligible validation coverage and strict lineage checks; reject any ungrouped fallback. | D-07 |
| F09 | HIGH | Five-fold stratification and manifest not established | C041–C042, C044 | Feasibility report before K choice; deterministic aligned records and auditable canonical manifest/schema. | D-07 |
| F10 | HIGH | Calibration/model-selection leakage unaddressed | C043, C045 | Separate/freeze calibration, inner validation and outer evaluation; reused controls become exploratory, no unseen claim. | D-07/D-08 |
| F11 | HIGH | Causal duration theorem and estimator overgeneralized | C047–C049, C058 | State fixed-command lag assumptions and general sum; distinguish analytical derived values from causal implementation results. | D-09 |
| F12 | HIGH | Timestamp error branches cannot work as written | C051 | Separate sorted offline/arrival modes; validate finite timestamps and normalized ordering before propagation. | D-09 |
| F13 | HIGH | Threshold/rounding rules contradict each other | C053 | Single approved numerical rule; unrounded internal state; display rounding only; quantify interval-estimator uncertainty. | D-09 |
| F14 | HIGH | Gate timing silently changes from 3s to6s | C054 | Restore3s comparison baseline and label6s cases explicitly synthetic alternatives. | D-09 |
| F16 | HIGH | Dropout/watchdog and final horizon missing | C052 | Choose independent watchdog timer events or detect-now policy; validate explicit cutoff; no fabricated observations/unknown dt. | D-09/controller policy |
| F17 | HIGH | Technical independence mistaken for authorization | C060–C061 | Five tracks; technical separability only; D-01..D-10 pending; synthetic implementation and real execution need separate approval. | D-04 and applicable decisions |
| F18 | HIGH | Manuscript/publication/release status overclaimed | C064–C066 | Record pending researcher-owned manuscript correction and privacy/release approval; no invented timetable or author roster. | D-08 |
| F19 | HIGH | Censoring/MTR and latency explanation unreliable | C062–C063 | Counts await GT; distinguish recorded lead-in from physical onset and MTR outcome; derive timing under approved convention. | D-10 |
| F20 | HIGH | Protocol readiness/authority claimed beyond evidence | C004, C006 | Protocol/schema/companion reconciliation before adoption and final-byte hash binding; no change to authority here. | D-01 |
| F22 | HIGH | Uncalibrated pilot tolerances and reviewer floor | C027–C028 | Keep all scientific tolerances/session caps pending; pilot purpose/usability and timing evidence specified before execution. | D-05 |
| F15 | MEDIUM | Interval command logging and mapping incomplete | C055 | Require interval start/end, pre/post state, applied/issued effective time, duration semantics, rejection/fault logs and target-state mapping. | D-09 |
| F21 | MEDIUM | Path, interface, line-range and digest errors | C005, C008–C009 | Document actual paths/contracts; historical lines remain preserved; target human CLI remains proposed only. | D-02/D-03 where design choice needed |
| F23 | MEDIUM | Historical arithmetic/examples/provenance erroneous | C057, C059 | Record6737/6710 and 46.0/28.8; preserve historical reports/results; conditional derived column only. | D-09 for publication format |
| F24 | MEDIUM | Prior completion/test claims cannot be reconstructed | C067–C068 | Record explicit evidence limitation; retain all available historical records and do not certify prior behavior. | Researcher evidence supply if available |

Applied correction means factual erratum/corrected prospective requirement, not a runtime fix. Factual choices preserve recorded RD directions; proposed changes to directions remain questions. The companion errata register preserves the original claim and evidence for each group. Source security/promotion defects remain unresolved in production because source/test modification is outside authority.

## 8. Unresolved evidence and researcher decisions

- No separately named 17A/17B completion report/transcript was located in tracked files or all-history completion-name search. 17A's569-line dossier and 162-line register plus 17B's four complete specifications were inspected; those authored conclusions are not receipts of prior execution. Off-repository conversations/logs may exist and were not represented as retrieved. No prior test/safety execution claim is certified from prose alone.
- No approved human GT establishes per-event landmarks, direction,20/23 censor count, environmental labels or train-free controls. Actual raw visibility, temporal offsets, nonlinear clock drift, camera calibration and scientific tolerances were not independently measured. No claim of “physically verified” synchronization, device certification or publication date is made.
- Development-image physical-event lineage, environmental strata, larger-session dependence and train/eval join are not established. Missing data block a certified grouped splitter; algorithm feasibility cannot be assumed from a generic23-event count.
- No malicious-user-resistant identity/signature/nonce/ledger anchoring or OS isolation is implemented/verified. Proposed controls and illustrative token fields cannot substitute for actual approved versions and trusted enforcement.
- No real-data causal run, protected cache/checkpoint integrity check, original-run full-code provenance, new split, trained model or evaluation result was produced. Conditional analytical values are not an empirical implementation validation.
- Manuscript author roster/AI disclosure/venue/release license and privacy sign-off remain researcher-owned. No venue-specific publication readiness or raw-media release approval is inferred.

The PI register contains exact questions/consequences for D-01–D-10 plus reviewer, trusted authority, development lineage, calibration, execution permits and missing transcript blockers. No entry is APPROVED WITH EVIDENCE. Researchers may request the missing historical transcripts for a supplemental audit without invalidating the safe documentation findings already established.

## 9. Validation, Git completion and safety declarations

Executed existing tests:

```text
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest --confcutdir=tests/unit -p no:cacheprovider tests/unit/test_split.py -q
.... [100%]
4 passed in 0.02s
```

Those four tests use invented Sample records, import the pure splitter, access no dataset/media/cache/checkpoint, and write no production artifacts. Their pass verifies existing synthetic split behavior only, not event lineage or the unimplemented proposed design. The proposed10 CLI/14 simulation/8 CV cases were not claimed executed. No broad test suite was run because isolation was not demonstrated for it. `python` was unavailable; the initial command failed before execution and subsequent audit scripts used python3. Exploratory reads of nonexistent historical paths were recorded as path defects, not repaired in production.

Additional checks: full protocol diffs; protocol text digests; canonical record-path absence; Decimal historical arithmetic; seven synthetic mathematical scenarios and 1,000 seeded identity comparisons;123 traceability rows; all cited local paths and line ranges; internal claim/defect/decision references; historical preservation; exact eight-file documentation scope; complete working/staged diff and whitespace/secret/resource checks. The code in §10 reproduces the mathematical scenarios and historical parsing without source imports or protected resources.

Git workflow: only the four 17C-0 files and four 17B specs may be staged, using their exact paths. Complete diff is reviewed before stage and complete staged diff before commit. Required commit message: `docs: independently reaudit missions 17A and 17B`. Push normally to origin/main only after validating live remote still equals baseline; verify resulting remote hash equals local HEAD, commit contains only these eight docs and working tree is clean. Final commit/hash/remote receipts are reported in the chat completion because embedding a commit's own hash would require a subsequent edit/commit. This report does not fabricate a pre-commit “pushed” receipt.

Safety declarations for this mission: no raw video/audio/image was opened, previewed, played, decoded or hashed; no production checkpoint/protected feature cache was accessed; no real inference/replay/timing pilot/training/evaluation; no human annotation/adjudication/promotion; no actual split generation; no authorization token issued/consumed; no reviewer/credential/signature/approval created; no protocol authority/governance/source/tests/data manifests/weights/results changed; no OS/privacy bypass. Only existing safe historical text/output fields and synthetic mathematical values were used. Python-level guards are not proof of OS isolation.

## 10. Reproducible audit calculations (safe, no production implementation)

The standalone verification script ran from /tmp; it writes only a temporary JSON receipt and does not import the production runner. The following is its complete mathematical/historical arithmetic core. It reads existing report CSV/JSON metadata; it never reads media/model/feature-cache paths or computes new empirical predictions.

```python
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
import csv, json, hashlib, random, re
ROOT = Path('/Users/sayemuddin/Desktop/Train_automation')
out = {}
def load(name):
    return json.loads((ROOT/name).read_text())
def sim(dts, commands, causal, initial=D(90)):
    angle=initial; total=D(0); states=[]
    for k,dt in enumerate(dts,1):
        command=commands[k-1 if causal else k]
        angle=min(D(90),max(D(0),angle+D(command)*D(30)*dt))
        blocked=angle<=45
        total += dt*blocked
        states.append((angle,blocked))
    return total,states
cases={
 'uniform_terminal':([D('.2')]*30,[0]+[-1]*30),
 'uniform_complete':([D('.2')]*70,[0]+[-1]*20+[0]*20+[1]*30),
 'multiple_episodes':([D('.2')]*100,[0]+[-1]*20+[1]*20+[0]*20+[-1]*40),
 'terminal_unblocked':([D('.2')]*4,[0]+[-1]*4),
 'partial_final':([D('.2')]*10+[D('.1')],[0]+[-1]*11),
 'initial_lower':([D('.2')]*30,[-1]*31),
}
rng=random.Random(1700)
cases['irregular_positive']=([D('1'),D('2')],[0,-1,1])
out['algebra_cases']={}
for name,(dts,cmds) in cases.items():
    a,sa=sim(dts,cmds,False);b,sb=sim(dts,cmds,True)
    out['algebra_cases'][name]={'A':str(a),'B':str(b),'delta':str(b-a),'terminal_A':str(sa[-1][0]),'terminal_B':str(sb[-1][0]),'last_dt':str(dts[-1]),'dts':list(map(str,dts)),'commands':cmds}
for _ in range(1000):
    dts=[D('.2')]*100;cmds=[0]+[rng.choice([-1,0,1]) for _ in dts]
    a,sa=sim(dts,cmds,False);b,sb=sim(dts,cmds,True)
    assert b-a == -D('.2')*sa[-1][1]
out['uniform_identity_checks']=1000
historical=load('results/experiments/B4/single_events.json')
table={r['Event ID']:D(r['Closed Duration'].removesuffix('s')) for r in csv.DictReader((ROOT/'results/experiments/tables/table11_per_event_summary.csv').open())}
ledger=[]
for rec in historical:
    eid=rec['event_id'];rel=f'results/experiments/B4/timelines/{eid}_timeline.csv'
    rows=list(csv.DictReader((ROOT/rel).open()));ts=[D(r['timestamp_s']) for r in rows]
    gates=[json.loads(r['gate_state']) for r in rows]
    dts=[b-a for a,b in zip(ts,ts[1:])]
    blocked=[g['is_passage_blocked'] for g in gates]
    total=sum((dt*bl for dt,bl in zip(dts,blocked[1:])),D(0))
    episodes=sum(bl and (i==0 or not blocked[i-1]) for i,bl in enumerate(blocked))
    # Historical schema contains no actuator command field: do not invent one.
    ledger.append(dict(event=eid,rows=len(rows),intervals=len(dts),uniform=all(dt==D('.2') for dt in dts),terminal_angle=gates[-1]['angle_deg'],terminal_blocked=blocked[-1],initial_angle=gates[0]['angle_deg'],episodes=episodes,closed=str(total),table=str(table[eid]),json_matches=abs(D(str(rec['total_closed_s']))-total)<D('.000000001'),path=rel,first_gate=gates[0],final_interval=str(dts[-1])))
out['timelines']=ledger
out['timeline_totals']={'rows':sum(r['rows'] for r in ledger),'intervals':sum(r['intervals'] for r in ledger),'all_uniform':all(r['uniform'] for r in ledger),'all_terminal_blocked':all(r['terminal_blocked'] for r in ledger),'all_match':all(r['json_matches'] and r['closed']==r['table'] for r in ledger)}
split=load('data/splits/705d388743ea/split_summary.json')
out['split']={'groups':len(split['group_assignments']),'partitions':{k:len(v) for k,v in split['partitions'].items()},'warnings':split['warnings'],'all_source_hints':all(k.startswith('source:') for k in split['group_assignments'])}
# Verify only the existing source-name hint; no raw image is opened or hashed.
seen={};overlap=[]
for part,ids in split['partitions'].items():
    for sid in ids:
        source=re.sub(r'\.rf\.[0-9a-fA-F]{32}$','',Path(sid).name)
        if source in seen and seen[source]!=part: overlap.append(source)
        seen[source]=part
out['split']['cross_partition_same_source_hints']=len(overlap)
inv=load('data/manifests/layer_b_v2_annotation_inventory.json')
out['inventory_counts']=dict(Counter(v['category'] for v in inv.values()))
out['inventory_has_strata']={k:sum(k in v for v in inv.values()) for k in ['weather','lighting','direction']}
out['protocols']={}
for name in ['docs/FINAL_GROUND_TRUTH_PROTOCOL.md','docs/generated/mission_5a/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md','docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md']:
    p=ROOT/name;out['protocols'][name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'lines':len(p.read_text().splitlines())}
Path('/tmp/mission17c0_evidence.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k not in ['timelines','algebra_cases']},indent=2))
print(json.dumps({k:{a:b for a,b in v.items() if a not in ['dts','commands']} for k,v in out['algebra_cases'].items()},indent=2))

```

## 11. Files inspected and source-access limitations

The table names exact safe text/code artifacts used. 17A/17B originals were read in full; protocol comparison used complete diffs plus relevant context. Other listed supporting source/reports were inspected for relevant interfaces/claims, not certified line-by-line as universally correct. Long generated reports may contain unrelated assertions outside this mission's evidence. No cited historical conclusion was accepted as approval or as a substitute for available underlying evidence. All27 canonical timelines are individually cited above.

| Exact inspected path | Text lines at baseline (17B current includes correction appendix) | Purpose / scope |
|---|---|---|
| configs/frozen_experiment_v1.yaml | 67 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| data/governance/leg_exec_authorization.json | 24 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| data/ground_truth/authorized_reviewers.json | 6 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| data/manifests/layer_b_v2_annotation_inventory.json | 1244 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| data/metadata/vision_v1_metadata.json | 87 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| data/splits/705d388743ea/run_manifest.json | 4561 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| data/splits/705d388743ea/split_summary.json | 4503 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/FINAL_GROUND_TRUTH_PROTOCOL.md | 847 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md | 462 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/master_reaudit/MASTER_COMPUTER_VISION_AUDIT.md | 131 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/master_reaudit/MISSION_16E_MASTER_DECISION_REGISTER_INDEPENDENT_CHALLENGE.md | 719 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/master_reaudit/MISSION_16F_INDEPENDENT_CHALLENGE_OF_MISSION_16E.md | 507 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/master_reaudit/MISSION_16G_TABLE11_INDEPENDENT_VERIFICATION.md | 350 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/master_reaudit/MISSION_16H_INDEPENDENT_CHALLENGE_OF_16G.md | 308 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/master_reaudit/MISSION_17A_PI_APPROVAL_REGISTER.md | 162 | Complete primary 17A/17B file; correction history appended only for 17B |
| docs/generated/master_reaudit/MISSION_17A_PI_DECISION_RECONCILIATION.md | 569 | Complete primary 17A/17B file; correction history appended only for 17B |
| docs/generated/master_reaudit/MISSION_17B_CONVENTION_B_SIMULATION_DESIGN.md | 361 | Complete primary 17A/17B file; correction history appended only for 17B |
| docs/generated/master_reaudit/MISSION_17B_GROUPED_CV_SPLIT_DESIGN.md | 308 | Complete primary 17A/17B file; correction history appended only for 17B |
| docs/generated/master_reaudit/MISSION_17B_HUMAN_REVIEW_CLI_TECHNICAL_SPEC.md | 400 | Complete primary 17A/17B file; correction history appended only for 17B |
| docs/generated/master_reaudit/MISSION_17B_INTEGRATED_DEPENDENCY_AND_APPROVAL_REGISTER.md | 236 | Complete primary 17A/17B file; correction history appended only for 17B |
| docs/generated/master_reaudit/MISSION_17_MASTER_ACTION_AND_DEPENDENCY_REGISTER.md | 302 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/master_reaudit/MISSION_17_PI_DECISION_BRIEFING.md | 433 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/master_reaudit/MTR_ARITHMETIC_CENSORING_RECHALLENGE.md | 307 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/master_reaudit/MTR_PROVENANCE_CHALLENGE_AUDIT.md | 282 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/master_reaudit/TABLE11_TIMING_BOUND_INDEPENDENT_CHALLENGE.md | 265 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/mission_5a/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md | 867 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/mission_5a/GOVERNANCE_APPROVAL_DRAFTS_20261101_M5A.md | 46 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/mission_5a/PAPER_REVISION_PROPOSAL_20261101_M5A.md | 59 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/mission_5a/PROTOCOL_RECONCILIATION_REPORT_20261101_M5A.md | 48 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md | 64 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/mission_5a/STAGE21_SCHEMA_AND_REVIEW_GOVERNANCE_PROPOSAL_20261101_M5A.md | 49 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/phase2/EXPERIMENT_DESIGN_CONSOLIDATED.md | 158 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md | 877 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| docs/generated/phase2/PAPER_REVISION_CONSOLIDATED.md | 139 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| experiments/vision/39f402dfe460/evaluation/metrics.json | 62 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| pyproject.toml | 60 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| results/experiments/B4/single_events.json | 380 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| results/experiments/phase5_full_dataset_run_20261013/execution_manifest.json | 623 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| results/experiments/phase5_full_dataset_run_20261013/frozen_config_meta.json | 18 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| results/experiments/tables/table11_per_event_summary.csv | 28 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| results/experiments/tables/table11_per_event_summary.md | 31 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/annotation/adjudication_session.py | 728 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/annotation/promotion_gate.py | 647 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/annotation/second_review.py | 335 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/annotation/stage2_1_schema.py | 433 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/cli/main.py | 870 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/data/contracts.py | 195 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/data/manifest.py | 354 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/data/split.py | 172 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/evaluation/cache_only_engine.py | 918 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/evaluation/governance.py | 569 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/evaluation/lead_in_screen.py | 243 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/evaluation/metrics.py | 966 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/evaluation/protocol_choices.py | 197 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/evaluation/timebase.py | 17 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/experiments/preflight_validator.py | 1845 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/fusion/decision_engine.py | 691 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/safety/media_guard.py | 699 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/simulation/gate_model.py | 78 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/simulation/runner.py | 469 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| src/railway_detection/simulation/state_machine.py | 164 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| tests/conftest.py | 55 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| tests/test_phase11_11_adjudication_session.py | 583 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |
| tests/unit/test_split.py | 72 | Safe source/text/metadata: relevant claim, interface, historical context or test isolation check |

The full Git filename/history search found no standalone 17A/17B completion artifact; the available record set and that limitation are both preserved. Raw paths appearing as strings in these metadata files were not followed.

## 12. Recommended next action and stop

Researcher reviews the four 17C-0 deliverables and correction appendices, then resolves foundational protocol/security/camera/development-corpus questions before authorizing a separately bounded implementation mission. **STOP. Do not begin 17C-B,17C-C or any other implementation.** No scientific or execution permission is implied by PASS WITH CORRECTIONS.
