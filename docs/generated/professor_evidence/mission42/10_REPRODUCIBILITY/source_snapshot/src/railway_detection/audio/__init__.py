"""Audio pipeline: features, dataset, model, training, evaluation, and inference.

Modules:
- features: STFT and Log-Mel spectrogram extraction (pure NumPy/SciPy).
- dataset: Manifest-driven window loading and batch generation.
- model: Classifier backends (spectral baseline, PyTorch CNN).
- training: Training config, checkpointing, and pretraining safety gates.
- evaluation: Binary metrics, calibration, ROC/PR curves, figures.
- pipeline: End-to-end audio processing pipeline.
- noise_mixer: Synthetic noise augmentation.
- preprocessor: Audio preprocessing utilities.
- classifier_hierarchy: Multi-level classifier taxonomy.
"""

from __future__ import annotations
