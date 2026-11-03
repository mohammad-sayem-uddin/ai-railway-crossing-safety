# Mission 13 — WP13.4 Promotion and Descriptive-Evaluation Gate Audit

**Date:** 2026-11-02. Evidence: static reading of `evaluation/governance.py`, `evaluation/execution_gate.py`, `evaluation/descriptive_exec_gate.py`, `evaluation/cache_only_engine.py`, `annotation/promotion_gate.py`, `annotation/receipt.py`; synthetic probes `mission13_probes/probe_receipt.py`, `probe_case.py`; seven current, safe-classified gate test files run under the read-blocking guard (262 passed, 0 blocked — see safe-runner audit §5).
**Nothing was created in `data/governance/`, `data/ground_truth/` or anywhere an authorization, receipt or approval could live.** RD-043 and all RD-001–RD-055 decisions were treated as directional, not adopted.

## 1. Implemented conservative behavior vs formally approved governance

| Item | Implemented in code | Formally adopted? |
|---|---|---|
| Second-review triggers (RD-043 / `GOV-REVIEW-SECOND-REVIEW-TRIGGERS`) | yes, as fail-closed engineering behavior (`second_review.py`) | **No — proposed** |
| Disagreement procedure (RD-045) | no tolerance, no clearing without an adopted format | **No — pending** |
| Back-stream condition names (DEC-B05) | not implemented in the cache engine | **No — pending** |
| Reviewer appointment | allowlist file exists; no appointment is asserted | **Researcher-controlled; not established here** |
| Promotion receipt / EVAL-AUTH / AUTH-MEDIA-ACCESS / AUTH-DESCRIPTIVE-EVAL-EXEC | schemas and verifiers exist | **None exist in the repository** (`data/governance/` holds only the earlier `leg_exec_authorization.json`) |

## 2. Promotion receipt (`governance.verify_promotion_receipt`, `governance.py:317-385`; producer `annotation/readiness_cli.py`; body hash `annotation/receipt.py:48-51`)

Synthetic receipts in a temporary root, `probe_receipt.py`:

| Case | Expected | Actual |
|---|---|---|
| R0 receipt computed by hand with the correct live hashes (CLI never run) | (documented) tamper-evident only | **ACCEPTED** |
| R1 invalid `receipt_sha256` | reject | rejected |
| R2 wrong review-record hash | reject | rejected, names the record |
| R3 wrong bound input (allowlist/inventory/proposal digest) | reject | rejected |
| R4 wrong `produced_by` | reject | rejected |
| R5 verdict not READY / blockers > 0 | reject | rejected |
| R6 `produced_at_utc` in the future | reject | rejected |
| R7 receipt dated five years ago | reject if "stale by age" | **accepted — there is no expiry** |
| R8 extra `"revoked": true` | reject if revocation existed | **accepted — unknown fields are ignored, there is no revocation mechanism** |

So: tampering, mis-binding and drift are caught; a motivated writer with the hash recipe can produce a passing receipt (the file says as much: "tamper-evident, not tamper-proof"). "Stale" is detected only by input drift; "revoked" cannot be expressed. Mission 11B **C-01** is **FIXED_VERIFIED within the documented trust model** (canonical schema used consistently, forged-by-edit rejected); the missing expiry/revocation is recorded as **F13-10**.

Items 4–8 of the brief (protocol binding, second reviewer, non-allowlisted reviewer, duplicate reviewers):

- The *receipt* binds the allowlist, annotation inventory, active proposals and each review-record hash (R2/R3). Protocol-profile binding lives in **EVAL-AUTH** (`protocol_profile_sha256`, `event_split_decision_sha256`, `r04_scope_decision_sha256`, `frozen_config_sha256`, `decision_policy_sha256`, `input_manifest_sha256`, `stage21_promotion_receipt_sha256`), not in the receipt.
- Allowlist loading refuses empty, duplicate, malformed or denylist-inconsistent files (`promotion_gate.py:66-137`); a reviewer outside it is refused (`:360-370`); a second review by the same reviewer as the first is refused (`:500-517`). I confirmed these by reading the code and by the current test files passing (`test_mission10_second_review` 33, `test_phase11_2_stage21_promotion_gate` 33, `test_phase5_review_tooling` 36). I did **not** write independent adversarial probes for duplicate-reviewer or timestamp paths, so these are recorded as code-reviewed rather than independently attacked.

## 3. Descriptive-evaluation authorization

`descriptive_exec_gate.verify_descriptive_authorization` requires a record with `expires_at_utc`, `revoked: false`, allowlisted signer, scope, and live bindings. It is enforced at **two** engine levels in `cache_only_engine.py`: `_load_cache_stream` (`:654-660`, before the path is resolved or any byte read) and `execute_replay` (`:747-756`, first statement). Order is correct: authorization precedes cache access and replay.

### 3.1 Defect: the gate decides "is this the real repository" by string comparison (F13-04)

`require_descriptive_authorization_for_engine` (`descriptive_exec_gate.py:270-278`):

```python
if repo_root.resolve() != media_guard.REAL_REPO_ROOT:
    return  # a synthetic tree is not real data
```

On this machine the repository sits on a case-insensitive APFS volume. `Path.resolve()` does not canonicalize case, so a path that differs only by case names the *same* directory but compares unequal. `probe_case.py`:

| Call | Result |
|---|---|
| `…/Train_automation` | `DescriptiveExecutionNotAuthorized` |
| `…/train_automation` (same directory) | **returns silently — gate skipped** |

`CacheOnlyReplayEngine(repo_root=<case-variant>)` then resolves cache paths relative to that root (`_validate_cache_path` compares against `repo_root.resolve()`, i.e. the same case-variant string), so cache reads proceed. I did not construct an engine because that would touch protected processed data; the skip itself is demonstrated.

Same root cause, other sites:
- `evaluation_runner.py:327-360` (`_checked_output_dir`) accepts `…/data/Ground_Truth/<new>` and `…/train_automation/data/ground_truth/<new>` as outputs although `data/ground_truth` is a protected output tree (`probe_outdir.py`; the function writes nothing).
- `media_guard._inside`/`is_synthetic_location` compare strings; for *existing* media a case-variant path still falls into `verify_authorization_record`, where `_dataset_of` fails and the call is denied, so the media guard fails closed by accident rather than design.
- `experiment_engine.py:207-215` and `stage21_timing_pilot.py:1365, 1491` use the same pattern.

## 4. Requested checks, consolidated

| # | Check | Result |
|---|---|---|
| 1 | Canonical receipt schema used consistently | yes (`PROMOTION_RECEIPT_SCHEMA`, `produced_by` constant, shared `receipt_body_sha256`) |
| 2 | Forged receipt rejected | only if mis-hashed or mis-bound (R0 vs R1–R6) |
| 3 | Invalid receipt hash | rejected |
| 4 | Invalid review-record hash | rejected |
| 5 | Invalid protocol binding | rejected at EVAL-AUTH level; the receipt has no protocol field |
| 6 | Missing second reviewer | enforced where a second review is required (code-reviewed; trigger set is a proposal) |
| 7 | Non-allowlisted reviewer | rejected (code-reviewed) |
| 8 | Duplicate reviewers | same-reviewer second review rejected (code-reviewed) |
| 9 | Stale or revoked receipt | stale-by-drift rejected; age/revocation **not implemented** |
| 10-11 | Descriptive authorization before cache access / replay | yes, both entry points |
| 12 | Missing / expired / wrong-scope / malformed / wrong-binding authorization | rejected for canonical roots (covered by `test_descriptive_exec_gate` 41 tests, run under guard); **bypassed by a case-variant root** |
| 13 | Temporary synthetic roots supported | yes (`repo_root != REAL` returns) — which is exactly what the defect exploits |

## 5. Official-readiness gate and checkpoints (F13-09)

`assess_official_phase12_readiness` always executes the frozen-configuration block (`execution_gate.py:866-890`), which calls `verify_checkpoint_integrity` and therefore hashes the vision, Audio-V3 and prohibited Audio-V2 checkpoints **whether or not EVAL-AUTH exists**. There is no authorization control for checkpoint reads (the opener tripwire allowlists `compute_file_sha256` as "weights, not media"). Mission 12's media-reader table calls checkpoints a "SEPARATE CHECKPOINT CONTROL"; none was found.

## 6. Findings

| ID | Sev | Finding |
|---|---|---|
| F13-04 | HIGH | Case-insensitive path identity defeats the descriptive gate, protected-output check and related guards. |
| F13-10 | MEDIUM | No expiry/revocation for EVAL-AUTH or promotion receipt; receipt is hand-computable. |
| F13-09 | MEDIUM | Readiness gate hashes protected checkpoints before and independent of authorization; no checkpoint-access control. |

## 7. Disposition

Gates behave as implemented for canonical paths and malformed/missing/drifted artifacts. One high-severity bypass (F13-04) and two design gaps remain. No gate result here is, or implies, formal approval or execution authorization.
