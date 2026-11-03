# Mission 14 — WP14.8 M-02, Promotion and Reviewer Regression Coverage (F13-12, H-01…H-05)

Every test named here is in a **safe-classified, synthetic-only** file and ran in the final safe-runner execution (PASSED, 2,198 tests, 0 blocked). Nothing was created in `data/governance/` or `data/ground_truth/`; every authorization-shaped artifact is a throw-away fixture in a temp directory. RD-043 and the other directional decisions are **not** treated as adopted.

## 1. Requirement → test matrix

`E` = `tests/unit/test_security_evaluation_input.py`, `G` = `tests/unit/test_security_governance_regressions.py`, `S` = existing safe-set file referenced by `G::test_referenced_safe_set_tests_still_exist` (fails if renamed/deleted).

| Required coverage | Test(s) | Status |
|---|---|---|
| Forged `_OfficialPermit` | `E::test_forged_permit_with_matching_digest_is_refused_with_zero_reads`; also in the synthetic sibling `test_phase12_official_replay_synthetic.py::test_a_forged_permit_cannot_unlock_the_runner_directly` | **new + restored to safe set** |
| Forged authorization context | `E::test_forged_authorization_context_is_refused_even_with_the_module_private_token` (object, correct private token, string) | new |
| Matching manifest digest | same permit test (permit digest = real manifest digest); `E::test_context_for_one_manifest_cannot_be_reused_for_another` | new |
| REAL evidence through `run()` | `E::test_public_run_and_run_safe_never_reach_the_producer`; `test_phase12_evaluation_runner.py::test_real_evidence_execution_is_refused_even_in_memory` (S) | new + existing |
| REAL evidence through `run_from_manifest()` | `E::test_explicit_real_request_is_refused_with_zero_reads` | new |
| Unauthorized REAL manifest pre-read | `E::test_real_manifest_with_the_classification_argument_omitted_reads_no_source`, `…caller_declaring_synthetic_cannot_relabel…`, `…private_core_demands_the_context_before_any_source_is_read`, `…manifests_in_the_repository_evidence_trees_are_not_read_by_the_public_api` | new |
| Unauthorized hashing | `E::test_loader_refuses_a_media_source_before_opening_or_hashing_it`; media suite `test_hashing_is_refused_before_the_file_is_opened` | new |
| No producer invocation on rejection | `Tripwires.assert_untouched` (producer patched to raise) in every refusal test | new |
| No cache access on rejection | same (`CacheOnlyReplayEngine.__init__` patched to raise) | new |
| No media read on rejection | same (engaged media-guard checks must be empty) | new |
| Invalid promotion receipt | `G::test_forged_receipt_with_a_wrong_self_hash_is_refused`, `…invalid_receipt_shapes_are_refused` (11 shapes), `…missing_receipt_is_its_own_code` | new |
| Wrong review-record hash | `G::test_wrong_review_record_hash_names_the_changed_record` | new |
| Protocol / input binding | `G::test_wrong_bound_input_is_stale`; EVAL-AUTH bindings: `G::test_eval_auth_bindings_cover_the_documented_artifacts` | new |
| Duplicate reviewers | `S`: `test_mission4b_review_operations.py::test_allowlist_rejects_duplicate_revoked_blocklisted_and_missing`, `test_second_review_requires_distinct_reviewer_…`; `test_mission10_second_review.py::test_same_reviewer_cannot_second_review_their_own_record`, `test_case_variant_of_same_identity_is_not_independent`; new `G::test_allowlist_rejects_duplicates_blanks_and_empty_lists` | existing + new |
| Non-allowlisted reviewer | `S`: `test_mission10_second_review.py::test_second_reviewer_must_be_allowlisted`, `test_phase11_12_readiness_gate.py::test_unallowlisted_reviewer_blocks_readiness` | existing |
| Missing second reviewer (where implemented) | `S`: `test_triggered_record_without_a_second_review_is_a_blocker`, `…second_review_requires_distinct_reviewer_and_missing_second_review_blocks` | existing |
| Timestamp / expiry controls | receipt: `G::…invalid_receipt_shapes…` (future-dated, unparsable); media authorization expiry/not-yet-valid in `test_media_authorization.py` (parametrized invalid-record cases); descriptive authorization in `test_descriptive_exec_gate.py` | existing + new |
| Scope mismatch | `S`: `test_valid_record_authorizes_exactly_its_scope`, `test_per_event_scope_with_undeterminable_event_is_denied`, `test_authorization_not_covering_the_operation_still_blocks_the_opener`, `test_engine_enforces_the_authorized_condition_scope` | existing |
| Revocation (where the schema supports it) | AUTH-MEDIA-ACCESS and AUTH-DESCRIPTIVE-EVAL-EXEC: `revoked` must be `false` (existing record-validation tests); schema presence asserted by `G::test_media_and_descriptive_authorizations_do_carry_expiry_and_revocation` | existing + new |
| **EVAL-AUTH expiry/revocation** | **Schema has none. `G::test_eval_auth_schema_has_no_expiry_or_revocation_fields` preserves Mission 13's correction of Mission 12's claim. Nothing was invented.** | documented |
| Receipt expiry/revocation | `G::test_receipt_has_no_age_limit_or_revocation_today_documented_gap` pins current behavior and says so; change it only when governance decides | documented gap (F13-10) |
| Tamper-evident-only trust model | `G::test_receipt_is_tamper_evident_only_a_hand_computed_one_passes` | documented |

## 2. Implemented behavior vs formally adopted governance

| Item | Implemented as engineering behavior | Formally adopted |
|---|---|---|
| Second-review triggers (RD-043 / `GOV-REVIEW-SECOND-REVIEW-TRIGGERS`) | yes (fail-closed code) | **no — proposed** |
| Disagreement handling (RD-045) | no tolerance, no clearing | **no — pending** |
| DEC-B05 back-stream condition names | not implemented in the cache engine | **no — pending** |
| EVAL-AUTH expiry/revocation | does not exist | n/a |
| Reviewer appointment | allowlist file mechanism only | researcher-controlled |

## 3. Do the new tests detect the original defects? (mutation check)

The new suites were run against a scratch copy of `src/` with the Mission 14 pre-edit backups swapped back in (the repository was not touched):

| Suite | Against pre-Mission-14 code |
|---|---|
| `test_security_media_boundary` | collection error (imports the new `classify_resource` API) |
| `test_security_evaluation_input` | collection error (imports new behavior/codes) |
| `test_security_scratch_scripts` | collection error (imports the new command guard) |
| `test_security_path_identity` | **5 failed**, 47 passed |
| `test_security_dashboard` | **22 failed**, 28 passed |
| `test_security_governance_regressions` | 25 passed (that code did not change; the tests pin current behavior) |

Collection errors prove only that the new API is absent. **Behavior-level before/after evidence** is the Mission 13 probe set re-run against the same two code states (saved as `mission14_evidence/probe_before_mission14.txt` and `probe_after_mission14.txt`): the 6b/6c source-read lists go from 6 reads to none; the symlink-alias, nine unlisted-suffix, `.mov.bak`, `.bin` and extensionless cases go from ALLOWED to DENIED; the case-variant output directories go from ACCEPTED to REFUSED; the dashboard traversals go from `200` with secret bytes to `404`; the loader's `I1` case no longer reaches a read. (The "before" run's case-variant lines for the descriptive gate are not meaningful because the scratch copy's `REAL_REPO_ROOT` is the scratch directory — the Mission 13 report holds the original observation.)

## 4. Honest limits of this coverage

* H-01…H-05 (reviewer / trigger / allowlist / identity / timestamp controls) now have a stable synthetic regression path, but **Mission 14 did not adversarially re-verify them**; independent verification belongs to Mission 15.
* The protected originals (`test_phase12_governance.py`, `test_phase12_official_replay.py`) still hold the real-repository tests; those assertions (real repository stays read-only and blocked) are exercised nowhere in the safe set by design.
* The unsigned `official_authorization_verified` flag, context binding and the checkpoint-hashing policy (F13-15, F13-09) are unchanged.
