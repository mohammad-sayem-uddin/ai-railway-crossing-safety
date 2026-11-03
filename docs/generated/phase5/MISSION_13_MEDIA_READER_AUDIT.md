# Mission 13 — WP13.2 Media-Reader Authorization Coverage Audit

**Date:** 2026-11-02. **Scope searched:** `src/`, `scripts/`, `research/`, plus root-level `dashboard.py`, `demo_video.py` and the git-ignored `scratch/` directory (found during the audit; not covered by any prior inventory).
**Method:** repository-wide text search for reader APIs (`Image.open`, `cv2.imread/VideoCapture/imdecode`, `ffmpeg`/`ffprobe`, `wave.open`, `YOLO(...).predict(source=...)`, `np.load`, `torch.load`, raw `open(..., "rb")`/`read_bytes`/`os.open` hashing, PyAV, ImageIO, SoundFile, Librosa, Torchaudio); direct reading of each site; synthetic probes (`mission13_probes/probe_media.py`, `probe_server.py`, `probe_case.py`, `reader_scan.py`). **No repository media was opened, listed or hashed.** Probe paths were fake (non-existent) repository paths or temporary files.

PyAV, ImageIO, SoundFile, Librosa and Torchaudio: **no occurrences** in `src/`, `scripts/`, `research/`.

## 1. The four boundaries named by Mission 12

| File:line | Reader | Guard placement | Result |
|---|---|---|---|
| `src/railway_detection/data/manifest.py:152-154` | `PIL.Image.open` | `require_media_authorization(image_path, "READ_RAW_MEDIA")` is the line immediately before the open | **GUARDED** — but the call sits inside `try: … except Exception:` (see F13-07) |
| `src/railway_detection/data/validator.py:192-193`, `:202-203`, `:210` | `Image.open` ×2, `_file_sha256` | guard immediately before each reader | **GUARDED** — `_check_image` and `_read_dimensions` also swallow the denial (F13-07) |
| `research/scripts/generate_qualitative_figures.py:94, 155, 246, 252` | `YOLO.predict(source=path)`, `cv2.imread` | guard immediately before each | **GUARDED** at these sites; one unguarded `predict(source=str(p))` at `:139` (F13-14) |
| `research/scripts/generate_video_progression_figure.py:86, 130` | `cv2.VideoCapture`, `cv2.imread` | guard immediately before each (video guarded as `INFERENCE`, images as `READ_RAW_MEDIA`) | **GUARDED** |

Guard semantics verified in `safety/media_guard.py`: reads the on-disk record on every call; no environment switch (full-source search found none; probe F1 with six override variables set was still denied); resolves symlinks for *media-suffixed* names; `repo_root` override refused for in-repository paths (probe F2).

## 2. Adversarial results (probe IDs refer to `probe_media.py`)

| Test | Result |
|---|---|
| A1/A2 synthetic temp image/video | allowed (as designed) |
| B1/B2 unauthorized repository video/image | denied `AUTH_MEDIA_ACCESS_NOT_GRANTED` |
| C1 existing media outside the repo and outside temp | denied |
| C2 *absent* path outside the repo | allowed (no bytes exist; by design) |
| D1 temp symlink named `*.mov` → repository media | denied (target resolved) |
| **D2 temp symlink named `*.dat` → repository media** | **allowed — guard returns without checking (F13-03)** |
| **D3 temp symlink with no suffix → repository media** | **allowed (F13-03)** |
| E1 `../` traversal, E2 relative path, E3 `//` and `./` noise | denied |
| F1 environment overrides | denied |
| F2 `repo_root` redirect | denied `…ROOT_OVERRIDE_REFUSED` |
| **G suffix gaps** `.m2ts .ts .3gp .wmv .flv .gif .heic .mxf .dng .mov.bak`, no-suffix, `.bin` | **all allowed — `looks_like_media` is a fixed suffix list (`media_guard.py:56-61, 132-133`)** |
| H1-H3 direct calls into `validator._check_image/_read_dimensions/_file_sha256` | no `PIL.Image.open` call occurred (tripwire count 0); denial reported (but see F13-07) |
| **I1 evaluation input loader with a `*.mov` `source_path`** | **guard never called (0 calls); full file read and hashed; actual SHA-256 returned in the `SOURCE_HASH_MISMATCH` message (F13-01)** |
| **J case-variant repository path** (`…/train_automation/…`, same directory on case-insensitive APFS) | `is_synthetic_location` False but fake path returned silently; descriptive gate skipped entirely (F13-04, see governance audit) |
| **K demo dashboard `/outputs/../…` and `/experiments/../…`** (synthetic tree, `probe_server.py`) | **served `data/raw/ds/secret.mov` and `configs/c.yaml` with status 200 (F13-05)** |

The claim "Symlink resolution and environment-variable bypass behavior remain governed by the existing guard" (Mission 12) is true only for media-suffixed link names.

## 3. Coverage matrix

Status vocabulary: **G** verified guarded · **U** verified unguarded · **NA** not applicable (no raw media bytes) · **NT** guarded but not exercised by a test I could run · **?** uncertain.

| Reader / API | File:line | Media | Guard at reader | Direct-call protection | Test evidence | Status |
|---|---|---|---|---|---|---|
| `Image.open` | `data/manifest.py:154` | image | yes, adjacent | yes (denial swallowed) | M12 static tripwire; probe H | **G** (F13-07) |
| `Image.open` | `data/validator.py:193,203` | image | yes, adjacent | yes (denial swallowed) | probe H1-H2 | **G** (F13-07) |
| `_file_sha256` | `data/validator.py:209-215` | image | yes | yes | probe H3 | **G** |
| `cv2.imread` | `generate_qualitative_figures.py:156, 247` | image | yes | yes | static | **G** |
| `YOLO.predict(source=path)` | `generate_qualitative_figures.py:95, 253` | image | yes | yes | static | **G** |
| `YOLO.predict(source=path)` | `generate_qualitative_figures.py:139` | image | **no** (covered only because `find_representative_images` already guarded every file it visited) | no | none | **U at boundary** (F13-14) |
| `cv2.VideoCapture` | `generate_video_progression_figure.py:89` | video | yes | yes | static | **G** |
| `cv2.imread` | `generate_video_progression_figure.py:134` | image | yes | yes | static | **G** |
| `cv2.VideoCapture` | `vision/video.py:93` (guard `:80`) | video | yes | yes | M10 tests | **G** |
| `cv2.VideoCapture` | `demo/video_demo.py:432` (guard `:431`) | video | yes | yes | static | **G** |
| `cv2.imdecode` | `demo/server.py:456` | uploaded bytes | n/a (bytes from the HTTP body) | – | – | **NA** |
| **raw file streaming** | `demo/server.py:536-578` (`/outputs/`, opens at 565 and 577), `:580-594` (`/experiments/`, opens at 593) | any file under repo | **none; no containment check** | none | `probe_server.py` | **U (F13-05)** |
| ffmpeg/ffprobe | `data/audio_extractor.py:41-62` | video→audio | yes (`:33`) | yes | static | **G** |
| ffprobe / ffmpeg frame | `annotation/media_inspector.py:96, 184` | video | yes | yes | static | **G** |
| raw-byte hash | `annotation/media_inspector.py:73`, scripts `compute_sha256/get_sha256` ×10 | media | yes (first statement) | yes | opener tripwire | **G** |
| `wave.open` | `audio/preprocessor.py:46→50`; `scripts/{preprocess_audio_dataset*,build_audio_training_pipeline,estimate_camera_sync_offsets,train_audio_model}.py` | audio | function-level guard present | yes | opener tripwire (function level only) | **G** (ordering not machine-checked) |
| `experiments/layer_b_processor.py:337` | video inference | video | yes | yes | static | **G** |
| **`load_evaluation_input_manifest(verify_sources=True)` → `_read_source_bytes_and_hash`** | `evaluation/input_contracts.py:82-92, 213-216` | any in-root file incl. media suffixes | **none** | none | `probe_media.py` I1 | **U (F13-01)** |
| `sha256_file` | `evaluation/input_contracts.py:67-79` | media | yes | yes | static | **G** |
| `np.load` | `audio/dataset.py:114`; training scripts | processed features | media guard n/a | separate processed-data control (none enforced) | – | **NA to this guard; ? for processed-data policy** |
| `torch.load` / `compute_file_sha256` / `YOLO(checkpoint)` | `audio/model.py:204`, `frozen_config.py:184-195`, `layer_b_processor.py:124`, etc. | checkpoints | **no authorization control exists** (allowlisted in the tripwire as "weights, not media") | none | – | **U for checkpoints (F13-09)** |
| `cache_only_engine` JSONL cache reads | `evaluation/cache_only_engine.py:450,657-668` | processed caches | descriptive-authorization gate at the reader | bypassed by case-variant `repo_root` | static + probe J | **G with defect (F13-04)** |
| ffmpeg / `wave.open` / subprocess | **`scratch/analyze_train_events.py, analyze_forensic_results.py, analyze_audio.py, extract_frames.py, forensic_event_auditor.py, measure_ground_truth_v7.py, run_phase2_verification.py`** | video/audio | **none**; directory is git-ignored and outside the tripwire's scan roots | none | static text search | **U (F13-06)** |
| `benchmark_suite.py:574-583` | `model.predict` on seeded noise | none | – | – | – | **NA** |
| `subprocess` for `git`/`sysctl` | various | none | – | – | – | **NA** |
| PyAV / ImageIO / SoundFile / Librosa / Torchaudio | – | – | – | – | none present | **NA** |

**Complete coverage is not established.** Three raw-byte readers in repository code (F13-01, F13-05, plus the guard's suffix/alias gap in F13-03) and seven unguarded scripts in `scratch/` remain.

## 4. Why the Mission 12 static tripwire did not see these

`tests/unit/test_media_opener_coverage.py` marks a function guarded if the text `require_media_authorization(` appears *anywhere* in it, skips any function mentioning `frame_generator(`, and only recognises `VideoCapture(`, `Image.open(`/`cv2.imread(`, binary-read `wave.open`, ffmpeg/ffprobe subprocess strings, and raw-byte *hash* patterns. It therefore:

- does not check that the guard precedes the reader (F13-14 passes);
- does not detect `model.predict(source=path)`, `os.open`/`os.fdopen` reads, or raw reads that are not hashed (F13-05, F13-01);
- carries an allowlist entry for `input_contracts.py::load_evaluation_input_manifest` described as "reads the evidence manifest JSON", which hides the source-file reads (F13-13).

I ran this test (and `test_media_authorization.py`) under the read-blocking guard plugin after static review showed both use only temporary trees and source text: **76 passed, 0 blocked** (see the safe-runner audit). The pass is real but it is a tripwire for the patterns above, not a proof of coverage.

## 5. Findings

| ID | Sev | Finding |
|---|---|---|
| F13-01 | HIGH | Evaluation input loader reads/hashes in-root media-suffixed sources without authorization and leaks the digest in an error. |
| F13-03 | HIGH | `looks_like_media` is a suffix list applied to the *given* path; aliases (symlink/hardlink/rename) and unlisted suffixes bypass the guard. Hard links were already a disclosed limit; symlink aliases and suffix gaps were not. |
| F13-05 | HIGH | Dashboard `/outputs/` and `/experiments/` handlers serve any file under the project root after a `..` in the URL; no media guard, no containment. Default bind is `127.0.0.1`, so exposure is local processes unless `--host` is changed. |
| F13-06 | MEDIUM | `scratch/` holds seven unguarded ffmpeg/wave scripts outside every scan root. |
| F13-07 | MEDIUM | `manifest.py:151-163` and `validator.py:190-206` catch `Exception`, converting an authorization denial into "unreadable image / excluded sample". Reads stay blocked, but an unauthorized caller silently receives an empty or partial manifest. |
| F13-13 | MEDIUM | The opener tripwire is function-level, not order-aware, and its allowlist hides F13-01. |
| F13-14 | LOW | `generate_qualitative_figures.py:139` predicts on a path with no adjacent guard. |
| F13-04 | HIGH | Case-variant repository paths defeat path-identity checks (details in the governance audit). |

## 6. Disposition

Mission 11B finding **C-02 / R-H01** ("alternate media readers unguarded"): **PARTIALLY_FIXED**. The four named boundaries are guarded and the guard behaves as documented for temporary, media-suffixed and non-aliased paths. Material unguarded raw-byte readers remain, so the "no material unguarded reader remains" criterion is not met.
