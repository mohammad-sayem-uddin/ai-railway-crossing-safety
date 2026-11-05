"""Local application commands; all execution routes remain constructed/resource-free."""

from __future__ import annotations

import json
import sqlite3
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REGISTER = ROOT / "docs/generated/master_reaudit/MISSION_26_TEST_CLASSIFICATION_REGISTER.json"


@dataclass(frozen=True)
class ComponentContract:
    package: str
    interface: str
    responsibility: str
    boundary: str


COMPONENTS = (
    ComponentContract(
        "WP01",
        "EventSimulationRunner.run_frames_convention_b",
        "exact causal actuator simulation",
        "constructed exact-clock frame envelopes",
    ),
    ComponentContract(
        "WP02",
        "validate_registry / join_lineage",
        "grouped-CV transitive exposure",
        "constructed registry only; no fitting",
    ),
    ComponentContract(
        "WP03",
        "TypedConstructedReviewService / ConstructedReviewService",
        "immutable review session/history",
        "fixture actors; genuine records rejected",
    ),
    ComponentContract(
        "WP04",
        "ConstructedAuthority / ConstructedResourceBroker",
        "point-of-use scope and shared transaction",
        "mock principals/time/local storage",
    ),
    ComponentContract(
        "WP05",
        "project_b_metrics / classify_m4",
        "sampled M4/M5 contracts and null reasons",
        "no empirical outcomes",
    ),
    ComponentContract(
        "WP06",
        "validate_stream_bindings",
        "independent exact camera sources",
        "no fusion/back-audio",
    ),
    ComponentContract(
        "WP07",
        "validate_manifest / join_lineage",
        "source/artifact identity and exposure joins",
        "lineage is not resource permission",
    ),
    ComponentContract(
        "WP08",
        "build_source_snapshot / write_source_snapshot",
        "explicit deterministic source snapshot",
        "protected roots excluded",
    ),
    ComponentContract(
        "WP09",
        "render_descriptive_support",
        "results-absent reporting",
        "no real results or release",
    ),
    ComponentContract(
        "WP10",
        "run_resource_free_acceptance",
        "source-bound guarded test selection",
        "protected dependencies not executed",
    ),
)


def add_arguments(subparsers):
    app = subparsers.add_parser("application", help="Unified constructed research application")
    commands = app.add_subparsers(dest="application_command", required=True)
    from railway_detection.annotation.evidence_review.integration import (
        add_arguments as add_review_arguments,
    )

    add_review_arguments(commands)
    from railway_detection.application.preflight.catalog import (
        add_arguments as add_readiness_arguments,
    )

    add_readiness_arguments(commands)
    demo = commands.add_parser("demo", help="Run the complete constructed application")
    demo.add_argument("--output", required=True)
    demo.add_argument("--seed", type=int, default=22)
    demo.add_argument("--code-identity")
    demo.add_argument("--resume", action="store_true")
    demo.add_argument(
        "--interrupt-after",
        choices=("initialization", "review_commit", "review", "workflow", "application_receipt"),
    )
    demo.set_defaults(func=_dispatch)
    for name in ("verify", "receipt"):
        parser = commands.add_parser(
            name, help="Verify and inspect a completed constructed application"
        )
        parser.add_argument("--output", required=True)
        parser.set_defaults(func=_dispatch)
    for name in ("acceptance", "synthetic-test"):
        parser = commands.add_parser(
            name, help="Run guarded selected tests with an explicit receipt"
        )
        parser.add_argument("--output", required=True)
        parser.add_argument("--register", type=Path, default=REGISTER)
        parser.set_defaults(func=_dispatch)
    validation = commands.add_parser(
        "validation", help="Inspect a resource-free validation receipt"
    )
    validation.add_argument("--receipt", type=Path, required=True)
    validation.set_defaults(func=_dispatch)
    architecture = commands.add_parser(
        "architecture", help="Inspect application dependency contracts"
    )
    architecture.set_defaults(func=_dispatch)


def _runner():
    from scripts import run_resource_free_acceptance

    return run_resource_free_acceptance


def _register_path(value: Path) -> Path:
    candidate = value.absolute()
    if not candidate.name.endswith("_TEST_CLASSIFICATION_REGISTER.json"):
        raise ValueError("only named test-classification metadata is accepted")
    for path in (candidate, candidate.parent.resolve() / candidate.name):
        for family in ("data", "results", "experiments", "models", "outputs"):
            protected = ROOT / family
            if path == protected or protected in path.parents:
                raise ValueError("protected resource cannot be a classification register")
    if candidate.is_symlink():
        raise ValueError("classification register alias refused")
    return value


def run_acceptance(args):
    _register_path(args.register)
    runner = _runner()
    if args.application_command == "acceptance":
        return runner.main(["run", "--output", args.output, "--register", str(args.register)])
    register = json.loads(args.register.read_text())
    problems = runner.validate(ROOT, register)
    chosen = runner.selection(register)
    if problems or chosen["unknown"]:
        print(
            json.dumps(
                {
                    "status": "CLASSIFICATION_UNTRUSTED",
                    "issues": problems,
                    "unknown": chosen["unknown"],
                }
            )
        )
        return 3
    selected = [
        node
        for node in chosen["selected"]
        if node.startswith(
            (
                "tests/synthetic_mission24/",
                "tests/synthetic_mission25/",
                "tests/synthetic_mission26/",
            )
        )
    ]
    if not selected:
        raise ValueError("no classified application tests; do not infer a pass")
    outside = sorted(set(chosen["selected"]) - set(selected))
    return runner.execute(
        runner.destination(args.output),
        selected,
        audit=False,
        exclusions={
            "NOT_EXECUTED_PROTECTED_DEPENDENCY": chosen["protected"],
            "NOT_EXECUTED_OUTSIDE_SYNTHETIC_SCOPE": outside,
            "NOT_EXECUTED_UNKNOWN": [],
        },
    )


def inspect_validation_receipt(value: Path):
    path = value.absolute()
    if path.name != "receipt.json" and not path.name.endswith("_EXECUTION_RECEIPT.json"):
        raise ValueError("named validation execution metadata required")
    for family in ("data", "results", "experiments", "models", "outputs"):
        protected = ROOT / family
        if path == protected or protected in path.parents:
            raise ValueError("protected resource cannot be validation metadata")
    resolved = path.resolve()
    for family in ("data", "results", "experiments", "models", "outputs"):
        protected = ROOT / family
        if resolved == protected or protected in resolved.parents:
            raise ValueError("validation alias enters protected resource tree")
    if path.is_symlink() or path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("validation alias or oversized receipt refused")
    from railway_detection.application.contracts import closed_json

    receipt = closed_json(path.read_text())
    if type(receipt) is not dict or receipt.get("schema") != "resource-free-execution/1":
        raise ValueError("unsupported validation receipt schema")
    groups = receipt.get("groups")
    totals = receipt.get("totals")
    if (
        type(groups) is not list
        or not groups
        or any(type(g) is not dict for g in groups)
        or type(totals) is not dict
    ):
        raise ValueError("executed groups and exact totals required")
    for key in ("tests", "passed", "failures", "errors", "skipped"):
        if type(totals.get(key)) is not int or totals[key] < 0:
            raise ValueError("exact nonnegative validation counts required")
    if totals["tests"] != sum(totals[k] for k in ("passed", "failures", "errors", "skipped")):
        raise ValueError("validation case totals inconsistent")
    for key in ("tests", "failures", "errors", "skipped"):
        if (
            any(type(g.get(key)) is not int or g[key] < 0 for g in groups)
            or sum(g[key] for g in groups) != totals[key]
        ):
            raise ValueError("validation group totals inconsistent")
    claimed_pass = receipt.get("status") == "PASSED_SELECTED_RESOURCE_FREE"
    if claimed_pass and (
        receipt.get("execution_complete") is not True
        or receipt.get("source_bindings_unchanged") is not True
        or any(type(g.get("exit_code")) is not int or g["exit_code"] != 0 for g in groups)
        or any(totals[k] for k in ("failures", "errors"))
    ):
        raise ValueError("validation cannot claim success for incomplete/nonpassing execution")
    return {
        "schema": "VALIDATION_RECEIPT_INSPECTION/1",
        "status": receipt.get("status"),
        "totals": totals,
        "not_executed": {key: len(nodes) for key, nodes in receipt.get("not_executed", {}).items()},
        "verification": "internal consistency only; no source or authentication assurance",
    }


def _dispatch(args):
    try:
        if args.application_command == "validation":
            print(json.dumps(inspect_validation_receipt(args.receipt), sort_keys=True))
            return 0
        if args.application_command == "architecture":
            print(
                json.dumps(
                    {
                        "schema": "APPLICATION_ARCHITECTURE/1",
                        "components": [asdict(c) for c in COMPONENTS],
                        "comparator_active": False,
                        "live_resource_route": False,
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.application_command in {"acceptance", "synthetic-test"}:
            return run_acceptance(args)
        from railway_detection.application.contracts import ApplicationRequest
        from railway_detection.application.workflow import ConstructedApplication, text_digest

        service = ConstructedApplication()
        if args.application_command in {"receipt", "verify"}:
            receipt = service.verify(args.output)
            print(receipt.to_json(), end="")
        else:
            code = (
                args.code_identity
                or subprocess.check_output(
                    ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
                ).strip()
            )
            request = ApplicationRequest.constructed(code_identity=code, seed=args.seed)
            receipt = service.run(
                args.output, request, resume=args.resume, stop_after=args.interrupt_after
            )
            print(
                json.dumps(
                    {
                        "schema": receipt.schema,
                        "classification": receipt.request.classification,
                        "complete": True,
                        "comparator_active": False,
                        "genuine_evidence": False,
                        "application_digest": text_digest(receipt.to_json()),
                    },
                    sort_keys=True,
                )
            )
        return 0
    except InterruptedError as error:
        print(
            json.dumps(
                {
                    "schema": "APPLICATION_ERROR/1",
                    "status": "CONSTRUCTED_INTERRUPTION",
                    "error": str(error),
                }
            )
        )
        return 75
    except (ValueError, OSError, TypeError, KeyError, sqlite3.Error) as error:
        print(
            json.dumps({"schema": "APPLICATION_ERROR/1", "status": "REFUSED", "error": str(error)})
        )
        return 2
