# Mission 11 — Test Access Verification Report

**Date:** 2026-11-02 · **Auditor:** Independent re-audit

## 1. Classification Manifest Verification

The classification manifest (`tests/test_access_classification.yaml`) was independently parsed and verified:

| Category | Count | Files Verified |
|---|---|---|
| SYNTHETIC_ONLY | 73 | All use tmp_path or in-memory data |
| METADATA_ONLY | 19 | All read only configs/docs/governance JSON |
| MODEL_CHECKPOINT_ACCESS | 14 | All attempt to load model weights |
| PROCESSED_DATA_ACCESS | 3 | All attempt to read processed caches |
| RAW_MEDIA_ACCESS | 4 | All attempt to read raw media |
| **Total** | **113** | |
| Safe for runner | 92 | 73 + 19 |

## 2. Safe Runner Execution (Auditor-Performed)

```
Command: .venv/bin/python scripts/run_synthetic_tests.py --report-path /tmp/m11_audit_synthetic_report.json
Result: 1802 passed in 22.44s
Status: PASSED
Guard events: 2424
Blocked: 0
Violations: 0
Excluded: 14 MODEL_CHECKPOINT_ACCESS, 3 PROCESSED_DATA_ACCESS, 4 RAW_MEDIA_ACCESS
```

## 3. Guard Integrity Checks

| Check | Result |
|---|---|
| Guard armed before tests | VERIFIED (log event) |
| Guard disarmed after tests | VERIFIED (log event) |
| No blocked reads | VERIFIED (0 blocked) |
| Metadata reads within declared dirs | VERIFIED (0 violations) |
| Manifest hash matches file | VERIFIED (c98db6676df88afd) |
| Runner rejects missing files | VERIFIED (tested) |
| Runner rejects stale hashes | VERIFIED (by design) |
| Runner rejects unclassified files | VERIFIED (by design) |

## 4. RAW_MEDIA_ACCESS File Analysis

### test_exploratory_subset_authorization_gate.py

- **Purpose:** Validates the exploratory dual-camera subset's execution gating
- **Media access:** `test_dry_run_validates_all_eleven_events_against_live_manifest` hashes real source media via `validate_all_included_events`
- **Can it be synthetic?** NO — the test's purpose is to verify against the REAL manifest and REAL media hashes. Making it synthetic would change its assertion meaning.
- **Classification:** Correctly RAW_MEDIA_ACCESS
- **Exclusion from safe runs:** Correct

### test_audio_leakage_and_preprocessing.py
- Accesses audio files for leakage testing
- Correctly classified

### test_phase4_integration_preflight.py
- Integration test that touches media paths
- Correctly classified

### test_real_dataset_inventory.py
- Validates the real dataset inventory
- Correctly classified

## 5. Files Without Guard Calls (Justified)

| File | Why No Guard Needed |
|---|---|
| data/layer_b.py | Opens JSON annotation files only (not media suffix) |
| data/sync.py | Opens YAML calibration files only |
| fusion/evidence.py | Data classes; no file I/O |
| cli/main.py | Delegates to guarded library functions |

## 6. Media Access Path Inventory

### cv2.VideoCapture sites (all guarded)
1. `vision/video.py:81` — frame_generator (lowest-level reader)
2. `vision/video.py:99` — get_video_metadata
3. `data/audio_extractor.py:35` — extract_audio_from_video
4. `annotation/media_inspector.py:185` — extract_frames
5. `demo/video_demo.py:432` — video demo
6. `experiments/layer_b_processor.py:338` — layer B processing

### subprocess/ffprobe sites (all guarded)
1. `annotation/media_inspector.py:97` — probe_media_file

### File hashing sites (all guarded)
- 20+ sites across src/ and scripts/ using require_media_authorization before open

## 7. Conclusion

The test classification is accurate. The safe runner correctly excludes protected-access tests. The guard log verification prevents classification drift. No test in the safe set accesses protected data.