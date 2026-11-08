"""``event_001`` exists in three cohorts of the real corpus.

Every per-event mapping in the readiness/promotion path used the bare event id, so a
genuine, fully valid corpus shaped like the real one would have been refused
(duplicate approved record; media/proposal entries overwritten by the last cohort).
These tests build that shape from synthetic records only.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from railway_detection.annotation.evaluation_readiness_gate import evaluate_readiness
from railway_detection.annotation.readiness_cli import (
    load_active_proposals,
    load_media_context,
)
from second_review_support import SECOND_REVIEWER, independent_second_review
from test_phase11_9_synthetic_pilot import (
    PILOT_REVIEWER,
    VALID_PROPOSAL_SHA,
    _build_pilot_record,
)

COHORTS = ("train_events", "no_train_events", "engine_events")


_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")


def _shift_times(value, seconds: float):
    """Shift every UTC timestamp in a record uniformly (keeps all orderings valid)."""
    if isinstance(value, dict):
        return {k: _shift_times(v, seconds) for k, v in value.items()}
    if isinstance(value, list):
        return [_shift_times(v, seconds) for v in value]
    if isinstance(value, str) and _ISO.match(value):
        moved = datetime.fromisoformat(value.replace("Z", "+00:00")) + timedelta(seconds=seconds)
        return moved.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return value


def _corpus(tmp_path: Path):
    records, registry, paths, active = [], {}, {}, {}
    for index, cohort in enumerate(COHORTS):
        media_root = tmp_path / cohort
        media_root.mkdir()
        event = {"event_id": "event_001", "cohort": cohort, "complexity": "simple"}
        # One reviewer cannot hold three simultaneous sessions: stagger them.
        record = _shift_times(_build_pilot_record(media_root, event), index * 3600.0)
        # distinct per-cohort proposals so a bare-id key collision is detectable
        sha = hashlib.sha256(f"proposal-{cohort}".encode()).hexdigest()
        record["proposal_reference"]["proposal_sha256"] = sha
        records.append(record)
        if cohort == "engine_events":
            records.append(independent_second_review(record))  # RD-043 engine T3/T4 trigger
        key = f"{cohort}/event_001"
        active[key] = sha
        registry[key] = {
            "front": record["reviewer_observed_media_hashes"]["front_sha256"],
            "back": record["reviewer_observed_media_hashes"]["back_sha256"],
        }
        paths[key] = {
            "front": str(media_root / "event_001_front.mov"),
            "back": str(media_root / "event_001_back.mov"),
        }
    return records, active, registry, paths


def _allowlist(tmp_path: Path) -> Path:
    path = tmp_path / "allow.json"
    path.write_text(json.dumps({"authorized_reviewers": [PILOT_REVIEWER, SECOND_REVIEWER]}), encoding="utf-8")
    return path


def _gate(tmp_path, records, active, registry, paths):
    return evaluate_readiness(
        records=records,
        active_proposal_sha256_by_event=active,
        media_sha256_registry=registry,
        allowlist_path=_allowlist(tmp_path),
        media_file_paths=paths,
    )


def test_same_event_id_in_every_cohort_is_ready_not_duplicate(tmp_path: Path):
    records, active, registry, paths = _corpus(tmp_path)
    verdict = _gate(tmp_path, records, active, registry, paths)
    assert verdict.ready, verdict.blockers


def test_a_true_duplicate_within_one_cohort_is_still_refused(tmp_path: Path):
    records, active, registry, paths = _corpus(tmp_path)
    twin = dict(records[0])
    twin["review_id"] = "twin"
    verdict = _gate(tmp_path, [*records, twin], active, registry, paths)
    assert not verdict.ready
    assert any("DUPLICATE_APPROVED_RECORD:event_001: cohort=train_events" in b
               for b in verdict.blockers)


def test_qualified_lookup_does_not_confuse_cohorts(tmp_path: Path):
    records, active, registry, paths = _corpus(tmp_path)
    # Swap the train cohort's proposal hash: only the train record may be stale.
    active["train_events/event_001"] = "0" * 64
    verdict = _gate(tmp_path, records, active, registry, paths)
    stale = [b for b in verdict.blockers if "STALE_PROPOSAL_REFERENCE" in b]
    assert len(stale) == 1


def test_inventory_loader_keeps_all_cohorts_apart(tmp_path: Path):
    inventory = {}
    for cohort in COHORTS:
        inventory[f"{cohort}/event_001"] = {
            "category": cohort,
            "event_id": "event_001",
            "front": {
                "path": f"{cohort}/f.mov",
                "sha256": hashlib.sha256(cohort.encode()).hexdigest(),
            },
            "back": {
                "path": f"{cohort}/b.mov",
                "sha256": hashlib.sha256(b"b" + cohort.encode()).hexdigest(),
            },
        }
    path = tmp_path / "inv.json"
    path.write_text(json.dumps(inventory), encoding="utf-8")
    registry, paths = load_media_context(path)
    assert sorted(registry) == sorted(f"{c}/event_001" for c in COHORTS)
    assert len({entry["front"] for entry in registry.values()}) == 3
    assert paths["no_train_events/event_001"]["back"] == "no_train_events/b.mov"


def test_proposal_loader_qualifies_by_cohort_directory(tmp_path: Path):
    for cohort in COHORTS:
        folder = tmp_path / "proposals" / cohort
        folder.mkdir(parents=True)
        (folder / "event_001_proposal_v2.json").write_text(cohort)
    (tmp_path / "proposals" / "train_events" / "event_001_proposal_v3.json").write_text("newer")
    active = load_active_proposals(tmp_path / "proposals")
    assert sorted(active) == sorted(f"{c}/event_001" for c in COHORTS)
    assert active["train_events/event_001"] == hashlib.sha256(b"newer").hexdigest()
    assert active["engine_events/event_001"] == hashlib.sha256(b"engine_events").hexdigest()


def test_valid_proposal_constant_is_not_a_cohort_collision_artifact():
    assert VALID_PROPOSAL_SHA == "d" * 64
