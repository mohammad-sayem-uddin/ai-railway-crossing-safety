"""Mission 5A.1 independent-audit regression tests -- SYNTHETIC-ONLY.

All inputs are hand-built or dummy temp files.  No real media, ground truth, dataset inventory,
cache, checkpoint or replay is read.  Tests exercise PRODUCTION code (``classify_m4``,
``evaluate_run``, ``aggregate_cohort``, ``resolve_event_cohort``, the lead-in screen and the
preservation-manifest tool); nothing here is a test-local reference implementation.

Tests named ``test_open_*`` pin CURRENT behaviour that Mission 5A.1 flagged as needing a
researcher decision.  They document, they do not endorse; a future decision should flip them
deliberately.
"""

from __future__ import annotations

import importlib.util
import math
import os
import pathlib
import sys

import pytest

from railway_detection.evaluation.lead_in_screen import (
    SCREEN_INSUFFICIENT_LEAD_IN,
    SCREEN_NOT_APPLIED,
    derive_min_block_latency_s,
    screen_missed_train_lead_in,
)
from railway_detection.evaluation.metrics import (
    M4_REASON_NO_INTERIOR_STEPS,
    M4_REASON_REPLAY_ENDED_BEFORE_T4,
    M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4,
    M4_REASON_REPLAY_STARTED_LATE,
    M4_STATUS_EVALUABLE,
    M4_STATUS_NOT_EVALUABLE,
    M4_WINDOW,
    EventMetricsCalculator,
    UnqualifiedEventIdError,
    classify_m4,
    resolve_event_cohort,
)
from railway_detection.simulation.runner import SimulationRunResult, SimulationStep

REPO = pathlib.Path(__file__).resolve().parents[2]
TRAIN = "train_events/event_001"


def _step(t, blocked=True, gate=None):
    gate = gate or ("CLOSED" if blocked else "OPEN")
    return SimulationStep(t, "TRAIN_PRESENT", gate, 0.0 if blocked else 90.0, blocked, None)  # type: ignore[arg-type]


def _run(steps, event=TRAIN):
    return SimulationRunResult(
        event_id=event,
        scenario_name="synthetic",
        steps=steps,
        total_duration_s=steps[-1].timestamp_s if steps else 0.0,
        closed_duration_s=0.0,
    )


def _line(flags, gates=None):
    return [_step(float(i), f, (gates[i] if gates else None)) for i, f in enumerate(flags)]


# ---------------------------------------------------------------------------
# 4.3 Strict temporal interval
# ---------------------------------------------------------------------------


class TestStrictInterval:
    def test_start_boundary_excluded_even_with_opening_label(self):
        steps = [_step(1.0, True, "OPENING"), _step(2.0), _step(6.0)]
        assert classify_m4(_run(steps), 5.0).premature is False

    def test_opening_exactly_at_t4_is_excluded_just_before_is_included(self):
        steps = [_step(0.0), _step(1.0), _step(5.0, False), _step(6.0)]
        assert classify_m4(_run(steps), 5.0).premature is False
        # 1 microsecond later is a genuinely later T4 (DEC-C05 grid); 0.1 us would collapse to 5.0
        assert classify_m4(_run(steps), 5.000001).premature is True

    def test_unblocked_step_immediately_after_start_is_a_violation(self):
        steps = [_step(0.0), _step(0.001, False), _step(6.0)]
        assert classify_m4(_run(steps), 5.0).premature is True

    @pytest.mark.parametrize(
        "steps",
        [
            [_step(0.0), _step(1.0), _step(1.0)],  # duplicate
            [_step(0.0), _step(2.0), _step(1.0)],  # reversed
            [_step(0.0), _step(math.nan)],  # NaN
            [_step(-0.5), _step(1.0)],  # negative
            [_step(0.0), _step(math.inf)],  # infinite
        ],
    )
    def test_invalid_timestamps_fail_closed(self, steps):
        with pytest.raises(ValueError, match="strictly increasing"):
            classify_m4(_run(steps), 5.0)

    @pytest.mark.parametrize("t4", [math.nan, math.inf, -0.1, True])
    def test_invalid_t4_fails_closed(self, t4):
        with pytest.raises(ValueError):
            classify_m4(_run(_line([True] * 4)), t4)

    def test_timestamps_are_compared_on_the_microsecond_grid(self):
        # 0.1 + 0.2 == 0.30000000000000004 is snapped to 0.3 (DEC-C05); no tolerance beyond that.
        steps = [_step(0.0), _step(0.1), _step(0.1 + 0.2)]
        c = classify_m4(_run(steps), 0.3)
        assert c.status == M4_STATUS_EVALUABLE and c.replay_complete is True
        assert c.interior_step_count == 1  # only the 0.1 step lies inside (0.0, 0.3)


# ---------------------------------------------------------------------------
# 4.2 Empty protection interval vs truncated replay
# ---------------------------------------------------------------------------


class TestEmptyIntervalVersusTruncation:
    def test_empty_interval_is_distinct_from_truncation(self):
        empty = classify_m4(_run([_step(0.0), _step(5.0)]), 5.0)
        trunc = classify_m4(_run([_step(0.0), _step(2.0)]), 5.0)
        assert (empty.reason, empty.replay_complete) == (M4_REASON_NO_INTERIOR_STEPS, True)
        assert (trunc.reason, trunc.replay_complete) == (M4_REASON_REPLAY_ENDED_BEFORE_T4, False)

    def test_truncation_takes_precedence_over_empty_interval(self):
        c = classify_m4(
            _run([_step(0.0), _step(4.9)]), 5.0
        )  # blocked, nothing inside? 4.9 is inside
        assert c.reason == M4_REASON_REPLAY_ENDED_BEFORE_T4
        c2 = classify_m4(_run([_step(4.9)]), 5.0)  # blocked at 4.9, replay ends at 4.9 < T4
        assert c2.reason == M4_REASON_REPLAY_ENDED_BEFORE_T4

    def test_empty_interval_never_enters_m4_or_m5_denominators(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run([_step(0.0), _step(5.0)]), clearance_time_s=5.0, premature_opening_window=M4_WINDOW
        )
        s = EventMetricsCalculator.aggregate_cohort([ev])
        assert s.premature_opening_evaluable_count == 0 and s.m4_no_violation_count == 0
        assert s.never_protected_evaluable_count == 0 and s.never_protected_count == 0
        assert s.m4_not_evaluable_reasons == {M4_REASON_NO_INTERIOR_STEPS: 1}

    def test_gap_is_exposed_so_unsampled_can_be_told_from_blocked_late(self):
        c = classify_m4(_run([_step(0.0), _step(30.0)]), 5.0)
        assert c.reason == M4_REASON_NO_INTERIOR_STEPS and c.max_step_gap_s == pytest.approx(30.0)

    def test_replay_start_coverage_is_required_for_m5(self):
        """Mission 5B (DEC-C01, C01-B): M5 needs a zero-origin replay that reaches T4.

        Mission 5A.1 left this open (a late replay was classified NEVER_PROTECTED); the researcher
        then required complete zero-origin coverage.  Full coverage is exercised in
        ``test_phase1_metric_closure.py``; this keeps the former counter-examples pinned.
        """
        c = classify_m4(_run([_step(6.0), _step(7.0)]), 5.0)
        assert c.status == M4_STATUS_NOT_EVALUABLE and c.never_protected is None
        assert c.reason == M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4
        late = classify_m4(_run([_step(4.0, False), _step(6.0, False)]), 5.0)
        assert late.status == M4_STATUS_NOT_EVALUABLE  # [0, 4) never observed
        assert late.reason == M4_REASON_REPLAY_STARTED_LATE


# ---------------------------------------------------------------------------
# 5.1 Event cohort identity (incl. cohort / routing-flag contradictions)
# ---------------------------------------------------------------------------


class TestIdentityMatrix:
    @pytest.mark.parametrize(
        "event,cohort,expected",
        [
            ("train_events/event_001", None, "train_events"),
            ("no_train_events/event_001", None, "no_train_events"),
            ("engine_events/event_001", None, "engine_events"),
            ("event_001", "train_events", "train_events"),
            ("train_events/event_001", "train_events", "train_events"),
        ],
    )
    def test_valid_identities(self, event, cohort, expected):
        assert resolve_event_cohort(event, cohort) == expected

    @pytest.mark.parametrize(
        "event,cohort",
        [
            ("event_001", None),  # bare, missing cohort
            ("train_events/event_001", "engine_events"),  # contradiction
            ("engine_events/event_001", "no_train_events"),
            ("event_001", "not_a_cohort"),  # invalid cohort
            ("mystery/event_001", None),  # unknown prefix
            ("train_events/", None),  # unknown (empty) event id
            ("train_events//x", None),
            ("", "train_events"),
            (None, "train_events"),
        ],
    )
    def test_rejected_identities(self, event, cohort):
        with pytest.raises(UnqualifiedEventIdError):
            resolve_event_cohort(event, cohort)

    def test_same_event_number_in_three_cohorts_is_distinct_when_qualified(self):
        evs = [
            EventMetricsCalculator.evaluate_run(
                _run(_line([True] * 4), f"{c}/event_001"),
                clearance_time_s=3.0,
                premature_opening_window=M4_WINDOW,
                has_train_ground_truth=(c == "train_events") or None,
            )
            for c in ("train_events", "no_train_events", "engine_events")
        ]
        assert len({e.event_id for e in evs}) == 3
        EventMetricsCalculator.aggregate_cohort(evs)  # no duplicate-id error

    def test_bare_ids_across_cohorts_collide_and_aggregation_fails_closed(self):
        a = EventMetricsCalculator.evaluate_run(
            _run(_line([True] * 4), "event_001"), clearance_time_s=3.0, cohort="train_events"
        )
        b = EventMetricsCalculator.evaluate_run(
            _run(_line([True] * 4), "event_001"),
            has_train_ground_truth=False,
            cohort="no_train_events",
        )
        with pytest.raises(ValueError, match="unique"):
            EventMetricsCalculator.aggregate_cohort([a, b])

    @pytest.mark.parametrize(
        "event,cohort,has_train,status",
        [
            (TRAIN, "train_events", False, None),  # train event routed as no-train negative
            ("no_train_events/event_001", "no_train_events", True, None),  # no-train as train
            (TRAIN, "train_events", True, "engine"),  # engine status on a train event
        ],
    )
    def test_cohort_versus_routing_flag_contradictions_fail_closed(
        self, event, cohort, has_train, status
    ):
        with pytest.raises(UnqualifiedEventIdError):
            EventMetricsCalculator.evaluate_run(
                _run(_line([True] * 4), event),
                clearance_time_s=3.0,
                has_train_ground_truth=has_train,
                cohort=cohort,
                ground_truth_status=status,
                premature_opening_window=M4_WINDOW,
            )

    def test_unverified_ground_truth_none_flag_is_still_allowed_for_train(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run(_line([True] * 4)), has_train_ground_truth=None, premature_opening_window=M4_WINDOW
        )
        assert ev.evaluable is False and ev.m4_status is None

    def test_official_callers_supply_cohort_from_ground_truth_and_check_replay_cohort(self):
        clock = (REPO / "src/railway_detection/evaluation/clock_aware.py").read_text("utf-8")
        runner = (REPO / "src/railway_detection/evaluation/evaluation_runner.py").read_text("utf-8")
        assert "cohort=truth.cohort" in clock and "cohort=truth.cohort" in runner
        assert (
            "MANIFEST_COHORT_MISMATCH" in runner
        )  # replay cohort must equal the ground-truth cohort


# ---------------------------------------------------------------------------
# 5.2 Engine isolation
# ---------------------------------------------------------------------------


class TestEngineIsolation:
    def _engine(self, **kw):
        return EventMetricsCalculator.evaluate_run(
            _run(_line([True, False, True, True]), "engine_events/event_001"),
            entry_time_s=0.5,
            clearance_time_s=3.0,
            premature_opening_window=M4_WINDOW,
            **kw,
        )

    def test_engine_takes_the_engine_branch_with_no_train_metrics(self):
        e = self._engine()
        assert e.notes == "engine_event_excluded" and e.evaluable is False
        assert e.has_train_ground_truth is False
        assert e.premature_opening is None and e.never_protected is None
        assert e.m4_status is None and e.missed_train is False  # engine branch constant

    def test_engine_never_runs_the_lead_in_screen(self):
        e = self._engine(
            lead_in_min_block_latency_s=3.6,
            lead_in_latency_source="unit-test",
            first_visible_left_censored=True,
        )
        assert e.missed_train_screen == SCREEN_NOT_APPLIED and e.lead_in_available_s is None

    def test_engine_does_not_enter_pooled_denominators(self):
        train = EventMetricsCalculator.evaluate_run(
            _run(_line([True] * 4), TRAIN), clearance_time_s=3.0, premature_opening_window=M4_WINDOW
        )
        s = EventMetricsCalculator.aggregate_cohort([self._engine(), train])
        assert s.engine_events == 1 and s.no_train_events == 0 and s.eligible_events == 1
        assert s.premature_opening_evaluable_count == 1 and s.never_protected_evaluable_count == 1
        assert s.missed_train_evaluable_count <= 1

    def test_engine_evaluable_true_cannot_re_enter_after_the_fact(self):
        e = self._engine(evaluable=True)  # caller asks for evaluable; engine branch ignores it
        assert e.evaluable is False

    def test_bare_engine_id_cannot_bypass_cohort_validation(self):
        with pytest.raises(UnqualifiedEventIdError):
            EventMetricsCalculator.evaluate_run(
                _run(_line([True] * 4), "event_001"), clearance_time_s=3.0
            )
        e = EventMetricsCalculator.evaluate_run(
            _run(_line([True] * 4), "event_001"), cohort="engine_events"
        )
        assert e.notes == "engine_event_excluded"


# ---------------------------------------------------------------------------
# 6 Lead-in screen: default off, unwired, provenance, derivation
# ---------------------------------------------------------------------------


class TestLeadInScreenAudit:
    def test_screen_is_off_by_default_and_unwired_in_src(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run(_line([False] * 8)), entry_time_s=1.0, clearance_time_s=7.0
        )
        assert ev.missed_train_screen == SCREEN_NOT_APPLIED and ev.missed_train is True
        users = []
        for path in (REPO / "src").rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "lead_in_min_block_latency_s" in text or "screen_missed_train_lead_in" in text:
                users.append(path.name)
        # Mission 5B: clock_aware.py only forwards an optional, default-off argument.  The official
        # runner and every other caller must still not reference the screen.
        assert sorted(users) == ["clock_aware.py", "lead_in_screen.py", "metrics.py"]

    def test_insufficient_lead_in_is_not_evaluable_not_a_failure(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run(_line([False] * 12)),
            entry_time_s=3.0,
            clearance_time_s=10.0,
            lead_in_min_block_latency_s=3.6,
            lead_in_latency_source="unit-test",
            first_visible_left_censored=True,
        )
        assert ev.missed_train is None and ev.missed_train_screen == SCREEN_INSUFFICIENT_LEAD_IN

    def test_enabling_without_t0_information_fails_closed_to_unverifiable(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run(_line([False] * 12)),
            entry_time_s=9.0,
            clearance_time_s=10.0,
            lead_in_min_block_latency_s=3.6,
            lead_in_latency_source="unit-test",
        )
        assert ev.missed_train is None and ev.missed_train_screen == "lead_in_unverifiable"

    def test_derivation_is_deterministic_and_tick_dependent(self):
        values = {derive_min_block_latency_s(tick_s=0.2) for _ in range(3)}
        assert len(values) == 1
        assert derive_min_block_latency_s(tick_s=0.2) == derive_min_block_latency_s(tick_s=0.1)
        # not a universal constant: quantized by the tick (documented, not endorsed as a threshold)
        assert derive_min_block_latency_s(tick_s=0.5) != derive_min_block_latency_s(tick_s=0.2)

    def test_derivation_agrees_with_the_frozen_configuration_runner(self):
        cfg_path = REPO / "configs" / "frozen_experiment_v1.yaml"
        if not cfg_path.exists():
            pytest.skip("frozen configuration not present")
        from railway_detection.experiments.frozen_config import load_frozen_config  # YAML only
        from railway_detection.simulation.runner import EventSimulationRunner

        cfg = load_frozen_config(cfg_path)
        tick = cfg.timing.tick_s
        assert derive_min_block_latency_s(tick_s=tick) == derive_min_block_latency_s(
            tick_s=tick, runner=EventSimulationRunner(config=cfg)
        )

    def test_screen_differs_from_literal_design_m3_in_two_documented_ways(self):
        # (a) observable T0 but T1 - T0 < latency: design M3 would call it evaluable
        a = screen_missed_train_lead_in(
            10.0,
            first_visible_time_s=8.0,
            first_visible_left_censored=False,
            min_block_latency_s=3.6,
            min_block_latency_source="unit-test",
        )
        assert a.evaluable is False
        # (c) T0 unknown/uncertain but T1 >= latency: design M3 would call it evaluable
        c = screen_missed_train_lead_in(
            9.0,
            first_visible_time_s=None,
            first_visible_left_censored=False,
            min_block_latency_s=3.6,
            min_block_latency_source="unit-test",
        )
        assert c.evaluable is False and c.outcome == "lead_in_unverifiable"


# ---------------------------------------------------------------------------
# 7 Preservation manifest: dummy media-like files must never be opened
# ---------------------------------------------------------------------------


def _tool():
    spec = importlib.util.spec_from_file_location(
        "mission5a_manifest_tool_audit",
        REPO / "scripts" / "mission5a_build_preservation_manifest.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["mission5a_manifest_tool_audit"] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


@pytest.fixture
def open_spy(monkeypatch):
    """Record the name of every file opened through pathlib or builtins."""
    opened: list[str] = []
    real_path_open = pathlib.Path.open
    real_os_open = os.open

    def spy_path_open(self, *a, **k):
        opened.append(self.name)
        return real_path_open(self, *a, **k)

    def spy_os_open(path, *a, **k):
        opened.append(os.path.basename(os.fspath(path)))
        return real_os_open(path, *a, **k)

    monkeypatch.setattr(pathlib.Path, "open", spy_path_open)
    monkeypatch.setattr(os, "open", spy_os_open)
    return opened


class TestManifestSafety:
    def _tree(self, tmp_path):
        root = tmp_path / "repo"
        (root / "src").mkdir(parents=True)
        (root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        (root / "src" / "clip.mov").write_bytes(b"DUMMY")
        (root / "src" / "audio.wav").write_bytes(b"DUMMY")
        (root / "src" / "blob.bin").write_bytes(b"\x00\x01")
        (root / "src" / "unknown_format").write_bytes(b"\x00\x01")
        (root / "data" / "raw").mkdir(parents=True)
        (root / "data" / "raw" / "v.mp4").write_bytes(b"DUMMY")
        (root / "data" / "raw" / "meta.json").write_text("{}", encoding="utf-8")
        outside = tmp_path / "outside.mp4"
        outside.write_bytes(b"DUMMY-OUTSIDE")
        os.symlink(outside, root / "src" / "link.txt")
        os.symlink(tmp_path, root / "src" / "dirlink")
        (root / "src" / "broken.txt").symlink_to(tmp_path / "nope")
        return root, outside

    def test_build_opens_only_allowlisted_regular_files(self, tmp_path, open_spy):
        root, _ = self._tree(tmp_path)
        open_spy.clear()  # ignore the fixture's own writes
        m = _tool().build_manifest(root)
        assert {e["path"] for e in m["entries"]} == {"src/a.py"}
        assert open_spy == ["a.py"]
        assert m["excluded"]["symlink_not_followed"]["file_count"] == 2
        assert "media_binary_or_model_not_opened" in m["excluded"]
        assert "unrecognized_extension" in m["excluded"]
        # Mission 5B (DEC-A02): output trees are pruned, not walked, unless counting is requested.
        assert "generated_output_tree" not in m["excluded"]
        assert m["pruned_output_trees"] == ["data/raw"]

    def test_verify_refuses_crafted_entries_without_opening_them(self, tmp_path, open_spy):
        root, outside = self._tree(tmp_path)
        open_spy.clear()  # ignore the fixture's own writes
        crafted = {
            "entries": [
                {"path": "src/clip.mov", "sha256": "0" * 64},
                {"path": "src/audio.wav", "sha256": "0" * 64},
                {"path": "src/blob.bin", "sha256": "0" * 64},
                {"path": "src/unknown_format", "sha256": "0" * 64},
                {"path": "data/raw/v.mp4", "sha256": "0" * 64},
                {"path": "data/raw/meta.json", "sha256": "0" * 64},
                {"path": "src/link.txt", "sha256": "0" * 64},
                {"path": "src/dirlink/outside.mp4", "sha256": "0" * 64},
                {"path": "../outside.mp4", "sha256": "0" * 64},
                {"path": str(outside), "sha256": "0" * 64},
                {"path": "src\\a.py", "sha256": "0" * 64},
                {"path": None, "sha256": "0" * 64},
            ]
        }
        result = _tool().verify_manifest(root, crafted)
        assert open_spy == []  # nothing was opened
        assert len(result["refused"]) == 12 and result["ok"] == 0 and result["clean"] is False

    def test_verify_refuses_a_file_replaced_by_a_symlink_after_build(self, tmp_path, open_spy):
        root, outside = self._tree(tmp_path)
        open_spy.clear()  # ignore the fixture's own writes
        tool = _tool()
        manifest = tool.build_manifest(root)
        (root / "src" / "a.py").unlink()
        os.symlink(outside, root / "src" / "a.py")
        open_spy.clear()
        result = tool.verify_manifest(root, manifest)
        assert open_spy == [] and result["refused"][0]["reason"] == "symlink_not_followed"

    def test_verify_still_works_for_honest_manifests(self, tmp_path):
        root, _ = self._tree(tmp_path)
        tool = _tool()
        manifest = tool.build_manifest(root)
        assert tool.verify_manifest(root, manifest)["clean"] is True
        (root / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
        assert tool.verify_manifest(root, manifest)["changed"] == ["src/a.py"]

    def test_frozen_checkpoint_paths_are_validated_before_opening(self, tmp_path, open_spy):
        root, outside = self._tree(tmp_path)
        open_spy.clear()  # ignore the fixture's own writes
        (root / "weights").mkdir()
        (root / "weights" / "best.pt").write_bytes(b"DUMMY")
        m = _tool().build_manifest(
            root,
            {
                "weights/best.pt": "0" * 64,  # legitimate shape
                "../outside.mp4": "0" * 64,  # traversal
                "src/clip.mov": "0" * 64,  # wrong suffix
            },
        )
        by_path = {c["path"]: c for c in m["frozen_checkpoints"]}
        assert by_path["../outside.mp4"]["refused"] == "absolute_or_traversal_path"
        assert by_path["src/clip.mov"]["refused"] == "unexpected_suffix"
        assert "best.pt" in open_spy and "clip.mov" not in open_spy

    def test_manifest_does_not_include_itself_and_refuses_overwrite(self, tmp_path):
        root, _ = self._tree(tmp_path)
        tool = _tool()
        out = root / "docs"
        out.mkdir()
        target = out / "M.json"
        assert tool.main(["build", "--root", str(root), "--out", str(target)]) == 0
        assert "docs/M.json" not in {
            e["path"] for e in __import__("json").loads(target.read_text())["entries"]
        }
        assert tool.main(["build", "--root", str(root), "--out", str(target)]) == 2

    def test_verify_cannot_detect_newly_added_files_documented_limit(self, tmp_path):
        root, _ = self._tree(tmp_path)
        tool = _tool()
        manifest = tool.build_manifest(root)
        (root / "src" / "new.py").write_text("y = 1\n", encoding="utf-8")
        assert tool.verify_manifest(root, manifest)["clean"] is True  # additions are not detected


# ---------------------------------------------------------------------------
# Regression introduced by Mission 5A and corrected in 5A.1: unannotated events
# ---------------------------------------------------------------------------


class TestUnannotatedEventsDoNotAbortAndDoNotLeak:
    """A bare-id event with unverified ground truth is a non-evaluable record, not a crash."""

    def test_runner_style_missing_ground_truth_is_recorded_not_raised(self):
        from railway_detection.data.contracts import LayerBEvent
        from railway_detection.experiments.runner import ExperimentRunner

        gt = ExperimentRunner._extract_event_ground_truth(
            LayerBEvent(event_id="event_007", metadata_status="unannotated")
        )
        assert gt["cohort"] is None and gt["has_train_ground_truth"] is None
        ev = EventMetricsCalculator.evaluate_run(
            sim_result=_run(_line([True] * 5), "event_007"),
            entry_time_s=gt["entry_time_s"],
            clearance_time_s=gt["clearance_time_s"],
            has_train_ground_truth=gt["has_train_ground_truth"],
            exclusion_reasons=gt["exclusion_reasons"],
            premature_opening_window=M4_WINDOW,
            evaluable=gt["evaluable"],
            ground_truth_status=gt["ground_truth_status"],
            cohort=gt["cohort"],
        )
        assert ev.evaluable is False and ev.notes == "ground_truth_missing"
        assert ev.premature_opening is None and ev.never_protected is None

    def test_such_records_never_enter_any_denominator(self):
        ev = EventMetricsCalculator.evaluate_run(
            _run(_line([True] * 5), "event_007"),
            has_train_ground_truth=None,
            ground_truth_status="missing",
            premature_opening_window=M4_WINDOW,
        )
        s = EventMetricsCalculator.aggregate_cohort([ev])
        assert s.eligible_events == 0 and s.no_train_events == 0 and s.engine_events == 0
        assert s.premature_opening_evaluable_count == 0 and s.never_protected_evaluable_count == 0

    @pytest.mark.parametrize("status", ["censored", "uncertain", "unknown", "unobservable"])
    def test_other_unverified_statuses_behave_the_same(self, status):
        ev = EventMetricsCalculator.evaluate_run(
            _run(_line([True] * 5), "event_007"),
            has_train_ground_truth=True,
            ground_truth_status=status,
            premature_opening_window=M4_WINDOW,
        )
        assert ev.evaluable is False and ev.notes == f"ground_truth_{status}"

    @pytest.mark.parametrize(
        "has_train,status",
        [
            (True, None),  # could be evaluated as a train event
            (False, None),  # could be evaluated as a no-train negative control
            (True, "confirmed_train"),
            (False, "confirmed_no_train"),
        ],
    )
    def test_anything_evaluable_with_an_unresolved_cohort_still_fails_closed(
        self, has_train, status
    ):
        with pytest.raises(UnqualifiedEventIdError):
            EventMetricsCalculator.evaluate_run(
                _run(_line([True] * 5), "event_007"),
                clearance_time_s=4.0,
                has_train_ground_truth=has_train,
                ground_truth_status=status,
                premature_opening_window=M4_WINDOW,
            )

    def test_malformed_or_contradictory_identity_still_raises_even_when_unverified(self):
        for event, cohort in (("train_events/event_001", "engine_events"), ("mystery/e", None)):
            with pytest.raises(UnqualifiedEventIdError):
                EventMetricsCalculator.evaluate_run(
                    _run(_line([True] * 5), event),
                    has_train_ground_truth=None,
                    ground_truth_status="missing",
                    cohort=cohort,
                )
