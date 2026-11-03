"""Mission 14 (WP14.2, WP14.8): evaluation input loader and M-02 regression tests, synthetic only.

Tripwires record every manifest load, every event-source read/hash, every producer call, every
cache-engine construction and every media-guard check.  A refused REAL request must leave all of
them empty (or, where a one-time manifest *header* read is the documented way to learn the
classification, exactly one header-only load and no source read).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from security_support import FakeRepo, make_fake_repo, outside_dir  # noqa: E402

from railway_detection.evaluation import evaluation_runner as er  # noqa: E402
from railway_detection.evaluation import input_contracts as ic  # noqa: E402
from railway_detection.evaluation.cache_only_engine import CacheOnlyReplayEngine  # noqa: E402
from railway_detection.evaluation.evaluation_runner import (  # noqa: E402
    EvaluationRefused,
    Phase12EvaluationRunner,
    _OfficialPermit,
    _VerifiedOfficialAuthorization,
)
from railway_detection.evaluation.ground_truth_loader import ApprovedEventGroundTruth  # noqa: E402
from railway_detection.evaluation.input_contracts import (  # noqa: E402
    EvaluationInputError,
    EvidenceClassification,
    load_evaluation_input_manifest,
)
from railway_detection.evaluation.output_contracts import EvaluationProvenance  # noqa: E402
from railway_detection.evaluation.replay_producer import RealEventReplayProducer  # noqa: E402
from railway_detection.safety.media_guard import classify_resource  # noqa: E402
from railway_detection.simulation.runner import SimulationRunResult  # noqa: E402

REQUIRED = "OFFICIAL_AUTHORIZATION_CONTEXT_REQUIRED"
HEX64 = "0123456789abcdef"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_manifest(
    root: Path,
    classification: str,
    *,
    names: dict[str, str] | None = None,
    wrong_hash: bool = False,
) -> Path:
    """Three-event manifest whose sources are JSON payloads (or caller-named files)."""
    root.mkdir(parents=True, exist_ok=True)
    groups = {"train": ["evt_train"], "val": ["evt_val"], "test": ["evt_test"]}
    events = []
    for role, ids in groups.items():
        for event_id in ids:
            name = (names or {}).get(event_id, f"{event_id}.json")
            source = root / name
            if not source.exists():
                source.write_text(
                    json.dumps({"event_id": event_id, "frames": []}), encoding="utf-8"
                )
            digest = "0" * 64 if wrong_hash else sha(source.read_bytes())
            events.append(
                {
                    "event_id": event_id,
                    "cohort": "train_events",
                    "split_role": role,
                    "source_path": name,
                    "source_sha256": digest,
                }  # fmt: skip
            )
    manifest = {
        "schema_version": "phase12-evaluation-inputs/1",
        "evidence_classification": classification,
        "partitions": groups,
        "events": events,
        "camera_scope_by_event": {e["event_id"]: "single_camera" for e in events},
        "accepted_sync_events": [],
    }
    path = root / "inputs.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def truth(event_id: str) -> ApprovedEventGroundTruth:
    return ApprovedEventGroundTruth(
        event_id=event_id,
        cohort="train_events",
        review_id=f"review_{event_id}",
        reviewer_id="synthetic_fixture",
        observable_boundaries={"T1_danger_zone_entry": 5.0, "T4_tail_clearance": 10.0},
        censored_boundaries=(),
        uncertain_boundaries=(),
        not_applicable_boundaries=("T0_first_visible", "T2", "T3", "T_scene_clear"),
    )


def sim(event_id: str) -> SimulationRunResult:
    return SimulationRunResult(
        event_id=event_id,
        scenario_name="synthetic",
        total_duration_s=15.0,
        closed_duration_s=8.0,
        warning_lead_time_s=3.0,
        premature_opening_detected=False,
    )


class Tripwires:
    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.manifest_loads: list[bool] = []  # verify_sources flag of each load
        self.source_reads: list[str] = []
        self.producer_calls = 0
        self.cache_engines = 0
        self.media_checks: list[str] = []

        real_load = er.load_evaluation_input_manifest
        real_read = ic._read_source_bytes_and_hash
        real_guard = ic.require_media_authorization

        def load(path, *, verify_sources=True):
            self.manifest_loads.append(bool(verify_sources))
            return real_load(path, verify_sources=verify_sources)

        def read(path):
            self.source_reads.append(Path(path).name)
            return real_read(path)

        def guard(path, op, **kw):
            if classify_resource(path, declared_media=kw.get("declared_media", False)).guarded:
                self.media_checks.append(Path(path).name)  # only checks that actually engage
            return real_guard(path, op, **kw)

        def producer(*_a, **_k):
            self.producer_calls += 1
            raise AssertionError("producer reached")

        def engine(*_a, **_k):
            self.cache_engines += 1
            raise AssertionError("cache engine reached")

        monkeypatch.setattr(er, "load_evaluation_input_manifest", load)
        monkeypatch.setattr(ic, "_read_source_bytes_and_hash", read)
        monkeypatch.setattr(ic, "require_media_authorization", guard)
        monkeypatch.setattr(RealEventReplayProducer, "produce", producer)
        monkeypatch.setattr(CacheOnlyReplayEngine, "__init__", engine)

    def assert_untouched(self, *, header_loads: int = 0) -> None:
        assert self.source_reads == [], "an event source was opened or hashed"
        assert self.producer_calls == 0
        assert self.cache_engines == 0
        assert self.media_checks == []
        assert self.manifest_loads == [False] * header_loads


@pytest.fixture
def trip(monkeypatch) -> Tripwires:
    return Tripwires(monkeypatch)


def forged_context(
    manifest: Path, *, token: object | None = None
) -> _VerifiedOfficialAuthorization:
    return _VerifiedOfficialAuthorization(
        token=object() if token is None else token,
        authorization_sha256="a" * 64,
        attestation_level="recorded_statement_unsigned",
        manifest_sha256=sha(manifest.read_bytes()),
    )


# ------------------------------------------------------ F13-01: the loader and protected media


@pytest.fixture
def repo(tmp_path_factory, monkeypatch) -> FakeRepo:
    return make_fake_repo(tmp_path_factory, monkeypatch)


def raw_manifest(
    repo: FakeRepo, source_name: str, payload: bytes = b"SYNTHETIC-MEDIA-BYTES"
) -> Path:
    media = repo.raw_dir / source_name
    media.write_bytes(payload)
    return write_manifest(repo.raw_dir, "synthetic", names={"evt_train": source_name})


def test_loader_refuses_a_media_source_before_opening_or_hashing_it(repo, monkeypatch):
    manifest = raw_manifest(repo, "camera_front.mov")
    with monkeypatch.context() as patch:
        patch.setattr(os, "open", lambda *a, **k: (_ for _ in ()).throw(AssertionError("opened")))
        with pytest.raises(EvaluationInputError) as info:
            load_evaluation_input_manifest(manifest, verify_sources=True)
    assert info.value.code == "SOURCE_MEDIA_ACCESS_DENIED"


@pytest.mark.parametrize(
    "name", ["camera_front.mov", "clip", "clip.m2ts", "clip.weird", "clip.bin"]
)
def test_refusal_is_by_location_and_never_leaks_a_digest(repo, name):
    payload = b"PROTECTED-" + name.encode()
    manifest = raw_manifest(repo, name, payload)
    with pytest.raises(EvaluationInputError) as info:
        load_evaluation_input_manifest(manifest, verify_sources=True)
    text = f"{info.value.code} {info.value.detail} {info.value}"
    assert info.value.code == "SOURCE_MEDIA_ACCESS_DENIED"
    assert sha(payload) not in text and sha(payload)[:12] not in text
    assert payload.decode() not in text
    assert not any(
        len(token) == 64 and set(token) <= set(HEX64) for token in text.replace("'", " ").split()
    )


def test_a_media_manifest_path_is_refused_before_it_is_read(repo, monkeypatch):
    fake_manifest = repo.raw_dir / "manifest.mov"
    fake_manifest.write_bytes(b"x")
    with monkeypatch.context() as patch:
        patch.setattr(
            Path, "read_bytes", lambda *a, **k: (_ for _ in ()).throw(AssertionError("read"))
        )
        with pytest.raises(EvaluationInputError) as info:
            load_evaluation_input_manifest(fake_manifest, verify_sources=False)
    assert info.value.code == "SOURCE_MEDIA_ACCESS_DENIED"


def test_a_symlinked_source_is_still_refused_without_a_read(repo, tmp_path_factory, trip):
    outside = outside_dir(tmp_path_factory, "symsrc")
    manifest = write_manifest(outside, "synthetic")
    (outside / "evt_train.json").unlink()
    os.symlink(repo.video, outside / "evt_train.json")  # innocent name, raw media target
    with pytest.raises(EvaluationInputError) as info:
        load_evaluation_input_manifest(manifest, verify_sources=True)
    assert info.value.code in {
        "SOURCE_PATH_ESCAPE", "SOURCE_SYMLINK_UNEXPECTED", "SOURCE_MEDIA_ACCESS_DENIED"
    }  # fmt: skip
    assert trip.source_reads == []


def test_metadata_only_loading_never_reads_sources(repo, trip):
    manifest = raw_manifest(repo, "camera_front.mov")
    inputs = load_evaluation_input_manifest(manifest, verify_sources=False)
    assert len(inputs.events) == 3
    assert trip.source_reads == []


def test_hash_mismatch_message_has_no_digest_at_all(tmp_path_factory):
    outside = outside_dir(tmp_path_factory, "mismatch")
    manifest = write_manifest(outside, "synthetic", wrong_hash=True)
    actual = sha((outside / "evt_train.json").read_bytes())
    with pytest.raises(EvaluationInputError) as info:
        load_evaluation_input_manifest(manifest, verify_sources=True)
    assert info.value.code == "SOURCE_HASH_MISMATCH"
    assert actual not in str(info.value) and "0" * 64 not in str(info.value)


def test_text_metadata_sources_under_data_raw_remain_loadable(repo):
    manifest = write_manifest(repo.raw_dir, "synthetic")  # JSON payloads inside data/raw
    assert len(load_evaluation_input_manifest(manifest, verify_sources=True).events) == 3


def test_valid_synthetic_manifests_still_work(tmp_path_factory):
    outside = outside_dir(tmp_path_factory, "valid")
    manifest = write_manifest(outside, "synthetic")
    inputs = load_evaluation_input_manifest(manifest)
    assert inputs.evidence_classification is EvidenceClassification.SYNTHETIC
    assert inputs.source_fingerprints["evt_test"] == sha((outside / "evt_test.json").read_bytes())


# -------------------------------------------- F13-02: public APIs and invalid REAL requests


@pytest.fixture
def real_manifest(tmp_path_factory) -> Path:
    return write_manifest(outside_dir(tmp_path_factory, "realmf"), "real")


def public_call(manifest: Path, **extra):
    return Phase12EvaluationRunner().run_from_manifest(
        manifest_path=manifest, ground_truth=[truth("evt_test")],
        simulation_results={"evt_test": sim("evt_test")}, **extra,
    )  # fmt: skip


def test_explicit_real_request_is_refused_with_zero_reads(trip, real_manifest):
    with pytest.raises(EvaluationRefused) as info:
        public_call(real_manifest, evidence_classification=EvidenceClassification.REAL)
    assert info.value.code == REQUIRED
    trip.assert_untouched(header_loads=0)


def test_forged_permit_with_matching_digest_is_refused_with_zero_reads(trip, real_manifest):
    permit = _OfficialPermit(
        "a" * 64, "recorded_statement_unsigned", sha(real_manifest.read_bytes())
    )
    for classification in (EvidenceClassification.REAL, EvidenceClassification.SYNTHETIC):
        with pytest.raises(EvaluationRefused) as info:
            public_call(real_manifest, evidence_classification=classification, _permit=permit)
        assert info.value.code == REQUIRED
    with pytest.raises(EvaluationRefused):
        Phase12EvaluationRunner().run(
            evidence_classification=EvidenceClassification.REAL, _permit=permit
        )
    trip.assert_untouched(header_loads=0)


def test_forged_authorization_context_is_refused_even_with_the_module_private_token(
    trip, real_manifest
):
    for token in (object(), er._OFFICIAL_CONTEXT_TOKEN, "token"):
        ctx = forged_context(real_manifest, token=token)
        with pytest.raises(EvaluationRefused) as info:
            public_call(real_manifest, _authorization_context=ctx)
        assert info.value.code == REQUIRED
        with pytest.raises(EvaluationRefused):
            Phase12EvaluationRunner().run(
                evidence_classification=EvidenceClassification.SYNTHETIC, _authorization_context=ctx
            )
    trip.assert_untouched(header_loads=0)


def test_real_manifest_with_the_classification_argument_omitted_reads_no_source(
    trip, real_manifest
):
    with pytest.raises(EvaluationRefused) as info:
        public_call(real_manifest)
    assert info.value.code == REQUIRED
    trip.assert_untouched(header_loads=1)  # exactly one header-only load, no source opened


def test_caller_declaring_synthetic_cannot_relabel_a_real_manifest(trip, real_manifest):
    with pytest.raises(EvaluationRefused) as info:
        public_call(real_manifest, evidence_classification=EvidenceClassification.SYNTHETIC)
    assert info.value.code == REQUIRED
    trip.assert_untouched(header_loads=1)


def test_private_core_demands_the_context_before_any_source_is_read(trip, real_manifest):
    runner = Phase12EvaluationRunner()
    for kwargs in (
        {},
        {"_permit": _OfficialPermit("a" * 64, "x", sha(real_manifest.read_bytes()))},
        {"_authorization_context": forged_context(real_manifest)},
    ):
        with pytest.raises(EvaluationRefused) as info:
            runner._run_from_manifest_verified(
                manifest_path=real_manifest, ground_truth=[], simulation_results={}, **kwargs
            )
        assert info.value.code == REQUIRED
    assert trip.source_reads == []
    assert trip.manifest_loads == [False, False, False]  # headers only
    assert trip.producer_calls == 0 and trip.cache_engines == 0 and trip.media_checks == []


def test_context_for_one_manifest_cannot_be_reused_for_another(trip, tmp_path_factory):
    first = write_manifest(outside_dir(tmp_path_factory, "ctx_a"), "real")
    second = write_manifest(outside_dir(tmp_path_factory, "ctx_b"), "real")
    body = json.loads(second.read_text(encoding="utf-8"))
    body["note"] = "a different manifest"
    second.write_text(json.dumps(body), encoding="utf-8")
    ctx = _VerifiedOfficialAuthorization(
        token=er._OFFICIAL_CONTEXT_TOKEN,
        authorization_sha256="a" * 64,
        attestation_level="recorded_statement_unsigned",
        manifest_sha256=sha(first.read_bytes()),
    )
    assert sha(first.read_bytes()) != sha(second.read_bytes())
    with pytest.raises(EvaluationRefused) as info:
        Phase12EvaluationRunner()._run_from_manifest_verified(
            manifest_path=second, ground_truth=[], simulation_results={}, _authorization_context=ctx
        )
    assert info.value.code == REQUIRED
    assert trip.source_reads == []


def test_manifests_in_the_repository_evidence_trees_are_not_read_by_the_public_api(repo, trip):
    for zone in ("data/manifests", "data/raw/layer_b", "configs", "results", "experiments"):
        directory = repo.root / zone
        directory.mkdir(parents=True, exist_ok=True)
        manifest = write_manifest(directory, "synthetic")
        with pytest.raises(EvaluationRefused) as info:
            public_call(manifest)
        assert info.value.code == "OFFICIAL_MANIFEST_LOCATION_REFUSED", zone
    trip.assert_untouched(header_loads=0)


def test_valid_synthetic_manifest_still_runs_end_to_end(trip, tmp_path_factory):
    outside = outside_dir(tmp_path_factory, "e2e")
    manifest = write_manifest(outside, "synthetic")
    result = public_call(manifest, output_dir=outside / "out")
    assert result.evidence_classification is EvidenceClassification.SYNTHETIC
    assert result.run_manifest["authorization_status"] == "not_verified"
    assert result.run_manifest["provenance"]["official_authorization_verified"] is False
    assert result.run_manifest["provenance"]["input_manifest_sha256"] == sha(manifest.read_bytes())
    assert trip.producer_calls == 0 and trip.cache_engines == 0
    # Each source is read twice by the documented validate-then-revalidate (TOCTOU) re-check.
    assert sorted(trip.source_reads) == sorted(
        ["evt_train.json", "evt_val.json", "evt_test.json"] * 2
    )


def test_public_run_and_run_safe_never_reach_the_producer(trip):
    kwargs = {"evidence_classification": EvidenceClassification.REAL}
    with pytest.raises(EvaluationRefused):
        Phase12EvaluationRunner().run(**kwargs)
    report = Phase12EvaluationRunner().run_safe(**kwargs)
    assert report.status == "BLOCKED" and report.blockers[0]["code"] == REQUIRED
    trip.assert_untouched()


def test_synthetic_result_marker_is_never_true_and_cannot_be_set_through_the_runner(tmp_path):
    runner = Phase12EvaluationRunner()
    result = runner.run(
        event_split={"train": ["evt_train"], "val": ["evt_val"], "test": ["evt_test"]},
        camera_scope={
            "evt_train": "single_camera",
            "evt_val": "single_camera",
            "evt_test": "single_camera",
        },  # fmt: skip
        accepted_sync_events=set(),
        ground_truth=[truth("evt_test")],
        simulation_results={"evt_test": sim("evt_test")},
    )
    assert result.run_manifest["provenance"]["official_authorization_verified"] is False
    # Documented limit: the marker is an unsigned bool on a plain dataclass. It proves nothing to a
    # downstream reader, which is why no code in this repository trusts it.
    forged = EvaluationProvenance(
        schema_version="x", phase="12", evidence_classification=EvidenceClassification.REAL,
        input_manifest_sha256="", source_sha256_by_event={}, frozen_config_sha256="",
        decision_policy_sha256="", checkpoint_sha256={}, seed=1, git_commit=None,
        official_authorization_verified=True,
    )  # fmt: skip
    assert forged.official_authorization_verified is True


def test_run_official_refuses_at_readiness_and_writes_nothing(tmp_path_factory):
    """A synthetic tree with no EVAL-AUTH: run_official refuses before any replay or output."""
    root = outside_dir(tmp_path_factory, "official_root")
    out = root / "out"
    with pytest.raises(EvaluationRefused) as info:
        Phase12EvaluationRunner().run_official(repository_root=root, output_dir=out)
    assert info.value.code == "OFFICIAL_PREREQUISITES_UNSATISFIED"
    assert info.value.stage == "readiness"
    assert not out.exists()
