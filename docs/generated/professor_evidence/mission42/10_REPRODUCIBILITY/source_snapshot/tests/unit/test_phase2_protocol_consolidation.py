"""Phase 2 (Mission 5B) -- protocol / design / paper consolidation and snapshot-helper tests.

Document tests read the GENERATED proposals under ``docs/generated/phase2/`` and check what they
actually say (with historical blocks stripped, because historical text is non-normative).  Where a
document states a code behaviour, the test also exercises the production function, so a document
and the code cannot silently disagree.  Snapshot-helper tests run on synthetic temporary
directories only.  No media, no real events, no inference.

The working-tree baseline test (``TestWorkingTreeUntouched``) is a Phase 2 guard.  When the
researcher adopts wording at Gate 2 the protocol hashes legitimately change; that test must then be
updated or retired by the researcher.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import os
import pathlib
import re
import subprocess
from dataclasses import fields

import pytest

from railway_detection.evaluation import metrics
from railway_detection.evaluation.clock_aware import evaluate_event_replay
from railway_detection.evaluation.lead_in_screen import (
    SCREEN_UNVERIFIABLE,
    LeadInScreenResult,
    screen_missed_train_lead_in,
)
from railway_detection.evaluation.metrics import (
    M4_REASON_NO_INTERIOR_STEPS,
    M4_REASON_REPLAY_ENDED_BEFORE_T4,
    M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4,
    M4_REASON_REPLAY_STARTED_LATE,
    M4_STATUS_EVALUABLE,
    M4_STATUS_NEVER_PROTECTED,
    M4_STATUS_NOT_EVALUABLE,
    M4_WINDOW,
    CohortEvaluationSummary,
    EventMetricsCalculator,
    SingleEventEvaluation,
    classify_m4,
)
from railway_detection.simulation.runner import SimulationRunResult, SimulationStep

REPO = pathlib.Path(__file__).resolve().parents[2]
P2 = REPO / "docs" / "generated" / "phase2"
V9 = P2 / "FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.1_PROPOSED.md"
V7 = P2 / "FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md"
DESIGN = P2 / "EXPERIMENT_DESIGN_CONSOLIDATED.md"
PAPER = P2 / "PAPER_REVISION_CONSOLIDATED.md"
HEAD9 = "# PROPOSED — Final Real-World Experiment Protocol (v9.1.1-PROPOSED)"
HEAD7 = "# PROPOSED — Final Ground Truth Annotation Protocol (v7.1.1-PROPOSED)"
BANNER = "PROPOSED — NOT APPROVED — NOT HASH-BOUND"
NEGATION = re.compile(
    r"\b(no|not|never|without|cannot|neither|nor|prohibited|removed|rejected)\b", re.I
)


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def historical_blocks(text: str) -> list[str]:
    return re.findall(r"<!--HISTORICAL-->(.*?)<!--/HISTORICAL-->", text, flags=re.S)


def active(text: str) -> str:
    """Normative text: everything outside historical blocks (emphasis markers removed)."""
    return re.sub(r"<!--HISTORICAL-->.*?<!--/HISTORICAL-->", "", text, flags=re.S).replace("*", "")


def without_not_claims(text: str) -> str:
    return re.sub(r"<!--NOT-CLAIMS-->.*?<!--/NOT-CLAIMS-->", "", text, flags=re.S)


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "phase2_snapshot_tool", REPO / "scripts" / "prepare_researcher_snapshot.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def step(t, blocked=True, gate=None):
    gate = gate or ("CLOSED" if blocked else "OPEN")
    return SimulationStep(t, "TRAIN_PRESENT", gate, 0.0 if blocked else 90.0, blocked, None)  # type: ignore[arg-type]


def run(steps):
    return SimulationRunResult(
        event_id="train_events/event_001",
        scenario_name="synthetic",
        steps=steps,
        total_duration_s=steps[-1].timestamp_s,
        closed_duration_s=0.0,
    )


# ---------------------------------------------------------------------------
# 1-3  Proposal labelling
# ---------------------------------------------------------------------------


class TestProposalLabelling:
    def test_v9_first_heading_is_the_proposed_heading(self):
        first = next(line for line in read(V9).splitlines() if line.strip())
        assert first == HEAD9

    def test_v7_first_heading_is_the_proposed_heading(self):
        first = next(line for line in read(V7).splitlines() if line.strip())
        assert first == HEAD7

    @pytest.mark.parametrize("path", [V9, V7, DESIGN, PAPER])
    def test_every_document_states_not_approved_and_not_hash_bound(self, path):
        header = "\n".join(read(path).splitlines()[:40])
        assert "NOT APPROVED" in header
        if path in (V9, V7, DESIGN):
            assert BANNER in header
            assert "NOT HASH-BOUND" in header

    @pytest.mark.parametrize(("path", "heading"), [(V9, HEAD9), (V7, HEAD7)])
    def test_the_helper_accepts_the_real_labels_and_no_header_claims_approval(self, path, heading):
        tool = load_tool()
        tool.check_proposal_label(read(path), heading, path.name)  # raises if mislabeled
        header = "\n".join(read(path).splitlines()[:40])
        claim = header.replace("NOT APPROVED", "").replace("NOT HASH-BOUND", "")
        assert not re.search(r"\bAPPROVED\b|HASH-BOUND", claim)

    @pytest.mark.parametrize("path", [V9, V7])
    def test_historical_blocks_are_balanced_and_marked_non_normative(self, path):
        text = read(path)
        assert text.count("<!--HISTORICAL-->") == text.count("<!--/HISTORICAL-->") > 0
        assert "<!--HISTORICAL-->" not in "".join(historical_blocks(text))  # no nesting
        for block in historical_blocks(text):
            assert re.search(r"NOT normative|non-normative", block)


# ---------------------------------------------------------------------------
# 4-6  EMA and audio authority (RD-031, RD-030)
# ---------------------------------------------------------------------------


class TestEmaAndAudioAuthority:
    @pytest.mark.parametrize("path", [V9, V7, DESIGN, PAPER])
    def test_no_active_ema_instruction(self, path):
        text = active(read(path))
        assert not re.search(r"(?i)\balpha\b\s*=?\s*0\.5|\\alpha|α", text)
        for line in text.splitlines():
            if re.search(r"\bEMA\b", line):
                assert NEGATION.search(line), line

    def test_frozen_configuration_and_code_really_have_no_ema(self):
        config = read(REPO / "configs" / "frozen_experiment_v1.yaml")
        assert not re.search(r"(?i)\bema\b|alpha", config)
        for directory in ("fusion", "simulation"):
            for path in (REPO / "src" / "railway_detection" / directory).glob("*.py"):
                assert not re.search(r"\bEMA\b|ema_alpha", path.read_text(encoding="utf-8")), path
        assert "confirm_frames: 2" in config and "miss_tolerance_frames: 2" in config

    def test_historical_ema_wording_is_kept_and_identifiable(self):
        blocks = "\n".join(historical_blocks(read(V9)))
        assert re.search(r"EMA", blocks) and re.search(r"0\.50", blocks)
        assert "RD-031" in blocks

    def test_no_active_statement_gives_audio_warning_or_clearance_authority(self):
        text = active(read(V9))
        assert not re.search(
            r"(?i)audio[^.\n]{0,80}\b(can|may|could)\s+(trigger|initiate|start)", text
        )
        assert not re.search(r"CAN trigger", text)
        assert "INV-2 (Single-Modality Warning)" not in text
        assert re.search(r"cannot independently initiate a warning", text)
        assert "RULE_2_AUDIO_SUPPORT_ONLY" in text

    def test_the_frozen_policy_is_unchanged_and_says_audio_is_support_only(self):
        policy = REPO / "configs" / "decision_policy_v1.yaml"
        assert sha(policy) == "c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575"
        assert "RULE_2_AUDIO_SUPPORT_ONLY" in read(policy)
        assert "Audio alone cannot actuate gate in IDLE" in read(policy)

    def test_no_active_text_credits_audio_with_warning_lead_time(self):
        text = active(read(V9))
        assert not re.search(r"(?i)provides advance warning", text)


# ---------------------------------------------------------------------------
# 7-10  Independent-camera design, R04 scope
# ---------------------------------------------------------------------------


class TestIndependentCameraDesign:
    @pytest.mark.parametrize("path", [V9, DESIGN])
    def test_independent_camera_is_primary_and_uses_the_provisional_names(self, path):
        text = active(read(path))
        assert re.search(
            r"(?i)independent[- ]camera (analysis )?is primary|independent-camera primary", text
        )
        for name in ("B0_back", "B0_back_stateless", "B2_back"):
            assert name in text
        assert re.search(r"(?i)provisional", text)

    def test_the_e_matrix_is_not_the_active_execution_matrix(self):
        text = active(read(V9))
        assert not re.search(r"\bE([1-9]|10)\b", text)
        assert "not restored as the primary execution matrix" in read(V9).replace("*", "")

    @pytest.mark.parametrize("path", [V9, DESIGN, PAPER])
    def test_fused_r04_is_exploratory_only(self, path):
        text = active(read(path))
        assert re.search(r"(?i)(fused|R04)[^.\n]{0,160}exploratory", text)

    @pytest.mark.parametrize("path", [V9, DESIGN, PAPER])
    def test_r04_scope_is_the_existing_eleven_events(self, path):
        text = active(read(path))
        assert re.search(r"(?i)\b11[- ]event", text)
        for line in text.splitlines():
            if re.search(r"(?i)\b(12|twelve)[- ]events?\b", line):
                assert NEGATION.search(line), line

    @pytest.mark.parametrize("path", [V9, V7, DESIGN, PAPER])
    def test_event_010_is_never_silently_added(self, path):
        for line in active(read(path)).splitlines():
            if "event_010" in line:
                assert NEGATION.search(line), line
                assert "added" in line or "add" in line


# ---------------------------------------------------------------------------
# 11-16  M4 / M5 / timestamps / censoring / M3 -- document vs production
# ---------------------------------------------------------------------------


class TestMetricContractMatchesPhase1:
    def test_every_reason_string_the_code_emits_is_in_the_protocol(self):
        text = active(read(V9))
        cases = {
            M4_REASON_REPLAY_ENDED_BEFORE_T4: [step(0.0, False), step(1.0)],
            M4_REASON_REPLAY_STARTED_LATE: [step(1.0, False), step(6.0, False)],
            M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4: [step(5.0, False), step(6.0, False)],
            M4_REASON_NO_INTERIOR_STEPS: [step(0.0), step(5.0)],
        }
        for reason, steps in cases.items():
            assert classify_m4(run(steps), 5.0).reason == reason
            assert reason in text, reason

    def test_m5_requires_zero_origin_and_coverage_in_document_and_code(self):
        text = active(read(V9))
        assert re.search(r"(?i)zero origin", text) and "replay_started_late" in text
        full = classify_m4(run([step(float(t), False) for t in range(7)]), 5.0)
        assert full.status == M4_STATUS_NEVER_PROTECTED and full.never_protected is True
        late = classify_m4(run([step(float(t), False) for t in range(1, 7)]), 5.0)
        assert late.never_protected is None and late.status == M4_STATUS_NOT_EVALUABLE
        at_t4 = classify_m4(run([step(5.0, False), step(6.0, False)]), 5.0)
        assert at_t4.never_protected is None

    def test_m4_uses_the_first_blocked_state_and_a_strict_open_interval(self):
        text = active(read(V9))
        assert re.search(r"(?i)first retained replay step whose passage is blocked", text)
        assert re.search(r"open interval \$\(t_\{\\text\{blocked\}\}, T_4\)\$", text)
        # a violation exactly at T4 is outside the open interval
        at = [step(0.0), step(1.0), step(5.0, False), step(6.0)]
        assert classify_m4(run(at), 5.0).premature is False
        inside = [step(0.0), step(1.0), step(4.999999, False), step(6.0)]
        assert classify_m4(run(inside), 5.0).premature is True

    def test_a_witnessed_violation_remains_evaluable_when_its_interval_is_observed(self):
        assert re.search(r"(?i)witnessed violation", active(read(V9)))
        short = classify_m4(run([step(2.0), step(3.0, False), step(4.0)]), 5.0)
        assert short.status == M4_STATUS_EVALUABLE and short.premature is True

    def test_empty_interval_stays_not_evaluable_and_is_never_safe(self):
        text = active(read(V9))
        assert re.search(r"no_steps_in_protection_interval", text)
        assert re.search(r"(?i)it is not safe", text)
        for diagnostic in (
            "first_blocked_s",
            "last_step_s",
            "interior_step_count",
            "max_step_gap_s",
        ):
            assert diagnostic in text
        result = classify_m4(run([step(0.0), step(5.0)]), 5.0)
        assert result.status == M4_STATUS_NOT_EVALUABLE and result.premature is None
        assert result.interior_step_count == 0 and result.max_step_gap_s == 5.0

    def test_timestamp_normalization_is_the_same_in_documents_and_code(self):
        from railway_detection.evaluation.timebase import TIMESTAMP_ROUND_DIGITS

        assert TIMESTAMP_ROUND_DIGITS == 6
        for path in (V9, V7):
            assert "round(float(t), 6)" in active(read(path))
        assert re.search(r"(?i)not a (physical )?timing tolerance", active(read(V9)))
        # 0.3 is not before T4 = 0.1 + 0.2 once both are on the grid
        steps = [step(0.0), step(0.1), step(0.3, False), step(0.5)]
        assert classify_m4(run(steps), 0.1 + 0.2).premature is False
        # genuine 1-microsecond differences keep their order
        assert classify_m4(run(steps), 0.300001).premature is True

    def test_no_sampling_density_or_gap_threshold_is_introduced(self):
        text = active(read(V9))
        assert re.search(r"(?i)no maximum-gap or sampling-density threshold", text)
        assert not re.search(r"(?i)max(imum)?[- ]gap\s*(of|<=|≤|<|>|=)\s*\d", text)
        assert not re.search(r"(?i)at least \d+\s+(retained )?(steps|samples|ticks)", text)
        sparse = [step(0.0), step(1.0), step(20.0), step(30.0)]  # a 19 s gap, one interior step
        result = classify_m4(run(sparse), 25.0)
        assert result.status == M4_STATUS_EVALUABLE and result.max_step_gap_s == 19.0

    def test_sampled_replay_limitation_is_stated(self):
        assert re.search(r"(?i)do not establish the continuous physical state", active(read(V9)))

    def test_censored_t0_with_unknown_direction_is_not_treated_as_visible(self):
        for path in (V9, V7):
            text = active(read(path))
            assert re.search(r"(?i)unverifiable", text)
            assert re.search(r"(?i)never inferred", text)
        outcome = screen_missed_train_lead_in(
            10.0,
            first_visible_time_s=None,
            first_visible_left_censored=False,
            min_block_latency_s=3.6,
            min_block_latency_source="unit-test",
        )
        assert outcome.outcome == SCREEN_UNVERIFIABLE and outcome.evaluable is False

    def test_literal_m3_is_secondary_and_not_yet_propagated(self):
        text = active(read(V9))
        assert re.search(r"(?i)literal Design M3 — secondary", text)
        assert re.search(r"(?i)physical lead-in feasibility screen — primary", text)
        assert "m3_design_literal_evaluable" in text and "Phase 4" in text
        assert "m3_design_literal_evaluable" in {f.name for f in fields(LeadInScreenResult)}
        assert "m3_design_literal_evaluable" not in {f.name for f in fields(SingleEventEvaluation)}
        assert "m3_design_literal_evaluable" not in {
            f.name for f in fields(CohortEvaluationSummary)
        }

    def test_the_physical_screen_is_default_off_in_documents_and_code(self):
        assert re.search(r"(?i)disabled by default", active(read(V9)))
        evaluate_run = inspect.signature(EventMetricsCalculator.evaluate_run)
        assert evaluate_run.parameters["lead_in_min_block_latency_s"].default is None
        replay = inspect.signature(evaluate_event_replay)
        assert replay.parameters["lead_in_min_block_latency_s"].default is None
        runner = read(REPO / "src/railway_detection/evaluation/evaluation_runner.py")
        assert "lead_in" not in runner and "screen_missed_train_lead_in" not in runner

    def test_the_minimum_latency_is_never_presented_as_an_approved_threshold(self):
        for path in (V9, V7, PAPER):
            assert not re.search(r"3\.6", active(read(path))), path
        for line in read(DESIGN).splitlines():
            if "3.6" in line:
                assert re.search(r"not an approved threshold", line)

    def test_the_metrics_module_still_exposes_the_documented_window_name(self):
        assert M4_WINDOW == "first_blocked_to_t4_clearance"
        assert M4_WINDOW in active(read(V9))
        assert hasattr(metrics, "REPLAY_ORIGIN_S")


# ---------------------------------------------------------------------------
# 18-22  Scope, statistics, claims, authors, results
# ---------------------------------------------------------------------------


class TestScopeStatisticsAndClaims:
    def test_occupancy_duration_is_deferred_and_has_no_implementation(self):
        for path in (V9, DESIGN):
            assert re.search(r"DEFERRED[^.\n]{0,20}RD-018", read(path))
        names = {
            f.name for cls in (SingleEventEvaluation, CohortEvaluationSummary) for f in fields(cls)
        }
        assert not [n for n in names if "occupan" in n.lower()]

    @pytest.mark.parametrize("path", [V9, DESIGN, PAPER])
    def test_engine_events_stay_outside_pooled_aggregates(self, path):
        assert re.search(
            r"(?i)engine[^.\n]{0,120}(excluded from pooled|never pooled|outside pooled)",
            active(read(path)),
        )

    def test_production_still_keeps_the_engine_out_of_train_aggregates(self):
        train = EventMetricsCalculator.evaluate_run(
            run([step(float(t), t >= 1) for t in range(8)]),
            entry_time_s=1.0,
            clearance_time_s=5.0,
            premature_opening_window=M4_WINDOW,
        )
        engine = EventMetricsCalculator.evaluate_run(
            SimulationRunResult(
                "engine_events/event_001",
                "synthetic",
                [step(float(t), True) for t in range(8)],
                7.0,
                0.0,
            ),
            clearance_time_s=5.0,
            has_train_ground_truth=False,
            premature_opening_window=M4_WINDOW,
        )
        pooled = EventMetricsCalculator.aggregate_cohort([train, engine])
        assert pooled.engine_events == 1 and pooled.eligible_events == 1

    @pytest.mark.parametrize("path", [V9, DESIGN, PAPER])
    def test_no_inferential_test_is_presented_as_approved(self, path):
        text = without_not_claims(active(read(path)))
        for line in text.splitlines():
            if re.search(r"(?i)mcnemar|wilcoxon|holm|p-value|bootstrap|effect size", line):
                assert NEGATION.search(line), line
        assert re.search(r"(?i)descriptive statistics only", active(read(path)))

    def test_no_active_unsupported_claim_remains_in_the_protocol_or_paper(self):
        forbidden = [
            r"statistically significant",
            r"significantly (better|improv|reduc)",
            r"improves? safety",
            r"reduces? accidents",
            r"outperform",
            r"generalizes? to",
            r"large effect",
            r"eliminat\w+ (of )?premature",
        ]
        for path in (V9, PAPER):
            text = without_not_claims(active(read(path)))
            for pattern in forbidden:
                for line in text.splitlines():
                    if re.search(pattern, line, flags=re.I):
                        assert NEGATION.search(line), (path.name, pattern, line)

    def test_paper_claims_follow_rd_051_to_rd_055(self):
        text = active(read(PAPER))
        assert re.search(r"(?i)single-site", text) and re.search(r"(?i)descriptive", text)
        assert "Human authors only" in text and "No AI agent is listed as an author" in text
        assert re.search(r"Publication venue: UNDECIDED", text)
        assert re.search(r"(?i)no raw media", text)
        assert "RD-051" in text and "RD-053" in text and "RD-054" in text and "RD-055" in text
        assert re.search(r"<!--NOT-CLAIMS-->", read(PAPER))
        not_claims = re.findall(
            r"<!--NOT-CLAIMS-->(.*?)<!--/NOT-CLAIMS-->", read(PAPER), flags=re.S
        )
        assert re.search(r"cross-site", not_claims[0]) and re.search(r"accident", not_claims[0])

    def test_no_author_identity_or_empirical_value_is_invented(self):
        text = read(PAPER)
        assert not re.search(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b", text)  # ORCID shape
        assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)  # e-mail
        assert "Antigravity" not in text
        assert text.count("to be supplied by the researcher") >= 3
        for path in (PAPER, DESIGN):
            sections = re.findall(
                r"<!--RESULTS-TABLES-->(.*?)<!--/RESULTS-TABLES-->", read(path), flags=re.S
            )
            assert len(sections) == 1
            rows = [r for r in sections[0].strip().splitlines() if r.startswith("|")][2:]
            assert rows
            for row in rows:
                cells = [c.strip() for c in row.strip("|").split("|")][1:]
                for cell in cells:
                    assert re.fullmatch(r"\[RESULTS PENDING\]|NOT COMPUTABLE.*", cell), cell

    def test_the_metric_table_has_the_required_columns_and_rows(self):
        text = read(DESIGN)
        header = next(line for line in text.splitlines() if line.startswith("| Metric |"))
        for column in (
            "Scientific meaning",
            "Required camera stream",
            "Required GT boundaries",
            "Evaluability conditions",
            "Denominator",
            "Known limitations",
            "Implementation status",
        ):
            assert column in header
        for metric in (
            "M4 premature opening",
            "M5 never protected",
            "MTR, physical screen",
            "Literal Design M3",
            "Full crossing occupancy duration",
        ):
            assert metric in text


# ---------------------------------------------------------------------------
# 23  Working-tree files untouched
# ---------------------------------------------------------------------------


class TestWorkingTreeUntouched:
    BASELINES = {
        "docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md": "7c183b323970591b68f0db692e70413e54dcacfc4bf78a358c28f1b1ed68734c",  # noqa: E501
        "docs/FINAL_GROUND_TRUTH_PROTOCOL.md": "d100c1e6a63280c375f94e297416efb0cf7dd3c15c9aa8df076ede052d49ecf4",  # noqa: E501
        "docs/EXPERIMENT_DESIGN_FINAL.md": "2e906c1e19426d2fa406fe626858b0b308fc6abb38510afd660768e954fbb407",  # noqa: E501
        "docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md": "03444930ec0d73e9dad16a2b510511c61e9a1302e3e6a25cf83307d81a26ea78",  # noqa: E501
        "configs/frozen_experiment_v1.yaml": "b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a",  # noqa: E501
        "configs/decision_policy_v1.yaml": "c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575",  # noqa: E501
    }

    def test_working_tree_files_are_byte_identical_to_their_verified_baselines(self):
        for rel, expected in self.BASELINES.items():
            assert sha(REPO / rel) == expected, rel

    def test_the_helper_baselines_equal_these_baselines(self):
        tool = load_tool()
        for rel, expected in tool.WORKING_TREE_BASELINES.items():
            assert self.BASELINES[rel] == expected

    def test_proposals_differ_from_the_working_tree_and_diffs_exist(self):
        assert sha(V9) != self.BASELINES["docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md"]
        assert sha(V7) != self.BASELINES["docs/FINAL_GROUND_TRUTH_PROTOCOL.md"]
        for name in (
            "v9_working_tree_vs_v9.1.1_PROPOSED.diff",
            "v7_working_tree_vs_v7.1.1_PROPOSED.diff",
        ):
            diff = read(P2 / name)
            assert diff.startswith("--- ") and "\n+++ " in diff and "\n@@ " in diff


# ---------------------------------------------------------------------------
# 24-26  Snapshot helper (synthetic temporary directories only)
# ---------------------------------------------------------------------------

BASE_A, BASE_B = "docs/PROTO_A.md", "docs/PROTO_B.md"
PROP_A, PROP_B = "docs/generated/phase2/A_PROPOSED.md", "docs/generated/phase2/B_PROPOSED.md"
HEAD_A, HEAD_B = "# PROPOSED — Alpha (v1-PROPOSED)", "# PROPOSED — Beta (v1-PROPOSED)"


def proposal_text(heading: str) -> str:
    return f"{heading}\n\n> **{BANNER}**\n\nBody.\n"


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    """A synthetic repository root plus a tool whose constants point at it."""
    root = tmp_path / "repo"
    (root / "docs" / "generated" / "phase2").mkdir(parents=True)
    (root / BASE_A).write_text("alpha baseline\n", encoding="utf-8")
    (root / BASE_B).write_text("beta baseline\n", encoding="utf-8")
    (root / PROP_A).write_text(proposal_text(HEAD_A), encoding="utf-8")
    (root / PROP_B).write_text(proposal_text(HEAD_B), encoding="utf-8")
    tool = load_tool()
    baselines = {
        BASE_A: hashlib.sha256(b"alpha baseline\n").hexdigest(),
        BASE_B: hashlib.sha256(b"beta baseline\n").hexdigest(),
    }
    proposals = {PROP_A: (HEAD_A, BASE_A), PROP_B: (HEAD_B, BASE_B)}
    monkeypatch.setattr(tool, "WORKING_TREE_BASELINES", baselines)
    monkeypatch.setattr(tool, "PROPOSALS", proposals)
    monkeypatch.setattr(tool, "INVENTORY_EXTRAS", (PROP_A, "docs/absent.md"))
    return tool, root, baselines, proposals


def tree_digest(root: pathlib.Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


class TestSnapshotHelperWorks:
    def test_check_and_prepare_on_a_synthetic_root(self, synthetic, capsys):
        tool, root, baselines, _ = synthetic
        before = tree_digest(root)
        assert tool.main(["check", "--root", str(root)]) == 0
        assert tree_digest(root) == before  # `check` writes nothing
        report = json.loads(capsys.readouterr().out)
        assert report["status"].startswith("PREPARATION_ONLY")
        assert [r["unchanged"] for r in report["working_tree_protocols"]] == [True, True]
        assert report["git"]["available"] is False  # a temporary directory is not a repository
        for row in report["proposals"]:
            key = "sha256_PROPOSAL_NOT_APPROVED_NOT_BOUND"
            assert row[key] == hashlib.sha256((root / row["path"]).read_bytes()).hexdigest()
            assert "sha256" not in row  # a proposal hash is never presented as a protocol hash
        out = "docs/generated/snap"
        assert tool.main(["prepare", "--root", str(root), "--out-dir", out]) == 0
        written = sorted(p.name for p in (root / out).iterdir())
        assert written == sorted(tool.OUTPUT_FILES)
        after = tree_digest(root)
        new = set(after) - set(before)
        assert new == {f"{out}/{name}" for name in tool.OUTPUT_FILES}
        assert {k: after[k] for k in before} == before  # nothing existing changed
        checklist = (root / out / "ADOPTION_CHECKLIST.md").read_text(encoding="utf-8")
        assert "PREPARATION ONLY" in checklist and "never copies anything" in checklist
        inventory = json.loads((root / out / "SNAPSHOT_INVENTORY.json").read_text(encoding="utf-8"))
        assert {i["path"]: i["present"] for i in inventory["inventory"]} == {
            PROP_A: True,
            "docs/absent.md": False,
        }

    def test_git_state_is_parsed_from_read_only_queries(self, synthetic):
        tool, root, _, _ = synthetic
        answers = {
            ("rev-parse", "HEAD"): "abc123\n",
            ("rev-parse", "--abbrev-ref", "HEAD"): "main\n",
            ("status", "--porcelain"): " M docs/a.md\n?? new.py\n?? clip.mov\n M x.mov\n",
            ("diff", "--cached", "--name-only"): "",
        }

        def fake(cmd, **kwargs):
            args = tuple(cmd[3:])
            return subprocess.CompletedProcess(cmd, 0, stdout=answers[args], stderr="")

        state = tool.git_state(root, fake)
        assert state["head"] == "abc123" and state["staged_count"] == 0
        assert state["untracked_entry_count"] == 2
        assert state["modified_tracked"] == ["docs/a.md"]  # a media-named entry is never reported

    def test_a_missing_git_binary_is_reported_not_raised(self, synthetic):
        tool, root, _, _ = synthetic

        def no_git(cmd, **kwargs):
            raise FileNotFoundError("git")

        assert tool.git_state(root, no_git) == {
            "available": False,
            "note": "not a git repository or git unavailable",
        }


class TestSnapshotHelperRefuses:
    @pytest.mark.parametrize(
        ("rel", "code"),
        [
            ("/etc/hosts.md", "PATH_OUTSIDE_ROOT"),
            ("../outside.md", "PATH_OUTSIDE_ROOT"),
            ("docs/clip.mov", "PATH_MEDIA_OR_BINARY_REFUSED"),
            ("docs/sound.wav", "PATH_MEDIA_OR_BINARY_REFUSED"),
            ("docs/model.pt", "PATH_MEDIA_OR_BINARY_REFUSED"),
            ("docs/table.csv", "PATH_EXTENSION_NOT_ALLOWED"),
            ("docs/missing.md", "SOURCE_MISSING"),
            ("", "PATH_MALFORMED"),
            ("docs\\x.md", "PATH_MALFORMED"),
        ],
    )
    def test_unsafe_or_missing_paths(self, synthetic, rel, code):
        tool, root, _, _ = synthetic
        with pytest.raises(tool.SnapshotError) as info:
            tool.resolve_in_root(root, rel)
        assert info.value.code == code

    def test_symlinks_are_refused(self, synthetic, tmp_path):
        tool, root, _, _ = synthetic
        outside = tmp_path / "outside.md"
        outside.write_text("secret\n", encoding="utf-8")
        os.symlink(outside, root / "docs" / "link.md")
        with pytest.raises(tool.SnapshotError) as info:
            tool.resolve_in_root(root, "docs/link.md")
        assert info.value.code == "PATH_SYMLINK_REFUSED"

    def test_a_changed_baseline_stops_everything_and_writes_nothing(self, synthetic):
        tool, root, _, _ = synthetic
        (root / BASE_A).write_text("alpha EDITED\n", encoding="utf-8")
        before = tree_digest(root)
        assert tool.main(["prepare", "--root", str(root), "--out-dir", "docs/generated/snap"]) == 3
        assert tree_digest(root) == before
        with pytest.raises(tool.SnapshotError) as info:
            tool.build_report(root)
        assert info.value.code == "BASELINE_MISMATCH" and info.value.exit_code == 3

    @pytest.mark.parametrize(
        "text",
        [
            "# Alpha\n\n> **PROPOSED — NOT APPROVED — NOT HASH-BOUND**\n",  # wrong heading
            f"{HEAD_A}\n\nBody without a banner.\n",
            f"{HEAD_A}\n\n> **{BANNER}**\n\nStatus: APPROVED by the researcher.\n",
            f"{HEAD_A}\n\n> **{BANNER}**\n\nThis text is HASH-BOUND to the protocol.\n",
        ],
    )
    def test_a_proposal_mislabeled_as_approved_is_refused(self, synthetic, text):
        tool, root, _, _ = synthetic
        (root / PROP_A).write_text(text, encoding="utf-8")
        with pytest.raises(tool.SnapshotError) as info:
            tool.build_report(root)
        assert info.value.code == "PROPOSAL_MISLABELED" and info.value.exit_code == 3

    def test_a_proposal_may_not_be_the_protocol_file_itself(self, synthetic):
        tool, root, baselines, _ = synthetic
        with pytest.raises(tool.SnapshotError) as info:
            tool.build_report(root, proposals={BASE_A: (HEAD_A, BASE_A)})
        assert info.value.code == "PROPOSAL_IS_PROTOCOL_FILE"

    def test_an_existing_destination_is_never_overwritten(self, synthetic):
        tool, root, _, _ = synthetic
        out = "docs/generated/snap"
        assert tool.main(["prepare", "--root", str(root), "--out-dir", out]) == 0
        first = tree_digest(root)
        assert tool.main(["prepare", "--root", str(root), "--out-dir", out]) == 2
        assert tree_digest(root) == first
        # one pre-existing file blocks the whole write, and nothing partial is left behind
        (root / out / "ADOPTION_CHECKLIST.md").unlink()
        (root / out / "SNAPSHOT_REPORT.md").unlink()
        (root / out / "SNAPSHOT_INVENTORY.json").write_text("keep me\n", encoding="utf-8")
        assert tool.main(["prepare", "--root", str(root), "--out-dir", out]) == 2
        assert (root / out / "SNAPSHOT_INVENTORY.json").read_text(encoding="utf-8") == "keep me\n"
        assert not (root / out / "ADOPTION_CHECKLIST.md").exists()

    def test_exclusive_create_refuses_a_file_that_appears_late_and_leaves_no_partial_output(
        self, synthetic, monkeypatch
    ):
        tool, root, _, _ = synthetic
        report = tool.build_report(root)
        real = tool.checklist_markdown
        race = root / "docs/generated/race"

        def racing(rep):
            race.mkdir(parents=True, exist_ok=True)
            (race / "SNAPSHOT_REPORT.md").write_text("late\n", encoding="utf-8")
            return real(rep)

        monkeypatch.setattr(tool, "checklist_markdown", racing)
        with pytest.raises(tool.SnapshotError) as info:
            tool.write_outputs(root, "docs/generated/race", report)
        assert info.value.code == "DESTINATION_EXISTS"
        assert sorted(p.name for p in race.iterdir()) == ["SNAPSHOT_REPORT.md"]
        assert (race / "SNAPSHOT_REPORT.md").read_text(encoding="utf-8") == "late\n"

    @pytest.mark.parametrize(
        "out_dir",
        ["/tmp/elsewhere", "../escape", "docs/other", "docs", "docs/generated/../../x", "", "a\\b"],
    )
    def test_output_directories_are_confined(self, synthetic, out_dir):
        tool, root, _, _ = synthetic
        report = tool.build_report(root)
        before = tree_digest(root)
        with pytest.raises(tool.SnapshotError):
            tool.write_outputs(root, out_dir, report)
        assert tree_digest(root) == before

    def test_a_symlinked_output_directory_is_refused(self, synthetic, tmp_path):
        tool, root, _, _ = synthetic
        target = tmp_path / "elsewhere"
        target.mkdir()
        os.symlink(target, root / "docs" / "generated" / "linked")
        with pytest.raises(tool.SnapshotError) as info:
            tool.write_outputs(root, "docs/generated/linked", tool.build_report(root))
        assert info.value.code == "OUTPUT_SYMLINK_REFUSED"
        assert list(target.iterdir()) == []


class TestSnapshotHelperNeverWritesToGit:
    FORBIDDEN = (
        "add",
        "commit",
        "push",
        "reset",
        "clean",
        "checkout",
        "restore",
        "revert",
        "stash",
        "fsck",
        "rm",
        "mv",
        "rebase",
        "merge",
        "tag",
        "branch",
        "config",
    )

    def test_every_git_command_the_helper_issues_is_on_the_read_only_allowlist(self, synthetic):
        tool, root, _, _ = synthetic
        seen: list[tuple[str, ...]] = []

        def spy(cmd, **kwargs):
            seen.append(tuple(cmd[3:]))
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")

        tool.build_report(root, runner=spy)
        assert seen and set(seen) <= set(tool.GIT_ALLOWED)
        assert not {arg for cmd in seen for arg in cmd} & set(self.FORBIDDEN)

    @pytest.mark.parametrize("verb", FORBIDDEN)
    def test_forbidden_git_verbs_are_refused_before_any_process_starts(self, synthetic, verb):
        tool, root, _, _ = synthetic
        called = []
        with pytest.raises(tool.SnapshotError) as info:
            tool._git(root, (verb, "."), lambda *a, **k: called.append(a))
        assert info.value.code == "GIT_COMMAND_REFUSED" and called == []

    def test_the_allowlist_contains_only_read_only_queries(self):
        tool = load_tool()
        for command in tool.GIT_ALLOWED:
            assert command[0] in {"rev-parse", "status", "diff"}
            assert not set(command) & set(self.FORBIDDEN)

    def test_the_script_has_no_direct_process_or_shell_call(self):
        tree = ast.parse(read(REPO / "scripts" / "prepare_researcher_snapshot.py"))
        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    called.add(f"{func.value.id}.{func.attr}")
        assert not {
            c
            for c in called
            if c.startswith(
                (
                    "subprocess.",
                    "os.system",
                    "os.popen",
                    "shutil.",
                    "os.remove",
                    "os.rename",
                    "os.unlink",
                    "os.replace",
                )
            )
        }

    def test_no_directory_is_ever_enumerated_and_nothing_is_copied(self, synthetic, monkeypatch):
        tool, root, _, _ = synthetic

        def boom(*args, **kwargs):
            raise AssertionError("directory enumeration attempted")

        before = hashlib.sha256((root / BASE_A).read_bytes()).hexdigest()
        with monkeypatch.context() as patched:
            patched.setattr(os, "listdir", boom)
            patched.setattr(os, "scandir", boom)
            patched.setattr(os, "walk", boom)
            patched.setattr(pathlib.Path, "iterdir", boom)
            patched.setattr(pathlib.Path, "glob", boom)
            patched.setattr(pathlib.Path, "rglob", boom)
            report = tool.build_report(root)
            tool.write_outputs(root, "docs/generated/snap", report)
        assert hashlib.sha256((root / BASE_A).read_bytes()).hexdigest() == before
        assert (root / PROP_A).read_text(encoding="utf-8") == proposal_text(HEAD_A)
