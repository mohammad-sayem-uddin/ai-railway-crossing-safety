"""Deterministic group-aware dataset splitting.

The splitter works over normalized sample records that carry a grouping field
(such as ``crossing_id`` or ``session_id``). It never assigns descendants of the
same group to different partitions.
"""

from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol


class GroupedSample(Protocol):
    sample_id: str
    split_group_id: str | None


@dataclass
class SplitSummary:
    split_id: str
    group_field: str
    seed: int
    ratios: dict[str, float]
    require_grouping: bool
    allow_ungrouped_fallback: bool
    partitions: dict[str, list[str]] = field(default_factory=dict)
    group_assignments: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict[str, Any]:
        is_fallback = bool(self.allow_ungrouped_fallback or any("leakage" in w.lower() or "no crossing" in w.lower() for w in self.warnings))
        data: dict[str, Any] = {
            "split_id": self.split_id,
            "split_type": "development_fallback" if is_fallback else "group_disjoint",
            "leakage_risk": is_fallback,
            "group_field": self.group_field,
            "seed": self.seed,
            "ratios": self.ratios,
            "require_grouping": self.require_grouping,
            "allow_ungrouped_fallback": self.allow_ungrouped_fallback,
            "partitions": self.partitions,
            "group_assignments": self.group_assignments,
            "warnings": self.warnings,
            "error": self.error,
            "group_counts": {
                name: len(ids) for name, ids in self.partitions.items()
            },
        }
        return data


def generate_group_split(
    samples: Iterable[GroupedSample],
    *,
    group_field: str,
    ratios: dict[str, float],
    seed: int,
    require_grouping: bool = True,
    allow_ungrouped_fallback: bool = False,
    split_id: str | None = None,
) -> SplitSummary:
    """Generate a deterministic, group-disjoint train/val/test split."""
    if split_id is None:
        split_id = _split_id(seed, ratios)

    summary = SplitSummary(
        split_id=split_id,
        group_field=group_field,
        seed=seed,
        ratios=dict(ratios),
        require_grouping=require_grouping,
        allow_ungrouped_fallback=allow_ungrouped_fallback,
    )

    expected = {"train", "val", "test"}
    if set(ratios.keys()) != expected:
        summary.error = f"ratios must contain exactly {sorted(expected)}"
        return summary

    groups: dict[str, list[str]] = defaultdict(list)
    ungrouped: list[str] = []
    for sample in samples:
        group = sample.split_group_id
        if group is None or group == "":
            ungrouped.append(sample.sample_id)
        else:
            groups[group].append(sample.sample_id)

    if ungrouped:
        warning = (
            f"{len(ungrouped)} sample(s) have no {group_field}. "
            "A group-disjoint split cannot be guaranteed for these records."
        )
        summary.warnings.append(warning)
        if require_grouping and not allow_ungrouped_fallback:
            summary.error = (
                f"grouping metadata ({group_field}) is required but missing for "
                f"{len(ungrouped)} sample(s). "
                "Set allow_ungrouped_fallback with explicit acknowledgement."
            )
            return summary

    group_names = sorted(groups.keys())
    if not group_names:
        summary.error = "no grouped samples found; cannot produce a leakage-safe split"
        return summary

    rng = random.Random(seed)
    shuffled = list(group_names)
    rng.shuffle(shuffled)

    train_ratio = ratios["train"]
    val_ratio = ratios["val"]
    n = len(shuffled)
    train_end = max(1, round(n * train_ratio))
    val_end = train_end + max(1 if val_ratio > 0 else 0, round(n * val_ratio))

    assignment: dict[str, str] = {}
    for idx, group in enumerate(shuffled):
        if idx < train_end:
            assignment[group] = "train"
        elif idx < val_end:
            assignment[group] = "val"
        else:
            assignment[group] = "test"

    partitions: dict[str, list[str]] = {"train": [], "val": [], "test": []}
    for group, members in groups.items():
        partitions[assignment[group]].extend(members)

    if ungrouped and allow_ungrouped_fallback:
        # Assign ungrouped samples deterministically but visibly flag the leakage risk.
        for sample_id in ungrouped:
            bucket = rng.choice(["train", "val", "test"])
            partitions[bucket].append(sample_id)
        summary.warnings.append(
            "ungrouped samples were fallback-assigned pseudo-randomly; "
            "this split is not leakage-safe for those records."
        )

    summary.partitions = {name: sorted(ids) for name, ids in partitions.items()}
    summary.group_assignments = assignment
    return summary


def verify_group_disjointness(summary: SplitSummary) -> dict[str, Any]:
    """Check that no group appears in more than one partition."""
    seen: dict[str, str] = {}
    overlap: list[str] = []
    for group, partition in summary.group_assignments.items():
        if group in seen and seen[group] != partition:
            overlap.append(group)
        seen[group] = partition
    return {"disjoint": not overlap, "overlapping_groups": overlap}


def _split_id(seed: int, ratios: dict[str, float]) -> str:
    payload = f"{seed}:{sorted(ratios.items())}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
