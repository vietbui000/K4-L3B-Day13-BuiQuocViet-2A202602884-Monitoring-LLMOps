from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml
import pytest

from scripts.dashboard import build_dashboard_payload


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_metrics_use_jsonl_events_in_the_60_minute_window() -> None:
    dashboard = yaml.safe_load(
        (REPO_ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8")
    )["dashboard"]
    now = datetime(2026, 9, 30, 10, 0, tzinfo=timezone.utc)
    records = [
        {"ts": "2026-09-30T09:59:00Z", "event": "request_received"},
        {
            "ts": "2026-09-30T09:59:05Z",
            "event": "response_sent",
            "latency_ms": 1200,
            "ttft_ms": 50,
            "cost_usd": 0.001,
            "tokens_in": 20,
            "tokens_out": 80,
            "quality_score": 0.8,
            "tool_success": True,
        },
        {"ts": "2026-09-30T09:58:00Z", "event": "request_received"},
        {
            "ts": "2026-09-30T09:58:05Z",
            "event": "request_failed",
            "tool_success": False,
        },
        {"ts": "2026-09-30T09:00:00Z", "event": "request_received"},
        {"ts": "2026-09-30T08:59:00Z", "event": "request_received"},
    ]

    payload = build_dashboard_payload(records, dashboard, now=now)

    assert payload["records"] == 5
    assert len(payload["series"]) == 61
    summary = payload["summary"]
    assert summary["requests"] == 3
    assert summary["latencyP95"] == 1200
    assert summary["errorRatePct"] == pytest.approx(100 / 3)
    assert summary["retrievalSuccessPct"] == 50
    assert summary["totalCostUsd"] == 0.001
    assert summary["totalTokens"] == 100
    assert summary["qualityMean"] == 0.8