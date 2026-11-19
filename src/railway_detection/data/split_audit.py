"""Forensic event-level split audit and targeted data-collection planning (Mission 4, Task 1).

Reads ONLY metadata manifests, QuickTime creation-time deltas, sync verdicts,
and unapproved proposal JSONs. Never touches ``data/raw/``, never alters
frozen protocol decisions, and never falsely marks a single-crossing or
two-session split ``leakage_safe=True``.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from railway_detection.research_contracts import ResearchContractError, validate_event_level_split
from railway_detection.safety.media_guard import require_media_authorization

SCHEMA_VERSION = "layer-b-event-split-audit/1.3"
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


def _exact_unconditional_mcnemar_power(
    n_pairs: int,
    p10: float,
    p01: float = 0.005,
    alpha_two_sided: float = 0.05,
) -> float:
    """Exact unconditional power of two-sided exact binomial McNemar test."""
    if n_pairs <= 0 or (p10 + p01) <= 0.0:
        return 0.0
    p_disc = p10 + p01
    q = p10 / p_disc
    power = 0.0
    for m in range(1, n_pairs + 1):
        pm = math.comb(n_pairs, m) * (p_disc**m) * ((1.0 - p_disc) ** (n_pairs - m))
        for b10 in range(0, m + 1):
            if b10 <= m - b10:
                continue
            k = m - b10
            p_val = min(1.0, 2.0 * sum(math.comb(m, i) * (0.5**m) for i in range(0, k + 1)))
            if p_val <= alpha_two_sided:
                p_b10 = math.comb(m, b10) * (q**b10) * ((1.0 - q) ** (m - b10))
                power += pm * p_b10
    return round(power, 4)


def _min_n_for_mcnemar_power(
    p10: float,
    *,
    p01: float = 0.005,
    target_power: float = 0.80,
    max_n: int = 200,
) -> int:
    """Smallest paired sample size N reaching at least target_power under McNemar exact test."""
    for n in range(1, max_n + 1):
        if _exact_unconditional_mcnemar_power(n, p10, p01=p01) >= target_power:
            return n
    return max_n


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
    """Recalculate Option C sample-size, ICC sensitivity, McNemar power, and cohort sums."""
    n_uncl_10 = _min_n_for_zero_failure_upper_bound(0.10)
    n_uncl_5 = _min_n_for_zero_failure_upper_bound(0.05)
    n_mcnemar_p20 = _min_n_for_mcnemar_power(0.20, p01=0.005, target_power=0.80)
    ref_m = 10
    primary_rho = 0.05
    primary_deff = round(1.0 + (ref_m - 1) * primary_rho, 2)
    n_cl_10 = math.ceil(n_uncl_10 * primary_deff)
    n_cl_5 = math.ceil(n_uncl_5 * primary_deff)
    n_cl_mcnemar_p20 = math.ceil(n_mcnemar_p20 * primary_deff)

    icc_sensitivity: list[dict[str, Any]] = []
    for rho in (0.00, 0.02, 0.05, 0.10, 0.15):
        deff = round(1.0 + (ref_m - 1) * rho, 2)
        icc_sensitivity.append(
            {
                "intra_session_icc_rho": rho,
                "reference_max_passages_per_session_m": ref_m,
                "design_effect_deff": deff,
                "test_trains_for_10pct_cp_bound": math.ceil(n_uncl_10 * deff),
                "test_trains_for_80pct_mcnemar_p20": math.ceil(n_mcnemar_p20 * deff),
                "test_trains_for_5pct_cp_bound": math.ceil(n_uncl_5 * deff),
            }
        )

    def _cohort_block(crossings: int, sessions: int, train_n: int, no_train_n: int, engine_n: int, role: str) -> dict[str, Any]:
        return {
            "crossings": crossings,
            "sessions": sessions,
            "train_events": train_n,
            "no_train_events": no_train_n,
            "engine_events": engine_n,
            "cohort_total_events": train_n + no_train_n + engine_n,
            "avg_train_per_session": round(train_n / sessions, 2),
            "avg_no_train_per_session": round(no_train_n / sessions, 2),
            "role": role,
        }

    train_fixed = _cohort_block(2, 5, 60, 30, 8, "Perception retraining and policy development")
    val_fixed = _cohort_block(1, 3, 24, 15, 4, "Threshold/calibration freeze only (never reused in test)")

    def _build_tier(
        *,
        name: str,
        description: str,
        rho: float,
        test_crossings: int,
        test_sessions: int,
        test_train: int,
        test_no_train: int,
        test_engine: int,
    ) -> dict[str, Any]:
        test_blk = _cohort_block(
            test_crossings,
            test_sessions,
            test_train,
            test_no_train,
            test_engine,
            "Locked single-shot evaluation after val freeze",
        )
        m_actual = test_train / test_sessions
        deff_actual = round(1.0 + max(0.0, m_actual - 1.0) * rho, 4)
        n_eff_train = test_train / deff_actual
        eff_bound = round(1.0 - (0.05 ** (1.0 / n_eff_train)), 4)
        n_eff_int = math.floor(n_eff_train)
        return {
            "name": name,
            "description": description,
            "assumed_icc_rho": rho,
            "total_crossings": train_fixed["crossings"] + val_fixed["crossings"] + test_crossings,
            "total_sessions": train_fixed["sessions"] + val_fixed["sessions"] + test_sessions,
            "grand_total_events": train_fixed["cohort_total_events"] + val_fixed["cohort_total_events"] + test_blk["cohort_total_events"],
            "totals_by_class": {
                "train_events": train_fixed["train_events"] + val_fixed["train_events"] + test_train,
                "no_train_events": train_fixed["no_train_events"] + val_fixed["no_train_events"] + test_no_train,
                "engine_events": train_fixed["engine_events"] + val_fixed["engine_events"] + test_engine,
            },
            "cohorts": {"train": train_fixed, "val": val_fixed, "test": test_blk},
            "effective_test_power_metrics": {
                "actual_deff": deff_actual,
                "effective_test_trains_n_eff": round(n_eff_train, 2),
                "effective_zero_failure_95_upper_bound": eff_bound,
                "unconditional_mcnemar_power_p20_p005": _exact_unconditional_mcnemar_power(n_eff_int, 0.20, 0.005),
                "unconditional_mcnemar_power_p25_p005": _exact_unconditional_mcnemar_power(n_eff_int, 0.25, 0.005),
                "unconditional_mcnemar_power_observed_sync11_rate": _exact_unconditional_mcnemar_power(n_eff_int, 4.0 / 11.0, 0.0),
            },
        }

    tier_c1 = _build_tier(
        name="tier_c1_unclustered_10pct_bound",
        description="Unclustered (rho=0.0) minimum reaching <=10% one-sided 95% risk bound on test trains & controls.",
        rho=0.0,
        test_crossings=2,
        test_sessions=5,
        test_train=n_uncl_10,
        test_no_train=n_uncl_10,
        test_engine=8,
    )
    tier_c2 = _build_tier(
        name="tier_c2_cluster_adjusted_10pct_bound_primary",
        description="Recommended primary target (rho=0.05, ref DEFF=1.45): exact 98 + 43 + 94 = 235 total events.",
        rho=primary_rho,
        test_crossings=2,
        test_sessions=5,
        test_train=n_cl_10,
        test_no_train=n_cl_10,
        test_engine=8,
    )
    tier_c3 = _build_tier(
        name="tier_c3_cluster_adjusted_80pct_mcnemar_p20",
        description=f"High-power paired McNemar target (rho=0.05, >=80% effective power for 20%->0.5% premature opening reduction): 98 + 43 + 130 = 271 events.",
        rho=primary_rho,
        test_crossings=2,
        test_sessions=6,
        test_train=n_cl_mcnemar_p20 + 1,
        test_no_train=60,
        test_engine=8,
    )

    return {
        "structural_floor_critique": {
            "minimal_3crossing_6session_total": {
                "crossings": 3,
                "sessions": 6,
                "assumed_test_train_passages": 12,
                "assumed_test_no_train_controls": 6,
                "zero_premature_opening_95_upper_bound": _clopper_pearson_zero_failure_upper_95(12),
                "zero_false_closure_95_upper_bound": _clopper_pearson_zero_failure_upper_95(6),
                "mcnemar_power_p20_p005": _exact_unconditional_mcnemar_power(12, 0.20, 0.005),
                "mcnemar_power_observed_sync11_rate": _exact_unconditional_mcnemar_power(12, 4.0 / 11.0, 0.0),
            },
            "why_insufficient": (
                "A structural minimum of 3 crossings x 2 sessions (~12 test trains, ~6 test no_train clips) leaves 0/12 premature openings with a 22.09% one-sided 95% upper bound (39.30% on 0/6 false closures), gives only 1.87% two-sided McNemar power at p10=0.20 (24.37% at p10=4/11), and leaves only 1 crossing in val and test."
            ),
        },
        "exact_binomial_and_cluster_targets": {
            "intra_session_icc_assumed": primary_rho,
            "passages_per_session_assumed": ref_m,
            "cluster_design_effect": primary_deff,
            "zero_failure_95_upper_bound_10pct_unclustered_n": n_uncl_10,
            "zero_failure_95_upper_bound_5pct_unclustered_n": n_uncl_5,
            "unclustered_n_for_80pct_mcnemar_power_p20": n_mcnemar_p20,
            "cluster_adjusted_test_trains_for_10pct_bound": n_cl_10,
            "cluster_adjusted_test_trains_for_5pct_bound": n_cl_5,
            "cluster_adjusted_test_trains_for_80pct_mcnemar_p20": n_cl_mcnemar_p20,
            "unclustered_test_no_train_for_10pct_bound": n_uncl_10,
            "cluster_adjusted_test_no_train_for_10pct_bound": n_cl_10,
            "unclustered_29_mcnemar_power_p20_p005": _exact_unconditional_mcnemar_power(n_uncl_10, 0.20, 0.005),
            "unclustered_29_mcnemar_power_p25_p005": _exact_unconditional_mcnemar_power(n_uncl_10, 0.25, 0.005),
            "unclustered_29_mcnemar_power_observed_sync11_rate": _exact_unconditional_mcnemar_power(n_uncl_10, 4.0 / 11.0, 0.0),
            "icc_sensitivity_table": icc_sensitivity,
        },
        "reconciled_cohort_tiers": {
            "tier_c1_unclustered_10pct_bound": tier_c1,
            "tier_c2_cluster_adjusted_10pct_bound_primary": tier_c2,
            "tier_c3_cluster_adjusted_80pct_mcnemar_p20": tier_c3,
        },
        "recommended_three_cohort_design": {
            "total_crossings_target": 5,
            "total_sessions_target": 13,
            "total_events_target": tier_c2["grand_total_events"],
            "cohorts": tier_c2["cohorts"],
            "confounding_controls": [
                "Identical camera & microphone hardware per crossing across train, no_train, and engine cohorts.",
                "2x2 lighting x weather factorial balance with matched no_train controls inside every capture session.",
                "NTP/GPS sync + audible/visual slate clapper establishing sub-100 ms sync on 100% of dual-camera clips.",
                "Physical crossing-box occupancy ground truth (calibrated overhead camera or inductive/radar logger).",
                "Minimum >=10 s pre-T0 approach buffer AND >=15 s post-T4 empty-track tail buffer per recording so 1.5 s dwell + 2.0 s reopening stroke can be verified on real footage.",
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


def _extract_back_stream_metrics(jsonl_path: Path, threshold: float = 0.35) -> dict[str, Any]:
    """Extract deterministic non-raw clearance timing metrics from a cached *_back.jsonl."""
    det_times: list[float] = []
    rear_times: list[float] = []
    body_or_rear_times: list[float] = []
    max_ts = 0.0
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        ts = float(rec.get("timestamp_sec", rec.get("timestamp_s", 0.0)))
        if ts > max_ts:
            max_ts = ts
        has_any = False
        has_rear = False
        for det in rec.get("detections", []):
            if float(det.get("confidence", 0.0)) < threshold:
                continue
            lbl = str(det.get("label", "")).lower()
            if lbl in {"front", "train_front", "side", "train_body", "carriage", "locomotive", "train_side", "rear", "train_rear", "last_carriage", "train_tail", "tail", "end_of_train"}:
                has_any = True
            if lbl in {"rear", "train_rear", "last_carriage", "train_tail", "tail", "end_of_train"}:
                has_rear = True
        if has_any:
            det_times.append(ts)
            body_or_rear_times.append(ts)
        if has_rear:
            rear_times.append(ts)

    det_times.sort()
    rear_times.sort()
    gaps = [round(det_times[i + 1] - det_times[i], 3) for i in range(len(det_times) - 1)] if len(det_times) > 1 else []
    m2_rear_pair_t: float | None = None
    for i in range(len(rear_times) - 1):
        if (rear_times[i + 1] - rear_times[i]) <= 1.0:
            m2_rear_pair_t = round(rear_times[i + 1], 4)
            break

    # M3 candidate: dense transit (>=20 dets, max gap <= 3.5 s), >=2 rear frames, then post-last-det silence >= 1.5 s
    m3_candidate_t: float | None = None
    last_det_t = round(det_times[-1], 4) if det_times else None
    max_gap = max(gaps) if gaps else None
    if len(det_times) >= 20 and (max_gap is None or max_gap <= 3.5) and len(rear_times) >= 2 and last_det_t is not None:
        m3_candidate_t = round(last_det_t + 1.5, 4)

    return {
        "det_count": len(det_times),
        "rear_det_count": len(rear_times),
        "rear_timestamps_s": [round(t, 4) for t in rear_times],
        "max_internal_gap_s": max_gap,
        "last_det_s": last_det_t,
        "stream_end_s": round(max_ts, 4),
        "m2_two_rear_pair_t_s": m2_rear_pair_t,
        "m3_monotonic_post_rear_clear_t_s": m3_candidate_t,
    }


def evaluate_autonomous_reopening_and_clearance_methods(
    repo_root: Path,
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    """Forensic investigation of 0/11 sync11 reopenings and comparison of M1-M5 clearance methods."""
    traces_path = repo_root / "results/exploratory_v2/replays/real_sync11_v3_traces.json"
    exp_d_path = repo_root / "results/exploratory_v2/experiments/exp_d_back_departure.json"
    m3_manifest_path = repo_root / "data/manifests/m3_multimodal_replay_manifest.json"
    if not (traces_path.is_file() and exp_d_path.is_file() and m3_manifest_path.is_file()):
        return {"available": False, "reason": "missing_exploratory_trace_or_manifest_artifacts"}

    traces = _read_json(traces_path)["traces"]
    exp_d = _read_json(exp_d_path)
    m3_manifest = {e["event_id"]: e for e in _read_json(m3_manifest_path)["events"]}

    state_counts = Counter(v["final_crossing_state"] for v in traces.values())
    eof_failsafe_events = sorted(
        ek for ek, v in traces.items() if v["final_crossing_state"] == "FAULT_FAIL_SAFE"
    )
    l1_closed_events = sorted(
        ek
        for ek, v in traces.items()
        if v["final_crossing_state"] in ("GATE_CLOSING", "CROSSING_OCCUPIED", "TRAIN_DEPARTING")
    )
    idle_events = sorted(ek for ek, v in traces.items() if v["final_crossing_state"] == "IDLE")

    per_event_back: list[dict[str, Any]] = []
    back27_by_key = {row["event_id"]: row for row in exp_d["back27_local_clock_summary"]}
    post_t4_tails: list[float] = []
    insufficient_post_t4_for_3_5s_reopen = 0
    for ek, brow in sorted(back27_by_key.items()):
        t4_b = brow.get("T4_back_s")
        if t4_b is None:
            continue
        back_cache_rel = m3_manifest[ek]["back_cache_path"]
        stats = _extract_back_stream_metrics(repo_root / back_cache_rel)
        tail_after_t4 = round(float(brow["back_dur_s"]) - float(t4_b), 3)
        post_t4_tails.append(tail_after_t4)
        ref_end = max(float(t4_b), stats["last_det_s"] or 0.0)
        rem_after_ref = float(brow["back_dur_s"]) - ref_end
        if rem_after_ref < 3.5:
            insufficient_post_t4_for_3_5s_reopen += 1
        m2_premature = bool(stats["m2_two_rear_pair_t_s"] is not None and stats["m2_two_rear_pair_t_s"] < float(t4_b))
        m3_premature = bool(
            stats["m3_monotonic_post_rear_clear_t_s"] is not None
            and stats["m3_monotonic_post_rear_clear_t_s"] < float(t4_b)
        )
        per_event_back.append(
            {
                "event_key": ek,
                "is_sync11": bool(brow["is_sync11"]),
                "T4_back_s": t4_b,
                "back_dur_s": brow["back_dur_s"],
                "post_t4_tail_s": tail_after_t4,
                "det_count": stats["det_count"],
                "rear_det_count": stats["rear_det_count"],
                "max_internal_gap_s": stats["max_internal_gap_s"],
                "last_det_s": stats["last_det_s"],
                "m2_two_rear_pair_t_s": stats["m2_two_rear_pair_t_s"],
                "m2_premature_vs_T4": m2_premature,
                "m3_monotonic_post_rear_clear_t_s": stats["m3_monotonic_post_rear_clear_t_s"],
                "m3_premature_vs_T4": m3_premature,
            }
        )

    sync11_back = [r for r in per_event_back if r["is_sync11"]]
    sync11_gaps = [r["max_internal_gap_s"] for r in sync11_back if r["max_internal_gap_s"] is not None]
    post_t4_sorted = sorted(post_t4_tails)
    sync11_prem = exp_d["sync11_premature_opening_counts"]

    # Deterministic closed-loop simulation comparison across M1-M5 on adversarial/nominal stress cases
    from railway_detection.fusion.collector import MultimodalFrame
    from railway_detection.fusion.decision_engine_v3_four_layer import MultimodalDecisionEngineV3FourLayer
    from railway_detection.fusion.evidence import Detection, EvidenceRecord, EvidenceStatus, Modality, OccupancyEvidence, OccupancyState
    from railway_detection.fusion.rules_v3_four_layer import DeparturePolicyMode

    def _run_m5_simulation(*, with_occ_clear: bool, post_t4_s: float) -> dict[str, Any]:
        eng = MultimodalDecisionEngineV3FourLayer(
            departure_mode=DeparturePolicyMode.CONSERVATIVE_POSITIVE,
            require_occupancy_for_reopen=True,
        )
        t_ticks = [round(i * 0.2, 1) for i in range(int((14.0 + post_t4_s) / 0.2) + 1)]
        final_rec = None
        reopened = False
        premature = False
        t4_true = 14.0
        for t in t_ticks:
            vrecs = []
            c1_dets = (Detection("front", 0.9, (10, 10, 50, 50)),) if 0.0 <= t <= 3.0 else ()
            vrecs.append(EvidenceRecord(t, "camera_1", Modality.VISION, True, c1_dets))
            if 5.0 <= t <= 12.6:
                c2_dets = (Detection("side", 0.85, (20, 20, 120, 120)),)
            elif 12.8 <= t <= t4_true:
                c2_dets = (Detection("rear", 0.88, (40, 20, 100, 100)),)
            else:
                c2_dets = ()
            vrecs.append(EvidenceRecord(t, "camera_2", Modality.VISION, True, c2_dets))
            orecs = ()
            if with_occ_clear:
                occ_state = OccupancyState.OCCUPIED if t <= t4_true else OccupancyState.CLEAR
                orecs = (OccupancyEvidence(t, "occ_sensor", occ_state, 0.99, True, EvidenceStatus.POSITIVE),)
            frame = MultimodalFrame(
                master_timestamp_s=t,
                vision_records=tuple(vrecs),
                audio_records=(EvidenceRecord(t, "audio_1", Modality.AUDIO, True, ()),),
                occupancy_records=orecs,
                source_availability={"camera_1": True, "camera_2": True, "audio_1": True},
            )
            rec = eng.evaluate_frame(frame, "m5_sim")
            final_rec = rec
            if rec.resulting_gate_state in ("OPENING", "OPEN") and t < t4_true and rec.previous_gate_state in ("CLOSING", "CLOSED"):
                premature = True
            if rec.resulting_state == "IDLE" and t > t4_true:
                reopened = True
        return {
            "final_state": final_rec.resulting_state if final_rec else "NONE",
            "final_gate_state": final_rec.resulting_gate_state if final_rec else "NONE",
            "reopened_cleanly": reopened,
            "premature_opening": premature,
        }

    m5_nominal = _run_m5_simulation(with_occ_clear=True, post_t4_s=8.0)
    m5_no_occ = _run_m5_simulation(with_occ_clear=False, post_t4_s=8.0)
    m5_short_tail = _run_m5_simulation(with_occ_clear=True, post_t4_s=1.4)

    return {
        "schema_version": "autonomous-reopening-clearance-audit/1.0",
        "sync11_v3_outcome_breakdown": {
            "total_sync11": len(traces),
            "l1_approach_closures": len(l1_closed_events),
            "l1_closed_event_ids": l1_closed_events,
            "eof_stream_mismatch_failsafe_clamps": len(eof_failsafe_events),
            "eof_failsafe_event_ids": eof_failsafe_events,
            "never_closed_idle": len(idle_events),
            "idle_event_ids": idle_events,
            "completed_automatic_reopenings": 0,
            "state_histogram": dict(sorted(state_counts.items())),
        },
        "root_causes_of_zero_real_reopenings": {
            "1_zero_rear_labels_in_sync11_and_long_dropouts": {
                "sync11_events_with_rear_dets": 0,
                "sync11_max_internal_back_dropout_gap_s": max(sync11_gaps) if sync11_gaps else None,
                "reason": "Pre-db40305 unrotated -90 deg camera_2 streams produced 0/11 'rear' boxes and up to 43.2 s internal blind gaps (event_017), triggering RULE_L4_BACK_SPARSE_DROPOUT_HOLD.",
            },
            "2_mid_passage_false_rear_boxes_on_unsynced_clips": {
                "m2_naive_rear_pair_premature_events": [r["event_key"] for r in per_event_back if r["m2_premature_vs_T4"]],
                "example_event_008": "2 consecutive rear dets at 21.6-22.2 s occur 39.0 s before true T4_back=61.2 s; rear alone cannot safely authorize reopening without sustained side/body cessation.",
                "example_event_004": "Intermittent rear dets at 8.0, 19.0, 44.0 s occur up to 68.8 s before T4_back=76.8 s.",
            },
            "3_post_t4_clip_truncation_prevents_3_5s_reopen_cycle": {
                "t4_annotated_events": len(post_t4_tails),
                "post_t4_tail_min_s": post_t4_sorted[0] if post_t4_sorted else None,
                "post_t4_tail_median_s": round(post_t4_sorted[len(post_t4_sorted) // 2], 3) if post_t4_sorted else None,
                "post_t4_tail_max_s": post_t4_sorted[-1] if post_t4_sorted else None,
                "clips_shorter_than_3_5s_required_dwell_plus_open": insufficient_post_t4_for_3_5s_reopen,
                "required_dwell_plus_open_s": 3.5,
            },
            "4_missing_physical_occupancy_sensor": {
                "physical_occupancy_sensors_present": 0,
                "impact": "Even with upright dense Session 2 back detections (events 021-023: 208-230 dets, 4-14 rear boxes near T4), missing physical occupancy sensors force V3 to remain CLOSED in REAR_CONFIRMED/TRAIN_DEPARTING (fail-closed hold != autonomous completion).",
            },
        },
        "method_comparison_m1_to_m5": [
            {
                "method_id": "M1_disappearance_timer",
                "description": "Legacy V2 or V3_GUARDED_DISAPPEARANCE opening after bounded negative back frames without positive tail.",
                "real_sync11_premature_openings": f"V2={sync11_prem['V2_RULE_3B_3C']}/11, V3_GUARDED={sync11_prem['V3_GUARDED_DISAPPEARANCE']}/11",
                "real_t4_corpus_premature": 4,
                "handles_43s_optical_dropout": False,
                "verdict": "UNSAFE_REJECTED",
            },
            {
                "method_id": "M2_naive_rear_label_only",
                "description": ">=2 consecutive YOLO rear boxes on camera_2 without side/body cessation or occupancy verification.",
                "real_sync11_premature_openings": "0/11 (only because rear=0 on sync11)",
                "real_t4_corpus_premature": sum(1 for r in per_event_back if r["m2_premature_vs_T4"]),
                "premature_events": [r["event_key"] for r in per_event_back if r["m2_premature_vs_T4"]],
                "handles_decoupled_dark_obstacle": False,
                "verdict": "UNSAFE_ALONE_REJECTED",
            },
            {
                "method_id": "M3_monotonic_transit_and_post_rear_silence",
                "description": "Requires dense transit tracking (>=20 dets, max gap <=3.5 s) + >=2 rear/last_carriage boxes + cessation of side/front detections + >=1.5 s post-last-detection silence.",
                "real_t4_corpus_premature": sum(1 for r in per_event_back if r["m3_premature_vs_T4"]),
                "qualified_clean_departure_events": [r["event_key"] for r in per_event_back if r["m3_monotonic_post_rear_clear_t_s"] is not None],
                "handles_event_008_false_rear": True,
                "handles_decoupled_dark_obstacle": False,
                "verdict": "STRONGEST_VISION_PREREQUISITE_LAYER",
            },
            {
                "method_id": "M4_multicamera_spatiotemporal_conservation",
                "description": "Requires ordered L1 front -> L2 moving side -> L4 M3 exit -> quiet L3 audio without independent occupancy sensor.",
                "real_sync11_premature_openings": "0/11",
                "real_sync11_completed_reopenings": "0/11",
                "handles_unlit_or_occluded_island_obstacle": False,
                "verdict": "NECESSARY_FUSION_INSUFFICIENT_FOR_AUTONOMOUS_REOPEN",
            },
            {
                "method_id": "M5_v3_plus_m3_and_independent_occupancy_sensor",
                "description": "V3_CONSERVATIVE_POSITIVE + M3 monotonic transit/post-rear silence + independent physical island OccupancyState.CLEAR + >=15 s post-T4 recording window.",
                "real_sync11_premature_openings": "0/11 (holds fail-closed safely)",
                "synthetic_nominal_with_occ_clear": m5_nominal,
                "synthetic_without_occ_sensor": m5_no_occ,
                "synthetic_truncated_1_4s_post_t4": m5_short_tail,
                "verdict": "REQUIRED_TARGET_ARCHITECTURE",
            },
        ],
        "per_event_back_clearance_audit": per_event_back,
    }


def generate_targeted_collection_plan() -> dict[str, Any]:
    """Targeted additional-data collection plan required for genuine OOD Phase 12 splits."""
    power = calculate_option_c_statistical_power_and_cohort_design()
    primary = power["reconciled_cohort_tiers"]["tier_c2_cluster_adjusted_10pct_bound_primary"]
    return {
        "why_current_27_cannot_form_leakage_safe_3way_split": [
            "crossing_id: all 27/27 events share crossing_A (pigeonhole minimum = 3 disjoint crossings for train/val/test).",
            "true_capture_session: only 2 distinct physical capture dates exist (2026-09-14: 20 train events; 2026-10-04: 3 night train + 3 no_train + 1 engine).",
            "hardware_and_class_confound: 100% of negative (no_train) and engine controls come exclusively from Session 2 (night/dusk with iPad 10th-gen back camera), whereas 20/23 train events come from daytime Session 1 (iPhone 15 Pro Max back camera).",
            "left_and_right_censoring: retrospective approach recordings begin with train already visible (0/23 un-censored distant T0/T1), engine_events/event_001 is right-censored at t=9.80s, 21/22 T4-annotated clips truncate <3.5s after passage/last-det, and 0/27 have physical occupancy sensors.",
        ],
        "minimum_new_collection_requirements": {
            "independent_crossings": {
                "minimum_new_crossings": 4,
                "target_total_crossings": f">= {primary['total_crossings']} disjoint crossings ({primary['cohorts']['train']['crossings']} train, {primary['cohorts']['val']['crossings']} val, {primary['cohorts']['test']['crossings']} test; vs invalid 3-crossing floor)",
                "rationale": "Eliminates background geometry, barrier appearance, acoustic reverberation, and crossing-specific false-alarm leakage while preventing single-crossing test fragility.",
            },
            "minimum_balanced_sessions": {
                "minimum_sessions_per_crossing": "2-3 balanced sessions per crossing spanning 2x2 Day/Night x Clear/Adverse-Weather strata",
                "target_total_sessions": primary["total_sessions"],
                "target_grand_total_events_primary": primary["grand_total_events"],
                "cohort_event_counts": {
                    role: primary["cohorts"][role]["cohort_total_events"]
                    for role in ("train", "val", "test")
                },
            },
            "hardware_and_synchronization_protocol": [
                "Use identical camera hardware across train/no_train/engine cohorts within each session (no mid-cohort iPhone-to-iPad swap).",
                "Lock orientation metadata upright or maintain strict orthogonal rotation tags; verify NTP/GPS clock sync plus an audible/visual slate clapper at session start & end to establish sub-100ms front-back sync across ALL events (eliminating the 15 non-CALIBRATION_SUPPORTED events).",
                "Treat 84–211 m upstream distance (7.6 s closure budget at 40–100 km/h) as an unvalidated kinematic engineering estimate until verified via site-specific lens focal length, small-object pixel height (>= 24–32 px at 416 px), curvature, >= 10 s pre-T0 buffer, AND >= 15 s post-T4 tail buffer.",
                "Record independent occupancy ground truth (calibrated overhead crossing camera or inductive/radar occupancy logger) plus dedicated lateral crossing-box FOV.",
            ],
        },
        "statistical_power_and_sample_size_recalculation": power,
        "interim_scientifically_defensible_path": {
            "recommended_now": "Honor active researcher decision SPLIT-DECISION-OPTION-A-2026-11-09 (27-event full-cohort descriptive benchmark via Stage-2.1 review + descriptive execution authorization), reporting exact Wilson/Clopper-Pearson 95% CIs and prohibiting cross-crossing generalization claims.",
            "do_not": "Do NOT relabel any partition of these 27 events as leakage_safe=true just to unlock Phase 12 held-out evaluation.",
        },
    }


def _sha256_or_none(path: Path) -> str | None:
    if not path.is_file():
        return None
    require_media_authorization(path, "HASH_RAW_MEDIA")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_research_ownership_and_authorization_workflow(repo_root: Path) -> dict[str, Any]:
    """Audit research ownership vs independent peer-review & fail-closed governance gates."""
    allowlist_path = repo_root / "data/ground_truth/authorized_reviewers.json"
    allowlist_data = _read_json(allowlist_path) if allowlist_path.is_file() else {}
    allowlisted = list(allowlist_data.get("authorized_reviewers", []))

    recorded_specs = [
        (
            "LEG-EXEC",
            "data/governance/leg_exec_authorization.json",
            "RESEARCH_OWNER_SUFFICIENT",
            "Legacy review invalidation execution across 27 stale 7.0.0 records",
        ),
        (
            "ADOPTED-AI-REFERENCE",
            "docs/generated/professor_evidence/mission43/RESEARCHER_ANNOTATION_ADOPTION.json",
            "RESEARCH_OWNER_SUFFICIENT",
            "Research owner adoption of active 27 AI-assisted event references (exploratory only)",
        ),
        (
            "PROTOCOL-CHOICE",
            "data/manifests/phase12_protocol_decision.json",
            "RESEARCH_OWNER_SUFFICIENT",
            "Primary premature-opening metric window (M4 first_blocked_to_t4_clearance) & censoring profile",
        ),
        (
            "R04-SYNC-SCOPE",
            "data/manifests/phase12_r04_scope_decision.json",
            "RESEARCH_OWNER_SUFFICIENT",
            "Acceptance of 11 CALIBRATION_SUPPORTED dual-camera events & 16 independent-camera events",
        ),
        (
            "POLICY-ADOPTION-V2",
            "docs/generated/research_decisions/POLICY_ADOPTION_V2_20261109.md",
            "RESEARCH_OWNER_SUFFICIENT",
            "Experimental policy v2 adoption (v1 frozen baseline retained)",
        ),
        (
            "SPLIT-DECISION-OPTION-A",
            "docs/generated/research_decisions/SPLIT_DECISION_OPTION_A_20261109.md",
            "RESEARCH_OWNER_SUFFICIENT",
            "Full 27-event single-crossing descriptive cohort scope (no leaky train/val/test split)",
        ),
    ]
    recorded_owner_authorizations = []
    for decision_id, rel_path, tier, purpose in recorded_specs:
        full_path = repo_root / rel_path
        recorded_owner_authorizations.append(
            {
                "decision_id": decision_id,
                "path": rel_path,
                "present_on_disk": full_path.is_file(),
                "sha256": _sha256_or_none(full_path),
                "authority_tier": tier,
                "purpose": purpose,
            }
        )

    reviews_root = repo_root / "data/ground_truth/reviews"
    stage21_active_count = 0
    if reviews_root.is_dir():
        for rev_file in sorted(reviews_root.rglob("*_review.json")):
            try:
                rev_json = _read_json(rev_file)
                if rev_json.get("schema_version") == "8.1.0-stage2.1" and rev_json.get("invalidation") is None:
                    stage21_active_count += 1
            except (OSError, json.JSONDecodeError):
                pass

    gates = [
        {
            "gate_id": "AUTH-MEDIA-ACCESS",
            "target_path": "data/governance/AUTH-MEDIA-ACCESS.json",
            "schema_version": "phase5-media-access-authorization/2",
            "authority_tier": "RESEARCH_OWNER_SUFFICIENT",
            "eligible_signers": [r for r in allowlisted if r == "raihankabirrahu@gmail.com"] or allowlisted[:1],
            "professor_signature_required": False,
            "current_on_disk_status": (
                "PRESENT" if (repo_root / "data/governance/AUTH-MEDIA-ACCESS.json").is_file() else "ABSENT_NOT_SIGNED_BY_OWNER"
            ),
            "why_gate_cannot_be_bypassed": (
                "Enforced on every data/raw/ media byte access (media_guard.py); dataset owner can sign directly using template."
            ),
        },
        {
            "gate_id": "STAGE21_PRIMARY_REVIEW",
            "target_path": "data/ground_truth/reviews/<cohort>/event_XXX_review.json",
            "schema_version": "8.1.0-stage2.1",
            "authority_tier": "RESEARCH_OWNER_SUFFICIENT",
            "eligible_signers": allowlisted,
            "professor_signature_required": False,
            "current_on_disk_status": f"{stage21_active_count}/27 valid Stage-2.1 records on disk (27 legacy 7.0.0 records invalidated)",
            "why_gate_cannot_be_bypassed": (
                "Requires >=30 s genuine raw media review per event and live reviewer_observed_media_hashes (promotion_gate.py); synthetic/bulk-stamped records fail integrity checks."
            ),
        },
        {
            "gate_id": "STAGE21_RD043_SECOND_REVIEW",
            "target_path": "data/ground_truth/reviews/<cohort>/event_XXX_review.json (second_review_of)",
            "schema_version": "8.1.0-stage2.1",
            "authority_tier": "INDEPENDENT_SECOND_REVIEWER_REQUIRED",
            "eligible_signers": [r for r in allowlisted if r != "raihankabirrahu@gmail.com"],
            "professor_signature_required": False,
            "current_on_disk_status": "PENDING_TRIGGERED_EVENTS (mandatory when T3/T4 interpreted on engine_events or UNCERTAIN/flag)",
            "why_gate_cannot_be_bypassed": (
                "Scientific peer-review integrity (RD-043 & BATCH_SAME_REVIEWER_SECOND_REVIEW): primary reviewer cannot second-review their own uncertain/engine adjudication."
            ),
        },
        {
            "gate_id": "COHORT_APPROVAL_AND_PROMOTION_RECEIPT",
            "target_path": "data/governance/stage21_promotion_receipt.json",
            "schema_version": "phase12-stage21-promotion-receipt/2",
            "authority_tier": "DERIVED_MACHINE_VERIFIED_ARTIFACT",
            "eligible_signers": ["readiness_cli (after owner + independent second reviews)"],
            "professor_signature_required": False,
            "current_on_disk_status": (
                "PRESENT" if (repo_root / "data/governance/stage21_promotion_receipt.json").is_file() else "ABSENT_WAITING_STAGE21_REVIEWS"
            ),
            "why_gate_cannot_be_bypassed": (
                "Cryptographically binds all active 8.1.0-stage2.1 reviews, allowlist, inventory, active proposals, and live media SHA-256 verification."
            ),
        },
        {
            "gate_id": "AUTH-DESCRIPTIVE-EVAL-EXEC",
            "target_path": "data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json",
            "schema_version": "phase5-descriptive-eval-execution-authorization/1",
            "authority_tier": "RESEARCH_OWNER_SUFFICIENT",
            "eligible_signers": [r for r in allowlisted if r == "raihankabirrahu@gmail.com"] or allowlisted[:1],
            "professor_signature_required": False,
            "current_on_disk_status": (
                "PRESENT"
                if (repo_root / "data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json").is_file()
                else "ABSENT_WAITING_PROMOTION_RECEIPT_AND_OWNER_SIGN"
            ),
            "why_gate_cannot_be_bypassed": (
                "Binds promotion_receipt_sha256, evaluation_manifest_sha256, protocol_sha256, metric_scope_sha256, and model_config_provenance_sha256 before official descriptive cohort replay."
            ),
        },
        {
            "gate_id": "EVENT_SPLIT_DECISION",
            "target_path": "data/splits/phase12_event_split_decision.json",
            "schema_version": "phase12-event-split-decision/1",
            "authority_tier": "RESEARCH_OWNER_SUFFICIENT",
            "eligible_signers": [r for r in allowlisted if r == "raihankabirrahu@gmail.com"] or allowlisted[:1],
            "professor_signature_required": False,
            "current_on_disk_status": (
                "PRESENT"
                if (repo_root / "data/splits/phase12_event_split_decision.json").is_file()
                else "INTENTIONALLY_ABSENT_UNDER_OPTION_A (SPLIT-DECISION-OPTION-A-2026-11-09)"
            ),
            "why_gate_cannot_be_bypassed": (
                "Research owner chose Option A descriptive cohort evaluation because 27 single-crossing events cannot yield a leakage-safe 3-way split; reserved for Option C multi-crossing capture."
            ),
        },
        {
            "gate_id": "EVAL_INPUT_MANIFEST_AND_EVAL_AUTH",
            "target_path": "data/manifests/phase12_evaluation_inputs.json + data/governance/eval_authorization.json",
            "schema_version": "phase12-evaluation-inputs/1 + phase12-eval-authorization/1",
            "authority_tier": "DERIVED_MANIFEST + RESEARCH_OWNER_SUFFICIENT_AFTER_STAGE21",
            "eligible_signers": [r for r in allowlisted if r == "raihankabirrahu@gmail.com"] or allowlisted[:1],
            "professor_signature_required": False,
            "current_on_disk_status": (
                "READY"
                if (repo_root / "data/governance/eval_authorization.json").is_file()
                else "HELD_BY_OPTION_A_UNTIL_STAGE21_AND_OPTION_C"
            ),
            "why_gate_cannot_be_bypassed": (
                "Requires real Stage-2.1 promoted reviews, clean phase12-replay-evidence/1 inputs (non-cache), split decision, and bound owner statement."
            ),
        },
    ]

    return {
        "schema_version": "research-ownership-authorization-audit/1.0",
        "ownership_structure": {
            "research_owner": {
                "identity": "raihankabirrahu@gmail.com",
                "role": "Independent Research Owner & Dataset Controller",
                "holds_professor_project_authorization": True,
                "professor_technical_signoff_required": False,
            },
            "independent_second_reviewer": {
                "identity": "elaf85777@gmail.com",
                "role": "Independent Peer Reviewer for RD-043 Second Review & Adjudication",
                "enforced_by": "promotion_gate.validate_batch_for_promotion (BATCH_SAME_REVIEWER_SECOND_REVIEW)",
            },
            "academic_professor_supervisor": {
                "role": "Academic Paper Preparation & Publication Submission from Verified Research Handover",
                "technical_signoff_required": False,
                "deliverable_path": "docs/generated/FINAL_PROFESSOR_RESEARCH_HANDOVER.md",
            },
        },
        "allowlisted_identities": allowlisted,
        "recorded_owner_authorizations": recorded_owner_authorizations,
        "recorded_owner_authorizations_present_count": sum(
            1 for r in recorded_owner_authorizations if r["present_on_disk"]
        ),
        "authorization_workflow_gates": gates,
    }


def evaluate_option_a_complete_descriptive_study_and_verification(repo_root: Path) -> dict[str, Any]:
    """Compile and independently cross-verify the complete Option A 27-event descriptive results."""
    required = {
        "master_v2": repo_root / "results/exploratory_v2/MASTER_V2_SUMMARY.json",
        "exp_n_csv": repo_root / "results/exploratory_v2/experiments/exp_n_event_matrix.csv",
        "exp_j": repo_root / "results/exploratory_v2/experiments/exp_j_temporal_vs_stateless.json",
        "exp_i": repo_root / "results/exploratory_v2/experiments/exp_i_complete_system.json",
        "stats": repo_root / "results/exploratory_v2/analysis/statistical_comparisons.json",
        "exp_r_val": repo_root / "results/exploratory_v2/optimization_and_stress/exp_r_independent_validation.json",
        "m43_cohort": repo_root / "docs/generated/professor_evidence/mission43/ACTUAL_FULL_COHORT_RESULTS.json",
        "m43_adopt": repo_root / "docs/generated/professor_evidence/mission43/RESEARCHER_ANNOTATION_ADOPTION.json",
        "leakage": repo_root / "results/dataset_audit/vision_audio_leakage_audit.json",
    }
    missing = [name for name, p in required.items() if not p.is_file()]
    if missing:
        return {
            "schema_version": "option-a-complete-descriptive-verification/1.0",
            "status": "ARTIFACTS_ABSENT_IN_TEMP_TREE",
            "missing_artifacts": missing,
            "independent_verification_passed": False,
            "discrepancy_count": len(missing),
        }

    master_v2 = _read_json(required["master_v2"])
    exp_j = _read_json(required["exp_j"])
    exp_i = _read_json(required["exp_i"])
    stats = _read_json(required["stats"])
    exp_r_val = _read_json(required["exp_r_val"])
    m43_cohort = _read_json(required["m43_cohort"])
    m43_adopt = _read_json(required["m43_adopt"])
    leakage = _read_json(required["leakage"])
    with required["exp_n_csv"].open(encoding="utf-8", newline="") as handle:
        exp_n_rows = list(csv.DictReader(handle))

    # Recompute metrics from raw CSV / per-event lists independently
    csv_train_closures = sum(
        1 for r in exp_n_rows if r["event_type"] == "REAL_WORLD_TRAIN_EVENT" and r["closure_decision"] == "True"
    )
    csv_nt_fp = sum(
        1 for r in exp_n_rows if r["event_type"] == "REAL_WORLD_NO_TRAIN" and r["closure_decision"] == "True"
    )
    csv_eng_fp = sum(
        1 for r in exp_n_rows if r["event_type"] == "REAL_WORLD_ENGINE_ONLY" and r["closure_decision"] == "True"
    )
    csv_s11_prem_v2 = sum(
        1 for r in exp_n_rows if r["is_sync11"] == "True" and r["v2_premature_opening_vs_T4"] == "True"
    )
    csv_s11_prem_v3 = sum(
        1 for r in exp_n_rows if r["is_sync11"] == "True" and r["v3_premature_opening_vs_T4"] == "True"
    )

    exp_a = master_v2["exp_a_summary"]
    exp_c = master_v2["exp_c_summary"]
    exp_d_prem = master_v2["exp_d_premature_counts"]
    m43_cm = m43_cohort["audio_event_reference_metrics"]["confusion_matrix"]
    loeo_base = exp_r_val["reproduced_published_loeo"]["baseline_metrics"]
    loeo_oof = exp_r_val["reproduced_published_loeo"]["oof_metrics"]
    v705 = leakage["vision_705d388743ea"]["split_image_counts"]
    vgrp = leakage["vision_session_grouped_candidate"]["audit"]["temporal_session_sweeps"]
    vgrp_600 = next(r for r in vgrp if r["gap_s"] == 600.0)
    agrp = leakage["audio_v3_stem_grouped_candidate"]

    checks = [
        ("adopted_event_count_equals_27", len(exp_n_rows) == 27 and len(m43_adopt["adopted_active_annotations"]) == 27 and m43_cohort["physical_events"] == 27, 27, len(exp_n_rows)),
        ("v3_train23_closures_cross_match", csv_train_closures == exp_a["train_events_triggered"] == exp_j["policies"]["v3_conservative"]["b4_train23_closures"] == exp_i["causal_vs_backfill_b4_train23_closures"]["causal"], csv_train_closures, exp_a["train_events_triggered"]),
        ("v3_no_train3_fp_cross_match", csv_nt_fp == exp_a["no_train_false_closures"] == exp_j["policies"]["v3_conservative"]["b4_no_train3_false_closures"], 0, csv_nt_fp),
        ("v3_engine1_fp_zero", csv_eng_fp == 0 and exp_a["engine_only_triggered"] is False, 0, csv_eng_fp),
        ("stateless_union_mcnemar_cross_match", exp_j["policies"]["stateless_union"]["b4_no_train3_false_closures"] == stats["exp_j_no_train_fp_mcnemar"]["b01_a_wrong_b_right"] == 3, 3, stats["exp_j_no_train_fp_mcnemar"]["b01_a_wrong_b_right"]),
        ("sync11_v2_premature_openings_cross_match", csv_s11_prem_v2 == exp_d_prem["V2_RULE_3B_3C"] == 4, 4, csv_s11_prem_v2),
        ("sync11_v3_premature_openings_cross_match", csv_s11_prem_v3 == exp_d_prem["V3_CONSERVATIVE_POSITIVE"] == 0, 0, csv_s11_prem_v3),
        ("audio23_confusion_matrix_m43_vs_v2_match", [m43_cm["tp"], m43_cm["fp"], m43_cm["fn"], m43_cm["tn"]] == [exp_c["TP"], exp_c["FP"], exp_c["FN"], exp_c["TN"]] == [loeo_base["tp"], loeo_base["fp"], loeo_base["fn"], loeo_base["tn"]], [exp_c["TP"], exp_c["FP"], exp_c["FN"], exp_c["TN"]], [m43_cm["tp"], m43_cm["fp"], m43_cm["fn"], m43_cm["tn"]]),
        ("audio_windows_2600_cross_match", m43_cohort["audio_windows"] == exp_r_val["corpus_verification"]["n_total_windows"] == 2600, 2600, exp_r_val["corpus_verification"]["n_total_windows"]),
        ("loeo_oof_counts_exact", [loeo_oof["tp"], loeo_oof["fp"], loeo_oof["tn"], loeo_oof["fn"]] == [8, 4, 6, 5], [8, 4, 6, 5], [loeo_oof["tp"], loeo_oof["fp"], loeo_oof["tn"], loeo_oof["fn"]]),
        ("vision_v1_total_images_3157_match", v705["train"] + v705["val"] + v705["test"] == 3157 and vgrp_600["crossing_timestamped_sessions"] == 0, 3157, v705["train"] + v705["val"] + v705["test"]),
        ("audio_v3_grouped_zero_stem_leakage", agrp["cross_split_positive_stem_count"] == 0 and agrp["positive_recordings_in_cross_split_stems"] == 0, 0, agrp["cross_split_positive_stem_count"]),
    ]

    verification_items = [
        {"check_id": cid, "passed": bool(passed), "expected": exp_v, "observed": obs_v}
        for cid, passed, exp_v, obs_v in checks
    ]
    discrepancies = [c for c in verification_items if not c["passed"]]

    policy_comparison = []
    for pkey, label in (
        ("stateless_union", "Stateless Union (any single modality frame)"),
        ("stateless_vision_rule2", "Stateless Vision Rule 2"),
        ("v1", "V1 Rule 3 Disappearance"),
        ("v2", "V2 Rule 3B/3C Disappearance (adopted experimental baseline)"),
        ("v3_conservative", "V3 Four-Layer Conservative Positive (target engine)"),
    ):
        pdata = exp_j["policies"][pkey]
        tr_c = pdata["b4_train23_closures"]
        nt_c = pdata["b4_no_train3_false_closures"]
        ill = sum(1 for r in pdata["b4_per_event"] if not r.get("transition_legal", True))
        policy_comparison.append(
            {
                "policy_id": pkey,
                "label": label,
                "train23_closures": tr_c,
                "train23_closure_rate": round(tr_c / 23.0, 4),
                "train23_wilson_95_ci": list(_wilson_ci_95(tr_c, 23)),
                "no_train3_false_closures": nt_c,
                "sync11_closures": pdata["sync11_closures"],
                "sync11_premature_openings_vs_T4": pdata["sync11_premature_openings_vs_T4"],
                "b4_illegal_transition_events": ill,
            }
        )

    return {
        "schema_version": "option-a-complete-descriptive-verification/1.0",
        "study_scope": "OPTION_A_SINGLE_CROSSING_DESCRIPTIVE_COHORT_27_EVENTS",
        "cross_site_generalization_claimed": False,
        "reference_status": {
            "adopted_ai_assisted_references_events": len(m43_adopt["adopted_active_annotations"]),
            "stage21_human_canonical_promotion_complete": (
                repo_root / "data/governance/stage21_promotion_receipt.json"
            ).is_file(),
            "raw_media_re_extraction_performed": False,
            "cache_basis": "pre-db40305 YOLOv8n inference + corrected natural-log-Mel Audio V3 caches",
        },
        "full_27_event_stream_inventory": {
            "physical_events": m43_cohort["physical_events"],
            "source_members_verified": m43_cohort["source_members_verified"],
            "front_sampled_frames": m43_cohort["visual"]["front"]["sampled_records"],
            "front_predicted_objects": m43_cohort["visual"]["front"]["predicted_objects"],
            "back_sampled_frames": m43_cohort["visual"]["back"]["sampled_records"],
            "back_predicted_objects": m43_cohort["visual"]["back"]["predicted_objects"],
            "audio_windows": m43_cohort["audio_windows"],
            "audio_positive_windows_at_037": m43_cohort["audio_model_positive_windows"],
            "b2_assembled_frames": m43_cohort["B2_input_frames"],
            "b2_paired_frames": m43_cohort["B2_both_record_frames"],
        },
        "policy_comparison_b4_and_sync11": policy_comparison,
        "independent_cross_verification": {
            "independent_verification_passed": len(discrepancies) == 0,
            "checks_total": len(verification_items),
            "checks_passed": len(verification_items) - len(discrepancies),
            "discrepancy_count": len(discrepancies),
            "items": verification_items,
        },
    }


def run_split_audit(repo_root: Path) -> dict[str, Any]:
    """Run complete non-raw audit of the 27-event split problem, ownership & Option A results."""
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
    primary = collection_plan["statistical_power_and_sample_size_recalculation"][
        "reconciled_cohort_tiers"
    ]["tier_c2_cluster_adjusted_10pct_bound_primary"]
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
            "recommended_for_generalization_and_model_retraining": (
                f"Option C ({primary['grand_total_events']} total events = "
                f"{primary['cohorts']['train']['cohort_total_events']} train + "
                f"{primary['cohorts']['val']['cohort_total_events']} val + "
                f"{primary['cohorts']['test']['cohort_total_events']} test across "
                f"{primary['total_crossings']} crossings and {primary['total_sessions']} sessions)"
            ),
            "research_owner_decision_sufficient_for_scope": True,
            "professor_technical_signoff_required": False,
        },
        "root_causes": [
            f"Single physical site: all 27 events share crossing_id={crossings!r} (0 held-out crossings).",
            f"Two physical sessions: only {true_sessions} exist (< 3 non-empty split roles required by validate_event_level_split).",
            "Session-hardware-class confounding: all 3 no_train_events and 1 engine_events clip occur only in Session 2 (2026-10-04 night, iPad back camera); 20/23 train events occur in Session 1 (2026-09-14 day, iPhone back camera).",
            "AI proposal metadata bug: batch_multimodal_annotator hardcoded recording_session_id='session_20260914_morning' on 27/27 events and lighting='day' on night clips train_events/021..023.",
        ],
        "proposal_metadata_inconsistencies_count": len(proposal_bugs),
        "proposal_metadata_inconsistencies": proposal_bugs,
        "research_ownership_and_authorization_audit": audit_research_ownership_and_authorization_workflow(repo_root),
        "option_a_complete_descriptive_evaluation_and_verification": (
            evaluate_option_a_complete_descriptive_study_and_verification(repo_root)
        ),
        "option_a_stratified_diagnostics": evaluate_option_a_stratified_corpus_diagnostics(repo_root, events),
        "autonomous_reopening_and_clearance_investigation": evaluate_autonomous_reopening_and_clearance_methods(
            repo_root, events
        ),
        "candidate_splits_evaluated": {
            "prior_hash_candidate_16_6_5": prior_eval,
            "chrono_temporal_block_15_5_7": chrono_eval,
        },
        "targeted_additional_data_collection_plan": collection_plan,
        "events": events,
    }
