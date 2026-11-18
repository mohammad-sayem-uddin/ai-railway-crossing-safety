"""Forensic event-level split audit and targeted data-collection planning (Mission 4, Task 1).

Reads ONLY metadata manifests, QuickTime creation-time deltas, sync verdicts,
and unapproved proposal JSONs. Never touches ``data/raw/``, never alters
frozen protocol decisions, and never falsely marks a single-crossing or
two-session split ``leakage_safe=True``.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from railway_detection.research_contracts import ResearchContractError, validate_event_level_split

SCHEMA_VERSION = "layer-b-event-split-audit/1.1"
_Z_95 = 1.959963984540054


def _wilson_ci_95(k: int, n: int) -> tuple[float, float]:
    """Two-sided 95% Wilson score interval for k successes in n trials."""
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    z2 = _Z_95 * _Z_95
    denom = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    half = (_Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * n)) / n)) / denom
    return (round(max(0.0, center - half), 4), round(min(1.0, center + half), 4))


def _clopper_pearson_zero_failure_upper_95(n: int, alpha: float = 0.05) -> float:
    """Exact one-sided (1-alpha) Clopper-Pearson upper risk bound given 0/n failures."""
    if n <= 0:
        return 1.0
    return round(1.0 - (alpha ** (1.0 / n)), 4)


def _min_n_for_zero_failure_upper_bound(p_max: float, alpha: float = 0.05) -> int:
    """Smallest n such that 0/n failures yields one-sided upper bound <= p_max."""
    if not (0.0 < p_max < 1.0):
        raise ValueError("p_max must lie in (0, 1)")
    return math.ceil(math.log(alpha) / math.log(1.0 - p_max))


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


def calculate_option_c_statistical_power_and_cohort_design() -> dict[str, Any]:
    """Recalculate Option C sample-size and cohort requirements from research questions."""
    n_unclustered_10pct = _min_n_for_zero_failure_upper_bound(0.10)
    n_unclustered_5pct = _min_n_for_zero_failure_upper_bound(0.05)
    passages_per_session = 10
    intra_session_icc = 0.05
    deff = round(1.0 + (passages_per_session - 1) * intra_session_icc, 2)
    n_cluster_10pct = math.ceil(n_unclustered_10pct * deff)
    n_cluster_5pct = math.ceil(n_unclustered_5pct * deff)
    return {
        "structural_floor_critique": {
            "minimal_3crossing_6session_total": {
                "crossings": 3,
                "sessions": 6,
                "assumed_test_train_passages": 12,
                "assumed_test_no_train_controls": 6,
                "zero_premature_opening_95_upper_bound": _clopper_pearson_zero_failure_upper_95(12),
                "zero_false_closure_95_upper_bound": _clopper_pearson_zero_failure_upper_95(6),
            },
            "why_insufficient": (
                "A structural minimum of 3 crossings x 2 sessions (yielding ~12 held-out test trains and "
                "~6 test no_train clips) leaves 0/12 premature openings with a 22.09% one-sided 95% upper "
                "risk bound and 0/6 false closures with a 39.30% upper bound, and puts only 1 crossing in "
                "val/test (crossing-specific outlier vulnerability)."
            ),
        },
        "exact_binomial_and_cluster_targets": {
            "intra_session_icc_assumed": intra_session_icc,
            "passages_per_session_assumed": passages_per_session,
            "cluster_design_effect": deff,
            "zero_failure_95_upper_bound_10pct_unclustered_n": n_unclustered_10pct,
            "zero_failure_95_upper_bound_5pct_unclustered_n": n_unclustered_5pct,
            "cluster_adjusted_test_trains_for_10pct_bound": n_cluster_10pct,
            "cluster_adjusted_test_trains_for_5pct_bound": n_cluster_5pct,
            "unclustered_test_no_train_for_10pct_bound": n_unclustered_10pct,
            "cluster_adjusted_test_no_train_for_10pct_bound": n_cluster_10pct,
            "mcnemar_80pct_power_note": (
                f"Detecting a paired premature-opening reduction from >=20% (V2) to <=1% (V3) at alpha=0.05 "
                f"requires >=8 discordant passages (>={n_cluster_10pct} cluster-adjusted synced test train passages at DEFF={deff})."
            ),
        },
        "recommended_three_cohort_design": {
            "total_crossings_target": ">= 5 disjoint rural/semi-urban level crossings (eliminating single-site val/test fragility)",
            "total_sessions_target": ">= 11 sessions spanning Day-Clear, Day-Rain/Fog, Night-Clear, Night-Rain/Fog",
            "total_events_target": ">= 220 balanced events across train, val, and test cohorts",
            "cohorts": {
                "train": {
                    "crossings": ">= 2 crossings (e.g., crossing_A + crossing_E)",
                    "sessions": ">= 4 sessions across day/night/rain",
                    "train_passages": ">= 60",
                    "no_train_controls": ">= 30 (>= 60 s road-horn/traffic clips)",
                    "engine_passages": ">= 8",
                },
                "val": {
                    "crossings": ">= 1-2 disjoint crossings (e.g., crossing_B; zero overlap with train/test)",
                    "sessions": ">= 3 sessions across day/night/rain",
                    "train_passages": ">= 24",
                    "no_train_controls": ">= 15 (>= 60 s road-horn/traffic clips)",
                    "engine_passages": ">= 4",
                    "role": "Strictly for model selection, acoustic hysteresis (tau, k), and temperature calibration only.",
                },
                "test": {
                    "crossings": ">= 2 unseen crossings (e.g., crossing_C + crossing_D; zero overlap with train/val)",
                    "sessions": ">= 4 sessions balanced across 2x2 Day/Night x Clear/Monsoon strata",
                    "train_passages": f">= {n_cluster_10pct} synced full-train passages (for <=10% cluster-adjusted 95% upper bound; >= {n_cluster_5pct} for <=5% bound)",
                    "no_train_controls": f">= {n_unclustered_10pct} road-horn/traffic clips >=60 s each (>= {n_cluster_10pct} cluster-adjusted)",
                    "engine_passages": ">= 8 uncensored entry-to-T4 clearance passages",
                    "role": "Locked single-shot evaluation only after model/threshold freeze on val.",
                },
            },
            "confounding_controls": [
                "Identical camera & microphone hardware per crossing across train, no_train, and engine cohorts.",
                "2x2 lighting x weather factorial balance with matched no_train controls inside every capture session.",
                "NTP/GPS sync + audible/visual slate clapper establishing sub-100 ms sync on 100% of dual-camera clips.",
                "Physical crossing-box occupancy ground truth (calibrated overhead camera or inductive/radar logger).",
                "Pre-collection distance/resolution calibration pilot (40-210 m) checking >=24-32 px train bbox height at 416 px.",
            ],
        },
    }


def evaluate_option_a_stratified_corpus_diagnostics(
    repo_root: Path,
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    """Stratified non-raw Option A diagnostics joining exp_n_event_matrix.csv with session metadata."""
    exp_n_path = repo_root / "results/exploratory_v2/experiments/exp_n_event_matrix.csv"
    if not exp_n_path.is_file():
        return {"available": False, "reason": "missing_exp_n_event_matrix_csv"}

    by_key = {e["event_key"]: e for e in events}
    with exp_n_path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    def _as_bool(v: str | None) -> bool:
        return str(v or "").strip().lower() == "true"

    def _as_int(v: str | None) -> int:
        return int(float(v)) if v and str(v).strip() else 0

    def _as_float(v: str | None) -> float | None:
        return float(v) if v and str(v).strip() else None

    train_rows = [r for r in rows if by_key.get(r["event_id"], {}).get("cohort") == "train_events"]
    no_train_rows = [r for r in rows if by_key.get(r["event_id"], {}).get("cohort") == "no_train_events"]
    engine_rows = [r for r in rows if by_key.get(r["event_id"], {}).get("cohort") == "engine_events"]

    def _summarize_train_group(group: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(group)
        front_det = sum(1 for r in group if _as_bool(r["front_detected"]))
        closures = sum(1 for r in group if _as_bool(r["closure_decision"]))
        side_frames = sum(_as_int(r["side_proxy_detected_frames"]) for r in group)
        rear_dets = sum(_as_int(r["back_rear_dets"]) for r in group)
        last_carriage = sum(_as_int(r["back_last_carriage_dets"]) for r in group)
        sync_n = sum(1 for r in group if _as_bool(r["is_sync11"]))
        c_rate = round(closures / n, 4) if n else 0.0
        return {
            "n_events": n,
            "sync11_count": sync_n,
            "front_detected_count": front_det,
            "closure_decision_count": closures,
            "closure_rate": c_rate,
            "closure_rate_wilson_95_ci": list(_wilson_ci_95(closures, n)),
            "side_proxy_frames_total": side_frames,
            "back_rear_dets_total": rear_dets,
            "back_last_carriage_dets_total": last_carriage,
        }

    s1_train = [
        r for r in train_rows if by_key[r["event_id"]]["true_capture_session"] == "session_20260914"
    ]
    s2_train = [
        r for r in train_rows if by_key[r["event_id"]]["true_capture_session"] == "session_20261004"
    ]
    all_summary = _summarize_train_group(train_rows)
    s1_summary = _summarize_train_group(s1_train)
    s2_summary = _summarize_train_group(s2_train)
    s2_side_pct = (
        round((s2_summary["side_proxy_frames_total"] / all_summary["side_proxy_frames_total"]) * 100.0, 2)
        if all_summary["side_proxy_frames_total"]
        else 0.0
    )
    s2_rear_pct = (
        round((s2_summary["back_rear_dets_total"] / all_summary["back_rear_dets_total"]) * 100.0, 2)
        if all_summary["back_rear_dets_total"]
        else 0.0
    )

    sync11_rows = [r for r in train_rows if _as_bool(r["is_sync11"])]
    sync11_l1_closed = [r for r in sync11_rows if _as_bool(r["closure_decision"])]
    rear_positive_events = [r["event_id"] for r in train_rows if _as_int(r["back_rear_dets"]) > 0]
    rear_pos_sync11 = [r["event_id"] for r in sync11_rows if _as_int(r["back_rear_dets"]) > 0]

    t2_vals = sorted(_as_float(r["T2_s"]) for r in train_rows if _as_float(r["T2_s"]) is not None)
    margins = [_as_float(r["safety_margin_vs_T2_s"]) for r in train_rows if _as_float(r["safety_margin_vs_T2_s"]) is not None]

    nt_closures = sum(1 for r in no_train_rows if _as_bool(r["closure_decision"]))
    eng_closures = sum(1 for r in engine_rows if _as_bool(r["closure_decision"]))
    proposal_occ_note_rows = [
        r["event_id"]
        for r in rows
        if str(r["occupancy_sensor_state"] or "").strip() not in ("", "MISSING_OR_UNKNOWN")
    ]

    return {
        "schema_version": "option-a-stratified-diagnostics/1.0",
        "evidence_classification": "CACHE_ONLY_EXPLORATORY_PRE_DB40305",
        "source_csv": "results/exploratory_v2/experiments/exp_n_event_matrix.csv",
        "approach_detection_by_session": {
            "all_train_events": all_summary,
            "session_20260914_daytime": s1_summary,
            "session_20261004_night_lowlight": s2_summary,
            "interpretation": (
                f"Pooled {all_summary['closure_decision_count']}/{all_summary['n_events']} "
                f"({all_summary['closure_rate'] * 100:.2f}%) closure mixes Session 1 daytime "
                f"({s1_summary['closure_decision_count']}/{s1_summary['n_events']} = "
                f"{s1_summary['closure_rate'] * 100:.1f}%, pre-db40305 -90 deg .mov rotation losses) "
                f"and Session 2 night low-light ({s2_summary['closure_decision_count']}/{s2_summary['n_events']} = "
                f"{s2_summary['closure_rate'] * 100:.1f}%, producing {s2_side_pct:.2f}% of all side_proxy "
                f"frames and {s2_rear_pct:.2f}% of all back_rear_dets on 0/3 sync11 clips)."
            ),
        },
        "exit_confirmation_and_sync11_fail_closed_finding": {
            "sync11_event_count": len(sync11_rows),
            "sync11_session_distribution": dict(
                sorted(Counter(by_key[r["event_id"]]["true_capture_session"] for r in sync11_rows).items())
            ),
            "sync11_l1_closed_count": len(sync11_l1_closed),
            "sync11_back_rear_dets_positive_count": len(rear_pos_sync11),
            "sync11_back_last_carriage_dets_positive_count": sum(
                1 for r in sync11_rows if _as_int(r["back_last_carriage_dets"]) > 0
            ),
            "sync11_physical_occupancy_sensor_count": 0,
            "sync11_clearance_decision_v3_count": sum(
                1 for r in sync11_rows if _as_bool(r["clearance_decision_v3_sync11"])
            ),
            "sync11_reopening_decision_v3_count": sum(
                1 for r in sync11_rows if _as_bool(r["reopening_decision_v3_sync11"])
            ),
            "sync11_v2_premature_opening_count": sum(
                1 for r in sync11_rows if _as_bool(r["v2_premature_opening_vs_T4"])
            ),
            "sync11_v3_premature_opening_count": sum(
                1 for r in sync11_rows if _as_bool(r["v3_premature_opening_vs_T4"])
            ),
            "sync11_zero_premature_opening_95_upper_bound_all11": _clopper_pearson_zero_failure_upper_95(
                len(sync11_rows)
            ),
            "sync11_zero_premature_opening_95_upper_bound_l1_closed": _clopper_pearson_zero_failure_upper_95(
                len(sync11_l1_closed)
            ),
            "events_with_positive_back_rear_dets": rear_positive_events,
            "events_with_positive_back_rear_dets_in_sync11": rear_pos_sync11,
            "architectural_implication": (
                "On pre-db40305 sync11 caches, 0/11 clips contain positive rear detections or physical "
                "occupancy sensors; V3_CONSERVATIVE_POSITIVE prevents premature openings (0/11 vs 4/11 V2) "
                "strictly by latching fail-closed until clip EOF (0/11 completed real-cache reopenings). "
                "Positive rear-exit + occupancy AND-gate reopening is verified in SYNTHETIC_ONLY runs (Exp K, L, Q)."
            ),
        },
        "false_closure_and_control_confounding": {
            "no_train_count": len(no_train_rows),
            "no_train_false_closures_v3": nt_closures,
            "no_train_false_closure_95_upper_bound": _clopper_pearson_zero_failure_upper_95(len(no_train_rows)),
            "no_train_daytime_count": sum(
                1 for r in no_train_rows if by_key[r["event_id"]]["true_lighting"] == "day"
            ),
            "engine_count": len(engine_rows),
            "engine_false_closures_v3": eng_closures,
        },
        "kinematic_lead_time_and_siting_limitations": {
            "t2_observed_train_count": len(t2_vals),
            "t2_min_s": min(t2_vals) if t2_vals else None,
            "t2_median_s": round(t2_vals[len(t2_vals) // 2], 4) if t2_vals else None,
            "t2_max_s": max(t2_vals) if t2_vals else None,
            "positive_margin_count": sum(1 for m in margins if m >= 0.0),
            "min_margin_vs_t2_s": min(margins) if margins else None,
            "max_margin_vs_t2_s": max(margins) if margins else None,
            "physical_occupancy_sensor_count": 0,
            "proposal_only_scene_clear_note_events": proposal_occ_note_rows,
            "siting_distance_validation_status": "UNVALIDATED_KINEMATIC_ENGINEERING_ESTIMATE",
        },
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
                "target_total_crossings": ">= 3 disjoint crossings minimum structural floor; >= 5 crossings recommended for outlier resilience and statistical power",
                "rationale": "Eliminates background geometry, barrier appearance, acoustic reverberation, and crossing-specific false-alarm leakage.",
            },
            "minimum_balanced_sessions": {
                "minimum_sessions_per_crossing": 2,
                "target_total_sessions": ">= 6 capture sessions structural floor; >= 11 balanced sessions across train/val/test recommended to reach >= 42 test trains",
                "within_each_session": {
                    "full_train_passages": ">= 6 passages (passenger + freight where available)",
                    "no_train_traffic_controls": ">= 3 daytime + >= 3 nighttime road-traffic horn clips per crossing (>= 60 s each)",
                    "engine_only_passages": ">= 1 full entry-to-exit passage covering complete rear clearance T4",
                },
            },
            "hardware_and_synchronization_protocol": [
                "Use identical camera hardware across train/no_train/engine cohorts within each session (no mid-cohort iPhone-to-iPad swap).",
                "Lock orientation metadata upright or maintain strict orthogonal rotation tags; verify NTP/GPS clock sync plus an audible/visual slate clapper at session start & end to establish sub-100ms front-back sync across ALL events (eliminating the 15 non-CALIBRATION_SUPPORTED events).",
                "Treat 84–211 m upstream distance (7.6 s closure budget at 40–100 km/h) as an unvalidated kinematic engineering estimate until verified via site-specific lens focal length, small-object pixel height (>= 24–32 px at 416 px), curvature, and >= 10 s pre-entry buffer.",
                "Record independent occupancy ground truth (calibrated overhead crossing camera or inductive/radar occupancy logger) plus dedicated lateral crossing-box FOV.",
            ],
        },
        "statistical_power_and_sample_size_recalculation": calculate_option_c_statistical_power_and_cohort_design(),
        "interim_scientifically_defensible_path": {
            "recommended_now": "Honor active researcher decision SPLIT-DECISION-OPTION-A-2026-11-09 (27-event full-cohort descriptive benchmark via Stage-2.1 review + descriptive execution authorization), reporting exact Wilson/Clopper-Pearson 95% CIs and prohibiting cross-crossing generalization claims.",
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
    collection_plan = generate_targeted_collection_plan()
    n_cluster_10pct = collection_plan["statistical_power_and_sample_size_recalculation"][
        "exact_binomial_and_cluster_targets"
    ]["cluster_adjusted_test_trains_for_10pct_bound"]
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
        "strategy_comparison": {
            "recommended_for_existing_27_events": "Option A (Descriptive single-crossing research via Stage-2.1 + AUTH-DESCRIPTIVE-EVAL-EXEC)",
            "recommended_for_generalization_and_model_retraining": f"Option C (Multi-crossing collection >=5 crossings / >=11 sessions / >={n_cluster_10pct} cluster-adjusted test synced train passages before Phase 12)",
            "pi_approval_required_before_scope_change": True,
        },
        "root_causes": [
            f"Single physical site: all 27 events share crossing_id={crossings!r} (0 held-out crossings).",
            f"Two physical sessions: only {true_sessions} exist (< 3 non-empty split roles required by validate_event_level_split).",
            "Session-hardware-class confounding: all 3 no_train_events and 1 engine_events clip occur only in Session 2 (2026-10-04 night, iPad back camera); 20/23 train events occur in Session 1 (2026-09-14 day, iPhone back camera).",
            "AI proposal metadata bug: batch_multimodal_annotator hardcoded recording_session_id='session_20260914_morning' on 27/27 events and lighting='day' on night clips train_events/021..023.",
        ],
        "proposal_metadata_inconsistencies_count": len(proposal_bugs),
        "proposal_metadata_inconsistencies": proposal_bugs,
        "option_a_stratified_diagnostics": evaluate_option_a_stratified_corpus_diagnostics(repo_root, events),
        "candidate_splits_evaluated": {
            "prior_hash_candidate_16_6_5": prior_eval,
            "chrono_temporal_block_15_5_7": chrono_eval,
        },
        "targeted_additional_data_collection_plan": collection_plan,
        "events": events,
    }
