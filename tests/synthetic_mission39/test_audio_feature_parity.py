"""V3 training/inference parity on constructed signals, without real checkpoints."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest
import torch

from railway_detection.audio.features import compute_log_mel_spectrogram
from railway_detection.audio.model import PyTorchTrainHornClassifier
from railway_detection.experiments.cache_provenance import build_audio_preprocessing_config
from railway_detection.experiments.frozen_config import load_frozen_config


def training_features(samples):
    # Import only the source; the script's main ingestion routine is not called.
    path = Path(__file__).resolve().parents[2] / 'scripts/preprocess_audio_dataset_v3.py'
    spec = importlib.util.spec_from_file_location('v3_training_preprocessor_parity', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.compute_log_mel_spectrogram(samples, f_min=80.0, f_max=8000.0)


@pytest.mark.parametrize('signal', ['silence', 'tone', 'noise', 'quiet'])
def test_v3_features_match_actual_training_source(signal):
    rng = np.random.default_rng(42)
    samples = {
        'silence': np.zeros(16000),
        'tone': .25 * np.sin(2 * np.pi * 440 * np.arange(16000) / 16000),
        'noise': rng.uniform(-.5, .5, 16000),
        'quiet': rng.uniform(-1e-8, 1e-8, 16000),
    }[signal]
    actual = compute_log_mel_spectrogram(
        samples, f_min=80.0, f_max=8000.0, log_scale='natural'
    )
    expected = training_features(samples)
    assert actual.shape == (64, 61)
    np.testing.assert_array_equal(actual, expected)


def test_classifier_receives_training_features_with_checkpoint_normalization():
    class CaptureModel(torch.nn.Module):
        def forward(self, value):
            self.received = value.detach().cpu().numpy()
            return torch.zeros(1)

    model = CaptureModel()
    classifier = PyTorchTrainHornClassifier(
        model=model, mean=-1.600999355316162, std=5.1239728927612305, threshold=.37
    )
    samples = .1 * np.sin(2 * np.pi * 300 * np.arange(16000) / 16000)
    probability, label = classifier.predict_window(samples)
    expected = ((training_features(samples) - classifier.mean) / classifier.std).astype('float32')
    np.testing.assert_array_equal(model.received, expected[None])
    assert probability == .5 and label == 'train'


def test_default_db_features_remain_compatible():
    samples = np.zeros(16000)
    spec = compute_log_mel_spectrogram(samples)
    np.testing.assert_array_equal(spec, np.full((64, 61), -100.0))
    assert not np.allclose(spec, training_features(samples))


def test_invalid_scale_refuses():
    with pytest.raises(ValueError, match='log_scale'):
        compute_log_mel_spectrogram(np.zeros(16000), log_scale='guessed')


def test_audio_cache_identity_declares_training_transform():
    preproc = build_audio_preprocessing_config(load_frozen_config())
    assert preproc['log_scale'] == 'natural'
    assert preproc['log_epsilon'] == 1e-10
    assert preproc['operating_threshold'] == .37
