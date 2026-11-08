from dataclasses import replace

import pytest

from railway_detection.data.constructed_manifest import (
    ConstructedManifest,
    ManifestRecord,
    manifest_digest,
    require_real_data_backend,
    validate_manifest,
    validate_successor,
)


def fixture():
    a = ManifestRecord(
        "synthetic:a", "synthetic:physical:a", "SOURCE", "DEVELOPMENT", source_digest="1" * 64
    )
    b = ManifestRecord(
        "synthetic:b", "synthetic:physical:b", "SOURCE", "EVALUATION", source_digest="2" * 64
    )
    derived = ManifestRecord(
        "synthetic:derived",
        b.physical_event,
        "DERIVED",
        b.role,
        (b.record_id,),
        transform_id="synthetic:transform:v1",
        fitted_exposure=(a.physical_event,),
    )
    annotation = ManifestRecord(
        "synthetic:annotation",
        b.physical_event,
        "ANNOTATION",
        b.role,
        (derived.record_id,),
        transform_id="synthetic:schema:v1",
        observation_origin="CONSTRUCTED_FIXTURE_NOT_HUMAN",
    )
    return ConstructedManifest("synthetic:version:1", (a, b, derived, annotation))


def validate(m):
    return validate_manifest(m, expected_digest=manifest_digest(m))


def test_exact_join_transitive_exposure_and_determinism():
    m = fixture()
    r = validate(m)
    assert r == validate(m)
    assert r["physical_events"] == 2 and r["records"] == 4
    assert dict(r["fitted_exposure"])["synthetic:annotation"] == ("synthetic:physical:a",)
    assert r["real_eligibility"] is False
    with pytest.raises(ValueError, match="binding"):
        validate_manifest(m, expected_digest="0" * 64)


@pytest.mark.parametrize(
    "field,value",
    [
        ("physical_event", "data/raw/event.mov"),
        ("kind", "PREDICTION"),
        ("role", "UNKNOWN"),
        ("parents", ("synthetic:missing",)),
        ("parents", ("synthetic:a",)),
        ("parents", ("synthetic:derived",)),
        ("transform_id", None),
        ("fitted_exposure", ("synthetic:physical:b",)),
        ("fitted_exposure", ("synthetic:unknown",)),
        ("parents", ["synthetic:b"]),
        ("source_digest", "3" * 64),
        ("observation_origin", "HUMAN"),
    ],
)
def test_derived_substitution_denied(field, value):
    m = fixture()
    broken = replace(m.records[2], **{field: value})
    with pytest.raises(ValueError):
        validate(replace(m, records=(m.records[0], m.records[1], broken, m.records[3])))


def test_aliases_cannot_launder_roles_or_source_identity():
    m = fixture()
    alias = replace(m.records[1], record_id="synthetic:alias", role="DEVELOPMENT")
    with pytest.raises(ValueError, match="aliases"):
        validate(replace(m, records=m.records + (alias,)))
    with pytest.raises(ValueError, match="source"):
        validate(
            replace(m, records=(replace(m.records[0], source_digest="unknown"),) + m.records[1:])
        )
    with pytest.raises(ValueError, match="duplicate"):
        validate(replace(m, records=m.records + (m.records[0],)))
    with pytest.raises(ValueError, match="observations"):
        validate(
            replace(
                m,
                records=m.records[:-1]
                + (replace(m.records[-1], observation_origin="HUMAN_CONFIRMED"),),
            )
        )


def test_append_only_version_chain():
    old = fixture()
    new_record = replace(old.records[-1], record_id="synthetic:annotation:correction")
    new = replace(
        old,
        version_id="synthetic:version:2",
        records=old.records + (new_record,),
        previous_digest=manifest_digest(old),
    )
    assert validate_successor(old, new)["records"] == 5
    for bad in (
        replace(new, version_id=old.version_id),
        replace(new, previous_digest="0" * 64),
        replace(new, records=new.records[1:]),
        replace(new, records=(replace(new.records[0], source_digest="f" * 64),) + new.records[1:]),
    ):
        with pytest.raises(ValueError):
            validate_successor(old, bad)


@pytest.mark.parametrize(
    "operation",
    [
        "TRAIN_MODEL",
        "FIT_CALIBRATOR",
        "READ_RAW_MEDIA",
        "READ_CACHE",
        "CREATE_OFFICIAL_SPLIT",
        "CREATE_MANIFEST",
    ],
)
def test_implementation_never_invokes_real_resources(operation):
    with pytest.raises(PermissionError):
        require_real_data_backend(operation=operation, authorized=True)
