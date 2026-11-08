"""Synthetic-only tests for non-executing Phase 12–16 contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from railway_detection.research_contracts import (
    AblationConditionContract,
    ResearchContractError,
    audit_evidence_references,
    missing_phase12_prerequisites,
    missing_phase13_prerequisites,
    missing_phase14_prerequisites,
    missing_phase15_prerequisites,
    missing_phase16_prerequisites,
    require_identical_tick_log_bytes,
    validate_ablation_condition_contracts,
    validate_camera_scope,
    validate_event_level_split,
)


def test_event_level_split_accepts_disjoint_synthetic_ids() -> None:
    validate_event_level_split(
        {"train": ["syn-1"], "val": ["syn-2"], "test": ["syn-3"]}
    )


@pytest.mark.parametrize("partitions", [None, [], "not-a-mapping"])
def test_event_level_split_rejects_non_mapping_inputs(partitions) -> None:
    with pytest.raises(ResearchContractError):
        validate_event_level_split(partitions)


@pytest.mark.parametrize(
    "partitions",
    [
        {"train": ["syn-1"], "val": ["syn-1"], "test": ["syn-3"]},
        {"train": ["syn-1"], "val": ["syn-2", "syn-1"], "test": ["syn-3"]},
        {"train": ["syn-1"], "val": ["syn-2"], "test": ["syn-2", "syn-3"]},
        {"train": ["syn-1", "syn-1"], "val": ["syn-2"], "test": ["syn-3"]},
        {"train": ["syn-1"], "val": [], "test": ["syn-3"]},
        {"train": ["syn-1"], "validation": ["syn-2"], "test": ["syn-3"]},
        {"train": "syn-1", "val": ["syn-2"], "test": ["syn-3"]},
        {"train": [" syn-1"], "val": ["syn-2"], "test": ["syn-3"]},
        {"train": [None], "val": ["syn-2"], "test": ["syn-3"]},
        {"train": ["syn-1"], "val": ["syn-2"], "test": ["syn-3"], "extra": []},
    ],
)
def test_event_level_split_rejects_leakage_or_malformed_roles(partitions) -> None:
    with pytest.raises(ResearchContractError):
        validate_event_level_split(partitions)


def test_camera_scope_requires_accepted_sync_only_for_merged_mode() -> None:
    validate_camera_scope(
        {"syn-1": "independent_camera", "syn-2": "dual_camera"},
        accepted_sync_events={"syn-2"},
    )


def test_camera_scope_membership_is_only_a_caller_assertion() -> None:
    # This mechanical check does not load calibration artifacts or prove human
    # acceptance; the R04 decision and supporting evidence remain external.
    validate_camera_scope(
        {"synthetic-event": "dual_camera"},
        accepted_sync_events={"synthetic-event"},
    )


def test_camera_scope_refuses_unaccepted_dual_camera_event() -> None:
    with pytest.raises(ResearchContractError, match="accepted synchronization"):
        validate_camera_scope(
            {"syn-unresolved": "dual_camera"}, accepted_sync_events=set()
        )


@pytest.mark.parametrize("event_modes", [None, [], "not-a-mapping"])
def test_camera_scope_rejects_non_mapping_inputs(event_modes) -> None:
    with pytest.raises(ResearchContractError):
        validate_camera_scope(event_modes, accepted_sync_events=set())


@pytest.mark.parametrize(
    "event_modes,sync_events",
    [
        ({}, set()),
        ({"syn-1": None}, set()),
        ({" syn-1": "single_camera"}, set()),
        ({"syn-1": "dual_camera"}, {"syn-1", "undeclared"}),
        ({"syn-1": "dual_camera"}, "syn-1"),
        ({"syn-1": "dual_camera"}, {None}),
    ],
)
def test_camera_scope_rejects_malformed_or_overbroad_declarations(
    event_modes, sync_events
) -> None:
    with pytest.raises(ResearchContractError):
        validate_camera_scope(event_modes, accepted_sync_events=sync_events)


def test_ablation_contract_requires_single_factor_and_frozen_hash() -> None:
    config_hash = "a" * 64
    validate_ablation_condition_contracts(
        [
            AblationConditionContract("synthetic-baseline", config_hash, (), is_baseline=True),
            AblationConditionContract("synthetic-condition", config_hash, ("audio_enabled",)),
        ],
        frozen_config_sha256=config_hash,
    )


@pytest.mark.parametrize(
    "conditions",
    [
        [
            AblationConditionContract("baseline", "a" * 64, (), is_baseline=True),
            AblationConditionContract("two-factors", "a" * 64, ("audio", "vision")),
        ],
        [
            AblationConditionContract("baseline", "a" * 64, (), is_baseline=True),
            AblationConditionContract("wrong-config", "b" * 64, ("audio",)),
        ],
        [
            AblationConditionContract("baseline", "a" * 64, (), is_baseline=True),
            AblationConditionContract(
                "legacy-audio", "a" * 64, ("audio",), uses_audio_v2=True
            ),
        ],
        [
            AblationConditionContract("baseline", "a" * 64, (), is_baseline=True),
            AblationConditionContract(
                "gt-perturbation", "a" * 64, ("timing_jitter",), applies_to_ground_truth=True
            ),
        ],
    ],
)
def test_ablation_contract_rejects_unsafe_description(conditions) -> None:
    with pytest.raises(ResearchContractError):
        validate_ablation_condition_contracts(conditions, frozen_config_sha256="a" * 64)


def test_ablation_contract_requires_exactly_one_baseline() -> None:
    with pytest.raises(ResearchContractError, match="exactly one unchanged baseline"):
        validate_ablation_condition_contracts(
            [AblationConditionContract("condition", "a" * 64, ("audio",))],
            frozen_config_sha256="a" * 64,
        )


@pytest.mark.parametrize(
    "conditions,frozen_hash",
    [
        (None, "a" * 64),
        ([{"condition_id": "baseline"}], "a" * 64),
        ([AblationConditionContract("baseline", "a" * 64, (), is_baseline=True)], None),
        (
            [
                AblationConditionContract("baseline", "a" * 64, (), is_baseline=True),
                AblationConditionContract("dupe-factors", "a" * 64, ("audio", "audio")),
            ],
            "a" * 64,
        ),
        (
            [
                AblationConditionContract("baseline", "a" * 64, (), is_baseline=True),
                AblationConditionContract("bad-flag", "a" * 64, ("audio",), uses_audio_v2=1),
            ],
            "a" * 64,
        ),
    ],
)
def test_ablation_contract_rejects_malformed_descriptions(conditions, frozen_hash) -> None:
    with pytest.raises((ResearchContractError, TypeError)):
        validate_ablation_condition_contracts(conditions, frozen_config_sha256=frozen_hash)


def test_predeclared_compound_perturbation_is_not_misclassified_as_ablation() -> None:
    config_hash = "a" * 64
    validate_ablation_condition_contracts(
        [
            AblationConditionContract("synthetic-baseline", config_hash, (), is_baseline=True),
            AblationConditionContract(
                "synthetic-compound-stress",
                config_hash,
                ("audio_loss", "frame_loss"),
                condition_type="perturbation",
            ),
        ],
        frozen_config_sha256=config_hash,
    )


def test_tick_log_equivalence_is_byte_exact_and_synthetic() -> None:
    require_identical_tick_log_bytes(b'{"tick":0}\n', b'{"tick":0}\n')
    with pytest.raises(ResearchContractError, match="byte-equivalence"):
        require_identical_tick_log_bytes(b'{"tick":0}\n', b'{"tick":0.0}\n')


@pytest.mark.parametrize(
    "baseline,candidate",
    [
        (b"", b""),
        (b"{\"tick\":0}\n", b"{\"tick\":0}"),
        (b"{\"tick\":0}\n", b"{\"tick\":0} \n"),
        (b"{\"tick\":0}\n", b"{\"tick\":1}\n"),
    ],
)
def test_tick_log_comparison_rejects_empty_or_any_byte_difference(baseline, candidate) -> None:
    with pytest.raises(ResearchContractError):
        require_identical_tick_log_bytes(baseline, candidate)


def test_tick_log_comparison_rejects_text_inputs() -> None:
    with pytest.raises(TypeError, match="bytes"):
        require_identical_tick_log_bytes('{"tick":0}\n', '{"tick":0}\n')


def test_phase15_checklist_fails_closed_by_default_and_lists_missing_items() -> None:
    assert missing_phase15_prerequisites() == (
        "phases_12_14_complete",
        "researcher_authorized",
        "site_access_authorized",
        "safety_case_approved",
    )
    assert missing_phase15_prerequisites(
        phases_12_14_complete=True,
        researcher_authorized=True,
        site_access_authorized=True,
        safety_case_approved=True,
    ) == ()


def test_phase12_to_14_and_16_checklists_default_blocked() -> None:
    assert "eval_auth_granted" in missing_phase12_prerequisites()
    assert "event_split_decided" in missing_phase12_prerequisites()
    assert "r04_scope_decided" in missing_phase12_prerequisites()
    assert "researcher_scope_authorized" in missing_phase13_prerequisites()
    assert "target_hardware_specified" in missing_phase14_prerequisites()
    assert "publication_scope_decided" in missing_phase16_prerequisites()


def test_phase_authorization_checklists_require_every_declared_prerequisite() -> None:
    assert missing_phase12_prerequisites(
        readiness_gate_passed=True,
        eval_auth_granted=True,
        event_split_decided=True,
        r04_scope_decided=True,
        approved_stage21_records_available=True,
    ) == ()


@pytest.mark.parametrize(
    "checklist,kwargs",
    [
        (missing_phase12_prerequisites, {"eval_auth_granted": "false"}),
        (missing_phase13_prerequisites, {"researcher_scope_authorized": 1}),
        (missing_phase14_prerequisites, {"target_hardware_specified": "yes"}),
        (missing_phase15_prerequisites, {"site_access_authorized": [True]}),
        (missing_phase16_prerequisites, {"publication_scope_decided": object()}),
    ],
)
def test_phase_checklists_reject_non_boolean_truthy_assertions(checklist, kwargs) -> None:
    with pytest.raises(ResearchContractError, match="must be a boolean"):
        checklist(**kwargs)
    assert missing_phase13_prerequisites(
        phase12_baseline_complete=True,
        approved_ground_truth_available=True,
        frozen_config_hash_verified=True,
        researcher_scope_authorized=True,
    ) == ()
    assert missing_phase14_prerequisites(
        phase12_baseline_complete=True,
        researcher_scope_authorized=True,
        target_hardware_specified=True,
    ) == ()
    assert missing_phase16_prerequisites(
        required_phase_evidence_complete=True,
        publication_scope_decided=True,
    ) == ()


def test_evidence_audit_accepts_existing_synthetic_text_artifact(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "synthetic-evidence.md").write_text("synthetic", encoding="utf-8")
    audit_evidence_references(
        tmp_path, {"synthetic-claim": ["docs/synthetic-evidence.md"]}
    )


def test_evidence_path_check_does_not_claim_semantic_support_or_authorization(
    tmp_path: Path,
) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "unrelated.md").write_text("unrelated", encoding="utf-8")
    # Path traceability intentionally cannot decide whether contents support a claim.
    audit_evidence_references(tmp_path, {"synthetic-claim": ["docs/unrelated.md"]})


@pytest.mark.parametrize(
    "reference",
    [
        "missing/evidence.md",
        "../outside.md",
        "/tmp/evidence.md",
        "data/raw/video/event.mp4",
        "DATA\\RAW\\VIDEO\\event.MP4",
        "docs/../data/raw/private.txt",
        "models/audio/best_checkpoint.pt",
        "C:\\repo\\docs\\evidence.md",
        "docs\\..\\outside.md",
    ],
)
def test_evidence_audit_refuses_missing_escaping_raw_or_blocked_reference(
    tmp_path: Path, reference: str
) -> None:
    with pytest.raises(ResearchContractError):
        audit_evidence_references(tmp_path, {"synthetic-claim": [reference]})


def test_evidence_audit_refuses_unresolved_claim(tmp_path: Path) -> None:
    with pytest.raises(ResearchContractError, match="no evidence"):
        audit_evidence_references(tmp_path, {"unsupported-claim": []})


@pytest.mark.parametrize(
    "claim_references",
    [
        {"": ["docs/evidence.md"]},
        {"claim": "docs/evidence.md"},
        {None: ["docs/evidence.md"]},
        {"claim": [None]},
    ],
)
def test_evidence_audit_rejects_malformed_claim_mappings(tmp_path: Path, claim_references) -> None:
    with pytest.raises(ResearchContractError):
        audit_evidence_references(tmp_path, claim_references)


def test_evidence_audit_rejects_symlink_into_raw_media(tmp_path: Path) -> None:
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "private.txt").write_text("synthetic", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    try:
        (docs / "evidence.md").symlink_to(raw_dir / "private.txt")
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(ResearchContractError, match="raw media"):
        audit_evidence_references(tmp_path, {"claim": ["docs/evidence.md"]})


def test_evidence_audit_rejects_existing_path_that_escapes_repository(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("not repository evidence", encoding="utf-8")
    with pytest.raises(ResearchContractError, match="escapes repository root"):
        audit_evidence_references(repository, {"claim": ["../outside.md"]})


def test_evidence_audit_rejects_symlink_escaping_repository(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    docs = repository / "docs"
    docs.mkdir(parents=True)
    outside = tmp_path / "outside.md"
    outside.write_text("not repository evidence", encoding="utf-8")
    try:
        (docs / "evidence.md").symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(ResearchContractError, match="escapes repository root"):
        audit_evidence_references(repository, {"claim": ["docs/evidence.md"]})
