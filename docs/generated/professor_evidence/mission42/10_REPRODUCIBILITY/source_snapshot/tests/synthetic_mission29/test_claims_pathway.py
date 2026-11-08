"""Constructed artifact mutations; none constitutes a real source permission or experiment."""

import copy
import json
from pathlib import Path

import pytest
from scripts import validate_mission29_research_decision as check


@pytest.fixture
def package():
    # Unit mutations exercise the original document package, not live admission.
    # Later legitimate code changes make its supporting-source manifest stale;
    # the real loader must continue refusing that drift. Never refresh old hashes.
    binding = check.closed_json(
        check._text("docs/generated/master_reaudit/" + check.BINDING)
    )
    result = {}
    for key, name in check.INPUTS.items():
        body = check._text("docs/generated/master_reaudit/" + name)
        assert check.sha(body) == binding["input_sha256"][name]
        result[key] = check.closed_json(body)
    return result


def test_live_loader_still_refuses_changed_supporting_source(monkeypatch):
    original = check._text
    monkeypatch.setattr(
        check, "_text", lambda name: original(name) + " " if name == "README.md" else original(name)
    )
    with pytest.raises(ValueError, match="stale supporting documentary/code source: README.md"):
        check.load()


def test_current_bounded_methods_preparation_is_consistent_and_deterministic(package):
    """Semantic consistency of the historical fixture; no live readiness claim."""
    a = check.report(package)
    assert a == check.report(copy.deepcopy(package))
    assert a["valid"] and a["new_grants"] == 0
    assert a["current_pathway"] == "PATH_B_DEFENSIBLE_MANUSCRIPT_PREPARATION"
    assert "not source authenticity" in a["assurance"]
    assert not package["decision"]["path_b"]["external_submission_authorized"]
    assert not package["decision"]["empirical_experiments_executed"]


@pytest.mark.parametrize(
    "fault",
    [
        "path_a_ready",
        "multiple_paths",
        "rights_unassessed",
        "raw_included",
        "external_submission",
        "genuine_relabel",
        "unsupported_field_claim",
        "field_relabel_as_software",
        "missing_limitations",
        "unknown_citation",
        "duplicate_claim",
        "historical_reproduced",
        "null_to_zero",
        "audio_v2_allowed",
        "leakage_removed",
        "audio_split_reconciled",
        "vision_value_changed",
        "audio_value_changed",
        "censoring_reconciled",
        "inventory_signed",
        "R04_expanded",
        "pilot_expanded",
        "new_original_invented",
        "author_venue_invented",
        "freeze_removed",
        "acceptance_guaranteed",
    ],
)
def test_claim_rights_pathway_mutations_never_become_valid_evidence(package, fault):
    p = copy.deepcopy(package)
    result = {r["id"]: r for r in p["results"]["results"]}
    claim = {r["id"]: r for r in p["claims"]["claims"]}
    if fault == "path_a_ready":
        p["decision"]["current_pathway"] = "PATH_A_READY_FOR_AUTHORIZATION_REVIEW"
    if fault == "multiple_paths":
        p["decision"]["current_pathway"] = [
            "PATH_A_READY_FOR_AUTHORIZATION_REVIEW",
            "PATH_B_DEFENSIBLE_MANUSCRIPT_PREPARATION",
        ]
    if fault == "rights_unassessed":
        p["rights"]["assessment_complete_for_defined_preparation_scope"] = False
    if fault == "raw_included":
        next(r for r in p["rights"]["assets"] if r["id"] == "PUB29-RAW-MEDIA")[
            "internal_preparation_allowed"
        ] = True
    if fault == "external_submission":
        p["decision"]["path_b"]["external_submission_authorized"] = True
    if fault == "genuine_relabel":
        p["sources"]["items"][0]["scientific_class"] = "GENUINE_SOURCE_WITH_VERIFIED_IDENTITY"
    if fault == "unsupported_field_claim":
        claim["C29-19"]["manuscript_use"] = "METHOD_ONLY"
    if fault == "field_relabel_as_software":
        claim["C29-19"].update(
            {
                "evidence_scope": "SOFTWARE_ONLY",
                "classification": "SUPPORTED_WITH_EXPLICIT_LIMITATIONS",
                "manuscript_use": "METHOD_ONLY",
            }
        )
    if fault == "missing_limitations":
        claim["C29-04"]["mandatory_limitations"] = []
    if fault == "unknown_citation":
        claim["C29-04"]["evidence_ids"] = ["CONSTRUCTED_TEST_NOT_REAL:unknown-evidence"]
    if fault == "duplicate_claim":
        p["claims"]["claims"][1]["id"] = p["claims"]["claims"][0]["id"]
    if fault == "historical_reproduced":
        result["H29-VISION"]["independently_reproduced"] = True
    if fault == "null_to_zero":
        result["H29-M4M5"]["reported_metrics"]["observed_real_M4_rate"] = 0
    if fault == "audio_v2_allowed":
        result["H29-AUDIO-V2"]["configuration_or_model_identity"]["execution"] = "ALLOWED"
    if fault == "leakage_removed":
        result["H29-VISION"]["dataset_split_provenance"]["reported_leakage_risk"] = False
    if fault == "audio_split_reconciled":
        result["H29-AUDIO-README"]["dataset_split_provenance"]["reported_split_role"] = (
            "TEST_WINDOWS"
        )
    if fault == "vision_value_changed":
        result["H29-VISION"]["reported_metrics"]["mAP50"] = "1.0000"
    if fault == "audio_value_changed":
        result["H29-AUDIO-REPORT"]["reported_metrics"]["ROC_AUC"] = "1.0000"
    if fault == "censoring_reconciled":
        result["H29-T0"]["reported_metrics"]["reported_left_censored"] = ["23/23"]
    if fault == "inventory_signed":
        p["sources"]["inventory_signed_off"] = True
    if fault == "R04_expanded":
        p["sources"]["R04_events"].append("train_events/event_010")
    if fault == "pilot_expanded":
        p["sources"]["pilot_events"].append("train_events/event_002")
    if fault == "new_original_invented":
        p["delta"]["new_genuine_originals"] = ["CONSTRUCTED_TEST_NOT_REAL:forged-document"]
    if fault == "author_venue_invented":
        p["rights"]["human_author_roster"] = ["CONSTRUCTED_TEST_NOT_REAL:author"]
    if fault == "freeze_removed":
        p["decision"]["engineering"]["core_freeze_recommended"] = False
    if fault == "acceptance_guaranteed":
        p["decision"]["path_b"]["publication_acceptance_guaranteed"] = True
    assert check.validate(p), fault
    assert not check.report(p)["valid"]


def test_missing_fields_refuse_instead_of_infer_approval(package):
    package["rights"].pop("external_submission_authorized")
    assert check.validate(package)


@pytest.mark.parametrize(
    "path",
    [
        "data/raw/permission.json",
        "results/summary.json",
        "experiments/weights.pt",
        "models/best.pt",
        "docs/generated/master_reaudit/../../../data/raw/video.mp4",
    ],
)
def test_non_whitelisted_metadata_is_refused_before_probe(path, monkeypatch):
    monkeypatch.setattr(
        Path, "is_symlink", lambda *a: (_ for _ in ()).throw(AssertionError("probed"))
    )
    with pytest.raises(ValueError, match="fixed reviewed"):
        check._text(path)


def test_changed_claim_input_refuses_bound_source(package, monkeypatch):
    original = check._text
    monkeypatch.setattr(
        check,
        "_text",
        lambda name: (
            original(name) + " " if name.endswith(check.INPUTS["claims"]) else original(name)
        ),
    )
    with pytest.raises(ValueError, match="binding"):
        check.load()


def test_source_manifest_cannot_smuggle_raw_resource_before_read(monkeypatch):
    original = check._text
    name = "docs/generated/master_reaudit/" + check.BINDING
    binding = json.loads(original(name))
    binding["supporting_source_sha256"]["data/raw/forbidden.mp4"] = "f" * 64

    def read(path):
        if path == name:
            return json.dumps(binding)
        raise AssertionError("read before closed manifest validation")

    monkeypatch.setattr(check, "_text", read)
    with pytest.raises(ValueError, match="exact bounded"):
        check.load()
