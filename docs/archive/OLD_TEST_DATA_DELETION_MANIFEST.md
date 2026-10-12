# Old Test Data Deletion Manifest

**Document Date:** 2026-10-07  
**Operation:** Controlled Dataset Replacement — Old Layer B Real-World Test Media Retirement  
**Status:** APPROVED FOR CONTROLLED DELETION  

---

## Executive Summary

This document records the exact inventory and disposition of all files evaluated during the controlled dataset replacement operation for the **AI Railway Level-Crossing Safety Research Project**.

- **Old Test Dataset (Layer B):** 21 train-passage events collected via dual-camera phone recordings (`1.mov` through `21.mov`, front and back).
- **Target of Deletion:** ONLY the raw and processed video/audio media files and symlinks strictly belonging to the retired Layer B 21-event evaluation dataset.
- **Protected Holdings:** Dataset V1 vision training, standalone train-horn audio training dataset (`positive` and `negative`), model checkpoints (`YOLO best.pt`, audio `best_checkpoint.pt`), source code, tests, configs, historical experiment benchmarks (B0–B7), and research documentation.

### Summary of Dispositions

| Category | Item Count | Storage Size | Notes |
|---|---|---|---|
| **DELETE: Old Raw Video Media** | 84 video files | 5,387,654,238 bytes (~5.018 GB) | 42 in `Train_test_video_new/`, 42 in `data/raw/layer_b/videos/` |
| **DELETE: Old Extracted Audio Media** | 42 audio files | 70,263,474 bytes (~67.01 MB) | 42 in `data/processed/layer_b/audio/` |
| **DELETE: Old Media Symlinks** | 21 symlinks | N/A | `camera_rear.mov -> camera_back.mov` in 21 event folders |
| **ARCHIVE: Old Event Metadata & Manifests** | 44 files | 101,071 bytes | 21 `metadata.json`, 21 `event_labels.json`, 2 manifests moved to `results/archive/` |
| **KEEP: Protected Datasets & Models** | 8,400+ files | > 1.5 GB | Dataset V1, audio training, model weights, code, tests, docs |
| **UNCERTAIN / PRESERVED (Not Deleted)** | 9 files | 204,849,623 bytes (~195.36 MB) | `Unseen_Video/` (5 files) & `outputs/temp_uploads/` (4 files) |

---

## 1. DELETE LIST (Old Real-World Testing Media Only)

The following files represent the old Layer B real-world evaluation dataset and their staging copies. They are confirmed for deletion.

### 1.1 Old Raw Video Media in `Train_test_video_new/` (42 Files)

| Path | Type | Size (Bytes) | Role | SHA-256 | Reason |
|---|---|---|---|---|---|
| `Train_test_video_new/Front/1.mov` | Raw Video (.mov) | 55,307,977 | Staging copy of old Layer B test video (front) | `d80bd6565b066edd...` | Old test dataset retirement |
| `Train_test_video_new/Front/2.mov` | Raw Video (.mov) | 35,947,506 | Staging copy of old Layer B test video (front) | `69811c9e515515e9...` | Old test dataset retirement |
| `Train_test_video_new/Front/3.mov` | Raw Video (.mov) | 36,797,256 | Staging copy of old Layer B test video (front) | `7a12b86be8511738...` | Old test dataset retirement |
| `Train_test_video_new/Front/4.mov` | Raw Video (.mov) | 83,172,830 | Staging copy of old Layer B test video (front) | `85215975b328cec5...` | Old test dataset retirement |
| `Train_test_video_new/Front/5.mov` | Raw Video (.mov) | 87,775,307 | Staging copy of old Layer B test video (front) | `015ec78146d47438...` | Old test dataset retirement |
| `Train_test_video_new/Front/6.mov` | Raw Video (.mov) | 149,828,230 | Staging copy of old Layer B test video (front) | `abae4c6f357171fd...` | Old test dataset retirement |
| `Train_test_video_new/Front/7.mov` | Raw Video (.mov) | 42,155,723 | Staging copy of old Layer B test video (front) | `26cc6236447deda9...` | Old test dataset retirement |
| `Train_test_video_new/Front/8.mov` | Raw Video (.mov) | 65,016,634 | Staging copy of old Layer B test video (front) | `5f0151fd09dd3563...` | Old test dataset retirement |
| `Train_test_video_new/Front/9.mov` | Raw Video (.mov) | 47,574,730 | Staging copy of old Layer B test video (front) | `7a4407f8ef68ea7e...` | Old test dataset retirement |
| `Train_test_video_new/Front/10.mov` | Raw Video (.mov) | 8,106,252 | Staging copy of old Layer B test video (front) | `feda74d909d5a888...` | Old test dataset retirement |
| `Train_test_video_new/Front/11.mov` | Raw Video (.mov) | 26,815,732 | Staging copy of old Layer B test video (front) | `9967e3666086e1f0...` | Old test dataset retirement |
| `Train_test_video_new/Front/12.mov` | Raw Video (.mov) | 42,116,210 | Staging copy of old Layer B test video (front) | `6107ebf5eb2b35da...` | Old test dataset retirement |
| `Train_test_video_new/Front/13.mov` | Raw Video (.mov) | 83,226,731 | Staging copy of old Layer B test video (front) | `840b6661622bca1d...` | Old test dataset retirement |
| `Train_test_video_new/Front/14.mov` | Raw Video (.mov) | 81,066,566 | Staging copy of old Layer B test video (front) | `3869d489098aeb5f...` | Old test dataset retirement |
| `Train_test_video_new/Front/15.mov` | Raw Video (.mov) | 60,580,154 | Staging copy of old Layer B test video (front) | `adfbf0cd5118015d...` | Old test dataset retirement |
| `Train_test_video_new/Front/16.mov` | Raw Video (.mov) | 35,028,875 | Staging copy of old Layer B test video (front) | `309203acd4bdc8dd...` | Old test dataset retirement |
| `Train_test_video_new/Front/17.mov` | Raw Video (.mov) | 51,795,611 | Staging copy of old Layer B test video (front) | `3a0d71da27ba66ae...` | Old test dataset retirement |
| `Train_test_video_new/Front/18.mov` | Raw Video (.mov) | 90,527,364 | Staging copy of old Layer B test video (front) | `188ff5ffd34d7108...` | Old test dataset retirement |
| `Train_test_video_new/Front/19.mov` | Raw Video (.mov) | 65,211,388 | Staging copy of old Layer B test video (front) | `ed376931b62de4a1...` | Old test dataset retirement |
| `Train_test_video_new/Front/20.mov` | Raw Video (.mov) | 66,718,917 | Staging copy of old Layer B test video (front) | `697f3c9ef9572e4b...` | Old test dataset retirement |
| `Train_test_video_new/Front/21.mov` | Raw Video (.mov) | 32,144,279 | Staging copy of old Layer B test video (front) | `3b45ba8f05622735...` | Old test dataset retirement |
| `Train_test_video_new/Back/1.mov` | Raw Video (.mov) | 307,285,865 | Staging copy of old Layer B test video (back) | `8cf3b1160817788f...` | Old test dataset retirement |
| `Train_test_video_new/Back/2.mov` | Raw Video (.mov) | 33,397,322 | Staging copy of old Layer B test video (back) | `964e66874e56127a...` | Old test dataset retirement |
| `Train_test_video_new/Back/3.mov` | Raw Video (.mov) | 35,822,761 | Staging copy of old Layer B test video (back) | `172d99ef4a2488ab...` | Old test dataset retirement |
| `Train_test_video_new/Back/4.mov` | Raw Video (.mov) | 86,118,013 | Staging copy of old Layer B test video (back) | `6ccfa9b6fe74adf0...` | Old test dataset retirement |
| `Train_test_video_new/Back/5.mov` | Raw Video (.mov) | 85,838,261 | Staging copy of old Layer B test video (back) | `55d7498db1449507...` | Old test dataset retirement |
| `Train_test_video_new/Back/6.mov` | Raw Video (.mov) | 139,914,925 | Staging copy of old Layer B test video (back) | `c69a3a221020378b...` | Old test dataset retirement |
| `Train_test_video_new/Back/7.mov` | Raw Video (.mov) | 37,930,769 | Staging copy of old Layer B test video (back) | `24065e2a271391c6...` | Old test dataset retirement |
| `Train_test_video_new/Back/8.mov` | Raw Video (.mov) | 68,634,610 | Staging copy of old Layer B test video (back) | `0ab126213b94d53f...` | Old test dataset retirement |
| `Train_test_video_new/Back/9.mov` | Raw Video (.mov) | 41,839,664 | Staging copy of old Layer B test video (back) | `4a0280c5421aad5e...` | Old test dataset retirement |
| `Train_test_video_new/Back/10.mov` | Raw Video (.mov) | 9,052,494 | Staging copy of old Layer B test video (back) | `f9a1beb31578cd70...` | Old test dataset retirement |
| `Train_test_video_new/Back/11.mov` | Raw Video (.mov) | 26,315,866 | Staging copy of old Layer B test video (back) | `566368738c357c2f...` | Old test dataset retirement |
| `Train_test_video_new/Back/12.mov` | Raw Video (.mov) | 41,726,426 | Staging copy of old Layer B test video (back) | `3579c9139f8a6239...` | Old test dataset retirement |
| `Train_test_video_new/Back/13.mov` | Raw Video (.mov) | 78,081,362 | Staging copy of old Layer B test video (back) | `d7cdfa047b88864d...` | Old test dataset retirement |
| `Train_test_video_new/Back/14.mov` | Raw Video (.mov) | 81,066,061 | Staging copy of old Layer B test video (back) | `e15fe819ea26440e...` | Old test dataset retirement |
| `Train_test_video_new/Back/15.mov` | Raw Video (.mov) | 59,315,994 | Staging copy of old Layer B test video (back) | `46235f16dfef70de...` | Old test dataset retirement |
| `Train_test_video_new/Back/16.mov` | Raw Video (.mov) | 24,635,515 | Staging copy of old Layer B test video (back) | `57e827d111540c3c...` | Old test dataset retirement |
| `Train_test_video_new/Back/17.mov` | Raw Video (.mov) | 49,978,515 | Staging copy of old Layer B test video (back) | `08a9f8695dfe0fd1...` | Old test dataset retirement |
| `Train_test_video_new/Back/18.mov` | Raw Video (.mov) | 92,415,591 | Staging copy of old Layer B test video (back) | `7b0d48f364c2f0a8...` | Old test dataset retirement |
| `Train_test_video_new/Back/19.mov` | Raw Video (.mov) | 57,815,481 | Staging copy of old Layer B test video (back) | `a7040a317018132f...` | Old test dataset retirement |
| `Train_test_video_new/Back/20.mov` | Raw Video (.mov) | 56,520,873 | Staging copy of old Layer B test video (back) | `f906e43305fcd183...` | Old test dataset retirement |
| `Train_test_video_new/Back/21.mov` | Raw Video (.mov) | 33,206,479 | Staging copy of old Layer B test video (back) | `ea0f90528bced198...` | Old test dataset retirement |

### 1.2 Old Raw Video Media in `data/raw/layer_b/videos/` (42 Files)

| Path | Type | Size (Bytes) | Role | SHA-256 | Reason |
|---|---|---|---|---|---|
| `data/raw/layer_b/videos/event_001/camera_front.mov` | Raw Video (.mov) | 55,307,977 | Active Layer B test video (camera_front.mov) | `d80bd6565b066edd...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_001/camera_back.mov` | Raw Video (.mov) | 307,285,865 | Active Layer B test video (camera_back.mov) | `8cf3b1160817788f...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_002/camera_front.mov` | Raw Video (.mov) | 35,947,506 | Active Layer B test video (camera_front.mov) | `69811c9e515515e9...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_002/camera_back.mov` | Raw Video (.mov) | 33,397,322 | Active Layer B test video (camera_back.mov) | `964e66874e56127a...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_003/camera_front.mov` | Raw Video (.mov) | 36,797,256 | Active Layer B test video (camera_front.mov) | `7a12b86be8511738...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_003/camera_back.mov` | Raw Video (.mov) | 35,822,761 | Active Layer B test video (camera_back.mov) | `172d99ef4a2488ab...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_004/camera_front.mov` | Raw Video (.mov) | 83,172,830 | Active Layer B test video (camera_front.mov) | `85215975b328cec5...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_004/camera_back.mov` | Raw Video (.mov) | 86,118,013 | Active Layer B test video (camera_back.mov) | `6ccfa9b6fe74adf0...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_005/camera_front.mov` | Raw Video (.mov) | 87,775,307 | Active Layer B test video (camera_front.mov) | `015ec78146d47438...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_005/camera_back.mov` | Raw Video (.mov) | 85,838,261 | Active Layer B test video (camera_back.mov) | `55d7498db1449507...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_006/camera_front.mov` | Raw Video (.mov) | 149,828,230 | Active Layer B test video (camera_front.mov) | `abae4c6f357171fd...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_006/camera_back.mov` | Raw Video (.mov) | 139,914,925 | Active Layer B test video (camera_back.mov) | `c69a3a221020378b...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_007/camera_front.mov` | Raw Video (.mov) | 42,155,723 | Active Layer B test video (camera_front.mov) | `26cc6236447deda9...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_007/camera_back.mov` | Raw Video (.mov) | 37,930,769 | Active Layer B test video (camera_back.mov) | `24065e2a271391c6...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_008/camera_front.mov` | Raw Video (.mov) | 65,016,634 | Active Layer B test video (camera_front.mov) | `5f0151fd09dd3563...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_008/camera_back.mov` | Raw Video (.mov) | 68,634,610 | Active Layer B test video (camera_back.mov) | `0ab126213b94d53f...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_009/camera_front.mov` | Raw Video (.mov) | 47,574,730 | Active Layer B test video (camera_front.mov) | `7a4407f8ef68ea7e...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_009/camera_back.mov` | Raw Video (.mov) | 41,839,664 | Active Layer B test video (camera_back.mov) | `4a0280c5421aad5e...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_010/camera_front.mov` | Raw Video (.mov) | 8,106,252 | Active Layer B test video (camera_front.mov) | `feda74d909d5a888...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_010/camera_back.mov` | Raw Video (.mov) | 9,052,494 | Active Layer B test video (camera_back.mov) | `f9a1beb31578cd70...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_011/camera_front.mov` | Raw Video (.mov) | 26,815,732 | Active Layer B test video (camera_front.mov) | `9967e3666086e1f0...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_011/camera_back.mov` | Raw Video (.mov) | 26,315,866 | Active Layer B test video (camera_back.mov) | `566368738c357c2f...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_012/camera_front.mov` | Raw Video (.mov) | 42,116,210 | Active Layer B test video (camera_front.mov) | `6107ebf5eb2b35da...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_012/camera_back.mov` | Raw Video (.mov) | 41,726,426 | Active Layer B test video (camera_back.mov) | `3579c9139f8a6239...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_013/camera_front.mov` | Raw Video (.mov) | 83,226,731 | Active Layer B test video (camera_front.mov) | `840b6661622bca1d...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_013/camera_back.mov` | Raw Video (.mov) | 78,081,362 | Active Layer B test video (camera_back.mov) | `d7cdfa047b88864d...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_014/camera_front.mov` | Raw Video (.mov) | 81,066,566 | Active Layer B test video (camera_front.mov) | `3869d489098aeb5f...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_014/camera_back.mov` | Raw Video (.mov) | 81,066,061 | Active Layer B test video (camera_back.mov) | `e15fe819ea26440e...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_015/camera_front.mov` | Raw Video (.mov) | 60,580,154 | Active Layer B test video (camera_front.mov) | `adfbf0cd5118015d...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_015/camera_back.mov` | Raw Video (.mov) | 59,315,994 | Active Layer B test video (camera_back.mov) | `46235f16dfef70de...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_016/camera_front.mov` | Raw Video (.mov) | 35,028,875 | Active Layer B test video (camera_front.mov) | `309203acd4bdc8dd...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_016/camera_back.mov` | Raw Video (.mov) | 24,635,515 | Active Layer B test video (camera_back.mov) | `57e827d111540c3c...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_017/camera_front.mov` | Raw Video (.mov) | 51,795,611 | Active Layer B test video (camera_front.mov) | `3a0d71da27ba66ae...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_017/camera_back.mov` | Raw Video (.mov) | 49,978,515 | Active Layer B test video (camera_back.mov) | `08a9f8695dfe0fd1...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_018/camera_front.mov` | Raw Video (.mov) | 90,527,364 | Active Layer B test video (camera_front.mov) | `188ff5ffd34d7108...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_018/camera_back.mov` | Raw Video (.mov) | 92,415,591 | Active Layer B test video (camera_back.mov) | `7b0d48f364c2f0a8...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_019/camera_front.mov` | Raw Video (.mov) | 65,211,388 | Active Layer B test video (camera_front.mov) | `ed376931b62de4a1...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_019/camera_back.mov` | Raw Video (.mov) | 57,815,481 | Active Layer B test video (camera_back.mov) | `a7040a317018132f...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_020/camera_front.mov` | Raw Video (.mov) | 66,718,917 | Active Layer B test video (camera_front.mov) | `697f3c9ef9572e4b...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_020/camera_back.mov` | Raw Video (.mov) | 56,520,873 | Active Layer B test video (camera_back.mov) | `f906e43305fcd183...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_021/camera_front.mov` | Raw Video (.mov) | 32,144,279 | Active Layer B test video (camera_front.mov) | `3b45ba8f05622735...` | Old test dataset retirement |
| `data/raw/layer_b/videos/event_021/camera_back.mov` | Raw Video (.mov) | 33,206,479 | Active Layer B test video (camera_back.mov) | `ea0f90528bced198...` | Old test dataset retirement |

### 1.3 Old Media Symlinks in `data/raw/layer_b/videos/` (21 Symlinks)

| Symlink Path | Target | Type | Reason |
|---|---|---|---|
| `data/raw/layer_b/videos/event_001/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_002/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_003/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_004/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_005/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_006/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_007/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_008/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_009/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_010/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_011/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_012/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_013/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_014/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_015/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_016/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_017/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_018/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_019/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_020/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |
| `data/raw/layer_b/videos/event_021/camera_rear.mov` | `camera_back.mov` | Symlink | Belongs to retired test video bundle |

### 1.4 Old Processed Audio Media in `data/processed/layer_b/audio/` (42 Files)

| Path | Type | Size (Bytes) | Role | SHA-256 | Reason |
|---|---|---|---|---|---|
| `data/processed/layer_b/audio/event_001/camera_front.wav` | Extracted Audio (.wav) | 1,595,428 | Audio extracted from old event_001 front camera | `7537e89f25a33ee6...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_001/camera_back.wav` | Extracted Audio (.wav) | 1,474,596 | Audio extracted from old event_001 back camera | `2585d211a73cb4c1...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_002/camera_front.wav` | Extracted Audio (.wav) | 1,039,736 | Audio extracted from old event_002 front camera | `148212243309188c...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_002/camera_back.wav` | Extracted Audio (.wav) | 966,692 | Audio extracted from old event_002 back camera | `05ab28de81833c2c...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_003/camera_front.wav` | Extracted Audio (.wav) | 1,067,044 | Audio extracted from old event_003 front camera | `b57be4b2c8983fbf...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_003/camera_back.wav` | Extracted Audio (.wav) | 1,041,784 | Audio extracted from old event_003 back camera | `82e311e6a2c499c5...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_004/camera_front.wav` | Extracted Audio (.wav) | 2,419,406 | Audio extracted from old event_004 front camera | `839a9e9c3b7af666...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_004/camera_back.wav` | Extracted Audio (.wav) | 2,498,596 | Audio extracted from old event_004 back camera | `6507384752cb5613...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_005/camera_front.wav` | Extracted Audio (.wav) | 2,546,382 | Audio extracted from old event_005 front camera | `0c76b852286d18fb...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_005/camera_back.wav` | Extracted Audio (.wav) | 2,499,960 | Audio extracted from old event_005 back camera | `f8577a34f103a1b9...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_006/camera_front.wav` | Extracted Audio (.wav) | 4,038,692 | Audio extracted from old event_006 front camera | `6bc883ffb298e1d8...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_006/camera_back.wav` | Extracted Audio (.wav) | 4,063,950 | Audio extracted from old event_006 back camera | `b4bc54b13f0e05fa...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_007/camera_front.wav` | Extracted Audio (.wav) | 1,224,740 | Audio extracted from old event_007 front camera | `29cdab9cbf3a3de5...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_007/camera_back.wav` | Extracted Audio (.wav) | 1,105,956 | Audio extracted from old event_007 back camera | `eaca130267665d6f...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_008/camera_front.wav` | Extracted Audio (.wav) | 1,884,196 | Audio extracted from old event_008 front camera | `662bbf299198d6e8...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_008/camera_back.wav` | Extracted Audio (.wav) | 2,007,086 | Audio extracted from old event_008 back camera | `6fb4a96508b6f969...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_009/camera_front.wav` | Extracted Audio (.wav) | 1,372,878 | Audio extracted from old event_009 front camera | `d6eeae510481a385...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_009/camera_back.wav` | Extracted Audio (.wav) | 1,203,576 | Audio extracted from old event_009 back camera | `968938360c6729c6...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_010/camera_front.wav` | Extracted Audio (.wav) | 230,094 | Audio extracted from old event_010 front camera | `d4b25ea4eb996a91...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_010/camera_back.wav` | Extracted Audio (.wav) | 249,892 | Audio extracted from old event_010 back camera | `5c5e9589b0310967...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_011/camera_front.wav` | Extracted Audio (.wav) | 768,718 | Audio extracted from old event_011 front camera | `7316c4976b9cc24b...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_011/camera_back.wav` | Extracted Audio (.wav) | 752,888 | Audio extracted from old event_011 back camera | `b612d122104b4df3...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_012/camera_front.wav` | Extracted Audio (.wav) | 1,206,308 | Audio extracted from old event_012 front camera | `83e3719a0e416071...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_012/camera_back.wav` | Extracted Audio (.wav) | 1,196,068 | Audio extracted from old event_012 back camera | `e7c1f4ada38e5442...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_013/camera_front.wav` | Extracted Audio (.wav) | 2,406,436 | Audio extracted from old event_013 front camera | `9f0706608cb219a1...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_013/camera_back.wav` | Extracted Audio (.wav) | 2,263,758 | Audio extracted from old event_013 back camera | `bcf55d512e4eb9ff...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_014/camera_front.wav` | Extracted Audio (.wav) | 2,358,648 | Audio extracted from old event_014 front camera | `6664524b97d32cdf...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_014/camera_back.wav` | Extracted Audio (.wav) | 2,344,312 | Audio extracted from old event_014 back camera | `068567f1084c3840...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_015/camera_front.wav` | Extracted Audio (.wav) | 1,761,316 | Audio extracted from old event_015 front camera | `d3168319697c0eb1...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_015/camera_back.wav` | Extracted Audio (.wav) | 1,712,846 | Audio extracted from old event_015 back camera | `16f472e431c74936...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_016/camera_front.wav` | Extracted Audio (.wav) | 997,412 | Audio extracted from old event_016 front camera | `c6044f86c00a6a8c...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_016/camera_back.wav` | Extracted Audio (.wav) | 712,056 | Audio extracted from old event_016 back camera | `b9d9a815b1f39bd3...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_017/camera_front.wav` | Extracted Audio (.wav) | 1,499,854 | Audio extracted from old event_017 front camera | `fca1a648f43f4e88...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_017/camera_back.wav` | Extracted Audio (.wav) | 1,449,336 | Audio extracted from old event_017 back camera | `8913f26c19b4a292...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_018/camera_front.wav` | Extracted Audio (.wav) | 2,613,284 | Audio extracted from old event_018 front camera | `be1c7a9030d7af19...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_018/camera_back.wav` | Extracted Audio (.wav) | 2,680,868 | Audio extracted from old event_018 back camera | `2ee51ef0ba4123d4...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_019/camera_front.wav` | Extracted Audio (.wav) | 1,886,244 | Audio extracted from old event_019 front camera | `c71c5f3c3492b2ba...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_019/camera_back.wav` | Extracted Audio (.wav) | 1,684,856 | Audio extracted from old event_019 back camera | `8bc4cb9a5cf892b5...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_020/camera_front.wav` | Extracted Audio (.wav) | 1,930,616 | Audio extracted from old event_020 front camera | `bcaab5ab196c11a6...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_020/camera_back.wav` | Extracted Audio (.wav) | 1,636,388 | Audio extracted from old event_020 back camera | `3da0730690eaa6bb...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_021/camera_front.wav` | Extracted Audio (.wav) | 914,126 | Audio extracted from old event_021 front camera | `32469ecaedb13151...` | Old test evaluation audio |
| `data/processed/layer_b/audio/event_021/camera_back.wav` | Extracted Audio (.wav) | 956,452 | Audio extracted from old event_021 back camera | `df031d2dfa5d07fd...` | Old test evaluation audio |

---

## 2. ARCHIVED METADATA & MANIFESTS (Not Deleted — Relocated for Historical Record)

The following metadata and manifest files belong to the old 21-event test dataset. To keep the active `data/raw/layer_b/videos/` clean for new data while ensuring 100% research reproducibility, these files are archived to `results/archive/old_test_dataset/` and labeled `HISTORICAL — OLD TEST DATASET — RETIRED`.

| Active Source Path | Archive Target Path | Size (Bytes) | Role |
|---|---|---|---|
| `data/manifests/layer_b_video_manifest.json` | `results/archive/old_test_dataset/manifests/layer_b_video_manifest.json` | 26,019 | Manifest of the 42 retired Layer B test videos |
| `data/manifests/layer_b_video_manifest.jsonl` | `results/archive/old_test_dataset/manifests/layer_b_video_manifest.jsonl` | 22,699 | JSONL manifest of the 42 retired Layer B test videos |
| `data/raw/layer_b/videos/event_001/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_001_metadata.json` | 356 | Metadata for event_001 |
| `data/raw/layer_b/videos/event_001/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_001_event_labels.json` | 2,137 | Reference ground truth for event_001 |
| `data/raw/layer_b/videos/event_002/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_002_metadata.json` | 356 | Metadata for event_002 |
| `data/raw/layer_b/videos/event_002/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_002_event_labels.json` | 2,137 | Reference ground truth for event_002 |
| `data/raw/layer_b/videos/event_003/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_003_metadata.json` | 356 | Metadata for event_003 |
| `data/raw/layer_b/videos/event_003/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_003_event_labels.json` | 2,137 | Reference ground truth for event_003 |
| `data/raw/layer_b/videos/event_004/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_004_metadata.json` | 356 | Metadata for event_004 |
| `data/raw/layer_b/videos/event_004/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_004_event_labels.json` | 2,137 | Reference ground truth for event_004 |
| `data/raw/layer_b/videos/event_005/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_005_metadata.json` | 356 | Metadata for event_005 |
| `data/raw/layer_b/videos/event_005/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_005_event_labels.json` | 2,137 | Reference ground truth for event_005 |
| `data/raw/layer_b/videos/event_006/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_006_metadata.json` | 356 | Metadata for event_006 |
| `data/raw/layer_b/videos/event_006/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_006_event_labels.json` | 2,137 | Reference ground truth for event_006 |
| `data/raw/layer_b/videos/event_007/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_007_metadata.json` | 356 | Metadata for event_007 |
| `data/raw/layer_b/videos/event_007/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_007_event_labels.json` | 2,137 | Reference ground truth for event_007 |
| `data/raw/layer_b/videos/event_008/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_008_metadata.json` | 356 | Metadata for event_008 |
| `data/raw/layer_b/videos/event_008/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_008_event_labels.json` | 2,137 | Reference ground truth for event_008 |
| `data/raw/layer_b/videos/event_009/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_009_metadata.json` | 356 | Metadata for event_009 |
| `data/raw/layer_b/videos/event_009/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_009_event_labels.json` | 2,137 | Reference ground truth for event_009 |
| `data/raw/layer_b/videos/event_010/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_010_metadata.json` | 356 | Metadata for event_010 |
| `data/raw/layer_b/videos/event_010/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_010_event_labels.json` | 2,137 | Reference ground truth for event_010 |
| `data/raw/layer_b/videos/event_011/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_011_metadata.json` | 356 | Metadata for event_011 |
| `data/raw/layer_b/videos/event_011/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_011_event_labels.json` | 2,137 | Reference ground truth for event_011 |
| `data/raw/layer_b/videos/event_012/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_012_metadata.json` | 356 | Metadata for event_012 |
| `data/raw/layer_b/videos/event_012/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_012_event_labels.json` | 2,137 | Reference ground truth for event_012 |
| `data/raw/layer_b/videos/event_013/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_013_metadata.json` | 356 | Metadata for event_013 |
| `data/raw/layer_b/videos/event_013/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_013_event_labels.json` | 2,137 | Reference ground truth for event_013 |
| `data/raw/layer_b/videos/event_014/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_014_metadata.json` | 356 | Metadata for event_014 |
| `data/raw/layer_b/videos/event_014/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_014_event_labels.json` | 2,137 | Reference ground truth for event_014 |
| `data/raw/layer_b/videos/event_015/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_015_metadata.json` | 356 | Metadata for event_015 |
| `data/raw/layer_b/videos/event_015/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_015_event_labels.json` | 2,137 | Reference ground truth for event_015 |
| `data/raw/layer_b/videos/event_016/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_016_metadata.json` | 356 | Metadata for event_016 |
| `data/raw/layer_b/videos/event_016/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_016_event_labels.json` | 2,137 | Reference ground truth for event_016 |
| `data/raw/layer_b/videos/event_017/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_017_metadata.json` | 356 | Metadata for event_017 |
| `data/raw/layer_b/videos/event_017/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_017_event_labels.json` | 2,137 | Reference ground truth for event_017 |
| `data/raw/layer_b/videos/event_018/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_018_metadata.json` | 356 | Metadata for event_018 |
| `data/raw/layer_b/videos/event_018/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_018_event_labels.json` | 2,137 | Reference ground truth for event_018 |
| `data/raw/layer_b/videos/event_019/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_019_metadata.json` | 356 | Metadata for event_019 |
| `data/raw/layer_b/videos/event_019/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_019_event_labels.json` | 2,137 | Reference ground truth for event_019 |
| `data/raw/layer_b/videos/event_020/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_020_metadata.json` | 356 | Metadata for event_020 |
| `data/raw/layer_b/videos/event_020/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_020_event_labels.json` | 2,137 | Reference ground truth for event_020 |
| `data/raw/layer_b/videos/event_021/metadata.json` | `results/archive/old_test_dataset/raw_layer_b_metadata/event_021_metadata.json` | 356 | Metadata for event_021 |
| `data/raw/layer_b/videos/event_021/labels/event_labels.json` | `results/archive/old_test_dataset/raw_layer_b_labels/event_021_event_labels.json` | 2,137 | Reference ground truth for event_021 |

---

## 3. KEEP LIST (Explicitly Protected Holdings — NEVER DELETE)

The following items are confirmed protected research data, model weights, code, and historical artifacts:

1. **Dataset V1 (Vision Training/Development):** `data/raw/vision/v1/` (6,321 images/labels in `baler.v1i.yolov8`). Status: UNTOUCHED.
2. **Standalone Train-Horn Audio Dataset:**
   - `data/raw/audio/train_horn/positive/` (87 recordings + 4 pdfs, train horn development)
   - `data/raw/audio/train_horn/negative/` (negative acoustic development)
   - `data/processed/audio/standardized_wav/` (standardized 16kHz audio)
   - `data/processed/audio/train_horn/` (windowed features)
   - `data/processed/audio/features/` (log-Mel spectrogram feature arrays)
3. **Staging Audio Data:** `Train_Audio_new/` (87 recordings matching positive train horn dataset). Status: PRESERVED.
4. **Trained Vision Model Checkpoint:** `experiments/vision/39f402dfe460/checkpoints/weights/best.pt` (24,493,159 bytes). Status: UNTOUCHED.
5. **Trained Audio Model Checkpoint:** `models/audio/best_checkpoint.pt` (334,839 bytes). Status: UNTOUCHED.
6. **Base Weights:** `yolov8n.pt` (6,549,796 bytes). Status: UNTOUCHED.
7. **Source Code:** `src/railway_detection/` (all modules). Status: UNTOUCHED.
8. **Test Suites:** `tests/` (unit, integration, smoke, fixtures). Status: UNTOUCHED.
9. **Configuration Files:** `configs/` (`vision.yaml`, `audio.yaml`, `fusion.yaml`, `simulation.yaml`). Status: UNTOUCHED.
10. **Scripts:** `scripts/` (all utility, evaluation, and reporting scripts). Status: UNTOUCHED.
11. **Negative Audio Corpus:** `ESC-50-master/` (2,000 environmental recordings). Status: UNTOUCHED.
12. **Historical Experiment Benchmark Results:** `results/experiments/` (B0–B7 summaries, single_events.json, timelines, metrics, figures, detection cache). Status: UNTOUCHED.
13. **Research Documentation & Reports:** `docs/`, `Railway_Crossing_Automation_Research_Report.docx`, `README.md`. Status: PRESERVED.

---

## 4. UNCERTAIN LIST (Ambiguous Candidates — Explicitly NOT Deleted)

Per the Absolute Safety Rule, any media file not strictly confirmed as part of the Layer B 21-event evaluation dataset is classified as UNCERTAIN and preserved:

| Path | Type | Size (Bytes) | Analysis / Classification Reason | Decision |
|---|---|---|---|---|
| `Unseen_Video/Screen Recording 2026-08-18 at 17.01.28.mov` | Mov Video | 20,208,846 | Standalone visual demo recording referenced in `scripts/demo_video.py` | **DO NOT DELETE (KEEP)** |
| `Unseen_Video/Screen Recording 2026-08-18 at 17.02.41.mov` | Mov Video | 5,663,231 | Standalone visual demo recording | **DO NOT DELETE (KEEP)** |
| `Unseen_Video/Screen Recording 2026-08-18 at 17.03.46.mov` | Mov Video | 6,717,991 | Standalone visual demo recording | **DO NOT DELETE (KEEP)** |
| `Unseen_Video/Screen Recording 2026-08-18 at 17.06.42.mov` | Mov Video | 11,596,337 | Standalone visual demo recording | **DO NOT DELETE (KEEP)** |
| `Unseen_Video/Screen Recording 2026-08-18 at 17.22.05.mov` | Mov Video | 61,070,022 | Standalone visual demo recording | **DO NOT DELETE (KEEP)** |
| `outputs/temp_uploads/Screen_Recording_2026-08-18_at_17.01.28_1787087394.mov` | Mov Video | 20,208,846 | Temporary upload copy of demo video | **DO NOT DELETE (KEEP)** |
| `outputs/temp_uploads/Screen_Recording_2026-08-18_at_17.03.46_1787087541.mov` | Mov Video | 6,717,991 | Temporary upload copy of demo video | **DO NOT DELETE (KEEP)** |
| `outputs/temp_uploads/Screen_Recording_2026-08-18_at_17.06.42_1787087306.mov` | Mov Video | 11,596,337 | Temporary upload copy of demo video | **DO NOT DELETE (KEEP)** |
| `outputs/temp_uploads/Screen_Recording_2026-08-18_at_17.22.05_1787088247.mov` | Mov Video | 61,070,022 | Temporary upload copy of demo video | **DO NOT DELETE (KEEP)** |

