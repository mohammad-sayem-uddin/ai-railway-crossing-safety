# Phase 0 — Repository Recovery Report

| | |
|---|---|
| Date | 2026-10-13 |
| Agent | Claude Sonnet 5 |
| Scope | Git reconciliation only, as explicitly bounded by the user's Phase 0 instruction. Backup verification, environment rebuild, inference and the test suite were explicitly excluded from this pass. |
| Preceding work | `docs/INDEPENDENT_MASTER_AUDIT.md`, `docs/IMPLEMENTATION_PLAN_FOR_SONNET.md`, `docs/OPEN_DECISIONS_AND_BLOCKERS.md`, `docs/FINDINGS_REGISTER.csv` (Opus 5.5, same date) |

## 1. What was found (reconciled against the Opus audit)

| Check | Opus audit (earlier today) | This pass, before any action | Match |
|---|---|---|---|
| HEAD | `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` | same | ✅ |
| Branch | `main` | same | ✅ |
| Assume-unchanged (`h`) entries | 73 | 73 | ✅ |
| Tracked files missing from disk | 68 | 68 | ✅ |
| Untracked paths | 108 | 113 (5 more — the Opus audit's own 5 new `docs/` files, created after that audit's own status snapshot) | ✅ consistent |
| Modified tracked files visible | 10 | 10 (an 11th, `data/sync.py`, was hidden by its assume-unchanged flag) | ✅ consistent |

No discrepancy with the Opus audit's figures. The user's instruction to "recheck these counts only" is satisfied: they reconfirmed exactly.

## 2. What was changed

### 2.1 Restored 68 tracked-but-absent files from HEAD

Every path returned by `git ls-files -d` was individually confirmed absent from disk immediately before restoration, then restored with `git checkout HEAD -- <path>`, then reconfirmed present. **68 of 68 restored, 0 overwrites possible or attempted** (all were confirmed absent first). Breakdown by area:

| Area | Count | Notable paths |
|---|---|---|
| `tests/unit/` | 10 | `test_cli.py`, `test_config.py`, `test_contracts.py`, `test_dashboard_server.py`, `test_failure_analysis.py`, `test_manifest.py`, `test_research_scripts.py`, `test_split.py`, `test_temporal_evidence.py`, `test_video_reader.py`, `test_vision_adapter.py` |
| `configs/` | 4 | `audio.yaml`, `fusion.yaml`, `simulation.yaml`, `vision.yaml` |
| `src/railway_detection/` package scaffolding | ~14 | `__main__.py`, `vision/adapter.py`, `audio/noise_mixer.py`, `*/__init__.py` × several, `py.typed` |
| `experiments/vision/*` run artifacts | ~10 | `resolved_config.yaml`, `run_manifest.json`, `results.csv`, `args.yaml`, `confusion_matrix.png`, `pr_curves.png`, `failure_analysis.json`, `failure_report.md`, `metrics.json/md`, `termination_note.json` |
| `results/` anchors | ~8 | `.gitkeep` files, `dataset_manifest.jsonl`, `manifest_summary.json`, `report.json`, `run_manifest.json` |
| Root project files | 5 | `pyproject.toml`, `dashboard.py`, `demo_video.py` |
| `data/` anchors and metadata | 6 | `.gitkeep` files, `vision_v1_metadata.json` |
| `tests/fixtures/`, `tests/integration/`, `tests/smoke/` | 3 | `mock_data.py`, `test_phase0_smoke.py`, `test_cli_smoke.py` |
| `research/` scaffolding | 2 | `__init__.py`, `scripts/__init__.py` |

Full exact list is reproducible via `git log -1 --stat` is not applicable (nothing committed); the authoritative list was `git ls-files -d` at the start of this phase, captured in this report's companion data and in `reports/progress.md`.

**Important caveat for Gemini:** `pyproject.toml` is now restored to its HEAD (August 2026, Phase-0-era) content. It has **not** been reconciled against whatever dependencies the current, more advanced `src/railway_detection` package (fusion, simulation, experiments, annotation, evaluation modules — all untracked, local-only, newer than this file) actually needs. Do not assume it is complete or correct for the current codebase. This is a known gap for the environment-rebuild phase (`IMPLEMENTATION_PLAN_FOR_SONNET.md` Phase 1), not resolved here.

### 2.2 Cleared 73 assume-unchanged flags

`git update-index --no-assume-unchanged` applied to all 73 paths. Verified zero `h`-flagged entries remain.

### 2.3 Surfaced one previously hidden local modification

Of the 5 assume-unchanged files that were actually present on disk:

- **4 are byte-identical to HEAD**: `src/railway_detection/config/__init__.py`, `config/exceptions.py`, `fusion/__init__.py`, `fusion/evidence.py`. Clearing their flags produces no visible diff — confirmed.
- **1 differs: `src/railway_detection/data/sync.py`.** The local version is a non-dataclass, restructured rewrite of `SyncAligner` that preserves the same public API (`add_source`, `to_master`, `is_aligned`, `alignment_summary`) but with renamed internals (`uncertainty_s` dict → `uncertainties_s`) and parameter defaults. This is the version the current (untracked) `fusion/collector.py` imports and depends on. **Left on disk unchanged.** Full diff saved to `reports/sync_py_local_vs_head.diff`. This matches and confirms Opus audit finding IMA-02's observation that this file was "rewritten today" — now with the actual diff captured for the record.

### 2.4 What was explicitly NOT touched

Verified by diffing the untracked-file list before and after (identical) and by direct hash spot-check:

- `data/ground_truth/` (candidate proposals, reviews, snapshots) — untouched, still untracked.
- `data/raw/` (video, audio, vision images) — untouched, still untracked/ignored.
- `models/audio/best_checkpoint.pt` (Audio V2, prohibited) — SHA-256 `59b0785f…fcf7d5`, unchanged.
- `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt` (Audio V3, frozen) — SHA-256 `ea1bb81d…6c512782`, unchanged.
- `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` (Vision, frozen) — SHA-256 `3f5bb5b2…fba18ebd`, unchanged.
- `results/experiments/`, `results/archive/`, `results/testing/` (legacy run outputs) — untouched.
- No `git add`, `git commit`, `git push`, `git reset --hard`, `git clean`, or history rewrite was performed. Nothing is staged.
- No approved-ground-truth file or approval manifest was created or modified.
- No Python environment was built or modified. No inference, training or test suite was executed.

## 3. Current repository state (end of this phase)

```
HEAD: d4db94d4a4ea83ae4c510d65dfc99c5d6798304b (main)
git status: 11 modified, 113 untracked, 0 staged
git ls-files -v | grep '^h': empty
git ls-files -d: empty
```

The 11 modified files are the 9 originally reported by the recovery reports plus `src/railway_detection/vision/video.py` (a sequential-decode fix made 2026-10-13, found by the Opus audit) plus `src/railway_detection/data/sync.py` (surfaced in this phase). The 113 untracked paths are unchanged in membership from before this phase: all local-only research code (`fusion/`, `simulation/`, `experiments/`, `annotation/`, newer `audio/` modules), 18 of 20 scripts, all candidate ground-truth data, `results/experiments/` and `results/archive/`, and the 5 documentation files produced by the Opus audit (now 7, including the two created in this phase).

## 4. Phase 0 acceptance — status against `IMPLEMENTATION_PLAN_FOR_SONNET.md`

| Criterion | Status |
|---|---|
| `git ls-files -v \| grep '^h'` empty | ✅ Pass |
| `git ls-files -d` empty | ✅ Pass |
| No pre-existing file content changed | ✅ Pass (restored files are HEAD copies by construction; the 4 identical flagged files show no diff; the 1 differing file, `sync.py`, was left untouched, only its visibility was corrected) |
| External copy re-hashed equal to an evidence manifest | ⚠️ **Not verified by either agent in this session.** User states personal Google Drive backup verification is complete and asked that it not be re-checked. No `EVIDENCE_MANIFEST` was generated this session (the full-scope Phase 0 in the plan calls for one; it was explicitly skipped per the user's instruction for this bounded pass). |
| Preservation commit/branch/tag created | ❌ Not done — explicitly out of scope ("Do not commit, push... or reorganize research files") |
| Fresh clone of preservation branch verifies | N/A — no branch created |

**Phase 0 did not fully pass the acceptance criteria in `IMPLEMENTATION_PLAN_FOR_SONNET.md`.** It passed the narrower, explicitly-scoped task given for this session: reconcile Git state safely, preserve all local work, do not commit. The outstanding full-Phase-0 items (independent evidence manifest, preservation commit) remain for whoever picks that up next — likely a short follow-up once the user is ready to commit, since no destructive action is needed first.

## 5. Unresolved problems (carried forward, not solved here)

These are from the Opus audit and remain exactly as documented; nothing in this phase bore on them:

- **IMA-22** (P0): Audio V3 inference ran without the training normalisation statistics (`norm_mean`/`norm_std` vs `feature_mean`/`feature_std` key mismatch). Not touched this phase.
- **IMA-15 / IMA-16** (P0): Clearance rule does not require positive rear confirmation; no liveness exit from closed/fault states. Not touched.
- **IMA-11** (P0): Zero-offset camera fusion assumption, contradicted by media metadata. Not touched.
- **IMA-28 / IMA-29** (P0): Premature-opening and missed-train metrics are decided by code path, not by ground truth, because no ground truth is linked. Not touched.
- **IMA-06**: All 27 ground-truth review files are marked `APPROVED` by a non-existent human review. Not touched — correctly left alone per the standing instruction that ground-truth approval is the user's act alone.
- **IMA-03**: No working Python environment on this machine can import torch, ultralytics and OpenCV together. Not rebuilt this phase (explicitly deferred).
- **`pyproject.toml` currency**: now restored to its August-2026 HEAD content; not reconciled against the current package's actual dependency needs. Flagged above as a new, narrow gap for whoever rebuilds the environment.
- **Backup independence**: the user's Google Drive backup has not been independently re-hashed by any agent against a generated evidence manifest. This is a trust-the-user gap, explicitly accepted by instruction, not a technical blocker.

## 6. Exact next task

See `docs/HANDOFF_TO_GEMINI.md`.
