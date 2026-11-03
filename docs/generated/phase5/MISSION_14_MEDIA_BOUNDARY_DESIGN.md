# Mission 14 — WP14.1 Centralised Media-Access Boundary: Design, Coverage and Limits

**Scope:** `src/railway_detection/safety/media_guard.py` (modified), `src/railway_detection/safety/path_identity.py` (new), reader call sites listed in §4.
**Trust boundary (unchanged and stated plainly):** this is a Python-level software guard on this repository's code paths. It is **not** cryptographic authorization and **not** an OS sandbox. Native code, shell tools run outside these wrappers, hard links and copies made by other means are outside it.

## 1. Why the old design failed

Mission 13 found `looks_like_media(path)` decided from the suffix of the path *as given*. A symlink named `*.dat`, an extensionless file, `clip.mov.bak`, and unlisted suffixes (`.m2ts .ts .3gp …`) returned without any check. Repository membership was a string comparison, so a case-variant spelling of the checkout was "elsewhere".

## 2. Design: resource classification first, operation authorization second

Three questions are now separate:

| Question | Answered by |
|---|---|
| **What resource is this?** (path authorization input) | `classify_resource(path, declared_media=False)` → `ResourceDecision(zone, guarded, real, reason)` |
| **Is this operation authorized for it?** | `verify_authorization_record(root, operation, media_path, event_id)` — unchanged record schema, read from disk on every call |
| **May a tool write here?** | `require_unprotected_output(path)` |

`classify_resource` canonicalises the path (`path_identity.canonical_path`: `~` expanded, symlinks resolved, nonexistent tail kept under its resolved parent, NUL/empty/loop/OS error ⇒ `UNRESOLVABLE`, which is **guarded**), then decides **by location first, name second**:

| Zone | Rule | Guarded? |
|---|---|---|
| `UNRESOLVABLE` | cannot canonicalise | **yes (refused: `AUTH_MEDIA_PATH_UNRESOLVABLE`)** |
| `REPO_RAW` | real location under `<repo>/data/raw`, **any name or suffix**; exception: given *and* resolved names both carry a known plain-text suffix (`.json .txt .yaml .csv …`) and the reader did not declare media | yes |
| `REPO_MEDIA_LIKE` | elsewhere in the repository, media suffix on the given **or the resolved** name, or `declared_media=True` | yes |
| `REPO_OTHER` | repository, not media (configs, source, JSON) | no |
| `SYNTHETIC_TEMP` | real location inside a **fixed** list of OS temp roots (`/tmp /private/tmp /var/tmp /var/folders …`) and outside the repository. `TMPDIR` and every environment variable are ignored | no |
| `EXTERNAL_MEDIA_LIKE` | outside repo and temp; media suffix **or an unrecognised suffix** or `declared_media=True` | yes (absent paths: no bytes, no-op — pre-existing, tested behaviour) |
| `EXTERNAL_OTHER` | outside repo and temp, known non-media suffix | no |

`declared_media=True` is set by reader call sites that know they are about to decode media; it can only make a decision stricter. Suffix lists were widened (video 30, audio 23, image 25 = 78 media suffixes; 39 known non-media) and a known-non-media list was added so JSON/YAML hashing helpers keep working. Archives (`.zip .gz .tar`) are **not** on the non-media list.

Why "synthetic by location, not by name": a file called `synthetic_fixture_tmp.jpg` under `data/raw` is `REPO_RAW`; the same name in a temp directory is `SYNTHETIC_TEMP`. A temp-resident symlink whose target is in the repository is classified by the target.

## 3. Shared canonicalisation

All "is X inside Y" decisions go through `safety/path_identity.py` (details in `MISSION_14_PATH_CANONICALIZATION.md`): comparison by filesystem identity (`os.path.samefile` on ancestors) so case variants, Unicode-normalisation variants and firmlink spellings agree; fold-compare fallback when a reference tree does not exist (over-matches, never under-matches).

## 4. Where enforcement happens (operation boundary)

| Operation | Boundary (immediately before the read) |
|---|---|
| raw hash | `input_contracts.sha256_file`, `_read_source_bytes_and_hash`; `validator._file_sha256`; `media_inspector.compute_file_sha256`; `leakage_guard`, `experiment_engine`, scripts' hash helpers (unchanged, location-aware now) |
| image decode | `data/manifest.py` (`Image.open`), `data/validator.py` (`_check_image`, `_read_dimensions`) — guard moved **outside** the `try` so a denial propagates (F13-07) |
| video decode | `vision/video.py:frame_generator`, `demo/video_demo.py:process_video`, `experiments/layer_b_processor.py`, `research/scripts/generate_video_progression_figure.py` |
| audio | `audio/preprocessor.py`, `data/audio_extractor.py` |
| ffmpeg/ffprobe | `annotation/media_inspector.py`; **new** `require_media_command_authorization(cmd, op)` (parses `-i` inputs, ffprobe operand, media-suffix operands, trailing `-y`-style flags; refuses unknown tools / no input; output operand must not be in `data configs models experiments results`) |
| model `predict(source=path)` | `research/scripts/generate_qualitative_figures.py` (adjacent guard added at line 139 — F13-14) |
| HTTP file serving | allowlisted roots, see `MISSION_14_DASHBOARD_SECURITY.md`; `/api/process` guarded |
| evaluation manifest + sources | `load_evaluation_input_manifest`, see `MISSION_14_EVALUATION_INPUT_SECURITY.md` |
| scratch scripts | seven scripts, see `MISSION_14_SCRATCH_MEDIA_SCRIPT_AUDIT.md` |

Unchanged by design: the authorization record (`phase5-media-access-authorization/2`), its signer allowlist, expiry, revocation, scope and protocol-binding checks. **No authorization record was created or modified.**

## 5. Updated reader inventory (supersedes the Mission 13 matrix where different)

| Reader / API | Status after Mission 14 | Evidence |
|---|---|---|
| `Image.open` manifest/validator | guarded, denial propagates, `declared_media` | `test_validator_and_manifest_refuse_before_any_image_reader` |
| `cv2.VideoCapture` (`video.py`, `video_demo.py`, figure script, `layer_b_processor`) | guarded, `declared_media` | `test_video_audio_and_frame_readers_refuse_before_decoding` |
| ffmpeg/ffprobe (`audio_extractor`, `media_inspector`) | guarded before subprocess | same test |
| ffmpeg in `scratch/` (7 scripts, 9 launch sites) | guarded immediately before launch | `test_security_scratch_scripts.py` |
| `wave.open` (`preprocessor`, scripts, `scratch/analyze_audio.py`) | guarded | opener tripwire + scratch tests |
| `predict(source=path)` figure script (all 3 sites) | guarded | opener tripwire (order-aware) |
| evaluation input loader sources | guarded before open/hash; no digest in errors | `test_security_evaluation_input.py` |
| dashboard `/outputs/`, `/experiments/`, static | allowlisted root + canonical containment | `test_security_dashboard.py` |
| `np.load`, `torch.load`, `compute_file_sha256` of checkpoints | **not media**; no authorization control exists (Mission 13 F13-09, **open, researcher decision**) | unchanged |
| PyAV / ImageIO / SoundFile / Librosa / Torchaudio | none present | text search |

## 6. Tests (all synthetic; fake repository in a temp dir, `REAL_REPO_ROOT` patched)

`tests/unit/test_security_media_boundary.py` — 55 tests: 22 media suffixes denied in the repository; 9 name patterns denied under `data/raw` (extensionless, `.bin`, `.mov.bak`, `CLIP.MOV`, `.zip`, unknown suffix …); text metadata exempt but re-guarded by `declared_media`; decoy "synthetic-looking" names denied; symlink aliases (`.dat`, none, `.txt`, `.json`, `.mov`), chains, directory symlinks, broken symlinks, symlink loop (fails closed); relative / absolute / `..` / `//./` traversal; NUL and empty path; **case-variant repository path** (skipped on a case-sensitive FS); synthetic temp allowed by location; nonexistent targets; external media and unknown files; environment variables (including `TMPDIR`) cannot grant or redefine temp; `repo_root` override refused; **hash / image / video / audio / ffmpeg refusals proven to occur before the protected operation** (tripwires on `os.open`, `Path.open`, `Image.open`, `cv2.VideoCapture`, `subprocess.run/Popen` raise `AssertionError` if reached); ffmpeg command parsing and output-zone refusal; observer sees the canonical path.

## 7. Residual limits (not fixed, stated)

1. Hard links, bind mounts created after the check, and files copied into a temp directory by other means.
2. A file swapped between check and use (TOCTOU).
3. A media file with an unrecognised suffix stored in the repository *outside* `data/raw`, read through a call site that does not pass `declared_media=True`.
4. Text-suffixed files under `data/raw` are treated as metadata unless a reader declares media.
5. Dashboard-served derived outputs in `outputs/` are served by containment, not by the media guard.
6. Native code / shell tools outside these wrappers; no OS-level isolation.
