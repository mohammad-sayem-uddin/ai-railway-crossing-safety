"""Phase 5 review tooling after the Mission 10 rewrite.

Replaces the earlier suite, whose receipt / trigger / adjudication classes tested APIs that have
been removed (a duplicate receipt authority, caller-constructed outcomes, invented triggers and an
automatic CONSENSUS status). The canonical behaviour is tested here and in
``tests/test_mission10_second_review.py``. All fixtures are synthetic.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import official_workspace as ow

from railway_detection.annotation import phase5_review_tooling as tooling
from railway_detection.annotation import receipt as receipt_module
from railway_detection.annotation.phase5_review_tooling import (
    PromotionViolation,
    ReviewEventIdentity,
    ReviewToolingError,
    assess_review_corpus,
    validate_reviewer_identity,
    validate_timestamps_ordering,
)
from railway_detection.evaluation import governance


@pytest.fixture
def allowlist(tmp_path: Path) -> Path:
    path = tmp_path / "authorized_reviewers.json"
    path.write_text(
        json.dumps({"authorized_reviewers": ["lead@example.org", "second@example.org"]}),
        encoding="utf-8",
    )
    return path


class TestReviewerIdentityValidation:
    def test_empty_and_whitespace_rejected(self, allowlist: Path):
        for blank in ("", "   "):
            ok, msg = validate_reviewer_identity(blank, allowlist)
            assert not ok and "empty" in msg

    def test_blocklisted_agents_rejected(self, allowlist: Path):
        for name in ("gemini_annotator", "researcher_agent", "llm_annotator", "claude_sonnet"):
            ok, msg = validate_reviewer_identity(name, allowlist)
            assert not ok and "blocklisted" in msg

    def test_missing_allowlist_fails_closed(self, tmp_path: Path):
        ok, msg = validate_reviewer_identity("lead@example.org", tmp_path / "absent.json")
        assert not ok and "not found" in msg

    def test_canonical_string_list_is_the_only_authority(self, allowlist: Path):
        assert validate_reviewer_identity("lead@example.org", allowlist) == (True, "Authorized")
        ok, msg = validate_reviewer_identity("stranger@example.org", allowlist)
        assert not ok and "not present" in msg

    def test_dict_style_allowlist_is_not_accepted(self, tmp_path: Path):
        path = tmp_path / "dict_style.json"
        path.write_text(
            json.dumps({"authorized_reviewers": [{"reviewer_id": "Lead", "status": "ACTIVE"}]}),
            encoding="utf-8",
        )
        ok, msg = validate_reviewer_identity("Lead", path)
        assert not ok and "Failed to load allowlist" in msg

    def test_no_role_parameter_exists(self, allowlist: Path):
        with pytest.raises(TypeError):
            validate_reviewer_identity("lead@example.org", allowlist, required_role="X")  # type: ignore[call-arg]


class TestEventIdentity:
    def test_bare_event_id_rejected(self):
        with pytest.raises(PromotionViolation):
            ReviewEventIdentity.parse("event_001")

    def test_empty_rejected(self):
        with pytest.raises(ReviewToolingError):
            ReviewEventIdentity.parse("  ")

    def test_qualified_identity_round_trips(self):
        identity = ReviewEventIdentity.parse("engine_events/event_001")
        assert (identity.cohort, identity.event_id) == ("engine_events", "event_001")
        assert identity.qualified_key == "engine_events/event_001"


class TestTimestampValidation:
    def test_valid_timestamps_ordering(self):
        valid_ts = {
            "t0_s": 10.0,
            "t1_s": 12.5,
            "t2_s": 15.0,
            "t3_s": 20.0,
            "t4_s": 25.0,
        }
        ok, errors = validate_timestamps_ordering(valid_ts)
        assert ok
        assert len(errors) == 0

    def test_partial_valid_timestamps(self):
        partial_ts = {
            "t0_s": 10.0,
            "t1_s": None,
            "t2_s": 15.0,
            "t3_s": None,
            "t4_s": 25.0,
        }
        ok, errors = validate_timestamps_ordering(partial_ts)
        assert ok
        assert len(errors) == 0

    def test_out_of_order_timestamps(self):
        invalid_ts = {
            "t0_s": 10.0,
            "t1_s": 15.0,
            "t2_s": 12.0,  # t1 > t2 violation
            "t3_s": 20.0,
            "t4_s": 25.0,
        }
        ok, errors = validate_timestamps_ordering(invalid_ts)
        assert not ok
        assert any("Timestamp sequence violation" in e for e in errors)

    def test_negative_timestamp_rejected(self):
        neg_ts = {
            "t0_s": -2.0,
            "t4_s": 10.0,
        }
        ok, errors = validate_timestamps_ordering(neg_ts)
        assert not ok
        assert any("cannot be negative" in e for e in errors)

    def test_boolean_timestamp_rejected(self):
        bool_ts = {
            "t0_s": True,
            "t4_s": 10.0,
        }
        ok, errors = validate_timestamps_ordering(bool_ts)
        assert not ok
        assert any("must be a real number, got bool" in e for e in errors)

    def test_nan_timestamp_rejected(self):
        nan_ts = {
            "t0_s": float("nan"),
            "t4_s": 10.0,
        }
        ok, errors = validate_timestamps_ordering(nan_ts)
        assert not ok
        assert any("must be finite" in e for e in errors)

    def test_inf_timestamp_rejected(self):
        inf_ts = {
            "t0_s": 5.0,
            "t4_s": float("inf"),
        }
        ok, errors = validate_timestamps_ordering(inf_ts)
        assert not ok
        assert any("must be finite" in e for e in errors)

    def test_invalid_type_timestamp_rejected(self):
        str_ts = {
            "t0_s": "not-a-number",
            "t4_s": 10.0,
        }
        ok, errors = validate_timestamps_ordering(str_ts)
        assert not ok
        assert any("must be a real number" in e for e in errors)


class TestRemovedNonCanonicalAuthorities:
    """The defects behind the two failed audits are removed, not patched."""

    @pytest.mark.parametrize(
        "name",
        [
            "PromotionReceiptV5",
            "generate_promotion_receipt",
            "verify_promotion_receipt",
            "AdjudicationOutcome",
            "adjudicate_dual_reviews",
            "evaluate_second_review_triggers",
            "SecondReviewTriggerResult",
        ],
    )
    def test_name_is_gone(self, name: str):
        assert not hasattr(tooling, name)

    def test_only_one_module_defines_the_receipt_producer_constant(self):
        root = Path(__file__).resolve().parents[2] / "src"
        definers = [
            p.relative_to(root).as_posix()
            for p in root.rglob("*.py")
            if "PROMOTION_RECEIPT_PRODUCER =" in p.read_text(encoding="utf-8")
        ]
        assert definers == ["railway_detection/annotation/receipt.py"]

    def test_no_module_other_than_the_readiness_cli_builds_a_promotion_receipt(self):
        root = Path(__file__).resolve().parents[2] / "src"
        builders = [
            p.relative_to(root).as_posix()
            for p in root.rglob("*.py")
            if "PROMOTION_RECEIPT_SCHEMA," in p.read_text(encoding="utf-8")
            and "receipt_body_sha256(" in p.read_text(encoding="utf-8")
            and "def build_promotion_receipt" in p.read_text(encoding="utf-8")
        ]
        assert builders == ["railway_detection/annotation/readiness_cli.py"]


def _reviews(ws) -> Path:
    return ws.root / "data/ground_truth/reviews"


def _assess(ws):
    return assess_review_corpus(
        _reviews(ws),
        allowlist_path=ws.root / receipt_module.DEFAULT_ALLOWLIST_RELATIVE,
        inventory_path=ws.root / receipt_module.DEFAULT_INVENTORY_RELATIVE,
        repository_root=ws.root,
    )


def _second_review_file(ws) -> Path:
    return next(_reviews(ws).rglob("*__second_review.json"))


class TestCorpusAssessmentOnActualRecords:
    def test_complete_synthetic_corpus_is_settled(self, tmp_path, monkeypatch):
        ws = ow.build_workspace(tmp_path, monkeypatch)
        result = _assess(ws)
        assert result.record_count == 4
        assert result.settled, (result.findings, result.schema_problems)

    def test_removing_the_second_review_unsettles_it(self, tmp_path, monkeypatch):
        ws = ow.build_workspace(tmp_path, monkeypatch)
        _second_review_file(ws).unlink()
        codes = {f.code for f in _assess(ws).findings}
        assert codes == {"INDEPENDENT_SECOND_REVIEW_MISSING"}

    def test_a_hand_built_outcome_has_nowhere_to_go(self):
        # The pre-rewrite API accepted a caller-constructed AdjudicationOutcome; nothing here does.
        import inspect

        sig = inspect.signature(assess_review_corpus)
        assert set(sig.parameters) == {
            "reviews_dir",
            "allowlist_path",
            "inventory_path",
            "repository_root",
        }


class TestCanonicalReceiptRoundTrip:
    """One authority: the readiness CLI issues the receipt, ``governance`` verifies it, and the
    execution gate (the consumer) repeats the second-review validation itself."""

    def _verify(self, ws):
        records = {
            p.relative_to(_reviews(ws)).as_posix(): receipt_module.sha256_file(p)
            for p in sorted(_reviews(ws).rglob("*_review.json"))
        }
        return governance.verify_promotion_receipt(
            ws.root,
            review_record_sha256=records,
            live_inputs=receipt_module.live_receipt_inputs(
                inventory=ws.root / receipt_module.DEFAULT_INVENTORY_RELATIVE,
                proposals_dir=ws.root / receipt_module.DEFAULT_PROPOSALS_RELATIVE,
                allowlist=ws.root / receipt_module.DEFAULT_ALLOWLIST_RELATIVE,
            ),
            now=ow.NOW,
        )

    def test_canonical_verifier_accepts_the_cli_receipt(self, tmp_path, monkeypatch):
        ws = ow.build_workspace(tmp_path, monkeypatch)
        verified = self._verify(ws)
        assert verified.payload["schema_version"] == receipt_module.PROMOTION_RECEIPT_SCHEMA
        assert verified.payload["produced_by"] == receipt_module.PROMOTION_RECEIPT_PRODUCER
        assert ws.assess().ready  # the consumer also accepts: receipt verified, RD-043 satisfied

    def test_receipt_covers_the_second_review_bytes(self, tmp_path, monkeypatch):
        ws = ow.build_workspace(tmp_path, monkeypatch)
        payload = json.loads((ws.root / governance.PROMOTION_RECEIPT_RELATIVE).read_text())
        assert any(k.endswith("__second_review.json") for k in payload["review_record_sha256"])

    def test_cli_refuses_to_issue_a_receipt_when_second_review_is_missing(
        self, tmp_path, monkeypatch
    ):
        from railway_detection.annotation.readiness_cli import main

        ws = ow.build_workspace(tmp_path, monkeypatch)
        _second_review_file(ws).unlink()
        target = tmp_path / "new_receipt.json"
        code = main(
            [
                "--reviews-dir",
                str(_reviews(ws)),
                "--allowlist",
                str(ws.root / receipt_module.DEFAULT_ALLOWLIST_RELATIVE),
                "--inventory",
                str(ws.root / receipt_module.DEFAULT_INVENTORY_RELATIVE),
                "--proposals-dir",
                str(ws.root / receipt_module.DEFAULT_PROPOSALS_RELATIVE),
                "--repository-root",
                str(ws.root),
                "--receipt-path",
                str(target),
            ]
        )
        assert code == 2 and not target.exists()

    def test_a_forged_self_consistent_receipt_cannot_hide_a_missing_second_review(
        self, tmp_path, monkeypatch
    ):
        ws = ow.build_workspace(tmp_path, monkeypatch)
        _second_review_file(ws).unlink()
        path = ws.root / governance.PROMOTION_RECEIPT_RELATIVE
        forged = json.loads(path.read_text())
        forged["review_record_sha256"] = {
            p.relative_to(_reviews(ws)).as_posix(): receipt_module.sha256_file(p)
            for p in sorted(_reviews(ws).rglob("*_review.json"))
        }
        forged["receipt_sha256"] = receipt_module.receipt_body_sha256(forged)
        path.write_text(json.dumps(forged), encoding="utf-8")
        self._verify(ws)  # the receipt is internally consistent and bound to live bytes ...
        assert "INDEPENDENT_SECOND_REVIEW_MISSING" in ws.assess().blocker_codes  # ... but refused

    def test_editing_a_record_after_issue_voids_the_receipt(self, tmp_path, monkeypatch):
        ws = ow.build_workspace(tmp_path, monkeypatch)
        victim = _second_review_file(ws)
        record = json.loads(victim.read_text())
        record["general_review_notes"] = "edited after issue"
        victim.write_text(json.dumps(record), encoding="utf-8")
        assert "STAGE21_PROMOTION_RECEIPT_INVALID" in ws.assess().blocker_codes

    def test_a_disagreeing_second_review_blocks_the_consumer(self, tmp_path, monkeypatch):
        ws = ow.build_workspace(tmp_path, monkeypatch)
        victim = _second_review_file(ws)
        record = json.loads(victim.read_text())
        record["boundary_adjudications"]["T4_tail_clearance"]["value_s"] += 0.5
        victim.write_text(json.dumps(record), encoding="utf-8")
        assert "SECOND_REVIEW_DISAGREEMENT_UNRESOLVED" in ws.assess().blocker_codes

    def test_receipt_digest_is_stable_for_identical_inputs(self, tmp_path, monkeypatch):
        ws = ow.build_workspace(tmp_path, monkeypatch)
        payload = json.loads((ws.root / governance.PROMOTION_RECEIPT_RELATIVE).read_text())
        assert payload["receipt_sha256"] == receipt_module.receipt_body_sha256(payload)
        assert hashlib.sha256  # imported for symmetry with the verifier
