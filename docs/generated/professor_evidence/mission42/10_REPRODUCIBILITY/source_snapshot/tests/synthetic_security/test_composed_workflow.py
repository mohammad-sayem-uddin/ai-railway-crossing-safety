"""Composed engineering path; all bytes/roles/observations are constructed fixtures."""

import hashlib
import importlib.util
import sqlite3
from pathlib import Path

import pytest

from railway_detection.annotation.human_review_adapter import project_constructed_boundaries
from railway_detection.annotation.human_review_domain import (
    BOUNDARIES,
    RISK_SUBJECTS,
    ConstructedPlayer,
    Observation,
    ReviewWorkflow,
    SyntheticReviewer,
    digest,
)
from railway_detection.annotation.human_review_store import ConstructedReviewStore
from railway_detection.data.constructed_manifest import (
    ConstructedManifest,
    ManifestRecord,
    manifest_digest,
    validate_manifest,
)
from railway_detection.evaluation.descriptive_constructed import (
    ConstructedDescriptiveJob,
    run_constructed_descriptive,
    run_real_descriptive,
)
from railway_detection.evaluation.metrics import DescriptiveMetricRow
from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
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
from railway_detection.synthetic.convention_b_pipeline import (
    ConstructedBatch,
    ConstructedInput,
    IntegrationRequest,
)

spec = importlib.util.spec_from_file_location(
    "constructed_publication_support",
    Path(__file__).resolve().parents[2] / "scripts/generate_publication_tables.py",
)
reporting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reporting)


def test_constructed_authority_review_lineage_controller_metric_and_draft_path():
    db = sqlite3.connect(":memory:")
    try:
        a = ConstructedAuthority(
            db,
            appointments=(
                ("synthetic:issuer", ("ISSUER",)),
                ("synthetic:r", ("REVIEWER",)),
                ("synthetic:p", ("PROMOTER",)),
            ),
            expected_context="synthetic:runtime",
            profile=PROFILE,
        )
        source = ConstructedResource(
            "synthetic:resource", "synthetic:v1", b"NEUTRAL_CONSTRUCTED_FRAME"
        )
        source_binding = resource_digest(source)
        broker = ConstructedResourceBroker(
            a,
            resources=(source,),
            expected_registry_digest=sha(canonical(((source.resource_id, source_binding),))),
        )
        grant = Grant(
            "synthetic:g",
            "synthetic:r",
            "synthetic:event",
            ("READ",),
            (source.resource_id,),
            "constructed example",
            "synthetic:runtime",
            0,
            10,
            1,
        )
        a.issue("synthetic:issuer", grant)
        scope = dict(
            actor=grant.actor,
            operation="READ",
            resource=source.resource_id,
            context=grant.context,
            purpose=grant.purpose,
            now=1,
        )
        fence = a.reserve(
            grant.grant_id, session="synthetic:s", initial_body=encode_payload({}), **scope
        )
        payload, receipt = broker.use(
            "synthetic:s",
            "synthetic:read",
            fence=fence,
            **scope,
            expected_resource_digest=source_binding,
        )
        assert a.audit(expected_count=receipt.sequence, expected_head=receipt.head)
        player = ConstructedPlayer(
            (
                (0, bytes.fromhex(payload["result"]).decode()),
                (1_000_000, bytes.fromhex(payload["result"]).decode()),
            )
        )
        assert player.seek(1)[0] == 1_000_000
        # Expected source clocks are declared fixture values, never human observations.
        observations = tuple(
            Observation(k, "back", "NOT_OBSERVABLE", "constructed missing") for k in BOUNDARIES
        )
        review = ConstructedReviewStore(
            db,
            reviewers=(SyntheticReviewer(grant.actor, ("REVIEWER",)),),
            events=(grant.event,),
            expected_anchor=(0, None),
        )
        review.execute(
            "SEAL", grant.actor, grant.event, request_id="synthetic:seal", observations=observations
        )
        review.execute(
            "COMPARE",
            grant.actor,
            grant.event,
            request_id="synthetic:compare",
            risk_inputs=tuple((k, False) for k in RISK_SUBJECTS),
        )
        with pytest.raises(ValueError, match="seal consumed"):
            review.execute(
                "SEAL",
                grant.actor,
                grant.event,
                request_id="synthetic:new-session",
                observations=observations,
            )
        projection = project_constructed_boundaries(
            observations,
            target_schema="8.1.0-stage2.1",
            expected_body_digest=digest(ReviewWorkflow._body(observations)),
            evidence_statuses=tuple((k, "MISSING") for k in BOUNDARIES),
        )
        assert projection["active_schema_satisfied"] is False
        original = ManifestRecord(
            "synthetic:source",
            grant.event,
            "SOURCE",
            "EVALUATION",
            source_digest=hashlib.sha256(source.contents).hexdigest(),
        )
        derived = ManifestRecord(
            "synthetic:derived",
            grant.event,
            "DERIVED",
            "EVALUATION",
            (original.record_id,),
            transform_id="synthetic:constructed_transform",
        )
        manifest = ConstructedManifest("synthetic:manifest:v1", (original, derived))
        assert (
            validate_manifest(manifest, expected_digest=manifest_digest(manifest))["records"] == 2
        )
        batch = ConstructedBatch.build(
            "synthetic:integration",
            tuple(
                ConstructedInput("synthetic:f" + str(i), t, MultimodalFrame(t / 1_000_000))
                for i, t in enumerate((0, 1_000_000))
            ),
            provenance="CONSTRUCTED_IN_MEMORY",
        )
        request = IntegrationRequest.prepare(
            batch, MultimodalDecisionEngine(), mode="ARRIVAL", code_identity="synthetic:code:21"
        )
        job = ConstructedDescriptiveJob("train_events/event_001", "back", "B0_back", request, None)
        result = run_constructed_descriptive(
            (job,), expected_controller_json=request.controller_json
        )
        assert all(m["denominator"] == 0 for m in result["metrics"])
        rows = tuple(
            DescriptiveMetricRow(
                job.event_key,
                job.camera,
                job.condition,
                metric,
                None,
                "t4_missing",
                "synthetic:composed",
            )
            for metric in ("M4", "M5")
        )
        text = reporting.render_descriptive_support(
            rows, expected_digest=reporting.descriptive_rows_digest(rows)
        )
        assert "UNAVAILABLE" in text and "CONSTRUCTED DEMONSTRATION ONLY" in text
        objects = (("synthetic:train:event:1", encode_payload({"projection_only": True})),)
        assert a.publish_constructed_batch(
            promoter="synthetic:p",
            batch_id="synthetic:mock-batch",
            objects=objects,
            approved_digest=sha(canonical(objects)),
        )
        assert db.execute("SELECT count(*) FROM objects").fetchone()[0] == 1
        a.revoke("synthetic:issuer", grant.grant_id)
        with pytest.raises(ValueError):
            broker.use(
                "synthetic:s",
                "synthetic:new",
                fence=fence,
                **scope,
                expected_resource_digest=source_binding,
            )
        with pytest.raises(PermissionError):
            run_real_descriptive(approved=True, receipt=receipt)
    finally:
        db.close()
