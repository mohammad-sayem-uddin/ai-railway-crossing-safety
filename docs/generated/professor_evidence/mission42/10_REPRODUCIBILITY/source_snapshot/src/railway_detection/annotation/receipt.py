"""Content-addressed Stage-2.1 promotion receipt: shared by the CLI and the gate.

The receipt is what lets the Phase 12 execution gate -- which must never open
media -- rely on the media-hashing readiness gate's READY verdict. It is bound to
*every metadata input that influenced that verdict*, so changing any of them after
the fact (a record, the reviewer allowlist, the annotation inventory, the active
proposals) makes the receipt stale and the gate refuses it.

Tamper-evident, not tamper-proof: anyone with write access can still write a file
that merely *looks* like a receipt for the current bytes. What the binding prevents
is silent reuse of a genuine receipt after inputs change, and a receipt that was
issued for different inputs than the ones in the repository now.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from railway_detection.safety.media_guard import require_media_authorization

PROMOTION_RECEIPT_SCHEMA = "phase12-stage21-promotion-receipt/2"
PROMOTION_RECEIPT_PRODUCER = "railway_detection.annotation.readiness_cli"

DEFAULT_INVENTORY_RELATIVE = Path("data/manifests/layer_b_v2_annotation_inventory.json")
DEFAULT_PROPOSALS_RELATIVE = Path("data/ground_truth/proposals")
DEFAULT_ALLOWLIST_RELATIVE = Path("data/ground_truth/authorized_reviewers.json")
DEFAULT_REVIEWS_RELATIVE = Path("data/ground_truth/reviews")


def sha256_file(path: Path) -> str:
    require_media_authorization(path, "HASH_RAW_MEDIA")  # no-op for non-media metadata files
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def mapping_digest(mapping: dict[str, str]) -> str:
    """Order-independent digest of a ``name -> sha256`` mapping."""
    body = json.dumps(sorted(mapping.items()), separators=(",", ":")).encode()
    return hashlib.sha256(b"receipt-mapping/1;" + body).hexdigest()


def receipt_body_sha256(receipt: dict[str, Any]) -> str:
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def review_record_hashes(reviews_dir: Path) -> dict[str, str]:
    """Digest of every *active* review record (legacy records with a verified invalidation
    notice are history, not input, and are excluded)."""
    from railway_detection.annotation.notices import excused_legacy_records

    excused = excused_legacy_records(reviews_dir)
    return {
        path.relative_to(reviews_dir).as_posix(): sha256_file(path)
        for path in sorted(reviews_dir.rglob("*_review.json"))
        if path.relative_to(reviews_dir).as_posix() not in excused
    }


def active_proposal_hashes(proposals_dir: Path) -> dict[str, str]:
    """Hash the highest-version ``*_proposal_v{N}.json`` per event (metadata only)."""
    if not proposals_dir.is_dir():
        return {}
    active: dict[str, tuple[int, Path]] = {}
    for path in sorted(proposals_dir.rglob("*_proposal_v*.json")):
        event_id, _, version = path.stem.partition("_proposal_v")
        if not event_id or not version.isdigit():
            continue
        key = f"{path.parent.name}/{event_id}"
        if key not in active or int(version) > active[key][0]:
            active[key] = (int(version), path)
    return {key: sha256_file(path) for key, (_, path) in sorted(active.items())}


def live_receipt_inputs(
    *, inventory: Path, proposals_dir: Path, allowlist: Path
) -> dict[str, str | None]:
    """Digests of the non-record inputs the readiness verdict depended on."""
    return {
        "inventory_sha256": sha256_file(inventory) if inventory.is_file() else None,
        "active_proposals_sha256": mapping_digest(active_proposal_hashes(proposals_dir)),
        "allowlist_sha256": sha256_file(allowlist) if allowlist.is_file() else None,
    }
