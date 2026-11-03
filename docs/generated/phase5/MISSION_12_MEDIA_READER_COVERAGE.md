# Mission 12 — Media Reader Coverage

**Scope:** post-remediation static inventory; no protected files were opened.

| Reader | Module/function | Boundary guard | Synthetic temp support | Status |
|---|---|---|---|---|
| PIL `Image.open` | `data/manifest.py:153` | `require_media_authorization(..., READ_RAW_MEDIA)` immediately before open | Yes | GUARDED |
| PIL `Image.open` | `data/validator.py:192` | same | Yes | GUARDED |
| PIL `Image.open` | `data/validator.py:202` | same | Yes | GUARDED |
| OpenCV `imread` | `research/scripts/generate_qualitative_figures.py:151` | guard immediately before read | Yes | GUARDED |
| OpenCV `imread` | `research/scripts/generate_qualitative_figures.py:237` | guard immediately before read | Yes | GUARDED |
| OpenCV `VideoCapture` | `research/scripts/generate_video_progression_figure.py:86` | guard immediately before capture | Yes | GUARDED |
| OpenCV `imread` | `research/scripts/generate_video_progression_figure.py:130` | guard immediately before read | Yes | GUARDED |
| OpenCV `VideoCapture` | `vision/video.py:80,93` | existing guard | Yes | GUARDED |
| FFmpeg | `data/audio_extractor.py:33,59` | existing guard before subprocess | Yes | GUARDED |
| FFprobe/FFmpeg | `annotation/media_inspector.py` | existing hash/probe/extract guards | Yes | GUARDED |
| WAV reader | `audio/preprocessor.py` | existing feature-extraction guard | Yes | GUARDED |
| `torch.load` | audio model/training paths | checkpoint integrity policy; not raw-media authorization | Synthetic tests only | SEPARATE CHECKPOINT CONTROL |
| `numpy.load` | feature-cache paths | processed-data classification/control | Synthetic tests only | SEPARATE PROCESSED-DATA CONTROL |

No PyAV, ImageIO, SoundFile, Librosa or Torchaudio calls were found in the searched source/script/research trees.

## Security properties

`media_guard` now includes image suffixes and image media type. It resolves symlinks, denies repository/non-temporary paths without the on-disk record, ignores the historical environment-variable bypass, and revalidates authorization from disk per operation. Python-level limitations remain: arbitrary shell/native code outside wrapped entry points is not an OS sandbox.

## Validation

- Synthetic image/video guard probe: allowed in temporary directory.
- Fake repository media path: denied with `AUTH_MEDIA_ACCESS_NOT_GRANTED`.
- Static opener tripwire and media authorization tests included in the 300-test focused run.
- No real media or protected image/video was accessed.