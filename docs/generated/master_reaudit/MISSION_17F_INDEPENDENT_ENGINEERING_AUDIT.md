# Mission 17F — Independent engineering audit

Date: 2026-11-04, America/New_York. Freshly verified baseline: `8221e96f8de48d995f4397a7e29255cdc8ec50f9`; branch `main`. Mission 17F authorizes source/metadata inspection, isolated synthetic audit tests, these five reports and normal exact-path Git delivery only. No implementation change or protected operation is authorized by this report.

**Disposition: the 114-test claim is reproduced; the isolated algorithms have substantial fresh supporting evidence, but the interfaces are NOT READY for research integration.** Five findings require resolution or an explicitly justified, tested contract before dependent integration. No incorrect actuator duration or false infeasibility was found in the audited synthetic domain. This is bounded evidence, not a proof over every input, deployed security acceptance or scientific independence.

The same assistant prepared the prior implementation and reports. This audit uses fresh source inspection, independent equations, newly constructed adversarial fixtures and an independently written small exhaustive oracle; it is not independent human/institutional review or railway safety certification. Prior narratives were treated as claims to check. No sub-agent or external reviewer was used.

Companions: [engineering audit](MISSION_17F_INDEPENDENT_ENGINEERING_AUDIT.md), [controller plan](MISSION_17F_CONVENTION_B_CONTROLLER_INTEGRATION_PLAN.md), [CV/OOF plan](MISSION_17F_CV_PROVENANCE_AND_OOF_IMPLEMENTATION_PLAN.md), [human/security readiness](MISSION_17F_HUMAN_REVIEW_SECURITY_READINESS.md), [gate register](MISSION_17F_IMPLEMENTATION_GATE_REGISTER.md).

## 1. Baseline and preservation

Initial location was `/Users/sayemuddin/Desktop/Train_automation`, branch main, clean including untracked files. Local HEAD, tracking origin/main and live `git ls-remote origin refs/heads/main` all returned the baseline above. Although the prompt warned not to assume that hash, fresh verification found it still was the latest delivered state. It was not used as a reset target. No divergence, preexisting 17F files or work to recover was found.

| Verified delivery | Actual commit | Added files |
|---|---|---|
| 17C-4 | `2165f8633827af477b0ab761013dfa82c8451e78` | Five specifications |
| 17D | `fbc60aa1e54f7fa69c824e6a73d2d52e3c7a1375` | Three package files, four test files, one report |
| 17E | `5809a08cb19aadfa0be3bb0e24abc93192159489` | Six blueprints |
| Final overnight report | `8221e96f8de48d995f4397a7e29255cdc8ec50f9` | One final report |

The chain starts after C3 `a809fa853e160161cf427a5b84ad96ba400fa92f`. All seven 17D Python files were read in full; all six 17E documents were inspected. Relevant actual controller, runner, gate, collector, manifest, split, training, cache provenance, leakage/preflight and guard/promotion sources were inspected as text. Safe existing metadata was read without following its resource paths. Production modules were not executed. All preexisting tracked bytes, including historical tests/results/protocol/governance, remain unchanged.

## 2. Findings ordered by integration impact

Severity describes risk of relying on the interface in a future research pipeline, not an observed protected-data incident. F17-01/02 are missing context contracts already outside the documented full trusted-registry scope; F17-03 is a concrete receipt-validation defect. No result below demonstrates that `allocate` itself returns a partition violating its own declared support policy.

| ID / severity | Reproduced evidence and consequence | Required disposition before reliance |
|---|---|---|
| F17-01 HIGH: role plan has no original registry binding | A coherent exchange of a reserved control and training event, with the development union updated, passes `validate_fit_membership`. RolePlan carries no dataset/version/digest/outer-assignment reference. Structural disjointness cannot establish original eligibility. | Accept a trusted expected registry/outer plan and independently reconstruct exact roles at verification; reject coherent substitution and foreign-plan reuse. Do not treat caller-created RolePlan as a scientific policy authority. |
| F17-02 HIGH: allocation verification lacks expected request | Strong and weak support requests for the same corpus share input_digest. A weak candidate with both required-r events in one fold passes verification because the receipt declares no r requirement. There is no expected-policy argument. | Bind corpus AND expected K/support/profile/objective/role-policy/limits; compare trusted expected request separately from candidate fields. Current verifier establishes validity under the candidate's own policy only. |
| F17-03 MEDIUM: receipt numeric/work validation incomplete | For an otherwise valid zero-objective allocation, objective `(False,False,False)` or `(0.0,0.0,0.0)`, negative greedy_choices, and FEASIBLE_SEARCH with visited_nodes=0 are all accepted. Equality with integer zero masks wrong types; some receipt counters/status relationships are unchecked. | Closed typed receipt; exact ints excluding bool, nonnegative counters and valid status/work relationships. Recompute objective and independently distinguish partition validity from execution provenance. |
| F17-04 MEDIUM: simulation log omits configuration | Two H commands at 0 and 1s produce identical canonical output under closing time 3s vs 6s; likewise NONE vs a scheduled watchdog due after horizon. Rates and watchdog settings are absent from RunResult. | Bind full model/clock/latency/watchdog/input/config/code identity in a versioned run record. Determinism is present, but current serialization alone is not a complete reproducibility recipe. |
| F17-05 MEDIUM: default reporting is quadratic | N intervals on the default event report grid cause N(N+1)/2 interval comparisons in angle_at: N=16/32/64/128 gives 136/528/2080/8256. Exact values remain correct. | Reuse event endpoint total on the default grid; use a monotone merge or indexed lookup for explicit grids. Preserve all estimator semantics and add operation-count acceptance before large replay integration. |

Source evidence: `src/railway_detection/synthetic/grouped_cv.py:576-667` (F17-01); `src/railway_detection/synthetic/grouped_cv.py:330-350` and `src/railway_detection/synthetic/grouped_cv.py:529-573` (F17-02/03); `src/railway_detection/synthetic/convention_b.py:135-171` (F17-04); `src/railway_detection/synthetic/convention_b.py:231-262` (F17-05).

Six strict expected-failure tests demonstrate the two context gaps and four malformed receipt variants. They are **six unmet rejection expectations**, not six accepted features, ordinary skips or fixes. The configurations and quadratic scans are passing characterization tests of limitations, not evidence those limitations are desirable. The full harness is preserved below for review/reproduction.

## 3. Convention B: derivation and boundary audit

Let q be angle at an accepted boundary, d the subsequent duration, v_down=90/closing_seconds and v_up=90/opening_seconds. LOWER yields max(0,q−v_down*d); RAISE yields min(90,q+v_up*d); HOLD yields q. The previous command propagates first, then the new command issues at the current boundary. Origin issues without motion. Thus default 90°, 3s closing and 0.2s active LOWER gives 84°; H@0 followed by L@0.2 leaves 90° at 0.2, then 84° at 0.4. These are commanded actuator examples; actual controller confirmation/dwell is separate.

For b(q)=1 exactly when q≤45, D_E_event=Σ d_i*b(q_i). D_C is the measure of time with q(t)≤45. A lowering segment above 45 contributes max(0,d−(q−45)/v_down), otherwise d; a raising segment starting at/below 45 contributes min(d,max(0,(45−q)/v_up)), otherwise zero. HOLD contributes d*b(q). Clipping at 0/90 does not change these threshold formulas. A single equality instant has zero integral measure, whereas HOLD at 45 contributes its full duration. Source: `src/railway_detection/synthetic/convention_b.py:174-185`.

The new oracle partitions each linear segment at independent 0/45/90 crossing times and sums subinterval lengths whose midpoint is blocked. Across 200 fresh deterministic irregular/asymmetric trajectories, initial angles include 45±0.0000001, exactly 45 and rational 1/7; final angle, D_E and D_C all match. This avoids calling the implementation's motion helper or copying its threshold formula.

Endpoint duration depends on reporting boundaries. With initial 90, LOWER and horizon 2s, event grid[0,2] gives D_E=2; adding a no-op event at 1 yields grid[0,1,2], D_E=1. Both end at 30° and have D_C=0.5. A fixed report grid preserves its own endpoint estimator across event subdivision. No endpoint estimate is the physical train occupancy measure. Existing subdivision tests were freshly rerun: `tests/synthetic_mission17d/test_convention_b.py:168-176`.

| Area | Actual behavior / checked boundary | Remaining limit |
|---|---|---|
| Numeric timestamps | Exact nonnegative integer microseconds or grid-aligned decimal seconds; bool, float, missing, negative, NaN/infinity/off-grid reject. Explicit float adapter uses repr without rounding. | Ordinary generated float `3*0.2` rejects while literal 0.2 imports. Future clock migration must resolve this explicitly; rejection is consistent with SC02. |
| Angles / threshold | Exact rational dynamics and strict internal≤45; no epsilon or display rounding. Positive asymmetric durations supported. | Legacy gate clamps durations to≥0.1s and uses additional float state thresholds. No automatic model equivalence outside a selected shared profile. |
| ARRIVAL | Preserves arrival order; duplicate/older timestamps log rejection without state/command advancement. Reused accepted IDs and invalid encountered input stop as INCOMPLETE. | A rejected late arrival cannot reset a watchdog generation. No claim of actual-controller rejection-record parity. |
| OFFLINE | Prevalidates whole input, stable sorts(time,index), records reordering; invalid input has no accepted prefix. | Not a replay of arrival fault chronology. Invalid command beyond a cutoff may invalidate OFFLINE while ARRIVAL stops before encountering it; confirmed by fresh fixture. |
| Horizon / partial | Empty/single/origin/cutoff-before/inside/after behavior explicit; no hidden pre-origin duration. Future sensor cannot issue before cutoff. | Invalid prefix at 1s after lowering retains q=60, horizon 1s and INCOMPLETE with no certified fixed-report total. Consumers must reject incomplete results for complete-run claims. |
| Reporting | Event endpoints, model continuous integral and explicit report-grid endpoint total remain separately named; strict grid spans origin/horizon. | F17-05 performance and F17-04 config provenance remain unresolved. |
| Watchdogs | NONE default; scheduled one-shot generation or detect-on-arrival; sensor-first equality; old command integrates before response; cutoff may fire timer without post-cutoff motion. | Optional profiles are engineering parameters, not adopted controller safety policy. Fresh older-arrival test gives scheduled 84° vs detect 90° at 3.2s with last accepted sensor 1s/timeout 2s. |
| Determinism | Exact arithmetic, stable sort and canonical output; existing 100-repeat test passes freshly. | Identical output need not identify original configuration (F17-04); mutable runner configuration must not be shared across concurrent runs without a future contract. |

References: `src/railway_detection/synthetic/convention_b.py:30-100`; `src/railway_detection/synthetic/convention_b.py:204-352`; `tests/synthetic_mission17d/test_convention_b.py:42-80`; `tests/synthetic_mission17d/test_convention_b.py:193-258`.

Historical A compatibility is conditional. On a uniform grid h, identical command stream/dynamics/origin/predicate and F(q0,u0,h)=q0 imply B_k=A_(k−1) by induction. Therefore D_E_B−D_E_A=h*(b(A0)−b(A_N)) by telescoping. Multiple episodes and common asymmetric rates preserve this identity; active initial LOWER, irregular/partial grids, changed feedback or changed commands need not. In general compare Σd_i*(b(B_i)−b(A_i)) directly. No universal −h correction applies to Table 11 or D_C. Fresh original tests include the boundary identity and counterexamples. Historical runner/results were not modified or executed.

## 4. Grouped CV: identity, mathematics and limits

The validator resolves exact synthetic canonical-event aliases, checks captures and source camera/crossing/session metadata (including explicit unknown reasons), original/annotation joins, transform parameter identity, PTS/timebase and single-event derivative DAGs. Orphans, cycles, ambiguous aliases, inconsistent labels, duplicate IDs and cross-event declared content identity reject. All supplied views/derivatives of a canonical pass are one group; multiple passes in one recording are not silently merged. Reserved calibration/control/case/final roles are excluded from development allocation. Every ungrouped fallback request rejects. Sources: `src/railway_detection/synthetic/grouped_cv.py:130-350`.

These checks certify internal metadata consistency, not the truth of supplied physical identity. content_identity may be absent and exact identity is caller supplied; there is no near-duplicate evidence resolver, capture authenticity or learned-exposure proof. Known near-duplicate uncertainty therefore remains a blocker to independent scientific claims under CVL04. Session/site correlation is not removed merely by event disjointness; any additional cohesion policy needs explicit scientific selection. The synthetic namespace is not authentication.

For a count vector x across K folds, Σ(K*x_f−T)^2=K²Σx_f²−K*T² with T=Σx_f. Adding δ to fold f updates Σx² by 2*x_f*δ+δ². This establishes the implemented sufficient-statistics score equivalence to complete recomputation. A fresh dense oracle independently recomputed all candidate prefix objectives for 50 constructed inputs and obtained identical assignments/objectives. Cost is O(M*K*(L+1)) arithmetic operations after metadata validation/sorting; it is not a constant-bit-cost or whole-pipeline wall-clock bound. Source: `src/railway_detection/synthetic/grouped_cv.py:382-487`.

Required support counts≥K*m and M≥K are necessary, not sufficient. The bounded search prunes only impossible empty-fold counts or missing-label capacity. First-use fold-label symmetry removes equivalent permutations because all fold constraints are identical; it would not be sound unchanged for future fold-specific rules. It searches canonical assignments, returns first feasible, and only claims exhaustive infeasibility after finishing all canonical branches. Node budget counts prefixes including root; a budget/size stop returns no accepted assignment. Per-node support work and exact integer bit costs remain additional costs. Source: `src/railway_detection/synthetic/grouped_cv.py:492-526`.

The fresh oracle enumerated all label masks from {empty,a,b,ab}, M=2…5 and K=2…min(M,3), requiring a,b in each fold: **2,704 inputs**. Independent exhaustive K^M assignments agreed with every feasible/infeasible classification at budget 10,000. No false INFEASIBLE or unexpected UNDETERMINED occurred in that finite domain. This supplements, not replaces, reasoning about pruning. The existing 1,315-event greedy case and K>32 case also passed; no real corpus was used in either test suite.

Feasible inputs CAN remain undetermined, by design. Four ordered equal-size events with labels `{r,a1,a2}`, `{b}`, `{a1,a2,b}`, `{r}` and K=2/required r=1 have a feasible assignment [0,0,1,1]. Greedy places both r events in fold 0. Budget 1 yields UNDETERMINED_BUDGET. Append 16 empty-label events and the same first-four witness remains feasible, yet the failed greedy candidate at M=20 yields UNDETERMINED_SIZE. Both statuses are honest lack of a solution within the chosen policy; neither means infeasible or accepts a split. No global optimality, complete large-corpus feasibility or full nested-plan guarantee exists.

Role construction correctly derives the chosen outer complement and explicit inner subsets when called with valid original inputs. Fit-membership operations distinguish training, tuning, final refit and reserved calibration; unverified INNER_OOF calibration denies. F17-01/02 limit reuse of detached records, and full fitted-artifact/initialization/selection/cache lineage remains deferred. Source: `src/railway_detection/synthetic/grouped_cv.py:590-667`. The existing tests covered overlapping role forgeries and altered objective values, but missed coherent role replacement, expected-policy substitution and equal-valued wrong numeric types: `tests/synthetic_mission17d/test_grouped_cv.py:246-316`.

## 5. Actual execution evidence

Exact 17D report command, executed freshly from repository root:

```sh
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest \
  --confcutdir=tests/synthetic_mission17d -p no:cacheprovider \
  --import-mode=importlib tests/synthetic_mission17d -q \
  --junitxml=/tmp/mission17d_final.xml
```

Observed: **114 passed in 0.43s**, exit 0; JUnit 70 simulation / 38 CV / 6 isolation, zero failures/errors/skips, Python 3.11.15. Any preexisting XML was preserved as `/tmp/mission17f_preexisting_17d_final.xml`; fresh receipt is `/tmp/mission17f_exact_test_receipt.json`, fresh XML copy `/tmp/mission17f_exact_17d_junit.xml`. These temporary paths are local evidence, not additional repository deliverables.

Additional exact command (stdout/stderr redirected to `/tmp/mission17f_additional_console.txt`):

```sh
PYTHONPATH=/Users/sayemuddin/Desktop/Train_automation/src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -c /tmp/mission17f_audit/pytest.ini --confcutdir=/tmp/mission17f_audit --import-mode=importlib -p no:cacheprovider /tmp/mission17f_audit -q --tb=short --junitxml=/tmp/mission17f_additional.xml > /tmp/mission17f_additional_console.txt 2>&1
```

Observed: **16 passed, 6 xfailed in 3.02s**, exit 0. JUnit encodes the six expected failures as skipped entries of type pytest.xfail; they are explicitly unmet rejection checks, not acceptance passes. No unexpected failure/error or XPASS occurred. The 22 collected tests include parameterized witnesses; the 200/2,704/50 oracle iterations are subcases, not extra pytest case counts. No source or committed test was changed to obtain results. The strict xfail markers and expected rejection assertions were present before this run; future repair must convert them into ordinary passing negative tests. Durations are local run metadata, not performance certification.

To ensure the xfail marks did not conceal fixture errors or unrelated exceptions, the six rejection witnesses were then run with expected-failure handling disabled:

```sh
PYTHONPATH=/Users/sayemuddin/Desktop/Train_automation/src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -c /tmp/mission17f_audit/pytest.ini --confcutdir=/tmp/mission17f_audit --import-mode=importlib -p no:cacheprovider /tmp/mission17f_audit -q --runxfail -k 'context_bound or receipt_validator' --tb=short --junitxml=/tmp/mission17f_rejection_witnesses.xml > /tmp/mission17f_rejection_witnesses_console.txt 2>&1
```

Observed: **6 failed, 16 deselected in 0.14s**, exit 1. Every failure is exactly `Failed: DID NOT RAISE InvalidInput` at the required rejection assertion, with zero errors. These are the same six witnesses, not six new defects or six additional accepted tests. The nonzero result is deliberately preserved as audit evidence; no oracle was weakened and no source fix was made. The harness session hook reports only the current invocation, so its observation JSON is replaced by this final witness-only run; the original full-run console/JUnit and embedded harness retain the full-run evidence.

All seven source/test SHA256 values before and after execution matched the fresh receipt and remain unchanged. The table below identifies safe code/test bytes only; no resource content was hashed.

| Path | SHA256 |
|---|---|
| `src/railway_detection/synthetic/__init__.py` | `a269b30d6399436161dc863db33fd4dccb7d243926ea6c1fd505adabec278f02` |
| `src/railway_detection/synthetic/convention_b.py` | `09d2756055484eb446794aaa719c7750968b5b1536415def5a0ed4d37eee8488` |
| `src/railway_detection/synthetic/grouped_cv.py` | `ec97aa858694542304c9f339e552dd758af5058ce3a08f2964671181d6bd8456` |
| `tests/synthetic_mission17d/conftest.py` | `e64acca4d8d4a390bf1c6eb07fbba3ad16827f839bba60c922a5f85793dc3438` |
| `tests/synthetic_mission17d/test_convention_b.py` | `2dfe06cb537a27f4d45cf4d2bda7d5722b25e7b935bdbca2a789e244e187f4da` |
| `tests/synthetic_mission17d/test_grouped_cv.py` | `582d4858e073a08953ea8b930f8bb047a6f492f5690bdd12bc0c66cff7649ac7` |
| `tests/synthetic_mission17d/test_isolation.py` | `5d9424894bb70979695114bb72b9955885b6448874f6c8eddbfddf8622c52986` |

## 6. Isolation and scope account

Fresh AST/syntax inspection covered all seven Python files. The components import only standard-library modules and expose constructed-object computation/canonical strings, with no file/network/process/dynamic-code entrypoints identified in the inspected source. A first mechanical scan incorrectly flagged `re.compile` as Python dynamic-code compilation; inspection identified regex construction and the corrected qualified-call scan passed. This tooling false positive did not change code, expected feature results or safety boundaries.

Both suites deny selected Python open/Path/socket/Popen operations during test bodies. Imports/pytest/JUnit and audit-receipt writing occur outside those guards. The isolation case confirms selected production/model modules are absent. This is scoped Python test isolation, **not an OS sandbox**, exhaustive syscall monitoring or a guarantee against malicious code. Standard-library-only does not by itself prove isolation. Existing production media_guard itself discloses software-only limits: `src/railway_detection/safety/media_guard.py:48-54`; test boundaries: `tests/synthetic_mission17d/conftest.py:28-37`, `tests/synthetic_mission17d/test_isolation.py:12-27`.

Actual activity counts: raw media opened/previewed/decoded/hashed 0; production checkpoints accessed 0; protected caches accessed 0; real inference/replay/training/evaluation 0; model/preprocessor/calibrator fits 0; official split generation 0; human annotation/adjudication 0/0; GT promotion 0; token issuance/consumption 0/0; appointments/allowlist changes 0; protocol promotion/camera-scope amendments/RD changes 0; researcher scientific/governance approvals created 0. Safe source/docs and existing metadata JSON were read; constructed in-memory synthetic allocations are the only new allocations. Legacy/root suites, production controller, resource loaders and training dry-runs were not executed. No OS-level sandbox or broader tooling pass is claimed.

The six 17E blueprints remain consistent in labeling human/security infrastructure as unimplemented and ES01–ES32/C4 SEC01–SEC20 as unexecuted. Their 114-test reference is reproduced but does not cure F17 findings, supply deployment trust or certify real lineage. Their historical “stop before 17F” instructions are preserved as past scope; the current explicit user request authorizes this audit only.

## 7. Delivery and stop

Document validation passed for all five reports, 48 source citation occurrences (46 unique ranges) and 34 internal links. Embedded harness blocks match executed bytes, the three JUnit receipts agree with reported results, and all seven tested source/test hashes are unchanged. A draft citation ending one line past data/split.py was corrected before validation. Only the five linked reports are added. Complete exact staged-diff review and commit `docs: audit mission 17D engineering and integration readiness`, push normally and verify clean/local/tracking/live equality. Actual resulting commit verification belongs in the final response, avoiding a self-referential commit hash. The gate register is the prospective handoff; none of its implementation or researcher gates is satisfied merely by writing this audit.

**STOP after delivery.** No controller integration, OOF registry, human-review infrastructure, token, real split or evaluation begins. Wait for researcher review.

## 8. Complete independent reproduction harness

These are documentation code blocks, not installed modules or modifications to committed tests. Copy each exact block to the indicated outside-repository `/tmp/mission17f_audit/` filename, then use the additional command above. SHA256 binds each original UTF-8 block including its final newline. Source line 250 instrumentation is intentionally tied to the audited baseline; a changed implementation requires a new reviewed complexity probe. The independent dataset factory uses no existing manifest or real sample IDs. The fixture keeps component work in memory; its session-end hook writes only synthetic observations after guards restore.

`/tmp/mission17f_audit/pytest.ini` — SHA256 `e426e9d19abc292755ba0193e87e40a93f26b61e87db8e131fe90288610e9aa7`

```ini
[pytest]
addopts = -ra
```

`/tmp/mission17f_audit/conftest.py` — SHA256 `e51a59e2b0971d4e91577a8ee40bc40ca469f1eebe1c12c750a364179e7ebcf7`

```python
"""Fresh 17F audit harness; all component work is in-memory synthetic."""
import builtins
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import pytest


@pytest.fixture(autouse=True)
def deny_component_io(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("17F synthetic probe attempted IO")
    for owner, name in [(builtins, 'open'), (io, 'open'), (os, 'open'),
                        (Path, 'open'), (Path, 'read_bytes'), (Path, 'read_text'),
                        (Path, 'write_bytes'), (Path, 'write_text'),
                        (socket, 'socket'), (socket, 'create_connection'),
                        (subprocess, 'Popen')]:
        monkeypatch.setattr(owner, name, denied)


def pytest_sessionfinish(session, exitstatus):
    # Report writing occurs after all per-test IO guards have been restored.
    for name, module in list(sys.modules.items()):
        if name.endswith('test_audit') and 'F17_RESULTS' in vars(module):
            Path('/tmp/mission17f_additional_observations.json').write_text(
                json.dumps(vars(module)['F17_RESULTS'], indent=2)+'\n')
```

`/tmp/mission17f_audit/test_audit.py` — SHA256 `fe770f6bda0b76e5ebd7fca1a12a85951adc60e85bfc725acd8f7334db7b6f27`

```python
"""Independent model/oracle checks and explicitly expected defect witnesses.

Strict xfails describe missing rejection requirements for integration. They are
not counted as passing acceptance tests and do not alter implementation/tests.
"""
from dataclasses import replace
from fractions import Fraction as Q
from itertools import product
import random
import sys

import pytest

from railway_detection.synthetic.convention_b import CausalRunner, SyntheticEvent, Watchdog, legacy_float_to_us
from railway_detection.synthetic.grouped_cv import (
    PhysicalEvent, DatasetRole, Capture, Asset, Annotation, SyntheticDataset,
    InvalidInput, allocate, validate_dataset, verify_allocation, role_plan,
    validate_fit_membership,
)

F17_RESULTS = {'actuator_oracles': 0, 'CV_oracles': 0, 'greedy_dense_oracles': 0,
               'quadratic_scans': [], 'known_feasible_undetermined': [],
               'configuration_collisions': [], 'expected_defects': []}


def dataset(labels=(('a',),)*6, roles=None, counts=None):
    roles = roles if roles is not None else (DatasetRole.DEVELOPMENT_POOL,)*len(labels)
    counts = counts if counts is not None else (1,)*len(labels)
    ev, cap, assets, ann = [], [], [], []
    for i, (ls, role, count) in enumerate(zip(labels, roles, counts, strict=True)):
        eid, cid = f'synthetic:f17:event:{i:04}', f'synthetic:f17:capture:{i:04}'
        ev.append(PhysicalEvent(eid, role, tuple(ls)))
        cap.append(Capture(cid, (eid,)))
        for j in range(count):
            aid, nid = f'synthetic:f17:asset:{i:04}:{j}', f'synthetic:f17:annotation:{i:04}:{j}'
            assets.append(Asset(aid, eid, 'STILL', (nid,), cid))
            ann.append(Annotation(nid, aid, tuple(ls), confirmed_empty=not ls))
    return SyntheticDataset('synthetic:f17:dataset', tuple(ev), tuple(cap), tuple(assets), tuple(ann))


def event_list(times_us, commands):
    return [SyntheticEvent(f'synthetic:f17:sensor:{i}', t, c)
            for i, (t, c) in enumerate(zip(times_us, commands, strict=True))]


def independent_segment(q, velocity, duration):
    # Geometric partition by clipping/threshold breakpoints; do not call _motion.
    cuts = {Q(0), duration}
    if velocity:
        for landmark in (0, 45, 90):
            point = (landmark-q)/velocity
            if 0 < point < duration:
                cuts.add(point)
    cuts = sorted(cuts)
    clipped = lambda t: min(Q(90), max(Q(0), q+velocity*t))
    integral = sum((b-a for a, b in zip(cuts, cuts[1:])
                    if clipped((a+b)/2) <= 45), Q(0))
    return clipped(duration), integral


def test_independent_geometric_oracle_200_trajectories():
    rng = random.Random(0x17F)
    for _ in range(200):
        initial = rng.choice([Q(0), Q(1, 7), Q(30), Q('44.9999999'), Q(45), Q('45.0000001'), Q(90)])
        closing, opening = rng.choice([Q(3), Q(6), Q(5, 2)]), rng.choice([Q(3), Q(7, 2)])
        times = [rng.choice([0, 1000000])]
        for _ in range(rng.randint(1, 24)):
            times.append(times[-1]+rng.choice([1000, 12500, 100000, 200000, 375000, 1000000]))
        commands = [rng.choice('HLR') for _ in times]
        q, endpoint, continuous = initial, Q(0), Q(0)
        for i in range(1, len(times)):
            d = Q(times[i]-times[i-1], 1000000)
            velocity = {'H': Q(0), 'L': -90/closing, 'R': 90/opening}[commands[i-1]]
            q, integral = independent_segment(q, velocity, d)
            endpoint += d*int(q <= 45)
            continuous += integral
        result = CausalRunner(initial_angle=initial, closing_seconds=closing, opening_seconds=opening).run(
            event_list(times, commands), fixture_id='synthetic:f17:geometric')
        assert (result.final_angle, result.endpoint_seconds, result.continuous_seconds) == (q, endpoint, continuous)
        F17_RESULTS['actuator_oracles'] += 1


def brute_possible(labels, k):
    for assignment in product(range(k), repeat=len(labels)):
        if set(assignment) != set(range(k)):
            continue
        if all(any(assignment[i] == f and label in labels[i] for i in range(len(labels)))
               for f in range(k) for label in ('a', 'b')):
            return True
    return False


def test_small_cv_exhaustive_oracle_2704_inputs():
    masks = ((), ('a',), ('b',), ('a', 'b'))
    for m in range(2, 6):
        for labels in product(masks, repeat=m):
            for k in range(2, min(m, 3)+1):
                result = allocate(dataset(labels), k=k, required_support=(('a', 1), ('b', 1)), node_budget=10000)
                possible = brute_possible(labels, k)
                assert result.status.startswith('FEASIBLE_') == possible
                if not possible:
                    assert result.status.startswith('INFEASIBLE_') and not result.assignments
                assert verify_allocation(dataset(labels), result) == possible
                F17_RESULTS['CV_oracles'] += 1
    assert F17_RESULTS['CV_oracles'] == 2704


@pytest.mark.parametrize('size,budget,expected', [(4, 1, 'UNDETERMINED_BUDGET'), (20, 100000, 'UNDETERMINED_SIZE')])
def test_known_feasible_inputs_can_legitimately_remain_undetermined(size, budget, expected):
    labels = (('r', 'a1', 'a2'), ('b',), ('a1', 'a2', 'b'), ('r',))+((),)*(size-4)
    d = dataset(labels)
    result = allocate(d, k=2, required_support=(('r', 1),), node_budget=budget)
    witness = {e.event_id: (0 if i < 2 else 1 if i < 4 else i % 2) for i, e in enumerate(d.events)}
    assert all(any('r' in e.labels and witness[e.event_id] == f for e in d.events) for f in range(2))
    assert result.status == expected and not result.assignments
    F17_RESULTS['known_feasible_undetermined'].append({'size': size, 'status': result.status, 'witness_r_support': [1, 1]})


def dense_objective(groups, assignment, k):
    labels = sorted({label for g in groups for label in g.labels})
    es = [sum(f == j for f in assignment.values()) for j in range(k)]
    fs = [sum(g.original_asset_count for g in groups if assignment.get(g.event_id) == j) for j in range(k)]
    score = lambda vs: sum((k*x-sum(vs))**2 for x in vs)
    cs = sum(score([sum(label in g.labels for g in groups if assignment.get(g.event_id) == j)
                    for j in range(k)]) for label in labels)
    return score(es), cs, score(fs)


def test_incremental_greedy_scores_match_dense_recomputation_50_inputs():
    rng = random.Random(1717)
    for _ in range(50):
        m, k = rng.randint(4, 12), rng.randint(2, 4)
        labels = tuple(tuple(label for label in ('a', 'b', 'c') if rng.randrange(2)) for _ in range(m))
        d = dataset(labels, counts=tuple(rng.randint(1, 3) for _ in range(m)))
        groups = validate_dataset(d).groups
        ordered = sorted(groups, key=lambda g: (-g.original_asset_count, g.event_id))
        assignment = {}
        for g in ordered:
            candidates = []
            for fold in range(k):
                candidate = dict(assignment); candidate[g.event_id] = fold
                candidates.append((dense_objective(groups, candidate, k), fold))
            assignment[g.event_id] = min(candidates)[1]
        result = allocate(d, k=k)
        assert dict(result.assignments) == assignment
        assert result.objective == dense_objective(groups, assignment, k)
        F17_RESULTS['greedy_dense_oracles'] += 1


@pytest.mark.xfail(strict=True, reason='17F role verifier has no original registry/plan identity context')
def test_context_bound_fit_gate_should_reject_coherent_control_to_train_swap():
    roles = (DatasetRole.DEVELOPMENT_POOL,)*6+(DatasetRole.RESERVED_CONTROL,)
    d = dataset((('a',),)*7, roles)
    a = allocate(d, k=3)
    complement = tuple(e for e, f in a.assignments if f != 0)
    plan = role_plan(d, a, outer_fold=0, validation_events=(complement[0],))
    control, former_train = plan.reserved_controls[0], plan.training[0]
    altered = replace(plan, training=(control,)+plan.training[1:],
                      reserved_controls=(former_train,),
                      development=tuple(control if e == former_train else e for e in plan.development))
    F17_RESULTS['expected_defects'].append('coherent control/train swap is structurally accepted')
    with pytest.raises(InvalidInput):
        validate_fit_membership(altered, 'BASE_MODEL_FIT', (control,))


@pytest.mark.xfail(strict=True, reason='17F allocation verifier has no expected allocation-policy argument')
def test_context_bound_allocation_gate_should_reject_weakened_request():
    d = dataset((('r', 'a1', 'a2'), ('b',), ('a1', 'a2', 'b'), ('r',)))
    strong = allocate(d, k=2, required_support=(('r', 1),))
    weak = allocate(d, k=2)
    assert strong.input_digest == weak.input_digest
    assert len({f for e, f in weak.assignments if 'r' in next(x.labels for x in d.events if x.event_id == e)}) == 1
    F17_RESULTS['expected_defects'].append('weaker support request shares corpus digest and is accepted without external expected policy')
    with pytest.raises(InvalidInput):
        verify_allocation(d, weak)


@pytest.mark.parametrize('change', ['bool_objective', 'float_objective', 'negative_work', 'search_without_nodes'])
@pytest.mark.xfail(strict=True, reason='17F incomplete typed objective/work/status receipt validation')
def test_receipt_validator_should_reject_invalid_types_and_work_semantics(change):
    d = dataset()
    a = allocate(d, k=3)
    assert a.objective == (0, 0, 0)
    variants = {
        'bool_objective': replace(a, objective=(False, False, False)),
        'float_objective': replace(a, objective=(0.0, 0.0, 0.0)),
        'negative_work': replace(a, greedy_choices=-1),
        'search_without_nodes': replace(a, status='FEASIBLE_SEARCH', visited_nodes=0),
    }
    F17_RESULTS['expected_defects'].append(change+' is accepted by verify_allocation')
    with pytest.raises(InvalidInput):
        verify_allocation(d, variants[change])


@pytest.mark.parametrize('configuration', ['actuator_rate', 'watchdog_profile'])
def test_result_configuration_binding_is_absent_on_unchanged_path(configuration):
    source = event_list([0, 1000000], 'HH')
    a = CausalRunner().run(source, fixture_id='synthetic:f17:same')
    runner = CausalRunner(closing_seconds=6) if configuration == 'actuator_rate' else CausalRunner(watchdog=Watchdog('SCHEDULED', 10000000, 'L'))
    b = runner.run(source, fixture_id='synthetic:f17:same')
    assert a.canonical_json() == b.canonical_json()
    F17_RESULTS['configuration_collisions'].append(configuration)


@pytest.mark.parametrize('n', [16, 32, 64, 128])
def test_default_reporting_performs_quadratic_interval_scans(n):
    scans = 0
    def trace(frame, event, arg):
        nonlocal scans
        if (event == 'line' and frame.f_code.co_name == 'angle_at'
                and frame.f_code.co_filename.endswith('/synthetic/convention_b.py')
                and frame.f_lineno == 250):
            scans += 1
        return trace
    previous = sys.gettrace()
    try:
        sys.settrace(trace)
        result = CausalRunner().run(event_list([i*10000 for i in range(n+1)], 'H'*(n+1)), fixture_id='synthetic:f17:scans')
    finally:
        sys.settrace(previous)
    assert result.endpoint_seconds == result.report_endpoint_seconds == result.continuous_seconds == 0
    assert scans == n*(n+1)//2
    F17_RESULTS['quadratic_scans'].append({'intervals': n, 'comparisons': scans})


def test_legacy_float_policy_exposes_common_tick_migration_problem():
    assert legacy_float_to_us(.2) == 200000
    with pytest.raises(ValueError):
        legacy_float_to_us(3*.2)


def test_propagated_incomplete_prefix_and_offline_lookahead_are_explicit():
    source = event_list([0, 1000000], 'LL')+[SyntheticEvent('synthetic:f17:invalid', 2000000, 'UNKNOWN')]
    r = CausalRunner().run(source, fixture_id='synthetic:f17:prefix')
    assert r.status == 'INCOMPLETE' and r.final_angle == 60 and r.horizon_us == 1000000
    assert r.report_endpoint_seconds is None
    source = event_list([0, 1000000], 'LL')+[SyntheticEvent('synthetic:f17:future-invalid', 3000000, 'UNKNOWN')]
    arrival = CausalRunner().run(source, fixture_id='synthetic:f17:cutoff', cutoff='1.5')
    offline = CausalRunner().run(source, fixture_id='synthetic:f17:cutoff', cutoff='1.5', mode='OFFLINE')
    assert arrival.status == 'COMPLETE' and arrival.final_angle == 45
    assert offline.status == 'INCOMPLETE' and offline.origin_us is None


@pytest.mark.parametrize('mode,expected', [('SCHEDULED', 84), ('DETECT_ON_ARRIVAL', 90)])
def test_rejected_older_arrival_cannot_reschedule_watchdog(mode, expected):
    source = event_list([0, 1000000, 500000], 'HHR')
    r = CausalRunner(watchdog=Watchdog(mode, 2000000, 'L')).run(
        source, fixture_id='synthetic:f17:watchdog', cutoff='3.2')
    assert len(r.rejections) == 1 and r.rejections[0].reason == 'OUT_OF_ORDER'
    assert r.final_angle == expected


def test_no_production_or_model_modules_loaded():
    assert not any(m in sys.modules for m in ('railway_detection.cli.main',
        'railway_detection.simulation.runner', 'railway_detection.data.split', 'torch', 'cv2', 'ultralytics'))
```
