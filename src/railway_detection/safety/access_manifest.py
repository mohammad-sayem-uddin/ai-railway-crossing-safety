"""Test-access classification manifest: loading, validation and selection (Mission 10, WP10.3).

The manifest (``tests/test_access_classification.yaml``) records, for every test file, the data it
was *observed* to touch when run under the read-blocking access guard. The safe runner trusts it
only after :func:`verify_manifest_against_tree` proves it is complete and current: every test file
on disk is classified, no entry is stale (file hash unchanged), categories are valid and each
entry's safety flag agrees with its category. Any doubt means the file is not run.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

MANIFEST_SCHEMA = "2.0.0"
MANIFEST_RELATIVE = Path("tests/test_access_classification.yaml")

SYNTHETIC_ONLY = "SYNTHETIC_ONLY"
METADATA_ONLY = "METADATA_ONLY"
MODEL_CHECKPOINT_ACCESS = "MODEL_CHECKPOINT_ACCESS"
PROCESSED_DATA_ACCESS = "PROCESSED_DATA_ACCESS"
RAW_MEDIA_ACCESS = "RAW_MEDIA_ACCESS"
UNKNOWN = "UNKNOWN"

CATEGORIES = (
    SYNTHETIC_ONLY,
    METADATA_ONLY,
    MODEL_CHECKPOINT_ACCESS,
    PROCESSED_DATA_ACCESS,
    RAW_MEDIA_ACCESS,
    UNKNOWN,
)
#: Categories the safe runner may execute. Everything else, UNKNOWN included, is excluded.
SAFE_CATEGORIES = frozenset({SYNTHETIC_ONLY, METADATA_ONLY})

CATEGORY_DEFINITIONS = {
    SYNTHETIC_ONLY: "Observed to read nothing in the repository except source/test code; "
    "every data "
    "file it touches is created in a temporary directory.",
    METADATA_ONLY: "Observed to read repository metadata (configs, docs, ground-truth / manifest / "
    "governance JSON) but no media, model weights, processed data or results.",
    MODEL_CHECKPOINT_ACCESS: "Attempted to read model weights (blocked by the guard when "
    "classified).",
    PROCESSED_DATA_ACCESS: "Attempted to read processed data, caches, results or experiment "
    "artifacts (blocked by the guard when classified).",
    RAW_MEDIA_ACCESS: "Attempted to read raw media or a media-suffixed repository file (blocked by "
    "the guard when classified).",
    UNKNOWN: "Access could not be established (collection error, timeout, spawned child process, "
    "or no test executed). Treated as unsafe.",
}

REQUIRED_ENTRY_KEYS = frozenset(
    {
        "sha256",
        "category",
        "safe_for_synthetic_runner",
        "reason",
        "access_paths",
        "blocked_attempts",
        "access_dirs",
        "static_hints",
        "spawns_child_process",
        "child_processes_guarded",
        "tests",
        "evidence",
    }
)


class ManifestError(ValueError):
    """The classification manifest is missing, malformed, incomplete or stale."""


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_test_files(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in (root / "tests").rglob("test_*.py"))


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ManifestError(f"classification manifest not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ManifestError(f"classification manifest unreadable: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError("classification manifest must be a mapping")
    if data.get("schema_version") != MANIFEST_SCHEMA:
        raise ManifestError(
            f"unsupported manifest schema {data.get('schema_version')!r}; expected "
            f"{MANIFEST_SCHEMA!r}"
        )
    if not isinstance(data.get("test_files"), dict) or not data["test_files"]:
        raise ManifestError("classification manifest has no test_files")
    return data


def verify_manifest_against_tree(manifest: dict[str, Any], root: Path) -> list[str]:
    """Return every reason the manifest cannot be trusted for this tree (empty = trustworthy)."""
    problems: list[str] = []
    entries = manifest.get("test_files", {})
    on_disk = set(discover_test_files(root))
    classified = set(entries)
    for missing in sorted(on_disk - classified):
        problems.append(f"UNCLASSIFIED: {missing} exists but has no manifest entry")
    for ghost in sorted(classified - on_disk):
        problems.append(f"GHOST_ENTRY: {ghost} is in the manifest but not on disk")
    for rel in sorted(on_disk & classified):
        entry = entries[rel]
        if not isinstance(entry, dict) or REQUIRED_ENTRY_KEYS - set(entry):
            problems.append(
                f"MALFORMED: {rel} lacks keys {sorted(REQUIRED_ENTRY_KEYS - set(entry or {}))}"
            )
            continue
        if entry["category"] not in CATEGORIES:
            problems.append(f"BAD_CATEGORY: {rel} has category {entry['category']!r}")
            continue
        if entry["sha256"] != sha256_of(root / rel):
            problems.append(f"STALE: {rel} changed since it was classified")
        expected_safe = entry["category"] in SAFE_CATEGORIES
        if entry["safe_for_synthetic_runner"] is not expected_safe:
            problems.append(f"INCONSISTENT_SAFETY_FLAG: {rel} ({entry['category']})")
        if not isinstance(entry["reason"], str) or len(entry["reason"].strip()) < 20:
            problems.append(f"GENERIC_REASON: {rel} has no test-specific reason")
        if (
            entry["spawns_child_process"] is True
            and entry["category"] in SAFE_CATEGORIES
            and entry["child_processes_guarded"] is not True
        ):
            problems.append(
                f"UNOBSERVED_CHILD_PROCESS: {rel} spawns processes the guard cannot see"
            )
        if entry["category"] in SAFE_CATEGORIES and entry["blocked_attempts"]:
            problems.append(f"SAFE_BUT_BLOCKED: {rel} is marked safe but has blocked attempts")
    return problems


def select_files(
    manifest: dict[str, Any], categories: frozenset[str] = SAFE_CATEGORIES
) -> list[str]:
    unknown = categories - set(CATEGORIES)
    if unknown:
        raise ManifestError(f"unknown categories requested: {sorted(unknown)}")
    return sorted(
        rel for rel, entry in manifest["test_files"].items() if entry["category"] in categories
    )
