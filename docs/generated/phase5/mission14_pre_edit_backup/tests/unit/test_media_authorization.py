# ruff: noqa: E501
"""Operation-boundary media authorization (Mission 10, WP10.2).

Everything here is synthetic. The "real repository" is a temporary tree that the tests install as
``media_guard.REAL_REPO_ROOT`` for the duration of a test, so no real media, checkpoint or
processed data is opened -- and nothing is ever written into the actual repository. The authorization
records built here live only in those temporary trees; none is, or stands in for, a researcher
authorization.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from railway_detection.safety import media_guard as guard
from railway_detection.safety.media_guard import MediaAccessAuthorizationError

SIGNER = "signer@example.org"
PROTOCOL_REL = "docs/PROTOCOL.md"
EVENT = "train_events/event_001"


class FakeRepo:
    def __init__(self, root: Path) -> None:
        self.root = root
        (root / "docs").mkdir(parents=True)
        (root / PROTOCOL_REL).write_text("protocol v1\n", encoding="utf-8")
        (root / "data/ground_truth").mkdir(parents=True)
        (root / "data/ground_truth/authorized_reviewers.json").write_text(
            json.dumps({"authorized_reviewers": [SIGNER]}), encoding="utf-8"
        )
        (root / "data/governance").mkdir(parents=True)
        media = root / "data/raw/layer_b/v2" / EVENT
        media.mkdir(parents=True)
        self.video = media / "camera_front.mov"
        self.video.write_bytes(b"FAKE-VIDEO")
        self.audio = media / "audio.wav"
        self.audio.write_bytes(b"FAKE-AUDIO")

    @property
    def record_path(self) -> Path:
        return self.root / guard.CANONICAL_MEDIA_AUTH_RELATIVE

    def payload(self, **over) -> dict:
        now = datetime.now(UTC)
        record = {
            "schema_version": guard.MEDIA_ACCESS_SCHEMA_VERSION,
            "authorization_id": "AUTH-MEDIA-ACCESS-0001",
            "authorization_class": "AUTH-MEDIA-ACCESS",
            "status": "APPROVED",
            "authorized_by": SIGNER,
            "authorized_at_utc": (now - timedelta(hours=1)).isoformat(),
            "expires_at_utc": (now + timedelta(days=1)).isoformat(),
            "revoked": False,
            "authorization_statement": "Synthetic fixture statement (test only).",
            "attestation": {"type": "RECORDED_RESEARCHER_STATEMENT", "signature": None},
            "recorded_by": {"kind": "researcher", "identity": SIGNER},
            "scope": {
                "operations": ["READ_RAW_MEDIA", "HASH_RAW_MEDIA", "MEDIA_PROBE"],
                "datasets": ["layer_b"],
                "events": [EVENT],
                "media_types": ["video"],
                "purpose": "synthetic fixture purpose for unit tests",
            },
            "restrictions": {"path_prefixes": []},
            "bindings": {
                "protocol_document": {
                    "path": PROTOCOL_REL,
                    "sha256": hashlib.sha256(b"protocol v1\n").hexdigest(),
                }
            },
        }
        for key, value in over.items():
            record[key] = value
        record["record_sha256"] = guard._canonical_sha256(record)
        return record

    def write(self, record: dict | None = None, **over) -> dict:
        record = record or self.payload(**over)
        self.record_path.write_text(json.dumps(record), encoding="utf-8")
        return record

    def write_raw(self, record: dict, *, reseal: bool = True) -> None:
        if reseal:
            record["record_sha256"] = guard._canonical_sha256(record)
        self.record_path.write_text(json.dumps(record), encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FakeRepo:
    fake = FakeRepo(tmp_path / "repo")
    monkeypatch.setattr(guard, "REAL_REPO_ROOT", fake.root.resolve())
    return fake


def _denied(path: Path, op: str = "READ_RAW_MEDIA", **kw) -> MediaAccessAuthorizationError:
    with pytest.raises(MediaAccessAuthorizationError) as info:
        guard.require_media_authorization(path, op, **kw)
    return info.value


# ------------------------------------------------------------------ default-deny behaviour


def test_no_record_denies_real_repository_media(repo: FakeRepo):
    assert _denied(repo.video).code == "AUTH_MEDIA_ACCESS_NOT_GRANTED"


def test_the_actual_repository_has_no_media_authorization():
    """A fact about the real tree, established without opening any media."""
    real = Path(guard.REAL_REPO_ROOT)
    assert not (real / guard.CANONICAL_MEDIA_AUTH_RELATIVE).exists()


def test_synthetic_temp_media_needs_no_authorization(tmp_path: Path):
    clip = tmp_path / "clip.mov"
    clip.write_bytes(b"x")
    guard.require_media_authorization(clip, "READ_RAW_MEDIA")


def test_non_media_files_are_not_guarded(repo: FakeRepo):
    guard.require_media_authorization(repo.root / PROTOCOL_REL, "HASH_RAW_MEDIA")


def test_unknown_operation_is_rejected_even_with_a_valid_record(repo: FakeRepo):
    repo.write()
    assert _denied(repo.video, "DELETE_EVERYTHING").code == "INVALID_OPERATION_TYPE"


def test_media_outside_repo_and_outside_temp_is_still_guarded(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setattr(guard, "REAL_REPO_ROOT", (tmp_path / "repo").resolve())
    monkeypatch.setattr(guard, "_system_temp_dirs", lambda: ())
    stray = tmp_path / "elsewhere.mov"
    stray.write_bytes(b"x")
    assert _denied(stray).code == "AUTH_MEDIA_ACCESS_NOT_GRANTED"


def test_absent_media_outside_the_repository_is_a_no_op_but_absent_media_inside_is_not(
    repo: FakeRepo, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(guard, "_system_temp_dirs", lambda: ())
    guard.require_media_authorization(Path("/nonexistent/elsewhere.wav"), "READ_RAW_MEDIA")
    ghost = repo.root / "data/raw/layer_b/v2" / EVENT / "ghost.mov"
    assert not ghost.exists()
    assert _denied(ghost).code == "AUTH_MEDIA_ACCESS_NOT_GRANTED"


def test_symlink_from_temp_to_real_media_is_guarded(repo: FakeRepo, tmp_path_factory):
    link = tmp_path_factory.mktemp("links") / "innocent.mov"
    os.symlink(repo.video, link)
    assert _denied(link).code == "AUTH_MEDIA_ACCESS_NOT_GRANTED"


def test_image_suffixes_are_guarded_at_reader_boundary(repo: FakeRepo):
    image = repo.video.with_suffix(".png")
    image.write_bytes(b"FAKE-IMAGE")
    assert _denied(image, "READ_RAW_MEDIA").code == "AUTH_MEDIA_ACCESS_NOT_GRANTED"


def test_repo_root_override_cannot_unlock_real_media(repo: FakeRepo, tmp_path_factory):
    shadow = FakeRepo(tmp_path_factory.mktemp("shadow") / "repo")
    shadow.write()  # a perfectly valid record, but in a different tree
    err = _denied(repo.video, repo_root=shadow.root)
    assert err.code == "AUTH_MEDIA_ACCESS_ROOT_OVERRIDE_REFUSED"


def test_relative_path_resolves_against_cwd_and_stays_guarded(repo: FakeRepo, monkeypatch):
    monkeypatch.chdir(repo.root)
    assert _denied(Path("data/raw/layer_b/v2") / EVENT / "camera_front.mov").code == (
        "AUTH_MEDIA_ACCESS_NOT_GRANTED"
    )


# ------------------------------------------------------------------ valid record


def test_valid_record_authorizes_exactly_its_scope(repo: FakeRepo):
    repo.write()
    guard.require_media_authorization(repo.video, "READ_RAW_MEDIA")
    guard.require_media_authorization(repo.video, "HASH_RAW_MEDIA", event_id=EVENT)


def test_record_is_reread_from_disk_on_every_call(repo: FakeRepo):
    repo.write()
    guard.require_media_authorization(repo.video, "READ_RAW_MEDIA")
    repo.record_path.unlink()
    assert _denied(repo.video).code == "AUTH_MEDIA_ACCESS_NOT_GRANTED"


def test_revocation_takes_effect_immediately(repo: FakeRepo):
    repo.write()
    guard.require_media_authorization(repo.video, "READ_RAW_MEDIA")
    record = json.loads(repo.record_path.read_text())
    record["revoked"] = True
    repo.write_raw(record)
    assert _denied(repo.video).code == "AUTH_MEDIA_ACCESS_INVALID"


def test_operation_level_precheck_never_authorizes_a_read(repo: FakeRepo):
    repo.write(
        scope={
            "operations": ["HASH_RAW_MEDIA"],
            "datasets": ["other"],
            "events": [EVENT],
            "media_types": ["audio"],
            "purpose": "synthetic fixture purpose for unit tests",
        }
    )
    guard.precheck_operation_authorized("HASH_RAW_MEDIA", repo_root=repo.root)  # record-level ok
    assert _denied(repo.video, "HASH_RAW_MEDIA").code == "AUTH_MEDIA_ACCESS_INVALID"


# ------------------------------------------------------------------ invalid records


def _mutations():
    def drop(key):
        return lambda r: r.pop(key)

    def setk(key, value):
        return lambda r: r.__setitem__(key, value)

    def scope(**kw):
        def apply(r):
            r["scope"] = {**r["scope"], **kw}

        return apply

    now = datetime.now(UTC)
    return {
        "wrong_schema": setk("schema_version", "phase5-media-access-authorization/1.0"),
        "extra_field": setk("allow_everything", True),
        "missing_field": drop("restrictions"),
        "wrong_class": setk("authorization_class", "AUTH-OTHER"),
        "not_approved": setk("status", "PENDING"),
        "revoked_true": setk("revoked", True),
        "revoked_string_true": setk("revoked", "true"),
        "revoked_null": setk("revoked", None),
        "revoked_zero": setk("revoked", 0),
        "naive_expiry": setk(
            "expires_at_utc", (now + timedelta(days=1)).replace(tzinfo=None).isoformat()
        ),
        "naive_issue": setk(
            "authorized_at_utc", (now - timedelta(days=1)).replace(tzinfo=None).isoformat()
        ),
        "expired": setk("expires_at_utc", (now - timedelta(minutes=1)).isoformat()),
        "issued_in_future": setk("authorized_at_utc", (now + timedelta(hours=2)).isoformat()),
        "expiry_before_issue": setk("expires_at_utc", (now - timedelta(days=3)).isoformat()),
        "garbage_expiry": setk("expires_at_utc", "next tuesday"),
        "signer_not_allowlisted": setk("authorized_by", "stranger@example.org"),
        "blank_signer": setk("authorized_by", "  "),
        "signature_present": setk(
            "attestation", {"type": "RECORDED_RESEARCHER_STATEMENT", "signature": "abc"}
        ),
        "wrong_attestation_type": setk("attestation", {"type": "PGP", "signature": None}),
        "bad_recorded_by": setk("recorded_by", {"kind": "robot", "identity": "x"}),
        "agent_without_source": setk(
            "recorded_by", {"kind": "agent_transcription", "identity": "claude"}
        ),
        "operation_not_granted": scope(operations=["MEDIA_PROBE"]),
        "unknown_operation_in_scope": scope(operations=["READ_RAW_MEDIA", "EXFILTRATE"]),
        "empty_operations": scope(operations=[]),
        "media_type_not_granted": scope(media_types=["audio"]),
        "dataset_out_of_scope": scope(datasets=["vision"]),
        "event_out_of_scope": scope(events=["train_events/event_002"]),
        "event_not_qualified": scope(events=["event_001"]),
        "duplicate_operations": scope(operations=["READ_RAW_MEDIA", "READ_RAW_MEDIA"]),
        "vague_purpose": scope(purpose="x"),
        "extra_scope_key": scope(everything=True),
        "path_prefix_miss": setk("restrictions", {"path_prefixes": ["data/raw/vision/"]}),
        "restrictions_extra_key": setk("restrictions", {"path_prefixes": [], "bypass": True}),
        "binding_wrong_hash": setk(
            "bindings", {"protocol_document": {"path": PROTOCOL_REL, "sha256": "0" * 64}}
        ),
        "binding_not_hex": setk(
            "bindings", {"protocol_document": {"path": PROTOCOL_REL, "sha256": "zz"}}
        ),
        "binding_missing_file": setk(
            "bindings", {"protocol_document": {"path": "docs/none.md", "sha256": "a" * 64}}
        ),
        "binding_outside_repo": setk(
            "bindings", {"protocol_document": {"path": "../outside.md", "sha256": "a" * 64}}
        ),
    }


@pytest.mark.parametrize("name", sorted(_mutations()))
def test_invalid_record_is_denied(repo: FakeRepo, name: str):
    record = repo.payload()
    _mutations()[name](record)
    repo.write_raw(record)
    assert _denied(repo.video, "READ_RAW_MEDIA").code == "AUTH_MEDIA_ACCESS_INVALID", name


def test_tampered_record_hash_is_denied(repo: FakeRepo):
    record = repo.payload()
    record["scope"]["events"] = ["train_events/event_999"]  # edit WITHOUT resealing
    repo.write_raw(record, reseal=False)
    err = _denied(repo.video)
    assert "record_sha256" in err.detail


def test_protocol_change_after_authorization_voids_it(repo: FakeRepo):
    repo.write()
    (repo.root / PROTOCOL_REL).write_text("protocol v2\n", encoding="utf-8")
    assert "protocol document changed" in _denied(repo.video).detail


def test_malformed_json_is_denied(repo: FakeRepo):
    repo.record_path.write_text("{not json", encoding="utf-8")
    assert _denied(repo.video).code == "AUTH_MEDIA_ACCESS_MALFORMED"


def test_non_object_json_is_denied(repo: FakeRepo):
    repo.record_path.write_text("[1, 2]", encoding="utf-8")
    assert _denied(repo.video).code == "AUTH_MEDIA_ACCESS_INVALID"


def test_event_declared_must_match_the_path(repo: FakeRepo):
    repo.write(
        scope={
            "operations": ["READ_RAW_MEDIA"],
            "datasets": ["layer_b"],
            "events": ["train_events/event_001", "train_events/event_002"],
            "media_types": ["video"],
            "purpose": "synthetic fixture purpose for unit tests",
        }
    )
    assert "contradicts" in _denied(repo.video, event_id="train_events/event_002").detail


def test_all_events_scope_allows_any_event_in_the_dataset(repo: FakeRepo):
    repo.write(
        scope={
            "operations": ["READ_RAW_MEDIA"],
            "datasets": ["layer_b"],
            "events": ["ALL_EVENTS_IN_DATASETS"],
            "media_types": ["video"],
            "purpose": "synthetic fixture purpose for unit tests",
        }
    )
    guard.require_media_authorization(repo.video, "READ_RAW_MEDIA")


def test_per_event_scope_with_undeterminable_event_is_denied(repo: FakeRepo):
    odd = repo.root / "data/raw/layer_b/loose.mov"
    odd.write_bytes(b"x")
    repo.write()
    assert "cannot be determined" in _denied(odd).detail


def test_media_outside_data_raw_cannot_be_scoped(repo: FakeRepo):
    stray = repo.root / "elsewhere.mov"
    stray.write_bytes(b"x")
    repo.write()
    assert "not under data/raw" in _denied(stray).detail


def test_path_prefix_restriction_allows_matching_paths(repo: FakeRepo):
    repo.write(restrictions={"path_prefixes": ["data/raw/layer_b/v2/train_events/"]})
    guard.require_media_authorization(repo.video, "READ_RAW_MEDIA")


# ------------------------------------------------------------------ the openers themselves


def _no_auth_repo_media(repo: FakeRepo) -> Path:
    return repo.video


def test_hash_pair_refuses_before_reading(repo: FakeRepo):
    from railway_detection.annotation.promotion_gate import compute_media_sha256_pair

    with pytest.raises(MediaAccessAuthorizationError):
        compute_media_sha256_pair(repo.video, repo.video)


def test_generic_receipt_hash_refuses_media_but_hashes_metadata(repo: FakeRepo):
    from railway_detection.annotation import receipt

    with pytest.raises(MediaAccessAuthorizationError):
        receipt.sha256_file(repo.video)
    assert len(receipt.sha256_file(repo.root / PROTOCOL_REL)) == 64


def test_audio_extraction_refuses(repo: FakeRepo, tmp_path: Path):
    from railway_detection.data.audio_extractor import extract_audio_from_video

    with pytest.raises(MediaAccessAuthorizationError):
        extract_audio_from_video(repo.video, tmp_path / "out.wav")
    assert not (tmp_path / "out.wav").exists()


def test_media_inspection_and_frame_extraction_refuse(repo: FakeRepo, tmp_path: Path):
    from railway_detection.annotation import media_inspector

    with pytest.raises(MediaAccessAuthorizationError):
        media_inspector.inspect_media_file(repo.video)
    with pytest.raises(MediaAccessAuthorizationError):
        media_inspector.compute_file_sha256(repo.video)
    with pytest.raises(MediaAccessAuthorizationError):
        media_inspector.extract_frame_at_timestamp(repo.video, 1.0, tmp_path / "f.jpg")


def test_frame_generator_refuses_on_first_iteration(repo: FakeRepo):
    from railway_detection.vision.video import frame_generator

    with pytest.raises(MediaAccessAuthorizationError):
        next(iter(frame_generator(repo.video)))


def test_wav_loader_refuses(repo: FakeRepo):
    from railway_detection.audio.preprocessor import load_wav

    with pytest.raises(MediaAccessAuthorizationError):
        load_wav(repo.audio)


def test_cli_audio_extract_refuses_through_the_library_guard(repo: FakeRepo, tmp_path: Path):
    import argparse

    from railway_detection.cli.main import _audio_extract

    args = argparse.Namespace(
        video_path=str(repo.video),
        output_wav=str(tmp_path / "o.wav"),
        sample_rate=16000,
        repository_root=str(repo.root),
    )
    assert _audio_extract(args) == 1


def test_direct_script_functions_refuse(repo: FakeRepo):
    scripts_dir = str(Path(__file__).resolve().parents[2])
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    module = importlib.import_module("scripts.run_phase5_full_inference")
    with pytest.raises(MediaAccessAuthorizationError):
        module.get_file_sha256(repo.video)
    with pytest.raises(MediaAccessAuthorizationError):
        module.get_stream_duration(repo.video)


def test_authorized_synthetic_media_is_readable_through_the_hash_pair(repo: FakeRepo):
    from railway_detection.annotation.promotion_gate import compute_media_sha256_pair

    repo.write()
    digests = compute_media_sha256_pair(repo.video, repo.video)
    assert digests["front"] == hashlib.sha256(b"FAKE-VIDEO").hexdigest()


def test_authorization_not_covering_the_operation_still_blocks_the_opener(
    repo: FakeRepo, tmp_path: Path
):
    from railway_detection.data.audio_extractor import extract_audio_from_video

    repo.write()  # grants READ/HASH/PROBE only, video only
    with pytest.raises(MediaAccessAuthorizationError):
        extract_audio_from_video(repo.video, tmp_path / "x.wav")


def test_record_is_not_mutated_by_verification(repo: FakeRepo):
    original = repo.write()
    before = copy.deepcopy(original)
    guard.require_media_authorization(repo.video, "READ_RAW_MEDIA")
    assert json.loads(repo.record_path.read_text()) == before
