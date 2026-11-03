"""Reproducibility audit and manuscript-claim scanner (no results are produced here)."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from official_workspace import build_workspace

from railway_detection.cli.main import main as cli_main
from railway_detection.evaluation.evaluation_runner import Phase12EvaluationRunner
from railway_detection.reproducibility import (
    render_markdown,
    run_reproducibility_audit,
    scan_manuscript_claims,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 12, 1, tzinfo=UTC)
EVIDENCE = {0.9946, 0.855, 0.8956}
COUNTS = {27, 23, 3, 1, 54}


def _scan(text: str, root: Path | None = None):
    return scan_manuscript_claims(
        text, source="m.md", evidence_numbers=EVIDENCE, allowed_counts=COUNTS, root=root
    )


def _codes(text: str, root: Path | None = None) -> list[str]:
    return [f["code"] for f in _scan(text, root)]


def _item(report: dict, item_id: str) -> dict:
    return next(item for item in report["items"] if item["id"] == item_id)


# ----------------------------------------------------------------------- claim scanner


def test_numbers_present_in_evidence_pass_in_either_percent_or_fraction_form():
    assert _codes("The detector reached mAP@50 of 99.46%.") == []
    assert _codes("Window accuracy was 0.8956 on the test set.") == []
    assert _codes("Precision 85.5% at the operating threshold.") == []


def test_numbers_without_evidence_are_flagged():
    found = _scan("The system achieved 97.3% accuracy on railway events.")
    assert [f["code"] for f in found] == ["UNSUPPORTED_EMPIRICAL_NUMBER"]
    assert "97.3%" in found[0]["detail"]
    assert _codes("Median latency was 41.2 ms per frame.") == ["UNSUPPORTED_EMPIRICAL_NUMBER"]
    assert _codes("The false alarm rate was 0.12 per hour.") == ["UNSUPPORTED_EMPIRICAL_NUMBER"]


def test_hedged_negated_and_status_marked_sentences_are_not_flagged():
    assert _codes("No accuracy of 97.3% has been measured.") == []
    assert _codes("Latency of 41.2 ms is NOT OBTAINED.") == []
    assert _codes("Results (BLOCKED): accuracy 97.3% is a placeholder.") == []
    assert _codes("This system is not proven to be safe.") == []
    assert _codes("It does not guarantee clearance.") == []
    assert _codes("The report did not establish flawless detection.") == []
    assert _codes("The historical report did not establish flawless detection.") == []


def test_overclaim_language_is_flagged_unless_negated():
    for sentence in (
        "The detector guarantees clearance before gate opening.",
        "Flawless rear detection was achieved.",
        "The design eliminates premature opening risks.",
        "The approach outperforms the baseline.",
        "The system is deployment-ready.",
        "The model is proven on railway data.",
        "This is state-of-the-art for level crossings.",
    ):
        assert _codes(sentence) == ["OVERCLAIM_LANGUAGE"], sentence
    assert _codes("We make no claim that the design is deployment-ready.") == []


def test_software_verification_statements_are_not_railway_claims():
    assert _codes("The full suite reported 862 passed, 3 failed in 12.4 s.") == []


def test_dataset_counts_must_match_the_inventory():
    assert _codes("The cohort has 27 events.") == []
    assert _codes("The cohort has 23 full-train events.") == []
    assert _codes("We recorded 40 events at the site.") == ["DATASET_COUNT_MISMATCH"]
    assert _codes("About 40 events are PLANNED.") == []


def test_evidence_tags_must_resolve(tmp_path: Path):
    (tmp_path / "results.json").write_text("{}")
    assert _codes("Accuracy was 97.3% [evidence: results.json].", tmp_path) == []
    assert _codes("Accuracy was 97.3% [evidence: missing.json].", tmp_path) == [
        "BROKEN_EVIDENCE_TAG",
        "UNSUPPORTED_EMPIRICAL_NUMBER",
    ]
    # a tag on an overclaim only counts if it resolves
    assert _codes("It guarantees clearance [evidence: results.json].", tmp_path) == []
    assert "OVERCLAIM_LANGUAGE" in _codes(
        "It guarantees clearance [evidence: nope.json].", tmp_path
    )


def test_an_evidence_tag_shown_as_inline_code_is_documentation_not_a_claim(tmp_path: Path):
    assert _codes("Tag claims with `[evidence: some/path.json]` before reuse.", tmp_path) == []


def test_findings_carry_source_line_and_text():
    finding = _scan("first line.\nThe system achieved 97.3% accuracy.")[0]
    assert finding["source"] == "m.md" and finding["line"] == 2
    assert "97.3%" in finding["text"]


# --------------------------------------------------------------------- the real repository


def test_real_audit_reports_the_actual_state_without_inventing_results():
    watched = ("data/ground_truth", "configs", "results/experiment_registry.jsonl")
    before = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for w in watched
        for p in (
            [REPO_ROOT / w] if (REPO_ROOT / w).is_file() else sorted((REPO_ROOT / w).rglob("*"))
        )
        if p.is_file()
    }
    report = run_reproducibility_audit(REPO_ROOT, now=NOW)
    after = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for w in watched
        for p in (
            [REPO_ROOT / w] if (REPO_ROOT / w).is_file() else sorted((REPO_ROOT / w).rglob("*"))
        )
        if p.is_file()
    }
    assert after == before
    assert report["read_only"] is True
    assert _item(report, "dataset_manifests")["status"] == "PASS"
    assert _item(report, "approved_ground_truth")["status"] == "UNRESOLVED"
    assert _item(report, "protocol_version")["status"] == "UNRESOLVED"
    assert _item(report, "event_split_decision")["status"] == "UNRESOLVED"
    assert _item(report, "r04_scope_decision")["status"] == "UNRESOLVED"
    assert _item(report, "model_checkpoint_fingerprints")["status"] == "PASS"
    assert _item(report, "evaluation_result_provenance")["status"] == "NOT_AVAILABLE"
    assert _item(report, "experiment_manifest_completeness")["status"] == "NOT_AVAILABLE"
    register = _item(report, "unresolved_decisions")["evidence"]["register"]
    assert register["premature_opening_window"].startswith("UNRESOLVED")
    assert register["leg_exec"].startswith("AUTHORIZED")
    classes = report["evidence_classes"]
    assert classes["real_data_evaluation"] == "NOT OBTAINED"
    assert classes["target_hardware_measurement"].startswith("NOT OBTAINED")
    assert classes["controlled_validation"].startswith("NOT OBTAINED")


def test_both_policy_hash_conventions_are_recorded():
    report = run_reproducibility_audit(REPO_ROOT, now=NOW)
    evidence = _item(report, "config_and_policy_fingerprints")["evidence"]
    assert evidence["decision_policy"]["canonical_sha256"].startswith("051c908d")
    assert evidence["decision_policy"]["raw_sha256"].startswith("c87c1432")


def test_the_current_manuscript_draft_is_free_of_unsupported_statements():
    report = run_reproducibility_audit(REPO_ROOT, now=NOW)
    in_draft = [f for f in report["claim_findings"] if f["source"].endswith("MANUSCRIPT_DRAFT.md")]
    assert in_draft == [], in_draft


def test_active_correction_is_clean_and_historical_findings_remain_auditable():
    report = run_reproducibility_audit(REPO_ROOT, now=NOW)
    active = _item(report, "manuscript_claims_vs_evidence")
    historical = report["historical_claim_findings"]
    texts = " ".join(f["text"] for f in historical)
    assert active["status"] == "PASS"
    assert active["evidence"]["scanned"] == [
        "docs/PHASE16_MANUSCRIPT_DRAFT.md",
        "docs/PHASE16_MANUSCRIPT_CORRECTION_v1.md",
    ]
    assert active["evidence"]["historical_findings"] == len(historical) == 9
    assert report["historical_source_disposition"] == "preserved_with_findings"
    assert any(f["code"] == "OVERCLAIM_LANGUAGE" for f in historical)
    assert "eliminating catastrophic premature opening" in texts


def test_layer_a_numbers_backed_by_artifacts_are_not_flagged():
    report = run_reproducibility_audit(REPO_ROOT, now=NOW)
    unsupported = [
        f["text"] for f in report["claim_findings"] if f["code"] == "UNSUPPORTED_EMPIRICAL_NUMBER"
    ]
    assert not any("99.46%" in t for t in unsupported)  # in experiments/vision/*/evaluation


def test_markdown_rendering_lists_items_and_findings():
    report = run_reproducibility_audit(REPO_ROOT, now=NOW)
    markdown = render_markdown(report)
    assert "# Reproducibility Audit" in markdown and "approved_ground_truth" in markdown
    assert "Historical source findings" in markdown
    assert "OVERCLAIM_LANGUAGE" in markdown
    assert "Railway_Crossing_Automation_Research_Report.docx" in markdown


def test_environment_findings_are_surfaced():
    report = run_reproducibility_audit(REPO_ROOT, now=NOW)
    assert _item(report, "dependency_lock")["status"] in {"PASS", "FAIL"}
    ultra = _item(report, "ultralytics_importable")
    assert ultra["status"] in {"PASS", "FAIL"}


# -------------------------------------------------------------- result provenance (synthetic)


def test_result_provenance_is_verified_for_a_complete_synthetic_run(tmp_path, monkeypatch):
    ws = build_workspace(tmp_path, monkeypatch)
    out = tmp_path / "official"
    Phase12EvaluationRunner().run_official(repository_root=ws.root, output_dir=out)
    report = run_reproducibility_audit(ws.root, result_dirs=[out], now=NOW)
    assert _item(report, "evaluation_result_provenance")["status"] == "PASS"


def test_result_provenance_fails_when_authorization_or_hashes_are_missing(tmp_path, monkeypatch):
    ws = build_workspace(tmp_path, monkeypatch)
    out = tmp_path / "official"
    Phase12EvaluationRunner().run_official(repository_root=ws.root, output_dir=out)
    path = out / "run_manifest.json"
    manifest = json.loads(path.read_text())

    def audit_with(mutate):
        broken = json.loads(json.dumps(manifest))
        mutate(broken)
        path.write_text(json.dumps(broken))
        return _item(
            run_reproducibility_audit(ws.root, result_dirs=[out], now=NOW),
            "evaluation_result_provenance",
        )

    for label, mutate in {
        "authorization": lambda m: m.update(authorization_status="not_verified"),
        "auth record": lambda m: m.update(authorization_record_sha256="0" * 64),
        "config hash": lambda m: m["provenance"].update(frozen_config_sha256=""),
        "classification": lambda m: m.update(evidence_classification="synthetic"),
        "undecided window": lambda m: m.update(premature_opening_window="undecided"),
        "contract versions": lambda m: m.pop("contract_versions"),
    }.items():
        item = audit_with(mutate)
        assert item["status"] == "FAIL", label
    path.write_text(json.dumps(manifest))
    (out / "run_manifest.json").unlink()
    assert (
        _item(
            run_reproducibility_audit(ws.root, result_dirs=[out], now=NOW),
            "evaluation_result_provenance",
        )["status"]
        == "FAIL"
    )


def test_experiment_manifests_must_be_complete_and_non_empirical(tmp_path):
    good = {
        "plan": {},
        "input_sha256_by_event": {},
        "run_id": "r",
        "status": "x",
        "failures": [],
        "empirical_performance_claim": False,
    }
    ok = tmp_path / "ok.json"
    ok.write_text(json.dumps(good))
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({**good, "empirical_performance_claim": True}))
    short = tmp_path / "short.json"
    short.write_text(json.dumps({"plan": {}}))
    assert (
        _item(
            run_reproducibility_audit(REPO_ROOT, experiment_manifests=[ok], now=NOW),
            "experiment_manifest_completeness",
        )["status"]
        == "PASS"
    )
    for broken in (bad, short):
        assert (
            _item(
                run_reproducibility_audit(REPO_ROOT, experiment_manifests=[broken], now=NOW),
                "experiment_manifest_completeness",
            )["status"]
            == "FAIL"
        )


def test_a_manuscript_with_unsupported_claims_makes_the_audit_fail(tmp_path):
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "docs/PAPER.md").write_text(
        "We achieved 97.3% accuracy.\nThe system guarantees safe clearance.\n"
        "We recorded 40 events.\n"
    )
    report = run_reproducibility_audit(root, manuscripts=("docs/PAPER.md",), now=NOW)
    codes = {f["code"] for f in report["claim_findings"]}
    assert codes == {"UNSUPPORTED_EMPIRICAL_NUMBER", "OVERCLAIM_LANGUAGE", "DATASET_COUNT_MISMATCH"}
    assert _item(report, "manuscript_claims_vs_evidence")["status"] == "FAIL"


def test_missing_provenance_everywhere_is_reported_not_papered_over(tmp_path):
    report = run_reproducibility_audit(tmp_path, manuscripts=(), now=NOW)
    assert _item(report, "dataset_manifests")["status"] == "FAIL"
    assert _item(report, "dependency_lock")["status"] == "FAIL"


# ------------------------------------------------------------------------------- CLI


def test_audit_command_writes_outside_the_repository_only(tmp_path, capsys):
    out_json, out_md = tmp_path / "a.json", tmp_path / "a.md"
    assert cli_main(["audit", "reproducibility", "--json", str(out_json), "--md", str(out_md)]) == 0
    assert json.loads(out_json.read_text())["schema_version"] == "reproducibility-audit/1"
    assert out_md.read_text().startswith("# Reproducibility Audit")
    for tree in ("docs", "data", "results", "src"):
        target = REPO_ROOT / tree / "audit_should_not_exist.json"
        assert cli_main(["audit", "reproducibility", "--json", str(target)]) == 2
        assert not target.exists()
