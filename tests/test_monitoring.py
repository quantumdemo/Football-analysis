"""Unit tests for Stage 21 Live Monitoring & Incident Response Engine."""

import pytest
from src.reporting.monitoring import SystemHealthMonitor, IncidentSeverity, SystemHealthMetrics, IncidentRecord, ProductionChangelogEntry


@pytest.fixture
def monitor():
    return SystemHealthMonitor()


def test_record_incident(monitor):
    inc = monitor.record_incident(
        severity=IncidentSeverity.CRITICAL,
        component="Database",
        title="DB Query High Latency",
        description="Database query latency exceeded 1000ms threshold.",
        response_procedure="Check connection pool and query execution plans."
    )

    assert isinstance(inc, IncidentRecord)
    assert inc.severity == IncidentSeverity.CRITICAL
    assert inc.resolved is False
    assert len(monitor.incidents) == 1


def test_log_production_change(monitor):
    entry = monitor.log_production_change(
        change_type="MODEL_VERSION",
        old_version="v1.0.0",
        new_version="v1.0.1",
        description="Re-calibrated temperature scaling parameter.",
        author="lead_engineer"
    )

    assert isinstance(entry, ProductionChangelogEntry)
    assert entry.change_type == "MODEL_VERSION"
    assert entry.new_version == "v1.0.1"
    assert len(monitor.changelog) == 1


def test_evaluate_system_health_healthy(monitor):
    metrics = SystemHealthMetrics(
        uptime_percentage=99.9,
        avg_latency_ms=120.0,
        error_rate_percentage=0.1,
        job_failure_rate_percentage=0.0,
        stale_data_rate_percentage=5.0,
        db_capacity_usage_percentage=35.0,
        db_query_latency_ms=15.0,
        abnormal_distribution_incidents=0,
        active_incidents_count=0
    )

    eval_result = monitor.evaluate_system_health(metrics)
    assert eval_result["health_status"] == "HEALTHY"
    assert eval_result["triggered_in_check"] == 0


def test_evaluate_system_health_triggers_incidents(monitor):
    metrics = SystemHealthMetrics(
        uptime_percentage=98.5,
        avg_latency_ms=450.0,
        error_rate_percentage=1.5,
        job_failure_rate_percentage=8.0,  # Spikes > 5.0%
        stale_data_rate_percentage=25.0,   # Spikes > 20.0%
        db_capacity_usage_percentage=75.0,
        db_query_latency_ms=120.0,
        abnormal_distribution_incidents=1, # Critical > 0
        active_incidents_count=0
    )

    eval_result = monitor.evaluate_system_health(metrics)
    assert eval_result["health_status"] == "ATTENTION_REQUIRED"
    assert eval_result["triggered_in_check"] == 3
    assert len(monitor.incidents) == 3
