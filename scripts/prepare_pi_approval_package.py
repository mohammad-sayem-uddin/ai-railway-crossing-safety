#!/usr/bin/env python3
"""Prepare schema-validated, unsigned PI human-approval templates & checklists.

This tool reads ONLY non-raw metadata artifacts (`STAGE21_REVIEW_QUEUE.json`,
`CANDIDATE_EVENT_SPLIT_PROPOSAL.json`, `layer_b_v2_annotation_inventory.json`,
`authorized_reviewers.json`, `phase12_r04_scope_decision.json`,
`phase12_protocol_decision.json`, and `docs/FINAL_GROUND_TRUTH_PROTOCOL.md`) and
writes human-review preparation packages strictly under
``docs/generated/approval_packages/``.

It NEVER reads or opens ``data/raw/``, NEVER invents human signatures or
timestamps, and NEVER creates or mutates active governance artifacts under
``data/governance/``, ``data/splits/``, ``data/manifests/``, or
``data/ground_truth/reviews/``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from railway_detection.annotation.stage2_1_schema import (
    MIN_PLAUSIBLE_REVIEW_DURATION_S,
    STAGE_2_1_SCHEMA_VERSION,
)
from railway_detection.evaluation import governance
from railway_detection.evaluation.execution_gate import assess_official_phase12_readiness
from railway_detection.safety import media_guard

HUMAN_PLACEHOLDER = "__HUMAN_APPROVAL_REQUIRED__"
PROTOCOL_DOC_REL = "docs/FINAL_GROUND_TRUTH_PROTOCOL.md"


def _sha256_file(path: Path) -> str:
    media_guard.require_media_authorization(path, "HASH_RAW_MEDIA")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _build_auth_media_access_template(
    repo_root: Path,
    event_keys: list[str],
    reviewers: list[str],
) -> dict[str, Any]:
    """Build exact-key ``phase5-media-access-authorization/2`` template."""
    protocol_path = repo_root / PROTOCOL_DOC_REL
    protocol_sha = _sha256_file(protocol_path)
    return {
        "schema_version": media_guard.MEDIA_ACCESS_SCHEMA_VERSION,
        "authorization_id": f"{HUMAN_PLACEHOLDER}_e.g._AUTH-MEDIA-ACCESS-2026-11-XX",
        "authorization_class": media_guard.AUTHORIZATION_CLASS,
        "status": f"{HUMAN_PLACEHOLDER}_SET_APPROVED_WHEN_SIGNED",
        "authorized_by": f"{HUMAN_PLACEHOLDER}_CHOOSE_FROM_{'|'.join(reviewers)}",
        "authorized_at_utc": f"{HUMAN_PLACEHOLDER}_ISO8601_UTC_WITH_TZ",
        "expires_at_utc": f"{HUMAN_PLACEHOLDER}_ISO8601_UTC_WITH_TZ_AFTER_ISSUED",
        "revoked": False,
        "authorization_statement": (
            f"{HUMAN_PLACEHOLDER}_EXPLICIT_RESEARCHER_STATEMENT_AUTHORIZING_LAYER_B_MEDIA_INSPECTION"
        ),
        "attestation": {
            "type": media_guard.ATTESTATION_RECORDED_STATEMENT,
            "signature": None,
        },
        "recorded_by": {
            "kind": "researcher",
            "identity": f"{HUMAN_PLACEHOLDER}_REVIEWER_EMAIL",
        },
        "scope": {
            "operations": sorted(media_guard.VALID_MEDIA_OPERATIONS),
            "datasets": ["layer_b"],
            "events": list(event_keys),
            "media_types": ["video", "audio"],
            "purpose": (
                "Authorized Stage-2.1 human ground-truth inspection across all 27 Layer-B events "
                "and subsequent official Phase-12 replay evidence production."
            ),
        },
        "restrictions": {"path_prefixes": ["data/raw/layer_b/"]},
        "bindings": {
            "protocol_document": {
                "path": PROTOCOL_DOC_REL,
                "sha256": protocol_sha,
            }
        },
        "record_sha256": f"{HUMAN_PLACEHOLDER}_COMPUTE_WITH_media_guard._canonical_sha256",
    }


def _build_stage21_checklist(
    repo_root: Path,
    queue: dict[str, Any],
    inventory: dict[str, Any],
    reviewers: list[str],
) -> tuple[dict[str, Any], str]:
    """Build machine-readable and Markdown Stage-2.1 checklists for all 27 events."""
    primary_reviewer = "raihankabirrahu@gmail.com" if "raihankabirrahu@gmail.com" in reviewers else reviewers[0]
    secondary_reviewer = (
        "elaf85777@gmail.com"
        if "elaf85777@gmail.com" in reviewers and primary_reviewer != "elaf85777@gmail.com"
        else reviewers[-1]
    )

    events_out: list[dict[str, Any]] = []
    for item in queue["items"]:
        key = item["event_key"]
        cohort = item["cohort"]
        event_id = item["event_id"]
        prop = item["active_candidate_proposal"]
        prop_path = repo_root / prop["path"]
        prop_sha_live = _sha256_file(prop_path)
        if prop_sha_live != prop["sha256"]:
            raise ValueError(f"Proposal hash drift detected for {key}")

        inv_entry = inventory[key]
        front_inv = inv_entry["front"]
        back_inv = inv_entry["back"]
        if (
            front_inv["sha256"] != item["inventory_media_sha256"]["front"]
            or back_inv["sha256"] != item["inventory_media_sha256"]["back"]
        ):
            raise ValueError(f"Inventory media hash mismatch vs review queue for {key}")

        primary_cmd = (
            f"PYTHONPATH=src .venv/bin/python scripts/run_stage21_review.py "
            f"--reviewer {primary_reviewer} --cohort {cohort} --event {event_id}"
        )
        second_review_cmd = (
            f"PYTHONPATH=src .venv/bin/python scripts/run_stage21_review.py "
            f"--reviewer {secondary_reviewer} --cohort {cohort} --event {event_id} "
            f"--second-of <PRIMARY_REVIEW_ID>"
        )
        events_out.append(
            {
                "event_key": key,
                "cohort": cohort,
                "event_id": event_id,
                "queue_category": item["queue_category"],
                "reason_codes": list(item.get("reason_codes", [])),
                "stage21_review_status": item.get("stage21_review_status", "NEW_STAGE21_RECORD_REQUIRED"),
                "required_schema_version": STAGE_2_1_SCHEMA_VERSION,
                "min_plausible_review_duration_s": MIN_PLAUSIBLE_REVIEW_DURATION_S,
                "active_proposal": prop,
                "expected_media": {
                    "front_path": front_inv["path"],
                    "front_sha256": front_inv["sha256"],
                    "back_path": back_inv["path"],
                    "back_sha256": back_inv["sha256"],
                },
                "rd043_second_review_note": (
                    "MANDATORY if T3 or T4 marked non-UNOBSERVABLE on engine_events; also triggers on any "
                    "UNCERTAIN boundary, explicit NEEDS_SECOND_REVIEW flag, or hash/proposal trigger."
                    if cohort == "engine_events"
                    else "Triggered if any boundary UNCERTAIN, explicit review flag, or hash/proposal trigger fires."
                ),
                "primary_review_command": primary_cmd,
                "second_review_command_template": second_review_cmd,
            }
        )

    payload = {
        "schema_version": "stage21-27-event-preparation-checklist/1",
        "generated_without_raw_media_access": True,
        "total_events": len(events_out),
        "authorized_reviewers": reviewers,
        "stage21_schema_version": STAGE_2_1_SCHEMA_VERSION,
        "min_plausible_review_duration_s": MIN_PLAUSIBLE_REVIEW_DURATION_S,
        "prerequisite": "data/governance/AUTH-MEDIA-ACCESS.json must be genuinely approved and signed before inspecting raw video/audio.",
        "events": events_out,
    }

    lines = [
        "# Stage-2.1 Ground-Truth Human Review Preparation Checklist (27 Events)",
        "",
        f"- **Required Schema:** `{STAGE_2_1_SCHEMA_VERSION}` (`MIN_PLAUSIBLE_REVIEW_DURATION_S = {MIN_PLAUSIBLE_REVIEW_DURATION_S:.1f}s`)",
        f"- **Authorized Reviewers:** `{', '.join(reviewers)}`",
        "- **Prerequisite:** Genuine `data/governance/AUTH-MEDIA-ACCESS.json` (`phase5-media-access-authorization/2`) MUST exist before running review sessions on raw media.",
        "- **Legacy Status:** All `27/27` existing `6.0.0` reviews are invalidated and quarantined cleanly (`0` valid Stage-2.1 records on disk).",
        "",
        "| # | Event Key | Active Proposal (SHA-256 prefix) | Expected Front SHA-256 prefix | Expected Back SHA-256 prefix | Review CLI Command |",
        "|---|---|---|---|---|---|",
    ]
    for idx, ev in enumerate(events_out, start=1):
        p = ev["active_proposal"]
        m = ev["expected_media"]
        lines.append(
            f"| {idx} | `{ev['event_key']}` | `{Path(p['path']).name}` (`{p['sha256'][:12]}...`) | "
            f"`{m['front_sha256'][:12]}...` | `{m['back_sha256'][:12]}...` | `{ev['primary_review_command']}` |"
        )
    lines.extend(
        [
            "",
            "## RD-043 Dual-Review Reminders",
            "- `engine_events/event_001` triggers mandatory second review (`elaf85777@gmail.com`) whenever `T3` or `T4` is marked in an interpreted state (`OBSERVABLE`, etc.), and ALL `27` events trigger dual review on `UNCERTAIN` boundaries, explicit flags, or `<= 30s` / batch-burst integrity flags (`check_review_batch_integrity`).",
            "- Every reviewer session MUST inspect actual `camera_front.mov` / `camera_back.mov` independently of model predictions and compute genuine live `reviewer_observed_media_hashes` during the session.",
            "",
        ]
    )
    return payload, "\n".join(lines)


def _build_cohort_approval_packages(
    queue: dict[str, Any],
    readiness_blockers: list[dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    """Prepare the three cohort approval packages required by execution_gate."""
    by_cohort: dict[str, list[str]] = {"train_events": [], "no_train_events": [], "engine_events": []}
    for item in queue["items"]:
        by_cohort[item["cohort"]].append(item["event_key"])

    receipt_cmd = (
        "PYTHONPATH=src .venv/bin/python -m railway_detection.annotation.readiness_cli "
        "--reviews-dir data/ground_truth/reviews "
        "--allowlist data/ground_truth/authorized_reviewers.json "
        "--inventory data/manifests/layer_b_v2_annotation_inventory.json "
        "--proposals-dir data/ground_truth/proposals "
        "--stage stage3_single_camera_baseline "
        "--repository-root . "
        "--receipt-path data/governance/stage21_promotion_receipt.json"
    )

    cohort_specs = {
        "train_events": {
            "cohort": "train_events",
            "total_events_in_cohort": len(by_cohort["train_events"]),
            "event_keys": by_cohort["train_events"],
            "minimum_gate_requirement": ">= 1 APPROVED primary Stage-2.1 (`8.1.0-stage2.1`) record (`execution_gate.py: COHORT_APPROVAL_MISSING`)",
            "full_programme_target": f"{len(by_cohort['train_events'])}/{len(by_cohort['train_events'])} approved + RD-043 second reviews where triggered",
            "current_approved_stage21_count": 0,
            "approval_status": "PENDING_HUMAN_STAGE21_REVIEWS",
        },
        "no_train_events": {
            "cohort": "no_train_events",
            "total_events_in_cohort": len(by_cohort["no_train_events"]),
            "event_keys": by_cohort["no_train_events"],
            "minimum_gate_requirement": ">= 1 APPROVED primary Stage-2.1 (`8.1.0-stage2.1`) record (`execution_gate.py: COHORT_APPROVAL_MISSING`)",
            "full_programme_target": f"{len(by_cohort['no_train_events'])}/{len(by_cohort['no_train_events'])} approved (note: verify acoustic road-horn vs locomotive independence cleanly)",
            "current_approved_stage21_count": 0,
            "approval_status": "PENDING_HUMAN_STAGE21_REVIEWS",
        },
        "engine_events": {
            "cohort": "engine_events",
            "total_events_in_cohort": len(by_cohort["engine_events"]),
            "event_keys": by_cohort["engine_events"],
            "minimum_gate_requirement": ">= 1 APPROVED primary Stage-2.1 (`8.1.0-stage2.1`) record (`execution_gate.py: COHORT_APPROVAL_MISSING`)",
            "full_programme_target": "1/1 approved + RD-043 second review by second allowlisted reviewer if T3/T4 interpreted",
            "current_approved_stage21_count": 0,
            "approval_status": "PENDING_HUMAN_STAGE21_REVIEWS",
        },
    }

    payload = {
        "schema_version": "phase12-cohort-approval-packages/1",
        "live_cohort_blockers_detected": [
            b for b in readiness_blockers if b["code"] in {"COHORT_APPROVAL_MISSING", "STAGE21_RECORDS_MISSING"}
        ],
        "cohorts": cohort_specs,
        "post_review_promotion_receipt_schema": governance.PROMOTION_RECEIPT_SCHEMA,
        "post_review_promotion_receipt_path": str(governance.PROMOTION_RECEIPT_RELATIVE),
        "post_review_promotion_receipt_command": receipt_cmd,
    }

    lines = [
        "# Three Cohort Approval Packages (`train_events`, `no_train_events`, `engine_events`)",
        "",
        "In `execution_gate.py`, **COHORT_APPROVAL_MISSING** clears for each of the three required cohorts once verified, batch-integrity-checked, and RD-043-satisfied `APPROVED` Stage-2.1 (`8.1.0-stage2.1`) review records exist on disk and a signed promotion receipt (`phase12-stage21-promotion-receipt/2`) is emitted by `readiness_cli`.",
        "",
        "| Cohort | Events in Cohort | Current Approved Stage-2.1 | Execution Gate Floor | Full Target | Status |",
        "|---|---|---|---|---|---|",
    ]
    for cname in ("train_events", "no_train_events", "engine_events"):
        c = cohort_specs[cname]
        lines.append(
            f"| `{cname}` | {c['total_events_in_cohort']} | {c['current_approved_stage21_count']} | >= 1 APPROVED | "
            f"{c['full_programme_target']} | `{c['approval_status']}` |"
        )
    lines.extend(
        [
            "",
            "## Post-Review Promotion Receipt Command (Run Only After Human Stage-2.1 Reviews Complete)",
            "```bash",
            receipt_cmd,
            "```",
            "",
        ]
    )
    return payload, "\n".join(lines)


def _build_split_decision_package(
    repo_root: Path,
    split_proposal: dict[str, Any],
    reviewers: list[str],
) -> tuple[dict[str, Any], str]:
    """Build exact-key ``phase12-event-split-decision/1`` candidate template & reconciliation."""
    partitions = {
        "train": list(split_proposal["partitions"]["train"]),
        "val": list(split_proposal["partitions"]["val"]),
        "test": list(split_proposal["partitions"]["test"]),
    }
    governance.validate_event_level_split(partitions)

    template = {
        "schema_version": governance.SPLIT_DECISION_SCHEMA,
        "decision_status": f"{HUMAN_PLACEHOLDER}_SET_APPROVED_ONLY_IF_ELECTING_HELD_OUT_EVALUATION",
        "decision_id": f"{HUMAN_PLACEHOLDER}_e.g._PHASE12-EVENT-SPLIT-2026-11-XX",
        "decided_by": f"{HUMAN_PLACEHOLDER}_CHOOSE_FROM_{'|'.join(reviewers)}",
        "decided_at_utc": f"{HUMAN_PLACEHOLDER}_ISO8601_UTC_WITH_TZ",
        "researcher_statement": (
            f"{HUMAN_PLACEHOLDER}_EXPLICIT_PI_STATEMENT_SUPERSEDING_SPLIT-DECISION-OPTION-A-2026-11-09_IF_ELECTED"
        ),
        "attestation": {
            "type": governance.ATTESTATION_RECORDED_STATEMENT,
            "signature": None,
        },
        "recorded_by": {
            "kind": "researcher",
            "identity": f"{HUMAN_PLACEHOLDER}_REVIEWER_EMAIL",
        },
        "partitions": partitions,
        "source_proposal": {
            "path": "docs/generated/CANDIDATE_EVENT_SPLIT_PROPOSAL.json",
            "proposal_id": split_proposal["proposal_id"],
            "proposal_sha256": split_proposal["proposal_sha256"],
            "leakage_safe": split_proposal["grouping"]["leakage_safe"],
            "leakage_warning": split_proposal["grouping"]["warning"],
        },
    }

    option_a_exists = (repo_root / "docs/generated/research_decisions/SPLIT_DECISION_OPTION_A_20261109.md").is_file()
    md = "\n".join(
        [
            "# Event-Level Split Decision Preparation & Reconciliation with Option A",
            "",
            f"- **Mechanical Validator Status:** `governance.validate_event_level_split(partitions)` **PASSED** (`train={len(partitions['train'])}`, `val={len(partitions['val'])}`, `test={len(partitions['test'])}`, total=`{sum(len(v) for v in partitions.values())}` disjoint events).",
            f"- **Active Prior PI Decision (`SPLIT-DECISION-OPTION-A-2026-11-09`, file present=`{option_a_exists}`):** Explicitly chose **Option A (Descriptive single-crossing study — NO Phase 12 train/val/test split)**. Therefore `data/splits/phase12_event_split_decision.json` MUST remain absent UNLESS you explicitly elect to supersede Option A for held-out Phase 12 evaluation.",
            f"- **Disclosed Limitation (`CANDIDATE_EVENT_SPLIT_PROPOSAL.json`):** `leakage_safe = {split_proposal['grouping']['leakage_safe']}` — all 27 events share `crossing_A` (`{split_proposal['grouping']['warning']}`), and the candidate `val` partition has 0 `no_train` / `engine` events (`no_train_events/002..003` & `engine_events/001` in `train`, `no_train_events/001` in `test`). Any Phase 12 held-out claim remains single-crossing / chronological rather than cross-crossing.",
            "- **Activation Target (ONLY if Option A is superseded):** Save signed JSON to `data/splits/phase12_event_split_decision.json` (and update/remove extra metadata keys only if desired; `verify_decision_envelope` validates envelope keys cleanly).",
            "",
        ]
    )
    return template, md


def _build_eval_input_manifest_package(repo_root: Path) -> tuple[dict[str, Any], str]:
    """Build exact-schema skeleton template and runbook for phase12-evaluation-inputs/1."""
    template = {
        "schema_version": "phase12-evaluation-inputs/1",
        "evidence_classification": "real",
        "manifest_id": f"{HUMAN_PLACEHOLDER}_GENERATED_BY_manifest_builder.build_evaluation_input_manifest",
        "generated_at_utc": f"{HUMAN_PLACEHOLDER}_UTC_TIMESTAMP",
        "generated_by": "railway_detection.evaluation.manifest_builder.build_evaluation_input_manifest",
        "partitions": {
            "train": ["<approved_train_event_keys>"],
            "val": ["<approved_val_event_keys>"],
            "test": ["<approved_test_event_keys>"],
        },
        "events": [
            {
                "event_id": "<cohort/event_id>",
                "cohort": "<train_events|no_train_events|engine_events>",
                "split_role": "<train|val|test>",
                "source_path": "data/manifests/<post_auth_phase12_replay_evidence_file>.json",
                "source_sha256": "<live_sha256_of_phase12-replay-evidence/1_source>",
            }
        ],
        "camera_scope_by_event": {
            "<cohort/event_id>": "<dual_camera|single_camera|single_camera_independent>",
        },
        "accepted_sync_events": ["<11 CALIBRATION_SUPPORTED event keys from phase12_r04_scope_decision.json>"],
    }

    md = "\n".join(
        [
            "# Evaluation Input Manifest Preparation Runbook (`phase12-evaluation-inputs/1`)",
            "",
            "- **Output Destination (Post-Approval Only):** `data/manifests/phase12_evaluation_inputs.json`",
            "- **Why Not Built Pre-Approval:** `manifest_builder.build_evaluation_input_manifest(repository_root, event_sources, output_path)` requires one verified `phase12-replay-evidence/1` source JSON (under `data/manifests/` with `evidence_classification = 'real'`) per split event. No synthetic fixtures, Mission 39 exploratory caches, or pre-`AUTH-MEDIA-ACCESS` caches under `data/cache/` may be substituted (`input_contracts.py` rejects non-real/unverified sources).",
            "",
            "## Exact Post-Stage-2.1 Execution Workflow",
            "1. Complete Stage-2.1 ground-truth reviews (valid `AUTH-MEDIA-ACCESS.json` active) and generate `data/governance/stage21_promotion_receipt.json`.",
            "2. Produce real per-event `phase12-replay-evidence/1` evidence files under `data/manifests/` using `RealEventReplayProducer` / authorized raw-media feature extraction against the Stage-2.1 ground truth and validated camera calibration.",
            "3. Invoke `railway_detection.evaluation.manifest_builder.build_evaluation_input_manifest(repository_root=Path('.'), event_sources=..., output_path=Path('data/manifests/phase12_evaluation_inputs.json'))`.",
            "4. Verify live readiness status with:",
            "```bash",
            "PYTHONPATH=src .venv/bin/python -m railway_detection evaluation status",
            "```",
            "Wait until ONLY `EVAL_AUTH_NOT_GRANTED` remains before computing the final `eval_authorization.json`.",
            "",
        ]
    )
    return template, md


def _build_eval_authorization_template(
    live_bindings: dict[str, str | None],
    reviewers: list[str],
) -> dict[str, Any]:
    """Build exact-key ``phase12-eval-authorization/1`` template with static live hashes prefilled."""
    bindings_template = {
        "decision_policy_sha256": live_bindings["decision_policy_sha256"],
        "frozen_config_sha256": live_bindings["frozen_config_sha256"],
        "protocol_profile_sha256": live_bindings["protocol_profile_sha256"],
        "r04_scope_decision_sha256": live_bindings["r04_scope_decision_sha256"],
        "stage21_promotion_receipt_sha256": f"{HUMAN_PLACEHOLDER}_FROM_assess_official_phase12_readiness().live_bindings",
        "event_split_decision_sha256": f"{HUMAN_PLACEHOLDER}_FROM_assess_official_phase12_readiness().live_bindings",
        "input_manifest_sha256": f"{HUMAN_PLACEHOLDER}_FROM_assess_official_phase12_readiness().live_bindings",
    }
    return {
        "schema_version": governance.EVAL_AUTH_SCHEMA,
        "authorization_id": f"{HUMAN_PLACEHOLDER}_e.g._EVAL-AUTH-2026-11-XX",
        "stage": "stage3_single_camera_baseline",
        "authorized_by": f"{HUMAN_PLACEHOLDER}_CHOOSE_FROM_{'|'.join(reviewers)}",
        "authorized_at_utc": f"{HUMAN_PLACEHOLDER}_ISO8601_UTC_WITH_TZ",
        "authorization_statement": (
            f"{HUMAN_PLACEHOLDER}_EXPLICIT_PI_STATEMENT_AUTHORIZING_OFFICIAL_PHASE12_EVALUATION"
        ),
        "attestation": {
            "type": governance.ATTESTATION_RECORDED_STATEMENT,
            "signature": None,
        },
        "recorded_by": {
            "kind": "researcher",
            "identity": f"{HUMAN_PLACEHOLDER}_REVIEWER_EMAIL",
        },
        "scope": {
            "operation": governance.AUTHORIZED_OPERATION,
            "stage": "stage3_single_camera_baseline",
            "field_or_physical_operations_authorized": False,
        },
        "bindings": bindings_template,
        "record_sha256": f"{HUMAN_PLACEHOLDER}_COMPUTE_WITH_governance.canonical_record_sha256",
    }


def build_pi_approval_packages(repo_root: Path, output_dir: Path) -> dict[str, Any]:
    """Generate all PI human-approval preparation templates & runbooks cleanly."""
    reviewers = sorted(governance.load_authorized_reviewers(repo_root / governance.ALLOWLIST_RELATIVE))
    queue = _load_json(repo_root / "docs/generated/STAGE21_REVIEW_QUEUE.json")
    inventory = _load_json(repo_root / "data/manifests/layer_b_v2_annotation_inventory.json")
    split_proposal = _load_json(repo_root / "docs/generated/CANDIDATE_EVENT_SPLIT_PROPOSAL.json")
    readiness = assess_official_phase12_readiness(repo_root)

    event_keys = [item["event_key"] for item in queue["items"]]
    auth_media_tmpl = _build_auth_media_access_template(repo_root, event_keys, reviewers)
    checklist_json, checklist_md = _build_stage21_checklist(repo_root, queue, inventory, reviewers)
    cohort_json, cohort_md = _build_cohort_approval_packages(
        queue,
        [{"code": b.code, "detail": b.detail} for b in readiness.blockers],
    )
    split_tmpl, split_md = _build_split_decision_package(repo_root, split_proposal, reviewers)
    manifest_tmpl, manifest_md = _build_eval_input_manifest_package(repo_root)
    eval_auth_tmpl = _build_eval_authorization_template(readiness.live_bindings, reviewers)

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "AUTH_MEDIA_ACCESS.template.json", auth_media_tmpl)
    _write_json(output_dir / "STAGE21_27_EVENT_REVIEW_CHECKLIST.json", checklist_json)
    (output_dir / "STAGE21_27_EVENT_REVIEW_CHECKLIST.md").write_text(checklist_md, encoding="utf-8")
    _write_json(output_dir / "COHORT_APPROVAL_PACKAGES.json", cohort_json)
    (output_dir / "COHORT_APPROVAL_PACKAGES.md").write_text(cohort_md, encoding="utf-8")
    _write_json(output_dir / "phase12_event_split_decision.candidate.template.json", split_tmpl)
    (output_dir / "SPLIT_OPTION_A_RECONCILIATION.md").write_text(split_md, encoding="utf-8")
    _write_json(output_dir / "phase12_evaluation_inputs.template.json", manifest_tmpl)
    (output_dir / "EVALUATION_INPUT_MANIFEST_RUNBOOK.md").write_text(manifest_md, encoding="utf-8")
    _write_json(output_dir / "eval_authorization.template.json", eval_auth_tmpl)

    guide = "\n".join(
        [
            "# PI Human-Approval Preparation Package Index",
            "",
            "All templates in this directory are **unsigned technical preparation artifacts** (`__HUMAN_APPROVAL_REQUIRED__` markers preserved). No active governance files under `data/governance/`, `data/splits/`, `data/manifests/`, or `data/ground_truth/reviews/` were created or modified.",
            "",
            "## Ordered PI Approval Sequence",
            "1. **Raw Media Access (`AUTH-MEDIA-ACCESS`):** Review & sign [`AUTH_MEDIA_ACCESS.template.json`](AUTH_MEDIA_ACCESS.template.json), compute `record_sha256 = media_guard._canonical_sha256(record)`, and write to `data/governance/AUTH-MEDIA-ACCESS.json`.",
            "2. **Stage-2.1 27-Event Ground-Truth Reviews:** Execute human frame-by-frame review across all 27 events per [`STAGE21_27_EVENT_REVIEW_CHECKLIST.md`](STAGE21_27_EVENT_REVIEW_CHECKLIST.md) ([JSON](STAGE21_27_EVENT_REVIEW_CHECKLIST.json)).",
            "3. **Three Cohort Packages & Promotion Receipt:** Confirm coverage across `train_events`, `no_train_events`, and `engine_events` via [`COHORT_APPROVAL_PACKAGES.md`](COHORT_APPROVAL_PACKAGES.md) ([JSON](COHORT_APPROVAL_PACKAGES.json)) and emit `data/governance/stage21_promotion_receipt.json` via `readiness_cli`.",
            "4. **Event-Level Split Decision (`Option A` Reconciliation):** Read [`SPLIT_OPTION_A_RECONCILIATION.md`](SPLIT_OPTION_A_RECONCILIATION.md); only if superseding `SPLIT-DECISION-OPTION-A-2026-11-09`, sign [`phase12_event_split_decision.candidate.template.json`](phase12_event_split_decision.candidate.template.json) to `data/splits/phase12_event_split_decision.json`.",
            "5. **Evaluation Input Manifest:** Follow [`EVALUATION_INPUT_MANIFEST_RUNBOOK.md`](EVALUATION_INPUT_MANIFEST_RUNBOOK.md) (schema: [`phase12_evaluation_inputs.template.json`](phase12_evaluation_inputs.template.json)) to produce `data/manifests/phase12_evaluation_inputs.json` from real post-Stage-2.1 `phase12-replay-evidence/1` sources.",
            "6. **Evaluation Authorization & Execution:** Populate dynamic hashes in [`eval_authorization.template.json`](eval_authorization.template.json) from `assess_official_phase12_readiness(Path('.')).live_bindings`, compute `record_sha256 = governance.canonical_record_sha256(record)`, save as `data/governance/eval_authorization.json`, verify `railway_detection evaluation status` (`ready: true`), then execute `railway_detection evaluation run`.",
            "",
            "## Pre-Verified Static Live Bindings (Current Repository)",
            f"- `decision_policy_sha256`: `{readiness.live_bindings['decision_policy_sha256']}`",
            f"- `frozen_config_sha256`: `{readiness.live_bindings['frozen_config_sha256']}`",
            f"- `protocol_profile_sha256`: `{readiness.live_bindings['protocol_profile_sha256']}`",
            f"- `r04_scope_decision_sha256`: `{readiness.live_bindings['r04_scope_decision_sha256']}`",
            "",
        ]
    )
    (output_dir / "PI_APPROVAL_EXECUTION_GUIDE.md").write_text(guide, encoding="utf-8")

    return {
        "output_dir": str(output_dir),
        "total_events_in_checklist": len(event_keys),
        "authorized_reviewers": reviewers,
        "static_live_bindings": {
            k: v
            for k, v in readiness.live_bindings.items()
            if v is not None
        },
        "files_written": sorted(p.name for p in output_dir.iterdir() if p.is_file()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare unsigned PI human-approval packages cleanly.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/generated/approval_packages"),
    )
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.output_dir if args.output_dir.is_absolute() else (root / args.output_dir)
    summary = build_pi_approval_packages(root, out)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
