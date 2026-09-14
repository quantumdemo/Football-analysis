"""Tests for Vercel Serverless Python API Handler (api/index.py)."""

import json
from io import BytesIO
from api.index import handler


class MockSocket:
    def __init__(self, request_bytes):
        self.rfile = BytesIO(request_bytes)
        self.wfile = BytesIO()

    def makefile(self, mode, *args, **kwargs):
        if 'r' in mode:
            return self.rfile
        elif 'w' in mode:
            return self.wfile

    def sendall(self, data):
        self.wfile.write(data)


def test_api_health_get():
    request = b"GET /api/health HTTP/1.1\r\nHost: localhost\r\n\r\n"
    sock = MockSocket(request)
    h = handler(sock, ("127.0.0.1", 8000), None)
    sock.wfile.seek(0)
    response_text = sock.wfile.read().decode("utf-8")

    assert "200 OK" in response_text
    assert '"status": "HEALTHY"' in response_text
    assert '"version": "1.0.0"' in response_text


def test_api_status_get():
    request = b"GET /api/status HTTP/1.1\r\nHost: localhost\r\n\r\n"
    sock = MockSocket(request)
    h = handler(sock, ("127.0.0.1", 8000), None)
    sock.wfile.seek(0)
    response_text = sock.wfile.read().decode("utf-8")

    assert "200 OK" in response_text
    assert '"system_name": "FOOTBALL_AI_SYSTEM"' in response_text
    assert '"stages_completed": "Stages 0 through 25 PASS"' in response_text


def test_api_predict_post():
    payload = json.dumps({
        "raw_match": {
            "home_team_id": "TEAM_ARSENAL",
            "away_team_id": "TEAM_CHELSEA",
            "scheduled_time": "2025-05-10T15:00:00Z",
            "competition": "Premier League",
            "venue": "Emirates Stadium"
        },
        "raw_evidence": []
    }).encode("utf-8")

    headers = f"POST /api/predict HTTP/1.1\r\nHost: localhost\r\nContent-Length: {len(payload)}\r\n\r\n".encode("utf-8")
    request = headers + payload
    sock = MockSocket(request)
    h = handler(sock, ("127.0.0.1", 8000), None)
    sock.wfile.seek(0)
    response_text = sock.wfile.read().decode("utf-8")

    assert "200 OK" in response_text
    assert '"match_id"' in response_text


def test_api_cleanup_post():
    payload = json.dumps({"dry_run": True}).encode("utf-8")
    headers = f"POST /api/cleanup HTTP/1.1\r\nHost: localhost\r\nContent-Length: {len(payload)}\r\n\r\n".encode("utf-8")
    request = headers + payload
    sock = MockSocket(request)
    h = handler(sock, ("127.0.0.1", 8000), None)
    sock.wfile.seek(0)
    response_text = sock.wfile.read().decode("utf-8")

    assert "200 OK" in response_text
    assert '"status": "SUCCESS"' in response_text
    assert '"cleanup_logs"' in response_text
