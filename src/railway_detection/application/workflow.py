"""One typed application adapter over the existing WP01–WP10 coordinator."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from railway_detection.application.authorization import TypedConstructedResourceBroker
from railway_detection.application.comparator import (
    ComparatorObservation,
    InactiveComparator,
    ProducerReference,
)
from railway_detection.application.contracts import (
    APPLICATION_SCHEMA,
    ApplicationReceipt,
    ApplicationRequest,
    CameraContract,
    MetricContract,
    ServiceState,
    canonical,
    closed_json,
)
from railway_detection.application.review import TypedConstructedReviewService
from railway_detection.synthetic.integration_fixture import make_fixture
from railway_detection.synthetic.integration_workflow import output_path, run_demo, write_atomic


def text_digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@dataclass(frozen=True)
class WorkflowExecution:
    canonical_core: str
    cameras: tuple[CameraContract, ...]
    metrics: tuple[MetricContract, ...]
    review: ServiceState
    authorization: ServiceState
    comparator_json: str
    lineage_digest: str


class WorkflowPort(Protocol):
    def execute(
        self, request: ApplicationRequest, output: Path, *, resume: bool, stop_after: str | None
    ) -> WorkflowExecution: ...


class ExistingWorkflowAdapter:
    """Legacy dictionaries stay inside this adapter; typed contracts leave it."""

    def execute(
        self, request: ApplicationRequest, output: Path, *, resume: bool, stop_after: str | None
    ) -> WorkflowExecution:
        request.validate()
        core = run_demo(
            output,
            seed=request.seed,
            code_identity=request.code_identity,
            resume=resume,
            stop_after=stop_after,
            review_factory=TypedConstructedReviewService,
            broker_factory=TypedConstructedResourceBroker,
        )
        if (
            core.get("identity", {}).get("physical_event") != request.event
            or core.get("producer_code_identity") != request.code_identity
            or any(
                core.get(k) is not False
                for k in ("empirical_results", "human_evidence", "promotion")
            )
        ):
            raise ValueError("workflow output identity/construction mismatch")
        fixture = make_fixture(seed=request.seed, code_identity=request.code_identity)
        cameras = []
        metrics = []
        for camera in ("front", "back"):
            q = fixture["requests"][camera]
            result = core["simulations"][camera]["result"]
            source = "camera_" + camera
            cameras.append(
                CameraContract(
                    camera,
                    source,
                    request.event,
                    result["causal"]["origin_us"],
                    result["controller_calls"],
                    text_digest(q.controller_json),
                )
            )
            m = core["B_metric_contracts"][camera]
            metrics.append(MetricContract(camera, m["M4"], m["M5"], reason=m.get("reason")))
        producer = ProducerReference(text_digest(fixture["requests"]["back"].controller_json))
        comparator = InactiveComparator(event=request.event, producer=producer)
        outcomes = []

        # Reuse the already retained exact frame envelope; no extra producer/model runs.
        # The batch's canonical wire format is parsed only within this adapter.
        rows = json.loads(fixture["requests"]["back"].batch.inputs_json)
        for row in rows:
            frame = row["frame"]
            records = frame["vision_records"]
            from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality

            record = None
            if records:
                value = records[0]
                record = EvidenceRecord(
                    value["timestamp_s"],
                    value["source_id"],
                    Modality(value["modality"]),
                    value["available"],
                    tuple(Detection(**d) for d in value["detections"]),
                )
            observed = row["timestamp_us"] if "timestamp_us" in row else row["timestamp"]
            observation = ComparatorObservation.from_vision(
                record,
                event=request.event,
                observation_id=row["event_id"],
                received_us=observed,
                observed_us=observed if record is not None else None,
                producer=producer,
            )
            outcomes.append(asdict(comparator.evaluate(observation)))
        review = core["mock_review"]
        if (
            review["classification"] != "CONSTRUCTED_REVIEW_FIXTURE"
            or review["real_human_evidence"] is not False
        ):
            raise ValueError("review fixture cannot become genuine evidence")
        return WorkflowExecution(
            canonical(core),
            tuple(cameras),
            tuple(metrics),
            ServiceState(
                "TYPED_REVIEW_RESPONSE/1",
                review["classification"],
                review["review_commit"]["count"],
            ),
            ServiceState(
                "CONSTRUCTED_AUTHORITY/1",
                "MOCK_PRINCIPAL_ONLY",
                review["authority_receipt"]["sequence"],
            ),
            canonical(outcomes),
            core["lineage_CV"]["manifest"]["manifest_digest"],
        )


def _application_output(value) -> Path:
    output = output_path(value)
    root = Path(__file__).resolve().parents[3]
    if output == root or root in output.parents:
        raise ValueError("application output requires an explicit directory outside the checkout")
    return output


def _aliases(output: Path):
    for name in (
        "APPLICATION_REQUEST.json",
        "APPLICATION.json",
        "APPLICATION_COMPLETE.json",
        "workflow",
    ):
        p = output / name
        if p.is_symlink() or p.with_name(p.name + ".pending").is_symlink():
            raise ValueError("application metadata alias refused before access")
        if p.with_name(p.name + ".pending").exists():
            raise ValueError("incomplete application metadata quarantined")


class ConstructedApplication:
    def __init__(self, workflow: WorkflowPort | None = None):
        self.workflow = workflow or ExistingWorkflowAdapter()

    def run(
        self,
        destination,
        request: ApplicationRequest,
        *,
        resume=False,
        stop_after=None,
        verify_only=False,
    ) -> ApplicationReceipt:
        if type(request) is not ApplicationRequest:
            raise ValueError("typed application request required")
        request.validate()
        if stop_after not in {
            None,
            "initialization",
            "review_commit",
            "review",
            "workflow",
            "application_receipt",
        }:
            raise ValueError("unknown constructed interruption stage")
        output = _application_output(destination)
        _aliases(output)
        existing = output.exists()
        if existing:
            if not resume:
                raise ValueError(
                    "new application destination required; exact resume must be explicit"
                )
            saved = ApplicationRequest.from_json((output / "APPLICATION_REQUEST.json").read_text())
            if saved != request:
                raise ValueError("stale application request/configuration/schema")
        else:
            if resume or verify_only:
                raise ValueError("no application state to resume/verify")
            output.mkdir()
            write_atomic(output / "APPLICATION_REQUEST.json", request.to_json())
        marker_path = output / "APPLICATION_COMPLETE.json"
        if verify_only and not marker_path.exists():
            raise ValueError("application incomplete; verify cannot certify it")
        workflow = output / "workflow"
        if not workflow.exists() and (
            (output / "APPLICATION.json").exists() or marker_path.exists()
        ):
            raise ValueError("acknowledged workflow parent missing")
        result = self.workflow.execute(
            request,
            workflow,
            resume=workflow.exists(),
            stop_after=stop_after
            if stop_after in {"initialization", "review_commit", "review"}
            else None,
        )
        if type(result) is not WorkflowExecution:
            raise ValueError("typed workflow result required")
        if stop_after == "workflow":
            raise InterruptedError("controlled interruption after constructed workflow")
        receipt = ApplicationReceipt(
            APPLICATION_SCHEMA,
            request,
            result.cameras,
            result.metrics,
            result.review,
            result.authorization,
            result.comparator_json,
            result.lineage_digest,
            text_digest(result.canonical_core),
        )
        encoded = receipt.to_json()
        artifacts = ("APPLICATION_REQUEST.json", "APPLICATION.json", "workflow/COMPLETE.json")
        if marker_path.exists():
            marker = closed_json(marker_path.read_text())
            expected = {
                "schema": "APPLICATION_ARTIFACT_SET/1",
                "request_digest": text_digest(request.to_json()),
                "artifacts": {name: text_digest((output / name).read_text()) for name in artifacts},
            }
            if marker != expected or (output / "APPLICATION.json").read_text() != encoded:
                raise ValueError("application artifact substitution or incomplete manifest")
        else:
            if verify_only:
                raise ValueError("missing application completion marker")
            write_atomic(output / "APPLICATION.json", encoded)
            if stop_after == "application_receipt":
                raise InterruptedError("controlled interruption before application completion")
            marker = {
                "schema": "APPLICATION_ARTIFACT_SET/1",
                "request_digest": text_digest(request.to_json()),
                "artifacts": {name: text_digest((output / name).read_text()) for name in artifacts},
            }
            write_atomic(marker_path, marker)
        return receipt

    def verify(self, destination) -> ApplicationReceipt:
        output = _application_output(destination)
        _aliases(output)
        request = ApplicationRequest.from_json((output / "APPLICATION_REQUEST.json").read_text())
        return self.run(output, request, resume=True, verify_only=True)
