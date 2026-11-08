# ruff: noqa: E501
"""Mission 10 / WP10.5: the back-stream scope of the descriptive cache-only engine, stated as tests.

Only front-stream conditions exist in ``cache_only_engine``. The back-stream condition names found in
the proposed protocol (``B0_back``, ``B0_back_stateless``, ``B2_back``, DEC-B05) are PROVISIONAL and
undecided, and ``B0_dual`` / stateless variants appear in no adopted document; none is implemented
here, and the engine must refuse them rather than silently substitute a front stream. The official
Phase 12 producer is the path that scores back-camera M4/M5, through an independent ``back`` system.
Synthetic only.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_cache_only_replay import _build_valid_cache_fixture

from railway_detection.evaluation import cache_only_engine as engine_module
from railway_detection.evaluation.cache_only_engine import CacheOnlyReplayEngine, CacheReplayRefusal
from railway_detection.evaluation.replay_evidence import MODE_FORBIDDEN, MODE_REQUIRED, STREAM_SPEC

UNDECIDED_OR_UNADOPTED = (
    "B0_back",
    "B0_back_stateless",
    "B2_back",
    "B0_dual",
    "B2_dual",
    "B0_stateless",
    "B3",
    "B4",
)


def test_engine_supports_exactly_the_three_front_conditions():
    assert engine_module.SUPPORTED_CONDITIONS == {"B0", "B1", "B2"}
    assert set(engine_module.CONDITION_STREAMS) == {"B0", "B1", "B2"}
    assert set(engine_module.SOURCE_IDS) == {"front_vision", "front_audio"}


@pytest.mark.parametrize("condition", UNDECIDED_OR_UNADOPTED)
def test_undecided_condition_names_are_refused_not_substituted(tmp_path, condition):
    manifest = _build_valid_cache_fixture(tmp_path)
    engine = CacheOnlyReplayEngine(manifest, repo_root=tmp_path)
    event = engine.list_events()[0]
    with pytest.raises(CacheReplayRefusal) as info:
        engine.execute_replay(event, condition)
    assert info.value.code == "UNSUPPORTED_CONDITION"


def test_cache_manifest_has_no_back_stream_cache_field():
    source = engine_module.__file__
    text = open(source, encoding="utf-8").read()
    assert "back_vision_cache" not in text and "back_audio_cache" not in text


def test_official_producer_stream_contract_has_an_independent_back_camera_stream():
    """The official path models the back camera as its own vision stream with its own clock."""
    assert STREAM_SPEC["back_vision"] == ("camera_2", STREAM_SPEC["back_vision"][1])
    assert "back_vision" in MODE_REQUIRED["independent_camera"]
    assert "back_vision" in MODE_REQUIRED["dual_camera"]
    assert "back_vision" in MODE_FORBIDDEN["single_camera"]
    assert "back_vision" not in MODE_REQUIRED["single_camera"]
