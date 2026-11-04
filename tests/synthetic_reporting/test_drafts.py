import importlib.util
from dataclasses import replace
from pathlib import Path

import pytest

from railway_detection.evaluation.metrics import DescriptiveMetricRow

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "publication_tables", ROOT / "scripts/generate_publication_tables.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
LEGACY = {
    name: compile((ROOT / "scripts" / name).read_text(), name, "exec")
    for name in (
        "generate_publication_figures.py",
        "generate_report_figures.py",
        "build_research_report_doc.py",
    )
}


def row():
    return DescriptiveMetricRow(
        "train_events/event_001", "back", "B0_back", "M5", 1, None, "synthetic:fixture"
    )


def test_absent_results_do_not_become_empirical_numbers_or_authors():
    text = module.render_descriptive_support()
    for required in (
        "UNAVAILABLE",
        "Venue: undecided",
        "actual human author",
        "AI use:",
        "M4 primary",
        "M5 integer",
        "Censored",
        "full occupancy remain deferred",
    ):
        assert required in text
    assert "100%" not in text and "GPT" not in text


def test_constructed_rows_bound_and_stratified_without_imputation():
    rows = (
        row(),
        replace(row(), event_key="train_events/event_002", value=None, exclusion_reason="missing"),
    )
    digest = module.descriptive_rows_digest(rows)
    text = module.render_descriptive_support(rows, expected_digest=digest)
    assert "CONSTRUCTED DEMONSTRATION ONLY" in text
    assert "| M5 | 1 | 1 |" in text and "'missing': 1" in text
    with pytest.raises(ValueError, match="digest"):
        module.render_descriptive_support((row(),), expected_digest=digest)
    with pytest.raises(ValueError, match="real or unverified"):
        real = (replace(row(), provenance="human:assertion"),)
        module.render_descriptive_support(
            real, expected_digest=module.descriptive_rows_digest(real)
        )


def test_markup_cannot_insert_claims():
    rows = (replace(row(), condition="B0_back|<script>\ninjected"),)
    text = module.render_descriptive_support(
        rows, expected_digest=module.descriptive_rows_digest(rows)
    )
    assert "<script>" not in text and "&#124;" in text


def test_table_entrypoint_never_reads_legacy_cache_or_writes_claims():
    with pytest.raises(PermissionError, match="unverified fixed claims"):
        module.generate_all_tables(approved=True, output_dir="/unopened")


@pytest.mark.parametrize("name", sorted(LEGACY))
def test_legacy_generators_refuse_before_third_party_import_or_io(name):
    with pytest.raises(PermissionError, match="Legacy publication generator disabled"):
        exec(LEGACY[name], {"__name__": "__main__"})


def test_private_historical_templates_also_fail_closed():
    with pytest.raises(PermissionError, match="audit only"):
        module._historical_unverified_templates(output_dir="/unopened")
