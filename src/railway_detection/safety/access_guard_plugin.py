"""Read-blocking pytest plugin used to classify and to safely run tests (Mission 10, WP10.3).

Load with ``-p railway_detection.safety.access_guard_plugin --access-guard-log <file.jsonl>``.

While active it **blocks** (raises, so the read never happens) any Python-level attempt to read:

* ``RAW_MEDIA``        -- ``data/raw/`` or any media-suffixed file inside the repository;
* ``MODEL_CHECKPOINT`` -- weights (``.pt``, ``.onnx``...), ``models/``,
``experiments/*/checkpoints``;
* ``PROCESSED_DATA``   -- ``data/processed/``, ``results/``, ``experiments/``, ``outputs/``;

and any **write** into the repository tree (outside caches). Reads of other repository files
(configs, docs, ground-truth/manifest/governance metadata) are allowed and logged as ``METADATA``.
Reads of code (``src``, ``tests``, ``scripts``, virtual environments) are ignored. Every blocked or
metadata attempt is appended to the JSONL log with the node id that caused it.

Covered primitives: ``builtins.open``, ``io.open``, ``os.open``, ``os.scandir``, ``os.listdir``,
``subprocess.Popen`` path arguments (relative ones resolved against the working directory) and
``cv2.VideoCapture``. NOT covered (disclosed limitation): native code that opens files itself
without going through those entry points, and shell tools run outside Python. This is a verified
guard over Python-level access, not an operating-system sandbox.
"""

from __future__ import annotations

import builtins
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
MEDIA_SUFFIXES = frozenset(
    {
        ".mov",
        ".mp4",
        ".m4v",
        ".avi",
        ".mkv",
        ".webm",
        ".wav",
        ".mp3",
        ".flac",
        ".aac",
        ".ogg",
        ".m4a",
    }
)
CHECKPOINT_SUFFIXES = frozenset(
    {".pt", ".pth", ".onnx", ".ckpt", ".safetensors", ".engine", ".weights"}
)
CODE_ROOTS = frozenset(
    {
        ".venv",
        "venv",
        ".git",
        "src",
        "tests",
        "scripts",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
    }
)
SESSION_ALLOWED_READS = frozenset({"results/experiment_registry.jsonl"})  # tests/conftest.py guard
WRITE_ALLOWED_ROOTS = (".pytest_cache", ".ruff_cache")

CATEGORY_RAW = "RAW_MEDIA"
CATEGORY_CHECKPOINT = "MODEL_CHECKPOINT"
CATEGORY_PROCESSED = "PROCESSED_DATA"
CATEGORY_METADATA = "METADATA"
BLOCKED_CATEGORIES = frozenset({CATEGORY_RAW, CATEGORY_CHECKPOINT, CATEGORY_PROCESSED})


def _called_from_conftest() -> bool:
    """True when the nearest non-plugin frames belong to ``tests/conftest.py`` (registry guard)."""
    frame = sys._getframe(2)
    for _ in range(8):
        if frame is None:
            break
        if frame.f_code.co_filename.replace("\\", "/").endswith("tests/conftest.py"):
            return True
        frame = frame.f_back  # type: ignore[assignment]
    return False


class AccessGuardError(AssertionError):
    """A test attempted a read or write the safe runner forbids."""


def categorize(path: str | os.PathLike[str], repo_root: Path = REPO_ROOT) -> tuple[str | None, str]:
    """Return ``(category, repo-relative path)``; category ``None`` = not a guarded location."""
    try:
        real = Path(os.path.realpath(os.fspath(path)))
    except (OSError, ValueError, TypeError):
        return None, ""
    root = Path(os.path.realpath(repo_root))
    if real != root and root not in real.parents:
        return None, ""
    rel = real.relative_to(root).as_posix() if real != root else "."
    first = rel.split("/", 1)[0]
    if first in CODE_ROOTS:
        return None, rel
    suffix = real.suffix.lower()
    if suffix in MEDIA_SUFFIXES or rel == "data/raw" or rel.startswith("data/raw/"):
        return CATEGORY_RAW, rel
    if (
        suffix in CHECKPOINT_SUFFIXES
        or rel == "models"
        or rel.startswith("models/")
        or (rel.startswith("experiments/") and "/checkpoints" in rel)
    ):
        return CATEGORY_CHECKPOINT, rel
    if (
        first in {"results", "experiments", "outputs"}
        or rel == "data/processed"
        or rel.startswith("data/processed/")
    ):
        return CATEGORY_PROCESSED, rel
    return CATEGORY_METADATA, rel


class _Guard:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.current_node = ""
        self._log = log_path.open("a", encoding="utf-8")
        self._originals: dict[str, Any] = {}

    # -- logging ---------------------------------------------------------------------------
    def record(self, category: str, rel: str, how: str, blocked: bool) -> None:
        node = os.environ.get("PYTEST_CURRENT_TEST") or self.current_node or "<session>"
        self._log.write(
            json.dumps(
                {"node": node, "category": category, "path": rel, "how": how, "blocked": blocked},
                sort_keys=True,
            )
            + "\n"
        )
        self._log.flush()

    # -- checks ----------------------------------------------------------------------------
    def check_read(self, path: Any, how: str) -> None:
        category, rel = categorize(path)
        if category is None or rel == ".":
            return
        in_test = bool(os.environ.get("PYTEST_CURRENT_TEST"))
        if category == CATEGORY_METADATA:
            if not Path(os.path.realpath(os.fspath(path))).is_dir():
                self.record(category, rel, how, blocked=False)
            return
        if (
            how == "os.open"
            and Path(os.path.realpath(os.fspath(path))).is_dir()
            and category != CATEGORY_RAW
        ):
            return  # bare directory descriptor (pytest bookkeeping); no listing, no bytes
        if rel in SESSION_ALLOWED_READS and (not in_test or _called_from_conftest()):
            self.record(category, rel, how + ":conftest-registry-guard", blocked=False)
            return
        self.record(category, rel, how, blocked=True)
        raise AccessGuardError(f"access guard: {category} read blocked ({how}): {rel}")

    def check_write(self, path: Any, how: str) -> None:
        try:
            real = Path(os.path.realpath(os.fspath(path)))
        except (OSError, ValueError, TypeError):
            return
        root = Path(os.path.realpath(REPO_ROOT))
        if real != root and root not in real.parents:
            return
        rel = real.relative_to(root).as_posix() if real != root else "."
        if "__pycache__" in rel or rel.split("/", 1)[0] in WRITE_ALLOWED_ROOTS:
            return
        self.record("REPO_WRITE", rel, how, blocked=True)
        raise AccessGuardError(f"access guard: write into the repository blocked ({how}): {rel}")

    # -- install ---------------------------------------------------------------------------
    def install(self) -> None:
        guard = self
        real_open, real_io_open, real_os_open = builtins.open, io.open, os.open
        real_scandir, real_listdir = os.scandir, os.listdir
        real_popen_init = subprocess.Popen.__init__

        def is_write(mode: Any) -> bool:
            return any(c in str(mode) for c in "wax+")

        def guarded_open(file: Any, mode: str = "r", *a: Any, **k: Any) -> Any:
            if isinstance(file, (str, bytes, os.PathLike)):
                (guard.check_write if is_write(mode) else guard.check_read)(file, "open")
            return real_open(file, mode, *a, **k)

        def guarded_io_open(file: Any, mode: str = "r", *a: Any, **k: Any) -> Any:
            if isinstance(file, (str, bytes, os.PathLike)):
                (guard.check_write if is_write(mode) else guard.check_read)(file, "io.open")
            return real_io_open(file, mode, *a, **k)

        def guarded_os_open(path: Any, flags: int, *a: Any, **k: Any) -> Any:
            if k.get("dir_fd") is not None:  # relative to a directory descriptor (tmp-dir cleanup)
                return real_os_open(path, flags, *a, **k)
            if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND):
                guard.check_write(path, "os.open")
            else:
                guard.check_read(path, "os.open")
            return real_os_open(path, flags, *a, **k)

        def guarded_scandir(path: Any = ".") -> Any:
            guard.check_read(path, "scandir")
            return real_scandir(path)

        def guarded_listdir(path: Any = ".") -> Any:
            guard.check_read(path, "listdir")
            return real_listdir(path)

        def guarded_popen_init(self: Any, args: Any, *a: Any, **k: Any) -> Any:
            argv = [args] if isinstance(args, (str, bytes)) else list(args)
            cwd = k.get("cwd") or os.getcwd()
            for item in argv:
                if isinstance(item, (str, os.PathLike)):
                    text = os.fspath(item)
                    if "/" in text or Path(text).suffix.lower() in MEDIA_SUFFIXES:
                        candidate = text if os.path.isabs(text) else os.path.join(cwd, text)
                        guard.check_read(candidate, "subprocess-arg")
            return real_popen_init(self, args, *a, **k)

        def media_observer(real_path: Path, operation: str) -> None:
            # A media check that reached the operation boundary is a raw-media attempt, whatever the
            # authorization says: tests must never touch real media.
            guard.check_read(real_path, f"media-guard:{operation}")

        from railway_detection.safety import media_guard

        media_guard.register_observer(media_observer)
        self._media_observer = media_observer

        self._originals = {
            "open": real_open,
            "io.open": real_io_open,
            "os.open": real_os_open,
            "scandir": real_scandir,
            "listdir": real_listdir,
            "popen": real_popen_init,
        }
        builtins.open, io.open, os.open = guarded_open, guarded_io_open, guarded_os_open
        os.scandir, os.listdir = guarded_scandir, guarded_listdir
        subprocess.Popen.__init__ = guarded_popen_init  # type: ignore[method-assign]
        try:  # cv2 reads files natively; guard its constructor when OpenCV is present
            import cv2  # type: ignore[import-not-found]

            real_capture = cv2.VideoCapture

            def guarded_capture(source: Any = None, *a: Any, **k: Any) -> Any:
                if isinstance(source, (str, os.PathLike)):
                    guard.check_read(source, "cv2.VideoCapture")
                return real_capture(source, *a, **k) if source is not None else real_capture()

            self._originals["cv2.VideoCapture"] = real_capture
            cv2.VideoCapture = guarded_capture
        except Exception:  # noqa: BLE001 - OpenCV absent or unusable: nothing to wrap
            pass

    def uninstall(self) -> None:
        o = self._originals
        if not o:
            return
        from railway_detection.safety import media_guard

        media_guard.unregister_observer(self._media_observer)
        builtins.open, io.open, os.open = o["open"], o["io.open"], o["os.open"]
        os.scandir, os.listdir = o["scandir"], o["listdir"]
        subprocess.Popen.__init__ = o["popen"]  # type: ignore[method-assign]
        if "cv2.VideoCapture" in o:
            import cv2  # type: ignore[import-not-found]

            cv2.VideoCapture = o["cv2.VideoCapture"]
        self._originals = {}
        self._log.close()


_GUARD: _Guard | None = None


def pytest_addoption(parser: Any) -> None:
    parser.addoption(
        "--access-guard-log",
        action="store",
        default=None,
        help="JSONL file that receives every blocked / metadata access attempt (required).",
    )


def pytest_configure(config: Any) -> None:
    global _GUARD
    log = config.getoption("--access-guard-log")
    if not log:
        raise RuntimeError("access guard: --access-guard-log is required so the run is verifiable")
    path = Path(log)
    if path.resolve() == REPO_ROOT or REPO_ROOT in path.resolve().parents:
        raise RuntimeError("access guard: the log must be written outside the repository")
    _GUARD = _Guard(path)
    _GUARD.install()
    _GUARD.record("GUARD", "-", "armed", blocked=False)


def pytest_unconfigure(config: Any) -> None:
    global _GUARD
    if _GUARD is not None:
        _GUARD.record("GUARD", "-", "disarmed", blocked=False)
        _GUARD.uninstall()
        _GUARD = None
