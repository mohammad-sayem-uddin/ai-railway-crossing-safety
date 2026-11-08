"""Unit tests for the Dashboard Web Server and API endpoints."""

from __future__ import annotations

import json
import urllib.request
from http.server import HTTPServer
from pathlib import Path
from threading import Thread

import pytest

from railway_detection.demo.server import (
    DashboardHTTPRequestHandler,
    parse_multipart_form,
)


def test_multipart_parser_preserves_binary_file_content_and_text_fields():
    boundary = "railway-form-boundary"
    file_bytes = b"video\x00payload\xff"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="video"; filename="sample.mp4"\r\n'
        "Content-Type: video/mp4\r\n\r\n"
    ).encode() + file_bytes + (
        f"\r\n--{boundary}\r\n"
        'Content-Disposition: form-data; name="conf"\r\n'
        "Content-Type: text/plain; charset=utf-8\r\n\r\n"
        "0.35"
        f"\r\n--{boundary}--\r\n"
    ).encode()

    form = parse_multipart_form(f"multipart/form-data; boundary={boundary}", body)

    assert form["video"].filename == "sample.mp4"
    assert form["video"].content == file_bytes
    assert form["video"].content_type == "video/mp4"
    assert form["conf"].text() == "0.35"


@pytest.mark.parametrize(
    ("content_type", "body", "message"),
    [
        ("application/json", b"{}", "not valid multipart"),
        (
            "multipart/form-data; boundary=b",
            b'--b\r\nContent-Disposition: form-data; filename="x"\r\n\r\nx\r\n--b--\r\n',
            "missing its name",
        ),
    ],
)
def test_multipart_parser_rejects_invalid_content_type_or_missing_name(
    content_type: str, body: bytes, message: str
):
    with pytest.raises(ValueError, match=message):
        parse_multipart_form(content_type, body)


def test_multipart_parser_rejects_duplicate_names():
    boundary = "duplicate-boundary"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"conf\"\r\n\r\n1"
        f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"conf\"\r\n\r\n2"
        f"\r\n--{boundary}--\r\n"
    ).encode()

    with pytest.raises(ValueError, match="duplicate multipart field"):
        parse_multipart_form(f"multipart/form-data; boundary={boundary}", body)


def test_dashboard_video_upload_endpoint_writes_parsed_binary_bytes(tmp_path, monkeypatch):
    from railway_detection.demo import server as dashboard_server

    monkeypatch.setattr(dashboard_server, "UPLOAD_TEMP_DIR", tmp_path)
    httpd = HTTPServer(("127.0.0.1", 0), DashboardHTTPRequestHandler)
    thread = Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    boundary = "endpoint-upload-boundary"
    file_bytes = b"small-video-fixture\x00\xff"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="video"; filename="fixture.mp4"\r\n'
        "Content-Type: video/mp4\r\n\r\n"
    ).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        f"http://127.0.0.1:{httpd.server_address[1]}/api/upload",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode("utf-8"))
            assert response.status == 200
        saved = Path(result["full_path"])
        assert result["filename"] == "fixture.mp4"
        assert result["size_bytes"] == len(file_bytes)
        assert saved.read_bytes() == file_bytes
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_dashboard_server_endpoints():
    """Verify that the dashboard server starts, responds on API endpoints, and serves status."""
    server = HTTPServer(("127.0.0.1", 0), DashboardHTTPRequestHandler)
    port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"

    try:
        # 1. Test GET /
        with urllib.request.urlopen(f"{base_url}/") as response:
            assert response.status == 200
            content = response.read().decode("utf-8")
            assert "<title>AI Railway Crossing Safety" in content

        # 2. Test GET /api/status
        with urllib.request.urlopen(f"{base_url}/api/status") as response:
            assert response.status == 200
            data = json.loads(response.read().decode("utf-8"))
            assert data["status"] == "online"
            assert "device_capabilities" in data
            assert data["canonical_classes"] == ["front", "rear", "side"]

        # 3. Test GET /api/benchmark
        with urllib.request.urlopen(f"{base_url}/api/benchmark") as response:
            assert response.status == 200
            data = json.loads(response.read().decode("utf-8"))
            assert data["run_id"] == "39f402dfe460"
            assert "metrics" in data

        # 4. Test GET /api/runs
        with urllib.request.urlopen(f"{base_url}/api/runs") as response:
            assert response.status == 200
            data = json.loads(response.read().decode("utf-8"))
            assert "runs" in data

    finally:
        server.shutdown()
        server.server_close()
