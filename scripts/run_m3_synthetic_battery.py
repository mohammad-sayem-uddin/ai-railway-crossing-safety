#!/usr/bin/env python3
"""Mission 3 synthetic decision-engine battery (UNGATED synthetic validation).

Drives BOTH decision engines (frozen v1 `MultimodalDecisionEngine` and candidate
v2 `MultimodalDecisionEngineV2Candidate`) through identical, hand-built
MultimodalFrame streams and records per-tick traces plus per-scenario
expectation checks. All inputs are synthetic: this validates state-machine
behaviour only and supports no claim about real-data performance.

Battery/2 note: run 1 (35/42) exposed expectation errors in this harness's
model of the frozen v1 engine -- v1 confirms departure from ambiguous labels
immediately (its defect is label conflation, not absence of confirmation),
and its RULE_7 self-interrupt ejects it from REAR_CONFIRMED within a tick,
after which it traps in CROSSING_OCCUPIED when evidence stops. The v1 checks
below were corrected against the v1 source and the run-1 traces; checks that
record behaviour rather than assert an expectation are labelled "recorded:" /
"documented:". All v2 checks are unchanged from run 1 (v2 passed all of its
checks in run 1). Run 1 outputs are preserved under results/m3_synthetic_battery/.

Scenarios:
  S1  nominal departure, rear label, then continuing side stream during dwell
  S2  disappearance-only departure (no rear label ever)
  S3a back camera unavailable during TRAIN_DEPARTING
  S3b all vision lost while active
  S4  back source goes silent (absent) during clearance dwell -> stale abort
  S5a contradictory: front 'front' + back 'rear' during dwell -> interrupt
  S5b audio-only in IDLE -> no actuation (RULE_2)
  S6  single-camera topology: absence alone (v1) vs disappearance rule (v2)
  S7a recovery from active-origin fault -> TRAIN_PRESENT (never direct open)
  S7b recovery from IDLE-origin fault -> IDLE permitted
  S8  second train during GATE_OPENING -> abort to GATE_CLOSING
  S9  duplicate + out-of-order timestamps rejected
  S10 audio horn during clearance dwell delays clearance (RULE_2)

Usage: python scripts/run_m3_synthetic_battery.py [--out DIR]
Default out: results/m3_synthetic_battery/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from railway_detection.experiments.frozen_config import load_frozen_config
from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.decision_engine_v2_candidate import (
    MultimodalDecisionEngineV2Candidate,
)
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality

DT = 0.2
FRONT = "camera_front"
BACK = "camera_back"
AUDIO = "audio_main"

# Segment spec per source: ("det", label, conf) | ("empty",) | ("down",) | ("absent",)
EMPTY = ("empty",)
DOWN = ("down",)
ABSENT = ("absent",)


def det(label: str, conf: float = 0.9):
    return ("det", label, conf)


def build_frames(segments):
    """segments: list of (duration_s, front_spec, back_spec, audio_spec)."""
    frames = []
    t = 0.0
    for duration, fs, bs, as_ in segments:
        n = max(1, int(round(duration / DT)))
        for _ in range(n):
            frames.append(_frame_at(t, fs, bs, as_))
            t = round(t + DT, 6)
    return frames


def _record(t, source_id, modality, spec):
    if spec[0] == "absent":
        return None
    if spec[0] == "down":
        return EvidenceRecord(t, source_id, modality, False, ())
    if spec[0] == "det":
        return EvidenceRecord(
            t, source_id, modality, True, (Detection(spec[1], float(spec[2])),)
        )
    return EvidenceRecord(t, source_id, modality, True, ())


def _frame_at(t, fs, bs, as_):
    vision, audio = [], []
    avail = {}
    for source_id, modality, spec, bucket in (
        (FRONT, Modality.VISION, fs, vision),
        (BACK, Modality.VISION, bs, vision),
        (AUDIO, Modality.AUDIO, as_, audio),
    ):
        rec = _record(t, source_id, modality, spec)
        if rec is not None:
            bucket.append(rec)
            avail[source_id] = bool(rec.available)
    return MultimodalFrame(
        master_timestamp_s=float(t),
        vision_records=tuple(vision),
        audio_records=tuple(audio),
        source_availability=avail,
    )


# Shared prefix: approach -> warning -> closing -> present -> occupied -> departing.
PREFIX = [
    (0.6, det("front"), EMPTY, EMPTY),          # approach confirmation
    (2.2, det("side"), det("side"), EMPTY),     # warning dwell elapses
    (3.2, det("side"), det("side"), EMPTY),     # gate closing elapses -> TRAIN_PRESENT
    (0.4, det("side"), det("side"), EMPTY),     # -> CROSSING_OCCUPIED
    (0.4, det("side"), det("side"), EMPTY),     # -> TRAIN_DEPARTING
]


def run_engine(engine, frames, run_id):
    engine.reset(0.0)
    trace = []
    for fr in frames:
        rec = engine.evaluate_frame(fr, run_id)
        trace.append(rec.to_dict())
    return trace


def states(trace):
    return [r["resulting_state"] for r in trace]


def rules(trace):
    return [r.get("rule_id") for r in trace]


def gate_states(trace):
    return [r["resulting_gate_state"] for r in trace]


def reached(trace, state):
    return state in states(trace)


def first_idx(trace, state):
    st = states(trace)
    return st.index(state) if state in st else -1


def last_detection_idx(frames):
    last = -1
    for i, fr in enumerate(frames):
        if any(r.detections for r in fr.vision_records if r.available):
            last = i
    return last


def any_label(frames, label):
    return any(
        d.label.lower() == label
        for fr in frames
        for r in fr.vision_records
        if r.available
        for d in r.detections
    )


CHECKS = []


def check(scenario, engine, name, passed, detail=""):
    CHECKS.append(
        {
            "scenario": scenario,
            "engine": engine,
            "check": name,
            "passed": bool(passed),
            "detail": detail,
        }
    )


def scenario_traces(name, frames, engines):
    return {ename: run_engine(eng, frames, f"{name}_{ename}") for ename, eng in engines.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/m3_synthetic_battery")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    config = load_frozen_config("configs/frozen_experiment_v1.yaml")
    engines = {
        "v1_frozen": MultimodalDecisionEngine(config),
        "v2_candidate": MultimodalDecisionEngineV2Candidate(config),
    }
    traces_all = {}

    # ---- S1: rear-confirmed departure, continuing side stream during dwell
    frames = build_frames(
        PREFIX
        + [
            (0.4, det("side"), det("rear"), EMPTY),   # rear confirmation
            (4.0, det("side"), det("side"), EMPTY),   # tail still passing laterally
            (4.0, EMPTY, EMPTY, EMPTY),               # gone; opening dwell -> IDLE
        ]
    )
    tr = scenario_traces("S1", frames, engines)
    traces_all["S1"] = tr
    for ename, trace in tr.items():
        check("S1", ename, "reaches REAR_CONFIRMED", reached(trace, "REAR_CONFIRMED"))
        start = first_idx(trace, "TRAIN_PRESENT")
        end = first_idx(trace, "CROSSING_CLEAR")
        window = gate_states(trace)[start : end if end >= 0 else len(trace)]
        check("S1", ename, "gate never reopens between closure and clearance",
              "OPEN" not in window and "OPENING" not in window)
    check("S1", "v2_candidate", "continuing side stream does not reset dwell: reaches CROSSING_CLEAR",
          reached(tr["v2_candidate"], "CROSSING_CLEAR"))
    check("S1", "v2_candidate", "no RULE_7 interrupt from continuing side stream",
          "RULE_7_NEW_TRAIN_INTERRUPT" not in rules(tr["v2_candidate"]))
    check("S1", "v2_candidate", "completes to IDLE with gate OPEN",
          states(tr["v2_candidate"])[-1] == "IDLE" and gate_states(tr["v2_candidate"])[-1] == "OPEN")
    check("S1", "v1_frozen", "documented defect: continuing side stream blocks clearance (no CROSSING_CLEAR)",
          not reached(tr["v1_frozen"], "CROSSING_CLEAR"),
          f"RULE_7 count={rules(tr['v1_frozen']).count('RULE_7_NEW_TRAIN_INTERRUPT')}")

    # ---- S2: disappearance-only departure
    frames = build_frames(
        PREFIX
        + [
            (1.0, det("side"), EMPTY, EMPTY),   # back available, empty: disappearance ticks
            (4.0, EMPTY, EMPTY, EMPTY),
            (4.0, EMPTY, EMPTY, EMPTY),
        ]
    )
    tr = scenario_traces("S2", frames, engines)
    traces_all["S2"] = tr
    check("S2", "v2_candidate", "disappearance confirms departure (RULE_3C) and clears",
          reached(tr["v2_candidate"], "REAR_CONFIRMED") and reached(tr["v2_candidate"], "CROSSING_CLEAR"))
    rear_idx = first_idx(tr["v1_frozen"], "REAR_CONFIRMED")
    last_det = last_detection_idx(frames)
    check("S2", "v1_frozen", "documented conflation: v1 confirms departure from ambiguous labels while the train is still detected",
          0 <= rear_idx < last_det,
          f"rear_idx={rear_idx} last_detection_idx={last_det}")
    check("S2", "v1_frozen", "recorded: v1 outcome after the evidence stream stops",
          True,
          f"cleared={reached(tr['v1_frozen'], 'CROSSING_CLEAR')} final={states(tr['v1_frozen'])[-1]}")

    # ---- S3a: back camera unavailable during TRAIN_DEPARTING
    frames = build_frames(PREFIX + [(6.0, det("side"), DOWN, EMPTY)])
    tr = scenario_traces("S3a", frames, engines)
    traces_all["S3a"] = tr
    for ename, trace in tr.items():
        check("S3a", ename, "gate stays CLOSED while departure camera down",
              all(g == "CLOSED" for g in gate_states(trace)[first_idx(trace, "TRAIN_PRESENT"):]))
        check("S3a", ename, "no clearance completes while departure camera down",
              not reached(trace, "CROSSING_CLEAR"))
    check("S3a", "v2_candidate", "never confirms departure from a down camera",
          not reached(tr["v2_candidate"], "REAR_CONFIRMED") or first_idx(tr["v2_candidate"], "FAULT_FAIL_SAFE") >= 0)
    check("S3a", "v1_frozen", "recorded: v1 REAR_CONFIRMED was reached from ambiguous labels before the failure",
          True, f"rear_idx={first_idx(tr['v1_frozen'], 'REAR_CONFIRMED')}")

    # ---- S3b: all vision lost while active
    frames = build_frames(PREFIX + [(3.0, DOWN, DOWN, EMPTY)])
    tr = scenario_traces("S3b", frames, engines)
    traces_all["S3b"] = tr
    for ename, trace in tr.items():
        check("S3b", ename, "all-vision loss while active => FAULT_FAIL_SAFE, gate CLOSED",
              reached(trace, "FAULT_FAIL_SAFE") and gate_states(trace)[-1] == "CLOSED")

    # ---- S4: back source absent (silent) during clearance dwell -> stale abort
    frames = build_frames(
        PREFIX
        + [
            (0.4, det("side"), det("rear"), EMPTY),  # REAR_CONFIRMED
            (6.0, EMPTY, ABSENT, EMPTY),            # back stops reporting entirely
        ]
    )
    tr = scenario_traces("S4", frames, engines)
    traces_all["S4"] = tr
    check("S4", "v2_candidate", "stale departure source aborts clearance => FAULT_FAIL_SAFE",
          reached(tr["v2_candidate"], "FAULT_FAIL_SAFE") and not reached(tr["v2_candidate"], "CROSSING_CLEAR"),
          f"rules={sorted(set(r for r in rules(tr['v2_candidate']) if r))}")
    check("S4", "v1_frozen", "documented: v1 does not reach CROSSING_CLEAR",
          not reached(tr["v1_frozen"], "CROSSING_CLEAR"))
    check("S4", "v1_frozen", "documented: v1 stale-abort is unreachable in practice (RULE_7 ejects it from REAR_CONFIRMED first; it traps in CROSSING_OCCUPIED when evidence stops)",
          not reached(tr["v1_frozen"], "FAULT_FAIL_SAFE") and states(tr["v1_frozen"])[-1] == "CROSSING_OCCUPIED",
          f"final={states(tr['v1_frozen'])[-1]} rules={sorted(set(r for r in rules(tr['v1_frozen']) if r))}")

    # ---- S5a: contradictory evidence during dwell -> new-train interrupt wins
    frames = build_frames(
        PREFIX
        + [
            (0.4, det("side"), det("rear"), EMPTY),   # REAR_CONFIRMED
            (0.6, det("front"), det("rear"), EMPTY),  # simultaneous front + rear
            (3.0, det("side"), det("side"), EMPTY),
        ]
    )
    tr = scenario_traces("S5a", frames, engines)
    traces_all["S5a"] = tr
    for ename, trace in tr.items():
        check("S5a", ename, "unambiguous new approach during dwell interrupts (RULE_7)",
              "RULE_7_NEW_TRAIN_INTERRUPT" in rules(trace))
        check("S5a", ename, "no clearance completes after interrupt",
              not reached(trace, "CROSSING_CLEAR"))

    # ---- S5b: audio-only in IDLE
    frames = build_frames([(4.0, EMPTY, EMPTY, det("train_horn", 0.9))])
    tr = scenario_traces("S5b", frames, engines)
    traces_all["S5b"] = tr
    for ename, trace in tr.items():
        check("S5b", ename, "audio alone never actuates: stays IDLE, gate OPEN",
              all(s == "IDLE" for s in states(trace)) and all(g == "OPEN" for g in gate_states(trace)))

    # ---- S6: single-camera topology (back absent from the start)
    frames = build_frames(
        [
            (0.6, det("front"), ABSENT, EMPTY),
            (2.2, det("side"), ABSENT, EMPTY),
            (3.2, det("side"), ABSENT, EMPTY),
            (0.4, det("side"), ABSENT, EMPTY),
            (0.4, det("side"), ABSENT, EMPTY),
            (6.0, EMPTY, ABSENT, EMPTY),   # train gone; front camera available+empty
            (4.0, EMPTY, ABSENT, EMPTY),
        ]
    )
    tr = scenario_traces("S6", frames, engines)
    traces_all["S6"] = tr
    check("S6", "v1_frozen", "documented conflation: v1 confirms departure with zero rear labels anywhere in the stream",
          reached(tr["v1_frozen"], "REAR_CONFIRMED") and not any_label(frames, "rear"))
    check("S6", "v1_frozen", "recorded: v1 eventual outcome in single-camera topology",
          True,
          f"cleared={reached(tr['v1_frozen'], 'CROSSING_CLEAR')} final={states(tr['v1_frozen'])[-1]}")
    check("S6", "v2_candidate", "single-camera disappearance path confirms and clears (documented 3C fallback)",
          reached(tr["v2_candidate"], "CROSSING_CLEAR"))
    for ename, trace in tr.items():
        check("S6", ename, "gate CLOSED throughout occupancy/departure",
              all(g == "CLOSED" for g in gate_states(trace)[first_idx(trace, "TRAIN_PRESENT"): first_idx(trace, "GATE_OPENING") if reached(trace, "GATE_OPENING") else len(trace)]))

    # ---- S7a: recovery from active-origin fault
    frames = build_frames(
        PREFIX
        + [
            (1.0, DOWN, DOWN, EMPTY),        # fault while active
            (4.0, EMPTY, EMPTY, EMPTY),      # sensors back, clean empty frames
        ]
    )
    tr = scenario_traces("S7a", frames, engines)
    traces_all["S7a"] = tr
    for ename, trace in tr.items():
        check("S7a", ename, "fault entered", reached(trace, "FAULT_FAIL_SAFE"))
        after = trace[first_idx(trace, "FAULT_FAIL_SAFE"):] if reached(trace, "FAULT_FAIL_SAFE") else []
        check("S7a", ename, "recovery never goes directly to IDLE/OPEN from active-origin fault",
              all(r["resulting_state"] != "IDLE" for r in after) and all(r["resulting_gate_state"] != "OPEN" for r in after),
              f"post-fault states={sorted(set(r['resulting_state'] for r in after))}")

    # ---- S7b: recovery from IDLE-origin fault
    frames = build_frames(
        [
            (1.0, DOWN, DOWN, EMPTY),        # vision loss in IDLE -> clamp after confirm frames
            (4.0, EMPTY, EMPTY, EMPTY),      # clean recovery
        ]
    )
    tr = scenario_traces("S7b", frames, engines)
    traces_all["S7b"] = tr
    for ename, trace in tr.items():
        check("S7b", ename, "IDLE-origin fault may recover to IDLE",
              reached(trace, "FAULT_FAIL_SAFE") and states(trace)[-1] == "IDLE",
              f"final={states(trace)[-1]}")

    # ---- S8: second train during GATE_OPENING
    frames = build_frames(
        PREFIX
        + [
            (0.4, det("side"), det("rear"), EMPTY),
            (3.6, EMPTY, EMPTY, EMPTY),          # dwell completes -> CROSSING_CLEAR -> GATE_OPENING
            (0.6, det("front"), EMPTY, EMPTY),   # new train while opening
            (2.0, det("side"), det("side"), EMPTY),
        ]
    )
    tr = scenario_traces("S8", frames, engines)
    traces_all["S8"] = tr
    check("S8", "v2_candidate", "reaches GATE_OPENING then aborts to GATE_CLOSING on new train",
          reached(tr["v2_candidate"], "GATE_OPENING")
          and states(tr["v2_candidate"])[-1] in ("GATE_CLOSING", "TRAIN_PRESENT", "WARNING")
          and gate_states(tr["v2_candidate"])[-1] != "OPEN")
    check("S8", "v1_frozen", "recorded behaviour (v1 may never reach opening; see trace)",
          True, f"reached_opening={reached(tr['v1_frozen'], 'GATE_OPENING')} final={states(tr['v1_frozen'])[-1]}")

    # ---- S9: duplicate + out-of-order timestamps
    base = build_frames(PREFIX + [(2.0, det("side"), det("side"), EMPTY)])
    for ename, eng in engines.items():
        eng.reset(0.0)
        recs = []
        for fr in base[:10]:
            recs.append(eng.evaluate_frame(fr, f"S9_{ename}"))
        dup = eng.evaluate_frame(base[9], f"S9_{ename}")          # same master t again
        ooo_frame = _frame_at(base[5].master_timestamp_s, det("side"), det("side"), EMPTY)
        ooo = eng.evaluate_frame(ooo_frame, f"S9_{ename}")        # earlier master t
        got_rules = {dup.to_dict().get("rule_id"), ooo.to_dict().get("rule_id")}
        check("S9", ename, "duplicate rejected (RULE_10) and out-of-order rejected (RULE_8)",
              "RULE_10_DUPLICATE_FRAME_REJECTION" in got_rules and "RULE_8_OUT_OF_ORDER_REJECTION" in got_rules,
              f"got={sorted(x for x in got_rules if x)}")
        traces_all.setdefault("S9", {})[ename] = [r.to_dict() for r in recs] + [dup.to_dict(), ooo.to_dict()]

    # ---- S10: audio during dwell delays clearance
    frames = build_frames(
        PREFIX
        + [
            (0.4, det("side"), det("rear"), EMPTY),        # REAR_CONFIRMED
            (4.0, EMPTY, EMPTY, det("train_horn", 0.9)),  # horn keeps dwell reset
            (5.0, EMPTY, EMPTY, EMPTY),                   # horn stops -> dwell completes
        ]
    )
    tr = scenario_traces("S10", frames, engines)
    traces_all["S10"] = tr
    check("S10", "v2_candidate", "clearance completes only after audio stops + full dwell",
          reached(tr["v2_candidate"], "CROSSING_CLEAR"))
    check("S10", "v2_candidate", "clearance latency exceeds horn duration + dwell (>= 7s)",
          (first_idx(tr["v2_candidate"], "CROSSING_CLEAR") - first_idx(tr["v2_candidate"], "REAR_CONFIRMED")) * DT >= 7.0,
          f"latency={round((first_idx(tr['v2_candidate'], 'CROSSING_CLEAR') - first_idx(tr['v2_candidate'], 'REAR_CONFIRMED')) * DT, 2)}s")
    check("S10", "v1_frozen", "documented: v1 never clears (limit-cycle trap in CROSSING_OCCUPIED once evidence stops)",
          not reached(tr["v1_frozen"], "CROSSING_CLEAR"),
          f"final={states(tr['v1_frozen'])[-1]}")

    # ---- write outputs
    for scen, per_engine in traces_all.items():
        for ename, trace in per_engine.items():
            with open(out / f"trace_{scen}_{ename}.jsonl", "w", encoding="utf-8") as fh:
                for row in trace:
                    fh.write(json.dumps(row, sort_keys=True) + "\n")
    summary = {
        "battery": "m3_synthetic_battery/2",
        "scope": "SYNTHETIC VALIDATION ONLY - no real-data performance claim",
        "checks_total": len(CHECKS),
        "checks_passed": sum(1 for c in CHECKS if c["passed"]),
        "checks": CHECKS,
    }
    with open(out / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    print(f"checks: {summary['checks_passed']}/{summary['checks_total']} passed")
    for c in CHECKS:
        if not c["passed"]:
            print(f"FAIL {c['scenario']} {c['engine']} :: {c['check']} :: {c['detail']}")
    return 0 if summary["checks_passed"] == summary["checks_total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
