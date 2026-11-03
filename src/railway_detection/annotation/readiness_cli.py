"""Phase 11.12 readiness CLI: the machine-readable Phase 12 handoff.

Runs the fail-closed evaluation-readiness gate over a reviews directory and
emits a JSON blocker report. The command is read-only with respect to research
evidence: it never writes into the reviews, proposals, or allowlist paths it
reads, and it refuses to write its report inside them.

Exit codes are the contract for callers:

* ``0`` -- READY. Every mechanical condition holds. This is **not** a
  researcher approval of ground truth; starting Phase 12 still requires a
  separate human EVAL-AUTH.
* ``2`` -- NOT_READY. The report enumerates every blocker.
* ``1`` -- the gate could not be evaluated (bad usage, unreadable input).

A NOT_READY corpus is the expected outcome while no genuine Stage-2.1 review
record exists; it is a result, not a tool failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from railway_detection.annotation.evaluation_readiness_gate import (
    GROUND_TRUTH_APPROVAL_AUTHORITY,
    evaluate_readiness,
)
from railway_detection.annotation.receipt import (
    PROMOTION_RECEIPT_PRODUCER,
    PROMOTION_RECEIPT_SCHEMA,
    live_receipt_inputs,
    receipt_body_sha256,
    review_record_hashes,
)
from railway_detection.safety.media_guard import require_media_authorization

EXIT_READY = 0
EXIT_ERROR = 1
EXIT_NOT_READY = 2

DEFAULT_REVIEWS_DIR = Path("data/ground_truth/reviews")
DEFAULT_ALLOWLIST = Path("data/ground_truth/authorized_reviewers.json")
DEFAULT_INVENTORY = Path("data/manifests/layer_b_v2_annotation_inventory.json")
DEFAULT_PROPOSALS_DIR = Path("data/ground_truth/proposals")
DEFAULT_STAGE = "stage3_single_camera_baseline"
_COHORTS = ("train_events", "no_train_events", "engine_events")


class ReadinessCliError(Exception):
    """Raised for actionable usage or input problems (exit code 1)."""


def _sha256_file(path: Path) -> str:
    require_media_authorization(path, "HASH_RAW_MEDIA")  # no-op for non-media metadata files
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_media_context(
    inventory_path: Path,
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    """Read the Layer B inventory into the gate's registry and path mappings.

    Returns ``(media_sha256_registry, media_file_paths)`` keyed by event id.
    The inventory is the independently verified manifest; this function does
    not re-hash media, because the gate itself performs the live comparison.
    """
    if not inventory_path.exists():
        raise ReadinessCliError(
            f"annotation inventory not found: {inventory_path}. "
            "Pass --inventory with the Layer B annotation inventory JSON."
        )
    try:
        raw = json.loads(inventory_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReadinessCliError(f"annotation inventory unreadable: {exc}") from exc
    if not isinstance(raw, dict):
        raise ReadinessCliError(
            f"annotation inventory {inventory_path} must contain a JSON object"
        )

    registry: dict[str, dict[str, str]] = {}
    paths: dict[str, dict[str, str]] = {}
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            raise ReadinessCliError(f"inventory entry {key!r} must be a JSON object")
        event_id = entry.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            raise ReadinessCliError(f"inventory entry {key!r} has no usable event_id")
        sides: dict[str, str] = {}
        side_paths: dict[str, str] = {}
        for side in ("front", "back"):
            side_entry = entry.get(side)
            if not isinstance(side_entry, dict):
                raise ReadinessCliError(f"inventory entry {key!r} has no {side!r} media block")
            sha = side_entry.get("sha256")
            path_value = side_entry.get("path")
            if not isinstance(sha, str) or len(sha) != 64:
                raise ReadinessCliError(f"inventory entry {key!r} {side} sha256 is not a digest")
            if not isinstance(path_value, str) or not path_value.strip():
                raise ReadinessCliError(f"inventory entry {key!r} {side} path is missing")
            sides[side] = sha
            side_paths[side] = path_value
        # Cohort-qualified identity: ``event_001`` exists in several cohorts, and keying by the
        # bare id would silently overwrite entries (the last cohort would win).
        category = entry.get("category")
        identity = f"{category}/{event_id}" if category in _COHORTS else event_id
        if identity in registry:
            raise ReadinessCliError(f"duplicate inventory identity {identity!r}")
        registry[identity] = sides
        paths[identity] = side_paths
    return registry, paths


def load_active_proposals(proposals_dir: Path) -> dict[str, str]:
    """Hash the currently active proposal file per event.

    The highest version present for an event is treated as active, matching
    the immutable ``*_proposal_v{N}.json`` naming the annotator writes. A
    missing directory yields an empty mapping, which the gate then reports as
    a per-record blocker rather than silently accepting.
    """
    if not proposals_dir.exists():
        return {}
    active: dict[str, tuple[int, Path]] = {}
    for path in sorted(proposals_dir.rglob("*_proposal_v*.json")):
        stem = path.stem
        event_id, _, version_part = stem.partition("_proposal_v")
        if not event_id or not version_part.isdigit():
            continue
        version = int(version_part)
        # Cohort directory qualifies the identity; a flat layout keeps the bare id.
        identity = f"{path.parent.name}/{event_id}" if path.parent.name in _COHORTS else event_id
        current = active.get(identity)
        if current is None or version > current[0]:
            active[identity] = (version, path)
    resolved: dict[str, str] = {}
    for event_id, (_, path) in active.items():
        try:
            resolved[event_id] = _sha256_file(path)
        except OSError as exc:
            raise ReadinessCliError(f"could not hash active proposal {path}: {exc}") from exc
    return resolved


def _assert_report_target_is_safe(report_path: Path, protected: list[Path]) -> None:
    """Refuse to write the report inside any research-evidence directory."""
    resolved = report_path.resolve()
    for guard in protected:
        guard_resolved = guard.resolve()
        if resolved == guard_resolved or guard_resolved in resolved.parents:
            raise ReadinessCliError(
                f"refusing to write the readiness report inside protected path {guard}. "
                "Choose a report path outside the review, proposal, and manifest trees."
            )


def render_markdown_report(report: dict[str, Any]) -> str:
    """Render a deterministic human-readable view of a readiness report.

    The JSON emitted by this CLI is the machine-readable contract.  This
    companion rendering deliberately contains no generation timestamp, random
    identifier, or filesystem metadata so that repeated audits remain diffable
    and idempotent.  It is a presentation of the same gate result; it never
    changes the fail-closed predicates or suppresses a blocker.
    """
    status = "READY" if report.get("ready") else "NOT_READY"
    lines = [
        "# Evaluation Readiness Blocker Report",
        "",
        f"- Status: **{status}**",
        f"- Stage: `{report.get('stage') or 'unspecified'}`",
        f"- Blockers: **{report.get('blocker_count', 0)}**",
        "- Mechanical checks do not constitute researcher approval; "
        "a human researcher signature remains required.",
        "",
        "## Blockers",
    ]
    blockers = report.get("blockers") or []
    if not blockers:
        lines.append("No mechanical blockers.")
    else:
        lines.extend(
            [
                "| Code | Event/cohort | Detail |",
                "|---|---|---|",
            ]
        )
        for blocker in blockers:
            if not isinstance(blocker, dict):
                lines.append(f"| — | — | {blocker} |")
                continue
            code = str(blocker.get("code") or "—").replace("|", "\\|")
            event_id = str(blocker.get("event_id") or "—").replace("|", "\\|")
            detail = str(blocker.get("detail") or "—").replace("|", "\\|")
            lines.append(f"| `{code}` | `{event_id}` | {detail} |")
    lines += [
        "",
        "## Inputs",
    ]
    inputs = report.get("inputs") or {}
    if inputs:
        for key in sorted(inputs):
            lines.append(f"- {key}: `{inputs[key]}`")
    else:
        lines.append("No input metadata supplied.")
    lines += [
        "",
        "## Evidence",
    ]
    evidence = report.get("evidence") or []
    lines.extend(f"- {item}" for item in evidence) if evidence else lines.append("None.")
    lines += [
        "",
        "## Contract",
        "- Exit code `0`: READY; exit code `2`: NOT_READY; exit code `1`: evaluation error.",
        "- This report is read-only with respect to review records, proposals, allowlists, and media.",
    ]
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="railway-readiness",
        description=(
            "Evaluate Phase 11.12 evaluation readiness and emit a machine-readable "
            "blocker report. Read-only; exit 2 means NOT_READY."
        ),
    )
    parser.add_argument(
        "--reviews-dir",
        type=Path,
        default=DEFAULT_REVIEWS_DIR,
        help=f"Directory of *_review.json records. Default: {DEFAULT_REVIEWS_DIR}",
    )
    parser.add_argument(
        "--allowlist",
        type=Path,
        default=DEFAULT_ALLOWLIST,
        help=f"Authorized-reviewer allowlist JSON. Default: {DEFAULT_ALLOWLIST}",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=DEFAULT_INVENTORY,
        help=f"Layer B annotation inventory JSON. Default: {DEFAULT_INVENTORY}",
    )
    parser.add_argument(
        "--proposals-dir",
        type=Path,
        default=DEFAULT_PROPOSALS_DIR,
        help=f"Directory of candidate proposals. Default: {DEFAULT_PROPOSALS_DIR}",
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path("."),
        help="Repository root used to verify the AI proposal each record is bound to "
        "(RD-043 'corrected from candidate' trigger). Default: current directory.",
    )
    parser.add_argument(
        "--stage",
        default=DEFAULT_STAGE,
        help=f"Named evaluation stage being checked. Default: {DEFAULT_STAGE}",
    )
    parser.add_argument(
        "--required-cohort",
        action="append",
        default=None,
        dest="required_cohorts",
        help="Cohort that must have an approved record; repeatable.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=None,
        help="Write the JSON report here in addition to stdout.",
    )
    parser.add_argument(
        "--markdown-path",
        "--md-path",
        type=Path,
        default=None,
        help="Write a deterministic human-readable Markdown report here.",
    )
    parser.add_argument(
        "--receipt-path",
        type=Path,
        default=None,
        help=(
            "On READY only, write a hash-bound promotion receipt "
            "(phase12-stage21-promotion-receipt/2) that the Phase 12 execution "
            "gate consumes instead of re-hashing media. Never written on NOT_READY."
        ),
    )
    return parser


def build_promotion_receipt(args: argparse.Namespace, report: dict[str, Any]) -> dict[str, Any]:
    """Bind a READY verdict to every metadata input that influenced it.

    Bound: the exact review-record bytes, the reviewer allowlist, the annotation
    inventory and the active proposals (see ``annotation.receipt``). The receipt is
    tamper-evident: changing any of them afterwards makes the execution gate reject
    it. It is not a signature and does not prove that this CLI produced it.
    """
    if not report.get("ready"):
        raise ReadinessCliError("a promotion receipt can only be written for a READY verdict")
    record_hashes = review_record_hashes(Path(args.reviews_dir))
    if not record_hashes:
        raise ReadinessCliError("no review records to bind in the receipt")
    receipt = {
        "schema_version": PROMOTION_RECEIPT_SCHEMA,
        "produced_by": PROMOTION_RECEIPT_PRODUCER,
        "produced_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stage": report["stage"],
        "verdict": {"ready": True, "blocker_count": int(report["blocker_count"])},
        "review_record_sha256": record_hashes,
        "inputs": live_receipt_inputs(
            inventory=Path(args.inventory),
            proposals_dir=Path(args.proposals_dir),
            allowlist=Path(args.allowlist),
        ),
        "media_hashes_verified_live": True,
    }
    receipt["receipt_sha256"] = receipt_body_sha256(receipt)
    return receipt


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    """Run the gate and assemble the machine-readable report."""
    registry, media_paths = load_media_context(args.inventory)
    active_proposals = load_active_proposals(args.proposals_dir)

    cohorts = tuple(args.required_cohorts) if args.required_cohorts else None
    kwargs: dict[str, Any] = {
        "reviews_dir": args.reviews_dir,
        "active_proposal_sha256_by_event": active_proposals,
        "media_sha256_registry": registry,
        "allowlist_path": args.allowlist,
        "media_file_paths": media_paths,
        "stage": args.stage,
        "repository_root": Path(args.repository_root),
    }
    if cohorts is not None:
        kwargs["required_cohorts"] = cohorts

    verdict = evaluate_readiness(**kwargs)
    report = verdict.to_dict()
    report["inputs"] = {
        "reviews_dir": str(args.reviews_dir),
        "allowlist": str(args.allowlist),
        "inventory": str(args.inventory),
        "proposals_dir": str(args.proposals_dir),
        "inventory_event_count": len(registry),
        "active_proposal_count": len(active_proposals),
    }
    report["exit_code"] = EXIT_READY if verdict.ready else EXIT_NOT_READY
    return report


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        protected = [args.reviews_dir, args.proposals_dir, args.allowlist, args.inventory]
        if args.report_path is not None:
            _assert_report_target_is_safe(args.report_path, protected)
        if args.markdown_path is not None:
            _assert_report_target_is_safe(args.markdown_path, protected)
        if args.receipt_path is not None:
            _assert_report_target_is_safe(args.receipt_path, protected)
        report = build_report(args)
        receipt = (
            build_promotion_receipt(args, report)
            if args.receipt_path is not None and report["ready"]
            else None
        )
    except ReadinessCliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, ValueError) as exc:
        print(f"error: readiness evaluation failed: {exc}", file=sys.stderr)
        return EXIT_ERROR

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report_path is not None:
        try:
            args.report_path.parent.mkdir(parents=True, exist_ok=True)
            args.report_path.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            print(f"error: could not write report to {args.report_path}: {exc}", file=sys.stderr)
            return EXIT_ERROR

    if args.markdown_path is not None:
        try:
            args.markdown_path.parent.mkdir(parents=True, exist_ok=True)
            args.markdown_path.write_text(render_markdown_report(report), encoding="utf-8")
        except OSError as exc:
            print(
                f"error: could not write Markdown report to {args.markdown_path}: {exc}",
                file=sys.stderr,
            )
            return EXIT_ERROR

    if receipt is not None:
        try:
            args.receipt_path.parent.mkdir(parents=True, exist_ok=True)
            args.receipt_path.write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        except OSError as exc:
            print(f"error: could not write receipt to {args.receipt_path}: {exc}", file=sys.stderr)
            return EXIT_ERROR

    print(rendered, end="")
    if report["ready"]:
        print(
            "READY: mechanical checks passed. Ground-truth approval remains "
            f"{GROUND_TRUTH_APPROVAL_AUTHORITY}; Phase 12 still requires EVAL-AUTH.",
            file=sys.stderr,
        )
        return EXIT_READY

    print(
        f"NOT_READY: {report['blocker_count']} blocker(s). See the report above.",
        file=sys.stderr,
    )
    return EXIT_NOT_READY


if __name__ == "__main__":
    sys.exit(main())
