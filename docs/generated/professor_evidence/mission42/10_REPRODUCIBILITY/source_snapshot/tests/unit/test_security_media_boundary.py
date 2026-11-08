"""Mission 14 (WP14.1): the centralised media-access boundary, tested on synthetic trees only.

A fake repository is built in a temporary directory and ``media_guard.REAL_REPO_ROOT`` is pointed
at it, so no test touches the real checkout.  Every "denied" test also proves the denial happened
*before* the protected operation (a tripwire on the reader/hasher/subprocess is never reached).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from security_support import (  # noqa: E402
    FakeRepo,
    case_variant,
    filesystem_is_case_insensitive,
    make_fake_repo,
    outside_dir,
)

from railway_detection.safety import media_guard as guard  # noqa: E402
from railway_detection.safety.media_guard import (  # noqa: E402
    MediaAccessAuthorizationError,
    classify_resource,
    require_media_authorization,
    require_media_command_authorization,
    require_unprotected_output,
)

NOT_GRANTED = "AUTH_MEDIA_ACCESS_NOT_GRANTED"

MEDIA_SUFFIXES = [
    ".jpg", ".jpeg", ".png", ".mp4", ".mov", ".wav", ".mp3", ".m2ts", ".ts", ".3gp", ".wmv",
    ".flv", ".gif", ".heic", ".mxf", ".avi", ".mkv", ".flac", ".m4a", ".webm", ".tiff", ".dng",
]  # fmt: skip


@pytest.fixture
def repo(tmp_path_factory, monkeypatch) -> FakeRepo:
    return make_fake_repo(tmp_path_factory, monkeypatch)


def denied(path, op="READ_RAW_MEDIA", **kw) -> MediaAccessAuthorizationError:
    with pytest.raises(MediaAccessAuthorizationError) as info:
        require_media_authorization(path, op, **kw)
    return info.value


def boom(*_a, **_k):
    raise AssertionError("protected operation reached")


# ----------------------------------------------------------------- suffix and name handling


@pytest.mark.parametrize("suffix", MEDIA_SUFFIXES)
def test_every_media_suffix_is_denied_in_the_repository_even_outside_data_raw(repo, suffix):
    target = repo.root / "outputs" / f"clip{suffix}"
    target.write_bytes(b"x")
    assert denied(target).code == NOT_GRANTED


@pytest.mark.parametrize(
    "name",
    ["clip", "clip.bin", "clip.dat", "clip.mov.bak", "CLIP.MOV", "clip.json.mov", "clip.zip",
     "clip.m2ts", "clip.unknownext"],
)  # fmt: skip
def test_any_name_under_data_raw_is_denied_not_only_known_suffixes(repo, name):
    target = repo.raw_dir / name
    target.write_bytes(b"x")
    assert classify_resource(target).zone == "REPO_RAW"
    assert denied(target).code == NOT_GRANTED


def test_plain_text_metadata_under_data_raw_is_not_media_unless_the_reader_declares_media(repo):
    labels = repo.raw_dir / "labels.txt"
    labels.write_text("0 0.5 0.5 0.1 0.1", encoding="utf-8")
    meta = repo.raw_dir / "meta.json"
    meta.write_text("{}", encoding="utf-8")
    require_media_authorization(labels, "HASH_RAW_MEDIA")
    require_media_authorization(meta, "HASH_RAW_MEDIA")
    assert denied(meta, "HASH_RAW_MEDIA", declared_media=True).code == NOT_GRANTED


def test_a_media_file_is_not_safe_because_it_is_an_image_or_because_its_name_looks_synthetic(repo):
    decoy = repo.raw_dir / "synthetic_fixture_tmp_do_not_guard.jpg"
    decoy.write_bytes(b"x")
    assert denied(decoy).code == NOT_GRANTED


def test_non_media_repository_files_are_not_guarded(repo):
    for rel in ("configs/frozen.yaml", "data/manifests/x.json", "README.md", "src/mod.py"):
        require_media_authorization(repo.root / rel, "HASH_RAW_MEDIA")
        assert classify_resource(repo.root / rel).guarded is False


def test_declared_media_removes_the_suffix_test_for_extensionless_repository_files(repo):
    odd = repo.root / "outputs" / "clip_without_extension"
    odd.write_bytes(b"x")
    require_media_authorization(odd, "READ_RAW_MEDIA")  # undeclared: just a file
    assert denied(odd, declared_media=True).code == NOT_GRANTED


# --------------------------------------------------------- symlinks, traversal, canonicalisation


def test_symlink_alias_with_a_non_media_name_to_raw_media_is_denied(repo, tmp_path_factory):
    links = outside_dir(tmp_path_factory, "links")
    for alias in ("innocent.dat", "innocent", "innocent.txt", "innocent.json", "innocent.mov"):
        link = links / alias
        os.symlink(repo.video, link)
        assert denied(link).code == NOT_GRANTED, alias


def test_symlink_chain_and_directory_symlink_are_resolved(repo, tmp_path_factory):
    links = outside_dir(tmp_path_factory, "chain")
    first = links / "first"
    os.symlink(repo.raw_dir, first)  # directory symlink
    assert denied(first / "camera_front.mov").code == NOT_GRANTED
    second = links / "second.bin"
    os.symlink(first / "camera_back.mov", second)  # link to a path that traverses a link
    assert denied(second).code == NOT_GRANTED


def test_broken_symlink_into_raw_data_is_denied_and_broken_link_elsewhere_is_inert(
    repo, tmp_path_factory
):
    links = outside_dir(tmp_path_factory, "broken")
    into_raw = links / "ghost"
    os.symlink(repo.raw_dir / "not_there.bin", into_raw)
    assert not into_raw.exists()
    assert denied(into_raw).code == NOT_GRANTED
    elsewhere = links / "dangling.mov"
    os.symlink(links / "missing_target", elsewhere)
    require_media_authorization(elsewhere, "READ_RAW_MEDIA")  # synthetic temp, nothing to read


def test_symlink_loop_fails_closed_with_a_safe_error(repo, tmp_path_factory):
    links = outside_dir(tmp_path_factory, "loop")
    a, b = links / "a", links / "b"
    os.symlink(b, a)
    os.symlink(a, b)
    err = denied(a / "x.mov")
    assert err.code == "AUTH_MEDIA_PATH_UNRESOLVABLE"


def test_relative_and_absolute_traversal_are_canonicalised(repo, tmp_path_factory, monkeypatch):
    outside = outside_dir(tmp_path_factory, "trav")
    rel = os.path.relpath(repo.video, outside)
    assert ".." in rel
    assert denied(outside / rel).code == NOT_GRANTED
    monkeypatch.chdir(repo.root)
    assert denied(Path("data/raw/layer_b/v2") / "train_events/event_001/camera_front.mov").code == (
        NOT_GRANTED
    )
    assert denied(repo.root / "outputs" / ".." / "data/raw/layer_b/v2" / "train_events/event_001"
                  / "camera_front.mov").code == NOT_GRANTED  # fmt: skip
    assert denied(str(repo.video).replace("/data/", "//data/./")).code == NOT_GRANTED


def test_nul_byte_and_empty_paths_fail_closed(repo):
    assert denied("clip\x00.mov").code == "AUTH_MEDIA_PATH_UNRESOLVABLE"
    assert denied("").code == "AUTH_MEDIA_PATH_UNRESOLVABLE"


def test_case_variant_repository_path_gets_the_same_decision(tmp_path_factory, monkeypatch):
    repo = make_fake_repo(tmp_path_factory, monkeypatch, name="MixedCaseRepo")
    if not filesystem_is_case_insensitive(repo.root):
        pytest.skip("filesystem is case sensitive: a case variant is a different directory")
    variant_root = case_variant(repo.root)
    variant_video = variant_root / "data/raw/layer_b/v2/train_events/event_001/camera_front.mov"
    assert variant_video.exists()
    assert classify_resource(variant_video).zone == "REPO_RAW"
    assert denied(variant_video).code == NOT_GRANTED
    # A case-variant spelling of a directory *inside* the repository, and of a nonexistent file.
    assert denied(repo.root / "DATA" / "RAW" / "layer_b" / "ghost.bin").code == NOT_GRANTED
    assert denied(variant_root / "data" / "raw" / "ghost").code == NOT_GRANTED


# ------------------------------------------------------- synthetic fixtures and non-existence


def test_synthetic_temporary_media_is_allowed_by_location_not_by_name(repo, tmp_path_factory):
    synth = outside_dir(tmp_path_factory, "synthetic")
    for name in ("clip.mp4", "frame.jpg", "audio.wav", "clip", "clip.m2ts", "x.bin"):
        target = synth / name
        target.write_bytes(b"x")
        require_media_authorization(target, "READ_RAW_MEDIA", declared_media=True)
        assert classify_resource(target).zone == "SYNTHETIC_TEMP"


def test_nonexistent_targets(repo, tmp_path_factory, monkeypatch):
    # inside the repository an absent media path is still refused
    assert denied(repo.raw_dir / "absent.mov").code == NOT_GRANTED
    # inside temp: nothing protected
    require_media_authorization(outside_dir(tmp_path_factory) / "absent.mov", "READ_RAW_MEDIA")
    # external and absent: there are no bytes to protect (documented behaviour)
    monkeypatch.setattr(guard, "_system_temp_dirs", lambda: ())
    require_media_authorization(Path("/nonexistent/elsewhere/clip.mov"), "READ_RAW_MEDIA")


def test_external_existing_media_and_unknown_files_are_guarded(repo, tmp_path_factory, monkeypatch):
    monkeypatch.setattr(guard, "_system_temp_dirs", lambda: ())
    ext = outside_dir(tmp_path_factory, "external")
    for name in ("clip.mov", "clip", "clip.m2ts", "clip.weird"):
        target = ext / name
        target.write_bytes(b"x")
        assert denied(target).code == NOT_GRANTED, name
    plain = ext / "notes.txt"
    plain.write_text("hello", encoding="utf-8")
    require_media_authorization(plain, "HASH_RAW_MEDIA")


# ----------------------------------------------------------------- environment cannot override


def test_environment_variables_cannot_grant_access_or_redefine_temp(
    repo, tmp_path_factory, monkeypatch
):
    ext = outside_dir(tmp_path_factory, "envdir")
    target = ext / "clip.mov"
    target.write_bytes(b"x")
    monkeypatch.setattr(guard, "_TEMP_ROOT_CANDIDATES", ())  # no standard temp root
    for key in ("AUTH_MEDIA_ACCESS", "RAILWAY_ALLOW_MEDIA", "ALLOW_RAW_MEDIA", "CI", "PYTEST"):
        monkeypatch.setenv(key, "1")
    monkeypatch.setenv("TMPDIR", str(ext))
    monkeypatch.setattr("tempfile.tempdir", None)
    assert denied(target).code == NOT_GRANTED
    assert denied(repo.video).code == NOT_GRANTED


def test_repo_root_override_cannot_unlock_real_repository_media(repo, tmp_path_factory):
    shadow = outside_dir(tmp_path_factory, "shadow")
    assert denied(repo.video, repo_root=shadow).code == "AUTH_MEDIA_ACCESS_ROOT_OVERRIDE_REFUSED"
    variant = repo.root.parent / (repo.root.name + "/.")
    assert denied(repo.video, repo_root=variant).code == NOT_GRANTED  # same root, not an override


# --------------------------------------- rejection happens before the protected operation


def test_hashing_is_refused_before_the_file_is_opened(repo, monkeypatch):
    from railway_detection.evaluation import input_contracts as ic

    with monkeypatch.context() as patch:
        patch.setattr(os, "open", boom)
        with pytest.raises(MediaAccessAuthorizationError):
            ic.sha256_file(repo.video)
        with pytest.raises(MediaAccessAuthorizationError):
            ic._read_source_bytes_and_hash(repo.video)


def test_validator_and_manifest_refuse_before_any_image_reader(repo, monkeypatch):
    from railway_detection.data import manifest as manifest_module
    from railway_detection.data import validator as validator_module

    image = repo.raw_dir / "frame.jpg"
    image.write_bytes(b"x")
    with monkeypatch.context() as patch:
        patch.setattr(validator_module.Image, "open", boom)
        patch.setattr(manifest_module.Image, "open", boom)
        patch.setattr(validator_module.Path, "open", boom)
        for call in (
            validator_module._check_image,
            validator_module._read_dimensions,
            validator_module._file_sha256,
        ):
            with pytest.raises(MediaAccessAuthorizationError):
                call(image)
        # the dataset builders propagate the denial instead of "excluding an unreadable image"
        with pytest.raises(MediaAccessAuthorizationError):
            manifest_module.build_vision_manifest(
                repo.raw_dir, repo.raw_dir, {"front": 0}, image_id_stem=None
            )


def test_video_audio_and_frame_readers_refuse_before_decoding(repo, monkeypatch):
    import cv2

    from railway_detection.annotation import media_inspector
    from railway_detection.data import audio_extractor
    from railway_detection.vision import video as video_module

    with monkeypatch.context() as patch:
        patch.setattr(subprocess, "run", boom)
        patch.setattr(subprocess, "Popen", boom)
        patch.setattr(cv2, "VideoCapture", boom)
        with pytest.raises(MediaAccessAuthorizationError):
            audio_extractor.extract_audio_from_video(repo.video, repo.root / "outputs" / "a.wav")
        with pytest.raises(MediaAccessAuthorizationError):
            media_inspector.extract_frame_at_timestamp(
                repo.video, 1.0, repo.root / "outputs" / "f.jpg"
            )
        with pytest.raises(MediaAccessAuthorizationError):
            media_inspector.inspect_media_file(repo.video)
        with pytest.raises(MediaAccessAuthorizationError):
            list(video_module.frame_generator(repo.video))


# ------------------------------------------------------------- commands and outputs


def test_ffmpeg_command_is_refused_before_launch_for_protected_inputs(repo, monkeypatch):
    cmd = ["/opt/homebrew/bin/ffmpeg", "-y", "-i", str(repo.video), "-vframes", "1",
           str(repo.root / "scratch" / "frame.jpg")]  # fmt: skip
    with monkeypatch.context() as patch:
        patch.setattr(subprocess, "run", boom)
        patch.setattr(subprocess, "Popen", boom)
        with pytest.raises(MediaAccessAuthorizationError) as info:
            require_media_command_authorization(cmd, "FRAME_EXTRACTION")
    assert info.value.code == NOT_GRANTED


def test_ffprobe_alias_input_and_odd_command_shapes(repo, tmp_path_factory):
    links = outside_dir(tmp_path_factory, "ffl")
    alias = links / "alias.dat"
    os.symlink(repo.video, alias)
    with pytest.raises(MediaAccessAuthorizationError):
        require_media_command_authorization(["ffprobe", "-v", "error", str(alias)], "MEDIA_PROBE")
    for bad in ([], ["curl", "x"], ["ffmpeg", "-version"]):
        with pytest.raises(MediaAccessAuthorizationError) as info:
            require_media_command_authorization(bad, "MEDIA_PROBE")
        assert info.value.code in {"MEDIA_COMMAND_UNRECOGNIZED", "MEDIA_COMMAND_NO_INPUT"}


def test_synthetic_inputs_to_media_commands_are_allowed(repo, tmp_path_factory):
    synth = outside_dir(tmp_path_factory, "ffsynth")
    clip = synth / "clip.mov"
    clip.write_bytes(b"x")
    require_media_command_authorization(
        ["ffmpeg", "-y", "-i", str(clip), "-vframes", "1", str(synth / "out.jpg")],
        "FRAME_EXTRACTION",
    )
    require_media_command_authorization(
        ["ffmpeg", "-i", str(clip), "-vn", "-f", "f32le", "pipe:1"], "AUDIO_EXTRACTION"
    )
    require_media_command_authorization(["ffprobe", "-v", "error", str(clip)], "MEDIA_PROBE")


def test_media_tools_cannot_write_into_evidence_trees(repo, tmp_path_factory):
    synth = outside_dir(tmp_path_factory, "ffout")
    clip = synth / "clip.mov"
    clip.write_bytes(b"x")
    for zone in ("data/raw/layer_b/new.jpg", "data/ground_truth/reviews/x.jpg", "configs/x.jpg",
                 "results/x.jpg", "experiments/vision/run1/x.jpg"):  # fmt: skip
        with pytest.raises(MediaAccessAuthorizationError) as info:
            require_media_command_authorization(
                ["ffmpeg", "-y", "-i", str(clip), str(repo.root / zone)], "FRAME_EXTRACTION"
            )
        assert info.value.code == "PROTECTED_OUTPUT_REFUSED", zone
    require_unprotected_output(repo.root / "scratch" / "frame.jpg")
    if filesystem_is_case_insensitive(repo.root):
        with pytest.raises(MediaAccessAuthorizationError):
            require_unprotected_output(repo.root / "DATA" / "Raw" / "new.jpg")


def test_observers_can_veto_and_see_the_canonical_path(repo):
    seen = []

    def observer(path, op):
        seen.append((path, op))

    guard.register_observer(observer)
    try:
        assert denied(repo.video).code == NOT_GRANTED
    finally:
        guard.unregister_observer(observer)
    assert seen and seen[0][0] == repo.video.resolve() and seen[0][1] == "READ_RAW_MEDIA"
