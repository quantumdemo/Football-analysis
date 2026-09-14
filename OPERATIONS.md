# PRODUCTION OPERATIONS MANUAL

## 1. SYSTEM MONITORING & HEALTH CHECKS
Production operational health is monitored via `SystemHealthMonitor` (`src/reporting/monitoring.py`).

### Health Metrics Monitored

| Metric Name | Normal Threshold | Critical Threshold | Action Required |
|-------------|------------------|--------------------|-----------------|
| `uptime_pct` | > 99.5% | < 98.0% | Inspect host server / process manager |
| `p95_latency_ms` | < 1,500 ms | > 5,000 ms | Scale DB read replicas / optimize features |
| `error_rate_pct` | < 1.0% | > 5.0% | Inspect error logs / failover to NO_BET |
| `job_failure_rate_pct` | < 2.0% | > 10.0% | Restart `ScheduledJobRunner` service |
| `stale_data_rate_pct` | < 5.0% | > 15.0% | Trigger research source health audit |
| `db_capacity_pct` | < 70.0% | > 85.0% | Trigger 6-hr cleanup / upgrade DB tier |
| `abnormal_dist_flag` | `False` | `True` | Halt automated predictions for review |

---

## 2. INCIDENT SEVERITY CLASSIFICATION & PROTOCOL

When operational anomalies occur, incidents are classified into 4 severity levels:

### `CRITICAL` Severity
- **Triggers**: Database outage, >5% system error rate, abnormal deletion volume, or prediction distribution breach.
- **Action**: Immediate automated fallback to `NO_BET / INSUFFICIENT EVIDENCE`. On-call engineering alert.

### `HIGH` Severity
- **Triggers**: Latency >5s, research source API failure, or rate limit threshold breach.
- **Action**: Switch to backup research providers and enable fallback cache mode.

### `MEDIUM` Severity
- **Triggers**: Minor job retries or stale research data rate between 5% and 15%.
- **Action**: Schedule research collector review in next operational cycle.

### `LOW` Severity
- **Triggers**: Minor logging warning or transient network retry.
- **Action**: Logged for routine inspection.

---

## 3. CLEANUP JOB MONITORING (`RetentionJobLog`)

Every execution of the 6-hour research cache cleanup emits a structured `RetentionJobLog` record:

```json
{
  "job_id": "CLEANUP_research_cache_1710000000",
  "started_at": "2025-03-10T00:00:00Z",
  "finished_at": "2025-03-10T00:00:02Z",
  "status": "SUCCESS",
  "dry_run": false,
  "records_examined": 1250,
  "records_deleted": 850,
  "records_skipped": 400,
  "errors": [],
  "duration_ms": 2150.5
}
```

### Abnormal Deletion Safeguards
If `status` equals `STOPPED_SAFETY_LIMIT`:
1. The cleanup engine automatically halted to prevent accidental deletion (>5,000 records or >50% ratio).
2. Permanent data (`predictions`, `matches`, `match_outcomes`) is guaranteed intact.
3. Review `errors` field in `RetentionJobLog` and run cleanup with `dry_run=True` to inspect pending deletions.

---

## 4. CONTROLLED MODEL LIFECYCLE & UPDATE PROTOCOL

Model updates MUST follow the controlled lifecycle enforced by `ControlledModelLifecycleManager` (`src/models/model_lifecycle.py`):

```
PROPOSE ➔ DEVELOP ➔ BACKTEST ➔ CALIBRATE ➔ SHADOW TEST ➔ REVIEW ➔ APPROVE ➔ DEPLOY ➔ MONITOR
```

### Rollback Protocol
If a newly deployed model exhibits calibration drift or abnormal outcome distributions in live production:
```python
from src.models.model_lifecycle import ControlledModelLifecycleManager

lifecycle = ControlledModelLifecycleManager()
lifecycle.rollback_model(target_version="v1.0.0", reason="Live calibration drift detected")
```

---

## 5. DISASTER RECOVERY & EMERGENCY RESTORATION

1. **Database Corruption / Outage**:
   - Restore database snapshot from Supabase automated backups.
   - Execute `ProductionDatabaseRepository.restore_database(snapshot)`.
2. **Research Service Outage**:
   - System automatically falls back to `NO_BET / INSUFFICIENT EVIDENCE` decisions without making unevidenced assumptions.
