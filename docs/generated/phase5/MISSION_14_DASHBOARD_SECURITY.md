# Mission 14 — WP14.4 Dashboard File-Serving Security (F13-05)

**File changed:** `src/railway_detection/demo/server.py` (tracked, already modified before Mission 14; backup of the pre-edit state in `mission14_pre_edit_backup/`). **Tests:** `tests/unit/test_security_dashboard.py` (50) plus a one-off real-socket smoke test on a synthetic tree (below). No real project document, media or checkpoint was served or read.

## 1. What was wrong

`_handle_serve_output_file` (`/outputs/…`) and `_handle_serve_experiment_file` (`/experiments/…`) built `PROJECT_ROOT / url_path.lstrip("/")`, resolved it, checked only that it existed and was a file, and streamed it. A client that sends `..` unnormalised (`curl --path-as-is`, any script) could read raw media, configs, checkpoints or governance records from the whole project root. The SPA fallback and the stdlib static handler also trusted the raw URL path.

## 2. What the routes do now

| Route | Allowlisted root | Allowed file types | Extra constraint |
|---|---|---|---|
| `/outputs/<path>` | `<project>/outputs` | `.mp4 .webm .json .jpg .jpeg .png .csv .txt` | none |
| `/experiments/<path>` | `<project>/experiments` | `.png .jpg .jpeg .svg .json .csv .txt` | path must be `vision/<run>/evaluation/<file>` (checkpoints, weights and everything else under `experiments/` are never served) |
| static (`/`, `/app.js`, …) | `demo/web` | any file inside it | `translate_path` overridden; SPA-fallback existence test uses the same resolver |

All three go through `path_identity.resolve_untrusted_relative`: full percent-decoding to a fixed point (max 4 rounds ⇒ `PATH_OVER_ENCODED`), refusal of control characters / NUL / backslashes / absolute forms / `..`-like components, **then canonicalisation and identity-containment in the root after symlink resolution**, then the suffix allowlist and "regular file" check. It does **not** strip `..` and hope. Every refusal is one generic `404 File not found` — no existence oracle, no echo of the requested or resolved path. Added `X-Content-Type-Options: nosniff`; byte-range requests are clamped (`start<0`, `start>end`, non-numeric ⇒ full response instead of an exception path).

`/api/process` now runs `require_media_authorization(video_path, "INFERENCE", declared_media=True)` before creating an output directory or starting a thread; denial ⇒ `403 {"error": "media access is not authorized for this path"}` (no path echoed).

## 3. Evidence

### Unit tests (fake connection, synthetic project tree)

* Allowed: MP4, JSON, evaluation plot served with correct bytes and `nosniff`; byte ranges `2-4`, `5-999999`, and three malformed ranges.
* **21 outputs-route denials** and **11 experiments-route denials**, each asserting `404` *and* an empty body: `..`, nested `..`, `%2e%2e`, `%2E%2E%2F`, double `%252e`, triple `%25252e…%25252f`, `..%2f`, backslash, `%5c`, mixed, absolute `//etc/passwd`, `%2fetc%2fpasswd`, `....//`, NUL-in-name, other tree names, a non-served type (`.py`), `.pt` weights, a plot outside `evaluation/`, missing files, directories, wrong route prefix.
* Symlink escapes: file → raw media, directory → raw directory, file → checkpoint, directory → outside tree ⇒ all 404; an *internal* symlink is still served.
* Case: `/outputs/VIDEO_TESTS/run1/SUMMARY.JSON` served (same resource); `…/../CONFIGS/…` refused; `/experiments/VISION/…/CHECKPOINTS/…/best.pt` refused; a case-variant `PROJECT_ROOT` neither widens nor narrows what is served.
* Static: asset, nested asset, `/`, query/fragment stripped; 8 escape attempts translate inside the static directory or to a not-found sentinel; a symlink escape is not served.
* `/api/process`: protected raw media, extensionless raw file, `.m2ts` in the repo ⇒ `403`, no thread, no output directory, path not echoed; synthetic temp video still accepted.

### Real-socket smoke test (synthetic tree in a temp dir, `http.client`, paths sent as-is)

```
/                                         -> 200 (SPA page)
/app.js                                   -> 200
/outputs/video_tests/r/a.mp4              -> 200 (OKVIDEO)
/outputs/../data/raw/ds/secret.mov        -> 404
/outputs/%2e%2e/data/raw/ds/secret.mov    -> 404
/outputs/%252e%252e/data/raw/ds/secret.mov-> 404
/outputs/..%5cdata%5craw%5cds%5csecret.mov-> 404
/experiments/../configs/c.yaml            -> 404
/../configs/c.yaml  /%2e%2e/configs/c.yaml  /etc/passwd -> 200 SPA index.html (pre-existing SPA fallback; the requested file is never returned)
```

Mission 13's `probe_server.py` (same synthetic tree) returned `200` with the secret bytes for the first four traversals; it now returns `404`.

## 4. Residual limits

* Derived outputs under `outputs/` (annotated videos produced by this dashboard) are protected by **containment**, not by the media guard (they would otherwise need AUTH-MEDIA-ACCESS to be previewed). A file placed in `outputs/` by other means is servable; a symlink to elsewhere is not.
* Default bind remains `127.0.0.1`; `run_dashboard_server(host=…)` can expose it. There is no authentication.
* The JSON API sends `Access-Control-Allow-Origin: *` (unchanged; it serves status/benchmark JSON, not files).
* `/api/status` still globs `experiments/vision/**/weights/*.pt` and returns file *names* (metadata, unchanged).
* The pre-existing `tests/unit/test_dashboard_server.py` is classified processed-data-access and was **not run**; its upload / status assertions are unaffected by static review of the diff, but that is not execution evidence.
