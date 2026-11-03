# R04 Event-Level Evidence and Candidate Scope

> **Status: CANDIDATE EVIDENCE ONLY.** This report does not promote calibration, approve labels, authorize a replay, or authorize field operation.

Generated from `r04-event-evidence/2`; 27 active events. Deterministic calibration verdicts: `{'AMBIGUOUS': 8, 'CALIBRATION_SUPPORTED': 12, 'PROVISIONAL': 7}`.

## Candidate scope

Exactly **12** events have `CALIBRATION_SUPPORTED` diagnostics and are candidates for a separately labelled exploratory dual-camera scope:

`train_events/event_001`, `train_events/event_002`, `train_events/event_005`, `train_events/event_006`, `train_events/event_007`, `train_events/event_009`, `train_events/event_010`, `train_events/event_011`, `train_events/event_012`, `train_events/event_013`, `train_events/event_014`, `train_events/event_017`

The remaining events are **blocked by R04** (PROVISIONAL, AMBIGUOUS, FAILED, or NOT_ASSESSABLE). The candidate manifest remains `CANDIDATE_UNVALIDATED_DO_NOT_MERGE`; all human review and ground-truth approval fields remain unresolved.

## Event-level candidate evidence

| Event | Active candidate proposal | Calibration | Lag (s) | T1 candidate | T4 candidate | Scope / decision |
|---|---|---|---:|---|---|---|
| `engine_events/event_001` | `data/ground_truth/proposals/engine_events/event_001_proposal_v3.json` v3 SHA-256 `aa0d94d83e16975fc6930bbd27cd874c7394959e4343c8c8ce02674d771f648a` | `PROVISIONAL` | 3.4964 | `CANDIDATE_CENSORED_LEFT (0.0; front)` | `CANDIDATE_CENSORED_RIGHT (None; back)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |
| `no_train_events/event_001` | `data/ground_truth/proposals/no_train_events/event_001_proposal_v2.json` v2 SHA-256 `6b2e4ddc7e43054666115d2f1ca0648ae7a47dce22490de13a29031a191cb6b2` | `AMBIGUOUS` | 1.4277 | `CANDIDATE_NOT_APPLICABLE (None; None)` | `CANDIDATE_NOT_APPLICABLE (None; None)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |
| `no_train_events/event_002` | `data/ground_truth/proposals/no_train_events/event_002_proposal_v2.json` v2 SHA-256 `0fd3a48a0c30675e46635795c6aacdbaed294a0d21ad510462fd4848db1de956` | `AMBIGUOUS` | -4.0483 | `CANDIDATE_NOT_APPLICABLE (None; None)` | `CANDIDATE_NOT_APPLICABLE (None; None)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |
| `no_train_events/event_003` | `data/ground_truth/proposals/no_train_events/event_003_proposal_v2.json` v2 SHA-256 `e7619841db2308290bde1cb3267e485a2edcf07bae389a1798c50a5aaabd670f` | `PROVISIONAL` | -0.4022 | `CANDIDATE_NOT_APPLICABLE (None; None)` | `CANDIDATE_NOT_APPLICABLE (None; None)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_001` | `data/ground_truth/proposals/train_events/event_001_proposal_v6.json` v6 SHA-256 `0d9596a928039387585dfeeeebe1596124c1f6467fee92639b5a9adb12ba0703` | `CALIBRATION_SUPPORTED` | 7.406 | `CANDIDATE_OBSERVABLE_UNAPPROVED (5.8; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (45.0; back)` | `EXPLORATORY_CANDIDATE_ONLY` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_002` | `data/ground_truth/proposals/train_events/event_002_proposal_v2.json` v2 SHA-256 `3079950c376a2085d747e9287badd92b3ef3915f305ddd250cb5325cf9e02ea3` | `CALIBRATION_SUPPORTED` | 4.1867 | `CANDIDATE_OBSERVABLE_UNAPPROVED (2.9; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (28.8; back)` | `EXPLORATORY_CANDIDATE_ONLY` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_003` | `data/ground_truth/proposals/train_events/event_003_proposal_v2.json` v2 SHA-256 `8042807536dc178e3c672385c5854336e6cf35c6141ebaf55728d7d9468c3674` | `PROVISIONAL` | 3.7272 | `CANDIDATE_OBSERVABLE_UNAPPROVED (2.1; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (30.5; back)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_004` | `data/ground_truth/proposals/train_events/event_004_proposal_v2.json` v2 SHA-256 `b5f892f737ceec53bcc5b00966107be03031e44d488d71d5dad06f04131301d3` | `AMBIGUOUS` | 4.9001 | `CANDIDATE_OBSERVABLE_UNAPPROVED (2.1; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (76.8; back)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_005` | `data/ground_truth/proposals/train_events/event_005_proposal_v4.json` v4 SHA-256 `020bd9c4a721ba8221b18ac3ca296193cd94ad17167cdc35800aa5d494c336e5` | `CALIBRATION_SUPPORTED` | 6.038 | `CANDIDATE_UNOBSERVABLE (None; front)` | `CANDIDATE_CENSORED_RIGHT (None; back)` | `EXPLORATORY_CANDIDATE_ONLY` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_006` | `data/ground_truth/proposals/train_events/event_006_proposal_v2.json` v2 SHA-256 `039a65f4fd4dab3b7f52413201969b742dc18e819b92f043c200f24b3a52ac6d` | `CALIBRATION_SUPPORTED` | 4.5124 | `CANDIDATE_OBSERVABLE_UNAPPROVED (2.5; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (125.8; back)` | `EXPLORATORY_CANDIDATE_ONLY` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_007` | `data/ground_truth/proposals/train_events/event_007_proposal_v2.json` v2 SHA-256 `88ac5f83e7561fb0f308ef143fee023cb27e98edf6ce67b2c110081c5269f785` | `CALIBRATION_SUPPORTED` | 8.8801 | `CANDIDATE_OBSERVABLE_UNAPPROVED (2.6; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (33.5; back)` | `EXPLORATORY_CANDIDATE_ONLY` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_008` | `data/ground_truth/proposals/train_events/event_008_proposal_v2.json` v2 SHA-256 `bb29b1848bb8685ba3bf91e393556c16edb0816767586866999587f1c9bf7330` | `AMBIGUOUS` | 3.6479 | `CANDIDATE_OBSERVABLE_UNAPPROVED (2.4; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (61.2; back)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_009` | `data/ground_truth/proposals/train_events/event_009_proposal_v2.json` v2 SHA-256 `b26fb9f09b8b76ec00d942a55994695494f99d9e1d16df7fc6429e7706bcd115` | `CALIBRATION_SUPPORTED` | 9.4043 | `CANDIDATE_OBSERVABLE_UNAPPROVED (4.2; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (36.4; back)` | `EXPLORATORY_CANDIDATE_ONLY` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_010` | `data/ground_truth/proposals/train_events/event_010_proposal_v2.json` v2 SHA-256 `315a70fd902de301864c9badf5b70f22f8928a68bb0cab6dfb0c9a1d39528dc7` | `CALIBRATION_SUPPORTED` | 2.7158 | `CANDIDATE_OBSERVABLE_UNAPPROVED (2.7; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (22.4; back)` | `EXPLORATORY_CANDIDATE_ONLY` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_011` | `data/ground_truth/proposals/train_events/event_011_proposal_v2.json` v2 SHA-256 `b93b4743dbec6a618040cdb6285dd17c40ac0736b1969e086e6a71e8b4a611ac` | `CALIBRATION_SUPPORTED` | 5.2713 | `CANDIDATE_OBSERVABLE_UNAPPROVED (2.8; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (29.4; back)` | `EXPLORATORY_CANDIDATE_ONLY` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_012` | `data/ground_truth/proposals/train_events/event_012_proposal_v2.json` v2 SHA-256 `a45da6b905de79b36db6382c5dc80bacf6646cfe3b3529c619479c3b2e6b8227` | `CALIBRATION_SUPPORTED` | 5.5679 | `CANDIDATE_OBSERVABLE_UNAPPROVED (3.1; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (69.2; back)` | `EXPLORATORY_CANDIDATE_ONLY` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_013` | `data/ground_truth/proposals/train_events/event_013_proposal_v2.json` v2 SHA-256 `cdb691cbfa415a05ce3dd390a71f6903964a865ee459cdc6d31c6c9edbc679fe` | `CALIBRATION_SUPPORTED` | 3.278 | `CANDIDATE_OBSERVABLE_UNAPPROVED (3.2; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (70.8; back)` | `EXPLORATORY_CANDIDATE_ONLY` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_014` | `data/ground_truth/proposals/train_events/event_014_proposal_v2.json` v2 SHA-256 `e6fe8f81e6b59154675b455cb6d20cd1698345d5321c0bb30db9c3f94efd112f` | `CALIBRATION_SUPPORTED` | 4.0806 | `CANDIDATE_OBSERVABLE_UNAPPROVED (2.6; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (51.2; back)` | `EXPLORATORY_CANDIDATE_ONLY` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_015` | `data/ground_truth/proposals/train_events/event_015_proposal_v2.json` v2 SHA-256 `e698947778110ac5a44102ccc7a6cc81a2a41f423e48a9e9810328043131c86f` | `AMBIGUOUS` | 11.4404 | `CANDIDATE_OBSERVABLE_UNAPPROVED (4.2; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (19.5; back)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_016` | `data/ground_truth/proposals/train_events/event_016_proposal_v2.json` v2 SHA-256 `f404feeb5d43513aeeb76804454efd1d2e98f5bc4b264337ab77258d0d5d22ea` | `PROVISIONAL` | 3.2592 | `CANDIDATE_OBSERVABLE_UNAPPROVED (4.2; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (44.1; back)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_017` | `data/ground_truth/proposals/train_events/event_017_proposal_v2.json` v2 SHA-256 `1a40c8bfc2a289db4a0cfe18edb5563f1ceddc0d24fde8a982420b888ee2ea02` | `CALIBRATION_SUPPORTED` | 4.5654 | `CANDIDATE_OBSERVABLE_UNAPPROVED (2.8; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (82.5; back)` | `EXPLORATORY_CANDIDATE_ONLY` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_018` | `data/ground_truth/proposals/train_events/event_018_proposal_v2.json` v2 SHA-256 `3ee97a958b356c40a266223dbe78a2018586c9f0d099bc5ca5df0fe0ee23edd1` | `PROVISIONAL` | 7.8752 | `CANDIDATE_OBSERVABLE_UNAPPROVED (2.7; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (50.8; back)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_019` | `data/ground_truth/proposals/train_events/event_019_proposal_v2.json` v2 SHA-256 `0deff3cad109ffd0199577f57a223affa3738d7d2974268e2ea7f7ebb4460908` | `PROVISIONAL` | 6.6558 | `CANDIDATE_OBSERVABLE_UNAPPROVED (3.0; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (47.2; back)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_020` | `data/ground_truth/proposals/train_events/event_020_proposal_v2.json` v2 SHA-256 `3b2537abc0bcd5c0c3554bb44e71b9f4b53fc5ab7744a9d64c55bd5f3345cb3c` | `AMBIGUOUS` | -0.0284 | `CANDIDATE_OBSERVABLE_UNAPPROVED (2.3; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (28.7; back)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_021` | `data/ground_truth/proposals/train_events/event_021_proposal_v2.json` v2 SHA-256 `65f1e27a5326bdb37c0377d8257d06974e658c20854fb1d5403217adcaff4395` | `PROVISIONAL` | -2.8056 | `CANDIDATE_OBSERVABLE_UNAPPROVED (3.2; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (60.1; back)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_022` | `data/ground_truth/proposals/train_events/event_022_proposal_v2.json` v2 SHA-256 `29e01ea7bbc866dd4165fd33443ddd3841178d72a4b11773f9d7c53f65a6e857` | `AMBIGUOUS` | 0.9626 | `CANDIDATE_OBSERVABLE_UNAPPROVED (2.5; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (45.1; back)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |
| `train_events/event_023` | `data/ground_truth/proposals/train_events/event_023_proposal_v2.json` v2 SHA-256 `cacdace3383b6829060cc4f9c5d3e9c12a76787312e6b5c7c2d1964bfd0b7a38` | `AMBIGUOUS` | 1.2277 | `CANDIDATE_OBSERVABLE_UNAPPROVED (2.8; front)` | `CANDIDATE_OBSERVABLE_UNAPPROVED (43.4; back)` | `BLOCKED_R04` / `RESEARCHER_DECISION_REQUIRED` |

## Premature-opening boundary coverage (not metric results)

- v9: candidate T1+T4 values on calibration-supported train events for 11/12 events. Accepted scope, approved labels, and replay traces are absent; official evaluable count: 0.
- M4: candidate observable T4 values for 22/24 train/engine events. Replay traces and `t_blocked` are absent; official evaluable count: 0.
- Candidate boundary availability only; not approved labels, accepted scope, replay outcomes, a metric denominator, or a performance result.


## Interpretation constraints

- Candidate T1/T4 and calibration diagnostics are evidence for human inspection only. The active proposal is chosen as the highest numeric proposal version; a differing frozen-snapshot proposal is separately hash-pinned in the JSON and is not silently treated as current.
- The human reviewer must inspect the cited source video/audio and decide boundary states; this report does not resolve visual ambiguity or human listening requirements.
- `CALIBRATION_SUPPORTED` means only that the frozen acoustic diagnostic rule passed (PSR, window stability, SNR, and QuickTime sanity bound). The reported `0.05 s` is a sub-frame geometric jitter bound, **not** a device-clock confidence interval.
- T0–T4 values and censoring states are candidate annotation evidence. `CANDIDATE_CENSORED_LEFT`, `CANDIDATE_CENSORED_RIGHT`, and `CANDIDATE_UNOBSERVABLE` are preserved; none is silently converted to a number.
- Dual-camera scope is exploratory-candidate-only. Full-cohort fusion remains blocked for the 15 non-supported events. No automatic approval or decision is emitted.

## Reproducibility

- `results/r04_sync_estimation/calibration_verdicts.json` SHA-256 `e09a89d30e2c1b05108ce512052cf9b9cd2af4c7b33e0d8b284f2a36139f733a`
- `data/ground_truth/snapshots/candidate_annotation_manifest_20261012.json` SHA-256 `7eaa0c9bde777d4b36ead21d0654d511cc103255c5bf965e8bc50417a3b8e4e1`
- `data/manifests/camera_sync_offsets_candidate.yaml` SHA-256 `aaac453b7047ff5302592203114bdc4fc13de1d149669ad4590f074fa4110dcc`
- `data/manifests/layer_b_v2_annotation_inventory.json` SHA-256 `5585e22ecc7841e2cca4d8e56b9d61999e252e1efaf5dfa6e57d81471b809a56`
