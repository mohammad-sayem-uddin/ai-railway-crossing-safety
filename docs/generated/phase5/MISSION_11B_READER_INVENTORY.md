# Mission 11B — Complete Static Reader Inventory

> **MISSION 12 CORRECTION NOTICE (2026-11-02):** The previously identified unguarded PIL/OpenCV readers were remediated at operation boundaries. See `MISSION_12_MEDIA_READER_COVERAGE.md` for the post-remediation inventory and limitations.

Source-only inventory. No media, checkpoints, caches or protected processed data were opened or hashed. Guard evidence is based on source inspection; `YES` means the file contains a media guard reference, not that every operation in the file is necessarily guarded.

| Operation/API | Module | Line | Source expression | Guard reference in module | Lowest-level interpretation |
|---|---|---:|---|---|---|
| builtins.open | `src/railway_detection/annotation/adjudication_session.py` | 148 | `with path.open("rb") as stream:` | YES | byte/file read |
| Path.open | `src/railway_detection/annotation/adjudication_session.py` | 148 | `with path.open("rb") as stream:` | YES | byte/file read |
| FFmpeg/FFprobe | `src/railway_detection/annotation/adjudication_session.py` | 210 | `inspection_tool: str = "ffmpeg"` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/annotation/adjudication_session.py` | 708 | `inspection_tool: str = "ffmpeg",` | YES | media operation boundary |
| builtins.open | `src/railway_detection/annotation/batch_multimodal_annotator.py` | 78 | `with open(self.inventory_path) as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/annotation/batch_multimodal_annotator.py` | 80 | `with open(self.audio_audit_path) as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/annotation/batch_multimodal_annotator.py` | 82 | `with open(self.motion_audit_path) as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/annotation/batch_multimodal_annotator.py` | 84 | `with open(self.candidates_path) as f:` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/batch_multimodal_annotator.py` | 91 | `raw_bytes = PROMPT_TEMPLATE_PATH.read_bytes()` | NO/NOT IN FILE | byte/file read |
| FFmpeg/FFprobe | `src/railway_detection/annotation/batch_multimodal_annotator.py` | 688 | `lines.append(f"ffmpeg -ss {v.value_s:.3f} -i {v_path} -frames:v 1 -q:v 2 preview_{ev_id}_{k}.jpg")` | NO/NOT IN FILE | media operation boundary |
| Path.read_bytes | `src/railway_detection/annotation/candidate_split_queue.py` | 81 | `return _sha256_bytes(path.read_bytes())` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/candidate_split_queue.py` | 94 | `raw = path.read_bytes()` | YES | byte/file read |
| Path.read_text | `src/railway_detection/annotation/evaluation_readiness_gate.py` | 159 | `value = json.loads(path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/annotation/gemini_annotator.py` | 466 | `with open(target_file, "w", encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/gemini_annotator.py` | 59 | `template_bytes = PROMPT_TEMPLATE_PATH.read_bytes()` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/annotation/invalidation_notice_writer.py` | 341 | `fd = os.open(str(path), os.O_WRONLY \| os.O_CREAT \| os.O_EXCL, 0o644)` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/annotation/invalidation_notice_writer.py` | 556 | ``.exists()` check as by a lost `os.open()` race, confirmed empirically` | NO/NOT IN FILE | byte/file read |
| Path.open | `src/railway_detection/annotation/invalidation_notice_writer.py` | 341 | `fd = os.open(str(path), os.O_WRONLY \| os.O_CREAT \| os.O_EXCL, 0o644)` | NO/NOT IN FILE | byte/file read |
| Path.open | `src/railway_detection/annotation/invalidation_notice_writer.py` | 556 | ``.exists()` check as by a lost `os.open()` race, confirmed empirically` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/invalidation_notice_writer.py` | 289 | `return hashlib.sha256(proposal_path.read_bytes()).hexdigest()` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/invalidation_notice_writer.py` | 323 | `raw_bytes = proposal_path.read_bytes()` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/invalidation_notice_writer.py` | 396 | `actual_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/invalidation_notice_writer.py` | 505 | `actual_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/annotation/invalidation_notice_writer.py` | 409 | `existing = output_path.read_text(encoding="utf-8")` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/annotation/invalidation_notice_writer.py` | 471 | `existing = dir_notice_path.read_text(encoding="utf-8")` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/annotation/invalidation_notice_writer.py` | 580 | `existing_text = output_path.read_text(encoding="utf-8")` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/leg_exec.py` | 159 | `record = json.loads(path.read_bytes())` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/legacy_reconciliation.py` | 56 | `return hashlib.sha256(path.read_bytes()).hexdigest()` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/legacy_reconciliation.py` | 85 | `raw = path.read_bytes()` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/annotation/media_inspector.py` | 78 | `with open(path, "rb") as f:` | YES | byte/file read |
| FFmpeg/FFprobe | `src/railway_detection/annotation/media_inspector.py` | 4 | `SHA-256 hashes using ffprobe and standard hashlib.` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/annotation/media_inspector.py` | 85 | `def is_ffprobe_available() -> bool:` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/annotation/media_inspector.py` | 86 | `return shutil.which("ffprobe") is not None` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/annotation/media_inspector.py` | 89 | `def is_ffmpeg_available() -> bool:` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/annotation/media_inspector.py` | 90 | `return shutil.which("ffmpeg") is not None` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/annotation/media_inspector.py` | 94 | `"""Inspect a single media file using ffprobe and hashlib."""` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/annotation/media_inspector.py` | 103 | `if not is_ffprobe_available():` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/annotation/media_inspector.py` | 104 | `raise RuntimeError("ffprobe is required for media inspection but not found in PATH")` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/annotation/media_inspector.py` | 107 | `"ffprobe",` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/annotation/media_inspector.py` | 119 | `raise RuntimeError(f"ffprobe failed on {path}: {proc.stderr[:200]}")` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/annotation/media_inspector.py` | 183 | `"""Extract a single JPEG frame at a precise timestamp using ffmpeg."""` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/annotation/media_inspector.py` | 185 | `if not is_ffmpeg_available():` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/annotation/media_inspector.py` | 186 | `logger.warning("ffmpeg unavailable; cannot extract frame")` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/annotation/media_inspector.py` | 193 | `"ffmpeg",` | YES | media operation boundary |
| subprocess | `src/railway_detection/annotation/media_inspector.py` | 117 | `proc = subprocess.run(cmd, capture_output=True, text=True, check=False)` | YES | child process boundary |
| subprocess | `src/railway_detection/annotation/media_inspector.py` | 205 | `proc = subprocess.run(cmd, capture_output=True, text=True, check=False)` | YES | child process boundary |
| Path.read_bytes | `src/railway_detection/annotation/notices.py` | 53 | `notice = json.loads(notice_path.read_bytes())` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/notices.py` | 65 | `raw = record_path.read_bytes()` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/promotion_gate.py` | 230 | `"front": hashlib.sha256(front_path.read_bytes()).hexdigest(),` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/promotion_gate.py` | 231 | `"back": hashlib.sha256(back_path.read_bytes()).hexdigest(),` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/promotion_gate.py` | 623 | `content = affected_record_path.read_bytes()` | YES | byte/file read |
| Path.read_text | `src/railway_detection/annotation/promotion_gate.py` | 84 | `raw = allowlist_path.read_text(encoding="utf-8")` | YES | byte/file read |
| Path.read_text | `src/railway_detection/annotation/promotion_gate.py` | 643 | `existing = json.loads(output_path.read_text()).get("disposition_events", [])` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/readiness_audit.py` | 130 | `record = json.loads(path.read_bytes())` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/annotation/readiness_cli.py` | 62 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.open | `src/railway_detection/annotation/readiness_cli.py` | 62 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.read_text | `src/railway_detection/annotation/readiness_cli.py` | 83 | `raw = json.loads(inventory_path.read_text(encoding="utf-8"))` | YES | byte/file read |
| builtins.open | `src/railway_detection/annotation/receipt.py` | 36 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.open | `src/railway_detection/annotation/receipt.py` | 36 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.read_text | `src/railway_detection/annotation/review_queue_validator.py` | 107 | `value = json.loads(path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/annotation/review_queue_validator.py` | 228 | `review_value = json.loads(review_path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| FFmpeg/FFprobe | `src/railway_detection/annotation/review_reporter.py` | 98 | `f"ffmpeg -ss {v.value_s:.3f} -i {vid_path} -frames:v 1 -q:v 2 preview_{proposal.event_id}_{k}.jpg"` | NO/NOT IN FILE | media operation boundary |
| Path.read_bytes | `src/railway_detection/annotation/second_review.py` | 134 | `raw = path.read_bytes()` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/annotation/stage21_timing_pilot.py` | 950 | `with path.open("rb") as stream:` | YES | byte/file read |
| builtins.open | `src/railway_detection/annotation/stage21_timing_pilot.py` | 1588 | `with temporary.open("wb") as stream:` | YES | byte/file read |
| Path.open | `src/railway_detection/annotation/stage21_timing_pilot.py` | 950 | `with path.open("rb") as stream:` | YES | byte/file read |
| Path.open | `src/railway_detection/annotation/stage21_timing_pilot.py` | 1588 | `with temporary.open("wb") as stream:` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/stage21_timing_pilot.py` | 265 | `raw = path.read_bytes()` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/stage21_timing_pilot.py` | 333 | `if _sha256_bytes(file_path.read_bytes()) != digest:` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/stage21_timing_pilot.py` | 680 | `inventory_raw = inventory_path.read_bytes()` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/stage21_timing_pilot.py` | 729 | `proposal_hash = _sha256_bytes(proposal_path.read_bytes())` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/stage21_timing_pilot.py` | 1389 | `existing = destination.read_bytes()` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/stage21_timing_pilot.py` | 1415 | `if destination.is_file() and destination.read_bytes() == desired:` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/annotation/stage21_timing_pilot.py` | 1532 | `release_hash = _sha256_bytes(manifest_path.read_bytes())` | YES | byte/file read |
| Path.read_text | `src/railway_detection/annotation/stage21_timing_pilot.py` | 183 | `payload = json.loads(path.read_text(encoding="utf-8"))` | YES | byte/file read |
| Path.read_text | `src/railway_detection/annotation/stage21_timing_pilot.py` | 682 | `queue = json.loads(queue_path.read_text(encoding="utf-8"))` | YES | byte/file read |
| builtins.open | `src/railway_detection/audio/dataset.py` | 64 | `with open(self.manifest_path, encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| NumPy load | `src/railway_detection/audio/dataset.py` | 114 | `return np.load(feat_path)` | NO/NOT IN FILE | byte/file read |
| Torch load | `src/railway_detection/audio/model.py` | 204 | `state = torch.load(ckpt_path, map_location=self.device, weights_only=True)` | NO/NOT IN FILE | byte/file read |
| Torch load | `src/railway_detection/audio/model.py` | 206 | `state = torch.load(ckpt_path, map_location=self.device, weights_only=False)` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/audio/preprocessor.py` | 50 | `with wave.open(str(path), "rb") as wav:` | YES | byte/file read |
| Path.open | `src/railway_detection/audio/preprocessor.py` | 50 | `with wave.open(str(path), "rb") as wav:` | YES | byte/file read |
| Path.read_text | `src/railway_detection/audio/training.py` | 83 | `data = json.loads(p.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/cli/main.py` | 430 | `split_summary = json.loads(summary_path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/cli/main.py` | 542 | `data = json.loads(metadata_path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/cli/main.py` | 584 | `text = path.read_text(encoding="utf-8")` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/config/loader.py` | 212 | `data = yaml.safe_load(resolved.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| FFmpeg/FFprobe | `src/railway_detection/data/audio_extractor.py` | 1 | `"""Audio extraction utility to isolate WAV streams from video recordings via ffmpeg."""` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/data/audio_extractor.py` | 20 | `"""Extracts an audio track from a video container to a PCM WAV file using ffmpeg.` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/data/audio_extractor.py` | 42 | `"ffmpeg",` | YES | media operation boundary |
| FFmpeg/FFprobe | `src/railway_detection/data/audio_extractor.py` | 62 | `"ffmpeg failed to extract audio from %s: %s",` | YES | media operation boundary |
| subprocess | `src/railway_detection/data/audio_extractor.py` | 59 | `res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)` | YES | child process boundary |
| Path.read_text | `src/railway_detection/data/layer_b.py` | 161 | `data = json.loads(path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| FFmpeg/FFprobe | `src/railway_detection/data/layer_b.py` | 78 | `to extract audio track from camera_1 or camera_front using ffmpeg.` | NO/NOT IN FILE | media operation boundary |
| builtins.open | `src/railway_detection/data/manifest.py` | 152 | `with Image.open(image_path) as img:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/data/manifest.py` | 251 | `with manifest_path.open("w", encoding="utf-8") as handle:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/data/manifest.py` | 267 | `with Path(manifest_path).open(encoding="utf-8") as handle:` | NO/NOT IN FILE | byte/file read |
| Path.open | `src/railway_detection/data/manifest.py` | 152 | `with Image.open(image_path) as img:` | NO/NOT IN FILE | byte/file read |
| Path.open | `src/railway_detection/data/manifest.py` | 251 | `with manifest_path.open("w", encoding="utf-8") as handle:` | NO/NOT IN FILE | byte/file read |
| Path.open | `src/railway_detection/data/manifest.py` | 267 | `with Path(manifest_path).open(encoding="utf-8") as handle:` | NO/NOT IN FILE | byte/file read |
| PIL | `src/railway_detection/data/manifest.py` | 20 | `from PIL import Image` | NO/NOT IN FILE | media operation boundary |
| PIL | `src/railway_detection/data/manifest.py` | 152 | `with Image.open(image_path) as img:` | NO/NOT IN FILE | media operation boundary |
| builtins.open | `src/railway_detection/data/r04_evidence.py` | 43 | `with path.open("rb") as stream:` | YES | byte/file read |
| Path.open | `src/railway_detection/data/r04_evidence.py` | 43 | `with path.open("rb") as stream:` | YES | byte/file read |
| Path.read_text | `src/railway_detection/data/r04_evidence.py` | 50 | `return json.loads(path.read_text(encoding="utf-8"))` | YES | byte/file read |
| Path.read_text | `src/railway_detection/data/r04_evidence.py` | 143 | `sync_manifest = yaml.safe_load(sync_manifest_path.read_text(encoding="utf-8")) or {}` | YES | byte/file read |
| builtins.open | `src/railway_detection/data/sync_calibration.py` | 456 | `with open(path, "rb") as f:` | YES | byte/file read |
| builtins.open | `src/railway_detection/data/sync_calibration.py` | 503 | `with open(manifest_file, encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `src/railway_detection/data/validator.py` | 192 | `with Image.open(path) as img:` | YES | byte/file read |
| builtins.open | `src/railway_detection/data/validator.py` | 201 | `with Image.open(path) as img:` | YES | byte/file read |
| builtins.open | `src/railway_detection/data/validator.py` | 210 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.open | `src/railway_detection/data/validator.py` | 192 | `with Image.open(path) as img:` | YES | byte/file read |
| Path.open | `src/railway_detection/data/validator.py` | 201 | `with Image.open(path) as img:` | YES | byte/file read |
| Path.open | `src/railway_detection/data/validator.py` | 210 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.read_text | `src/railway_detection/data/validator.py` | 236 | `lines = path.read_text(encoding="utf-8").splitlines()` | YES | byte/file read |
| Path.read_text | `src/railway_detection/data/validator.py` | 285 | `lines = path.read_text(encoding="utf-8").splitlines()` | YES | byte/file read |
| PIL | `src/railway_detection/data/validator.py` | 12 | `from PIL import Image` | YES | media operation boundary |
| PIL | `src/railway_detection/data/validator.py` | 192 | `with Image.open(path) as img:` | YES | media operation boundary |
| PIL | `src/railway_detection/data/validator.py` | 201 | `with Image.open(path) as img:` | YES | media operation boundary |
| builtins.open | `src/railway_detection/demo/server.py` | 318 | `with open(dest_path, "wb") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/demo/server.py` | 565 | `with open(full_path, "rb") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/demo/server.py` | 577 | `with open(full_path, "rb") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/demo/server.py` | 593 | `with open(full_path, "rb") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/demo/server.py` | 637 | `threading.Timer(0.8, lambda: webbrowser.open(url)).start()` | NO/NOT IN FILE | byte/file read |
| Path.open | `src/railway_detection/demo/server.py` | 637 | `threading.Timer(0.8, lambda: webbrowser.open(url)).start()` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/demo/server.py` | 230 | `metrics_data = json.loads(metrics_json_path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/demo/server.py` | 236 | `failure_data = json.loads(failure_json_path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/demo/server.py` | 268 | `sum_data = json.loads(summary_file.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| cv2.VideoCapture | `src/railway_detection/demo/video_demo.py` | 432 | `cap = cv2.VideoCapture(str(input_path.resolve()))` | YES | media operation boundary |
| subprocess | `src/railway_detection/demo/video_demo.py` | 310 | `proc = subprocess.run(` | YES | child process boundary |
| builtins.open | `src/railway_detection/evaluation/cache_only_engine.py` | 444 | `fd = os.open(file_path, os.O_RDONLY \| getattr(os, "O_NOFOLLOW", 0))` | NO/NOT IN FILE | byte/file read |
| Path.open | `src/railway_detection/evaluation/cache_only_engine.py` | 444 | `fd = os.open(file_path, os.O_RDONLY \| getattr(os, "O_NOFOLLOW", 0))` | NO/NOT IN FILE | byte/file read |
| FFmpeg/FFprobe | `src/railway_detection/evaluation/cache_only_engine.py` | 8 | `- ``INV-CACHE-1`` (Zero Fallback): no references to cv2, av, ffmpeg.` | NO/NOT IN FILE | media operation boundary |
| Path.read_bytes | `src/railway_detection/evaluation/descriptive_exec_gate.py` | 147 | `payload = json.loads(path.read_bytes())` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/evaluation/execution_gate.py` | 536 | `raw = path.read_bytes()` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/evaluation/execution_gate.py` | 489 | `value = json.loads(path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/evaluation/execution_gate.py` | 616 | `raw = json.loads(inventory_path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/evaluation/execution_gate.py` | 874 | `policy = yaml.safe_load(policy_file.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/evaluation/experiment_engine.py` | 189 | `with temporary.open("wb") as handle:` | YES | byte/file read |
| builtins.open | `src/railway_detection/evaluation/experiment_engine.py` | 201 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.open | `src/railway_detection/evaluation/experiment_engine.py` | 189 | `with temporary.open("wb") as handle:` | YES | byte/file read |
| Path.open | `src/railway_detection/evaluation/experiment_engine.py` | 201 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.read_text | `src/railway_detection/evaluation/experiment_engine.py` | 351 | `prior_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))` | YES | byte/file read |
| Path.read_text | `src/railway_detection/evaluation/experiment_engine.py` | 352 | `checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/evaluation/governance.py` | 103 | `return sha256_bytes(path.read_bytes())` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/evaluation/governance.py` | 122 | `raw = path.read_bytes()` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/evaluation/governance.py` | 222 | `value = yaml.safe_load(path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/evaluation/ground_truth_loader.py` | 238 | `raw = path.read_bytes()` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/evaluation/input_contracts.py` | 74 | `with os.fdopen(os.open(path, flags), "rb") as handle:` | YES | byte/file read |
| builtins.open | `src/railway_detection/evaluation/input_contracts.py` | 88 | `with os.fdopen(os.open(path, flags), "rb") as handle:` | YES | byte/file read |
| Path.open | `src/railway_detection/evaluation/input_contracts.py` | 74 | `with os.fdopen(os.open(path, flags), "rb") as handle:` | YES | byte/file read |
| Path.open | `src/railway_detection/evaluation/input_contracts.py` | 88 | `with os.fdopen(os.open(path, flags), "rb") as handle:` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/evaluation/input_contracts.py` | 111 | `raw_bytes = path.read_bytes()` | YES | byte/file read |
| Path.read_text | `src/railway_detection/experiments/cache_provenance.py` | 1147 | `for line in cache_path.read_text(encoding="utf-8").splitlines()` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/experiments/cache_provenance.py` | 1238 | `for line in cache_path.read_text(encoding="utf-8").splitlines()` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/experiments/frozen_config.py` | 190 | `with open(p, "rb") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/experiments/frozen_config.py` | 351 | `with open(path, "r", encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/experiments/layer_b_processor.py` | 380 | `with open(cache_file, "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `src/railway_detection/experiments/layer_b_processor.py` | 481 | `with open(cache_file, "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `src/railway_detection/experiments/leakage_guard.py` | 65 | `with open(path, "rb") as f:` | YES | byte/file read |
| builtins.open | `src/railway_detection/experiments/leakage_guard.py` | 126 | `with open(audio_train_manifest, "r", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `src/railway_detection/experiments/timeline_generator.py` | 102 | `with open(out, "w", newline="", encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/field_validation/capture_session.py` | 287 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.open | `src/railway_detection/field_validation/capture_session.py` | 287 | `with path.open("rb") as handle:` | YES | byte/file read |
| builtins.open | `src/railway_detection/field_validation/capture_session_v2.py` | 731 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.open | `src/railway_detection/field_validation/capture_session_v2.py` | 731 | `with path.open("rb") as handle:` | YES | byte/file read |
| subprocess | `src/railway_detection/field_validation/capture_session_v2.py` | 701 | `out = subprocess.run(` | YES | child process boundary |
| builtins.open | `src/railway_detection/optimization/benchmark_suite.py` | 165 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.open | `src/railway_detection/optimization/benchmark_suite.py` | 165 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.read_text | `src/railway_detection/optimization/benchmark_suite.py` | 91 | `for line in Path("/proc/cpuinfo").read_text().splitlines():` | YES | byte/file read |
| Path.read_text | `src/railway_detection/optimization/benchmark_suite.py` | 186 | `policy = yaml.safe_load(policy_file.read_text(encoding="utf-8"))` | YES | byte/file read |
| subprocess | `src/railway_detection/optimization/benchmark_suite.py` | 79 | `out = subprocess.run(` | YES | child process boundary |
| subprocess | `src/railway_detection/optimization/benchmark_suite.py` | 127 | `out = subprocess.run(` | YES | child process boundary |
| Path.read_text | `src/railway_detection/reproducibility/audit.py` | 213 | `return path.read_text(encoding="utf-8", errors="replace")` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/reproducibility/audit.py` | 222 | `values \|= _extract_floats(path.read_text(encoding="utf-8", errors="replace"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/reproducibility/audit.py` | 258 | `raw = json.loads(path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/reproducibility/audit.py` | 282 | `for line in lock.read_text().splitlines()` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/reproducibility/audit.py` | 336 | `manifest = json.loads(manifest_path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/reproducibility/audit.py` | 472 | `data = json.loads(path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/safety/access_guard_plugin.py` | 130 | `self._log = log_path.open("a", encoding="utf-8")` | NO/NOT IN FILE | byte/file read |
| Path.open | `src/railway_detection/safety/access_guard_plugin.py` | 130 | `self._log = log_path.open("a", encoding="utf-8")` | NO/NOT IN FILE | byte/file read |
| cv2.VideoCapture | `src/railway_detection/safety/access_guard_plugin.py` | 19 | ```cv2.VideoCapture``. NOT covered (disclosed limitation): native code that opens files itself` | NO/NOT IN FILE | media operation boundary |
| cv2.VideoCapture | `src/railway_detection/safety/access_guard_plugin.py` | 253 | `real_capture = cv2.VideoCapture` | NO/NOT IN FILE | media operation boundary |
| cv2.VideoCapture | `src/railway_detection/safety/access_guard_plugin.py` | 257 | `guard.check_read(source, "cv2.VideoCapture")` | NO/NOT IN FILE | media operation boundary |
| cv2.VideoCapture | `src/railway_detection/safety/access_guard_plugin.py` | 260 | `self._originals["cv2.VideoCapture"] = real_capture` | NO/NOT IN FILE | media operation boundary |
| cv2.VideoCapture | `src/railway_detection/safety/access_guard_plugin.py` | 261 | `cv2.VideoCapture = guarded_capture` | NO/NOT IN FILE | media operation boundary |
| cv2.VideoCapture | `src/railway_detection/safety/access_guard_plugin.py` | 275 | `if "cv2.VideoCapture" in o:` | NO/NOT IN FILE | media operation boundary |
| cv2.VideoCapture | `src/railway_detection/safety/access_guard_plugin.py` | 278 | `cv2.VideoCapture = o["cv2.VideoCapture"]` | NO/NOT IN FILE | media operation boundary |
| subprocess | `src/railway_detection/safety/access_guard_plugin.py` | 18 | ```subprocess.Popen`` path arguments (relative ones resolved against the working directory) and` | NO/NOT IN FILE | child process boundary |
| subprocess | `src/railway_detection/safety/access_guard_plugin.py` | 186 | `real_popen_init = subprocess.Popen.__init__` | NO/NOT IN FILE | child process boundary |
| subprocess | `src/railway_detection/safety/access_guard_plugin.py` | 249 | `subprocess.Popen.__init__ = guarded_popen_init  # type: ignore[method-assign]` | NO/NOT IN FILE | child process boundary |
| subprocess | `src/railway_detection/safety/access_guard_plugin.py` | 274 | `subprocess.Popen.__init__ = o["popen"]  # type: ignore[method-assign]` | NO/NOT IN FILE | child process boundary |
| Path.read_bytes | `src/railway_detection/safety/access_manifest.py` | 78 | `return hashlib.sha256(path.read_bytes()).hexdigest()` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `src/railway_detection/safety/access_manifest.py` | 89 | `data = yaml.safe_load(path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/safety/media_guard.py` | 244 | `payload = json.loads(path.read_bytes())` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/safety/media_guard.py` | 422 | `if hashlib.sha256(doc_path.read_bytes()).hexdigest() != doc["sha256"]:` | YES | byte/file read |
| Path.read_bytes | `src/railway_detection/simulation/runner.py` | 338 | `"simulation_runner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/simulation/runner.py` | 339 | `"stage_profiler": hashlib.sha256(profiler_path.read_bytes()).hexdigest(),` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `src/railway_detection/simulation/runner.py` | 346 | `"runner_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),` | NO/NOT IN FILE | byte/file read |
| builtins.open | `src/railway_detection/utils/reproducibility.py` | 86 | `with registry_path.open("a", encoding="utf-8") as handle:` | NO/NOT IN FILE | byte/file read |
| Path.open | `src/railway_detection/utils/reproducibility.py` | 86 | `with registry_path.open("a", encoding="utf-8") as handle:` | NO/NOT IN FILE | byte/file read |
| subprocess | `src/railway_detection/utils/reproducibility.py` | 22 | `result = subprocess.run(` | NO/NOT IN FILE | child process boundary |
| cv2.VideoCapture | `src/railway_detection/vision/video.py` | 93 | `capture = cv2.VideoCapture(str(path))` | YES | media operation boundary |
| builtins.open | `src/railway_detection/vision/yolo_adapter.py` | 197 | `with manifest_path.open(encoding="utf-8") as handle:` | NO/NOT IN FILE | byte/file read |
| Path.open | `src/railway_detection/vision/yolo_adapter.py` | 197 | `with manifest_path.open(encoding="utf-8") as handle:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/analyze_audit.py` | 12 | `with open(AUDIT_FILE) as f:` | NO/NOT IN FILE | byte/file read |
| FFmpeg/FFprobe | `scripts/analyze_audit.py` | 27 | `print("None! All media probed successfully by ffprobe.")` | NO/NOT IN FILE | media operation boundary |
| builtins.open | `scripts/audit_train_video_audio_2.py` | 18 | `with open(filepath, "rb") as f:` | YES | byte/file read |
| builtins.open | `scripts/audit_train_video_audio_2.py` | 129 | `with open(out_file, "w") as f:` | YES | byte/file read |
| FFmpeg/FFprobe | `scripts/audit_train_video_audio_2.py` | 26 | `"ffprobe",` | YES | media operation boundary |
| subprocess | `scripts/audit_train_video_audio_2.py` | 33 | `res = subprocess.run(cmd, capture_output=True, text=True, check=True)` | YES | child process boundary |
| builtins.open | `scripts/build_audio_training_pipeline.py` | 40 | `with open(path, "rb") as f:` | YES | byte/file read |
| builtins.open | `scripts/build_audio_training_pipeline.py` | 91 | `with wave.open(str(dst_path), "rb") as wav:` | YES | byte/file read |
| builtins.open | `scripts/build_audio_training_pipeline.py` | 103 | `with wave.open(str(dst_path), "wb") as wav:` | YES | byte/file read |
| builtins.open | `scripts/build_audio_training_pipeline.py` | 113 | `with wave.open(str(path), "rb") as wav:` | YES | byte/file read |
| builtins.open | `scripts/build_audio_training_pipeline.py` | 181 | `with open(manifest_dir / "negative_selection_manifest.json") as f:` | YES | byte/file read |
| builtins.open | `scripts/build_audio_training_pipeline.py` | 311 | `with open(split_dir / "dataset_split.json", "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/build_audio_training_pipeline.py` | 406 | `with open(manifest_json, "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/build_audio_training_pipeline.py` | 408 | `with open(manifest_jsonl, "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/build_audio_training_pipeline.py` | 459 | `with open(summary_file, "w", encoding="utf-8") as f:` | YES | byte/file read |
| Path.open | `scripts/build_audio_training_pipeline.py` | 91 | `with wave.open(str(dst_path), "rb") as wav:` | YES | byte/file read |
| Path.open | `scripts/build_audio_training_pipeline.py` | 103 | `with wave.open(str(dst_path), "wb") as wav:` | YES | byte/file read |
| Path.open | `scripts/build_audio_training_pipeline.py` | 113 | `with wave.open(str(path), "rb") as wav:` | YES | byte/file read |
| FFmpeg/FFprobe | `scripts/build_audio_training_pipeline.py` | 49 | `"ffprobe",` | YES | media operation boundary |
| FFmpeg/FFprobe | `scripts/build_audio_training_pipeline.py` | 72 | `# Step 1: ffmpeg conversion to mono 16k WAV` | YES | media operation boundary |
| FFmpeg/FFprobe | `scripts/build_audio_training_pipeline.py` | 75 | `"ffmpeg",` | YES | media operation boundary |
| subprocess | `scripts/build_audio_training_pipeline.py` | 56 | `res = subprocess.run(cmd, capture_output=True, text=True, check=True)` | YES | child process boundary |
| subprocess | `scripts/build_audio_training_pipeline.py` | 84 | `res = subprocess.run(cmd, capture_output=True, text=True)` | YES | child process boundary |
| builtins.open | `scripts/build_camera_sync_candidate_manifest.py` | 45 | `with open(path, "rb") as f:` | YES | byte/file read |
| builtins.open | `scripts/build_camera_sync_candidate_manifest.py` | 213 | `with open(out_path, "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/build_camera_sync_candidate_manifest.py` | 218 | `with open(out_verdicts_path, "w", encoding="utf-8") as f:` | YES | byte/file read |
| Path.read_text | `scripts/build_camera_sync_candidate_manifest.py` | 65 | `diag = json.loads((R04_DIR / "gcc_phat_raw_results.json").read_text())` | YES | byte/file read |
| Path.read_text | `scripts/build_camera_sync_candidate_manifest.py` | 66 | `qt = json.loads((R04_DIR / "quicktime_creationdate_deltas.json").read_text())` | YES | byte/file read |
| Path.read_text | `scripts/build_camera_sync_candidate_manifest.py` | 72 | `old_manifest = yaml.safe_load(candidate_manifest_path.read_text(encoding="utf-8")) or {}` | YES | byte/file read |
| Path.read_text | `scripts/build_camera_sync_candidate_manifest.py` | 105 | `rec_data = json.loads(review_record_path.read_text(encoding="utf-8"))` | YES | byte/file read |
| Path.read_text | `scripts/build_candidate_split_and_review_queue.py` | 51 | `inventory = json.loads(inventory_path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/classify_test_access.py` | 79 | `tree = ast.parse(path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/classify_test_access.py` | 144 | `events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line]` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/classify_test_access.py` | 213 | `and "access_guard_plugin" in path.read_text(encoding="utf-8")` | NO/NOT IN FILE | byte/file read |
| cv2.VideoCapture | `scripts/classify_test_access.py` | 251 | `"os.open, os.scandir/listdir, subprocess arguments or cv2.VideoCapture is "` | NO/NOT IN FILE | media operation boundary |
| subprocess | `scripts/classify_test_access.py` | 121 | `proc = subprocess.run(` | NO/NOT IN FILE | child process boundary |
| FFmpeg/FFprobe | `scripts/collect_camera_creation_time_deltas.py` | 33 | `"ffprobe", "-v", "error",` | YES | media operation boundary |
| subprocess | `scripts/collect_camera_creation_time_deltas.py` | 39 | `out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()` | YES | child process boundary |
| builtins.open | `scripts/estimate_camera_sync_offsets.py` | 58 | `with wave.open(str(path), "rb") as wf:` | YES | byte/file read |
| Path.open | `scripts/estimate_camera_sync_offsets.py` | 58 | `with wave.open(str(path), "rb") as wf:` | YES | byte/file read |
| builtins.open | `scripts/extract_sync_review_frames.py` | 258 | `with open(path, "rb") as f:` | YES | byte/file read |
| FFmpeg/FFprobe | `scripts/extract_sync_review_frames.py` | 13 | `- Running without authorization will raise a PermissionError and refuse to invoke ffmpeg.` | YES | media operation boundary |
| FFmpeg/FFprobe | `scripts/extract_sync_review_frames.py` | 271 | `"""Extract a single frame at timestamp t_s using ffmpeg."""` | YES | media operation boundary |
| FFmpeg/FFprobe | `scripts/extract_sync_review_frames.py` | 275 | `"ffmpeg", "-y", "-v", "error",` | YES | media operation boundary |
| subprocess | `scripts/extract_sync_review_frames.py` | 285 | `result = subprocess.run(cmd, capture_output=True, text=True)` | YES | child process boundary |
| builtins.open | `scripts/generate_experiment_manifests.py` | 78 | `with open(frozen_params_path, "w", encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/generate_experiment_manifests.py` | 85 | `with open(layer_b_src_manifest, "r", encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/generate_experiment_manifests.py` | 90 | `with open(layer_b_dst_manifest, "w", encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/generate_experiment_manifests.py` | 105 | `with open(exp_manifest_path, "w", encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| subprocess | `scripts/generate_experiment_manifests.py` | 30 | `res = subprocess.run(` | NO/NOT IN FILE | child process boundary |
| subprocess | `scripts/generate_experiment_manifests.py` | 44 | `res = subprocess.run(` | NO/NOT IN FILE | child process boundary |
| builtins.open | `scripts/generate_publication_figures.py` | 84 | `with open(front_v, encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/generate_publication_figures.py` | 123 | `with open(af, encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/generate_publication_figures.py` | 395 | `with open(b4_singles_p) as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/generate_publication_tables.py` | 40 | `with open(output_dir / f"{table_id}.csv", "w", newline="", encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/generate_publication_tables.py` | 89 | `with open(EXP_DIR / "B0" / "single_events.json", encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/generate_publication_tables.py` | 93 | `with open(EXP_DIR / "B4" / "single_events.json", encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/generate_publication_tables.py` | 163 | `with open(front_v, encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/generate_publication_tables.py` | 201 | `with open(af, encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/generate_publication_tables.py` | 344 | `with open(sp) as f:` | NO/NOT IN FILE | byte/file read |
| Path.read_bytes | `scripts/mission10_artifact_manifest.py` | 74 | `raw = path.read_bytes()` | YES | byte/file read |
| builtins.open | `scripts/mission5a_build_preservation_manifest.py` | 71 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.open | `scripts/mission5a_build_preservation_manifest.py` | 71 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.read_text | `scripts/mission5a_build_preservation_manifest.py` | 291 | `text = cfg.read_text(encoding="utf-8")` | YES | byte/file read |
| Path.read_text | `scripts/mission5a_build_preservation_manifest.py` | 306 | `result = verify_manifest(Path(args.root), json.loads(Path(args.manifest).read_text("utf-8")))` | YES | byte/file read |
| subprocess | `scripts/mission5a_build_preservation_manifest.py` | 79 | `out = subprocess.run(` | YES | child process boundary |
| builtins.open | `scripts/organize_and_manifest_datasets.py` | 36 | `with open(path, "rb") as f:` | YES | byte/file read |
| builtins.open | `scripts/organize_and_manifest_datasets.py` | 238 | `with open(v_jsonl, "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/organize_and_manifest_datasets.py` | 243 | `with open(v_json, "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/organize_and_manifest_datasets.py` | 248 | `with open(a_jsonl, "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/organize_and_manifest_datasets.py` | 253 | `with open(a_json, "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/organize_and_manifest_datasets.py` | 305 | `with open(summary_file, "w", encoding="utf-8") as f:` | YES | byte/file read |
| FFmpeg/FFprobe | `scripts/organize_and_manifest_datasets.py` | 45 | `"ffprobe",` | YES | media operation boundary |
| subprocess | `scripts/organize_and_manifest_datasets.py` | 52 | `res = subprocess.run(cmd, capture_output=True, text=True, check=True)` | YES | child process boundary |
| builtins.open | `scripts/organize_v2_dataset.py` | 29 | `with open(filepath, "rb") as f:` | YES | byte/file read |
| builtins.open | `scripts/organize_v2_dataset.py` | 60 | `with open(AUDIT_FILE) as f:` | YES | byte/file read |
| builtins.open | `scripts/organize_v2_dataset.py` | 392 | `with open(v_manifest_json, "w") as f:` | YES | byte/file read |
| builtins.open | `scripts/organize_v2_dataset.py` | 406 | `with open(v_manifest_jsonl, "w") as f:` | YES | byte/file read |
| builtins.open | `scripts/organize_v2_dataset.py` | 486 | `with open(a_manifest_json, "w") as f:` | YES | byte/file read |
| builtins.open | `scripts/organize_v2_dataset.py` | 499 | `with open(a_manifest_jsonl, "w") as f:` | YES | byte/file read |
| builtins.open | `scripts/organize_v2_dataset.py` | 592 | `with open(selection_json, "w") as f:` | YES | byte/file read |
| builtins.open | `scripts/prepare_researcher_snapshot.py` | 140 | `with path.open("rb") as handle:` | YES | byte/file read |
| builtins.open | `scripts/prepare_researcher_snapshot.py` | 404 | `with (target / name).open("x", encoding="utf-8") as handle:  # 'x': fail if it exists` | YES | byte/file read |
| Path.open | `scripts/prepare_researcher_snapshot.py` | 140 | `with path.open("rb") as handle:` | YES | byte/file read |
| Path.open | `scripts/prepare_researcher_snapshot.py` | 404 | `with (target / name).open("x", encoding="utf-8") as handle:  # 'x': fail if it exists` | YES | byte/file read |
| Path.read_text | `scripts/prepare_researcher_snapshot.py` | 195 | `check_proposal_label(path.read_text(encoding="utf-8"), heading, rel)` | YES | byte/file read |
| subprocess | `scripts/prepare_researcher_snapshot.py` | 223 | `def git_state(root: Path, runner=subprocess.run) -> dict:` | YES | child process boundary |
| subprocess | `scripts/prepare_researcher_snapshot.py` | 259 | `runner=subprocess.run,` | YES | child process boundary |
| builtins.open | `scripts/preprocess_audio_dataset.py` | 41 | `with open(path, "rb") as f:` | YES | byte/file read |
| builtins.open | `scripts/preprocess_audio_dataset.py` | 116 | `with wave.open(str(path), "rb") as wav:` | YES | byte/file read |
| builtins.open | `scripts/preprocess_audio_dataset.py` | 372 | `with open(manifest_json, "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/preprocess_audio_dataset.py` | 375 | `with open(manifest_jsonl, "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/preprocess_audio_dataset.py` | 420 | `with open(summary_file, "w", encoding="utf-8") as f:` | YES | byte/file read |
| Path.open | `scripts/preprocess_audio_dataset.py` | 116 | `with wave.open(str(path), "rb") as wav:` | YES | byte/file read |
| FFmpeg/FFprobe | `scripts/preprocess_audio_dataset.py` | 50 | `"ffprobe",` | YES | media operation boundary |
| FFmpeg/FFprobe | `scripts/preprocess_audio_dataset.py` | 98 | `"ffmpeg",` | YES | media operation boundary |
| subprocess | `scripts/preprocess_audio_dataset.py` | 57 | `res = subprocess.run(cmd, capture_output=True, text=True, check=True)` | YES | child process boundary |
| subprocess | `scripts/preprocess_audio_dataset.py` | 107 | `res = subprocess.run(cmd, capture_output=True, text=True)` | YES | child process boundary |
| builtins.open | `scripts/preprocess_audio_dataset_v2.py` | 145 | `with wave.open(str(wav_path), "rb") as wf:` | YES | byte/file read |
| builtins.open | `scripts/preprocess_audio_dataset_v2.py` | 163 | `with open(SELECTION_MANIFEST) as f:` | YES | byte/file read |
| builtins.open | `scripts/preprocess_audio_dataset_v2.py` | 243 | `with open(SPLITS_DIR / "dataset_split.json", "w") as f:` | YES | byte/file read |
| builtins.open | `scripts/preprocess_audio_dataset_v2.py` | 335 | `with open(manifest_v2_json, "w") as f:` | YES | byte/file read |
| builtins.open | `scripts/preprocess_audio_dataset_v2.py` | 337 | `with open(manifest_v2_jsonl, "w") as f:` | YES | byte/file read |
| Path.open | `scripts/preprocess_audio_dataset_v2.py` | 145 | `with wave.open(str(wav_path), "rb") as wf:` | YES | byte/file read |
| FFmpeg/FFprobe | `scripts/preprocess_audio_dataset_v2.py` | 130 | `"ffmpeg",` | YES | media operation boundary |
| subprocess | `scripts/preprocess_audio_dataset_v2.py` | 139 | `subprocess.run(cmd, capture_output=True, check=True)` | YES | child process boundary |
| builtins.open | `scripts/preprocess_audio_dataset_v3.py` | 147 | `with wave.open(str(wav_path), "rb") as wf:` | YES | byte/file read |
| builtins.open | `scripts/preprocess_audio_dataset_v3.py` | 169 | `with open(SELECTION_MANIFEST) as f:` | YES | byte/file read |
| builtins.open | `scripts/preprocess_audio_dataset_v3.py` | 286 | `with open(manifest_v3_json, "w") as f:` | YES | byte/file read |
| builtins.open | `scripts/preprocess_audio_dataset_v3.py` | 288 | `with open(manifest_v3_jsonl, "w") as f:` | YES | byte/file read |
| builtins.open | `scripts/preprocess_audio_dataset_v3.py` | 300 | `with open(PROCESSED_AUDIO_DIR / "normalization_stats.json", "w") as f:` | YES | byte/file read |
| Path.open | `scripts/preprocess_audio_dataset_v3.py` | 147 | `with wave.open(str(wav_path), "rb") as wf:` | YES | byte/file read |
| FFmpeg/FFprobe | `scripts/preprocess_audio_dataset_v3.py` | 132 | `"ffmpeg",` | YES | media operation boundary |
| subprocess | `scripts/preprocess_audio_dataset_v3.py` | 141 | `subprocess.run(cmd, capture_output=True, check=True)` | YES | child process boundary |
| builtins.open | `scripts/run_canonical_tests.py` | 29 | `with open(path, "rb") as f:` | YES | byte/file read |
| builtins.open | `scripts/run_canonical_tests.py` | 178 | `with open(candidate_manifest_path) as fp:` | YES | byte/file read |
| builtins.open | `scripts/run_canonical_tests.py` | 198 | `with open(pf) as f:` | YES | byte/file read |
| builtins.open | `scripts/run_canonical_tests.py` | 220 | `with open(pf) as f:` | YES | byte/file read |
| builtins.open | `scripts/run_canonical_tests.py` | 244 | `with open(pf) as f:` | YES | byte/file read |
| builtins.open | `scripts/run_canonical_tests.py` | 264 | `with open(index_file) as f:` | YES | byte/file read |
| builtins.open | `scripts/run_canonical_tests.py` | 412 | `with open(json_results_path, "w") as fp:` | YES | byte/file read |
| FFmpeg/FFprobe | `scripts/run_canonical_tests.py` | 296 | `["ffmpeg", "-v", "error", "-ss", "00:00:01.000", "-i", vpath, "-frames:v", "1", "-f", "null", "-"],` | YES | media operation boundary |
| FFmpeg/FFprobe | `scripts/run_canonical_tests.py` | 311 | `["ffmpeg", "-v", "error", "-i", vpath, "-vn", "-af", "volumedetect", "-f", "null", "-"],` | YES | media operation boundary |
| FFmpeg/FFprobe | `scripts/run_canonical_tests.py` | 383 | `["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", mpath],` | YES | media operation boundary |
| FFmpeg/FFprobe | `scripts/run_canonical_tests.py` | 393 | `tracker.record("Layer E", f"replay_{cat}_{eid}_media_stream", False, dt, f"ffprobe error: {res.stderr}")` | YES | media operation boundary |
| subprocess | `scripts/run_canonical_tests.py` | 295 | `res = subprocess.run(` | YES | child process boundary |
| subprocess | `scripts/run_canonical_tests.py` | 310 | `res = subprocess.run(` | YES | child process boundary |
| subprocess | `scripts/run_canonical_tests.py` | 382 | `res = subprocess.run(` | YES | child process boundary |
| Path.read_text | `scripts/run_exploratory_dual_camera_subset.py` | 65 | `raw = yaml.safe_load(path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_exploratory_dual_camera_subset.py` | 334 | `exploratory_cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_leg_exec.py` | 56 | `statement=Path(args.statement_file).read_text(encoding="utf-8").strip(),` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_phase10_1_candidate_comparison.py` | 81 | `raw = yaml.safe_load(path.read_text(encoding="utf-8"))` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_phase10_1_candidate_comparison.py` | 164 | `calib_manifest = yaml.safe_load(CALIBRATION_MANIFEST_PATH.read_text())` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_phase10_1_candidate_comparison.py` | 320 | `p9_ticks = [json.loads(l) for l in p9_file.read_text().splitlines() if l.strip()]` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_phase10_1_candidate_comparison.py` | 327 | `p10_ticks = [json.loads(l) for l in p10_file.read_text().splitlines() if l.strip()]` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_phase11_1_integrity_audit.py` | 37 | `records = [json.loads(Path(f).read_text()) for f in review_files]` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_phase11_1_integrity_audit.py` | 45 | `d = json.loads(Path(f).read_text())` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/run_phase11_annotation_inventory.py` | 211 | `with open(out_csv, "w", newline="", encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_phase11_annotation_inventory.py` | 65 | `structural = json.loads(STRUCTURAL_INVENTORY.read_text())` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_phase11_annotation_inventory.py` | 81 | `proposal = json.loads(proposal_path.read_text()) if proposal_path else None` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_phase11_annotation_inventory.py` | 83 | `review = json.loads(review_path.read_text()) if review_path else None` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/run_phase5_full_inference.py` | 63 | `with open(p, "rb") as f:` | YES | byte/file read |
| builtins.open | `scripts/run_phase5_full_inference.py` | 344 | `with open(front_v_file, "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/run_phase5_full_inference.py` | 363 | `with open(front_a_file, "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/run_phase5_full_inference.py` | 381 | `with open(back_v_file, "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/run_phase5_full_inference.py` | 531 | `with open(dec_file, "w", encoding="utf-8") as f_dec, open(kin_file, "w", encoding="utf-8") as f_kin:` | YES | byte/file read |
| builtins.open | `scripts/run_phase5_full_inference.py` | 567 | `with open(progress_file, "a", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/run_phase5_full_inference.py` | 592 | `with open(progress_md, "a", encoding="utf-8") as f:` | YES | byte/file read |
| Path.read_text | `scripts/run_phase5_full_inference.py` | 138 | `dec_raw = yaml.safe_load(dec_policy_file.read_text(encoding="utf-8"))` | YES | byte/file read |
| FFmpeg/FFprobe | `scripts/run_phase5_full_inference.py` | 72 | `"ffprobe",` | YES | media operation boundary |
| subprocess | `scripts/run_phase5_full_inference.py` | 81 | `res = subprocess.run(cmd, capture_output=True, text=True, check=True)` | YES | child process boundary |
| builtins.open | `scripts/run_real_world_experiments.py` | 179 | `with open(out_single_path, "r", encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/run_real_world_experiments.py` | 215 | `with open(stats_dir / "comprehensive_statistics.json", "w", encoding="utf-8") as f:` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_real_world_experiments.py` | 201 | `b0_singles = json.loads((RESULTS_DIR / "B0" / "single_events.json").read_text())` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_real_world_experiments.py` | 202 | `b2_singles = json.loads((RESULTS_DIR / "B2" / "single_events.json").read_text())` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_real_world_experiments.py` | 203 | `b3_singles = json.loads((RESULTS_DIR / "B3" / "single_events.json").read_text())` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_real_world_experiments.py` | 204 | `b4_singles = json.loads((RESULTS_DIR / "B4" / "single_events.json").read_text())` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/run_synthetic_tests.py` | 165 | `[json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line]` | NO/NOT IN FILE | byte/file read |
| subprocess | `scripts/run_synthetic_tests.py` | 163 | `proc = subprocess.run(cmd, cwd=REPO_ROOT, env=env, capture_output=True, text=True)` | NO/NOT IN FILE | child process boundary |
| builtins.open | `scripts/select_and_manifest_audio_v3.py` | 46 | `with open(path, "rb") as f:` | YES | byte/file read |
| builtins.open | `scripts/select_and_manifest_audio_v3.py` | 178 | `with open(ESC50_CSV) as f:` | YES | byte/file read |
| builtins.open | `scripts/select_and_manifest_audio_v3.py` | 200 | `with open(MANIFESTS_DIR / "audio_v3_esc50_manifest.json", "w") as f:` | YES | byte/file read |
| builtins.open | `scripts/select_and_manifest_audio_v3.py` | 203 | `with open(MANIFESTS_DIR / "audio_v3_esc50_manifest.jsonl", "w") as f:` | YES | byte/file read |
| builtins.open | `scripts/select_and_manifest_audio_v3.py` | 382 | `with open(MANIFESTS_DIR / "audio_v3_selection.json", "w") as f:` | YES | byte/file read |
| builtins.open | `scripts/select_and_manifest_audio_v3.py` | 413 | `with open(SPLITS_DIR / "dataset_split.json", "w") as f:` | YES | byte/file read |
| FFmpeg/FFprobe | `scripts/select_and_manifest_audio_v3.py` | 55 | `"ffprobe",` | YES | media operation boundary |
| subprocess | `scripts/select_and_manifest_audio_v3.py` | 62 | `res = subprocess.run(cmd, capture_output=True, text=True, check=True)` | YES | child process boundary |
| builtins.open | `scripts/train_audio_model.py` | 690 | `with wave.open(str(wav_path), "rb") as wfp:` | YES | byte/file read |
| builtins.open | `scripts/train_audio_model.py` | 742 | `with open(run_dir / "metrics/metrics.json", "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/train_audio_model.py` | 746 | `with open(run_dir / "metrics/training_history.json", "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/train_audio_model.py` | 790 | `with open(run_dir / "config/experiment_config.json", "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/train_audio_model.py` | 799 | `with open(run_dir / "predictions/predictions.jsonl", "w", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/train_audio_model.py` | 803 | `with open(run_dir / "predictions/test_predictions.csv", "w", newline="", encoding="utf-8") as f:` | YES | byte/file read |
| builtins.open | `scripts/train_audio_model.py` | 843 | `with open(run_dir / "report/error_analysis.json", "w", encoding="utf-8") as f:` | YES | byte/file read |
| Path.open | `scripts/train_audio_model.py` | 690 | `with wave.open(str(wav_path), "rb") as wfp:` | YES | byte/file read |
| NumPy load | `scripts/train_audio_model.py` | 468 | `feat = np.load(feat_path)` | YES | byte/file read |
| Torch load | `scripts/train_audio_model.py` | 617 | `best_state = torch.load(best_checkpoint_path, map_location=device)` | YES | byte/file read |
| builtins.open | `scripts/train_audio_model_v2.py` | 86 | `with open(manifest_path) as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v2.py` | 407 | `with open(RUN_DIR / "predictions/predictions.jsonl", "w") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v2.py` | 411 | `with open(RUN_DIR / "predictions/test_predictions.csv", "w", newline="") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v2.py` | 427 | `with open(RUN_DIR / "report/error_analysis.json", "w") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v2.py` | 432 | `with open(v1_metrics_file) as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v2.py` | 495 | `with open(RUN_DIR / "metrics/v1_vs_v2_comparison.json", "w") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v2.py` | 516 | `with open(RUN_DIR / "metrics/metrics.json", "w") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v2.py` | 518 | `with open(RUN_DIR / "metrics/training_history.json", "w") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v2.py` | 531 | `with open(RUN_DIR / "config/experiment_config.json", "w") as f:` | NO/NOT IN FILE | byte/file read |
| NumPy load | `scripts/train_audio_model_v2.py` | 101 | `feats.append(np.load(fp))` | NO/NOT IN FILE | byte/file read |
| NumPy load | `scripts/train_audio_model_v2.py` | 749 | `f_arr = np.load(feat_p)` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v3_esc50.py` | 88 | `with open(manifest_path) as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v3_esc50.py` | 281 | `with open(RUN_DIR / "config/config.json", "w") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v3_esc50.py` | 500 | `with open(RUN_DIR / "reports/per_category_analysis.json", "w") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v3_esc50.py` | 507 | `with open(v2_metrics_file) as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v3_esc50.py` | 536 | `with open(RUN_DIR / "metrics/v2_vs_v3_comparison.json", "w") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v3_esc50.py` | 548 | `with open(RUN_DIR / "metrics/metrics.json", "w") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v3_esc50.py` | 578 | `with open(RUN_DIR / "predictions/test_predictions.json", "w") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v3_esc50.py` | 585 | `with open(WORKSPACE / "data/manifests/audio_v3_selection.json") as f:` | NO/NOT IN FILE | byte/file read |
| builtins.open | `scripts/train_audio_model_v3_esc50.py` | 843 | `with open(RUN_DIR / "reports/forensic_analysis.json", "w") as f:` | NO/NOT IN FILE | byte/file read |
| NumPy load | `scripts/train_audio_model_v3_esc50.py` | 103 | `feats.append(np.load(fp))` | NO/NOT IN FILE | byte/file read |
| Torch load | `scripts/train_audio_model_v3_esc50.py` | 415 | `ckpt_dict = torch.load(best_ckpt_path)` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/validate_exploratory_run_output.py` | 39 | `manifest = json.loads(manifest_path.read_text())` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/validate_exploratory_run_output.py` | 66 | `steps = json.loads(steps_file.read_text())` | NO/NOT IN FILE | byte/file read |
| Path.read_text | `scripts/validate_exploratory_run_output.py` | 89 | `Path("data/manifests/camera_sync_offsets_candidate.yaml").read_text()` | NO/NOT IN FILE | byte/file read |

**Rows:** 407

## Static interpretation

- `src/railway_detection/vision/video.py` guards the lowest-level `cv2.VideoCapture` opener.
- `src/railway_detection/data/audio_extractor.py` guards the source path immediately before invoking ffmpeg.
- `src/railway_detection/annotation/media_inspector.py` guards hashing/probing before open/subprocess.
- `torch.load` and `np.load` are model/processed-data paths and are not raw-media readers; they are covered by the separate access-classification guard when tests exercise them.
- Generic metadata/cache readers are not media readers unless their input path can resolve to protected media.
- Python-level guards do not constitute an OS sandbox against arbitrary native or shell access.
