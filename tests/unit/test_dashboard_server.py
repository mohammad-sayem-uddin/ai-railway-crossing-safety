"""Unit tests for the Dashboard Web Server and API endpoints."""

from __future__ import annotations

import json
import urllib.request
from http.server import HTTPServer
from threading import Thread

from railway_detection.demo.server import DashboardHTTPRequestHandler


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
