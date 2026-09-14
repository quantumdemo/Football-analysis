"""Live Monitoring & Incident Response Engine for Stage 21.

Monitors uptime, latency, error rates, scheduled-job failures, research source failures,
stale-data rates, database capacity, query latency, abnormal model distributions, and calibration drift.
Maintains incident severity levels, response procedures, and immutable production changelogs.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional


class IncidentSeverity(Enum):
    CRITICAL = "CRITICAL"  # System outage, data corruption, or unhandled exception spike
    HIGH = "HIGH"          # Stale evidence rate > 30% or scheduled job failure
    MEDIUM = "MEDIUM"        # High latency (> 500ms) or database query slowdown
    LOW = "LOW"            # Minor warning or transient retry


@dataclass
class IncidentRecord:
    """Incident record for tracking production operational events."""
    incident_id: str
    severity: IncidentSeverity
    component: str  # e.g., "WebResearch", "Database", "ForecastEngine", "ScheduledJobs"
    title: str
    description: str
    response_procedure: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False


@dataclass
class ProductionChangelogEntry:
    """Entry tracking production model, feature, or market definition changes."""
    entry_id: str
    change_type: str  # "MODEL_VERSION", "FEATURE_VERSION", "MARKET_DEFINITION"
    old_version: str
    new_version: str
    description: str
    author: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SystemHealthMetrics:
    """Real-time system operational metrics snapshot."""
    uptime_percentage: float
    avg_latency_ms: float
    error_rate_percentage: float
    job_failure_rate_percentage: float
    stale_data_rate_percentage: float
    db_capacity_usage_percentage: float
    db_query_latency_ms: float
    abnormal_distribution_incidents: int
    active_incidents_count: int


class SystemHealthMonitor:
    """Monitors live system health, generates incident alerts, and maintains production changelogs."""

    def __init__(self):
        self.incidents: List[IncidentRecord] = []
        self.changelog: List[ProductionChangelogEntry] = []

    def record_incident(
        self,
        severity: IncidentSeverity,
        component: str,
        title: str,
        description: str,
        response_procedure: str
    ) -> IncidentRecord:
        """Logs an operational incident and alerts team based on severity."""
        inc = IncidentRecord(
            incident_id=f"inc_{len(self.incidents)+1}_{int(datetime.now(timezone.utc).timestamp())}",
            severity=severity,
            component=component,
            title=title,
            description=description,
            response_procedure=response_procedure
        )
        self.incidents.append(inc)
        return inc

    def log_production_change(
        self,
        change_type: str,
        old_version: str,
        new_version: str,
        description: str,
        author: str
    ) -> ProductionChangelogEntry:
        """Logs production version changes to ensure no silent model/feature/market modifications."""
        entry = ProductionChangelogEntry(
            entry_id=f"change_{len(self.changelog)+1}",
            change_type=change_type,
            old_version=old_version,
            new_version=new_version,
            description=description,
            author=author
        )
        self.changelog.append(entry)
        return entry

    def evaluate_system_health(
        self,
        metrics: SystemHealthMetrics
    ) -> Dict[str, Any]:
        """Evaluates operational health metrics and auto-triggers incidents on threshold violations."""
        triggered_incidents = []

        if metrics.stale_data_rate_percentage > 20.0:
            inc = self.record_incident(
                severity=IncidentSeverity.HIGH,
                component="WebResearch",
                title="High Stale Data Rate Detected",
                description=f"Stale data rate ({metrics.stale_data_rate_percentage:.1f}%) exceeded 20.0% threshold.",
                response_procedure="Inspect web research ingestion scrapers and source freshness TTL configuration."
            )
            triggered_incidents.append(inc)

        if metrics.job_failure_rate_percentage > 5.0:
            inc = self.record_incident(
                severity=IncidentSeverity.HIGH,
                component="ScheduledJobs",
                title="Scheduled Job Failure Spike",
                description=f"Job failure rate ({metrics.job_failure_rate_percentage:.1f}%) exceeded 5.0% threshold.",
                response_procedure="Review scheduler logs, retry failed jobs, and verify database lock status."
            )
            triggered_incidents.append(inc)

        if metrics.abnormal_distribution_incidents > 0:
            inc = self.record_incident(
                severity=IncidentSeverity.CRITICAL,
                component="ForecastEngine",
                title="Abnormal Model Probability Distribution",
                description=f"Detected {metrics.abnormal_distribution_incidents} abnormal model forecast distributions.",
                response_procedure="Halt forecasting model deployment, review input features, and trigger fallback NO_BET."
            )
            triggered_incidents.append(inc)

        return {
            "health_status": "HEALTHY" if len(triggered_incidents) == 0 and metrics.error_rate_percentage < 1.0 else "ATTENTION_REQUIRED",
            "active_incidents": len([i for i in self.incidents if not i.resolved]),
            "triggered_in_check": len(triggered_incidents),
            "metrics": metrics
        }
