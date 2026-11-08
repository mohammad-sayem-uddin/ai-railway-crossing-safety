"""Command-line interface for the AI-Assisted Railway Annotation Workflow.

Provides pilot single-event processing and gated batch operations.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from railway_detection.annotation.gemini_annotator import GeminiAnnotator
from railway_detection.annotation.review_reporter import ReviewReporter
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("annotation.cli")

EVENT_TYPE_MAPPING = {
    "train_events": "REAL_WORLD_TRAIN_EVENT",
    "no_train_events": "REAL_WORLD_NO_TRAIN",
    "engine_events": "REAL_WORLD_ENGINE_ONLY",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="railway_annotation",
        description="AI-Assisted Ground-Truth Annotation Tool (Protocol v5.0.0)",
    )
    parser.add_argument(
        "--event-id",
        default="event_001",
        help="Event identifier to process (e.g. event_001). Default: event_001",
    )
    parser.add_argument(
        "--event-type",
        choices=("train_events", "no_train_events", "engine_events"),
        default="train_events",
        help="Event type category folder. Default: train_events",
    )
    parser.add_argument(
        "--raw-root",
        default="data/raw/layer_b/v2",
        help="Path to Layer B raw data root. Default: data/raw/layer_b/v2",
    )
    parser.add_argument(
        "--proposal-root",
        default="data/ground_truth/proposals",
        help="Output directory for immutable candidate proposals. Default: data/ground_truth/proposals",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Run batch proposal generation across events. (Requires explicit flag).",
    )
    parser.add_argument(
        "--force-version",
        type=int,
        default=None,
        help="Explicit proposal version number to generate when updating an existing proposal.",
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check Gemini API environment configuration and exit.",
    )
    return parser


def process_single_event(
    annotator: GeminiAnnotator,
    event_id: str,
    event_type_dir: str,
    raw_root: Path,
    force_version: int | None = None,
) -> tuple[Path, Path]:
    event_dir = raw_root / event_type_dir / event_id
    if not event_dir.exists():
        raise FileNotFoundError(f"Event directory not found: {event_dir}")

    protocol_event_type = EVENT_TYPE_MAPPING[event_type_dir]
    logger.info("Generating candidate proposal for %s (%s)...", event_id, protocol_event_type)

    proposal = annotator.generate_candidate_proposal(
        event_dir=event_dir,
        event_type=protocol_event_type,
    )

    saved_proposal_file = annotator.save_proposal(
        proposal=proposal,
        event_type_dir=event_type_dir,
        force_version=force_version,
    )

    # Generate review sheet alongside proposal
    review_sheet_file = saved_proposal_file.parent / f"{event_id}_review_sheet.md"
    ReviewReporter.save_review_report(
        proposal=proposal,
        output_file=review_sheet_file,
        event_raw_dir=event_dir,
    )
    logger.info("Generated review sheet at %s", review_sheet_file)

    return saved_proposal_file, review_sheet_file


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    raw_root = Path(args.raw_root)
    annotator = GeminiAnnotator(base_proposal_dir=args.proposal_root)

    if args.check_env:
        status = annotator.check_gemini_api_status()
        print("Gemini Environment Status:")
        for k, v in status.items():
            print(f"  {k}: {v}")
        return 0

    if not args.batch:
        try:
            prop_file, review_file = process_single_event(
                annotator=annotator,
                event_id=args.event_id,
                event_type_dir=args.event_type,
                raw_root=raw_root,
                force_version=args.force_version,
            )
            print(f"Pilot proposal created: {prop_file}")
            print(f"Review sheet created:  {review_file}")
            return 0
        except Exception as exc:
            logger.exception("Failed to process event %s: %s", args.event_id, exc)
            return 1
    else:
        logger.info("Batch mode initiated for category: %s", args.event_type)
        cat_dir = raw_root / args.event_type
        if not cat_dir.exists():
            logger.error("Category directory does not exist: %s", cat_dir)
            return 1

        events = sorted([d.name for d in cat_dir.iterdir() if d.is_dir() and not d.name.startswith(".")])
        logger.info("Found %d events in %s", len(events), args.event_type)

        success = 0
        failed = 0
        for ev in events:
            try:
                process_single_event(
                    annotator=annotator,
                    event_id=ev,
                    event_type_dir=args.event_type,
                    raw_root=raw_root,
                    force_version=args.force_version,
                )
                success += 1
            except Exception as exc:
                logger.error("Failed event %s: %s", ev, exc)
                failed += 1

        print(f"Batch processing completed: {success} succeeded, {failed} failed.")
        return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
