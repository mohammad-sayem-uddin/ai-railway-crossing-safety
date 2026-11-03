# Mission 14 — WP14.3 Shared Path and Case Canonicalisation (F13-03, F13-04)

**New module:** `src/railway_detection/safety/path_identity.py`. **Tests:** `tests/unit/test_security_path_identity.py` (52) plus the case/alias tests in the media-boundary, evaluation-input and dashboard suites. Case-variant tests build the fake tree on the local APFS volume (case-insensitive) and **skip with a stated reason on a case-sensitive filesystem**, where a different spelling really is a different directory. No test touches a real protected path.

## 1. The problem, reproduced and closed

Mission 13 demonstrated on this machine that `…/Train_automation` and `…/train_automation` name one directory but `Path.resolve()` keeps the caller's spelling, so every string comparison against the real checkout said "elsewhere": the descriptive-evaluation gate returned silently, `_checked_output_dir` accepted `data/Ground_Truth/…`, and `media_guard` took the "outside the repository" branch. Before/after, same probe scripts (`mission13_probes/probe_case.py`, `probe_outdir.py`):

| Probe | Mission 13 | Mission 14 |
|---|---|---|
| descriptive gate, canonical root | refused | refused |
| descriptive gate, case-variant root | **returned silently** | refused (`AUTH_DESCRIPTIVE_EVAL_EXEC_NOT_GRANTED`) |
| output dir `data/Ground_Truth/x` | **accepted** | `OUTPUT_DIR_PROTECTED` |
| output dir `…/train_automation/data/ground_truth/x` | **accepted** | `OUTPUT_DIR_PROTECTED` |
| symlink alias (`*.dat`, no suffix) → raw media | **allowed** | denied |

## 2. Approach

`path_identity.py` provides `canonical_path`, `is_same_location`, `is_within`, `is_within_any`, `relative_parts` and `resolve_untrusted_relative`.

| Requirement | How it is met |
|---|---|
| Resolve existing components; handle nonexistent targets | `Path.resolve(strict=False)` after `~` expansion and absolutisation: every existing component (symlinks included) is resolved, the nonexistent tail is kept below its resolved parent |
| Unresolvable or ambiguous ⇒ refuse | NUL bytes, empty text, bytes paths, non-path-like, symlink loops (`RuntimeError`), I/O errors ⇒ `PathIdentityError` (`PATH_INVALID` / `PATH_UNRESOLVABLE`). Callers fail closed: the media guard refuses (`AUTH_MEDIA_PATH_UNRESOLVABLE`), the descriptive gate treats the tree as real, `_is_real_checkout` returns True |
| Filesystem-appropriate case handling | comparison by **identity**: `os.path.samefile(ancestor, root)` over every ancestor of the target. No case-sensitivity probe, so it is correct on APFS (insensitive), on a case-sensitive volume (different spellings are different), and for Unicode-normalisation variants |
| Aliases of different depth (firmlinks) | every ancestor is tried, not only the same-depth one |
| Reference tree absent (synthetic root never created) | folded fallback (NFC + `casefold`) that can only over-match ⇒ fail closed |
| Not a string-prefix test | `repo2` is not inside `repo`; a parent is not inside its child (tested) |
| Same resource ⇒ same decision | `/outputs/VIDEO_TESTS/run1/SUMMARY.JSON` and the canonical spelling both served; `/outputs/../CONFIGS/x` and the canonical spelling both refused |
| Untrusted relative paths | `resolve_untrusted_relative`: percent-decode to a fixed point (max 4 rounds, otherwise `PATH_OVER_ENCODED`), then refuse control characters/NUL, backslashes, absolute forms (`/`, `~`, `C:`), `..`-like components (`..`, `...`, `.. `), then canonicalise and require containment **after symlink resolution** |
| Outputs cannot escape their authorized root | `_checked_output_dir`, `require_unprotected_output` and `_refuse_official_locations` test identity-containment in protected trees; `…/alias → data/ground_truth` refused |

## 3. Consumers converted from string comparison to identity

| Operation | Site |
|---|---|
| media access | `media_guard.classify_resource` / `require_media_authorization`, `_dataset_of`, `_check_path_scope` (prefix scope), `_check_bindings` |
| descriptive evaluation | `descriptive_exec_gate.require_descriptive_authorization_for_engine` → `_touches_real_repository`: gated if the root **is, contains or lies inside** the real checkout (previously: only if its resolved string equalled it) |
| protected outputs | `evaluation_runner._checked_output_dir`; `experiment_engine._refuse_official_locations`; `media_guard.require_unprotected_output` |
| cache access | `cache_only_engine._validate_cache_path` (symlink escape, traversal, case) |
| manifest input | `input_contracts` (manifest path, source containment) and the public runner's location check |
| dashboard serving | `demo/server.py` via `resolve_untrusted_relative` |
| pilot checkout identity | `stage21_timing_pilot._is_real_checkout` (the media-hash verification before a draft write was skipped for a case-variant root) |

## 4. Tests added (selection)

* canonical path: relative input, nonexistent tail below a symlink, NUL/empty/bytes/None, symlink loop;
* containment: sibling-prefix, parent-not-inside, symlink escape and symlink alias, case variants of existing and nonexistent paths, absent reference tree;
* untrusted paths: allowed forms; 12 traversal encodings (plain, `%2e%2e`, double and triple encoded, `..%2f`, `....//`, `.. `, `..;`); 6 absolute forms; 8 backslash/NUL/control forms; over-encoding; file and directory symlink escape; internal symlink allowed; suffix allowlist, missing file, directory; case variants;
* `_checked_output_dir`: 8 canonical protected trees + symlink alias + 3 case-variant spellings refused; non-empty output refused;
* descriptive gate: real checkout, a directory inside it, its parent, a symlink alias, a case variant ⇒ gated; a disjoint synthetic tree ⇒ not gated; un-canonicalisable ⇒ gated; case-variant root raises like the canonical root;
* cache paths: symlink escape, traversal, absolute, case-variant root; experiment-output and pilot-checkout identity.

## 5. Limits

Identity comparison needs the objects to exist for the strongest guarantee; nonexistent tails are compared by their existing ancestors. Hard links, mount changes after the check and swaps between check and use remain outside a user-space check. A Unicode-different spelling of a *nonexistent* file name below an existing ancestor is judged by its ancestor, which is the intended behavior. No claim of OS-level isolation is made.
