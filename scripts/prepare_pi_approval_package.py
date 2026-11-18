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
from railway_detection.data.split_audit import (
    build_event_provenance_table,
    evaluate_candidate_split,
    propose_chronological_within_site_split,
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
    provenance_by_key: dict[str, dict[str, Any]],
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
        prov = provenance_by_key[key]
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
            f"PYTHONPATH=src:. .venv/bin/python scripts/run_stage21_review.py "
            f"--reviewer {primary_reviewer} --cohort {cohort} --event {event_id}"
        )
        second_review_cmd = (
            f"PYTHONPATH=src:. .venv/bin/python scripts/run_stage21_review.py "
            f"--reviewer {secondary_reviewer} --cohort {cohort} --event {event_id} "
            f"--second-of <PRIMARY_REVIEW_ID>"
        )
        events_out.append(
            {
                "event_key": key,
                "cohort": cohort,
                "event_id": event_id,
                "capture_session": prov["true_capture_session"],
                "creationdate_front": prov["creationdate_front"],
                "creationdate_back": prov["creationdate_back"],
                "true_lighting": prov["true_lighting"],
                "original_files": {
                    "front": prov["original_front_file"],
                    "back": prov["original_back_file"],
                },
                "r04_scope_mode": prov["r04_scope_mode"],
                "sync_verdict": prov["sync_verdict"],
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
        "| # | Event Key | Session / Lighting / R04 Scope | Active Proposal (SHA-256 prefix) | Expected Front & Back SHA-256 prefixes | Primary Review CLI Command |",
        "|---|---|---|---|---|---|",
    ]
    for idx, ev in enumerate(events_out, start=1):
        p = ev["active_proposal"]
        m = ev["expected_media"]
        ctx = f"{ev['capture_session']} / {ev['true_lighting']} / `{ev['r04_scope_mode']}`"
        lines.append(
            f"| {idx} | `{ev['event_key']}` | {ctx} | `{Path(p['path']).name}` (`{p['sha256'][:12]}...`) | "
            f"`F:{m['front_sha256'][:10]}` / `B:{m['back_sha256'][:10]}` | `{ev['primary_review_command']}` |"
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
        "PYTHONPATH=src:. .venv/bin/python -m railway_detection.annotation.readiness_cli "
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
    provenance_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    """Build exact-key ``phase12-event-split-decision/1`` candidate template & Option A reconciliation."""
    chrono_partitions = propose_chronological_within_site_split()
    governance.validate_event_level_split(chrono_partitions)
    prior_eval = evaluate_candidate_split(
        provenance_rows,
        split_proposal["partitions"],
        name="prior_hash_candidate_16_6_5",
    )
    chrono_eval = evaluate_candidate_split(
        provenance_rows,
        chrono_partitions,
        name="chrono_temporal_block_15_5_7",
    )

    template = {
        "schema_version": governance.SPLIT_DECISION_SCHEMA,
        "decision_status": f"{HUMAN_PLACEHOLDER}_SET_APPROVED_ONLY_IF_ELECTING_SINGLE_SITE_HELD_OUT_EVALUATION",
        "decision_id": f"{HUMAN_PLACEHOLDER}_e.g._PHASE12-EVENT-SPLIT-2026-11-XX",
        "decided_by": f"{HUMAN_PLACEHOLDER}_CHOOSE_FROM_{'|'.join(reviewers)}",
        "decided_at_utc": f"{HUMAN_PLACEHOLDER}_ISO8601_UTC_WITH_TZ",
        "researcher_statement": (
            f"{HUMAN_PLACEHOLDER}_EXPLICIT_PI_STATEMENT_SUPERSEDING_SPLIT-DECISION-OPTION-A-2026-11-09_IF_ELECTED_WITHIN_SITE_ONLY"
        ),
        "attestation": {
            "type": governance.ATTESTATION_RECORDED_STATEMENT,
            "signature": None,
        },
        "recorded_by": {
            "kind": "researcher",
            "identity": f"{HUMAN_PLACEHOLDER}_REVIEWER_EMAIL",
        },
        "partitions": chrono_partitions,
        "source_proposal": {
            "path": "docs/generated/CANDIDATE_EVENT_SPLIT_PROPOSAL.json",
            "proposal_id": split_proposal["proposal_id"],
            "proposal_sha256": split_proposal["proposal_sha256"],
            "audit_report": "results/dataset_audit/layer_b_split_audit_and_collection_plan.json",
            "candidate_name": "chrono_temporal_block_15_5_7",
            "leakage_safe": False,
            "cross_crossing_leakage_safe": False,
            "cross_session_leakage_safe": False,
            "leakage_warning": (
                "No 3-way split of the 27 events can be leakage-safe: all 27 share crossing_A and only 2 capture "
                "sessions exist (2026-09-14 vs 2026-10-04). Keep Option A (descriptive) for publication unless new "
                "multi-crossing data (>=3 crossings) is collected."
            ),
        },
    }

    option_a_exists = (repo_root / "docs/generated/research_decisions/SPLIT_DECISION_OPTION_A_20261109.md").is_file()
    md = "\n".join(
        [
            "# Event-Level Split Decision Preparation & Option A Reconciliation",
            "",
            f"- **Mechanical Validator Status (`chrono_temporal_block_15_5_7`):** `governance.validate_event_level_split(partitions)` **PASSED** (`train={len(chrono_partitions['train'])}`, `val={len(chrono_partitions['val'])}`, `test={len(chrono_partitions['test'])}`, total=`27` disjoint events).",
            f"- **Active Prior PI Decision (`SPLIT-DECISION-OPTION-A-2026-11-09`, file present=`{option_a_exists}`):** Explicitly chose **Option A (Descriptive single-crossing study — NO Phase 12 train/val/test split)**. Keeping `data/splits/phase12_event_split_decision.json` absent remains scientifically preferred for this 27-event single-crossing corpus.",
            "- **Why NO Split of These 27 Events Can Be `leakage_safe = true` ([audit JSON](../../results/dataset_audit/layer_b_split_audit_and_collection_plan.json)):**",
            "  1. All `27/27` events share one physical site (`crossing_id = crossing_A`).",
            "  2. Only `2` physical capture sessions exist (`session_20260914`: 20 train events; `session_20261004`: 3 night train + 3 no_train + 1 engine) — mathematically fewer than `3` non-empty split roles.",
            "  3. `100%` of negative (`no_train`) and engine controls occur exclusively in dusk/night `session_20261004` (`iPad` back camera), confounding class with date/illumination/sensor.",
            f"- **Why Prior `16/6/5` (`CANDIDATE_EVENT_SPLIT_PROPOSAL.json`) Was Rejected (`leakage_safe={prior_eval['leakage_safe']}`):** Hash-shuffling caused `{', '.join(prior_eval['scientific_defects'])}` — specifically `0` `no_train` events in `val` and `0` R04 `dual_camera` events in `test`, plus split adjacent pair `event_007`/`event_008`.",
            f"- **Improved Within-Site Chronological Candidate (`chrono_temporal_block_15_5_7`, `leakage_safe={chrono_eval['leakage_safe']}`):** Keeps tied `event_007`/`008` together, places `1` `no_train` and `>=1` R04 `dual_camera` event in every role (`9/1/1`), and holds out late chronological clips per session — yet STILL carries `leakage_safe = false` and permits **no cross-crossing OOD claim**.",
            "- **For True Leakage-Free Held-Out Evaluation (`Option C`):** Execute the targeted collection plan in `results/dataset_audit/layer_b_split_audit_and_collection_plan.json` (`>= 3` independent crossings, `>= 6` day/night/weather sessions with matched controls).",
            "- **Activation Target (ONLY if PI explicitly elects chronological single-site diagnostic split):** Sign `phase12_event_split_decision.candidate.template.json` to `data/splits/phase12_event_split_decision.json`.",
            "",
        ]
    )
    return template, md


def _build_eval_input_manifest_package(repo_root: Path) -> tuple[dict[str, Any], str]:
    """Build exact-schema template and runbook matching ``manifest_builder.build_evaluation_input_manifest``."""
    template = {
        "schema_version": "phase12-evaluation-inputs/1",
        "evidence_classification": "real",
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
                "source_path": "<relative_to_data/manifests_e.g._phase12_replay_evidence/train_events_event_001.json>",
                "source_sha256": "<live_sha256_of_phase12-replay-evidence/1_source>",
            }
        ],
        "camera_scope_by_event": {
            "<cohort/event_id>": "<dual_camera|independent_camera|single_camera>",
        },
        "accepted_sync_events": ["<11 accepted events from phase12_r04_scope_decision.json>"],
        "derived_from": {
            "event_split_decision_sha256": f"{HUMAN_PLACEHOLDER}_SHA256_OF_data/splits/phase12_event_split_decision.json",
            "r04_scope_decision_sha256": f"{HUMAN_PLACEHOLDER}_SHA256_OF_data/manifests/phase12_r04_scope_decision.json",
        },
    }

    md = "\n".join(
        [
            "# Evaluation Input Manifest Preparation Runbook (`phase12-evaluation-inputs/1`)",
            "",
            "- **Output Destination (Post-Approval Only):** `data/manifests/phase12_evaluation_inputs.json`",
            "- **Why Not Built Pre-Approval:** `manifest_builder.build_evaluation_input_manifest(repository_root, event_sources, output_path)` requires one verified `phase12-replay-evidence/1` source JSON (inside `data/manifests/`, non-symlink, `annotation_labels_used: false`) per split event. No synthetic fixtures, Mission 39 exploratory caches, or pre-`AUTH-MEDIA-ACCESS` caches under `data/cache/` may be substituted (`cache_phase12_adapter.to_official_evidence_payload` refuses by design).",
            "",
            "## Required `phase12-replay-evidence/1` Source Payload Contract",
            "- Exact top-level keys (`replay_evidence.py`): `schema_version`, `event_id`, `cohort`, `camera_mode` (`dual_camera` | `independent_camera` | `single_camera`), `streams` (`front_vision`, `back_vision`, optional `front_audio`), `provenance` (`frozen_config_canonical_sha256`, `checkpoint_sha256` `{vision, audio_v3}`, `vision_confidence_threshold`, `audio_operating_threshold`, `media_sha256`, `inference_run_id`, `annotation_labels_used: false`, `generated_by`).",
            "",
            "## Exact Post-Stage-2.1 Execution Workflow",
            "1. Ensure `data/governance/AUTH-MEDIA-ACCESS.json`, all Stage-2.1 reviews, `data/governance/stage21_promotion_receipt.json`, and an explicit `data/splits/phase12_event_split_decision.json` exist.",
            "2. After `AUTH-MEDIA-ACCESS` approval, extract upright `LayerBEventProcessor` `EvidenceRecord` streams (`camera_1`, `camera_2`, `audio_1`) into per-event `phase12-replay-evidence/1` JSON files under `data/manifests/phase12_replay_evidence/`.",
            "3. Invoke `railway_detection.evaluation.manifest_builder.build_evaluation_input_manifest(repository_root=Path('.'), event_sources=..., output_path=Path('data/manifests/phase12_evaluation_inputs.json'))`.",
            "4. Check readiness (`EVAL_AUTH_NOT_GRANTED` should remain alone), bind `live_bindings` into `data/governance/eval_authorization.json`, then run:",
            "```bash",
            "PYTHONPATH=src:. .venv/bin/python -m railway_detection evaluation status",
            "PYTHONPATH=src:. .venv/bin/python scripts/prepare_and_execute_official_evaluation.py --mode execute-after-approval --output-dir <OUT_DIR_OUTSIDE_REPO_TREES>",
            "```",
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

    provenance_rows = build_event_provenance_table(repo_root)
    provenance_by_key = {row["event_key"]: row for row in provenance_rows}

    event_keys = [item["event_key"] for item in queue["items"]]
    auth_media_tmpl = _build_auth_media_access_template(repo_root, event_keys, reviewers)
    checklist_json, checklist_md = _build_stage21_checklist(
        repo_root, queue, inventory, reviewers, provenance_by_key
    )
    cohort_json, cohort_md = _build_cohort_approval_packages(
        queue,
        [{"code": b.code, "detail": b.detail} for b in readiness.blockers],
    )
    split_tmpl, split_md = _build_split_decision_package(
        repo_root, split_proposal, reviewers, provenance_rows
    )
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
            "All templates in this directory are **unsigned technical preparation artifacts** (`__HUMAN_APPROVAL_REQUIRED__` markers preserved). No active governance files under `data/governance/`, `data/splits/`, `data/manifests/`, or `data/ground_truth/reviews/` were created or modified. For a single plain-English supervisor summary, read [`FINAL_PI_ACTION_REQUIRED.md`](../FINAL_PI_ACTION_REQUIRED.md).",
            "",
            "## Ordered PI Approval Sequence",
            "1. **Raw Media Access (`AUTH-MEDIA-ACCESS`):** Review & sign [`AUTH_MEDIA_ACCESS.template.json`](AUTH_MEDIA_ACCESS.template.json), compute `record_sha256 = media_guard._canonical_sha256(record)`, and write to `data/governance/AUTH-MEDIA-ACCESS.json`.",
            "2. **Stage-2.1 27-Event Ground-Truth Reviews:** Execute human frame-by-frame review across all 27 events per [`STAGE21_27_EVENT_REVIEW_CHECKLIST.md`](STAGE21_27_EVENT_REVIEW_CHECKLIST.md) ([JSON](STAGE21_27_EVENT_REVIEW_CHECKLIST.json)).",
            "3. **Three Cohort Packages & Promotion Receipt:** Confirm coverage across `train_events`, `no_train_events`, and `engine_events` via [`COHORT_APPROVAL_PACKAGES.md`](COHORT_APPROVAL_PACKAGES.md) ([JSON](COHORT_APPROVAL_PACKAGES.json)) and emit `data/governance/stage21_promotion_receipt.json` via `PYTHONPATH=src:. .venv/bin/python -m railway_detection.annotation.readiness_cli ...`.",
            "4. **Event-Level Split Decision (`Option A` Reconciliation):** Read [`SPLIT_OPTION_A_RECONCILIATION.md`](SPLIT_OPTION_A_RECONCILIATION.md) & `results/dataset_audit/layer_b_split_audit_and_collection_plan.json`. **Keep `Option A` (`SPLIT-DECISION-OPTION-A-2026-11-09` descriptive 27-event evaluation -> `AUTH-DESCRIPTIVE-EVAL-EXEC`)**, OR collect `>= 3` independent crossings (`Option C`) before held-out evaluation; only sign [`phase12_event_split_decision.candidate.template.json`](phase12_event_split_decision.candidate.template.json) to `data/splits/phase12_event_split_decision.json` if explicitly electing single-site chronological diagnostics (`leakage_safe = false`).",
            "5. **Evaluation Input Manifest:** Follow [`EVALUATION_INPUT_MANIFEST_RUNBOOK.md`](EVALUATION_INPUT_MANIFEST_RUNBOOK.md) (exact schema: [`phase12_evaluation_inputs.template.json`](phase12_evaluation_inputs.template.json)) to produce `data/manifests/phase12_evaluation_inputs.json` from real post-Stage-2.1 `phase12-replay-evidence/1` sources.",
            "6. **Evaluation Authorization & Execution:** Populate dynamic hashes in [`eval_authorization.template.json`](eval_authorization.template.json) from `assess_official_phase12_readiness(Path('.')).live_bindings`, compute `record_sha256 = governance.canonical_record_sha256(record)`, save as `data/governance/eval_authorization.json`, verify `PYTHONPATH=src:. .venv/bin/python -m railway_detection evaluation status` (`ready: true`), then execute `PYTHONPATH=src:. .venv/bin/python -m railway_detection evaluation run --output-dir <OUT_DIR_OUTSIDE_REPO_TREES>` (or `scripts/prepare_and_execute_official_evaluation.py --mode execute-after-approval --output-dir <OUT_DIR>`).",
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
