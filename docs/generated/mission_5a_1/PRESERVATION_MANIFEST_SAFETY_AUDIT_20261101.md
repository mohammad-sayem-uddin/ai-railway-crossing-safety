# Preservation Manifest Safety Audit (Mission 5A.1)

> Method: static reading of `scripts/mission5a_build_preservation_manifest.py`, structural reading of the generated manifest JSON (no listed file was opened except by the tool's own `verify` on the 858 recorded entries — all text-like), and behavioural tests on **synthetic temp trees containing dummy files with media-like names**. No real media was opened, previewed, hashed or newly enumerated.

## 1. Verdict on the Mission 5A claims
| Claim | Result |
|---|---|
| `build` classifies by extension before any open; excluded files never opened | **Verified** (spy over `Path.open`/`os.open`: only the allowlisted `.py` file opened; `.mov .wav .bin .mp4`, unknown-format and out-of-tree symlink target untouched) |
| Symlinks are not followed | **Verified for build** (file symlinks skipped; directory symlinks not traversed; broken symlinks skipped). Before 5A.1 they were skipped *silently*; they are now counted (`symlink_not_followed`) |
| Allowlist (not an incomplete denylist) | **Verified**: a file is hashed only if its extension is in `HASHED_EXTENSIONS` (text-like) and it is inside a governing root and not in an excluded/output tree; unknown or extension-less files are excluded |
| 858 entries; 734 untracked; 11,322 generated-output files counted not hashed; both frozen checkpoints match; self-verify clean | **Verified** from the manifest (counts below); verify at audit start: 858 ok, 0 missing, 0 changed |
| "Media is not read through verification" | **CONTRADICTED at baseline, fixed in 5A.1** (next section) |
| "Manifest is self-verifying" | **Partially**: it re-hashes recorded entries; it cannot detect added files and its own integrity needs an external digest (recorded in the 5A report) |

## 2. Defect found: `verify` opened whatever the manifest listed (MEDIUM — fixed)
`verify_manifest` joined `entry["path"]` to the root and hashed it without re-applying the extension rules. A crafted or tampered manifest could therefore make `verify` read: a `.mov`/`.wav`/`.mp4`, a binary, an extension-less file, an absolute path, a `../` traversal, a file under `data/raw`, or a symlink pointing outside the tree. **Reproduced pre-fix** on a synthetic tree: six dummy media-like targets were opened. Honest manifests produced by `build` were never affected.
**Fix (5A.1):** `path_refusal()` — no I/O — rejects malformed/absolute/`..` paths, anything `classify()` would not hash (media, binary, output trees, wrong extension), symlinks, and anything whose `realpath` leaves the root; `verify` reports them under `refused` (never opened) and `clean` is false. The same guard validates frozen-checkpoint paths read from configuration (must be relative, inside the root, non-symlink, `.pt`). Re-run of the probe: **0 files opened**; 12 crafted entries refused (tested). Before/after hashes are in the change log.

## 3. Remaining observations
* **Enumeration scope (LOW):** `build` walks the whole tree, so it lists and `lstat`s every file *name* under output trees such as `data/raw` (3,492 names) and `data/processed` (5,093) to produce the counts. Nothing is opened, but media enumeration is broader than needed. Recommendation: prune output trees at directory level and report counts from `git ls-files`/a name-only scan, or drop the per-tree counts.
* **Renamed binaries (INFORMATIONAL):** an allowlisted text extension is trusted; a media file renamed `*.txt` inside a governing root would be hashed. Not realistic in this repository; a content-sniff would be a defence-in-depth addition.
* **Replacement between build and verify:** a changed file is reported `changed`; a file replaced by a symlink is now `refused` (tested).
* **Duplicates / path normalization:** `os.walk` yields each path once; paths are POSIX-relative to the root; no case-folding (macOS is case-insensitive by default — two paths differing only by case cannot coexist on disk).
* **Hidden directories:** pruned by name (`.git .venv .commandcode …`); other hidden directories inside governing roots would be included.
* **Self-inclusion / completeness:** `build` refuses to overwrite and cannot contain its own output (the file does not exist at walk time). The 5A manifest does **not** contain itself or the 5A execution report (created afterwards), nor anything created later (including the 5A.1 files).

## 4. Why 734 of 858 entries are untracked
The governing code and documents were never committed. Untracked entries by category: documentation 329, ground-truth metadata 148 (legacy reviews, proposals, notices), source 94, tests 81, scripts 39, manifest metadata 24, split metadata 8, configuration 5, root documents 3, schema 1, governance data 1, dependency/environment 1. They are exactly what a preservation effort must protect; the manifest records bytes only. **A hash does not mean a file is validated or authoritative** (legacy invalidated reviews and unapproved candidates are in the manifest too).
Generated-output trees by top-level directory (`data` 8,585 = `data/processed` 5,093 + `data/raw` 3,492; `results` 1,363; `scratch` 1,196; `experiments` 118; `research/figures` 51; `reports` 6; `models` 2; `outputs` 1; total 11,322) are counted, not hashed. Unrecognized extension 10; media/binary not opened 2; root non-governing 2; outside governing roots 1.

## 5. `.git/lost-found` count reconciliation (read-only)
| Method | Result | What it counts |
|---|---|---|
| `ls commit \| wc -l` | 146 | entries in `commit/` |
| `ls other \| wc -l` | 163 | entries in `other/` |
| sum | **309** | regular files |
| `find -type f` | **309** | regular files (same) |
| `find -type d` | 3 | root, `commit`, `other` |
| `find -type l` | 0 | symlinks |
| `ls -la commit \| wc -l` | 149 | 146 files + `total`, `.`, `..` lines |
By size: **301 files are 41 bytes** (a hash plus newline: pointer files) and **8 files are larger (5,558–61,912 bytes)**, which are dumped dangling-blob contents. So the earlier statement "309 pointer files" was imprecise: 301 pointers + 8 blob dumps. The figure 309 itself is consistent across Missions 4E.2, 5A and now. The directory was not modified (no write, no `fsck`).
