"""Phase 11.12 readiness CLI: exit-code contract, safety, and idempotency.

All fixtures are synthetic and live under pytest's temporary directory. The
CLI is read-only with respect to research evidence; these tests assert that
property rather than assuming it.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from railway_detection.annotation.readiness_cli import (
    EXIT_ERROR,
    EXIT_NOT_READY,
    EXIT_READY,
    ReadinessCliError,
    load_active_proposals,
    load_media_context,
    main,
    render_markdown_report,
)
from test_phase11_12_readiness_gate import _allowlist, _three_records


def _write_reviews(tmp_path: Path, records: list[dict]) -> Path:
    reviews = tmp_path / "reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    for record in records:
        path = reviews / f"{record.get('review_id', record['event_id'])}_review.json"
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return reviews


def _write_inventory(tmp_path: Path, records: list[dict], paths: dict) -> Path:
    inventory: dict[str, dict] = {}
    for record in records:
        event_id = record["event_id"]
        side_paths = paths[event_id]
        entry = {"category": record["cohort"], "event_id": event_id}
        for side in ("front", "back"):
            media_path = Path(side_paths[side])
            entry[side] = {
                "path": str(media_path),
                "sha256": hashlib.sha256(media_path.read_bytes()).hexdigest(),
            }
        inventory[f"{record['cohort']}/{event_id}"] = entry
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    return path


def _argv(tmp_path: Path, reviews: Path, inventory: Path, **overrides) -> list[str]:
    argv = [
        "--reviews-dir", str(reviews),
        "--allowlist", str(_allowlist(tmp_path)),
        "--inventory", str(inventory),
        "--proposals-dir", str(overrides.get("proposals_dir", tmp_path / "proposals")),
        "--stage", overrides.get("stage", "phase12_single_camera_baseline"),
    ]
    if "repository_root" in overrides:
        argv += ["--repository-root", str(overrides["repository_root"])]
    if "report_path" in overrides:
        argv += ["--report-path", str(overrides["report_path"])]
    if "markdown_path" in overrides:
        argv += ["--markdown-path", str(overrides["markdown_path"])]
    return argv


def test_legacy_only_corpus_exits_not_ready(tmp_path: Path, capsys):
    """A legacy-schema corpus must exit 2 with enumerated blockers."""
    legacy = {
        "schema_version": "6.0.0",
        "event_id": "event_001",
        "cohort": "train_events",
        "adjudication_status": "APPROVED",
    }
    reviews = _write_reviews(tmp_path, [legacy])
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps({}), encoding="utf-8")

    code = main(_argv(tmp_path, reviews, inventory))
    assert code == EXIT_NOT_READY

    report = json.loads(capsys.readouterr().out)
    assert report["ready"] is False
    assert "LEGACY_OR_UNKNOWN_SCHEMA" in report["blocker_codes"]
    assert report["exit_code"] == EXIT_NOT_READY


def test_valid_synthetic_corpus_exits_ready_but_defers_approval(tmp_path: Path, capsys):
    records, _active, _registry, paths = _three_records(tmp_path)
    reviews = _write_reviews(tmp_path, records)
    inventory = _write_inventory(tmp_path, records, paths)

    proposals = tmp_path / "proposals"
    proposals.mkdir()
    for record in records:
        # A real, verifiable proposal whose candidates equal the review (nothing was corrected),
        # stored where the record's own proposal_file points, relative to the repository root.
        candidates = {
            name: {
                "candidate_observable": entry["state"] == "OBSERVABLE",
                "value_s": entry["value_s"],
            }
            for name, entry in record["boundary_adjudications"].items()
        }
        target = tmp_path / record["proposal_reference"]["proposal_file"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"proposed_timestamps": candidates}), encoding="utf-8")
        (proposals / target.name).write_bytes(target.read_bytes())
        record["proposal_reference"]["proposal_sha256"] = hashlib.sha256(
            target.read_bytes()
        ).hexdigest()
    reviews = _write_reviews(tmp_path, records)

    code = main(
        _argv(tmp_path, reviews, inventory, proposals_dir=proposals, repository_root=tmp_path)
    )
    report = json.loads(capsys.readouterr().out)
    assert code == EXIT_READY, report["blockers"]
    assert report["ready"] is True
    assert report["researcher_approval_still_required"] is True
    assert report["ground_truth_approval_authority"] == "human_researcher_only"


def test_missing_inventory_is_an_actionable_error(tmp_path: Path, capsys):
    reviews = _write_reviews(tmp_path, [])
    code = main(_argv(tmp_path, reviews, tmp_path / "absent.json"))
    assert code == EXIT_ERROR
    assert "annotation inventory not found" in capsys.readouterr().err


def test_report_may_not_be_written_inside_the_reviews_tree(tmp_path: Path, capsys):
    records, _a, _r, paths = _three_records(tmp_path)
    reviews = _write_reviews(tmp_path, records)
    inventory = _write_inventory(tmp_path, records, paths)

    code = main(
        _argv(tmp_path, reviews, inventory, report_path=reviews / "sub" / "report.json")
    )
    assert code == EXIT_ERROR
    assert "refusing to write" in capsys.readouterr().err
    assert not (reviews / "sub").exists()


def test_cli_does_not_modify_the_reviews_it_reads(tmp_path: Path, capsys):
    records, _a, _r, paths = _three_records(tmp_path)
    reviews = _write_reviews(tmp_path, records)
    inventory = _write_inventory(tmp_path, records, paths)
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(reviews.glob("*.json"))
    }

    main(_argv(tmp_path, reviews, inventory, report_path=tmp_path / "out" / "report.json"))
    capsys.readouterr()

    after = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(reviews.glob("*.json"))
    }
    assert before == after


def test_repeated_runs_produce_an_identical_report(tmp_path: Path, capsys):
    """The report is idempotent, so re-running is safe and diffable."""
    records, _a, _r, paths = _three_records(tmp_path)
    reviews = _write_reviews(tmp_path, records)
    inventory = _write_inventory(tmp_path, records, paths)
    target = tmp_path / "out" / "report.json"

    argv = _argv(tmp_path, reviews, inventory, report_path=target)
    first_code = main(argv)
    capsys.readouterr()
    first = target.read_text(encoding="utf-8")
    second_code = main(argv)
    capsys.readouterr()
    second = target.read_text(encoding="utf-8")

    assert first_code == second_code
    assert first == second


def test_markdown_report_is_deterministic_and_contains_every_blocker(tmp_path: Path, capsys):
    """JSON and Markdown are two views of the same fail-closed verdict."""
    legacy = {
        "schema_version": "6.0.0",
        "event_id": "event_001",
        "cohort": "train_events",
        "adjudication_status": "APPROVED",
    }
    reviews = _write_reviews(tmp_path, [legacy])
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps({}), encoding="utf-8")
    code = main(
        _argv(
            tmp_path,
            reviews,
            inventory,
            report_path=tmp_path / "out" / "report.json",
            markdown_path=tmp_path / "out" / "report.md",
        )
    )
    assert code == EXIT_NOT_READY
    capsys.readouterr()
    report = json.loads((tmp_path / "out" / "report.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "out" / "report.md").read_text(encoding="utf-8")
    assert report["stage"] == "phase12_single_camera_baseline"
    assert "`LEGACY_OR_UNKNOWN_SCHEMA`" in markdown
    assert "event_001" in markdown
    assert report["blocker_count"] == 4
    assert all(f"`{code}`" in markdown for code in report["blocker_codes"])
    assert markdown == render_markdown_report(report)
    assert markdown == render_markdown_report(report)


def test_markdown_report_may_not_be_written_inside_protected_inputs(tmp_path: Path, capsys):
    records, _a, _r, paths = _three_records(tmp_path)
    reviews = _write_reviews(tmp_path, records)
    inventory = _write_inventory(tmp_path, records, paths)
    code = main(
        _argv(tmp_path, reviews, inventory, markdown_path=reviews / "sub" / "report.md")
    )
    assert code == EXIT_ERROR
    assert "refusing to write" in capsys.readouterr().err
    assert not (reviews / "sub").exists()


def test_load_media_context_rejects_a_truncated_digest(tmp_path: Path):
    inventory = tmp_path / "inventory.json"
    inventory.write_text(
        json.dumps(
            {
                "train_events/event_001": {
                    "event_id": "event_001",
                    "front": {"path": "a.mov", "sha256": "abc"},
                    "back": {"path": "b.mov", "sha256": "d" * 64},
                }
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ReadinessCliError, match="sha256 is not a digest"):
        load_media_context(inventory)


def test_active_proposal_resolution_prefers_the_highest_version(tmp_path: Path):
    proposals = tmp_path / "proposals"
    proposals.mkdir()
    (proposals / "event_001_proposal_v1.json").write_bytes(b"v1")
    newest = proposals / "event_001_proposal_v2.json"
    newest.write_bytes(b"v2")

    resolved = load_active_proposals(proposals)
    assert resolved == {"event_001": hashlib.sha256(b"v2").hexdigest()}


def test_absent_proposals_directory_yields_no_active_proposals(tmp_path: Path):
    assert load_active_proposals(tmp_path / "nope") == {}
