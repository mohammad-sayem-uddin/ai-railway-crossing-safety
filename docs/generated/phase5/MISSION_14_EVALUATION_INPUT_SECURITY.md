# Mission 14 — WP14.2 Evaluation Input Loader (F13-01, F13-02)

**Files changed:** `src/railway_detection/evaluation/input_contracts.py`, `src/railway_detection/evaluation/evaluation_runner.py`, `src/railway_detection/evaluation/execution_gate.py` (one `BLOCKER_CATALOGUE` entry; no pre-edit backup — see the artifact manifest).
**Tests:** `tests/unit/test_security_evaluation_input.py` (24, synthetic only; every refusal is checked against tripwires on source reads, manifest loads, the replay producer, `CacheOnlyReplayEngine` construction and engaged media-guard checks).

## 1. F13-01 — loader hashed media-suffixed sources without authorization and leaked the digest

Before (Mission 13 probe `I1`): a manifest source named `clip.mov` was opened, read in full and hashed with **zero** guard calls; the actual SHA-256 appeared in `SOURCE_HASH_MISMATCH`.

After:

| Behavior | Implementation |
|---|---|
| Authorization **before any open** | `_read_source_bytes_and_hash` calls `require_media_authorization(path, "HASH_RAW_MEDIA")` as its first statement (lowest level, so direct callers meet it too) |
| Authorization before reading the manifest file itself | `load_evaluation_input_manifest` guards the manifest path (`READ_RAW_MEDIA`); a media-looking "manifest" is refused unread |
| Location, not name | the guard now treats anything under `data/raw` (other than plain-text metadata), any alias that resolves there, and any media-suffixed/declared path as protected — an extensionless `clip` or `clip.bin` source is refused |
| Safe error | translated to `EvaluationInputError("SOURCE_MEDIA_ACCESS_DENIED", …)` carrying only the event id and the guard's code. No digest, no resolved alias target, no content |
| No digest on mismatch either | `SOURCE_HASH_MISMATCH` now reads "source digest does not match the manifest"; neither the computed nor the declared digest is echoed |
| No path-escape by spelling | source containment is `pid.is_within(source, manifest_root)` (identity-based), symlink handling unchanged (`SOURCE_SYMLINK_UNEXPECTED`) |
| Classification | `SOURCE_MEDIA_ACCESS_DENIED` added to `BLOCKER_CATALOGUE` (an existing governance test requires every loader code to be classified) |

Tests: media source refused with `os.open` patched to raise (never reached); five name patterns (`.mov`, none, `.m2ts`, `.weird`, `.bin`) refused with no 64-hex token, no content, no digest prefix in `code`/`detail`/`str(exc)`; media manifest path refused with `Path.read_bytes` patched to raise; symlinked source refused without a source read; `verify_sources=False` never reads sources; wrong-hash JSON source message contains neither digest; text metadata under `data/raw` still loads; valid synthetic manifests still load.

## 2. F13-02 — a REAL manifest without the classification argument was opened and hashed twice

Root cause: the public `run_from_manifest` decided "real or not" from the caller's `evidence_classification` keyword, while the private path took the classification from the manifest and read every source (twice) before `_run_verified` finally refused.

After — three independent layers, none of which trusts the caller's keyword:

1. **Argument check (unchanged, zero reads):** `evidence_classification=REAL`, any `_permit`, any `_authorization_context` ⇒ refuse immediately, before a single file is touched.
2. **Location check (zero reads):** the public synthetic API refuses a manifest whose canonical location lies in `data configs models experiments results` of the repository (`OFFICIAL_MANIFEST_LOCATION_REFUSED`).
3. **Header check (one metadata-only load, no source opened):** the public path loads the manifest with `verify_sources=False` and refuses `evidence_classification: real` (`OFFICIAL_AUTHORIZATION_CONTEXT_REQUIRED`). The private `_run_from_manifest_verified` does the same *before* its source loads and requires the module-private verified context (`_require_official_context`); a forged permit, a forged context with any token, or a context bound to a different manifest digest is refused with zero source reads.

**Honest note on "before opening the manifest":** an invalid REAL *request* (keyword, permit, context, protected location) is refused with zero file reads. A REAL *manifest* handed over with innocuous arguments can only be recognised by reading its small JSON control header; that single read happens, no event source is opened or hashed, and the request is then refused. Mission 13 case 6b/6c went from "6 source reads then refusal" to "0 source reads".

Authorization is not inferred from classification: REAL runs still need the context created only by `run_official` after `RealEventReplayProducer` re-validates the on-disk EVAL-AUTH, promotion receipt, manifest, protocol, configuration and review state. No EVAL-AUTH was created.

Tests: explicit REAL request (0 loads); forged permit with matching digest, REAL and SYNTHETIC labels, `run()` and `run_from_manifest()` (0 loads); forged context with `object()`, the module's private token, and a string (public API refuses even a *correct* token); omitted keyword (exactly 1 header load, 0 sources); caller-declared SYNTHETIC on a REAL manifest (1 header load, 0 sources); private core with no context / permit / forged context (header loads only); context for manifest A reused on manifest B (refused by digest binding); manifests in five protected repository trees refused (0 loads); a valid synthetic manifest runs end-to-end with `official_authorization_verified False`; `run_safe` returns a BLOCKED report; `run_official` on an empty tree refuses at the `readiness` stage and writes nothing.

## 3. What is deliberately not claimed

* The context object is still a Python-level capability: not bound to a runner instance, operation or time, and importable by name inside the same process (Mission 13 F13-15, unchanged, accepted as the documented limit).
* `EvaluationProvenance(official_authorization_verified=True)` can still be constructed by anyone; the flag proves nothing to a downstream reader (asserted in a test so the limit stays visible).
* The readiness gate still hashes the production checkpoints whether or not EVAL-AUTH exists (F13-09, open for a researcher decision; out of this work package).
