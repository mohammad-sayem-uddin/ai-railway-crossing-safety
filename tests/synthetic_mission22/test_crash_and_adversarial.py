import json
import sqlite3
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from railway_detection.annotation.human_review_domain import (
    BOUNDARIES,
    Observation,
    SyntheticReviewer,
)
from railway_detection.annotation.human_review_service import ConstructedReviewService, ReviewScope
from railway_detection.annotation.human_review_store import ConstructedReviewStore
from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.safety.constructed_authority import (
    PROFILE,
    ConstructedAuthority,
    Grant,
    encode_payload,
)
from railway_detection.simulation.runner import EventSimulationRunner
from railway_detection.synthetic.convention_b_pipeline import (
    ConstructedBatch,
    ConstructedInput,
    IntegrationRequest,
)
from railway_detection.synthetic.integration_contracts import validate_stream_bindings
from railway_detection.synthetic.integration_fixture import make_fixture
from railway_detection.synthetic.integration_workflow import run_demo

ROOT = Path(__file__).resolve().parents[2]
CODE = "0" * 40
OBS = tuple(
    Observation(k, "front", "NOT_OBSERVABLE", "CONSTRUCTED_REVIEW_FIXTURE") for k in BOUNDARIES
)


def build(path, *, anchor=(0, None), fresh=False):
    db = sqlite3.connect(path)
    a = ConstructedAuthority(
        db,
        appointments=(("synthetic:i", ("ISSUER",)), ("synthetic:r", ("REVIEWER",))),
        expected_context="synthetic:runtime",
        profile=PROFILE,
    )
    scope = ReviewScope(
        "synthetic:s",
        1,
        "synthetic:r",
        "synthetic:resource",
        "synthetic:runtime",
        "CONSTRUCTED_REVIEW_FIXTURE",
        1,
    )
    if fresh:
        a.issue(
            "synthetic:i",
            Grant(
                "synthetic:g",
                scope.actor,
                "synthetic:event",
                ("REVIEW",),
                (scope.resource,),
                scope.purpose,
                scope.context,
                0,
                10,
                5,
            ),
        )
        a.reserve(
            "synthetic:g", session=scope.session, initial_body=encode_payload({}), **scope.current()
        )
    store = ConstructedReviewStore(
        db,
        reviewers=(SyntheticReviewer(scope.actor, ("REVIEWER",)),),
        events=("synthetic:event",),
        expected_anchor=anchor,
    )
    return a, store, ConstructedReviewService(a, store), scope


def test_abrupt_exit_during_shared_transaction_rolls_back(tmp_path):
    path = tmp_path / "constructed.sqlite"
    program = """
import os,sqlite3
from pathlib import Path
import sys
sys.path.insert(0,sys.argv[2])
from test_crash_and_adversarial import build,OBS
a,s,service,scope=build(Path(sys.argv[1]),fresh=True)
a.db.create_function('constructed_exit',0,lambda:os._exit(73))
a.db.execute("CREATE TRIGGER fail BEFORE INSERT ON entries BEGIN SELECT constructed_exit(); END")
service.execute(scope,'SEAL','synthetic:event',request_id='synthetic:r1',observations=OBS)
"""
    child = subprocess.run(
        [sys.executable, "-c", program, str(path), str(Path(__file__).parent)],
        capture_output=True,
        text=True,
    )
    assert child.returncode == 73, child.stdout + child.stderr
    a, s, service, scope = build(path)
    assert s.anchor == (0, None) and a.db.execute("SELECT count(*) FROM tx").fetchone()[0] == 0
    assert a.db.execute("SELECT uses FROM sessions").fetchone()[0] == 0
    a.db.execute("DROP TRIGGER fail")
    assert (
        service.execute(
            scope, "SEAL", "synthetic:event", request_id="synthetic:r1", observations=OBS
        )["review_commit"]["count"]
        == 1
    )
    a.db.close()


def test_two_connections_cannot_commit_duplicate_first_seals(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    path = tmp_path / "constructed.sqlite"
    a, s, service, scope = build(path, fresh=True)
    a.db.close()
    barrier = Barrier(2)

    def worker(number):
        a, s, service, scope = build(path)
        try:
            barrier.wait(timeout=10)
            try:
                service.execute(
                    scope,
                    "SEAL",
                    "synthetic:event",
                    request_id="synthetic:r" + str(number),
                    observations=OBS,
                )
                return "COMMITTED"
            except ValueError:
                return "DENIED"
        finally:
            a.db.close()

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(worker, [1, 2])) == ["COMMITTED", "DENIED"]
    db = sqlite3.connect(path)
    assert db.execute("SELECT count(*) FROM constructed_review_log").fetchone()[0] == 1
    assert db.execute("SELECT uses FROM sessions").fetchone()[0] == 1
    db.close()


def test_missing_scope_wrong_role_replay_and_malformed_receipt(tmp_path):
    a, s, service, scope = build(tmp_path / "fixture.sqlite", fresh=True)
    with pytest.raises(ValueError):
        service.execute(None, "SEAL", "synthetic:event", request_id="synthetic:r", observations=OBS)
    a.roles[scope.actor] = ("ISSUER",)
    with pytest.raises(ValueError):
        service.execute(
            scope, "SEAL", "synthetic:event", request_id="synthetic:r", observations=OBS
        )
    a.roles[scope.actor] = ("REVIEWER",)
    service.execute(scope, "SEAL", "synthetic:event", request_id="synthetic:r", observations=OBS)
    with pytest.raises(ValueError):
        service.execute(
            scope, "SEAL", "synthetic:event", request_id="synthetic:replay", observations=OBS
        )
    a.db.execute("UPDATE tx SET receipt='{}'")
    with pytest.raises(ValueError, match="malformed historical"):
        service.execute(
            scope, "SEAL", "synthetic:event", request_id="synthetic:r", observations=OBS
        )
    a.db.close()


def test_checkpoint_step_cannot_skip_committed_prefix(tmp_path):
    path = tmp_path / "run"
    with pytest.raises(InterruptedError):
        run_demo(path, code_identity=CODE, stop_after="review")
    (path / "ACK.json").write_text(
        json.dumps({"schema": "M22_CONSTRUCTED_RUN/1", "step": 3, "anchor": [0, None]})
    )
    with pytest.raises(ValueError, match="checkpoint step"):
        run_demo(path, code_identity=CODE, resume=True)
    assert not (path / "COMPLETE.json").exists()


@pytest.mark.parametrize("fault", ["missing", "wrong_camera", "wrong_event", "fused"])
def test_camera_boundary_failure(fault):
    f = make_fixture(code_identity=CODE)
    if fault == "missing":
        del f["requests"]["back"]
    else:
        q = f["requests"]["back"]
        if fault == "wrong_event":
            q = replace(q, batch=replace(q.batch, fixture_id="synthetic:other:back"))
        else:
            rows = json.loads(q.batch.inputs_json)
            rows[0]["frame"]["vision_records"][0]["source_id"] = "camera_front"
            q = replace(q, batch=replace(q.batch, inputs_json=json.dumps(rows)))
        f["requests"]["back"] = q
    with pytest.raises(ValueError):
        validate_stream_bindings(f)


def test_audio_alone_neither_closes_nor_grants_clearance():
    rows = []
    for i, t in enumerate((0, 200000, 2200000, 4200000, 6200000)):
        audio = EvidenceRecord(
            t / 1_000_000, "audio_1", Modality.AUDIO, True, (Detection("train_horn", 0.99),)
        )
        rows.append(
            ConstructedInput(
                "synthetic:f" + str(i), t, MultimodalFrame(t / 1_000_000, audio_records=(audio,))
            )
        )
    b = ConstructedBatch.build("synthetic:audio", tuple(rows), provenance="CONSTRUCTED_IN_MEMORY")
    engine = MultimodalDecisionEngine()
    q = IntegrationRequest.prepare(b, engine, mode="ARRIVAL", code_identity="synthetic:code")
    result = EventSimulationRunner(engine).run_frames_convention_b(q)
    assert result.status == "COMPLETE" and result.causal.final_angle == 90
    assert all(link.command != "LOWER" for link in result.decisions)
    assert all(
        json.loads(link.decision_json)["resulting_state"] != "CROSSING_CLEAR"
        for link in result.decisions
    )


def test_sqlite_full_preserves_original_error_after_automatic_rollback(tmp_path):
    a, s, service, scope = build(tmp_path / "full.sqlite", fresh=True)
    a.db.execute("CREATE TABLE constructed_capacity(payload BLOB)")
    pages = a.db.execute("PRAGMA page_count").fetchone()[0]
    a.db.execute("PRAGMA max_page_count=" + str(pages))
    with pytest.raises(sqlite3.OperationalError, match="database or disk is full"):
        with a._transaction():
            a.db.execute("INSERT INTO constructed_capacity VALUES(zeroblob(1048576))")
    assert not a.db.in_transaction
    assert a.db.execute("SELECT count(*) FROM constructed_capacity").fetchone()[0] == 0
    a.db.close()


@pytest.mark.parametrize(
    "times,kind",
    [
        ([0, None], "invalid"),
        ([0, 200_000, 100_000, 400_000], "out_of_order"),
        ([0, 200_000, 200_000, 400_000], "duplicate"),
    ],
)
def test_native_rejections_remain_traceable_at_metric_boundary(times, kind):
    from railway_detection.synthetic.integration_contracts import project_b_metrics

    inputs = tuple(
        ConstructedInput(
            "synthetic:frame:" + str(i), t, MultimodalFrame(0.0 if t is None else t / 1_000_000)
        )
        for i, t in enumerate(times)
    )
    batch = ConstructedBatch.build("synthetic:reject", inputs, provenance="CONSTRUCTED_IN_MEMORY")
    engine = MultimodalDecisionEngine()
    request = IntegrationRequest.prepare(
        batch, engine, mode="ARRIVAL", code_identity="synthetic:code"
    )
    result = EventSimulationRunner(engine).run_frames_convention_b(request)
    if kind == "invalid":
        assert result.status == "INCOMPLETE"
    else:
        rejected = [link for link in result.decisions if not link.accepted]
        assert len(rejected) == 1 and rejected[0].input_index == 2 and rejected[0].command is None
    metrics = project_b_metrics(result, expected_request=request, t4_us=500_000)
    assert metrics["M4"] is None and metrics["M5"] is None


def test_inconsistent_controller_configuration_denied_before_execution():
    f = make_fixture(code_identity=CODE)
    engine = MultimodalDecisionEngine()
    engine.warning_dwell_s += 1
    with pytest.raises(ValueError, match="settings differ"):
        EventSimulationRunner(engine).run_frames_convention_b(f["requests"]["front"])


def test_source_version_change_after_authorization_is_not_rebound(tmp_path):
    from railway_detection.safety.constructed_authority import canonical, sha
    from railway_detection.safety.constructed_broker import (
        ConstructedResource,
        ConstructedResourceBroker,
        resource_digest,
    )

    a, s, service, scope = build(tmp_path / "fixture.sqlite", fresh=True)
    original = ConstructedResource("synthetic:resource", "synthetic:v1", b"CONSTRUCTED_SOURCE")
    retained = sha(canonical(((original.resource_id, resource_digest(original)),)))
    changed = replace(original, contents=b"CHANGED_SOURCE")
    with pytest.raises(ValueError, match="registry binding"):
        ConstructedResourceBroker(a, resources=(changed,), expected_registry_digest=retained)
    assert a.db.execute("SELECT uses FROM sessions").fetchone()[0] == 0
    a.db.close()
