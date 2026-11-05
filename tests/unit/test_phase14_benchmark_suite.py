"""Phase 14 reproducible benchmark reports: metadata, fingerprints, claims, equivalence."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from railway_detection.cli.main import main as cli_main
from railway_detection.optimization.benchmark import BenchmarkProtocol, BenchmarkProtocolError
from railway_detection.optimization.benchmark_suite import (
    LIMITATIONS,
    InputDescription,
    artifact_fingerprints,
    assess_acceptance,
    check_candidate_equivalence,
    collect_host_environment,
    run_staged_benchmark,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HOST = {
    "system": "Linux",
    "machine": "aarch64",
    "processor": "x",
    "cpu_count": 4,
    "cpu_model": "Synthetic CPU",
}
GOOD_FP = {"verified": True, "frozen_config": {}, "decision_policy": {}, "checkpoints": {}}
SYNTHETIC = InputDescription("synthetic", "unit-test inputs")
REAL = InputDescription("real", "recorded footage", {"manifest_sha256": "a" * 64})


class StepClock:
    """Advances ``step_s`` on every call: durations become exact multiples."""

    def __init__(self, step_s=0.001):
        self.now, self.step = 0.0, step_s

    def __call__(self):
        self.now += self.step
        return self.now


def _stages():
    return [("pre", lambda x: x + 1), ("infer", lambda x: x * 2)]


def _run(
    protocol=None,
    inputs=(1, 2, 3),
    description=SYNTHETIC,
    fp=GOOD_FP,
    host=HOST,
    clock=None,
    stages=None,
):
    protocol = protocol or BenchmarkProtocol(
        warmup_iterations=1, measured_iterations=2, repetitions=2
    )
    return run_staged_benchmark(
        "unit",
        _stages() if stages is None else stages,
        list(inputs),
        protocol,
        description,
        root=REPO_ROOT,
        clock=clock or StepClock(),
        host=host,
        fingerprints=fp,
    )


# ------------------------------------------------------------------ arithmetic & metadata


def test_stage_latency_throughput_and_counts_are_exact_with_a_stepped_clock():
    report = _run()
    # per item: item_start, 2 x (stage start, stage end), item_end = 6 clock reads of 1 ms
    assert report["stage_latency_ms"]["pre"]["mean_ms"] == pytest.approx(1.0)
    assert report["stage_latency_ms"]["infer"]["mean_ms"] == pytest.approx(1.0)
    assert report["stage_latency_ms"]["item_total"]["mean_ms"] == pytest.approx(5.0)
    assert report["stage_latency_ms"]["item_total"]["sample_count"] == 2 * 2 * 3
    assert report["item_count"] == 12
    assert report["throughput_items_per_s"] == pytest.approx(
        12 / (sum(report["repetition_wall_ms"]) / 1000.0)
    )
    assert report["protocol"]["warmup_iterations"] == 1  # warm-up ran but is excluded
    assert report["limitations"] == list(LIMITATIONS)


def test_reports_are_deterministic_given_injected_environment_and_clock(monkeypatch):
    from types import SimpleNamespace

    from railway_detection.optimization import benchmark_suite

    # The entire report includes lifetime process peak RSS, a third measured input.
    # Fix it alongside the injected clock/host; never assume allocator state is stable.
    monkeypatch.setattr(
        benchmark_suite.resource, "getrusage", lambda _: SimpleNamespace(ru_maxrss=1024)
    )
    first, second = _run(clock=StepClock()), _run(clock=StepClock())
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_output_fingerprint_depends_on_outputs_and_their_order():
    base = _run()["output_fingerprint_sha256"]
    assert _run()["output_fingerprint_sha256"] == base
    assert _run(inputs=(1, 2, 4))["output_fingerprint_sha256"] != base
    assert _run(inputs=(3, 2, 1))["output_fingerprint_sha256"] != base


def test_a_nondeterministic_workload_cannot_be_fingerprinted():
    counter = {"n": 0}

    def drifting(x):
        counter["n"] += 1
        return counter["n"]

    with pytest.raises(BenchmarkProtocolError, match="differs between repetitions"):
        _run(stages=[("drift", drifting)])


def test_unserializable_outputs_need_an_explicit_serializer():
    with pytest.raises(BenchmarkProtocolError, match="no canonical serialization"):
        _run(stages=[("obj", lambda x: object())])


@pytest.mark.parametrize("bad_clock", [lambda: float("nan"), lambda: float("inf")])
def test_non_finite_timing_aborts_the_report(bad_clock):
    with pytest.raises(BenchmarkProtocolError, match="finite"):
        _run(clock=bad_clock)


def test_a_decreasing_clock_aborts_the_report():
    reads = {"n": 0}

    def clock():
        reads["n"] += 1
        # increases by 1 ms per read, except one read late in the measured region goes backwards
        return reads["n"] * 0.001 - (0.01 if reads["n"] == 40 else 0.0)

    with pytest.raises(BenchmarkProtocolError, match="non-negative"):
        _run(clock=clock)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"stages": []},
        {"inputs": ()},
        {"stages": [("a", len), ("a", len)]},
        {"stages": [("a", "not callable")]},
    ],
)
def test_malformed_stage_or_input_specs_are_refused(kwargs):
    with pytest.raises(BenchmarkProtocolError):
        _run(**kwargs)


# --------------------------------------------------------------- classification & claims


def test_synthetic_inputs_never_become_empirical_railway_performance():
    report = _run(description=SYNTHETIC)
    assert report["inputs"]["classification"] == "synthetic"
    assert report["inputs"]["empirical_railway_performance"] is False
    assert report["is_safety_evidence"] is False


def test_real_inputs_require_provenance_and_unknown_classes_are_refused():
    with pytest.raises(BenchmarkProtocolError, match="provenance"):
        InputDescription("real", "footage")
    with pytest.raises(BenchmarkProtocolError, match="digest"):
        InputDescription("real", "footage", {"source": "camera"})
    with pytest.raises(BenchmarkProtocolError):
        InputDescription("maybe", "x")
    with pytest.raises(BenchmarkProtocolError):
        InputDescription("synthetic", "  ")


CRITERION = {"statistic": "p99_ms", "limit_ms": 1000.0, "documented_in": "docs/X.md"}


def _claim_protocol(**kw):
    base = dict(
        warmup_iterations=0,
        measured_iterations=34,
        repetitions=1,
        target_platform={"system": "Linux", "machine": "aarch64"},
        acceptance_criterion=CRITERION,
    )
    base.update(kw)
    return BenchmarkProtocol(**base)


def test_a_claim_needs_real_inputs_target_hardware_documented_criterion_and_a_pass():
    ok = _run(_claim_protocol(), description=REAL)
    assert ok["is_target_hardware_evidence"] and ok["real_time_claim_permitted"]
    assert ok["acceptance"]["status"] == "observed_within_criterion"

    # synthetic inputs: measured and compared, but no claim
    synthetic = _run(_claim_protocol(), description=SYNTHETIC)
    assert synthetic["acceptance"]["status"] == "observed_within_criterion"
    assert not synthetic["real_time_claim_permitted"]
    assert "inputs are synthetic" in synthetic["acceptance"]["claim_blockers"]

    # wrong host
    wrong = _run(_claim_protocol(target_platform={"machine": "armv7l"}), description=REAL)
    assert not wrong["is_target_hardware_evidence"] and not wrong["real_time_claim_permitted"]
    assert wrong["target_mismatches"]

    # no criterion documented => measurements only, no compliance statement
    nocrit = _run(_claim_protocol(acceptance_criterion=None), description=REAL)
    assert nocrit["acceptance"]["status"] == "not_assessed_no_documented_criterion"
    assert not nocrit["real_time_claim_permitted"]

    # criterion exceeded
    tight = _run(
        _claim_protocol(acceptance_criterion={**CRITERION, "limit_ms": 0.001}), description=REAL
    )
    assert tight["acceptance"]["status"] == "observed_exceeds_criterion"
    assert not tight["real_time_claim_permitted"]

    # too few samples for target evidence
    few = _run(_claim_protocol(measured_iterations=2), description=REAL)
    assert not few["is_target_hardware_evidence"] and not few["real_time_claim_permitted"]


def test_stale_checkpoint_fingerprints_void_every_claim():
    stale = {"verified": False, "checkpoints": {"vision": {"matches_frozen_config": False}}}
    report = _run(_claim_protocol(), description=REAL, fp=stale)
    assert report["fingerprints_verified"] is False
    assert report["is_target_hardware_evidence"] is False
    assert report["real_time_claim_permitted"] is False


@pytest.mark.parametrize(
    "criterion",
    [
        {"statistic": "p42_ms", "limit_ms": 1.0, "documented_in": "d"},
        {"statistic": "p99_ms", "limit_ms": 0, "documented_in": "d"},
        {"statistic": "p99_ms", "limit_ms": float("nan"), "documented_in": "d"},
        {"statistic": "p99_ms", "limit_ms": 1.0, "documented_in": " "},
        {"statistic": "p99_ms", "limit_ms": 1.0},
    ],
)
def test_acceptance_criteria_must_be_complete_and_cite_a_document(criterion):
    with pytest.raises(BenchmarkProtocolError):
        BenchmarkProtocol(acceptance_criterion=criterion)


def test_assess_acceptance_is_descriptive_without_a_criterion():
    out = assess_acceptance({"p99_ms": 1.0}, BenchmarkProtocol(), target_evidence=True, inputs=REAL)
    assert out["claim_permitted"] is False
    assert "no documented acceptance criterion" in out["claim_blockers"]


# ----------------------------------------------------------------------- fingerprints


def test_real_artifacts_verify_and_both_hash_conventions_are_recorded():
    fp = artifact_fingerprints(REPO_ROOT)
    assert fp["verified"] is True and fp["checkpoints"]["prohibited_audio_v2_used"] is False
    # Policy-hash investigation (2026-10-16): the Phase 5 report's 051c908d... is the
    # CANONICAL-content hash of the unchanged file whose RAW-byte hash is c87c1432...
    assert fp["decision_policy"]["canonical_sha256"] == (
        "051c908d4db23687db33cbc8349945b241a0735b362413be876d7017a5eacc9d"
    )
    assert fp["decision_policy"]["raw_sha256"] == (
        "c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575"
    )
    assert fp["frozen_config"]["canonical_sha256"] == (
        "999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e"
    )
    assert fp["frozen_config"]["raw_sha256"] == (
        "b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a"
    )


def _copy_config_tree(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "configs").mkdir(parents=True)
    for name in ("frozen_experiment_v1.yaml", "decision_policy_v1.yaml"):
        shutil.copyfile(REPO_ROOT / "configs" / name, root / "configs" / name)
    return root


def test_missing_or_altered_checkpoints_fail_verification(tmp_path):
    root = _copy_config_tree(tmp_path)
    missing = artifact_fingerprints(root)
    assert missing["verified"] is False
    assert missing["checkpoints"]["vision"]["actual_sha256"] is None

    for relative in (
        "experiments/vision/39f402dfe460/checkpoints/weights/best.pt",
        "experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"not the pinned weights")
    altered = artifact_fingerprints(root)
    assert altered["verified"] is False
    assert not altered["checkpoints"]["vision"]["matches_frozen_config"]
    assert (
        altered["checkpoints"]["vision"]["actual_sha256"]
        != (altered["checkpoints"]["vision"]["expected_sha256"])
    )


def test_host_environment_records_revision_hosts_and_dependencies():
    env = collect_host_environment(REPO_ROOT)
    for key in (
        "system",
        "machine",
        "cpu_model",
        "ram_bytes",
        "accelerators",
        "packages",
        "code_revision",
        "worktree_dirty",
        "python_version",
    ):
        assert key in env
    assert len(env["code_revision"]) == 40
    assert set(env["packages"]) >= {"torch", "numpy", "PyYAML"}


# ------------------------------------------------------------------------ equivalence


def test_equivalence_needs_identical_outputs_and_the_same_inputs():
    inputs = [1, 2, 3]
    ref = lambda x: {"y": x * 2}  # noqa: E731
    good = lambda x: {"y": x + x}  # noqa: E731
    report = check_candidate_equivalence(ref, good, inputs)
    assert report["equivalent"] and report["failures"] == []
    assert (
        report["input_set_sha256"]
        == check_candidate_equivalence(ref, good, inputs)["input_set_sha256"]
    )
    assert (
        report["input_set_sha256"]
        != check_candidate_equivalence(ref, good, [1, 2, 4])["input_set_sha256"]
    )


def test_mismatched_outputs_properties_errors_and_self_comparison_are_all_refused():
    inputs = [1, 2, 3]
    ref = lambda x: {"y": x * 2}  # noqa: E731
    drift = lambda x: {"y": x * 2 + (1 if x == 2 else 0)}  # noqa: E731
    bad = check_candidate_equivalence(ref, drift, inputs)
    assert not bad["equivalent"] and bad["failures"][0]["index"] == 1

    def boom(x):
        raise RuntimeError("optimized path crashed")

    crashed = check_candidate_equivalence(ref, boom, inputs)
    assert not crashed["equivalent"] and "RuntimeError" in crashed["failures"][0]["error"]

    # outputs equal, but a required property is violated
    prop = check_candidate_equivalence(
        ref,
        lambda x: {"y": x * 2},
        inputs,
        property_checks={"y_is_even": lambda a, b: b["y"] % 2 == 1},
    )
    assert not prop["equivalent"] and prop["failures"][0]["property"] == "y_is_even"

    same = check_candidate_equivalence(ref, ref, inputs)
    assert same["candidate_is_reference"] and not same["equivalent"]
    with pytest.raises(BenchmarkProtocolError):
        check_candidate_equivalence(ref, drift, [])


# -------------------------------------------------------------------------------- CLI


def test_benchmark_command_writes_a_complete_unclaiming_report(tmp_path):
    out = tmp_path / "bench.json"
    code = cli_main(
        [
            "benchmark",
            "run",
            "--output",
            str(out),
            "--warmup",
            "1",
            "--iterations",
            "2",
            "--repetitions",
            "2",
        ]
    )
    assert code == 0
    report = json.loads(out.read_text())
    assert report["schema_version"] == "phase14-benchmark-report/2"
    assert report["inputs"]["classification"] == "synthetic"
    assert report["fingerprints_verified"] is True
    assert report["real_time_claim_permitted"] is False
    assert report["is_target_hardware_evidence"] is False
    assert set(report["stage_latency_ms"]) == {"frame_assembly", "decision_replay", "item_total"}
    assert report["derived_per_frame"]["throughput_frames_per_s"] > 0
    assert report["environment"]["code_revision"]
    assert report["memory"]["process_peak_rss_bytes"] > 0
    assert report["limitations"]
    again = tmp_path / "bench2.json"
    cli_main(
        [
            "benchmark",
            "run",
            "--output",
            str(again),
            "--warmup",
            "1",
            "--iterations",
            "2",
            "--repetitions",
            "2",
        ]
    )
    assert (
        json.loads(again.read_text())["output_fingerprint_sha256"]
        == (report["output_fingerprint_sha256"])
    )


@pytest.mark.parametrize("tree", ["docs", "data", "configs", "results", "src", "experiments"])
def test_benchmark_command_refuses_to_write_into_repository_trees(tmp_path, tree):
    target = REPO_ROOT / tree / "bench_should_not_exist.json"
    code = cli_main(["benchmark", "run", "--output", str(target)])
    assert code != 0 and not target.exists()


def test_target_claim_through_the_command_is_not_granted_to_a_dev_machine(tmp_path):
    out = tmp_path / "claim.json"
    cli_main(
        [
            "benchmark",
            "run",
            "--output",
            str(out),
            "--iterations",
            "2",
            "--repetitions",
            "1",
            "--target-machine",
            "armv7l",
            "--acceptance-statistic",
            "p99_ms",
            "--acceptance-limit-ms",
            "200",
            "--acceptance-doc",
            "docs/NONE.md",
        ]
    )
    report = json.loads(out.read_text())
    assert report["host_matches_declared_target"] is False
    assert report["real_time_claim_permitted"] is False
    assert report["acceptance"]["claim_permitted"] is False
