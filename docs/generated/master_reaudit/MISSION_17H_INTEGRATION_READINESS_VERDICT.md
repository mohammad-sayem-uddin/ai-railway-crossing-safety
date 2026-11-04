# Mission 17H — Integration readiness decision

Date: 2026-11-04, America/New_York. Audited commit: `ea5da77c58577056521e362271e5bceff290aff9`; main, initially clean, local/origin/live equal, no post-17G commits. Scope: read-only implementation verification and two new reports. Same assistant as 17G; no human-independent review or approval is claimed.

**Overall disposition: CONDITIONALLY_READY_WITH_DOCUMENTED_RESTRICTIONS.**

[Full verification evidence and exact commands](MISSION_17H_INDEPENDENT_VERIFICATION_REPORT.md); [original 17F defects](MISSION_17F_INDEPENDENT_ENGINEERING_AUDIT.md); [17G claims](MISSION_17G_FIVE_DEFECT_REMEDIATION_REPORT.md).

## 1. Separate decisions

| Subject | Decision / evidence status |
|---|---|
| F17-01 original roles | **Verified — fixed** against separately retained original dataset/allocation/role context. Authenticity of that context is caller-trusted. |
| F17-02 policy binding | **Verified — fixed** for canonical complete policy content, expected-request comparison and receipt binding; not signed authorization. |
| F17-03 allocation receipts | **Verified — fixed** for strict typed fields and complete bounded operation recomputation. Serialization alone does not verify the operation or past execution. |
| F17-04 simulation configuration | **Verified — fixed** for actual producer snapshot/log binding. **Partially verified** as detached-result provenance: config checks do not validate fabricated trajectory values. |
| F17-05 reporting | **Verified — original quadratic time removed**; default total reuse and O(S+R) fixed-grid work. Ancillary O(1) extra space claim is **Contradicted** by H-N01. |
| 216 existing tests | **Verified:** 114 original + 22 migrated audit + 80 hardening; 216 unique cases. Combined and subset runs all passed, zero failures/errors/skips/xfails. |
| Six former expected failures | **Verified:** six ordinary rejection cases with valid controls and specific InvalidInput expectations passed; no expected-failure markers. |
| Important adversarial observations | 48 expected rejections and 13 positive cases matched; four disclosed trust-limit constructions were accepted. Six extra boundary experiments, 11 public edge groups, 15 reporting profiles, five memory measurements and 28 CV cost profiles were completed. These are not extra pytest tests. |
| Isolation | **Verified within Python test scope:** six isolation cases pass, guard bytes unchanged, safe component imports, no protected access observed. OS/runtime security is **Unsupported**, not inferred. |
| Caller-trust risks | **Remain:** source truth/retention, intended policy, actual fitting/exposure and original run provenance are not externally authenticated. Coherent replacement of both expected source and candidate succeeds. |
| Receipt overhead | **Verified:** each fit check recomputes one allocation and three registry validations; ten fits at M=1536 perform 61,440 greedy candidates. Search-budget work repeats. No current stale verification cache, but no adversarial resource-exhaustion guarantee. |
| Reporting complexity | **Acceptable for bounded synthetic use:** O(S+R) reporting arithmetic; OFFLINE adds O(N log N) sorting; actual helper auxiliary memory O(R), total stored/temporary data linear in N/S/R. |
| Ruff / Mypy | Ruff 0.16.3 is available at `.venv/bin/ruff`; the configured no-fix check exits 1 with 68 unresolved diagnostics (H-N02). Mypy API still fails before analysis because `mypy.bogus_type` is missing. No dependency/config change or passing lint/type result claimed. |
| Controller integration recommended? | **Conditional, synthetic-only:** a separately authorized constructed-frame adapter stage may be considered after the selected time/order/state/estimator contract, expected-input ownership and numerical regression gates are explicit. No production wiring recommended by this audit. |
| Grouped-CV integration recommended? | **Conditional, metadata-only:** retain original corpus/policy/role inputs independently, run full receipt verification, preserve all role/no-fallback/OOF restrictions and select practical budgets. No official split/fitting/real-loader integration endorsed. |
| Human-review implementation recommended? | **No readiness recommendation from 17G/17H evidence.** Identity, authority, blinding, ledger/publication services and their acceptance remain separate future scope. |
| Real-data research execution authorized? | **NO.** No new review/media/model/cache/split/training/evaluation/promotion capability, scientific adoption or governance approval was created. |

## 2. Open findings and mandatory reliance restrictions

**H-N01 — LOW, open:** `src/railway_detection/synthetic/convention_b.py:283-299` uses `report[1:]`. This adds a temporary R-element tuple and contradicts the 17G O(1) extra traversal-space statement (`docs/generated/master_reaudit/MISSION_17G_FIVE_DEFECT_REMEDIATION_REPORT.md:73-73`). Isolated helper peak traced memory rose 1192→66504 bytes for R=32→8192, consistent with source reasoning. The linear time correction remains valid. Correct the description in a separately authorized follow-up; optionally remove the slice if constant auxiliary traversal storage is required. No fix was made here.

**H-N02 — LOW, open:** direct Ruff 0.16.3 execution returns 68 diagnostics under the unchanged project rules. The same tool finds 26 on the seven 17F baseline files; the current set includes 38 in the two added 17G test modules. The results are lint debt, not 68 proven runtime failures. The B023 closure warnings were reviewed as synchronously consumed callbacks, and adjacent-grid B905 warnings require semantic care; no configured check was waived or fixed here. Mypy analysis remains unavailable.

Before any next stage relies on these components:

1. Retain expected dataset/policy/role/configuration outside candidate submissions; a frozen dataclass or a self-hash is not an independent authority.
2. Use full allocation verification, not canonical serialization, as the operation-consistency check. Treat configuration verification as configuration-only; retain actual input/code receipts and independent numerical checks for simulation results.
3. Keep the report helper internal to ordered contiguous interval producers. Arbitrary gapped/overlapping private inputs are not validated there.
4. Account for O(R) temporary grid copies and repeated full allocation/registry work. Select explicit practical sizes/budgets; do not infer resource resistance or complete feasibility from the heuristic/budgeted profile.
5. Keep scientific adoption, actual-controller policy, complete fitted-artifact/OOF provenance, human/security services and protected permissions as separate unmet gates. Passing 216 tests supplies none of them.
6. Address or explicitly review the configured Ruff diagnostics in a separately authorized task; a passing runtime suite does not convert the lint failure into a pass.

## 3. Recommended next action and delivery boundary

Researcher review first, then a separately scoped synthetic follow-up addressing the space-claim correction, lint debt and expected-input/result-validation/budget/precondition contracts before Mission 18. This decision is engineering evidence, not authorization to begin that work. No implementation or test file was added/modified; no silent repair occurred. The source and nine Python-file hashes remain equal to the audited commit.

Exact 17H changed-file list (two additions only):

- `docs/generated/master_reaudit/MISSION_17H_INDEPENDENT_VERIFICATION_REPORT.md`
- `docs/generated/master_reaudit/MISSION_17H_INTEGRATION_READINESS_VERDICT.md`

Normal Git delivery uses `docs: independently verify mission 17G remediations`; actual commit/local/tracking/live/clean verification is supplied in the final completion response. The six 17G source/test/report changes are listed as historical evidence in the companion report, not modifications made by 17H.

**STOP. Do not begin Mission 18, modify implementation or tests, or conduct real-data work. Wait for researcher review.**
