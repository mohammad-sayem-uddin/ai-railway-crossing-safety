"""Deterministic constructed crossing_A fixture and explicit CV/lineage joins."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from fractions import Fraction

from railway_detection.data.constructed_manifest import (
    ConstructedManifest,
    ManifestRecord,
    manifest_digest,
)
from railway_detection.experiments.provenance_registry import (
    Artifact,
    ExpectedRegistry,
    InnerSplit,
    Prediction,
    Registry,
    digest,
)
from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.synthetic.convention_b_pipeline import (
    ConstructedBatch,
    ConstructedInput,
    IntegrationRequest,
)
from railway_detection.synthetic.grouped_cv import (
    Annotation,
    Asset,
    Capture,
    DatasetRole,
    MetadataValue,
    PhysicalEvent,
    RoleContext,
    SyntheticDataset,
    Transform,
    allocate,
    allocation_policy,
    role_plan,
    validate_dataset,
)
from railway_detection.synthetic.integration_contracts import ConstructedIdentity, join_lineage


def make_fixture(*, seed=22, code_identity):
    if type(seed) is not int or not 0 <= seed <= 1_000_000:
        raise ValueError("bounded deterministic constructed seed required")
    identity = ConstructedIdentity(
        physical_event=f"synthetic:m22:s{seed}:event", fixture_id=f"synthetic:m22:s{seed}:fixture"
    )
    identity.validate()
    requests = {}
    for camera, offset in (("front", 0), ("back", 100_000)):
        inputs = []
        for i, t in enumerate(
            (0, 200_000, 2_200_000, 3_200_000, 4_200_000, 5_200_000, 6_200_000, 7_200_000)
        ):
            us = t + offset
            source = "camera_" + camera
            evidence = EvidenceRecord(
                us / 1_000_000, source, Modality.VISION, True, (Detection("front", 0.99),)
            )
            frame = MultimodalFrame(us / 1_000_000, (evidence,), source_availability={source: True})
            inputs.append(ConstructedInput(f"synthetic:{camera}:frame:{i}", us, frame))
        batch = ConstructedBatch.build(
            identity.fixture_id + ":" + camera, tuple(inputs), provenance="CONSTRUCTED_IN_MEMORY"
        )
        requests[camera] = IntegrationRequest.prepare(
            batch,
            MultimodalDecisionEngine(),
            mode="ARRIVAL",
            code_identity="synthetic:code:" + code_identity,
        )
    source_bytes = json.dumps(
        {camera: asdict(request.batch) for camera, request in requests.items()},
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    events = []
    captures = []
    assets = []
    annotations = []
    records = []
    for i in range(9):
        eid = identity.physical_event if i == 8 else f"synthetic:dev:{i}"
        role = DatasetRole.FINAL_DESCRIPTIVE if i == 8 else DatasetRole.DEVELOPMENT_POOL
        events.append(PhysicalEvent(eid, role, ("front",)))
        capture = f"synthetic:capture:{i}"
        source = f"synthetic:source:{i}"
        captures.append(
            Capture(
                capture,
                (eid,),
                camera=MetadataValue("constructed-front", None, "synthetic:metadata"),
                crossing=MetadataValue("crossing_A", None, "synthetic:metadata"),
            )
        )
        byte_digest = hashlib.sha256(
            source_bytes if i == 8 else (eid + ":CONSTRUCTED_ONLY").encode()
        ).hexdigest()
        assets.append(
            Asset(
                source,
                eid,
                "STILL",
                (f"synthetic:annotation:{i}",),
                capture,
                content_identity="synthetic:sha256:" + byte_digest,
            )
        )
        annotations.append(Annotation(f"synthetic:annotation:{i}", source, ("front",)))
        records.append(
            ManifestRecord(
                source,
                eid,
                "SOURCE",
                "EVALUATION" if i == 8 else "DEVELOPMENT",
                source_digest=byte_digest,
            )
        )
        derived = source + ":derived"
        aid = f"synthetic:annotation:derived:{i}"
        assets.append(
            Asset(
                derived,
                eid,
                "DERIVATIVE",
                (aid,),
                parent_ids=(source,),
                transform=Transform("synthetic:transform:fixture", "v1", (("seed", str(seed)),)),
            )
        )
        annotations.append(Annotation(aid, derived, ("front",)))
    dataset = SyntheticDataset(
        "synthetic:dataset:m22", tuple(events), tuple(captures), tuple(assets), tuple(annotations)
    )
    policy = allocation_policy(k=4, required_support=(("front", 1),))
    allocation = allocate(dataset, k=4, required_support=(("front", 1),))
    context = RoleContext(dataset, allocation, policy, 0, frozen_rule_id="synthetic:m22:frozen")
    plan = role_plan(
        dataset,
        allocation,
        outer_fold=0,
        expected_policy=policy,
        frozen_rule_id="synthetic:m22:frozen",
    )
    held = plan.training[:1]
    training = plan.training[1:]
    inner = InnerSplit("synthetic:inner:0", training, (), held)
    initialization = Artifact("synthetic:init", "INITIALIZATION", selection_events=training[:1])
    pre = Artifact(
        "synthetic:pre",
        "PREPROCESSOR",
        training,
        parents=(initialization.artifact_id,),
        inner_id=inner.inner_id,
    )
    model = Artifact(
        "synthetic:model",
        "BASE_MODEL",
        training,
        parents=(pre.artifact_id,),
        inner_id=inner.inner_id,
    )
    producer_map: list[tuple[str, tuple[str, ...]]] = []
    for asset in assets:
        if asset.kind == "DERIVATIVE":
            if asset.transform is None:
                raise ValueError("constructed derivative transform missing")
            producer_map.append((asset.asset_id, (pre.artifact_id,)))
            records.append(
                ManifestRecord(
                    asset.asset_id,
                    asset.event_id,
                    "DERIVED",
                    "EVALUATION" if asset.event_id == identity.physical_event else "DEVELOPMENT",
                    asset.parent_ids,
                    transform_id=asset.transform.transform_id,
                    fitted_exposure=tuple(sorted(training)),
                )
            )
        else:
            producer_map.append((asset.asset_id, ()))
    held_asset = next(
        a.asset_id for a in assets if a.event_id == held[0] and a.kind == "DERIVATIVE"
    )
    score = Prediction(
        "synthetic:score",
        held[0],
        held_asset,
        model.artifact_id,
        ("front",),
        (Fraction(1, 2),),
        0,
        inner.inner_id,
    )
    registry = Registry(
        validate_dataset(dataset).input_digest,
        (initialization, pre, model),
        (score,),
        tuple(producer_map),
    )
    expected = ExpectedRegistry(context, digest(registry), (inner,), held, ("front",))
    manifest = ConstructedManifest("synthetic:manifest:m22:v1", tuple(records))
    joined = join_lineage(
        manifest, registry, expected=expected, expected_manifest_digest=manifest_digest(manifest)
    )
    return {
        "source_bytes": source_bytes,
        "identity": identity,
        "requests": requests,
        "dataset": dataset,
        "registry": registry,
        "expected_registry": expected,
        "manifest": manifest,
        "joined": joined,
        "seed": seed,
        "classification": "CONSTRUCTED_EVENT_NOT_V2_OBSERVATION",
        "identity_manifest": asdict(identity),
    }
