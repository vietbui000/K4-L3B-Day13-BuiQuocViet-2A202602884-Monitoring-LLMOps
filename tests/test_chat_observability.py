from __future__ import annotations

import json
import asyncio
import re
from pathlib import Path

import httpx

from app import logging_config
from app.main import app


def test_middleware_generates_request_id_when_missing() -> None:
    async def get_health() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.get("/health")

    response = asyncio.run(get_health())

    assert response.status_code == 200
    assert re.fullmatch(r"req-[0-9a-f]{8}", response.headers["x-request-id"])
    assert float(response.headers["x-response-time-ms"]) >= 0


def test_chat_response_log_exposes_quality_for_dashboard(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.post(
                "/chat",
                json={
                    "user_id": "student-01",
                    "session_id": "session-01",
                    "feature": "qa",
                    "message": "Contact a@b.vn 0901234567 001099012345 4111 1111 1111 1111",
                },
                headers={"x-request-id": "req-1a2b3c4d"},
            )

    response = asyncio.run(send_request())

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-1a2b3c4d"
    assert float(response.headers["x-response-time-ms"]) >= 0
    assert response.json()["correlation_id"] == "req-1a2b3c4d"
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    response_event = next(event for event in events if event["event"] == "response_sent")
    request_event = next(event for event in events if event["event"] == "request_received")
    assert response_event["quality_score"] == response.json()["quality_score"]
    assert response_event["ttft_ms"] == response.json()["ttft_ms"]
    assert response_event["tool_name"] == "retrieval"
    assert response_event["tool_success"] is True
    for event in (request_event, response_event):
        assert event["correlation_id"] == "req-1a2b3c4d"
        assert event["user_id_hash"] != "student-01"
        assert event["session_id"] == "session-01"
        assert event["feature"] == "qa"
        assert event["model"] == "claude-sonnet-4-5"
        assert event["env"]

    serialized_logs = log_path.read_text(encoding="utf-8")
    for raw_pii in ("a@b.vn", "0901234567", "001099012345", "4111 1111 1111 1111"):
        assert raw_pii not in serialized_logs
