from dataclasses import dataclass

from railway_detection.data.split import generate_group_split, verify_group_disjointness


@dataclass
class Sample:
    sample_id: str
    split_group_id: str | None


def make_samples() -> list[Sample]:
    return [
        Sample("a1", "cross_a"),
        Sample("a2", "cross_a"),
        Sample("b1", "cross_b"),
        Sample("b2", "cross_b"),
        Sample("c1", "cross_c"),
        Sample("c2", "cross_c"),
        Sample("d1", "cross_d"),
        Sample("d2", "cross_d"),
    ]


def test_deterministic_seed():
    ratios = {"train": 0.5, "val": 0.25, "test": 0.25}
    first = generate_group_split(make_samples(), group_field="crossing_id", ratios=ratios, seed=42)
    second = generate_group_split(make_samples(), group_field="crossing_id", ratios=ratios, seed=42)
    assert first.partitions == second.partitions
    assert first.group_assignments == second.group_assignments


def test_group_disjoint_split():
    summary = generate_group_split(
        make_samples(),
        group_field="crossing_id",
        ratios={"train": 0.5, "val": 0.25, "test": 0.25},
        seed=7,
    )
    assert summary.ok
    assert verify_group_disjointness(summary)["disjoint"] is True
    all_ids = [sample_id for ids in summary.partitions.values() for sample_id in ids]
    assert sorted(all_ids) == sorted(sample.sample_id for sample in make_samples())


def test_missing_group_metadata_warns():
    samples = [Sample("a1", "cross_a"), Sample("orphan", None)]
    summary = generate_group_split(
        samples,
        group_field="crossing_id",
        ratios={"train": 0.7, "val": 0.15, "test": 0.15},
        seed=1,
        require_grouping=True,
        allow_ungrouped_fallback=False,
    )
    assert not summary.ok
    assert summary.error
    assert any("no crossing_id" in warning for warning in summary.warnings)


def test_missing_group_fallback_requires_explicit_flag():
    samples = [Sample("a1", "cross_a"), Sample("orphan", None)]
    summary = generate_group_split(
        samples,
        group_field="crossing_id",
        ratios={"train": 0.7, "val": 0.15, "test": 0.15},
        seed=1,
        require_grouping=True,
        allow_ungrouped_fallback=True,
    )
    assert summary.ok
    assert any("not leakage-safe" in warning for warning in summary.warnings)
