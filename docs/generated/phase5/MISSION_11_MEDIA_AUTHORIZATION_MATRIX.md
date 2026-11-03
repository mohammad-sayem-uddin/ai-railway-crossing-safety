# Mission 11 — Media Authorization Coverage Matrix

**Date:** 2026-11-02 · **Auditor:** Independent re-audit

## A. Complete Access Inventory

### Video Readers (cv2.VideoCapture)

| # | Module | Function | Guard Present | Guard Location | Verified |
|---|---|---|---|---|---|
| 1 | vision/video.py | frame_generator | YES | L80 | Live test |
| 2 | vision/video.py | get_video_metadata | YES | L98 | Source inspection |
| 3 | data/audio_extractor.py | extract_audio_from_video | YES | L34 | Live test |
| 4 | annotation/media_inspector.py | extract_frames | YES | L184 | Source inspection |
| 5 | demo/video_demo.py | run_video_demo | YES | L431 | Source inspection |
| 6 | experiments/layer_b_processor.py | process_event | YES | L337 | Source inspection |

### Audio/FFprobe Readers

| # | Module | Function | Guard Present | Guard Location | Verified |
|---|---|---|---|---|---|
| 1 | annotation/media_inspector.py | probe_media_file | YES | L96 | Source inspection |

### File Hashers (open + sha256)

| # | Module | Function | Guard Present | Guard Location |
|---|---|---|---|---|
| 1 | annotation/media_inspector.py | compute_file_sha256 | YES | L73 |
| 2 | annotation/receipt.py | sha256_file | YES | L34 |
| 3 | annotation/readiness_cli.py | _sha256_file | YES | L60 |
| 4 | annotation/promotion_gate.py | (internal) | YES | L226 |
| 5 | annotation/adjudication_session.py | (internal) | YES | L146 |
| 6 | annotation/candidate_split_queue.py | (internal) | YES | L80 |
| 7 | annotation/stage21_timing_pilot.py | (internal) | YES | L945 |
| 8 | data/r04_evidence.py | (internal) | YES | L41 |
| 9 | data/sync_calibration.py | (internal) | YES | L454 |
| 10 | data/validator.py | (internal) | YES | L208 |
| 11 | evaluation/experiment_engine.py | (internal) | YES | L199 |
| 12 | evaluation/input_contracts.py | (internal) | YES | L68 |
| 13 | experiments/leakage_guard.py | (internal) | YES | L61 |
| 14 | field_validation/capture_session.py | (internal) | YES | L285 |
| 15 | field_validation/capture_session_v2.py | (internal) | YES | L729 |
| 16 | optimization/benchmark_suite.py | (internal) | YES | L163 |

### Script-Level Guards

| # | Script | Guard Type | Operations |
|---|---|---|---|
| 1 | run_phase5_full_inference.py | precheck + per-file | INFERENCE, HASH, PROBE |
| 2 | extract_sync_review_frames.py | precheck + per-file | FRAME_EXTRACTION, HASH |
| 3 | audit_train_video_audio_2.py | per-file | HASH, PROBE |
| 4 | build_audio_training_pipeline.py | per-file | HASH, PROBE, AUDIO_EXTRACTION, FEATURE |
| 5 | build_camera_sync_candidate_manifest.py | per-file | HASH |
| 6 | collect_camera_creation_time_deltas.py | per-file | PROBE |
| 7 | estimate_camera_sync_offsets.py | per-file | FEATURE_EXTRACTION |
| 8 | mission5a_build_preservation_manifest.py | per-file | HASH |
| 9 | organize_and_manifest_datasets.py | per-file | HASH, PROBE |
| 10 | organize_v2_dataset.py | per-file | HASH |
| 11 | prepare_researcher_snapshot.py | per-file | HASH |
| 12 | preprocess_audio_dataset.py | per-file | HASH, PROBE, AUDIO_EXTRACTION, FEATURE |
| 13 | preprocess_audio_dataset_v2.py | per-file | AUDIO_EXTRACTION, FEATURE |
| 14 | preprocess_audio_dataset_v3.py | per-file | AUDIO_EXTRACTION, FEATURE |
| 15 | run_canonical_tests.py | per-file | HASH, FRAME, AUDIO, PROBE |
| 16 | select_and_manifest_audio_v3.py | per-file | HASH, PROBE |
| 17 | train_audio_model.py | per-file | FEATURE_EXTRACTION |
| 18 | mission10_artifact_manifest.py | per-file | HASH (no-op for non-media) |

## B. Authorization Validation Schema

### AUTH-MEDIA-ACCESS v2 Contract

| Field | Validation |
|---|---|
| schema_version | Must be "phase5-media-access-authorization/2" |
| authorization_id | Non-empty string |
| authorization_class | Must be "AUTH-MEDIA-ACCESS" |
| status | Must be "APPROVED" |
| authorized_by | Must be on allowlist |
| authorized_at_utc | TZ-aware, not in future |
| expires_at_utc | TZ-aware, after issue, not expired |
| revoked | Must be strict `False` (not truthiness) |
| scope.operations | Subset of VALID_MEDIA_OPERATIONS |
| scope.datasets | Non-empty string list |
| scope.events | Cohort-qualified or ALL_EVENTS_IN_DATASETS |
| scope.media_types | Subset of VIDEO/AUDIO |
| scope.purpose | Specific (≥10 chars) |
| restrictions.path_prefixes | Checked against resolved path |
| bindings.protocol_document | Path + SHA-256, re-hashed live |
| record_sha256 | Must match canonical record hash |

### Security Properties Verified

| Property | Result |
|---|---|
| Signer on allowlist | Enforced |
| Expiration checked | Enforced (tz-aware) |
| Revocation strict bool | Enforced |
| Dataset scope | Enforced |
| Event scope (cohort-qualified) | Enforced |
| Media type scope | Enforced |
| Operation scope | Enforced |
| Path prefix restriction | Enforced |
| Protocol hash revalidation | Enforced (live re-hash) |
| Symlink resolution | Enforced (Path.resolve()) |
| repo_root override for real repo | Denied |
| Environment variable bypass | Denied |
| In-memory permit construction | N/A (no permit for media) |
| Import-time caching | None (reads disk every call) |

## C. Bypass Test Results (Auditor-Performed)

| Test | Input | Expected | Actual | Status |
|---|---|---|---|---|
| Synthetic temp media | tmp/*.mov | Allowed | Allowed | PASS |
| Real repo media | data/raw/.../*.mov | Denied | AUTH_MEDIA_ACCESS_NOT_GRANTED | PASS |
| Env var override | RAILWAY_ALLOW_RESTRICTED_MEDIA_ACCESS=1 | Denied | AUTH_MEDIA_ACCESS_NOT_GRANTED | PASS |
| Non-media file | *.json | Allowed (no-op) | Allowed | PASS |

## D. Trust Boundary Disclosure

This is a **Python-level software guard**. It defends against:
- Accidental media access through repository code paths
- Scripts and CLI commands that forget authorization checks
- New code that calls existing openers

It does NOT defend against:
- `cp`, `cat`,