#!/usr/bin/env python3
"""Descriptive manuscript support plus preserved historical UNVERIFIED templates.

Legacy fixed claims are not empirical evidence; default generation fails closed.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
TABLES_DIR = REPO_ROOT / "results" / "experiments" / "tables"
CACHE_DIR = REPO_ROOT / "results" / "experiments" / "cache"
EXP_DIR = REPO_ROOT / "results" / "experiments"


def write_table_files(
    table_id: str,
    title: str,
    headers: list[str],
    rows: list[list[Any]],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Markdown
    md_lines = [
        f"### {title}\n",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        md_lines.append("| " + " | ".join(str(c) for c in row) + " |")
    (output_dir / f"{table_id}.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # 2. CSV
    with open(output_dir / f"{table_id}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    # 3. LaTeX
    align_str = "l" * len(headers)
    tex_lines = [
        r"\begin{table*}[t]",
        r"\centering",
        f"\\caption{{{title}}}",
        f"\\label{{tab:{table_id}}}",
        f"\\begin{{tabular}}{{{align_str}}}",
        r"\hline",
        " & ".join(h.replace("_", "\\_").replace("%", "\\%") for h in headers) + r" \\",
        r"\hline",
    ]
    for row in rows:
        row_str = " & ".join(str(c).replace("_", "\\_").replace("%", "\\%") for c in row) + r" \\"
        tex_lines.append(row_str)
    tex_lines.extend(
        [
            r"\hline",
            r"\end{tabular}",
            r"\end{table*}",
        ]
    )
    (output_dir / f"{table_id}.tex").write_text("\n".join(tex_lines) + "\n", encoding="utf-8")


def _get_event_order() -> list[str]:
    """Return all 27 active events in canonical order."""
    events = [f"train_events_event_{i:03d}" for i in range(1, 24)]
    events.extend([f"no_train_events_event_{i:03d}" for i in range(1, 4)])
    events.append("engine_events_event_001")
    return events


def _historical_unverified_templates(
    output_dir: Path | str = "results/experiments/tables",
    all_summaries: dict[str, Any] | None = None,
) -> None:
    raise PermissionError("Historical fixed-value templates are preserved for audit only")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    events_27 = _get_event_order()

    # Load B0 and B4 single events
    b0_singles = {}
    b4_singles = {}
    if (EXP_DIR / "B0" / "single_events.json").exists():
        with open(EXP_DIR / "B0" / "single_events.json", encoding="utf-8") as f:
            for s in json.load(f):
                b0_singles[s["event_id"]] = s
    if (EXP_DIR / "B4" / "single_events.json").exists():
        with open(EXP_DIR / "B4" / "single_events.json", encoding="utf-8") as f:
            for s in json.load(f):
                b4_singles[s["event_id"]] = s

    # Table 1: Dataset Composition
    write_table_files(
        table_id="table01_dataset_composition",
        title="Table 1: Multi-Layer Dataset Inventory and Isolation Scheme",
        headers=[
            "Dataset Layer",
            "Total Samples",
            "Target Classes",
            "Split Composition",
            "Role",
            "Isolation Mechanism",
        ],
        rows=[
            [
                "Layer A: Vision",
                "3,157 annotated images",
                "front, side, rear",
                "2,218 train / 467 val / 472 test",
                "YOLOv8n Development",
                "Group-disjoint / Frozen",
            ],
            [
                "Layer A: Audio",
                "2,276 audio files (276 horn / 2,000 ESC-50)",
                "train_horn vs ambient",
                "Group-disjoint cross-validation",
                "CompactTrainHornCNN Dev",
                "ESC-50 + Field / Frozen",
            ],
            [
                "Layer B: Real Events",
                "27 active events (54 videos, 2,617s)",
                "passage approach/departure",
                "23 train / 3 no-train / 1 engine",
                "Final Multimodal Evaluation",
                "100% Unseen / Frozen",
            ],
            [
                "Layer B: Audio",
                "54 extracted tracks (16kHz mono)",
                "ambient / train horn",
                "4,741 windows evaluated",
                "Evaluation Only",
                "Excluded from Training",
            ],
        ],
        output_dir=out,
    )

    # Table 2: Vision Model Configuration
    write_table_files(
        table_id="table02_vision_model_config",
        title="Table 2: YOLOv8n Vision Model Checkpoint and Configuration",
        headers=["Parameter", "Specification / Value", "Methodological Rationale"],
        rows=[
            ["Architecture", "YOLOv8n (nano)", "Edge deployment efficiency"],
            ["Image Dimensions", "640 x 640 pixels", "Standard high-resolution feature grid"],
            [
                "Frozen Checkpoint Path",
                "experiments/vision/39f402dfe460/checkpoints/weights/best.pt",
                "Preserved pre-evaluation weights",
            ],
            [
                "Checkpoint SHA-256",
                "3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd",
                "Cryptographic immutability verified",
            ],
            [
                "Operating Threshold",
                "0.35 (approach), 0.35 (departure)",
                "Frozen development-data calibration",
            ],
            ["Inference FPS", "5.0 frames/second", "Standard temporal sampling stride"],
        ],
        output_dir=out,
    )

    # Table 3: Audio Model Configuration
    write_table_files(
        table_id="table03_audio_model_config",
        title="Table 3: CompactTrainHornCNN Audio Model Configuration",
        headers=["Parameter", "Specification / Value", "Methodological Rationale"],
        rows=[
            [
                "Architecture",
                "CompactTrainHornCNN (3-block CNN, 25,697 params)",
                "Overfitting prevention on small acoustic pools",
            ],
            [
                "Acoustic Representation",
                "64-band Log-Mel Spectrogram (64 x 61)",
                "Time-frequency horn harmonic resolution",
            ],
            [
                "Analysis Window",
                "1.0s window, 0.5s hop stride, 16kHz mono",
                "Standard sliding acoustic window",
            ],
            [
                "Frozen Checkpoint Path",
                "experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt",
                "Preserved optimal validation model",
            ],
            [
                "Checkpoint SHA-256",
                "ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782",
                "Cryptographic immutability verified",
            ],
            [
                "Operating Threshold",
                "T* = 0.3700",
                "Optimal F1 calibrated on held-out validation (ESC-50)",
            ],
            [
                "Safety Constraint",
                "Supporting Only (Never commands gate opening)",
                "Safety policy invariant INV-1",
            ],
        ],
        output_dir=out,
    )

    # Table 4: Vision Performance on Layer B (B0)
    b0_rows = []
    total_audio_windows = 0
    total_audio_train_dets = 0
    audio_det_events = 0

    for ev in events_27:
        # Check active cache files ONLY (avoiding orphaned historical caches)
        front_v = CACHE_DIR / f"{ev}_camera_front_camera_1_vision.jsonl"

        front_det = False
        side_det = False
        rear_det = False
        onset = None
        n_frames = 0
        n_det_frames = 0
        confs = []

        if front_v.exists():
            with open(front_v, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    n_frames += 1
                    rec = json.loads(line)
                    dets = rec.get("detections", [])
                    if dets:
                        n_det_frames += 1
                        if onset is None:
                            onset = float(rec["timestamp_s"])
                        for d in dets:
                            lbl = d["label"]
                            confs.append(float(d["confidence"]))
                            if lbl == "front":
                                front_det = True
                            elif lbl == "side":
                                side_det = True
                            elif lbl == "rear":
                                rear_det = True

        continuity = (n_det_frames / n_frames * 100.0) if n_frames > 0 else 0.0
        mean_conf = (sum(confs) / len(confs)) if confs else 0.0
        onset_str = f"{onset:.2f}s" if onset is not None else "N/A"
        b0_rows.append(
            [
                ev,
                "Yes" if front_det else "No",
                "Yes" if side_det else "No",
                "Yes" if rear_det else "No",
                onset_str,
                f"{continuity:.1f}%",
                f"{mean_conf:.3f}",
            ]
        )

        # Track active audio stats
        af = CACHE_DIR / f"{ev}_audio_1_audio.jsonl"
        ev_has_audio_det = False
        if af.exists():
            with open(af, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    total_audio_windows += 1
                    arec = json.loads(line)
                    if arec.get("detections"):
                        total_audio_train_dets += 1
                        ev_has_audio_det = True
        if ev_has_audio_det and "train_events" in ev and "no_train" not in ev:
            audio_det_events += 1

    write_table_files(
        table_id="table04_vision_layerb_performance",
        title="Table 4: Single-Camera Vision Performance Across 27 Real Events (B0)",
        headers=[
            "Event ID",
            "Front Detected",
            "Side Detected",
            "Rear Detected",
            "Onset Latency",
            "Continuity Rate",
            "Mean Conf",
        ],
        rows=b0_rows,
        output_dir=out,
    )

    # Table 5: Audio Performance on Layer B (B1)
    write_table_files(
        table_id="table05_audio_layerb_performance",
        title="Table 5: Standalone Audio Performance on Real-World Embedded Audio (B1)",
        headers=["Metric", "Empirical Value on Layer B", "Evaluation Note"],
        rows=[
            [
                "Total Evaluated Audio Streams",
                "27 active audio streams (1 per event)",
                "Extracted 16kHz mono PCM",
            ],
            [
                "Total Analyzed Windows (1.0s/0.5s)",
                f"{total_audio_windows:,} windows",
                "Sliding Log-Mel windows",
            ],
            [
                "Positive Acoustic Horn Windows",
                f"{total_audio_train_dets:,} detections",
                f"T* = 0.3700 ({total_audio_train_dets / max(1, total_audio_windows):.1%})",
            ],
            [
                "Event-Level Acoustic Recall (train)",
                f"{audio_det_events}/23 events ({audio_det_events / 23:.1%})",
                "Horn sound present in event_004, event_017, event_018",
            ],
            [
                "Gate Safety Authorization",
                "0 opening commands",
                "Verified 100% adherence to INV-1 (supporting only)",
            ],
        ],
        output_dir=out,
    )

    # Table 6: Modality Comparison (B0-B4)
    write_table_files(
        table_id="table06_modality_comparison",
        title="Table 6: Cross-Modality Benchmark Comparison (B0 through B4)",
        headers=[
            "Condition ID",
            "Sensory Modalities",
            "Temporal / State Policy",
            "Actuation Rate (Train)",
            "Actuation Rate (No-Train)",
            "MTR [95% CI]",
            "POR [95% CI]",
        ],
        rows=[
            [
                "B0",
                "Front Vision Only",
                "Stateless 1-frame threshold",
                "100.0% (23/23)",
                "100.0% (3/3)*",
                "Blocked (GT Unapproved)",
                "Blocked (GT Unapproved)",
            ],
            [
                "B1",
                "Audio Only",
                "Stateless horn detection",
                "0.0% (0/23)**",
                "0.0% (0/3)",
                "Blocked (GT Unapproved)",
                "Blocked (GT Unapproved)",
            ],
            [
                "B2",
                "Dual Vision + Audio",
                "Stateless 3-frame persistence",
                "100.0% (23/23)",
                "100.0% (3/3)*",
                "Blocked (GT Unapproved)",
                "Blocked (GT Unapproved)",
            ],
            [
                "B3",
                "Dual Vision Only",
                "Temporal filtering, stateless",
                "100.0% (23/23)",
                "100.0% (3/3)*",
                "Blocked (GT Unapproved)",
                "Blocked (GT Unapproved)",
            ],
            [
                "B4",
                "Dual Vision + Audio",
                "Temporal + State Machine",
                "100.0% (23/23)",
                "100.0% (3/3)*",
                "Blocked (GT Unapproved)",
                "Blocked (GT Unapproved)",
            ],
        ],
        output_dir=out,
    )

    # Table 7: Temporal Comparison
    write_table_files(
        table_id="table07_temporal_comparison",
        title="Table 7: Impact of Temporal Evidence Filtering on Detection Jitter",
        headers=[
            "Temporal Metric",
            "Raw Independent Frames (B0)",
            "Temporal Filtering (B3)",
            "Full Policy (B4) / Gain",
        ],
        rows=[
            ["Mean Detection Continuity", "76.4%", "91.8%", "+15.4% continuity gain"],
            [
                "Chattering Events (Whole Cohort N=23)",
                "21 events (91.3%)",
                "17 events (73.9%)",
                "0 events (100% eliminated in B4)",
            ],
            [
                "Chattering Events (Observable Tail N=22)",
                "20 events (90.9%)",
                "16 events (72.7%)",
                "0 events (event_005 excluded due to censoring)",
            ],
            ["Mean Warning Confirmation Latency", "0.20s", "0.40s", "0.40s (confirm_frames=2)"],
            [
                "Premature Openings Caused by Dropouts",
                "Severe chattering in B0/B3",
                "Partial smoothing in B3",
                "0 events (100% eliminated by state machine)",
            ],
        ],
        output_dir=out,
    )

    # Table 8: Multimodal Fusion Results (B4 Full Policy)
    b4_rows = []
    for ev in events_27:
        b4_eval = b4_singles.get(ev)
        closed_s = f"{b4_eval['total_closed_s']:.1f}s" if b4_eval else "N/A"
        is_train = "train_events" in ev and "no_train" not in ev
        is_engine = "engine_events" in ev

        if is_train:
            detected = "Yes"
            premature = "Blocked (GT Unapproved)"
            lifecycle = "Yes"
            failure_codes = "None"
        elif is_engine:
            detected = "Yes"
            premature = "Blocked (GT Unapproved - Censored)"
            lifecycle = "Yes"
            failure_codes = "None"
        else:
            detected = "Yes (False Alarm)"
            premature = "N/A (No Train)"
            lifecycle = "N/A (Nuisance)"
            failure_codes = "F18 (Clutter FP)"

        b4_rows.append(
            [
                ev,
                detected,
                premature,
                closed_s,
                lifecycle,
                failure_codes,
            ]
        )

    write_table_files(
        table_id="table08_multimodal_fusion_b4",
        title="Table 8: Event-by-Event Safety Replay Outcomes Under B4 Proposed Policy",
        headers=[
            "Event ID",
            "Detected",
            "Premature Opening",
            "Gate Closed Duration",
            "Lifecycle Completed",
            "Failure Codes",
        ],
        rows=b4_rows,
        output_dir=out,
    )

    # Table 9: Primary Safety Endpoints Results
    cond_labels = [
        ("B0", "Vision Only (raw frames)", "original"),
        ("B1", "Audio Only (no vision)", "original"),
        ("B2", "Vision + Audio (stateless)", "original"),
        ("B3", "Temporal Evidence (dual vision)", "original"),
        ("B4", "Full Proposed Policy", "original"),
        ("B5a", "Camera 1 Intermittent Dropout", "original"),
        ("B5b", "Camera 1 Permanent Dropout", "original"),
        ("B5c", "Camera 1 Temporal Delay", "original"),
        ("B6a", "Camera 2 Rear Dropout", "original"),
        ("B6b (Original)", "Dual Camera Blackout (Flawed IDLE Fail-Safe)", "original_b6b"),
        ("B6b (Corrected)", "Dual Camera Blackout (Corrected FAULT_FAIL_SAFE)", "corrected_b6b"),
        ("B6c", "Camera Rate Asymmetry", "original"),
        ("B7a", "Audio Loss Robustness", "original"),
        ("B7b (Original)", "Dropped Frames 30% (Flawed Injector: 100% Drop)", "original_b7b"),
        ("B7b (Corrected)", "Dropped Frames 30% (Corrected Deterministic PRNG)", "corrected_b7b"),
        ("B7c", "False Detection Noise", "original"),
        ("B7d", "Timestamp Disorder", "original"),
        ("B7e", "Stale Timestamps", "original"),
        ("B7f (Original)", "Compound Audio Loss + 10% Drop (Flawed Injector)", "original_b7f"),
        ("B7f (Corrected)", "Compound Audio Loss + 10% Drop (Corrected PRNG)", "corrected_b7f"),
    ]
    t9_rows = []
    CORRECTED_EXP_DIR = EXP_DIR / "corrected_run"

    for c_id, c_desc, source_mode in cond_labels:
        base_id = c_id.split()[0]
        if source_mode == "original":
            sp = EXP_DIR / base_id / "summary.json"
        elif source_mode in ("original_b6b", "original_b7b", "original_b7f"):
            sp = EXP_DIR / base_id / "summary.json"
        else:
            sp = CORRECTED_EXP_DIR / base_id / "summary.json"

        if sp.exists():
            with open(sp) as f:
                sdata = json.load(f)

            # Ground truth is unapproved: MTR and POR are strictly blocked
            mtr = "Blocked (GT Unapproved)"
            por = "Blocked (GT Unapproved)"

            # Show mean closed duration or operational behavior
            if source_mode == "original_b6b":
                behavior = "0.0s closed (Failed Fail-Safe in IDLE)"
            elif source_mode == "corrected_b6b":
                behavior = "48.3s mean closed (FAULT_FAIL_SAFE @ 0.4s)"
            elif source_mode in ("original_b7b", "original_b7f"):
                behavior = "0.0s closed (100% Injected Drop)"
            elif source_mode in ("corrected_b7b", "corrected_b7f"):
                behavior = "45.2s mean closed (PRNG Drop Compensated)"
            else:
                behavior = "Normal Safe Operation"

            t9_rows.append([c_id, c_desc, sdata["eligible_events"], behavior, mtr, por])

    write_table_files(
        table_id="table09_primary_safety_endpoints",
        title="Table 9: Primary Safety Endpoints Summary Across Benchmark Conditions",
        headers=[
            "Condition",
            "Description",
            "Eligible Events",
            "Operational Gate Behavior",
            "Missed-Train Rate (MTR)",
            "Premature-Opening Rate (POR)",
        ],
        rows=t9_rows,
        output_dir=out,
    )

    # Table 10: Failure Injection Results (B5-B7)
    write_table_files(
        table_id="table10_failure_injection_results",
        title="Table 10: Fault-Injection Resilience and Safety Invariant Verification",
        headers=[
            "Scenario ID",
            "Failure Perturbation Mode",
            "Events",
            "Operational Gate State",
            "FAULT_FAIL_SAFE Entered",
            "Invariant Violations",
            "Audit Note",
        ],
        rows=[
            [
                "B5a",
                "Camera 1 Dropout (Full Event)",
                "27",
                "Closed during passage",
                "Degraded Operation",
                "0",
                "Single camera coverage maintained",
            ],
            [
                "B5b",
                "Camera 1 Dropout (Midway 30-70%)",
                "27",
                "Closed during passage",
                "Degraded Operation",
                "0",
                "Single camera coverage maintained",
            ],
            [
                "B5c",
                "Camera 1 Flapping (2s on/2s off)",
                "27",
                "Closed during passage",
                "Degraded Operation",
                "0",
                "Camera toggling smoothed by tracker",
            ],
            [
                "B6a",
                "Camera 2 Dropout (Full Event)",
                "27",
                "Held Closed Conservatively",
                "Degraded Operation",
                "0",
                "Clearance dwell timeout holds gate closed",
            ],
            [
                "B6b (Original)",
                "Both Cameras Fail (Simultaneous)",
                "27",
                "OPEN (0.0s closed)",
                "FAILED (Remained in IDLE)",
                "Fail-Safe Violation",
                "Identified in forensic audit",
            ],
            [
                "B6b (Corrected)",
                "Both Cameras Fail (Simultaneous)",
                "27",
                "CLOSED (48.3s mean)",
                "Yes (27/27 @ 0.4s)",
                "0",
                "Fixed via IDLE loss counter transition",
            ],
            [
                "B6c",
                "Both Cameras Fail (Sequential)",
                "27",
                "CLOSED via timeout",
                "Yes (27/27)",
                "0",
                "Secondary failure handled in active state",
            ],
            [
                "B7a",
                "Audio Dropout (Complete Loss)",
                "27",
                "Closed during passage",
                "Normal Vision Operation",
                "0",
                "INV-1 audio independence verified",
            ],
            [
                "B7b (Original)",
                "Dropped Frames (30% Random)",
                "27",
                "OPEN (0.0s closed)",
                "No (No frames received)",
                "Test Failure",
                "Injector bug: any() dropped 100%",
            ],
            [
                "B7b (Corrected)",
                "Dropped Frames (30% Random)",
                "27",
                "Closed during passage",
                "Normal Operation",
                "0",
                "Deterministic PRNG: ~30.0% actual drop",
            ],
            [
                "B7c",
                "False Detection Noise (0.85 conf)",
                "27",
                "Closed conservatively",
                "Warning Triggered",
                "0",
                "Clutter handled safely",
            ],
            [
                "B7d",
                "Timestamp Out-of-Order Swaps",
                "27",
                "Closed during passage",
                "Rejected by Rule 8",
                "0",
                "Temporal ordering enforced",
            ],
            [
                "B7e",
                "Stale Timestamps (2s Midway)",
                "27",
                "Closed during passage",
                "Rejected by Tracker",
                "0",
                "Stale sensor timeout enforced",
            ],
            [
                "B7f (Original)",
                "Compound Audio Loss + 10% Drop",
                "27",
                "OPEN (0.0s closed)",
                "No (No frames received)",
                "Test Failure",
                "Injector bug: any() dropped 100%",
            ],
            [
                "B7f (Corrected)",
                "Compound Audio Loss + 10% Drop",
                "27",
                "Closed during passage",
                "Normal Operation",
                "0",
                "Deterministic PRNG: ~10.0% actual drop",
            ],
        ],
        output_dir=out,
    )

    # Table 11: Per-Event Evaluation Summary
    b11_rows = []
    for ev in events_27:
        b4_eval = b4_singles.get(ev)
        b0_eval = b0_singles.get(ev)
        closed_s = f"{b4_eval['total_closed_s']:.1f}s" if b4_eval else "N/A"
        is_train = "train_events" in ev and "no_train" not in ev
        is_engine = "engine_events" in ev
        cohort = (
            "Train (N=23)"
            if is_train
            else ("Engine (N=1)" if is_engine else "Negative Control (N=3)")
        )
        outcome = (
            "Correct Safe Lifecycle"
            if (is_train or is_engine)
            else "Nuisance False Alarm Actuation (FAR=100%)"
        )
        b11_rows.append(
            [
                ev,
                closed_s,
                cohort,
                "Detection Active (Chattering)" if b0_eval else "N/A",
                outcome,
                "Safe Degraded Operation",
                "None" if (is_train or is_engine) else "F18 (Static Clutter)",
            ]
        )

    write_table_files(
        table_id="table11_per_event_summary",
        title="Table 11: Per-Event Comprehensive Replay Evaluation Summary",
        headers=[
            "Event ID",
            "Closed Duration",
            "Cohort",
            "B0 Outcome",
            "B4 Outcome",
            "B5 Outcome",
            "B4 Failure Codes",
        ],
        rows=b11_rows,
        output_dir=out,
    )

    # Table 12: Failure Analysis Summary
    write_table_files(
        table_id="table12_failure_analysis_taxonomy",
        title="Table 12: Failure Mode Taxonomy (F01–F18) Distribution and Root Causes",
        headers=[
            "Failure Code",
            "Category Description",
            "Total Occurrences",
            "Primary Condition",
            "Root Cause Analysis",
        ],
        rows=[
            [
                "F01",
                "Missed Approach",
                "Blocked (GT Unapproved)",
                "None in Simulation",
                "Robust visual and acoustic coverage across events",
            ],
            [
                "F08",
                "Detection Dropout",
                "Mitigated by buffer",
                "B0 (Stateless)",
                "Compensated by dual-camera and temporal smoothing in B3/B4",
            ],
            [
                "F10",
                "Incorrect Clearance",
                "0 in B4..B7",
                "B0, B2 (Stateless)",
                "Prevented 100% by positive rear confirmation and clearance dwell",
            ],
            [
                "F14",
                "Camera Failure Undetected",
                "0 occurrences",
                "None",
                "SourceTracker correctly detected 100% of heartbeat timeouts",
            ],
            [
                "F16",
                "Timestamp Disorder",
                "27 occurrences in B7d",
                "B7d (Perturbation)",
                "Intentionally injected out-of-order frames, safely rejected by Rule 8",
            ],
            [
                "F17",
                "Premature Opening",
                "Blocked (GT Unapproved)",
                "None in Simulation",
                "Eliminated in logic by state machine latching and dwell timers",
            ],
            [
                "F18",
                "False Alarm (Negative Control)",
                "3 occurrences in no-train",
                "All vision conditions",
                "Static trackside machinery misclassified by YOLOv8n",
            ],
        ],
        output_dir=out,
    )

    print(f"Generated all 12 publication tables (MD, CSV, LaTeX) empirically in {out}")


def descriptive_rows_digest(rows) -> str:
    """Canonical constructed row binding; not authority or execution attestation."""
    import hashlib
    from dataclasses import asdict

    return hashlib.sha256(
        json.dumps(
            [asdict(row) for row in rows], sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def render_descriptive_support(rows=(), *, expected_digest=None) -> str:
    """Pure Markdown: absent empirical results or explicitly constructed examples only.

    No files, caches or models are opened. Real results need a separate receipt
    verification adapter; a boolean `approved` flag cannot enable this renderer.
    """
    from railway_detection.evaluation.metrics import summarize_descriptive_rows

    if type(rows) is not tuple:
        raise ValueError("immutable constructed rows required")
    if rows:
        if descriptive_rows_digest(rows) != expected_digest:
            raise ValueError("independently retained row digest mismatch")
        if any(not row.provenance.startswith("synthetic:") for row in rows):
            raise ValueError("real or unverified results cannot enter constructed renderer")
    summaries = summarize_descriptive_rows(rows)
    lines = [
        "# Descriptive benchmark manuscript support — DRAFT",
        "",
        "Venue: undecided. Author roster: pending actual human author agreement.",
        "",
        "AI use: Codex assisted code, tests and draft preparation; human authors must "
        "verify the final account of use and take responsibility for the manuscript.",
        "",
        "Design: fixed-site finite-cohort descriptive benchmark; independent front/back "
        "camera clocks. M4 primary; M5 integer failure companion; MTR requires its "
        "separate lead-in screen. Fused analysis is separately scoped exploratory work.",
        "",
        "Counts follow each metric's observed denominator. Censored/unavailable points "
        "carry reasons; no imputation, inferential p-values or population claims.",
        "",
        "Physical roadway-entry evidence and full occupancy remain deferred. "
        "Frozen models, policy constants and historical tables retain their recorded scope.",
        "",
        "Real-data evaluation: UNAVAILABLE — no completed real evaluation is established "
        "by this report. No empirical outcome or safety/deployment claim follows.",
        "",
    ]
    if not rows:
        lines += ["No empirical results supplied. Outcome cells remain UNAVAILABLE."]
    else:
        lines += [
            "## CONSTRUCTED DEMONSTRATION ONLY — NOT EMPIRICAL RESULTS",
            "",
            "Retained row SHA256: `" + expected_digest + "`.",
            "",
            "| Cohort | Camera | Condition | Metric | Numerator | Denominator | Exclusions |",
            "|---|---|---|---|---:|---:|---|",
        ]

        def cell(value):
            return (
                str(value)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("|", "&#124;")
                .replace("\n", " ")
                .replace("\r", " ")
            )

        for summary in summaries:
            values = [
                summary[k]
                for k in (
                    "cohort",
                    "camera",
                    "condition",
                    "metric",
                    "numerator",
                    "denominator",
                    "excluded_by_reason",
                )
            ]
            lines.append("| " + " | ".join(cell(v) for v in values) + " |")
    return "\n".join(lines) + "\n"


def generate_all_tables(*args, **kwargs) -> None:
    raise PermissionError(
        "Historical templates contain unverified fixed claims. Real publication tables require "
        "a verified receipt adapter; use render_descriptive_support for a results-absent draft "
        "or constructed demonstration. No legacy cache traversal is activated."
    )


if __name__ == "__main__":
    generate_all_tables()
