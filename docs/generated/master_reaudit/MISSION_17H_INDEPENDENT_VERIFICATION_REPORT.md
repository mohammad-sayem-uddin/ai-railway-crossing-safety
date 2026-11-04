# Mission 17H — Independent engineering verification of 17G remediations

Date: 2026-11-04, America/New_York. Repository: `/Users/sayemuddin/Desktop/Train_automation`; branch main. Audited baseline: `ea5da77c58577056521e362271e5bceff290aff9`. Mission scope is implementation read-only: existing synthetic test reproduction, source/history review, one-off constructed-input observations and exactly two new Markdown reports.

## 1. Executive verdict and evidence standard

**Overall disposition: CONDITIONALLY_READY_WITH_DOCUMENTED_RESTRICTIONS.** The five original 17F defects are corrected within the documented synthetic contracts. All 216 unique existing cases reproduce, and the six former expected failures are ordinary, specific rejection tests. Fresh probes support expected-input comparison, strict allocation-receipt validation, actual producer configuration snapshots and linear reporting time. This does not approve production wiring or real-data research execution.

Two LOW-severity findings are recorded. **H-N01 — the 17G O(1) extra traversal-space claim is false** because fixed-grid reporting copies `report[1:]`: helper auxiliary space is O(R), while the original quadratic-time defect remains fixed. **H-N02 — the current Ruff check fails with 68 diagnostics**, comprising existing and added lint debt rather than 68 demonstrated functional defects. Four important trust/validation boundaries and a private-helper precondition limit were also demonstrated; these are restrictions on reliance, not proof of new protected-data incidents. No implementation or test was repaired during this audit.

The same assistant authored 17G in this conversation. This is a fresh technical challenge using newly executed commands/fixtures, not human-independent or institutional review, a separate human sign-off or hardware safety certification. A session boundary alone would not establish that independence.

Evidence labels used below: **Verified** means directly observed source, execution or explicitly stated algorithmic reasoning; **Partially verified** means only the named portion was established; **Contradicted** means observed evidence conflicts with a claim; **Unsupported** means insufficient supporting evidence; **Not verifiable** means required external evidence was unavailable or outside authorized access. Passing execution is finite evidence, not an all-input theorem.

Companion: [integration readiness decision](MISSION_17H_INTEGRATION_READINESS_VERDICT.md). Original defect specification: [17F audit](MISSION_17F_INDEPENDENT_ENGINEERING_AUDIT.md). Remediation claims: [17G report](MISSION_17G_FIVE_DEFECT_REMEDIATION_REPORT.md).

## 2. Fresh repository verification and exact 17G scope

**Verified — Git inspection.** Initial repository location and branch matched the request. Local HEAD, origin/main and live `git ls-remote origin refs/heads/main` each returned `ea5da77c58577056521e362271e5bceff290aff9`. The tree was clean including untracked files. `git merge-base --is-ancestor ea5da77c58577056521e362271e5bceff290aff9 HEAD` succeeded; the commit was HEAD itself. `git log ea5da77c58577056521e362271e5bceff290aff9..HEAD` was empty. There were no additional post-17G changes to preserve or reconcile.

Actual 17G parent: `7c247716e390400421c4b0c293e37a90ec1b499e` (17F). Actual subject: `fix: remediate mission 17F synthetic engineering findings`. Git diff/history, all nine current synthetic Python files, the complete 17G report and relevant 17F specification/reproduction evidence were inspected. The changed-file list, not a narrative inventory, is:

| Status | Exact 17G path |
|---|---|
| M | `src/railway_detection/synthetic/convention_b.py` |
| M | `src/railway_detection/synthetic/grouped_cv.py` |
| M | `tests/synthetic_mission17d/test_grouped_cv.py` |
| A | `tests/synthetic_mission17d/test_mission17f_regressions.py` |
| A | `tests/synthetic_mission17d/test_mission17g_hardening.py` |
| A | `docs/generated/master_reaudit/MISSION_17G_FIVE_DEFECT_REMEDIATION_REPORT.md` |

This is three modifications, three additions, zero deletions; 1256 inserted/130 removed lines. Fresh byte comparison confirms conftest.py, test_isolation.py and the 70-case simulation test module equal 17F. Fresh AST comparison confirms unchanged core motion/timestamp/command functions and the grouping validator/objective/feasibility predicate. The actual diff shows added bindings and changed verification/reporting, with the original greedy/search algorithm retained. Git identity and hashes establish observed bytes/history, not signed researcher approval.

## 3. Five defect dispositions

| Original defect | Independent disposition within stated scope | Evidence and qualification |
|---|---|---|
| F17-01 Original-role binding | **Verified — fixed for retained original context** | RolePlan now binds dataset/version/input/policy/allocation/original roles/outer fold. Missing, contradictory, stale or independently mismatched contexts reject after full registry and allocation reconstruction. Replacing BOTH expected source and candidate coherently can succeed: expected-source authenticity remains caller-trusted. |
| F17-02 Allocation-policy binding | **Verified — fixed** | Canonical policy content, version/profile, K/support/budget/search limit/objective/role/no-fallback semantics are hashed and compared with separately supplied expected policy. Same profile name with different parameters cannot validate an old receipt. This is unkeyed content consistency, not authenticated authority. |
| F17-03 Receipt validation | **Verified — fixed for typed allocation receipts** | Exact numeric types exclude bool/float substitutions; identity/shape/ranges/duplicates/status/work are checked and the full bounded operation is recomputed. Plausible but incorrect assignments/counters reject. Serialization alone is not operation verification or proof an operation historically occurred. |
| F17-04 Missing run configuration | **Verified — fixed at producer/configuration boundary** | Every returned status records the same immutable effective settings snapshot used for motion/watchdog/reporting. Different settings distinguish identical trajectories. **Partially verified** as general provenance: configuration checks do not authenticate source/input/run identity or validate detached trajectory values. |
| F17-05 Quadratic reporting | **Verified — original time defect fixed** | Default totals reused; fixed-grid index moves only forward. Source and 15 scaling profiles support O(S+R) reporting time. **Contradicted** ancillary 17G space claim: tuple slicing adds O(R) auxiliary storage (H-N01). |

### A. Original source and role context

`src/railway_detection/synthetic/grouped_cv.py:181-357` (validate_dataset); `src/railway_detection/synthetic/grouped_cv.py:691-700` (RoleContext); `src/railway_detection/synthetic/grouped_cv.py:703-739` (role_plan); `src/railway_detection/synthetic/grouped_cv.py:742-807` (validate_fit_membership).

PhysicalEvent.role is mandatory and typed. Assets/aliases/annotations/parents resolve to canonical events; orphan, cyclic, multi-event and ambiguous identities reject. RoleContext is not treated as proof merely because an object exists: verification rebuilds the expected plan from its original dataset/allocation/policy/outer/inner/calibration/refit inputs and compares all plan fields before membership checking.

**Verified — execution:** valid original fit membership, reserved derivative lineage, missing role/context, coherent control/train swap, altered parent/event linkage, duplicate source and ambiguous alias challenges behaved as required. Changing only expected dataset/version while retaining the old receipt rejects. Even bypassing normal frozen assignment through an instance dictionary did not make a stale context pass: the original input digest mismatch was detected. However, a newly allocated/reconstructed candidate using a fully reclassified expected dataset did pass; there is no external original-source authority to distinguish that deliberate replacement. This is an important retained-input trust limit, explicitly disclosed in 17G.

### B. Policy content and mutation

`src/railway_detection/synthetic/grouped_cv.py:383-415` (AllocationPolicy); `src/railway_detection/synthetic/grouped_cv.py:426-445` (Allocation); `src/railway_detection/synthetic/grouped_cv.py:643-666` (verify_allocation).

Policy digest covers canonical dataclass content: K, sorted support, node budget, algorithm profile, fixed search limit, objective, role policy, fallback=False and schema. The receipt carries this digest alongside its separate corpus digest and repeated K/support/budget/profile fields. Shape validation reconstructs and checks the policy binding; verification separately compares the retained expected policy. It does not rely on the policy name alone. Factory-normalized equivalent support orders agree; duplicates and unsupported policy variants reject.

**Verified — execution:** missing identity, wrong expected policy/budget, same-name changed content, foreign dataset receipt and old receipt/new policy reuse reject. Normal frozen mutation fails; a deliberate instance-dictionary policy mutation also causes the old receipt to reject against the changed expected content. There is no cached digest that remains silently valid after such a mutation. Replacing both expected policy and a newly recomputed candidate is a new declared request, not an authenticated authorization decision.

### C. Receipt-to-operation relation

`src/railway_detection/synthetic/grouped_cv.py:584-640` (_validate_receipt_shape); `src/railway_detection/synthetic/grouped_cv.py:643-666` (verify_allocation).

Exact Allocation type, profile/schema, IDs/digests, integer fields, canonical support, unique sorted assignments, exact fold indices, objective tuple, reason, limitations and work/status relationships are validated. Dicts, missing/wrong identity, unexpected string-enum status, IntEnum fold, bool/float counters/objectives, malformed nested tuples, duplicates, stale schema, reordered assignments, altered balanced partitions and plausible forged work/status all reject in fresh observations. Valid infeasible/undetermined receipts return False because they contain no accepted allocation; that is not the same as accepting a malformed receipt.

The verifier re-executes deterministic allocate on the validated original registry and expected policy and compares the complete record. It does not prove that this operation ran previously or that the source labels/roles are true. Allocation.canonical_json checks self-declared receipt shape/policy consistency without a dataset/expected request; a positive but false greedy counter can serialize and is rejected only by full verify_allocation. Consumers must not turn serialization success into receipt acceptance.

### D. Effective configuration and result detachment

`src/railway_detection/synthetic/convention_b.py:119-175` (RunConfiguration); `src/railway_detection/synthetic/convention_b.py:211-238` (RunResult); `src/railway_detection/synthetic/convention_b.py:241-266` (verify_run_configuration); `src/railway_detection/synthetic/convention_b.py:334-476` (CausalRunner.run).

Constructor settings plus actual mode/cutoff/report arguments form one local frozen snapshot. Motion rates, initial state and watchdog logic use its captured values. Config records include the exact numeric/model/timestamp/latency/timer rules; defaults are recorded as actual defaults rather than reconstructed from missing data. Empty/incomplete results retain their configuration while physical origin/angle may remain absent.

**Verified — execution:** literal defaults equal equivalent explicit defaults; 3s versus 6s closing distinguishes config provenance on the same no-motion path. Missing config/expected config and changed config against retained expected settings reject. Normal post-run mutation is blocked. Changing runner settings before a run changes both used/logged settings; a profile callback changing settings during motion leaves the current snapshot 3s/final 30° intact and the later run uses 6s/final 60°. Computational functions were not patched for this probe.

**Verified limitation:** a dataclass-replaced result can carry a different internally consistent configuration/digest and serialize without proving its old trajectory matches those settings. Config verification with a correct retained expected record detects a config substitution, but does not reject fabricated final_angle/endpoint duration 999 under unchanged expected settings. The function explicitly documents configuration-only scope. This contradicts a stronger interpretation of complete result authenticity, not the specific 17G producer-configuration claim. Trusted producer/input provenance or a separate full result verifier is required before treating detached output as evidence.

## 4. Adversarial observations and actual outcomes

No test module or implementation file was added or edited. New cases were one-off stdin commands over freshly constructed `synthetic:h:`/`synthetic:hp:`/`synthetic:he:` fixtures, with exact transcripts below. Temporary JSON receipts contain engineering evidence only. Counts here are observation groups, not extra pytest tests.

| Observation set | Actual result | Interpretation |
|---|---|---|
| 65 A–D/import probes | 48 expected rejections and 13 expected acceptances matched; four explicitly demonstrated trust limits also accepted; 0 unexpected outcomes | The four trust-limit acceptances are not security passes. |
| Six supplementary boundary observations | Four missing-parent/orphan/mutated-context/mutated-policy cases rejected; two malformed private interval lists accepted | Public CausalRunner creates ordered contiguous intervals. The private reporting helper is not a standalone interval validator. |
| 11 public grid/reset groups | Empty/singleton/interior-grid/duplicate/older cases and six bad-grid variants matched requirements; reused-run totals 2→0→2 | No stale total observed; duplicate report grids/nonspanning/disjoint horizons reject. |
| 15 reporting profiles | Default/fixed workloads at S=32,128,512,2048,8192 matched exact endpoint/integral oracles and linear operation counts | Numerical and finite scaling evidence, not a hardware benchmark. |
| Five isolated memory measurements | Peak grew with R, including an extra tuple slice | H-N01 space claim contradicted; see below. |
| 28 CV operation profiles | Registry/allocation/search/candidate-evaluation counts measured across M=24…1536 and four budgets | Recalculation cost is real, deterministic and repeated. |

The two private-helper experiments supplied gaps or overlaps that the public producer cannot emit. The helper returned 3s/0s respectively instead of rejecting arbitrary interval geometry. This is an internal precondition limit: future integration must preserve the public producer's ordered-contiguous interval guarantee or add a separately reviewed validator before exposing this helper. No valid public case was shown to produce such malformed intervals.

The 65-case and cost-measurement commands ran under selected Python open/Path/socket/Popen denial hooks and observed zero denied-call attempts. Supplementary boundary commands used only constructed objects and the inspected pure component paths. All nine source/test hashes remained identical throughout.

## 5. Test reproduction: exact commands, outputs and quality

**Verified — execution.** Commands were parsed from the actual 17G report, not guessed. Environment: repository Python 3.11.15; plugin autoload, cache and bytecode writes disabled; root conftest excluded. The first command is exactly the requested 17D directory selector and now collects 216 cases. The three subset selectors were also executed, with JUnit evidence flags shown. The unique union of their testcase IDs is 216; do not add the combined result again.

```sh
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest --confcutdir=tests/synthetic_mission17d -p no:cacheprovider --import-mode=importlib tests/synthetic_mission17d -q
```

**combined — exit 0**, exact stdout:

```text
........................................................................ [ 33%]
........................................................................ [ 66%]
........................................................................ [100%]
216 passed in 4.13s
```

```sh
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest --confcutdir=tests/synthetic_mission17d -p no:cacheprovider --import-mode=importlib tests/synthetic_mission17d/test_convention_b.py tests/synthetic_mission17d/test_grouped_cv.py tests/synthetic_mission17d/test_isolation.py -q --junitxml=/tmp/mission17h_original.xml -o junit_family=legacy
```

**original — exit 0**, exact stdout:

```text
........................................................................ [ 63%]
..........................................                               [100%]
114 passed in 0.56s
```

```sh
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest --confcutdir=tests/synthetic_mission17d -p no:cacheprovider --import-mode=importlib tests/synthetic_mission17d/test_mission17f_regressions.py -q --junitxml=/tmp/mission17h_audit.xml -o junit_family=legacy
```

**audit — exit 0**, exact stdout:

```text
......................                                                   [100%]
22 passed in 3.73s
```

```sh
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest --confcutdir=tests/synthetic_mission17d -p no:cacheprovider --import-mode=importlib tests/synthetic_mission17d/test_mission17g_hardening.py -q --junitxml=/tmp/mission17h_hardening.xml -o junit_family=legacy
```

**hardening — exit 0**, exact stdout:

```text
........................................................................ [ 90%]
........                                                                 [100%]
80 passed in 0.32s
```

Original subset: 70 simulation/38 CV/6 isolation. Migrated subset: 22 including the six former expected failures. Hardening subset: 80. All JUnit subset failures/errors/skips were 0. No expected-failure/skip markers exist in the current test AST. The six specific case IDs are:

- `test_context_bound_fit_gate_should_reject_coherent_control_to_train_swap`
- `test_context_bound_allocation_gate_should_reject_weakened_request`
- `test_receipt_validator_should_reject_invalid_types_and_work_semantics[bool_objective]`
- `test_receipt_validator_should_reject_invalid_types_and_work_semantics[float_objective]`
- `test_receipt_validator_should_reject_invalid_types_and_work_semantics[negative_work]`
- `test_receipt_validator_should_reject_invalid_types_and_work_semantics[search_without_nodes]`

Their bodies include valid controls and explicit expected policy/context; malformed bool/float objectives, negative work and zero-node search fail at the matching rejection assertions. They do not merely pass because an expected argument was omitted. Fresh 65-case probes also exercised these validation categories with independently constructed inputs.

**Verified source quality:** exact rational reference vectors and geometric oracles check numerical values; tiny exhaustive feasibility and dense greedy-score oracles avoid relying solely on allocate's own verifier. Scaling tests check operation counts instead of one elapsed time. The corrected six negatives require InvalidInput and, for the migrated cases, the relevant message. Positive controls prevent blanket rejection from looking successful.

**Limitations:** 35 source `pytest.raises(ValueError)` constructs are broader than the 23 InvalidInput constructs (these are AST constructs, not case counts), so some negatives could pass at an unintended earlier ValueError. The original fixture factory uses `roles = roles or default` and derivative helper uses `parents or original`; empty supplied tuples can therefore be replaced in fixtures, although production validation still rejects missing role/parent evidence. Direct fresh probes covered those states. The fixed-grid slow oracle uses implementation interval starts; the separate geometric oracle supplies stronger trajectory evidence but finite coverage. Default lookup-stub tests can miss a future differently named inline rescan; current source and fresh profiles were checked directly. Global F17_RESULTS oracle counters assume a fresh-process run rather than repeated pytest calls in one interpreter. The documented commands use fresh processes. None of these limitations was repaired or hidden by changing tests.

The repeated allocator verifier shares algorithm code with allocation; it can reproduce a correlated algorithm bug. The retained 2704 tiny exhaustive inputs and independent scoring/geometry checks provide finite complementary evidence, not a universal proof or a claim of scientific independence.

## 6. Caller-trust inventory

| Important input / source | What is checked | What remains trusted / consequence | Synthetic-use restriction |
|---|---|---|---|
| SyntheticDataset event role/aliases/labels from fixture author | Typed IDs, canonical resolution, annotation/original joins, DAG, metadata/version/digest | Physical pass truth, prospective permission and label/exposure accuracy; coherent full replacement is possible | Retain an independently selected original fixture/registry; never treat prefix/hash as approval. |
| Capture/camera/session/content/transform metadata from caller | Required joins, parameters, timing shape, explicit unknowns, exact duplicate conflicts | Actual source identity, camera relation, transform execution and near-duplicate truth are not independently established | Constructed-only metadata; no independent-held-out or real lineage claim. |
| RoleContext from caller | Rebuild plan/receipt against dataset+policy and outer/inner/calibration/refit settings | Context preservation/authenticity; replacing both expected source and candidate succeeds | Owning caller must retain expected context outside the candidate submission. Frozen objects are cooperative immutability, not a protected trust root. |
| Expected AllocationPolicy from caller | Canonical body and exact parameters/version, digest and candidate comparison | Whether it is the intended authorized request | Retain expected parameters separately; a name alone or candidate-derived expectation is insufficient. |
| Allocation candidate from caller/allocate | Exact shape/types and complete deterministic recomputation | Historical execution and actual scientific eligibility are not authenticated | Use full verifier; canonical_json alone is insufficient. |
| FIT/SELECT/producer event lists from caller | Disjointness and subset membership relative to bound plan | Actual fitting/model/initialization/cache exposure is self-reported; no artifact bytes/DAG proof | Metadata proposal checks only; INNER_OOF remains denied without evidence. |
| SyntheticEvent/time/target/report grid from caller | Exact numeric rules, identity/type/order, rejection/cutoff/priority and increasing report grid | Sensor truth, clock accuracy/alignment and scientific suitability | Explicitly constructed commands only; no real controller/sensor/hardware claim. |
| Expected RunConfiguration from caller | Exact schema/settings and recorded binding; producer uses local snapshot | Which original input/code/run produced a detached result, and trajectory correctness | Retain source/input receipts and numerical oracle; configuration validation is not result acceptance. |
| Python runtime, module globals and caller execution | Audited source hashes/imports and selected guard tests | Same-process mutation, arbitrary external Python code, hostile OS/admin and resource limits | Trusted cooperative test process only; no sandbox/security capability claim. |

**Verified:** accidental changes relative to retained inputs reject in the challenged cases; normal frozen mutation is blocked, but instance-dictionary mutation can bypass Python's normal assignment protection and must not be considered impossible. Content revalidation caught stale context/policy mutations in the supplementary cases. **Unsupported/Not verifiable:** human truth, independent approval, authenticated source retention, actual model exposure and deployed OS enforcement. No protected resource was inspected to manufacture that missing evidence.

## 7. Receipt recomputation: cost and necessity

Let V be complete registry validation/canonicalization cost and A be allocation work after validation. V includes derivative traversal and sorting canonical tables/aliases/parameters; it is not constant or just event count. Greedy scoring uses O(M*K*(L+1)) arithmetic work after sorting/validation. Canonical assignment checking/serialization includes O(M log M) ID sorting. Bounded search can be exponential in its small search domain, curtailed by explicit node budget; it is not globally optimal or generally polynomial. Exact integer/rational bit costs are additional.

**Verified — profiles/source:** raw allocate performs one registry validation plus one allocation. verify_allocation performs two registry validations overall plus one recomputed allocation; role_plan and each fit-membership call perform three validations plus one recomputed allocation. The original receipt generation is not reused as execution proof. A sequence generate→verify→build plan→one fit therefore entails four allocation executions and nine registry validations (sum of the observed per-operation counts). Repeating Q fit checks repeats Q full allocations, not O(1) membership-only work.

| Operation, M=1536 / K=4 / two supplied labels | allocate calls | validate_dataset calls | Greedy candidate evaluations |
|---|---|---|---|
| allocate | 1 | 1 | 6144 |
| verify | 1 | 2 | 6144 |
| role_plan | 1 | 3 | 6144 |
| one_fit_membership | 1 | 3 | 6144 |
| ten_fit_memberships | 10 | 30 | 61440 |

The same count relationships held for M=24,96,384. With 18 constructed events (15 empty-label events followed by an impossible mixed-label triangle), budgets 1/32/512/4096 each produced UNDETERMINED_BUDGET with exactly that many visited nodes; verification repeated the same budgeted search. Profiled search-function calls were budget+1 because the final call detects exhaustion without incrementing the visited receipt. No infeasibility or accepted assignment was fabricated at a budget stop.

This overhead is material when checks repeat: ten fits at M=1536 re-score 61,440 fold candidates and validate 30 registries. A verification after budget 4096 repeats 4096 visited nodes. These are operation counts, not platform-speed claims. One verification preserves the allocation-order bound with additional passes. For Q membership checks, total work includes Q repeated allocations/validations; if Q itself grows with M, that orchestration can have a higher asymptotic cost (for example Q=M multiplies the greedy work by M). It does not cause the separate simulation reporter to become quadratic, and it does not remove the allocator's potential exponential search cost.

No verification cache currently substitutes stale values. Policy digest and input validation are recomputed. Revalidating at acceptance is defensible; repeating full validation/allocation for every membership query is not mathematically necessary if a future trusted immutable verified-plan object has a sound lifetime/invalidations contract. Future options include one verified plan per immutable input version or memoization bound to complete source/policy/inner-role/code identity. Such a design must invalidate on every relevant change and preserve fail-closed behavior. It is a separate optimization/security-contract decision, not implemented here. Callers must choose practical explicit budgets and input sizes; no denial-of-service resistance is established for arbitrary valid huge requests.

## 8. Reporting time, sorting, space and preconditions

**Verified — source/history/reasoning.** At 17F the default angle lookup restarted a full interval scan for every endpoint: Theta(S²), or O(S*R) for a general report grid. The current helper keeps a single increasing index. It visits at most max(0,S−1) interval advances and R endpoints, giving O(S+R) arithmetic time. Default reporting does not call the helper and reuses the freshly computed event total. Public grids are normalized/strictly increasing; generated intervals are ordered and contiguous. Duplicate/older sensors become rejection records and do not duplicate accepted boundaries.

The report merge performs no sort. Public ARRIVAL processing adds O(N) event work and O(S+R) reporting/config traversal; OFFLINE adds O(N log N) stable time sorting. Interval creation/timer work and output/configuration copies remain linear in their list sizes. Exact arithmetic costs depend on operand bit lengths. No whole-run constant-memory or constant-bit-cost claim follows.

Fresh measurements at S=32,128,512,2048,8192 show: default extra report evaluations/advances 0; fixed grids R=S and R=4S have exactly R endpoint evaluations and S−1 advances. For S=8192/R=32768 the measured counts are 32768 report evaluations, 8191 advances and 40960 total motion calls including 8192 propagation calls. Reused-run totals 2→0→2 show no stale default total. Empty/singleton grids, in-between sensor endpoints, duplicate/older sensor inputs, invalid duplicate/unsorted/out-of-horizon report grids were explicitly challenged. Arbitrary overlapping/gapped interval lists are private-helper precondition violations and remain unvalidated there.

### H-N01 — LOW: fixed-grid auxiliary-space claim contradicted

**Contradicted — source and execution.** `src/railway_detection/synthetic/convention_b.py:283-299`, specifically line 288, uses `zip(report, report[1:])`. The slice is an additional R-element tuple, not the original retained grid or an output. Thus auxiliary helper storage is O(R) plus scalar/rational state, not O(1) extra traversal storage as claimed in `docs/generated/master_reaudit/MISSION_17G_FIVE_DEFECT_REMEDIATION_REPORT.md:73-73`. Total producer storage remains O(N+S+R) elements; the original linear-time correction is unaffected.

The isolated memory experiment preallocated a single covering interval and the report tuple before tracemalloc started; only the helper ran under measurement. Observed local CPython 3.11.15 values:

| R report intervals | Extra tuple slice bytes | Helper peak traced bytes |
|---|---|---|
| 32 | 296 | 1192 |
| 128 | 1064 | 1960 |
| 512 | 4136 | 5064 |
| 2048 | 16424 | 17352 |
| 8192 | 65576 | 66504 |

Tuple slice size grew as 40+8*R bytes locally; exact bytes are interpreter-specific. Multiple R values and direct source reasoning establish the auxiliary growth, rather than one timing result. Grid validation and configuration serialization also perform linear copies/passes. Future follow-up should correct the space description, and may replace slicing with a reviewed adjacent-pair iterator if reducing extra storage is required; no source/doc history was silently repaired in 17H.

Reporting time is acceptable for a bounded synthetic stage. Memory planning must use the actual linear storage bound and declared input limits. Private reporting must remain internal to a producer that guarantees its interval preconditions.

## 9. Isolation, static tools and untouched implementation

**Verified — source/byte comparison/runtime:** all nine Python files compile syntactically; component imports are standard-library-only, with no production loader import or component file/network/process/dynamic-code entrypoint identified. The selected pytest guards are unchanged from 17F. All six isolation cases passed as part of the 114/216 runs. Selected CLI/runner/splitter/model/decoder imports remained absent. Per-test guards operate after collection/imports, not over the whole interpreter; standard-library imports alone do not establish security. This remains Python-level cooperative test isolation, not an OS sandbox, syscall monitor or protection from arbitrary same-process code.

Audited safe source/test byte identities, unchanged before and after all executions:

| Source/test path | SHA256 |
|---|---|
| `src/railway_detection/synthetic/__init__.py` | `a269b30d6399436161dc863db33fd4dccb7d243926ea6c1fd505adabec278f02` |
| `src/railway_detection/synthetic/convention_b.py` | `654ba0d93ef05c0fa25f37c8424c0ba2dd7c4d413c98f8c48174045a2de0ee5c` |
| `src/railway_detection/synthetic/grouped_cv.py` | `dfc88ffbdff31f5db8339a5b799aa1f6fd6228efdcf775e243de8b6addc1339e` |
| `tests/synthetic_mission17d/conftest.py` | `e64acca4d8d4a390bf1c6eb07fbba3ad16827f839bba60c922a5f85793dc3438` |
| `tests/synthetic_mission17d/test_convention_b.py` | `2dfe06cb537a27f4d45cf4d2bda7d5722b25e7b935bdbca2a789e244e187f4da` |
| `tests/synthetic_mission17d/test_grouped_cv.py` | `4785409852b179154c9d454f4568127e5a1e6535ee63e14f4547d5e6b8a67e08` |
| `tests/synthetic_mission17d/test_isolation.py` | `5d9424894bb70979695114bb72b9955885b6448874f6c8eddbfddf8622c52986` |
| `tests/synthetic_mission17d/test_mission17f_regressions.py` | `4dc90466b9185a7d8a84df5ea8e6867174db551dccad948a4ae5f8fb659a8898` |
| `tests/synthetic_mission17d/test_mission17g_hardening.py` | `996e80263645cad239e3c56590ef333472554182e6234e04210f8664c3336d51` |

### H-N02 — LOW: current lint gate fails; no automatic fixes applied

**Verified — direct tool execution.** The initial module/PATH checks missed a valid executable in `.venv/bin`. Direct `.venv/bin/ruff --version` returned `ruff 0.16.3`. The following command used the existing project configuration, disabled cache writes and applied no fixes:

```sh
.venv/bin/ruff check --no-cache --output-format=json src/railway_detection/synthetic tests/synthetic_mission17d
```

Observed exit 1, stderr empty, 68 diagnostics in the JSON output. These remain unresolved; no lint pass is claimed. Exact output is retained in `/tmp/mission17h_ruff_direct.json`, and the command reproduces it at the audited source version. Current rule counts:

| Rule | Count |
|---|---|
| B023 | 8 |
| B905 | 6 |
| E501 | 46 |
| E702 | 1 |
| E731 | 3 |
| I001 | 2 |
| UP042 | 2 |

The two component sources have 22 diagnostics; the two new 17G test modules have 38; original test/conftest files have 8. A same-tool/config comparison over the seven 17F Python files via `git show` and Ruff stdin (without materializing any source files) yielded 26 diagnostics. Thus the current net count is 42 higher over nine files; not all 68 arose in 17G and a net count is not precise line-by-line attribution.

The eight B023 warnings concern the greedy cost closure at `src/railway_detection/synthetic/grouped_cv.py:511-523`. Source inspection shows it is consumed immediately by synchronous `min(..., key=cost)` before the loop advances; it is not retained as a late callback. No late-binding allocation error was demonstrated in the fresh scoring/oracle runs. B905 warnings include deliberately adjacent shifted grids; blindly enabling strict=True would change that behavior. The other diagnostics concern long lines, import order, lambda/semicolon style and str+Enum modernization. These observations explain scope but do not waive the configured lint checks. A separately authorized cleanup/review should resolve the diagnostics or explicitly justify scoped policy choices before treating lint as an acceptance gate.

Mypy still cannot analyze: no executable was found on PATH or in `.venv/bin`, and a fresh API invocation failed before analysis with `ModuleNotFoundError: No module named 'mypy.bogus_type'`. Exact attempted API arguments were `['--follow-imports=skip','--cache-dir=/tmp/mission17h_mypy_cache','src/railway_detection/synthetic']`. No passing type result is claimed. Project configuration was not changed and no dependency was installed/upgraded. Type correctness remains **Not verifiable** through Mypy here; Ruff's actual failing result is **Verified**, not an unavailable-tool disclaimer.


Raw media opened/previewed/probed/decoded/hashed 0; checkpoints/protected caches/processed data accessed 0; real inference/training/replay/evaluation 0; official splits/GT changes 0; human annotation/adjudication 0; tokens/appointments/authorization records created or consumed 0. Only safe source/docs and newly constructed objects were used. Root/legacy/protected workflows were not executed. No implementation file, test, safeguard, configuration, protocol, governance decision or historical result was modified. Only the two named 17H reports are authorized repository additions.

## 10. Remaining findings, restrictions and next action

H-N01 remains open as a low-severity space-claim/auxiliary-memory issue; H-N02 records 68 unresolved Ruff diagnostics. Retained expected-source trust, serialization-versus-verification, detached simulation result provenance, private-helper preconditions and repeated recomputation are demonstrated limitations to carry into any next contract. No new public numerical failure or full-verifier acceptance of the malformed/stale candidates was found in the executed challenge domain. This is finite evidence and does not exclude all defects.

Recommended next action: researcher review, then a separately scoped synthetic follow-up to correct the memory claim/optional slice allocation, address lint debt and define the owning caller's expected-input, result-validation, budget and interval-precondition contracts before integration. Controller/CV work is conditionally recommended only as isolated constructed-input adapter engineering after those contracts and the relevant selected policy are explicit. Human-review implementation is not recommended on the strength of these tests; real-data execution is not authorized. Do not begin Mission 18 automatically.

Delivery is exactly [this report](MISSION_17H_INDEPENDENT_VERIFICATION_REPORT.md) and [the decision record](MISSION_17H_INTEGRATION_READINESS_VERDICT.md). Review all references, numerical/count claims, scope and full staged diff; commit `docs: independently verify mission 17G remediations`, push normally, and verify local/tracking/live equality and clean tree. Actual final commit verification is supplied in the completion response, avoiding self-reference. No force/reset/clean/amend/rebase/history rewrite or broad staging occurs.

**STOP after delivery; wait for researcher review.** No implementation/test code was added or modified; the command transcripts below document ephemeral audit observations only.

## Appendix — Exact one-off audit command transcripts

Each command ran from the repository root with constructed inputs only. It writes a new temporary JSON receipt; where denial hooks are used, receipt writing follows their restoration. To rerun, choose fresh `/tmp/mission17h_*` output names so existing evidence is preserved. No test module or implementation file is created by these transcripts.

Executed command transcripts follow.

### A–D adversarial command: 65 observations

```sh
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
from dataclasses import replace, asdict, FrozenInstanceError
from fractions import Fraction as Q
from enum import Enum, IntEnum
from contextlib import ExitStack
from unittest.mock import patch
import builtins, io, os, socket, subprocess, sys, json
from pathlib import Path
from railway_detection.synthetic import grouped_cv as cv, convention_b as sim

rows=[]; io_attempts=[]
def deny(*args, **kwargs):
    io_attempts.append('denied')
    raise AssertionError('17H probe attempted component IO')
def rejected(name, fn, error=cv.InvalidInput):
    try:
        fn()
    except error as exc:
        rows.append({'case':name,'expected':'reject','observed':type(exc).__name__,'detail':str(exc),'ok':True})
    except Exception as exc:
        rows.append({'case':name,'expected':'reject','observed':type(exc).__name__,'detail':str(exc),'ok':False})
    else:
        rows.append({'case':name,'expected':'reject','observed':'ACCEPTED','ok':False})
def accepted(name, fn, boundary=False):
    try:
        ok=bool(fn())
        rows.append({'case':name,'expected':'accept' if not boundary else 'documented caller-trust limit',
                     'observed':'ACCEPTED' if ok else 'FALSE','ok':ok})
    except Exception as exc:
        rows.append({'case':name,'expected':'accept','observed':type(exc).__name__,'detail':str(exc),'ok':False})
def make(labels=(('x','y'),)*9, roles=None, identity='synthetic:h:dataset'):
    roles=(cv.DatasetRole.DEVELOPMENT_POOL,)*len(labels) if roles is None else roles
    es=[];cs=[];ss=[];aa=[]
    for i,(ls,role) in enumerate(zip(labels,roles,strict=True)):
        e=f'synthetic:h:event:{i:04}'; c=f'synthetic:h:capture:{i:04}'
        a=f'synthetic:h:asset:{i:04}'; n=f'synthetic:h:annotation:{i:04}'
        es.append(cv.PhysicalEvent(e,role,tuple(ls)))
        cs.append(cv.Capture(c,(e,)))
        ss.append(cv.Asset(a,e,'STILL',(n,),c))
        aa.append(cv.Annotation(n,a,tuple(ls),confirmed_empty=not ls))
    return cv.SyntheticDataset(identity,tuple(es),tuple(cs),tuple(ss),tuple(aa))
def plan_for(d,p):
    a=cv.allocate(d,k=p.k,required_support=p.required_support,node_budget=p.node_budget)
    tune=(next(e for e,f in a.assignments if f!=0),)
    c=cv.RoleContext(d,a,p,0,tune)
    r=cv.role_plan(d,a,expected_policy=p,outer_fold=0,validation_events=tune)
    return a,c,r
class OddStatus(str,Enum):
    GREEDY='FEASIBLE_GREEDY'
class OddFold(IntEnum):
    ZERO=0

with ExitStack() as stack:
    for owner,name in [(builtins,'open'),(io,'open'),(os,'open'),(Path,'open'),
                       (Path,'read_bytes'),(Path,'read_text'),(Path,'write_bytes'),(Path,'write_text'),
                       (socket,'socket'),(socket,'create_connection'),(subprocess,'Popen')]:
        stack.enter_context(patch.object(owner,name,deny))
    roles=(cv.DatasetRole.DEVELOPMENT_POOL,)*8+(cv.DatasetRole.RESERVED_CONTROL,)
    d=make(roles=roles); p=cv.allocation_policy(k=3,required_support=(('x',1),))
    a,context,plan=plan_for(d,p)
    accepted('A01_valid_original',lambda: cv.validate_fit_membership(plan,'BASE_MODEL_FIT',plan.training,expected_context=context) is None)
    rejected('A02_missing_context',lambda: cv.validate_fit_membership(plan,'BASE_MODEL_FIT',plan.training))
    for field,value in [('original_roles',()),('input_digest',None),('policy_digest',''),('allocation_digest','0'*64),('outer_fold',True)]:
        rejected('A03_missing_or_wrong_'+field,lambda field=field,value=value: cv.validate_fit_membership(replace(plan,**{field:value}),'BASE_MODEL_FIT',plan.training,expected_context=context))
    control=plan.reserved_controls[0]; trained=plan.training[0]
    swapped=replace(plan,training=(control,)+plan.training[1:],reserved_controls=(trained,),development=tuple(control if e==trained else e for e in plan.development))
    rejected('A04_coherent_role_swap_original_context',lambda: cv.validate_fit_membership(swapped,'BASE_MODEL_FIT',(control,),expected_context=context))
    reclassified=replace(d,events=d.events[:-1]+(replace(d.events[-1],role=cv.DatasetRole.DEVELOPMENT_POOL),))
    rejected('A05_source_only_substitution',lambda: cv.validate_fit_membership(plan,'BASE_MODEL_FIT',plan.training,expected_context=replace(context,dataset=reclassified)))
    new_a,new_context,new_plan=plan_for(reclassified,p)
    accepted('A06_replace_candidate_AND_expected_source',lambda: cv.validate_fit_membership(new_plan,'BASE_MODEL_FIT',(control,),expected_context=new_context) is None,boundary=True)
    rejected('A07_missing_original_role',lambda: cv.validate_dataset(replace(d,events=(replace(d.events[0],role=None),)+d.events[1:])))
    rejected('A08_ambiguous_alias',lambda: cv.validate_dataset(replace(d,events=(d.events[0],replace(d.events[1],aliases=(d.events[0].event_id,)))+d.events[2:])))
    rejected('A09_duplicate_source',lambda: cv.validate_dataset(replace(d,events=d.events+(d.events[0],))))
    child=cv.Asset('synthetic:h:derived',control,'DERIVATIVE',('synthetic:h:derived-ann',),parent_ids=(d.assets[-1].asset_id,),transform=cv.Transform('synthetic:h:transform','1',()))
    derived=replace(d,assets=d.assets+(child,),annotations=d.annotations+(cv.Annotation(child.annotation_ids[0],child.asset_id,('x','y')),))
    accepted('A10_valid_reserved_lineage',lambda: next(g for g in cv.validate_dataset(derived).groups if g.event_id==control).role is cv.DatasetRole.RESERVED_CONTROL)
    changed=replace(derived,assets=derived.assets[:-1]+(replace(child,event_id=d.events[0].event_id),))
    rejected('A11_altered_derivative_ancestry',lambda: cv.validate_dataset(changed))
    rejected('A12_normal_context_mutation',lambda: setattr(context,'outer_fold',1),FrozenInstanceError)
    accepted('B01_correct_policy',lambda: cv.verify_allocation(d,a,expected_policy=p))
    rejected('B02_missing_expected_policy',lambda: cv.verify_allocation(d,a))
    for value in (None,'','0'*64):
        rejected('B03_missing_policy_identity_'+repr(value),lambda value=value: cv.verify_allocation(d,replace(a,policy_digest=value),expected_policy=p))
    changed_p=cv.allocation_policy(k=3,required_support=(('x',2),))
    accepted('B04_same_profile_different_body_digest',lambda: changed_p.profile==p.profile and changed_p.digest!=p.digest)
    rejected('B05_old_receipt_new_policy',lambda: cv.verify_allocation(d,a,expected_policy=changed_p))
    changed_budget=cv.allocation_policy(k=3,required_support=(('x',1),),node_budget=17)
    rejected('B06_changed_budget_same_name',lambda: cv.verify_allocation(d,a,expected_policy=changed_budget))
    rejected('B07_copied_receipt_foreign_dataset',lambda: cv.verify_allocation(replace(d,dataset_id='synthetic:h:another'),a,expected_policy=p))
    pxy=cv.allocation_policy(k=3,required_support=(('x',1),('y',1)))
    pyx=cv.allocation_policy(k=3,required_support=(('y',1),('x',1)))
    accepted('B08_equivalent_parameter_order',lambda: pxy==pyx and pxy.digest==pyx.digest)
    rejected('B09_duplicate_support',lambda: cv.allocation_policy(k=3,required_support=(('x',1),('x',1))))
    rejected('B10_policy_mutation',lambda: setattr(p,'k',4),FrozenInstanceError)
    bad_receipts=[('receipt_dictionary',asdict(a)),('receipt_none',None)]
    for field,value in [('status',OddStatus.GREEDY),('visited_nodes',False),('visited_nodes',1.0),('greedy_choices',True),('greedy_choices',a.greedy_choices+1),('objective',(False,False,False)),('objective',(0.0,0.0,0.0)),('objective',(0,0,-1)),('assignments',(None,)),('assignments',(('synthetic:h:missing',),)),('assignments',((a.assignments[0][0],OddFold.ZERO),)+a.assignments[1:]),('assignments',a.assignments+(a.assignments[0],)),('assignments',tuple(reversed(a.assignments))),('required_support',(('x',True),)),('receipt_version','SYNTHETIC_ALLOCATION_RECEIPT_V1'),('reason','trust me'),('limitations',None)]:
        bad_receipts.append((field+'_'+repr(value),replace(a,**{field:value})))
    bad_receipts.append(('plausible_search_status',replace(a,status='FEASIBLE_SEARCH',visited_nodes=1)))
    bad_receipts.append(('different_balanced_partition',replace(a,assignments=tuple((e,(f+1)%3) for e,f in a.assignments))))
    for label,candidate in bad_receipts:
        rejected('C_'+label,lambda candidate=candidate: cv.verify_allocation(d,candidate,expected_policy=p))
    accepted('C_serialization_only_not_operation_validation',lambda: bool(replace(a,greedy_choices=a.greedy_choices+1).canonical_json()),boundary=True)
    impossible=make(labels=(('rare',),(),(),()))
    pi=cv.allocation_policy(k=2,required_support=(('rare',1),))
    ai=cv.allocate(impossible,k=2,required_support=pi.required_support)
    accepted('C_infeasible_valid_receipt_returns_FALSE',lambda: cv.verify_allocation(impossible,ai,expected_policy=pi) is False)
    rejected('C_missing_infeasibility_reason',lambda: cv.verify_allocation(impossible,replace(ai,reason=None),expected_policy=pi))
    source=[sim.SyntheticEvent('synthetic:h:t0',0,'L'),sim.SyntheticEvent('synthetic:h:t2',2000000,'L')]
    expected=sim.RunConfiguration(Q(90),Q(3),Q(3),sim.Watchdog(),'ARRIVAL',None,None)
    r=sim.CausalRunner().run(source,fixture_id='synthetic:h:run')
    accepted('D01_actual_defaults',lambda: sim.verify_run_configuration(r,expected_configuration=expected) is None and r.final_angle==30)
    explicit=sim.CausalRunner(initial_angle=90,closing_seconds=3,opening_seconds=3,watchdog=sim.Watchdog()).run(source,fixture_id='synthetic:h:run')
    accepted('D02_default_equals_explicit',lambda: r.canonical_json()==explicit.canonical_json())
    h=[replace(e,target='H') for e in source]
    h3=sim.CausalRunner().run(h,fixture_id='synthetic:h:hold')
    h6=sim.CausalRunner(closing_seconds=6).run(h,fixture_id='synthetic:h:hold')
    accepted('D03_same_trajectory_different_provenance',lambda: h3.final_angle==h6.final_angle==90 and h3.configuration_digest!=h6.configuration_digest)
    rejected('D04_missing_config',lambda: sim.verify_run_configuration(replace(r,configuration=None),expected_configuration=expected),ValueError)
    rejected('D05_missing_expected',lambda: sim.verify_run_configuration(r),ValueError)
    other=replace(expected,closing_seconds=Q(6))
    detached=replace(r,configuration=other,configuration_digest=other.digest)
    rejected('D06_replaced_config_original_expected',lambda: sim.verify_run_configuration(detached,expected_configuration=expected),ValueError)
    accepted('D07_self_serialization_does_not_prove_trajectory',lambda: bool(detached.canonical_json()) and detached.final_angle==30 and other.closing_seconds==6,boundary=True)
    fabricated=replace(r,final_angle=Q(999),endpoint_seconds=Q(999),report_endpoint_seconds=Q(999))
    accepted('D08_config_check_is_not_result_check',lambda: sim.verify_run_configuration(fabricated,expected_configuration=expected) is None,boundary=True)
    rejected('D09_post_run_config_assignment',lambda: setattr(r.configuration,'closing_seconds',Q(6)),FrozenInstanceError)
    runner=sim.CausalRunner(); runner._configuration=other
    after_init=runner.run(source,fixture_id='synthetic:h:reconfigured')
    accepted('D10_change_before_run',lambda: after_init.configuration==other and after_init.final_angle==60)
    runner=sim.CausalRunner(); changed={'done':False}
    def during(frame,event,arg):
        if event=='call' and frame.f_code is sim._motion.__code__ and not changed['done']:
            changed['done']=True; runner._configuration=other
    prior=sys.getprofile()
    try:
        sys.setprofile(during)
        during_result=runner.run(source,fixture_id='synthetic:h:during',report_times=(0,1000000,2000000))
    finally:
        sys.setprofile(prior)
    accepted('D11_change_during_run_snapshot',lambda: changed['done'] and during_result.configuration.closing_seconds==3 and during_result.final_angle==30)
    accepted('D12_later_run_uses_new_config',lambda: runner.run(source,fixture_id='synthetic:h:later').final_angle==60 and during_result.configuration.closing_seconds==3)
    accepted('isolation_modules_absent',lambda: not any(m in sys.modules for m in ('railway_detection.cli.main','railway_detection.simulation.runner','railway_detection.data.split','torch','cv2','ultralytics')))

out={'probe_cases':len(rows),'unexpected':sum(not r['ok'] for r in rows),'io_attempts':len(io_attempts),'cases':rows}
p=Path('/tmp/mission17h_adversarial.json'); assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'probe_cases':len(rows),'unexpected':[r for r in rows if not r['ok']],'io_attempts':len(io_attempts),'trust_limits':[r for r in rows if r['expected']=='documented caller-trust limit']},indent=2))
PY
```

### Reporting/cost command: operation profiles, memory and edge observations

```sh
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
from pathlib import Path
from dataclasses import replace
from fractions import Fraction as Q
from collections import Counter
from contextlib import ExitStack
from unittest.mock import patch
import ast,builtins,io,os,socket,subprocess,sys,json,tracemalloc,gc
from railway_detection.synthetic import convention_b as sim, grouped_cv as cv

source=Path(sim.__file__).read_text();tree=ast.parse(source)
helper=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_report_endpoint_seconds')
advance_line=next(n.lineno for n in ast.walk(helper) if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='index')
scaling=[];space=[];overhead=[];edges=[];attempts=[]
def deny(*a,**kw):
    attempts.append(True);raise AssertionError('17H measurement attempted IO')
def make(labels):
    events=[];captures=[];assets=[];anns=[]
    for i,labels_i in enumerate(labels):
        e=f'synthetic:hp:e:{i:05}';c=f'synthetic:hp:c:{i:05}';a=f'synthetic:hp:a:{i:05}';n=f'synthetic:hp:n:{i:05}'
        events.append(cv.PhysicalEvent(e,cv.DatasetRole.DEVELOPMENT_POOL,tuple(labels_i)))
        captures.append(cv.Capture(c,(e,)))
        assets.append(cv.Asset(a,e,'STILL',(n,),c))
        anns.append(cv.Annotation(n,a,tuple(labels_i),confirmed_empty=not labels_i))
    return cv.SyntheticDataset('synthetic:hp:dataset',tuple(events),tuple(captures),tuple(assets),tuple(anns))
def measured_cv(fn):
    calls=Counter();prior=sys.getprofile()
    def profile(frame,event,arg):
        if event=='call' and frame.f_code.co_filename==cv.__file__ and frame.f_code.co_name in ('allocate','validate_dataset','search','cost'):
            calls[frame.f_code.co_name]+=1
    try:
        sys.setprofile(profile);value=fn()
    finally:
        sys.setprofile(prior)
    return value,dict(calls)

with ExitStack() as guards:
    for owner,name in [(builtins,'open'),(io,'open'),(os,'open'),(Path,'open'),(Path,'read_bytes'),(Path,'read_text'),(Path,'write_bytes'),(Path,'write_text'),(socket,'socket'),(socket,'create_connection'),(subprocess,'Popen')]:
        guards.enter_context(patch.object(owner,name,deny))
    for n in (32,128,512,2048,8192):
        for factor in (None,1,4):
            events=[sim.SyntheticEvent(f'synthetic:hp:t:{i}',i*10000,'L') for i in range(n+1)]
            report=None if factor is None else tuple(range(0,n*10000+1,10000//factor))
            counts=Counter();prior_trace=sys.gettrace();prior_profile=sys.getprofile()
            def trace(frame,event,arg):
                if frame.f_code is sim._report_endpoint_seconds.__code__ and event=='line' and frame.f_lineno==advance_line:
                    counts['interval_advances']+=1
                return trace
            def profile(frame,event,arg):
                if event=='call' and frame.f_code is sim._report_endpoint_seconds.__code__:counts['report_helper_calls']+=1
                if event=='call' and frame.f_code is sim._motion.__code__:
                    counts['motion_calls']+=1
                    if frame.f_back.f_code is sim._report_endpoint_seconds.__code__:counts['report_endpoint_evaluations']+=1
            try:
                sys.settrace(trace);sys.setprofile(profile)
                r=sim.CausalRunner().run(events,fixture_id='synthetic:hp:scaling',report_times=report)
            finally:
                sys.settrace(prior_trace);sys.setprofile(prior_profile)
            grid=r.report_grid_us
            expected=sum((Q(b-a,1000000) for a,b in zip(grid,grid[1:]) if b>=1500000),Q(0))
            assert r.report_endpoint_seconds==expected
            assert r.continuous_seconds==max(Q(0),Q(n,100)-Q(3,2))
            if factor is None:
                assert counts['report_helper_calls']==counts['interval_advances']==counts['report_endpoint_evaluations']==0
                assert counts['motion_calls']==n
            else:
                assert counts['interval_advances']==n-1
                assert counts['report_endpoint_evaluations']==n*factor
                assert counts['motion_calls']==n+n*factor
            scaling.append({'S':n,'R':len(grid)-1,'mode':'default' if factor is None else 'fixed','counts':dict(counts)})
    # Measure only the private reporting operation, with all inputs already allocated.
    # This distinguishes extra report[1:] memory from the original stored grid.
    for count in (32,128,512,2048,8192):
        report=tuple(range(count+1))
        intervals=[sim.Interval(0,count,sim.Command.HOLD,0,'synthetic:hp:origin',Q(90),Q(90),False,Q(0),'SENSOR')]
        gc.collect();tracemalloc.start()
        value=sim._report_endpoint_seconds(intervals,report,Q(30),Q(30))
        current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        assert value==0
        space.append({'R':count,'helper_peak_traced_bytes':peak,'extra_slice_bytes':sys.getsizeof(report[1:])})
    # Stale totals, duplicate/older arrivals, partially overlapping grids and singletons.
    runner=sim.CausalRunner()
    for commands,expected in [('LL',Q(2)),('HH',Q(0)),('LL',Q(2))]:
        r=runner.run([sim.SyntheticEvent('synthetic:hp:a',0,commands[0]),sim.SyntheticEvent('synthetic:hp:b',2000000,commands[1])],fixture_id='synthetic:hp:reset')
        assert r.report_endpoint_seconds==expected
    edges.append({'case':'reused_runner_no_stale_total','durations':['2','0','2'],'ok':True})
    for label,events,grid,status,expected in [
        ('empty',[],None,'EMPTY',Q(0)),
        ('singleton',[sim.SyntheticEvent('synthetic:hp:one',7,'H')],(7,),'COMPLETE',Q(0)),
        ('report_between_sensor_keys',[sim.SyntheticEvent('synthetic:hp:a',0,'L'),sim.SyntheticEvent('synthetic:hp:b',2000000,'L')],(0,100000,1700000,2000000),'COMPLETE',Q('1.9')),
        ('duplicate_and_older',[sim.SyntheticEvent('synthetic:hp:a',0,'L'),sim.SyntheticEvent('synthetic:hp:b',1000000,'L'),sim.SyntheticEvent('synthetic:hp:c',1000000,'R'),sim.SyntheticEvent('synthetic:hp:d',500000,'R'),sim.SyntheticEvent('synthetic:hp:e',2000000,'L')],(0,500000,2000000),'COMPLETE',Q('1.5')),
    ]:
        r=runner.run(events,fixture_id='synthetic:hp:edge',report_times=grid)
        assert r.status==status and r.report_endpoint_seconds==expected
        edges.append({'case':label,'status':r.status,'report_duration':str(r.report_endpoint_seconds),'rejections':len(r.rejections),'ok':True})
    source=[sim.SyntheticEvent('synthetic:hp:a',1000000,'L'),sim.SyntheticEvent('synthetic:hp:b',2000000,'L')]
    for grid in [(),(1000000,1000000),(1000000,500000,2000000),(0,2000000),(1000000,3000000),(3000000,4000000)]:
        try:runner.run(source,fixture_id='synthetic:hp:bad-grid',report_times=grid)
        except ValueError:edges.append({'case':'invalid_report_grid','grid':grid,'observed':'ValueError','ok':True})
        else:raise AssertionError(('bad grid accepted',grid))
    for n in (24,96,384,1536):
        d=make((('x','y'),)*n);p=cv.allocation_policy(k=4)
        a,calls=measured_cv(lambda:cv.allocate(d,k=4));overhead.append({'M':n,'operation':'allocate','calls':calls})
        ok,calls=measured_cv(lambda:cv.verify_allocation(d,a,expected_policy=p));assert ok
        overhead.append({'M':n,'operation':'verify','calls':calls})
        tune=(next(e for e,f in a.assignments if f!=0),)
        plan,calls=measured_cv(lambda:cv.role_plan(d,a,expected_policy=p,outer_fold=0,validation_events=tune))
        overhead.append({'M':n,'operation':'role_plan','calls':calls})
        context=cv.RoleContext(d,a,p,0,tune)
        _,calls=measured_cv(lambda:cv.validate_fit_membership(plan,'BASE_MODEL_FIT',plan.training,expected_context=context))
        overhead.append({'M':n,'operation':'one_fit_membership','calls':calls})
        def ten():
            for _ in range(10):cv.validate_fit_membership(plan,'BASE_MODEL_FIT',plan.training,expected_context=context)
        _,calls=measured_cv(ten);overhead.append({'M':n,'operation':'ten_fit_memberships','calls':calls})
    labels=((),)*15+(('a','b'),('a','c'),('b','c'))
    d=make(labels);support=(('a',1),('b',1),('c',1))
    for budget in (1,32,512,4096):
        p=cv.allocation_policy(k=2,required_support=support,node_budget=budget)
        a,calls=measured_cv(lambda:cv.allocate(d,k=2,required_support=support,node_budget=budget))
        assert a.status=='UNDETERMINED_BUDGET' and a.visited_nodes==budget
        overhead.append({'M':18,'operation':'budget_allocate','budget':budget,'visited_nodes':a.visited_nodes,'calls':calls})
        valid,calls=measured_cv(lambda:cv.verify_allocation(d,a,expected_policy=p));assert valid is False
        overhead.append({'M':18,'operation':'budget_verify','budget':budget,'visited_nodes':a.visited_nodes,'calls':calls})

out={'scaling':scaling,'report_space':space,'edge_cases':edges,'receipt_overhead':overhead,'io_attempts':len(attempts)}
p=Path('/tmp/mission17h_cost_measurements.json');assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
PY
```

### Supplementary source/private-helper boundary command: six observations

```sh
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
from dataclasses import replace
from fractions import Fraction as Q
from enum import Enum,IntEnum
import json
from pathlib import Path
from railway_detection.synthetic import grouped_cv as c, convention_b as s

def make():
    ev=[];ca=[];assets=[];anns=[]
    for i in range(6):
        e=f'synthetic:he:e:{i}';cap=f'synthetic:he:c:{i}';a=f'synthetic:he:a:{i}';n=f'synthetic:he:n:{i}'
        ev.append(c.PhysicalEvent(e,c.DatasetRole.DEVELOPMENT_POOL,('x',)))
        ca.append(c.Capture(cap,(e,)));assets.append(c.Asset(a,e,'STILL',(n,),cap));anns.append(c.Annotation(n,a,('x',)))
    return c.SyntheticDataset('synthetic:he:dataset',tuple(ev),tuple(ca),tuple(assets),tuple(anns))
def outcome(label,fn):
    try:fn()
    except Exception as ex:return {'case':label,'outcome':type(ex).__name__,'detail':str(ex)}
    return {'case':label,'outcome':'ACCEPTED'}
rows=[];d=make();p=c.allocation_policy(k=3);a=c.allocate(d,k=3)
tune=(next(e for e,f in a.assignments if f!=0),)
context=c.RoleContext(d,a,p,0,tune)
plan=c.role_plan(d,a,expected_policy=p,outer_fold=0,validation_events=tune)
child=c.Asset('synthetic:he:child',d.events[0].event_id,'DERIVATIVE',('synthetic:he:child-ann',),parent_ids=(d.assets[0].asset_id,),transform=c.Transform('synthetic:he:transform','1',()))
d2=replace(d,assets=d.assets+(child,),annotations=d.annotations+(c.Annotation(child.annotation_ids[0],child.asset_id,('x',)),))
for label,parents in [('A13_missing_parent',()),('A14_orphan_parent',('synthetic:he:missing',))]:
    bad=replace(d2,assets=d2.assets[:-1]+(replace(child,parent_ids=parents),))
    rows.append(outcome(label,lambda bad=bad:c.validate_dataset(bad)))
changed=replace(d,version='2');context.__dict__['dataset']=changed
rows.append(outcome('A15_bypass_frozen_context_assignment_still_digest_checked',lambda:c.validate_fit_membership(plan,'BASE_MODEL_FIT',plan.training,expected_context=context)))
p.__dict__['k']=2
rows.append(outcome('B11_bypass_frozen_policy_assignment_still_content_checked',lambda:c.verify_allocation(d,a,expected_policy=p)))
# Private helper preconditions: public run() always produces contiguous ordered intervals.
def interval(a,b,q):return s.Interval(a,b,s.Command.HOLD,a,'synthetic:he:origin',Q(q),Q(q),q<=45,Q(b-a,1000000)*int(q<=45),'SENSOR')
for label,intervals in [('E_private_gap',[interval(0,1000000,90),interval(2000000,3000000,0)]),('E_private_overlap',[interval(0,3000000,90),interval(1000000,3000000,0)])]:
    value=s._report_endpoint_seconds(intervals,(0,3000000),Q(30),Q(30))
    rows.append({'case':label,'outcome':'ACCEPTED_PRIVATE_INPUT','report_seconds':str(value)})
assert all(r['outcome']=='InvalidInput' for r in rows[:4])
out=Path('/tmp/mission17h_boundary_experiments.json');assert not out.exists();out.write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
PY
```
