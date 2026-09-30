from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_validator(config_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "validate_dashboard.py"),
            "--config",
            str(config_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_repository_dashboard_contract_is_valid() -> None:
    result = run_validator(REPO_ROOT / "config" / "dashboard.yaml")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "6/6 panel" in result.stdout


def test_retrieval_success_uses_success_and_failure_events() -> None:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8")
    )
    errors_panel = next(
        panel for panel in payload["dashboard"]["panels"] if panel["id"] == "errors"
    )

    assert "response_sent" in errors_panel["events"]
    assert "request_failed" in errors_panel["events"]
    assert "tool_success == true" in errors_panel["query"]
    assert "tool_success != null" in errors_panel["query"]


def test_slo_and_alert_rules_are_concrete() -> None:
    slo = yaml.safe_load((REPO_ROOT / "config" / "slo.yaml").read_text(encoding="utf-8"))
    alerts = yaml.safe_load(
        (REPO_ROOT / "config" / "alert_rules.yaml").read_text(encoding="utf-8")
    )["alerts"]

    assert slo["primary_slo"]["target_percent"] == 99.5
    assert slo["primary_slo"]["error_budget_example_allowed"] == 50
    assert len(alerts) == 3
    for alert in alerts:
        assert alert["type"] == "symptom-based"
        assert alert["condition"] != "TODO"
        assert alert["duration"]
        assert alert["owner"]
        assert alert["channel"].startswith("#")
        assert "TODO" not in alert["name"]


def test_validator_rejects_panel_without_threshold(tmp_path: Path) -> None:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8")
    )
    del payload["dashboard"]["panels"][0]["threshold"]
    invalid_config = tmp_path / "dashboard.yaml"
    invalid_config.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    result = run_validator(invalid_config)

    assert result.returncode == 1
    assert "latency.threshold" in result.stdout


def test_validator_rejects_panel_without_query_example(tmp_path: Path) -> None:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8")
    )
    payload["dashboard"]["panels"][0].pop("query", None)
    invalid_config = tmp_path / "dashboard.yaml"
    invalid_config.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    result = run_validator(invalid_config)

    assert result.returncode == 1
    assert "latency.query" in result.stdout
