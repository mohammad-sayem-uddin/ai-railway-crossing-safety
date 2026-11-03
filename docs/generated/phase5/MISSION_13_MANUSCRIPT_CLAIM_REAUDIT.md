# Mission 13 — WP13.5a Manuscript Claim Re-Audit

**Document audited:** `docs/generated/phase5/PAPER_DRAFT_PHASE5_REVISION.md` (206 lines, mtime 2026-11-02 10:35).
**Baseline ledger:** `MISSION_11B_COMPLETE_MANUSCRIPT_CLAIM_LEDGER.md` (CL-001–CL-036). **Mission 12 claims under test:** `MISSION_12_MANUSCRIPT_CORRECTIONS.md`.
**Literature:** no web research, no external verification. Citation statuses below are limited to what the repository shows.
Status vocabulary: SUPPORTED · SUPPORTED-AS-PROPOSED (qualified correctly as proposed) · PARTIAL · UNSUPPORTED · UNVERIFIED · CONTRADICTED · PENDING. "Rechecked" = I opened the cited source in this audit.

## 1. The 36 Mission 11B claims

| ID | Lines now | Claim / topic | M13 finding | Status | Rechecked |
|---|---|---|---|---|---|
| CL-001 | 1-7 | Correction notice; failed audits; no authorization implied | Notice present; matches repository governance state | SUPPORTED | yes |
| CL-002 | 9-24 | Auditable benchmark; results pending | Abstract now states "methodology and engineering specification, not an evaluated real-world system" | SUPPORTED | yes |
| CL-003 | 13-17 | Baseline, agent, date | Agent "not independently verified"; author block placeholder; date correct | SUPPORTED | yes |
| CL-004 | 18, 133-158 | No performance numbers | All result cells `[PENDING]`; the 120.8 s negative exposure is metadata, not a result | SUPPORTED | yes |
| CL-005 | 24 | Affordable alternative to track circuits | Removed; abstract says cost-effectiveness not evaluated (grep: no "afford") | SUPPORTED (as non-assertion) | yes |
| CL-006 | 32-36 | Literature failure frequency | Hedged preface, but "often treated", "frequently begin", "severely distorts", "exhibit non-stationary offsets… severe artifacts" remain as uncited generalizations | PARTIAL | yes |
| CL-007 | 61-64 | 27-event cohort (23/3/1) | `data/ground_truth/reviews` holds 23 + 3 + 1 record files = 27 (names counted; contents not used). These are legacy records under invalidation notices, so this supports *inventory*, not approved ground truth | SUPPORTED as metadata | yes |
| CL-008 | 112-129 | M4/M5/MTR contracts | `metrics.classify_m4` docstring: strict open interval `(t_blocked, T4)`, 1 µs snapping, `replay_ended_before_T4` never "safe", M5 requires zero origin. MTR lead-in screen exists in `lead_in_screen.py` (not re-read) | SUPPORTED (code + synthetic tests; not empirical) | partly |
| CL-009 | 86-89 | Two-reviewer governance | Now explicitly "RD-043 … NOT ADOPTED / proposal" | SUPPORTED-AS-PROPOSED | yes |
| CL-010 | 90 | Model-independence firewall; agents blocked from authoring GT | Cited to `stage2_1_schema.py`, not re-read here; Mission 11B supported it | SUPPORTED (prior audit) | no |
| CL-011 | 30 | Fatality ranking, crossing counts, costs | Removed ("not asserted") | SUPPORTED (as non-assertion) | yes |
| CL-012 | 32-38 | Replay/censoring/clock/generalization risks | As CL-006 | PARTIAL | yes |
| CL-013 | 42-47 | Research questions | Proposed; RQ3 conditional | SUPPORTED-AS-PROPOSED | yes |
| CL-014 | 51-67 | Single site `crossing_A`, 23/3/1, engine isolated | `crossing_A` appears in repository docs; cohort counts as CL-007; "RD-051–053 / RD-022" are directional decisions, not signed approvals | SUPPORTED-AS-PROPOSED | yes |
| CL-015 | 66-67 | Cohort-qualified IDs; bare IDs rejected | Safe-set test `test_phase11_cohort_qualified_identity` is current and classified safe; not re-run individually | SUPPORTED (prior audit) | partly |
| CL-016 | 75-84 | Protocol v7.1.1 landmarks; T2 deferred | T2 deferral (RD-006) is documented in `docs/FINAL_GROUND_TRUTH_PROTOCOL.md`, a modified, unadopted working-tree document; code names `T1_danger_zone_entry`, `T4_tail_clearance` match | PARTIAL (proposal status) | yes |
| CL-017 | 84 | 1 µs snapping, strict comparison | `evaluation/timebase.py` docstring and `classify_m4` | SUPPORTED | yes |
| CL-018 | 86-90 | RD-043 six triggers, no tolerance | Qualified as "implementation tests … not a formal approval" | SUPPORTED-AS-PROPOSED | yes |
| CL-019 | 96-100 | YOLOv8n, native FPS, audio cadence, 5 Hz tick | YOLOv8n ✓ (`frozen_experiment_v1.yaml:16`); native FPS removed ✓; 1.0 s window/0.5 s hop ✓ (`audio/preprocessor.py:112-113`, policy `audio_nominal_hop_s: 0.5`); `timing.tick_s: 0.2` ✓. **But** "CNN … detecting locomotive engine rumble, horn, and rail clatter" is **not supported**: the repository classifier is binary (`train_horn` / `non_train_sound`; `Non-Horn / Train Horn`); "engine rumble" occurs only in annotator sample text | PARTIAL; class list UNSUPPORTED | yes |
| CL-020 | 100, 177 | Decision-policy SHA-256 | `shasum -a 256 configs/decision_policy_v1.yaml` = `c87c1432…8575` ✓ | SUPPORTED | yes |
| CL-021 | 102-103 | Audio supporting only | Policy `RULE_2_AUDIO_SUPPORT_ONLY` ✓ | SUPPORTED | yes |
| CL-022 | 105-108 | Camera roles; B0_back provisional; R04 pending | Provisional/pending wording present; R04 subset config lists 11 included events, `authorized_for_execution: false` ✓ | SUPPORTED-AS-PROPOSED | yes |
| CL-023 | 114-119 | M4 wording | Now "operational replay definition, not continuous physical occupancy" — matches code | SUPPORTED | yes |
| CL-024 | 121-129 | M5 origin, MTR lead-in | As CL-008 | SUPPORTED | partly |
| CL-025 | 133-158 | Tables, negative controls, engine IDs | "Engine Movement Case Study" ✓; placeholders ✓; "approx. 120.8 camera-stream-seconds" is carried from older manuscripts and not checked against data here | PENDING / 120.8 UNVERIFIED | yes |
| CL-026 | 162-167 | Limitations | Limitation 3 ("rural developing regions often lack…") and limitation 4 ("valuable empirical evidence regarding multi-modal sensor fusion dynamics in South Asian rail operating environments") assert more than a pending-results paper can: no empirical evidence is presented | PARTIAL (limitation 4 overclaims) | yes |
| CL-027 | 171-181 | Claim matrix labels | "VERIFIED" relabeled to SUPPORTED-BY-SYNTHETIC / PROPOSED / PENDING; "47 tests" gone. **Line 181 cites `data/ground_truth/stage21_promotion_receipt.json`; the code constant is `data/governance/stage21_promotion_receipt.json`** (`governance.py:56`) | PARTIAL (wrong path) | yes |
| CL-028 | 178-181 | Empirical outcomes / receipt pending | Pending; no receipt exists | PENDING | yes |
| CL-029 | 185-193 | Citations [1]-[9] | [1]-[3] carry author/year strings but are "UNVERIFIED IN THIS AUDIT"; [4]-[9] have no bibliographic detail at all; there is no reference list | UNVERIFIED | yes |
| CL-030 | 197-199 | "Complete implementation verified" | Replaced by "current working-tree implementation … not a committed release" | SUPPORTED | yes |
| CL-031 | 200 | HEAD | `git rev-parse HEAD` = `d4db94d4…` ✓ | SUPPORTED | yes |
| CL-032 | 200 | Modified tracked files | Text says "current working tree has 22". `git diff --name-only` now = **25**. The sentence is time-stamped "at the Mission 12 baseline" but then says "current" | CONTRADICTED (stale) | yes |
| CL-033 | 201 | Software versions | Re-verified: Python 3.11.15, torch 2.13.0, ultralytics 8.4.121, ruff 0.16.3, pytest 9.1.1 | SUPPORTED | yes |
| CL-034 | 201 | macOS / Darwin | `sw_vers`: macOS 26.6.2 (25G83); `uname`: Darwin 25.6.0 arm64 ✓ | SUPPORTED (Mission 11B contradiction resolved) | yes |
| CL-035 | 202 | Safe-runner pass count | "1,802 tests passed across 92 files in the verified safe set". The runner refuses today; recorded passes sum to 1,801; 1,802 is that sum plus one new test. Not an executed result. "21 … tests" is a unit error (21 **files**) | CONTRADICTED as "verified"; UNVERIFIED as number | yes |
| CL-036 | 202-204 | No protected access | "no protected checkpoint was opened or hashed during this audit" cannot be accepted: Mission 12 ran protected-classified test files directly (see safe-runner audit §3.3) | UNVERIFIED | yes |

## 2. Mandatory scientific checks

| Check | Result |
|---|---|
| 27 events: 23 train / 3 no-train / 1 engine | consistent with 23/3/1 review-record files; legacy records, not approved GT |
| Single fixed crossing `crossing_A` | present in repository docs; stated as scope limitation, no cross-site claim ✓ |
| M4/M5/MTR definitions and status | definitions consistent with code; "implementation" = synthetic tests only ✓ |
| T1–T4; T2 deferred | T2 deferral stated as deferred; source is an unadopted protocol draft ✓ (qualified) |
| 1 µs snapping | ✓ |
| 5 Hz / 0.2 s | ✓ |
| Audio supporting only | ✓ |
| Back-stream, `B0_back` | marked provisional, DEC-B05 pending, not implemented in cache engine ✓ |
| R04 11-event exploratory | ✓ (config), execution not authorized ✓ |
| No cross-site generalization | ✓ in §3.1; undermined by CL-026 limitation 4 wording |
| No invented performance/safety/affordability/fatality figures | ✓ none found |
| No fabricated empirical results | ✓ none found |

## 3. Governance claims

RD-043 proposed ✓ · DEC-B05 pending ✓ · RD-045 "remains a researcher decision" ✓ · no invented reviewer appointment ✓ · protocol proposals not presented as adopted ✓ · no fabricated authorization or promotion status ✓ (line 203 lists exactly the artifacts that are absent; `data/governance/leg_exec_authorization.json` is a different record type and is not mentioned).

## 4. Citations

| Ref | Class |
|---|---|
| [1] Jocher et al. 2023 (Ultralytics YOLOv8) | Bibliographic details present, not independently verified |
| [2] Hershey et al. 2017 | Bibliographic details present, not independently verified |
| [3] Wilson 1927 | Bibliographic details present, not independently verified |
| [4] "Bangladesh Railway Information Book (2020)" | Unverified |
| [5]-[9] | Unverified (no details) |
| any claim leaning on a citation for a numeric/frequency fact | Unsupported (none remain after Mission 12 removals except CL-006 wording) |

## 5. Mission 12 correction accuracy

| Mission 12 statement | Accurate? |
|---|---|
| Removed unsupported affordability / collision / literature-frequency claims | Mostly — residual "often/frequently/severely" wording (CL-006) |
| RD-043, DEC-B05 marked proposed/pending | Yes |
| Native FPS removed | Yes |
| R04 "established calibration" corrected | Yes |
| "Shunting" → "Engine Movement" | Yes |
| Claim-matrix "Verified" relabeled | Yes, but receipt path is wrong |
| Citations marked unverified | Yes |
| Stale values corrected: 1,802 safe-runner tests, 22 modified files | **No** — 22 is already stale (25), 1,802 is not reproducible, "21 tests" mis-states files |
| macOS 26.6.2 / Darwin 25.6.0 | Yes |
| Checkpoint hashes `NOT_VERIFIED` | Yes as a status, but the "no checkpoint opened or hashed" sentence is unverified |

## 6. Findings

| ID | Sev | Finding |
|---|---|---|
| F13-16 | MEDIUM | Residual inaccuracies: modified-file count (22 vs 25); "1,802 verified"; "21 tests" (files); wrong receipt path (line 181); unsupported audio class list (line 99); overclaiming limitation 4 (line 167); unchecked 120.8 s; "no checkpoint hashed" unverifiable. |
| H-09 / R-H05 | HIGH→ carried as **PARTIALLY_FIXED** | Unsupported manuscript claims largely removed; the items above remain. |
| M-08 | MEDIUM | Bibliography absent; citations unverified (unchanged, researcher task). |
| L-03 | LOW | Uncited statistic removed — **FIXED_VERIFIED**. |

## 7. Disposition

The manuscript is correctly framed as a methodology/specification draft with pending results and no fabricated numbers. It is **not yet accurate enough** to be described as independently verified: fix the seven items in F13-16 and have the researcher complete authorship, bibliography and the AI-use statement.
