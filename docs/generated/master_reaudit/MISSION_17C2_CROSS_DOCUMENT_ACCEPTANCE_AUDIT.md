# Mission 17C-2 — Cross-document acceptance audit

Date: 2026-11-03. Repository: `/Users/sayemuddin/Desktop/Train_automation`. Baseline: `d4353ad9d49d427a129a9a4e83023fbd24e1a111` on `main`.

**PROPOSED SPECIFICATION — RESEARCHER REVIEW PENDING — NO IMPLEMENTATION OR REAL-DATA AUTHORIZATION.** Every future rule, interface, algorithm, transition and test in a section marked PROPOSED is proposed behavior, not implemented functionality or an adopted decision. VERIFIED facts below describe inspected source/text or exact document arithmetic only. PARTIALLY VERIFIED means support is conditional; CONTRADICTED means source/counterexample disagrees; UNSUPPORTED means evidence does not justify a claim; NOT VERIFIABLE means required evidence is unavailable or prohibited. NOT VERIFIED explicitly flags an unestablished fact without inventing a sixth claim classification.

Companion documents: [Human review/security](MISSION_17C2_REVISED_HUMAN_REVIEW_AND_SECURITY_SPEC.md) · [Simulation](MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md) · [Grouped CV](MISSION_17C2_REVISED_GROUPED_CV_SPLIT_SPEC.md) · [Decision/traceability register](MISSION_17C2_INTEGRATED_DECISION_AND_TRACEABILITY_REGISTER.md) · [Acceptance audit](MISSION_17C2_CROSS_DOCUMENT_ACCEPTANCE_AUDIT.md).

Historical 17B and C1 files are preserved unchanged. This document consolidates a candidate acceptance contract; it does not silently replace a historical record, adopt a protocol, approve Option C, appoint a person, issue/consume a token or authorize a next mission. R01–R08 and T01–T04 remain PENDING; X00–X07 remain NOT AUTHORIZED, with C1 qualifications preserved in the register.

Mission boundary: no raw-media inspection/preview/playback/decode/hash; no checkpoint or protected-cache access; no real inference/training/replay/evaluation/calibration/split generation; no annotation/adjudication/promotion; no source/test/config/protocol/governance edits. Only the five named documents and safe temporary documentation-validation scripts are created. Planned feature tests are not passing test results.

<a id="a1"></a>

## A1. Baseline, complete reading and preservation inventory

VERIFIED at mission start: repository path, main branch, local HEAD, local origin/main and live remote all matched `d4353ad9d49d427a129a9a4e83023fbd24e1a111`; working tree was clean, with all four C1 deliverables present. Every byte of the following eight required documents was read. Repeated path strings were aliased only in temporary display copies to reduce repetition; all original wording/equations/statuses/tables/code remained available and the alias map retained the full exact paths. No historical document was edited.

| Historical document — NOT MODIFIED | Baseline line count | Read/preservation scope |
|---|---|---|
| `docs/generated/master_reaudit/MISSION_17B_HUMAN_REVIEW_CLI_TECHNICAL_SPEC.md` | 400 | Complete contents read; baseline bytes retained; no silent deletion/supersession edit. |
| `docs/generated/master_reaudit/MISSION_17B_CONVENTION_B_SIMULATION_DESIGN.md` | 361 | Complete contents read; baseline bytes retained; no silent deletion/supersession edit. |
| `docs/generated/master_reaudit/MISSION_17B_GROUPED_CV_SPLIT_DESIGN.md` | 308 | Complete contents read; baseline bytes retained; no silent deletion/supersession edit. |
| `docs/generated/master_reaudit/MISSION_17B_INTEGRATED_DEPENDENCY_AND_APPROVAL_REGISTER.md` | 236 | Complete contents read; baseline bytes retained; no silent deletion/supersession edit. |
| `docs/generated/master_reaudit/MISSION_17C1_INDEPENDENT_CHALLENGE_OF_17C0.md` | 1036 | Complete contents read; baseline bytes retained; no silent deletion/supersession edit. |
| `docs/generated/master_reaudit/MISSION_17C1_CRITICAL_SECURITY_AND_DATA_GOVERNANCE_REVIEW.md` | 111 | Complete contents read; baseline bytes retained; no silent deletion/supersession edit. |
| `docs/generated/master_reaudit/MISSION_17C1_CORRECTION_COMPLETENESS_AUDIT.md` | 180 | Complete contents read; baseline bytes retained; no silent deletion/supersession edit. |
| `docs/generated/master_reaudit/MISSION_17C1_FINAL_PI_DECISION_PACKET.md` | 88 | Complete contents read; baseline bytes retained; no silent deletion/supersession edit. |

The exact required production source paths below were inspected as safe source text, including the stated relevant sections. VERIFIED here means source inspection, never runtime security/production acceptance. None was modified/imported for feature execution. No required source section was inaccessible; protected resource contents and human evidence remain outside scope.

| Source — NOT MODIFIED | Relevant inspected sections | What the evidence establishes |
|---|---|---|
| `src/railway_detection/safety/media_guard.py` | `src/railway_detection/safety/media_guard.py:48-54` | Python guard limits, not OS isolation |
| `src/railway_detection/safety/media_guard.py` | `src/railway_detection/safety/media_guard.py:113-151` | Enumerated operations and exact /2 record keys |
| `src/railway_detection/safety/media_guard.py` | `src/railway_detection/safety/media_guard.py:389-456` | Unsigned attestation, expiry/revocation, shared issuer/reviewer list |
| `src/railway_detection/safety/media_guard.py` | `src/railway_detection/safety/media_guard.py:530-564` | Protocol-byte binding and entry/per-operation API |
| `src/railway_detection/evaluation/governance.py` | `src/railway_detection/evaluation/governance.py:52-76` | Canonical decision/authorization paths and seven bindings |
| `src/railway_detection/evaluation/governance.py` | `src/railway_detection/evaluation/governance.py:424-501` | Current evaluation authority/unsigned attestation checks |
| `src/railway_detection/annotation/promotion_gate.py` | `src/railway_detection/annotation/promotion_gate.py:66-140` | String allowlist validation |
| `src/railway_detection/annotation/promotion_gate.py` | `src/railway_detection/annotation/promotion_gate.py:253-310` | Qualified lookup fallback and single-record/caller-state/media-hash boundary |
| `src/railway_detection/annotation/promotion_gate.py` | `src/railway_detection/annotation/promotion_gate.py:540-567` | Current bare-ID write/overwrite behavior |
| `src/railway_detection/annotation/stage2_1_schema.py` | `src/railway_detection/annotation/stage2_1_schema.py:33-79` | Active version,30s plausibility floor and existing state vocabulary |
| `src/railway_detection/annotation/stage2_1_schema.py` | `src/railway_detection/annotation/stage2_1_schema.py:279-350` | Actual record and history contract |
| `src/railway_detection/annotation/second_review.py` | `src/railway_detection/annotation/second_review.py:6-28` | Pending trigger-policy status and current conservative checks |
| `src/railway_detection/annotation/second_review.py` | `src/railway_detection/annotation/second_review.py:170-328` | Trigger inputs, independent review, unresolved disagreement |
| `src/railway_detection/simulation/runner.py` | `src/railway_detection/simulation/runner.py:26-35` | Nested decision in current SimulationStep |
| `src/railway_detection/simulation/runner.py` | `src/railway_detection/simulation/runner.py:161-233` | Sorting/arrival option, rejection, current retrospective application |
| `src/railway_detection/simulation/gate_model.py` | `src/railway_detection/simulation/gate_model.py:19-71` | 3s defaults, strict blockage predicate and target-state kinematics |
| `src/railway_detection/fusion/evidence.py` | `src/railway_detection/fusion/evidence.py:39-79` | Optional nested issued-command information |
| `src/railway_detection/fusion/decision_engine.py` | `src/railway_detection/fusion/decision_engine.py:113-147` | Actual order/duplicate comparison context |
| `src/railway_detection/fusion/decision_engine.py` | `src/railway_detection/fusion/decision_engine.py:391-430` | Two-tick confirmation/warning transition context |
| `src/railway_detection/data/split.py` | `src/railway_detection/data/split.py:1-172` | Actual deterministic old splitter, fallback and metadata semantics |
| `src/railway_detection/data/manifest.py` | `src/railway_detection/data/manifest.py:183-209` | Actual split_group_id versus source hint and metadata fields |

Additional safe evidence inspected: synthetic harness guards (`src/railway_detection/annotation/adjudication_session.py:126-142`; `src/railway_detection/annotation/adjudication_session.py:231-249`); inactive schema/version/boundary/adjudication proposal (`src/railway_detection/annotation/stage2_1_schema_proposed.py:1-60`; `src/railway_detection/annotation/stage2_1_schema_proposed.py:96-149`; `src/railway_detection/annotation/stage2_1_schema_proposed.py:254-278`); existing pure splitter test text (`tests/unit/test_split.py:1-72`); test-function inventory in existing second-review/governance tests (read-only AST inspection, not execution); full55-row RD source (`docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:1-64`); review-governance proposal (`docs/generated/mission_5a/STAGE21_SCHEMA_AND_REVIEW_GOVERNANCE_PROPOSAL_20261101_M5A.md:1-49`); safe metadata and consolidated design references cited in C1/C2. Raw/media/cache/model paths inside those texts were never followed. Metadata parsing counted27 entries/23+3+1 and 1,315 historical source groups, without content inspection or new splitting.

Explicit preservation scope includes every preexisting tracked file: all original 17B/17C-1/17C-0/17A/Mission 16 records; the eleven required source modules above; synthetic harness and inactive schema; existing tests including tests/unit/test_split.py and second-review/governance suites; configs/frozen_experiment_v1.yaml; protocols including docs/FINAL_GROUND_TRUTH_PROTOCOL.md and proposed v7.1.1; data/governance and reviewer allowlist; dataset metadata/manifests/splits; manuscript and historical results/Table11. No untracked user file was removed/overwritten. The final Git comparison excludes only the five authorized new C2 documents and must be empty.

<a id="a2"></a>

## A2. Cross-document consistency checks

The following is a document audit, not future feature-test acceptance. Each result is VERIFIED only for the reviewed candidate text; referenced behaviors remain PROPOSED and require pending decisions/implementation evidence.

| Check | Document result / evidence | Remaining acceptance boundary |
|---|---|---|
| 1. Roles and permissions | Identical six-role vocabulary, no reviewer→issuer/promoter implication; [Human review/security](MISSION_17C2_REVISED_HUMAN_REVIEW_AND_SECURITY_SPEC.md#h2), [Human review/security](MISSION_17C2_REVISED_HUMAN_REVIEW_AND_SECURITY_SPEC.md#h8), [Decision/traceability register](MISSION_17C2_INTEGRATED_DECISION_AND_TRACEABILITY_REGISTER.md#d1) | R05/T01 role registry, identity, conflicts and actual permissions remain unverified. |
| 2. Grant/session terminology | One reservation per session; repeated operation checks; same-session recovery/fencing; terminal state never resets grant; [Human review/security](MISSION_17C2_REVISED_HUMAN_REVIEW_AND_SECURITY_SPEC.md#h6), [Decision/traceability register](MISSION_17C2_INTEGRATED_DECISION_AND_TRACEABILITY_REGISTER.md#d1) | No actual grant/service/nonce state implemented. |
| 3. Observations/adjudication | DRAFT/SEALED preservation separate from review/boundary states and eligibility; originals immutable by policy; separate human adjudication; [Human review/security](MISSION_17C2_REVISED_HUMAN_REVIEW_AND_SECURITY_SPEC.md#h3), [Human review/security](MISSION_17C2_REVISED_HUMAN_REVIEW_AND_SECURITY_SPEC.md#h4) | Active8.1 compatibility and adoption remain R01 pending; no silent coercion. |
| 4. Time indices | Sensor observation k distinguished from merged timer/command boundaries; interval pre/post state and logical issue/application times defined; [Simulation](MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md#s2), [Simulation](MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md#s3) | Idealized zero latency is not measured physical runtime. |
| 5. Convention A/B | A historical newly-issued retroactive interval; B prior-effective command; fixed-command theorem conditions explicit; [Simulation](MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md#s1), [Simulation](MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md#s5) | Closed-loop output equality unverified; historical Table11 unchanged. |
| 6. Actuator parameters | P3 close/open 3s and 30°/s; TC01/02=84°; P6/asymmetric changes explicitly separate; [Simulation](MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md#s2), [Simulation](MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md#s6), [Decision/traceability register](MISSION_17C2_INTEGRATED_DECISION_AND_TRACEABILITY_REGISTER.md#d1) | T02/R04 do not become approved through a parity recommendation. |
| 7. Blockage predicate | One unrounded theta≤45 across all proposed oracles; inclusive equality retained; no rounding/epsilon classifier substitution | Numeric tolerance never excuses a different blocked bit or proves physical precision. |
| 8. Duration estimators | D_E right-endpoint sum versus D_C piecewise model integral, with distinct values/captions; [Simulation](MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md#s4), [Simulation](MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md#s6) | Neither is a measured physical-duration result; no universal−dt_final rule. |
| 9. Dataset roles | V1 development distinct from V2 descriptive27 inventory; actual train category not model eligibility; [Grouped CV](MISSION_17C2_REVISED_GROUPED_CV_SPLIT_SPEC.md#c1), [Decision/traceability register](MISSION_17C2_INTEGRATED_DECISION_AND_TRACEABILITY_REGISTER.md#d5) | R03/R06 actual corpus/eligibility/exposure are pending. |
| 10. Split/fold terms | Exactly-once OUTER_EVAL coverage and within-iteration pairwise disjointness; inner subsets exclude outer evaluation; [Grouped CV](MISSION_17C2_REVISED_GROUPED_CV_SPLIT_SPEC.md#c3), [Grouped CV](MISSION_17C2_REVISED_GROUPED_CV_SPLIT_SPEC.md#c4) | Cross-iteration training overlap allowed; no actual split. |
| 11. IDs/statuses | Exact C1 questions/approval-state strings for 8 R,4 T,8 X preserved; [Decision/traceability register](MISSION_17C2_INTEGRATED_DECISION_AND_TRACEABILITY_REGISTER.md#d2), [Decision/traceability register](MISSION_17C2_INTEGRATED_DECISION_AND_TRACEABILITY_REGISTER.md#d3), [Decision/traceability register](MISSION_17C2_INTEGRATED_DECISION_AND_TRACEABILITY_REGISTER.md#d4) | Recommendations are not approvals or execution records. |
| 12. Real-data prohibition | Same mission boundary in all five banners; no protected resource operation is specified as completed | All X00–X07 remain NOT AUTHORIZED. |
| 13. RD-001…055 | All 55 recorded directions explicitly mapped to source lines; no silent amendment; [Decision/traceability register](MISSION_17C2_INTEGRATED_DECISION_AND_TRACEABILITY_REGISTER.md#d8) | Conditional proposals that change science stay pending; RD-003 scoped mission Git instruction explained in A5. |
| 14. Evidence/implementation claims | Existing source facts cited and separate from PROPOSED contracts; missing facts labeled NOT VERIFIED/NOT VERIFIABLE | No independent human review, production acceptance, adopted protocol or real execution is claimed. |

<a id="a3"></a>

## A3. Oracle and algorithm consistency audit

VERIFIED document mathematics: under P3,90−30×.2=84°. TC03/04 endpoint sum1.6 differs from the 1.5 continuous model integral. The complete TC05 sequence repeats its four intervals five times and ends at 5s, with D_E3.55/D_C3.5. TC09 remains a counterexample to universal−dt_final. TC12 contains distinct conditional W1/W2 outcomes and selects neither policy. The source-grounded transition equation, inclusive predicate, exact horizon and input sequence permit independent checking of every proposed oracle; the temporary documentation validator checks these numeric references without importing any production module or reading any dataset output.

These checks validate **document arithmetic**, not execution of TC-SIM-01…20 by a future B implementation. TC-SIM-14's100-repeat behavior is a planned test and is NOT EXECUTED. Input-rejection, watchdog, command-adapter and logging fixtures are also planned tests, not passed tests. Numeric precision/accuracy/physical accuracy remain distinct. No existing production suite is run.

VERIFIED document structure of C4: the proposed allocation has frozen inputs/objective/hard constraints, exact deterministic traversal/tie-break/node counting, a declared null seed, canonical payload/receipt procedure and distinct exhaustive-infeasible/budget-undetermined results. This is a specification completeness finding, not execution of the search, proof of practical scalability, proof of real K feasibility or a generated synthetic/real split. All CV-T cases remain NOT EXECUTED; actual V1 lineage/labels/roles/exposure remain unverified. A prospective independent held-out claim is prohibited when exposure is unknown.

Completed reference-arithmetic receipt (VERIFIED exact rational calculations; **not executed feature tests**): the temporary checker used only the S4 equations and explicit synthetic numeric constants. It imported no production module, ran no allocator, opened no historical media/report output and wrote only temporary validation receipts. Fractions below are exact. TC14 repeatability, TC15 invalid-input behavior and TC19 command-conflict behavior remain future fixtures; no software behavior is certified by this table.

| Reference for proposed case | D_E(B) | D_C(B) | Final angle | D_E(A), when compared |
|---|---|---|---|---|
| 01 | 0 | 0 | 84 | not compared |
| 02 | 0 | 0 | 84 | not compared |
| 03 | 8/5 | 3/2 | 0 | not compared |
| 04 | 8/5 | 3/2 | 0 | not compared |
| 05 | 71/20 | 7/2 | 0 | not compared |
| 06 | 8 | 8 | 90 | 8 |
| 07 | 22/5 | 43/10 | 0 | 23/5 |
| 08 | 52/5 | 103/10 | 0 | 53/5 |
| 09 | 1/2 | 2/5 | 33 | 7/10 |
| 10-accepted-prefix | 0 | 0 | 78 | not compared |
| 11-accepted-prefix | 0 | 0 | 72 | not compared |
| 12-W1 | 0 | 0 | 60 | not compared |
| 12-W2 | 0 | 0 | 90 | not compared |
| 13-above | 0 | 0 | 450000001/10000000 | not compared |
| 13-equal | 1/5 | 1/5 | 45 | not compared |
| 13-below | 1/5 | 1/5 | 449999999/10000000 | not compared |
| 16 | 7/10 | 3/5 | 27 | not compared |
| 17 | 28/5 | 11/2 | 57 | 28/5 |
| 18 | 23/5 | 9/2 | 0 | 23/5 |
| 20-CLOSED | 2 | 3/2 | 0 | not compared |
| 20-OPEN | 0 | 1/2 | 90 | not compared |

<a id="a4"></a>

## A4. F01–F24 traceability and closure state

VERIFIED documentation coverage: [Decision/traceability register](MISSION_17C2_INTEGRATED_DECISION_AND_TRACEABILITY_REGISTER.md#d6) maps every F01–F24 group individually to corrected candidate sections, exact source/C1 evidence, a remaining technical question, R/T and X dependencies, and required future test/evidence. All 24 remain OPEN — NO IMPLEMENTATION ACCEPTANCE. Historical C1 priorities/assessments are retained; no new incident count or blanket “fixed” claim is introduced. F24 specifically remains a historical evidence limitation, not an observed production defect. Actual protected security, human review, physical identity, lineage and model exposure cannot be established by improving prose.

<a id="a5"></a>

## A5. RD conflicts and scoped instructions

VERIFIED documentary consistency: RD-001…055 source wording is retained in D8. No pending policy has been adopted. RD-043 remains risk-based, with its named trigger adoption still pending; C2 does not impose universal dual review. RD-015/028/035/052 independent-camera baseline persists; Option C remains unapproved. RD-024 pooled engine exclusion does not become a detector-training ban/permit. RD-025 controls do not become calibration/FAR-hour data. RD-039 full cohort does not become a V2 training/CV split. RD-006/012/018/046 deferrals persist. These were the material overreach paths; each now points to an explicit pending choice rather than silently altering direction.

Scoped instruction tension: RD-003 records researcher commit/snapshot custody (`docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:10`). The present user's explicit Mission 17C-2 instruction authorizes automatic commit/push of exactly five documentation files. That authority applies to this documentation delivery only; no broader scientific snapshot custody or protected execution direction is amended. No extra confirmation is needed for this already-authorized Git action. No other RD conflict is resolved by this mission; any later requested conflicting scope must return to its corresponding researcher decision.

<a id="a6"></a>

## A6. Missing facts and limitations

| Fact / evidence gap | Status and reason | Consequence |
|---|---|---|
| Human identities, qualifications, independence, appointments, allowed multi-role/recusal policy | NOT VERIFIED / NOT VERIFIABLE from the available string allowlist and source | R05/T01 and genuine evidence needed; no reviewer/issuer invented. |
| Protected issuer/anchor/backup/broker deployment and resistance to admin/authority compromise | NOT VERIFIED; no such infrastructure verified by text checks | Cooperative local profile cannot claim malicious-local-user security/OS isolation; stronger profile needs deployment evidence. |
| Applicable external approvals or historical session/test transcripts | NOT VERIFIABLE within inspected records | Missing repository evidence is not proof no external approval ever existed; no fabricated approval/transcript or human audit. |
| Actual media identity/visibility/landmark accuracy/censor counts/synchronization/player timing | NOT VERIFIABLE because raw inspection/hash/review/pilot is prohibited | No physical certification,20/23 GT acceptance or3.6s safety threshold. |
| Actual V1 physical-event/derivative/annotation join, label support and K feasibility | NOT VERIFIED; safe metadata lacks required evidence | No actual split/eligibility transfer; five folds not declared impossible merely from missing labels. |
| Actual historical/model initialization training exposure | NOT VERIFIABLE without trusted provenance, with checkpoints prohibited | No independent held-out/generalization claim. |
| Future numeric adapter, watchdog, actual B runner, ledger/adapter and CV allocator behavior | NOT VERIFIED; no implementation or feature suite is executed | Corrected specifications are not production acceptance; T01–T04/X00 remain pending/unauthorized. |
| Practical scalability of exhaustive reference search | NOT VERIFIED | T03 must accept a justified resource budget or reviewed equivalent algorithm; a budget limit is not infeasibility. |
| Actual manuscript/venue/release correction | NOT VERIFIED as completed action; historical draft unchanged | R07 remains pending; no submission/release/author roster is created. |

<a id="a7"></a>

## A7. Decisions and acceptance outcome

R01–R08 remain PENDING (R02 retains “Option C NOT APPROVED”; R05 retains “no appointments created”). T01–T04 remain PENDING. X00–X07 remain NOT AUTHORIZED. The exact full strings/questions and the scientific/technical/execution separation are checked against C1 rather than inferred from recommendations. C2 is a coherent candidate specification and documentary acceptance baseline **for researcher review only**. It does not adopt the candidate canonical codec, reference allocator, role policy, watchdog, numeric policy or schema; each is explicitly PROPOSED under the relevant decision. No F group is technically closed.

<a id="a8"></a>

## A8. Documentation validation and Git receipt

VERIFIED documentation-validation receipt: all five files passed table/fence/anchor/relative-link and citation-range checks; every F01–F24 and RD-001–RD-055 is mapped; all 20 exact C1 R/T/X questions and approval-state strings are preserved. The set specifies 18 human-security,20 simulation and 14 CV cases, all NOT EXECUTED. Twenty-one exact reference-arithmetic vectors were checked solely to validate printed oracle numbers, not a feature implementation. Secret/credential/approval-payload scans found none; no source imports, protected operations, feature tests or production tests were run. All preexisting tracked files remain byte-identical to baseline.

Final range statistics: 319 citation occurrences / 241 unique path-range tuples validated. They are range checks, not 319 independent factual confirmations or authenticated attestations. All 14 cross-document checks were reviewed; all 52 proposed feature cases remain NOT EXECUTED. Passing documentation checks means the candidate is reviewable; it does not confer implementation or scientific acceptance.

| Authorized new deliverable | Final lines |
|---|---|
| `MISSION_17C2_REVISED_HUMAN_REVIEW_AND_SECURITY_SPEC.md` | 238 |
| `MISSION_17C2_REVISED_CONVENTION_B_SIMULATION_SPEC.md` | 162 |
| `MISSION_17C2_REVISED_GROUPED_CV_SPLIT_SPEC.md` | 185 |
| `MISSION_17C2_INTEGRATED_DECISION_AND_TRACEABILITY_REGISTER.md` | 206 |
| `MISSION_17C2_CROSS_DOCUMENT_ACCEPTANCE_AUDIT.md` | 173 |

PROPOSED Git acceptance procedure (explicitly authorized for this documentation mission): inspect complete status/diff, require exactly the five named new Markdown files and no unrelated changes; validate unstaged and exact staged bytes, citations/links/IDs/oracles/safety; exact-path add; commit `docs: consolidate mission 17C2 corrective specifications`; normal `git push origin main`; verify local HEAD/origin/main/live remote equality, parent baseline, exactly-five-file addition scope and clean tree. Stop on divergence/unrelated changes or unresolved validation failure; never reset, amend, rebase, force-push or rewrite history. Final commit hash/synchronization evidence is reported after commit in chat so no self-referential commit hash is fabricated inside it.

**STOP after Mission 17C-2 for researcher review. No 17C-3, implementation, protocol promotion, Option C adoption, reviewer appointment or real-data execution starts.**
