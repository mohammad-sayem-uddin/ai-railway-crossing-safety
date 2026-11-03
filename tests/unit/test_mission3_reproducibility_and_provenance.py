"""Mission 3 synthetic regression suite: Cache Provenance, Collision Matrix,
Experiment Configuration Reproducibility, Preflight Validation, and Stage-2.1 Readiness.

All tests operate strictly on synthetic in-memory fixtures and temporary directories
(`tmp_path`). No raw media files (`.mov`, `.mp4`, `.wav`) are opened, decoded, or hashed.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from railway_detection.annotation.evaluation_readiness_gate import evaluate_readiness
from railway_detection.annotation.promotion_gate import validate_for_promotion
from railway_detection.annotation.review_session import build_review_record
from railway_detection.annotation.stage2_1_schema import (
    STAGE_2_1_SCHEMA_VERSION,
    build_stage2_1_record_from_dict,
)
from railway_detection.data.contracts import EventLabel, LayerBEvent
from railway_detection.evaluation.descriptive_only import (
    DescriptiveOnlyInput,
    DescriptiveOnlyRefusal,
    aggregate_descriptive_only,
)
from railway_detection.evaluation.metrics import SingleEventEvaluation
from railway_detection.experiments.cache_provenance import (
    CACHE_REUSE_IDENTICAL_CONFIG,
    CACHE_REUSE_ISOLATED_RUN,
    CANONICAL_SERIALIZATION_VERSION,
    CONTROLLED_CACHE_SCHEMA_VERSION,
    HISTORICAL_DIAGNOSTIC_CACHE_CLASS,
    HISTORICAL_DIAGNOSTIC_UNVERIFIED,
    PROHIBITED_AUDIO_V2_SHA256,
    PROVENANCE_ENVELOPE_KEY,
    REQUIRED_PROVENANCE_FIELDS,
    CacheProvenanceError,
    ControlledCacheProvenance,
    build_audio_preprocessing_config,
    canonical_json_str,
    canonicalize_config,
    load_controlled_cache_jsonl,
    load_historical_diagnostic_cache_jsonl,
    resolve_checkpoint_identity,
    serialize_evidence_record,
    write_controlled_cache_jsonl,
)
from railway_detection.experiments.frozen_config import load_frozen_config
from railway_detection.experiments.layer_b_processor import LayerBEventProcessor
from railway_detection.experiments.preflight_validator import (
    CONFIG_CLASS_RESEARCHER_APPROVED,
    CONFIG_CLASS_SOFTWARE_DEFAULT,
    CONFIG_CLASS_UNRESOLVED,
    ExperimentConfigurationSpec,
    build_experiment_configuration_spec,
    classify_experiment_parameters,
    run_experiment_preflight,
)
from railway_detection.experiments.runner import BenchmarkCondition, ExperimentRunner
from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality

SYNTHETIC_VISION_SHA256 = (
    "3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd"
)
SYNTHETIC_AUDIO_V3_SHA256 = (
    "ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782"
)
ALT_CHECKPOINT_SHA256 = "a" * 64
SYNTHETIC_CONFIG_SHA256 = "b" * 64


def _make_provenance(**overrides: object) -> ControlledCacheProvenance:
    defaults: dict[str, object] = {
        "cohort": "train_events",
        "event_id": "event_001",
        "source_id": "camera_1",
        "modality": "vision",
        "model_architecture": "YOLOv8n_COCO_Pretrained",
        "checkpoint_sha256": SYNTHETIC_VISION_SHA256,
        "preprocessing_config": {
            "sampling_fps": 5.0,
            "image_size": [640, 640],
            "confidence_threshold_approach": 0.35,
            "confidence_threshold_departure": 0.25,
            "class_mapping": {"6": "train"},
        },
        "experiment_config_sha256": SYNTHETIC_CONFIG_SHA256,
        "failure_injector": "none",
        "injector_parameters": {},
        "timing_config": {
            "tick_s": 0.2,
            "source_staleness_s": 2.0,
            "window_tolerance_s": 0.25,
        },
        "cache_schema_version": CONTROLLED_CACHE_SCHEMA_VERSION,
        "software_version": "1.0.0-frozen",
        "run_id": "synthetic_run_001",
        "roi_config": {
            "roi_enabled": True,
            "polygon": [[0, 0], [640, 0], [640, 480], [0, 480]],
        },
        "git_commit": "d4db94d4a4ea83ae4c510d65dfc99c5d6798304b",
    }
    defaults.update(overrides)
    return ControlledCacheProvenance(**defaults)  # type: ignore[arg-type]


def _make_synthetic_records() -> list[EvidenceRecord]:
    return [
        EvidenceRecord(
            timestamp_s=0.2,
            source_id="camera_1",
            modality=Modality.VISION,
            available=True,
            detections=(
                Detection(
                    label="train",
                    confidence=0.88,
                    bbox_xyxy=(10.0, 20.0, 200.0, 300.0),
                ),
            ),
            metadata={"frame_index": 1},
        ),
        EvidenceRecord(
            timestamp_s=0.4,
            source_id="camera_1",
            modality=Modality.VISION,
            available=True,
            detections=(),
            metadata={"frame_index": 2},
        ),
    ]


# ===========================================================================
# 4.1 Provenance Hash Determinism & Canonicalization Tests
# ===========================================================================


def test_provenance_14_required_fields_contract_preserved() -> None:
    assert len(REQUIRED_PROVENANCE_FIELDS) == 14
    assert CANONICAL_SERIALIZATION_VERSION == "canonical-json/1.0"
    prov = _make_provenance()
    payload = prov.to_dict()
    for field_name in REQUIRED_PROVENANCE_FIELDS:
        assert field_name in payload


def test_provenance_hash_deterministic_across_nested_key_ordering() -> None:
    p1 = _make_provenance(
        preprocessing_config={
            "sampling_fps": 5.0,
            "confidence_threshold_approach": 0.35,
            "nested": {"z": 1, "a": 2, "m": [3, 2, 1]},
        },
        timing_config={
            "window_tolerance_s": 0.25,
            "source_staleness_s": 2.0,
            "tick_s": 0.2,
        },
    )
    p2 = _make_provenance(
        preprocessing_config={
            "nested": {"a": 2, "m": [3, 2, 1], "z": 1},
            "confidence_threshold_approach": 0.35,
            "sampling_fps": 5.0,
        },
        timing_config={
            "tick_s": 0.2,
            "source_staleness_s": 2.0,
            "window_tolerance_s": 0.25,
        },
    )
    assert p1.provenance_sha256() == p2.provenance_sha256()
    assert p1.configuration_sha256() == p2.configuration_sha256()
    assert p1.cache_identity_sha256() == p2.cache_identity_sha256()


def test_canonicalization_negative_zero_and_unknown_keys_preserved() -> None:
    cfg1 = canonicalize_config(
        {"offset": -0.0, "custom_research_param": {"beta": -0.0, "alpha": 1}}
    )
    cfg2 = canonicalize_config(
        {"custom_research_param": {"alpha": 1, "beta": 0.0}, "offset": 0.0}
    )
    assert canonical_json_str(cfg1) == canonical_json_str(cfg2)
    assert cfg1["custom_research_param"]["alpha"] == 1


@pytest.mark.parametrize("bad_val", [float("nan"), float("inf"), float("-inf")])
def test_canonicalization_rejects_non_finite_floats(bad_val: float) -> None:
    with pytest.raises(CacheProvenanceError) as exc_info:
        canonicalize_config({"threshold": bad_val})
    assert exc_info.value.code == "PROVENANCE_NONFINITE_NUMBER"


@pytest.mark.parametrize(
    "raw_media_ref",
    [
        "data/train_events/event_001/camera_front.mov",
        "clip.mp4",
        "track.wav",
    ],
)
def test_canonicalization_rejects_raw_media_paths_in_provenance(
    raw_media_ref: str,
) -> None:
    with pytest.raises(CacheProvenanceError) as exc_info:
        _make_provenance(preprocessing_config={"media_path": raw_media_ref})
    assert exc_info.value.code == "RAW_MEDIA_REFERENCE_FORBIDDEN"


# ===========================================================================
# 4.2 Model & Checkpoint Identity Collision Tests
# ===========================================================================


def test_checkpoint_hash_change_produces_collision_miss(tmp_path: Path) -> None:
    p_v1 = _make_provenance(checkpoint_sha256=SYNTHETIC_VISION_SHA256)
    p_v2 = _make_provenance(checkpoint_sha256=ALT_CHECKPOINT_SHA256)
    assert p_v1.provenance_sha256() != p_v2.provenance_sha256()
    assert p_v1.configuration_sha256() != p_v2.configuration_sha256()

    cache_path = write_controlled_cache_jsonl(tmp_path, p_v1, _make_synthetic_records())
    with pytest.raises(CacheProvenanceError) as exc_info:
        load_controlled_cache_jsonl(cache_path, p_v2)
    assert exc_info.value.code == "PROVENANCE_MISMATCH"


def test_prohibited_audio_v2_checkpoint_hash_and_path_rejected(tmp_path: Path) -> None:
    with pytest.raises(CacheProvenanceError) as exc_info:
        _make_provenance(
            modality="audio",
            source_id="audio_1",
            model_architecture="Audio_V2_Legacy",
            checkpoint_sha256=PROHIBITED_AUDIO_V2_SHA256,
        )
    assert exc_info.value.code == "PROHIBITED_CHECKPOINT_REJECTED"

    with pytest.raises(CacheProvenanceError) as path_exc:
        resolve_checkpoint_identity(
            tmp_path / "models" / "audio" / "best_checkpoint.pt",
            expected_sha256=SYNTHETIC_AUDIO_V3_SHA256,
        )
    assert path_exc.value.code == "PROHIBITED_CHECKPOINT_REJECTED"


@pytest.mark.parametrize(
    "unresolved_ckpt",
    ["yolov8n.pt", "best.pt", "pending", "unknown", "unresolved", "not_a_sha256_digest"],
)
def test_unresolved_or_filename_only_checkpoint_rejected(unresolved_ckpt: str) -> None:
    with pytest.raises(CacheProvenanceError) as exc_info:
        _make_provenance(checkpoint_sha256=unresolved_ckpt)
    assert exc_info.value.code in (
        "PROVENANCE_CHECKPOINT_UNRESOLVED",
        "PROVENANCE_CHECKPOINT_DIGEST_INVALID",
    )


def test_resolve_checkpoint_identity_and_raw_media_guard(tmp_path: Path) -> None:
    resolved = resolve_checkpoint_identity(
        "models/vision/yolov8n.pt",
        expected_sha256=SYNTHETIC_VISION_SHA256,
    )
    assert resolved["status"] == "RESOLVED"
    assert resolved["checkpoint_sha256"] == SYNTHETIC_VISION_SHA256

    with pytest.raises(CacheProvenanceError) as unres_exc:
        resolve_checkpoint_identity("models/vision/yolov8n.pt", expected_sha256=None)
    assert unres_exc.value.code == "PROVENANCE_CHECKPOINT_UNRESOLVED"

    raw_media_dummy = tmp_path / "camera_front.mov"
    with pytest.raises(CacheProvenanceError) as media_exc:
        resolve_checkpoint_identity(raw_media_dummy, expected_sha256=SYNTHETIC_VISION_SHA256)
    assert media_exc.value.code == "RAW_MEDIA_REFERENCE_FORBIDDEN"


# ===========================================================================
# 4.3 Preprocessing & ROI Collision Tests
# ===========================================================================


def test_vision_preprocessing_and_roi_collisions() -> None:
    base = _make_provenance()
    fps_changed = _make_provenance(
        preprocessing_config={**base.preprocessing_config, "sampling_fps": 10.0}
    )
    conf_approach_changed = _make_provenance(
        preprocessing_config={
            **base.preprocessing_config,
            "confidence_threshold_approach": 0.50,
        }
    )
    conf_departure_changed = _make_provenance(
        preprocessing_config={
            **base.preprocessing_config,
            "confidence_threshold_departure": 0.40,
        }
    )
    img_size_changed = _make_provenance(
        preprocessing_config={**base.preprocessing_config, "image_size": [1280, 1280]}
    )
    roi_polygon_changed = _make_provenance(
        roi_config={
            "roi_enabled": True,
            "polygon": [[10, 10], [600, 10], [600, 400], [10, 400]],
        }
    )
    roi_disabled = _make_provenance(roi_config={"roi_enabled": False})

    variants = [
        base,
        fps_changed,
        conf_approach_changed,
        conf_departure_changed,
        img_size_changed,
        roi_polygon_changed,
        roi_disabled,
    ]
    hashes = {v.provenance_sha256() for v in variants}
    config_hashes = {v.configuration_sha256() for v in variants}
    assert len(hashes) == len(variants)
    assert len(config_hashes) == len(variants)


def test_audio_preprocessing_collisions() -> None:
    frozen = load_frozen_config()
    base_audio_cfg = build_audio_preprocessing_config(frozen)
    p_base = _make_provenance(
        modality="audio",
        source_id="audio_1",
        model_architecture="CompactTrainHornCNN",
        checkpoint_sha256=SYNTHETIC_AUDIO_V3_SHA256,
        preprocessing_config=base_audio_cfg,
    )
    p_thresh = _make_provenance(
        modality="audio",
        source_id="audio_1",
        model_architecture="CompactTrainHornCNN",
        checkpoint_sha256=SYNTHETIC_AUDIO_V3_SHA256,
        preprocessing_config=build_audio_preprocessing_config(
            frozen, operating_threshold=0.50
        ),
    )
    p_window = _make_provenance(
        modality="audio",
        source_id="audio_1",
        model_architecture="CompactTrainHornCNN",
        checkpoint_sha256=SYNTHETIC_AUDIO_V3_SHA256,
        preprocessing_config=build_audio_preprocessing_config(frozen, window_s=2.0),
    )
    p_mels = _make_provenance(
        modality="audio",
        source_id="audio_1",
        model_architecture="CompactTrainHornCNN",
        checkpoint_sha256=SYNTHETIC_AUDIO_V3_SHA256,
        preprocessing_config=build_audio_preprocessing_config(
            frozen, extra={"n_mels": 128}
        ),
    )
    assert (
        len(
            {
                p_base.provenance_sha256(),
                p_thresh.provenance_sha256(),
                p_window.provenance_sha256(),
                p_mels.provenance_sha256(),
            }
        )
        == 4
    )


# ===========================================================================
# 4.4 Injector & Timing Collision Tests (including B7d and B7e Fail-Closed)
# ===========================================================================


def test_injector_and_timing_collisions_across_b5_b6_b7() -> None:
    p_none = _make_provenance(failure_injector="none", injector_parameters={})
    p_b5a = _make_provenance(
        failure_injector="B5a",
        injector_parameters={
            "target_source": "camera_1",
            "start_time_s": 0.0,
            "end_time_s": 999.0,
        },
    )
    p_b6b = _make_provenance(
        failure_injector="B6b",
        injector_parameters={
            "target_source": "both_cameras",
            "start_time_s": 5.0,
            "end_time_s": 15.0,
        },
    )
    p_b7d_seed1 = _make_provenance(
        failure_injector="B7d",
        injector_parameters={
            "seed": 42,
            "swap_window": 2,
            "perturbation_layer": "delivery",
        },
    )
    p_b7d_seed2 = _make_provenance(
        failure_injector="B7d",
        injector_parameters={
            "seed": 99,
            "swap_window": 2,
            "perturbation_layer": "delivery",
        },
    )
    p_b7e_cam1_3s = _make_provenance(
        failure_injector="B7e",
        injector_parameters={"delay_s": 3.0, "target_source": "camera_1"},
    )
    p_b7e_cam1_5s = _make_provenance(
        failure_injector="B7e",
        injector_parameters={"delay_s": 5.0, "target_source": "camera_1"},
    )
    p_b7e_cam2_3s = _make_provenance(
        failure_injector="B7e",
        injector_parameters={"delay_s": 3.0, "target_source": "camera_2"},
    )
    p_staleness_changed = _make_provenance(
        timing_config={
            "tick_s": 0.2,
            "source_staleness_s": 4.0,
            "window_tolerance_s": 0.25,
        }
    )

    all_provs = [
        p_none,
        p_b5a,
        p_b6b,
        p_b7d_seed1,
        p_b7d_seed2,
        p_b7e_cam1_3s,
        p_b7e_cam1_5s,
        p_b7e_cam2_3s,
        p_staleness_changed,
    ]
    assert len({p.provenance_sha256() for p in all_provs}) == len(all_provs)


@pytest.mark.parametrize(
    "missing_b7e_params",
    [
        {},
        {"delay_s": 2.5},
        {"target_source": "camera_1"},
        {"delay_s": -1.0, "target_source": "camera_1"},
        {"delay_s": 2.5, "target_source": ""},
    ],
)
def test_b7e_without_delay_s_or_target_source_fails_closed(
    missing_b7e_params: dict[str, object],
) -> None:
    with pytest.raises(CacheProvenanceError) as exc_info:
        _make_provenance(failure_injector="B7e", injector_parameters=missing_b7e_params)
    assert exc_info.value.code == "PROVENANCE_INJECTOR_INVALID"


# ===========================================================================
# 4.5 Event, Cohort, Source, Modality & Run Reuse Policy Tests
# ===========================================================================


def test_event_cohort_source_modality_and_run_id_separation(tmp_path: Path) -> None:
    p_train = _make_provenance(cohort="train_events", event_id="event_001")
    p_notrain = _make_provenance(cohort="no_train_events", event_id="event_001")
    p_engine = _make_provenance(cohort="engine_events", event_id="event_001")
    p_cam2 = _make_provenance(source_id="camera_2")
    p_audio = _make_provenance(
        source_id="audio_1",
        modality="audio",
        model_architecture="CompactTrainHornCNN",
        checkpoint_sha256=SYNTHETIC_AUDIO_V3_SHA256,
    )
    assert (
        len(
            {
                p_train.cache_identity_sha256(),
                p_notrain.cache_identity_sha256(),
                p_engine.cache_identity_sha256(),
                p_cam2.cache_identity_sha256(),
                p_audio.cache_identity_sha256(),
            }
        )
        == 5
    )

    # Same config & stream, different run_id
    p_run1 = _make_provenance(run_id="run_alpha")
    p_run2 = _make_provenance(run_id="run_beta")
    assert p_run1.configuration_sha256() == p_run2.configuration_sha256()
    assert p_run1.cache_identity_sha256() == p_run2.cache_identity_sha256()
    assert p_run1.provenance_sha256() != p_run2.provenance_sha256()

    cache_file = write_controlled_cache_jsonl(
        tmp_path, p_run1, _make_synthetic_records()
    )

    # Default policy CACHE_REUSE_ISOLATED_RUN rejects different run_id
    with pytest.raises(CacheProvenanceError) as isolated_exc:
        load_controlled_cache_jsonl(
            cache_file, p_run2, reuse_policy=CACHE_REUSE_ISOLATED_RUN
        )
    assert isolated_exc.value.code == "PROVENANCE_MISMATCH"

    # Explicit policy CACHE_REUSE_IDENTICAL_CONFIG allows reuse when config & stream match
    reused_records = load_controlled_cache_jsonl(
        cache_file, p_run2, reuse_policy=CACHE_REUSE_IDENTICAL_CONFIG
    )
    assert len(reused_records) == 2

    # Even under CACHE_REUSE_IDENTICAL_CONFIG, any config difference is rejected
    p_run2_diff_conf = _make_provenance(
        run_id="run_beta",
        preprocessing_config={**p_run1.preprocessing_config, "sampling_fps": 2.0},
    )
    with pytest.raises(CacheProvenanceError) as diff_exc:
        load_controlled_cache_jsonl(
            cache_file, p_run2_diff_conf, reuse_policy=CACHE_REUSE_IDENTICAL_CONFIG
        )
    assert diff_exc.value.code == "PROVENANCE_MISMATCH"


# ===========================================================================
# 4.6 Envelope, Duplicate JSON Key & Payload Corruption Tests
# ===========================================================================


def test_envelope_and_payload_corruption_rejected(tmp_path: Path) -> None:
    prov = _make_provenance()
    records = _make_synthetic_records()
    cache_path = write_controlled_cache_jsonl(tmp_path, prov, records)

    # 1. Empty file
    empty_path = tmp_path / "empty.jsonl"
    empty_path.write_text("", encoding="utf-8")
    with pytest.raises(CacheProvenanceError) as empty_exc:
        load_controlled_cache_jsonl(empty_path, prov)
    assert empty_exc.value.code == "CACHE_EMPTY"

    # 2. Missing header
    no_header_path = tmp_path / "no_header.jsonl"
    no_header_path.write_text(
        json.dumps(serialize_evidence_record(records[0])) + "\n", encoding="utf-8"
    )
    with pytest.raises(CacheProvenanceError) as no_hdr_exc:
        load_controlled_cache_jsonl(no_header_path, prov)
    assert no_hdr_exc.value.code == "HISTORICAL_UNVERIFIED_CACHE_REJECTED"

    # 3. Duplicate JSON keys in header
    dup_key_path = tmp_path / "dup_key.jsonl"
    dup_key_path.write_text(
        f'{{"{PROVENANCE_ENVELOPE_KEY}": {{"cohort": "train_events", "cohort": "no_train_events"}}}}\n',
        encoding="utf-8",
    )
    with pytest.raises(CacheProvenanceError) as dup_exc:
        load_controlled_cache_jsonl(dup_key_path, prov)
    assert dup_exc.value.code == "CACHE_DUPLICATE_JSON_KEY"

    # 4. Unsupported schema version
    lines = cache_path.read_text(encoding="utf-8").splitlines()
    hdr = json.loads(lines[0])
    hdr[PROVENANCE_ENVELOPE_KEY]["cache_schema_version"] = "controlled-cache-v99.0"
    bad_schema_path = tmp_path / "bad_schema.jsonl"
    bad_schema_path.write_text(
        "\n".join([json.dumps(hdr), *lines[1:]]) + "\n", encoding="utf-8"
    )
    with pytest.raises(CacheProvenanceError) as schema_exc:
        load_controlled_cache_jsonl(bad_schema_path, prov)
    assert schema_exc.value.code == "PROVENANCE_SCHEMA_VERSION_INVALID"

    # 5. Tampered detection payload line with intact header
    tampered_record = json.loads(lines[1])
    tampered_record["timestamp_s"] = 99.9
    tampered_payload_path = tmp_path / "tampered_payload.jsonl"
    tampered_payload_path.write_text(
        "\n".join([lines[0], json.dumps(tampered_record), *lines[2:]]) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(CacheProvenanceError) as payload_exc:
        load_controlled_cache_jsonl(tampered_payload_path, prov)
    assert payload_exc.value.code == "CACHE_PAYLOAD_CORRUPTED"

    # 6. Truncated record count with intact header
    truncated_path = tmp_path / "truncated.jsonl"
    truncated_path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(CacheProvenanceError) as trunc_exc:
        load_controlled_cache_jsonl(truncated_path, prov)
    assert trunc_exc.value.code == "CACHE_PAYLOAD_CORRUPTED"


# ===========================================================================
# 4.7 Historical Cache Compatibility & Descriptive-Only Provenance Enforcement
# ===========================================================================


def test_historical_cache_compatibility_and_descriptive_only_enforcement(
    tmp_path: Path,
) -> None:
    records = _make_synthetic_records()
    legacy_file = tmp_path / "train_events_event_001_camera_front_camera_1_vision.jsonl"
    legacy_file.write_text(
        "\n".join(json.dumps(serialize_evidence_record(r)) for r in records) + "\n",
        encoding="utf-8",
    )

    prov = _make_provenance()
    with pytest.raises(CacheProvenanceError) as ctrl_exc:
        load_controlled_cache_jsonl(legacy_file, prov)
    assert ctrl_exc.value.code == "HISTORICAL_UNVERIFIED_CACHE_REJECTED"

    loaded_legacy, diag_meta = load_historical_diagnostic_cache_jsonl(legacy_file)
    assert len(loaded_legacy) == 2
    assert diag_meta["cache_classification"] == HISTORICAL_DIAGNOSTIC_CACHE_CLASS
    assert diag_meta["provenance_status"] == HISTORICAL_DIAGNOSTIC_UNVERIFIED
    assert diag_meta["official_evaluation_eligible"] is False
    for r in loaded_legacy:
        assert r.metadata["cache_classification"] == HISTORICAL_DIAGNOSTIC_CACHE_CLASS
        assert r.metadata["provenance_status"] == HISTORICAL_DIAGNOSTIC_UNVERIFIED

    # Descriptive-only refuses controlled_experimental claim without valid ControlledCacheProvenance
    eval_item = SingleEventEvaluation(
        event_id="train_events/event_001",
        scenario_name="desc",
        has_train_ground_truth=True,
        missed_train=False,
        evaluable=True,
    )
    with pytest.raises(DescriptiveOnlyRefusal) as desc_exc:
        aggregate_descriptive_only(
            DescriptiveOnlyInput(
                event_evaluations=(eval_item,),
                population_label="synthetic_cohort",
                provenance={"cache_classification": "controlled_experimental"},
                limitations=("Synthetic test only",),
                permitted_claims=("Fixed-site synthetic descriptive summary only",),
            )
        )
    assert desc_exc.value.code == "CONTROLLED_PROVENANCE_REQUIRED"

    # Descriptive-only accepts valid ControlledCacheProvenance and rejects mismatched expected_cache_provenance
    valid_report = aggregate_descriptive_only(
        DescriptiveOnlyInput(
            event_evaluations=(eval_item,),
            population_label="synthetic_cohort",
            provenance={
                "cache_classification": "controlled_experimental",
                "cache_provenance": prov.to_dict(),
                "expected_cache_provenance": prov.to_dict(),
            },
            limitations=("Synthetic test only",),
            permitted_claims=("Fixed-site synthetic descriptive summary only",),
        )
    )
    assert valid_report.official_evaluation_eligible is False

    mismatched_prov = _make_provenance(run_id="other_run")
    with pytest.raises(DescriptiveOnlyRefusal) as mismatch_desc_exc:
        aggregate_descriptive_only(
            DescriptiveOnlyInput(
                event_evaluations=(eval_item,),
                population_label="synthetic_cohort",
                provenance={
                    "cache_classification": "controlled_experimental",
                    "cache_provenance": prov.to_dict(),
                    "expected_cache_provenance": mismatched_prov.to_dict(),
                },
                limitations=("Synthetic test only",),
                permitted_claims=("Fixed-site synthetic descriptive summary only",),
            )
        )
    assert mismatch_desc_exc.value.code == "CACHE_PROVENANCE_INVALID"


# ===========================================================================
# LayerBEventProcessor Provenance Integration Tests
# ===========================================================================


def test_layer_b_processor_build_stream_provenance_and_parameter_checks(
    tmp_path: Path,
) -> None:
    processor = LayerBEventProcessor(cache_dir=tmp_path)
    v_prov = processor.build_stream_provenance(
        cohort="train_events",
        event_id="event_001",
        source_id="camera_1",
        modality="vision",
        run_id="run_m3_01",
    )
    assert v_prov.model_architecture == processor.config.checkpoints.vision.model_name
    assert v_prov.preprocessing_config["image_size"] == [640, 640]
    assert v_prov.preprocessing_config["confidence_threshold_departure"] == 0.35

    a_prov = processor.build_stream_provenance(
        cohort="train_events",
        event_id="event_001",
        source_id="audio_1",
        modality="audio",
        run_id="run_m3_01",
    )
    assert a_prov.model_architecture == processor.config.checkpoints.audio_v3.model_name
    assert a_prov.preprocessing_config["n_mels"] == 64
    assert a_prov.preprocessing_config["n_fft"] == 512

    # Write controlled cache and load through run_vision_inference
    write_controlled_cache_jsonl(tmp_path, v_prov, _make_synthetic_records())
    loaded = processor.run_vision_inference(
        video_path=tmp_path / "train_events" / "event_001" / "camera_front.mov",
        checkpoint_path=tmp_path / "yolov8n.pt",
        source_id="camera_1",
        target_fps=v_prov.preprocessing_config["sampling_fps"],
        conf=v_prov.preprocessing_config["confidence_threshold_approach"],
        use_cache=True,
        provenance=v_prov,
    )
    assert len(loaded) == 2

    # Calling run_vision_inference with mismatched target_fps raises PROVENANCE_PREPROCESSING_MISMATCH
    with pytest.raises(CacheProvenanceError) as fps_exc:
        processor.run_vision_inference(
            video_path=tmp_path / "train_events" / "event_001" / "camera_front.mov",
            checkpoint_path=tmp_path / "yolov8n.pt",
            source_id="camera_1",
            target_fps=15.0,
            conf=0.35,
            use_cache=True,
            provenance=v_prov,
        )
    assert fps_exc.value.code == "PROVENANCE_PREPROCESSING_MISMATCH"


# ===========================================================================
# Section 5: Experiment Configuration Reproducibility & 5 Config Classes
# ===========================================================================


def test_experiment_configuration_classes_and_reconstructable_spec(
    tmp_path: Path,
) -> None:
    frozen = load_frozen_config()
    classifications = classify_experiment_parameters(
        frozen,
        experiment_family="B4",
        failure_injector="none",
        d1_approved=False,
        d2_approved=False,
        d4_approved=False,
    )
    by_key = {c.parameter_key: c.classification for c in classifications}
    assert by_key["checkpoints.vision"] == CONFIG_CLASS_RESEARCHER_APPROVED
    assert by_key["checkpoints.audio_v3"] == CONFIG_CLASS_RESEARCHER_APPROVED
    assert (
        by_key["clock_semantics.b7d_delivery_disorder"]
        == CONFIG_CLASS_RESEARCHER_APPROVED
    )
    assert (
        by_key["ground_truth_and_cohort_separation"]
        == CONFIG_CLASS_RESEARCHER_APPROVED
    )
    assert by_key["fusion_and_operating_thresholds"] == CONFIG_CLASS_UNRESOLVED
    assert by_key["roi_and_calibration_geometry"] == CONFIG_CLASS_UNRESOLVED
    assert by_key["timing.cross_camera_sync"] == CONFIG_CLASS_UNRESOLVED
    assert (
        by_key["temporal_and_state_machine_defaults"] == CONFIG_CLASS_SOFTWARE_DEFAULT
    )

    # Ensure software_default and unresolved_configuration are never labeled researcher_approved
    spec = build_experiment_configuration_spec(
        frozen,
        experiment_family="B4",
        condition_id="B4",
        run_id="synth_run_b4",
    )
    assert spec.configuration_class_summary == CONFIG_CLASS_UNRESOLVED
    roundtrip = ExperimentConfigurationSpec.from_dict(spec.to_dict())
    assert roundtrip.spec_sha256 == spec.spec_sha256
    assert roundtrip.to_dict() == spec.to_dict()

    # Verify ExperimentRunner writes reconstructable_experiment_spec in frozen_config_meta.json
    runner = ExperimentRunner(output_root=tmp_path, config=frozen, verify_safeguards=False)
    synth_event = LayerBEvent(
        event_id="train_events/event_001",
        camera_1_path=None,
        camera_2_path=None,
        labels=(
            EventLabel(
                name="T1_danger_zone_entry", timestamp_s=2.0, label_status="observable"
            ),
            EventLabel(
                name="T4_tail_clearance", timestamp_s=10.0, label_status="observable"
            ),
        ),
        train_type="passenger",
        metadata_status="verified_synthetic",
    )
    synth_frames = [
        MultimodalFrame(
            master_timestamp_s=0.0,
            vision_records=tuple(_make_synthetic_records()[:1]),
            audio_records=(),
        )
    ]
    runner.run_condition(
        BenchmarkCondition.B0,
        [(synth_event, synth_frames)],
        custom_output_dir=tmp_path / "B0_out",
        run_id="test_run_b0",
    )
    meta = json.loads(
        (tmp_path / "B0_out" / "frozen_config_meta.json").read_text(encoding="utf-8")
    )
    assert "reconstructable_experiment_spec" in meta
    reconstructed = ExperimentConfigurationSpec.from_dict(
        meta["reconstructable_experiment_spec"]
    )
    assert reconstructed.run_id == "test_run_b0"
    assert reconstructed.experiment_family == "B0"


# ===========================================================================
# Section 6 & 7: Non-Authoritative Preflight Validator & Fail-Closed Paths
# ===========================================================================


def test_preflight_validator_blocks_missing_prerequisites_and_never_grants_eval_auth(
    tmp_path: Path,
) -> None:
    frozen = load_frozen_config()

    # 1. Official evaluation mode without Stage-2.1, promotion, split, manifest, or EVAL-AUTH
    report = run_experiment_preflight(
        frozen,
        experiment_family="B4",
        condition_id="B4_official_attempt",
        evaluation_mode="official_evaluation",
        cache_dir=tmp_path,
    )
    assert report.grants_eval_auth is False
    assert report.grants_official_readiness is False
    assert report.is_diagnostic_only is True
    assert report.structurally_valid is True
    assert report.ready_for_requested_mode is False

    auth_codes = {f.code for f in report.missing_authorization_blockers}
    assert "STAGE2_1_HUMAN_ADJUDICATION_MISSING" in auth_codes
    assert "GROUND_TRUTH_PROMOTION_RECEIPT_MISSING" in auth_codes
    assert "OFFICIAL_EVENT_SPLIT_MISSING" in auth_codes
    assert "OFFICIAL_EVALUATION_MANIFEST_MISSING" in auth_codes
    assert "EVAL_AUTH_NOT_GRANTED" in auth_codes

    decision_codes = {f.code for f in report.unresolved_scientific_decision_blockers}
    assert "DECISION_D1_PENDING" in decision_codes
    assert "DECISION_D2_PENDING" in decision_codes
    assert "DECISION_D4_PENDING" in decision_codes

    # 2. B7e without delay_s/target_source fails closed in preflight
    b7e_report = run_experiment_preflight(
        frozen,
        experiment_family="B7e",
        condition_id="B7e",
        failure_injector="B7e",
        injector_parameters={},
    )
    assert b7e_report.ready_for_requested_mode is False
    assert any(
        f.code == "B7E_PARAMETERS_MISSING"
        for f in b7e_report.missing_configuration_blockers
    )

    # 3. Prohibited Audio V2 checkpoint in config fails closed structurally
    bad_audio_ckpt = dataclasses.replace(
        frozen.checkpoints.audio_v3, expected_sha256=PROHIBITED_AUDIO_V2_SHA256
    )
    bad_config = dataclasses.replace(
        frozen,
        checkpoints=dataclasses.replace(frozen.checkpoints, audio_v3=bad_audio_ckpt),
    )
    bad_ckpt_report = run_experiment_preflight(bad_config, experiment_family="B1")
    assert bad_ckpt_report.structurally_valid is False
    assert any(
        f.code == "PROHIBITED_AUDIO_V2_CHECKPOINT"
        for f in bad_ckpt_report.structural_errors
    )


def test_stage21_and_readiness_gates_fail_closed_on_synthetic_checks(
    tmp_path: Path,
) -> None:
    # Create synthetic non-media placeholder files in tmp_path to test build_review_record
    synth_front = tmp_path / "synthetic_front.bin"
    synth_back = tmp_path / "synthetic_back.bin"
    synth_front.write_bytes(b"synthetic-front-stream-bytes")
    synth_back.write_bytes(b"synthetic-back-stream-bytes")

    rec_dict = build_review_record(
        event_id="event_001",
        cohort="train_events",
        reviewer_id="reviewer_alpha",
        authorized_reviewers=frozenset({"reviewer_alpha"}),
        review_session_id="session_synth_001",
        review_start_utc="2026-11-01T10:00:00Z",
        review_end_utc="2026-11-01T10:05:00Z",
        inspection_tool="synthetic_frame_inspector_v1",
        attestation_statement=(
            "I independently inspected the synchronized video streams and recorded "
            "each boundary timestamp or explicit observability state."
        ),
        attested_at_utc="2026-11-01T10:05:05Z",
        front_media_path=synth_front,
        back_media_path=synth_back,
        observed_at_utc="2026-11-01T10:01:00Z",
        proposal_file="data/ground_truth/proposals/train_events_event_001.json",
        proposal_sha256="3" * 64,
        boundary_adjudications={
            "T0_first_visible": {
                "state": "OBSERVABLE",
                "rationale": "First visible appearance on front camera.",
                "value_s": 2.8,
                "reference_camera": "front",
                "frame_index": 14,
            },
            "T1_danger_zone_entry": {
                "state": "OBSERVABLE",
                "rationale": "Clear train nose entry into danger zone.",
                "value_s": 3.2,
                "reference_camera": "front",
                "frame_index": 16,
            },
            "T2_crossing_occupancy_start": {
                "state": "OBSERVABLE",
                "rationale": "Crossing occupancy started.",
                "value_s": 4.0,
                "reference_camera": "front",
                "frame_index": 20,
            },
            "T3_locomotive_unit_clearance": {
                "state": "OBSERVABLE",
                "rationale": "Locomotive unit cleared danger zone.",
                "value_s": 12.0,
                "reference_camera": "back",
                "frame_index": 60,
            },
            "T4_tail_clearance": {
                "state": "OBSERVABLE",
                "rationale": "Tail clearance observed on rear camera.",
                "value_s": 14.4,
                "reference_camera": "back",
                "frame_index": 72,
            },
            "T_scene_clear": {
                "state": "OBSERVABLE",
                "rationale": "Scene fully clear.",
                "value_s": 15.2,
                "reference_camera": "back",
                "frame_index": 76,
            },
        },
        adjudication_status="APPROVED",
    )
    assert rec_dict["schema_version"] == STAGE_2_1_SCHEMA_VERSION
    parsed_rec = build_stage2_1_record_from_dict(rec_dict)
    assert parsed_rec.event_id == "event_001"

    # Promotion gate fails closed when reviewer is unauthorized or proposal sha mismatches
    violations = validate_for_promotion(
        rec_dict,
        active_proposal_sha256_by_event={"train_events/event_001": "4" * 64},
        media_sha256_registry={},
        authorized_reviewers=frozenset({"other_reviewer"}),
        media_file_paths={},
    )
    v_codes = {v.code for v in violations}
    assert "REVIEWER_NOT_AUTHORIZED" in v_codes
    assert "STALE_PROPOSAL_REFERENCE" in v_codes

    # Official evaluation readiness gate fails closed on repository state
    readiness = evaluate_readiness(
        reviews_dir=tmp_path / "reviews",
        active_proposal_sha256_by_event={},
        media_sha256_registry={},
        allowlist_path=tmp_path / "authorized_reviewers.json",
        media_file_paths={},
    )
    assert readiness.ready is False
