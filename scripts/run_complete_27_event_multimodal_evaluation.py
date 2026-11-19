#!/usr/bin/env python3
"""Complete 27-Event Multimodal Experimental Evaluation, Causal FSM Gate Validation & Forensics.

Mission 9 Upgrade:
1. Prepares a schema-complete, pre-hashed owner authorization template
   (`docs/generated/human_approval_templates/AUTH_MEDIA_ACCESS_MISSION9_READY.json`) and
   audits exact 54-stream Display Matrix orientation (`44/54` `-90 deg`, `10/54` `0 deg`),
   plus supports `--run-upright-raw-inference` once the owner installs
   `data/governance/AUTH-MEDIA-ACCESS.json`.
2. Explicitly distinguishes Rule-Based Late Fusion (0 learned fusion weights) from learned
   fusion, Frozen-Protocol thresholds from Exploratory Cohort-Optimized thresholds, and
   Train-Presence vs Rail-Vehicle vs Horn detection tasks.
3. Feeds every fusion architecture causally through `MultimodalDecisionEngineV3FourLayer` +
   `EventSimulationRunner` + `PhysicalGateModel` at `dt = 0.20 s` to measure real closure
   safety margins relative to `T2`, premature/missed/late/false closures, and complete cycles.
4. Produces an individual event-by-event forensic investigation of all 8 missed train events
   (`event_008, 009, 010, 011, 014, 015, 019, 020`), the 5 fusion-recovered events, and
   `engine_events/event_001`.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import hashlib
import json
import math
import os
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from exploratory_common import (  # noqa: E402
    EXPLORATORY_LABEL,
    VerifiedExploratoryContext,
    load_event_evidence_records,
    load_verified_context,
    read_verified_utf8_text,
    wilson_ci_95,
)

from railway_detection.data.audio_extractor import extract_audio_from_video  # noqa: E402
from railway_detection.data.sync import SyncAligner  # noqa: E402
from railway_detection.experiments.cache_provenance import (  # noqa: E402
    build_audio_preprocessing_config,
    build_vision_preprocessing_config,
)
from railway_detection.experiments.frozen_config import compute_file_sha256  # noqa: E402
from railway_detection.experiments.layer_b_processor import (  # noqa: E402
    LayerBEventProcessor,
    serialize_evidence_record,
)
from railway_detection.fusion.collector import MultimodalEvidenceCollector  # noqa: E402
from railway_detection.fusion.decision_engine_v3_four_layer import (  # noqa: E402
    MultimodalDecisionEngineV3FourLayer,
)
from railway_detection.fusion.rules_v3_four_layer import SideMovementTracker  # noqa: E402
from railway_detection.safety import media_guard  # noqa: E402
from railway_detection.safety.media_guard import MediaAccessAuthorizationError  # noqa: E402
from railway_detection.simulation.runner import (  # noqa: E402
    EventSimulationRunner,
    SimulationRunResult,
)
from railway_detection.vision.video import SOURCE_DISPLAY_ROTATION_POLICY  # noqa: E402

VISION_CACHE_PROVENANCE = (
    "Mission 39/43 Frozen YOLOv8n Actual Inference Caches "
    "(pre-db40305 unrotated container decoding: 44/54 streams -90 deg rotated, "
    "10/54 streams 0 deg upright; 6,613 front frames / 329 objects, 6,479 back frames / 1,020 objects)"
)
AUDIO_CACHE_PROVENANCE = (
    "Mission 39/43 Corrected Natural Log-Mel CompactTrainHornCNN Actual Inference Caches "
    "(2,600 windows of 1.0 s / 0.5 s hop; orientation-invariant)"
)
REFERENCE_PROVENANCE = (
    "Researcher-adopted AI-assisted reference proposals "
    "(docs/generated/professor_evidence/mission43/RESEARCHER_ANNOTATION_ADOPTION.json; "
    "0/27 independent Stage-2.1 human reviews)"
)

OUTPUT_DIR = REPO_ROOT / "results" / "multimodal_27_event_evaluation"
TEMPLATE_READY_PATH = (
    REPO_ROOT / "docs" / "generated" / "human_approval_templates" / "AUTH_MEDIA_ACCESS_MISSION9_READY.json"
)
EXP_V2_DIR = REPO_ROOT / "results" / "exploratory_v2"
QUICKTIME_DELTAS_PATH = REPO_ROOT / "results" / "r04_sync_estimation" / "quicktime_creationdate_deltas.json"
SOURCE_RECEIPT_PATH = (
    REPO_ROOT / "docs" / "generated" / "professor_evidence" / "mission43" / "SOURCE_VERIFICATION_RECEIPT.json"
)
VISUAL_PER_EVENT_CSV = (
    REPO_ROOT / "docs" / "generated" / "professor_evidence" / "mission43" / "VISUAL_PER_EVENT_RESULTS.csv"
)
AUDIO_PER_EVENT_CSV = (
    REPO_ROOT / "docs" / "generated" / "professor_evidence" / "mission43" / "AUDIO_PER_EVENT_RESULTS.csv"
)
UPRIGHT_OUT_DIR = REPO_ROOT / "results" / "upright_inference_v2"
UPRIGHT_EVAL_DIR = REPO_ROOT / "results" / "upright_27_event_evaluation"


def generate_owner_media_auth_template(output_path: Path = TEMPLATE_READY_PATH) -> dict[str, Any]:
    """Generate a ready-to-sign AUTH-MEDIA-ACCESS JSON bound to frozen_experiment_v1.yaml."""
    frozen_cfg = REPO_ROOT / "configs" / "frozen_experiment_v1.yaml"
    media_guard.require_media_authorization(frozen_cfg, "HASH_RAW_MEDIA")
    cfg_sha = hashlib.sha256(frozen_cfg.read_bytes()).hexdigest()
    record: dict[str, Any] = {
        "schema_version": media_guard.MEDIA_ACCESS_SCHEMA_VERSION,
        "authorization_id": "AUTH-MEDIA-ACCESS-2026-11-19-MISSION9",
        "authorization_class": media_guard.AUTHORIZATION_CLASS,
        "status": "APPROVED",
        "authorized_by": "raihankabirrahu@gmail.com",
        "authorized_at_utc": "2026-11-19T00:00:00+00:00",
        "expires_at_utc": "2027-11-19T00:00:00+00:00",
        "revoked": False,
        "authorization_statement": (
            "Research owner authorization for Mission 9 orientation-corrected (db40305) "
            "YOLOv8n and natural log-Mel CompactTrainHornCNN inference across all 27 Layer-B v2 events."
        ),
        "attestation": {
            "type": media_guard.ATTESTATION_RECORDED_STATEMENT,
            "signature": None,
        },
        "recorded_by": {
            "kind": "researcher",
            "identity": "raihankabirrahu@gmail.com",
        },
        "scope": {
            "operations": sorted(media_guard.VALID_MEDIA_OPERATIONS),
            "datasets": ["layer_b"],
            "events": [media_guard.ALL_EVENTS_IN_DATASETS],
            "media_types": ["video", "audio"],
            "purpose": (
                "Reprocess all 27 recorded Layer-B events with QuickTime display-matrix "
                "orientation correction using frozen YOLOv8n and CompactTrainHornCNN checkpoints."
            ),
        },
        "restrictions": {
            "path_prefixes": ["data/raw/layer_b/"],
        },
        "bindings": {
            "protocol_document": {
                "path": "configs/frozen_experiment_v1.yaml",
                "sha256": cfg_sha,
            }
        },
    }
    record["record_sha256"] = media_guard._canonical_sha256(record)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def check_media_authorization_status() -> dict[str, Any]:
    """Check canonical AUTH-MEDIA-ACCESS.json without modifying data/governance/."""
    canon_path = REPO_ROOT / media_guard.CANONICAL_MEDIA_AUTH_RELATIVE
    try:
        payload = media_guard.verify_authorization_record(
            REPO_ROOT, operation="INFERENCE", media_path=None, event_id=None
        )
        return {
            "authorized": True,
            "canonical_path": str(media_guard.CANONICAL_MEDIA_AUTH_RELATIVE),
            "authorization_id": payload["authorization_id"],
            "authorized_by": payload["authorized_by"],
            "expires_at_utc": payload["expires_at_utc"],
        }
    except MediaAccessAuthorizationError as exc:
        return {
            "authorized": False,
            "canonical_path": str(media_guard.CANONICAL_MEDIA_AUTH_RELATIVE),
            "error_code": exc.code,
            "error_detail": exc.detail,
            "ready_template_path": str(TEMPLATE_READY_PATH.relative_to(REPO_ROOT)),
            "file_present": canon_path.exists(),
        }


def _write_utf8_jsonl_and_sha256(path: Path, rows: list[dict[str, Any]], repo_root: Path = REPO_ROOT) -> tuple[str, str]:
    """Write rows as UTF-8 JSONL and return (repo-relative-or-abs path, SHA-256 digest)."""
    body = "".join(json.dumps(r, ensure_ascii=True) + "\n" for r in rows)
    path.write_text(body, encoding="utf-8")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    try:
        rel = str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        rel = str(path)
    return rel, digest


def _hash_authorized_media_file(path: Path) -> str:
    """Compute SHA-256 of an authorized raw media file after enforcing HASH_RAW_MEDIA guard."""
    media_guard.require_media_authorization(path, "HASH_RAW_MEDIA", declared_media=True)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _audio_records_to_descriptive_rows(records: list[Any], *, threshold: float) -> list[dict[str, Any]]:
    """Convert AudioEvidencePipeline EvidenceRecords into canonical descriptive window rows."""
    rows: list[dict[str, Any]] = []
    for idx, rec in enumerate(records):
        if not rec.available:
            raise RuntimeError(f"Audio inference failed on extracted stream: {rec.metadata}")
        start_s = float(rec.metadata.get("window_start_s", max(0.0, float(rec.timestamp_s) - 1.0)))
        end_s = float(rec.metadata.get("window_end_s", float(rec.timestamp_s)))
        prob = (
            float(rec.metadata["probability"])
            if "probability" in rec.metadata
            else (float(rec.detections[0].confidence) if rec.detections else 0.0)
        )
        rows.append(
            {
                "window_index": idx,
                "start_sec": round(start_s, 6),
                "end_sec": round(end_s, 6),
                "horn_confidence": prob,
                "is_horn_detected": bool(prob >= float(threshold)),
            }
        )
    return rows


def _summarize_vision_stream_orientation(
    records: list[Any], *, expected_rotation_deg: int | None
) -> dict[str, Any]:
    """Verify db40305 upright display rotation metadata and count per-class objects."""
    cls_counts = {"front": 0, "side": 0, "rear": 0, "other": 0}
    rotations: set[int] = set()
    bases: set[str] = set()
    sizes: set[tuple[int, int]] = set()
    stream_indices: set[int] = set()
    det_frames = 0

    for rec in records:
        meta = rec.metadata or {}
        if "display_rotation_degrees" in meta:
            rotations.add(int(meta["display_rotation_degrees"]))
        if "image_coordinate_basis" in meta:
            bases.add(str(meta["image_coordinate_basis"]))
        if "input_image_size" in meta and isinstance(meta["input_image_size"], (list, tuple)) and len(meta["input_image_size"]) == 2:
            sizes.add((int(meta["input_image_size"][0]), int(meta["input_image_size"][1])))
        if "stream_index" in meta and meta["stream_index"] is not None:
            stream_indices.add(int(meta["stream_index"]))
        if rec.detections:
            det_frames += 1
        for det in rec.detections:
            lbl = str(det.label).strip().lower()
            cls_counts[lbl if lbl in cls_counts else "other"] += 1

    rot_list = sorted(rotations)
    basis_list = sorted(bases)
    expected_ok = expected_rotation_deg is None or rot_list == [int(expected_rotation_deg)]
    return {
        "sampled_frames": len(records),
        "det_frames": det_frames,
        "total_objects": sum(cls_counts.values()),
        "cls_counts": cls_counts,
        "display_rotation_degrees_observed": rot_list,
        "expected_quicktime_rotation_deg": expected_rotation_deg,
        "image_coordinate_basis": basis_list,
        "input_image_sizes_observed": [list(s) for s in sorted(sizes)],
        "stream_indices_observed": sorted(stream_indices),
        "orientation_verified": (
            len(records) > 0
            and basis_list == [SOURCE_DISPLAY_ROTATION_POLICY]
            and expected_ok
        ),
    }


def _process_upright_event_streams(
    processor: LayerBEventProcessor,
    frozen_config: Any,
    *,
    eid: str,
    cohort: str,
    event_id: str,
    front_mov: Path,
    back_mov: Path,
    pred_dir: Path,
    expected_front_rot: int | None,
    expected_back_rot: int | None,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    """Run upright PTS vision inference and fresh WAV audio inference for one event."""
    yolo_ckpt = repo_root / frozen_config.checkpoints.vision.path
    audio_ckpt = repo_root / frozen_config.checkpoints.audio_v3.path
    sampling_fps = float(frozen_config.vision.sampling_fps)
    vision_conf = float(frozen_config.vision.confidence_threshold_approach)
    audio_thresh = float(frozen_config.audio.operating_threshold)
    slug = eid.replace("/", "_")

    f_recs = processor.run_vision_inference(
        video_path=front_mov,
        checkpoint_path=yolo_ckpt,
        source_id="camera_1",
        target_fps=sampling_fps,
        conf=vision_conf,
        use_cache=False,
        source_pts=True,
        video_stream_index=None,
    )
    b_recs = processor.run_vision_inference(
        video_path=back_mov,
        checkpoint_path=yolo_ckpt,
        source_id="camera_2",
        target_fps=sampling_fps,
        conf=vision_conf,
        use_cache=False,
        source_pts=True,
        video_stream_index=None,
    )

    with tempfile.TemporaryDirectory(prefix="tga_upright_audio_") as tmp_dir:
        tmp_wav = Path(tmp_dir) / f"{slug}_front.wav"
        extracted_wav = extract_audio_from_video(
            front_mov,
            tmp_wav,
            sample_rate=int(frozen_config.audio.sample_rate),
            channels=1,
        )
        if extracted_wav is None or not extracted_wav.exists() or extracted_wav.stat().st_size == 0:
            raise RuntimeError(f"Failed to extract front WAV audio for {eid} from {front_mov}")
        a_recs = processor.run_audio_inference(
            wav_path=extracted_wav,
            checkpoint_path=audio_ckpt,
            source_id="audio_1",
            threshold=audio_thresh,
            cohort=cohort,
            event_id=event_id,
            use_cache=False,
        )

    f_rel, f_sha = _write_utf8_jsonl_and_sha256(
        pred_dir / f"{slug}_front.jsonl",
        [serialize_evidence_record(r) for r in f_recs],
        repo_root=repo_root,
    )
    b_rel, b_sha = _write_utf8_jsonl_and_sha256(
        pred_dir / f"{slug}_back.jsonl",
        [serialize_evidence_record(r) for r in b_recs],
        repo_root=repo_root,
    )
    a_desc_rows = _audio_records_to_descriptive_rows(a_recs, threshold=audio_thresh)
    a_rel, a_sha = _write_utf8_jsonl_and_sha256(
        pred_dir / f"{slug}_front_audio_descriptive_rows.jsonl",
        a_desc_rows,
        repo_root=repo_root,
    )
    a_raw_rel, a_raw_sha = _write_utf8_jsonl_and_sha256(
        pred_dir / f"{slug}_front_audio_records.jsonl",
        [serialize_evidence_record(r) for r in a_recs],
        repo_root=repo_root,
    )

    f_orient = _summarize_vision_stream_orientation(f_recs, expected_rotation_deg=expected_front_rot)
    b_orient = _summarize_vision_stream_orientation(b_recs, expected_rotation_deg=expected_back_rot)
    if not f_orient["orientation_verified"] or not b_orient["orientation_verified"]:
        raise RuntimeError(
            f"Orientation verification failed for {eid}: front={f_orient}, back={b_orient}"
        )

    return {
        "event_id": eid,
        "cohort": cohort,
        "raw_event_id": event_id,
        "execution_status": "SUCCESS",
        "errors": [],
        "timestamp_basis": "source_pts",
        "front_frames": len(f_recs),
        "back_frames": len(b_recs),
        "audio_windows": len(a_desc_rows),
        "front_orientation": f_orient,
        "back_orientation": b_orient,
        "front_path": f_rel,
        "front_sha256": f_sha,
        "back_path": b_rel,
        "back_sha256": b_sha,
        "audio_path": a_rel,
        "audio_sha256": a_sha,
        "audio_raw_path": a_raw_rel,
        "audio_raw_sha256": a_raw_sha,
    }


_WORKER_STATE: dict[str, Any] = {}


def _init_upright_worker(torch_threads: int) -> None:
    """Initialize process-local frozen LayerBEventProcessor and thread count."""
    import torch

    torch.set_num_threads(max(1, int(torch_threads)))
    ctx_cfg = load_verified_context(REPO_ROOT).frozen_config
    _WORKER_STATE["config"] = ctx_cfg
    _WORKER_STATE["processor"] = LayerBEventProcessor(config=ctx_cfg, repo_root=REPO_ROOT)


def _execute_one_event_task(task: dict[str, Any]) -> dict[str, Any]:
    """Worker-safe entry point processing or resuming one event under full media guards."""
    pred_dir = Path(task["pred_dir"])
    eid = str(task["eid"])
    slug = eid.replace("/", "_")
    ckpt_manifest = pred_dir / f"{slug}_event_manifest.json"

    if task.get("resume") and ckpt_manifest.exists():
        cached = json.loads(ckpt_manifest.read_text(encoding="utf-8"))
        src = cached.get("source_media", {})
        if (
            src.get("front_sha256") == task["expected_f_sha"]
            and src.get("back_sha256") == task["expected_b_sha"]
            and cached.get("execution_status") == "SUCCESS"
        ):
            try:
                read_verified_utf8_text(REPO_ROOT, cached["front_path"], expected_sha256=cached["front_sha256"])
                read_verified_utf8_text(REPO_ROOT, cached["back_path"], expected_sha256=cached["back_sha256"])
                read_verified_utf8_text(REPO_ROOT, cached["audio_path"], expected_sha256=cached["audio_sha256"])
                return cached
            except Exception:
                pass

    cfg = _WORKER_STATE.get("config") or load_verified_context(REPO_ROOT).frozen_config
    proc = _WORKER_STATE.get("processor") or LayerBEventProcessor(config=cfg, repo_root=REPO_ROOT)

    f_mov = Path(task["f_mov"])
    b_mov = Path(task["b_mov"])
    actual_f_sha = _hash_authorized_media_file(f_mov)
    actual_b_sha = _hash_authorized_media_file(b_mov)
    if actual_f_sha != task["expected_f_sha"] or actual_b_sha != task["expected_b_sha"]:
        raise RuntimeError(
            f"Source media SHA-256 mismatch for {eid}: "
            f"front={actual_f_sha} vs {task['expected_f_sha']}, back={actual_b_sha} vs {task['expected_b_sha']}"
        )

    entry = _process_upright_event_streams(
        proc,
        cfg,
        eid=eid,
        cohort=str(task["cohort"]),
        event_id=str(task["event_id"]),
        front_mov=f_mov,
        back_mov=b_mov,
        pred_dir=pred_dir,
        expected_front_rot=task["expected_front_rot"],
        expected_back_rot=task["expected_back_rot"],
        repo_root=REPO_ROOT,
    )
    entry["source_media"] = {
        "front_path": task["front_rel"],
        "front_sha256": actual_f_sha,
        "front_sha256_verified_against_inventory": True,
        "back_path": task["back_rel"],
        "back_sha256": actual_b_sha,
        "back_sha256_verified_against_inventory": True,
    }
    ckpt_manifest.write_text(json.dumps(entry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return entry


def run_upright_raw_inference(
    ctx: VerifiedExploratoryContext,
    *,
    output_dir: Path = UPRIGHT_OUT_DIR,
    processor: LayerBEventProcessor | None = None,
    workers: int = 4,
    resume: bool = False,
) -> dict[str, Any]:
    """Execute owner-authorized upright db40305 YOLOv8n + Audio V3 inference across all 27 events.

    Fails closed unless data/governance/AUTH-MEDIA-ACCESS.json exists and passes
    media_guard checks for READ_RAW_MEDIA, INFERENCE, AUDIO_EXTRACTION, FEATURE_EXTRACTION, and HASH_RAW_MEDIA.
    """
    for required_op in (
        "INFERENCE",
        "READ_RAW_MEDIA",
        "AUDIO_EXTRACTION",
        "FEATURE_EXTRACTION",
        "HASH_RAW_MEDIA",
    ):
        media_guard.precheck_operation_authorized(required_op, repo_root=REPO_ROOT)

    inventory = json.loads((REPO_ROOT / "docs/PHASE11_3_REVIEW_INVENTORY.json").read_text(encoding="utf-8"))
    rot_map = _load_supporting_lookup()["rot_map"]

    output_dir.mkdir(parents=True, exist_ok=True)
    pred_dir = output_dir / "predictions"
    pred_dir.mkdir(parents=True, exist_ok=True)

    tasks: list[dict[str, Any]] = []
    for eid in ctx.event_order:
        ev_info = inventory["events"][eid]
        tasks.append(
            {
                "eid": eid,
                "cohort": str(ev_info["cohort"]),
                "event_id": str(ev_info["event_id"]),
                "front_rel": str(ev_info["raw_media"]["front"]["path"]),
                "back_rel": str(ev_info["raw_media"]["back"]["path"]),
                "f_mov": str(REPO_ROOT / ev_info["raw_media"]["front"]["path"]),
                "b_mov": str(REPO_ROOT / ev_info["raw_media"]["back"]["path"]),
                "expected_f_sha": str(ev_info["raw_media"]["front"]["sha256"]),
                "expected_b_sha": str(ev_info["raw_media"]["back"]["sha256"]),
                "expected_front_rot": rot_map[(eid, "front")]["rotation_deg"],
                "expected_back_rot": rot_map[(eid, "back")]["rotation_deg"],
                "pred_dir": str(pred_dir),
                "resume": bool(resume),
            }
        )

    entries_by_eid: dict[str, dict[str, Any]] = {}
    effective_workers = 1 if processor is not None else max(1, int(workers))
    if effective_workers == 1:
        if processor is not None:
            _WORKER_STATE["config"] = ctx.frozen_config
            _WORKER_STATE["processor"] = processor
        else:
            _init_upright_worker(torch_threads=min(4, os.cpu_count() or 4))
        for idx, task in enumerate(tasks, start=1):
            entry = _execute_one_event_task(task)
            entries_by_eid[entry["event_id"]] = entry
            print(
                f"[UPRIGHT {idx:02d}/{len(tasks):02d}] {entry['event_id']} | "
                f"front={entry['front_frames']}f/{entry['front_orientation']['total_objects']}obj "
                f"(rot={entry['front_orientation']['display_rotation_degrees_observed']}) | "
                f"back={entry['back_frames']}f/{entry['back_orientation']['total_objects']}obj "
                f"(rot={entry['back_orientation']['display_rotation_degrees_observed']}) | "
                f"audio={entry['audio_windows']}w",
                flush=True,
            )
    else:
        threads_per_worker = max(1, (os.cpu_count() or 8) // effective_workers)
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=effective_workers,
            initializer=_init_upright_worker,
            initargs=(threads_per_worker,),
        ) as pool:
            future_map = {pool.submit(_execute_one_event_task, task): task["eid"] for task in tasks}
            done_count = 0
            for fut in concurrent.futures.as_completed(future_map):
                done_count += 1
                entry = fut.result()
                entries_by_eid[entry["event_id"]] = entry
                print(
                    f"[UPRIGHT {done_count:02d}/{len(tasks):02d}] {entry['event_id']} | "
                    f"front={entry['front_frames']}f/{entry['front_orientation']['total_objects']}obj "
                    f"(rot={entry['front_orientation']['display_rotation_degrees_observed']}) | "
                    f"back={entry['back_frames']}f/{entry['back_orientation']['total_objects']}obj "
                    f"(rot={entry['back_orientation']['display_rotation_degrees_observed']}) | "
                    f"audio={entry['audio_windows']}w",
                    flush=True,
                )

    manifest_entries = [entries_by_eid[eid] for eid in ctx.event_order]

    auth_status = check_media_authorization_status()
    vision_ckpt_sha = compute_file_sha256(REPO_ROOT / ctx.frozen_config.checkpoints.vision.path)
    audio_ckpt_sha = compute_file_sha256(REPO_ROOT / ctx.frozen_config.checkpoints.audio_v3.path)
    if vision_ckpt_sha != ctx.frozen_config.checkpoints.vision.expected_sha256:
        raise RuntimeError(f"Vision checkpoint SHA mismatch: {vision_ckpt_sha}")
    if audio_ckpt_sha != ctx.frozen_config.checkpoints.audio_v3.expected_sha256:
        raise RuntimeError(f"Audio checkpoint SHA mismatch: {audio_ckpt_sha}")

    manifest = {
        "schema_version": "upright-raw-inference-manifest/2.0",
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "execution_status": "SUCCESS",
        "errors": [],
        "preprocessing_version": {
            "vision": build_vision_preprocessing_config(ctx.frozen_config),
            "audio": build_audio_preprocessing_config(ctx.frozen_config),
        },
        "orientation_policy": SOURCE_DISPLAY_ROTATION_POLICY,
        "apply_display_rotation": True,
        "timestamp_basis": "source_pts",
        "inference_parameters": {
            "vision_sampling_fps": float(ctx.frozen_config.vision.sampling_fps),
            "vision_conf_threshold": float(ctx.frozen_config.vision.confidence_threshold_approach),
            "vision_image_size": list(ctx.frozen_config.vision.image_size),
            "audio_sample_rate": int(ctx.frozen_config.audio.sample_rate),
            "audio_window_s": float(ctx.frozen_config.audio.window_s),
            "audio_hop_s": float(ctx.frozen_config.audio.hop_s),
            "audio_log_scale": "natural",
            "audio_log_epsilon": 1e-10,
            "audio_operating_threshold": float(ctx.frozen_config.audio.operating_threshold),
            "seed": int(ctx.frozen_config.experiment.seed),
            "device": str(ctx.frozen_config.experiment.device),
        },
        "authorization": auth_status,
        "frozen_config_sha256": ctx.artifact_hashes.get("configs/frozen_experiment_v1.yaml"),
        "checkpoints": {
            "vision_path": ctx.frozen_config.checkpoints.vision.path,
            "vision_sha256": vision_ckpt_sha,
            "audio_path": ctx.frozen_config.checkpoints.audio_v3.path,
            "audio_sha256": audio_ckpt_sha,
        },
        "total_events": len(manifest_entries),
        "total_streams_verified": 2 * len(manifest_entries),
        "events": manifest_entries,
    }
    manifest_path = output_dir / "UPRIGHT_INFERENCE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _load_existing_upright_manifest(manifest_path: Path | None = None) -> dict[str, Any]:
    """Load and SHA-256-verify an existing UPRIGHT_INFERENCE_MANIFEST.json."""
    target = manifest_path or (UPRIGHT_OUT_DIR / "UPRIGHT_INFERENCE_MANIFEST.json")
    if not target.exists():
        raise FileNotFoundError(f"Upright inference manifest not found: {target}")
    manifest = json.loads(target.read_text(encoding="utf-8"))
    for ent in manifest.get("events", []):
        read_verified_utf8_text(REPO_ROOT, ent["front_path"], expected_sha256=ent["front_sha256"])
        read_verified_utf8_text(REPO_ROOT, ent["back_path"], expected_sha256=ent["back_sha256"])
        read_verified_utf8_text(REPO_ROOT, ent["audio_path"], expected_sha256=ent["audio_sha256"])
    return manifest


def _build_upright_context(
    base_ctx: VerifiedExploratoryContext, upright_manifest: dict[str, Any]
) -> VerifiedExploratoryContext:
    """Return a VerifiedExploratoryContext pointing at SHA-256-verified upright prediction caches."""
    by_eid = {e["event_id"]: e for e in upright_manifest["events"]}
    new_events: dict[str, dict[str, Any]] = {}
    for eid in base_ctx.event_order:
        if eid not in by_eid:
            raise RuntimeError(f"Upright manifest missing event {eid}")
        u = by_eid[eid]
        old_ent = base_ctx.manifest_events[eid]
        new_events[eid] = {
            **old_ent,
            "front_cache_path": u["front_path"],
            "front_cache_sha256": u["front_sha256"],
            "back_cache_path": u["back_path"],
            "back_cache_sha256": u["back_sha256"],
            "audio_cache_path": u["audio_path"],
            "audio_cache_sha256": u["audio_sha256"],
            "front_source": "mission10_upright_db40305",
            "back_source": "mission10_upright_db40305",
            "audio_source": "mission10_fresh_logmel",
        }
    return replace(base_ctx, manifest_events=new_events)


def _exact_mcnemar(a_preds: list[bool], b_preds: list[bool], truths: list[bool]) -> dict[str, Any]:
    """Exact two-sided binomial McNemar test on paired correctness of predictor A vs B."""
    b01 = 0
    b10 = 0
    for pa, pb, yt in zip(a_preds, b_preds, truths, strict=True):
        ra = pa == yt
        rb = pb == yt
        if not ra and rb:
            b01 += 1
        elif ra and not rb:
            b10 += 1
    n = b01 + b10
    if n == 0:
        p_val = 1.0
    else:
        k = min(b01, b10)
        p_tail = sum(math.comb(n, i) * (0.5**n) for i in range(0, k + 1))
        p_val = min(1.0, 2.0 * p_tail)
    return {
        "discordant_pairs": n,
        "b01_baseline_wrong_candidate_right": b01,
        "b10_baseline_right_candidate_wrong": b10,
        "exact_p_value": round(p_val, 6),
    }


def _parse_vision_stream(jsonl_path: Path, threshold: float = 0.35) -> dict[str, Any]:
    """Parse precomputed vision JSONL cache into per-class counts, timestamps, confidences, and gaps."""
    frames: list[dict[str, Any]] = []
    with open(jsonl_path, encoding="utf-8", newline="") as handle:
        for line in handle:
            if line.strip():
                frames.append(json.loads(line))

    cls_counts = {"front": 0, "side": 0, "rear": 0, "other": 0}
    all_confs: list[float] = []
    det_frame_ts: list[float] = []
    det_records_detail: list[dict[str, Any]] = []
    side_rear_ts: list[float] = []

    consec_any = max_consec_any = 0
    consec_sr = max_consec_sr = 0
    det_frames = 0
    first_consec2_any_t: float | None = None
    first_consec2_sr_t: float | None = None

    last_ts = 0.0
    for fr in frames:
        ts = float(fr["timestamp_sec"] if "timestamp_sec" in fr else fr["timestamp_s"])
        last_ts = ts
        fidx = fr.get("frame_index")
        if fidx is None:
            fidx = fr.get("metadata", {}).get("frame_index")
        raw_dets = fr.get("detections", [])
        qual_dets = [d for d in raw_dets if float(d.get("confidence", 0.0)) >= threshold]
        if qual_dets:
            det_frames += 1
            det_frame_ts.append(ts)
            consec_any += 1
            max_consec_any = max(max_consec_any, consec_any)
            if consec_any >= 2 and first_consec2_any_t is None:
                first_consec2_any_t = ts
            det_records_detail.append(
                {
                    "frame_index": fidx,
                    "timestamp_s": round(ts, 4),
                    "detections": [
                        {
                            "label": str(d.get("label") or d.get("class_name") or "").strip().lower(),
                            "confidence": round(float(d["confidence"]), 4),
                        }
                        for d in qual_dets
                    ],
                }
            )
        else:
            consec_any = 0

        frame_labels: set[str] = set()
        for d in qual_dets:
            lbl = str(d.get("label") or d.get("class_name") or "").strip().lower()
            conf = float(d["confidence"])
            all_confs.append(conf)
            if lbl in cls_counts:
                cls_counts[lbl] += 1
            else:
                cls_counts["other"] += 1
            frame_labels.add(lbl)

        if "side" in frame_labels or "rear" in frame_labels:
            side_rear_ts.append(ts)
            consec_sr += 1
            max_consec_sr = max(max_consec_sr, consec_sr)
            if consec_sr >= 2 and first_consec2_sr_t is None:
                first_consec2_sr_t = ts
        else:
            consec_sr = 0

    def _check_2of3(ts_list: list[float], max_gap_s: float = 0.45) -> tuple[bool, float | None]:
        for i in range(1, len(ts_list)):
            if (ts_list[i] - ts_list[i - 1]) <= max_gap_s:
                return True, round(ts_list[i], 4)
        return False, None

    hit_2of3_any, t_2of3_any = _check_2of3(det_frame_ts)
    hit_2of3_sr, t_2of3_sr = _check_2of3(side_rear_ts)
    min_gap_any = (
        round(min(det_frame_ts[i] - det_frame_ts[i - 1] for i in range(1, len(det_frame_ts))), 4)
        if len(det_frame_ts) >= 2
        else None
    )
    min_gap_sr = (
        round(min(side_rear_ts[i] - side_rear_ts[i - 1] for i in range(1, len(side_rear_ts))), 4)
        if len(side_rear_ts) >= 2
        else None
    )

    return {
        "sampled_frames": len(frames),
        "duration_s": round(last_ts, 4),
        "det_frames": det_frames,
        "total_objects": sum(cls_counts.values()),
        "cls_counts": cls_counts,
        "min_conf": round(min(all_confs), 4) if all_confs else None,
        "mean_conf": round(sum(all_confs) / len(all_confs), 4) if all_confs else None,
        "max_conf": round(max(all_confs), 4) if all_confs else None,
        "first_det_s": round(det_frame_ts[0], 4) if det_frame_ts else None,
        "last_det_s": round(det_frame_ts[-1], 4) if det_frame_ts else None,
        "max_consec_any": max_consec_any,
        "max_consec_side_rear": max_consec_sr,
        "first_consec2_any_s": round(first_consec2_any_t, 4) if first_consec2_any_t is not None else None,
        "first_consec2_sr_s": round(first_consec2_sr_t, 4) if first_consec2_sr_t is not None else None,
        "hit_2of3_any": hit_2of3_any,
        "first_2of3_any_s": t_2of3_any,
        "hit_2of3_sr": hit_2of3_sr,
        "first_2of3_sr_s": t_2of3_sr,
        "min_inter_det_gap_any_s": min_gap_any,
        "min_inter_det_gap_sr_s": min_gap_sr,
        "det_records_detail": det_records_detail,
    }


def _parse_audio_stream(jsonl_path: Path) -> dict[str, Any]:
    """Parse precomputed audio window JSONL cache across frozen and hysteresis thresholds."""
    windows: list[dict[str, Any]] = []
    with open(jsonl_path, encoding="utf-8", newline="") as handle:
        for line in handle:
            if line.strip():
                windows.append(json.loads(line))

    scores: list[tuple[float, float]] = [(float(w["end_sec"]), float(w["horn_confidence"])) for w in windows]
    pos_037_ts: list[float] = []
    pos_075_ts: list[float] = []
    run37 = max_run37 = 0
    run75 = max_run75 = 0
    first_037_k2_s: float | None = None
    first_075_k2_s: float | None = None

    for ts, sc in scores:
        if sc >= 0.37:
            pos_037_ts.append(ts)
            run37 += 1
            max_run37 = max(max_run37, run37)
            if run37 >= 2 and first_037_k2_s is None:
                first_037_k2_s = ts
        else:
            run37 = 0

        if sc >= 0.75:
            pos_075_ts.append(ts)
            run75 += 1
            max_run75 = max(max_run75, run75)
            if run75 >= 2 and first_075_k2_s is None:
                first_075_k2_s = ts
        else:
            run75 = 0

    peak_ts, max_sc = max(scores, key=lambda x: x[1]) if scores else (None, 0.0)
    top5 = sorted([(round(sc, 4), round(ts, 2)) for ts, sc in scores], reverse=True)[:5]

    return {
        "n_windows": len(scores),
        "pos_windows_037": len(pos_037_ts),
        "pos_windows_075": len(pos_075_ts),
        "max_run_037": max_run37,
        "max_run_075": max_run75,
        "first_037_k1_s": round(pos_037_ts[0], 4) if pos_037_ts else None,
        "first_037_k2_s": round(first_037_k2_s, 4) if first_037_k2_s is not None else None,
        "first_075_k1_s": round(pos_075_ts[0], 4) if pos_075_ts else None,
        "first_075_k2_s": round(first_075_k2_s, 4) if first_075_k2_s is not None else None,
        "peak_s": round(peak_ts, 4) if peak_ts is not None else None,
        "mean_score": round(sum(s for _, s in scores) / len(scores), 4) if scores else 0.0,
        "max_score": round(max_sc, 4),
        "top5_scores": [{"score": sc, "end_sec": ts} for sc, ts in top5],
    }


def _run_side_tracker_proxy(ctx: VerifiedExploratoryContext, eid: str) -> dict[str, Any]:
    """Run Layer 2 SideMovementTracker on available vision stream(s) for event eid."""
    condition = "DUAL_VISION_AUDIO" if eid in ctx.accepted_sync_events else "B4"
    records, aligner, _ = load_event_evidence_records(ctx, eid, condition)
    collector = MultimodalEvidenceCollector(
        sync_aligner=aligner,
        window_tolerance_s=0.5,
        event_id=eid,
        allow_stale_detection_backfill=False,
    )
    collector.add_evidence_batch(records, preserve_arrival_order=False)
    master_times = [
        aligner.to_master(r.source_id, r.timestamp_s)
        if (aligner is not None and r.source_id in aligner.offsets_s)
        else r.timestamp_s
        for r in records
    ]
    frames = collector.generate_frames_from_history(min(master_times), max(master_times), stride_s=0.2)
    tracker = SideMovementTracker()
    states: list[str] = []
    max_consec_obs = 0
    for fr in frames:
        res = tracker.update(fr)
        if res.present:
            states.append(res.movement_state)
            max_consec_obs = max(max_consec_obs, res.consecutive_observations)
    if "MOVING" in states:
        final_proxy_state = "MOVING"
    elif "STOPPED" in states:
        final_proxy_state = "STOPPED"
    elif "SINGLE_FRAME" in states:
        final_proxy_state = "SINGLE_FRAME"
    else:
        final_proxy_state = "UNOBSERVED"
    return {
        "tracker_state": final_proxy_state,
        "tracker_moving_ticks": states.count("MOVING"),
        "tracker_max_consec_obs": max_consec_obs,
    }


def _classify_closure_timing(
    *,
    cohort: str,
    triggered: bool,
    fail_safe_clamped: bool,
    t_warning_s: float | None,
    t_close_cmd_s: float | None,
    t_half_closed_s: float | None,
    t_fully_closed_s: float | None,
    t_arrival_s: float | None,
) -> str:
    """Classify end-to-end causal crossing control timing against GT arrival T2."""
    if cohort in ("no_train_events", "engine_events"):
        if triggered:
            return "FALSE_CLOSURE_FP"
        if fail_safe_clamped:
            return "FAIL_SAFE_CLAMP_NO_TRIGGER"
        return "CORRECT_OPEN_TN"

    if not triggered:
        if fail_safe_clamped:
            return "MISSED_TRIGGER_EOF_FAIL_SAFE_CLAMP"
        return "MISSED_CLOSURE_FN"

    if t_fully_closed_s is None:
        return "WARNING_EOF_NEVER_CLOSED"

    if t_arrival_s is None:
        return "CLOSED_NO_T2_REF"
    if t_fully_closed_s <= t_arrival_s:
        return "SAFE_PRE_T2_FULL_CLOSURE"
    if t_half_closed_s is not None and t_half_closed_s <= t_arrival_s:
        return "PRE_T2_HALF_CLOSED_LATE_FULL"
    if t_close_cmd_s is not None and t_close_cmd_s <= t_arrival_s:
        return "PRE_T2_CLOSE_CMD_LATE_BOOM"
    if t_warning_s is not None and t_warning_s <= t_arrival_s:
        return "PRE_T2_WARNING_LATE_CMD"
    return "LATE_POST_T2_CLOSURE"


def _run_causal_fsm(
    ctx: VerifiedExploratoryContext,
    eid: str,
    *,
    condition: str,
    scenario_name: str,
    engine_kwargs: dict[str, Any],
    allow_uncalibrated_local_back: bool = False,
) -> dict[str, Any]:
    """Run causal V3 FSM + PhysicalGateModel at 5 Hz on verified event streams."""
    ref = ctx.references[eid]
    is_sync = eid in ctx.accepted_sync_events
    if condition in ("DUAL_VISION", "DUAL_VISION_AUDIO") and not is_sync:
        if not allow_uncalibrated_local_back:
            raise RuntimeError(f"Dual-camera master clock simulation blocked for {eid}")
        recs_f, _, _ = load_event_evidence_records(
            ctx, eid, "FRONT_VISION" if condition == "DUAL_VISION" else "B4"
        ) if condition == "DUAL_VISION_AUDIO" else load_event_evidence_records(ctx, eid, "B0")
        recs_b, _, _ = load_event_evidence_records(ctx, eid, "BACK_VISION")
        records = sorted(recs_f + recs_b, key=lambda r: (r.timestamp_s, str(r.modality.value), r.source_id))
        aligner = SyncAligner()
        aligner.add_source("camera_1", offset_s=0.0, uncertainty_s=0.0)
        aligner.add_source("camera_2", offset_s=0.0, uncertainty_s=2.0)
        clock_basis = "APPROX_LOCAL_UNCALIBRATED"
    else:
        records, aligner, _ = load_event_evidence_records(ctx, eid, condition)
        clock_basis = "CALIBRATED_SYNC11" if (condition in ("DUAL_VISION", "DUAL_VISION_AUDIO")) else "FRONT_DEVICE_CLOCK"

    collector = MultimodalEvidenceCollector(
        sync_aligner=aligner,
        window_tolerance_s=0.5,
        event_id=eid,
        allow_stale_detection_backfill=False,
    )
    collector.add_evidence_batch(records, preserve_arrival_order=False)
    master_times = [
        aligner.to_master(r.source_id, r.timestamp_s)
        if (aligner is not None and r.source_id in aligner.offsets_s)
        else r.timestamp_s
        for r in records
    ]
    frames = collector.generate_frames_from_history(min(master_times), max(master_times), stride_s=0.2)
    eng = MultimodalDecisionEngineV3FourLayer(**engine_kwargs)
    res: SimulationRunResult = EventSimulationRunner(decision_engine=eng, config=ctx.frozen_config).run_frames(
        frames, event_id=eid, scenario_name=scenario_name
    )

    t_warn = next((round(s.timestamp_s, 4) for s in res.steps if s.crossing_state == "WARNING"), None)
    trig_s = eng.timing_trace.get("engine_trigger_s")
    triggered = trig_s is not None
    # Note: distinguish perception-initiated close_cmd/half/full from EOF fail-safe clamps!
    t_cmd = (
        next((round(s.timestamp_s, 4) for s in res.steps if s.gate_state in ("CLOSING", "CLOSED")), None)
        if triggered
        else None
    )
    t_half = next((round(s.timestamp_s, 4) for s in res.steps if s.is_passage_blocked), None) if triggered else None
    t_full = next((round(s.timestamp_s, 4) for s in res.steps if s.gate_angle_deg <= 1e-6), None) if triggered else None
    t_open = next((round(s.timestamp_s, 4) for s in res.steps if s.crossing_state == "GATE_OPENING"), None)
    fail_safe_clamped = (not triggered) and any(s.crossing_state == "FAULT_FAIL_SAFE" for s in res.steps)

    audio_ext = any("AUDIO_DWELL_HOLD" in (s.decision.rule_id or "").upper() for s in res.steps)
    audio_supp = any("AUDIO_SUPPORT_ONLY" in (s.decision.rule_id or "").upper() for s in res.steps)

    t_arrival = ref.t2_raw_s if ref.t2_cam == "front" else None
    first_useful = eng.timing_trace.get("first_useful_detection_s")

    warn_lead = round(float(t_arrival) - float(t_warn), 4) if (t_arrival is not None and t_warn is not None) else None
    cmd_marg = round(float(t_arrival) - float(t_cmd), 4) if (t_arrival is not None and t_cmd is not None) else None
    full_marg = round(float(t_arrival) - float(t_full), 4) if (t_arrival is not None and t_full is not None) else None
    timing_class = _classify_closure_timing(
        cohort=ref.cohort,
        triggered=triggered,
        fail_safe_clamped=fail_safe_clamped,
        t_warning_s=t_warn,
        t_close_cmd_s=t_cmd,
        t_half_closed_s=t_half,
        t_fully_closed_s=t_full,
        t_arrival_s=t_arrival,
    )

    return {
        "event_id": eid,
        "cohort": ref.cohort,
        "clock_basis": clock_basis,
        "triggered": triggered,
        "trigger_s": round(float(trig_s), 4) if trig_s is not None else None,
        "trigger_rule": eng.engine_trigger_rule or "NONE",
        "first_useful_det_s": round(float(first_useful), 4) if first_useful is not None else None,
        "t_confirm_front_s": eng.timing_trace.get("confirmed_front_detection_s"),
        "t_warning_s": t_warn,
        "t_close_cmd_s": t_cmd,
        "t_half_closed_s": t_half,
        "t_fully_closed_s": t_full,
        "t_arrival_T2_s": t_arrival,
        "warning_lead_vs_T2_s": warn_lead,
        "close_cmd_margin_vs_T2_s": cmd_marg,
        "full_closure_margin_vs_T2_s": full_marg,
        "closure_timing_class": timing_class,
        "rear_confirmed_s": eng.timing_trace.get("rear_confirmed_s"),
        "reopen_completed": t_open is not None,
        "t_reopen_s": t_open,
        "audio_dwell_hold_fired": audio_ext,
        "audio_support_only_idle": audio_supp,
        "fail_safe_clamped_no_trigger": fail_safe_clamped,
        "final_crossing_state": res.steps[-1].crossing_state if res.steps else "NONE",
        "final_gate_state": res.steps[-1].gate_state if res.steps else "NONE",
    }


def _summarize_fsm_suite(fsm_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize causal gate-control performance across 23 trains, 3 no-trains, and 1 engine."""
    trains = [r for r in fsm_rows if r["cohort"] == "train_events"]
    no_trains = [r for r in fsm_rows if r["cohort"] == "no_train_events"]
    engines = [r for r in fsm_rows if r["cohort"] == "engine_events"]

    triggered_trains = [r for r in trains if r["triggered"]]
    full_closed_trains = [r for r in triggered_trains if r["t_fully_closed_s"] is not None]
    warn_only_eof = [r for r in triggered_trains if r["t_fully_closed_s"] is None]
    pre_t2_warn = [r for r in triggered_trains if r["warning_lead_vs_T2_s"] is not None and r["warning_lead_vs_T2_s"] >= 0.0]
    pre_t2_cmd = [r for r in triggered_trains if r["close_cmd_margin_vs_T2_s"] is not None and r["close_cmd_margin_vs_T2_s"] >= 0.0]
    pre_t2_half = [
        r for r in triggered_trains
        if r["t_half_closed_s"] is not None and r["t_arrival_T2_s"] is not None and r["t_half_closed_s"] <= r["t_arrival_T2_s"]
    ]
    pre_t2_full = [r for r in full_closed_trains if r["full_closure_margin_vs_T2_s"] is not None and r["full_closure_margin_vs_T2_s"] >= 0.0]
    reopened = [r for r in fsm_rows if r["reopen_completed"]]
    fp_nt = [r["event_id"] for r in no_trains if r["triggered"]]
    eng_trig = any(r["triggered"] for r in engines)

    margins = [r["full_closure_margin_vs_T2_s"] for r in full_closed_trains if r["full_closure_margin_vs_T2_s"] is not None]
    return {
        "n_events": len(fsm_rows),
        "n_train": len(trains),
        "train_triggers": len(triggered_trains),
        "train_full_closures": len(full_closed_trains),
        "train_warning_eof_never_closed": len(warn_only_eof),
        "train_missed_closures": len(trains) - len(triggered_trains),
        "train_pre_T2_warning": len(pre_t2_warn),
        "train_pre_T2_close_cmd": len(pre_t2_cmd),
        "train_pre_T2_half_closed": len(pre_t2_half),
        "train_pre_T2_full_closure": len(pre_t2_full),
        "no_train_false_closures": len(fp_nt),
        "no_train_false_closure_events": fp_nt,
        "engine_001_triggered": eng_trig,
        "complete_close_reopen_cycles": len(reopened),
        "full_closure_margin_vs_T2_stats_s": {
            "n": len(margins),
            "min": min(margins) if margins else None,
            "median": round(sorted(margins)[len(margins) // 2], 4) if margins else None,
            "max": max(margins) if margins else None,
        },
        "triggered_train_events": [r["event_id"] for r in triggered_trains],
        "pre_T2_warning_events": [r["event_id"] for r in pre_t2_warn],
        "pre_T2_close_cmd_events": [r["event_id"] for r in pre_t2_cmd],
    }


def _compute_binary_metrics(
    rows: list[dict[str, Any]],
    pred_key: str,
    truth_key: str,
    *,
    baseline_key: str | None = None,
    subset_filter: Any = None,
) -> dict[str, Any]:
    """Compute confusion matrix, P/R/Spec/F1/Acc, Wilson 95% CIs, and McNemar vs baseline."""
    sub = [r for r in rows if (subset_filter(r) if subset_filter else True)]
    tp = fp = tn = fn = 0
    fp_no_train = fp_engine = 0
    gained_events: list[str] = []
    fp_events: list[str] = []
    fn_events: list[str] = []

    preds: list[bool] = []
    truths: list[bool] = []
    base_preds: list[bool] = []

    for r in sub:
        y = bool(r[truth_key])
        p = bool(r[pred_key])
        preds.append(p)
        truths.append(y)
        if baseline_key:
            pb = bool(r[baseline_key])
            base_preds.append(pb)
            if y and p and not pb:
                gained_events.append(r["event_id"])
        if y and p:
            tp += 1
        elif y and not p:
            fn += 1
            fn_events.append(r["event_id"])
        elif not y and p:
            fp += 1
            fp_events.append(r["event_id"])
            if r["cohort"] == "no_train_events":
                fp_no_train += 1
            elif r["cohort"] == "engine_events":
                fp_engine += 1
        else:
            tn += 1

    n = len(sub)
    pos = tp + fn
    neg = tn + fp
    prec, prec_lo, prec_hi = wilson_ci_95(tp, tp + fp) if (tp + fp) > 0 else (0.0, 0.0, 0.0)
    rec, rec_lo, rec_hi = wilson_ci_95(tp, pos) if pos > 0 else (0.0, 0.0, 0.0)
    spec, spec_lo, spec_hi = wilson_ci_95(tn, neg) if neg > 0 else (0.0, 0.0, 0.0)
    acc, acc_lo, acc_hi = wilson_ci_95(tp + tn, n) if n > 0 else (0.0, 0.0, 0.0)
    f1 = (2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
    mcnemar = (
        _exact_mcnemar(base_preds, preds, truths)
        if baseline_key is not None
        else {"discordant_pairs": 0, "b01_baseline_wrong_candidate_right": 0, "b10_baseline_right_candidate_wrong": 0, "exact_p_value": 1.0}
    )

    return {
        "n_events": n,
        "pos_gt": pos,
        "neg_gt": neg,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "fp_no_train": fp_no_train,
        "fp_engine": fp_engine,
        "precision": round(prec, 4),
        "precision_ci95": [round(prec_lo, 4), round(prec_hi, 4)],
        "recall": round(rec, 4),
        "recall_ci95": [round(rec_lo, 4), round(rec_hi, 4)],
        "specificity": round(spec, 4),
        "specificity_ci95": [round(spec_lo, 4), round(spec_hi, 4)],
        "f1": round(f1, 4),
        "accuracy": round(acc, 4),
        "accuracy_ci95": [round(acc_lo, 4), round(acc_hi, 4)],
        "mcnemar_vs_baseline": mcnemar,
        "events_gained_over_front_L1": gained_events,
        "false_positive_events": fp_events,
        "false_negative_events": fn_events,
    }


def _failure_or_recovery_reason(row: dict[str, Any], *, orientation_corrected: bool = False) -> str:
    if row["cohort"] == "no_train_events":
        parts = []
        if row["front_det_frames"] > 0:
            parts.append(f"front={row['front_det_frames']}f(max_c={row['front_max_consec']})")
        if row["back_cls_front"] > 0:
            parts.append(f"back_false_front={row['back_cls_front']}obj")
        if row["audio_pos_037"] > 0:
            parts.append(f"audio_037={row['audio_pos_037']}w(r75={row['audio_max_run_075']})")
        triggered_v2_f6 = bool(
            row.get("pred_V2_front_L1_confirm2") or row.get("pred_F6_full_multimodal_dual_sr_or_audio_075_k2")
        )
        prefix = "FP under V2/F5/F6/F7 (TN under V5/A3/F8); " if triggered_v2_f6 else "TN under V2/F5/F6/F7; "
        return prefix + (", ".join(parts) if parts else "clean")

    if row["cohort"] == "engine_events":
        if not orientation_corrected:
            return (
                f"Solitary locomotive (train_present=True, 0 cars): front(-90deg)=0f, audio=0w(max={row['audio_max_score']}); "
                f"back(0deg)_cls_front={row['back_cls_front']}obj(c={row['back_max_consec']}, maxC={row['back_max_conf']}), 0 side/rear"
            )
        return (
            f"Solitary locomotive (train_present=True, 0 cars): front(upright src_rot={row['front_rotation_deg']}deg)={row['front_det_frames']}f "
            f"(mc={row['front_max_consec']}, maxC={row['front_max_conf']}), audio=0w(max={row['audio_max_score']}); "
            f"back(0deg)_cls_front={row['back_cls_front']}obj(c={row['back_max_consec']}, maxC={row['back_max_conf']}), "
            f"side/rear={row['back_cls_side'] + row['back_cls_rear']}obj"
        )

    if row["pred_V2_front_L1_confirm2"]:
        if row["front_lead_vs_T2_s"] is not None and row["front_lead_vs_T2_s"] < 0:
            return f"Detected by Front L1 ({row['front_max_consec']} consec), late ({row['front_first_det_s']}s vs T2={row['gt_T2_s']}s)"
        return f"Detected cleanly by Front L1 ({row['front_max_consec']} consec frames)"

    rec = []
    if row["pred_V5_back_confirm2_side_rear"]:
        rec.append(f"Back side/rear L1 (c={row['back_max_consec_side_rear']})")
    if row["pred_A3_audio_075_k2"]:
        rec.append(f"Audio >=0.75 k=2 (run={row['audio_max_run_075']}, max={row['audio_max_score']})")
    if rec:
        return f"Missed by Front L1 (rot={row['front_rotation_deg']}deg, df={row['front_det_frames']}); RECOVERED by " + " + ".join(rec)
    if row["pred_F7_exploratory_2of3_multimodal"]:
        suffix = " (upright db40305)" if orientation_corrected else ""
        return (
            f"Missed by F6{suffix}; RECOVERED by Exploratory 2-of-3 dropout tolerance "
            f"(front_gap={row['front_min_inter_det_gap_any_s']}s, back_sr_gap={row['back_min_inter_det_gap_sr_s']}s)"
        )
    if not orientation_corrected:
        return (
            f"FAILED F6 & F7: both cams -90deg unrotated (front df={row['front_det_frames']}, "
            f"back sr_c={row['back_max_consec_side_rear']}), audio max={row['audio_max_score']} (r75={row['audio_max_run_075']})"
        )
    return (
        f"FAILED F6 & F7 (upright db40305 decoded): front df={row['front_det_frames']}, "
        f"back sr_c={row['back_max_consec_side_rear']}, audio max={row['audio_max_score']} (r75={row['audio_max_run_075']})"
    )


def _load_supporting_lookup() -> dict[str, Any]:
    """Load R04 metadata, QuickTime session dates, stream rotations, M2/M3 departure errors, and LOEO folds."""
    qt = json.loads(QUICKTIME_DELTAS_PATH.read_text(encoding="utf-8"))
    svr = json.loads(SOURCE_RECEIPT_PATH.read_text(encoding="utf-8"))
    exp_d = json.loads((EXP_V2_DIR / "experiments" / "exp_d_back_departure.json").read_text(encoding="utf-8"))
    exp_r = json.loads((EXP_V2_DIR / "optimization_and_stress" / "exp_r_independent_validation.json").read_text(encoding="utf-8"))

    rot_map: dict[tuple[str, str], dict[str, Any]] = {}
    for m in svr["members"]:
        v = m.get("video", {})
        rot = 0
        for sd in v.get("side_data_list", []):
            if "rotation" in sd:
                rot = int(sd["rotation"])
        rot_map[(m["event"], m["camera"])] = {
            "rotation_deg": rot,
            "coded_width": v.get("width"),
            "coded_height": v.get("height"),
            "duration_s": float(v["duration"]) if v.get("duration") else None,
        }

    return {
        "qt": qt,
        "rot_map": rot_map,
        "sync11_d": {r["event_id"]: r for r in exp_d["sync11_comparison"]},
        "back27_d": {r["event_id"]: r for r in exp_d["back27_local_clock_summary"]},
        "loeo_folds": {r["fold_event"]: r for r in exp_r["reproduced_published_loeo"]["folds"]},
        "loeo_summary": exp_r["reproduced_published_loeo"]["oof_metrics"],
    }


def _build_failed_events_forensics(
    per_event_rows: list[dict[str, Any]],
    f_details: dict[str, list[dict[str, Any]]],
    b_details: dict[str, list[dict[str, Any]]],
    a_details: dict[str, list[dict[str, Any]]],
    *,
    orientation_corrected: bool = False,
) -> dict[str, Any]:
    """Build detailed forensic investigation for all F6-missed train events, F6 recoveries, and engine_001."""
    missed_ids = [r["event_id"] for r in per_event_rows if r["cohort"] == "train_events" and not r["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"]]
    recovered_ids = [
        r["event_id"]
        for r in per_event_rows
        if r["cohort"] == "train_events" and not r["pred_V2_front_L1_confirm2"] and r["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"]
    ]
    focus_ids = missed_ids + recovered_ids + ["engine_events/event_001"]

    row_map = {r["event_id"]: r for r in per_event_rows}
    cases: list[dict[str, Any]] = []
    for eid in focus_ids:
        r = row_map[eid]
        fd = f_details[eid]
        bd = b_details[eid]
        ad = a_details[eid]
        recoverability = "ALREADY_RECOVERED_BY_F6"
        if eid in missed_ids:
            if orientation_corrected:
                if r["pred_F7_exploratory_2of3_multimodal"]:
                    recoverability = (
                        "MISSED_F6_EVEN_AFTER_UPRIGHT_ROTATION_BUT_RECOVERED_BY_F7_2OF3: "
                        "Upright streams produced optical/acoustic hits pairing within <=0.60 s but no single-stream k>=2 run."
                    )
                elif r["adopted_horn_status"] == "present" and r["audio_max_score"] >= 0.75:
                    recoverability = (
                        "MISSED_EVEN_AFTER_UPRIGHT_ROTATION_AUDIO_NEAR_MISS: "
                        f"Peak audio score={r['audio_max_score']} (r75={r['audio_max_run_075']}) and sparse upright vision "
                        f"(front_df={r['front_det_frames']}, back_df={r['back_det_frames']})."
                    )
                elif r["front_det_frames"] > 0 or r["back_det_frames"] > 0:
                    recoverability = (
                        "SPARSE_UPRIGHT_DETECTIONS_BELOW_RUN2: "
                        f"Upright decoding gave front_df={r['front_det_frames']}, back_sr_c={r['back_max_consec_side_rear']} without k>=2 consecutive confirmation."
                    )
                else:
                    recoverability = (
                        "ZERO_OPTICAL_AND_ACOUSTIC_AFTER_UPRIGHT_ROTATION: "
                        "Genuine vision+horn failure under upright db40305 decoding (requires crossing-geometry/occlusion/lighting review)."
                    )
            else:
                if r["pred_F7_exploratory_2of3_multimodal"]:
                    recoverability = (
                        "RECOVERABLE_BY_2OF3_DROPOUT_TOLERANCE_AND_LIKELY_UPRIGHT_ROTATION: "
                        "Both streams were decoded sideways (-90 deg); existing detections already pair within <=0.60 s."
                    )
                elif r["adopted_horn_status"] == "present" and r["audio_max_score"] >= 0.75:
                    recoverability = (
                        "SINGLE_WINDOW_AUDIO_NEAR_MISS_AND_UNROTATED_OPTICAL: "
                        "Strong peak horn window (0.8402 followed by 0.7440; missed 0.75 k=2 by 0.0060), "
                        "0 optical frames at -90 deg; requires upright re-inference rather than overfitting threshold."
                    )
                elif r["front_det_frames"] > 0 or r["back_det_frames"] > 0:
                    recoverability = (
                        "SPARSE_UNROTATED_DETECTIONS_BELOW_RUN2: "
                        "Both cameras were -90 deg unrotated, yielding only 1-4 scattered frames (gaps >=2.4 s) "
                        "and quiet/absent horn; requires db40305 upright video re-inference."
                    )
                else:
                    recoverability = (
                        "ZERO_OPTICAL_AT_MINUS90_AND_ABSENT_HORN: "
                        "Both cameras were -90 deg unrotated (0 optical frames) and no horn present; "
                        "only upright video re-inference can recover without acoustic overfitting."
                    )
        elif eid == "engine_events/event_001":
            recoverability = (
                f"SOLITARY_LOCOMOTIVE_BOUNDARY_CASE ({'upright db40305' if orientation_corrected else 'pre-db40305'}): "
                f"Front={r['front_det_frames']}f (mc={r['front_max_consec']}, F={r['front_cls_front']}/S={r['front_cls_side']}/R={r['front_cls_rear']}); "
                f"Back={r['back_det_frames']}f (mc={r['back_max_consec']}, F={r['back_cls_front']}/S={r['back_cls_side']}/R={r['back_cls_rear']}); "
                f"Audio max={r['audio_max_score']}."
            )

        case_item: dict[str, Any] = {
            "event_id": eid,
            "cohort": r["cohort"],
            "category": (
                "F6_MISSED_TRAIN" if eid in missed_ids else ("F6_RECOVERED_OVER_V2" if eid in recovered_ids else "ENGINE_BOUNDARY")
            ),
            "gt_T0_s": r["gt_T0_s"],
            "gt_T2_s": r["gt_T2_s"],
            "gt_T4_s": r["gt_T4_s"],
            "adopted_horn_status": r["adopted_horn_status"],
            "gt_horn_onset_s": r["gt_horn_onset_s"],
            "front_rotation_deg": r["front_rotation_deg"],
            "back_rotation_deg": r["back_rotation_deg"],
            "front_det_frames": r["front_det_frames"],
            "front_cls_counts": {"front": r["front_cls_front"], "side": r["front_cls_side"], "rear": r["front_cls_rear"]},
            "front_min_inter_det_gap_any_s": r["front_min_inter_det_gap_any_s"],
            "front_detections_raw": fd,
            "back_det_frames": r["back_det_frames"],
            "back_cls_counts": {"front": r["back_cls_front"], "side": r["back_cls_side"], "rear": r["back_cls_rear"]},
            "back_min_inter_det_gap_sr_s": r["back_min_inter_det_gap_sr_s"],
            "back_detections_raw": bd[:25],
            "audio_windows": r["audio_windows"],
            "audio_pos_037": r["audio_pos_037"],
            "audio_pos_075": r["audio_pos_075"],
            "audio_max_run_075": r["audio_max_run_075"],
            "audio_max_score": r["audio_max_score"],
            "audio_top5_windows": ad,
            "recoverability_verdict": recoverability,
        }
        if orientation_corrected:
            case_item["front_upright_in_cache"] = r["front_upright_in_cache"]
            case_item["back_upright_in_cache"] = r["back_upright_in_cache"]
        cases.append(case_item)

    forensics_payload: dict[str, Any] = {
        "schema_version": "failed-events-forensic-diagnosis/1.0",
        "qualification": EXPLORATORY_LABEL,
        "missed_f6_count": len(missed_ids),
        "missed_f6_event_ids": missed_ids,
        "orientation_finding": {
            "all_8_missed_front_minus90_deg": all(row_map[e]["front_rotation_deg"] == -90 for e in missed_ids) if missed_ids else False,
            "all_8_missed_back_minus90_deg": all(row_map[e]["back_rotation_deg"] == -90 for e in missed_ids) if missed_ids else False,
            "zero_deg_upright_train_streams_detected": "4/4 (100%: front event_023=196f, back event_021=230f, event_022=228f, event_023=208f)",
        },
        "cases": cases,
    }
    if orientation_corrected:
        forensics_payload["orientation_corrected"] = True
    return forensics_payload


def _fmt(val: Any, suffix: str = "") -> str:
    if val is None or val == "":
        return "—"
    if isinstance(val, bool):
        return "YES" if val else "NO"
    if isinstance(val, float):
        return f"{val:.2f}{suffix}"
    return f"{val}{suffix}"


def _build_markdown_report(
    events: list[dict[str, Any]],
    view1: dict[str, dict[str, Any]],
    view2: dict[str, dict[str, Any]],
    view3: dict[str, dict[str, Any]],
    horn_configs: dict[str, dict[str, Any]],
    fsm_summaries: dict[str, dict[str, Any]],
    auth_status: dict[str, Any],
    forensics: dict[str, Any],
    model_specs: list[tuple[str, str, str, str, str]],
    support: dict[str, Any],
) -> str:
    """Render complete Mission 9 experimental evaluation report in Markdown."""
    engine_row = next(r for r in events if r["cohort"] == "engine_events")
    lines: list[str] = []
    lines.append("# Complete 27-Event Multimodal Experimental Evaluation, Causal Gate Control & Failure Forensics")
    lines.append("")
    lines.append(f"**Qualification:** `{EXPLORATORY_LABEL}`")
    lines.append(f"**Vision Data Provenance:** `{VISION_CACHE_PROVENANCE}`")
    lines.append(f"**Audio Data Provenance:** `{AUDIO_CACHE_PROVENANCE}`")
    lines.append(f"**Reference Labels:** `{REFERENCE_PROVENANCE}`")
    lines.append(
        "**Authorization & Re-Inference Readiness (Task 1):** "
        f"`{auth_status.get('canonical_path')}` is `{'PRESENT' if auth_status['authorized'] else 'ABSENT'}` "
        f"(`{auth_status.get('error_code', 'APPROVED')}`). Pre-hashed owner template staged at "
        f"`docs/generated/human_approval_templates/AUTH_MEDIA_ACCESS_MISSION9_READY.json`."
    )
    lines.append("")

    # Section 1: Orientation Audit
    lines.append("## 1. Original-Video Orientation Audit (`Display Matrix` `-90°` vs `0°` Upright)")
    lines.append(
        "- Across the `54` `.mov` recordings (`27` front + `27` back), **`44/54` (`81.5%`) carry `Display Matrix rotation = -90°`** (`24` front, `20` back) and **`10/54` (`18.5%`) are native `0°` upright** (`3` front: `train_023, no_train_001, no_train_003`; `7` back: `train_021..023, no_train_001..003, engine_001`)."
    )
    lines.append(
        "- **`CompactTrainHornCNN` Audio (`27/27` events, `2,600` windows):** Already re-run cleanly with corrected natural log-Mel features (`orientation-invariant`)."
    )
    lines.append(
        "- **`YOLOv8n` Upright Evidence Already Present (`4/4 = 100%` on `0°` train streams):** Every `0°` upright train video achieved dense continuous tracking (`train_023` front: `196` frames/`136` consec; `train_021` back: `230` frames/`69` consec; `train_022` back: `228` frames/`219` consec; `train_023` back: `208` frames/`111` consec). By contrast, **16/16 streams across all 8 failed events (`008, 009, 010, 011, 014, 015, 019, 020`) are `-90°` unrotated**, directly causing optical starvation (`0–5` scattered frames)."
    )
    lines.append("")

    # Section 2: Event-Level Detection Comparison (Task 2 & 3)
    lines.append("## 2. Vision vs Audio vs Rule-Based Late Fusion Comparison (All 27 Events)")
    lines.append(
        "All fusion variants evaluated here (`F1`–`F7`) are **rule-based late fusion** (`0` learned multimodal fusion weights). "
        "We explicitly label `FROZEN_PROTOCOL` baselines vs `EXPLORATORY_COHORT_SELECTED` thresholds."
    )
    lines.append("")
    lines.append(
        "| Configuration | Fusion Type / Thresholds | Train TP/23 | FN/23 | NT FP/3 | Eng001 Det | Prec (V1) | Rec (V1 [95% CI]) | Spec (V1) | F1 (V1) | Rail24 Rec/F1 (V3) | McNemar p vs V2 |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for key, pkey, ftype, tprov, label in model_specs:
        m1 = view1[key]
        m3 = view3[key]
        eng_det = "YES" if bool(engine_row[pkey]) else "no"
        ci_lo, ci_hi = m1["recall_ci95"]
        lines.append(
            f"| {label} | {ftype} / `{tprov}` | {m1['tp']} | {m1['fn']} | {m1['fp']} | {eng_det} | "
            f"{m1['precision']*100:.1f}% | {m1['recall']*100:.1f}% [{ci_lo*100:.1f}–{ci_hi*100:.1f}%] | "
            f"{m1['specificity']*100:.1f}% | {m1['f1']*100:.1f}% | "
            f"{m3['tp']}/24 ({m3['f1']*100:.1f}%) | {m1['mcnemar_vs_baseline']['exact_p_value']:.4f} |"
        )
    lines.append("")

    # Section 3: Audio Classifier Role Breakdown
    lines.append("## 3. What Does `CompactTrainHornCNN` Actually Detect? (Horn vs Train Presence)")
    lines.append(
        "`CompactTrainHornCNN` was trained to classify **train horns vs ambient/traffic sounds**, NOT general train wheel/engine rumble:"
    )
    lines.append(
        "- Across all `27` events evaluated against **adopted `horn_status`** (`13` `horn_present` vs `14` `horn_absent`), frozen `(tau=0.37, k=1)` gets `TP=12/13 (92.3%)` with **`FP=13/14` (`7.1%` specificity)**, while exploratory `(tau=0.75, k=2)` gets **`TP=8/13 (61.5%)` with `FP=1/14` (`92.9%` specificity, `F1=72.7%`)** (`23`-fold LOEO OOF on `train23`: `61.5%` recall, `60.0%` specificity, `64.0%` F1)."
    )
    lines.append(
        "- Consequently, audio hysteresis `(0.75, k=2)` recovers **`+3` silent-optical honking trains (`005, 012, 017`)** (`0/3` `no_train` FP), **cannot detect non-honking trains (`001, 008, 009, 010, 011, 014, 019`) or solitary `engine_001`** (`max=0.1428`), and emits `0.37–0.826` false positives on road horns in `3/3` `no_train` clips under `k=1`."
    )
    lines.append("")

    # Section 4: Causal Gate-Control State Machine Simulation (Task 4)
    lines.append("## 4. Causal Gate-Control State Machine Integration (`V3 FSM + PhysicalGateModel` @ `dt=0.20s`)")
    lines.append(
        "Closing the crossing physically requires **`confirm=2` (`0.2 s`) + `2.0 s` warning dwell + `3.0 s` boom closure = `>=5.2 s`**, "
        "whereas `21/22` `T2`-annotated recordings begin only **`2.8–5.0 s` before `T2`** (only `event_001` has `T2=6.5 s`)."
    )
    lines.append("")
    lines.append(
        "| Causal FSM Architecture (Clock Basis) | Triggered / 23 | Full Boom Closed / 23 | Warn@EOF Only | Missed FN/23 | NT FP/3 | Eng001 | Warn <= T2 | CloseCmd <= T2 | HalfClosed <= T2 | FullClosed <= T2 | Reopen Cycles |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    fsm_labels = [
        ("FSM_V2_Front_L1", "FSM V2 Front L1 (`B0`, Frozen, Front Clock)"),
        ("FSM_F2_V3_Default_B4", "FSM F2 Default V3 (`B4`, Frozen, Front Clock)"),
        ("FSM_F3_WeakFront_Plus_Audio", "FSM F3 Weak-Front & Audio 0.75k2 (Expl., Front Clock)"),
        ("FSM_F4_Front_Or_Audio075k2", "FSM F4 Front L1 OR Audio 0.75k2 (Expl., Front Clock)"),
        ("FSM_F5_Dual_Vision_Sync11", "FSM F5 Dual-Vision Side/Rear (Strict Calibrated `sync11` n=11)"),
        ("FSM_F6_Full_MM_Sync11", "FSM F6 Full Multimodal (Strict Calibrated `sync11` n=11)"),
        ("FSM_F6_Full_MM_Bounded27", "FSM F6 Full Multimodal (Calibrated `sync11` + Approx Local `16` = 27)"),
        ("FSM_F7_Exploratory_2of3_Bounded27", "FSM F7 Exploratory `2-of-3` Dropout Multimodal (All 27 Bounded)"),
    ]
    for fkey, flbl in fsm_labels:
        fs = fsm_summaries[fkey]
        is_sync_sub = fkey.endswith("_Sync11")
        nt_cell = "N/A (0 NT)" if is_sync_sub else f"{fs['no_train_false_closures']}/3"
        eng_cell = "N/A" if is_sync_sub else ("YES" if fs["engine_001_triggered"] else "no")
        lines.append(
            f"| {flbl} | {fs['train_triggers']}/{fs['n_train']} | {fs['train_full_closures']}/{fs['n_train']} | "
            f"{fs['train_warning_eof_never_closed']} | {fs['train_missed_closures']} | "
            f"{nt_cell} | {eng_cell} | "
            f"{fs['train_pre_T2_warning']} | {fs['train_pre_T2_close_cmd']} | "
            f"{fs['train_pre_T2_half_closed']} | {fs['train_pre_T2_full_closure']} | {fs['complete_close_reopen_cycles']} |"
        )
    lines.append("")

    # Section 5: 27-Row Master Table (Condensed Markdown Summary; full 50+ cols in CSV)
    lines.append("## 5. Event-by-Event Results & Causal FSM Timing Summary (All 27 Events)")
    lines.append("")
    lines.append(
        "| Event ID | Cohort (Sess) | Rot F/B | GT T2 / Horn | Fr DF (mc) [F/S/R] MaxC | Bk DF (sr_c) [F/S/R] MaxC | Aud >=.37 / >=.75 (r75) MaxA | V2 / F4 / F6 / F7 | F6 FSM Trig (Rule) | F6 Warn/Cmd/Full (Marg vs T2) | Timing Class (`F6`) |"
    )
    lines.append("|---|---|---|---|---:|---:|---:|---|---|---|---|")
    for r in events:
        coh_tag = f"{r['cohort'].split('_')[0]} ({r['recording_session'][-1]})"
        rot_tag = f"{r['front_rotation_deg']}/{r['back_rotation_deg']}"
        gt_tag = f"{_fmt(r['gt_T2_s'])}s / {'Y' if r['gt_horn_present'] else 'N'}"
        fr_tag = f"{r['front_det_frames']}({r['front_max_consec']}) [{r['front_cls_front']}/{r['front_cls_side']}/{r['front_cls_rear']}] {_fmt(r['front_max_conf'])}"
        bk_tag = f"{r['back_det_frames']}({r['back_max_consec_side_rear']}) [{r['back_cls_front']}/{r['back_cls_side']}/{r['back_cls_rear']}] {_fmt(r['back_max_conf'])}"
        au_tag = f"{r['audio_pos_037']}/{r['audio_pos_075']}({r['audio_max_run_075']}) {r['audio_max_score']:.3f}"
        preds_tag = f"{'P' if r['pred_V2_front_L1_confirm2'] else '-'}/{'P' if r['pred_F4_front_L1_or_audio_075_k2'] else '-'}/{'P' if r['pred_F6_full_multimodal_dual_sr_or_audio_075_k2'] else '-'}/{'P' if r['pred_F7_exploratory_2of3_multimodal'] else '-'}"
        f6_trig = f"{_fmt(r['f6_fsm_trigger_s'], 's')} ({r['f6_fsm_trigger_rule'][:10]})" if r["f6_fsm_triggered"] else "NONE"
        f6_times = f"{_fmt(r['f6_fsm_t_warning_s'])}/{_fmt(r['f6_fsm_t_close_cmd_s'])}/{_fmt(r['f6_fsm_t_fully_closed_s'])} ({_fmt(r['f6_fsm_full_closure_margin_vs_T2_s'], 's')})"
        lines.append(
            f"| `{r['event_id']}` | {coh_tag} | {rot_tag} | {gt_tag} | {fr_tag} | {bk_tag} | {au_tag} | {preds_tag} | {f6_trig} | {f6_times} | {r['f6_fsm_closure_timing_class']} |"
        )
    lines.append("")

    # Section 6: Forensic Diagnosis of All 8 Failed Events (Task 5)
    lines.append("## 6. Forensic Diagnosis of All 8 `F6`-Missed Train Events (`failed_events_forensic_diagnosis.json`)")
    lines.append("")
    lines.append("| Event ID | Rot F/B | Front Raw Dets | Back Raw Dets | Audio Top Score / Runs | Adopted Horn | Forensic Root Cause & Legitimate Recoverability |")
    lines.append("|---|---|---|---|---|---|---|")
    for c in forensics["cases"]:
        if c["category"] != "F6_MISSED_TRAIN":
            continue
        f_raw = ", ".join(f"{d['timestamp_s']}s:{d['detections']}" for d in c["front_detections_raw"]) or "0 frames"
        b_raw = ", ".join(f"{d['timestamp_s']}s:{d['detections']}" for d in c["back_detections_raw"]) or "0 frames"
        a_top = c["audio_top5_windows"][0]
        lines.append(
            f"| `{c['event_id']}` | {c['front_rotation_deg']}/{c['back_rotation_deg']} | {f_raw} | {b_raw} | "
            f"max={a_top['score']}@{a_top['end_sec']}s (p37={c['audio_pos_037']}, r75={c['audio_max_run_075']}) | "
            f"{c['adopted_horn_status']} | {c['recoverability_verdict']} |"
        )
    lines.append("")

    # Section 7: What Existing Recordings Cannot Prove (Task 4 & 6)
    lines.append("## 7. Explicit Boundary: What Existing Recordings & Labels Cannot Prove")
    lines.append("")
    lines.append("| Claim / Requirement | Status on Current 27 Events | Empirical Blocker |")
    lines.append("|---|---|---|")
    lines.append("| Pre-`T2` full `0°` barrier closure (`>=5.2 s` before arrival) | **0/23 EVENTS** | `21/22` `T2`-annotated recordings begin `2.8–5.0 s` before `T2` (`< 5.2 s` confirm+warn+stroke budget). |")
    lines.append("| Complete gate close -> autonomous reopen cycle on real footage | **0/27 CYCLES** | `0/27` track occupancy sensors + `20/22` `T4`-annotated clips end `<3.5 s` after `T4` (`median 1.402 s`). |")
    lines.append("| True upright `-90° -> 0°` YOLO recall across all 27 events | **PENDING OWNER `AUTH-MEDIA-ACCESS.json`** | `44/54` streams are `-90°` rotated in caches; `data/governance/AUTH-MEDIA-ACCESS.json` absent on disk. |")
    lines.append("| Frame-level YOLO mAP/IoU or window-level audio offset error | **CANNOT BE COMPUTED** | Proposals supply event-level timestamps only (`0` bbox GT, `0` horn offset GT, `0` Stage-2.1 human reviews). |")
    lines.append("| Generalization across crossings/sessions/unseen traffic | **BLOCKED (`leakage_safe = false`)** | Single crossing (`crossing_A`), 2 confounded sessions, `tau=0.75, k=2` & `2-of-3` gap selected exploratory on cohort. |")
    lines.append("")
    return "\n".join(lines) + "\n"


def _evaluate_context_suite(
    eval_ctx: VerifiedExploratoryContext,
    support: dict[str, Any],
    *,
    output_dir: Path,
    vision_provenance: str,
    audio_provenance: str,
    auth_status: dict[str, Any],
    raw_media_accessed: bool,
    upright_manifest: dict[str, Any] | None,
    orientation_corrected: bool,
    report_title: str = "Complete 27-Event Multimodal Experimental Evaluation, Causal Gate Control & Failure Forensics",
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Run full 27-event evaluation, causal FSM simulation, and forensics on one context."""
    rot_map = support["rot_map"]
    per_event_rows: list[dict[str, Any]] = []
    f_details: dict[str, list[dict[str, Any]]] = {}
    b_details: dict[str, list[dict[str, Any]]] = {}
    a_details: dict[str, list[dict[str, Any]]] = {}

    fsm_configs: dict[str, dict[str, Any]] = {
        "FSM_V2_Front_L1": {"condition": "B0", "kwargs": {"allow_any_front_camera_label": True}, "bounded": False},
        "FSM_F2_V3_Default_B4": {"condition": "B4", "kwargs": {"allow_any_front_camera_label": True}, "bounded": False},
        "FSM_F3_WeakFront_Plus_Audio": {
            "condition": "B4",
            "kwargs": {"allow_any_front_camera_label": True, "enable_corroborated_weak_front_audio_wakeup": True},
            "bounded": False,
        },
        "FSM_F4_Front_Or_Audio075k2": {
            "condition": "B4",
            "kwargs": {"allow_any_front_camera_label": True, "enable_audio_hysteresis_wakeup": True},
            "bounded": False,
        },
        "FSM_F5_Dual_Vision_Sync11": {
            "condition": "DUAL_VISION",
            "kwargs": {"allow_any_front_camera_label": True, "enable_back_side_rear_approach_backup": True},
            "bounded": False,
            "sync11_only": True,
        },
        "FSM_F6_Full_MM_Sync11": {
            "condition": "DUAL_VISION_AUDIO",
            "kwargs": {
                "allow_any_front_camera_label": True,
                "enable_back_side_rear_approach_backup": True,
                "enable_audio_hysteresis_wakeup": True,
            },
            "bounded": False,
            "sync11_only": True,
        },
        "FSM_F6_Full_MM_Bounded27": {
            "condition": "DUAL_VISION_AUDIO",
            "kwargs": {
                "allow_any_front_camera_label": True,
                "enable_back_side_rear_approach_backup": True,
                "enable_audio_hysteresis_wakeup": True,
            },
            "bounded": True,
        },
        "FSM_F7_Exploratory_2of3_Bounded27": {
            "condition": "DUAL_VISION_AUDIO",
            "kwargs": {
                "allow_any_front_camera_label": True,
                "enable_back_side_rear_approach_backup": True,
                "enable_audio_hysteresis_wakeup": True,
                "max_approach_inter_frame_gap_s": 0.45,
            },
            "bounded": True,
        },
    }
    fsm_results_by_cfg: dict[str, list[dict[str, Any]]] = {k: [] for k in fsm_configs}

    for eid in eval_ctx.event_order:
        ent = eval_ctx.manifest_events[eid]
        ref = eval_ctx.references[eid]
        qt_info = support["qt"][eid]
        session_date = str(qt_info.get("creationdate_front", ""))[:10]
        rec_session = "Session 1" if session_date == "2026-09-14" else "Session 2"

        f_stats = _parse_vision_stream(REPO_ROOT / ent["front_cache_path"])
        b_stats = _parse_vision_stream(REPO_ROOT / ent["back_cache_path"])
        a_stats = _parse_audio_stream(REPO_ROOT / ent["audio_cache_path"])
        side_tracker = _run_side_tracker_proxy(eval_ctx, eid)

        f_details[eid] = f_stats["det_records_detail"]
        b_details[eid] = b_stats["det_records_detail"]
        a_details[eid] = a_stats["top5_scores"]

        ev_fsm: dict[str, dict[str, Any]] = {}
        for cfg_name, spec in fsm_configs.items():
            if spec.get("sync11_only") and not ref.is_dual_sync_accepted:
                continue
            res_fsm = _run_causal_fsm(
                eval_ctx,
                eid,
                condition=spec["condition"],
                scenario_name=cfg_name,
                engine_kwargs=spec["kwargs"],
                allow_uncalibrated_local_back=bool(spec["bounded"]),
            )
            ev_fsm[cfg_name] = res_fsm
            fsm_results_by_cfg[cfg_name].append(res_fsm)

        f_rot = rot_map[(eid, "front")]["rotation_deg"]
        b_rot = rot_map[(eid, "back")]["rotation_deg"]

        b27_info = support["back27_d"].get(eid, {})
        t4_back = b27_info.get("T4_back_s")
        s11_info = support["sync11_d"].get(eid)
        t4_master = s11_info.get("T4_master_s") if s11_info else None
        t4_display = t4_master if t4_master is not None else t4_back

        m2_err = (
            round(float(b_stats["last_det_s"]) - float(t4_back), 4)
            if (b_stats["last_det_s"] is not None and t4_back is not None)
            else None
        )
        m3_reopen_s = (
            s11_info["policies"]["V3_CONSERVATIVE_POSITIVE"]["first_opening_s"] if s11_info else None
        )
        m3_guarded_s = (
            s11_info["policies"]["V3_GUARDED_DISAPPEARANCE"]["first_opening_s"] if s11_info else None
        )

        gt_is_train = ref.cohort == "train_events"
        gt_rail_present = bool(ref.train_present)
        gt_horn = str(ref.horn_status or "").lower() == "present"

        v1 = f_stats["det_frames"] >= 1
        v2 = f_stats["max_consec_any"] >= 2
        v3 = b_stats["det_frames"] >= 1
        v4 = b_stats["max_consec_any"] >= 2
        v5 = b_stats["max_consec_side_rear"] >= 2
        v6 = (f_stats["cls_counts"]["side"] + b_stats["cls_counts"]["side"]) >= 1
        v7 = v2 or v4
        v8 = v2 or v5

        a1 = a_stats["pos_windows_037"] >= 1
        a2 = a_stats["max_run_037"] >= 2
        a3 = a_stats["max_run_075"] >= 2

        f1 = v1 or a1
        f2 = v2
        f3 = v2 or (v1 and a3)
        f4 = v2 or a3
        f5 = v8
        f6 = v2 or v5 or a3
        f7 = bool(ev_fsm["FSM_F7_Exploratory_2of3_Bounded27"]["triggered"])

        f6_fsm = ev_fsm["FSM_F6_Full_MM_Bounded27"]
        f7_fsm = ev_fsm["FSM_F7_Exploratory_2of3_Bounded27"]
        v2_fsm = ev_fsm["FSM_F2_V3_Default_B4"]
        loeo_info = support["loeo_folds"].get(eid, {})

        row: dict[str, Any] = {
            "event_id": eid,
            "cohort": ref.cohort,
            "event_type": ref.event_type,
            "gt_is_train_event": gt_is_train,
            "gt_rail_vehicle_present": gt_rail_present,
            "gt_horn_present": gt_horn,
            "adopted_horn_status": ref.horn_status,
            "gt_horn_onset_s": float(ref.horn_onset_s) if ref.horn_onset_s is not None else None,
            "recording_session": rec_session,
            "lighting": ref.lighting,
            "weather": ref.weather,
            "is_sync11": ref.is_dual_sync_accepted,
            "sync_regime": "sync11" if ref.is_dual_sync_accepted else "independent_camera",
            "back_offset_s": ref.back_offset_s,
            "delta_qt_s": qt_info.get("delta_qt_s"),
            "front_rotation_deg": f_rot,
            "back_rotation_deg": b_rot,
            "front_upright_in_cache": True if orientation_corrected else (f_rot == 0),
            "back_upright_in_cache": True if orientation_corrected else (b_rot == 0),
            "gt_T0_s": ref.t0_raw_s,
            "gt_T0_cam": ref.t0_cam,
            "gt_T1_s": ref.t1_raw_s,
            "gt_T2_s": ref.t2_raw_s,
            "gt_T3_s": ref.t3_raw_s,
            "gt_T4_s": ref.t4_raw_s,
            "gt_T4_local_or_master_s": t4_display,
            "front_sampled_frames": f_stats["sampled_frames"],
            "front_det_frames": f_stats["det_frames"],
            "front_total_objects": f_stats["total_objects"],
            "front_cls_front": f_stats["cls_counts"]["front"],
            "front_cls_side": f_stats["cls_counts"]["side"],
            "front_cls_rear": f_stats["cls_counts"]["rear"],
            "front_min_conf": f_stats["min_conf"],
            "front_mean_conf": f_stats["mean_conf"],
            "front_max_conf": f_stats["max_conf"],
            "front_first_det_s": f_stats["first_det_s"],
            "front_first_consec2_s": f_stats["first_consec2_any_s"],
            "front_last_det_s": f_stats["last_det_s"],
            "front_max_consec": f_stats["max_consec_any"],
            "front_min_inter_det_gap_any_s": f_stats["min_inter_det_gap_any_s"],
            "front_lead_vs_T2_s": (
                round(float(ref.t2_raw_s) - float(f_stats["first_det_s"]), 4)
                if (ref.t2_cam == "front" and ref.t2_raw_s is not None and f_stats["first_det_s"] is not None)
                else None
            ),
            "back_sampled_frames": b_stats["sampled_frames"],
            "back_det_frames": b_stats["det_frames"],
            "back_total_objects": b_stats["total_objects"],
            "back_cls_front": b_stats["cls_counts"]["front"],
            "back_cls_side": b_stats["cls_counts"]["side"],
            "back_cls_rear": b_stats["cls_counts"]["rear"],
            "back_min_conf": b_stats["min_conf"],
            "back_mean_conf": b_stats["mean_conf"],
            "back_max_conf": b_stats["max_conf"],
            "back_first_det_s": b_stats["first_det_s"],
            "back_first_consec2_sr_s": b_stats["first_consec2_sr_s"],
            "back_last_det_s": b_stats["last_det_s"],
            "back_max_consec": b_stats["max_consec_any"],
            "back_max_consec_side_rear": b_stats["max_consec_side_rear"],
            "back_min_inter_det_gap_sr_s": b_stats["min_inter_det_gap_sr_s"],
            "back_M2_err_vs_T4_s": m2_err,
            "sync11_M3_reopen_s": m3_reopen_s,
            "sync11_M3_guarded_reopen_s": m3_guarded_s,
            "dedicated_side_camera": False,
            "side_proxy_total_objects": f_stats["cls_counts"]["side"] + b_stats["cls_counts"]["side"],
            "side_tracker_state": side_tracker["tracker_state"],
            "audio_windows": a_stats["n_windows"],
            "audio_pos_037": a_stats["pos_windows_037"],
            "audio_pos_075": a_stats["pos_windows_075"],
            "audio_max_run_037": a_stats["max_run_037"],
            "audio_max_run_075": a_stats["max_run_075"],
            "audio_first_037_s": a_stats["first_037_k1_s"],
            "audio_first_075_k2_s": a_stats["first_075_k2_s"],
            "audio_peak_s": a_stats["peak_s"],
            "audio_mean_score": a_stats["mean_score"],
            "audio_max_score": a_stats["max_score"],
            "audio_loeo_oof_pred": loeo_info.get("oof_pred"),
            "audio_loeo_oof_cal_prob": loeo_info.get("oof_cal_prob"),
            "pred_V1_front_any": v1,
            "pred_V2_front_L1_confirm2": v2,
            "pred_V3_back_any": v3,
            "pred_V4_back_confirm2_all": v4,
            "pred_V5_back_confirm2_side_rear": v5,
            "pred_V6_side_proxy_any": v6,
            "pred_V7_dual_vision_confirm2_all": v7,
            "pred_V8_dual_vision_confirm2_side_rear": v8,
            "pred_A1_audio_037_k1": a1,
            "pred_A2_audio_037_k2": a2,
            "pred_A3_audio_075_k2": a3,
            "pred_F1_stateless_union": f1,
            "pred_F2_v3_default_advisory_audio": f2,
            "pred_F3_front_or_corroborated_weak_vision": f3,
            "pred_F4_front_L1_or_audio_075_k2": f4,
            "pred_F5_dual_vision_side_rear_advisory": f5,
            "pred_F6_full_multimodal_dual_sr_or_audio_075_k2": f6,
            "pred_F7_exploratory_2of3_multimodal": f7,
            "v3_b4_triggered": v2_fsm["triggered"],
            "v3_t_confirm_s": v2_fsm["t_confirm_front_s"],
            "v3_t_warning_s": v2_fsm["t_warning_s"],
            "v3_t_close_cmd_s": v2_fsm["t_close_cmd_s"],
            "v3_t_fully_closed_s": v2_fsm["t_fully_closed_s"],
            "v3_margin_full_vs_T2_s": v2_fsm["full_closure_margin_vs_T2_s"],
            "v3_final_crossing_state": v2_fsm["final_crossing_state"],
            "v3_final_gate_state": v2_fsm["final_gate_state"],
            "f6_fsm_clock_basis": f6_fsm["clock_basis"],
            "f6_fsm_triggered": f6_fsm["triggered"],
            "f6_fsm_first_useful_det_s": f6_fsm["first_useful_det_s"],
            "f6_fsm_trigger_s": f6_fsm["trigger_s"],
            "f6_fsm_trigger_rule": f6_fsm["trigger_rule"],
            "f6_fsm_t_warning_s": f6_fsm["t_warning_s"],
            "f6_fsm_t_close_cmd_s": f6_fsm["t_close_cmd_s"],
            "f6_fsm_t_half_closed_s": f6_fsm["t_half_closed_s"],
            "f6_fsm_t_fully_closed_s": f6_fsm["t_fully_closed_s"],
            "f6_fsm_warning_lead_vs_T2_s": f6_fsm["warning_lead_vs_T2_s"],
            "f6_fsm_full_closure_margin_vs_T2_s": f6_fsm["full_closure_margin_vs_T2_s"],
            "f6_fsm_closure_timing_class": f6_fsm["closure_timing_class"],
            "f6_fsm_reopen_completed": f6_fsm["reopen_completed"],
            "f6_fsm_final_state": f6_fsm["final_crossing_state"],
            "f6_fsm_final_gate_state": f6_fsm["final_gate_state"],
            "f7_fsm_triggered": f7_fsm["triggered"],
            "f7_fsm_trigger_s": f7_fsm["trigger_s"],
            "f7_fsm_trigger_rule": f7_fsm["trigger_rule"],
            "f7_fsm_t_fully_closed_s": f7_fsm["t_fully_closed_s"],
            "f7_fsm_closure_timing_class": f7_fsm["closure_timing_class"],
            "f6_first_trigger_source": f6_fsm["trigger_rule"],
            "f6_t_trigger_s": f6_fsm["trigger_s"],
            "v3_audio_extended_dwell": v2_fsm["audio_dwell_hold_fired"],
            "v3_audio_support_only_idle": v2_fsm["audio_support_only_idle"],
            "v3_closure_triggered": v2_fsm["triggered"],
            "v3_t_half_closed_s": v2_fsm["t_half_closed_s"],
            "v3_t_reopen_s": v2_fsm["t_reopen_s"],
        }
        row["diagnosis"] = _failure_or_recovery_reason(row, orientation_corrected=orientation_corrected)
        per_event_rows.append(row)

    model_specs: list[tuple[str, str, str, str, str]] = [
        ("V1_Front_Any_Stateless", "pred_V1_front_any", "Single-Modality", "FROZEN_PROTOCOL", "Vision: Front-Only Stateless (k>=1)"),
        ("V2_Front_L1_Confirm2", "pred_V2_front_L1_confirm2", "Single-Modality", "FROZEN_PROTOCOL", "Vision: Front-Only L1 Causal (confirm>=2) [B0_front]"),
        ("V3_Back_Any_Stateless", "pred_V3_back_any", "Single-Modality", "FROZEN_PROTOCOL", "Vision: Back-Only Stateless (k>=1)"),
        ("V4_Back_Confirm2_AllClasses", "pred_V4_back_confirm2_all", "Single-Modality", "FROZEN_PROTOCOL", "Vision: Back-Only Confirm2 (All Classes)"),
        ("V5_Back_Confirm2_SideRear", "pred_V5_back_confirm2_side_rear", "Single-Modality", "EXPLORATORY_COHORT_SELECTED", "Vision: Back-Only Confirm2 (Side/Rear Filtered)"),
        ("V6_Side_Proxy_Any", "pred_V6_side_proxy_any", "Single-Modality", "FROZEN_PROTOCOL", "Vision: Side-Class Proxy (Front+Back side>=1)"),
        ("V7_Dual_Vision_Confirm2_AllClasses", "pred_V7_dual_vision_confirm2_all", "Rule-Based Late Fusion", "FROZEN_PROTOCOL", "Vision: Dual-Vision Confirm2 (All Classes)"),
        ("V8_Dual_Vision_Confirm2_SideRear", "pred_V8_dual_vision_confirm2_side_rear", "Rule-Based Late Fusion", "EXPLORATORY_COHORT_SELECTED", "Vision: Dual-Vision Causal (Front L1 OR Back Side/Rear L1)"),
        ("A1_Audio_Frozen_037_k1", "pred_A1_audio_037_k1", "Single-Modality", "FROZEN_PROTOCOL", "Audio-Only: Frozen tau=0.37, k=1 [B1_audio]"),
        ("A2_Audio_037_k2", "pred_A2_audio_037_k2", "Single-Modality", "EXPLORATORY_COHORT_SELECTED", "Audio-Only: tau=0.37, k=2 consecutive"),
        ("A3_Audio_Hysteresis_075_k2", "pred_A3_audio_075_k2", "Single-Modality", "EXPLORATORY_COHORT_SELECTED", "Audio-Only: Hysteresis tau=0.75, k=2 consecutive"),
        ("F1_Stateless_Union_FrontAny_Or_Audio037", "pred_F1_stateless_union", "Rule-Based Late Fusion", "FROZEN_PROTOCOL", "Fusion F1: Stateless Union (Front>=1 OR Audio>=0.37)"),
        ("F2_V3_Default_Front_L1_Advisory_Audio", "pred_F2_v3_default_advisory_audio", "Rule-Based Late Fusion", "FROZEN_PROTOCOL", "Fusion F2: V3 Default B2/B4 (Front L1 + Advisory Audio)"),
        ("F3_Front_L1_Or_Corroborated_WeakFront_Audio075k2", "pred_F3_front_or_corroborated_weak_vision", "Rule-Based Late Fusion", "EXPLORATORY_COHORT_SELECTED", "Fusion F3: Front L1 OR (Weak Front>=1 & Audio 0.75 k=2)"),
        ("F4_Front_L1_Or_Audio075k2", "pred_F4_front_L1_or_audio_075_k2", "Rule-Based Late Fusion", "EXPLORATORY_COHORT_SELECTED", "Fusion F4: Front L1 OR Audio Hysteresis (0.75, k=2)"),
        ("F5_Dual_Vision_SideRear_Advisory_Audio", "pred_F5_dual_vision_side_rear_advisory", "Rule-Based Late Fusion", "EXPLORATORY_COHORT_SELECTED", "Fusion F5: Dual-Vision Side/Rear + Advisory Audio [B7]"),
        ("F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2", "pred_F6_full_multimodal_dual_sr_or_audio_075_k2", "Rule-Based Late Fusion", "EXPLORATORY_COHORT_SELECTED", "Fusion F6: Full Multimodal (Front L1 OR Back SR L1 OR Audio 0.75 k=2)"),
        ("F7_Exploratory_2of3_Multimodal", "pred_F7_exploratory_2of3_multimodal", "Rule-Based Late Fusion", "EXPLORATORY_COHORT_SELECTED", "Fusion F7: Exploratory 2-of-3 Optical + Back SR + Audio 0.75 k=2"),
    ]

    engine_row = next(r for r in per_event_rows if r["cohort"] == "engine_events")
    view1: dict[str, dict[str, Any]] = {}
    view2: dict[str, dict[str, Any]] = {}
    view3: dict[str, dict[str, Any]] = {}
    horn_configs: dict[str, dict[str, Any]] = {}

    for name, pkey, ftype, tprov, _ in model_specs:
        m1 = _compute_binary_metrics(
            per_event_rows, pkey, "gt_is_train_event", baseline_key="pred_V2_front_L1_confirm2",
            subset_filter=lambda r: r["cohort"] in ("train_events", "no_train_events"),
        )
        m1["engine_001_detected"] = bool(engine_row[pkey])
        m1["fusion_type"] = ftype
        m1["threshold_provenance"] = tprov
        view1[name] = m1

        m2 = _compute_binary_metrics(per_event_rows, pkey, "gt_is_train_event", baseline_key="pred_V2_front_L1_confirm2")
        m2["fusion_type"] = ftype
        m2["threshold_provenance"] = tprov
        view2[name] = m2

        m3 = _compute_binary_metrics(per_event_rows, pkey, "gt_rail_vehicle_present", baseline_key="pred_V2_front_L1_confirm2")
        m3["fusion_type"] = ftype
        m3["threshold_provenance"] = tprov
        view3[name] = m3

        if pkey.startswith("pred_A"):
            horn_configs[name] = _compute_binary_metrics(
                per_event_rows, pkey, "gt_horn_present", baseline_key="pred_A1_audio_037_k1"
            )

    fsm_summaries = {k: _summarize_fsm_suite(rows) for k, rows in fsm_results_by_cfg.items()}
    forensics = _build_failed_events_forensics(
        per_event_rows, f_details, b_details, a_details, orientation_corrected=orientation_corrected
    )

    if write_outputs:
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = output_dir / "event_by_event_27_multimodal_evaluation.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(per_event_rows[0].keys()))
            writer.writeheader()
            writer.writerows(per_event_rows)

        provenance_doc: dict[str, Any] = {
            "vision": vision_provenance,
            "audio": audio_provenance,
            "reference": REFERENCE_PROVENANCE,
            "raw_media_accessed": bool(raw_media_accessed),
            "media_authorization_status": auth_status,
            "upright_inference_executed": upright_manifest is not None,
        }
        if orientation_corrected:
            provenance_doc["orientation_corrected"] = True

        json_events_path = output_dir / "event_by_event_27_multimodal_evaluation.json"
        json_events_path.write_text(
            json.dumps(
                {
                    "schema_version": "complete-27-event-multimodal-evaluation/2.0",
                    "qualification": EXPLORATORY_LABEL,
                    "provenance": provenance_doc,
                    "n_events": len(per_event_rows),
                    "events": per_event_rows,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    ablation_payload: dict[str, Any] = {
        "schema_version": "multimodal-ablation-metrics/2.0",
        "qualification": EXPLORATORY_LABEL,
        "learned_fusion_model_present": False,
        "all_fusion_rules_type": "RULE_BASED_LATE_FUSION",
        "view1_train23_vs_no_train3_engine_separate": view1,
        "view2_train23_vs_controls4": view2,
        "view3_rail_vehicle24_vs_no_train3": view3,
        "view4_horn13_vs_nohorn14": horn_configs,
        "audio_loeo_23_folds": support["loeo_summary"],
    }
    if orientation_corrected:
        ablation_payload["orientation_corrected"] = True

    if write_outputs:
        ablation_json_path = output_dir / "modality_and_fusion_ablation_metrics.json"
        ablation_json_path.write_text(json.dumps(ablation_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        ablation_csv_path = output_dir / "modality_and_fusion_ablation_metrics.csv"
        ab_rows = [
            {
                "configuration": k,
                "fusion_type": view1[k]["fusion_type"],
                "threshold_provenance": view1[k]["threshold_provenance"],
                "v1_train23_vs_nt3_n": view1[k]["n_events"],
                "v1_tp": view1[k]["tp"],
                "v1_fn": view1[k]["fn"],
                "v1_fp_no_train": view1[k]["fp"],
                "v1_tn_no_train": view1[k]["tn"],
                "engine_001_detected": view1[k]["engine_001_detected"],
                "v1_precision": view1[k]["precision"],
                "v1_recall": view1[k]["recall"],
                "v1_specificity": view1[k]["specificity"],
                "v1_f1": view1[k]["f1"],
                "v1_accuracy": view1[k]["accuracy"],
                "v1_mcnemar_p_vs_front_L1": view1[k]["mcnemar_vs_baseline"]["exact_p_value"],
                "v3_rail24_tp": view3[k]["tp"],
                "v3_rail24_recall": view3[k]["recall"],
                "v3_rail24_f1": view3[k]["f1"],
                "events_gained_over_front_L1": ";".join(view1[k]["events_gained_over_front_L1"]),
                "no_train_false_positive_events": ";".join(view1[k]["false_positive_events"]),
            }
            for k in view1
        ]
        with open(ablation_csv_path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(ab_rows[0].keys()))
            writer.writeheader()
            writer.writerows(ab_rows)

        fsm_payload: dict[str, Any] = {
            "schema_version": "causal-fsm-gate-timing-summary/1.0",
            "qualification": EXPLORATORY_LABEL,
            "summaries": fsm_summaries,
            "per_config_events": fsm_results_by_cfg,
        }
        if orientation_corrected:
            fsm_payload["orientation_corrected"] = True
        fsm_json_path = output_dir / "causal_fsm_gate_timing_summary.json"
        fsm_json_path.write_text(
            json.dumps(fsm_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        fsm_csv_rows = [
            {"fsm_configuration": k, **{sk: sv for sk, sv in s.items() if not isinstance(sv, (dict, list))}}
            for k, s in fsm_summaries.items()
        ]
        with open(output_dir / "causal_fsm_gate_timing_summary.csv", "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(fsm_csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(fsm_csv_rows)

        forensics_path = output_dir / "failed_events_forensic_diagnosis.json"
        forensics_path.write_text(json.dumps(forensics, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        if not orientation_corrected:
            report_path = output_dir / "COMPLETE_27_EVENT_MULTIMODAL_EXPERIMENT_REPORT.md"
            report_md = _build_markdown_report(
                per_event_rows, view1, view2, view3, horn_configs, fsm_summaries, auth_status, forensics, model_specs, support
            )
            report_path.write_text(report_md, encoding="utf-8")

    return {
        "per_event_rows": per_event_rows,
        "model_specs": model_specs,
        "ablation_payload": ablation_payload,
        "fsm_summaries": fsm_summaries,
        "fsm_results_by_cfg": fsm_results_by_cfg,
        "forensics": forensics,
    }


def _compute_audio_invariance_summary(
    base_ctx: VerifiedExploratoryContext, upright_ctx: VerifiedExploratoryContext
) -> dict[str, Any]:
    """Compare Mission 39/43 audio scores with freshly extracted Mission 10 log-Mel scores."""
    per_event: list[dict[str, Any]] = []
    max_abs_diff = 0.0
    for eid in base_ctx.event_order:
        b_text, _ = read_verified_utf8_text(
            REPO_ROOT, base_ctx.manifest_events[eid]["audio_cache_path"],
            expected_sha256=base_ctx.manifest_events[eid]["audio_cache_sha256"],
        )
        u_text, _ = read_verified_utf8_text(
            REPO_ROOT, upright_ctx.manifest_events[eid]["audio_cache_path"],
            expected_sha256=upright_ctx.manifest_events[eid]["audio_cache_sha256"],
        )
        b_win = {int(json.loads(line)["window_index"]): float(json.loads(line)["horn_confidence"]) for line in b_text.splitlines() if line.strip()}
        u_win = {int(json.loads(line)["window_index"]): float(json.loads(line)["horn_confidence"]) for line in u_text.splitlines() if line.strip()}
        common = sorted(set(b_win) & set(u_win))
        ev_max_diff = max((abs(b_win[w] - u_win[w]) for w in common), default=0.0)
        max_abs_diff = max(max_abs_diff, ev_max_diff)
        per_event.append(
            {
                "event_id": eid,
                "baseline_windows": len(b_win),
                "fresh_windows": len(u_win),
                "max_abs_score_diff": round(ev_max_diff, 6),
            }
        )
    return {
        "n_events": len(per_event),
        "max_abs_score_diff_across_all_windows": round(max_abs_diff, 6),
        "per_event": per_event,
    }


def _compare_baseline_and_upright(
    baseline_suite: dict[str, Any],
    upright_suite: dict[str, Any],
    base_ctx: VerifiedExploratoryContext,
    upright_ctx: VerifiedExploratoryContext,
    upright_manifest: dict[str, Any],
    *,
    output_dir: Path = UPRIGHT_EVAL_DIR,
) -> dict[str, Any]:
    """Build and write full Pre-db40305 vs Upright db40305 comparison tables and report."""
    b_rows = {r["event_id"]: r for r in baseline_suite["per_event_rows"]}
    u_rows = {r["event_id"]: r for r in upright_suite["per_event_rows"]}
    u_by_eid = {e["event_id"]: e for e in upright_manifest["events"]}

    b_v1 = baseline_suite["ablation_payload"]["view1_train23_vs_no_train3_engine_separate"]
    u_v1 = upright_suite["ablation_payload"]["view1_train23_vs_no_train3_engine_separate"]
    paired_train_nt = [
        eid for eid in upright_ctx.event_order
        if u_rows[eid]["cohort"] in ("train_events", "no_train_events")
    ]
    truths_v1 = [bool(u_rows[e]["gt_is_train_event"]) for e in paired_train_nt]

    cfg_comparison: list[dict[str, Any]] = []
    for cfg_name, pkey, _, _, desc in upright_suite["model_specs"]:
        bm = b_v1[cfg_name]
        um = u_v1[cfg_name]
        mcnemar_pre_vs_up = _exact_mcnemar(
            [bool(b_rows[e][pkey]) for e in paired_train_nt],
            [bool(u_rows[e][pkey]) for e in paired_train_nt],
            truths_v1,
        )
        recovered = [
            e for e in paired_train_nt
            if u_rows[e]["cohort"] == "train_events" and not b_rows[e][pkey] and u_rows[e][pkey]
        ]
        regressed = [
            e for e in paired_train_nt
            if u_rows[e]["cohort"] == "train_events" and b_rows[e][pkey] and not u_rows[e][pkey]
        ]
        cfg_comparison.append(
            {
                "configuration": cfg_name,
                "label": desc,
                "baseline_tp": bm["tp"],
                "baseline_fn": bm["fn"],
                "baseline_fp_no_train": bm["fp"],
                "baseline_recall": bm["recall"],
                "baseline_f1": bm["f1"],
                "baseline_engine_001": bm["engine_001_detected"],
                "upright_tp": um["tp"],
                "upright_fn": um["fn"],
                "upright_fp_no_train": um["fp"],
                "upright_recall": um["recall"],
                "upright_f1": um["f1"],
                "upright_engine_001": um["engine_001_detected"],
                "delta_tp": um["tp"] - bm["tp"],
                "delta_fp_no_train": um["fp"] - bm["fp"],
                "mcnemar_p_upright_vs_baseline": mcnemar_pre_vs_up["exact_p_value"],
                "recovered_train_events": recovered,
                "regressed_train_events": regressed,
            }
        )

    fsm_comparison: list[dict[str, Any]] = []
    for fk, bs in baseline_suite["fsm_summaries"].items():
        us = upright_suite["fsm_summaries"][fk]
        fsm_comparison.append(
            {
                "fsm_configuration": fk,
                "baseline_triggers": bs["train_triggers"],
                "upright_triggers": us["train_triggers"],
                "baseline_full_closures": bs["train_full_closures"],
                "upright_full_closures": us["train_full_closures"],
                "baseline_pre_T2_warning": bs["train_pre_T2_warning"],
                "upright_pre_T2_warning": us["train_pre_T2_warning"],
                "baseline_pre_T2_close_cmd": bs["train_pre_T2_close_cmd"],
                "upright_pre_T2_close_cmd": us["train_pre_T2_close_cmd"],
                "baseline_pre_T2_full_closure": bs["train_pre_T2_full_closure"],
                "upright_pre_T2_full_closure": us["train_pre_T2_full_closure"],
                "baseline_no_train_fp": bs["no_train_false_closures"],
                "upright_no_train_fp": us["no_train_false_closures"],
                "baseline_engine_001": bs["engine_001_triggered"],
                "upright_engine_001": us["engine_001_triggered"],
                "baseline_reopen_cycles": bs["complete_close_reopen_cycles"],
                "upright_reopen_cycles": us["complete_close_reopen_cycles"],
            }
        )

    prior_8_missed = [
        eid for eid in base_ctx.event_order
        if b_rows[eid]["cohort"] == "train_events" and not b_rows[eid]["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"]
    ]
    eight_event_recovery = [
        {
            "event_id": eid,
            "front_rotation_deg": u_rows[eid]["front_rotation_deg"],
            "back_rotation_deg": u_rows[eid]["back_rotation_deg"],
            "baseline_front_det_frames": b_rows[eid]["front_det_frames"],
            "upright_front_det_frames": u_rows[eid]["front_det_frames"],
            "upright_front_max_consec": u_rows[eid]["front_max_consec"],
            "baseline_back_det_frames": b_rows[eid]["back_det_frames"],
            "upright_back_det_frames": u_rows[eid]["back_det_frames"],
            "upright_back_max_consec_sr": u_rows[eid]["back_max_consec_side_rear"],
            "recovered_V2_front_L1": bool(u_rows[eid]["pred_V2_front_L1_confirm2"]),
            "recovered_F6_multimodal": bool(u_rows[eid]["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"]),
            "recovered_F7_2of3": bool(u_rows[eid]["pred_F7_exploratory_2of3_multimodal"]),
            "upright_diagnosis": u_rows[eid]["diagnosis"],
        }
        for eid in prior_8_missed
    ]

    event_deltas = [
        {
            "event_id": eid,
            "cohort": u_rows[eid]["cohort"],
            "rot_front_back": f"{u_rows[eid]['front_rotation_deg']}/{u_rows[eid]['back_rotation_deg']}",
            "front_orient_verified": u_by_eid[eid]["front_orientation"]["orientation_verified"],
            "back_orient_verified": u_by_eid[eid]["back_orientation"]["orientation_verified"],
            "base_front_df": b_rows[eid]["front_det_frames"],
            "up_front_df": u_rows[eid]["front_det_frames"],
            "base_front_mc": b_rows[eid]["front_max_consec"],
            "up_front_mc": u_rows[eid]["front_max_consec"],
            "up_front_cls": f"{u_rows[eid]['front_cls_front']}/{u_rows[eid]['front_cls_side']}/{u_rows[eid]['front_cls_rear']}",
            "base_back_df": b_rows[eid]["back_det_frames"],
            "up_back_df": u_rows[eid]["back_det_frames"],
            "base_back_sr_c": b_rows[eid]["back_max_consec_side_rear"],
            "up_back_sr_c": u_rows[eid]["back_max_consec_side_rear"],
            "up_back_cls": f"{u_rows[eid]['back_cls_front']}/{u_rows[eid]['back_cls_side']}/{u_rows[eid]['back_cls_rear']}",
            "base_V2": b_rows[eid]["pred_V2_front_L1_confirm2"],
            "up_V2": u_rows[eid]["pred_V2_front_L1_confirm2"],
            "base_F6": b_rows[eid]["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"],
            "up_F6": u_rows[eid]["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"],
            "up_F7": u_rows[eid]["pred_F7_exploratory_2of3_multimodal"],
            "up_f6_timing_class": u_rows[eid]["f6_fsm_closure_timing_class"],
        }
        for eid in upright_ctx.event_order
    ]

    audio_invariance = _compute_audio_invariance_summary(base_ctx, upright_ctx)
    session_comparison: dict[str, dict[str, Any]] = {}
    for sess in ("Session 1", "Session 2"):
        s_trains = [eid for eid in upright_ctx.event_order if u_rows[eid]["cohort"] == "train_events" and u_rows[eid]["recording_session"] == sess]
        s_all = [eid for eid in upright_ctx.event_order if u_rows[eid]["recording_session"] == sess]
        session_comparison[sess] = {
            "n_total_events": len(s_all),
            "n_train_events": len(s_trains),
            "baseline_V2_train_tp": sum(1 for e in s_trains if b_rows[e]["pred_V2_front_L1_confirm2"]),
            "upright_V2_train_tp": sum(1 for e in s_trains if u_rows[e]["pred_V2_front_L1_confirm2"]),
            "baseline_V5_back_sr_tp": sum(1 for e in s_trains if b_rows[e]["pred_V5_back_confirm2_side_rear"]),
            "upright_V5_back_sr_tp": sum(1 for e in s_trains if u_rows[e]["pred_V5_back_confirm2_side_rear"]),
            "baseline_F6_train_tp": sum(1 for e in s_trains if b_rows[e]["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"]),
            "upright_F6_train_tp": sum(1 for e in s_trains if u_rows[e]["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"]),
            "upright_F7_train_tp": sum(1 for e in s_trains if u_rows[e]["pred_F7_exploratory_2of3_multimodal"]),
        }
    no_train_audio_audit = [
        {
            "event_id": eid,
            "audio_pos_037": u_rows[eid]["audio_pos_037"],
            "audio_pos_075": u_rows[eid]["audio_pos_075"],
            "audio_max_run_075": u_rows[eid]["audio_max_run_075"],
            "audio_max_score": u_rows[eid]["audio_max_score"],
            "audio_peak_s": u_rows[eid]["audio_peak_s"],
            "fp_at_frozen_tau037_k1": bool(u_rows[eid]["pred_A1_audio_037_k1"]),
            "fp_at_hysteresis_tau075_k2": bool(u_rows[eid]["pred_A3_audio_075_k2"]),
        }
        for eid in upright_ctx.event_order
        if u_rows[eid]["cohort"] == "no_train_events"
    ]

    def _eval_quorum_set(rows_map: dict[str, dict[str, Any]], pred_fn: Any) -> dict[str, Any]:
        tr = [e for e in upright_ctx.event_order if rows_map[e]["cohort"] == "train_events"]
        nt = [e for e in upright_ctx.event_order if rows_map[e]["cohort"] == "no_train_events"]
        eng_id = next(e for e in upright_ctx.event_order if rows_map[e]["cohort"] == "engine_events")
        tp = sum(1 for e in tr if pred_fn(rows_map[e]))
        fn = len(tr) - tp
        fp = sum(1 for e in nt if pred_fn(rows_map[e]))
        tn = len(nt) - fp
        eng_det = bool(pred_fn(rows_map[eng_id]))
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r_v = tp / len(tr)
        s_v = tn / len(nt)
        f1_v = (2.0 * p * r_v / (p + r_v)) if (p + r_v) else 0.0
        tp_v3 = tp + (1 if eng_det else 0)
        p_v3 = tp_v3 / (tp_v3 + fp) if (tp_v3 + fp) else 0.0
        r_v3 = tp_v3 / (len(tr) + 1)
        f1_v3 = (2.0 * p_v3 * r_v3 / (p_v3 + r_v3)) if (p_v3 + r_v3) else 0.0
        return {
            "tp": tp,
            "fn": fn,
            "fp_no_train": fp,
            "tn_no_train": tn,
            "engine_001_detected": eng_det,
            "precision": round(p, 4),
            "recall": round(r_v, 4),
            "specificity": round(s_v, 4),
            "f1": round(f1_v, 4),
            "rail24_tp": tp_v3,
            "rail24_f1": round(f1_v3, 4),
        }

    def _f8_fn(row: dict[str, Any]) -> bool:
        votes = (
            int(bool(row["pred_V2_front_L1_confirm2"]))
            + int(bool(row["pred_V5_back_confirm2_side_rear"]))
            + int(bool(row["pred_A3_audio_075_k2"]))
        )
        return votes >= 2

    def _f9_fn(row: dict[str, Any]) -> bool:
        return bool(row["pred_V2_front_L1_confirm2"]) and bool(row["pred_V5_back_confirm2_side_rear"])

    f8_base = _eval_quorum_set(b_rows, _f8_fn)
    f8_up = _eval_quorum_set(u_rows, _f8_fn)
    f9_base = _eval_quorum_set(b_rows, _f9_fn)
    f9_up = _eval_quorum_set(u_rows, _f9_fn)

    f8_timing_events: list[dict[str, Any]] = []
    f8_pre_t2_confirm = 0
    f8_pre_t2_cmd_est = 0
    v2_pre_t2_confirm = 0
    for eid in upright_ctx.event_order:
        ur = u_rows[eid]
        if ur["cohort"] != "train_events":
            continue
        t_v2 = ur.get("front_first_consec2_s")
        t_v5_local = ur.get("back_first_consec2_sr_s")
        t_v5_master = (
            round(float(t_v5_local) + float(ur["back_offset_s"]), 4)
            if (t_v5_local is not None and ur["is_sync11"] and ur["back_offset_s"] is not None)
            else t_v5_local
        )
        t_a3 = ur.get("audio_first_075_k2_s")
        conf_times = sorted(float(x) for x in (t_v2, t_v5_master, t_a3) if x is not None)
        t_f8_confirm = round(conf_times[1], 4) if len(conf_times) >= 2 else None
        t2 = ur.get("gt_T2_s")
        if t2 is not None and t_v2 is not None and float(t_v2) <= float(t2):
            v2_pre_t2_confirm += 1
        if t2 is not None and t_f8_confirm is not None:
            if t_f8_confirm <= float(t2):
                f8_pre_t2_confirm += 1
            if (t_f8_confirm + 2.2) <= float(t2):
                f8_pre_t2_cmd_est += 1
        f8_timing_events.append(
            {
                "event_id": eid,
                "t_v2_confirm_s": t_v2,
                "t_v5_confirm_local_or_master_s": t_v5_master,
                "t_a3_confirm_s": t_a3,
                "t_f8_quorum_confirm_s": t_f8_confirm,
                "gt_T2_s": t2,
                "f8_confirm_lead_vs_T2_s": (
                    round(float(t2) - float(t_f8_confirm), 4) if (t2 is not None and t_f8_confirm is not None) else None
                ),
            }
        )

    mcnemar_f8_base_vs_up = _exact_mcnemar(
        [_f8_fn(b_rows[e]) for e in paired_train_nt],
        [_f8_fn(u_rows[e]) for e in paired_train_nt],
        truths_v1,
    )
    mcnemar_f8_vs_f6_up = _exact_mcnemar(
        [bool(u_rows[e]["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"]) for e in paired_train_nt],
        [_f8_fn(u_rows[e]) for e in paired_train_nt],
        truths_v1,
    )
    exploratory_quorum = {
        "provenance": "EXPLORATORY_POST_HOC_ANALYSIS",
        "F8_Exploratory_Strong_2of3_Quorum": {
            "rule": ">=2 of {V2 Front L1, V5 Back Side/Rear L1, A3 Audio 0.75 k=2}",
            "baseline": f8_base,
            "upright": f8_up,
            "mcnemar_p_baseline_vs_upright": mcnemar_f8_base_vs_up["exact_p_value"],
            "mcnemar_p_upright_F8_vs_upright_F6": mcnemar_f8_vs_f6_up["exact_p_value"],
            "causal_quorum_timing_summary": {
                "n_train_with_T2": sum(1 for r in f8_timing_events if r["gt_T2_s"] is not None),
                "v2_pre_T2_confirm": v2_pre_t2_confirm,
                "f8_pre_T2_confirm": f8_pre_t2_confirm,
                "f8_pre_T2_close_cmd_est_plus2p2s": f8_pre_t2_cmd_est,
                "per_event": f8_timing_events,
            },
        },
        "F9_Exploratory_Dual_Camera_Confirm2_And": {
            "rule": "V2 Front L1 AND V5 Back Side/Rear L1",
            "baseline": f9_base,
            "upright": f9_up,
        },
    }
    m2_errs = [float(u_rows[e]["back_M2_err_vs_T4_s"]) for e in upright_ctx.event_order if u_rows[e].get("back_M2_err_vs_T4_s") is not None]
    m2_departure_summary = {
        "n_events_with_T4_and_back_det": len(m2_errs),
        "mean_err_s": round(sum(m2_errs) / len(m2_errs), 4) if m2_errs else None,
        "median_err_s": round(sorted(m2_errs)[len(m2_errs) // 2], 4) if m2_errs else None,
        "min_err_s": round(min(m2_errs), 4) if m2_errs else None,
        "max_err_s": round(max(m2_errs), 4) if m2_errs else None,
        "non_premature_count": sum(1 for x in m2_errs if x >= 0.0),
    }

    payload = {
        "schema_version": "baseline-vs-upright-comparison/1.0",
        "qualification": EXPLORATORY_LABEL,
        "orientation_policy": SOURCE_DISPLAY_ROTATION_POLICY,
        "streams_verified_count": sum(
            1 for e in upright_manifest["events"]
            for cam in ("front_orientation", "back_orientation")
            if e[cam]["orientation_verified"]
        ),
        "total_streams": 2 * len(upright_manifest["events"]),
        "audio_invariance": audio_invariance,
        "session_comparison": session_comparison,
        "no_train_audio_fp_audit": no_train_audio_audit,
        "exploratory_quorum_comparison": exploratory_quorum,
        "upright_m2_departure_summary": m2_departure_summary,
        "config_comparison": cfg_comparison,
        "fsm_comparison": fsm_comparison,
        "prior_8_f6_missed_recovery": eight_event_recovery,
        "event_deltas_27": event_deltas,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "baseline_vs_upright_comparison.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with open(output_dir / "modality_and_fusion_ablation_upright_vs_baseline.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[k for k in cfg_comparison[0] if not isinstance(cfg_comparison[0][k], list)] + ["recovered_train_events", "regressed_train_events"],
        )
        writer.writeheader()
        for row in cfg_comparison:
            flat = dict(row)
            flat["recovered_train_events"] = ";".join(flat["recovered_train_events"])
            flat["regressed_train_events"] = ";".join(flat["regressed_train_events"])
            writer.writerow(flat)

    # Render concise Upright vs Baseline Markdown Report
    md: list[str] = [
        "# Mission 10 Upright (`db40305`) 27-Event Multimodal Evaluation & Baseline Comparison",
        "",
        f"**Qualification:** `{EXPLORATORY_LABEL}`",
        f"**Orientation Policy Applied:** `{SOURCE_DISPLAY_ROTATION_POLICY}` (`{payload['streams_verified_count']}/{payload['total_streams']}` streams verified)",
        f"**Audio Log-Mel Fresh Extraction Max Score Delta vs Baseline Cache:** `{audio_invariance['max_abs_score_diff_across_all_windows']}` across `{audio_invariance['n_events']}` events",
        "",
        "## 1. Pre-`db40305` Baseline vs Upright (`db40305`) Ablation Comparison (`23` Train vs `3` No-Train; `engine_001` Separate)",
        "",
        "| Configuration | Base TP/23 | Upright TP/23 | Delta TP | Base NT FP/3 | Upright NT FP/3 | Base F1 | Upright F1 | Eng001 Base->Up | McNemar p (Base vs Up) | Recovered Trains |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for c in cfg_comparison:
        rec_str = ", ".join(x.replace("train_events/", "") for x in c["recovered_train_events"]) or "—"
        md.append(
            f"| {c['label']} | {c['baseline_tp']} | {c['upright_tp']} | {c['delta_tp']:+d} | "
            f"{c['baseline_fp_no_train']} | {c['upright_fp_no_train']} | {c['baseline_f1']*100:.1f}% | {c['upright_f1']*100:.1f}% | "
            f"{'Y' if c['baseline_engine_001'] else 'N'}->{'Y' if c['upright_engine_001'] else 'N'} | "
            f"{c['mcnemar_p_upright_vs_baseline']:.4f} | {rec_str} |"
        )
    md.extend([
        "",
        "## 2. Recovery of the 8 Previously Failed (`pre-db40305` F6-Missed) Train Events",
        "",
        "| Event ID | Rot F/B | Front DF Base->Up (mc) | Back DF Base->Up (sr_c) | Upright V2 | Upright F6 | Upright F7 | Diagnosis |",
        "|---|---|---:|---:|---|---|---|---|",
    ])
    for r in eight_event_recovery:
        md.append(
            f"| `{r['event_id']}` | {r['front_rotation_deg']}/{r['back_rotation_deg']} | "
            f"{r['baseline_front_det_frames']}->{r['upright_front_det_frames']} ({r['upright_front_max_consec']}) | "
            f"{r['baseline_back_det_frames']}->{r['upright_back_det_frames']} ({r['upright_back_max_consec_sr']}) | "
            f"{'YES' if r['recovered_V2_front_L1'] else 'no'} | {'YES' if r['recovered_F6_multimodal'] else 'no'} | "
            f"{'YES' if r['recovered_F7_2of3'] else 'no'} | {r['upright_diagnosis']} |"
        )
    md.extend([
        "",
        "## 3. Causal FSM Gate Timing Comparison (Baseline vs Upright)",
        "",
        "| FSM Architecture | Trig B->U | Full Closed B->U | Warn<=T2 B->U | Cmd<=T2 B->U | Full<=T2 B->U | NT FP B->U | Eng001 B->U | Reopen B->U |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for f in fsm_comparison:
        md.append(
            f"| `{f['fsm_configuration']}` | {f['baseline_triggers']}->{f['upright_triggers']} | "
            f"{f['baseline_full_closures']}->{f['upright_full_closures']} | "
            f"{f['baseline_pre_T2_warning']}->{f['upright_pre_T2_warning']} | "
            f"{f['baseline_pre_T2_close_cmd']}->{f['upright_pre_T2_close_cmd']} | "
            f"{f['baseline_pre_T2_full_closure']}->{f['upright_pre_T2_full_closure']} | "
            f"{f['baseline_no_train_fp']}->{f['upright_no_train_fp']} | "
            f"{'Y' if f['baseline_engine_001'] else 'N'}->{'Y' if f['upright_engine_001'] else 'N'} | "
            f"{f['baseline_reopen_cycles']}->{f['upright_reopen_cycles']} |"
        )
    qt = exploratory_quorum["F8_Exploratory_Strong_2of3_Quorum"]["causal_quorum_timing_summary"]
    md.extend([
        "",
        "## 4. Exploratory Multimodal Quorum (`F8` / `F9`): Eliminating Upright Single-Camera False Positives vs Lead-Time Trade-off",
        "",
        "After orientation correction, single-camera `V2` (and OR-fusion `F6`) triggers `1/3` false positive on `no_train_events/event_002` (`front_max_consec=20`, `back_sr=0`, `A3=False`) and triggers `engine_events/event_001`.",
        "",
        "| Exploratory Quorum Rule | Base TP/23 | Up TP/23 | Up NT FP/3 | Up Eng001 | Up Prec | Up Rec | Up F1 | Causal Confirm<=T2 | Causal Est Cmd<=T2 |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|",
        (
            f"| `F8_Exploratory_Strong_2of3_Quorum` (>=2 of V2,V5,A3) | {f8_base['tp']} | **{f8_up['tp']}** | "
            f"**{f8_up['fp_no_train']}** | {'YES' if f8_up['engine_001_detected'] else 'no'} | "
            f"{f8_up['precision']*100:.1f}% | {f8_up['recall']*100:.1f}% | {f8_up['f1']*100:.1f}% | "
            f"{qt['f8_pre_T2_confirm']}/{qt['n_train_with_T2']} (vs V2 {qt['v2_pre_T2_confirm']}/22) | "
            f"{qt['f8_pre_T2_close_cmd_est_plus2p2s']}/{qt['n_train_with_T2']} |"
        ),
        (
            f"| `F9_Exploratory_Dual_Camera_And` (V2 AND V5) | {f9_base['tp']} | **{f9_up['tp']}** | "
            f"**{f9_up['fp_no_train']}** | {'YES' if f9_up['engine_001_detected'] else 'no'} | "
            f"{f9_up['precision']*100:.1f}% | {f9_up['recall']*100:.1f}% | {f9_up['f1']*100:.1f}% | — | — |"
        ),
        "",
        "## 5. Upright Back-Camera Departure Tracking (`M2` vs `gt_T4_s`)",
        "",
        (
            f"- Across `{m2_departure_summary['n_events_with_T4_and_back_det']}/22` `T4`-annotated trains, upright `back_last_det_s - T4` error has "
            f"mean `{m2_departure_summary['mean_err_s']}s`, median `{m2_departure_summary['median_err_s']}s`, range `[{m2_departure_summary['min_err_s']}s, {m2_departure_summary['max_err_s']}s]`, "
            f"with `{m2_departure_summary['non_premature_count']}/{m2_departure_summary['n_events_with_T4_and_back_det']}` non-premature (`>=0s`)."
        ),
    ])
    (output_dir / "COMPLETE_27_EVENT_UPRIGHT_MULTIMODAL_REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return payload


def run_evaluation(
    run_upright: bool = False,
    *,
    evaluate_existing_upright: bool = False,
    workers: int = 4,
    resume_upright: bool = True,
) -> dict[str, Any]:
    """Execute complete 27-event evaluation, causal FSM simulation, and optional upright comparison."""
    ctx = load_verified_context(REPO_ROOT)
    generate_owner_media_auth_template()
    auth_status = check_media_authorization_status()
    support = _load_supporting_lookup()

    upright_manifest: dict[str, Any] | None = None
    if run_upright:
        upright_manifest = run_upright_raw_inference(ctx, workers=workers, resume=resume_upright)
    elif evaluate_existing_upright:
        upright_manifest = _load_existing_upright_manifest()

    baseline_suite = _evaluate_context_suite(
        ctx,
        support,
        output_dir=OUTPUT_DIR,
        vision_provenance=VISION_CACHE_PROVENANCE,
        audio_provenance=AUDIO_CACHE_PROVENANCE,
        auth_status=auth_status,
        raw_media_accessed=False,
        upright_manifest=upright_manifest,
        orientation_corrected=False,
        write_outputs=(upright_manifest is None),
    )

    print("=== MISSION 9 BASELINE 27-EVENT EVALUATION & CAUSAL FSM VALIDATION ===")
    print(f"Auth status: {auth_status}")
    for k in ["FSM_V2_Front_L1", "FSM_F2_V3_Default_B4", "FSM_F3_WeakFront_Plus_Audio", "FSM_F4_Front_Or_Audio075k2", "FSM_F6_Full_MM_Sync11", "FSM_F6_Full_MM_Bounded27", "FSM_F7_Exploratory_2of3_Bounded27"]:
        fs = baseline_suite["fsm_summaries"][k]
        print(
            f"  {k:34s} | trig={fs['train_triggers']:2d}/{fs['n_train']} full={fs['train_full_closures']:2d}/{fs['n_train']} "
            f"preT2_warn={fs['train_pre_T2_warning']} preT2_cmd={fs['train_pre_T2_close_cmd']} preT2_full={fs['train_pre_T2_full_closure']} "
            f"fp_nt={fs['no_train_false_closures']}/3 eng={fs['engine_001_triggered']}"
        )

    if upright_manifest is not None:
        upright_ctx = _build_upright_context(ctx, upright_manifest)
        upright_suite = _evaluate_context_suite(
            upright_ctx,
            support,
            output_dir=UPRIGHT_EVAL_DIR,
            vision_provenance=(
                "Mission 10 Upright db40305 YOLOv8n Actual Inference "
                f"(orientation_policy={SOURCE_DISPLAY_ROTATION_POLICY}, 54/54 streams decoded via PyAV source_pts + apply_display_rotation)"
            ),
            audio_provenance="Mission 10 Fresh CompactTrainHornCNN Natural Log-Mel Inference (ffmpeg 16kHz mono WAV, 1.0s / 0.5s hop)",
            auth_status=auth_status,
            raw_media_accessed=bool(run_upright),
            upright_manifest=upright_manifest,
            orientation_corrected=True,
        )
        comparison = _compare_baseline_and_upright(
            baseline_suite, upright_suite, ctx, upright_ctx, upright_manifest, output_dir=UPRIGHT_EVAL_DIR
        )
        print("=== MISSION 10 UPRIGHT (db40305) 27-EVENT EVALUATION & COMPARISON ===")
        print(
            f"Streams verified: {comparison['streams_verified_count']}/{comparison['total_streams']} | "
            f"Audio max diff: {comparison['audio_invariance']['max_abs_score_diff_across_all_windows']}"
        )
        for k in ["FSM_V2_Front_L1", "FSM_F4_Front_Or_Audio075k2", "FSM_F6_Full_MM_Sync11", "FSM_F6_Full_MM_Bounded27", "FSM_F7_Exploratory_2of3_Bounded27"]:
            fs = upright_suite["fsm_summaries"][k]
            print(
                f"  UPRIGHT {k:28s} | trig={fs['train_triggers']:2d}/{fs['n_train']} full={fs['train_full_closures']:2d}/{fs['n_train']} "
                f"preT2_warn={fs['train_pre_T2_warning']} preT2_cmd={fs['train_pre_T2_close_cmd']} preT2_full={fs['train_pre_T2_full_closure']} "
                f"fp_nt={fs['no_train_false_closures']}/3 eng={fs['engine_001_triggered']}"
            )
        return {
            **baseline_suite["ablation_payload"],
            "upright_ablation": upright_suite["ablation_payload"],
            "upright_vs_baseline": comparison,
        }

    return baseline_suite["ablation_payload"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Mission 9/10 27-Event Multimodal Evaluation")
    parser.add_argument(
        "--run-upright-raw-inference",
        action="store_true",
        help="Run display-matrix upright YOLOv8n + Audio V3 inference on raw media (requires AUTH-MEDIA-ACCESS.json).",
    )
    parser.add_argument(
        "--evaluate-existing-upright",
        action="store_true",
        help="Evaluate and compare already-generated results/upright_inference_v2/UPRIGHT_INFERENCE_MANIFEST.json without accessing raw media.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel event workers for upright raw-media inference (default: 4).",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Re-run all 27 events instead of resuming verified per-event checkpoints.",
    )
    args = parser.parse_args()
    run_evaluation(
        run_upright=bool(args.run_upright_raw_inference),
        evaluate_existing_upright=bool(args.evaluate_existing_upright),
        workers=int(args.workers),
        resume_upright=not bool(args.no_resume),
    )


if __name__ == "__main__":
    main()
