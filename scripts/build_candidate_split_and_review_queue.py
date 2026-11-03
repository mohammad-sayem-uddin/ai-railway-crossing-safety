#!/usr/bin/env python3
"""Build candidate-only event split and Stage-2.1 review queue reports.

The command is read-only on proposals, reviews, notices, manifests, and raw
media.  It writes only the two caller-selected reports (defaults under
``docs/generated``), and neither report grants approval or changes a record.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from railway_detection.annotation.candidate_split_queue import (  # noqa: E402
    build_candidate_event_split,
    build_stage21_review_queue,
    write_candidate_event_split,
    write_stage21_review_queue,
    write_stage21_review_queue_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("data/manifests/layer_b_v2_annotation_inventory.json"),
    )
    parser.add_argument("--proposals-dir", type=Path, default=Path("data/ground_truth/proposals"))
    parser.add_argument("--reviews-dir", type=Path, default=Path("data/ground_truth/reviews"))
    parser.add_argument(
        "--split-output",
        type=Path,
        default=Path("docs/generated/CANDIDATE_EVENT_SPLIT_PROPOSAL.json"),
    )
    parser.add_argument(
        "--queue-output",
        type=Path,
        default=Path("docs/generated/STAGE21_REVIEW_QUEUE.json"),
    )
    parser.add_argument("--queue-markdown-output", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    inventory_path = args.inventory if args.inventory.is_absolute() else root / args.inventory
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    proposals_dir = args.proposals_dir
    if not proposals_dir.is_absolute():
        proposals_dir = root / proposals_dir
    split = build_candidate_event_split(
        inventory,
        proposals_dir=proposals_dir,
        root=root,
        inventory_path=inventory_path,
    )
    queue = build_stage21_review_queue(
        root,
        inventory_path=inventory_path,
        proposals_dir=proposals_dir,
        reviews_dir=args.reviews_dir,
    )
    split_output = args.split_output
    if not split_output.is_absolute():
        split_output = root / split_output
    queue_output = args.queue_output
    if not queue_output.is_absolute():
        queue_output = root / queue_output
    write_candidate_event_split(split_output, split, root=root)
    write_stage21_review_queue(queue_output, queue, root=root)
    if args.queue_markdown_output is not None:
        queue_markdown = args.queue_markdown_output
        if not queue_markdown.is_absolute():
            queue_markdown = root / queue_markdown
        write_stage21_review_queue_markdown(queue_markdown, queue, root=root)
    print(
        json.dumps(
            {
                "split": split["proposal_id"],
                "queue_sha256": queue["queue_sha256"],
                "queue_summary": queue["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
