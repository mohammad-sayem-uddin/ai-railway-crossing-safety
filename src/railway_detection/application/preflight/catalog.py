"""Fixed documentary catalog and local readiness report. Never dereference resource paths."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from railway_detection.annotation.evidence_review.contracts import canonical, digest
from railway_detection.application.contracts import closed_json
from railway_detection.application.preflight.engine import DOCUMENTARY, PreflightEngine, Request

ROOT = Path(__file__).resolve().parents[4]
DOCS = ROOT / "docs/generated/master_reaudit"
CATALOG = "MISSION_26_READINESS_CATALOG.json"
BINDING = "MISSION_26_CATALOG_BINDING.json"


def _metadata(path: Path) -> str:
    # Check lexical and all resolved parents before read/stat; never probe resource strings.
    path = path.absolute()
    if (
        ".." in path.parts
        or (
            ROOT / "docs" not in path.parents
            and path not in (ROOT / "README.md", ROOT / "configs/vision.yaml")
        )
        or path.suffix not in (".json", ".md", ".yaml")
    ):
        raise ValueError("only reviewed documentary metadata allowed")
    for parent in reversed((path, *path.parents)):
        if parent.is_symlink():
            raise ValueError("document metadata alias refused")
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("bounded documentary metadata required")
    return path.read_text()


def load_catalog() -> dict:
    binding = closed_json(_metadata(DOCS / BINDING))
    if (
        set(binding) != {"schema", "catalog_sha256", "document_bindings"}
        or binding["schema"] != "MISSION26_CATALOG_BINDING/1"
    ):
        raise ValueError("unknown catalog binding schema")
    from railway_detection.safety.constructed_authority import sha

    body = _metadata(DOCS / CATALOG)
    if sha(body) != binding["catalog_sha256"]:
        raise ValueError("altered source catalog")
    catalog = closed_json(body)
    if catalog.get("schema") != "RESEARCH_PREFLIGHT_CATALOG/1":
        raise ValueError("unknown readiness catalog schema")
    if type(binding["document_bindings"]) is not dict:
        raise ValueError("typed document manifest required")
    for relative, expected in binding["document_bindings"].items():
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("document provenance escape")
        if sha(_metadata(ROOT / relative)) != expected:
            raise ValueError("stale source-document manifest: " + relative)
    verify_catalog(catalog)
    return catalog


def verify_catalog(catalog: dict):
    from railway_detection.annotation.evidence_review.contracts import CANDIDATE_EVENTS, R04_EVENTS

    if (
        set(catalog["candidate_events"]) != set(CANDIDATE_EVENTS)
        or len(catalog["candidate_events"]) != 27
        or set(catalog["R04_events"]) != set(R04_EVENTS)
        or len(catalog["R04_events"]) != 11
        or catalog["inventory_signoff"] is not False
    ):
        raise ValueError("candidate/R04 inventory direction or signoff substituted")
    sources = catalog["sources"]
    if len({s["source_id"] for s in sources}) != len(sources):
        raise ValueError("duplicate documentary source identity")
    active = [s for s in sources if s["eligibility"] == "CANDIDATE_ONLY"]
    if (
        {(s["event"], s["camera"]) for s in active}
        != {(e, c) for e in CANDIDATE_EVENTS for c in ("front", "back")}
        or len(active) != 54
        or any(s["live_digest_verified"] is not False for s in sources)
    ):
        raise ValueError("documentary source coverage/claimed live verification altered")
    for s in sources:
        if s["classification"] != "UNVERIFIED_DOCUMENTARY_SOURCE" or not s["provenance"]:
            raise ValueError("source provenance/classification missing")


def engine(catalog: dict) -> PreflightEngine:
    verify_catalog(catalog)
    return PreflightEngine(
        catalog_digest=digest(catalog),
        decisions=tuple((r["id"], r["selection_preserved"]) for r in catalog["operations"]),
        resources=tuple((s["source_id"], digest(s)) for s in catalog["sources"]),
        purposes=tuple((r["id"], r["purpose"]) for r in catalog["operations"]),
        parents=tuple(
            (s["source_id"], (s["provenance"]["document_sha256"],)) for s in catalog["sources"]
        ),
    )


def current_request(
    catalog: dict,
    operation: str,
    resource_id: str,
    *,
    actor=None,
    role=None,
    purpose=None,
    environment=None,
) -> Request:
    sources = {s["source_id"]: s for s in catalog["sources"]}
    if resource_id not in sources:
        raise ValueError(
            "exact named documentary resource required; filesystem paths are not accepted"
        )
    source = sources[resource_id]
    return Request(
        "readiness:" + operation + ":" + resource_id,
        operation,
        resource_id,
        digest(source),
        actor,
        role,
        purpose,
        environment,
        None,
        None,
        None,
        None,
        (source["provenance"]["document_sha256"],),
        classification=DOCUMENTARY,
    )


def dashboard(catalog: dict, *, now: int) -> dict:
    service = engine(catalog)
    # Every operation still lacks its own exact complete resource package. The
    # example documentary source below is explicitly a diagnostic binding only.
    source = catalog["sources"][0]["source_id"]
    operations = []
    for row in catalog["operations"]:
        result = service.check(current_request(catalog, row["id"], source), (), now=now)
        operations.append(
            {
                "id": row["id"],
                "operation": row["operation"],
                "selection": row["selection_preserved"],
                "exact_operation_resource": None,
                "diagnostic_documentary_resource": source,
                "preflight": asdict(result),
                "resource_classification": row["readiness_classification"],
                "authority_record": None,
                "executed": False,
            }
        )
    return {
        "schema": "MISSION26_READINESS_DASHBOARD/1",
        "catalog_digest": digest(catalog),
        "inventory": {
            "candidate_events": 27,
            "train": 23,
            "no_train": 3,
            "engine_case": 1,
            "current_video_references": 54,
            "other_reference_rows": len(catalog["sources"]) - 54,
            "R04_count": 11,
            "signoff": False,
            "physical_inventory_verified": False,
        },
        "source_rights": [
            {
                "source_id": s["source_id"],
                "status": s["rights_status"],
                "rights": s["rights"],
                "provenance": s["provenance"],
            }
            for s in catalog["sources"]
        ],
        "human_roles": catalog["human_roles"],
        "landmarks": catalog["landmarks"],
        "external_requirements": catalog["external_requirements"],
        "operations": operations,
        "experiments": catalog["experiments"],
        "documentary_conflicts": catalog["documentary_conflicts"],
        "authorized_but_not_executed": [],
        "executed_operations": [],
        "new_grants": 0,
        "protected_resources_accessed": False,
    }


def render(report: dict) -> str:
    rows = [
        "# Mission 26 — Real-data readiness dashboard",
        "",
        "Metadata-only readiness. No new permission, real operation, human observation or result.",
        "",
        "Candidate inventory: 27 = 23+3+1; 54 current camera references; R04 exact 11. "
        "Documentary consistency verified; physical/source identity and signoff remain unverified.",
        "",
        "| Operation | Selection | State | Missing prerequisite count |",
        "|---|---|---|---:|",
    ]
    rows += [
        f"| {r['id']} — {r['operation']} | {r['selection']} | "
        f"{r['preflight']['state']} | {len(r['preflight']['issues'])} |"
        for r in report["operations"]
    ]
    rows += [
        "",
        "Source rights, participation, landmark, external applicability and experiment details "
        "remain in the bound JSON dashboard/catalog. Unknown is distinct from denied. "
        "Selected is distinct from authorized; authorized is distinct from executed.",
        "",
        "Authorized-but-not-executed operations: 0. Completed operations: 0. "
        "This readiness command cannot execute an operation.",
        "",
    ]
    return "\n".join(rows)


def add_arguments(commands):
    parser = commands.add_parser(
        "readiness", help="Metadata-only real-data readiness; execution disabled"
    )
    sub = parser.add_subparsers(dest="readiness_command", required=True)
    report = sub.add_parser("report")
    report.add_argument("--format", choices=("json", "markdown"), default="markdown")
    report.add_argument("--now", type=int, required=True)
    report.set_defaults(func=dispatch)
    check = sub.add_parser("check")
    check.add_argument("--operation", required=True)
    check.add_argument("--resource", required=True)
    check.add_argument("--now", type=int, required=True)
    for field in ("actor", "role", "purpose", "environment"):
        check.add_argument("--" + field)
    check.set_defaults(func=dispatch)


def dispatch(args):
    try:
        catalog = load_catalog()
        if args.readiness_command == "report":
            report = dashboard(catalog, now=args.now)
            print(render(report) if args.format == "markdown" else canonical(report))
            return 0  # Successful report generation is not operation readiness.
        request = current_request(
            catalog,
            args.operation,
            args.resource,
            actor=args.actor,
            role=args.role,
            purpose=args.purpose,
            environment=args.environment,
        )
        result = engine(catalog).check(request, (), now=args.now)
        print(canonical(asdict(result)))
        return 3  # No live verification/grant adapter ships in this mission.
    except (ValueError, TypeError, KeyError, OSError) as error:
        print(
            canonical(
                {"schema": "MISSION26_ERROR/1", "status": "PREFLIGHT_BLOCKED", "reason": str(error)}
            )
        )
        return 2
