# DATABASE DOCUMENTATION & RETENTION ARCHITECTURE

## 1. OVERVIEW & SELECTED BACKEND
The Football AI Intelligence System is designed with a decoupled repository pattern (`ProductionDatabaseRepository` in `src/data/database.py`) supporting **Supabase / PostgreSQL** as the primary backend provider.

All database tables are strictly classified under the **Database Retention Framework** to control storage growth while protecting permanent predictions, historical match outcomes, backtesting results, calibration data, and security audit logs.

---

## 2. DATABASE CLASSIFICATION & SCHEMA MATRIX

| Table / Collection | Purpose | Retention Class | Retention Policy | Foreign Keys / Constraints |
|--------------------|---------|-----------------|------------------|----------------------------|
| `matches` | Fixture and match metadata | `PERMANENT` | Do NOT delete | Primary Key: `match_id` |
| `predictions` | Auditable prediction reports and decision outputs | `PERMANENT` | Do NOT delete | Primary Key: `match_id`, FK: `matches.match_id` (Immutable) |
| `match_outcomes` | Settled match scores and outcome statistics | `PERMANENT` | Do NOT delete | Primary Key: `match_id`, FK: `matches.match_id` |
| `backtesting_results` | Historical validation and simulation metrics | `PERMANENT` | Do NOT delete | Primary Key: `backtest_id` |
| `calibration_data` | Probability calibration and ECE metrics | `PERMANENT` | Do NOT delete | Primary Key: `calibration_id` |
| `model_versions` | ML model version registry and lifecycle state | `PERMANENT` | Do NOT delete | Primary Key: `version_id` |
| `audit_logs` | System audit and Master Rule compliance logs | `AUDIT_REQUIRED` | Preserve for security/compliance | Primary Key: `log_id` |
| `users` | User profiles and beta participation data | `USER_DATA` | Preserve user records | Primary Key: `user_id` |
| `system_config` | System settings and runtime configuration | `SYSTEM_DATA` | Preserve configuration | Primary Key: `config_id` |
| `research_cache` | Web research evidence and article cache | `CACHE` | Expire & delete every 6 hrs | Primary Key: `record_id`, FK: `matches.match_id` |
| `web_research_raw` | Raw web search HTTP response payloads | `CACHE` | Expire & delete every 6 hrs | Primary Key: `record_id` |
| `temporary_feature_cache` | Intermediate calculated match feature sets | `CACHE` | Expire & delete every 6 hrs | Primary Key: `record_id`, FK: `matches.match_id` |
| `temporary_research_sessions` | Active research session state tracking | `SHORT_TERM` | Delete inactive after 6 hrs | Primary Key: `session_id` |

---

## 3. SQL MIGRATION & SCHEMA INITIALIZATION

Execute the following SQL script in the Supabase SQL Editor to initialize all tables, indexes, and constraints:

```sql
-- 1. Create Fixtures / Matches Table
CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    home_team_id TEXT NOT NULL,
    away_team_id TEXT NOT NULL,
    scheduled_time TIMESTAMPTZ NOT NULL,
    competition TEXT NOT NULL,
    venue TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'SCHEDULED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_matches_scheduled_time ON matches (scheduled_time);

-- 2. Create Predictions Table (Immutable)
CREATE TABLE IF NOT EXISTS predictions (
    match_id TEXT PRIMARY KEY REFERENCES matches(match_id) ON DELETE RESTRICT,
    report_json JSONB NOT NULL,
    decision TEXT NOT NULL,
    model_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictions_match_version ON predictions (match_id, model_version);

-- 3. Create Settled Match Outcomes Table
CREATE TABLE IF NOT EXISTS match_outcomes (
    match_id TEXT PRIMARY KEY REFERENCES matches(match_id) ON DELETE RESTRICT,
    home_score INT NOT NULL,
    away_score INT NOT NULL,
    settled_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Create Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id TEXT PRIMARY KEY,
    audit_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    overall_passed BOOLEAN NOT NULL,
    details_json JSONB NOT NULL
);

-- 5. Create Temporary Research Cache Table
CREATE TABLE IF NOT EXISTS research_cache (
    record_id TEXT PRIMARY KEY,
    match_id TEXT NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    research_session_id TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    retention_required BOOLEAN NOT NULL DEFAULT FALSE,
    prediction_saved BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_research_cache_expires_at ON research_cache (expires_at) WHERE is_active = FALSE;
```

---

## 4. ROW LEVEL SECURITY (RLS) & POLICIES

To prevent unauthorized deletion and client-side tampering, apply Row Level Security (RLS) in Supabase:

```sql
-- Enable RLS on all tables
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_cache ENABLE ROW LEVEL SECURITY;

-- Read-only public access policy for predictions
CREATE POLICY "Public Read Access" ON predictions FOR SELECT USING (true);

-- Server-only write/delete policies for background runner / service role
CREATE POLICY "Service Role Full Access" ON predictions FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service Role Cache Cleanup" ON research_cache FOR ALL USING (auth.role() = 'service_role');
```

---

## 5. AUTOMATED 6-HOUR CLEANUP MECHANISM

### Supabase `pg_cron` Extension Requirement
To run `cron.schedule(...)` in Supabase without triggering `ERROR: 3F000: schema "cron" does not exist`, you must enable the `pg_cron` extension first:

1. **Option A (Supabase Dashboard)**: Navigate to **Database -> Extensions**, search for `pg_cron`, and click **Enable**.
2. **Option B (SQL Editor)**: Execute:
   ```sql
   -- Enable pg_cron extension in Supabase
   CREATE EXTENSION IF NOT EXISTS pg_cron;
   ```

After enabling the extension, schedule the 6-hour cleanup job in the Supabase SQL Editor:

```sql
-- PostgreSQL pg_cron Schedule (Supabase)
SELECT cron.schedule(
    '0 */6 * * *',
    $$ DELETE FROM research_cache WHERE expires_at <= NOW() AND is_active = FALSE AND retention_required = FALSE; $$
);
```

### Fallback Option (Python Background Scheduler)
If `pg_cron` is unavailable on your Supabase plan, run `ScheduledJobRunner` via Python background service or cron job:
```python
from src.data.scheduler import ScheduledJobRunner

runner = ScheduledJobRunner()
runner.run_6hour_research_cleanup_job(dry_run=False)
```

### Safety Controls
1. **Active Session Protection**: Records where `is_active = TRUE` or `retention_required = TRUE` are strictly skipped.
2. **Permanent Table Protection**: Operations attempting `DELETE` on `predictions`, `matches`, or `match_outcomes` trigger a `RetentionSafetyError`.
3. **Abnormal Volume Stops**: If deletion volume exceeds 5,000 records or >50% of the cache, the cleanup job halts immediately to prevent accidental data loss.
