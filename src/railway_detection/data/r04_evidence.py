# ruff: noqa: E501
"""Reproducible, fail-closed R04 evidence and candidate-scope reporting.

The module reads only the existing calibration diagnostics, candidate annotation
snapshot, active candidate proposals, calibration candidate manifest, and media inventory. It deliberately
does *not* read approved ground truth (there is none) and it never promotes a
candidate calibration or annotation.  The output is an evidence inventory: every
event is retained, including events blocked by R04, missing boundaries, and
censored boundaries.

The report is useful for deciding what could be attempted in an explicitly
labelled exploratory run.  It is not an authorization gate and must not be
interpreted as one.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from railway_detection.safety.media_guard import require_media_authorization

BOUNDARY_NAMES = (
    "T0_first_visible",
    "T1_danger_zone_entry",
    "T2_crossing_occupancy_start",
    "T3_locomotive_unit_clearance",
    "T4_tail_clearance",
    "T_scene_clear",
)
BOUNDARY_PROPOSAL_ALIASES = {
    "T3_locomotive_unit_clearance": "T3_locomotive_exit",
}
CALIBRATION_SUPPORTED = "CALIBRATION_SUPPORTED"


def sha256(path: Path) -> str:
    require_media_authorization(path, "HASH_RAW_MEDIA")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _proposal_timestamp(
    proposal: dict[str, Any], marker: str, fallback: float | None
) -> dict[str, Any]:
    """Normalize one *candidate* marker without calling it approved truth."""
    proposal_timestamps = proposal.get("proposed_timestamps", {})
    raw = proposal_timestamps.get(
        marker,
        proposal_timestamps.get(BOUNDARY_PROPOSAL_ALIASES.get(marker, ""), {}),
    )
    if not isinstance(raw, dict):
        raw = {}
    value = raw.get("value_s", fallback)
    rationale = str(raw.get("rationale", ""))
    lower = rationale.lower()
    if value is None:
        if any(token in lower for token in ("right-censor", "right censor", "recording terminates", "still visible")):
            status = "CANDIDATE_CENSORED_RIGHT"
        elif raw.get("applicable") is False:
            status = "CANDIDATE_NOT_APPLICABLE"
        else:
            status = "CANDIDATE_UNOBSERVABLE"
    elif "left-censor" in lower or "left censor" in lower:
        status = "CANDIDATE_CENSORED_LEFT"
    elif raw.get("candidate_observable") is False:
        status = "CANDIDATE_UNOBSERVABLE"
    elif raw.get("ambiguity_flag"):
        status = "CANDIDATE_AMBIGUOUS"
    else:
        status = "CANDIDATE_OBSERVABLE_UNAPPROVED"
    return {
        "value_s": value,
        "status": status,
        "candidate_observable": raw.get("candidate_observable"),
        "applicable": raw.get("applicable"),
        "ambiguity_flag": bool(raw.get("ambiguity_flag", False)),
        "reference_camera": raw.get("reference_camera"),
        "native_fps": raw.get("native_fps"),
        "rationale": rationale,
    }


def _proposal_path(repo: Path, snapshot_event: dict[str, Any]) -> Path | None:
    cohort = snapshot_event.get("cohort")
    event_id = snapshot_event.get("event_id")
    if isinstance(cohort, str) and isinstance(event_id, str):
        proposal_dir = repo / "data/ground_truth/proposals" / cohort
        candidates: list[tuple[int, Path]] = []
        for path in proposal_dir.glob(f"{event_id}_proposal_v*.json"):
            suffix = path.stem.rsplit("_proposal_v", 1)[-1]
            if suffix.isdigit():
                candidates.append((int(suffix), path))
        if candidates:
            return max(candidates, key=lambda item: (item[0], item[1].name))[1]
    raw = snapshot_event.get("active_proposal_file")
    if not raw:
        return None
    path = repo / str(raw)
    return path if path.is_file() else None


def _source_entry(manifest_event: dict[str, Any] | None, camera: str) -> dict[str, Any]:
    if not manifest_event:
        return {}
    entry = manifest_event.get(camera, {})
    return entry if isinstance(entry, dict) else {}


def build_r04_evidence(repo_root: Path) -> dict[str, Any]:
    """Build the complete event-level R04 evidence inventory.

    The function raises on missing primary inputs rather than manufacturing an
    empty report.  Missing optional proposal files remain visible as
    ``CANDIDATE_METADATA_MISSING`` in the event record.
    """
    root = Path(repo_root)
    calibration_path = root / "results/r04_sync_estimation/calibration_verdicts.json"
    snapshot_path = root / "data/ground_truth/snapshots/candidate_annotation_manifest_20261012.json"
    sync_manifest_path = root / "data/manifests/camera_sync_offsets_candidate.yaml"
    inventory_path = root / "data/manifests/layer_b_v2_annotation_inventory.json"
    required = (calibration_path, snapshot_path, sync_manifest_path, inventory_path)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("R04 evidence inputs missing: " + ", ".join(missing))

    calibration_rows = _load_json(calibration_path)
    calibration = {str(row["event_key"]): row for row in calibration_rows}
    snapshot = _load_json(snapshot_path)
    snapshot_events = {
        f"{row['cohort']}/{row['event_id']}": row for row in snapshot.get("events", [])
    }
    sync_manifest = yaml.safe_load(sync_manifest_path.read_text(encoding="utf-8")) or {}
    sync_events = sync_manifest.get("events", {})
    inventory = _load_json(inventory_path)

    event_keys = sorted(set(calibration) | set(snapshot_events) | set(inventory))
    events: list[dict[str, Any]] = []
    for event_key in event_keys:
        cohort, event_id = event_key.split("/", 1)
        row = calibration.get(event_key, {})
        snap = snapshot_events.get(event_key, {})
        sync = sync_events.get(event_key, {})
        proposal_path = _proposal_path(root, snap)
        proposal: dict[str, Any] = {}
        if proposal_path:
            proposal = _load_json(proposal_path)
        boundaries = {
            marker: _proposal_timestamp(proposal, marker, None)
            for marker in BOUNDARY_NAMES
        }
        verdict = str(row.get("verdict", sync.get("calibration_verdict", "NOT_ASSESSABLE")))
        candidate_scope = verdict == CALIBRATION_SUPPORTED
        front = _source_entry(sync, "camera_front")
        back = _source_entry(sync, "camera_back")
        train_present = bool(snap.get("train_present", cohort != "no_train_events"))
        t1 = boundaries["T1_danger_zone_entry"]
        t4 = boundaries["T4_tail_clearance"]
        event = {
            "event_key": event_key,
            "cohort": cohort,
            "event_id": event_id,
            "candidate_proposal": {
                "path": str(proposal_path.relative_to(root)) if proposal_path else None,
                "sha256": sha256(proposal_path) if proposal_path else None,
                "version": (
                    int(proposal_path.stem.rsplit("_proposal_v", 1)[-1])
                    if proposal_path and proposal_path.stem.rsplit("_proposal_v", 1)[-1].isdigit()
                    else None
                ),
                "snapshot_path": snap.get("active_proposal_file"),
                "snapshot_sha256": (
                    sha256(root / str(snap["active_proposal_file"]))
                    if snap.get("active_proposal_file")
                    and (root / str(snap["active_proposal_file"])).is_file()
                    else None
                ),
                "matches_snapshot": bool(
                    proposal_path
                    and snap.get("active_proposal_file")
                    and proposal_path.resolve()
                    == (root / str(snap["active_proposal_file"])).resolve()
                ),
            },
            "train_present_candidate": train_present,
            "approval_status": str(snap.get("approval_status", "UNAPPROVED_CANDIDATE_PROPOSAL")),
            "human_review_status": str(sync_manifest.get("human_review_status", "NOT_REVIEWED")),
            "calibration": {
                "verdict": verdict,
                "lag_s": row.get("lag_s"),
                "uncertainty_s": row.get("uncertainty_s", back.get("uncertainty_s", "unknown")),
                "psr": row.get("psr"),
                "snr": row.get("snr"),
                "window_range_s": row.get("window_range_s"),
                "qt_disagreement_s": row.get("qt_disagreement_s"),
                "reasons": list(row.get("reasons", sync.get("verdict_reasons", []))),
            },
            "media": {
                "front": {"path": front.get("relative_path"), "sha256": front.get("sha256")},
                "back": {"path": back.get("relative_path"), "sha256": back.get("sha256")},
            },
            "boundaries": boundaries,
            "clock_scope": {
                "master_clock": "front_camera_clock" if candidate_scope else "camera_local_clocks",
                "sign_convention": "t_master = t_back + offset_s",
                "dual_camera_candidate": candidate_scope,
                "dual_camera_candidate_scope": "CALIBRATION_SUPPORTED_CANDIDATE_ONLY" if candidate_scope else "NOT_CANDIDATE_SUPPORTED",
                "scope_decision_status": "RESEARCHER_DECISION_REQUIRED",
                "scope_status": "EXPLORATORY_CANDIDATE_ONLY" if candidate_scope else "BLOCKED_R04",
                "reason": (
                    "Calibration candidate meets the deterministic acoustic rule; no human landmark review "
                    "or governance promotion has occurred."
                    if candidate_scope
                    else "Calibration is not CALIBRATION_SUPPORTED; cross-camera fusion must fail closed."
                ),
            },
            "metric_boundary_compatibility": {
                "v9": {
                    "requires": ["T1_danger_zone_entry", "T4_tail_clearance", "aligned_common_clock"],
                    "candidate_boundary_status": {
                        "T1": t1["status"],
                        "T4": t4["status"],
                    },
                    "candidate_evaluable": False,
                    "candidate_prerequisites_status": {
                        "T1_candidate_available": t1["value_s"] is not None,
                        "T4_candidate_available": t4["value_s"] is not None,
                        "accepted_scope": False,
                        "approved_ground_truth": False,
                        "replay_trace_available": False,
                    },
                    "official_status": "BLOCKED_UNAPPROVED_GROUND_TRUTH",
                    "researcher_scope_decision_required": bool(candidate_scope),
                },
                "m4": {
                    "requires": ["T4_tail_clearance", "replay_t_blocked"],
                    "candidate_boundary_status": {"T4": t4["status"]},
                    "candidate_evaluable": False,
                    "candidate_prerequisites_status": {
                        "T4_candidate_available": t4["value_s"] is not None,
                        "replay_trace_available": False,
                        "replay_t_blocked_available": False,
                    },
                    "official_status": "BLOCKED_UNAPPROVED_GROUND_TRUTH",
                    "researcher_scope_decision_required": bool(candidate_scope),
                },
            },
        }
        events.append(event)

    counts: dict[str, int] = {}
    cohorts: dict[str, int] = {}
    for event in events:
        verdict = event["calibration"]["verdict"]
        counts[verdict] = counts.get(verdict, 0) + 1
        cohorts[event["cohort"]] = cohorts.get(event["cohort"], 0) + 1
    supported = [
        event["event_key"]
        for event in events
        if event["clock_scope"]["dual_camera_candidate"]
    ]
    supported_train = [
        event
        for event in events
        if event["cohort"] == "train_events"
        and event["clock_scope"]["dual_camera_candidate"]
    ]
    observable_candidate = "CANDIDATE_OBSERVABLE_UNAPPROVED"
    v9_candidate_boundary_events = [
        event["event_key"]
        for event in supported_train
        if event["boundaries"]["T1_danger_zone_entry"]["status"] == observable_candidate
        and event["boundaries"]["T4_tail_clearance"]["status"] == observable_candidate
    ]
    m4_candidate_t4_events = [
        event["event_key"]
        for event in events
        if event["cohort"] in ("train_events", "engine_events")
        and event["boundaries"]["T4_tail_clearance"]["status"] == observable_candidate
    ]
    return {
        "schema_version": "r04-event-evidence/2",
        "status": "CANDIDATE_EVIDENCE_ONLY_NO_AUTOMATIC_APPROVAL",
        "purpose": "Event-level R04 synchronization evidence and candidate scope; not an authorization.",
        "decision_required": {
            "artifact": "data/manifests/phase12_r04_scope_decision.json",
            "status": "MISSING_RESEARCHER_DECISION",
            "instruction": "Researcher must choose event_modes and accepted_sync_events. CALIBRATION_SUPPORTED is candidate evidence only and never implies scope approval.",
        },
        "source_files": {
            str(path.relative_to(root)): sha256(path) for path in required
        },
        "candidate_proposal_selection": (
            "highest numeric *_proposal_vN.json per cohort/event; the frozen snapshot is retained "
            "as a separately hashed historical reference and is never used to fill missing active-proposal timestamps"
        ),
        "calibration_manifest_status": str(sync_manifest.get("status", "UNKNOWN")),
        "human_review_status": str(sync_manifest.get("human_review_status", "NOT_REVIEWED")),
        "summary": {
            "total_events": len(events),
            "cohort_counts": dict(sorted(cohorts.items())),
            "verdict_counts": dict(sorted(counts.items())),
            "dual_camera_candidate_count": len(supported),
            "dual_camera_candidate_events": supported,
            "premature_opening_candidate_coverage": {
                "decision_status": "UNRESOLVED_NO_METRIC_SELECTED",
                "v9": {
                    "candidate_boundary_coverage_count": len(v9_candidate_boundary_events),
                    "calibration_supported_train_candidates": len(supported_train),
                    "candidate_events": v9_candidate_boundary_events,
                    "replay_trace_count": 0,
                    "official_evaluable_count": 0,
                },
                "m4": {
                    "candidate_T4_coverage_count": len(m4_candidate_t4_events),
                    "train_and_engine_event_count": sum(
                        event["cohort"] in ("train_events", "engine_events")
                        for event in events
                    ),
                    "candidate_events": m4_candidate_t4_events,
                    "replay_t_blocked_count": 0,
                    "official_evaluable_count": 0,
                },
                "interpretation": (
                    "Candidate boundary availability only; not approved labels, accepted scope, "
                    "replay outcomes, a metric denominator, or a performance result."
                ),
            },
            "full_cohort_dual_camera_status": "BLOCKED_R04_NON_SUPPORTED_EVENTS",
            "approval_status": "NO_APPROVED_GROUND_TRUTH",
        },
        "events": events,
    }


def render_scope_markdown(evidence: dict[str, Any]) -> str:
    """Render a compact human-readable report from the machine inventory."""
    summary = evidence["summary"]
    lines = [
        "# R04 Event-Level Evidence and Candidate Scope",
        "",
        "> **Status: CANDIDATE EVIDENCE ONLY.** This report does not promote calibration, approve labels, authorize a replay, or authorize field operation.",
        "",
        f"Generated from `r04-event-evidence/2`; {summary['total_events']} active events. "
        f"Deterministic calibration verdicts: `{summary['verdict_counts']}`.",
        "",
        "## Candidate scope",
        "",
        f"Exactly **{summary['dual_camera_candidate_count']}** events have `CALIBRATION_SUPPORTED` diagnostics and are candidates for a separately labelled exploratory dual-camera scope:",
        "",
        "`" + "`, `".join(summary["dual_camera_candidate_events"]) + "`",
        "",
        "The remaining events are **blocked by R04** (PROVISIONAL, AMBIGUOUS, FAILED, or NOT_ASSESSABLE). The candidate manifest remains `CANDIDATE_UNVALIDATED_DO_NOT_MERGE`; all human review and ground-truth approval fields remain unresolved.",
        "",
        "## Event-level candidate evidence",
        "",
        "| Event | Active candidate proposal | Calibration | Lag (s) | T1 candidate | T4 candidate | Scope / decision |",
        "|---|---|---|---:|---|---|---|",
    ]
    for event in evidence["events"]:
        cal = event["calibration"]
        proposal = event["candidate_proposal"]
        proposal_ref = (
            f"`{proposal['path']}` v{proposal['version']} "
            f"SHA-256 `{proposal['sha256']}`"
            if proposal["path"]
            else "missing"
        )
        t1 = event["boundaries"]["T1_danger_zone_entry"]
        t4 = event["boundaries"]["T4_tail_clearance"]
        t1_text = f"{t1['status']} ({t1['value_s']}; {t1['reference_camera']})"
        t4_text = f"{t4['status']} ({t4['value_s']}; {t4['reference_camera']})"
        lines.append(
            f"| `{event['event_key']}` | {proposal_ref} | `{cal['verdict']}` | "
            f"{cal['lag_s']} | `{t1_text}` | `{t4_text}` | "
            f"`{event['clock_scope']['scope_status']}` / "
            f"`{event['clock_scope']['scope_decision_status']}` |"
        )
    coverage = summary["premature_opening_candidate_coverage"]
    lines.extend(
        [
            "",
            "## Premature-opening boundary coverage (not metric results)",
            "",
            f"- v9: candidate T1+T4 values on calibration-supported train events for {coverage['v9']['candidate_boundary_coverage_count']}/{coverage['v9']['calibration_supported_train_candidates']} events. Accepted scope, approved labels, and replay traces are absent; official evaluable count: 0.",
            f"- M4: candidate observable T4 values for {coverage['m4']['candidate_T4_coverage_count']}/{coverage['m4']['train_and_engine_event_count']} train/engine events. Replay traces and `t_blocked` are absent; official evaluable count: 0.",
            f"- {coverage['interpretation']}",
            "",
            "",
            "## Interpretation constraints",
            "",
            "- Candidate T1/T4 and calibration diagnostics are evidence for human inspection only. The active proposal is chosen as the highest numeric proposal version; a differing frozen-snapshot proposal is separately hash-pinned in the JSON and is not silently treated as current.",
            "- The human reviewer must inspect the cited source video/audio and decide boundary states; this report does not resolve visual ambiguity or human listening requirements.",
            "- `CALIBRATION_SUPPORTED` means only that the frozen acoustic diagnostic rule passed (PSR, window stability, SNR, and QuickTime sanity bound). The reported `0.05 s` is a sub-frame geometric jitter bound, **not** a device-clock confidence interval.",
            "- T0–T4 values and censoring states are candidate annotation evidence. `CANDIDATE_CENSORED_LEFT`, `CANDIDATE_CENSORED_RIGHT`, and `CANDIDATE_UNOBSERVABLE` are preserved; none is silently converted to a number.",
            f"- Dual-camera scope is exploratory-candidate-only. Full-cohort fusion remains blocked for the {summary['total_events'] - summary['dual_camera_candidate_count']} non-supported events. No automatic approval or decision is emitted.",
            "",
            "## Reproducibility",
            "",
        ]
    )
    for path, digest in evidence["source_files"].items():
        lines.append(f"- `{path}` SHA-256 `{digest}`")
    return "\n".join(lines) + "\n"


def render_comparison_markdown(evidence: dict[str, Any]) -> str:
    """Render the exact v9/M4 decision record while preserving unresolved status."""
    summary = evidence.get("summary", {})
    supported_count = summary.get("dual_camera_candidate_count", 12)
    total_count = summary.get("total_events", 27)
    non_supported_count = total_count - supported_count
    review_status = evidence.get(
        "human_review_status", "CANDIDATE_UNVALIDATED_DO_NOT_MERGE"
    )

    return f"""# Premature-Opening: v9 vs M4 Technical Comparison and Decision Record

**Decision status: UNRESOLVED — no automatic approval.** This record is a technical comparison, not a researcher decision. The evaluator must continue to refuse an official run until an allowlisted researcher records `choices.premature_opening_window`.

## Exact predicates

| Candidate | Predicate | Required evidence | What is *not* included |
|---|---|---|---|
| **Protocol v9** (`t1_entry_to_t4_clearance`) | Failure if an opening command occurs while **T1 ≤ t < T4**; implemented replay flag additionally requires `OPENING`/`OPEN` and `not is_passage_blocked`. | Candidate/approved T1 and T4; one aligned common timeline. | T0, pre-T1 openings, and events with missing/unobservable T4. |
| **M4** (`first_blocked_to_t4_clearance`) | Set `t_blocked` to the first replay tick with `blocked=true`. Failure if a blocked→not-blocked transition or opening command occurs at **t_blocked < t < T4**; blocked status does not suppress the opening-command check. | Candidate/approved T4; replay trace with blocked state and opening commands. | T0 and T1 are not required by the predicate. A command exactly at `t_blocked` or exactly T4 is outside the strict interval. |

M4 is paired with **M5 (never protected)**: if no blocked tick occurs strictly before T4 (`t_blocked` is absent or `t_blocked ≥ T4`), the event is `never_protected`; M4 is **not evaluable**, not a zero-premature-opening success. The implementation records M5 as its own count and evaluable denominator; events where a metric cannot be computed remain excluded with reasons.

## Code/protocol compatibility note

The implemented v9 window is **[T1, T4)**. The trace predicate requires a gate state of `OPENING` or `OPEN` and `is_passage_blocked == false` at the sampled step. The window and this sampled-step/physical-blocked predicate are implementation semantics, not researcher acceptance. M4 is separately available through the trace-level `m4_premature_opening` function and intentionally flags an opening command even when the arm remains physically blocked; it also requires a blocked→not-blocked trace transition.

## T0–T4 and censoring

- **T0** first visual appearance; recording-start presence may be left-censored (`true physical T0 ≤ 0`) and must never be converted to a numeric point time for these metrics.
- **T1** danger-zone entry on the front-camera clock. v9 requires an observable, approved T1; M4 does not.
- **T2** occupancy start; diagnostic for physical occupancy, not required by either v9 or M4.
- **T3** locomotive-unit clearance on the back-camera clock; diagnostic only for these predicates.
- **T4** final-vehicle tail clearance on the back-camera clock; primary right boundary for both candidates.
- For v9, missing, ambiguous, unobservable, or right-censored T1 or T4 makes the event not evaluable; for M4, T4 is required but T1 is not. A missing T0 does not by itself exclude either candidate. `T3` and `T_scene_clear` do not define either window. The engine-only cohort has `T3 ≡ T4` only when that relationship is established by the annotation protocol; it does not supply a substitute T4 when T4 is censored.
- Candidate boundaries are not approved ground truth. Censoring is preserved as a status/reason and never replaced with `0`, an imputed time, or a favorable outcome.

## Clock and camera compatibility

T1 is on the front clock and T4 on the back clock. v9 requires both boundaries on one valid common timeline; compare them only after the researcher accepts the event scope and validated event-specific offset, with `t_master = t_back + offset_s` (front is master). M4 may use the back-local T4 and back-local replay trace without fusing camera clocks. The acoustic diagnostic has {supported_count} `CALIBRATION_SUPPORTED` candidate events and {non_supported_count} non-supported events; its manifest remains `CANDIDATE_UNVALIDATED_DO_NOT_MERGE`, with `human_review_status: {review_status}`. Calibration availability does not approve scope.

- **Dual-camera candidate scope:** v9 can be computed only after accepted alignment and approved T1/T4. M4 can use the approved back-clock T4 and replay trace; it does not inherently require a fused clock.
- **Independent camera scope:** M4 may be computed on a back-stream replay if the system produces a back-clock `t_blocked` and back-clock T4. v9 is not comparable because T1 and T4 are on different clocks. This does not make an independent-camera M4 result a full physical safety result.
- **Front-only/single-camera scope:** T4 is on the back clock, so neither candidate is evaluable from front-only evidence; do not infer or synthesize T4.

## Edge cases and compatibility

| Edge case | v9 | M4 / M5 |
|---|---|---|
| Opening before T1 after an earlier block | Not a v9 failure; report separately only if a separate endpoint is predeclared. | Failure if strictly after `t_blocked` and before T4. |
| Opening exactly at T1 | Inside the window, but the implemented v9 sample still requires `not is_passage_blocked`; discrete samples and boundary equality must follow the locked trace rule. | Not determined by T1; apply only the M4 blocked-time interval. |
| Opening exactly at `t_blocked` | Not special to v9 except as it relates to T1 and blocked state. | Excluded by strict lower bound. |
| Opening exactly at T4 | Excluded by the half-open interval. | Excluded by strict upper bound. |
| Opening command while arm remains physically blocked | Implemented v9 predicate does not flag a sample with `is_passage_blocked == true`. | M4 command-level rule flags the opening command regardless of `blocked`; a blocked→not-blocked transition is also a failure. |
| Repeated blocked ticks | No special state needed. | First blocked tick defines `t_blocked`; later blocked ticks do not reset it. |
| Never blocked before T4 | Not a special class; v9 can still be evaluated if T1/T4 and trace are available. | M5=`never_protected`; M4 premature value is `null`, excluded from M4 denominator. |
| T4 missing, ambiguous, or right-censored | Not evaluable. | Not evaluable; do not classify as M5 from censoring. |
| T1 missing/ambiguous | Not evaluable. | Does not by itself affect M4. |
| Engine-only event | Apply T4 only if independently adjudicated under the engine-event rule. Do not assume T3=T4. | Same requirement; T4 censoring blocks M4 and M5 classification. |
| No-train event | Not applicable. | Not applicable; retain nuisance/false-alarm counts separately. |
| Sparse/no replay samples in the interval | No sampled qualifying v9 event is not evidence about unobserved times; use the evaluator's discrete trace semantics and sampling disclosure. | No observed transition/command only describes the available replay trace, not continuous-time behavior. |

## Decision and blocking record

No candidate is selected here. The exact unresolved choice remains either `t1_entry_to_t4_clearance` (v9) or `first_blocked_to_t4_clearance` (M4). The choice changes inclusion criteria and denominator: v9 requires approved T1 and T4 on a compatible common timeline, while M4 requires approved T4 plus replay `t_blocked` and makes never-protected events a separate M5 count rather than M4 successes. Censoring and unavailable clocks remain exclusions with reasons, never favorable zeroes. Selecting by recency, implementation convenience, or an AI recommendation would be an unauthorized scientific decision. Until a researcher records one option in `data/manifests/phase12_protocol_decision.json`, official evaluation remains blocked. This document also does not authorize the {supported_count}-event exploratory scope; that scope requires its separate decision and remains candidate-only.
"""

