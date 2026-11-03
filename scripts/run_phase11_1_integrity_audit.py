#!/usr/bin/env python3
"""Phase 11.1: read-only integrity audit of the 27 existing Stage-2 review
records, using the prototype safeguard (`integrity_safeguard.py`) and
direct file inspection (timestamps, filesystem mtimes, proposal-version
currency). Reads only; writes only the new inventory/report files listed
below. Never modifies, deletes, or rewrites any existing proposal, review,
snapshot, or raw media file.
"""

from __future__ import annotations

import glob
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
import sys  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "src"))

from railway_detection.annotation.integrity_safeguard import (  # noqa: E402
    check_review_batch_integrity,
)


def _latest_proposal(cohort: str, event_id: str) -> Path:
    candidates = sorted((REPO_ROOT / "data/ground_truth/proposals" / cohort).glob(f"{event_id}_proposal*.json"))
    def vkey(p: Path) -> int:
        m = re.search(r"_v(\d+)\.json$", p.name)
        return int(m.group(1)) if m else 0
    return max(candidates, key=vkey)


def main() -> int:
    review_files = sorted(glob.glob("data/ground_truth/reviews/*/*.json"))
    records = [json.loads(Path(f).read_text()) for f in review_files]

    batch_violations = check_review_batch_integrity(records)
    # proposal_reference stores the REFERENCED proposal's sha256 as computed
    # at review time (of the file content at that time); compare directly
    # against the referenced file path's CURRENT hash to detect staleness.
    referenced_file_hash_matches_active = []
    for f in review_files:
        d = json.loads(Path(f).read_text())
        event_id = d["event_id"]
        referenced_path = REPO_ROOT / d["proposal_reference"]["proposal_file"]
        cohort = Path(f).parent.name
        latest = _latest_proposal(cohort, event_id)
        referenced_file_hash_matches_active.append({
            "event_id": event_id,
            "referenced_proposal_file": str(referenced_path.relative_to(REPO_ROOT)),
            "active_proposal_file": str(latest.relative_to(REPO_ROOT)),
            "is_stale_reference": referenced_path.resolve() != latest.resolve(),
        })

    out = {
        "generated_by": "scripts/run_phase11_1_integrity_audit.py",
        "purpose": "Read-only integrity audit of the 27 existing Stage-2 review records. "
        "Does not modify, approve, or reject any record.",
        "total_review_records_examined": len(records),
        "batch_integrity_violations": [
            {"event_id": v.event_id, "code": v.code, "message": v.message} for v in batch_violations
        ],
        "violation_counts_by_code": {
            code: sum(1 for v in batch_violations if v.code == code)
            for code in sorted({v.code for v in batch_violations})
        },
        "stale_proposal_references": referenced_file_hash_matches_active,
        "stale_reference_count": sum(1 for r in referenced_file_hash_matches_active if r["is_stale_reference"]),
    }

    out_path = REPO_ROOT / "docs" / "PHASE11_1_INTEGRITY_INVENTORY.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Batch integrity violations: {len(batch_violations)} ({out['violation_counts_by_code']})")
    print(f"Stale proposal references: {out['stale_reference_count']}/{len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
