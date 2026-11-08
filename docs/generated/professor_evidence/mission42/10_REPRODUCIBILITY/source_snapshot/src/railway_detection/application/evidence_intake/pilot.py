"""Read-only five-event activation diagnosis using existing documentary/preflight ports."""

from __future__ import annotations

from dataclasses import asdict

from railway_detection.annotation.evidence_review.contracts import digest, integer
from railway_detection.application.contracts import closed_json
from railway_detection.application.preflight.catalog import (
    DOCS,
    _metadata,
    current_request,
    engine,
    load_catalog,
)
from railway_detection.safety.constructed_authority import sha

from .ports import ActivationPorts
from .reporting import dashboard as previous_dashboard
from .reporting import load_package

EVENTS = (
    "train_events/event_005",
    "train_events/event_021",
    "engine_events/event_001",
    "train_events/event_001",
    "no_train_events/event_001",
)
SOURCE_IDS = tuple(
    f"doc:v2:{event}:{camera}:video" for event in EVENTS for camera in ("front", "back")
)
DISCOVERY = "MISSION_28_GENUINE_EVIDENCE_DISCOVERY_RECEIPT.json"


def report(*, now: int) -> dict:
    integer(now)
    body = _metadata(DOCS / DISCOVERY)
    binding = closed_json(_metadata(DOCS / "MISSION_28_DOCUMENT_BINDING.json"))
    if binding != {"schema": "MISSION28_BINDING/1", "discovery_sha256": sha(body)}:
        raise ValueError("stale Mission28 documentary discovery binding")
    discovery = closed_json(body)
    if discovery.get("schema") != "mission28-documentary-delta/1":
        raise ValueError("known Mission28 documentary discovery schema required")
    if discovery.get("actual_new_original_evidence_items") != []:
        raise ValueError("new originals require existing independently verified intake, not flags")
    catalog = load_catalog()
    package = load_package()
    sources = {s["source_id"]: s for s in package["sources"]["sources"]}
    rights = {s["source_id"]: s for s in package["rights"]["sources"]}
    service = engine(catalog)
    decisions = []
    for event in EVENTS:
        for camera in ("front", "back"):
            key = f"doc:v2:{event}:{camera}:video"
            if key not in sources or (sources[key]["event"], sources[key]["camera"]) != (
                event,
                camera,
            ):
                raise ValueError("exact existing five-event/ten-source pilot required")
            if key not in rights:
                raise ValueError("exact source rights row required")
            source_result = service.check(current_request(catalog, "M19-PERM-26", key), (), now=now)
            decisions.append(
                {
                    "source_id": key,
                    "event": event,
                    "camera": camera,
                    "source_identity_status": "SOURCE_IDENTITY_UNKNOWN",
                    "documentary_parent": sources[key]["parent"],
                    "rights_status": rights[key]["rights_status"],
                    "rights_by_dimension": rights[key]["rights"],
                    "independently_verified_identity": None,
                    "actual_reviewer_assignment": None,
                    "canonical_authorization": None,
                    "preflight": asdict(source_result),
                    "resource_binding": "DOCUMENTARY_ONLY_NOT_VERIFIED_PHYSICAL_IDENTITY",
                }
            )
    requirements = (
        (
            "SOURCE_IDENTITY",
            "ACT-01",
            "Attributable original acquisition/member/custodian evidence",
        ),
        ("EXACT_SOURCE_RIGHTS", "ACT-02", "Current exact-source and purpose rights"),
        ("EXTERNAL_APPLICABILITY", "ACT-03/04", "Actual scoped applicability determinations"),
        ("PRIMARY_REVIEWER", "ACT-05", "Actual qualified appointed primary reviewer"),
        (
            "INDEPENDENT_SECOND_REVIEW",
            "ACT-05",
            "Distinct qualified physical person and exposure evidence",
        ),
        (
            "SEPARATE_ADJUDICATION",
            "ACT-05",
            "Actual separate qualified adjudication capability",
        ),
        ("SOURCE_PRESENTATION", "ACT-06", "Accepted blind guarded source presentation"),
        (
            "TRUSTED_IDENTITY",
            "ACT-05/06",
            "Authenticated physical people and current scoped assignment",
        ),
        (
            "TRUSTED_TIME",
            "ACT-06",
            "Accepted current time service; diagnostic clock is insufficient",
        ),
        (
            "EVIDENCE_STORAGE",
            "ACT-06",
            "Authenticated immutable storage; local SQLite is not proof",
        ),
        ("AUDIT_REVOCATION", "ACT-06", "Retained anchors, current revocation and audit acceptance"),
        (
            "PROTOCOL_SCHEMA",
            "ACT-06",
            "Exact operative protocol/adoption and active 8.1 compatibility",
        ),
        (
            "CANONICAL_AUTHORIZATION",
            "ACT-06",
            "Actual current operation-specific canonical authorization",
        ),
    )
    # This is a diagnosis of shipped, absent genuine ports. JSON approval flags
    # cannot instantiate those services or authenticate an original document.
    result = previous_dashboard(now=now)
    result.update(
        {
            "schema": "MISSION28_READINESS_DASHBOARD/1",
            "discovery_digest": digest(discovery),
            "new_original_evidence_received": [],
            "pilot": {
                "schema": "MISSION28_PILOT_READINESS/1",
                "state": "PILOT_NOT_READY",
                "events": list(EVENTS),
                "sources": decisions,
                "prerequisites": [
                    {
                        "id": key,
                        "action": action,
                        "missing": reason,
                        "evidence_reference": None,
                        "status": "EVIDENCE_PENDING",
                        "required_for": "EXECUTION_ONLY"
                        if key == "CANONICAL_AUTHORIZATION"
                        else "AUTHORIZATION_REVIEW_READINESS",
                    }
                    for key, action, reason in requirements
                ],
                "missing_services": list(ActivationPorts().missing()),
                "optional_external_audit_is_universal_blocker": False,
                "release_permission_required_for_private_pilot": False,
                "T2": (
                    "DEFERRED; blocks observable physical entry/occupancy, not T1/T3/T4 preparation"
                ),
                "canonical_schema": "8.1.0-stage2.1",
                "canonical_plausibility_floor_seconds": 30,
                "RD046": "SCIENTIFIC_DURATION_SUFFICIENCY_DEFERRED",
                "authorization": None,
                "execution_receipt": None,
                "grant_issued": False,
                "execution_permitted": False,
            },
        }
    )
    return result


def render(value: dict) -> str:
    pilot = value["pilot"]
    lines = [
        "# Mission 28 updated readiness dashboard",
        "",
        f"Pilot: **{pilot['state']}**. Five existing events; ten documentary source references.",
        "No new originals received, independently verified or accepted for a purpose. "
        "Zero source authorizations, human appointments and genuine review executions.",
        "",
        (
            "21 conditional operations remain blocked; six denied/deferred "
            "selections remain preserved."
        ),
        "",
        "| Prerequisite | Missing evidence | Action |",
        "|---|---|---|",
    ]
    lines += [f"| {r['id']} | {r['missing']} | {r['action']} |" for r in pilot["prerequisites"]]
    lines += [
        "",
        "Canonical authorization is required for execution; its absence alone does not "
        "create a circular prerequisite for authorization review. The other genuine "
        "prerequisites are also absent. T2 stays deferred. Optional external audit and "
        "public release do not become universal private-pilot blockers.",
        "",
        "Exact per-source rights and preflight issues are in the JSON report and "
        "MISSION_28_FINAL_PILOT_READINESS_DECISION.json. Existing ACT-01/02 remain the priorities.",
        "",
    ]
    return "\n".join(lines)
