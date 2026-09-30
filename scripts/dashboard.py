from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
CONFIG_PATH = REPO_ROOT / "config" / "dashboard.yaml"

HTML_PAGE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>Day 13 | LLMOps Monitor</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #18332d;
      --muted: #61736d;
      --line: #d9e2dc;
      --paper: #f0f4f0;
      --panel: #ffffff;
      --green: #087e68;
      --blue: #3979a8;
      --orange: #c9652e;
      --red: #bd4b47;
      --gold: #a87b18;
      --shadow: 0 8px 26px rgba(29, 58, 47, .06);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: "Trebuchet MS", "Segoe UI", sans-serif;
      font-size: 14px;
    }
    .shell { max-width: 1440px; margin: 0 auto; padding: 28px 32px 40px; }
    header {
      display: flex; align-items: center; justify-content: space-between; gap: 20px;
      padding-bottom: 22px; border-bottom: 1px solid var(--line);
    }
    .eyebrow { color: var(--green); font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.1px; }
    h1 { margin: 6px 0 0; font-size: 27px; line-height: 1.15; font-weight: 700; }
    .subline { margin-top: 7px; color: var(--muted); font-size: 13px; }
    .actions { display: flex; align-items: center; gap: 14px; }
    #updated { color: var(--muted); font-size: 12px; white-space: nowrap; }
    button {
      border: 0; border-radius: 5px; background: var(--ink); color: white;
      font: inherit; font-weight: 700; padding: 10px 14px; cursor: pointer;
    }
    button:hover { background: var(--green); }
    button:focus-visible { outline: 3px solid #73baa9; outline-offset: 2px; }
    .stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }
    .stat {
      min-height: 92px; padding: 15px 17px; background: var(--panel);
      border: 1px solid var(--line); border-radius: 6px; box-shadow: var(--shadow);
    }
    .stat-label { color: var(--muted); font-size: 12px; font-weight: 700; }
    .stat-value { margin-top: 8px; font: 700 25px/1.05 "Consolas", "Courier New", monospace; }
    .stat-note { margin-top: 6px; color: var(--muted); font-size: 11px; }
    .panel-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .panel {
      min-width: 0; padding: 17px 18px 12px; background: var(--panel);
      border: 1px solid var(--line); border-radius: 6px; box-shadow: var(--shadow);
      animation: arrive .35s both;
    }
    .panel:nth-child(2) { animation-delay: .04s; }
    .panel:nth-child(3) { animation-delay: .08s; }
    .panel:nth-child(4) { animation-delay: .12s; }
    .panel:nth-child(5) { animation-delay: .16s; }
    .panel:nth-child(6) { animation-delay: .2s; }
    .panel-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
    .panel h2 { margin: 0; font-size: 15px; line-height: 1.3; }
    .unit { margin-top: 4px; color: var(--muted); font-size: 11px; }
    .metric { color: var(--ink); font: 700 12px "Consolas", "Courier New", monospace; text-align: right; white-space: nowrap; }
    .chart-wrap { position: relative; height: 205px; margin-top: 12px; }
    canvas { width: 100%; height: 100%; display: block; }
    .legend { display: flex; flex-wrap: wrap; gap: 8px 14px; min-height: 19px; padding-top: 5px; }
    .legend-item { display: inline-flex; align-items: center; gap: 6px; color: var(--muted); font-size: 11px; }
    .legend-mark { width: 14px; height: 3px; border-radius: 3px; }
    .foot { display: flex; justify-content: space-between; gap: 10px; margin-top: 18px; color: var(--muted); font-size: 11px; }
    .empty { color: var(--muted); }
    @keyframes arrive { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
    @media (max-width: 760px) {
      .shell { padding: 20px 16px 28px; }
      header { align-items: flex-start; }
      h1 { font-size: 22px; }
      .actions { align-items: flex-end; flex-direction: column-reverse; gap: 8px; }
      .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; }
      .stat { min-height: 83px; padding: 12px; }
      .stat-value { font-size: 21px; }
      .panel-grid { grid-template-columns: 1fr; }
      .chart-wrap { height: 190px; }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div>
        <div class="eyebrow">K4-L3B / Service telemetry</div>
        <h1>LLMOps Monitor</h1>
        <div class="subline">Rolling 60 minutes <span aria-hidden="true">·</span> UTC <span aria-hidden="true">·</span> data/logs.jsonl</div>
      </div>
      <div class="actions">
        <span id="updated" role="status">Loading log data...</span>
        <button id="refresh" type="button" title="Refresh dashboard data">Refresh now</button>
      </div>
    </header>
    <section class="stats" aria-label="Current service summary">
      <div class="stat"><div class="stat-label">Requests / 60m</div><div class="stat-value" id="stat-requests">--</div><div class="stat-note">From request_received events</div></div>
      <div class="stat"><div class="stat-label">Latency P95</div><div class="stat-value" id="stat-latency">--</div><div class="stat-note">Target at or below 3000 ms</div></div>
      <div class="stat"><div class="stat-label">Request errors</div><div class="stat-value" id="stat-errors">--</div><div class="stat-note">Guardrail at or below 2%</div></div>
      <div class="stat"><div class="stat-label">Retrieval success</div><div class="stat-value" id="stat-retrieval">--</div><div class="stat-note">Target at or above 90%</div></div>
    </section>
    <section class="panel-grid" aria-label="Six monitoring panels">
      <article class="panel" data-panel="latency"><div class="panel-head"><div><h2>Latency percentiles and TTFT</h2><div class="unit">Milliseconds</div></div><div class="metric" id="metric-latency">--</div></div><div class="chart-wrap"><canvas aria-label="Latency chart"></canvas></div><div class="legend"></div></article>
      <article class="panel" data-panel="traffic"><div class="panel-head"><div><h2>Request traffic</h2><div class="unit">Requests per minute</div></div><div class="metric" id="metric-traffic">--</div></div><div class="chart-wrap"><canvas aria-label="Traffic chart"></canvas></div><div class="legend"></div></article>
      <article class="panel" data-panel="errors"><div class="panel-head"><div><h2>Error rate and retrieval success</h2><div class="unit">Percent</div></div><div class="metric" id="metric-errors">--</div></div><div class="chart-wrap"><canvas aria-label="Error and retrieval chart"></canvas></div><div class="legend"></div></article>
      <article class="panel" data-panel="cost"><div class="panel-head"><div><h2>Cost over time</h2><div class="unit">Cumulative USD</div></div><div class="metric" id="metric-cost">--</div></div><div class="chart-wrap"><canvas aria-label="Cost chart"></canvas></div><div class="legend"></div></article>
      <article class="panel" data-panel="tokens"><div class="panel-head"><div><h2>Input and output tokens</h2><div class="unit">Cumulative tokens</div></div><div class="metric" id="metric-tokens">--</div></div><div class="chart-wrap"><canvas aria-label="Token chart"></canvas></div><div class="legend"></div></article>
      <article class="panel" data-panel="quality"><div class="panel-head"><div><h2>Quality proxy</h2><div class="unit">Score from 0 to 1</div></div><div class="metric" id="metric-quality">--</div></div><div class="chart-wrap"><canvas aria-label="Quality chart"></canvas></div><div class="legend"></div></article>
    </section>
    <footer class="foot"><span id="record-count">No records loaded</span><span>Refresh interval: 30 seconds</span></footer>
  </main>
  <script>
    const colors = { green: "#087e68", blue: "#3979a8", orange: "#c9652e", red: "#bd4b47", gold: "#a87b18" };
    const definitions = {
      latency: [{ key: "latencyP50", label: "P50", color: colors.green }, { key: "latencyP95", label: "P95", color: colors.orange }, { key: "latencyP99", label: "P99", color: colors.red }, { key: "ttftP95", label: "TTFT P95", color: colors.blue }],
      traffic: [{ key: "traffic", label: "Requests / min", color: colors.green }],
      errors: [{ key: "errorRatePct", label: "Error rate", color: colors.red }, { key: "retrievalSuccessPct", label: "Retrieval success", color: colors.blue }],
      cost: [{ key: "cumulativeCostUsd", label: "Total cost", color: colors.orange }],
      tokens: [{ key: "cumulativeTokensIn", label: "Input", color: colors.blue }, { key: "cumulativeTokensOut", label: "Output", color: colors.green }],
      quality: [{ key: "qualityMean", label: "Mean score", color: colors.gold }]
    };
    const thresholdKeys = { p50: "latencyP50", p95: "latencyP95", p99: "latencyP99", ttft_p95: "ttftP95", rate_per_minute: "traffic", error_rate_pct: "errorRatePct", tool_success_rate_pct: "retrievalSuccessPct", total: "cumulativeCostUsd", sum_by_field: "cumulativeTokensTotal", mean: "qualityMean" };
    const format = (value, digits = 1) => value == null || !Number.isFinite(value) ? "n/a" : Number(value).toFixed(digits);
    const configById = (payload, id) => payload.panels.find((panel) => panel.id === id);

    function thresholdsFor(panel) {
      return [panel.threshold, ...(panel.additional_thresholds || [])].map((item) => ({
        key: thresholdKeys[item.aggregation], value: item.value, operator: item.operator
      })).filter((item) => item.key);
    }

    function drawChart(canvas, rows, lines, thresholdLines) {
      const rect = canvas.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.floor(rect.width * ratio));
      canvas.height = Math.max(1, Math.floor(rect.height * ratio));
      const ctx = canvas.getContext("2d");
      ctx.scale(ratio, ratio);
      const width = rect.width, height = rect.height;
      const pad = { left: 43, right: 9, top: 10, bottom: 25 };
      const plotW = width - pad.left - pad.right, plotH = height - pad.top - pad.bottom;
      const values = lines.flatMap((line) => rows.map((row) => row[line.key]).filter(Number.isFinite));
      const limits = thresholdLines.map((line) => line.value).filter(Number.isFinite);
      let min = 0, max = Math.max(1, ...values, ...limits);
      if (lines.length === 1 && lines[0].key === "qualityMean") max = Math.max(1, max);
      if (max <= 1 && lines.some((line) => line.key === "qualityMean")) max = 1;
      max *= 1.08;
      const y = (value) => pad.top + plotH - ((value - min) / (max - min || 1)) * plotH;
      const x = (index) => pad.left + (rows.length < 2 ? plotW / 2 : index * plotW / (rows.length - 1));
      ctx.clearRect(0, 0, width, height);
      ctx.font = "10px Trebuchet MS, sans-serif";
      ctx.textBaseline = "middle";
      for (let tick = 0; tick <= 4; tick += 1) {
        const value = max * tick / 4, py = y(value);
        ctx.strokeStyle = "#e5ebe6"; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(pad.left, py); ctx.lineTo(width - pad.right, py); ctx.stroke();
        ctx.fillStyle = "#718078";
        ctx.textAlign = "right";
        ctx.fillText(value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value.toFixed(value < 10 ? 1 : 0), pad.left - 7, py);
      }
      thresholdLines.forEach((line) => {
        if (!Number.isFinite(line.value)) return;
        const py = y(line.value);
        ctx.save(); ctx.setLineDash([5, 4]); ctx.strokeStyle = line.operator === "gte" ? colors.blue : colors.red;
        ctx.beginPath(); ctx.moveTo(pad.left, py); ctx.lineTo(width - pad.right, py); ctx.stroke(); ctx.restore();
      });
      lines.forEach((line) => {
        ctx.strokeStyle = line.color; ctx.lineWidth = 2; ctx.lineJoin = "round"; ctx.lineCap = "round";
        ctx.beginPath(); let started = false;
        rows.forEach((row, index) => {
          const value = row[line.key];
          if (!Number.isFinite(value)) { started = false; return; }
          if (!started) { ctx.moveTo(x(index), y(value)); started = true; }
          else ctx.lineTo(x(index), y(value));
        });
        ctx.stroke();
      });
      ctx.fillStyle = "#718078"; ctx.textAlign = "center"; ctx.textBaseline = "top";
      [0, 15, 30, 45, 59].forEach((index) => {
        if (rows[index]) ctx.fillText(rows[index].minute.slice(11, 16), x(index), height - pad.bottom + 7);
      });
    }

    function updatePanel(panel, payload) {
      const id = panel.dataset.panel;
      const config = configById(payload, id);
      const lines = definitions[id];
      const thresholds = thresholdsFor(config);
      const legend = panel.querySelector(".legend");
      legend.replaceChildren();
      [...lines.map((line) => ({ label: line.label, color: line.color })), ...thresholds.map((line) => ({ label: `Threshold ${line.operator === "gte" ? "≥" : "≤"} ${line.value}`, color: line.operator === "gte" ? colors.blue : colors.red }))].forEach((item) => {
        const label = document.createElement("span"); label.className = "legend-item";
        const mark = document.createElement("span"); mark.className = "legend-mark"; mark.style.background = item.color;
        label.append(mark, document.createTextNode(item.label)); legend.append(label);
      });
      drawChart(panel.querySelector("canvas"), payload.series, lines, thresholds);
    }

    function updateStats(payload) {
      const summary = payload.summary;
      document.getElementById("stat-requests").textContent = summary.requests;
      document.getElementById("stat-latency").textContent = `${format(summary.latencyP95, 0)} ms`;
      document.getElementById("stat-errors").textContent = `${format(summary.errorRatePct)}%`;
      document.getElementById("stat-retrieval").textContent = `${format(summary.retrievalSuccessPct)}%`;
      document.getElementById("metric-latency").textContent = `P95 ${format(summary.latencyP95, 0)} ms`;
      document.getElementById("metric-traffic").textContent = `${summary.requests} requests`;
      document.getElementById("metric-errors").textContent = `${format(summary.errorRatePct)}% errors · ${format(summary.retrievalSuccessPct)}% retrieval`;
      document.getElementById("metric-cost").textContent = `$${format(summary.totalCostUsd, 4)}`;
      document.getElementById("metric-tokens").textContent = `${summary.totalTokens.toLocaleString()} total`;
      document.getElementById("metric-quality").textContent = format(summary.qualityMean, 2);
      document.getElementById("record-count").textContent = `${payload.records} valid log records in rolling window`;
      document.getElementById("updated").textContent = `Updated ${new Date(payload.generatedAt).toLocaleTimeString()}`;
    }

    async function refresh() {
      const updated = document.getElementById("updated");
      try {
        const response = await fetch("/api/dashboard", { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        updateStats(payload);
        document.querySelectorAll(".panel").forEach((panel) => updatePanel(panel, payload));
      } catch (error) {
        updated.textContent = `Unable to load logs: ${error.message}`;
      }
    }
    document.getElementById("refresh").addEventListener("click", refresh);
    window.addEventListener("resize", refresh);
    refresh();
    setInterval(refresh, 30000);
  </script>
</body>
</html>
"""


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def build_dashboard_payload(
    records: list[dict[str, Any]],
    dashboard: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    window_minutes = dashboard["time_range_minutes"]
    start = now - timedelta(minutes=window_minutes)
    filtered: list[tuple[datetime, dict[str, Any]]] = []
    for record in records:
        timestamp = _parse_timestamp(record.get("ts"))
        if timestamp is not None and start <= timestamp <= now:
            filtered.append((timestamp, record))

    current_minute = now.replace(second=0, microsecond=0)
    first_minute = start.replace(second=0, microsecond=0)
    minute_count = int((current_minute - first_minute).total_seconds() // 60) + 1
    minute_starts = [
      first_minute + timedelta(minutes=index) for index in range(minute_count)
    ]
    by_minute: dict[datetime, list[dict[str, Any]]] = {minute: [] for minute in minute_starts}
    for timestamp, record in filtered:
        minute = timestamp.replace(second=0, microsecond=0)
        if minute in by_minute:
            by_minute[minute].append(record)

    series: list[dict[str, Any]] = []
    cumulative_cost = 0.0
    cumulative_tokens_in = 0
    cumulative_tokens_out = 0
    for minute in minute_starts:
        minute_records = by_minute[minute]
        responses = [record for record in minute_records if record.get("event") == "response_sent"]
        requests = [record for record in minute_records if record.get("event") == "request_received"]
        failures = [record for record in minute_records if record.get("event") == "request_failed"]
        tool_results = [record.get("tool_success") for record in minute_records if record.get("tool_success") is not None]
        latencies = [value for record in responses if (value := _number(record.get("latency_ms"))) is not None]
        ttfts = [value for record in responses if (value := _number(record.get("ttft_ms"))) is not None]
        costs = [value for record in responses if (value := _number(record.get("cost_usd"))) is not None]
        input_tokens = sum(int(value) for record in responses if (value := _number(record.get("tokens_in"))) is not None)
        output_tokens = sum(int(value) for record in responses if (value := _number(record.get("tokens_out"))) is not None)
        quality = [value for record in responses if (value := _number(record.get("quality_score"))) is not None]
        cumulative_cost += sum(costs)
        cumulative_tokens_in += input_tokens
        cumulative_tokens_out += output_tokens
        series.append(
            {
                "minute": minute.isoformat(),
                "latencyP50": _percentile(latencies, 50),
                "latencyP95": _percentile(latencies, 95),
                "latencyP99": _percentile(latencies, 99),
                "ttftP95": _percentile(ttfts, 95),
                "traffic": len(requests),
                "errorRatePct": len(failures) / len(requests) * 100 if requests else None,
                "retrievalSuccessPct": (
                    sum(result is True for result in tool_results) / len(tool_results) * 100
                    if tool_results else None
                ),
                "cumulativeCostUsd": cumulative_cost,
                "cumulativeTokensIn": cumulative_tokens_in,
                "cumulativeTokensOut": cumulative_tokens_out,
                "cumulativeTokensTotal": cumulative_tokens_in + cumulative_tokens_out,
                "qualityMean": sum(quality) / len(quality) if quality else None,
            }
        )

    in_window = [record for _, record in filtered]
    requests = [record for record in in_window if record.get("event") == "request_received"]
    failures = [record for record in in_window if record.get("event") == "request_failed"]
    responses = [record for record in in_window if record.get("event") == "response_sent"]
    tool_results = [record.get("tool_success") for record in in_window if record.get("tool_success") is not None]
    latencies = [value for record in responses if (value := _number(record.get("latency_ms"))) is not None]
    qualities = [value for record in responses if (value := _number(record.get("quality_score"))) is not None]
    total_cost = sum(value for record in responses if (value := _number(record.get("cost_usd"))) is not None)
    total_tokens_in = sum(int(value) for record in responses if (value := _number(record.get("tokens_in"))) is not None)
    total_tokens_out = sum(int(value) for record in responses if (value := _number(record.get("tokens_out"))) is not None)
    panels = dashboard["panels"]

    return {
        "generatedAt": now.isoformat(),
        "windowMinutes": window_minutes,
        "refreshSeconds": dashboard["refresh_seconds"],
        "records": len(in_window),
        "panels": panels,
        "series": series,
        "summary": {
            "requests": len(requests),
            "latencyP95": _percentile(latencies, 95),
            "errorRatePct": len(failures) / len(requests) * 100 if requests else 0.0,
            "retrievalSuccessPct": (
                sum(result is True for result in tool_results) / len(tool_results) * 100
                if tool_results else None
            ),
            "totalCostUsd": total_cost,
            "totalTokens": total_tokens_in + total_tokens_out,
            "qualityMean": sum(qualities) / len(qualities) if qualities else None,
        },
    }


def read_log_records(path: Path = LOG_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/":
            content = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif self.path == "/api/dashboard":
            config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["dashboard"]
            payload = build_dashboard_payload(read_log_records(), config)
            content = json.dumps(payload, allow_nan=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
        else:
            self.send_error(404)
            return
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Local dashboard for Day 13 JSONL logs")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Dashboard ready at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()