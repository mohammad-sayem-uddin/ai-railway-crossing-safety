"""Immutable constructed source/derived/annotation lineage. No IO or fit backend.

Content digests describe supplied metadata only. They do not attest to real raw
bytes, physical identity, human observations, rights or model execution.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass

_ID = re.compile(r"synthetic:[a-zA-Z0-9][a-zA-Z0-9:._-]*\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
ROLES = frozenset({"DEVELOPMENT", "CALIBRATION", "EVALUATION", "CONTROL", "CASE"})


@dataclass(frozen=True)
class ManifestRecord:
    record_id: str
    physical_event: str
    kind: str
    role: str
    parents: tuple[str, ...] = ()
    source_digest: str | None = None
    transform_id: str | None = None
    fitted_exposure: tuple[str, ...] = ()
    observation_origin: str | None = None


@dataclass(frozen=True)
class ConstructedManifest:
    version_id: str
    records: tuple[ManifestRecord, ...]
    previous_digest: str | None = None
    schema: str = "CONSTRUCTED_MANIFEST_V1"


def manifest_digest(manifest: ConstructedManifest) -> str:
    return hashlib.sha256(
        json.dumps(
            asdict(manifest), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _identifier(value):
    if type(value) is not str or not _ID.fullmatch(value):
        raise ValueError("explicit synthetic identifier required")


def _identifiers(values):
    if type(values) is not tuple or len(values) != len(set(values)):
        raise ValueError("unique immutable identifiers required")
    for value in values:
        _identifier(value)


def validate_manifest(manifest: ConstructedManifest, *, expected_digest: str):
    if type(manifest) is not ConstructedManifest or manifest.schema != "CONSTRUCTED_MANIFEST_V1":
        raise ValueError("typed constructed manifest required")
    _identifier(manifest.version_id)
    if type(manifest.records) is not tuple or not manifest.records:
        raise ValueError("nonempty immutable records required")
    if manifest.previous_digest is not None and not _SHA.fullmatch(manifest.previous_digest):
        raise ValueError("previous content digest malformed")
    if manifest_digest(manifest) != expected_digest:
        raise ValueError("independent retained metadata binding mismatch")
    by_id: dict[str, ManifestRecord] = {}
    event_roles: dict[str, str] = {}
    for record in manifest.records:
        if type(record) is not ManifestRecord:
            raise ValueError("typed immutable record required")
        _identifier(record.record_id)
        _identifier(record.physical_event)
        _identifiers(record.parents)
        _identifiers(record.fitted_exposure)
        if record.record_id in by_id or record.role not in ROLES:
            raise ValueError("duplicate record or unknown role")
        if event_roles.setdefault(record.physical_event, record.role) != record.role:
            raise ValueError("physical-event aliases cannot cross roles")
        if record.kind == "SOURCE":
            if (
                record.parents
                or record.transform_id is not None
                or record.fitted_exposure
                or record.observation_origin is not None
                or record.source_digest is None
                or not _SHA.fullmatch(record.source_digest)
            ):
                raise ValueError(
                    "source requires exact synthetic byte digest and no derived fields"
                )
        elif record.kind in {"DERIVED", "ANNOTATION"}:
            if not record.parents or record.source_digest is not None:
                raise ValueError(
                    "derivative requires exact parent join; source digest not inherited"
                )
            _identifier(record.transform_id)
            if record.kind == "ANNOTATION":
                if record.observation_origin != "CONSTRUCTED_FIXTURE_NOT_HUMAN":
                    raise ValueError("cannot manufacture human observations")
            elif record.observation_origin is not None:
                raise ValueError("unexpected observation field")
        else:
            raise ValueError("unknown record kind")
        by_id[record.record_id] = record
    all_events = set(event_roles)
    for record in manifest.records:
        if set(record.fitted_exposure) - all_events:
            raise ValueError("unresolved fitted exposure")
        if any(event_roles[e] != "DEVELOPMENT" for e in record.fitted_exposure):
            raise ValueError("fit exposure outside development role")
        for parent in record.parents:
            if parent not in by_id or by_id[parent].physical_event != record.physical_event:
                raise ValueError("missing parent or cross-event source join")
    # Topological validation also accumulates transitive fitted producer exposure.
    pending = set(by_id)
    exposure: dict[str, tuple[str, ...]] = {}
    while pending:
        ready = sorted(k for k in pending if set(by_id[k].parents) <= exposure.keys())
        if not ready:
            raise ValueError("cyclic lineage")
        for key in ready:
            record = by_id[key]
            inherited = set(record.fitted_exposure)
            for parent in record.parents:
                inherited.update(exposure[parent])
            if record.role in {"EVALUATION", "CONTROL", "CASE", "CALIBRATION"}:
                if record.physical_event in inherited:
                    raise ValueError("evaluation/calibration parent leakage")
            exposure[key] = tuple(sorted(inherited))
            pending.remove(key)
    return {
        "classification": "CONSTRUCTED_METADATA_ONLY",
        "manifest_digest": expected_digest,
        "records": len(by_id),
        "physical_events": len(all_events),
        "fitted_exposure": tuple(sorted(exposure.items())),
        "real_eligibility": False,
    }


def validate_successor(old: ConstructedManifest, new: ConstructedManifest):
    validate_manifest(old, expected_digest=manifest_digest(old))
    receipt = validate_manifest(new, expected_digest=manifest_digest(new))
    if old.version_id == new.version_id or new.previous_digest != manifest_digest(old):
        raise ValueError("successor needs new version and exact predecessor")
    old_records = {r.record_id: r for r in old.records}
    new_records = {r.record_id: r for r in new.records}
    if any(new_records.get(k) != value for k, value in old_records.items()):
        raise ValueError("historical records are immutable; append new identifiers")
    return receipt


def require_real_data_backend(*args, **kwargs):
    raise PermissionError(
        "No real data backend activated: exact resource grant/actor/context and verified adapter "
        "required; training/calibration/official split remain denied"
    )
