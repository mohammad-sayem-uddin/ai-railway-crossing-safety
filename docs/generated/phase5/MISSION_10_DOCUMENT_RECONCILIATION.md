# Mission 10 — Documentation and Provenance Reconciliation (WP10.6)

> Written for: the researcher and the next auditor. Pre-edit copies of every file below are in
> `/private/tmp/claude-501/m10/backup/phase5_docs/`. `SONNET_PHASE5_INDEPENDENT_AUDIT_REPORT.md` and
> `SONNET_PHASE5_REMEDIATION_REAUDIT_REPORT.md` were **not** modified (SHA-256 prefixes `965bfeab93827201`,
> `371727d92cdbce69` equal the baseline).

## 1. Method
All 64-hex strings in each Phase 5 document were recomputed against the repository files (1,315 non-media files
indexed). Claims about behaviour were checked against the code or the tests that exist now.

## 2. Result per document
| Document | Hash check | Action |
|---|---|---|
| PHASE_5_COMPLETION_REPORT | 7 of 7 file hashes unverifiable (the files were later rewritten) | banner; hash cells removed; disposition and invented-trigger lines marked superseded |
| PHASE_5_REMEDIATION_REPORT | 6 of 6 match | banner (its "Remaining Risk: None" lines are withdrawn) |
| WP_5_0_EXECUTION_READINESS_AUDIT | 3 of 3 match | banner (stale governance paths are listed in the re-audit; not rewritten) |
| REPRODUCIBILITY_PACKAGE_SPECIFICATION | 6 of 12 unverifiable | banner; hash cells removed; "97 synthetic files" corrected to 92 |
| PAPER_DRAFT_PHASE5_REVISION | 1 of 1 matches (`configs/decision_policy_v1.yaml` = `c87c1432f473f84d…`) | banner; `B0_back`/`B2_back` marked provisional; "shunting" removed |
| RELEASE_READINESS_ASSESSMENT | no hashes | banner |
| BACK_STREAM_REPLAY_GAP_ASSESSMENT | none | banner; **RD-054 mis-attribution corrected** (RD-054 is authorship/AI disclosure) |
| SONNET_INDEPENDENT_AUDIT_PACKAGE | 7 of 8 unverifiable | banner; hash cells removed; "97/1,902" corrected |

## 3. Not reconciled (open)
* Manuscript claims beyond the ones fixed (H-09/R-H05): a line-by-line claim audit of the paper draft was not done.
* References/authors/AI-disclosure block (M-08), uncited statistic (L-03), reproducibility completeness (M-06).
* `reports/synthetic_test_report.json` is Gemini's stale telemetry (says 97 files); it was left in place.
* `WP_5_0` still cites some governance paths from Gemini's numbering.

## 4. Facts established during reconciliation (verified in this session)
* Real artifact names: `data/governance/eval_authorization.json`, `data/governance/stage21_promotion_receipt.json`.
* Tick = 0.2 s (`timing.tick_s`); policy raw SHA-256 `c87c1432f473f84d…`; real ids `no_train_events/event_001–003`,
  `engine_events/event_001`.
* Hashes in documents go stale on every edit; the generated `MISSION_10_ARTIFACT_MANIFEST.json`
  (`python scripts/mission10_artifact_manifest.py`) is the single source and says it hashes a working tree, not a commit.
