"""Mission 14 (WP14.4): dashboard file serving is limited to explicit allowlisted roots.

``server.PROJECT_ROOT`` and ``server.STATIC_WEB_DIR`` are pointed at a synthetic tree, so the
tests serve only files created here.  The handler methods are driven directly with a minimal fake
connection (no sockets), which also lets every test assert exactly what bytes would have been sent.
"""

from __future__ import annotations

import io
import json
import os
import sys
from http import HTTPStatus
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from security_support import (  # noqa: E402
    case_variant,
    filesystem_is_case_insensitive,
    make_fake_repo,
    outside_dir,
)

from railway_detection.demo import server  # noqa: E402
from railway_detection.safety import path_identity as pid  # noqa: E402

Handler = server.DashboardHTTPRequestHandler


class FakeConnection:
    """Just enough of ``BaseHTTPRequestHandler`` for the file-serving methods."""

    def __init__(self, headers: dict[str, str] | None = None, body: bytes = b"") -> None:
        self.wfile = io.BytesIO()
        self.rfile = io.BytesIO(body)
        self.headers = headers or {}
        self.status: object = None
        self.sent_headers: dict[str, str] = {}
        self.json: dict | None = None

    def send_response(self, code, *_a):
        self.status = code

    def send_header(self, key, value):
        self.sent_headers[key] = value

    def end_headers(self):
        pass

    def send_error(self, code, *_a):
        self.status = ("error", code)

    def _send_json(self, data, status=HTTPStatus.OK):
        self.status = status
        self.json = data


@pytest.fixture
def tree(tmp_path_factory, monkeypatch):
    repo = make_fake_repo(tmp_path_factory, monkeypatch, name="DashRepo")
    root = repo.root
    (root / "outputs/video_tests/run1").mkdir(parents=True, exist_ok=True)
    (root / "outputs/video_tests/run1/annotated.mp4").write_bytes(b"0123456789")
    (root / "outputs/video_tests/run1/summary.json").write_text('{"ok": true}', encoding="utf-8")
    (root / "outputs/video_tests/run1/notes.py").write_text("print('no')", encoding="utf-8")
    (root / "experiments/vision/run1/evaluation/pr.png").write_bytes(b"PNG-PR")
    (root / "experiments/vision/run1/checkpoints/weights/best.pt").write_bytes(b"WEIGHTS")
    (root / "experiments/vision/run1/weights_plot.png").write_bytes(b"PNG-NOT-EVAL")
    (root / "configs/secret.yaml").write_text("k: v", encoding="utf-8")
    (root / "data/governance/auth.json").write_text("{}", encoding="utf-8")
    static = outside_dir(tmp_path_factory, "static")
    (static / "index.html").write_text("<html>spa</html>", encoding="utf-8")
    (static / "app.js").write_text("//js", encoding="utf-8")
    (static / "assets").mkdir()
    (static / "assets" / "logo.svg").write_text("<svg/>", encoding="utf-8")
    monkeypatch.setattr(server, "PROJECT_ROOT", root)
    monkeypatch.setattr(server, "STATIC_WEB_DIR", static)
    monkeypatch.setattr(server, "OUTPUTS_DIR", root / "outputs/video_tests")
    return repo, static


def serve_output(url: str, headers: dict[str, str] | None = None) -> FakeConnection:
    conn = FakeConnection(headers)
    Handler._handle_serve_output_file(conn, url)  # type: ignore[arg-type]
    return conn


def serve_experiment(url: str) -> FakeConnection:
    conn = FakeConnection()
    Handler._handle_serve_experiment_file(conn, url)  # type: ignore[arg-type]
    return conn


NOT_FOUND = ("error", HTTPStatus.NOT_FOUND)


# ------------------------------------------------------------------ allowed assets


def test_allowed_outputs_and_plots_are_served_with_nosniff(tree):
    conn = serve_output("/outputs/video_tests/run1/annotated.mp4")
    assert conn.status == HTTPStatus.OK and conn.wfile.getvalue() == b"0123456789"
    assert conn.sent_headers["X-Content-Type-Options"] == "nosniff"
    conn = serve_output("/outputs/video_tests/run1/summary.json")
    assert json.loads(conn.wfile.getvalue()) == {"ok": True}
    conn = serve_experiment("/experiments/vision/run1/evaluation/pr.png")
    assert conn.status == HTTPStatus.OK and conn.wfile.getvalue() == b"PNG-PR"


def test_byte_ranges_are_clamped_and_bad_ranges_fall_back_to_a_full_response(tree):
    conn = serve_output("/outputs/video_tests/run1/annotated.mp4", {"Range": "bytes=2-4"})
    assert conn.status == HTTPStatus.PARTIAL_CONTENT and conn.wfile.getvalue() == b"234"
    conn = serve_output("/outputs/video_tests/run1/annotated.mp4", {"Range": "bytes=5-999999"})
    assert conn.wfile.getvalue() == b"56789"
    for bad in ("bytes=-5-3", "bytes=9-2", "bytes=abc-"):
        conn = serve_output("/outputs/video_tests/run1/annotated.mp4", {"Range": bad})
        assert conn.status == HTTPStatus.OK and conn.wfile.getvalue() == b"0123456789"


# --------------------------------------------------------------- everything else is a 404


TRAVERSAL = [
    "/outputs/../configs/secret.yaml",
    "/outputs/video_tests/../../configs/secret.yaml",
    "/outputs/%2e%2e/configs/secret.yaml",
    "/outputs/%2E%2E%2Fconfigs%2Fsecret.yaml",
    "/outputs/%252e%252e/configs/secret.yaml",
    "/outputs/%25252e%25252e%25252fconfigs%25252fsecret.yaml",
    "/outputs/..%2fconfigs/secret.yaml",
    "/outputs/..\\configs\\secret.yaml",
    "/outputs/%5c..%5cconfigs%5csecret.yaml",
    "/outputs/video_tests/run1/..%5c..%5c..%5cconfigs%5csecret.yaml",
    "/outputs//etc/passwd",
    "/outputs/%2fetc%2fpasswd",
    "/outputs/....//configs/secret.yaml",
    "/outputs/video_tests/run1/annotated.mp4%00.json",
    "/outputs/data/governance/auth.json",
    "/outputs/video_tests/run1/notes.py",  # inside the root but not a served file type
    "/outputs/video_tests/run1/missing.mp4",
    "/outputs/video_tests/run1",  # a directory
    "/outputs/",
    "/outputs/.",
    "/elsewhere/video_tests/run1/annotated.mp4",
]


@pytest.mark.parametrize("url", TRAVERSAL)
def test_outputs_route_denies_traversal_encodings_and_unserved_files(tree, url):
    conn = serve_output(url)
    assert conn.status == NOT_FOUND
    assert conn.wfile.getvalue() == b""


EXPERIMENT_DENIALS = [
    "/experiments/../configs/secret.yaml",
    "/experiments/%2e%2e/configs/secret.yaml",
    "/experiments/%252e%252e/data/governance/auth.json",
    "/experiments/vision/run1/checkpoints/weights/best.pt",  # weights are never served
    "/experiments/vision/run1/weights_plot.png",  # not under .../evaluation/
    "/experiments/vision/run1/evaluation/../checkpoints/weights/best.pt",
    "/experiments/vision/run1/evaluation/..%2fcheckpoints%2fweights%2fbest.pt",
    "/experiments/other/run1/evaluation/pr.png",
    "/experiments/vision/run1/evaluation/missing.png",
    "/experiments/vision/run1/evaluation",
    "/experiments/vision",
]


@pytest.mark.parametrize("url", EXPERIMENT_DENIALS)
def test_experiments_route_serves_only_evaluation_plots(tree, url):
    conn = serve_experiment(url)
    assert conn.status == NOT_FOUND
    assert conn.wfile.getvalue() == b""


def test_symlink_escape_is_denied_for_files_and_directories(tree, tmp_path_factory):
    repo, _static = tree
    (repo.root / "outputs/video_tests/run1/link.mp4").symlink_to(repo.video)  # raw media
    (repo.root / "outputs/video_tests/rawdir").symlink_to(repo.raw_dir)
    (repo.root / "experiments/vision/run1/evaluation/weights.png").symlink_to(
        repo.root / "experiments/vision/run1/checkpoints/weights/best.pt"
    )
    outside = outside_dir(tmp_path_factory, "stolen")
    (outside / "x.json").write_text("{}", encoding="utf-8")
    (repo.root / "outputs/outdir").symlink_to(outside)
    for url in (
        "/outputs/video_tests/run1/link.mp4",
        "/outputs/video_tests/rawdir/camera_front.mov",
        "/outputs/outdir/x.json",
    ):
        conn = serve_output(url)
        assert conn.status == NOT_FOUND and conn.wfile.getvalue() == b"", url
    conn = serve_experiment("/experiments/vision/run1/evaluation/weights.png")
    assert conn.status == NOT_FOUND and conn.wfile.getvalue() == b""


def test_a_symlink_that_stays_inside_the_root_is_still_served(tree):
    repo, _ = tree
    (repo.root / "outputs/video_tests/run1/alias.json").symlink_to(
        repo.root / "outputs/video_tests/run1/summary.json"
    )
    conn = serve_output("/outputs/video_tests/run1/alias.json")
    assert conn.status == HTTPStatus.OK and json.loads(conn.wfile.getvalue()) == {"ok": True}


def test_case_variants_are_the_same_resource_and_cannot_escape(tree):
    repo, _ = tree
    if not filesystem_is_case_insensitive(repo.root):
        pytest.skip("case-sensitive filesystem")
    same = serve_output("/outputs/VIDEO_TESTS/run1/SUMMARY.JSON")
    assert same.status == HTTPStatus.OK  # the identical file, allowed like its canonical spelling
    conn = serve_output("/outputs/video_tests/../CONFIGS/secret.yaml")
    assert conn.status == NOT_FOUND
    conn = serve_experiment("/experiments/VISION/run1/EVALUATION/pr.png")
    assert conn.status == HTTPStatus.OK
    conn = serve_experiment("/experiments/VISION/run1/CHECKPOINTS/weights/best.pt")
    assert conn.status == NOT_FOUND
    # A project root spelled with different case does not widen what is served.
    original = server.PROJECT_ROOT
    server.PROJECT_ROOT = case_variant(original)
    try:
        assert serve_output("/outputs/../configs/secret.yaml").status == NOT_FOUND
        assert serve_output("/outputs/video_tests/run1/summary.json").status == HTTPStatus.OK
    finally:
        server.PROJECT_ROOT = original


def test_resolve_served_file_rejects_unknown_routes_and_non_text(tree):
    for route_url in ("/other/x.png", "outputs/x.png", "", None, 5):
        with pytest.raises(pid.PathIdentityError):
            server.resolve_served_file(route_url, route="outputs")  # type: ignore[arg-type]
    with pytest.raises(pid.PathIdentityError):
        server.resolve_served_file("/outputs/x.png", route="nonexistent")


# --------------------------------------------------------------------- static assets


def static_path(url: str) -> Path:
    return Path(Handler.translate_path(None, url))  # type: ignore[arg-type]


def test_static_assets_resolve_inside_the_static_directory(tree):
    _repo, static = tree
    assert static_path("/app.js") == static / "app.js"
    assert static_path("/assets/logo.svg") == static / "assets" / "logo.svg"
    assert static_path("/") == static / "index.html"
    assert static_path("/app.js?x=1#frag") == static / "app.js"
    assert Handler._static_asset_exists("/app.js")
    assert not Handler._static_asset_exists("/missing.js")


@pytest.mark.parametrize(
    "url",
    ["/../configs/secret.yaml", "/%2e%2e/%2e%2e/configs/secret.yaml", "/%252e%252e/x",
     "/assets/../../x", "/..\\x", "/%5c..%5cx", "//etc/passwd", "/\x00"],
)  # fmt: skip
def test_static_translation_cannot_leave_the_static_directory(tree, url):
    _repo, static = tree
    translated = static_path(url)
    assert translated.name in {"__not_found__", "index.html"} or pid.is_within(translated, static)
    assert not translated.exists() or pid.is_within(translated, static)


def test_static_symlink_escape_is_not_served(tree, tmp_path_factory):
    _repo, static = tree
    outside = outside_dir(tmp_path_factory, "static_out")
    (outside / "leak.txt").write_text("leak", encoding="utf-8")
    os.symlink(outside / "leak.txt", static / "leak.txt")
    assert static_path("/leak.txt").name == "__not_found__"
    assert not Handler._static_asset_exists("/leak.txt")


# ---------------------------------------------------------------- /api/process guard


def post_process(video_path: str) -> FakeConnection:
    body = json.dumps({"video_path": video_path}).encode()
    conn = FakeConnection({"Content-Length": str(len(body))}, body)
    Handler._handle_api_process(conn)  # type: ignore[arg-type]
    return conn


def test_process_route_refuses_protected_media_before_starting_a_job(tree, monkeypatch):
    repo, _ = tree
    started: list[str] = []
    monkeypatch.setattr(server.threading, "Thread", lambda *a, **k: started.append("thread"))
    monkeypatch.setattr(server, "create_output_directory", lambda *a, **k: started.append("outdir"))
    for target in (
        repo.video,
        repo.raw_dir / "clip_without_extension",
        repo.root / "outputs" / "x.m2ts",
    ):
        conn = post_process(str(target))
        assert conn.status == HTTPStatus.FORBIDDEN, target
        assert "not authorized" in conn.json["error"]
        assert str(target) not in json.dumps(conn.json)
    assert started == []


def test_process_route_still_accepts_synthetic_temporary_video(tree, tmp_path_factory, monkeypatch):
    synthetic = outside_dir(tmp_path_factory, "proc") / "clip.mp4"
    synthetic.write_bytes(b"x")
    jobs: list[object] = []
    monkeypatch.setattr(server, "create_output_directory", lambda *a, **k: synthetic.parent / "out")
    monkeypatch.setattr(
        server.threading,
        "Thread",
        lambda *a, **k: type("T", (), {"start": lambda s: jobs.append(1)})(),
    )
    conn = post_process(str(synthetic))
    assert conn.status == HTTPStatus.OK and conn.json["status"] == "started"
    assert jobs == [1]
