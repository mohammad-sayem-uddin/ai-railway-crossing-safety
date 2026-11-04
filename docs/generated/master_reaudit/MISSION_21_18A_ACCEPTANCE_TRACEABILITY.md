# Mission21 — Current 18A synthetic acceptance traceability

This records current constructed engineering acceptance for 17I-CB-V1 and the
14 adopted A selections. Historical 18A blocker reports and original contracts
remain unchanged. No scientific protocol promotion, live permission, real replay
or physical safety acceptance follows. Test names below are executed cases in
`tests/synthetic_mission18a`; legacy helper evidence ran separately in the
unchanged 238-case suite.

| Contract | Executed evidence | Current result and limit |
|---|---|---|
| CB01 | `test_actual_controller_a_compatibility_and_different_motion`, `test_engine_reset_once_per_production_run` | Explicit existing-runner B delegation; actual current engine; retained decision/command correspondence |
| CB02 | `test_invalid_exact_clocks`, `test_float_boundary_mismatch`, `test_original_exact_clock_normalized_once_per_supplied_row` | Original lexical/tick snapshot retained; one normalization per input in each selected mode; no real clock-accuracy claim |
| CB03 | `test_new_command_never_applies_retroactively`, `test_causal_oracle_and_three_estimators` | Old command advances before new boundary issue; independent exact numerical oracle |
| CB04 | `test_native_rejections_and_original_indices`, `test_horizon_empty_single_partial_extended`, `test_offline_prevalidation_failure_does_not_claim_reordered_execution` | Explicit ARRIVAL/OFFLINE, stable original correspondence, failure prefixes and cutoffs |
| CB05 | `test_causal_oracle_and_three_estimators`, `test_exact_threshold_and_noop_subdivision`, `test_asymmetric_motion_oracle` | Separate event/continuous/fixed estimators; exact 45-degree threshold; no universal A/B offset |
| CB06 | `test_invalid_configuration`, `test_input_nested_mutation_and_effective_settings_reset`, `test_invalid_effective_controller_settings` | Effective actuator/controller settings retained; nested snapshot owned; invalid settings deny |
| CB07 | `test_actual_controller_a_compatibility_and_different_motion`, `test_declared_maximum_workloads_and_clock_boundaries`; original helper watchdog tests | Selected integrated NONE verified explicitly, with no timeout or timer issue. Other helper profiles remain component evidence only; no integrated policy adoption |
| CB08 | `test_full_detached_result_substitutions`, `test_swapped_trajectory_and_request_fail_verification` | Typed B result; canonical complete envelope; logical/applied/physical meanings separate |
| CB09 | Same substitution cases plus fresh reset and repeated deterministic replay | Full deterministic candidate replay against independently retained request/code label; unkeyed consistency, not execution authentication |
| CB10 | `test_declared_maximum_workloads_and_clock_boundaries`; original no-slice/merge reporting tests | Executed 8,192 supplied frames and emitted intervals; 32,768 fixed report intervals; exact one-hour horizon. Finite bound evidence, not adversarial resource resistance |
| CB11 | `test_actual_controller_a_compatibility_and_different_motion` | A before/after results identical; command parity and intentionally different physical timing demonstrated |
| CB12 | Entire 65-case integration/isolation suite plus separate original 238-case suite | Current selected synthetic design accepted within stated scope; no protected-resource or production acceptance |

| 18A criterion | Covered contract/cases | Disposition |
|---|---|---|
| A01 | CB01/03/11 actual controller, numerical oracle, A compatibility | PASS for constructed integration |
| A02 | CB02/04 exact clocks, float mismatch, duplicates/order and prevalidation | PASS for selected exact-envelope migration |
| A03 | CB04 empty/single/interior/extended cutoff and incomplete prefix cases | PASS; diagnostic prefixes remain incomplete |
| A04 | CB05/06 thresholds, asymmetric rates, clipping, estimators/settings | PASS; no physical-state tolerance translation into A |
| A05 | CB07 explicit NONE baseline | PASS for selected NONE; SCHEDULED/DETECT are not integrated options |
| A06 | CB08/09 full envelope, substitutions, snapshots and reset | PASS under independently retained cooperative expectations |
| A07 | CB10/12 scale, reporting, repeated runs, oracle and IO tripwires | PASS within selected bounded fixture envelope |

The maximum report-grid case holds the exact modeled angle at 45 degrees over
3,600 seconds and independently expects 3,600 seconds for every estimator. It
also checks a larger report grid is refused. This is synthetic model blockage,
not train occupancy or an empirical protection result.

IO tripwires and forbidden-import checks cover the selected test process. They
do not provide an OS sandbox or establish retrospective non-access. The current
A runner's old instrumentation typing and one lint line remain outside the
adopted B-entrypoint-only edit scope. Current exact cases/source hashes and final
regression counts are in MISSION_21_FINAL_ENGINEERING_VALIDATION.json.
