# Decision-Policy Hash Provenance — Discrepancy Resolved

**Question.** The Phase 5 report records `configs/decision_policy_v1.yaml` as `051c908d…`; today's file
hashes (raw bytes) to `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575`.

**Finding: not a discrepancy. Two different hash conventions were being compared.**

| Convention | Definition | Value for the current file |
|---|---|---|
| Raw-file SHA-256 | SHA-256 of the file's bytes (`shasum -a 256`) | `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575` |
| Canonical-content SHA-256 | `compute_canonical_config_hash(yaml.safe_load(file))`: sorted-key compact JSON of the parsed content | `051c908d4db23687db33cbc8349945b241a0735b362413be876d7017a5eacc9d` |

Evidence:
- `scripts/run_phase5_full_inference.py:127-134` computes `compute_canonical_config_hash(yaml.safe_load(...))` and asserts it equals `051c908d…`; that assertion holds for the file today.
- The current file's mtime is 2026-10-13T17:18:26Z (UTC), 49 minutes before the Phase 5 run (2026-10-13T18:07:22Z). `PHASE3_SENSOR_HEALTH_DECISION_POLICY.md` and eight later reports cite the same canonical value; `PHASE11_6F` recomputed it with the project function and found it unchanged.
- The file is untracked, so Git history cannot be consulted; no evidence suggests it changed after Phase 5.
- The same pattern holds for the other two files: frozen config raw `b8ef5da0…` vs canonical `999a7970…`; v2 candidate raw `d90828b2ec37169d663c72ab7de7d86600728c0db170ebef3934b9565abaf07f` vs canonical `143782d1…`.

The policy file was **not** modified. The readiness gate binds EVAL-AUTH to the **raw** policy hash and checks the
policy's `reference_frozen_config_sha256` against the **canonical** frozen-config hash; `artifact_fingerprints` and the
reproducibility audit now record both conventions side by side, and
`tests/unit/test_phase14_benchmark_suite.py::test_real_artifacts_verify_and_both_hash_conventions_are_recorded`
pins the relationship so any future edit to either file is caught.

Residual note: reports should name the convention whenever they quote a hash. A few older documents quote
"hash" without saying which; the values themselves are all consistent with the table above.
