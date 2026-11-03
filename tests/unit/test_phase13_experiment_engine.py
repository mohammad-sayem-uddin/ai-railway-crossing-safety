"""Synthetic integration tests for reusable Phase 13 experiment infrastructure."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from railway_detection.evaluation.experiment_engine import (
    ExperimentCondition,
    ExperimentPlan,
    ExperimentPlanError,
    Phase13ExperimentEngine,
)
from railway_detection.evaluation.input_contracts import EvidenceClassification

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


@dataclass
class SyntheticProvider:
    @property
    def evidence_classification(self):
        return EvidenceClassification.SYNTHETIC

    def event_ids(self):
        return ["evt_b", "evt_a"]

    def load_event(self, event_id: str):
        return {"event_id": event_id, "synthetic": True}

    def input_sha256(self, event_id: str):
        return hashlib.sha256(event_id.encode()).hexdigest()


def _plan(seeds: tuple[int, ...] = (42, 43)) -> ExperimentPlan:
    return ExperimentPlan(
        plan_id="synthetic-phase13-plan",
        frozen_config_sha256=HASH_A,
        policy_sha256=HASH_B,
        checkpoint_sha256={"vision": HASH_C},
        input_split_sha256=HASH_B,
        repeat_seeds=seeds,
        conditions=(
            ExperimentCondition("baseline", "baseline"),
            ExperimentCondition(
                "confidence-noise",
                "treatment",
                changed_factors=("confidence_noise",),
                perturbation={"kind": "confidence_noise", "sigma": 0.1},
            ),
        ),
    )


def _inference(*, condition, event_id, event_input, seed):
    assert event_input["synthetic"] is True
    scale = 1.0 if condition.role == "baseline" else 0.8
    return {"toy_score": scale + (seed % 10) / 100 + (0.01 if event_id == "evt_b" else 0)}


def test_synthetic_experiment_is_deterministic_and_reports_comparison(tmp_path: Path):
    first = Phase13ExperimentEngine().run(
        plan=_plan(),
        data_provider=SyntheticProvider(),
        inference_provider=_inference,
        output_dir=tmp_path / "run_one",
    )
    second = Phase13ExperimentEngine().run(
        plan=_plan(),
        data_provider=SyntheticProvider(),
        inference_provider=_inference,
        output_dir=tmp_path / "run_two",
    )

    assert first.status == "SYNTHETIC_ENGINEERING_ONLY"
    assert first.evidence_classification is EvidenceClassification.SYNTHETIC
    assert first.metrics_by_condition == second.metrics_by_condition
    assert first.comparisons_to_baseline["confidence-noise"]["toy_score"] == pytest.approx(
        -0.2
    )
    assert first.manifest["empirical_performance_claim"] is False
    assert first.manifest["authorization_status"] == "not_authorized"
    assert first.manifest["evidence_classification"] == "synthetic"
    assert first.manifest["git_commit"]
    assert (first.output_dir / "experiment_manifest.json").read_bytes() == (
        second.output_dir / "experiment_manifest.json"
    ).read_bytes()


def test_plan_requires_one_baseline_one_factor_and_unique_seeds():
    with pytest.raises(ExperimentPlanError, match="exactly one baseline"):
        ExperimentPlan(
            plan_id="missing-baseline",
            frozen_config_sha256=HASH_A,
            policy_sha256=HASH_B,
            checkpoint_sha256={},
            input_split_sha256=HASH_C,
            repeat_seeds=(1,),
            conditions=(ExperimentCondition("treatment", "treatment", ("factor",)),),
        )
    with pytest.raises(ExperimentPlanError, match="exactly one changed factor"):
        ExperimentCondition("compound", "treatment", ("factor_a", "factor_b"))
    with pytest.raises(ExperimentPlanError, match="unique"):
        _plan((42, 42))


def test_experiment_engine_rejects_real_provider_and_bad_metric_contract(tmp_path: Path):
    class RealProvider(SyntheticProvider):
        @property
        def evidence_classification(self):
            return EvidenceClassification.REAL

    with pytest.raises(ExperimentPlanError, match="synthetic inputs only"):
        Phase13ExperimentEngine().run(
            plan=_plan(),
            data_provider=RealProvider(),
            inference_provider=_inference,
            output_dir=tmp_path / "real",
        )
    assert not (tmp_path / "real").exists()

    with pytest.raises(ExperimentPlanError, match="must be numeric"):
        Phase13ExperimentEngine().run(
            plan=_plan(),
            data_provider=SyntheticProvider(),
            inference_provider=lambda **_: {"bad": "metric"},
            output_dir=tmp_path / "bad",
        )


def test_manifest_has_complete_fingerprints_and_stable_serialization(tmp_path: Path):
    result = Phase13ExperimentEngine().run(
        plan=_plan(),
        data_provider=SyntheticProvider(),
        inference_provider=_inference,
        output_dir=tmp_path / "run",
    )
    manifest = json.loads((tmp_path / "run/experiment_manifest.json").read_text())
    assert manifest["plan"]["frozen_config_sha256"] == HASH_A
    assert manifest["plan"]["policy_sha256"] == HASH_B
    assert manifest["plan"]["checkpoint_sha256"] == {"vision": HASH_C}
    assert set(manifest["input_sha256_by_event"]) == {"evt_a", "evt_b"}
    assert result.manifest["repeat_count"] == 2

    class DifferentInputProvider(SyntheticProvider):
        def input_sha256(self, event_id: str):
            return hashlib.sha256((event_id + "-different").encode()).hexdigest()

    changed = Phase13ExperimentEngine().run(
        plan=_plan(),
        data_provider=DifferentInputProvider(),
        inference_provider=_inference,
        output_dir=tmp_path / "changed-input",
    )
    assert changed.manifest["run_id"] != result.manifest["run_id"]


def test_continue_on_error_records_partial_failure_without_fake_aggregate(tmp_path: Path):
    def flaky(**kwargs):
        if kwargs["event_id"] == "evt_a" and kwargs["condition"].role == "treatment":
            raise RuntimeError("synthetic injected failure")
        return {"toy_score": 1.0}

    result = Phase13ExperimentEngine().run(
        plan=_plan(seeds=(42,)),
        data_provider=SyntheticProvider(),
        inference_provider=flaky,
        output_dir=tmp_path / "partial",
        continue_on_error=True,
    )
    assert result.status == "PARTIAL"
    assert len(result.failures) == 1
    assert result.metrics_by_condition["baseline"]["toy_score"] == 1.0
    assert "confidence-noise" not in result.comparisons_to_baseline
    assert result.manifest["evidence_classification"] == "synthetic"
    assert result.manifest["comparison_status"]["confidence-noise"] == (
        "unavailable_failed_condition"
    )


def test_failed_baseline_is_fatal_and_fingerprint_changes_are_recorded(tmp_path: Path):
    def failing_baseline(**kwargs):
        if kwargs["condition"].role == "baseline":
            raise RuntimeError("baseline unavailable")
        return {"toy_score": 1.0}

    with pytest.raises(ExperimentPlanError, match="baseline has failed"):
        Phase13ExperimentEngine().run(
            plan=_plan(seeds=(42,)),
            data_provider=SyntheticProvider(),
            inference_provider=failing_baseline,
            output_dir=tmp_path / "baseline-failed",
            continue_on_error=True,
        )

    class ChangingProvider(SyntheticProvider):
        calls = 0

        def input_sha256(self, event_id: str):
            self.calls += 1
            digest = super().input_sha256(event_id)
            return digest if self.calls == 1 else hashlib.sha256(b"changed").hexdigest()

    with pytest.raises(ExperimentPlanError, match="fingerprint changed"):
        Phase13ExperimentEngine().run(
            plan=_plan(seeds=(42,)),
            data_provider=ChangingProvider(),
            inference_provider=_inference,
            output_dir=tmp_path / "changed",
            continue_on_error=False,
        )


def test_nonfinite_metric_is_rejected(tmp_path: Path):
    with pytest.raises(ExperimentPlanError, match="must be finite"):
        Phase13ExperimentEngine().run(
            plan=_plan(seeds=(42,)),
            data_provider=SyntheticProvider(),
            inference_provider=lambda **_: {"toy_score": float("nan")},
            output_dir=tmp_path / "nonfinite",
        )

def test_failed_baseline_still_persists_a_failure_manifest_without_aggregates(tmp_path: Path):
    def failing_baseline(**kwargs):
        if kwargs["condition"].role == "baseline":
            raise RuntimeError("baseline unavailable")
        return {"toy_score": 1.0}

    out = tmp_path / "baseline-failed"
    with pytest.raises(ExperimentPlanError, match="baseline has failed"):
        Phase13ExperimentEngine().run(
            plan=_plan(seeds=(42,)),
            data_provider=SyntheticProvider(),
            inference_provider=failing_baseline,
            output_dir=out,
            continue_on_error=True,
        )
    manifest = json.loads((out / "experiment_manifest.json").read_text())
    assert manifest["status"] == "FAILED_BASELINE"
    assert manifest["metrics_by_condition"] == {} and manifest["comparisons_to_baseline"] == {}
    assert manifest["empirical_performance_claim"] is False
    assert len(manifest["failures"]) == 2
    assert manifest["completed_cells_by_condition"]["baseline"] == 0
    assert not (out / "metrics_by_condition.json").exists()


def test_abort_without_continue_on_error_records_progress_not_aggregates(tmp_path: Path):
    def fail_second_event(**kwargs):
        if kwargs["event_id"] == "evt_b":
            raise RuntimeError("injected")
        return {"toy_score": 1.0}

    out = tmp_path / "aborted"
    with pytest.raises(ExperimentPlanError, match="inference failed"):
        Phase13ExperimentEngine().run(
            plan=_plan(seeds=(42,)),
            data_provider=SyntheticProvider(),
            inference_provider=fail_second_event,
            output_dir=out,
        )
    manifest = json.loads((out / "experiment_manifest.json").read_text())
    assert manifest["status"] == "FAILED"
    assert manifest["metrics_by_condition"] == {}
    assert manifest["completed_cells_by_condition"] == {"baseline": 1, "confidence-noise": 0}
    assert manifest["failures"][0]["event_id"] == "evt_b"


def test_baseline_and_treatment_see_identical_inputs_and_seeds(tmp_path: Path):
    seen: dict[str, set[tuple[str, int, str]]] = {}

    def recording(*, condition, event_id, event_input, seed):
        digest = hashlib.sha256(json.dumps(event_input, sort_keys=True).encode()).hexdigest()
        seen.setdefault(condition.condition_id, set()).add((event_id, seed, digest))
        return {"toy_score": 1.0}

    result = Phase13ExperimentEngine().run(
        plan=_plan(),
        data_provider=SyntheticProvider(),
        inference_provider=recording,
        output_dir=tmp_path / "paired",
    )
    assert seen["baseline"] == seen["confidence-noise"]
    assert len(seen["baseline"]) == 2 * 2
    assert result.manifest["expected_cells_per_condition"] == 4
    assert result.manifest["completed_cells_by_condition"] == {
        "baseline": 4,
        "confidence-noise": 4,
    }
    assert result.manifest["comparison_status"]["confidence-noise"] == "available"


def test_treatment_must_change_exactly_one_thing(tmp_path: Path):
    def plan_with(condition: ExperimentCondition) -> ExperimentPlan:
        return ExperimentPlan(
            plan_id="p",
            frozen_config_sha256=HASH_A,
            policy_sha256=HASH_B,
            checkpoint_sha256={},
            input_split_sha256=HASH_C,
            repeat_seeds=(1,),
            conditions=(ExperimentCondition("baseline", "baseline"), condition),
        )

    with pytest.raises(ExperimentPlanError, match="identical to the baseline"):
        plan_with(ExperimentCondition("noop", "treatment", ("factor",)))
    with pytest.raises(ExperimentPlanError, match="changes more than the one declared factor"):
        plan_with(
            ExperimentCondition(
                "both",
                "treatment",
                ("factor",),
                overrides={"factor": 1},
                perturbation={"kind": "factor", "sigma": 0.1},
            )
        )
    assert plan_with(
        ExperimentCondition("ok", "treatment", ("factor",), overrides={"factor": 1})
    ).conditions[1].condition_id == "ok"


# --- additional Phase 13 guarantees ---------------------------------------------------------


def _plan_with(*treatments: ExperimentCondition, seeds=(1, 2)) -> ExperimentPlan:
    return ExperimentPlan(
        plan_id="p",
        frozen_config_sha256=HASH_A,
        policy_sha256=HASH_B,
        checkpoint_sha256={},
        input_split_sha256=HASH_C,
        repeat_seeds=seeds,
        conditions=(ExperimentCondition("baseline", "baseline"), *treatments),
    )


def test_hidden_configuration_changes_in_a_treatment_are_refused():
    with pytest.raises(ExperimentPlanError, match="hidden configuration changes"):
        _plan_with(
            ExperimentCondition(
                "t", "treatment", ("a",), overrides={"a": 1, "b": 2}
            )
        )
    with pytest.raises(ExperimentPlanError, match="declared factor"):
        _plan_with(ExperimentCondition("t", "treatment", ("a",), overrides={"b": 2}))
    with pytest.raises(ExperimentPlanError, match="does not match its declared factor"):
        _plan_with(
            ExperimentCondition(
                "t", "treatment", ("a",), perturbation={"kind": "other", "sigma": 0.1}
            )
        )


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), object(), {"x": float("nan")}])
def test_non_finite_or_non_plain_condition_parameters_are_refused(bad):
    with pytest.raises(ExperimentPlanError):
        _plan_with(ExperimentCondition("t", "treatment", ("a",), overrides={"a": bad}))


def test_inference_that_mutates_its_input_is_a_failure(tmp_path: Path):
    def mutating(*, condition, event_id, event_input, seed):
        event_input["synthetic"] = False  # edits the shared input
        return {"toy_score": 1.0}

    out = tmp_path / "mut"
    with pytest.raises(ExperimentPlanError, match="mutated its input"):
        Phase13ExperimentEngine().run(
            plan=_plan(seeds=(42,)),
            data_provider=SyntheticProvider(),
            inference_provider=mutating,
            output_dir=out,
        )
    assert json.loads((out / "experiment_manifest.json").read_text())["status"] == "FAILED"


def test_inputs_cannot_leak_between_conditions(tmp_path: Path):
    shared = {"evt_a": {"event_id": "evt_a", "synthetic": True},
              "evt_b": {"event_id": "evt_b", "synthetic": True}}

    class Shared(SyntheticProvider):
        def load_event(self, event_id):
            return shared[event_id]

    seen = []

    def spy(*, condition, event_id, event_input, seed):
        seen.append((condition.condition_id, id(event_input)))
        return {"toy_score": 1.0}

    Phase13ExperimentEngine().run(
        plan=_plan(seeds=(1,)), data_provider=Shared(), inference_provider=spy,
        output_dir=tmp_path / "leak",
    )
    assert len({identity for _, identity in seen}) == len(seen)  # a fresh copy every call
    assert all(event == {"event_id": event["event_id"], "synthetic": True}
               for event in shared.values())


def test_a_treatment_with_a_different_metric_set_is_not_compared(tmp_path: Path):
    def uneven(*, condition, event_id, event_input, seed):
        metrics = {"toy_score": 1.0}
        if condition.role == "treatment":
            metrics["extra"] = 2.0
        return metrics

    result = Phase13ExperimentEngine().run(
        plan=_plan(seeds=(1,)), data_provider=SyntheticProvider(), inference_provider=uneven,
        output_dir=tmp_path / "uneven",
    )
    assert result.manifest["comparison_status"]["confidence-noise"] == (
        "unavailable_incompatible_metrics"
    )
    assert result.comparisons_to_baseline == {}


def test_a_failure_on_a_single_seed_makes_the_whole_comparison_unavailable(tmp_path: Path):
    def flaky(*, condition, event_id, event_input, seed):
        if condition.role == "treatment" and seed == 43 and event_id == "evt_a":
            raise RuntimeError("one cell failed")
        return {"toy_score": 1.0}

    result = Phase13ExperimentEngine().run(
        plan=_plan(), data_provider=SyntheticProvider(), inference_provider=flaky,
        output_dir=tmp_path / "cell", continue_on_error=True,
    )
    assert result.status == "PARTIAL"
    assert result.manifest["comparison_status"]["confidence-noise"] == (
        "unavailable_failed_condition"
    )
    assert result.comparisons_to_baseline == {}
    assert result.manifest["condition_status"] == {"baseline": "complete",
                                                   "confidence-noise": "failed"}


def test_run_id_is_deterministic_and_sensitive_to_every_pinned_input(tmp_path: Path):
    def run(plan, provider=None):
        return Phase13ExperimentEngine().run(
            plan=plan, data_provider=provider or SyntheticProvider(),
            inference_provider=_inference, output_dir=tmp_path / f"r{run.count}",
        ).manifest["run_id"], run.__setattr__("count", run.count + 1)

    run.count = 0
    first, _ = run(_plan())
    again, _ = run(_plan())
    assert first == again

    class Reordered(SyntheticProvider):
        def event_ids(self):
            return ["evt_a", "evt_b"]  # same events, different provider order

    assert run(_plan(), Reordered())[0] == first
    assert run(_plan((7, 8)))[0] != first  # different seeds
    class OtherInput(SyntheticProvider):
        def input_sha256(self, event_id):
            return hashlib.sha256(b"x" + event_id.encode()).hexdigest()

    assert run(_plan(), OtherInput())[0] != first


def test_partial_run_can_resume_only_missing_cells_and_retry_failures(tmp_path: Path):
    attempts: list[tuple[str, str]] = []
    failed_once = {"value": True}

    def flaky(*, condition, event_id, event_input, seed):
        attempts.append((condition.condition_id, event_id))
        if condition.role == "treatment" and event_id == "evt_a" and failed_once["value"]:
            failed_once["value"] = False
            raise RuntimeError("transient synthetic failure")
        return _inference(
            condition=condition, event_id=event_id, event_input=event_input, seed=seed
        )

    out = tmp_path / "resume"
    first = Phase13ExperimentEngine().run(
        plan=_plan(seeds=(42,)),
        data_provider=SyntheticProvider(),
        inference_provider=flaky,
        output_dir=out,
        continue_on_error=True,
    )
    assert first.status == "PARTIAL"
    attempts_before_resume = len(attempts)
    second = Phase13ExperimentEngine().run(
        plan=_plan(seeds=(42,)),
        data_provider=SyntheticProvider(),
        inference_provider=flaky,
        output_dir=out,
        resume=True,
    )
    assert second.status == "SYNTHETIC_ENGINEERING_ONLY"
    # Baseline cells were checkpointed and skipped; only the failed treatment
    # cell was retried.
    assert attempts[attempts_before_resume:] == [("confidence-noise", "evt_a")]
    assert second.manifest["comparison_status"]["confidence-noise"] == "available"


def test_resume_refuses_altered_input_fingerprint(tmp_path: Path):
    out = tmp_path / "resume-altered"
    Phase13ExperimentEngine().run(
        plan=_plan(seeds=(42,)),
        data_provider=SyntheticProvider(),
        inference_provider=_inference,
        output_dir=out,
    )

    class Altered(SyntheticProvider):
        def input_sha256(self, event_id: str):
            return hashlib.sha256((event_id + "-altered").encode()).hexdigest()

    with pytest.raises(ExperimentPlanError, match="run_id|plan or input fingerprints"):
        Phase13ExperimentEngine().run(
            plan=_plan(seeds=(42,)),
            data_provider=Altered(),
            inference_provider=_inference,
            output_dir=out,
            resume=True,
        )


def test_duplicate_conditions_events_and_baselines_are_refused():
    with pytest.raises(ExperimentPlanError, match="unique"):
        _plan_with(
            ExperimentCondition("t", "treatment", ("a",), overrides={"a": 1}),
            ExperimentCondition("t", "treatment", ("b",), overrides={"b": 1}),
        )
    with pytest.raises(ExperimentPlanError, match="exactly one baseline"):
        ExperimentPlan(
            plan_id="p", frozen_config_sha256=HASH_A, policy_sha256=HASH_B, checkpoint_sha256={},
            input_split_sha256=HASH_C, repeat_seeds=(1,),
            conditions=(ExperimentCondition("b1", "baseline"),
                        ExperimentCondition("b2", "baseline")),
        )


@pytest.mark.parametrize("bad", [True, "1.0", None, float("inf"), float("-inf")])
def test_invalid_metric_values_are_rejected_or_recorded(tmp_path: Path, bad):
    with pytest.raises(ExperimentPlanError):
        Phase13ExperimentEngine().run(
            plan=_plan(seeds=(1,)), data_provider=SyntheticProvider(),
            inference_provider=lambda **_: {"toy_score": bad}, output_dir=tmp_path / "bad",
        )


def test_synthetic_experiments_cannot_write_into_official_result_trees():
    from pathlib import Path as P

    repo = P(__file__).resolve().parents[2]
    for tree in ("results", "experiments", "data", "configs", "models"):
        target = repo / tree / "phase13_should_never_exist"
        with pytest.raises(ExperimentPlanError, match="may not be written"):
            Phase13ExperimentEngine().run(
                plan=_plan(seeds=(1,)), data_provider=SyntheticProvider(),
                inference_provider=_inference, output_dir=target,
            )
        assert not target.exists()


def test_official_prerequisites_still_block_the_legacy_empirical_entry_point(tmp_path):
    import shutil

    from railway_detection.evaluation.ablation_runner import (
        Phase13AblationRunner,
        Phase13ExecutionBlocked,
        Phase13Prerequisites,
    )

    config = tmp_path / "frozen.yaml"
    shutil.copyfile(Path(__file__).resolve().parents[2] / "configs/frozen_experiment_v1.yaml",
                    config)
    runner = Phase13AblationRunner(config)
    with pytest.raises(Phase13ExecutionBlocked):
        runner.run(plan=None, prerequisites=Phase13Prerequisites(*([True] * 4)))  # type: ignore[arg-type]
