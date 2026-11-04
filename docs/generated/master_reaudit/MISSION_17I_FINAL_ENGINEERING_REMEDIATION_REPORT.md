# Mission 17I — Final engineering remediation and contract freeze

Date: 2026-11-04, America/New_York. Repository `/Users/sayemuddin/Desktop/Train_automation`, main. Verified starting local HEAD, origin/main and live remote: **17cc6273544618f0b402a027b41eb527845d3252** (Mission 17H). That commit is present as HEAD/ancestor; tree initially clean including untracked files. No divergence or user work was overwritten. Mission scope: synthetic remediation, directly related tests/docs and exactly four new reports; no Mission 18 implementation.

**Mission status: COMPLETE within the authorized engineering scope.** H-N01 is corrected by implementation plus an explicitly dated historical-claim correction. H-N02's Ruff portion is closed: 68 initial findings, 68 remediated, zero remaining scoped diagnostics; no lint rule/config change or suppressions. **Mypy remains an unresolved environment/static-analysis gate**, accurately investigated rather than claimed passing. Integration remains conditional on researcher review and explicit authorization, retained expectations, chosen policy/workload and disposition of that type-analysis gate.

The same assistant authored 17G, 17H and 17I. This is technical remediation evidence, not an independent human audit, institutional approval or hardware safety certification. Labels below distinguish **Verified** source/execution evidence, **Required** future acceptance and **Recommendation**; researcher decisions remain pending. Prior complete 17H reports, 17G report/history, relevant 17F plans/audit and current synthetic code/tests were inspected directly. Production runner/gate source was read as text for compatibility, never imported or executed.

Companions: [Convention B contract](MISSION_17I_CONVENTION_B_INTEGRATION_CONTRACT.md), [grouped-CV contract](MISSION_17I_GROUPED_CV_INTEGRATION_CONTRACT.md), [Mission 18 acceptance/dependency register](MISSION_17I_MISSION18_ACCEPTANCE_AND_DEPENDENCY_REGISTER.md). Historical [17H verification](MISSION_17H_INDEPENDENT_VERIFICATION_REPORT.md) and [17H verdict](MISSION_17H_INTEGRATION_READINESS_VERDICT.md) remain unchanged.

## 1. H-N01 root cause, correction and actual bounds

**Decision: Approach A.** The fixed-grid helper's `zip(report,report[1:])` copied R endpoint references even though each adjacent pair is consumed once. That copy is unnecessary. `itertools.pairwise(report)` removes it, retains exact ordering/equality/endpoint math and needs no buffering/sort. Both public and RunConfiguration grid-order checks likewise use pairwise, removing their shifted tuple copies. No scientific threshold, controller behavior, watchdog policy or estimator changed.

The only affirmative historical O(1) reporting-space claim found was Mission 17G report line73. It now explicitly states that the old 17G implementation used O(R) auxiliary storage and that O(1) helper objects applies only after 17I. 17H statements correctly described their audited commit and are preserved as historical findings, not rewritten as retrospective passes. The old source docstring's O(1) visits per boundary was a time statement, now clarified with actual auxiliary scope. Searches covered relevant source/tests and Markdown reporting claims; unrelated constant-time claims were not edited.

| Quantity | Actual 17I bound / storage ownership |
|---|---|
| Fixed-grid helper time | O(S+R) arithmetic work: monotonically advancing interval index plus one endpoint evaluation per report interval; no sort. |
| Helper auxiliary memory | O(1) live iterator/scalar/rational objects excluding preexisting inputs; integer/rational bit lengths can grow, so not an absolute byte bound. A scalar Fraction result is its only output. |
| Input storage | Caller stores N events, producer stores S intervals and R+1 report boundaries; the helper does not duplicate these. |
| Whole-run output storage | O(N+S+R) objects across intervals, issue/rejection/accepted logs and event/report/config fields. |
| Whole-run temporaries | O(N+S+R): indexed event list, normalized fixed tuple, output tuple conversion, config dataclass/JSON/digest copies. pairwise does not make the entire run O(1) memory. |
| Sorting | ARRIVAL has no sort. OFFLINE stable input sort adds O(N log N) time and O(N) storage. Fixed-report merge does not sort. |
| Default grid | Reuse freshly calculated endpoint total; zero extra trajectory lookups. Computing event/continuous totals/grid still O(S). |
| Numeric cost | Fraction arithmetic and hash/serialization cost depend on input/operand sizes; operation-count bounds are not constant-bit or real-time guarantees. |

N=input events, S=emitted intervals (including timer/cutoff segments), R=report intervals. A fully streaming whole-run producer is not implemented; no need to redesign retained provenance/output merely to optimize one avoidable slice.

Required edge coverage maps to existing and added tests: empty/singleton and missing timestamps; disjoint/partly overlapping/unmatched report horizons reject; duplicate/older arrivals leave accepted order unchanged; duplicate/nonincreasing report keys reject; interior report keys without matching sensor keys are valid; missing interval records cause private out-of-trajectory rejection; repeated runs reuse fresh default totals; large synthetic grids and deterministic output remain covered. Arbitrary gapped/overlapping PRIVATE interval geometry remains a documented precondition violation, not a newly supported input format. Public producer intervals are contiguous; future adapters must not expose the helper as a general interval joiner.

Memory observation, inputs/interval list/rates allocated before tracing, one warm-up call then helper-only tracemalloc:

| R | Peak traced bytes |
|---|---|
| 32 | 1152 |
| 128 | 624 |
| 512 | 656 |
| 2048 | 656 |
| 8192 | 656 |

These interpreter-specific finite measurements show no R-sized tuple growth; early allocator/lazy effects explain the first larger value. A separate cold measurement observed 1775,784,816,816,816 bytes. Source reasoning and `test_17i_report_traversal_never_copies_or_indexes_report_grid` supply the structural evidence, rather than a fragile byte threshold test. Historical17H 1192→66504 bytes applied to the old helper. No claimed universal byte ceiling.

Source/test references: `src/railway_detection/synthetic/convention_b.py:291-311` (`_report_endpoint_seconds`); `tests/synthetic_mission17d/test_mission17g_hardening.py:403-411` (`test_17i_report_traversal_never_copies_or_indexes_report_grid`); `tests/synthetic_mission17d/test_mission17g_hardening.py:422-437` (`test_17i_missing_records_and_unmatched_interior_endpoints`).

## 2. H-N02 complete diagnostic classification and remediation

**Verified fresh initial command:** `.venv/bin/ruff check --no-cache --output-format=json src/railway_detection/synthetic tests/synthetic_mission17d`, Ruff 0.16.3, exit 1, 68 findings. Exact raw JSON is in `/tmp/mission17i_initial_ruff.json`; line-by-line Git provenance in `/tmp/mission17i_lint_inventory.json`. Final identical scoped check exits 0 with `[]` (`/tmp/mission17i_final_ruff.json`). This is not a repository-wide clean-lint claim.

Classification dimensions are explicit to avoid counting a test-only warning twice as a separate finding: **C1 mission-introduced:68** (23 lines attributed to 17D fbc60aa;45 to 17G ea5da77); **C2 unrelated pre-existing repository diagnostics:0 in this scoped inventory**; **C3 test-only:46** (secondary to C1), source 22; **C4 documentation/config issue:0 Ruff findings**; **C5 contextual interpretation:16** (8B023,6B905,2UP042, secondary tags); **C6 unclear provenance:0**. All 68 pre-existed17I, but none belongs to unrelated older repository code: every affected file was introduced by 17D or 17G, confirmed by Git additions/history. The17H same-tool net comparison was not substituted for provenance. No outside-scope lint scan or cleanup is claimed.

| Rule | Initial | Exact remediation |
|---|---|---|
| E501 | 46 | Targeted statement-range formatting only; unchanged original assertion/raises ASTs. |
| B023 | 8 | Bind current group/present-label set and running scalar scores as keyword-only defaults in greedy cost callback. The original callback was consumed synchronously; no demonstrated algorithm defect is claimed. |
| B905 | 6 | Three component adjacent-grid loops use pairwise; three independent test-oracle shifted zips explicitly use strict=False (unequal lengths intentional). Never blindly changed to strict=True. |
| E731 | 3 | Replace local fixture/oracle lambdas with equivalent named defs; IO guard unchanged. |
| I001 | 2 | Sort two new17G test import blocks using scoped Ruff fix. |
| UP042 | 2 | Use StrEnum while explicitly retaining Enum.__str__/__format__ display behavior. New tests verify display,format,repr,value equality and JSON; exact typed enum membership remains. |
| E702 | 1 | Split two statements onto separate lines in dense oracle. |

Only configured tools already installed were used. Targeted formatting and import sorting are confined to these diagnostics; no project-wide config, broad per-file suppression, noqa waiver, test deletion or assertion weakening. During development the added profiling test itself produced B023 and one long-line warning; these were corrected (capture local counts, wrap assertion) before final lint acceptance. No functional test failed during development.

The table below enumerates every initial diagnostic. Locations are at baseline17H and deliberately retain those historical line numbers; current lines shift after formatting. D=`fbc60aa1e54f7fa69c824e6a73d2d52e3c7a1375`; G=`ea5da77c58577056521e362271e5bceff290aff9`. Each row is FIXED in current scoped Ruff. Category C1 applies to every row; C3/C5 shown as secondary tags. File paths are exact repository paths.

| ID | Baseline path:line | Rule | Git origin | Categories | Disposition |
|---|---|---|---|---|---|
| L01 | `src/railway_detection/synthetic/convention_b.py:25` | UP042 | D | C1,C5 | FIXED |
| L02 | `src/railway_detection/synthetic/convention_b.py:156` | B905 | G | C1,C5 | FIXED |
| L03 | `src/railway_detection/synthetic/convention_b.py:261` | E501 | G | C1 | FIXED |
| L04 | `src/railway_detection/synthetic/convention_b.py:264` | E501 | G | C1 | FIXED |
| L05 | `src/railway_detection/synthetic/convention_b.py:288` | B905 | G | C1,C5 | FIXED |
| L06 | `src/railway_detection/synthetic/convention_b.py:343` | B905 | D | C1,C5 | FIXED |
| L07 | `src/railway_detection/synthetic/grouped_cv.py:38` | UP042 | D | C1,C5 | FIXED |
| L08 | `src/railway_detection/synthetic/grouped_cv.py:251` | E501 | D | C1 | FIXED |
| L09 | `src/railway_detection/synthetic/grouped_cv.py:255` | E501 | D | C1 | FIXED |
| L10 | `src/railway_detection/synthetic/grouped_cv.py:268` | E501 | D | C1 | FIXED |
| L11 | `src/railway_detection/synthetic/grouped_cv.py:512` | B023 | D | C1,C5 | FIXED |
| L12 | `src/railway_detection/synthetic/grouped_cv.py:513` | B023 | D | C1,C5 | FIXED |
| L13 | `src/railway_detection/synthetic/grouped_cv.py:513` | B023 | D | C1,C5 | FIXED |
| L14 | `src/railway_detection/synthetic/grouped_cv.py:514` | B023 | D | C1,C5 | FIXED |
| L15 | `src/railway_detection/synthetic/grouped_cv.py:515` | B023 | D | C1,C5 | FIXED |
| L16 | `src/railway_detection/synthetic/grouped_cv.py:515` | B023 | D | C1,C5 | FIXED |
| L17 | `src/railway_detection/synthetic/grouped_cv.py:517` | B023 | D | C1,C5 | FIXED |
| L18 | `src/railway_detection/synthetic/grouped_cv.py:518` | B023 | D | C1,C5 | FIXED |
| L19 | `src/railway_detection/synthetic/grouped_cv.py:537` | E501 | D | C1 | FIXED |
| L20 | `src/railway_detection/synthetic/grouped_cv.py:597` | E501 | G | C1 | FIXED |
| L21 | `src/railway_detection/synthetic/grouped_cv.py:657` | E501 | G | C1 | FIXED |
| L22 | `src/railway_detection/synthetic/grouped_cv.py:733` | E501 | D | C1 | FIXED |
| L23 | `tests/synthetic_mission17d/conftest.py:46` | E731 | D | C1,C3 | FIXED |
| L24 | `tests/synthetic_mission17d/test_convention_b.py:200` | E501 | D | C1,C3 | FIXED |
| L25 | `tests/synthetic_mission17d/test_convention_b.py:233` | E501 | D | C1,C3 | FIXED |
| L26 | `tests/synthetic_mission17d/test_grouped_cv.py:126` | E501 | D | C1,C3 | FIXED |
| L27 | `tests/synthetic_mission17d/test_grouped_cv.py:133` | E501 | D | C1,C3 | FIXED |
| L28 | `tests/synthetic_mission17d/test_grouped_cv.py:230` | E501 | D | C1,C3 | FIXED |
| L29 | `tests/synthetic_mission17d/test_grouped_cv.py:265` | E501 | D | C1,C3 | FIXED |
| L30 | `tests/synthetic_mission17d/test_grouped_cv.py:299` | E501 | G | C1,C3 | FIXED |
| L31 | `tests/synthetic_mission17d/test_mission17f_regressions.py:6` | I001 | G | C1,C3 | FIXED |
| L32 | `tests/synthetic_mission17d/test_mission17f_regressions.py:14` | E501 | G | C1,C3 | FIXED |
| L33 | `tests/synthetic_mission17d/test_mission17f_regressions.py:38` | E501 | G | C1,C3 | FIXED |
| L34 | `tests/synthetic_mission17d/test_mission17f_regressions.py:55` | E731 | G | C1,C3 | FIXED |
| L35 | `tests/synthetic_mission17d/test_mission17f_regressions.py:56` | B905 | G | C1,C3,C5 | FIXED |
| L36 | `tests/synthetic_mission17d/test_mission17f_regressions.py:77` | E501 | G | C1,C3 | FIXED |
| L37 | `tests/synthetic_mission17d/test_mission17f_regressions.py:79` | E501 | G | C1,C3 | FIXED |
| L38 | `tests/synthetic_mission17d/test_mission17f_regressions.py:98` | E501 | G | C1,C3 | FIXED |
| L39 | `tests/synthetic_mission17d/test_mission17f_regressions.py:103` | E501 | G | C1,C3 | FIXED |
| L40 | `tests/synthetic_mission17d/test_mission17f_regressions.py:108` | E501 | G | C1,C3 | FIXED |
| L41 | `tests/synthetic_mission17d/test_mission17f_regressions.py:114` | E501 | G | C1,C3 | FIXED |
| L42 | `tests/synthetic_mission17d/test_mission17f_regressions.py:116` | E501 | G | C1,C3 | FIXED |
| L43 | `tests/synthetic_mission17d/test_mission17f_regressions.py:122` | E501 | G | C1,C3 | FIXED |
| L44 | `tests/synthetic_mission17d/test_mission17f_regressions.py:123` | E731 | G | C1,C3 | FIXED |
| L45 | `tests/synthetic_mission17d/test_mission17f_regressions.py:133` | E501 | G | C1,C3 | FIXED |
| L46 | `tests/synthetic_mission17d/test_mission17f_regressions.py:141` | E702 | G | C1,C3 | FIXED |
| L47 | `tests/synthetic_mission17d/test_mission17f_regressions.py:155` | E501 | G | C1,C3 | FIXED |
| L48 | `tests/synthetic_mission17d/test_mission17f_regressions.py:161` | E501 | G | C1,C3 | FIXED |
| L49 | `tests/synthetic_mission17d/test_mission17f_regressions.py:176` | E501 | G | C1,C3 | FIXED |
| L50 | `tests/synthetic_mission17d/test_mission17f_regressions.py:177` | E501 | G | C1,C3 | FIXED |
| L51 | `tests/synthetic_mission17d/test_mission17f_regressions.py:179` | E501 | G | C1,C3 | FIXED |
| L52 | `tests/synthetic_mission17d/test_mission17f_regressions.py:182` | E501 | G | C1,C3 | FIXED |
| L53 | `tests/synthetic_mission17d/test_mission17f_regressions.py:205` | E501 | G | C1,C3 | FIXED |
| L54 | `tests/synthetic_mission17d/test_mission17f_regressions.py:207` | E501 | G | C1,C3 | FIXED |
| L55 | `tests/synthetic_mission17d/test_mission17f_regressions.py:222` | E501 | G | C1,C3 | FIXED |
| L56 | `tests/synthetic_mission17d/test_mission17f_regressions.py:223` | E501 | G | C1,C3 | FIXED |
| L57 | `tests/synthetic_mission17d/test_mission17f_regressions.py:234` | E501 | G | C1,C3 | FIXED |
| L58 | `tests/synthetic_mission17d/test_mission17f_regressions.py:238` | E501 | G | C1,C3 | FIXED |
| L59 | `tests/synthetic_mission17d/test_mission17f_regressions.py:240` | E501 | G | C1,C3 | FIXED |
| L60 | `tests/synthetic_mission17d/test_mission17f_regressions.py:256` | E501 | G | C1,C3 | FIXED |
| L61 | `tests/synthetic_mission17d/test_mission17g_hardening.py:3` | I001 | G | C1,C3 | FIXED |
| L62 | `tests/synthetic_mission17d/test_mission17g_hardening.py:207` | E501 | G | C1,C3 | FIXED |
| L63 | `tests/synthetic_mission17d/test_mission17g_hardening.py:290` | E501 | G | C1,C3 | FIXED |
| L64 | `tests/synthetic_mission17d/test_mission17g_hardening.py:318` | E501 | G | C1,C3 | FIXED |
| L65 | `tests/synthetic_mission17d/test_mission17g_hardening.py:350` | B905 | G | C1,C3,C5 | FIXED |
| L66 | `tests/synthetic_mission17d/test_mission17g_hardening.py:365` | B905 | G | C1,C3,C5 | FIXED |
| L67 | `tests/synthetic_mission17d/test_mission17g_hardening.py:369` | E501 | G | C1,C3 | FIXED |
| L68 | `tests/synthetic_mission17d/test_mission17g_hardening.py:377` | E501 | G | C1,C3 | FIXED |

There are no remaining pre-existing scoped diagnostics requiring an exemption/file-specific deferral. Repository-wide diagnostics outside these paths were neither enumerated nor represented as fixed.

## 3. Mypy environment investigation

**Verified unresolved environment failure, not a code diagnostic.** `.venv/bin/python` can import the existing compiled mypy package, but there is no mypy executable in `.venv/bin`, no mypy.__main__ module, and no installed `mypy/bogus_type*` file. Fresh `mypy.api.run(['--follow-imports=skip','--cache-dir=/tmp/mission17i_mypy_cache','src/railway_detection/synthetic'])` raises before analysis:

```text
ModuleNotFoundError: No module named 'mypy.bogus_type'
```

Trace path: api→main→build→semanal_main→checker→checkexpr→applytype→subtypes→constraints→typeops→checker_state→checker_shared→errors→types→missing bogus_type. Exact traceback retained at `/tmp/mission17i_mypy_failure.txt`. No dependency installation, upgrade, replacement or environment repair occurred. Syntax/AST compilation is not a Mypy pass. Type analysis remains **NOT EXECUTED**, with future separately authorized repair and rerun, or an explicit researcher disposition limited to synthetic-stage work. No waiver is fabricated here.

## 4. Caller-trust contract and meaning of validation

**Structural validation** checks exact types, schema, IDs, tuple shape and field ranges. **Semantic validation** checks joins/DAG, roles, feasible assignments, time order and deterministic operation consistency. **Provenance binding** links declared canonical inputs/policy/config to output and separately retained expectations. **Authenticity** means knowing the actual original producer/authority; it is not provided by a synthetic ID or frozen object. **Integrity here** means content consistency relative to independently retained expectations; unkeyed SHA256 is used, but there is no cryptographic authentication, signature/MAC verification or protected storage establishing trusted integrity. **Authorization** is permission for an operation and is not conferred by any validation/hash/test result.

All following inputs originate with a trusted cooperative synthetic caller. Acceptability is conditional on constructed-only fixtures, independent expectation ownership, nonmutation during a call and the stated verifier scope. None is acceptable alone as real-data scientific or resource authority.

| Exact input(s) | Origin / copied, referenced, derived or recomputed | Current checks | Not established; caller retention / substitution consequence |
|---|---|---|---|
| SyntheticDataset.dataset_id/version/events/captures/assets/annotations | Fixture owner; frozen records referenced, registry/group/canonical payload rebuilt | Typed nonempty registry, version, complete joins, digest | Original corpus authenticity/role truth. Retain original fixture/version outside candidate; coherent full replacement can reclassify reserved sources. |
| PhysicalEvent.event_id/aliases/role/labels/weather/lighting/direction/provenance_ref | Fixture declarations referenced; canonical event/groups derived | Alias uniqueness, typed roles, original-label support, known/unknown metadata | Physical pass equivalence, labels/conditions/role adoption. Caller retains originating identity/role record. |
| Capture.capture_id/event_ids/kind/camera/crossing/session/provenance_ref | Caller source metadata; joins recomputed | Valid capture memberships and exact source type/metadata | Actual capture/camera/crossing independence. False coherent metadata can pass; retain intended evidence separately. |
| Asset IDs/event/kind/capture/parents/transform/annotation IDs/frame_index/pts_ticks/timebase/unavailable_reason/content_identity/provenance_ref | Caller source/derived declarations referenced; DAG/topology and group weights derived | Timing shape, original/derivative rules, same-event ancestry, duplicate-content conflicts | Real byte identity, transform execution, near-duplicates and timing accuracy. Retain complete declared lineage; no resource hashing. |
| Transform.transform_id/version/parameters/provenance_ref; Annotation IDs/asset/labels/confirmed_empty/provenance_ref | Caller declarations; sorted canonical copies | Exact parameters/version consistency, annotation ownership/label/empty disposition | Actual transformation/human label truth; coherent fabricated evidence remains possible. |
| expected_policy / allocate(k,required_support,node_budget,allow_ungrouped_fallback) | Independently chosen request; canonical policy derived/revalidated, digest recomputed | Exact fixed profile/schema/objective/role/search/no-fallback and parameters | Intended authorized request. Retain policy before candidate; candidate-derived expectation defeats mismatch protection. |
| Allocation candidate, including assignments/objective/status/work/reasons/digests/version/limitations | Allocator output or caller-supplied candidate; full operation recomputed | Exact field types plus complete record comparison | Prior execution/history and scientific eligibility; self-serialization alone can accept false plausible work. |
| RoleContext.dataset/allocation/policy/outer_fold/validation_events/calibration_mode/frozen_rule_id | Original owner references; expected RolePlan rebuilt on every fit call | Fresh registry/allocation, full original roles/plan comparison, disjointness | Context authenticity and actual frozen-rule adoption. Retain outside candidate channel; replacement of both candidate/context can pass. |
| RolePlan and operation/fit_events/selection_events/producing_fit_events | Caller metadata proposal; sets derived, compared to reconstructed plan | Declared membership/subsets, no outer/reserved contamination, INNER_OOF denial | Actual fitting/cache/initialization/exposure. Empty/false declared lists do not prove training history; future artifact/OOF registry required. |
| CausalRunner(initial_angle,closing_seconds,opening_seconds,watchdog), run(mode,cutoff,report_times) | Caller settings normalized into local effective RunConfiguration; fixed tuple copied | Exact range/mode/grid/watchdog/model constraints; snapshot consumed | Approved dynamics/clock/safety policy. Retain selected exact configuration separately; self-selected config is not adoption. |
| SyntheticEvent(event_id,timestamp,target,nested_command), fixture_id | Caller ordered records; indexed list copied, records referenced | Namespace, exact time/command, accepted identity/order/cutoff semantics | Actual controller decision/sensor truth/time alignment. Retain full original order/values and expected command mapping. |
| RunResult / expected_configuration | Producer output and independent caller-selected expected record | Config type/digest/settings/profile/mode/initial/report-grid consistency | Detached angles/durations/events/code/run authenticity. Retain producing code+inputs and recompute/full-oracle-check before detached-result acceptance. |
| Python runtime/module globals and private helper/solver arguments | Cooperative trusted process; no protected execution boundary | Source/import/guard checks and public validation | Hostile concurrent mutation/OS access resistance. Frozen __dict__ can be bypassed; private routines are not externally trusted APIs. |

The companion contracts enumerate exact schemas/units and failures. No additional authenticity infrastructure is implemented. Configuration-only verification still accepts fabricated trajectory numbers under unchanged settings; that documented boundary is preserved honestly, not described as a verified trajectory.

## 5. Fit-membership validation: justified local reuse

Before 17I: allocate validated once; verify twice; role_plan and fit-membership three times, each repeating one full allocation. The duplicate registry traversals inside a single synchronous call consumed the same validated data and were not mathematically necessary. **Implemented:** private `_allocate_validated(registry,policy)` contains the unchanged allocation algorithm; private `_verify_allocation` freshly validates once, checks/recomputes the complete receipt and returns that same registry for role construction. Public `verify_allocation` still returns only bool. Public role_plan/fit validation never accepts a caller-created validated registry. No cache, invalidation parameter or long-lived verified-plan shortcut exists.

| Public operation | Before registry passes | After registry passes | Allocation computations after |
|---|---|---|---|
| allocate | 1 | 1 | 1 |
| verify_allocation | 2 | 1 | 1 |
| role_plan | 3 | 1 | 1 |
| validate_fit_membership | 3 | 1 | 1 |
| Ten fit checks | 30 | 10 | 10 |

New profiling regression executes each public operation twice at M24 and1536,K4 and asserts exactly 2 registry validations, 2 internal solver calls and 2*M*4 greedy cost calls. Thus a single 1536-event operation still scores 6144 fold choices; ten such fits would score 61440 (derived, not a new ten-fit benchmark). Solver replay remains essential to the complete deterministic receipt contract and is retained. With Q checks, cost remains Q*(V+allocation), including repeated bounded search. No cross-call asymptotic speedup or resource-exhaustion protection is claimed.

Mutation tests bypass normal frozen assignment after a passing check and alter version, annotations, policy budget, receipt work or role; all subsequent checks reject. Caller-supplied ValidatedDataset rejects at both public allocate/verify entrypoints. Existing six failure regressions, all status cases,2704 exhaustive tiny inputs and50 independent dense scoring fixtures still pass. Cooperative nonmutation during a call remains assumed; redundant passes never constituted protection against arbitrary same-process attackers. Greedy callback binding removes lint ambiguity without changing scoring/tie order. Full registry semantic validator, motion math and original assertions remain AST-equivalent apart from formatting.

References: `src/railway_detection/synthetic/grouped_cv.py:500-605` (`_allocate_validated`); `src/railway_detection/synthetic/grouped_cv.py:686-706` (`_verify_allocation`); `src/railway_detection/synthetic/grouped_cv.py:743-789` (`role_plan`); `src/railway_detection/synthetic/grouped_cv.py:792-857` (`validate_fit_membership`).

## 6. Executed validation and isolation

Development command (existing isolated harness, root conftest excluded):

```sh
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest --confcutdir=tests/synthetic_mission17d -p no:cacheprovider --import-mode=importlib tests/synthetic_mission17d -q --junitxml=/tmp/mission17i_development.xml -o junit_family=legacy
```

**Observed:** 238 passed in 7.29s, exit 0. Unique cases: 114 original (70 simulation / 38 CV / 6 isolation),22migrated17F,80prior 17G,22new17I. New cases reside in existing `test_mission17g_hardening.py` (now 102); no new test module. All prior test names, assertions and raises expectations are retained; exact AST comparison passed for each existing test's assertions/raises. Syntax compile passed for all nine Python files without bytecode. No xfail/skip was introduced. Python-level no_component_io guard text and entire test_isolation.py are byte-identical to baseline; conftest's only edit is an unrelated fixture lambda-to-def. All tests inherit the existing IO guard. This is cooperative Python isolation, not an OS sandbox.

**Final staged-state execution:** `238 passed in 7.31s`, exit0, Python3.11.15. JUnit:70 simulation,38 CV,6 isolation,22 migrated audit,102 hardening;238 unique cases,22 new,zero failures/errors/skips. Command is the development command above with JUnit path `/tmp/mission17i_staged.xml`. Fresh staged Ruff check exits0 with empty JSON. Source/test SHA256 values before and after execution match. This report-only receipt update changes no tested source/test byte; final index comparison retains that identity. Receipt: `/tmp/mission17i_staged_test_receipt.json`.

Document validation passed: four new reports,42 valid current-source citation ranges,17 internal links,68 unique lint inventory IDs and12 requirements in each component contract. A draft production gate-model citation exceeded its file length; corrected before acceptance. Current implementation/AST references and historical baseline lint locations are distinguished. Full source/test diff was reviewed; original assertions/raises, motion/lineage/receipt checks and search body retained. Final delivery gate requires exact scope and remote checks below.

| Tested safe source/test path | SHA256 |
|---|---|
| `src/railway_detection/synthetic/__init__.py` | `a269b30d6399436161dc863db33fd4dccb7d243926ea6c1fd505adabec278f02` |
| `src/railway_detection/synthetic/convention_b.py` | `345b0b89c988224855caa1208078d4eb6de4384e2090c1e27c75d1fdfbec5d10` |
| `src/railway_detection/synthetic/grouped_cv.py` | `38b315fc94e27bfa9aee21ac0d32ebabac6ed90081ac2af570fd2d1321841a74` |
| `tests/synthetic_mission17d/conftest.py` | `47d348f9b41ea8d99cb6bb900dd701b6d09c12d91c862d63dfb11ed1a6725505` |
| `tests/synthetic_mission17d/test_convention_b.py` | `2aa21e462217ee7126afc98a4d5a26633e50da6063fbf8418b9205d695fae658` |
| `tests/synthetic_mission17d/test_grouped_cv.py` | `81018f5539a144e650d5206c9cf9bda5ca8474230773310b781b5e733c42c12d` |
| `tests/synthetic_mission17d/test_isolation.py` | `5d9424894bb70979695114bb72b9955885b6448874f6c8eddbfddf8622c52986` |
| `tests/synthetic_mission17d/test_mission17f_regressions.py` | `9b5cb17c176079275d8261cd6f33906268524f009b37c2a28a116d22590f5ff4` |
| `tests/synthetic_mission17d/test_mission17g_hardening.py` | `5e6e62b3cf8f8b85dc3532d03fb6942fe02f7a51bd3fa60d18c6cc994cd7ddaa` |

New tests (case counts sum22):

| Test in tests/synthetic_mission17d/test_mission17g_hardening.py | Cases | Purpose |
|---|---|---|
| test_17i_report_traversal_never_copies_or_indexes_report_grid | 4 | No report indexing/slicing at empty/small/8192 scale; exact total. |
| test_17i_duplicate_disjoint_overlapping_and_unmatched_report_horizons_reject | 6 | Invalid duplicate/order/horizon grids reject. |
| test_17i_missing_records_and_unmatched_interior_endpoints | 1 | Empty,singleton,missing timestamp,valid unmatched interior endpoints and missing interval rejection. |
| test_17i_duplicate_arrivals_order_and_default_totals_reset | 1 | Deterministic accepted/rejected order,default reuse and no stale total. |
| test_17i_enum_modernization_preserves_display_value_and_serialization | 2 | Command and DatasetRole display/value/format/repr/JSON compatibility. |
| test_17i_each_public_cv_operation_validates_once_and_recomputes | 2 | Measured call counts and recomputation on repeated calls at24/1536events. |
| test_17i_repeated_fit_calls_do_not_reuse_stale_context | 5 | Five post-validation mutations reject. |
| test_17i_prevalidated_caller_object_is_not_a_public_trust_shortcut | 1 | Forged/prevalidated wrapper cannot bypass public original input validation. |

Ruff final scoped JSON is empty. Mypy unexecuted due startup failure as above. Static AST import inspection keeps components standard-library-only with no file/network/process/dynamic-code entrypoint; legacy/root suites and production modules were not executed. Memory probes used only newly constructed intervals/grids. Temporary receipts are engineering evidence outside the repository, not extra deliverables. Final diff/reference/byte checks are required before exact-path normal commit.

## 7. Exact authorized changed files

| Status | Exact path |
|---|---|
| M | `docs/generated/master_reaudit/MISSION_17G_FIVE_DEFECT_REMEDIATION_REPORT.md` |
| M | `src/railway_detection/synthetic/convention_b.py` |
| M | `src/railway_detection/synthetic/grouped_cv.py` |
| M | `tests/synthetic_mission17d/conftest.py` |
| M | `tests/synthetic_mission17d/test_convention_b.py` |
| M | `tests/synthetic_mission17d/test_grouped_cv.py` |
| M | `tests/synthetic_mission17d/test_mission17f_regressions.py` |
| M | `tests/synthetic_mission17d/test_mission17g_hardening.py` |
| A | `docs/generated/master_reaudit/MISSION_17I_FINAL_ENGINEERING_REMEDIATION_REPORT.md` |
| A | `docs/generated/master_reaudit/MISSION_17I_CONVENTION_B_INTEGRATION_CONTRACT.md` |
| A | `docs/generated/master_reaudit/MISSION_17I_GROUPED_CV_INTEGRATION_CONTRACT.md` |
| A | `docs/generated/master_reaudit/MISSION_17I_MISSION18_ACCEPTANCE_AND_DEPENDENCY_REGISTER.md` |

Seven existing Python files modified, one related 17G report corrected, exactly four new 17I reports;12 changed files,zero deletions. Existing synthetic __init__.py/test_isolation.py unchanged. No configuration/dependency/production/controller/adjudication_session.py/governance/protocol/decision/allowlist/resource/GT/history change.

## 8. Acceptance, remaining limits and delivery

All 17I gates are met when final staged-state validation below is recorded: baseline verified; memory implementation/claim corrected; actual bounds disclosed;68lint findings classified/remediated; no rules weakened; Mypy failure investigated; caller trust inventoried; redundant validation safely reduced/tested; two complete contracts and categorized18A/18B register delivered; synthetic tests/isolation pass; only authorized scope changes; accurate reference/scope/secret checks. COMPLETE refers to these gates; the user explicitly permits unresolved Mypy environment failure if captured honestly. It does not assert type correctness or integration acceptance.

Remaining restrictions: expected-source authenticity is caller-trusted; detached trajectory values need a future complete acceptance envelope; private helper assumes producer geometry; whole-run storage is linear; repeated full allocation/search cost remains; no global CV optimum, actual fit/OOF/exposure registry, scientific independence, human/security infrastructure or protected execution readiness is established. All future adapter tests in the dependency register are planned/unexecuted. Researcher selections/approvals remain pending, v7.1.1 proposed, OptionC unapproved and RD001–RD055 unchanged.

Protected account: raw media access/preview/playback/decode/hash0; checkpoint/protected-cache access0; real-data inference/training/replay/evaluation0; fitting/prediction/real calibration0; official split creation/promotion0; human annotation/adjudication/GT modification0; authorization-token implementation/issuance0; protocol/threshold/camera-scope/governance/researcher decision changes0. Safe source/docs and constructed objects only; no macOS privacy bypass. Test IO guards are preserved.

Review full worktree/staged diff; stage only these 12 paths; verify staged bytes equal tested bytes, scoped secrets/resources scan and exact four additions; run relevant tests against staged state; check remote still at baseline. Commit exactly `feat: finalize synthetic engineering contracts for mission 18`, push normally to origin/main, verify local=tracking=live and clean tree. No force/reset/clean/amend/rebase/history rewrite or broad staging. Actual final commit/hash verification belongs in the completion response; the report cannot contain its own hash.

**Stop for researcher review. Mission 18 has not begun and must not begin automatically.** Contract-defined synthetic adapter work is conditionally implementable only after explicit scope authorization and selected policy/ownership/workload/static-gate decisions. Real-data,production,human-review and official-split work remain unauthorized.
