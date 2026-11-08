"""AUTH-DESCRIPTIVE-EVAL-EXEC gate (Mission 10, WP10.2). Synthetic only.

Records built here live in temporary trees installed as the "real" repository for one test; none is
a researcher authorization, and nothing is written into the actual repository.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import official_workspace as ow
from test_cache_only_replay import _build_valid_cache_fixture

from railway_detection.evaluation import descriptive_exec_gate as gate
from railway_detection.evaluation import governance
from railway_detection.evaluation.cache_only_engine import (
    CacheOnlyReplayEngine,
    ReplayRefusalRecord,
)
from railway_detection.evaluation.descriptive_exec_gate import DescriptiveExecutionNotAuthorized
from railway_detection.safety import media_guard

SIGNER = "signer@example.org"
LIVE = {key: f"{i}" * 64 for i, key in enumerate(gate.BINDING_KEYS)}
LIVE["metric_scope_sha256"] = gate.metric_scope_sha256()


def _record(**over) -> dict:
    now = datetime.now(UTC)
    record = {
        "schema_version": gate.DESCRIPTIVE_AUTH_SCHEMA,
        "authorization_id": "AUTH-DESCRIPTIVE-EVAL-EXEC-0001",
        "authorization_class": gate.AUTHORIZATION_CLASS,
        "status": "APPROVED",
        "authorized_by": SIGNER,
        "authorized_at_utc": (now - timedelta(hours=1)).isoformat(),
        "expires_at_utc": (now + timedelta(days=1)).isoformat(),
        "revoked": False,
        "authorization_statement": "Synthetic fixture statement (test only).",
        "attestation": {"type": governance.ATTESTATION_RECORDED_STATEMENT, "signature": None},
        "recorded_by": {"kind": "researcher", "identity": SIGNER},
        "scope": {
            "operation": gate.DESCRIPTIVE_OPERATION,
            "conditions": ["B0", "B1", "B2"],
            "events": ["train_events/event_001"],
            "metric_scope": list(gate.DESCRIPTIVE_METRIC_SCOPE),
            "purpose": "synthetic fixture purpose for unit tests",
            "field_or_physical_operations_authorized": False,
        },
        "bindings": dict(LIVE),
    }
    record.update(over)
    record["record_sha256"] = governance.canonical_record_sha256(record)
    return record


def _root(tmp_path: Path, record: dict | None) -> Path:
    root = tmp_path / "repo"
    (root / "data/ground_truth").mkdir(parents=True)
    (root / "data/ground_truth/authorized_reviewers.json").write_text(
        json.dumps({"authorized_reviewers": [SIGNER]}), encoding="utf-8"
    )
    if record is not None:
        (root / "data/governance").mkdir(parents=True)
        (root / gate.DESCRIPTIVE_AUTH_RELATIVE).write_text(json.dumps(record), encoding="utf-8")
    return root


def _verify(root: Path, *, condition="B0", event="train_events/event_001", live=None):
    return gate.verify_descriptive_authorization(
        root,
        condition=condition,
        event_id=event,
        manifest_sha256=LIVE["evaluation_manifest_sha256"],
        live=live if live is not None else dict(LIVE),
    )


def _code(root: Path, **kw) -> str:
    with pytest.raises(DescriptiveExecutionNotAuthorized) as info:
        _verify(root, **kw)
    return info.value.code


def test_no_record_means_not_granted(tmp_path: Path):
    assert _code(_root(tmp_path, None)) == "AUTH_DESCRIPTIVE_EVAL_EXEC_NOT_GRANTED"


def test_the_actual_repository_has_no_descriptive_authorization():
    assert not (Path(media_guard.REAL_REPO_ROOT) / gate.DESCRIPTIVE_AUTH_RELATIVE).exists()


def test_valid_record_is_accepted_and_reports_its_bindings(tmp_path: Path):
    verified = _verify(_root(tmp_path, _record()))
    assert verified.authorization_id.startswith("AUTH-DESCRIPTIVE-EVAL-EXEC")
    assert set(verified.bindings) == set(gate.BINDING_KEYS)


def _set(key, value):
    def apply(r):
        r[key] = value

    return apply


def _scope(**kw):
    def apply(r):
        r["scope"] = {**r["scope"], **kw}

    return apply


MUTATIONS = {
    "wrong_schema": _set("schema_version", "x/1"),
    "extra_field": _set("run_anyway", True),
    "wrong_class": _set("authorization_class", "AUTH-MEDIA-ACCESS"),
    "not_approved": _set("status", "DRAFT"),
    "revoked": _set("revoked", True),
    "revoked_string": _set("revoked", "true"),
    "unlisted_signer": _set("authorized_by", "stranger@example.org"),
    "signed_attestation": _set(
        "attestation", {"type": governance.ATTESTATION_RECORDED_STATEMENT, "signature": "x"}
    ),
    "naive_expiry": _set(
        "expires_at_utc", (datetime.now(UTC) + timedelta(days=1)).replace(tzinfo=None).isoformat()
    ),
    "expired": _set("expires_at_utc", (datetime.now(UTC) - timedelta(minutes=5)).isoformat()),
    "future_issue": _set("authorized_at_utc", (datetime.now(UTC) + timedelta(hours=3)).isoformat()),
    "wrong_operation": _scope(operation="official_phase12_evaluation"),
    "physical_ops": _scope(field_or_physical_operations_authorized=True),
    "metric_subset": _scope(metric_scope=["missed_train"]),
    "vague_purpose": _scope(purpose="x"),
    "event_out_of_scope": _scope(events=["train_events/event_002"]),
    "condition_out_of_scope": _scope(conditions=["B1"]),
    "binding_missing": _set("bindings", {k: v for k, v in LIVE.items() if k != "protocol_sha256"}),
    "binding_extra": _set("bindings", {**LIVE, "extra": "0" * 64}),
    "binding_not_hex": _set("bindings", {**LIVE, "protocol_sha256": "nothex"}),
}


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_invalid_record_is_refused(tmp_path: Path, name: str):
    record = _record()
    MUTATIONS[name](record)
    record["record_sha256"] = governance.canonical_record_sha256(record)
    assert _code(_root(tmp_path, record)) == "AUTH_DESCRIPTIVE_EVAL_EXEC_INVALID", name


def test_tampered_record_is_refused(tmp_path: Path):
    record = _record()
    record["scope"]["events"] = ["train_events/event_999"]  # edited without resealing
    assert _code(_root(tmp_path, record)) == "AUTH_DESCRIPTIVE_EVAL_EXEC_INVALID"


@pytest.mark.parametrize("key", gate.BINDING_KEYS)
def test_binding_drift_voids_the_authorization(tmp_path: Path, key: str):
    drifted = {**LIVE, key: "f" * 64}
    assert _code(_root(tmp_path, _record()), live=drifted) == "AUTH_DESCRIPTIVE_EVAL_EXEC_INVALID"


@pytest.mark.parametrize("key", gate.BINDING_KEYS)
def test_unverifiable_live_artifact_blocks(tmp_path: Path, key: str):
    unknown = {**LIVE, key: None}
    assert _code(_root(tmp_path, _record()), live=unknown) == "AUTH_DESCRIPTIVE_EVAL_EXEC_INVALID"


def test_changing_the_metric_set_voids_prior_authorizations(tmp_path: Path, monkeypatch):
    root = _root(tmp_path, _record())
    _verify(root)
    monkeypatch.setattr(
        gate, "DESCRIPTIVE_METRIC_SCOPE", (*gate.DESCRIPTIVE_METRIC_SCOPE, "new_metric")
    )
    assert _code(root, live={**LIVE, "metric_scope_sha256": gate.metric_scope_sha256()}) == (
        "AUTH_DESCRIPTIVE_EVAL_EXEC_INVALID"
    )


def test_all_manifest_events_scope(tmp_path: Path):
    record = _record()
    record["scope"]["events"] = [gate.ALL_MANIFEST_EVENTS]
    record["record_sha256"] = governance.canonical_record_sha256(record)
    _verify(_root(tmp_path, record), event="engine_events/event_007")


# ---- live bindings come from the real verification chain ----------------------------------


def test_live_bindings_track_the_promotion_receipt_protocol_and_config(tmp_path, monkeypatch):
    ws = ow.build_workspace(tmp_path, monkeypatch)
    live = gate.live_bindings(ws.root, manifest_sha256="a" * 64)
    assert all(live[k] for k in gate.BINDING_KEYS), live
    # voiding the promotion receipt (edit a record) makes that binding unverifiable
    victim = next((ws.root / "data/ground_truth/reviews").rglob("*_review.json"))
    record = json.loads(victim.read_text())
    record["general_review_notes"] = "edited"
    victim.write_text(json.dumps(record), encoding="utf-8")
    assert gate.live_bindings(ws.root, manifest_sha256="a" * 64)["promotion_receipt_sha256"] is None


# ---- the replay engine meets the gate at its operation boundary ---------------------------


def test_engine_is_ungated_in_a_synthetic_tree(tmp_path: Path):
    manifest = _build_valid_cache_fixture(tmp_path)
    engine = CacheOnlyReplayEngine(manifest, repo_root=tmp_path)
    event = engine.list_events()[0]
    assert engine.execute_replay(event, "B0")


def test_engine_on_the_real_repository_refuses_without_authorization(tmp_path: Path, monkeypatch):
    manifest = _build_valid_cache_fixture(tmp_path)
    monkeypatch.setattr(media_guard, "REAL_REPO_ROOT", tmp_path.resolve())
    engine = CacheOnlyReplayEngine(manifest, repo_root=tmp_path)
    event = engine.list_events()[0]
    with pytest.raises(DescriptiveExecutionNotAuthorized):
        engine.execute_replay(event, "B0")
    with pytest.raises(DescriptiveExecutionNotAuthorized):
        engine.load_visual_records(event)
    with pytest.raises(DescriptiveExecutionNotAuthorized):
        engine.load_audio_records(event)


def test_batch_replay_records_the_refusal_instead_of_executing(tmp_path: Path, monkeypatch):
    manifest = _build_valid_cache_fixture(tmp_path)
    monkeypatch.setattr(media_guard, "REAL_REPO_ROOT", tmp_path.resolve())
    engine = CacheOnlyReplayEngine(manifest, repo_root=tmp_path)
    results = engine.replay_all_events("B0")
    assert results and all(isinstance(r, ReplayRefusalRecord) for r in results.values())
    assert {r.code for r in results.values()} == {"AUTH_DESCRIPTIVE_EVAL_EXEC_NOT_GRANTED"}


def test_engine_enforces_the_authorized_condition_scope(tmp_path: Path, monkeypatch):
    """A record that authorizes only B1 must not unlock a B0 replay of the same event."""
    manifest = _build_valid_cache_fixture(tmp_path)
    monkeypatch.setattr(media_guard, "REAL_REPO_ROOT", tmp_path.resolve())
    engine = CacheOnlyReplayEngine(manifest, repo_root=tmp_path)
    event = engine.list_events()[0]
    live = {**LIVE, "evaluation_manifest_sha256": engine.manifest_sha256}
    monkeypatch.setattr(gate, "live_bindings", lambda *a, **k: dict(live))
    record = _record()
    record["scope"]["conditions"] = ["B1"]
    record["scope"]["events"] = [gate.ALL_MANIFEST_EVENTS]
    record["bindings"] = dict(live)
    record["record_sha256"] = governance.canonical_record_sha256(record)
    root = _root(tmp_path, record)
    assert root == tmp_path / "repo"
    (tmp_path / "data/governance").mkdir(parents=True, exist_ok=True)
    (tmp_path / gate.DESCRIPTIVE_AUTH_RELATIVE).write_text(json.dumps(record), encoding="utf-8")
    (tmp_path / "data/ground_truth").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data/ground_truth/authorized_reviewers.json").write_text(
        json.dumps({"authorized_reviewers": [SIGNER]}), encoding="utf-8"
    )
    with pytest.raises(DescriptiveExecutionNotAuthorized):
        engine.execute_replay(event, "B0")
    assert engine.execute_replay(event, "B1")
