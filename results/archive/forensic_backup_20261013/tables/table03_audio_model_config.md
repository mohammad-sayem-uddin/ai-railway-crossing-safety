### Table 3: CompactTrainHornCNN Audio Model Configuration

| Parameter | Specification / Value | Methodological Rationale |
| --- | --- | --- |
| Architecture | CompactTrainHornCNN (3-block CNN, 25,697 params) | Overfitting prevention on small acoustic pools |
| Acoustic Representation | 64-band Log-Mel Spectrogram (64 x 61) | Time-frequency horn harmonic resolution |
| Analysis Window | 1.0s window, 0.5s hop stride, 16kHz mono | Standard sliding acoustic window |
| Frozen Checkpoint Path | experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt | Preserved optimal validation model |
| Checkpoint SHA-256 | ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782 | Cryptographic immutability verified |
| Operating Threshold | T* = 0.3700 | Optimal F1 calibrated on held-out validation (ESC-50) |
| Safety Constraint | Supporting Only (Never commands gate opening) | Safety policy invariant INV-1 |
