"""Local constructed integration demonstration; all persisted records are fixtures.

Only a new explicit output directory is used. No corpus/model/media loader,
public release or real human evidence can be activated by this command.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any

from scripts.generate_publication_tables import render_descriptive_support
from scripts.prepare_researcher_snapshot import build_source_snapshot, write_source_snapshot

from railway_detection.annotation.human_review_adapter import project_constructed_boundaries
from railway_detection.annotation.human_review_domain import (
    BOUNDARIES,
    RISK_SUBJECTS,
    Observation,
    ReviewWorkflow,
    SyntheticReviewer,
    digest,
)
from railway_detection.annotation.human_review_service import ConstructedReviewService, ReviewScope
from railway_detection.annotation.human_review_store import ConstructedReviewStore
from railway_detection.evaluation.descriptive_constructed import (
    ConstructedDescriptiveJob,
    run_constructed_descriptive,
)
from railway_detection.experiments.provenance_registry import canonical as json_values
from railway_detection.safety.constructed_authority import (
    PROFILE,
    ConstructedAuthority,
    Grant,
    canonical,
    encode_payload,
    sha,
)
from railway_detection.safety.constructed_broker import (
    ConstructedResource,
    ConstructedResourceBroker,
    resource_digest,
)
from railway_detection.simulation.runner import EventSimulationRunner
from railway_detection.synthetic.convention_b_pipeline import ConstructedBatch, IntegrationRequest
from railway_detection.synthetic.integration_contracts import project_b_metrics
from railway_detection.synthetic.integration_fixture import make_fixture

SCHEMA = "M22_CONSTRUCTED_RUN/1"


def text(value):
    return (
        json.dumps(json_values(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    )


def write_atomic(path, value):
    payload = value if type(value) is str else text(value)
    if path.exists():
        if path.read_text() != payload:
            raise ValueError("existing constructed artifact changed: " + path.name)
        return
    temporary = path.with_name(path.name + ".pending")
    if temporary.exists():
        raise ValueError("incomplete constructed write quarantined: " + temporary.name)
    with temporary.open("x", encoding="utf-8") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def checkpoint(path, value):
    pending = path.with_name(path.name + ".pending")
    if pending.exists():
        raise ValueError("partial checkpoint quarantined")
    with pending.open("x", encoding="utf-8") as stream:
        stream.write(text(value))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, path)


def output_path(value):
    path = Path(value).absolute()
    root = Path(__file__).resolve().parents[3]

    def deny(p):
        try:
            relative = p.relative_to(root)
        except ValueError:
            return
        if relative.parts and relative.parts[0] in {
            "data",
            "results",
            "experiments",
            "models",
            "outputs",
        }:
            raise ValueError("protected project output root refused before access")

    deny(path)
    path = path.parent.resolve(strict=True) / path.name
    deny(path)
    if path.is_symlink():
        raise ValueError("output symlink refused")
    return path


def verify_completed(output, descriptor):
    marker = json.loads((output / "COMPLETE.json").read_text())
    if marker.get("schema") != SCHEMA or marker.get("descriptor_sha256") != sha(text(descriptor)):
        raise ValueError("completion schema/binding mismatch")
    expected_paths = {
        "RUN.json",
        "ACK.json",
        "execution.json",
        "results_absent_report.md",
        "source_fixture/docs/input_envelope.json",
        "source_fixture/src/fixture.py",
        "snapshot/SOURCE_MANIFEST.json",
        "snapshot/docs/input_envelope.json",
        "snapshot/src/fixture.py",
    }
    if (
        set(marker) != {"schema", "descriptor_sha256", "artifacts"}
        or type(marker.get("artifacts")) is not dict
        or set(marker["artifacts"]) != expected_paths
    ):
        raise ValueError("closed complete constructed artifact manifest required")
    for relative, expected in marker["artifacts"].items():
        p = Path(relative)
        if (
            p.is_absolute()
            or ".." in p.parts
            or any(
                x.is_symlink() for x in [output / p, *list((output / p).parents)[: len(p.parts)]]
            )
        ):
            raise ValueError("invalid constructed artifact path")
        if hashlib.sha256((output / p).read_bytes()).hexdigest() != expected:
            raise ValueError("completed artifact digest mismatch")
    core = json.loads((output / "execution.json").read_text())
    if (
        core.get("schema") != SCHEMA
        or core.get("classification") != descriptor["classification"]
        or core.get("identity") != descriptor["identity"]
        or core.get("resource_binding") != descriptor["source_digest"]
        or core.get("producer_code_identity") != descriptor["code_identity"]
        or any(
            core.get(k) is not False for k in ("empirical_results", "human_evidence", "promotion")
        )
    ):
        raise ValueError("completed artifact cannot become real evidence or another event")
    return core


def run_demo(destination, *, seed=22, code_identity, resume=False, stop_after=None):
    output = output_path(destination)
    fixture = make_fixture(seed=seed, code_identity=code_identity)
    identity = fixture["identity"]
    source = ConstructedResource(
        "synthetic:resource:frames", "synthetic:resource:v1", fixture["source_bytes"]
    )
    source_hash = resource_digest(source)
    descriptor = {
        "schema": SCHEMA,
        "classification": "CONSTRUCTED_EVENT_NOT_V2_OBSERVATION",
        "identity": asdict(identity),
        "seed": seed,
        "code_identity": code_identity,
        "source_digest": source_hash,
        "lineage_digest": fixture["joined"]["manifest"]["manifest_digest"],
        "cv_registry_digest": fixture["joined"]["cv"]["registry_digest"],
        "controller": fixture["requests"]["front"].controller_json,
        "live_operations": False,
    }
    if output.exists():
        if not resume:
            raise ValueError("new destination required; use --resume only for this exact fixture")
        if json.loads((output / "RUN.json").read_text()) != descriptor:
            raise ValueError("stale run/config/source/schema binding")
        if (output / "COMPLETE.json").exists():
            return verify_completed(output, descriptor)
    else:
        if resume:
            raise ValueError("no constructed run to recover")
        output.mkdir()
        write_atomic(output / "RUN.json", descriptor)
    if stop_after == "initialization":
        raise InterruptedError("controlled constructed interruption after initialization")
    context = "synthetic:context:" + sha(text(descriptor))
    db_path = output / "constructed.sqlite"
    existing_db = db_path.exists()
    if not existing_db and (output / "ACK.json").exists():
        raise ValueError("acknowledged constructed database missing")
    connection = sqlite3.connect(db_path)
    try:
        authority = ConstructedAuthority(
            connection,
            appointments=(("synthetic:issuer", ("ISSUER",)), ("synthetic:reviewer", ("REVIEWER",))),
            expected_context=context,
            profile=PROFILE,
        )
        grant = Grant(
            "synthetic:grant:m22",
            "synthetic:reviewer",
            identity.physical_event,
            ("READ", "REVIEW"),
            (source.resource_id,),
            "CONSTRUCTED_REVIEW_FIXTURE",
            context,
            0,
            10,
            8,
        )
        scope = ReviewScope(
            "synthetic:session:m22", 1, grant.actor, source.resource_id, context, grant.purpose, 1
        )
        grant_row = connection.execute(
            "SELECT body,revoked FROM grants WHERE id=?", (grant.grant_id,)
        ).fetchone()
        if not existing_db:
            authority.issue("synthetic:issuer", grant)
        elif grant_row != (canonical(asdict(grant)), 0):
            raise ValueError("missing/modified/revoked constructed grant")
        read_args = scope.current() | {"operation": "READ"}
        if not existing_db:
            fence = authority.reserve(
                grant.grant_id,
                session=scope.session,
                initial_body=encode_payload({"schema": SCHEMA}),
                **read_args,
            )
        else:
            fence = authority.recover(scope.session, **scope.current())
        from dataclasses import replace

        scope = replace(scope, fence=fence)
        broker = ConstructedResourceBroker(
            authority,
            resources=(source,),
            expected_registry_digest=sha(canonical(((source.resource_id, source_hash),))),
        )
        supplied, read_receipt = broker.use(
            scope.session,
            "synthetic:read:frames",
            fence=fence,
            **read_args,
            expected_resource_digest=source_hash,
        )
        batches = json.loads(bytes.fromhex(supplied["result"]).decode())
        simulations = {}
        jobs = []
        metrics = {}
        for camera in ("front", "back"):
            request = fixture["requests"][camera]
            if batches[camera] != asdict(request.batch):
                raise ValueError("source bytes no longer bind constructed frame batch")
            batch = ConstructedBatch(**batches[camera])
            request = IntegrationRequest(
                batch, request.mode, request.controller_json, request.code_identity
            )
            engine = __import__(
                "railway_detection.fusion.decision_engine", fromlist=["MultimodalDecisionEngine"]
            ).MultimodalDecisionEngine()
            result = EventSimulationRunner(engine).run_frames_convention_b(request)
            t4 = 7_200_000 + (100_000 if camera == "back" else 0)
            metrics[camera] = project_b_metrics(result, expected_request=request, t4_us=t4)
            simulations[camera] = {
                "classification": "CONSTRUCTED_B_EXECUTION",
                "request": json.loads(request.canonical_json()),
                "result": json.loads(result.canonical_json()),
                "time_unit": "microseconds",
                "angle_unit": "degrees",
            }
            jobs.append(
                ConstructedDescriptiveJob(
                    identity.metric_display_slot,
                    camera,
                    "B0_" + camera,
                    request,
                    t4,
                    vision_source_id="camera_" + camera,
                )
            )
        separate_a = run_constructed_descriptive(
            tuple(jobs), expected_controller_json=descriptor["controller"]
        )
        observations = tuple(
            Observation(
                k, "front", "NOT_OBSERVABLE", "CONSTRUCTED_REVIEW_FIXTURE: no human observation"
            )
            for k in BOUNDARIES
        )
        actions: list[tuple[str, dict[str, Any]]] = [
            ("SEAL", {"observations": observations}),
            ("COMPARE", {"risk_inputs": tuple((k, False) for k in RISK_SUBJECTS)}),
            (
                "CORRECT",
                {
                    "observations": observations,
                    "reason": "CONSTRUCTED_REVIEW_FIXTURE informed correction",
                },
            ),
        ]
        ack_path = output / "ACK.json"
        ack: dict[str, Any] = (
            json.loads(ack_path.read_text())
            if ack_path.exists()
            else {"schema": SCHEMA, "step": 0, "anchor": [0, None]}
        )
        if (
            ack.get("schema") != SCHEMA
            or type(ack.get("step")) is not int
            or not 0 <= ack["step"] <= len(actions)
        ):
            raise ValueError("unsupported checkpoint")
        anchor = tuple(ack["anchor"])
        try:
            store = ConstructedReviewStore(
                connection,
                reviewers=(SyntheticReviewer(scope.actor, ("REVIEWER",)),),
                events=(identity.physical_event,),
                expected_anchor=anchor,
            )
        except ValueError as error:
            if "anchor mismatch" not in str(error) or ack["step"] >= len(actions):
                raise
            op, args = actions[ack["step"]]
            anchor = ConstructedReviewService.recover_anchor(
                authority,
                scope,
                request_id="synthetic:review:" + str(ack["step"]),
                operation=op,
                event=identity.physical_event,
                args=args,
                previous_anchor=anchor,
            )
            store = ConstructedReviewStore(
                connection,
                reviewers=(SyntheticReviewer(scope.actor, ("REVIEWER",)),),
                events=(identity.physical_event,),
                expected_anchor=anchor,
            )
        service = ConstructedReviewService(authority, store)
        last = None
        for index, (op, args) in enumerate(actions):
            last = service.execute(
                scope,
                op,
                identity.physical_event,
                request_id="synthetic:review:" + str(index),
                **args,
            )
            if stop_after == "review_commit" and index == 0:
                raise InterruptedError("controlled interruption after commit before checkpoint")
            if index >= ack["step"]:
                checkpoint(ack_path, {"schema": SCHEMA, "step": index + 1, "anchor": store.anchor})
        if stop_after == "review":
            raise InterruptedError("controlled interruption after review")
        projection = project_constructed_boundaries(
            observations,
            target_schema="8.1.0-stage2.1",
            expected_body_digest=digest(ReviewWorkflow._body(observations)),
            evidence_statuses=tuple((k, "MISSING") for k in BOUNDARIES),
        )
        if last is None:
            raise RuntimeError("constructed review did not execute")
        authority.audit(
            expected_head=last["authority_receipt"]["head"],
            expected_count=last["authority_receipt"]["sequence"],
        )
        core = {
            "schema": SCHEMA,
            "classification": "CONSTRUCTED_EVENT_NOT_V2_OBSERVATION",
            "identity": asdict(identity),
            "synthetic_inputs": True,
            "empirical_results": False,
            "human_evidence": False,
            "promotion": False,
            "simulations": simulations,
            "B_metric_contracts": metrics,
            "separate_A_metric_receipt": separate_a,
            "lineage_CV": fixture["joined"],
            "mock_review": last,
            "boundary_projection": projection,
            "resource_binding": source_hash,
            "producer_code_identity": code_identity,
            "operational_readiness": "CONSTRUCTED_INTEGRATION_ONLY",
        }
        write_atomic(output / "execution.json", core)
        write_atomic(output / "results_absent_report.md", render_descriptive_support())
        source_root = output / "source_fixture"
        (source_root / "docs").mkdir(parents=True, exist_ok=True)
        (source_root / "src").mkdir(exist_ok=True)
        write_atomic(source_root / "docs/input_envelope.json", descriptor)
        write_atomic(
            source_root / "src/fixture.py",
            "# CONSTRUCTED_REVIEW_FIXTURE — no model, media or human evidence\nSEED = "
            + str(seed)
            + "\n",
        )
        paths = ("docs/input_envelope.json", "src/fixture.py")
        snapshot = output / "snapshot"
        encoded, contents = build_source_snapshot(source_root, paths, code_identity=code_identity)
        if snapshot.exists():
            if not (snapshot / "SOURCE_MANIFEST.json").exists():
                raise ValueError("incomplete snapshot quarantined; completion marker absent")
        else:
            write_source_snapshot(
                source_root, paths, destination=snapshot, code_identity=code_identity
            )
        if (snapshot / "SOURCE_MANIFEST.json").read_bytes() != encoded or any(
            (snapshot / p).read_bytes() != data for p, data in contents.items()
        ):
            raise ValueError("stale/tampered snapshot")
        artifacts = [
            "RUN.json",
            "ACK.json",
            "execution.json",
            "results_absent_report.md",
            "source_fixture/docs/input_envelope.json",
            "source_fixture/src/fixture.py",
            "snapshot/SOURCE_MANIFEST.json",
            "snapshot/docs/input_envelope.json",
            "snapshot/src/fixture.py",
        ]
        marker = {
            "schema": SCHEMA,
            "descriptor_sha256": sha(text(descriptor)),
            "artifacts": {
                p: hashlib.sha256((output / p).read_bytes()).hexdigest() for p in artifacts
            },
        }
        write_atomic(output / "COMPLETE.json", marker)
        return json.loads(text(core))
    finally:
        connection.close()
