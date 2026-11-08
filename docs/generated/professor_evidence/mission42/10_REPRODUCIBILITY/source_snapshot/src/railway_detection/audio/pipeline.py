"""Audio evidence generation pipeline emitting typed EvidenceRecords.

Adheres strictly to the research safety constraint:
Audio evidence carries metadata 'audio_safety_role': 'supporting_only'.
Audio can support train presence but can never independently authorize gate opening.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from railway_detection.audio.model import AudioClassifierBackend, SpectralEnergyBaseline
from railway_detection.audio.preprocessor import (
    AudioWindow,
    load_wav,
    sliding_windows,
    standardize_wav,
)
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.utils.logging import get_logger

logger = get_logger("audio.pipeline")


class AudioEvidencePipeline:
    """Processes continuous audio recordings and emits EvidenceRecords for fusion."""

    def __init__(
        self,
        classifier: AudioClassifierBackend | None = None,
        source_id: str = "audio_1",
        window_s: float = 1.0,
        hop_s: float = 0.5,
        target_sample_rate: int = 16000,
        min_confidence_to_emit: float = 0.0,
        require_classifier: bool = False,
    ) -> None:
        if require_classifier and classifier is None:
            raise ValueError(
                "A trained AudioClassifierBackend must be explicitly provided in the experiment path. "
                "Silent fallback to uncalibrated energy baseline is prohibited."
            )
        self.classifier = classifier if classifier is not None else SpectralEnergyBaseline()
        self.source_id = source_id
        self.window_s = float(window_s)
        self.hop_s = float(hop_s)
        self.target_sample_rate = int(target_sample_rate)
        self.min_confidence_to_emit = float(min_confidence_to_emit)

    def process_file(self, wav_path: str | Path) -> list[EvidenceRecord]:
        """Process a WAV audio file into a sequence of EvidenceRecord objects."""
        path = Path(wav_path)
        if not path.exists() or path.stat().st_size == 0:
            logger.warning("audio file missing or empty: %s", path)
            return [
                EvidenceRecord(
                    timestamp_s=0.0,
                    source_id=self.source_id,
                    modality=Modality.AUDIO,
                    available=False,
                    detections=(),
                    metadata={
                        "audio_safety_role": "supporting_only",
                        "error": "file_not_found_or_empty",
                        "file_path": str(path),
                    },
                )
            ]

        try:
            samples, source_rate = load_wav(path)
            standardized = standardize_wav(
                samples, source_rate, target_rate=self.target_sample_rate
            )
            windows = sliding_windows(
                standardized,
                self.target_sample_rate,
                window_s=self.window_s,
                hop_s=self.hop_s,
            )
            return self.process_windows(windows)
        except Exception as exc:
            logger.error("failed to process audio file %s: %s", path, exc)
            return [
                EvidenceRecord(
                    timestamp_s=0.0,
                    source_id=self.source_id,
                    modality=Modality.AUDIO,
                    available=False,
                    detections=(),
                    metadata={
                        "audio_safety_role": "supporting_only",
                        "error": str(exc),
                    },
                )
            ]

    def process_windows(self, windows: list[AudioWindow]) -> list[EvidenceRecord]:
        """Process pre-windowed audio segments into EvidenceRecords stamped causally at window end."""
        records: list[EvidenceRecord] = []
        for window in windows:
            confidence, label = self.classifier.predict_window(
                window.samples, sample_rate=window.sample_rate
            )

            # Causal timestamp invariant: window evidence is available at the window end
            window_end_s = window.start_time_s + window.duration_s

            detections: list[Detection] = []
            if label == "train" or confidence >= self.min_confidence_to_emit:
                detections.append(
                    Detection(
                        label=label,
                        confidence=confidence,
                        metadata={
                            "window_id": window.window_id,
                            "raw_label": label,
                            "probability": confidence,
                        },
                    )
                )

            record = EvidenceRecord(
                timestamp_s=window_end_s,
                source_id=self.source_id,
                modality=Modality.AUDIO,
                available=True,
                detections=tuple(detections),
                metadata={
                    "audio_safety_role": "supporting_only",
                    "window_start_s": window.start_time_s,
                    "window_duration_s": window.duration_s,
                    "window_end_s": window_end_s,
                    "window_id": window.window_id,
                    "probability": confidence,
                    "model_class": type(self.classifier).__name__,
                },
            )
            records.append(record)

        return records

    def process_samples(
        self, samples: np.ndarray, sample_rate: int, start_offset_s: float = 0.0
    ) -> list[EvidenceRecord]:
        """Process in-memory numpy array samples."""
        standardized = standardize_wav(
            samples, sample_rate, target_rate=self.target_sample_rate
        )
        windows = sliding_windows(
            standardized,
            self.target_sample_rate,
            window_s=self.window_s,
            hop_s=self.hop_s,
        )
        # Apply offset if provided
        if start_offset_s > 0:
            windows = [
                AudioWindow(
                    window_id=w.window_id,
                    start_sample=w.start_sample,
                    end_sample=w.end_sample,
                    sample_rate=w.sample_rate,
                    samples=w.samples,
                    start_time_s=w.start_time_s + start_offset_s,
                )
                for w in windows
            ]
        return self.process_windows(windows)
