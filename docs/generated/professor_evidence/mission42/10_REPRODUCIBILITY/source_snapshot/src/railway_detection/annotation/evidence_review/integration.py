"""Exact review/source/CV joins and a resource-free CLI demonstration."""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import asdict, replace
from pathlib import Path

from railway_detection.annotation.evidence_review.contracts import (
    FIXTURE,
    RISKS,
    Batch,
    BoundaryObservation,
    Permission,
    Qualification,
    Reviewer,
    ReviewerStatus,
    Source,
    canonical,
    digest,
)
from railway_detection.annotation.evidence_review.journal import ConstructedGovernanceJournal
from railway_detection.annotation.evidence_review.lifecycle import Assignment, ReviewLifecycle
from railway_detection.annotation.human_review_domain import Observation
from railway_detection.annotation.human_review_service import ReviewScope
from railway_detection.application.contracts import closed_json
from railway_detection.safety.constructed_authority import (
    ConstructedAuthority,
    Grant,
    encode_payload,
    sha,
)
from railway_detection.synthetic.integration_contracts import join_lineage
from railway_detection.synthetic.integration_fixture import make_fixture
from railway_detection.synthetic.integration_workflow import output_path

ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = ("REVIEW_DASHBOARD.json", "REVIEW_LINEAGE.json", "RESULTS_ABSENT.md")
SNAPSHOT_PATHS = (
    "src/railway_detection/annotation/evidence_review/contracts.py",
    "src/railway_detection/annotation/evidence_review/lifecycle.py",
    "src/railway_detection/annotation/evidence_review/journal.py",
    "src/railway_detection/annotation/evidence_review/integration.py",
)


def fixture_contracts(code_identity: str):
    if type(code_identity) is not str or re.fullmatch(r"[0-9a-f]{40}", code_identity) is None:
        raise ValueError("exact producing code identity required")
    fixture = make_fixture(code_identity=code_identity)
    event = fixture["identity"].physical_event
    source = next(
        r for r in fixture["manifest"].records if r.physical_event == event and r.kind == "SOURCE"
    )
    batch = Batch(
        "synthetic:mission25:batch",
        "synthetic:protocol:v1",
        fixture["manifest"].version_id,
        "synthetic:boundary-projection:v1",
        "synthetic:boundary-definition:v1",
        ((event, "TRAIN"),),
        (
            Source(
                source.record_id,
                event,
                "front",
                source.source_digest,
                fixture["manifest"].version_id,
                0,
                (1, 1_000_000),
                10_000_000,
            ),
        ),
        ("T1", "T2", "T3", "T4"),
        "synthetic:batch-creation",
        FIXTURE,
        digest(fixture["joined"]),
    )
    roster = tuple(
        Reviewer(
            f"synthetic:reviewer:{n}",
            f"synthetic:physical-person:{n}",
            ReviewerStatus.MOCK,
            Qualification(
                f"synthetic:qualification:{n}", ("REVIEWER", "ADJUDICATOR"), (event,), 0, 1000
            ),
            None,
            (),
            f"synthetic:independence:{n}",
            f"synthetic:participation:{n}",
        )
        for n in range(3)
    )
    permissions = tuple(
        Permission(
            f"synthetic:permission:{n}",
            r.reviewer_id,
            digest(batch),
            (event,),
            ("ASSIGN", "OPEN_SESSION", "SUBMIT", "COMPLETE", "ADJUDICATE"),
            "synthetic:mission25:runtime",
            "constructed review governance",
            0,
            1000,
        )
        for n, r in enumerate(roster)
    )
    return fixture, batch, roster, permissions


def join_review_lineage(engine: ReviewLifecycle, fixture: dict) -> dict:
    joined = join_lineage(
        fixture["manifest"],
        fixture["registry"],
        expected=fixture["expected_registry"],
        expected_manifest_digest=fixture["joined"]["manifest"]["manifest_digest"],
    )
    if digest(joined) != engine.batch.lineage_digest:
        raise ValueError("batch lineage/CV digest substitution")
    records = {r.record_id: r for r in fixture["manifest"].records}
    if engine.batch.manifest_reference != fixture["manifest"].version_id:
        raise ValueError("review manifest version substitution")
    for source in engine.batch.sources:
        record = records.get(source.source_id)
        if (
            record is None
            or record.kind != "SOURCE"
            or record.physical_event != source.event
            or record.source_digest != source.content_digest
        ):
            raise ValueError("review source/physical-event/content substitution")
    parents = set(records)
    overlays: list[dict[str, object]] = []
    for observation in engine.observations:
        observation.validate(engine.batch)
        if observation.previous and observation.previous not in parents:
            raise ValueError("correction observation parent missing")
        item_digest = digest(observation)
        overlays.append(
            {
                "id": item_digest,
                "source": observation.source_id,
                "previous": observation.previous,
                "classification": FIXTURE,
            }
        )
        parents.add(item_digest)
    for value in engine._adjudications.values():
        if not set(value.contributors) <= parents or (
            value.previous and value.previous not in parents
        ):
            raise ValueError("adjudication parent missing")
        item_digest = digest(value)
        overlays.append(
            {
                "id": item_digest,
                "contributors": value.contributors,
                "previous": value.previous,
                "classification": FIXTURE,
            }
        )
        parents.add(item_digest)
    return {
        "schema": "REVIEW_LINEAGE_JOIN/1",
        "classification": FIXTURE,
        "batch_digest": digest(engine.batch),
        "history_digest": digest(engine.history),
        "WP02_WP07": joined,
        "observation_overlays": overlays,
        "genuine_evidence": False,
        "eligible_for_fit_or_promotion": False,
    }


def open_fixture_journal(db, batch, roster, permissions, *, anchor):
    authority = ConstructedAuthority(
        db,
        appointments=(("synthetic:issuer", ("ISSUER",)),)
        + tuple((r.reviewer_id, ("REVIEWER",)) for r in roster),
        expected_context=permissions[0].environment,
        profile="CONSTRUCTED_ONLY",
    )
    scopes = []
    existing_history = authority.db.execute("SELECT count(*) FROM entries").fetchone()[0] > 0
    for n, (r, p) in enumerate(zip(roster, permissions, strict=True)):
        gid = f"synthetic:grant:{n}"
        resource = batch.batch_id
        if authority.db.execute("SELECT id FROM grants WHERE id=?", (gid,)).fetchone() is None:
            if existing_history:
                raise ValueError("missing authority parent; never reconstruct grants")
            authority.issue(
                "synthetic:issuer",
                Grant(
                    gid,
                    r.reviewer_id,
                    batch.events[0][0],
                    ("REVIEW",),
                    (resource,),
                    p.purpose,
                    p.environment,
                    0,
                    1000,
                    100,
                ),
            )
        if (
            existing_history
            and authority.db.execute(
                "SELECT id FROM sessions WHERE id=?", (f"synthetic:session:{n}",)
            ).fetchone()
            is None
        ):
            raise ValueError("missing authority session parent; never reconstruct")
        fence = authority.reserve(
            gid,
            session=f"synthetic:session:{n}",
            actor=r.reviewer_id,
            initial_body=encode_payload({"batch": digest(batch)}),
            operation="REVIEW",
            resource=resource,
            context=p.environment,
            purpose=p.purpose,
            now=10,
        )
        scopes.append(
            ReviewScope(
                f"synthetic:session:{n}",
                fence,
                r.reviewer_id,
                resource,
                p.environment,
                p.purpose,
                10,
            )
        )
    journal = ConstructedGovernanceJournal(authority, batch, roster, expected_anchor=anchor)
    return journal, tuple(scopes)


def run_fixture_commands(journal, scopes, batch, roster, permissions):
    for n in (0, 1):
        a = Assignment(
            f"synthetic:assignment:{n}",
            digest(batch),
            batch.events[0][0],
            roster[n].reviewer_id,
            "REVIEWER",
            tuple(s.source_id for s in batch.sources),
            permissions[n].reference,
        )
        commands = [
            ("ASSIGN", {"assignment": asdict(a)}),
            ("OPEN_SESSION", {"assignment_id": a.assignment_id}),
        ]
        for i, boundary in enumerate(batch.boundaries):
            state = "UNCERTAIN" if boundary == "T2" else "OBSERVABLE"
            point = (i + 1) * 1_000_000 + n * 100_000 if state == "OBSERVABLE" else None
            o = BoundaryObservation(
                f"synthetic:observation:{n}:{boundary}",
                roster[n].reviewer_id,
                batch.sources[0].source_id,
                batch.boundary_version,
                Observation(
                    boundary,
                    "front",
                    state,
                    "constructed fixture; no human observation",
                    value_us=point,
                    uncertainty_us=None,
                    pts_ticks=point,
                    timebase=(1, 1_000_000) if point is not None else None,
                ),
            )
            commands.append(
                ("SUBMIT", {"assignment_id": a.assignment_id, "observation": asdict(o)})
            )
        commands.append(
            (
                "COMPLETE",
                {
                    "assignment_id": a.assignment_id,
                    "risks": [(r, r == "UNCERTAIN_BOUNDARY") for r in RISKS],
                },
            )
        )
        for i, (operation, args) in enumerate(commands):
            journal.perform(
                scopes[n],
                request_id=f"synthetic:request:{n}:{i}",
                operation=operation,
                arguments=args,
                permission=permissions[n],
            )
    # An append-only informed correction, not a replacement of either blind record.
    original = journal.restore().observations[0]
    corrected = replace(
        original,
        observation_id="synthetic:correction:0:T1",
        previous=digest(original),
        correction_reason="constructed correction history exercise",
        observation=replace(original.observation, rationale="informed constructed correction"),
    )
    journal.perform(
        scopes[0],
        request_id="synthetic:request:correction",
        operation="SUBMIT",
        arguments={"assignment_id": "synthetic:assignment:0", "observation": asdict(corrected)},
        permission=permissions[0],
    )


def deterministic_result(code_identity: str) -> tuple[dict, dict, str, tuple[int, str | None]]:
    from scripts.generate_publication_tables import render_descriptive_support

    fixture, batch, roster, permissions = fixture_contracts(code_identity)
    with sqlite3.connect(":memory:") as db:
        journal, scopes = open_fixture_journal(db, batch, roster, permissions, anchor=(0, None))
        run_fixture_commands(journal, scopes, batch, roster, permissions)
        engine = journal.restore()
        return (
            engine.dashboard(now=10, permissions=permissions),
            join_review_lineage(engine, fixture),
            render_descriptive_support(),
            journal.anchor,
        )


def _output(value: Path) -> Path:
    path = output_path(value)
    if path == ROOT or ROOT in path.parents:
        raise ValueError("review demonstration requires explicit outside-checkout destination")
    return path


def _named(path: Path) -> Path:
    # Parent-first validation before reading metadata or opening SQLite.
    _output(path.parent)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("missing/aliased/oversized review artifact")
    return path


def demo(value: Path, code_identity: str) -> dict:
    from scripts.prepare_researcher_snapshot import write_source_snapshot

    out = _output(value)
    if out.exists():
        raise ValueError("destination exists; use review verify, never overwrite evidence")
    fixture, batch, roster, permissions = fixture_contracts(code_identity)
    out.mkdir()
    with sqlite3.connect(out / "constructed-governance.sqlite") as db:
        journal, scopes = open_fixture_journal(db, batch, roster, permissions, anchor=(0, None))
        run_fixture_commands(journal, scopes, batch, roster, permissions)
        engine = journal.restore()
        dashboard = engine.dashboard(now=10, permissions=permissions)
        lineage = join_review_lineage(engine, fixture)
        anchor = journal.anchor
    from scripts.generate_publication_tables import render_descriptive_support

    contents = {
        "REVIEW_DASHBOARD.json": canonical(dashboard) + "\n",
        "REVIEW_LINEAGE.json": canonical(lineage) + "\n",
        "RESULTS_ABSENT.md": render_descriptive_support(),
    }
    for name, body in contents.items():
        with (out / name).open("x") as stream:
            stream.write(body)
    write_source_snapshot(
        ROOT, SNAPSHOT_PATHS, destination=out / "snapshot", code_identity=code_identity
    )
    marker = {
        "schema": "CONSTRUCTED_REVIEW_DEMONSTRATION/1",
        "code_identity": code_identity,
        "artifacts": {name: sha(body) for name, body in contents.items()},
        "snapshot_digest": sha((out / "snapshot/SOURCE_MANIFEST.json").read_text()),
        "retained_anchor": anchor,
        "classification": FIXTURE,
        "genuine_evidence": False,
        "promotion": False,
        "live_ui": False,
    }
    with (out / "REVIEW_COMPLETE.json").open("x") as stream:
        stream.write(canonical(marker) + "\n")
    return verify(out)


def verify(value: Path) -> dict:
    from scripts.prepare_researcher_snapshot import build_source_snapshot

    out = _output(value)
    if {p.name for p in out.iterdir()} != set(ARTIFACTS) | {
        "REVIEW_COMPLETE.json",
        "constructed-governance.sqlite",
        "snapshot",
    }:
        raise ValueError("review publication is incomplete or contains pending/unknown artifacts")
    marker = closed_json(_named(out / "REVIEW_COMPLETE.json").read_text())
    if (
        set(marker)
        != {
            "schema",
            "code_identity",
            "artifacts",
            "snapshot_digest",
            "retained_anchor",
            "classification",
            "genuine_evidence",
            "promotion",
            "live_ui",
        }
        or marker["schema"] != "CONSTRUCTED_REVIEW_DEMONSTRATION/1"
        or marker["classification"] != FIXTURE
        or marker["genuine_evidence"] is not False
        or marker["promotion"] is not False
        or marker["live_ui"] is not False
        or set(marker["artifacts"]) != set(ARTIFACTS)
    ):
        raise ValueError("review completion schema/classification/artifact substitution")
    dashboard, lineage, report, anchor = deterministic_result(marker["code_identity"])
    expected = {
        "REVIEW_DASHBOARD.json": canonical(dashboard) + "\n",
        "REVIEW_LINEAGE.json": canonical(lineage) + "\n",
        "RESULTS_ABSENT.md": report,
    }
    for name, body in expected.items():
        if _named(out / name).read_text() != body or marker["artifacts"][name] != sha(body):
            raise ValueError("review artifact differs from deterministic constructed replay")
    if marker["retained_anchor"] != list(anchor):
        raise ValueError("retained journal anchor substitution")
    snapshot, contents = build_source_snapshot(
        ROOT, SNAPSHOT_PATHS, code_identity=marker["code_identity"]
    )
    if _named(out / "snapshot/SOURCE_MANIFEST.json").read_bytes() != snapshot or marker[
        "snapshot_digest"
    ] != sha(snapshot.decode()):
        raise ValueError("snapshot metadata substitution/source changed")
    for name, body in contents.items():
        if _named(out / "snapshot" / name).read_bytes() != body:
            raise ValueError("snapshot content substitution")
    fixture, batch, roster, permissions = fixture_contracts(marker["code_identity"])
    with sqlite3.connect(_named(out / "constructed-governance.sqlite")) as db:
        required_tables = {
            "grants",
            "sessions",
            "tx",
            "entries",
            "metadata",
            "batches",
            "objects",
            "governance_context",
            "governance_log",
        }
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not required_tables <= tables:
            raise ValueError(
                "missing persisted service schema; never initialize during verification"
            )
        journal, _scopes = open_fixture_journal(db, batch, roster, permissions, anchor=anchor)
        if canonical(journal.restore().dashboard(now=10, permissions=permissions)) != canonical(
            dashboard
        ):
            raise ValueError("persisted governance history differs from replay")
    return json.loads(canonical(marker))


def interface_contract() -> dict:
    return {
        "schema": "HUMAN_REVIEW_INTERFACE/1",
        "genuine_mode_enabled": False,
        "operations": [
            "batch",
            "assign",
            "session",
            "observation",
            "correction",
            "complete",
            "compare",
            "adjudication",
            "readiness",
            "receipt_validation",
            "publication",
        ],
        "required_ports": [
            "authenticated identity/session",
            "qualification and role verifier",
            "current authorization/time/revocation",
            "neutral source-access player",
            "human statement verification",
            "canonical schema acceptance",
            "external promotion receipt verification",
            "immutable publication service",
        ],
        "fixture_classification": FIXTURE,
        "automatic_adjudication": False,
        "receipt_issuer_enabled": False,
        "physical_entry_landmark": "DEFERRED",
        "duration_floor": "DEFERRED_ACTIVE_SCHEMA_RECONCILIATION_REQUIRED",
    }


def add_arguments(commands):
    parser = commands.add_parser("review", help="Metadata review governance; genuine mode disabled")
    sub = parser.add_subparsers(dest="review_command", required=True)
    for name in ("demo", "verify", "dashboard"):
        command = sub.add_parser(name)
        command.add_argument("--output", type=Path, required=True)
        if name == "demo":
            command.add_argument("--code-identity", required=True)
        command.set_defaults(func=dispatch)
    sub.add_parser("interface").set_defaults(func=dispatch)


def dispatch(args):
    try:
        if args.review_command == "interface":
            result = interface_contract()
        elif args.review_command == "demo":
            result = demo(args.output, args.code_identity)
        else:
            result = verify(args.output)
            if args.review_command == "dashboard":
                result = closed_json(
                    _named(_output(args.output) / "REVIEW_DASHBOARD.json").read_text()
                )
        print(canonical(result))
        return 0
    except (ValueError, PermissionError, OSError, TypeError, KeyError, sqlite3.Error) as exc:
        print(
            canonical(
                {"schema": "REVIEW_GOVERNANCE_ERROR/1", "status": "REFUSED", "reason": str(exc)}
            )
        )
        return 2
