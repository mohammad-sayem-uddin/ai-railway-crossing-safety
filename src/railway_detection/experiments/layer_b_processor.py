"""Layer B real-world video and audio processing pipeline.

Ingests real video files (.mov), samples frames at target FPS, runs YOLOv8n inference,
extracts audio tracks to 16kHz mono WAV, runs CompactTrainHornCNN inference, and
constructs synchronized MultimodalFrame sequences for benchmark simulation.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

from railway_detection.audio.model import PyTorchTrainHornClassifier
from railway_detection.audio.pipeline import AudioEvidencePipeline
from railway_detection.data.audio_extractor import extract_audio_from_video
from railway_detection.data.contracts import LayerBEvent
from railway_detection.data.layer_b import load_event_bundle
from railway_detection.data.sync import SyncAligner
from railway_detection.experiments.cache_provenance import (
    CACHE_REUSE_ISOLATED_RUN,
    CONTROLLED_CACHE_SCHEMA_VERSION,
    CacheProvenanceError,
    ControlledCacheProvenance,
    build_audio_preprocessing_config,
    build_vision_preprocessing_config,
    load_controlled_cache_jsonl,
    load_historical_diagnostic_cache_jsonl,
    write_controlled_cache_jsonl,
)
from railway_detection.experiments.frozen_config import (
    FrozenExperimentConfig,
    TimingIntegrityError,
    load_frozen_config,
)
from railway_detection.fusion.collector import MultimodalEvidenceCollector, MultimodalFrame
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.safety.media_guard import require_media_authorization
from railway_detection.utils.logging import get_logger
from railway_detection.vision.video import frame_generator

logger = get_logger("experiments.layer_b_processor")


def serialize_evidence_record(record: EvidenceRecord) -> dict[str, Any]:
    """Serialize an EvidenceRecord to a JSON-compatible dict."""
    return {
        "timestamp_s": float(record.timestamp_s),
        "source_id": record.source_id,
        "modality": record.modality.value if isinstance(record.modality, Modality) else str(record.modality),
        "available": bool(record.available),
        "detections": [
            {
                "label": d.label,
                "confidence": float(d.confidence),
                "bbox_xyxy": list(d.bbox_xyxy) if d.bbox_xyxy else None,
                "metadata": d.metadata,
            }
            for d in record.detections
        ],
        "metadata": record.metadata,
    }


def deserialize_evidence_record(data: dict[str, Any]) -> EvidenceRecord:
    """Deserialize an EvidenceRecord from a dict."""
    dets = [
        Detection(
            label=d["label"],
            confidence=float(d["confidence"]),
            bbox_xyxy=tuple(d["bbox_xyxy"]) if d.get("bbox_xyxy") else None,
            metadata=d.get("metadata", {}),
        )
        for d in data.get("detections", [])
    ]
    return EvidenceRecord(
        timestamp_s=float(data["timestamp_s"]),
        source_id=data["source_id"],
        modality=Modality(data["modality"]),
        available=bool(data["available"]),
        detections=tuple(dets),
        metadata=data.get("metadata", {}),
    )


class LayerBEventProcessor:
    """Processes raw Layer B video and audio into synchronized multimodal frames."""

    def __init__(
        self,
        repo_root: Path | str = ".",
        processed_audio_dir: Path | str = "data/processed/layer_b/audio",
        cache_dir: Path | str = "results/experiments/cache",
        config: FrozenExperimentConfig | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.processed_audio_dir = self.repo_root / processed_audio_dir
        self.cache_dir = self.repo_root / cache_dir
        self.processed_audio_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if config is not None:
            self.config = config
        else:
            cfg_path = self.repo_root / "configs/frozen_experiment_v1.yaml"
            self.config = (
                load_frozen_config(cfg_path)
                if cfg_path.exists()
                else load_frozen_config()
            )

        # Enforce checkpoint immutability and timing safeguards
        self.config.verify_all_safeguards(self.repo_root)

        self._yolo_model: Any = None
        self._audio_classifier: PyTorchTrainHornClassifier | None = None
        self._audio_pipeline: AudioEvidencePipeline | None = None

    def _get_yolo_model(self, checkpoint_path: Path) -> Any:
        if self._yolo_model is None:
            from ultralytics import YOLO  # type: ignore[import-not-found]
            self._yolo_model = YOLO(str(checkpoint_path))
        return self._yolo_model

    def _get_audio_pipeline(
        self, checkpoint_path: Path, threshold: float | None = None
    ) -> AudioEvidencePipeline:
        target_thresh = (
            float(threshold) if threshold is not None else self.config.audio.operating_threshold
        )
        if self._audio_pipeline is None:
            self._audio_classifier = PyTorchTrainHornClassifier(
                checkpoint_path=checkpoint_path,
                threshold=target_thresh,
            )
            self._audio_pipeline = AudioEvidencePipeline(
                classifier=self._audio_classifier,
                source_id="audio_1",
                window_s=self.config.audio.window_s,
                hop_s=self.config.audio.hop_s,
                target_sample_rate=self.config.audio.sample_rate,
                require_classifier=True,
            )
        return self._audio_pipeline

    def extract_audio(self, event_dir: Path) -> dict[str, Path | None]:
        """Extract mono 16kHz WAV from front and back videos for an event."""
        cohort = event_dir.parent.name
        event_id = event_dir.name
        event_audio_dir = self.processed_audio_dir / cohort / event_id
        event_audio_dir.mkdir(parents=True, exist_ok=True)

        front_video = event_dir / "camera_front.mov"
        back_video = event_dir / "camera_back.mov"

        front_wav = event_audio_dir / "camera_front.wav"
        back_wav = event_audio_dir / "camera_back.wav"

        extracted: dict[str, Path | None] = {}

        if front_video.exists():
            if not front_wav.exists() or front_wav.stat().st_size == 0:
                extracted["front"] = extract_audio_from_video(
                    front_video, front_wav, sample_rate=16000, channels=1
                )
            else:
                extracted["front"] = front_wav
        else:
            extracted["front"] = None

        if back_video.exists():
            if not back_wav.exists() or back_wav.stat().st_size == 0:
                extracted["back"] = extract_audio_from_video(
                    back_video, back_wav, sample_rate=16000, channels=1
                )
            else:
                extracted["back"] = back_wav
        else:
            extracted["back"] = None

        return extracted

    def build_stream_provenance(
        self,
        *,
        cohort: str,
        event_id: str,
        source_id: str,
        modality: str,
        run_id: str,
        failure_injector: str = "none",
        injector_parameters: dict[str, Any] | None = None,
        software_version: str = "0.1.0",
        roi_config: dict[str, Any] | None = None,
        sampling_fps: float | None = None,
        conf_threshold: float | None = None,
        audio_threshold: float | None = None,
        git_commit: str | None = None,
        injector_version: str | None = None,
    ) -> ControlledCacheProvenance:
        """Build a deterministic 14-field ControlledCacheProvenance from the frozen config."""
        if modality == "vision":
            model_arch = self.config.checkpoints.vision.model_name
            ckpt_sha = self.config.checkpoints.vision.expected_sha256
            preproc = build_vision_preprocessing_config(
                self.config,
                sampling_fps=sampling_fps,
                confidence_threshold_approach=conf_threshold,
                roi_config=roi_config,
            )
        elif modality == "audio":
            model_arch = self.config.checkpoints.audio_v3.model_name
            ckpt_sha = self.config.checkpoints.audio_v3.expected_sha256
            preproc = build_audio_preprocessing_config(
                self.config,
                operating_threshold=audio_threshold,
            )
        else:
            raise CacheProvenanceError(
                "PROVENANCE_MODALITY_INVALID", f"Unsupported modality: {modality!r}"
            )

        timing_cfg = {
            "tick_s": float(self.config.timing.tick_s),
            "confirm_frames": int(self.config.timing.confirm_frames),
            "miss_tolerance_frames": int(self.config.timing.miss_tolerance_frames),
            "warning_dwell_s": float(self.config.timing.warning_dwell_s),
            "gate_closing_s": float(self.config.timing.gate_closing_s),
            "gate_opening_s": float(self.config.timing.gate_opening_s),
            "clearance_dwell_s": float(self.config.timing.clearance_dwell_s),
            "source_staleness_s": float(self.config.timing.source_staleness_s),
            "fault_confirmation_frames": int(
                self.config.timing.fault_confirmation_frames
            ),
            "fault_recovery_hold_s": float(self.config.timing.fault_recovery_hold_s),
            "cross_camera_sync_mode": str(self.config.timing.cross_camera_sync.mode),
            "cross_camera_sync_status": str(
                self.config.timing.cross_camera_sync.status
            ),
            "allow_unverified_zero_offset": bool(
                self.config.timing.cross_camera_sync.allow_unverified_zero_offset
            ),
        }
        return ControlledCacheProvenance(
            cohort=cohort,
            event_id=event_id,
            source_id=source_id,
            modality=modality,
            model_architecture=model_arch,
            checkpoint_sha256=ckpt_sha,
            preprocessing_config=preproc,
            experiment_config_sha256=self.config.canonical_hash,
            failure_injector=failure_injector,
            injector_parameters=dict(injector_parameters or {}),
            timing_config=timing_cfg,
            cache_schema_version=CONTROLLED_CACHE_SCHEMA_VERSION,
            software_version=software_version,
            run_id=run_id,
            roi_config=roi_config,
            git_commit=git_commit,
            injector_version=injector_version,
        )

    def run_vision_inference(
        self,
        video_path: Path,
        checkpoint_path: Path,
        source_id: str,
        target_fps: float = 5.0,
        conf: float = 0.35,
        use_cache: bool = True,
        *,
        provenance: ControlledCacheProvenance | None = None,
        allow_historical_unverified_cache: bool = False,
        reuse_policy: str = CACHE_REUSE_ISOLATED_RUN,
    ) -> list[EvidenceRecord]:
        """Sample frames at target_fps and run YOLOv8n inference."""
        cohort = video_path.parent.parent.name
        if provenance is not None:
            if provenance.modality != "vision":
                raise CacheProvenanceError(
                    "PROVENANCE_MODALITY_MISMATCH",
                    f"Vision inference received provenance with modality={provenance.modality!r}",
                )
            if provenance.source_id != source_id:
                raise CacheProvenanceError(
                    "PROVENANCE_MISMATCH",
                    f"Vision inference source_id {source_id!r} != provenance.source_id {provenance.source_id!r}",
                )
            prov_fps = provenance.preprocessing_config.get("sampling_fps")
            if prov_fps is not None and abs(float(prov_fps) - float(target_fps)) > 1e-9:
                raise CacheProvenanceError(
                    "PROVENANCE_PREPROCESSING_MISMATCH",
                    f"Vision target_fps {target_fps} != provenance sampling_fps {prov_fps}",
                )
            prov_conf = provenance.preprocessing_config.get(
                "confidence_threshold_approach",
                provenance.preprocessing_config.get("conf"),
            )
            if prov_conf is not None and abs(float(prov_conf) - float(conf)) > 1e-9:
                raise CacheProvenanceError(
                    "PROVENANCE_PREPROCESSING_MISMATCH",
                    f"Vision conf {conf} != provenance confidence threshold {prov_conf}",
                )
        if use_cache:
            if provenance is not None:
                controlled_file = self.cache_dir / provenance.cache_filename()
                if controlled_file.exists():
                    return load_controlled_cache_jsonl(
                        controlled_file, provenance, reuse_policy=reuse_policy
                    )
            else:
                cache_file = (
                    self.cache_dir
                    / f"{cohort}_{video_path.parent.name}_{video_path.stem}_{source_id}_vision.jsonl"
                )
                if cache_file.exists():
                    if not allow_historical_unverified_cache:
                        raise CacheProvenanceError(
                            "HISTORICAL_UNVERIFIED_CACHE_REJECTED",
                            f"Refusing to load unverified legacy cache {cache_file.name} without "
                            "ControlledCacheProvenance or explicit allow_historical_unverified_cache=True.",
                        )
                    records, _ = load_historical_diagnostic_cache_jsonl(cache_file)
                    return records

        if not video_path.exists():
            logger.warning("Video file not found for inference: %s", video_path)
            return []

        yolo = self._get_yolo_model(checkpoint_path)
        records = []

        try:
            require_media_authorization(video_path, "INFERENCE", declared_media=True)
            for frame in frame_generator(video_path, target_fps=target_fps, source_id=source_id):
                try:
                    preds = yolo.predict(frame.image, conf=conf, verbose=False)
                    detections: list[Detection] = []
                    if preds and len(preds) > 0 and preds[0].boxes is not None:
                        for box in preds[0].boxes:
                            cls_id = int(box.cls[0])
                            label_name = yolo.names.get(cls_id, str(cls_id))
                            score = float(box.conf[0])
                            xyxy = tuple(float(c) for c in box.xyxy[0])
                            detections.append(
                                Detection(
                                    label=label_name,
                                    confidence=score,
                                    bbox_xyxy=xyxy,
                                )
                            )

                    records.append(
                        EvidenceRecord(
                            timestamp_s=frame.timestamp_s,
                            source_id=source_id,
                            modality=Modality.VISION,
                            available=True,
                            detections=tuple(detections),
                            metadata={"frame_index": frame.frame_index},
                        )
                    )
                except Exception as frame_exc:
                    logger.warning("Error processing frame %d in %s: %s", frame.frame_index, video_path, frame_exc)
        except Exception as vid_exc:
            logger.error("Error reading video %s: %s", video_path, vid_exc)

        # Write cache
        if use_cache and records:
            if provenance is not None:
                write_controlled_cache_jsonl(self.cache_dir, provenance, records)
            elif allow_historical_unverified_cache:
                cache_file = (
                    self.cache_dir
                    / f"{cohort}_{video_path.parent.name}_{video_path.stem}_{source_id}_vision.jsonl"
                )
                with open(cache_file, "w", encoding="utf-8") as f:
                    for rec in records:
                        f.write(json.dumps(serialize_evidence_record(rec)) + "\n")
            else:
                raise CacheProvenanceError(
                    "PROVENANCE_REQUIRED",
                    "Writing controlled vision cache requires a ControlledCacheProvenance.",
                )

        return records

    def run_audio_inference(
        self,
        wav_path: Path | None,
        checkpoint_path: Path,
        source_id: str = "audio_1",
        threshold: float = 0.3700,
        cohort: str = "train_events",
        event_id: str = "event_001",
        use_cache: bool = True,
        *,
        provenance: ControlledCacheProvenance | None = None,
        allow_historical_unverified_cache: bool = False,
        reuse_policy: str = CACHE_REUSE_ISOLATED_RUN,
    ) -> list[EvidenceRecord]:
        """Run CompactTrainHornCNN inference on windowed audio."""
        if provenance is not None:
            if provenance.modality != "audio":
                raise CacheProvenanceError(
                    "PROVENANCE_MODALITY_MISMATCH",
                    f"Audio inference received provenance with modality={provenance.modality!r}",
                )
            if provenance.source_id != source_id:
                raise CacheProvenanceError(
                    "PROVENANCE_MISMATCH",
                    f"Audio inference source_id {source_id!r} != provenance.source_id {provenance.source_id!r}",
                )
            if provenance.cohort != cohort:
                raise CacheProvenanceError(
                    "PROVENANCE_MISMATCH",
                    f"Audio inference cohort {cohort!r} != provenance.cohort {provenance.cohort!r}",
                )
            if provenance.event_id != event_id:
                raise CacheProvenanceError(
                    "PROVENANCE_MISMATCH",
                    f"Audio inference event_id {event_id!r} != provenance.event_id {provenance.event_id!r}",
                )
            prov_thresh = provenance.preprocessing_config.get(
                "operating_threshold",
                provenance.preprocessing_config.get("threshold"),
            )
            if prov_thresh is not None and abs(float(prov_thresh) - float(threshold)) > 1e-9:
                raise CacheProvenanceError(
                    "PROVENANCE_PREPROCESSING_MISMATCH",
                    f"Audio threshold {threshold} != provenance operating_threshold {prov_thresh}",
                )
        if use_cache:
            if provenance is not None:
                controlled_file = self.cache_dir / provenance.cache_filename()
                if controlled_file.exists():
                    return load_controlled_cache_jsonl(
                        controlled_file, provenance, reuse_policy=reuse_policy
                    )
            else:
                cache_file = self.cache_dir / f"{cohort}_{event_id}_{source_id}_audio.jsonl"
                if cache_file.exists():
                    if not allow_historical_unverified_cache:
                        raise CacheProvenanceError(
                            "HISTORICAL_UNVERIFIED_CACHE_REJECTED",
                            f"Refusing to load unverified legacy cache {cache_file.name} without "
                            "ControlledCacheProvenance or explicit allow_historical_unverified_cache=True.",
                        )
                    records, _ = load_historical_diagnostic_cache_jsonl(cache_file)
                    return records

        if wav_path is None or not wav_path.exists() or wav_path.stat().st_size == 0:
            logger.warning("WAV path missing or empty for audio inference: %s", wav_path)
            return [
                EvidenceRecord(
                    timestamp_s=0.0,
                    source_id=source_id,
                    modality=Modality.AUDIO,
                    available=False,
                    detections=(),
                    metadata={"audio_safety_role": "supporting_only", "error": "file_missing"},
                )
            ]

        pipeline = self._get_audio_pipeline(checkpoint_path, threshold=threshold)
        pipeline.source_id = source_id
        records = pipeline.process_file(wav_path)

        # Verify invariant: audio_safety_role == supporting_only
        for r in records:
            assert r.metadata.get("audio_safety_role") == "supporting_only", "Audio safety invariant violated!"

        if use_cache and records:
            if provenance is not None:
                write_controlled_cache_jsonl(self.cache_dir, provenance, records)
            elif allow_historical_unverified_cache:
                cache_file = self.cache_dir / f"{cohort}_{event_id}_{source_id}_audio.jsonl"
                with open(cache_file, "w", encoding="utf-8") as f:
                    for rec in records:
                        f.write(json.dumps(serialize_evidence_record(rec)) + "\n")
            else:
                raise CacheProvenanceError(
                    "PROVENANCE_REQUIRED",
                    "Writing controlled audio cache requires a ControlledCacheProvenance.",
                )

        return records

    def build_multimodal_frames(
        self,
        vision_records: list[EvidenceRecord],
        audio_records: list[EvidenceRecord],
        duration_s: float = 30.0,
        stride_s: float = 0.2,
        sync_aligner: SyncAligner | None = None,
        aligner: SyncAligner | None = None,
    ) -> list[MultimodalFrame]:
        """Align vision and audio records onto master clock at target stride (e.g. 0.2s for 5 FPS)."""
        actual_aligner = sync_aligner if sync_aligner is not None else aligner

        # Timing safeguard R04: Check if multiple cameras are merged without an accepted sync aligner
        cam_sources = {r.source_id for r in vision_records if r.modality == Modality.VISION}
        if len(cam_sources) > 1 and actual_aligner is None:
            if not self.config.timing.cross_camera_sync.allow_unverified_zero_offset:
                raise TimingIntegrityError(
                    f"R04 Timing Violation: Attempting to fuse cross-camera sources {cam_sources} "
                    "without empirical offset calibration or SyncAligner. "
                    "Front and back camera start times differ by up to 33 seconds. "
                    "Unverified zero-offset cross-camera temporal fusion is strictly blocked."
                )
            else:
                logger.warning(
                    "EXPLORATORY_UNVERIFIED_ZERO_OFFSET: Fusing cameras %s with unverified zero offset",
                    cam_sources,
                )

        collector = MultimodalEvidenceCollector(
            sync_aligner=actual_aligner, window_tolerance_s=0.25
        )
        collector.add_evidence_batch(vision_records)
        collector.add_evidence_batch(audio_records)
        return collector.generate_frames_from_history(0.0, max(duration_s, 1.0), stride_s=stride_s)

    def process_event(
        self,
        event_dir: Path,
        yolo_checkpoint: Path | None = None,
        audio_checkpoint: Path | None = None,
        fps: float | None = None,
        conf: float | None = None,
        audio_threshold: float | None = None,
        stride_s: float | None = None,
        sync_aligner: SyncAligner | None = None,
        use_cache: bool = True,
        *,
        run_id: str | None = None,
        failure_injector: str = "none",
        injector_parameters: Mapping[str, Any] | None = None,
        roi_config: Mapping[str, Any] | None = None,
        allow_historical_unverified_cache: bool = False,
        reuse_policy: str = CACHE_REUSE_ISOLATED_RUN,
    ) -> tuple[LayerBEvent, list[MultimodalFrame]]:
        """Run complete ingestion and inference pipeline for one event."""
        # Resolve parameters from authoritative frozen configuration if not passed
        yolo_ckpt = yolo_checkpoint or (self.repo_root / self.config.checkpoints.vision.path)
        audio_ckpt = audio_checkpoint or (self.repo_root / self.config.checkpoints.audio_v3.path)
        sampling_fps = fps if fps is not None else self.config.vision.sampling_fps
        conf_thresh = conf if conf is not None else self.config.vision.confidence_threshold_approach
        aud_thresh = (
            audio_threshold if audio_threshold is not None else self.config.audio.operating_threshold
        )
        tick_stride = stride_s if stride_s is not None else self.config.timing.tick_s

        cohort = event_dir.parent.name
        # Load event contract
        load_res = load_event_bundle(event_dir, strict_metadata=False)
        assert load_res.event is not None, f"Failed to load event {event_dir}"
        raw_event_id = load_res.event.event_id
        event = replace(load_res.event, event_id=f"{cohort}_{raw_event_id}")

        v1_prov: ControlledCacheProvenance | None = None
        v2_prov: ControlledCacheProvenance | None = None
        a1_prov: ControlledCacheProvenance | None = None
        if run_id is not None:
            v1_prov = self.build_stream_provenance(
                cohort=cohort,
                event_id=raw_event_id,
                source_id="camera_1",
                modality="vision",
                run_id=run_id,
                failure_injector=failure_injector,
                injector_parameters= dict(injector_parameters or {}),
                roi_config=dict(roi_config) if roi_config is not None else None,
                sampling_fps=sampling_fps,
                conf_threshold=conf_thresh,
            )
            v2_prov = self.build_stream_provenance(
                cohort=cohort,
                event_id=raw_event_id,
                source_id="camera_2",
                modality="vision",
                run_id=run_id,
                failure_injector=failure_injector,
                injector_parameters=dict(injector_parameters or {}),
                roi_config=dict(roi_config) if roi_config is not None else None,
                sampling_fps=sampling_fps,
                conf_threshold=conf_thresh,
            )
            a1_prov = self.build_stream_provenance(
                cohort=cohort,
                event_id=raw_event_id,
                source_id="audio_1",
                modality="audio",
                run_id=run_id,
                failure_injector=failure_injector,
                injector_parameters=dict(injector_parameters or {}),
                roi_config=dict(roi_config) if roi_config is not None else None,
                audio_threshold=aud_thresh,
            )

        # Extract audio tracks
        audio_paths = self.extract_audio(event_dir)
        front_wav = audio_paths.get("front")

        # Run vision inference
        front_video = event_dir / "camera_front.mov"
        back_video = event_dir / "camera_back.mov"

        v1_records = self.run_vision_inference(
            video_path=front_video,
            checkpoint_path=yolo_ckpt,
            source_id="camera_1",
            target_fps=sampling_fps,
            conf=conf_thresh,
            use_cache=use_cache,
            provenance=v1_prov,
            allow_historical_unverified_cache=allow_historical_unverified_cache,
            reuse_policy=reuse_policy,
        )

        v2_records = self.run_vision_inference(
            video_path=back_video,
            checkpoint_path=yolo_ckpt,
            source_id="camera_2",
            target_fps=sampling_fps,
            conf=conf_thresh,
            use_cache=use_cache,
            provenance=v2_prov,
            allow_historical_unverified_cache=allow_historical_unverified_cache,
            reuse_policy=reuse_policy,
        )

        # Run audio inference on front audio track
        a_records = self.run_audio_inference(
            wav_path=front_wav,
            checkpoint_path=audio_ckpt,
            source_id="audio_1",
            threshold=aud_thresh,
            cohort=cohort,
            event_id=raw_event_id,
            use_cache=use_cache,
            provenance=a1_prov,
            allow_historical_unverified_cache=allow_historical_unverified_cache,
            reuse_policy=reuse_policy,
        )

        all_v_records = v1_records + v2_records
        all_timestamps = [r.timestamp_s for r in all_v_records] + [r.timestamp_s for r in a_records]
        max_duration = max(all_timestamps) if all_timestamps else 30.0

        frames = self.build_multimodal_frames(
            vision_records=all_v_records,
            audio_records=a_records,
            duration_s=max_duration,
            stride_s=tick_stride,
            sync_aligner=sync_aligner,
        )

        return event, frames
