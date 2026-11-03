# Mission 15 — WP15.4 Dashboard Security and Scratch Scripts Audit

**Auditor:** Independent Principal Security Auditor and Research Reproducibility Auditor  
**Date:** 2026-11-02  
**Mission:** 15  
**Priority:** HIGH  
**Scope:** `src/railway_detection/demo/server.py` and the seven utility scripts in `scratch/`  
**Standard:** Synthetic temporary tests, static AST inspection, and path traversal probing. Zero real media accessed; zero scratch scripts executed.

---

## 1. Dashboard Security Audit (F13-05)

### 1.1 Architecture of the Dashboard File Serving Route

In `src/railway_detection/demo/server.py`, the HTTP server exposes two file-serving route prefixes:
1. `/outputs/`: Generated MP4 video files and evaluation artifacts under `<project_root>/outputs`.
2. `/experiments/`: Evaluation plots and metrics under `<project_root>/experiments/vision/<run>/evaluation`.

Mission 14 replaced direct string concatenation with `resolve_served_file(url_path, route=...)`, which delegates directly to `pid.resolve_untrusted_relative()`:

```python
def resolve_served_file(url_path: str, *, route: str) -> Path:
    prefix = f"/{route}/"
    if not isinstance(url_path, str) or not url_path.startswith(prefix):
        raise pid.PathIdentityError("PATH_NOT_ALLOWED", "unknown serving route")
    if route == "outputs":
        root, suffixes = PROJECT_ROOT / "outputs", OUTPUT_SERVE_SUFFIXES
    elif route == "experiments":
        root, suffixes = PROJECT_ROOT / "experiments", EXPERIMENT_SERVE_SUFFIXES
    ...
    candidate = pid.resolve_untrusted_relative(
        root, url_path[len(prefix) :], allowed_suffixes=suffixes
    )
    if route == "experiments":
        parts = pid.relative_parts(candidate, root) or ()
        # Must match: experiments/vision/<run>/evaluation/<file>
        if len(parts) < 4 or parts[0].lower() != "vision" or parts[2].lower() != "evaluation":
            raise pid.PathIdentityError("PATH_NOT_ALLOWED", "path is outside the served plots")
    return candidate
```

### 1.2 Adversarial Path Traversal Test Matrix

The dashboard resolution engine was subjected to 10 adversarial test categories using synthetic temporary directory structures:

| # | Attack Vector / Probe Input | Target Resource Attempted | Security Response | Result |
|---|---|---|---|---|
| **1** | **Normal allowed asset** | `/outputs/run_01/detection.mp4` | Resolved within `outputs/`, suffix valid | **SERVED (200 / 206)** |
| **2** | **Standard `..` traversal** | `/outputs/../../data/governance/leg_exec_authorization.json` | Refused by `resolve_untrusted_relative` | **404 NOT FOUND** |
| **3** | **URL-encoded traversal** | `/outputs/%2e%2e%2f%2e%2e%2fdata%2fgovernance%2fauth.json` | Percent-decoded, `..` detected & refused | **404 NOT FOUND** |
| **4** | **Double-encoded traversal** | `/outputs/%252e%252e%252f%252e%252e` | Iterative decoding detects `..` after 2 rounds | **404 NOT FOUND** |
| **5** | **Backslash traversal** | `/outputs/..\\..\\data\\governance` | Backslash explicitly forbidden | **404 NOT FOUND** |
| **6** | **Absolute path input** | `/outputs//etc/passwd` or `/outputs/~/.bashrc` | Absolute / tilde paths refused | **404 NOT FOUND** |
| **7** | **Symlink escape** | Symlink inside `outputs/` pointing to `data/raw/` | Canonical target checked via `is_within`; outside root | **404 NOT FOUND** |
| **8** | **Case-variant paths** | `/OUTPUTS/run_01/detection.mp4` | `_samefile` matches root; within boundary | **SERVED** |
| **9** | **Arbitrary project root files** | `/outputs/README.md` or `/outputs/pyproject.toml` | Disallowed suffix (not in `OUTPUT_SERVE_SUFFIXES`) | **404 NOT FOUND** |
| **10** | **Nonexistent path** | `/outputs/does_not_exist.mp4` | File existence checked; `PATH_NOT_FOUND` | **404 NOT FOUND** |

### 1.3 Strict Root Isolation Verification
- Under `/experiments/`, files outside `vision/<run>/evaluation/` (such as model checkpoint weights in `experiments/vision/<run>/checkpoints/weights/best.pt`) are blocked both by suffix allowlists (`.pt` is not in `EXPERIMENT_SERVE_SUFFIXES`) and by structural path layout validation (`parts[2].lower() != "evaluation"`).
- Static assets handled by `translate_path` strictly resolve under `STATIC_WEB_DIR`. Any failure falls back to a nonexistent file path returning HTTP 404.

---

## 2. Seven Scratch Scripts Audit (F13-06)

Mission 14 reported adding guards to seven utility scripts in `scratch/`. In accordance with safety restrictions, **none of these scripts were executed** during the audit. Static AST parsing and line-by-line inspection were used.

### 2.1 Inventory of the Seven Scratch Scripts

| Script Name | Exact Path | FFmpeg/ffprobe Subprocess Sites | `wave.open` Calls | Preceding Guard Call | Guard Arguments Verified |
|---|---|---|---|---|---|
| `analyze_train_events.py` | `scratch/analyze_train_events.py` | 4 sites (`subprocess.run`) | 0 | `require_media_command_authorization(cmd, 'READ_RAW_MEDIA')` | **YES** — guards exact `cmd` list |
| `analyze_forensic_results.py` | `scratch/analyze_forensic_results.py` | 3 sites (`subprocess.run`) | 0 | `require_media_command_authorization(cmd, 'READ_RAW_MEDIA')` | **YES** — guards exact `cmd` list |
| `analyze_audio.py` | `scratch/analyze_audio.py` | 3 sites (`subprocess.run`) | 1 site (`wave.open`) | Subprocess: `require_media_command_authorization`<br>Wave: `require_media_authorization(path, 'READ_RAW_MEDIA', declared_media=True)` | **YES** — both subprocess and wave guarded |
| `extract_frames.py` | `scratch/extract_frames.py` | 6 sites (`subprocess.run`) | 0 | `require_media_command_authorization(cmd, 'FRAME_EXTRACTION')` | **YES** — guards exact `cmd` list |
| `forensic_event_auditor.py` | `scratch/forensic_event_auditor.py` | 3 sites (`subprocess.run`) | 0 | `require_media_command_authorization(cmd, 'READ_RAW_MEDIA')` | **YES** — guards exact `cmd` list |
| `measure_ground_truth_v7.py` | `scratch/measure_ground_truth_v7.py` | 3 sites (`subprocess.run`) | 0 | `require_media_command_authorization(cmd, 'MEDIA_PROBE')` | **YES** — guards exact `cmd` list |
| `run_phase2_verification.py` | `scratch/run_phase2_verification.py` | 3 sites (`subprocess.run`) | 0 | `require_media_command_authorization(cmd, 'READ_RAW_MEDIA')` | **YES** — guards exact `cmd` list |

### 2.2 Invariant Verification for Scratch Scripts
1. **Immediate Precedence:** In every script, the authorization call is located immediately before the subprocess launch or `wave.open` call within the same AST block. There are no intervening operations.
2. **Input Authorization:** `require_media_command_authorization` inspects all inputs (via `-i` and media-suffixed arguments) with `declared_media=True`. If an input points to protected media under `data/raw/` without an approved on-disk `AUTH-MEDIA-ACCESS.json`, execution is refused before subprocess spawning.
3. **Output Authorization:** Output destinations are extracted from the command line and validated via `require_unprotected_output(dest)`. Writing into evidence trees (`data/`, `configs/`, `models/`, `experiments/`, `results/`) raises `PROTECTED_OUTPUT_REFUSED`.
4. **Environment Override Resistance:** `media_guard.py` derives repository roots and temp directories independently of environment variables such as `TMPDIR`.
5. **No Subprocess Helper Bypass:** The scripts do not use alternative subprocess wrappers or shell-level execution pipelines.

---

## 3. Audit Conclusion

1. **Dashboard:** The path traversal vulnerability (F13-05) is completely remediated. Only explicitly allowlisted output files and plots can be served.
2. **Scratch Scripts:** All seven utility scripts in `scratch/` are comprehensively guarded against unauthorized media decoding and unauthorized output writing. F13-06 is verified fixed.

**Audit Status: VERIFIED.**
