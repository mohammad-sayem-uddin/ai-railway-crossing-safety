"""Governance verification for official Phase 12 readiness (synthetic fixtures only).

These tests build a self-contained synthetic repository root under pytest's tmp
directory. They never read, write or hash the real review records, frozen
configurations, checkpoints or the tracked experiment registry, and they
assert (against the real repository) that gate assessment leaves those files
byte-identical.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from railway_detection.annotation.readiness_cli import main as readiness_main
from railway_detection.evaluation import execution_gate, governance, protocol_choices
from railway_detection.evaluation.execution_gate import assess_official_phase12_readiness
from railway_detection.evaluation.output_contracts import canonical_json_bytes
from second_review_support import SECOND_REVIEWER, write_verifiable_proposal
from test_phase11_9_synthetic_pilot import PILOT_REVIEWER, SYNTHETIC_EVENTS, VALID_PROPOSAL_SHA
from test_phase11_12_readiness_gate import _three_records

REPO_ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 12, 1, tzinfo=UTC)
CONFIG_HASH = "c" * 64
PREMATURE = {"premature_opening_window": "t1_entry_to_t4_clearance"}  # fixture-only choice
GT_EVENTS = [f"{event['cohort']}/{event['event_id']}" for event in SYNTHETIC_EVENTS]
COHORT_OF = {
    f"{event['cohort']}/{event['event_id']}": event["cohort"] for event in SYNTHETIC_EVENTS
}
EVENTS = {"train": ["train_events/evt_a"], "val": ["train_events/evt_b"], "test": list(GT_EVENTS)}
SCOPE = {event_id: "single_camera" for ids in EVENTS.values() for event_id in ids}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def _envelope(schema: str, **body: object) -> dict:
    return {
        "schema_version": schema,
        "decision_status": "APPROVED",
        "decision_id": f"dec-{schema.split('/')[0]}",
        "decided_by": PILOT_REVIEWER,
        "decided_at_utc": "2026-01-14T10:00:00Z",
        "researcher_statement": "Synthetic fixture statement (test only).",
        **body,
    }


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A synthetic repository root in which every prerequisite is genuinely satisfied."""
    root = tmp_path / "repo"
    ground_truth = root / "data/ground_truth"
    _write_json(
        ground_truth / "authorized_reviewers.json",
        {"authorized_reviewers": [PILOT_REVIEWER, SECOND_REVIEWER]},
    )

    # Synthetic Stage-2.1 records produced by the real builder.
    (tmp_path / "media").mkdir()
    records, _active, _registry, paths = _three_records(tmp_path / "media")
    proposals = root / "data/ground_truth/proposals"
    inventory_path = root / "data/manifests/layer_b_v2_annotation_inventory.json"
    reviews = ground_truth / "reviews"
    for record in records:
        proposal = proposals / record["cohort"] / f"{record['event_id']}_proposal_v1.json"
        proposal.parent.mkdir(parents=True, exist_ok=True)
        record["proposal_reference"]["proposal_sha256"] = write_verifiable_proposal(
            proposal, record
        )
        _write_json(reviews / record["cohort"] / f"{record['review_id']}_review.json", record)
    inventory: dict[str, dict] = {}
    for record in records:
        entry = {"category": record["cohort"], "event_id": record["event_id"]}
        for side in ("front", "back"):
            media = Path(paths[record["event_id"]][side])
            entry[side] = {
                "path": str(media),
                "sha256": hashlib.sha256(media.read_bytes()).hexdigest(),
            }
        inventory[f"{record['cohort']}/{record['event_id']}"] = entry
    for extra in ("evt_a", "evt_b"):  # fixture events without records (train/val)
        inventory[f"train_events/{extra}"] = {
            "category": "train_events",
            "event_id": extra,
            "front": {"path": "x", "sha256": "a" * 64},
            "back": {"path": "y", "sha256": "b" * 64},
        }
    _write_json(inventory_path, inventory)

    # The media-hashing readiness CLI (a separate, authorized workflow) issues the receipt.
    code = readiness_main(
        [
            "--reviews-dir", str(reviews),
            "--allowlist", str(ground_truth / "authorized_reviewers.json"),
            "--inventory", str(inventory_path),
            "--proposals-dir", str(proposals),
            "--stage", "synthetic_stage",
            "--repository-root", str(root),
            "--receipt-path", str(root / governance.PROMOTION_RECEIPT_RELATIVE),
        ]
    )
    assert code == 0

    _write_json(
        root / governance.SPLIT_DECISION_RELATIVE,
        _envelope(governance.SPLIT_DECISION_SCHEMA, partitions=EVENTS),
    )
    _write_json(
        root / governance.R04_DECISION_RELATIVE,
        _envelope(
            governance.R04_DECISION_SCHEMA, event_modes=SCOPE, accepted_sync_events=[]
        ),
    )
    # Fixture-only: a researcher choice for the one decision with no documented default.
    _write_json(
        root / governance.PROTOCOL_DECISION_RELATIVE,
        _envelope(governance.PROTOCOL_DECISION_SCHEMA, choices=dict(PREMATURE)),
    )
    events = []
    for role, ids in EVENTS.items():
        for event_id in ids:
            source = root / "data/manifests" / f"src_{event_id.replace('/', '__')}.json"
            source.write_bytes(json.dumps({"event_id": event_id}).encode())
            events.append(
                {
                    "event_id": event_id,
                    "cohort": COHORT_OF.get(event_id, "train_events"),
                    "split_role": role,
                    "source_path": source.name,
                    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                }
            )
    _write_json(
        root / "data/manifests/phase12_evaluation_inputs.json",
        {
            "schema_version": "phase12-evaluation-inputs/1",
            "evidence_classification": "real",
            "partitions": EVENTS,
            "events": events,
            "camera_scope_by_event": SCOPE,
            "accepted_sync_events": [],
        },
    )

    # Frozen config / policy / checkpoints are protected real files; use stand-ins.
    policy = root / "configs/decision_policy_v1.yaml"
    policy.parent.mkdir(parents=True)
    policy.write_text(
        f"policy_metadata:\n  reference_frozen_config_sha256: '{CONFIG_HASH}'\n",
        encoding="utf-8",
    )
    (root / "configs/frozen_experiment_v1.yaml").write_text("stand_in: true\n", encoding="utf-8")
    monkeypatch.setattr(
        execution_gate, "load_frozen_config", lambda _path: SimpleNamespace(config_hash=CONFIG_HASH)
    )
    monkeypatch.setattr(execution_gate, "verify_checkpoint_integrity", lambda *a, **k: None)
    monkeypatch.setattr(execution_gate, "verify_timing_safeguards", lambda *a, **k: None)
    return root


def _assess(root: Path):
    return assess_official_phase12_readiness(root, now=NOW)


def _record_authorization(root: Path, **overrides: object) -> dict:
    """Record an EVAL-AUTH the way a researcher would: bind to the live evidence."""
    live = _assess(root).live_bindings
    record = {
        "schema_version": governance.EVAL_AUTH_SCHEMA,
        "authorization_id": "auth-synthetic-1",
        "stage": "synthetic_stage",
        "authorized_by": PILOT_REVIEWER,
        "authorized_at_utc": "2026-01-15T12:00:00Z",
        "authorization_statement": "Synthetic fixture statement (test only).",
        "attestation": {"type": governance.ATTESTATION_RECORDED_STATEMENT, "signature": None},
        "recorded_by": {"kind": "researcher", "identity": PILOT_REVIEWER},
        "scope": {
            "operation": governance.AUTHORIZED_OPERATION,
            "stage": "synthetic_stage",
            "field_or_physical_operations_authorized": False,
        },
        "bindings": dict(live),
    }
    record.update(overrides)
    record["record_sha256"] = governance.canonical_record_sha256(record)
    _write_json(root / governance.EVAL_AUTH_RELATIVE, record)
    return record


def _rewrite_auth(root: Path, mutate) -> None:
    path = root / governance.EVAL_AUTH_RELATIVE
    record = json.loads(path.read_text())
    mutate(record)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _rehash_auth(root: Path, mutate) -> None:
    def both(record: dict) -> None:
        mutate(record)
        record["record_sha256"] = governance.canonical_record_sha256(record)

    _rewrite_auth(root, both)


# --- the positive path: valid existing evidence is recognized -------------------


def test_every_prerequisite_without_authorization_blocks_only_on_eval_auth(workspace: Path):
    verdict = _assess(workspace)
    assert verdict.blocker_codes == ("EVAL_AUTH_NOT_GRANTED",), verdict.blockers
    assert all(value is not None for value in verdict.live_bindings.values())
    assert any("promotion receipt verified" in item for item in verdict.evidence)


def test_recorded_authorization_bound_to_live_evidence_is_recognized(workspace: Path):
    _record_authorization(workspace)
    verdict = _assess(workspace)
    assert verdict.ready, verdict.blockers
    payload = verdict.to_dict()
    assert payload["authorization_verified"] is True
    assert payload["authorization_attestation_level"] == "recorded_statement_unsigned"
    assert payload["authorization_is_cryptographic"] is False
    assert any("not a cryptographic attestation" in item for item in verdict.evidence)


# --- forged or tampered authorization cannot authorize ---------------------------


@pytest.mark.parametrize("flag", ["ready", "approved", "eval_auth", "authorized"])
def test_forged_flag_fields_in_authorization_are_refused(workspace: Path, flag: str):
    _record_authorization(workspace)
    _rehash_auth(workspace, lambda record: record.__setitem__(flag, True))
    verdict = _assess(workspace)
    assert not verdict.ready
    assert "EVAL_AUTH_INVALID" in verdict.blocker_codes


def test_flag_only_authorization_file_never_authorizes(workspace: Path):
    _write_json(workspace / governance.EVAL_AUTH_RELATIVE, {"eval_auth": True, "ready": True})
    verdict = _assess(workspace)
    assert not verdict.ready
    assert "EVAL_AUTH_INVALID" in verdict.blocker_codes


def test_authorizer_must_be_on_allowlist(workspace: Path):
    _record_authorization(workspace, authorized_by="some.agent@example.com")
    verdict = _assess(workspace)
    assert "EVAL_AUTH_INVALID" in verdict.blocker_codes
    assert any("allowlist" in b.detail for b in verdict.blockers)


def test_edited_statement_breaks_record_hash(workspace: Path):
    _record_authorization(workspace)
    _rewrite_auth(
        workspace, lambda record: record.__setitem__("authorization_statement", "edited later")
    )
    verdict = _assess(workspace)
    assert any(
        b.code == "EVAL_AUTH_INVALID" and "record_sha256" in b.detail for b in verdict.blockers
    )


@pytest.mark.parametrize(
    "attestation",
    [
        {"type": "ED25519", "signature": "AAAA"},
        {"type": governance.ATTESTATION_RECORDED_STATEMENT, "signature": "AAAA"},
        {"type": governance.ATTESTATION_RECORDED_STATEMENT},
        "signed",
    ],
)
def test_signature_style_attestations_are_refused_not_trusted(workspace: Path, attestation):
    _record_authorization(workspace, attestation=attestation)
    verdict = _assess(workspace)
    assert not verdict.ready
    assert "EVAL_AUTH_ATTESTATION_UNSUPPORTED" in verdict.blocker_codes


def test_authorization_can_never_cover_physical_operations(workspace: Path):
    _record_authorization(
        workspace,
        scope={
            "operation": governance.AUTHORIZED_OPERATION,
            "stage": "synthetic_stage",
            "field_or_physical_operations_authorized": True,
        },
    )
    assert "EVAL_AUTH_INVALID" in _assess(workspace).blocker_codes


def test_future_dated_authorization_is_refused(workspace: Path):
    _record_authorization(workspace, authorized_at_utc="2999-06-01T00:00:00Z")
    assert "EVAL_AUTH_INVALID" in _assess(workspace).blocker_codes


def test_agent_transcription_requires_a_source(workspace: Path):
    _record_authorization(
        workspace, recorded_by={"kind": "agent_transcription", "identity": "agent"}
    )
    assert "EVAL_AUTH_INVALID" in _assess(workspace).blocker_codes
    _record_authorization(
        workspace,
        recorded_by={
            "kind": "agent_transcription",
            "identity": "agent",
            "transcription_source": "researcher chat message, session of 2026-01-15",
        },
    )
    verdict = _assess(workspace)
    assert verdict.ready
    assert any("recorded_by=agent_transcription" in item for item in verdict.evidence)


def test_stage_must_match_the_promotion_receipt(workspace: Path):
    _record_authorization(
        workspace,
        stage="another_stage",
        scope={
            "operation": governance.AUTHORIZED_OPERATION,
            "stage": "another_stage",
            "field_or_physical_operations_authorized": False,
        },
    )
    assert "EVAL_AUTH_INVALID" in _assess(workspace).blocker_codes


@pytest.mark.parametrize(
    "mutation",
    [
        lambda root: _write_json(
            root / governance.SPLIT_DECISION_RELATIVE,
            _envelope(
                governance.SPLIT_DECISION_SCHEMA,
                decision_id="reissued",
                partitions=EVENTS,
            ),
        ),
        lambda root: (root / "configs/decision_policy_v1.yaml").write_text(
            f"policy_metadata:\n  reference_frozen_config_sha256: '{CONFIG_HASH}'\n# edited\n",
            encoding="utf-8",
        ),
        lambda root: _write_json(
            root / governance.PROTOCOL_DECISION_RELATIVE,
            _envelope(
                governance.PROTOCOL_DECISION_SCHEMA,
                choices={**PREMATURE, "false_alarm_measure": "event_level_any_closure"},
            ),
        ),
    ],
    ids=["split", "policy", "protocol"],
)
def test_changing_any_bound_evidence_voids_the_authorization(workspace: Path, mutation):
    _record_authorization(workspace)
    assert _assess(workspace).ready
    mutation(workspace)
    verdict = _assess(workspace)
    assert not verdict.ready
    assert "EVAL_AUTH_BINDING_MISMATCH" in verdict.blocker_codes


def test_authorization_with_missing_prerequisite_reports_unverifiable_binding(workspace: Path):
    _record_authorization(workspace)
    (workspace / governance.R04_DECISION_RELATIVE).unlink()
    verdict = _assess(workspace)
    assert "R04_SCOPE_DECISION_MISSING" in verdict.blocker_codes
    assert "EVAL_AUTH_BINDING_UNVERIFIABLE" in verdict.blocker_codes
    assert verdict.to_dict()["authorization_verified"] is False


# --- decision artifacts ------------------------------------------------------------


@pytest.mark.parametrize(
    ("relative", "invalid_code"),
    [
        (governance.SPLIT_DECISION_RELATIVE, "EVENT_SPLIT_DECISION_INVALID"),
        (governance.R04_DECISION_RELATIVE, "R04_SCOPE_DECISION_INVALID"),
        (governance.PROTOCOL_DECISION_RELATIVE, "PROTOCOL_DECISION_INVALID"),
    ],
)
def test_decision_artifacts_reject_forged_authority_and_missing_statements(
    workspace: Path, relative: Path, invalid_code: str
):
    path = workspace / relative
    if relative == governance.PROTOCOL_DECISION_RELATIVE:
        _write_json(
            path,
            _envelope(
                governance.PROTOCOL_DECISION_SCHEMA,
                choices={**PREMATURE, "false_alarm_measure": "event_level_any_closure"},
            ),
        )
    original = json.loads(path.read_text())
    for field, value in (
        ("decided_by", "model-generated@example.com"),
        ("researcher_statement", "  "),
        ("decision_status", "PENDING"),
        ("decided_at_utc", "2999-01-01T00:00:00Z"),
        ("decided_at_utc", "2026-01-14T10:00:00"),
    ):
        broken = copy.deepcopy(original)
        broken[field] = value
        _write_json(path, broken)
        assert invalid_code in _assess(workspace).blocker_codes, (field, value)
    _write_json(path, original)
    assert invalid_code not in _assess(workspace).blocker_codes


def test_premature_opening_window_has_no_default_and_blocks_until_decided(workspace: Path):
    (workspace / governance.PROTOCOL_DECISION_RELATIVE).unlink()
    verdict = _assess(workspace)
    assert "PREMATURE_OPENING_DEFINITION_UNDECIDED" in verdict.blocker_codes
    assert verdict.live_bindings["protocol_profile_sha256"] is None
    blocker = next(
        b for b in verdict.blockers if b.code == "PREMATURE_OPENING_DEFINITION_UNDECIDED"
    )
    assert blocker.category == "MISSING_RESEARCH_DECISION"
    assert "PREMATURE_OPENING_DECISION_EVIDENCE" in blocker.remedy


def test_override_naming_other_decisions_does_not_settle_premature_opening(workspace: Path):
    _write_json(
        workspace / governance.PROTOCOL_DECISION_RELATIVE,
        _envelope(
            governance.PROTOCOL_DECISION_SCHEMA,
            choices={"false_alarm_measure": "event_level_any_closure"},
        ),
    )
    assert "PREMATURE_OPENING_DEFINITION_UNDECIDED" in _assess(workspace).blocker_codes


def test_documented_values_fill_every_other_decision(workspace: Path):
    verdict = _assess(workspace)
    profile = protocol_choices.effective_profile(
        {"premature_opening_window": "t1_entry_to_t4_clearance"}
    )
    assert profile["continuous_metric_weighting"] == "event_weighted"
    assert verdict.live_bindings["protocol_profile_sha256"] == protocol_choices.profile_sha256(
        profile
    )
    assert "PROTOCOL_DECISION_INVALID" not in verdict.blocker_codes


def test_valid_override_changes_the_bound_profile(workspace: Path):
    before = _assess(workspace).live_bindings["protocol_profile_sha256"]
    _write_json(
        workspace / governance.PROTOCOL_DECISION_RELATIVE,
        _envelope(
            governance.PROTOCOL_DECISION_SCHEMA,
            choices={**PREMATURE, "false_alarm_measure": "event_level_any_closure"},
        ),
    )
    verdict = _assess(workspace)
    assert verdict.blocker_codes == ("EVAL_AUTH_NOT_GRANTED",)
    assert verdict.live_bindings["protocol_profile_sha256"] != before
    assert any("researcher override" in e for e in verdict.evidence)


@pytest.mark.parametrize(
    ("choices", "code"),
    [
        ({"continuous_metric_weighting": "exposure_time_weighted"},
         "PROTOCOL_CHOICE_NOT_IMPLEMENTED"),
        ({"premature_opening_window": "t0_first_visible_to_t4_clearance"},
         "PROTOCOL_CHOICE_NOT_IMPLEMENTED"),
        ({"censoring_treatment": "report_censored_as_bounds"}, "PROTOCOL_CHOICE_NOT_IMPLEMENTED"),
        ({"premature_opening_window": "made_up"}, "PROTOCOL_DECISION_INVALID"),
        ({"unknown_decision": "x"}, "PROTOCOL_DECISION_INVALID"),
        ({}, "PROTOCOL_DECISION_INVALID"),
    ],
)
def test_an_override_the_evaluator_cannot_honor_is_refused_not_degraded(
    workspace: Path, choices: dict, code: str
):
    _write_json(
        workspace / governance.PROTOCOL_DECISION_RELATIVE,
        _envelope(governance.PROTOCOL_DECISION_SCHEMA, choices=choices),
    )
    verdict = _assess(workspace)
    assert code in verdict.blocker_codes
    assert verdict.live_bindings["protocol_profile_sha256"] is None


def test_manifest_must_realize_the_researcher_split(workspace: Path):
    path = workspace / "data/manifests/phase12_evaluation_inputs.json"
    manifest = json.loads(path.read_text())
    manifest["partitions"] = {
        "train": ["train_events/evt_a", "train_events/evt_b"],
        "val": [GT_EVENTS[0]],
        "test": GT_EVENTS[1:],
    }
    roles = {"train_events/evt_a": "train", "train_events/evt_b": "train", GT_EVENTS[0]: "val"}
    for event in manifest["events"]:
        event["split_role"] = roles.get(event["event_id"], "test")
    _write_json(path, manifest)
    assert "INPUT_MANIFEST_DECISION_MISMATCH" in _assess(workspace).blocker_codes


def test_synthetic_manifest_can_never_satisfy_official_readiness(workspace: Path):
    path = workspace / "data/manifests/phase12_evaluation_inputs.json"
    manifest = json.loads(path.read_text())
    manifest["evidence_classification"] = "synthetic"
    _write_json(path, manifest)
    _record_authorization(workspace)
    verdict = _assess(workspace)
    assert not verdict.ready
    assert "SYNTHETIC_INPUTS_NOT_OFFICIAL" in verdict.blocker_codes


# --- Stage-2.1 evidence and the promotion receipt ---------------------------------


def test_receipt_is_bound_to_the_exact_review_record_bytes(workspace: Path):
    record_path = next((workspace / "data/ground_truth/reviews").rglob("*_review.json"))
    record = json.loads(record_path.read_text())
    record["general_review_notes"] = "touched after the receipt was issued"
    _write_json(record_path, record)
    verdict = _assess(workspace)
    assert "STAGE21_PROMOTION_RECEIPT_INVALID" in verdict.blocker_codes


def test_missing_receipt_blocks_even_when_records_are_valid(workspace: Path):
    (workspace / governance.PROMOTION_RECEIPT_RELATIVE).unlink()
    assert "STAGE21_PROMOTION_RECEIPT_MISSING" in _assess(workspace).blocker_codes


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r["verdict"].__setitem__("ready", False),
        lambda r: r["verdict"].__setitem__("blocker_count", 2),
        lambda r: r.__setitem__("produced_by", "someone_else"),
        lambda r: r.__setitem__("allowlist_sha256", "0" * 64),
        lambda r: r.__setitem__("review_record_sha256", {}),
    ],
)
def test_forged_receipt_fields_are_refused(workspace: Path, mutate):
    path = workspace / governance.PROMOTION_RECEIPT_RELATIVE
    receipt = json.loads(path.read_text())
    mutate(receipt)
    _write_json(path, receipt)
    assert "STAGE21_PROMOTION_RECEIPT_INVALID" in _assess(workspace).blocker_codes


def test_readiness_cli_never_writes_a_receipt_when_not_ready(tmp_path: Path, workspace: Path):
    reviews = workspace / "data/ground_truth/reviews"
    victim = next(reviews.rglob("*_review.json"))
    record = json.loads(victim.read_text())
    record["adjudication_status"] = "DISPUTED"
    _write_json(victim, record)
    receipt = tmp_path / "out" / "receipt.json"
    code = readiness_main(
        [
            "--reviews-dir", str(reviews),
            "--allowlist", str(workspace / "data/ground_truth/authorized_reviewers.json"),
            "--inventory", str(workspace / "data/manifests/layer_b_v2_annotation_inventory.json"),
            "--proposals-dir", str(workspace / "data/ground_truth/proposals"),
            "--receipt-path", str(receipt),
        ]
    )
    assert code == 2
    assert not receipt.exists()


def test_readiness_cli_refuses_a_receipt_inside_the_review_tree(tmp_path: Path, workspace: Path):
    reviews = workspace / "data/ground_truth/reviews"
    before = {p: p.read_bytes() for p in reviews.rglob("*") if p.is_file()}
    code = readiness_main(
        [
            "--reviews-dir", str(reviews),
            "--allowlist", str(workspace / "data/ground_truth/authorized_reviewers.json"),
            "--inventory", str(workspace / "data/manifests/layer_b_v2_annotation_inventory.json"),
            "--proposals-dir", str(workspace / "data/ground_truth/proposals"),
            "--receipt-path", str(reviews / "receipt.json"),
        ]
    )
    assert code == 1
    assert {p: p.read_bytes() for p in reviews.rglob("*") if p.is_file()} == before


def test_legacy_records_cannot_be_rescued_by_any_authorization(workspace: Path):
    legacy = {
        "schema_version": "6.0.0",
        "event_id": "event_001",
        "adjudication_status": "APPROVED",
        "reviewer_metadata": {"reviewer_id": "human_researcher_lead"},
    }
    _write_json(workspace / "data/ground_truth/reviews/train_events/event_001_review.json", legacy)
    _record_authorization(workspace)
    verdict = _assess(workspace)
    assert not verdict.ready
    assert "LEGACY_OR_UNKNOWN_GROUND_TRUTH_SCHEMA" in verdict.blocker_codes
    detail = next(
        b.detail for b in verdict.blockers if b.code == "LEGACY_OR_UNKNOWN_GROUND_TRUTH_SCHEMA"
    )
    assert "train_events/event_001_review.json" in detail
    assert "REVIEWER_ID_BLOCKLIST" in detail


# --- diagnostics ----------------------------------------------------------------------


def test_same_event_id_in_different_cohorts_is_not_collapsed(tmp_path: Path):
    reviews = tmp_path / "data/ground_truth/reviews"
    for cohort in ("train_events", "no_train_events", "engine_events"):
        _write_json(
            reviews / cohort / "event_001_review.json",
            {"schema_version": "6.0.0", "event_id": "event_001", "reviewer_id": "x"},
        )
    verdict = assess_official_phase12_readiness(tmp_path, now=NOW)
    legacy = [b for b in verdict.blockers if b.code == "LEGACY_OR_UNKNOWN_GROUND_TRUTH_SCHEMA"]
    assert len(legacy) == 3


def test_every_emitted_blocker_is_classified_with_artifact_and_remedy(tmp_path: Path):
    verdict = assess_official_phase12_readiness(tmp_path, now=NOW)
    assert verdict.blockers
    for blocker in verdict.blockers:
        payload = blocker.to_dict()
        assert payload["category"] != execution_gate.UNCLASSIFIED, blocker.code
        assert payload["required_artifact"] and payload["remedy"], blocker.code
    assert verdict.to_dict()["authorization_verification_available"] is True


def test_catalogue_codes_all_have_complete_entries():
    for code, (category, artifact, remedy) in execution_gate.BLOCKER_CATALOGUE.items():
        assert category and artifact and remedy, code


def test_canonical_record_hash_ignores_only_its_own_field():
    record = {"a": 1, "record_sha256": "x"}
    assert governance.canonical_record_sha256(record) == hashlib.sha256(
        canonical_json_bytes({"a": 1})
    ).hexdigest()
    other = governance.canonical_record_sha256({"a": 2})
    assert other != governance.canonical_record_sha256(record)


# --- the real repository stays untouched ------------------------------------------------


def _digest_tree(*relative: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in relative:
        base = REPO_ROOT / item
        paths = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        for path in paths:
            out[str(path.relative_to(REPO_ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def test_assessing_the_real_repository_is_read_only_and_fail_closed():
    protected = (
        "data/ground_truth/reviews",
        "data/ground_truth/authorized_reviewers.json",
        "configs/frozen_experiment_v1.yaml",
        "configs/decision_policy_v1.yaml",
        "results/experiment_registry.jsonl",
    )
    before = _digest_tree(*protected)
    verdict = assess_official_phase12_readiness(REPO_ROOT)
    assert _digest_tree(*protected) == before
    assert not verdict.ready
    # The legacy records are neither promoted nor silently recognised as approvals.
    review_count = len(list((REPO_ROOT / "data/ground_truth/reviews").rglob("*_review.json")))
    legacy = [b for b in verdict.blockers if b.code == "LEGACY_OR_UNKNOWN_GROUND_TRUTH_SCHEMA"]
    # LEG-EXEC has now created verified sibling notices.  The original records
    # remain byte-identical, but verified invalidation notices excuse them from
    # the active-record blocker set; they are never promoted or treated as GT.
    assert len(legacy) == 0
    assert review_count == 27
    assert "EVAL_AUTH_NOT_GRANTED" in verdict.blocker_codes
    assert not (REPO_ROOT / governance.EVAL_AUTH_RELATIVE).exists()
    assert not (REPO_ROOT / "data/ground_truth/approved").exists()


def test_fixture_constants_are_consistent():
    assert VALID_PROPOSAL_SHA and len(SYNTHETIC_EVENTS) == 3


# --- CLI ----------------------------------------------------------------------------------


def test_cli_status_prints_categorized_report_and_exits_blocked(workspace: Path, capsys):
    from railway_detection.cli.main import main

    code = main(["evaluation", "status", "--repository-root", str(workspace)])
    payload = json.loads(capsys.readouterr().out)
    assert code == 3
    assert payload["blocker_codes"] == ["EVAL_AUTH_NOT_GRANTED"]
    assert payload["blockers_by_category"] == {"AUTHORIZATION": ["EVAL_AUTH_NOT_GRANTED"]}
    assert set(payload["live_bindings"]) == set(governance.EVAL_AUTH_BINDING_KEYS)




# --- the official runner path ---------------------------------------------------------------


def _sim(event_id: str):
    from railway_detection.simulation.runner import SimulationRunResult

    return SimulationRunResult(
        event_id=event_id,
        scenario_name="synthetic",
        total_duration_s=20.0,
        closed_duration_s=8.0,
        warning_lead_time_s=3.0,
        premature_opening_detected=False,
    )








def test_forged_permit_cannot_unlock_real_or_synthetic_runs():
    from railway_detection.evaluation.evaluation_runner import (
        EvaluationRefused,
        Phase12EvaluationRunner,
        _OfficialPermit,
    )
    from railway_detection.evaluation.input_contracts import EvidenceClassification

    forged = _OfficialPermit("a" * 64, "recorded_statement_unsigned", "b" * 64)
    base = dict(
        event_split={"train": ["a"], "val": ["b"], "test": ["c"]},
        camera_scope={"a": "single_camera", "b": "single_camera", "c": "single_camera"},
        accepted_sync_events=set(),
        ground_truth=[],
        simulation_results={},
    )
    with pytest.raises(EvaluationRefused, match="only through run_official"):
        Phase12EvaluationRunner().run(
            **base, evidence_classification=EvidenceClassification.REAL, _permit=forged,
            input_manifest_sha256="b" * 64,
        )
    with pytest.raises(EvaluationRefused, match="cannot be applied to synthetic"):
        Phase12EvaluationRunner().run(
            **base, evidence_classification=EvidenceClassification.SYNTHETIC, _permit=forged
        )


# --- manifest builder --------------------------------------------------------------------------


def test_manifest_builder_derives_manifest_from_verified_decisions(workspace: Path):
    from railway_detection.evaluation.manifest_builder import (
        EventSourceSpec,
        build_evaluation_input_manifest,
    )

    existing = json.loads((workspace / "data/manifests/phase12_evaluation_inputs.json").read_text())
    sources = {
        item["event_id"]: EventSourceSpec(item["cohort"], item["source_path"])
        for item in existing["events"]
    }
    built = build_evaluation_input_manifest(
        workspace, sources, "data/manifests/derived_inputs.json"
    )
    assert built["partitions"] == EVENTS
    assert built["camera_scope_by_event"] == SCOPE
    assert built["evidence_classification"] == "real"
    assert [e["source_sha256"] for e in built["events"]] == [
        e["source_sha256"] for e in sorted(existing["events"], key=lambda e: e["event_id"])
    ]


def test_manifest_builder_refuses_overwrite_unverified_decisions_and_wrong_events(
    workspace: Path,
):
    from railway_detection.evaluation.manifest_builder import (
        EventSourceSpec,
        ManifestBuildError,
        build_evaluation_input_manifest,
    )

    existing = json.loads((workspace / "data/manifests/phase12_evaluation_inputs.json").read_text())
    sources = {
        item["event_id"]: EventSourceSpec(item["cohort"], item["source_path"])
        for item in existing["events"]
    }
    with pytest.raises(ManifestBuildError, match="MANIFEST_EXISTS"):
        build_evaluation_input_manifest(
            workspace, sources, "data/manifests/phase12_evaluation_inputs.json"
        )
    short = dict(list(sources.items())[:-1])
    with pytest.raises(ManifestBuildError, match="EVENT_SPLIT_MISMATCH"):
        build_evaluation_input_manifest(workspace, short, "data/manifests/x.json")
    split_path = workspace / governance.SPLIT_DECISION_RELATIVE
    forged = json.loads(split_path.read_text())
    forged["decided_by"] = "not.on.allowlist@example.com"
    split_path.write_text(json.dumps(forged))
    with pytest.raises(ManifestBuildError, match="EVENT_SPLIT_DECISION_INVALID"):
        build_evaluation_input_manifest(workspace, sources, "data/manifests/y.json")
    assert not (workspace / "data/manifests/y.json").exists()


# --- receipt lifecycle: stale / altered inputs --------------------------------------------------


def _receipt_path(root: Path) -> Path:
    return root / governance.PROMOTION_RECEIPT_RELATIVE


def test_receipt_is_bound_to_inventory_proposals_and_allowlist(workspace: Path):
    inventory = workspace / "data/manifests/layer_b_v2_annotation_inventory.json"
    original = inventory.read_bytes()
    inventory.write_bytes(original + b"\n")  # any byte change
    assert "STAGE21_PROMOTION_RECEIPT_INVALID" in _assess(workspace).blocker_codes
    inventory.write_bytes(original)
    assert _assess(workspace).blocker_codes == ("EVAL_AUTH_NOT_GRANTED",)

    proposal = next((workspace / "data/ground_truth/proposals").rglob("*_proposal_v1.json"))
    proposal.write_bytes(b"a newer candidate")
    verdict = _assess(workspace)
    assert any(
        b.code == "STAGE21_PROMOTION_RECEIPT_INVALID" and "active_proposals" in b.detail
        for b in verdict.blockers
    )


def test_a_new_active_proposal_version_voids_the_receipt(workspace: Path):
    proposal = next((workspace / "data/ground_truth/proposals").rglob("*_proposal_v1.json"))
    proposal.with_name(proposal.name.replace("_v1", "_v2")).write_bytes(b"v2")
    assert "STAGE21_PROMOTION_RECEIPT_INVALID" in _assess(workspace).blocker_codes


def test_allowlist_change_voids_receipt_and_authorization(workspace: Path):
    _record_authorization(workspace)
    assert _assess(workspace).ready
    allowlist = workspace / "data/ground_truth/authorized_reviewers.json"
    _write_json(
        allowlist, {"authorized_reviewers": [PILOT_REVIEWER, "second.reviewer@example.org"]}
    )
    codes = _assess(workspace).blocker_codes
    assert "STAGE21_PROMOTION_RECEIPT_INVALID" in codes
    assert "EVAL_AUTH_BINDING_UNVERIFIABLE" in codes or "EVAL_AUTH_BINDING_MISMATCH" in codes


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r["inputs"].update({"inventory_sha256": "0" * 64}),
        lambda r: r["inputs"].pop("inventory_sha256"),
        lambda r: r["inputs"].update({"surprise": "x"}),
        lambda r: r.update({"media_hashes_verified_live": False}),
        lambda r: r.update({"produced_at_utc": "2999-01-01T00:00:00Z"}),
        lambda r: r.update({"produced_at_utc": "yesterday"}),
        lambda r: r.update({"stage": "other_stage"}),
    ],
)
def test_edited_receipts_fail_their_own_content_hash_or_binding(workspace: Path, mutate):
    path = _receipt_path(workspace)
    receipt = json.loads(path.read_text())
    mutate(receipt)
    _write_json(path, receipt)  # edited without re-deriving receipt_sha256
    assert "STAGE21_PROMOTION_RECEIPT_INVALID" in _assess(workspace).blocker_codes


def test_a_receipt_with_a_recomputed_self_hash_still_needs_live_input_agreement(workspace: Path):
    from railway_detection.annotation.receipt import receipt_body_sha256

    path = _receipt_path(workspace)
    receipt = json.loads(path.read_text())
    receipt["inputs"]["inventory_sha256"] = "0" * 64
    receipt["receipt_sha256"] = receipt_body_sha256(receipt)
    _write_json(path, receipt)
    verdict = _assess(workspace)
    assert any("inventory_sha256 differs" in b.detail for b in verdict.blockers)


def test_old_receipt_schema_is_refused(workspace: Path):
    path = _receipt_path(workspace)
    receipt = json.loads(path.read_text())
    receipt["schema_version"] = "phase12-stage21-promotion-receipt/1"
    _write_json(path, receipt)
    assert any("unsupported schema_version" in b.detail for b in _assess(workspace).blockers)


# --- a manifest cannot vouch for its own identity, cohort or approval --------------------------


def _edit_manifest(root: Path, mutate) -> None:
    path = root / "data/manifests/phase12_evaluation_inputs.json"
    manifest = json.loads(path.read_text())
    mutate(manifest)
    _write_json(path, manifest)


def test_manifest_cohort_cannot_be_relabelled(workspace: Path):
    def relabel(manifest):
        next(e for e in manifest["events"] if e["event_id"] == GT_EVENTS[0])["cohort"] = (
            "no_train_events"
        )

    _edit_manifest(workspace, relabel)
    assert "MANIFEST_COHORT_MISMATCH" in _assess(workspace).blocker_codes


def test_manifest_events_must_be_inventory_identities(workspace: Path):
    inventory = workspace / "data/manifests/layer_b_v2_annotation_inventory.json"
    entries = json.loads(inventory.read_text())
    entries.pop("train_events/evt_a")
    _write_json(inventory, entries)
    verdict = _assess(workspace)
    assert "MANIFEST_EVENT_NOT_IN_INVENTORY" in verdict.blocker_codes
    assert any("train_events/evt_a" in b.detail for b in verdict.blockers
               if b.code == "MANIFEST_EVENT_NOT_IN_INVENTORY")


def test_unqualified_event_ids_cannot_pass_as_real(workspace: Path):
    def strip_cohort(manifest):
        for event in manifest["events"]:
            event["event_id"] = event["event_id"].split("/")[1]
        manifest["partitions"] = {
            role: [i.split("/")[1] for i in ids] for role, ids in manifest["partitions"].items()
        }
        manifest["camera_scope_by_event"] = {
            k.split("/")[1]: v for k, v in manifest["camera_scope_by_event"].items()
        }

    _edit_manifest(workspace, strip_cohort)
    assert "MANIFEST_EVENT_NOT_IN_INVENTORY" in _assess(workspace).blocker_codes


def test_missing_inventory_means_events_cannot_be_checked(workspace: Path):
    (workspace / "data/manifests/layer_b_v2_annotation_inventory.json").unlink()
    assert "ANNOTATION_INVENTORY_MISSING" in _assess(workspace).blocker_codes


def test_test_split_event_needs_an_approved_record(workspace: Path):
    victim = next(
        p for p in (workspace / "data/ground_truth/reviews").rglob("*_review.json")
        if "no_train" in str(p)
    )
    victim.unlink()
    verdict = _assess(workspace)
    assert "MANIFEST_TEST_EVENT_WITHOUT_APPROVED_RECORD" in verdict.blocker_codes
    assert "STAGE21_PROMOTION_RECEIPT_INVALID" in verdict.blocker_codes  # and the receipt is stale


# --- diagnostics -----------------------------------------------------------------------------


def test_every_blocker_explains_what_is_missing_why_and_how_to_fix(workspace: Path, tmp_path):
    states = [
        assess_official_phase12_readiness(tmp_path / "empty", now=NOW),
        assess_official_phase12_readiness(REPO_ROOT, now=NOW),
        _assess(workspace),
    ]
    seen = 0
    for verdict in states:
        for blocker in verdict.blockers:
            payload = blocker.to_dict()
            for key in ("code", "category", "cause_class", "required_artifact", "remedy",
                        "verification_evidence", "insufficient_because"):
                assert payload[key], (blocker.code, key)
            assert payload["cause_class"] != "unclassified", blocker.code
            seen += 1
    assert seen > 0


def test_loader_error_codes_are_all_classified():
    import re

    source = (REPO_ROOT / "src/railway_detection/evaluation/input_contracts.py").read_text()
    codes = set(re.findall(r'EvaluationInputError\(\s*"([A-Z_]+)"', source))
    missing = sorted(code for code in codes if code not in execution_gate.BLOCKER_CATALOGUE)
    assert not missing, missing


def test_real_repository_blockers_distinguish_missing_from_invalid(tmp_path):
    verdict = assess_official_phase12_readiness(REPO_ROOT, now=NOW)
    classes = {b.code: b.cause_class for b in verdict.blockers}
    assert classes["STAGE21_RECORDS_MISSING"] == "missing_artifact"
    # Verified LEG-EXEC notices exclude the untouched legacy records from the
    # active gate; they do not turn them into valid evidence.
    assert "LEGACY_OR_UNKNOWN_GROUND_TRUTH_SCHEMA" not in classes
    assert classes["COHORT_APPROVAL_MISSING"] == "derived"
    assert classes["EVENT_SPLIT_DECISION_MISSING"] == "undecided_decision"
    assert classes["PREMATURE_OPENING_DEFINITION_UNDECIDED"] == "undecided_decision"
    assert classes["EVAL_AUTH_NOT_GRANTED"] == "authorization_gap"
