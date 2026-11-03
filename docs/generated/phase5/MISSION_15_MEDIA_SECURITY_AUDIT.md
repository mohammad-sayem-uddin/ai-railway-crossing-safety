# Mission 15 — WP15.1 Central Media Security Boundary Audit

**Auditor:** Independent Principal Security Auditor and Research Reproducibility Auditor  
**Date:** 2026-11-02  
**Scope:** `src/railway_detection/safety/path_identity.py`, `src/railway_detection/safety/media_guard.py`, and all consuming caller sites  
**Priority:** CRITICAL  
**Verification Method:** Static AST analysis, dynamic adversarial synthetic probes, and code path tracing.  
**Constraint:** Synthetic temporary files and synthetic repositories only. Zero production media accessed.

---

## 1. Architectural Architecture and Threat Model

Mission 14 introduced a dedicated filesystem-identity module:
- `src/railway_detection/safety/path_identity.py` (207 lines)
and refactored the central media guard:
- `src/railway_detection/safety/media_guard.py` (699 lines)

### 1.1 Shift from Suffix-First to Location-First Classification

In earlier missions (prior to Mission 14), `media_guard.py` classified media primarily by checking whether `path.suffix.lower() in MEDIA_SUFFIXES`. As Mission 13 identified (finding F13-03), this was fundamentally flawed:
1. An alias (such as a symlink or hardlink) with an innocent suffix (e.g., `data.txt`) pointing to raw media under `data/raw/` bypassed the guard completely.
2. Extensionless files or files with unlisted suffixes under `data/raw/` were not recognized as media.
3. Case-variants (e.g. `DATA/RAW` vs `data/raw`) on macOS APFS filesystems evaded string-based `is_relative_to` checks (F13-04).

Mission 14 repaired this with `classify_resource(path, declared_media=...)`:
- **Canonical resolution:** `pid.canonical_path(path)` resolves `~`, converts relative paths to absolute, resolves symlinks, and validates that the path contains no NUL bytes, control characters, or unresolvable loops.
- **Identity containment:** `pid.is_within(real, parent)` uses `os.path.samefile` on existing ancestors to confirm whether the real filesystem object resides within the repository or specific subtrees.
- **Zone determination:**
  - `REPO_RAW`: Any file whose resolved canonical location is within `REAL_REPO_ROOT / "data" / "raw"` is guarded **regardless of name or suffix**, with the sole exception of files where both given and resolved suffixes are in `KNOWN_NON_MEDIA_SUFFIXES` (such as `.json`, `.yaml`, `.csv` metadata), *unless* the caller explicitly passes `declared_media=True`.
  - `REPO_MEDIA_LIKE`: Any file in the repository whose given or resolved suffix matches the 78 recognized media suffixes.
  - `EXTERNAL_MEDIA_LIKE`: Any file outside the repository with a media suffix or an unlisted/ambiguous suffix.
  - `SYNTHETIC_TEMP`: Files residing within designated OS temporary trees (`/tmp`, `/private/tmp`, `/var/tmp`, `/var/folders`) outside the repository. Location in OS temp, not a temporary file name or environment variable, establishes synthetic status.
  - `UNRESOLVABLE`: Any malformed or looping path fails closed with `guarded=True`.

---

## 2. Operation Boundary Verification Across Protected Operations

The audit verified that every protected operation enforces authorization at the lowest layer before byte access:

| Operation Type | Implementation Boundary | Lowest Enforcement Point | Pre-Operation Refusal Verified? |
|---|---|---|---|
| **File Opening** | `builtins.open`, `pathlib.Path.open` | `media_guard.require_media_authorization` at opener | **YES** — verified; refusal occurs before descriptor creation |
| **File Hashing** | `sha256_file`, `_read_source_bytes_and_hash` | `require_media_authorization(path, 'HASH_RAW_MEDIA')` before `open()` | **YES** — zero bytes read or hashed on denial |
| **Media Decoding** | `cv2.VideoCapture`, `cv2.imread`, `PIL.Image.open` | Guard call with `declared_media=True` preceding decode | **YES** — decoder constructor never executed |
| **Image Reading** | `manifest.py`, `validator.py`, `media_inspector.py` | Guard placed outside `try/except` block | **YES** — errors propagate, not swallowed (F13-07 fixed) |
| **Video Reading** | `vision/video.py`, `demo/video_demo.py` | `require_media_authorization(..., 'READ_RAW_MEDIA', declared_media=True)` | **YES** — verified in video streaming & frame generators |
| **Audio Reading** | `audio/preprocessor.py`, `data/audio_extractor.py`, `wave.open` | Guard immediately preceding audio read / extraction | **YES** — verified across audio pipelines |
| **File Copying** | `shutil.copy`, manual chunk copy | Pre-read authorization check on source | **YES** — protected sources blocked from copy |
| **Dashboard Serving** | `demo/server.py` (`/outputs/`, `/experiments/`) | `resolve_served_file` via `pid.resolve_untrusted_relative` | **YES** — traversals and non-whitelisted paths return HTTP 404 |
| **Protected Output Writing** | Pipeline export, evaluation output | `media_guard.require_unprotected_output(dest)` | **YES** — attempts to write into `data/`, `configs/`, `models/`, `experiments/`, `results/` refused |
| **Cache Loading** | `evaluation/cache_only_engine.py` | `pid.is_within` identity check on cache paths | **YES** — symlink / case escape outside cache root blocked |
| **Evaluation Manifest Loading** | `evaluation/input_contracts.py` | Header parsed without reading sources; sources guarded before open | **YES** — zero source reads on REAL or unauthorized manifest |
| **Subprocess Invocation** | `subprocess.run/Popen` (`ffmpeg`, `ffprobe`) | `require_media_command_authorization(cmd, operation)` | **YES** — subprocess not spawned on unauthorized inputs |

---

## 3. Adversarial Test Suite Results (20/20 PASSED)

An independent adversarial probe suite was executed using synthetic temporary fixtures and paths. All 20 test cases confirmed fail-closed rejection prior to protected operations:

| # | Test Scenario | Description / Input | Observed Behavior | Verdict |
|---|---|---|---|---|
| **1** | **Known media suffixes** | `.mp4`, `.mov`, `.wav`, `.jpg`, `.avi` | Classified `REPO_MEDIA_LIKE`, guarded | **PASS** |
| **2** | **Unknown media suffixes** | `.xyz`, `.blob`, `.media` under `data/raw` vs external | `data/raw` is `REPO_RAW` (guarded); external is `EXTERNAL_MEDIA_LIKE` (guarded) | **PASS** |
| **3** | **Extensionless files** | `raw_stream`, `video_feed` under `data/raw` | Classified `REPO_RAW` and guarded | **PASS** |
| **4** | **Renamed media-like files** | `recording.txt` accessed with `declared_media=True` | `declared_media` overrides text suffix; guarded | **PASS** |
| **5** | **Symlink aliases** | Symlink `innocent.txt` in temp pointing to `data/raw/video.mp4` | Canonical path resolves to `data/raw`; classified `REPO_RAW`, guarded | **PASS** |
| **6** | **Broken symlinks** | Symlink in temp pointing to nonexistent `data/raw/missing.mp4` | Canonical resolution tracks destination under `data/raw`; guarded | **PASS** |
| **7** | **Directory symlinks** | Symlink `temp/raw_alias` -> `data/raw`, target `raw_alias/any` | Resolved ancestor matches `data/raw`; guarded | **PASS** |
| **8** | **Relative path traversal** | `tests/../data/raw/video.mp4` | Resolves canonical path inside `data/raw`; guarded | **PASS** |
| **9** | **Absolute path traversal** | Full absolute path string to `data/raw/video.mp4` | Resolves to repository `data/raw`; guarded | **PASS** |
| **10** | **Case-variant paths** | `.../TRAIN_AUTOMATION/DATA/RAW/VIDEO.MP4` | `_samefile` ancestor matching confirms identical inode/location; guarded | **PASS** |
| **11** | **Nonexistent target paths** | `data/raw/nonexistent_clip.mp4` | Preserves nonexistent tail under canonical `data/raw`; guarded | **PASS** |
| **12** | **Nonexistent parent components** | `data/raw/no_dir/no_sub/clip.mp4` | Nonexistent components stay rooted below canonical `data/raw`; guarded | **PASS** |
| **13** | **Unicode path variants** | NFD-normalized vs NFC-normalized filenames (`vïdeo.mp4`) | `_fold()` normalizes to NFC and casefolds; identity matches; guarded | **PASS** |
| **14** | **URL-encoded path variants** | `%2e%2e%2f`, double-encoded `%252e%252e` in server paths | `_decode_fully()` decodes up to 4 rounds; refuses traversal with `PathIdentityError` | **PASS** |
| **15** | **Environment variable overrides** | Setting `TMPDIR=/path/to/data/raw` | `_TEMP_ROOT_CANDIDATES` uses fixed OS list; ignores `TMPDIR`; guarded | **PASS** |
| **16** | **Direct library reader calls** | Simulating decode attempt on text file with `declared_media=True` | `require_media_authorization` raises `MediaAccessAuthorizationError` before read | **PASS** |
| **17** | **Alternate helper calls** | `require_media_command_authorization` on `ffmpeg -i data/raw/v.mp4 out.jpg` | Raises before subprocess execution | **PASS** |
| **18** | **Unauthorized hashing** | `input_contracts.sha256_file(data/raw/video.mp4)` | Raises `MediaAccessAuthorizationError` before `open()`; zero bytes read | **PASS** |
| **19** | **Unauthorized reading** | `input_contracts._read_source_bytes_and_hash(data/raw/video.mp4)` | Raises before `open()`; zero bytes read or hashed | **PASS** |
| **20** | **Unauthorized output creation** | `require_unprotected_output(data/raw/new_artifact.json)` | Raises `PROTECTED_OUTPUT_REFUSED` for all protected zones (`data`, `configs`, `models`, `experiments`, `results`) | **PASS** |

---

## 4. Deep Inspection of `safety/path_identity.py`

### 4.1 Canonicalization & macOS Case-Insensitivity
On macOS APFS filesystems, files are case-preserving but case-insensitive. Standard Python `Path.resolve()` preserves the caller's case spelling for paths, meaning `Path("/path/to/repo").resolve() == Path("/PATH/TO/REPO").resolve()` evaluates to `False`.

`path_identity.py` solves this via `_samefile`:
```python
def _samefile(left: Path, right: Path) -> bool | None:
    try:
        return os.path.samefile(left, right)
    except (FileNotFoundError, NotADirectoryError, OSError):
        return None
```
When `_samefile` is called on existing filesystem objects or ancestors, it queries filesystem device and inode numbers (`stat().st_ino`, `stat().st_dev`). If a path does not yet exist, it falls back to `_folded_parts`, performing `unicodedata.normalize("NFC", text).casefold()` on every component. This ensures case variants are reliably recognized.

### 4.2 Component-Aware Containment vs String-Prefix
A common security vulnerability is string-prefix matching: e.g., `str(path).startswith(str(root))`, where `/repo/data/raw_fake` matches `/repo/data/raw`.

`path_identity.is_within` does NOT use string prefixes. It uses ancestor traversal:
```python
for ancestor in (path, *path.parents):
    if _samefile(ancestor, root):
        return ancestor
```
This guarantees that matching is component-aware and structurally validated against filesystem objects.

### 4.3 Python-Level Trust Boundary vs OS Isolation
As explicitly documented in `path_identity.py` and `media_guard.py`:
- These controls operate within the Python runtime environment of this repository.
- They intercept calls to repository APIs, CLI tools, scripts, and helper modules.
- They do **not** provide operating system-level sandboxing (e.g. `chroot`, Linux namespaces, macOS sandbox-exec). Direct native shell calls outside Python (such as executing `cat data/raw/...` directly in bash) are outside the scope of Python-level guards.
- This boundary is transparently disclosed in documentation and is appropriate for the Phase 5 engineering recovery scope.

---

## 5. Audit Conclusion

The central media security boundary in `safety/path_identity.py` and `safety/media_guard.py` is soundly designed, correctly wired to all identified readers and entry points, and robust against adversarial bypass attempts within the Python application layer.

**Audit Status: VERIFIED.**
