# Mission 14 — WP14.9 Reproducibility and Documentation Corrections

**Policy:** no Mission 10, 11, 11B, 12 or 13 report and no manuscript text was edited. Corrections are issued here as notices. Each is limited to what Mission 14 verified with new evidence.

## 1. Correction notices

| # | Statement in an earlier document | Correction (evidence) |
|---|---|---|
| C1 | "1,802 tests passed across 92 files in the verified safe set" (Mission 12 reports; manuscript §11) | Not an executed result. The old manifest recorded **1,801 passes + 1 recorded failure = 1,802 recorded tests** over 92 files. The runner refused at that time. The first executed figure is Mission 14's: **2,198 passed, 0 failed, 100 files, 0 blocked** (§3). *Evidence:* old manifest backup; archived runner report |
| C2 | "21 checkpoint/processed-data/raw-media tests remain excluded" | They are **21 files** (before and after Mission 14: 15 checkpoint, 2 processed-data, 4 raw-media), holding 426 recorded tests at classification time |
| C3 | Mission 13 summary: "recorded pass counts for 92 safe files sum to 1,801" | Correct as *passes*; it omitted the 1 recorded failure (C1) |
| C4 | "EVAL-AUTH expiry/revocation are rechecked" (Mission 12 M02 design note) | EVAL-AUTH has **no** expiry, revocation or status field (`governance._EVAL_AUTH_KEYS`); Mission 13's correction stands and is asserted by `test_eval_auth_schema_has_no_expiry_or_revocation_fields`. AUTH-MEDIA-ACCESS and AUTH-DESCRIPTIVE-EVAL-EXEC do have them. **No field was added.** |
| C5 | "No protected checkpoint was opened or hashed" (Mission 12; manuscript §11) | **Not established** — see `MISSION_14_MISSION12_EXECUTION_PROVENANCE.md` §6 for the notice text |
| C6 | "22 modified tracked files" | Correct at 10:11 on 2026-11-02 (Mission 12's own snapshot); **25** after Mission 12 edited three previously clean tracked files. Mission 14 did not change the tracked-modified set (25 before and after) |
| C7 | Mission 12 media-reader table: checkpoints are a "SEPARATE CHECKPOINT CONTROL" | No checkpoint access control exists; hashing is allowlisted in the opener tripwire as "weights, not media" (F13-09, open) |
| C8 | Mission 12 media-reader table, `generate_qualitative_figures.py` fully guarded | One `predict(source=path)` site lacked an adjacent guard (F13-14, now fixed) |
| C9 | Mission 12: symlink / environment behavior "remain governed by the existing guard" | True only for media-suffixed link names; alias bypass and suffix gaps are fixed in Mission 14 |
| C10 | "ruff clean" (Mission 12, for changed files) | Mission 14 measured only what it touched: `ruff check` passes on the new test/support/tool files and on `safety/`, `evaluation_runner.py`, `input_contracts.py`, `descriptive_exec_gate.py`, `cache_only_engine.py`, `demo/server.py`. Pre-existing findings remain in files Mission 14 only touched lightly (import-order `I001` in `stage21_timing_pilot.py` and `experiment_engine.py`; line-length findings in `experiments/layer_b_processor.py`, `UP022`/`I001` elsewhere). `ruff format` was run on Mission 14's own new files only. **No repository-wide lint or format cleanliness is claimed.** |

## 2. Updated media-reader inventory and security architecture

* The reader inventory is §5 of `MISSION_14_MEDIA_BOUNDARY_DESIGN.md` (supersedes the Mission 12 and Mission 13 matrices where it differs).
* **Security architecture after Mission 14 (summary):**
  1. *Path identity* (`safety/path_identity.py`): canonicalise, compare by filesystem identity, fail closed.
  2. *Resource classification* (`media_guard.classify_resource`): by location first, name second; synthetic only by real location in OS temp.
  3. *Operation authorization* (`media_guard.verify_authorization_record`): on-disk AUTH-MEDIA-ACCESS, read every call, signer allowlist, expiry, revocation, operation / dataset / event / media-type / path-prefix scope, protocol-document binding. **None exists in the repository.**
  4. *Operation boundary* call sites: image / video / audio decode, hashing, ffmpeg (command guard), model `predict(source=path)`, evaluation loader, dashboard routes, scratch scripts.
  5. *Official evaluation*: `run_official` only; private verified context; REAL refused on every public path before any source read.
  6. *Descriptive evaluation*: AUTH-DESCRIPTIVE-EVAL-EXEC at the cache-engine boundary; gate applies to the real checkout in any spelling.
  7. *Test safety*: read-blocking plugin + classification manifest + safe runner (fail-closed).
* **Trust boundary (unchanged):** all of the above is Python-level. It is **not** cryptographic authorization (every authorization artifact is a recorded researcher statement, `signature: null`, tamper-evident only) and **not** an OS sandbox (native code, shell tools outside the wrappers, hard links, copies in temp, and swaps between check and use are outside it).

## 3. Test-count and execution record (for citation)

| Item | Value |
|---|---|
| Runner command | `scripts/run_synthetic_tests.py --report-path /tmp/mission14_synthetic_test_report.json` |
| Result | PASSED; 2,198 passed / 0 failed / 0 skipped; 100 files; guard events 2,601; **blocked 0**; metadata reads 2,597; violations none |
| Executed files | the 100 listed under `selected` in `mission14_evidence/mission14_synthetic_test_report.json` (78 SYNTHETIC_ONLY, 22 METADATA_ONLY) |
| Not run | 21 protected-access files; the full repository suite; `tests/unit/test_dashboard_server.py` (processed-data class) |
| New in the safe set | 10 files: `test_security_{media_boundary,evaluation_input,path_identity,dashboard,scratch_scripts,governance_regressions}.py`, `test_phase12_{governance,official_replay}_synthetic.py`, and the re-classified `test_media_authorization.py`, `test_media_opener_coverage.py` |
| Reproducibility | two consecutive executions identical |
| Mutation / before-after | `MISSION_14_SECURITY_REGRESSION_TESTS.md` §3 |

This is **not** a Phase 5 empirical result, not an evaluation of any model, and not evidence about real data.

## 4. Manuscript items from Mission 13 (F13-16) — left for the researcher

The manuscript is the researcher's document and was not edited. Verified replacement values, if the researcher chooses to apply them:

| Manuscript location | Current text | Verified value / action |
|---|---|---|
| §11 line 200 | "22 modified tracked files" | 25 (Mission 12 changed three more); give a timestamped snapshot instead of a number |
| §11 line 202 | "1,802 tests passed across 92 files in the verified safe set; 21 … tests excluded" | "2,198 tests passed across 100 files in the safe set (Mission 14 run); 21 test **files** excluded" — still *not* an empirical result |
| §11 line 204 | "no protected checkpoint was opened or hashed during this audit" | unverified; see C5 |
| line 181 | `data/ground_truth/stage21_promotion_receipt.json` | `data/governance/stage21_promotion_receipt.json` (`governance.PROMOTION_RECEIPT_RELATIVE`) |
| line 99 | audio classifier "detecting locomotive engine rumble, horn, and rail clatter" | repository classifier is binary (`train_horn` / `non_train_sound`) |
| line 167 | "valuable empirical evidence regarding multi-modal sensor fusion dynamics" | no empirical evidence is presented; reword |
| Mission 12 provenance table | "Frozen configuration SHA-256 `b8ef5da0…`" | that is the raw file hash; gates bind the **canonical** hash (`999a7970…`, `decision_policy_v1.yaml: reference_frozen_config_sha256`) |
| bibliography [1]–[9] | unverified | still unverified; no web research in this mission |

## 5. What is deliberately not claimed

No empirical-evaluation readiness; no adoption of RD-043, RD-045, DEC-B05 or any reviewer appointment; no authorization, receipt, review or approval exists or was created; no independent closure — Mission 15 must audit.
