# Reproducibility

## Repository and environment

- Repository: `mohammad-sayem-uddin/ai-railway-crossing-safety`
  (Mac working copy: `/Users/sayemuddin/Desktop/Train_automation`).
  State at programme start: local == remote == `25bab639d50dbc72d7fc15f337b585647b128cd6`
  (Mission 2 release). Mission 3 additions are committed as separate,
  exact-path commits listed in the completion report.
- Runtime: macOS (MacBook Air), Python 3.11.15, project `.venv`.
  Test invocation used by the programme: `.venv/bin/python -m pytest …`
  (Mission 2 acceptance run: `tests/synthetic_mission44/` 9/9).

## Frozen identities (SHA-256)

| Artifact | Hash |
|---|---|
| `configs/frozen_experiment_v1.yaml` (canonical config hash / model_config_provenance) | `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e` |
| `configs/decision_policy_v1.yaml` (file hash, Phase 10.1) | `051c908d4db23687db33cbc8349945b241a0735b362413be876d7017a5eacc9d` |
| `configs/decision_policy_v2_candidate.yaml` (canonical hash) | `143782d15632d2d840e3c3a1d0437a113cd810356d8ce59757d1b6b97f55ea60` |
| Vision checkpoint (frozen, `experiments/vision/39f402dfe460/…/best.pt`) | `3f5bb5b2…e4ebd` (full value in frozen config) |
| Audio V3 checkpoint | `ea1bb81d…82782` (full value in frozen config) |
| Descriptive metric scope binding | `1e10c02d…c36` |
| Mission 43 B2 evaluation input manifest (27 events) | `2fb08c92e6d389e55e3963c0f47f0d7fa7959922f39b9b4b600f244a57a46b72` |
| Mission 39 pilot manifest (5 events; the binding cited as `61155c9b…fe7` in earlier reports) | `61155c9b…fe7` |
| Mission 3 multimodal replay manifest (27 events, front+audio+back) | `3c720167ea06b67141beb7cf33bd02ce325db62a3e100819f8aa4ad213d5bbbb` |
| Adopted annotation proposals (27 files) | Per-file SHA-256 in `RESEARCHER_ANNOTATION_ADOPTION.json` (Mission 43 package); re-verified 27/27 in Mission 3 |

## How each result class is reproduced

- **Perception results (Mission 43):** the professor-evidence package
  `docs/generated/professor_evidence/mission43/` contains run manifests,
  per-event CSVs, the adoption record, and `verify_package.py` +
  `PACKAGE_FILES.sha256` for byte-level verification.
- **Policy trajectory comparison (Phase 10.1):**
  `scripts/run_phase10_1_candidate_comparison.py` re-verifies the candidate
  policy hash at execution time and cross-checks both policies against the
  Phase 9/10 outputs; outputs are preserved under
  `results/r04_sync_estimation/phase10_1_restricted_comparison_20261014T054615Z/`.
- **Synthetic battery (Mission 3):**
  `.venv/bin/python scripts/run_m3_synthetic_battery.py --out results/m3_synthetic_battery_r2`
  — deterministic: fixed synthetic frame streams, both engines, per-tick
  JSONL traces + `summary.json` with per-check pass/fail. Final run
  (battery/2): **46/46 checks passed**. Script SHA-256
  `02be83454cd566c0f97fc78a38b52da7feadfdde95e7c65a612fb12b7576be7d9`
  (run 1, 35/42 with harness expectation errors, preserved in
  `results/m3_synthetic_battery/`).
- **Multimodal assembly (Mission 3):**
  `.venv/bin/python scripts/build_m3_mm_manifest_v2.py` — anchors on the
  Mission 43 B2 manifest (hash-asserted), re-verifies every front/audio
  cache hash, resolves back predictions, writes
  `data/manifests/m3_multimodal_replay_manifest.json` +
  `results/m3_mm_assembly/` (coverage CSV + summary).
- **Access-classification manifest:** Mission 3 added the two missing
  entries (UNKNOWN, pending executed review, per the generator's own
  convention) via `scripts/fix_m3_classification.py` +
  `scripts/fix_m3_classification2.py`; the tools suite passes 58/58 and
  the manifest now covers 170 test files.
- **Governed replay (when authorized):** `CacheOnlyReplayEngine` verifies
  every cache file's SHA-256 and line count against the manifest before
  parsing, refuses media extensions absolutely, and emits a
  `deterministic_run_id` derived from manifest hash + event + replay config.
  The descriptive gate re-verifies all five live bindings at load and at
  replay time.
- **Governance verification:** `evaluation.execution_gate.
  assess_official_phase12_readiness(root)` recomputes readiness and all live
  bindings from the repository state; its blocker list is the authoritative
  statement of what remains missing.

## Determinism and preservation notes

Historical reports, caches and outputs (Phases 8–10.1, Missions 39–44) are
preserved byte-for-byte; corrections are always additive (new files, new
runs) — including the Phase 10.1 duration correction, which lives only in
that phase's own script. Original media and original annotations were never
modified, renamed or deleted at any point in the programme.
