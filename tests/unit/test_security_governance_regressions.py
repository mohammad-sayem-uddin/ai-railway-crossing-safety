"""Mission 14 (WP14.8): governance-gate regressions with a synthetic-only test path.

These tests distinguish what the code *implements* from what governance has *adopted*.  They create
no authorization, receipt or approval in the repository: every artifact lives in a temporary tree
and is a deliberately fake fixture.  RD-043 and the other directional decisions are not treated as
adopted anywhere here.

Coverage that already existed in the safe set (and is only referenced, not duplicated, here):
reviewer allowlist loading, non-allowlisted reviewers, duplicate / same-reviewer second review and
missing second review live in ``tests/test_mission4b_review_operations.py``,
``tests/test_mission10_second_review.py`` and ``tests/test_phase11_12_readiness_gate.py``; media
and descriptive authorization expiry, revocation, scope and signer checks live in
``tests/unit/test_media_authorization.py`` and ``tests/unit/test_descriptive_exec_gate.py``.
``test_referenced_safe_set_tests_still_exist`` fails if any of them is renamed or deleted.
"""

from __future__ import annotations

import ast
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from security_support import outside_dir  # noqa: E402

from railway_detection.annotation.promotion_gate import (  # noqa: E402
    AuthorizedReviewersLoadError,
    load_authorized_reviewers,
)
from railway_detection.annotation.receipt import receipt_body_sha256  # noqa: E402
from railway_detection.evaluation import descriptive_exec_gate as descriptive  # noqa: E402
from railway_detection.evaluation import governance  # noqa: E402
from railway_detection.safety import media_guard  # noqa: E402

TESTS = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 2, tzinfo=UTC)
REVIEW = {"train_events/event_001_review.json": "a" * 64}
INPUTS = {"allowlist_sha256": "b" * 64, "inventory_sha256": "c" * 64}


def make_receipt(**override) -> dict:
    receipt = {
        "schema_version": governance.PROMOTION_RECEIPT_SCHEMA,
        "produced_by": governance.PROMOTION_RECEIPT_PRODUCER,
        "produced_at_utc": "2026-10-01T00:00:00Z",
        "verdict": {"ready": True, "blocker_count": 0},
        "media_hashes_verified_live": True,
        "stage": "stage-2.1",
        "review_record_sha256": dict(REVIEW),
        "inputs": dict(INPUTS),
    }
    receipt.update(override)
    receipt["receipt_sha256"] = receipt_body_sha256(receipt)
    return receipt


def verify(tmp_path_factory, receipt: dict, *, review=None, live=None, now=NOW):
    root = outside_dir(tmp_path_factory, "receipt_root")
    path = root / governance.PROMOTION_RECEIPT_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return governance.verify_promotion_receipt(
        root,
        review_record_sha256=REVIEW if review is None else review,
        live_inputs=INPUTS if live is None else live,
        now=now,
    )


def refused(tmp_path_factory, receipt: dict, **kw) -> governance.GovernanceError:
    with pytest.raises(governance.GovernanceError) as info:
        verify(tmp_path_factory, receipt, **kw)
    assert info.value.code == "STAGE21_PROMOTION_RECEIPT_INVALID"
    return info.value


# ------------------------------------------------------------------ promotion receipt


def test_a_consistent_receipt_is_accepted(tmp_path_factory):
    assert verify(tmp_path_factory, make_receipt()).payload["verdict"]["ready"] is True


def test_missing_receipt_is_its_own_code(tmp_path_factory):
    root = outside_dir(tmp_path_factory, "no_receipt")
    with pytest.raises(governance.GovernanceError) as info:
        governance.verify_promotion_receipt(
            root, review_record_sha256=REVIEW, live_inputs=INPUTS, now=NOW
        )
    assert info.value.code == "STAGE21_PROMOTION_RECEIPT_MISSING"


def test_forged_receipt_with_a_wrong_self_hash_is_refused(tmp_path_factory):
    receipt = make_receipt()
    receipt["receipt_sha256"] = "0" * 64
    assert "receipt_sha256" in refused(tmp_path_factory, receipt).detail
    receipt = make_receipt()
    receipt["verdict"]["blocker_count"] = 0
    receipt["stage"] = "tampered-after-hashing"
    assert "receipt_sha256" in refused(tmp_path_factory, receipt).detail


def test_wrong_review_record_hash_names_the_changed_record(tmp_path_factory):
    receipt = make_receipt(review_record_sha256={"train_events/event_001_review.json": "d" * 64})
    assert "event_001_review.json" in refused(tmp_path_factory, receipt).detail
    extra = dict(REVIEW, **{"train_events/event_002_review.json": "e" * 64})
    assert "event_002_review.json" in refused(tmp_path_factory, make_receipt(), review=extra).detail


def test_wrong_bound_input_is_stale(tmp_path_factory):
    live = dict(INPUTS, allowlist_sha256="f" * 64)
    assert "allowlist_sha256" in refused(tmp_path_factory, make_receipt(), live=live).detail
    missing = dict(INPUTS, inventory_sha256=None)
    assert "inventory_sha256" in refused(tmp_path_factory, make_receipt(), live=missing).detail
    narrower = {"allowlist_sha256": INPUTS["allowlist_sha256"]}
    assert "must bind exactly" in refused(tmp_path_factory, make_receipt(), live=narrower).detail


@pytest.mark.parametrize(
    "override",
    [
        {"produced_by": "someone.else"},
        {"schema_version": "phase12-stage21-promotion-receipt/1"},
        {"verdict": {"ready": False, "blocker_count": 0}},
        {"verdict": {"ready": True, "blocker_count": 2}},
        {"verdict": "READY"},
        {"media_hashes_verified_live": False},
        {"stage": "  "},
        {"review_record_sha256": {}},
        {"review_record_sha256": {"x_review.json": "not-a-digest"}},
        {"produced_at_utc": "2027-01-01T00:00:00Z"},
        {"produced_at_utc": "yesterday"},
    ],
)
def test_invalid_receipt_shapes_are_refused(tmp_path_factory, override):
    refused(tmp_path_factory, make_receipt(**override))


def test_receipt_is_tamper_evident_only_a_hand_computed_one_passes():
    """Documents the disclosed trust model: the self-hash has no secret (not a signature)."""
    receipt = make_receipt()
    body = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    assert receipt["receipt_sha256"] == receipt_body_sha256(body)  # anyone can compute this


def test_receipt_has_no_age_limit_or_revocation_today_documented_gap(tmp_path_factory):
    """Mission 13 F13-10. Pinned deliberately: change this test only when governance decides to
    add an expiry/revocation field to the receipt schema."""
    ancient = make_receipt(produced_at_utc="2021-01-01T00:00:00Z")
    assert verify(tmp_path_factory, ancient)
    revoked = make_receipt(revoked=True)  # an unknown field is simply not part of the schema
    assert verify(tmp_path_factory, revoked)


# --------------------------------------------- schemas: what expiry/revocation fields exist


def test_eval_auth_schema_has_no_expiry_or_revocation_fields():
    """Mission 13 corrected Mission 12: EVAL-AUTH has *no* expires/revoked/status field."""
    for field in ("expires_at_utc", "revoked", "status"):
        assert field not in governance._EVAL_AUTH_KEYS, field
    assert "authorized_by" in governance._EVAL_AUTH_KEYS
    assert "bindings" in governance._EVAL_AUTH_KEYS


def test_media_and_descriptive_authorizations_do_carry_expiry_and_revocation():
    for keys in (media_guard._AUTH_KEYS, descriptive._KEYS):
        assert {"expires_at_utc", "revoked", "status", "authorized_by"} <= set(keys)


def test_eval_auth_bindings_cover_the_documented_artifacts():
    assert set(governance.EVAL_AUTH_BINDING_KEYS) == {
        "decision_policy_sha256",
        "event_split_decision_sha256",
        "frozen_config_sha256",
        "input_manifest_sha256",
        "protocol_profile_sha256",
        "r04_scope_decision_sha256",
        "stage21_promotion_receipt_sha256",
    }


def test_missing_eval_auth_is_refused_and_never_inferred_from_flags(tmp_path_factory):
    root = outside_dir(tmp_path_factory, "no_eval_auth")
    with pytest.raises(governance.GovernanceError) as info:
        governance.verify_eval_authorization(
            root, allowlist=frozenset({"x"}), live_bindings={}, promotion_stage=None, now=NOW
        )
    assert info.value.code == "EVAL_AUTH_NOT_GRANTED"


# ------------------------------------------------------------------- reviewer allowlist


def write_allowlist(path: Path, payload) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_allowlist_rejects_duplicates_blanks_and_empty_lists(tmp_path_factory):
    root = outside_dir(tmp_path_factory, "allowlist")
    good = write_allowlist(root / "good.json", {"authorized_reviewers": ["a@x.test", "b@x.test"]})
    assert load_authorized_reviewers(good) == frozenset({"a@x.test", "b@x.test"})
    for name, payload in {
        "dup": {"authorized_reviewers": ["a@x.test", "a@x.test"]},
        "empty": {"authorized_reviewers": []},
        "blank": {"authorized_reviewers": ["a@x.test", "  "]},
        "shape": ["a@x.test"],
        "notlist": {"authorized_reviewers": "a@x.test"},
    }.items():
        with pytest.raises(AuthorizedReviewersLoadError):
            load_authorized_reviewers(write_allowlist(root / f"{name}.json", payload))
    with pytest.raises(AuthorizedReviewersLoadError):
        load_authorized_reviewers(root / "absent.json")


def test_duplicate_reviewers_cannot_widen_the_set_by_case_or_whitespace(tmp_path_factory):
    root = outside_dir(tmp_path_factory, "allowlist_case")
    allowlist = load_authorized_reviewers(
        write_allowlist(root / "list.json", {"authorized_reviewers": ["a@x.test", "b@x.test"]})
    )
    assert "A@X.TEST" not in allowlist and " a@x.test" not in allowlist


# ------------------------------------------------------- referenced coverage still exists

REFERENCED = {
    "test_mission4b_review_operations.py": [
        "test_allowlist_rejects_duplicate_revoked_blocklisted_and_missing",
        "test_second_review_requires_distinct_reviewer_and_missing_second_review_blocks",
    ],
    "test_mission10_second_review.py": [
        "test_triggered_record_without_a_second_review_is_a_blocker",
        "test_same_reviewer_cannot_second_review_their_own_record",
        "test_case_variant_of_same_identity_is_not_independent",
        "test_second_reviewer_must_be_allowlisted",
        "test_non_approved_second_review_does_not_count",
        "test_disagreement_stays_unresolved_and_no_tolerance_is_applied",
    ],
    "test_phase11_12_readiness_gate.py": [
        "test_unallowlisted_reviewer_blocks_readiness",
        "test_duplicate_approved_event_blocks_readiness",
        "test_missing_allowlist_fails_closed",
    ],
    "unit/test_media_authorization.py": [
        "test_valid_record_authorizes_exactly_its_scope",
        "test_all_events_scope_allows_any_event_in_the_dataset",
        "test_per_event_scope_with_undeterminable_event_is_denied",
        "test_authorization_not_covering_the_operation_still_blocks_the_opener",
    ],
    "unit/test_descriptive_exec_gate.py": [
        "test_all_manifest_events_scope",
        "test_engine_enforces_the_authorized_condition_scope",
    ],
}


def test_referenced_safe_set_tests_still_exist():
    missing = []
    for relative, names in REFERENCED.items():
        path = TESTS / relative
        defined = {
            node.name
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, ast.FunctionDef)
        }
        missing += [f"{relative}::{name}" for name in names if name not in defined]
    assert missing == []
