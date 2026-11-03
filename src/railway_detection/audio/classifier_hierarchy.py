"""Acoustic classifier hierarchy: Level 1 (Heuristic), Level 2 (Classical ML), Level 3 (Deep 2D CNN).

Provides unified model interfaces conforming to AudioClassifierBackend Protocol.
Enables experimental comparison across model complexities under identical evaluation data.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from railway_detection.audio.features import compute_log_mel_spectrogram
from railway_detection.utils.logging import get_logger

logger = get_logger("audio.hierarchy")


def extract_tabular_features_from_mel(log_mel: np.ndarray) -> np.ndarray:
    """Summarize a 2D Log-Mel spectrogram (n_mels, n_frames) into a compact 1D feature vector.

    Extracts summary statistics per frequency band across time:
    - Mean power per band (64)
    - Standard deviation per band (64)
    - Peak power per band (64)
    - Spectral flux / differential across time (64)

    Total feature dimension: 256.
    """
    mean_band = np.mean(log_mel, axis=1)
    std_band = np.std(log_mel, axis=1)
    max_band = np.max(log_mel, axis=1)
    diff_band = np.mean(np.abs(np.diff(log_mel, axis=1)), axis=1)
    return np.concatenate([mean_band, std_band, max_band, diff_band]).astype(np.float64)


class ClassicalAudioClassifier:
    """Level 2 ML baseline operating on summarized spectral/Mel features.

    Supports linear / tree-based models (Logistic Regression, Random Forest)
    conforming strictly to AudioClassifierBackend protocol.
    """

    def __init__(
        self,
        model_type: str = "logistic_regression",
        operating_threshold: float = 0.5,
        model_weights: Any | None = None,
    ) -> None:
        self.model_type = model_type
        self.operating_threshold = float(operating_threshold)
        self.model_weights = model_weights

    def predict_features(self, features: np.ndarray) -> float:
        """Predict train horn probability from a 1D feature vector."""
        if self.model_weights is None:
            # Fallback prior before model is trained
            return 0.0

        # When model weights are loaded (e.g. scikit-learn estimator or coefficient vector)
        if hasattr(self.model_weights, "predict_proba"):
            probs = self.model_weights.predict_proba(features.reshape(1, -1))[0]
            return float(probs[1]) if len(probs) > 1 else float(probs[0])
        elif isinstance(self.model_weights, dict) and "coef" in self.model_weights:
            # Simple linear dot product
            coef = np.asarray(self.model_weights["coef"])
            intercept = float(self.model_weights.get("intercept", 0.0))
            z = float(np.dot(features, coef) + intercept)
            return float(1.0 / (1.0 + np.exp(-np.clip(z, -30.0, 30.0))))
        return 0.0

    def predict_window(
        self, window: np.ndarray, sample_rate: int = 16000
    ) -> tuple[float, str]:
        """Classify a 1D audio sample window using extracted Mel features."""
        samples = np.asarray(window, dtype=np.float64).flatten()
        if len(samples) == 0:
            return 0.0, "ambient"

        # Check silent noise floor
        rms = float(np.sqrt(np.mean(samples**2.0)))
        if rms < 0.001:
            return 0.0, "ambient"

        log_mel = compute_log_mel_spectrogram(
            samples, sample_rate=sample_rate, n_fft=512, hop_length=256, n_mels=64
        )
        feats = extract_tabular_features_from_mel(log_mel)
        prob = self.predict_features(feats)
        label = "train" if prob >= self.operating_threshold else "ambient"
        return float(prob), label


class LightweightAudioCNNInterface:
    """Level 3 Deep Learning architecture interface.

    Blueprint for 3-block 2D CNN consuming (64, 63) Log-Mel spectrograms.
    Conforms strictly to AudioClassifierBackend protocol.
    """

    def __init__(
        self,
        operating_threshold: float = 0.5,
        model_checkpoint_path: str | None = None,
    ) -> None:
        self.operating_threshold = float(operating_threshold)
        self.model_checkpoint_path = model_checkpoint_path
        self._model = None

    def predict_spectrogram(self, log_mel: np.ndarray) -> float:
        """Predict horn probability from (64, 63) Log-Mel spectrogram tensor."""
        if self._model is None:
            return 0.0
        # Deep learning forward pass logic once weights are trained
        return 0.0

    def predict_window(
        self, window: np.ndarray, sample_rate: int = 16000
    ) -> tuple[float, str]:
        """Classify audio window using 2D CNN inference."""
        samples = np.asarray(window, dtype=np.float64).flatten()
        if len(samples) == 0:
            return 0.0, "ambient"

        log_mel = compute_log_mel_spectrogram(
            samples, sample_rate=sample_rate, n_fft=512, hop_length=256, n_mels=64
        )
        prob = self.predict_spectrogram(log_mel)
        label = "train" if prob >= self.operating_threshold else "ambient"
        return float(prob), label
