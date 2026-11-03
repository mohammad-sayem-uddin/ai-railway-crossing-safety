#!/usr/bin/env python3
"""Mission 5A -- build or verify a SHA-256 preservation manifest of the governing project files.

READ-ONLY with respect to the project: it never stages, commits, modifies or deletes anything and
only writes the manifest file you name with ``--out``.  It NEVER opens raw media: files are
classified by extension *before* any open, and media/binary/model files are excluded (the two
frozen checkpoints named in the frozen configuration are the only binary exception, listed
explicitly with their expected hash for comparison).

Usage:
    python scripts/mission5a_build_preservation_manifest.py build  --root . --out MANIFEST.json
    python scripts/mission5a_build_preservation_manifest.py verify --root . --manifest MANIFEST.json

A manifest records hashes; it does not by itself make the project reproducible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402

TOOL_VERSION = "mission5a-preservation-manifest/1"

#: Extensions that are read and hashed (text-like governing artifacts).
HASHED_EXTENSIONS = {
    ".py", ".md", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".txt", ".lock",
    ".csv", ".cfg", ".ini", ".diff", ".sh", ".example", ".schema",
}  # fmt: skip
#: Never opened, whatever the directory.
NEVER_OPEN_EXTENSIONS = {
    ".mov", ".mp4", ".m4v", ".avi", ".mkv", ".wav", ".mp3", ".flac", ".aac", ".ogg",
    ".pt", ".pth", ".ckpt", ".onnx", ".npy", ".npz", ".pkl", ".bin",
    ".png", ".jpg", ".jpeg", ".gif", ".tif", ".pdf", ".docx", ".xlsx", ".zip", ".gz",
}  # fmt: skip
EXCLUDED_DIR_NAMES = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    "node_modules", ".idea", ".vscode", ".commandcode", "ESC-50-master", "Unseen_Video",
    "lost-found",
}  # fmt: skip
#: Generated/output trees: never hashed.  ``build`` does not descend into them at all (so raw
#: media file names are never enumerated) unless ``count_excluded_trees`` is requested, in which
#: case their files are only counted.
OUTPUT_TREES = (
    "data/raw", "data/processed", "results", "experiments", "outputs", "models", "scratch",
    "reports", "research/figures", "venv", ".venv",
)  # fmt: skip
GOVERNING_ROOTS = {
    "src": "source", "tests": "tests", "configs": "configuration", "docs": "documentation",
    "schemas": "schema", "scripts": "scripts", "research": "research_code",
    "data/governance": "governance_data", "data/ground_truth": "ground_truth_metadata",
    "data/manifests": "manifest_metadata", "data/splits": "split_metadata",
}  # fmt: skip
ROOT_FILE_ROLES = {
    "pyproject.toml": "dependency_environment", "requirements.lock": "dependency_environment",
    ".env.example": "dependency_environment", ".gitignore": "repository_hygiene",
}  # fmt: skip
MAX_HASH_BYTES = 200 * 1024 * 1024


def sha256_file(path: Path) -> str:
    require_media_authorization(path, "HASH_RAW_MEDIA")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(root: Path, *args: str) -> str:
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, env=env, check=False
    )
    return out.stdout if out.returncode == 0 else ""


def git_state(root: Path) -> dict:
    tracked = set(filter(None, _git(root, "ls-files").split("\n")))
    modified = set()
    for line in filter(None, _git(root, "status", "--porcelain").split("\n")):
        if line[:2].strip() in {"M", "MM", "AM"} or line[1:2] == "M":
            modified.add(line[3:])
    return {
        "branch": _git(root, "branch", "--show-current").strip(),
        "head": _git(root, "rev-parse", "HEAD").strip(),
        "tracked": tracked,
        "modified": modified,
    }


def classify(rel: str) -> tuple[str, str]:
    """Return (decision, category).  decision is 'hash' or 'exclude:<reason>'; no I/O."""
    parts = rel.split("/")
    if any(p in EXCLUDED_DIR_NAMES for p in parts):
        return "exclude:excluded_directory", ""
    for tree in OUTPUT_TREES:
        if rel == tree or rel.startswith(tree + "/"):
            return "exclude:generated_output_tree", ""
    ext = Path(rel).suffix.lower()
    if ext in NEVER_OPEN_EXTENSIONS:
        return "exclude:media_binary_or_model_not_opened", ""
    if ext not in HASHED_EXTENSIONS and Path(rel).name not in ROOT_FILE_ROLES:
        return "exclude:unrecognized_extension", ""
    if len(parts) == 1:
        if rel in ROOT_FILE_ROLES:
            return "hash", ROOT_FILE_ROLES[rel]
        return (
            ("hash", "root_document") if ext == ".md" else ("exclude:root_file_not_governing", "")
        )
    for prefix, category in GOVERNING_ROOTS.items():
        if rel.startswith(prefix + "/"):
            return "hash", category
    return "exclude:not_in_governing_roots", ""


def path_refusal(root: Path, rel: object, *, require_suffix: str | None = None) -> str | None:
    """Return why a manifest/config path must NOT be opened, or ``None`` if it is safe.

    Opens nothing.  Applies the same extension/directory rules as ``build`` (so a crafted
    manifest cannot steer ``verify`` onto media, binaries or excluded trees) and refuses
    absolute paths, ``..`` traversal, symlinks and anything resolving outside ``root``.
    """
    if not isinstance(rel, str) or not rel or "\x00" in rel or "\\" in rel:
        return "malformed_path"
    pure = PurePosixPath(rel)
    if pure.is_absolute() or ".." in pure.parts:
        return "absolute_or_traversal_path"
    if require_suffix is not None:
        if pure.suffix.lower() != require_suffix:
            return "unexpected_suffix"
    else:
        decision, _ = classify(rel)
        if decision != "hash":
            return decision.split(":", 1)[1]
    full = root / rel
    if full.is_symlink():
        return "symlink_not_followed"
    real_root = os.path.realpath(root)
    real = os.path.realpath(full)
    if os.path.commonpath([real, real_root]) != real_root:
        return "outside_root"
    return None


def build_manifest(
    root: Path,
    frozen_checkpoints: dict[str, str] | None = None,
    *,
    count_excluded_trees: bool = False,
) -> dict:
    root = root.resolve()
    state = git_state(root)
    entries: list[dict] = []
    excluded: dict[str, dict] = {}
    pruned: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIR_NAMES)
        if not count_excluded_trees:
            # Prune output trees at directory level so their contents are never listed (DEC-A02).
            rel_dir = Path(dirpath).relative_to(root).as_posix()
            kept = []
            for d in dirnames:
                child = d if rel_dir == "." else f"{rel_dir}/{d}"
                if child in OUTPUT_TREES:
                    pruned.append(child)
                else:
                    kept.append(d)
            dirnames[:] = kept
        for name in sorted(filenames):
            full = Path(dirpath) / name
            rel = full.relative_to(root).as_posix()
            if full.is_symlink():
                link = excluded.setdefault(
                    "symlink_not_followed", {"file_count": 0, "examples": {}}
                )
                link["file_count"] += 1
                continue
            decision, category = classify(rel)
            if decision == "hash":
                size = full.stat().st_size
                if size > MAX_HASH_BYTES:
                    decision = "exclude:too_large"
                else:
                    status = (
                        "untracked"
                        if rel not in state["tracked"]
                        else ("tracked-modified" if rel in state["modified"] else "tracked-clean")
                    )
                    entries.append(
                        {"path": rel, "category": category, "bytes": size,
                         "sha256": sha256_file(full), "git_status": status}
                    )  # fmt: skip
                    continue
            reason = decision.split(":", 1)[1]
            top = "/".join(rel.split("/")[:2]) if "/" in rel else "(root)"
            bucket = excluded.setdefault(reason, {"file_count": 0, "examples": {}})
            bucket["file_count"] += 1
            bucket["examples"].setdefault(top, 0)
            bucket["examples"][top] += 1
    checkpoints = []
    for rel, expected in (frozen_checkpoints or {}).items():
        refusal = path_refusal(root, rel, require_suffix=".pt")
        if refusal is not None:
            checkpoints.append({"path": rel, "expected_sha256": expected, "refused": refusal})
            continue
        full = root / rel
        if full.is_file():
            actual = sha256_file(full)
            checkpoints.append(
                {"path": rel, "expected_sha256": expected, "sha256": actual,
                 "matches_expected": actual == expected, "role": "frozen_checkpoint_dependency"}
            )  # fmt: skip
        else:
            checkpoints.append({"path": rel, "expected_sha256": expected, "missing": True})
    counts: dict[str, int] = {}
    for entry in entries:
        key = f"{entry['category']}|{entry['git_status']}"
        counts[key] = counts.get(key, 0) + 1
    return {
        "tool": TOOL_VERSION,
        "generated_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "PROPOSED_PRESERVATION_MANIFEST -- NOT AN APPROVAL, NOT A REPRODUCIBILITY CLAIM",
        "git": {"branch": state["branch"], "head": state["head"]},
        "count_excluded_trees": count_excluded_trees,
        "pruned_output_trees": sorted(pruned),
        "entry_count": len(entries),
        "counts_by_category_and_git_status": dict(sorted(counts.items())),
        "frozen_checkpoints": checkpoints,
        "excluded": excluded,
        "entries": entries,
    }


def verify_manifest(root: Path, manifest: dict) -> dict:
    """Recompute hashes of the recorded entries; report missing, changed (never rewrites)."""
    root = root.resolve()
    missing, changed, refused, ok = [], [], [], 0
    for entry in manifest.get("entries", []):
        rel = entry.get("path") if isinstance(entry, dict) else None
        reason = path_refusal(root, rel)
        if reason is not None:  # never opened: media/binary/outside-root/symlink/malformed
            refused.append({"path": rel, "reason": reason})
            continue
        full = root / rel
        if not full.is_file():
            missing.append(rel)
        elif sha256_file(full) != entry.get("sha256"):
            changed.append(rel)
        else:
            ok += 1
    return {
        "ok": ok,
        "missing": missing,
        "changed": changed,
        "refused": refused,
        "clean": not (missing or changed or refused),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--root", default=".")
    b.add_argument("--out", required=True)
    b.add_argument("--frozen-config", default="configs/frozen_experiment_v1.yaml")
    b.add_argument(
        "--count-excluded-trees",
        action="store_true",
        help="descend into output trees (data/raw, ...) to count their files; off by default",
    )
    v = sub.add_parser("verify")
    v.add_argument("--root", default=".")
    v.add_argument("--manifest", required=True)
    args = parser.parse_args(argv)
    if args.cmd == "build":
        root = Path(args.root)
        checkpoints: dict[str, str] = {}
        cfg = root / args.frozen_config
        if cfg.is_file():
            import re

            text = cfg.read_text(encoding="utf-8")
            for m in re.finditer(
                r'path:\s*"([^"]+\.pt)"\s*\n\s*expected_sha256:\s*"([0-9a-f]{64})"', text
            ):
                checkpoints[m.group(1)] = m.group(2)
        out = Path(args.out)
        if out.exists():
            print(f"refusing to overwrite existing {out}", file=sys.stderr)
            return 2
        manifest = build_manifest(
            root, checkpoints, count_excluded_trees=args.count_excluded_trees
        )
        out.write_text(json.dumps(manifest, indent=1, sort_keys=False), encoding="utf-8")
        print(f"wrote {out}: {manifest['entry_count']} entries")
        return 0
    result = verify_manifest(Path(args.root), json.loads(Path(args.manifest).read_text("utf-8")))
    print(json.dumps(result, indent=1))
    return 0 if result["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
