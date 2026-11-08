"""Pure constructed fitted-artifact/OOF evidence verification. No fit/load/write API.

An accepted registry proves supplied synthetic consistency, never real source
identity, genuine execution, independent scientific exposure or authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from enum import Enum
from fractions import Fraction

from railway_detection.synthetic.grouped_cv import RoleContext, role_plan, validate_dataset

SCHEMA = "CONSTRUCTED_ARTIFACT_OOF_V1"
ID = re.compile(r"synthetic:[A-Za-z0-9][A-Za-z0-9._:-]*\Z")


def canonical(value):
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [canonical(x) for x in value]
    return value


def digest(value):
    return hashlib.sha256(
        json.dumps(
            canonical(asdict(value)), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def ids(values):
    if type(values) is not tuple or len(values) != len(set(values)):
        raise ValueError("immutable unique identifiers required")
    if any(type(x) is not str or not ID.fullmatch(x) for x in values):
        raise ValueError("constructed identifiers required")


@dataclass(frozen=True)
class InnerSplit:
    inner_id: str
    training: tuple[str, ...]
    tuning: tuple[str, ...]
    heldout: tuple[str, ...]


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    kind: str
    fit_events: tuple[str, ...] = ()
    selection_events: tuple[str, ...] = ()
    parents: tuple[str, ...] = ()
    inner_id: str | None = None
    exposure_status: str = "DECLARED_SYNTHETIC_COMPLETE"
    parameters_version: str = "synthetic:parameters:v1"


@dataclass(frozen=True)
class Prediction:
    prediction_id: str
    event_id: str
    asset_id: str
    producer: str
    vocabulary: tuple[str, ...]
    values: tuple[Fraction, ...]
    outer_fold: int
    inner_id: str


@dataclass(frozen=True)
class Registry:
    dataset_digest: str
    artifacts: tuple[Artifact, ...]
    predictions: tuple[Prediction, ...]
    asset_artifacts: tuple[tuple[str, tuple[str, ...]], ...] = ()
    excluded_events: tuple[str, ...] = ()
    unresolved_duplicates: tuple[str, ...] = ()
    version: str = SCHEMA


@dataclass(frozen=True)
class ExpectedRegistry:
    context: RoleContext
    registry_digest: str
    inner_splits: tuple[InnerSplit, ...]
    score_events: tuple[str, ...]
    vocabulary: tuple[str, ...]
    calibration_mode: str = "NONE"
    frozen_rule_id: str | None = None


@dataclass(frozen=True)
class RegistryReceipt:
    registry_digest: str
    context_digest: str
    exposure: tuple[tuple[str, tuple[str, ...]], ...]
    score_count: int
    calibration_mode: str
    schema: str = SCHEMA
    limitation: str = "constructed consistency only; no fitting, authority or authenticity"


def validate_registry(registry: Registry, *, expected: ExpectedRegistry) -> RegistryReceipt:
    if type(registry) is not Registry or type(expected) is not ExpectedRegistry:
        raise ValueError("typed registry and independent expected context required")
    if registry.version != SCHEMA or digest(registry) != expected.registry_digest:
        raise ValueError("registry version/content binding mismatch")
    c = expected.context
    if type(c) is not RoleContext:
        raise ValueError("original context required")
    plan = role_plan(
        c.dataset,
        c.allocation,
        expected_policy=c.policy,
        outer_fold=c.outer_fold,
        validation_events=c.validation_events,
        calibration_mode=c.calibration_mode,
        frozen_rule_id=c.frozen_rule_id,
    )
    dataset = validate_dataset(c.dataset)
    if registry.dataset_digest != dataset.input_digest:
        raise ValueError("dataset binding mismatch")
    if expected.calibration_mode not in ("NONE", "INNER_OOF", "RESERVED_CALIBRATION"):
        raise ValueError("unknown calibration mode")
    if expected.frozen_rule_id is not None:
        ids((expected.frozen_rule_id,))
    if (
        type(expected.vocabulary) is not tuple
        or not expected.vocabulary
        or any(type(v) is not str or not v for v in expected.vocabulary)
        or len(set(expected.vocabulary)) != len(expected.vocabulary)
    ):
        raise ValueError("exact nonempty vocabulary required")
    outer_train = set(plan.training + plan.validation)
    canonical_events = {g.event_id for g in dataset.groups}
    splits = {}
    for split in expected.inner_splits:
        if type(split) is not InnerSplit:
            raise ValueError("typed inner split required")
        ids((split.inner_id,))
        if split.inner_id in splits:
            raise ValueError("duplicate inner plan")
        parts = [split.training, split.tuning, split.heldout]
        for part in parts:
            ids(part)
        if (
            not split.training
            or not split.heldout
            or len(set(sum(parts, ()))) != sum(len(p) for p in parts)
            or set(sum(parts, ())) != outer_train
        ):
            raise ValueError("inner plan coverage/disjointness")
        splits[split.inner_id] = split
    ids(expected.score_events)
    if not set(expected.score_events) <= outer_train:
        raise ValueError("score request uses outer/reserved event")
    if type(registry.artifacts) is not tuple or type(registry.predictions) is not tuple:
        raise ValueError("immutable registry required")
    artifacts = {}
    for a in registry.artifacts:
        if type(a) is not Artifact:
            raise ValueError("typed artifact required")
        ids((a.artifact_id,))
        ids((a.parameters_version,))
        if a.artifact_id in artifacts:
            raise ValueError("duplicate artifact")
        for part in (a.fit_events, a.selection_events, a.parents):
            ids(part)
        if a.exposure_status != "DECLARED_SYNTHETIC_COMPLETE":
            raise ValueError("unknown initialization/parent exposure")
        if not set(a.fit_events + a.selection_events) <= canonical_events:
            raise ValueError("unknown physical event exposure")
        if a.kind in ("BASE_MODEL", "PREPROCESSOR", "FEATURE_CACHE"):
            if a.inner_id not in splits:
                raise ValueError("missing producing inner plan")
            split = splits[a.inner_id]
            allowed_fit = set(split.training)
            allowed_select = allowed_fit | set(split.tuning)
        elif a.kind == "INITIALIZATION":
            allowed_fit = allowed_select = outer_train
        elif a.kind == "FINAL_REFIT" and expected.frozen_rule_id is not None:
            allowed_fit = allowed_select = outer_train
        elif a.kind == "CALIBRATOR" and expected.calibration_mode != "NONE":
            allowed_fit = (
                set(plan.calibration)
                if expected.calibration_mode == "RESERVED_CALIBRATION"
                else set(expected.score_events)
            )
            allowed_select = allowed_fit
            if not allowed_fit or set(a.fit_events) != allowed_fit:
                raise ValueError("calibrator exact membership required")
        else:
            raise ValueError("unsupported kind or unapproved refit/calibration")
        if not set(a.fit_events) <= allowed_fit or not set(a.selection_events) <= allowed_select:
            raise ValueError("direct fit/selection violates frozen role plan")
        artifacts[a.artifact_id] = a
    exposure: dict[str, set[str]] = {}
    pending = set(artifacts)
    while pending:
        ready = sorted(k for k in pending if set(artifacts[k].parents) <= exposure.keys())
        if not ready:
            raise ValueError("orphan or cyclic artifact lineage")
        for k in ready:
            a = artifacts[k]
            value = set(a.fit_events + a.selection_events)
            for parent in a.parents:
                value |= exposure[parent]
            # Calibrators may use calibration-only evidence; other outputs cannot inherit it.
            allowed = outer_train | (set(plan.calibration) if a.kind == "CALIBRATOR" else set())
            if not value <= allowed:
                raise ValueError("transitive outer/reserved contamination")
            exposure[k] = value
            pending.remove(k)
    ids(registry.excluded_events)
    if registry.unresolved_duplicates:
        raise ValueError("unresolved duplicate identity blocks acceptance")
    assets = {a.asset_id: a.event_id for a in c.dataset.assets}
    asset_exposure = {}
    for asset_id, refs in registry.asset_artifacts:
        ids(refs)
        if asset_id not in assets or asset_id in asset_exposure or not set(refs) <= exposure.keys():
            raise ValueError("unknown/duplicate asset producer binding")
        asset_exposure[asset_id] = set().union(*(exposure[k] for k in refs))
    calibrators = [a for a in artifacts.values() if a.kind == "CALIBRATOR"]
    if expected.calibration_mode != "NONE" and len(calibrators) != 1:
        raise ValueError("one explicit calibration composition required")
    seen, scored = set(), set()
    for score in registry.predictions:
        if type(score) is not Prediction:
            raise ValueError("typed prediction required")
        ids((score.prediction_id,))
        if score.prediction_id in seen or score.event_id in scored:
            raise ValueError("duplicate/repeated OOF score")
        seen.add(score.prediction_id)
        scored.add(score.event_id)
        prediction_split = splits.get(score.inner_id)
        producer = artifacts.get(score.producer)
        if (
            prediction_split is None
            or producer is None
            or producer.kind != "BASE_MODEL"
            or producer.inner_id != score.inner_id
            or score.event_id not in prediction_split.heldout
            or score.outer_fold != c.outer_fold
            or type(score.outer_fold) is not int
            or assets.get(score.asset_id) != score.event_id
            or score.vocabulary != expected.vocabulary
        ):
            raise ValueError("score event/asset/model/vocabulary/fold mismatch")
        if (
            score.event_id in registry.excluded_events
            or score.event_id in exposure[score.producer]
            or score.event_id in asset_exposure.get(score.asset_id, set())
        ):
            raise ValueError("OOF event leaked through FIT/SELECT/initialization ancestry")
        if (
            type(score.values) is not tuple
            or len(score.values) != len(expected.vocabulary)
            or any(type(v) is not Fraction or not 0 <= v <= 1 for v in score.values)
        ):
            raise ValueError("exact typed score values required")
    if scored != set(expected.score_events):
        raise ValueError("missing or foreign OOF score coverage")
    return RegistryReceipt(
        digest(registry),
        digest(expected),
        tuple((k, tuple(sorted(v))) for k, v in sorted(exposure.items())),
        len(scored),
        expected.calibration_mode,
    )


def verify_receipt(candidate, registry, *, expected):
    if type(candidate) is not RegistryReceipt or type(candidate.score_count) is not int:
        return False
    try:
        return candidate == validate_registry(registry, expected=expected)
    except (ValueError, TypeError, KeyError):
        return False
