"""Forensic event-level split audit and targeted data-collection planning (Mission 4, Task 1).

Reads ONLY metadata manifests, QuickTime creation-time deltas, sync verdicts,
and unapproved proposal JSONs. Never touches ``data/raw/``, never alters
frozen protocol decisions, and never falsely marks a single-crossing or
two-session split ``leakage_safe=True``.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from railway_detection.research_contracts import ResearchContractError, validate_event_level_split

SCHEMA_VERSION = "layer-b-event-split-audit/1.0"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_proposal_path(proposals_dir: Path, cohort: str, event_id: str) -> Path | None:
    candidates = sorted(
        (proposals_dir / cohort).glob(f"{event_id}_proposal_v*.json"),
        key=lambda p: int(p.stem.rsplit("_v", 1)[1]),
    )
    return candidates[-1] if candidates else None


def _parse_iso(ts: str | None) -> float | None:
    if not ts:
        return None
    return datetime.fromisoformat(ts).timestamp()


def build_event_provenance_table(repo_root: Path) -> list[dict[str, Any]]:
    """Reconstruct authoritative metadata for all 27 eligible Layer-B events."""
    inventory = _read_json(repo_root / "data/manifests/layer_b_v2_annotation_inventory.json")
    rw_manifest = _read_json(repo_root / "data/manifests/real_world_v2_video_manifest.json")
    qt_deltas = _read_json(repo_root / "results/r04_sync_estimation/quicktime_creationdate_deltas.json")
    sync_yaml = yaml.safe_load(
        (repo_root / "data/manifests/camera_sync_offsets_candidate.yaml").read_text(encoding="utf-8")
    )
    r04_decision = _read_json(repo_root / "data/manifests/phase12_r04_scope_decision.json")
    proposals_dir = repo_root / "data/ground_truth/proposals"

    rw_by_key_cam: dict[tuple[str, str], dict[str, Any]] = {}
    cohort_by_event_type = {
        "full_train": "train_events",
        "full_train_night": "train_events",
        "no_train": "no_train_events",
        "engine_only": "engine_events",
    }
    for rec in rw_manifest.get("records", []):
        if not rec.get("evaluation_eligible"):
            continue
        cohort = cohort_by_event_type.get(rec.get("event_type"))
        if not cohort:
            continue
        event_key = f"{cohort}/{rec['event_id']}"
        rw_by_key_cam[(event_key, rec["camera_id"])] = rec

    rows: list[dict[str, Any]] = []
    for event_key in sorted(inventory):
        inv = inventory[event_key]
        cohort, event_id = event_key.split("/", 1)
        qt = qt_deltas.get(event_key, {})
        front_ts = _parse_iso(qt.get("creationdate_front"))
        back_ts = _parse_iso(qt.get("creationdate_back"))
        date_str = str(qt.get("creationdate_front") or "")[:10]
        true_session = (
            "session_20260914"
            if date_str == "2026-09-14"
            else ("session_20261004" if date_str == "2026-10-04" else f"session_{date_str}")
        )
        rw_f = rw_by_key_cam.get((event_key, "front"), {})
        rw_b = rw_by_key_cam.get((event_key, "back"), {})

        prop_path = _latest_proposal_path(proposals_dir, cohort, event_id)
        prop_data = _read_json(prop_path) if prop_path else {}
        prop_site = prop_data.get("proposed_site_metadata", {})
        prop_env = prop_data.get("proposed_environmental_conditions", {})

        is_night_filename = "night" in str(rw_f.get("original_filename", "")).lower()
        true_lighting = (
            "night_lowlight"
            if (is_night_filename or true_session == "session_20261004")
            else "day"
        )
        proposal_bugs: list[str] = []
        if prop_site.get("recording_session_id") == "session_20260914_morning" and true_session != "session_20260914":
            proposal_bugs.append("proposal_session_id_hardcoded_20260914_on_20261004_event")
        if is_night_filename and prop_env.get("lighting") == "day":
            proposal_bugs.append("proposal_lighting_mislabeled_day_on_night_lowlight_file")

        sync_info = (sync_yaml.get("events") or {}).get(event_key, {})
        rows.append(
            {
                "event_key": event_key,
                "cohort": cohort,
                "event_id": event_id,
                "crossing_id": str(prop_site.get("crossing_id") or "crossing_A"),
                "true_capture_session": true_session,
                "creationdate_front": qt.get("creationdate_front"),
                "creationdate_back": qt.get("creationdate_back"),
                "front_epoch_s": front_ts,
                "back_epoch_s": back_ts,
                "delta_qt_s": qt.get("delta_qt_s"),
                "original_front_file": rw_f.get("original_filename"),
                "original_back_file": rw_b.get("original_filename"),
                "front_sha256": inv["front"]["sha256"],
                "back_sha256": inv["back"]["sha256"],
                "front_res": f"{rw_f.get('width')}x{rw_f.get('height')}@{rw_f.get('fps')}",
                "back_res": f"{rw_b.get('width')}x{rw_b.get('height')}@{rw_b.get('fps')}",
                "true_lighting": true_lighting,
                "proposal_site_metadata": prop_site,
                "proposal_environmental_conditions": prop_env,
                "proposal_metadata_bugs": proposal_bugs,
                "r04_scope_mode": (r04_decision.get("event_modes") or {}).get(event_key),
                "sync_verdict": sync_info.get("calibration_verdict"),
            }
        )

    # Assign contiguous intraday capture blocks (gap > 900s = 15 min)
    dated_rows = sorted(rows, key=lambda r: (r["front_epoch_s"] or 0.0, r["event_key"]))
    cluster_idx_by_session: Counter[str] = Counter()
    prev_session: str | None = None
    prev_epoch: float | None = None
    for row in dated_rows:
        sess = row["true_capture_session"]
        ep = row["front_epoch_s"] or 0.0
        if sess != prev_session or prev_epoch is None or (ep - prev_epoch) > 900.0:
            cluster_idx_by_session[sess] += 1
        row["intraday_block_id"] = f"{sess}_blk_{cluster_idx_by_session[sess]:02d}"
        prev_session = sess
        prev_epoch = ep

    return sorted(rows, key=lambda r: r["event_key"])


def evaluate_candidate_split(
    events: list[dict[str, Any]],
    partitions: dict[str, list[str]],
    *,
    name: str,
    description: str = "",
    adjacent_gap_s: float = 180.0,
) -> dict[str, Any]:
    """Audit mechanical validity, group leakage, adjacent pairs, and cohort balance."""
    validate_event_level_split(partitions)
    expected_keys = {e["event_key"] for e in events}
    assigned_keys = {ek for ids in partitions.values() for ek in ids}
    if assigned_keys != expected_keys:
        raise ResearchContractError(
            f"partition events differ from corpus events: missing={sorted(expected_keys - assigned_keys)}, "
            f"extra={sorted(assigned_keys - expected_keys)}"
        )

    role_by_event = {ek: role for role, ids in partitions.items() for ek in ids}
    by_key = {e["event_key"]: e for e in events}

    def _overlaps(field: str) -> dict[str, list[str]]:
        groups: dict[str, set[str]] = defaultdict(set)
        for ek, role in role_by_event.items():
            groups[str(by_key[ek].get(field))].add(role)
        return {g: sorted(roles) for g, roles in sorted(groups.items()) if len(roles) > 1}

    crossing_overlaps = _overlaps("crossing_id")
    session_overlaps = _overlaps("true_capture_session")
    block_overlaps = _overlaps("intraday_block_id")
    front_sha_overlaps = _overlaps("front_sha256")
    back_sha_overlaps = _overlaps("back_sha256")

    # Detect close-in-time pairs (< adjacent_gap_s) or identical back/front timestamps split across roles
    dated = sorted(
        (by_key[ek] for ek in role_by_event),
        key=lambda e: (e.get("front_epoch_s") or 0.0, e["event_key"]),
    )
    split_adjacent_pairs: list[dict[str, Any]] = []
    for i in range(len(dated) - 1):
        a, b = dated[i], dated[i + 1]
        if a["true_capture_session"] != b["true_capture_session"]:
            continue
        dt_front = abs((b.get("front_epoch_s") or 0.0) - (a.get("front_epoch_s") or 0.0))
        same_back_ts = (
            a.get("creationdate_back") is not None
            and a.get("creationdate_back") == b.get("creationdate_back")
        )
        if (dt_front <= adjacent_gap_s or same_back_ts) and (
            role_by_event[a["event_key"]] != role_by_event[b["event_key"]]
        ):
            split_adjacent_pairs.append(
                {
                    "event_a": a["event_key"],
                    "role_a": role_by_event[a["event_key"]],
                    "event_b": b["event_key"],
                    "role_b": role_by_event[b["event_key"]],
                    "front_gap_s": round(dt_front, 2),
                    "same_creationdate_back": same_back_ts,
                }
            )

    n_crossings = len({e["crossing_id"] for e in events})
    n_sessions = len({e["true_capture_session"] for e in events})

    role_summary: dict[str, dict[str, Any]] = {}
    empty_negative_roles: list[str] = []
    zero_dual_cam_roles: list[str] = []
    for role in ("train", "val", "test"):
        keys = partitions[role]
        cohorts = Counter(by_key[k]["cohort"] for k in keys)
        sessions = Counter(by_key[k]["true_capture_session"] for k in keys)
        lighting = Counter(by_key[k]["true_lighting"] for k in keys)
        modes = Counter(by_key[k]["r04_scope_mode"] for k in keys)
        if cohorts.get("no_train_events", 0) == 0:
            empty_negative_roles.append(role)
        if modes.get("dual_camera", 0) == 0:
            zero_dual_cam_roles.append(role)
        role_summary[role] = {
            "count": len(keys),
            "cohorts": dict(sorted(cohorts.items())),
            "sessions": dict(sorted(sessions.items())),
            "lighting": dict(sorted(lighting.items())),
            "r04_modes": dict(sorted(modes.items())),
        }

    raw_media_disjoint = not front_sha_overlaps and not back_sha_overlaps
    crossing_disjoint = n_crossings >= 3 and not crossing_overlaps
    session_disjoint = n_sessions >= 3 and not session_overlaps
    adjacent_disjoint = len(split_adjacent_pairs) == 0
    # Strict OOD/generalization leakage_safe requires raw media disjointness AND crossing + session independence
    leakage_safe = bool(raw_media_disjoint and crossing_disjoint and session_disjoint)

    scientific_defects: list[str] = []
    if not crossing_disjoint:
        scientific_defects.append(f"SINGLE_CROSSING_OVERLAP (n_crossings={n_crossings} < 3)")
    if not session_disjoint:
        scientific_defects.append(f"INSUFFICIENT_OR_OVERLAPPING_SESSIONS (n_sessions={n_sessions} < 3)")
    if block_overlaps:
        scientific_defects.append(f"INTRADAY_CLUSTER_OVERLAP ({list(block_overlaps)})")
    if split_adjacent_pairs:
        scientific_defects.append(f"ADJACENT_OR_TIED_TIMESTAMP_PAIR_SPLIT (n={len(split_adjacent_pairs)})")
    if empty_negative_roles:
        scientific_defects.append(f"ZERO_NO_TRAIN_CONTROLS_IN_ROLES ({empty_negative_roles})")
    if zero_dual_cam_roles:
        scientific_defects.append(f"ZERO_DUAL_CAMERA_IN_ROLES ({zero_dual_cam_roles})")

    return {
        "name": name,
        "description": description,
        "mechanical_event_disjoint": True,
        "leakage_safe": leakage_safe,
        "checks": {
            "raw_media_sha256_disjoint": raw_media_disjoint,
            "crossing_disjoint": crossing_disjoint,
            "session_disjoint": session_disjoint,
            "intraday_block_disjoint": not block_overlaps,
            "adjacent_or_shared_back_ts_disjoint": adjacent_disjoint,
        },
        "overlaps": {
            "crossing_id": crossing_overlaps,
            "true_capture_session": session_overlaps,
            "intraday_block_id": block_overlaps,
            "split_adjacent_pairs": split_adjacent_pairs,
        },
        "role_summary": role_summary,
        "scientific_defects": scientific_defects,
        "partitions": {r: sorted(partitions[r]) for r in ("train", "val", "test")},
    }


def propose_chronological_within_site_split() -> dict[str, list[str]]:
    """Chronological within-site diagnostic candidate (STILL ``leakage_safe=False``!).

    Avoids hash-shuffling Session 1, keeps tied ``event_007``/``event_008``
    together in ``train``, places one ``no_train`` and at least one R04
    ``dual_camera`` event in every split role, and holds out the latest
    chronological events per session for ``val`` and ``test``. Because only
    1 crossing and 2 capture sessions exist, this candidate remains
    ``leakage_safe=False`` and does NOT support cross-crossing claims.
    """
    return {
        "train": sorted(
            [*(f"train_events/event_{i:03d}" for i in range(1, 14)), "no_train_events/event_002", "engine_events/event_001"]
        ),
        "val": sorted(
            ["train_events/event_014", "train_events/event_015", "train_events/event_016", "train_events/event_021", "no_train_events/event_003"]
        ),
        "test": sorted(
            ["train_events/event_017", "train_events/event_018", "train_events/event_019", "train_events/event_020", "train_events/event_022", "train_events/event_023", "no_train_events/event_001"]
        ),
    }


def generate_targeted_collection_plan() -> dict[str, Any]:
    """Targeted additional-data collection plan required for genuine OOD Phase 12 splits."""
    return {
        "why_current_27_cannot_form_leakage_safe_3way_split": [
            "crossing_id: all 27/27 events share crossing_A (pigeonhole minimum = 3 disjoint crossings for train/val/test).",
            "true_capture_session: only 2 distinct physical capture dates exist (2026-09-14: 20 train events; 2026-10-04: 3 night train + 3 no_train + 1 engine).",
            "hardware_and_class_confound: 100% of negative (no_train) and engine controls come exclusively from Session 2 (night/dusk with iPad 10th-gen back camera), whereas 20/23 train events come from daytime Session 1 (iPhone 15 Pro Max back camera).",
            "left_and_right_censoring: retrospective approach recordings begin with train already visible (0/23 un-censored distant T0/T1), engine_events/event_001 is right-censored at t=9.80s, and no physical crossing occupancy sensors exist (0/27).",
        ],
        "minimum_new_collection_requirements": {
            "independent_crossings": {
                "minimum_new_crossings": 2,
                "target_total_crossings": ">= 3 disjoint rural/semi-urban level crossings (crossing_A=train, crossing_B=val, crossing_C=test, or K-fold leave-one-crossing-out)",
                "rationale": "Eliminates background geometry, barrier appearance, acoustic reverberation, and crossing-specific false-alarm leakage.",
            },
            "minimum_balanced_sessions": {
                "minimum_sessions_per_crossing": 2,
                "target_total_sessions": ">= 6 capture sessions spanning day, dusk/night, and overcast/monsoon rain across every split role",
                "within_each_session": {
                    "full_train_passages": ">= 6 passages (passenger + freight where available)",
                    "no_train_traffic_controls": ">= 3 daytime + >= 3 nighttime road-traffic horn clips per crossing (>= 60 s each)",
                    "engine_only_passages": ">= 1 full entry-to-exit passage covering complete rear clearance T4",
                },
            },
            "hardware_and_synchronization_protocol": [
                "Use identical camera hardware across train/no_train/engine cohorts within each session (no mid-cohort iPhone-to-iPad swap).",
                "Lock orientation metadata upright or maintain strict orthogonal rotation tags; verify NTP/GPS clock sync plus an audible/visual slate clapper at session start & end to establish sub-100ms front-back sync across ALL events (eliminating the 15 non-CALIBRATION_SUPPORTED events).",
                "Site approach cameras 84–211 m upstream along the rail corridor with >= 10 s pre-entry buffer so T0, T1, and T2 satisfy the 7.6 s V3 closure budget without left-censoring.",
                "Record independent occupancy ground truth (calibrated overhead crossing camera or inductive/radar occupancy logger) plus dedicated lateral crossing-box FOV.",
            ],
        },
        "interim_scientifically_defensible_path": {
            "recommended_now": "Honor active researcher decision SPLIT-DECISION-OPTION-A-2026-11-09 (27-event full-cohort descriptive benchmark via Stage-2.1 review + descriptive execution authorization), reporting exact Wilson 95% CIs and prohibiting cross-crossing generalization claims.",
            "do_not": "Do NOT relabel any partition of these 27 events as leakage_safe=true just to unlock Phase 12 held-out evaluation.",
        },
    }


def run_split_audit(repo_root: Path) -> dict[str, Any]:
    """Run complete non-raw audit of the 27-event split problem."""
    events = build_event_provenance_table(repo_root)
    prior_proposal = _read_json(repo_root / "docs/generated/CANDIDATE_EVENT_SPLIT_PROPOSAL.json")
    prior_eval = evaluate_candidate_split(
        events,
        prior_proposal["partitions"],
        name="prior_hash_candidate_16_6_5",
        description="Existing CANDIDATE_EVENT_SPLIT_PROPOSAL.json (sha256 hash order): overlaps crossing_A and both sessions, leaves val with 0 no_train/engine controls, and splits event_007/event_008 (shared 16:12:34 back timestamp).",
    )
    chrono_eval = evaluate_candidate_split(
        events,
        propose_chronological_within_site_split(),
        name="chrono_temporal_block_15_5_7",
        description="Chronological within-site diagnostic alternative: groups tied 007/008 together, places 1 no_train and >=1 dual_camera event in every role, holds out tail events per session — yet remains strictly leakage_safe=False because only 1 crossing and 2 sessions exist.",
    )
    proposal_bugs = [
        {"event_key": e["event_key"], "bugs": e["proposal_metadata_bugs"]}
        for e in events
        if e["proposal_metadata_bugs"]
    ]
    crossings = sorted({e["crossing_id"] for e in events})
    true_sessions = sorted({e["true_capture_session"] for e in events})
    return {
        "schema_version": SCHEMA_VERSION,
        "raw_media_accessed": False,
        "corpus_counts": {
            "total_events": len(events),
            "cohorts": dict(sorted(Counter(e["cohort"] for e in events).items())),
            "crossings": crossings,
            "true_capture_sessions": dict(sorted(Counter(e["true_capture_session"] for e in events).items())),
            "true_lighting": dict(sorted(Counter(e["true_lighting"] for e in events).items())),
            "r04_modes": dict(sorted(Counter(e["r04_scope_mode"] for e in events).items())),
        },
        "can_27_events_produce_leakage_safe_3way_split": False,
        "root_causes": [
            f"Single physical site: all 27 events share crossing_id={crossings!r} (0 held-out crossings).",
            f"Two physical sessions: only {true_sessions} exist (< 3 non-empty split roles required by validate_event_level_split).",
            "Session-hardware-class confounding: all 3 no_train_events and 1 engine_events clip occur only in Session 2 (2026-10-04 night, iPad back camera); 20/23 train events occur in Session 1 (2026-09-14 day, iPhone back camera).",
            "AI proposal metadata bug: batch_multimodal_annotator hardcoded recording_session_id='session_20260914_morning' on 27/27 events and lighting='day' on night clips train_events/021..023.",
        ],
        "proposal_metadata_inconsistencies_count": len(proposal_bugs),
        "proposal_metadata_inconsistencies": proposal_bugs,
        "candidate_splits_evaluated": {
            "prior_hash_candidate_16_6_5": prior_eval,
            "chrono_temporal_block_15_5_7": chrono_eval,
        },
        "targeted_additional_data_collection_plan": generate_targeted_collection_plan(),
        "events": events,
    }
