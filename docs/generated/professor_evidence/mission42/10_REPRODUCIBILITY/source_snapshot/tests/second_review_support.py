# ruff: noqa: E501
"""Synthetic helpers for RD-043 second-review fixtures (Mission 10).

Pure dictionary manipulation: no media is opened and nothing is written.
"""

from __future__ import annotations

import copy
from datetime import UTC, datetime, timedelta
from typing import Any

SECOND_REVIEWER = "second.reviewer@synthetic.example.com"


def _shift(stamp: str, seconds: float) -> str:
    moved = datetime.fromisoformat(stamp.replace("Z", "+00:00")) + timedelta(seconds=seconds)
    return moved.astimezone(UTC).isoformat().replace("+00:00", "Z")


def independent_second_review(
    primary: dict[str, Any],
    *,
    reviewer: str = SECOND_REVIEWER,
    shift_s: float = 7 * 86400.0,
    review_id: str | None = None,
) -> dict[str, Any]:
    """An APPROVED, agreeing, independently attributed review of ``primary``."""
    second = copy.deepcopy(primary)
    second["review_id"] = review_id or f"{primary['review_id']}__second"
    second["second_review_of"] = primary["review_id"]
    meta = second["reviewer_metadata"]
    meta["reviewer_id"] = reviewer
    meta["review_session_id"] = f"{meta['review_session_id']}-second"
    meta["review_start_utc"] = _shift(meta["review_start_utc"], shift_s)
    meta["review_end_utc"] = _shift(meta["review_end_utc"], shift_s)
    meta.pop("review_duration_s", None)
    second["model_independence_attestation"]["attested_at_utc"] = _shift(
        second["model_independence_attestation"]["attested_at_utc"], shift_s
    )
    second["reviewer_observed_media_hashes"]["observed_at_utc"] = _shift(
        second["reviewer_observed_media_hashes"]["observed_at_utc"], shift_s
    )
    for entry in second["adjudication_history"]:
        entry["by"] = reviewer
        entry["at_utc"] = _shift(entry["at_utc"], shift_s)
    return second


def write_verifiable_proposal(path, record: dict[str, Any]) -> str:
    """Write a proposal whose candidates equal ``record`` (nothing corrected); return its SHA-256."""
    import hashlib
    import json
    from pathlib import Path

    candidates = {
        name: {"candidate_observable": e["state"] == "OBSERVABLE", "value_s": e["value_s"]}
        for name, e in record["boundary_adjudications"].items()
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"proposed_timestamps": candidates}), encoding="utf-8")
    return hashlib.sha256(target.read_bytes()).hexdigest()
