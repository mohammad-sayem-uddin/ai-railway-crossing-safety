"""Synthetic-only tests for the Phase 12 computation engine and CLI gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from railway_detection.evaluation.evaluation_runner import (
    EvaluationRefused,
    Phase12EvaluationRunner,
    serialize_tick_log,
)
from railway_detection.evaluation.execution_gate import assess_official_phase12_readiness
from railway_detection.evaluation.ground_truth_loader import ApprovedEventGroundTruth
from railway_detection.evaluation.input_contracts import (
    EvaluationInputError,
    EvidenceClassification,
    load_evaluation_input_manifest,
)
from railway_detection.evaluation.metrics import SingleEventEvaluation
from railway_detection.simulation.runner import SimulationRunResult

SPLIT = {
    "train": ["evt_train_1"],
    "val": ["evt_val_1"],
    "test": ["evt_test_1", "evt_test_2"],
}
CAMERA_SCOPE = {event_id: "single_camera" for ids in SPLIT.values() for event_id in ids}


def _truth(
    event_id: str,
    *,
    entry: float | None = 5.0,
    clearance: float | None = 10.0,
    cohort: str = "train_events",
) -> ApprovedEventGroundTruth:
    observable: dict[str, float] = {}
    censored: list[str] = []
    if entry is not None:
        observable["T1_danger_zone_entry"] = entry
    else:
        censored.append("T1_danger_zone_entry")
    if clearance is not None:
        observable["T4_tail_clearance"] = clearance
    else:
        censored.append("T4_tail_clearance")
    return ApprovedEventGroundTruth(
        event_id=event_id,
        cohort=cohort,
        review_id=f"review_{event_id}",
        reviewer_id="synthetic_fixture",
        observable_boundaries=observable,
        censored_boundaries=tuple(sorted(censored)),
        uncertain_boundaries=(),
        not_applicable_boundaries=("T0_first_visible", "T2", "T3", "T_scene_clear"),
    )


def _sim_result(event_id: str, *, closed_s: float = 8.0) -> SimulationRunResult:
    return SimulationRunResult(
        event_id=event_id,
        scenario_name="synthetic_phase12_baseline",
        total_duration_s=15.0,
        closed_duration_s=closed_s,
        warning_lead_time_s=3.0,
        premature_opening_detected=False,
    )


def _full_inputs() -> dict:
    return {
        "event_split": SPLIT,
        "camera_scope": dict(CAMERA_SCOPE),
        "accepted_sync_events": set(),
        "ground_truth": [_truth("evt_test_1"), _truth("evt_test_2")],
        "simulation_results": {
            "evt_test_1": _sim_result("evt_test_1"),
            "evt_test_2": _sim_result("evt_test_2"),
        },
    }


def test_valid_synthetic_run_calculates_and_serializes_deterministically(tmp_path: Path):
    kwargs = _full_inputs()
    output = tmp_path / "phase12_synthetic"
    result = Phase12EvaluationRunner().run(**kwargs, output_dir=output)
    repeated = Phase12EvaluationRunner().run(**kwargs)

    assert result.cohort_summary.total_events == 2
    assert result.cohort_summary.eligible_events == 2
    assert result.cohort_summary.missed_train_rate is None
    assert result.evidence_classification is EvidenceClassification.SYNTHETIC
    assert result.run_manifest["evidence_classification"] == "synthetic"
    assert result.run_manifest["authorization_status"] == "not_verified"
    assert result.run_manifest["provenance"]["official_authorization_verified"] is False
    assert result.tick_logs == repeated.tick_logs
    assert json.loads((output / "run_manifest.json").read_text())["phase"] == "12"
    assert (output / "cohort_summary.json").is_file()
    assert (output / "tick_logs/evt_test_1.ticklog.json").is_file()
    changed_config = Phase12EvaluationRunner().run(
        **kwargs, frozen_config_sha256="frozen-config-changed"
    )
    assert changed_config.run_manifest["run_id"] != result.run_manifest["run_id"]


def test_invalid_split_camera_scope_missing_replay_and_extra_input_refused():
    kwargs = _full_inputs()
    kwargs["event_split"] = {
        "train": ["evt_test_1"],
        "val": ["evt_val_1"],
        "test": ["evt_test_1", "evt_test_2"],
    }
    with pytest.raises(EvaluationRefused, match="event split or camera scope"):
        Phase12EvaluationRunner().run(**kwargs)

    kwargs = _full_inputs()
    kwargs["camera_scope"]["evt_test_1"] = "dual_camera"
    with pytest.raises(EvaluationRefused, match="camera scope"):
        Phase12EvaluationRunner().run(**kwargs)

    kwargs = _full_inputs()
    kwargs["camera_scope"] = dict(CAMERA_SCOPE)
    kwargs["simulation_results"].pop("evt_test_2")
    with pytest.raises(EvaluationRefused, match="lack simulation replays"):
        Phase12EvaluationRunner().run(**kwargs)

    kwargs = _full_inputs()
    kwargs["simulation_results"]["evt_train_1"] = _sim_result("evt_train_1")
    with pytest.raises(EvaluationRefused, match="outside test split"):
        Phase12EvaluationRunner().run(**kwargs)


def test_duplicate_truth_invalid_record_and_invalid_timestamps_refused():
    kwargs = _full_inputs()
    kwargs["camera_scope"] = dict(CAMERA_SCOPE)
    kwargs["ground_truth"] = [_truth("evt_test_1"), _truth("evt_test_1")]
    with pytest.raises(EvaluationRefused, match="duplicate ground-truth"):
        Phase12EvaluationRunner().run(**kwargs)

    kwargs = _full_inputs()
    kwargs["camera_scope"] = dict(CAMERA_SCOPE)
    kwargs["ground_truth"][0] = {"event_id": "evt_test_1"}
    with pytest.raises(EvaluationRefused, match="validated typed records"):
        Phase12EvaluationRunner().run(**kwargs)

    kwargs = _full_inputs()
    kwargs["camera_scope"] = dict(CAMERA_SCOPE)
    kwargs["simulation_results"]["evt_test_1"].total_duration_s = float("nan")
    with pytest.raises(EvaluationRefused, match="invalid duration"):
        Phase12EvaluationRunner().run(**kwargs)


def test_censored_boundaries_are_not_substituted_with_zero():
    kwargs = _full_inputs()
    kwargs["camera_scope"] = dict(CAMERA_SCOPE)
    kwargs["ground_truth"] = [_truth("evt_test_1", entry=None), _truth("evt_test_2")]
    result = Phase12EvaluationRunner().run(**kwargs)
    event = next(item for item in result.single_evaluations if item.event_id == "evt_test_1")
    assert event.missed_train is None
    assert event.premature_opening is None
    assert event.excess_closed_duration_s is None


def test_manifest_cohort_metrics_keep_no_train_out_of_train_denominator(tmp_path: Path):
    path = _write_input_manifest(tmp_path / "cohorts")
    manifest = json.loads(path.read_text())
    manifest["events"][-1]["cohort"] = "no_train_events"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    result = Phase12EvaluationRunner().run_from_manifest(
        manifest_path=path,
        ground_truth=[_truth("evt_test", cohort="no_train_events")],
        simulation_results={"evt_test": _sim_result("evt_test", closed_s=8.0)},
    )
    assert result.cohort_summary.eligible_events == 0
    assert result.cohort_summary.no_train_events == 1
    assert result.cohort_summary.false_alarm_count == 1


def test_tick_log_serialization_is_canonical():
    simulation = _sim_result("evt_deterministic")
    evaluation = SingleEventEvaluation(event_id="evt_deterministic", scenario_name="synthetic")
    first = serialize_tick_log(simulation, evaluation)
    second = serialize_tick_log(simulation, evaluation)
    assert first == second
    assert json.loads(first)["kind"] == "phase12_tick_log"


def test_real_evidence_execution_is_refused_even_in_memory():
    kwargs = _full_inputs()
    kwargs["camera_scope"] = dict(CAMERA_SCOPE)
    kwargs["evidence_classification"] = EvidenceClassification.REAL
    with pytest.raises(EvaluationRefused, match="only through run_official"):
        Phase12EvaluationRunner().run(**kwargs)


def test_run_safe_emits_machine_readable_failure(tmp_path: Path):
    failure = Phase12EvaluationRunner().run_safe(
        failure_report_path=tmp_path / "failure.json",
        **{**_full_inputs(), "ground_truth": []},
    )
    assert failure.status == "BLOCKED"
    assert failure.to_dict()["blockers"][0]["code"] == "EVALUATION_REFUSED"
    assert json.loads((tmp_path / "failure.json").read_text())["partial_outputs_written"] is False


def _write_input_manifest(root: Path, *, split_override: dict | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    event_groups = {"train": ["evt_train"], "val": ["evt_val"], "test": ["evt_test"]}
    if split_override is not None:
        event_groups = split_override
    for role, ids in event_groups.items():
        for event_id in ids:
            source = root / f"{event_id}.json"
            source.write_text(json.dumps({"event_id": event_id, "frames": []}), encoding="utf-8")
            import hashlib

            entries.append(
                {
                    "event_id": event_id,
                    "cohort": "train_events",
                    "split_role": role,
                    "source_path": source.name,
                    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                }
            )
    manifest = {
        "schema_version": "phase12-evaluation-inputs/1",
        "evidence_classification": "synthetic",
        "partitions": event_groups,
        "events": entries,
        "camera_scope_by_event": {
            event_id: "single_camera"
            for ids in event_groups.values()
            for event_id in ids
        },
        "accepted_sync_events": [],
    }
    path = root / "inputs.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_manifest_bound_runner_uses_manifest_identity_and_synthetic_label(tmp_path: Path):
    path = _write_input_manifest(tmp_path / "bound")
    inputs = load_evaluation_input_manifest(path)
    truth = [_truth("evt_test")]
    result = Phase12EvaluationRunner().run_from_manifest(
        manifest_path=path,
        ground_truth=truth,
        simulation_results={"evt_test": _sim_result("evt_test")},
        output_dir=tmp_path / "out",
        command="synthetic-test",
    )
    assert result.evidence_classification is EvidenceClassification.SYNTHETIC
    assert result.run_manifest["provenance"]["input_manifest_sha256"] == inputs.manifest_sha256
    assert result.run_manifest["provenance"]["input_manifest_path"] == str(path.resolve())


def test_manifest_bound_runner_rejects_missing_declared_camera_scope(tmp_path: Path):
    path = _write_input_manifest(tmp_path / "scope")
    manifest = json.loads(path.read_text())
    manifest.pop("camera_scope_by_event")
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(EvaluationRefused, match="CAMERA_SCOPE_MISSING"):
        Phase12EvaluationRunner().run_from_manifest(
            manifest_path=path,
            ground_truth=[_truth("evt_test")],
            simulation_results={"evt_test": _sim_result("evt_test")},
        )


def test_manifest_bound_runner_rejects_cohort_claim_mismatch(tmp_path: Path):
    path = _write_input_manifest(tmp_path / "cohort-mismatch")
    with pytest.raises(EvaluationRefused, match="MANIFEST_COHORT_MISMATCH"):
        Phase12EvaluationRunner().run_from_manifest(
            manifest_path=path,
            ground_truth=[_truth("evt_test", cohort="no_train_events")],
            simulation_results={"evt_test": _sim_result("evt_test")},
        )


def test_manifest_bound_runner_rejects_swapped_source_bytes(tmp_path: Path):
    path = _write_input_manifest(tmp_path / "swapped")
    root = path.parent
    first = (root / "evt_train.json").read_bytes()
    second = (root / "evt_val.json").read_bytes()
    (root / "evt_train.json").write_bytes(second)
    (root / "evt_val.json").write_bytes(first)
    with pytest.raises(EvaluationRefused, match="SOURCE_HASH_MISMATCH"):
        Phase12EvaluationRunner().run_from_manifest(
            manifest_path=path,
            ground_truth=[_truth("evt_test")],
            simulation_results={"evt_test": _sim_result("evt_test")},
        )


def test_manifest_bound_runner_detects_source_change_between_validation_and_use(
    tmp_path: Path, monkeypatch
):
    path = _write_input_manifest(tmp_path / "toctou")
    source = path.parent / "evt_test.json"
    original_loader = __import__(
        "railway_detection.evaluation.input_contracts", fromlist=["load_evaluation_input_manifest"]
    ).load_evaluation_input_manifest
    calls = 0

    def mutate_after_first_validation(manifest_path, *, verify_sources=True):
        nonlocal calls
        calls += 1
        result = original_loader(manifest_path, verify_sources=verify_sources)
        if calls == 1:
            source.write_text('{"event_id":"changed"}', encoding="utf-8")
        return result

    monkeypatch.setattr(
        "railway_detection.evaluation.evaluation_runner.load_evaluation_input_manifest",
        mutate_after_first_validation,
    )
    with pytest.raises(EvaluationRefused, match="SOURCE_HASH_MISMATCH"):
        Phase12EvaluationRunner().run_from_manifest(
            manifest_path=path,
            ground_truth=[_truth("evt_test")],
            simulation_results={"evt_test": _sim_result("evt_test")},
        )


def test_forged_manifest_approval_fields_do_not_grant_authorization(tmp_path: Path):
    path = _write_input_manifest(tmp_path / "forged-approval")
    manifest = json.loads(path.read_text())
    manifest["approval_status"] = "APPROVED"
    manifest["eval_auth"] = True
    path.write_text(json.dumps(manifest), encoding="utf-8")
    verdict = assess_official_phase12_readiness(
        tmp_path / "forged-approval",
        input_manifest_path=path,
    )
    assert not verdict.ready
    assert "SYNTHETIC_INPUTS_NOT_OFFICIAL" in verdict.blocker_codes
    assert "EVAL_AUTH_NOT_GRANTED" in verdict.blocker_codes


def test_gate_manifest_validation_does_not_open_source_media(tmp_path: Path, monkeypatch):
    path = _write_input_manifest(tmp_path / "metadata_only")
    manifest = json.loads(path.read_text())
    manifest["events"][0]["source_path"] = "missing_media.mov"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    def fail_if_hashing(_path):
        raise AssertionError("official gate must not hash or open source media")

    monkeypatch.setattr(
        "railway_detection.evaluation.input_contracts.sha256_file", fail_if_hashing
    )
    verdict = assess_official_phase12_readiness(
        tmp_path,
        input_manifest_path=path,
    )
    assert "INPUT_MISSING" not in verdict.blocker_codes
    assert "SOURCE_HASH_MISMATCH" not in verdict.blocker_codes


def test_input_manifest_loads_in_sorted_order_and_hashes_sources(tmp_path: Path):
    path = _write_input_manifest(tmp_path / "inputs")
    inputs = load_evaluation_input_manifest(path)
    assert inputs.evidence_classification is EvidenceClassification.SYNTHETIC
    assert [item.event_id for item in inputs.events] == ["evt_test", "evt_train", "evt_val"]
    assert len(inputs.manifest_sha256) == 64
    assert set(inputs.source_fingerprints) == {"evt_train", "evt_val", "evt_test"}


def test_input_manifest_rejects_split_leakage_duplicate_ids_and_hash_mismatch(tmp_path: Path):
    leaked = _write_input_manifest(
        tmp_path / "leaked",
        split_override={"train": ["same"], "val": ["evt_val"], "test": ["same"]},
    )
    with pytest.raises(EvaluationInputError, match="SPLIT_LEAKAGE"):
        load_evaluation_input_manifest(leaked)

    valid = _write_input_manifest(tmp_path / "hash")
    manifest = json.loads(valid.read_text())
    manifest["events"][0]["source_sha256"] = "0" * 64
    valid.write_text(json.dumps(manifest))
    with pytest.raises(EvaluationInputError, match="SOURCE_HASH_MISMATCH"):
        load_evaluation_input_manifest(valid)


def test_official_gate_reports_actual_blockers_without_writing(tmp_path: Path):
    from railway_detection.cli.main import main

    workspace = tmp_path / "isolated_workspace"
    workspace.mkdir()
    verdict = assess_official_phase12_readiness(workspace)
    assert not verdict.ready
    assert "EVAL_AUTH_NOT_GRANTED" in verdict.blocker_codes
    # The EVAL-AUTH verification mechanism is now defined (governance.py), so the
    # "mechanism undefined" blocker no longer exists; an absent record is "not granted".
    assert "EVAL_AUTH_MECHANISM_UNDEFINED" not in verdict.blocker_codes
    # The protocol profile is documented; an override file is optional, never a blocker.
    assert "PROTOCOL_DECISION_MISSING" not in verdict.blocker_codes
    assert "AUTHORITY_ALLOWLIST_UNAVAILABLE" in verdict.blocker_codes
    assert "EVENT_SPLIT_DECISION_MISSING" in verdict.blocker_codes
    assert "R04_SCOPE_DECISION_MISSING" in verdict.blocker_codes
    assert "STAGE21_RECORDS_MISSING" in verdict.blocker_codes

    report = tmp_path / "blockers.json"
    code = main(
        [
            "evaluation",
            "run",
            "--repository-root",
            str(workspace),
            "--blocker-report",
            str(report),
        ]
    )
    assert code == 3
    payload = json.loads(report.read_text())
    assert payload["status"] == "BLOCKED"
    assert payload["evidence_classification"] == "real"
    assert payload["partial_outputs_written"] is False


def test_cli_default_block_has_no_result_artifacts(tmp_path: Path, monkeypatch):
    from railway_detection.cli.main import main

    monkeypatch.chdir(tmp_path)
    code = main(["evaluation", "run"])
    assert code == 3
    assert list(tmp_path.iterdir()) == []