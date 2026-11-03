"""Audio classifier backends and baseline spectral energy model."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import math
import numpy as np

from railway_detection.audio.features import compute_stft
from railway_detection.utils.logging import get_logger

logger = get_logger("audio.model")


@runtime_checkable
class AudioClassifierBackend(Protocol):
    """Protocol for audio window classification backends."""

    def predict_window(
        self, window: np.ndarray, sample_rate: int = 16000
    ) -> tuple[float, str]:
        """Predict probability and class label for an audio window.

        Args:
            window: 1D numpy array of audio samples in [-1.0, 1.0].
            sample_rate: Sampling frequency in Hz.

        Returns:
            Tuple of (confidence in [0.0, 1.0], label string e.g. 'train' or 'ambient').
        """
        ...


class SpectralEnergyBaseline:
    """Deterministic spectral energy ratio classifier baseline for railway sounds.

    Computes the proportion of power spectral energy within characteristic
    railway acoustic bands (diesel rumble + wheel-rail flange + horn: 80–2500 Hz)
    relative to wideband noise.
    """

    def __init__(
        self,
        band_low_hz: float = 80.0,
        band_high_hz: float = 2500.0,
        energy_threshold: float = 0.35,
        min_rms_threshold: float = 0.005,
    ) -> None:
        self.band_low_hz = float(band_low_hz)
        self.band_high_hz = float(band_high_hz)
        self.energy_threshold = float(energy_threshold)
        self.min_rms_threshold = float(min_rms_threshold)

    def predict_window(
        self, window: np.ndarray, sample_rate: int = 16000
    ) -> tuple[float, str]:
        """Classify audio window using spectral energy ratio."""
        samples = np.asarray(window, dtype=np.float64).flatten()
        if len(samples) == 0:
            return 0.0, "ambient"

        # Check silence / noise floor
        rms = float(np.sqrt(np.mean(samples**2.0)))
        if rms < self.min_rms_threshold:
            return 0.0, "ambient"

        n_fft = min(512, len(samples))
        if n_fft < 16:
            return 0.0, "ambient"

        stft = compute_stft(samples, n_fft=n_fft, hop_length=n_fft // 2)
        power = np.abs(stft) ** 2.0
        total_energy = float(np.sum(power))

        if total_energy <= 1e-12:
            return 0.0, "ambient"

        freqs = np.fft.rfftfreq(n_fft, d=1.0 / sample_rate)
        band_mask = (freqs >= self.band_low_hz) & (freqs <= self.band_high_hz)

        in_band_energy = float(np.sum(power[band_mask, :]))
        energy_ratio = in_band_energy / total_energy

        # Scale ratio around energy_threshold to produce a smooth confidence score [0.0, 1.0]
        # Ratio above energy_threshold mapped towards 1.0
        if energy_ratio >= self.energy_threshold:
            normalized = (energy_ratio - self.energy_threshold) / max(
                1.0 - self.energy_threshold, 1e-6
            )
            confidence = float(np.clip(0.5 + 0.5 * normalized, 0.0, 1.0))
            label = "train"
        else:
            normalized = energy_ratio / max(self.energy_threshold, 1e-6)
            confidence = float(np.clip(0.5 * (1.0 - normalized), 0.0, 0.5))
            label = "ambient"

        return confidence, label


class CompactTrainHornCNN:
    """Compact 2D Convolutional Neural Network for train horn detection on Log-Mel spectrograms.

    Input tensor shape: (B, 1, 64, 61) or (B, 64, 61).
    Total parameter count: ~75,000 parameters.
    Designed for high generalization and strict prevention of overfitting on small acoustic pools.
    """

    def __new__(cls, *args, **kwargs):
        # Lazily import torch to preserve zero-dependency import if torch is not required
        import torch
        import torch.nn as nn
        import torch.nn.functional as F

        class _CNNModule(nn.Module):
            def __init__(self, in_channels: int = 1, dropout: float = 0.3) -> None:
                super().__init__()
                self.conv1 = nn.Conv2d(in_channels, 16, kernel_size=3, padding=1)
                self.bn1 = nn.BatchNorm2d(16)
                self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)

                self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
                self.bn2 = nn.BatchNorm2d(32)
                self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

                self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
                self.bn3 = nn.BatchNorm2d(64)
                self.pool3 = nn.AdaptiveAvgPool2d((1, 1))

                self.fc1 = nn.Linear(64, 32)
                self.bn_fc = nn.BatchNorm1d(32)
                self.dropout = nn.Dropout(dropout)
                self.fc2 = nn.Linear(32, 1)

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                if x.dim() == 3:
                    x = x.unsqueeze(1)
                x = self.pool1(F.relu(self.bn1(self.conv1(x))))
                x = self.pool2(F.relu(self.bn2(self.conv2(x))))
                x = self.pool3(F.relu(self.bn3(self.conv3(x))))
                x = x.flatten(start_dim=1)
                x = self.dropout(F.relu(self.bn_fc(self.fc1(x))))
                return self.fc2(x).squeeze(-1)

        return _CNNModule(*args, **kwargs)


class PyTorchTrainHornClassifier:
    """Production inference wrapper around trained CompactTrainHornCNN conforming to AudioClassifierBackend."""

    def __init__(
        self,
        model: Any | None = None,
        checkpoint_path: str | Path | None = None,
        threshold: float | None = None,
        mean: float = 0.0,
        std: float = 1.0,
        device: str = "cpu",
    ) -> None:
        import torch

        self.device = torch.device(device)
        self.threshold = float(threshold) if threshold is not None else 0.3700
        self._user_threshold = threshold
        self.mean = float(mean)
        self.std = float(std) if std > 1e-6 else 1.0

        if checkpoint_path is not None:
            self._load_checkpoint(checkpoint_path)
        elif model is not None:
            self.model = model.to(self.device)
            self.model.eval()
            self._validate_normalization_params()
        else:
            self.model = CompactTrainHornCNN().to(self.device)
            self.model.eval()
            self._validate_normalization_params()

    def _validate_normalization_params(self) -> None:
        if not math.isfinite(self.mean):
            raise ValueError(f"Normalization mean must be finite, got {self.mean}")
        if not math.isfinite(self.std):
            raise ValueError(f"Normalization std must be finite, got {self.std}")
        if self.std <= 1e-6:
            raise ValueError(f"Normalization std must be positive and > 1e-6, got {self.std}")
        if not math.isfinite(self.threshold) or not (0.0 <= self.threshold <= 1.0):
            raise ValueError(
                f"Operating threshold must be finite and within [0.0, 1.0], got {self.threshold}"
            )

    def _load_checkpoint(self, path: str | Path) -> None:
        import torch

        ckpt_path = Path(path)
        if not ckpt_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {ckpt_path}")

        # Hard failure on prohibited checkpoints (e.g. Audio V2)
        from railway_detection.experiments.leakage_guard import verify_not_prohibited_checkpoint
        verify_not_prohibited_checkpoint(ckpt_path)

        try:
            state = torch.load(ckpt_path, map_location=self.device, weights_only=True)
        except Exception:
            state = torch.load(ckpt_path, map_location=self.device, weights_only=False)

        if not isinstance(state, dict):
            raise ValueError(f"Checkpoint at {ckpt_path} is not a dictionary")

        self.model = CompactTrainHornCNN()
        if "model_state_dict" in state:
            self.model.load_state_dict(state["model_state_dict"])
        elif "state_dict" in state:
            self.model.load_state_dict(state["state_dict"])
        else:
            raise ValueError(
                f"Checkpoint at {ckpt_path} contains no recognized model weights key ('model_state_dict' or 'state_dict')"
            )

        # Read normalization statistics: check 'norm_mean' (Audio V3 standard) or legacy 'feature_mean'
        if "norm_mean" in state:
            self.mean = float(state["norm_mean"])
        elif "feature_mean" in state:
            self.mean = float(state["feature_mean"])
        else:
            raise ValueError(
                f"Checkpoint at {ckpt_path} lacks required normalization mean ('norm_mean' / 'feature_mean'). "
                "Silent fallback to unnormalized default is prohibited."
            )

        if "norm_std" in state:
            self.std = float(state["norm_std"])
        elif "feature_std" in state:
            self.std = float(state["feature_std"])
        else:
            raise ValueError(
                f"Checkpoint at {ckpt_path} lacks required normalization standard deviation ('norm_std' / 'feature_std'). "
                "Silent fallback to unnormalized default is prohibited."
            )

        if "operating_threshold" in state:
            ckpt_thresh = float(state["operating_threshold"])
            # Prevent unauthorized caller override of frozen threshold
            if self._user_threshold is not None and abs(self._user_threshold - ckpt_thresh) > 1e-4:
                raise ValueError(
                    f"Threshold override mismatch: caller supplied {self._user_threshold}, but checkpoint records {ckpt_thresh}. "
                    "Unauthorized runtime threshold mutation is prohibited."
                )
            self.threshold = ckpt_thresh

        self._validate_normalization_params()
        self.model.to(self.device)
        self.model.eval()

    def predict_window(
        self, window: np.ndarray, sample_rate: int = 16000
    ) -> tuple[float, str]:
        """Classify raw audio window (default 1.0s = 16,000 samples)."""
        import torch
        from railway_detection.audio.features import compute_log_mel_spectrogram

        samples = np.asarray(window, dtype=np.float64).flatten()
        if len(samples) == 0:
            return 0.0, "ambient"

        target_len = int(1.0 * sample_rate)
        if len(samples) < target_len:
            samples = np.pad(samples, (0, target_len - len(samples)), mode="reflect")
        elif len(samples) > target_len:
            samples = samples[:target_len]

        # Extract 64-band Log-Mel spectrogram (shape: 64, 61)
        log_mel = compute_log_mel_spectrogram(
            samples,
            sample_rate=sample_rate,
            n_fft=512,
            hop_length=256,
            n_mels=64,
            f_min=80.0,
            f_max=8000.0,
        )
        norm_mel = (log_mel - self.mean) / self.std
        tensor = torch.from_numpy(norm_mel).float().unsqueeze(0).to(self.device)

        with torch.no_grad():
            logit = self.model(tensor)
            prob = float(torch.sigmoid(logit).item())

        label = "train" if prob >= self.threshold else "ambient"
        return prob, label
