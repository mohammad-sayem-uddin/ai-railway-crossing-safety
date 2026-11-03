# Mission 12 — Reproducibility and Provenance

## Observed environment

| Item | Observed value |
|---|---|
| HEAD | `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` |
| Python | 3.11.15 |
| PyTorch | 2.13.0 |
| Ultralytics | 8.4.121 |
| Ruff | 0.16.3 |
| Pytest | 9.1.1 |
| macOS | 26.6.2 |
| Darwin kernel | 25.6.0 ARM64 |
| Controller tick | 0.2 s from frozen configuration |
| Decision policy SHA-256 | `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575` |
| Frozen configuration SHA-256 | `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a` |
| Ground-truth protocol SHA-256 | `d100c1e6a63280c375f94e297416efb0cf7dd3c15c9aa8df076ede052d49ecf4` |
| Safe runner source SHA-256 | `058893c16471e98d5b58bcd445b15446833c5135ec5400a39e9a8578404dfafb` |
| Replay producer identity | `phase12-replay-producer/1` |

## Not verified

- Model/checkpoint hashes: **`NOT_VERIFIED — REQUIRES AUTHORIZED ACCESS`**.
- Raw-media hashes: not recomputed; prohibited by mission constraints.
- Real-data dataset provenance: metadata references exist, but no real-data evaluation or authorization exists.
- Ground-truth approval/provenance: no new review/adjudication/receipt created.

## Engineering identity

- Cache conditions: B0/B1/B2 implemented in the descriptive cache engine.
- Official modes: single, independent and dual camera paths exist; independent mode has separate front/back systems.
- B0_back/B2_back: provisional/proposed, not adopted and not implemented in cache engine.
- M4/M5/lead-in metrics: existing Phase 1 implementation and synthetic differential tests.

## Known limitations and unexecuted operations

The safe runner excludes 14 checkpoint, 3 processed-data and 4 raw-media tests. After Mission 12 test changes, the runner correctly refuses to execute because four manifest entries are stale; no safe-runner tests were executed in that invocation. Python-level authorization is not an OS sandbox. No real inference, replay, cache evaluation, media inspection or human review was performed.