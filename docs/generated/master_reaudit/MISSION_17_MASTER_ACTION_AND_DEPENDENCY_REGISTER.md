# MISSION 17: MASTER ACTION, GOVERNANCE, AND DEPENDENCY REGISTER

**Project:** Train Gate Automation — Bangladesh  
**Mission ID:** `17-MASTER-REAUDIT-FINAL-SYNTHESIS`  
**Document Role:** Comprehensive Technical Traceability, Issue Register, and Action Matrix  
**Auditor:** Independent Principal Research, Security, and Governance Auditor  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Historical Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Execution Authority:** NONE — AUDITOR DOES NOT DECIDE OR EXECUTE  
**Date:** 2026-11-03  

---

## 1. Complete Reaudit Deliverable Inventory (31 Deliverables)

The audit repository contains exactly **31 master reaudit deliverables** in `docs/generated/master_reaudit/`. Every report has been verified on disk:

| Report ID | Exact Filename | Audit Phase / Mission | Main Topic | Statutory Disposition | Primary Dependencies | Limitations & Evidentiary Scope |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REP-01** | `MASTER_HISTORICAL_RECONSTRUCTION.md` | Mission 16A | Conception to Phase 15 History | `COMPLETE AUDIT` | Historical commit logs | Read-only retrospective reconstruction |
| **REP-02** | `MASTER_DATASET_INTEGRITY_AUDIT.md` | Mission 16A | Corpus Inventory & Pairing | `COMPLETE AUDIT` | Video manifests | Zero raw media decoding |
| **REP-03** | `MASTER_COMPUTER_VISION_AUDIT.md` | Mission 16A | CV Architecture & YOLO Splits | `COMPLETE AUDIT` | Detection configs | Zero checkpoint byte access |
| **REP-04** | `MASTER_AUDIO_SENSOR_AUDIT.md` | Mission 16A | Audio Engine & FFT Windows | `COMPLETE AUDIT` | Audio pipeline | Zero raw audio playback |
| **REP-05** | `MASTER_SYSTEM_ARCHITECTURE_AUDIT.md` | Mission 16A | SM Rules & Actuator Model | `COMPLETE AUDIT` | `runner.py`, SM code | Software simulation trace |
| **REP-06** | `MASTER_METRIC_AND_EXPERIMENT_AUDIT.md` | Mission 16A | Metrics M1–M10 & B0–B5 Design | `COMPLETE AUDIT` | Metrics code | Real evaluation unauthorized |
| **REP-07** | `MASTER_GROUND_TRUTH_GOVERNANCE_AUDIT.md` | Mission 16A | Ground Truth Protocols & Gates | `COMPLETE AUDIT` | Schemas, protocols | No ground truth promoted |
| **REP-08** | `MASTER_SECURITY_GOVERNANCE_AUDIT.md` | Mission 16A | Incident F13-08 & Safe Guards | `COMPLETE AUDIT` | Safety modules | Python-level boundary only |
| **REP-09** | `MASTER_SOFTWARE_ENGINEERING_AUDIT.md` | Mission 16A | Code Quality, Tests & CI | `COMPLETE AUDIT` | Repo source tree | Untracked porcelain modules |
| **REP-10** | `MASTER_SCIENTIFIC_NOVELTY_AUDIT.md` | Mission 16A | State of the Art & Contribution | `COMPLETE AUDIT` | Literature review | Single-site research limitation |
| **REP-11** | `MASTER_MANUSCRIPT_READINESS_AUDIT.md` | Mission 16A | Paper Draft Benchmarking | `COMPLETE AUDIT` | Paper draft text | No performance claims verified |
| **REP-12** | `MASTER_PROJECT_COMPLETION_MATRIX.md` | Mission 16A | Work Package Tracking | `COMPLETE AUDIT` | Phase 1–15 logs | Qualitative readiness status |
| **REP-13** | `MASTER_PROJECT_RISK_REGISTER.json` | Mission 16A | Security & Metric Risks | `COMPLETE AUDIT` | Finding logs | Machine-readable risk ledger |
| **REP-14** | `MASTER_RESEARCHER_DECISION_REGISTER.md` | Mission 16A | 13 Mandatory Decisions Dossier | `COMPLETE AUDIT` | Historical registers | Unratified proposals |
| **REP-15** | `MASTER_REAUDIT_FINAL_REPORT.md` | Mission 16A | Executive Synthesis 16A | `COMPLETE AUDIT` | Reports 01–14 | Comprehensive 16A summary |
| **REP-16** | `MASTER_REAUDIT_ARTIFACT_MANIFEST.json` | Mission 16A | Cryptographic File Manifest | `COMPLETE AUDIT` | SHA-256 digests | Validates 16A artifact set |
| **REP-17** | `DATA_CHALLENGE_AUDIT.md` | 16A-Data | Ground Truth & Censoring | `DATA_AUDIT_CONTRADICTIONS_FOUND` | Corpus manifests | Discloses 20/23 left-censoring |
| **REP-18** | `CV_CHALLENGE_AUDIT.md` | 16A-CV | CV Split Leakage & mAP | `CV_AUDIT_PARTIALLY_VERIFIED` | Split metadata | Confirms split leakage risk |
| **REP-19** | `AUDIO_CHALLENGE_AUDIT.md` | 16A-Audio | Audio F1 & Checkpoint Pointers | `AUDIO_AUDIT_VERIFIED_WITH_LIMITATIONS` | Model configs | Checkpoint hash unverified |
| **REP-20** | `METRIC_CHALLENGE_AUDIT.md` | 16A-Metric | M4/M5 Definitions & MTR Screen | `METRIC_AUDIT_CONTRADICTIONS_FOUND` | Metric formulas | M4/M5 non-computable historically |
| **REP-21** | `METRIC_RECONCILIATION_AUDIT.md` | 16A-Recon | Metric Contracts & Terminology | `METRIC_CONTRACT_RECONCILED_WITH_LIMITATIONS` | Metrics source | Reconciles M5 as companion count |
| **REP-22** | `MTR_PROVENANCE_CHALLENGE_AUDIT.md` | 16A-MTR | 3.6s Derivation & Censoring | `MTR_PROVENANCE_CONTRADICTIONS_FOUND` | Lead-in screen code | 3.6s is discrete simulation artifact |
| **REP-23** | `MTR_ARITHMETIC_CENSORING_RECHALLENGE.md`| 16A-Rechallenge | 5 Hz vs 10 Hz Discretization | `MTR_TIMING_AND_CENSORING_CONTRADICTIONS_FOUND` | Simulation traces | Continuous latency is 3.7s at 5 Hz |
| **REP-24** | `SIMULATION_CAUSALITY_AUDIT.md` | 16A-Sim | Interval Actuation Semantics | `SIMULATION_CAUSALITY_CONTRADICTIONS_FOUND` | `runner.py:187-234` | Proves retroactive stepping |
| **REP-25** | `HISTORICAL_BENCHMARK_CAUSALITY_IMPACT_AUDIT.md`| Mission 16B | Impact on Historical Benchmarks | `HISTORICAL_METRICS_PARTIALLY_AFFECTED` | 17 summary JSONs | Confirms real M4/M5 were null |
| **REP-26** | `TABLE11_CLOSED_DURATION_PROVENANCE_AUDIT.md` | Mission 16C | Table 11 Source & Delta Bound | `TABLE11_DURATION_VERIFIED_WITH_LIMITATIONS` | Table 11 markdown | Refutes symmetric $\pm 0.20\,\text{s}$ bound |
| **REP-27** | `TABLE11_TIMING_BOUND_INDEPENDENT_CHALLENGE.md`| Mission 16D | Forward-Causal Bound Theorem | `ONE_SIDED_BOUND_VERIFIED_WITH_CONDITIONS` | B4 timelines | Proves $[T-0.2, T]$ under uniform dt |
| **REP-28** | `MISSION_16E_MASTER_DECISION_REGISTER_INDEPENDENT_CHALLENGE.md`| Mission 16E | Challenge of 13 Decisions & Plan | `MASTER_REGISTER_REQUIRES_MAJOR_RESTRUCTURING` | Register & code | Proves adjudication tool synthetic |
| **REP-29** | `MISSION_16F_INDEPENDENT_CHALLENGE_OF_MISSION_16E.md`| Mission 16F | Challenge of 16E Proposals | `MISSION_16E_RECOMMENDATIONS_REQUIRE_MAJOR_REVISION`| Security & math | Refutes ad-hoc $\pm 0.10\,\text{s}$ tolerance |
| **REP-30** | `MISSION_16G_TABLE11_INDEPENDENT_VERIFICATION.md`| Mission 16G | 27-Event Table 11 Forensic Proof | `EXACT_MINUS_0_20_PROVEN_FOR_ALL_27` | 27 B4 CSV timelines | Proves exact $-0.20\,\text{s}$ on B4 |
| **REP-31** | `MISSION_16H_INDEPENDENT_CHALLENGE_OF_16G.md`| Mission 16H | Adversarial Audit of 16G | `MISSION_16G_FULLY_INDEPENDENTLY_CONFIRMED` | 27 CSVs & Decimal math | Independent confirmation of 16G |

---

## 2. Complete Researcher Directional Decision History (RD-001 through RD-055)

The 55 researcher directional decisions recorded in [`docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md) are classified by current governance and implementation status:

| RD ID | Short Title / Direction | Current Status | Implemented in Code? | PI Ratification Required? | Reconciliation Finding / Consequence |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **RD-001** | Protocol Authority (v7 boundaries, v9 metrics) | `PENDING_RESEARCHER_CONFIRMATION` | No (in docs) | **YES** | Requires formal hash binding under Gate 3 |
| **RD-002** | Protocol Wording Before Hash Binding | `PENDING_RESEARCHER_CONFIRMATION` | No (in docs) | **YES** | Must promote `v7.1.0_PROPOSED.md` before binding |
| **RD-003** | Git + Hashed Snapshot Protocol | `PENDING_RESEARCHER_CONFIRMATION` | Yes (tool ready) | **YES** | Requires maintainer administrative commit |
| **RD-004** | $T_1$ Approach Landmark (Frog Switch Line) | `IMPLEMENTED_AND_VERIFIED` | Yes (in docs) | **YES** | Formally defined in v7.1.0 §2.1/§2.4 |
| **RD-005** | $T_2$ Physical Entry Boundary (Not Lens Plane) | `IMPLEMENTED_AND_VERIFIED` | Yes (code guard) | **YES** | Legacy lens-plane annotations rejected |
| **RD-006** | $T_2$ Physical Entry Landmark Deferral | `DIRECTION_RECORDED` | N/A | **YES** | Entry landmark deferred; $T_2$ unevaluable |
| **RD-007** | `T_OCC_START` Alias Restricted | `IMPLEMENTED_AND_VERIFIED` | Yes (in docs) | **YES** | Alias prohibited until entry landmark defined |
| **RD-008** | Replace $T_1$ POR Text with M4/M5 | `IMPLEMENTED_AND_VERIFIED` | Yes (in docs) | **YES** | Obsolete $T_1$ POR wrapped in historical tags |
| **RD-009** | Adopt GOV-, EXP-, AUTH- Canonical IDs | `IMPLEMENTED_AND_VERIFIED` | Yes (code aliases)| **YES** | Eliminates ambiguous D-1..D-11 notation |
| **RD-010** | Travel Direction Verified per Event | `PENDING_RESEARCHER_CONFIRMATION` | In schema | **YES** | Direction must be confirmed by human reviewer |
| **RD-011** | Censored Events Excluded from Point Estimates | `IMPLEMENTED_AND_VERIFIED` | Yes (metrics code)| **YES** | Censored counts tracked separately by reason |
| **RD-012** | Review Agreement Tolerance Deferral | `DIRECTION_RECORDED` | Deferred | **YES** | Mission 16F proved tolerance needs pilot |
| **RD-013** | Blind First Pass in Pilot Review | `PENDING_RESEARCHER_CONFIRMATION` | In schema | **YES** | Reviewers must annotate without candidate bias |
| **RD-014** | M4 Selected as Primary Premature Opening | `DIRECTION_RECORDED` | Yes (metrics) | **YES** | Contract adopted; historical runs were null |
| **RD-015** | Back-Stream Primary for M4/M5; Fused Exploratory| `DIRECTION_RECORDED` | In docs | **YES** | Scopes M4 to rear departure camera |
| **RD-016** | Corrected 6-Case M4/M5 Classification | `IMPLEMENTED_AND_VERIFIED` | Yes (code change) | **YES** | Evaluates strict protection interval |
| **RD-017** | M5 Reported as Integer Count Only | `IMPLEMENTED_AND_VERIFIED` | Yes (code change) | **YES** | Prohibits invalid M5 percentage rate |
| **RD-018** | Full Crossing Occupancy Duration Deferred | `DIRECTION_RECORDED` | N/A | **YES** | No same-camera pair; metric deferred |
| **RD-019** | Per-Event, Median, Range Reporting | `DIRECTION_RECORDED` | N/A | **YES** | Governs future duration tables |
| **RD-020** | Scoped Metric Suite (M4, M5, MTR Only) | `IMPLEMENTED_AND_VERIFIED` | Yes (metrics) | **YES** | Prevents unvalidated M1–M10 implementation |
| **RD-021** | Insufficient Lead-In Feasibility Screen | `IMPLEMENTED_AND_VERIFIED` | Yes (`lead_in.py`)| **YES** | Separates truncated footage from failure |
| **RD-022** | M4 Primary, M5 Companion, MTR Feasibility | `DIRECTION_RECORDED` | In docs | **YES** | Hierarchical safety metric reporting |
| **RD-023** | Descriptive Statistics Only (No P-values) | `IMPLEMENTED_AND_VERIFIED` | Yes (metrics) | **YES** | Prohibits inferential hypothesis testing |
| **RD-024** | Engine-Only Event Excluded from Pooled Cohort | `IMPLEMENTED_AND_VERIFIED` | Yes (metrics code)| **YES** | Engine event evaluated as separate case study |
| **RD-025** | No-Train Events: Exposure Hours Reported | `DIRECTION_RECORDED` | In docs | **YES** | Reports FAR without claiming train-free |
| **RD-026** | Fused R04 Scope Frozen to 11 Events | `DIRECTION_RECORDED` | In preflight | **YES** | Excludes `event_010`; blocks silent expansion |
| **RD-027** | Acoustic Offsets Never Shift Ground Truth | `IMPLEMENTED_AND_VERIFIED` | In docs | **YES** | Preserves camera-local physical clock |
| **RD-028** | Independent-Camera Primary; Fused Secondary | `DIRECTION_RECORDED` | In docs | **YES** | Single-camera primary benchmark |
| **RD-029** | Freeze `decision_policy_v1` Policy | `DIRECTION_RECORDED` | Config locked | **YES** | Documents heuristic controller limits |
| **RD-030** | Audio Supporting Only (Cannot Actuate Gate) | `IMPLEMENTED_AND_VERIFIED` | Yes (fusion code) | **YES** | Audio horn confirms, cannot close barrier |
| **RD-031** | Controller Constants (2-tick, 2-miss, no EMA) | `DIRECTION_RECORDED` | Config locked | **YES** | Design heuristics; not safety standards |
| **RD-032** | Model Detection Thresholds Exploratory Only | `DIRECTION_RECORDED` | In docs | **YES** | Prohibits claiming certified thresholds |
| **RD-033** | No ROI-Dependent Official Analysis | `DIRECTION_RECORDED` | In docs | **YES** | Full-frame inference standard |
| **RD-034** | B7e Numerics Deferred | `DIRECTION_RECORDED` | N/A | **YES** | Fault injection numerical bounds deferred |
| **RD-035** | Replay Conditions Scoped (B0–B2 + Back) | `DIRECTION_RECORDED` | In docs | **YES** | Front B0–B2 primary; back deferred (M-03) |
| **RD-036** | Historical Results Diagnostic Only | `DIRECTION_RECORDED` | In docs | **YES** | Replaces unverified historical scores |
| **RD-037** | Zero New Recordings for Version 1.0 | `DIRECTION_RECORDED` | In docs | **YES** | Fixed single-site 27-event scope |
| **RD-038** | Fault Injection Evaluated Separately | `DIRECTION_RECORDED` | In docs | **YES** | Keeps nominal benchmark clean |
| **RD-039** | Real-Data Pathway Requires Explicit Gate | `DIRECTION_RECORDED` | In preflight | **YES** | Enforces fail-closed evaluation authorization |
| **RD-040** | Per-Metric Evaluability Denominators | `IMPLEMENTED_AND_VERIFIED` | Yes (metrics) | **YES** | Separates unobserved from compliant events |
| **RD-041** | Event Inventory Frozen at 27 Events | `IMPLEMENTED_AND_VERIFIED` | Yes (manifests) | **YES** | 23 train + 3 negative + 1 engine |
| **RD-042** | External Second Reviewer Appointable | `PENDING_RESEARCHER_CONFIRMATION` | Blocked on PI | **YES** | Allowlist expansion required for dual review |
| **RD-043** | Risk-Based Second-Review Mandatory Triggers | `PENDING_RESEARCHER_CONFIRMATION` | In `second_review`| **YES** | Triggers defined; needs tolerance & reviewer |
| **RD-044** | Risk-Based Ground-Truth Audit Strategy | `DIRECTION_RECORDED` | In docs | **YES** | Focuses human audit on boundary shifts |
| **RD-045** | Adjudication via Separate Record; UNCERTAIN | `PENDING_RESEARCHER_CONFIRMATION` | In schema | **YES** | Never overwrite original; reject averaging |
| **RD-046** | Review Duration Floor Deferred | `DIRECTION_RECORDED` | Code floor 30s | **YES** | Retains 30.0s plausibility floor |
| **RD-047** | Hard-Case Review Pilot Proposal | `PENDING_RESEARCHER_CONFIRMATION` | In docs | **YES** | Calibration pilot before full 27 review |
| **RD-048** | Prioritize $T_1 - T_4$ Over Horn Boundaries | `DIRECTION_RECORDED` | In schema | **YES** | Focuses human effort on critical planes |
| **RD-049** | Ratify 2026-10-30 Decisions Record | `PENDING_RESEARCHER_CONFIRMATION` | Draft ready | **YES** | Formal signing required under Gate 3 |
| **RD-050** | Raw Media Direct Access Strictly Prohibited | `IMPLEMENTED_AND_VERIFIED` | Yes (`media_guard`)| **YES** | Enforces zero media decoding without token |
| **RD-051** | Descriptive Benchmark Title & RQs | `DIRECTION_RECORDED` | In paper draft | **YES** | Reframes paper to descriptive benchmark |
| **RD-052** | Reframe Abstract to Independent-Camera | `DIRECTION_RECORDED` | In paper draft | **YES** | Eliminates unproven dual-camera claims |
| **RD-053** | Publication Claims Strictly Limited | `DIRECTION_RECORDED` | In paper draft | **YES** | Discloses single-site and weather limits |
| **RD-054** | Human Authors Only; AI Disclosure Draft | `DIRECTION_RECORDED` | In paper draft | **YES** | Removes AI co-author; adds COPE disclosure |
| **RD-055** | Venue Undecided; Future Data Release Plan | `DIRECTION_RECORDED` | In docs | **YES** | Controlled research access; privacy review |

---

## 3. Consolidated Technical Findings Register

| Finding ID | Domain / Module | Verified Technical Fact | Primary Evidence | Confidence | Research Consequence |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **TF-01** | **Simulation Causality** | Decision engine evaluated at $t_k$; command applied retroactively to $[t_{k-1}, t_k]$. | `runner.py:187-229` | **CERTAIN** | Actuator moves 1 tick too early in legacy simulation. |
| **TF-02** | **Table 11 Uniformity** | All 27 B4 timelines have strictly uniform 5.0 Hz cadence ($\Delta t = 0.200000\,\text{s}$). | 27 CSV timelines | **CERTAIN** | Zero timing jitter; step summation matches Table 11. |
| **TF-03** | **Table 11 Termination** | All 27 B4 recordings terminated while gate was fully lowered ($\theta_N = 0.0^\circ$). | 27 CSV timelines | **CERTAIN** | Accumulator included final step across all 27 events. |
| **TF-04** | **Table 11 Timing Offset** | Forward-causal duration under Convention B is exactly $T - 0.2000\,\text{s}$ for all 27 events. | Missions 16G, 16H | **CERTAIN** | Causal correction mathematically & empirically proven. |
| **TF-05** | **Historical M4/M5 Status**| Historical real-data M4/M5 and clearance latency were non-computable ($T_4 = \text{null}$). | 17 summary JSONs | **CERTAIN** | Must report as `NON-COMPUTABLE`, never as zero. |
| **TF-06** | **Lead-In Censoring** | 20 of 23 train events are left-censored ($T_0 \le 0.0\,\text{s}$); $T_1$ measures recording pre-roll. | Proposal metadata | **CERTAIN** | Physical MTR is `NOT_ESTIMABLE` on this corpus. |
| **TF-07** | **MTR 3.6s Origin** | 3.6s threshold is implementation-derived ($0.2\text{s} + 2.0\text{s} + 1.5\text{s} - 0.1\text{s}$). | `lead_in.py`, 16A-Recon | **CERTAIN** | Not a certified railway regulatory standard. |
| **TF-08** | **CV Generalization** | YOLO still-image mAP@50=99.46% on Layer A split, but carries `leakage_risk: true`. | `split_metadata.json` | **HIGH** | Test split shares recording scenes; field generalization unproven. |
| **TF-09** | **Audio Model V3** | Audio V3 historical F1=0.869; checkpoint hash was config-declared only. | Audio configs | **MEDIUM** | Checkpoint integrity unverified under media guard. |
| **TF-10** | **Adjudication Tooling** | `adjudication_session.py` rejects real IDs (`_require_synthetic_id`) and non-temp paths. | `adjudication_session.py:126`| **CERTAIN** | Tool is synthetic-only; human review needs new CLI. |
| **TF-11** | **Promotion Gate Token** | `promotion_gate.py` live-hashes raw media; requires `AUTH-MEDIA-ACCESS (PROMOTION)`. | `promotion_gate.py:219` | **CERTAIN** | Promotion cannot execute without media permissions. |
| **TF-12** | **Back-Stream Replay Gap**| `cache_only_engine.py` supports B0–B2 only; back-stream feature caches do not exist. | `cache_only_engine.py:77` | **CERTAIN** | Primary benchmark must be scoped to front camera (M-03). |

---

## 4. Consolidated Project Risk and Issue Register (20 Issues)

| Issue ID | Risk Title & Description | Severity | Impacted Activity | Required Owner | Concrete Resolution Required |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **ISSUE-01** | **Protocol In-Place Contradiction:** v7.0.0 defines POR via $T_1$; contradicts M4/M5. | **CRITICAL** | GT Review & Promotion | PI / Lead Researcher | Promote `v7.1.0_PROPOSED.md` to in-place canonical protocol. |
| **ISSUE-02** | **Deferred $T_2$ Entry Landmark:** Physical roadway entry landmark undefined (RD-006). | **HIGH** | Occupancy Evaluation | PI / Field Team | Defer $T_2$ occupancy duration to Version 2.0. |
| **ISSUE-03** | **Single Reviewer Allowlist:** Only 1 reviewer on disk (`authorized_reviewers.json`). | **CRITICAL** | Dual Human Review | PI | Nominate & appoint qualified 2nd reviewer (RD-042). |
| **ISSUE-04** | **Ad-Hoc Tolerance Rejection:** $\pm 0.10\,\text{s}$ tolerance mathematically flawed (16F). | **HIGH** | Second Review Gate | PI / Researchers | Conduct human calibration pilot; establish empirical variance. |
| **ISSUE-05** | **Missing Adjudication Schema:** No schema format for recorded researcher adjudication. | **HIGH** | Disagreement Handling | Software Engineer | Implement append-only adjudication schema in `stage2_1_schema.py`. |
| **ISSUE-06** | **Synthetic-Only Adjudication Tool:** `adjudication_session.py` blocks real corpus. | **CRITICAL** | Human Adjudication | Software Engineer | Implement dedicated `human_review_session.py` CLI (Option D2). |
| **ISSUE-07** | **Uncommitted Working Tree Risk:** 25 modified files bypass commit-bound tokens. | **HIGH** | Token Verification | Maintainer / Engineer | Bind tokens to working tree tree-hash (`git write-tree`). |
| **ISSUE-08** | **Token Replay Vulnerability:** `EVAL-AUTH` lacks atomic stateful nonce locking. | **HIGH** | Official Evaluation | Software Engineer | Implement atomic locking against local revocation ledger. |
| **ISSUE-09** | **Promotion Gate Media Permitting:** Promotion gate live-hashes media without token. | **CRITICAL** | Stage-3 GT Promotion | PI / Engineer | Issue scoped `AUTH-MEDIA-ACCESS (PROMOTION)` permit. |
| **ISSUE-10** | **Simulation Retroactive Stepping:** Actuator steps retroactively over preceding `dt`. | **HIGH** | Version 2.0 Simulation | Software Engineer | Refactor `runner.py` to forward-causal stepping (Convention B). |
| **ISSUE-11** | **Left-Censored MTR Conflation:** 20/23 train arrivals truncated at clip onset. | **HIGH** | Manuscript Reporting | Authors | Classify physical MTR as `NOT_ESTIMABLE` in manuscript. |
| **ISSUE-12** | **Historical M4/M5 Non-Computability:** Missing $T_4$ prevented historical computation. | **HIGH** | Manuscript Reporting | Authors | Report historical M4/M5 as `NON-COMPUTABLE` in Table 3. |
| **ISSUE-13** | **Table 11 Historical Baseline:** Historical values must not be overwritten in-place. | **HIGH** | Manuscript Reporting | Authors | Retain Table 11; publish derived causal column with note. |
| **ISSUE-14** | **Back-Stream Cache Gap (M-03):** Back-stream conditions unsupported in cache engine. | **HIGH** | Benchmark Scope | PI / Authors | Scope paper v1.0 strictly to front-camera B0, B1, B2. |
| **ISSUE-15** | **Mission 12 Incident F13-08 Open:** Test execution without proof of non-access. | **MEDIUM** | Governance Closure | PI | Sign administrative risk-acceptance closure memo. |
| **ISSUE-16** | **R04 Camera Clock Desynchronization:** Front & back clocks uncalibrated (RD-026). | **HIGH** | Dual-Camera Fusion | Researchers | Keep dual-camera analysis strictly exploratory (11 events). |
| **ISSUE-17** | **CV Split Scene Leakage:** Test images share video sequences with train/val. | **MEDIUM** | CV Claims | Authors | Explicitly disclose development-split leakage limitation. |
| **ISSUE-18** | **Checkpoint Access Policy (F13-09):** Preflight reads bytes without permit. | **MEDIUM** | Readiness Gate | Software Engineer | Decouple preflight metadata checks from runtime byte reads. |
| **ISSUE-19** | **Manuscript Authorship Ethics:** AI agent listed as co-author (violates COPE). | **HIGH** | Publication | PI / Authors | Remove AI agent; list human authors; add AI disclosure. |
| **ISSUE-20** | **Dataset Privacy Scrub (RD-055):** Public release requires human face/plate scrub. | **HIGH** | Code/Data Release | PI | Complete privacy scrub before public repository release. |

---

## 5. Comprehensive Activity Authorization Matrix

| Project Activity | Required Governing Document / Token | Current Disk Evidence | Statutory Status | Permitted to Execute Now? |
| :--- | :--- | :--- | :---: | :---: |
| **Safe Code Inspection** | Audit Charter | Verified safe files in `src/` | **AUTHORIZED** | **`YES`** |
| **Synthetic Unit Testing** | `pytest` Safe Allowlist | 100 safe test files | **AUTHORIZED** | **`YES`** |
| **Mathematical Simulation** | Isolated Synthetic Scripts | Manually supplied data | **AUTHORIZED** | **`YES`** |
| **Raw Media Video Inspection** | `AUTH-MEDIA-ACCESS (REVIEW)` | None on disk | **UNAUTHORIZED** | **`NO`** |
| **Raw Media Hashing (Promotion)**| `AUTH-MEDIA-ACCESS (PROMOTION)` | None on disk | **UNAUTHORIZED** | **`NO`** |
| **Model Checkpoint Byte Hashing**| `AUTH-CHECKPOINT-ACCESS` | None on disk | **UNAUTHORIZED** | **`NO`** |
| **Human Annotation Sessions** | Reviewer Allowlist + Media Permit | Single reviewer; no permit | **UNAUTHORIZED** | **`NO`** |
| **Stage-3 Ground Truth Promotion**| Batch Promotion Approval Memo | None on disk | **UNAUTHORIZED** | **`NO`** |
| **Feature-Cache Descriptive Replay**| `AUTH-DESCRIPTIVE-CACHE-EXEC` | None on disk | **UNAUTHORIZED** | **`NO`** |
| **Full Pipeline Real Evaluation**| `EVAL-AUTH` v1.1 | None on disk | **UNAUTHORIZED** | **`NO`** |
| **In-Place Protocol Mutation** | Formal PI Ratification Memo | Unratified proposals | **UNAUTHORIZED** | **`NO`** |
| **Git Commits / History Changes** | Repository Maintainer Action | Working tree dirty (25/388)| **UNAUTHORIZED** | **`NO`** |
| **External Paper Submission** | Author Agreement & Privacy Sign-off | Incomplete draft | **UNAUTHORIZED** | **`NO`** |

---

## 6. Execution Roadmap and Work Package Specifications

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ EIGHT WORK PACKAGES (WP-1 THROUGH WP-8)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ WP-1: Protocol & Administrative Ratification (Immediate PI Action)          │
│ WP-2: Reviewer Onboarding & Calibration Pilot (Human Governance)             │
│ WP-3: Tooling Recovery & Adjudication Architecture (Software Engineering)   │
│ WP-4: Human Ground-Truth Annotation & Adjudication (Human Research Activity) │
│ WP-5: Ground-Truth Certification & Promotion (Governance & Security)        │
│ WP-6: Simulation Engine Causality Refactoring (Software Engineering)         │
│ WP-7: Descriptive Benchmark Replay Execution (Authorized Evaluation)         │
│ WP-8: Manuscript Completion & Submission Packaging (Academic Finalization)  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Work Package Specifications:

#### Work Package 1: Protocol & Administrative Ratification
- **Objective:** Establish unambiguous, non-contradictory canonical protocol baselines and close historical administrative issues.
- **Prerequisites:** None (Can execute immediately).
- **Human Owner:** Principal Investigator (`raihankabirrahu@gmail.com`).
- **Permissible AI Contribution:** Draft ratification memos and promotion diffs.
- **Deliverables:** Promoted `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` (v7.1.0), signed Incident F13-08 closure memo, updated manuscript author block.
- **Acceptance Criteria:** `diff` between proposed and canonical is clean; protocol bindings SHA-256 registered.
- **Stop Condition:** Halt if protocol retains $T_1$ Premature Opening text.

#### Work Package 2: Reviewer Onboarding & Calibration Pilot
- **Objective:** Establish dual-reviewer capability and measure empirical boundary variance across video frame rates.
- **Prerequisites:** WP-1 completion.
- **Human Owner:** PI and Nominated Second Reviewer.
- **Permissible AI Contribution:** Prepare blind calibration event packages and statistical variance scripts.
- **Deliverables:** Expanded `data/ground_truth/authorized_reviewers.json`, Calibration Variance Report, ratified agreement tolerance $\epsilon$.
- **Acceptance Criteria:** Independent reviewer qualifications documented; empirical variance measured across 29.97 fps and 59.94 fps streams.
- **Stop Condition:** Halt if only one reviewer remains on the allowlist.

#### Work Package 3: Tooling Recovery & Adjudication Architecture
- **Objective:** Modernize annotation and gate tooling to process real corpus events safely without breaking synthetic test isolation.
- **Prerequisites:** WP-1, WP-2.
- **Human Owner:** Software Verification Engineer.
- **Permissible AI Contribution:** Implement `human_review_session.py`, implement adjudication schema in `stage2_1_schema.py`, decouple checkpoint preflight in `frozen_config.py`.
- **Deliverables:** Verified `human_review_session.py`, passing synthetic unit tests.
- **Acceptance Criteria:** Tool accepts real event IDs under `AUTH-MEDIA-ACCESS`; `adjudication_session.py` remains untouched for synthetic tests.
- **Stop Condition:** Halt if synthetic test isolation is compromised.

#### Work Package 4: Human Ground-Truth Annotation & Adjudication
- **Objective:** Produce genuine, dual-reviewed, certified Stage-2.1 ground truth across all 27 corpus events.
- **Prerequisites:** WP-1, WP-2, WP-3, issuance of `AUTH-MEDIA-ACCESS (REVIEW)`.
- **Human Owner:** Primary Reviewer, Second Reviewer, Lead Researcher (Adjudicator).
- **Permissible AI Contribution:** Zero boundary generation. AI can only run file validation checks.
- **Deliverables:** 27 Stage-2.1 review JSON files in `data/ground_truth/reviews/`, recorded adjudication records for all RD-043 triggered events.
- **Acceptance Criteria:** Zero unadjudicated disputes; minimum review duration $\ge 30.0\,\text{s}$ per event; reviewer observed hashes recorded.
- **Stop Condition:** Halt if any boundary disagreement remains unresolved.

#### Work Package 5: Ground-Truth Certification & Promotion
- **Objective:** Execute the fail-closed promotion gate to generate immutable Stage-3 ground truth receipts.
- **Prerequisites:** WP-4 completion, issuance of `AUTH-MEDIA-ACCESS (PROMOTION)`.
- **Human Owner:** Principal Investigator.
- **Permissible AI Contribution:** Execute `promotion_gate.py` under human observation; format promotion manifest.
- **Deliverables:** 27 promoted ground-truth receipts in `data/ground_truth/promoted/`.
- **Acceptance Criteria:** `promotion_gate.py` exits with 0 violations; live SHA-256 digests match inventory.
- **Stop Condition:** Halt if promotion gate rejects any record.

#### Work Package 6: Simulation Engine Causality Refactoring
- **Objective:** Refactor `EventSimulationRunner` to enforce forward-causal actuator stepping (Convention B) and resolve timing artifacts.
- **Prerequisites:** WP-1.
- **Human Owner:** Simulation Engineer.
- **Permissible AI Contribution:** Refactor `_run_frames()` in `runner.py`, update synthetic simulation tests, verify Table 11 timing bound theorem.
- **Deliverables:** Refactored `runner.py`, passing forward-causal synthetic test suite.
- **Acceptance Criteria:** Gate command issued at $t_k$ acts strictly on $[t_k, t_{k+1}]$; Table 11 forward-causal delta is verified.
- **Stop Condition:** Halt if forward-causal stepping introduces non-deterministic state jitter.

#### Work Package 7: Descriptive Benchmark Replay Execution
- **Objective:** Execute official descriptive benchmark replay across conditions B0, B1, and B2 from static feature caches.
- **Prerequisites:** WP-5, WP-6, issuance of `AUTH-DESCRIPTIVE-CACHE-EXEC`.
- **Human Owner:** Research Team Lead.
- **Permissible AI Contribution:** Run `cache_only_engine.py`, collect metric outputs, verify zero raw media access.
- **Deliverables:** Official benchmark replay outputs, verified descriptive summary table.
- **Acceptance Criteria:** Execution gate validates Stage-3 receipts and run token; zero raw media opened.
- **Stop Condition:** Halt if runner attempts to access `.mov` files or unverified caches.

#### Work Package 8: Manuscript Completion & Submission Packaging
- **Objective:** Populate manuscript tables with certified empirical counts, finalize scientific narrative, and package for submission.
- **Prerequisites:** WP-7 completion.
- **Human Owner:** Principal Investigator and Co-Authors.
- **Permissible AI Contribution:** Draft descriptive prose, format LaTeX tables, verify citation links.
- **Deliverables:** Submission-ready `PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`, reproducibility manifest.
- **Acceptance Criteria:** M4/M5 and physical MTR reported with required qualifications; authorship adheres to COPE guidelines.
- **Stop Condition:** Halt if manuscript claims unverified safety improvements or zero premature openings.

---

## 7. Section-by-Section Manuscript Readiness Assessment

| Paper Section | Current Readiness Status | Evidence Available | Required Scientific Qualification | Remaining Work Dependency |
| :--- | :---: | :--- | :--- | :--- |
| **Title & Subtitle** | **`DRAFTABLE_NOW`** | RD-051, RD-052 | Must state "Descriptive Benchmark" and "Single-Site". | WP-1 (Confirm wording) |
| **Abstract** | **`DRAFTABLE_NOW`** | Reaudit findings | Must state B0–B2 scope; no safety-gain claims. | WP-1 (Confirm framing) |
| **Introduction** | **`DRAFTABLE_NOW`** | Historical context | Frame as computational feasibility study in Bangladesh. | WP-1 |
| **Related Work** | **`DRAFTABLE_NOW`** | Literature matrix | Distinguish laboratory CV from field deployment. | None |
| **Research Questions** | **`DRAFTABLE_NOW`** | RD-051 (RQ1–RQ4) | Restrict to multimodal fusion latency & lead time. | WP-1 |
| **System Architecture**| **`DRAFTABLE_NOW`** | Source code | Disclose discrete 5.0 Hz stepping & heuristic rules. | WP-6 (Causality note) |
| **CV Methodology** | **`DRAFTABLE_NOW`** | Layer A metrics | Disclose still-image fallback split and leakage risk. | None |
| **Audio Methodology** | **`DRAFTABLE_NOW`** | Audio V3 docs | Explicitly state audio is supporting-only. | None |
| **Annotation Protocol**| **`DRAFTABLE_NOW`** | v7.1.0-PROPOSED | Disclose deferred $T_2$ landmark & left-censoring. | WP-1 (Promote v7.1.0) |
| **Experimental Design**| **`DRAFTABLE_NOW`** | RD-035 (B0–B2) | Front-camera primary; back-stream exploratory (M-03). | WP-7 (Scope lock) |
| **Table 11 (Closed Time)**| **`DRAFTABLE_NOW`** | Missions 16G, 16H | Present Convention A baseline + derived causal column. | None (Math verified) |
| **Detection Performance**| **`PENDING_EVALUATION`** | Raw cache data | Awaits authorized descriptive cache replay. | WP-7 (Replay run) |
| **M4 / M5 Safety Table**| **`DRAFTABLE_WITH_QUAL.`**| Mission 16B | Must report historical real-data M4/M5 as `NON-COMPUTABLE`.| WP-7 (Replay check) |
| **MTR Lead-In Feasibility**| **`DRAFTABLE_WITH_QUAL.`**| Missions 16A-MTR | Report physical MTR as `NOT_ESTIMABLE` (20/23 censored). | None |
| **Threats to Validity**| **`DRAFTABLE_NOW`** | Risk register | Document single site, weather, and camera clock gaps. | None |
| **Conclusion** | **`DRAFTABLE_NOW`** | Reaudit findings | Highlight multimodal feasibility; call for field trials. | WP-8 |
| **Authorship Block** | **`DRAFTABLE_NOW`** | RD-054 | Human authors only; affiliations & ORCIDs required. | WP-1 (Supply names) |
| **AI-Use Disclosure** | **`DRAFTABLE_NOW`** | Draft disclosure | Formal COPE/IEEE statement detailing AI agent roles. | WP-1 |

---

REAL-DATA EXECUTION: NOT AUTHORIZED.
