"""Deterministic Mission27 documentary overlay on the unchanged Mission26 preflight."""

from __future__ import annotations

from railway_detection.annotation.evidence_review.contracts import digest, integer
from railway_detection.application.contracts import closed_json
from railway_detection.application.preflight.catalog import DOCS, _metadata, load_catalog
from railway_detection.application.preflight.catalog import dashboard as prior_dashboard
from railway_detection.application.preflight.catalog import render as prior_render

FILES = {
    "sources": "MISSION_27_SOURCE_IDENTITY_AND_PROVENANCE_REGISTER.json",
    "rights": "MISSION_27_SOURCE_RIGHTS_VERIFICATION_REGISTER.json",
    "external": "MISSION_27_EXTERNAL_REQUIREMENTS_RESOLUTION.json",
    "reviewers": "MISSION_27_REVIEWER_APPOINTMENT_AND_QUALIFICATION_REGISTER.json",
    "actions": "MISSION_27_RESEARCHER_ACTION_REGISTER.json",
    "evidence": "MISSION_27_EVIDENCE_REGISTER.json",
}


def load_package() -> dict:
    binding = closed_json(_metadata(DOCS / "MISSION_27_DOCUMENT_BINDING.json"))
    if set(binding) != {"schema", "document_sha256"} or binding["schema"] != "MISSION27_BINDING/1":
        raise ValueError("known documentary binding schema required")
    if set(binding["document_sha256"]) != set(FILES.values()):
        raise ValueError("exact Mission27 document set required")
    from railway_detection.safety.constructed_authority import sha

    package = {}
    for key, name in FILES.items():
        body = _metadata(DOCS / name)
        if sha(body) != binding["document_sha256"][name]:
            raise ValueError("stale Mission27 documentary binding: " + name)
        package[key] = closed_json(body)
    return package


def dashboard(*, now: int) -> dict:
    integer(now)
    catalog = load_catalog()
    package = load_package()
    report = prior_dashboard(catalog, now=now)
    if package["evidence"]["submitted_items"]:
        raise ValueError("new submissions require independently reviewed dashboard integration")
    # No production verifier is available. Status flags never manufacture verification.
    report.update(
        {
            "schema": "MISSION27_READINESS_DASHBOARD/1",
            "documentary_package_digest": digest(package),
            "documentary_evidence_found": package["evidence"]["documentary_findings"],
            "evidence_stages": {
                "submitted": 0,
                "parsed": 0,
                "structurally_valid": 0,
                "attributable": 0,
                "independently_verified": 0,
                "permission_accepted_for_specific_purpose": 0,
                "expired": 0,
                "revoked": 0,
                "rejected": 0,
            },
            "reviewers_appointed": 0,
            "reviewers_qualified": 0,
            "source_identities_verified": 0,
            "human_review_ready": False,
            "operations_ready_for_authorization_review": 0,
            "operations_authorized": 0,
            "operations_executed": 0,
            "submission_register": FILES["evidence"],
            "source_identity_register": FILES["sources"],
            "rights_verification_register": FILES["rights"],
            "reviewer_register": FILES["reviewers"],
            "external_resolution_register": FILES["external"],
            "missing_evidence_requests": package["actions"]["requests"],
            "expired_evidence": [],
            "revoked_evidence": [],
            "unverified_dates_are_not_inferred_current": True,
            "trusted_adapters_enabled": False,
            "historical_mission26_modified": False,
            "evidence_scope": (
                "Accessible documentary findings; not original permissions or human evidence"
            ),
        }
    )
    return report


def render(report: dict) -> str:
    body = prior_render(report).replace(
        "# Mission 26 — Real-data readiness dashboard",
        "# Mission 27 — Updated genuine evidence and review readiness",
    )
    body += "\n## Evidence and activation stages\n\n| Stage | Actual count/state |\n|---|---|\n"
    count = len(report["documentary_evidence_found"])
    body += f"| Documentary findings (references, not approvals) | {count} |\n"
    for key, value in report["evidence_stages"].items():
        body += f"| {key} | {value} |\n"
    for key in (
        "reviewers_appointed",
        "reviewers_qualified",
        "source_identities_verified",
        "human_review_ready",
        "operations_ready_for_authorization_review",
        "operations_authorized",
        "operations_executed",
    ):
        body += f"| {key} | {report[key]} |\n"
    body += (
        "\nNo submitted original permission/appointment items, known expired items "
        "or known revoked "
        "items are present. Missing dates are unknown, never current permission.\n\n"
        "Documentary findings: `MISSION_27_EVIDENCE_REGISTER.json`; full search references: "
        "`MISSION_27_DOCUMENTARY_SEARCH_RECEIPT.json`. Exact source, rights, human and external "
        "gaps are in the Mission27 registers; no status flag enables genuine verification.\n\n"
        "## Prioritized missing evidence\n\n"
    )
    for row in report["missing_evidence_requests"]:
        body += f"- {row['id']} — {row['responsible_party']}: {row['why_required']}.\n"
    return body
