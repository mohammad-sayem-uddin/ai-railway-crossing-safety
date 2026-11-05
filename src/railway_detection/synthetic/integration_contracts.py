"""Constructed cross-package identity/lineage and sampled B metric projections.

No source identity authentication or empirical B metric adoption is implied.
Exact physical geometry is projected explicitly; A's tolerance mapping is not reused.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from fractions import Fraction

from railway_detection.data.constructed_manifest import validate_manifest
from railway_detection.evaluation.metrics import classify_m4
from railway_detection.experiments.provenance_registry import validate_registry
from railway_detection.fusion.evidence import DecisionRecord
from railway_detection.simulation.runner import SimulationRunResult, SimulationStep
from railway_detection.synthetic.convention_b_pipeline import verify_result


@dataclass(frozen=True)
class ConstructedIdentity:
    physical_event: str = "synthetic:mission22:event:001"
    fixture_id: str = "synthetic:mission22:fixture:001"
    metric_display_slot: str = "train_events/event_001"
    crossing: str = "crossing_A"
    classification: str = "CONSTRUCTED_EVENT_NOT_V2_OBSERVATION"

    def validate(self):
        if (
            type(self.physical_event) is not str
            or not self.physical_event.startswith("synthetic:")
            or type(self.fixture_id) is not str
            or not self.fixture_id.startswith("synthetic:")
            or self.crossing != "crossing_A"
            or self.classification != "CONSTRUCTED_EVENT_NOT_V2_OBSERVATION"
        ):
            raise ValueError("explicit constructed single-crossing identity required")
        # A display slot exists only to exercise the old typed metric interface.
        # It is never asserted to be the identity of an actual inventory event.
        if self.metric_display_slot != "train_events/event_001":
            raise ValueError("unbound metric display slot")


def join_lineage(manifest, registry, *, expected, expected_manifest_digest):
    lineage = validate_manifest(manifest, expected_digest=expected_manifest_digest)
    cv = validate_registry(registry, expected=expected)
    records = {r.record_id: r for r in manifest.records}
    assets = {a.asset_id: a for a in expected.context.dataset.assets}
    roles = {e.event_id: e.role.value for e in expected.context.dataset.events}
    role_map = {
        "DEVELOPMENT_POOL": "DEVELOPMENT",
        "CALIBRATION_ONLY": "CALIBRATION",
        "RESERVED_CONTROL": "CONTROL",
        "CASE_STUDY": "CASE",
        "FINAL_DESCRIPTIVE": "EVALUATION",
    }
    producers = dict(registry.asset_artifacts)
    exposure = dict(cv.exposure)
    manifest_exposure = dict(lineage["fitted_exposure"])
    if (
        set(records) != set(assets)
        or len(producers) != len(registry.asset_artifacts)
        or set(producers) != set(assets)
    ):
        raise ValueError("complete exact source/asset/producer join required")
    for key, asset in assets.items():
        record = records[key]
        if (
            record.physical_event != asset.event_id
            or record.role != role_map[roles[asset.event_id]]
            or record.parents != asset.parent_ids
        ):
            raise ValueError("lineage group/role/parent substitution")
        if asset.kind == "DERIVATIVE":
            if (
                record.kind != "DERIVED"
                or asset.transform is None
                or record.transform_id != asset.transform.transform_id
            ):
                raise ValueError("transform identity mismatch")
        elif record.kind != "SOURCE" or asset.content_identity != "synthetic:sha256:" + str(
            record.source_digest
        ):
            raise ValueError("source content identity mismatch")
        required = set().union(*(set(exposure[p]) for p in producers[key]))
        if set(manifest_exposure[key]) != required:
            raise ValueError(
                "transitive FIT/SELECT/initialization exposure lost at lineage boundary"
            )
    return {
        "classification": "CONSTRUCTED_LINEAGE_CV_JOIN",
        "manifest": lineage,
        "cv": asdict(cv),
        "dataset_digest": registry.dataset_digest,
        "physical_events": tuple(sorted(roles)),
        "real_eligibility": False,
    }


def project_b_metrics(result, *, expected_request, t4_us, boundary_state="OBSERVABLE"):
    if not verify_result(result, expected_request=expected_request):
        raise ValueError("B candidate differs from independently retained replay")
    if boundary_state not in {"OBSERVABLE", "CENSORED", "UNCERTAIN", "NOT_OBSERVABLE"}:
        raise ValueError("unknown boundary state")
    if boundary_state == "OBSERVABLE":
        if type(t4_us) is not int or not 0 <= t4_us <= 3_600_000_000:
            raise ValueError("observable exact local T4 microseconds required")
    elif t4_us is not None:
        raise ValueError("nonpoint evidence cannot carry a computed point")
    c = result.causal
    points = []
    if c.origin_us is not None:
        accepted = [link for link in result.decisions if link.accepted]

        def point(t, angle, previous_angle):
            # Explicit exact geometry contract: OPEN at90, CLOSED at0;
            # actual positive/negative motion is OPENING/CLOSING, stationary
            # partial blockage is HOLD_PHYSICAL. No logical target is a state.
            state = (
                "OPEN"
                if angle == 90
                else "CLOSED"
                if angle == 0
                else "OPENING"
                if angle > previous_angle
                else "CLOSING"
                if angle < previous_angle
                else "HOLD_PHYSICAL"
            )
            link = next((x for x in reversed(accepted) if x.timestamp_us <= t), accepted[0])
            data = json.loads(link.decision_json)
            for k, value in data.get("observation_ages", {}).items():
                if isinstance(value, dict) and value.get("nonfinite_age") in {"inf", "-inf"}:
                    data["observation_ages"][k] = float(value["nonfinite_age"])
            return SimulationStep(
                t / 1_000_000,
                "CONSTRUCTED_B_GEOMETRY",
                state,
                float(angle),
                angle <= Fraction(45),
                DecisionRecord(**data),
            )

        points.append(point(c.origin_us, c.initial_angle, c.initial_angle))
        points.extend(
            point(interval.end_us, interval.post_angle, interval.pre_angle)
            for interval in c.intervals
        )
    timeline = SimulationRunResult(
        event_id=expected_request.batch.fixture_id,
        scenario_name="CONSTRUCTED_B_SAMPLED_GEOMETRY",
        steps=points,
    )
    outcome = classify_m4(timeline, None if t4_us is None else t4_us / 1_000_000)
    m4, m5, reason = outcome.premature, outcome.never_protected, outcome.reason
    if boundary_state != "OBSERVABLE":
        m4 = m5 = None
        reason = "t4_" + boundary_state.lower()
    elif c.status == "INCOMPLETE" and m4 is not True:
        m4 = m5 = None
        reason = "incomplete_constructed_B_prefix"
    return {
        "classification": "CONSTRUCTED_B_SAMPLED_METRIC_CONTRACT",
        "convention": "B",
        "research_metric_adoption": False,
        "empirical_result": False,
        "timestamp_unit": "microseconds",
        "M4": m4,
        "M5": None if m5 is None else int(m5),
        "reason": reason,
        "classification_detail": asdict(outcome),
        "points": [
            {
                "time_us": round(p.timestamp_s * 1_000_000),
                "geometry_state": p.gate_state,
                "angle": str(c.initial_angle if i == 0 else c.intervals[i - 1].post_angle),
                "blocked": p.is_passage_blocked,
            }
            for i, p in enumerate(points)
        ],
        "limit": "sampled exact-geometry software projection; no continuous safety inference",
    }


def validate_stream_bindings(fixture):
    """No display-slot identity, missing stream or fused source can stand in for this fixture."""
    identity = fixture["identity"]
    identity.validate()
    requests = fixture["requests"]
    if set(requests) != {"front", "back"}:
        raise ValueError("both explicitly independent constructed camera streams required")
    for camera, request in requests.items():
        if request.batch.fixture_id != identity.fixture_id + ":" + camera:
            raise ValueError("camera/event fixture identity mismatch")
        rows = json.loads(request.batch.inputs_json)
        if not rows:
            raise ValueError("missing camera stream; no zero metric substitution")
        for row in rows:
            if not row["frame"]["vision_records"] or any(
                evidence["source_id"] != "camera_" + camera or evidence["modality"] != "vision"
                for evidence in row["frame"]["vision_records"]
            ):
                raise ValueError("camera identity mismatch or unapproved cross-camera fusion")
