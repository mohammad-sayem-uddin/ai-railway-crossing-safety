# Mission 13 — WP13.5b Reproducibility and Provenance Audit

**Date:** 2026-11-02. Evidence is local and read-only. No checkpoint, media file or processed dataset was opened or hashed. Only small configuration/documentation files (policy, frozen config, protocol document) were hashed.

## 1. Code reproducibility vs data reproducibility

| Layer | Status |
|---|---|
| **Code identity** | HEAD `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` is real, but the delivered behavior is **not in git**: 25 tracked files are modified and all of `safety/`, `annotation/` and most of `evaluation/` (including the M-02 fix and the media guard) are untracked. A fresh checkout of HEAD does not reproduce this implementation. |
| **Environment** | Reproducible from local evidence (§2). No lock-file verification was performed by this audit. |
| **Test evidence** | The designated reproducible entry point (safe runner) currently refuses. Partial guarded runs: 76 + 262 tests passed (safe-runner audit §5). The "1,802" figure is not reproducible today. |
| **Configuration identity** | Policy hash verified; frozen-config identity is ambiguous between a raw-file hash and a canonical hash (§3). |
| **Model identity** | `NOT_VERIFIED — REQUIRES AUTHORIZED ACCESS` (checkpoints were deliberately not hashed). Note that Mission 12 may have hashed them (F13-08). |
| **Dataset identity** | Raw-media hashes not recomputed (prohibited). Dataset manifests exist in `data/manifests/`; no signed dataset release exists. |
| **Ground-truth provenance** | 27 legacy review files exist, each paired with an invalidation notice; no promotion receipt, EVAL-AUTH or approved Stage-2.1 record exists. |
| **Results** | None. Every empirical cell is a placeholder. |

## 2. Environment, re-observed in this audit

| Item | Value | Matches Mission 12? |
|---|---|---|
| Python | 3.11.15 (`.venv`) | yes |
| PyTorch | 2.13.0 | yes |
| Ultralytics | 8.4.121 (package importable; spec resolves to `site-packages/ultralytics/__init__.py`) | yes |
| Ruff / pytest | 0.16.3 / 9.1.1 | yes |
| NumPy / OpenCV / Pillow / PyYAML | 2.4.6 / 5.0.0.93 / 12.3.0 / 6.0.3 | not previously listed |
| macOS | 26.6.2 (build 25G83), Darwin 25.6.0, arm64 | yes |
| Git | HEAD d4db94d…; staged 0; modified tracked **25**; untracked status entries **379** | Mission 12 baseline said 22 modified |

Earlier project memory recorded Ultralytics as broken in this environment; it is importable now. I did not import or execute any model.

## 3. Hash and identity items

| Item | Mission 12 value | M13 check | Note |
|---|---|---|---|
| Decision policy SHA-256 | `c87c1432…8575` | recomputed identical | file hash |
| "Frozen configuration SHA-256" | `b8ef5da0…ac9a` | `shasum -a 256 configs/frozen_experiment_v1.yaml` = identical | **This is the raw-file hash.** The code binds *canonical* hashes: `FrozenExperimentConfig.canonical_hash` (JSON-canonical, hash field excluded), which the decision policy records as `reference_frozen_config_sha256: 999a7970…a42e`, and EVAL-AUTH binds `frozen_config_sha256` to the canonical value. A reader comparing M12's "SHA-256" to any gate output will see a mismatch (F13-16). |
| Ground-truth protocol SHA-256 | `d100c1e6…ecf4` | identical | file is a modified working-tree document, not an adopted release |
| Safe-runner source SHA-256 | `058893c1…fafb` | not re-hashed | |
| Replay producer identity | `phase12-replay-producer/1` | present in code | |
| Checkpoint hashes | `NOT_VERIFIED` | not touched | correct status |

## 4. Reported counts

| Count | Reported | Verified |
|---|---|---|
| Safe-runner tests | 1,802 across 92 files | **not reproducible**: runner refuses; recorded sum 1,801; see safe-runner audit §6 |
| Older figure | 1,902 | not repeated; contradicted earlier |
| Excluded | "21 tests" | **21 files** (14 checkpoint, 3 processed, 4 raw-media) |
| Modified tracked files | 22 (M12 baseline), 19 (older) | **25 now**; timestamped snapshot at audit start recorded in the final report |
| Untracked entries | 379 | 379 (collapsed directory entries; not a file count) |
| Focused M12 runs | 300 + 151 passed | not reproduced (they include protected-classified files that this audit did not run) |
| Audit runs | – | 76 passed (2 media tests), 262 passed (7 gate tests), all under the read-blocking guard with 0 blocked |

## 5. Missing or unavailable artifacts (stated honestly)

- Dataset release manifest tying `data/manifests/*.json` to a signed or tagged state: absent.
- Model/checkpoint hashes: not independently confirmed (`NOT_VERIFIED`).
- Approved ground truth, promotion receipt, EVAL-AUTH, AUTH-MEDIA-ACCESS, AUTH-DESCRIPTIVE-EVAL-EXEC: absent.
- A committed (tagged) implementation: absent (F13-17).
- Bibliography: absent.
- OS-level isolation: not provided; Python-level guards only.

## 6. Disposition

Code reproducibility is **not demonstrated** (untracked implementation, runner refusal, volatile backups). Data reproducibility is **not demonstrated** and cannot be without authorized access. Mission 11B **M-06** is **PARTIALLY_FIXED**: versions and OS strings are now accurate; counts, the frozen-config identifier and the "no checkpoint hashed" sentence are not.
