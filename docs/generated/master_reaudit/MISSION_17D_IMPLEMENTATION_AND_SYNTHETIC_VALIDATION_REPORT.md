# Mission 17D — Implementation and synthetic validation report

Date: 2026-11-04, America/New_York. Branch: main. Phase baseline: `2165f8633827af477b0ab761013dfa82c8451e78` (17C-4), whose local/tracking/live equality and clean tree were verified before implementation. Original resume baseline: `a809fa853e160161cf427a5b84ad96ba400fa92f`.

## 1. Disposition and authorized scope

**PASS for both isolated synthetic components: 114 tests passed, zero failed, zero skipped.** This is acceptance of the named in-memory engineering scope requested by the current user. It does not adopt a research controller, corpus, CV methodology, protocol, scientific tolerance or protected authority. Researcher R01–R08/T01–T04 remain pending for their real scientific/governance subjects; X01–X07 remain unauthorized. The explicit resume instruction supplies the bounded synthetic implementation/test instruction only. No credential or approval artifact is issued.

Exactly three new package files, four new test files and this report form the17D commit scope. Production/historical modules, configurations, protocol authority, reviewer lists, source manifests, splits, GT and results remain byte-identical. The new package is deliberately separate and not wired into any CLI, media opener or official evaluator. It accepts constructed Python metadata/commands and emits immutable records/optional deterministic strings in memory.

## 2. Implemented causal component

`src/railway_detection/synthetic/convention_b.py:188-352` implements SYNTHETIC_CONVENTION_B_V1. Initialization issues a command without retroactive motion. Each later accepted boundary propagates the previously active command before issuing current intention. Applied origin/effective time and newly requested/issued commands are separate records. CLOSED/CLOSING lower, OPEN/OPENING raise, HOLD is explicit. No actual research controller is imported or evaluated; commanded actuator parity is the implemented scope, not a claim of integrated controller parity.

Timestamp integers mean microseconds; decimal strings mean exact grid-aligned seconds. bool/negative/nonfinite/off-grid/missing/implicit float inputs reject. The explicit legacy adapter interprets a float's shortest round-trip decimal without rounding;0.2 imports,0.1+0.2 rejects off-grid. Exact rational angles/rates and strict unrounded theta≤45 eliminate epsilon/display ambiguity. `src/railway_detection/synthetic/convention_b.py:30-38`; `src/railway_detection/synthetic/convention_b.py:41-49`.

ARRIVAL preserves input order and logs duplicate/older rejections without state advancement. OFFLINE validates timestamps, identities and commands before stable time/index sorting and discloses reordering; invalid OFFLINE input has no actuated prefix. Invalid encountered input returns INCOMPLETE with explicitly labeled prefix values and no certified fixed-grid duration. Invalid constructor/configuration is a ValueError. Empty/single/cutoff-before/at/inside/after cases have explicit outcomes. A future observation beyond cutoff cannot issue a command.

D_E_event is the right-endpoint sum on actual sensor/timer/cutoff intervals. D_C is the exact threshold integral of the declared constant-speed clipped model. Optional fixed reporting endpoints produce separately labeled D_E_report without injecting sensor events. Adding no-op boundaries can change event-grid D_E while D_C/fixed-grid D_E remain unchanged. Neither duration is physical train occupancy or hardware evidence. The historical A runner and Table11 remain unchanged.

NONE is default watchdog. Named optional SCHEDULED and DETECT_ON_ARRIVAL profiles implement C4 sensor-first exact-time priority, one-shot scheduled generations, cancellation, explicit response, gap detection and cutoff behavior. They are conditional synthetic models, not adopted safety timeouts. No timer fabricates a sensor observation or applies a new response retroactively.

## 3. Implemented grouped-CV component

`src/railway_detection/synthetic/grouped_cv.py:174-350` validates typed immutable synthetic event/alias/capture/asset/transform/annotation registries. All views/versions/derivatives of one canonical event remain one group. Known camera/crossing/environment metadata and explicit unknown reasons are preserved. Complete joins, unique IDs, confirmed-empty negatives, frame/PTS/timebase evidence and exact transform parameters are checked. Missing/ambiguous/conflicting identities, orphan/cyclic descendants, cross-event duplicate identity, multi-event derivatives and all fallback requests fail closed. Namespace checks prevent accidental real-input use; they do not authenticate synthetic provenance or implement an OS sandbox.

`src/railway_detection/synthetic/grouped_cv.py:410-526` implements SYNTHETIC_GROUPED_V1. A sufficient-statistics greedy path makes M*K deterministic fold choices with O(M*K*(L+1)) scoring after metadata validation/sorting. If that candidate fails constraints and M≤18, bounded DFS uses declared fold-label symmetry/necessary-condition pruning and returns the first verified feasible candidate. Larger failed candidates or exhausted budgets remain undetermined. This separately named profile does not silently replace C2's global lexicographic optimum, and makes no OPTIMAL claim.

InvalidInput(ValueError) carries status INVALID_INPUT and returns no allocation. Results distinguish INFEASIBLE_NECESSARY, FEASIBLE_GREEDY, FEASIBLE_SEARCH, INFEASIBLE_EXHAUSTIVE, UNDETERMINED_BUDGET and UNDETERMINED_SIZE. Only feasible statuses contain accepted in-memory assignments; the verifier recomputes input identity, complete eligible event coverage, support, fold bounds and objective. Exact infeasibility is used only after a necessary proof or exhausted canonical bounded search. `src/railway_detection/synthetic/grouped_cv.py:529-573`.

`src/railway_detection/synthetic/grouped_cv.py:590-622` separates development, outer evaluation, inner training/validation, calibration-only, reserved controls, case study and final descriptive roles. Outer complements and sibling disjointness are explicit. A final refit requires a named synthetic frozen rule. `src/railway_detection/synthetic/grouped_cv.py:625-667` checks base-model/preprocessor/calibrator/cache-producer/selection memberships without fitting anything. RESERVED_CALIBRATION may use calibration-only data for calibrator metadata; base/preprocessing fit and independent control/evaluation reuse reject. Unverified INNER_OOF calibration fails closed because full per-model/score evidence is not implemented.

RD024 pooled engine exclusion is not turned into a detector-training ban/zero-shot claim. RD025 no-train confirmation/event/exposure limits remain pending for real data. Synthetic supplied role policy alone determines these toy memberships; no V2 case is assigned to training/calibration or an official research split.

## 4. Exact executed test evidence

Python: repository .venv Python3.11.15. Component imports are standard-library only plus their parent package's inert __init__. Root conftest imports the production CLI, so it was deliberately excluded with confcutdir. Plugin autoload, bytecode writes and pytest cache were disabled. Only the new directory was executed; legacy suites were not assumed synthetic.

```sh
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest \
  --confcutdir=tests/synthetic_mission17d -p no:cacheprovider \
  --import-mode=importlib tests/synthetic_mission17d -q \
  --junitxml=/tmp/mission17d_final.xml
```

Final observed summary: `114 passed in 0.42s` (elapsed time is local test-run metadata, not a performance/hardware claim). JUnit confirms70 simulation tests,38 CV tests and6 isolation tests, no failures/errors/skips. Test/component source digests before and after the run match. Earlier development runs passed112 then113 cases; contract review removed an unpublished fold cap and added explicit invalid-input/forged-policy checks, producing the final114. No failing feature suite was weakened into success.

| Module | Executed cases | Evidence |
|---|---|---|
| Causal simulation | 70 | `tests/synthetic_mission17d/test_convention_b.py:73-80`; `tests/synthetic_mission17d/test_convention_b.py:170-176`; `tests/synthetic_mission17d/test_convention_b.py:246-258` |
| Grouped CV | 38 | `tests/synthetic_mission17d/test_grouped_cv.py:201-208`; `tests/synthetic_mission17d/test_grouped_cv.py:230-236`; `tests/synthetic_mission17d/test_grouped_cv.py:260-292` |
| Isolation | 6 | `tests/synthetic_mission17d/test_isolation.py:12-15`; `tests/synthetic_mission17d/test_isolation.py:25-27`. IO-denial fixture is test isolation, not a deployment security guarantee. |

The21 C2 A3 numerical vectors all execute against the new runner. Duplicate/order tests additionally exercise actual implemented rejection behavior, rather than treating accepted-prefix arithmetic as that behavior. Independent synthetic A arithmetic checks the conditional duration identity and its counterexamples;100 fresh runs check deterministic output. Fixed-report/continuous subdivision properties check the exact estimator distinction.

CV feasibility is checked against a separate tiny brute-force oracle. A mixed-label triangle is proved infeasible; a greedy miss finds a feasible search candidate; budget/size limits return no accepted assignments;1,315 newly constructed synthetic events take the polynomial greedy path with zero DFS nodes. This is an in-memory synthetic allocation, expressly permitted by the new request, not an official or real-data split. No metadata was extracted from actual media/manifests to populate it.

## 5. C4 readiness coverage and explicit deferrals

| Readiness cases | Disposition / concrete evidence |
|---|---|
| SIM01–SIM02 | Executed: delayed issue, exact21 numeric vectors, irregular/asymmetric/partial/threshold oracles and provenance. |
| SIM03–SIM07 | Executed: invalid/float adapter, arrival rejection/offline sort, empty/single/cutoff and strict threshold cases. |
| SIM08–SIM10 | Executed: report-grid/no-op invariants, target mapping/conflict, boundary identity and counterexamples. |
| SIM11–SIM13 | Executed: both conditional watchdog profiles, equality/cancellation/rejection/one-shot/cutoff and100-run deterministic serialization. |
| SIM14 | Executed isolation/source-preservation checks. Actual research controller integration remains explicitly outside implementation; no claim that its full sensing/confirmation/dwell path was executed. |
| CV01–CV04 | Executed: physical aliases/views/derivatives, retained metadata, invalid/duplicate/ambiguous IDs, orphan/cycle/multi-event/duplicate-content rejection. |
| CV05–CV11 | Executed: prospective role separation, necessary/exhaustive/oracle feasibility, deterministic greedy/search/budget/size behavior, large synthetic metadata and inner subset/frozen-rule constraints. |
| CV12–CV14 | Executed within documented metadata subset: fit/selection/cache-producing membership negatives, forged result/objective/roles, synthetic-only boundaries and RD role limitations. |
| CV15 | DEFERRED: full trusted evidence-binding resolver, authenticated source/exposure registry, fitted-artifact DAG, OOF per-model score proof and scientific adoption. INNER_OOF calibration denies rather than accepting unverified evidence. No fitting/cache bytes are accessed. |
| SEC01–SEC20 | NOT EXECUTED. Security authority, credentials, grant transactions, blind human workflow, ledger codec/recovery and protected publication are blueprint-only, to be prepared in17E. Test fixture IO guards do not satisfy security acceptance. |
| Original C2 52 feature plans | No blanket execution/acceptance claim. Only the explicitly mapped isolated simulation/CV behaviors above were implemented/tested. Human/security/real-controller/deployment cases remain pending. |

General C4 CVL registries describe future scientific evidence requirements; this module implements the typed synthetic grouping/role subset documented above. It does not implement official schema migration, human identity, trusted manifests or complete nested-plan global optimization. A failed frozen outer/inner plan does not prove all nested plans infeasible. Unknown real lineage/model exposure and researcher roles remain unresolved, not certified by namespaces or hashes.

## 6. Tested source identities and safety validation

The following SHA256 values identify only the new safe Python source/test bytes used in the final run; no media/checkpoint/cache was hashed.

| New source/test path | Tested SHA256 |
|---|---|
| `src/railway_detection/synthetic/__init__.py` | `a269b30d6399436161dc863db33fd4dccb7d243926ea6c1fd505adabec278f02` |
| `src/railway_detection/synthetic/convention_b.py` | `09d2756055484eb446794aaa719c7750968b5b1536415def5a0ed4d37eee8488` |
| `src/railway_detection/synthetic/grouped_cv.py` | `ec97aa858694542304c9f339e552dd758af5058ce3a08f2964671181d6bd8456` |
| `tests/synthetic_mission17d/conftest.py` | `e64acca4d8d4a390bf1c6eb07fbba3ad16827f839bba60c922a5f85793dc3438` |
| `tests/synthetic_mission17d/test_convention_b.py` | `2dfe06cb537a27f4d45cf4d2bda7d5722b25e7b935bdbca2a789e244e187f4da` |
| `tests/synthetic_mission17d/test_grouped_cv.py` | `582d4858e073a08953ea8b930f8bb047a6f492f5690bdd12bc0c66cff7649ac7` |
| `tests/synthetic_mission17d/test_isolation.py` | `5d9424894bb70979695114bb72b9955885b6448874f6c8eddbfddf8622c52986` |

Static syntax/AST checks verified the three component modules use only standard-library imports, expose no file-loading/writing/dynamic-code/process entrypoint and do not import production modules. All seven new Python files were syntax checked; the selected tests compile/import under Python3.11. Ruff was unavailable and not claimed executed. The test guard denies file/network/process attempts in each component case; source imports and the temporary JUnit/test receipt are safe engineering evidence, not protected resources.

Raw media accessed:0; production checkpoints:0; protected caches:0; real inference/replay/training/evaluation:0; model fits:0; official splits:0; human annotation/adjudication:0; GT promotions:0; authorization tokens issued/consumed:0; protocol promotions:0; researcher scientific/governance approvals created:0. Existing production safety guards were not modified or bypassed.

## 7. Git gate and next authorized action

Validate this report's links/citations and exact eight-file addition scope; inspect full code/test/document diff and secret/protected-path scan; ensure source hashes still equal the passing run, then stage only the exact named files. Commit: `feat: implement synthetic causal simulation and grouped CV splitter`. Push normally; verify exact paths, clean tree and local/tracking/live equality. The actual commit hash/remote verification is supplied at the completed phase boundary and consolidated final report, not fabricated into this pre-commit document.

Next authorized phase only after that gate:17E's six human-review/security blueprint documents. No authority/CLI security implementation is started by this pass, and no real-resource capability or research approval follows. Stop after17E and the requested final report; no17F.

Contract sources: [17C-4 resolution](MISSION_17C4_ACCEPTANCE_GAP_RESOLUTION.md#resolution), [simulation/calibration](MISSION_17C4_SIMULATION_AND_CALIBRATION_ACCEPTANCE_SPEC.md#simulation), [recovery/lineage](MISSION_17C4_RECOVERY_AND_CV_LINEAGE_ACCEPTANCE_SPEC.md#lineage), [readiness matrix](MISSION_17C4_SYNTHETIC_TEST_READINESS_MATRIX.md#readiness).
