# 18. 6-HOUR DATABASE RESEARCH RETENTION & CLEANUP SPECIFICATION

## 1. OBJECTIVE & OVERVIEW
This specification defines the automated 6-hour database retention and cleanup system for the Football AI Intelligence System.
The primary goal is to manage database storage growth and maintain long-term capacity by automatically removing temporary prediction-research data every 6 hours, while strictly protecting all permanent predictions, historical outcomes, calibration data, and audit trails required for backtesting and model evaluation.

---

## 2. DATABASE CLASSIFICATION MATRIX

All database tables and collections are classified into 6 retention categories. No cleanup operation may run on a table unless its retention policy is explicitly defined.

| Table / Collection | Retention Classification | Retention Policy | Purge Interval |
|--------------------|-------------------------|------------------|----------------|
| `research_cache` | `CACHE` / `SHORT_TERM` | Delete expired records | 6 Hours |
| `web_research_raw` | `CACHE` | Delete expired records | 6 Hours |
| `extracted_articles_cache` | `CACHE` | Delete expired records | 6 Hours |
| `temporary_feature_cache` | `CACHE` | Delete expired records | 6 Hours |
| `temporary_research_sessions` | `SHORT_TERM` | Delete inactive & expired sessions | 6 Hours |
| `matches` | `PERMANENT` | Do NOT delete | NEVER |
| `predictions` | `PERMANENT` | Do NOT delete | NEVER |
| `match_outcomes` | `PERMANENT` | Do NOT delete | NEVER |
| `backtesting_results` | `PERMANENT` | Do NOT delete | NEVER |
| `calibration_data` | `PERMANENT` | Do NOT delete | NEVER |
| `model_versions` | `PERMANENT` | Do NOT delete | NEVER |
| `audit_logs` | `AUDIT_REQUIRED` | Preserve for audit/security | NEVER |
| `users` | `USER_DATA` | Preserve user accounts | NEVER |
| `system_config` | `SYSTEM_DATA` | Preserve configuration | NEVER |

---

## 3. PREDICTION RESEARCH LIFECYCLE & EXPIRATION RULE

```
MATCH INPUT
  │
  ▼
TEMPORARY RESEARCH SESSION (SHORT_TERM)
  │
  ▼
WEB RESEARCH & EXTRACTION CACHE (CACHE)
  │
  ▼
DATA VALIDATION (TEMPORARY EVIDENCE)
  │
  ▼
FEATURE GENERATION & FORECAST
  │
  ▼
FINAL PREDICTION & REPORT WRITTEN TO PERMANENT DB (PERMANENT)
  │
  ▼
TEMPORARY RESEARCH DATA EXPIRES (expires_at <= current_utc_time)
  │
  ▼
AUTOMATED 6-HOUR CLEANUP PURGES EXPIRED RESEARCH CACHE
```

### Expiration Criteria:
1. `expires_at <= current_server_utc_time()`
2. `is_active == False` (Research session must be completed)
3. `retention_required == False` (Record must not be marked for audit/debugging hold)
4. Permanent prediction write confirmation (`prediction_saved == True` for the associated `match_id`)

---

## 4. SERVER-SIDE SCHEDULING MECHANISM (SUPABASE & FIREBASE)

### Supabase Implementation
- Uses PostgreSQL `pg_cron` extension scheduled as:
  ```sql
  SELECT cron.schedule(
    '0 */6 * * *',
    $$ SELECT execute_6hour_research_cleanup(); $$
  );
  ```
- Executes server-side stored procedure using `SECURITY DEFINER` with service-role permissions.

### Firebase Implementation
- Uses Scheduled Cloud Functions v2:
  ```typescript
  export const scheduled6HourResearchCleanup = onSchedule('every 6 hours', async (event) => {
    await runDatabaseResearchCleanup();
  });
  ```

### Local / Production Fallback
- `ScheduledJobRunner` in `src/data/scheduler.py` executes `DatabaseRetentionManager.run_cleanup_job()` every 21,600 seconds (6 hours).

---

## 5. SAFETY & ABNORMAL-DELETION PROTECTION

1. **Dry-Run Mode**: Supports `dry_run=True` to calculate examine/delete counts without modifying data.
2. **Batch Processing**: Deletions are executed in configurable safe batches (default max 500 records per batch, max 5,000 total deletions per job execution).
3. **Abnormal Volume Safety Threshold**: If a job attempts to delete more than `max_allowed_deletions` (e.g., 5,000 records or >50% of the research cache), the job halts immediately and raises `RetentionSafetyError`.
4. **Active Session Protection**: Research records tied to active research sessions (`is_active=True`) or pending predictions are strictly preserved or extended.
5. **Idempotency**: Running cleanup multiple times produces zero additional deletions once expired records are purged.
6. **Audit & Monitoring**: Every job run creates a structured `RetentionJobLog` record with duration, record counts, and failure reports.
