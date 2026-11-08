"""Bounded Mission29 claim/rights consistency check, never an evidence authenticator."""

from __future__ import annotations

import json
from pathlib import Path

from railway_detection.annotation.evidence_review.contracts import digest
from railway_detection.application.contracts import closed_json
from railway_detection.safety.constructed_authority import sha

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/generated/master_reaudit"
INPUTS = {
    "sources": "MISSION_29_SOURCE_SCIENTIFIC_EVIDENCE_REGISTER.json",
    "results": "MISSION_29_HISTORICAL_RESULTS_REGISTER.json",
    "claims": "MISSION_29_SCIENTIFIC_CLAIMS_REGISTER.json",
    "rights": "MISSION_29_PUBLICATION_RIGHTS_REGISTER.json",
    "decision": "MISSION_29_FINAL_SCIENTIFIC_EXECUTION_DECISION.json",
    "delta": "MISSION_29_EVIDENCE_RECONCILIATION_RECEIPT.json",
}
BINDING = "MISSION_29_DOCUMENT_BINDING.json"
SOURCE_PATHS = (
    "README.md",
    "pyproject.toml",
    "configs/frozen_experiment_v1.yaml",
    "configs/vision.yaml",
    "configs/audio.yaml",
    "docs/AUDIO_MODEL_V3_ESC50_REPORT.md",
    "src/railway_detection/experiments/frozen_config.py",
    "src/railway_detection/evaluation/replay_producer.py",
    "docs/PHASE5_OUTPUT_AUDIT_AND_R04_FEASIBILITY.md",
    "docs/R04_CALIBRATION_VALIDATION_REPORT.md",
    "docs/R04_ALL_EVENT_CALIBRATION_INVESTIGATION.md",
    "docs/DATASET_ANNOTATION_QUALITY_AUDIT.md",
    "docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md",
    "docs/generated/SAME_CAMERA_FEASIBILITY_CENSORING_AND_ENGINE_EXCLUSION_20261101_M4E3.md",
    "docs/generated/master_reaudit/HISTORICAL_BENCHMARK_CAUSALITY_IMPACT_AUDIT.md",
    "docs/generated/phase2/EXPERIMENT_DESIGN_CONSOLIDATED.md",
    "docs/generated/master_reaudit/MTR_ARITHMETIC_CENSORING_RECHALLENGE.md",
    "docs/generated/master_reaudit/MISSION_28_SOURCE_IDENTITY_VERIFICATION_REGISTER.json",
    "docs/generated/master_reaudit/MISSION_28_RESOURCE_FREE_EXECUTION_RECEIPT.json",
    "docs/generated/master_reaudit/MISSION_21_DESCRIPTIVE_MANUSCRIPT_SUPPORT_DRAFT.md",
    "docs/generated/master_reaudit/MISSION_28_FINAL_VALIDATION.json",
    "docs/generated/master_reaudit/MISSION_28_EXACT_SOURCE_RIGHTS_VERIFICATION_REGISTER.json",
    "docs/generated/master_reaudit/MISSION_28_REVIEWER_IDENTITY_AND_QUALIFICATION_REGISTER.json",
)
CLASSES = {
    "SUPPORTED_BY_VERIFIED_EVIDENCE",
    "SUPPORTED_WITH_EXPLICIT_LIMITATIONS",
    "DOCUMENTARY_ONLY",
    "HISTORICAL_DIAGNOSTIC_ONLY",
    "NOT_SUPPORTED",
    "REQUIRES_FUTURE_EXPERIMENT",
}
EVIDENCE_CLASSES = {
    "GENUINE_SOURCE_WITH_VERIFIED_IDENTITY",
    "DOCUMENTARY_REFERENCE_ONLY",
    "CONSTRUCTED_TEST_FIXTURE",
    "HISTORICAL_RESULT_WITH_LIMITATIONS",
    "UNVERIFIED_EXTERNAL_REFERENCE",
    "PROTECTED_RESOURCE_NOT_ACCESSED",
    "UNKNOWN",
}
PATHS = {
    "PATH_A_BLOCKED_PATH_B_UNDER_ASSESSMENT",
    "PATH_A_READY_FOR_AUTHORIZATION_REVIEW",
    "PATH_B_DEFENSIBLE_MANUSCRIPT_PREPARATION",
    "BOTH_PATHS_REQUIRE_ADDITIONAL_EVIDENCE",
}
EMPIRICAL_TOPICS = {
    "train_detection",
    "direction_classification",
    "weather_robustness",
    "night_performance",
    "fog_rain",
    "premature_opening",
    "occupancy",
    "physical_entry",
    "real_time_performance",
    "safety_improvement",
    "cross_site_generalization",
    "human_review_accuracy",
    "identity_and_reproducibility",
}


def _text(relative: str) -> str:
    fixed = {
        *SOURCE_PATHS,
        *("docs/generated/master_reaudit/" + n for n in (*INPUTS.values(), BINDING)),
    }
    if relative not in fixed:
        raise ValueError("only fixed reviewed source/document metadata allowed")
    path = ROOT / relative
    for parent in reversed((path, *path.parents)):
        if parent.is_symlink():
            raise ValueError("documentary alias refused before read")
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("bounded documentary metadata required")
    return path.read_text()


def load() -> dict:
    binding = closed_json(_text("docs/generated/master_reaudit/" + BINDING))
    if (
        set(binding) != {"schema", "input_sha256", "supporting_source_sha256"}
        or binding["schema"] != "mission29-document-binding/1"
        or set(binding["input_sha256"]) != set(INPUTS.values())
        or set(binding["supporting_source_sha256"]) != set(SOURCE_PATHS)
    ):
        raise ValueError("exact bounded Mission29 document/source manifest required")
    package = {}
    for key, name in INPUTS.items():
        body = _text("docs/generated/master_reaudit/" + name)
        if sha(body) != binding["input_sha256"][name]:
            raise ValueError("altered Mission29 input binding: " + name)
        package[key] = closed_json(body)
    for path, expected in binding["supporting_source_sha256"].items():
        if sha(_text(path)) != expected:
            raise ValueError("stale supporting documentary/code source: " + path)
    return package


def validate(p: dict) -> list[str]:
    """Consistency of this closed evidence case; not legal/source authenticity verification."""
    issues = []

    def require(ok, message):
        if not ok:
            issues.append(message)

    try:
        sources, results = p["sources"], {r["id"]: r for r in p["results"]["results"]}
        claims, rights, decision, delta = (
            p["claims"]["claims"],
            p["rights"],
            p["decision"],
            p["delta"],
        )
        require(
            delta["new_genuine_originals"] == []
            and delta["originals_independently_verified"] == [],
            "new genuine evidence requires actual verification outside this documentary checker",
        )
        require(
            sources["genuine_verified_recording_count"] == 0,
            "no verified recording identity established by this case",
        )
        require(sources["inventory_signed_off"] is False, "inventory signoff is not supplied")
        from railway_detection.annotation.evidence_review.contracts import (
            CANDIDATE_EVENTS,
            R04_EVENTS,
        )
        from railway_detection.application.evidence_intake.pilot import EVENTS, SOURCE_IDS

        require(
            set(sources["candidate_events"]) == set(CANDIDATE_EVENTS)
            and len(sources["candidate_events"]) == 27,
            "preserve exact 27 candidate events",
        )
        require(
            set(sources["R04_events"]) == set(R04_EVENTS) and len(sources["R04_events"]) == 11,
            "preserve exact R04 eleven-event scope",
        )
        require(
            sources["pilot_events"] == list(EVENTS)
            and sources["pilot_source_ids"] == list(SOURCE_IDS),
            "preserve fixed five-event/ten-source pilot",
        )
        items = sources["items"]
        ids = [r["id"] for r in items]
        require(len(ids) == len(set(ids)), "duplicate scientific evidence IDs")
        require(
            all(r["scientific_class"] in EVIDENCE_CLASSES for r in items), "unknown evidence class"
        )
        require(
            not any(
                r["scientific_class"] == "GENUINE_SOURCE_WITH_VERIFIED_IDENTITY" for r in items
            ),
            "documentary/constructed evidence cannot become verified recordings",
        )
        require(
            len(claims) == 24 and len({r["id"] for r in claims}) == 24,
            "exact unique claims required",
        )
        for row in claims:
            require(row["classification"] in CLASSES, "unknown scientific claim class")
            require(
                bool(row["evidence_ids"]) and set(row["evidence_ids"]) <= set(ids),
                "claim evidence references missing/substituted: " + row["id"],
            )
            require(bool(row["mandatory_limitations"]), "claim limitations omitted: " + row["id"])
            require(
                row["independent_empirical_validation"] is False,
                "no independent empirical validation: " + row["id"],
            )
            if row["topic"] in EMPIRICAL_TOPICS:
                require(
                    row["evidence_scope"] == "FIELD_EMPIRICAL",
                    "field claim cannot be relabeled as software evidence",
                )
            if row["evidence_scope"] == "FIELD_EMPIRICAL":
                require(
                    row["classification"] in {"NOT_SUPPORTED", "REQUIRES_FUTURE_EXPERIMENT"}
                    and row["manuscript_use"] in {"EXCLUDE", "FUTURE_WORK"},
                    "unsupported field claim cannot be a manuscript result: " + row["id"],
                )
            if row["classification"] == "HISTORICAL_DIAGNOSTIC_ONLY":
                require(
                    row["manuscript_use"] == "HISTORICAL_LIMITATION_ONLY",
                    "historical diagnostic must remain a qualified limitation note",
                )
        require(
            all(
                r["independently_reproduced"] is False
                and r["protected_inputs_accessed"] is False
                and r["external_publication_authorized"] is False
                for r in results.values()
            ),
            "historical reports are not new reproductions or release permission",
        )
        v = results["H29-VISION"]
        require(
            v["reported_metrics"]
            == {
                "mAP50": "0.9946",
                "mAP50_95": "0.855",
                "reported_objects": 487,
                "reported_cropped_images": 3165,
            },
            "historical vision values must match the cited documentary record",
        )
        for key, expected in {
            "H29-AUDIO-README": {
                "F1": "0.869",
                "ROC_AUC": "0.961",
                "operating_threshold": "0.3700",
            },
            "H29-AUDIO-REPORT": {
                "F1": "0.8690",
                "ROC_AUC": "0.9613",
                "operating_threshold": "0.3700",
            },
        }.items():
            require(
                all(
                    results[key]["reported_metrics"].get(k) == value
                    for k, value in expected.items()
                ),
                "historical audio values/precision must match cited documents",
            )
        require(
            results["H29-T0"]["reported_metrics"]["reported_left_censored"] == ["20/23", "23/23"],
            "retain the conflicting censoring counts",
        )
        require(
            v["dataset_split_provenance"]["reported_leakage_risk"] is True
            and v["dataset_split_provenance"]["reported_allow_ungrouped_fallback"] is True
            and v["dataset_split_provenance"]["split"] == "development_fallback",
            "retain historical fallback/leakage qualifications",
        )
        require(
            results["H29-AUDIO-README"]["dataset_split_provenance"]["reported_split_role"]
            == "VALIDATION_IN_README"
            and results["H29-AUDIO-REPORT"]["dataset_split_provenance"]["reported_split_role"]
            == "TEST_WINDOWS",
            "do not silently reconcile audio validation/test labels",
        )
        require(
            results["H29-M4M5"]["reported_metrics"]["observed_real_M4_rate"] is None
            and results["H29-M4M5"]["reported_metrics"]["observed_real_M5_count"] is None,
            "non-evaluable M4/M5 is not a measured zero",
        )
        require(
            results["H29-AUDIO-V2"]["configuration_or_model_identity"]["execution"] == "PROHIBITED",
            "Audio V2 remains prohibited",
        )
        require(
            rights["external_submission_authorized"] is False
            and rights["raw_or_protected_assets_release_authorized"] is False,
            "preparation is not submission or protected release",
        )
        require(
            rights["human_author_roster"] is None and rights["venue"] is None,
            "no invented author roster or venue",
        )
        assets = rights["assets"]
        require(
            len(assets) == 9 and len({r["id"] for r in assets}) == 9,
            "exact asset rights assessment",
        )
        require(
            all(
                r["external_release_authorized"] is False and r["evidence"] and r["restrictions"]
                for r in assets
            ),
            "artifact-specific release/restriction evidence required",
        )
        for r in assets:
            if r["assessment"] in {"EXCLUDED_PROTECTED_ASSET", "EXCLUDED_FROM_REPRODUCTION"}:
                require(
                    r["internal_preparation_allowed"] is False, "excluded original asset included"
                )
        classification = decision["current_pathway"]
        require(
            type(classification) is str and classification in PATHS, "exactly one current pathway"
        )
        require(
            decision["path_a"]["state"] == "BLOCKED"
            and decision["path_a"]["current_canonical_authorization"] is None,
            "Path A remains blocked; metadata is not canonical authorization",
        )
        pb = decision["path_b"]
        require(
            pb["human_author_roster"] is None
            and pb["venue"] is None
            and pb["publication_acceptance_guaranteed"] is False,
            "actual human author/venue approval absent; no guaranteed publication",
        )
        require(
            pb["external_submission_authorized"] is False
            and pb["raw_or_protected_release_authorized"] is False,
            "Path B preparation cannot authorize external release",
        )
        if classification == "PATH_B_DEFENSIBLE_MANUSCRIPT_PREPARATION":
            require(
                rights["assessment_complete_for_defined_preparation_scope"] is True
                and rights["preparation_authority"]["not_a_canonical_resource_grant"] is True
                and pb["publication_rights_assessed"] is True
                and pb["manuscript_preparation_can_begin"] is True
                and pb["protected_artifacts_excluded"] is True
                and pb["scope"] == "ORIGINAL_METHODS_TEXT_AND_QUALIFIED_SOFTWARE_VALIDATION",
                "Path B needs assessed, restricted original-draft scope",
            )
        else:
            require(
                pb["manuscript_preparation_can_begin"] is False,
                "preparation decision contradicts current pathway",
            )
        require(
            decision["engineering"]["core_freeze_recommended"] is True,
            "no unsupported new engineering work packages",
        )
        require(
            decision["empirical_experiments_executed"] is False
            and decision["protected_resources_accessed"] is False
            and decision["new_grants_issued"] == 0,
            "no execution, grant or protected access",
        )
    except (KeyError, TypeError, ValueError) as error:
        issues.append("incomplete or malformed documentary package: " + str(error))
    return issues


def report(package: dict) -> dict:
    issues = validate(package)
    return {
        "schema": "mission29-documentary-validation/1",
        "package_digest": digest(package),
        "valid": not issues,
        "issues": issues,
        "current_pathway": package.get("decision", {}).get("current_pathway"),
        "assurance": "Documentary consistency only; not source authenticity, legal clearance, "
        "canonical authorization or empirical scientific validity",
        "new_grants": 0,
    }


def main() -> int:
    try:
        value = report(load())
        print(json.dumps(value, sort_keys=True))
        return 0 if value["valid"] else 3
    except (ValueError, TypeError, KeyError, OSError) as error:
        print(
            json.dumps(
                {
                    "schema": "mission29-documentary-validation/1",
                    "valid": False,
                    "error": str(error),
                    "new_grants": 0,
                },
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
