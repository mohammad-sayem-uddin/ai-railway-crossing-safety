"""Mission 14 (WP14.3): one canonicalisation approach for every authorization-sensitive path.

All trees are synthetic temporary directories.  Case-variant tests skip (with a reason) on a
case-sensitive filesystem, where a different spelling really is a different directory.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from security_support import (  # noqa: E402
    case_variant,
    filesystem_is_case_insensitive,
    make_fake_repo,
    outside_dir,
)

from railway_detection.safety import path_identity as pid  # noqa: E402


@pytest.fixture
def repo(tmp_path_factory, monkeypatch):
    return make_fake_repo(tmp_path_factory, monkeypatch, name="CaseRepo")


def need_case_insensitive(path: Path) -> None:
    if not filesystem_is_case_insensitive(path):
        pytest.skip("case-sensitive filesystem: a case variant is a different directory")


# ----------------------------------------------------------------------- canonical_path


def test_canonical_path_resolves_existing_components_and_keeps_a_nonexistent_tail(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    os.symlink(real, link)
    out = pid.canonical_path(link / "new" / "file.bin")
    assert out == real.resolve() / "new" / "file.bin"
    assert not out.exists()


def test_canonical_path_is_absolute_for_relative_input(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert pid.canonical_path("a/../b.txt") == tmp_path.resolve() / "b.txt"


@pytest.mark.parametrize("bad", ["", "   ", "x\x00y"])
def test_canonical_path_refuses_unusable_text(bad):
    with pytest.raises(pid.PathIdentityError) as info:
        pid.canonical_path(bad)
    assert info.value.code == "PATH_INVALID"


def test_canonical_path_refuses_bytes_and_non_paths():
    with pytest.raises(pid.PathIdentityError):
        pid.canonical_path(b"/tmp/x")
    with pytest.raises(pid.PathIdentityError):
        pid.canonical_path(None)  # type: ignore[arg-type]


def test_symlink_loop_is_unresolvable(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    os.symlink(b, a)
    os.symlink(a, b)
    with pytest.raises(pid.PathIdentityError) as info:
        pid.canonical_path(a / "x")
    assert info.value.code == "PATH_UNRESOLVABLE"


# --------------------------------------------------------------------- containment


def test_within_is_not_a_string_prefix_test(tmp_path):
    root = tmp_path / "repo"
    sibling = tmp_path / "repo2"
    root.mkdir()
    sibling.mkdir()
    assert pid.is_within(root / "a" / "b", root)
    assert pid.is_within(root, root)
    assert not pid.is_within(root, root, include_root=False)
    assert not pid.is_within(sibling / "a", root)  # "repo2" starts with "repo"
    assert not pid.is_within(tmp_path, root)  # a parent is not inside its child


def test_within_follows_symlinks_in_both_directions(tmp_path):
    root = tmp_path / "root"
    inside = root / "inside"
    inside.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    os.symlink(outside, inside / "escape")
    os.symlink(root, tmp_path / "alias_of_root")
    assert not pid.is_within(inside / "escape" / "f.txt", root)
    assert pid.is_within(tmp_path / "alias_of_root" / "inside" / "f.txt", root)


def test_within_handles_case_variants_of_existing_and_nonexistent_paths(repo):
    need_case_insensitive(repo.root)
    variant = case_variant(repo.root)
    assert pid.is_same_location(variant, repo.root)
    assert pid.is_within(variant / "data" / "raw" / "ghost.bin", repo.root)
    assert pid.is_within(repo.root / "DATA" / "RAW" / "ghost.bin", repo.root / "data" / "raw")
    assert pid.relative_parts(variant / "DATA" / "x", repo.root) == ("DATA", "x")


def test_within_falls_back_to_folded_spelling_when_the_reference_tree_is_absent(tmp_path):
    ghost_root = tmp_path / "NeverCreated"
    assert pid.is_within(tmp_path / "nevercreated" / "a", ghost_root)  # over-matches: fail closed
    assert not pid.is_within(tmp_path / "other" / "a", ghost_root)


def test_relative_parts_for_paths_outside_the_root_is_none(tmp_path):
    root = tmp_path / "r"
    root.mkdir()
    assert pid.relative_parts(tmp_path / "x", root) is None
    assert pid.relative_parts(root / "a" / "b", root) == ("a", "b")


# ------------------------------------------------------------- untrusted relative paths


@pytest.fixture
def served(tmp_path):
    root = tmp_path / "served"
    (root / "sub").mkdir(parents=True)
    (root / "ok.png").write_bytes(b"png")
    (root / "sub" / "deep.json").write_text("{}", encoding="utf-8")
    (tmp_path / "secret.png").write_bytes(b"secret")
    return root


def resolve(root, text, **kw):
    return pid.resolve_untrusted_relative(root, text, **kw)


def code_of(root, text, **kw) -> str:
    with pytest.raises(pid.PathIdentityError) as info:
        resolve(root, text, **kw)
    return info.value.code


def test_allowed_relative_paths_resolve(served):
    assert resolve(served, "ok.png") == served.resolve() / "ok.png"
    assert resolve(served, "sub/deep.json") == served.resolve() / "sub" / "deep.json"
    assert resolve(served, "./sub//deep.json") == served.resolve() / "sub" / "deep.json"
    assert resolve(served, "sub%2Fdeep.json") == served.resolve() / "sub" / "deep.json"


@pytest.mark.parametrize(
    "text",
    ["../secret.png", "sub/../../secret.png", "%2e%2e/secret.png", "%2E%2E%2Fsecret.png",
     "%252e%252e/secret.png", "%25252e%25252e%25252fsecret.png", "sub/%2e%2e/%2e%2e/secret.png",
     "..%2fsecret.png", "....//secret.png", "sub/..", ".. ", "..;/secret.png"],
)  # fmt: skip
def test_parent_traversal_in_every_encoding_is_refused(served, text):
    with pytest.raises(pid.PathIdentityError):
        resolve(served, text)  # the exact code varies ("..;" is just a missing literal name)


@pytest.mark.parametrize(
    "text",
    ["/etc/passwd", "//etc/passwd", "~/x", "C:/Windows/x", "%2fetc%2fpasswd", "%252fetc"],
)
def test_absolute_forms_are_refused(served, text):
    assert code_of(served, text) == "PATH_ABSOLUTE"


@pytest.mark.parametrize(
    "text",
    [
        "sub\\deep.json",
        "..\\secret.png",
        "sub%5cdeep.json",
        "%5c%5cserver%5cshare",
        "a\x00b",
        "ok.png%00.json",
        "ok\n.png",
        "%0d%0aok.png",
    ],
)
def test_backslashes_nul_and_control_characters_are_refused(served, text):
    assert code_of(served, text) == "PATH_INVALID"


def test_over_encoded_input_is_refused(served):
    text = "ok.png"
    for _ in range(6):
        text = text.replace("%", "%25").replace(".", "%2e")
    assert code_of(served, text) == "PATH_OVER_ENCODED"


def test_symlink_escape_is_refused_for_files_and_directories(served, tmp_path):
    os.symlink(tmp_path / "secret.png", served / "link.png")
    os.symlink(tmp_path, served / "dirlink")
    assert code_of(served, "link.png") == "PATH_OUTSIDE_ROOT"
    assert code_of(served, "dirlink/secret.png") == "PATH_OUTSIDE_ROOT"


def test_an_internal_symlink_that_stays_inside_the_root_is_allowed(served):
    os.symlink(served / "sub" / "deep.json", served / "alias.json")
    assert resolve(served, "alias.json") == served.resolve() / "sub" / "deep.json"


def test_suffix_allowlist_existence_and_directories(served):
    assert code_of(served, "ok.png", allowed_suffixes=[".json"]) == "PATH_TYPE_NOT_ALLOWED"
    assert resolve(served, "ok.png", allowed_suffixes=[".PNG"]).name == "ok.png"  # case-insensitive
    assert code_of(served, "missing.png") == "PATH_NOT_FOUND"
    assert code_of(served, "sub") == "PATH_NOT_FOUND"  # a directory is not a servable file
    assert resolve(served, "sub", must_exist=False).name == "sub"


def test_case_variant_of_an_allowed_directory_is_the_same_resource(served):
    need_case_insensitive(served)
    assert resolve(served, "SUB/DEEP.JSON") == (served / "SUB" / "DEEP.JSON").resolve()


# ----------------------------------------------- consumers use identity, not spelling


def test_checked_output_dir_refuses_protected_trees_in_every_spelling(repo, tmp_path_factory):
    from railway_detection.evaluation.evaluation_runner import (
        EvaluationRefused,
        Phase12EvaluationRunner,
    )

    check = Phase12EvaluationRunner._checked_output_dir
    safe = outside_dir(tmp_path_factory, "results") / "official_run"
    assert check(repo.root, safe) == safe.resolve()
    spellings = [repo.root / "data/ground_truth/new_run", repo.root / "configs/new",
                 repo.root / "models/new", repo.root / "experiments/new",
                 repo.root / "data/governance/new", repo.root / "data/raw/new",
                 repo.root / "data/manifests/new", repo.root / "data/splits/new"]  # fmt: skip
    link = outside_dir(tmp_path_factory, "alias") / "to_gt"
    os.symlink(repo.root / "data/ground_truth", link)
    spellings.append(link / "via_symlink")
    if filesystem_is_case_insensitive(repo.root):
        spellings += [repo.root / "data/Ground_Truth/new_run", repo.root / "CONFIGS/new",
                      case_variant(repo.root) / "data/ground_truth/new_run"]  # fmt: skip
    for target in spellings:
        with pytest.raises(EvaluationRefused) as info:
            check(repo.root, target)
        assert info.value.code == "OUTPUT_DIR_PROTECTED", target


def test_output_dir_must_be_new_or_empty(repo, tmp_path_factory):
    from railway_detection.evaluation.evaluation_runner import (
        EvaluationRefused,
        Phase12EvaluationRunner,
    )

    full = outside_dir(tmp_path_factory, "full")
    (full / "keep.txt").write_text("x", encoding="utf-8")
    with pytest.raises(EvaluationRefused) as info:
        Phase12EvaluationRunner._checked_output_dir(repo.root, full)
    assert info.value.code == "OUTPUT_DIR_NOT_EMPTY"


def test_descriptive_gate_applies_to_every_spelling_of_the_real_repository(repo, tmp_path_factory):
    from railway_detection.evaluation import descriptive_exec_gate as gate

    touches = gate._touches_real_repository
    assert touches(repo.root)
    assert touches(repo.root / "data")  # a directory inside the checkout
    assert touches(repo.root.parent)  # the checkout's parent contains it
    alias = outside_dir(tmp_path_factory, "gatealias") / "repo_alias"
    os.symlink(repo.root, alias)
    assert touches(alias)
    assert not touches(outside_dir(tmp_path_factory, "disjoint"))  # a disjoint synthetic tree
    if filesystem_is_case_insensitive(repo.root):
        assert touches(case_variant(repo.root))
    assert touches("x\x00y")  # cannot be canonicalised -> treated as real (fail closed)


def test_descriptive_gate_refuses_a_case_variant_root_exactly_like_the_canonical_one(repo):
    from railway_detection.evaluation import descriptive_exec_gate as gate

    roots = [repo.root]
    if filesystem_is_case_insensitive(repo.root):
        roots.append(case_variant(repo.root))
    for root in roots:
        with pytest.raises(gate.DescriptiveExecutionNotAuthorized):
            gate.require_descriptive_authorization_for_engine(
                root, condition=None, event_id="train_events/event_001", manifest_sha256="0" * 64
            )


def test_a_disjoint_synthetic_root_is_not_gated(tmp_path_factory, monkeypatch):
    from railway_detection.evaluation import descriptive_exec_gate as gate

    make_fake_repo(tmp_path_factory, monkeypatch)
    gate.require_descriptive_authorization_for_engine(
        outside_dir(tmp_path_factory, "synthetic_tree"),
        condition=None,
        event_id="e",
        manifest_sha256="0" * 64,
    )


def test_cache_paths_cannot_escape_the_engine_root_by_symlink_traversal_or_case(
    repo, tmp_path_factory
):
    from railway_detection.evaluation.cache_only_engine import (
        CacheReplayRefusal,
        _validate_cache_path,
    )

    cache_dir = repo.root / "data/processed/cache"
    cache_dir.mkdir(parents=True)
    (cache_dir / "ok.jsonl").write_text("{}\n", encoding="utf-8")
    assert _validate_cache_path("data/processed/cache/ok.jsonl", repo.root).name == "ok.jsonl"
    outside = outside_dir(tmp_path_factory, "cache_out")
    (outside / "stolen.jsonl").write_text("{}\n", encoding="utf-8")
    os.symlink(outside, cache_dir / "escape")
    for bad in ("data/processed/cache/escape/stolen.jsonl", "../x.jsonl", "/etc/x.jsonl"):
        with pytest.raises(CacheReplayRefusal):
            _validate_cache_path(bad, repo.root)
    if filesystem_is_case_insensitive(repo.root):
        assert (
            _validate_cache_path(
                "DATA/Processed/CACHE/ok.jsonl", case_variant(repo.root)
            ).name.lower()
            == "ok.jsonl"
        )


def test_synthetic_experiment_outputs_cannot_target_official_trees(repo, monkeypatch):
    from railway_detection.evaluation import experiment_engine as engine

    monkeypatch.setattr(engine, "_REPOSITORY_ROOT", repo.root)
    for rel in ("results/x", "experiments/x", "data/x", "configs/x", "models/x"):
        with pytest.raises(engine.ExperimentPlanError):
            engine._refuse_official_locations(repo.root / rel)
    if filesystem_is_case_insensitive(repo.root):
        with pytest.raises(engine.ExperimentPlanError):
            engine._refuse_official_locations(repo.root / "Results" / "x")


def test_pilot_checkout_identity_is_not_spelling_sensitive(repo, monkeypatch):
    from railway_detection.annotation import stage21_timing_pilot as pilot

    monkeypatch.setattr(pilot, "_REPOSITORY_ROOT", repo.root)
    assert pilot._is_real_checkout(repo.root)
    assert not pilot._is_real_checkout(repo.root / "data")
    if filesystem_is_case_insensitive(repo.root):
        assert pilot._is_real_checkout(case_variant(repo.root))
