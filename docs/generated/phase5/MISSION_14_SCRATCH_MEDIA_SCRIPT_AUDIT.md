# Mission 14 — WP14.5 `scratch/` FFmpeg Scripts (F13-06)

`scratch/` is git-ignored (no history). Every file below was backed up to `docs/generated/phase5/mission14_pre_edit_backup/scratch/` **before** being edited (`SHA256SUMS.txt`). No script was deleted, renamed, imported or executed; FFmpeg was never launched.

## 1. Inventory — the seven scripts

Common pattern in each: hard-coded `data/raw/layer_b/v2/{train,no_train,engine}_events/…/camera_{front,back}.mov` (or paths read from `data/manifests/layer_b_v2_annotation_inventory.json`), a one-off analysis, and results written into `scratch/`.

| # | Script | FFmpeg launch sites (after edit) | Input | Output | Can touch repository media? | Operation |
|---|---|---|---|---|---|---|
| 1 | `analyze_train_events.py` | `:50` and `:63` (`Popen`, frames to stdout) — guard `:49`, `:62` | inventory `front.path` / `back.path` (raw `.mov`) | stdout → in-memory arrays; JSON in `scratch/` | **yes** | `FRAME_EXTRACTION` |
| 2 | `analyze_forensic_results.py` | `:67` (`Popen`, audio to stdout) — guard `:66` | `RAW_DIR/train_events/<ev>/camera_front.mov` | stdout; JSON in `scratch/` | **yes** | `AUDIO_EXTRACTION` |
| 3 | `analyze_audio.py` | `:32` (`run`) — guard `:31`; also `wave.open` `:36` — guard `:35` | `data/raw/layer_b/v2/train_events/event_001/camera_{front,back}.mov` | `scratch/pilot_inspection_event_001/*_audio.wav`, then read back | **yes** | `AUDIO_EXTRACTION`, `FEATURE_EXTRACTION` |
| 4 | `extract_frames.py` | `:41` and `:51` (`run`) — guard `:40`, `:50` | `event_001` front/back `.mov` | `scratch/pilot_inspection_event_001/*.jpg` (**overwrites** with `-y`) | **yes** | `FRAME_EXTRACTION` |
| 5 | `forensic_event_auditor.py` | `:56` (`run`) — guard `:55` (inside `extract_frame_at`) | `RAW_DIR/train_events/<ev>/camera_*.mov` | `scratch/forensic_inspection/*.jpg` (`-y`) | **yes** | `FRAME_EXTRACTION` |
| 6 | `measure_ground_truth_v7.py` | `:66` (`Popen`) — guard `:65` | `…/camera_front.mov` | stdout | **yes** | `AUDIO_EXTRACTION` |
| 7 | `run_phase2_verification.py` | `:64` (`Popen`) — guard `:63` (inside `extract_audio_snr`) | `…/camera_*.mov` | stdout | **yes** | `AUDIO_EXTRACTION` |

(9 launch sites + 1 `wave.open`.) Every site is `require_media_command_authorization(cmd, op)` (or `require_media_authorization(path, op, declared_media=True)`) as the **immediately preceding statement**, on the same command variable. The helper checks every `-i` input as declared media, refuses outputs inside `data configs models experiments results`, and refuses an unrecognised tool or a command with no identifiable input. Absolute-path binaries (`/opt/homebrew/bin/ffmpeg`) are recognised by basename. Environment variables are not consulted. Each script gained the same short bootstrap block (adds `<repo>/src` to `sys.path` from `__file__`, imports the shared guard); no other line changed.

Behavior now: without a recorded AUTH-MEDIA-ACCESS (none exists) every script refuses **before** the subprocess is created or the WAV opened; with synthetic temporary inputs the original behavior is unchanged.

## 2. The other six `scratch/*.py` files

| Script | Media tool use | Finding |
|---|---|---|
| `physical_frame_inspector.py` | imports `subprocess`, never launches it | no media operation |
| `dense_event_measurer.py` | imports `subprocess`, never launches it; reads inventory JSON; `Image` import only | none |
| `audit_train_events.py`, `compute_candidates.py` | JSON analysis only | none |
| `generate_v7_proposals.py` | writes annotation **proposal** JSON through the repository schemas; names `camera_*.mov` only as strings | no media read |
| `run_unit_tests.py` | runs `tests.test_annotation_workflow` | no media read |

**Governance observation (not changed, for the researcher):** `run_phase2_verification.py` also *writes* `data/ground_truth/reviews/*_review.json` records. Its only media step (`extract_audio_snr`, launch `:64`, called at `:146-147` in the first, train-events loop) is now guarded and runs before every review write in the file (`:333`, `:409`, `:505`), so when the guard refuses the script aborts before writing any review record. The script is otherwise untouched and its purpose is not a Mission 14 decision. Human-review artifacts must not be created by scripts; flagging this is not an approval or an action.

## 3. Obsolescence

Nothing was disabled or removed. Several scripts target a single event (`event_001`) and look one-off, but their status is a researcher decision; they are guarded, not retired.

## 4. Tests — `tests/unit/test_security_scratch_scripts.py` (24)

* **Static (AST):** all 9 launch sites in the seven scripts are immediately preceded by `require_media_command_authorization` **on the same command variable**; every `wave.open` in `scratch/` is preceded by `require_media_authorization`; no `scratch/*.py` launches a process unguarded; each of the seven imports the shared guard (not a local copy).
* **Dynamic (real function bodies extracted from the scripts, executed with a recording `subprocess` stand-in against a fake repository):** `extract_frame_at` and `extract_audio_snr` refuse protected raw input before any launch; an innocent-named symlink (`notes.txt`) to raw media is refused; a **synthetic** input with an **evidence-tree output** is refused (`PROTECTED_OUTPUT_REFUSED`) before launch; a synthetic input with a `scratch/` output reaches the launch (stand-in proves exactly one launch with the expected input); `analyze_wav` refuses before `wave.open`; six environment variables set ⇒ still refused.
* The scripts are **not imported** (they do I/O at import time); the module-level scripts (1, 4, 6 partially) are covered statically.
* The shared tripwire `tests/unit/test_media_opener_coverage.py` now scans `scratch/`, module-level code, full-path `ffmpeg` names and guard-before-reader order, with four self-tests proving it detects each.

## 5. Residual

`scratch/` remains git-ignored and therefore unpreserved by Git; the guarded versions and the pre-edit backups exist only in the working tree (F13-17). A copy of any script placed outside `scratch/` would not be covered by the scratch-specific tests (the repository-wide tripwire scans `src scripts research scratch`).
