#!/usr/bin/env python3
"""Phase 2 (Mission 5B) -- prepare, but never perform, the researcher's protocol-adoption snapshot.

This is a NON-DESTRUCTIVE PREPARATION utility.  It verifies that the two working-tree protocol files
still equal their verified baselines, that the proposed replacements exist and are labelled as
proposals, hashes a fixed list of text documents, reads Git state with read-only queries, and writes
three report files into a new directory.  It does NOT stage, commit, push, reset, clean, check out,
restore, copy proposals over protocol files, edit governance records, create signatures or
hash-bound approval records, or read, hash or enumerate media.  A proposal hash printed here is
**not** an approved protocol hash.

Usage:
    python scripts/prepare_researcher_snapshot.py check   --root .
    python scripts/prepare_researcher_snapshot.py prepare --root . \
        --out-dir docs/generated/phase2/snapshot_prep

Exit codes: 0 ok; 2 refused (unsafe path, existing destination, git command refused);
3 baseline mismatch or mislabeled proposal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402

TOOL_VERSION = "phase2-researcher-snapshot-preparation/1"
PROPOSAL_HASH_KEY = "sha256_PROPOSAL_NOT_APPROVED_NOT_BOUND"
STATUS = "PREPARATION_ONLY -- NOT AN APPROVAL, NOT A SNAPSHOT, NOT A HASH BINDING"
PROPOSAL_BANNER = "PROPOSED — NOT APPROVED — NOT HASH-BOUND"

#: Only these are ever opened (as text).  Anything else, and every media/binary type, is refused
#: before a file is touched.
TEXT_EXTENSIONS = {".md", ".json", ".diff", ".txt", ".py", ".yaml", ".yml", ".toml"}
NEVER_OPEN_EXTENSIONS = {
    ".mov", ".mp4", ".m4v", ".avi", ".mkv", ".wav", ".mp3", ".flac", ".aac", ".ogg",
    ".pt", ".pth", ".ckpt", ".onnx", ".npy", ".npz", ".pkl", ".bin",
    ".png", ".jpg", ".jpeg", ".gif", ".tif", ".pdf", ".docx", ".xlsx", ".zip", ".gz",
}  # fmt: skip
MAX_BYTES = 20 * 1024 * 1024

#: Reports may only be written below this prefix of the repository root.
OUTPUT_PREFIX = "docs/generated/"
OUTPUT_FILES = ("SNAPSHOT_INVENTORY.json", "ADOPTION_CHECKLIST.md", "SNAPSHOT_REPORT.md")

#: Verified Mission 5B baselines of the working-tree protocols (references, not approvals).
WORKING_TREE_BASELINES = {
    "docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md": (
        "7c183b323970591b68f0db692e70413e54dcacfc4bf78a358c28f1b1ed68734c"
    ),
    "docs/FINAL_GROUND_TRUTH_PROTOCOL.md": (
        "d100c1e6a63280c375f94e297416efb0cf7dd3c15c9aa8df076ede052d49ecf4"
    ),
}
#: proposal path -> (required first heading, working-tree file it would replace)
PROPOSALS = {
    "docs/generated/phase2/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.1_PROPOSED.md": (
        "# PROPOSED — Final Real-World Experiment Protocol (v9.1.1-PROPOSED)",
        "docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md",
    ),
    "docs/generated/phase2/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md": (
        "# PROPOSED — Final Ground Truth Annotation Protocol (v7.1.1-PROPOSED)",
        "docs/FINAL_GROUND_TRUTH_PROTOCOL.md",
    ),
}
#: Other documents that are hashed into the inventory when present (never required).
INVENTORY_EXTRAS = (
    "docs/generated/phase2/v9_working_tree_vs_v9.1.1_PROPOSED.diff",
    "docs/generated/phase2/v7_working_tree_vs_v7.1.1_PROPOSED.diff",
    "docs/generated/phase2/EXPERIMENT_DESIGN_CONSOLIDATED.md",
    "docs/generated/phase2/PAPER_REVISION_CONSOLIDATED.md",
    "docs/generated/phase1/PHASE_1_COMPLETION_REPORT.md",
    "docs/EXPERIMENT_DESIGN_FINAL.md",
    "docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md",
)

#: The ONLY git invocations this tool can make.  All are read-only queries.
GIT_ALLOWED = (
    ("rev-parse", "HEAD"),
    ("rev-parse", "--abbrev-ref", "HEAD"),
    ("status", "--porcelain"),
    ("diff", "--cached", "--name-only"),
)


class SnapshotError(Exception):
    """A refusal.  ``code`` is stable; ``exit_code`` is the process exit status."""

    def __init__(self, code: str, detail: str, exit_code: int = 2) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.exit_code = exit_code


# --------------------------------------------------------------------------- paths


def resolve_in_root(root: Path, rel: object, *, must_exist: bool = True) -> Path:
    """Return a safe absolute path for ``rel`` or refuse.  Opens nothing."""
    if not isinstance(rel, str) or not rel or "\x00" in rel or "\\" in rel:
        raise SnapshotError("PATH_MALFORMED", repr(rel))
    pure = PurePosixPath(rel)
    if pure.is_absolute() or ".." in pure.parts:
        raise SnapshotError("PATH_OUTSIDE_ROOT", rel)
    suffix = pure.suffix.lower()
    if suffix in NEVER_OPEN_EXTENSIONS:
        raise SnapshotError("PATH_MEDIA_OR_BINARY_REFUSED", rel)
    if suffix not in TEXT_EXTENSIONS:
        raise SnapshotError("PATH_EXTENSION_NOT_ALLOWED", rel)
    real_root = os.path.realpath(root)
    full = Path(real_root) / rel
    # No symlink anywhere on the path below the root.
    probe = Path(real_root)
    for part in pure.parts:
        probe = probe / part
        if probe.is_symlink():
            raise SnapshotError("PATH_SYMLINK_REFUSED", rel)
    if os.path.commonpath([os.path.realpath(full), real_root]) != real_root:
        raise SnapshotError("PATH_OUTSIDE_ROOT", rel)
    if must_exist:
        if not full.is_file():
            raise SnapshotError("SOURCE_MISSING", rel)
        if full.stat().st_size > MAX_BYTES:
            raise SnapshotError("SOURCE_TOO_LARGE", rel)
    return full


def sha256_file(path: Path) -> str:
    require_media_authorization(path, "HASH_RAW_MEDIA")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------------------------------------------------------- checks


def check_baselines(root: Path, baselines: dict[str, str]) -> list[dict]:
    """Every working-tree protocol must still equal its baseline, or the run is refused."""
    rows, bad = [], []
    for rel, expected in sorted(baselines.items()):
        actual = sha256_file(resolve_in_root(root, rel))
        match = actual == expected
        rows.append(
            {"path": rel, "expected_sha256": expected, "sha256": actual, "unchanged": match}
        )
        if not match:
            bad.append(rel)
    if bad:
        raise SnapshotError(
            "BASELINE_MISMATCH",
            f"working-tree protocol differs from the verified baseline: {bad}",
            exit_code=3,
        )
    return rows


def check_proposal_label(text: str, heading: str, rel: str) -> None:
    """A proposal must open with its PROPOSED heading, carry the banner, never claim approval."""
    lines = text.splitlines()
    first = next((line for line in lines if line.strip()), "")
    if first.strip() != heading:
        raise SnapshotError(
            "PROPOSAL_MISLABELED", f"{rel}: first heading is not {heading!r}", exit_code=3
        )
    header = "\n".join(lines[:40])
    if PROPOSAL_BANNER not in header:
        raise SnapshotError("PROPOSAL_MISLABELED", f"{rel}: banner missing", exit_code=3)
    claim = header.replace("NOT APPROVED", "").replace("NOT HASH-BOUND", "")
    if re.search(r"\bAPPROVED\b|\bHASH-BOUND\b", claim) or re.search(
        r"status:\s*approved", claim, flags=re.I
    ):
        raise SnapshotError(
            "PROPOSAL_MISLABELED", f"{rel}: header contains an approval claim", exit_code=3
        )


def check_proposals(root: Path, proposals: dict, baselines: dict[str, str]) -> list[dict]:
    rows = []
    for rel, (heading, replaces) in sorted(proposals.items()):
        if rel in baselines or rel == replaces:
            raise SnapshotError("PROPOSAL_IS_PROTOCOL_FILE", rel)
        path = resolve_in_root(root, rel)
        check_proposal_label(path.read_text(encoding="utf-8"), heading, rel)
        rows.append(
            {
                "path": rel,
                "would_replace": replaces,
                PROPOSAL_HASH_KEY: sha256_file(path),
                "labelled_proposed": True,
            }
        )
    return rows


# --------------------------------------------------------------------------- git (read-only)


def _git(root: Path, args: tuple[str, ...], runner) -> str | None:
    if tuple(args) not in GIT_ALLOWED:
        raise SnapshotError("GIT_COMMAND_REFUSED", " ".join(args))
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    try:
        done = runner(
            ["git", "-C", str(root), *args], capture_output=True, text=True, env=env, check=False
        )
    except OSError:  # git is not installed
        return None
    return done.stdout if done.returncode == 0 else None


def git_state(root: Path, runner=subprocess.run) -> dict:
    """Counts and names of modified tracked files; untracked entries are only counted."""
    head = _git(root, ("rev-parse", "HEAD"), runner)
    if head is None:
        return {"available": False, "note": "not a git repository or git unavailable"}
    branch = _git(root, ("rev-parse", "--abbrev-ref", "HEAD"), runner) or ""
    status = _git(root, ("status", "--porcelain"), runner) or ""
    staged = _git(root, ("diff", "--cached", "--name-only"), runner) or ""
    modified, untracked = [], 0
    for line in status.splitlines():
        if line.startswith("??"):
            untracked += 1
        elif len(line) > 3:
            name = line[3:]
            if PurePosixPath(name).suffix.lower() not in NEVER_OPEN_EXTENSIONS:
                modified.append(name)
    return {
        "available": True,
        "head": head.strip(),
        "branch": branch.strip(),
        "staged_count": len([x for x in staged.splitlines() if x.strip()]),
        "modified_tracked_count": len(modified),
        "modified_tracked": sorted(modified),
        "untracked_entry_count": untracked,
    }


# --------------------------------------------------------------------------- report


def build_report(
    root: Path,
    *,
    baselines: dict[str, str] | None = None,
    proposals: dict | None = None,
    inventory_extras: tuple[str, ...] | None = None,
    runner=subprocess.run,
) -> dict:
    root = Path(root)
    inventory_extras = INVENTORY_EXTRAS if inventory_extras is None else inventory_extras
    baselines = WORKING_TREE_BASELINES if baselines is None else baselines
    proposals = PROPOSALS if proposals is None else proposals
    baseline_rows = check_baselines(root, baselines)
    proposal_rows = check_proposals(root, proposals, baselines)
    inventory = []
    for rel in inventory_extras:
        try:
            path = resolve_in_root(root, rel)
        except SnapshotError as exc:
            if exc.code == "SOURCE_MISSING":
                inventory.append({"path": rel, "present": False})
                continue
            raise
        inventory.append(
            {
                "path": rel,
                "present": True,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "tool": TOOL_VERSION,
        "status": STATUS,
        "generated_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "working_tree_protocols": baseline_rows,
        "proposals": proposal_rows,
        "inventory": inventory,
        "git": git_state(root, runner),
        "notes": [
            "A proposal hash is not an approved or bound protocol hash.",
            "Final protocol hashes must be computed by the researcher AFTER adopting wording.",
            "This tool performed no Git write, no copy over a protocol file and no signing.",
        ],
    }


def checklist_markdown(report: dict) -> str:
    git = report["git"]
    state = (
        f"HEAD `{git['head']}`, branch `{git['branch']}`, staged {git['staged_count']}, "
        f"modified tracked {git['modified_tracked_count']}, untracked entries "
        f"{git['untracked_entry_count']}"
        if git.get("available")
        else "git state unavailable"
    )
    protocol_rows = "\n".join(
        f"| `{r['path']}` | `{r['sha256']}` | {'unchanged' if r['unchanged'] else 'CHANGED'} |"
        for r in report["working_tree_protocols"]
    )
    proposal_rows = "\n".join(
        f"| `{r['path']}` | `{r[PROPOSAL_HASH_KEY]}` | `{r['would_replace']}` |"
        for r in report["proposals"]
    )
    return f"""# Researcher adoption checklist (PREPARATION ONLY)

> {STATUS}. Nothing below has been done for you. Only you can adopt wording, commit, snapshot and
> author governance records.

Git state when this was prepared: {state}.

## Working-tree protocols (unchanged at preparation time)
| File | SHA-256 | Status |
|---|---|---|
{protocol_rows}

## Proposed replacements (proposal hashes are NOT approved or bound hashes)
| Proposal | SHA-256 | Would replace |
|---|---|---|
{proposal_rows}

## Steps for you (in order)
1. Read both proposals and both unified diffs. Decide: adopt, request revisions, or preserve
   without adopting.
2. If adopting, copy the wording into the protocol files yourself and remove the `PROPOSED` labels.
   This tool never copies anything.
3. Review `git status` before committing: raw media and generated output trees must not be committed
   by accident. Commit the governing set on a branch you choose.
4. Re-run the manifest build against the final tree, then create the off-Desktop snapshot you
   approve.
5. Compute the final protocol hashes from the adopted files. Only then author the GOV-D1 record.
6. After adoption, the working-tree baselines in this tool and the Phase 2 baseline test are
   intentionally out of date; update or retire them.
"""


def report_markdown(report: dict) -> str:
    git = report["git"]
    lines = [
        "# Proposed snapshot report (PREPARATION ONLY)",
        "",
        f"> {STATUS}.",
        "",
        f"Generated: {report['generated_utc']} by `{report['tool']}`.",
        "",
        "## Inventory",
        "| Path | Present | SHA-256 |",
        "|---|---|---|",
    ]
    for item in report["inventory"]:
        lines.append(f"| `{item['path']}` | {item['present']} | `{item.get('sha256', '-')}` |")
    lines += ["", "## Git (read-only)", "", "```json", json.dumps(git, indent=1), "```", ""]
    lines += ["## Notes", *[f"- {n}" for n in report["notes"]], ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- output


def write_outputs(root: Path, out_dir: object, report: dict) -> list[str]:
    """Create the three report files with exclusive-create; never overwrite anything."""
    if not isinstance(out_dir, str) or not out_dir or "\x00" in out_dir or "\\" in out_dir:
        raise SnapshotError("OUTPUT_PATH_MALFORMED", repr(out_dir))
    pure = PurePosixPath(out_dir)
    if pure.is_absolute() or ".." in pure.parts:
        raise SnapshotError("OUTPUT_OUTSIDE_ROOT", out_dir)
    if not (out_dir.rstrip("/") + "/").startswith(OUTPUT_PREFIX):
        raise SnapshotError(
            "OUTPUT_OUTSIDE_ALLOWED_PREFIX", f"{out_dir} (must be under {OUTPUT_PREFIX})"
        )
    real_root = os.path.realpath(root)
    probe = Path(real_root)
    for part in pure.parts:
        probe = probe / part
        if probe.is_symlink():
            raise SnapshotError("OUTPUT_SYMLINK_REFUSED", out_dir)
    target = Path(real_root) / pure
    if os.path.commonpath([os.path.realpath(target), real_root]) != real_root:
        raise SnapshotError("OUTPUT_OUTSIDE_ROOT", out_dir)
    existing = [name for name in OUTPUT_FILES if (target / name).exists()]
    if existing:
        raise SnapshotError("DESTINATION_EXISTS", f"{out_dir}: {existing}")
    target.mkdir(parents=True, exist_ok=True)
    contents = {
        OUTPUT_FILES[0]: json.dumps(report, indent=1) + "\n",
        OUTPUT_FILES[1]: checklist_markdown(report),
        OUTPUT_FILES[2]: report_markdown(report),
    }
    written, created = [], []
    try:
        for name, text in contents.items():
            with (target / name).open("x", encoding="utf-8") as handle:  # 'x': fail if it exists
                created.append(target / name)
                handle.write(text)
            written.append(f"{out_dir.rstrip('/')}/{name}")
    except FileExistsError as exc:
        for path in created:  # remove only what THIS call created; never an existing file
            path.unlink()
        raise SnapshotError("DESTINATION_EXISTS", f"{out_dir}: {exc.filename}") from exc
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="verify and print; writes nothing")
    c.add_argument("--root", default=".")
    p = sub.add_parser(
        "prepare", help="verify and write the three report files into a NEW directory"
    )
    p.add_argument("--root", default=".")
    p.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    try:
        root = Path(args.root)
        report = build_report(root)
        if args.cmd == "check":
            print(json.dumps(report, indent=1))
            return 0
        for path in write_outputs(root, args.out_dir, report):
            print(f"wrote {path}")
        return 0
    except SnapshotError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
