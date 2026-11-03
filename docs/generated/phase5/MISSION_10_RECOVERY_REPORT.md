# Mission 10 — Phase 5 Recovery Report

> Written for: the researcher (decision-maker) and the next independent auditor. Author: Claude Sonnet 5.5
> acting as recovery agent. This report asserts only what was run in this session; every claim names its
> evidence. It is **not** a completion certificate.

## 1. Disposition

**`PHASE_5_ENGINEERING_RECOVERED_PENDING_REAUDIT_AND_GOVERNANCE`**

* Engineering defects found by the two failed audits are fixed in code with tests that fail when the fix is
  reverted; the independent re-audit has not happened.
* Phase 5 **cannot** be `PHASE_5_COMPLETE`: no AUTH-MEDIA-ACCESS, AUTH-DESCRIPTIVE-EVAL-EXEC, AUTH-PROMOTE-EXEC,
  EVAL-AUTH, Stage-2.1 approval, second reviewer, or promotion receipt exists, and Mission 10 created none.
  `data/governance/` still contains only `leg_exec_authorization.json`.
* Nothing in the repository is committed for the new/changed `annotation/`, `evaluation/`, `safety/` code
  (those packages were never tracked); see register N-06.

## 2. What was implemented

| WP | Result | Key artifacts |
|---|---|---|
| 10.1 canonical promotion integrity | One receipt authority (`readiness_cli.build_promotion_receipt`, verified by `governance.verify_promotion_receipt`). `PromotionReceiptV5`, `generate_promotion_receipt`, `AdjudicationOutcome`, `adjudicate_dual_reviews`, the invented triggers and the dict-style allowlist were **deleted**. The gate reads the actual review files; the Phase 12 execution gate (consumer) repeats the second-review check itself; a forged, self-consistent receipt cannot hide a missing second review. | `annotation/second_review.py`, `evaluation_readiness_gate.py` (cond. 7), `execution_gate.py`, `ground_truth_loader.py`, `phase5_review_tooling.py` |
| 10.2 media authorization | `safety/media_guard.py`: guard inside the lowest-level openers (hash, probe, ffmpeg, cv2, WAV, generic file hashers), direct/CLI/module paths all meet it; `AUTH-MEDIA-ACCESS` v2 contract (id, class, signer on allowlist, status, tz-aware issue/expiry, strict `revoked`, operations, datasets, cohort-qualified events, media types, purpose, path-prefix restrictions, protocol-document binding re-hashed live, `record_sha256`). Separate `AUTH-DESCRIPTIVE-EVAL-EXEC` gate (`descriptive_exec_gate.py`) binds promotion receipt, cache manifest, protocol profile, metric scope and frozen config; enforced in `CacheOnlyReplayEngine` (execute and load). Verified live: `extract_sync_review_frames.py` and `run_phase5_full_inference.py` refuse and touch nothing. | `safety/media_guard.py`, `descriptive_exec_gate.py`, 13 scripts + ≈20 src sites |
| 10.3 test classification + safe runner | All **113** test files classified individually by running each alone under a blocking guard; runner rewritten. | `MISSION_10_TEST_CLASSIFICATION_AND_SAFE_RUNNER.md` |
| 10.4 RD-043 | Exact six-trigger set (one disclosed as not mechanically evaluable); no tolerance; RD-046 floor not a trigger; agreement never replaces adjudication; disagreement stays unresolved; missing independent reviewer = blocker. | `second_review.py`, 33 tests |
| 10.5 back stream | Investigated; **no code invented**. `B0_back`/`B0_back_stateless`/`B2_back` are provisional names (DEC-B05 PENDING); the engine refuses them. | rebuild readiness §3 |
| 10.6 docs | 8 Phase 5 documents bannered and corrected; hash tables replaced by a generated manifest; the two Sonnet reports untouched (hash-verified). | reconciliation doc |
| 10.7 M4/M5 | Independent integer-µs oracle vs `classify_m4` over >3,000 cases: 0 mismatches. | `test_mission10_m4_m5_differential.py` |
| 10.8 conditions | `MISSION_10_CONDITION_MAPPING.md` |
| 10.9 readiness | `MISSION_10_REBUILD_READINESS.md` |

## 3. Verification actually run (this session)

| Check | Result |
|---|---|
| Safe runner (`scripts/run_synthetic_tests.py`) | **1,802 passed**, 0 failed, 92 files, guard: 2,424 events, **0 blocked**, 0 violations |
| Full suite under the Mission 6 read-blocking harness | 2,163 passed / 65 failed; the 65 are the **identical set** as the Mission 6 baseline (diff empty) — all are tests that read real checkpoints/processed data/media, which the harness blocks |
| Collected tests | 2,228 |
| Mutation probes | 17 mutants of the new enforcement code, 17 killed (2 initially survived; tests added) |
| Ruff | all 19 new/rewritten files: `All checks passed`, format clean. Edited pre-existing files: finding counts equal to or below the pre-edit counts. Repo-wide Ruff **not** clean (≈1,750 pre-existing) |
| Protected inputs | protocol, ground-truth protocol, policy, frozen config, allowlist, leg-exec authorization, design/paper docs and both Sonnet reports: SHA-256 prefixes identical to the Mission 10 baseline |
| Git | HEAD unchanged (`d4db94d`), nothing staged, no git write command run |

## 4. Honest limits

1. The guards are **Python-level**. A process can still read bytes through `cp`/`cat`, hard links, or a native
   library this repository does not wrap. The static opener scan is a tripwire for *new* openers, not proof.
2. Records are unsigned, tamper-evident researcher statements; this repository has no signature infrastructure.
3. FRONT_BACK_CONFLICT (RD-043 trigger 4) cannot be evaluated from a Stage-2.1 record (no structured field); a
   reviewer must set `NEEDS_SECOND_REVIEW`. RD-043 itself is a *proposal* (policy id PENDING); enforcing it is
   stricter, not an adopted rule.
4. With one allowlisted reviewer, any record that fires a trigger (every engine event with an interpreted
   T3/T4, any UNCERTAIN boundary, any boundary corrected from the AI candidate) is blocked until a second
   reviewer is allowlisted and reviews. That is the intended behaviour, and it is a real project blocker.
5. The legacy `ExperimentRunner` B0–B7 and the cache engine's B0–B2 share names with different meanings.
6. `M-02` (forgeable in-process `_OfficialPermit`), `M-06`, `M-08`, `L-03`, manuscript claims (H-09/R-H05) remain.
7. The classification reflects behaviour at generation time; a test that fails on its first blocked read can hide
   later reads. The manifest is hash-bound, and the runner re-verifies the guard log on every run.
8. 21 test files (14 checkpoint, 3 processed-data, 4 raw-media) are excluded from safe runs and were *not*
   executed against real data.

## 5. Constraints honoured

No raw media was opened, decoded, hashed, probed or run through inference (live refusals observed; the guard
blocks before any open). No human-review artifact, approval, authorization or receipt was written. No git
write command. Original Sonnet reports unmodified. Changed files are listed in
`MISSION_10_ARTIFACT_MANIFEST.json`.

Three disclosed process notes: (a) tracked files `audio/preprocessor.py`, `demo/video_demo.py`,
`data/validator.py` received one-line guard calls; (b) `reports/synthetic_test_report.json` is Gemini's stale
telemetry and was left in place; (c) the readiness-gate edit and the CLI edit were made before backups began
(their pre-edit state is not preserved; the diff is described in `changes.txt`).
