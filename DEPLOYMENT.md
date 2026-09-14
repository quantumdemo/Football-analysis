# PRODUCTION DEPLOYMENT GUIDE

## 1. OVERVIEW & PRE-REQUISITES
This deployment guide details the steps required to deploy the **Football AI Intelligence System** to production.

### Supported Hosting Providers
1. **Vercel** (Serverless API + Static Status Dashboard Landing Page + Vercel Cron).
2. **Linux / Container Runtime** (Python `ScheduledJobRunner` background runner).
3. **Supabase / PostgreSQL** (Production database provider).

---

## 2. STEP 1 — VERCEL DEPLOYMENT (PREVENTING 404 NOT_FOUND ERRORS)

When deploying to Vercel, the repository includes `vercel.json`, `api/index.py` (Vercel Python serverless request handler), and `public/index.html` (root dashboard page) to prevent browser `404 NOT_FOUND` errors.

### Vercel Deployment Steps
1. Log in to [Vercel](https://vercel.com) and click **Add New -> Project**.
2. Connect your GitHub repository (`football-ai-system`).
3. Configure project settings:
   - **Framework Preset**: Other / None.
   - **Root Directory**: `./`.
   - **Build Command**: Leave default / empty.
   - **Output Directory**: `public` (automatically routed via `vercel.json`).
4. Configure Environment Variables in Vercel Dashboard:
   ```env
   ENV=production
   LOG_LEVEL=INFO
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOi...
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...
   CRON_SECRET=your_production_cron_secret
   ```
5. Click **Deploy**. Vercel will automatically route:
   - `GET /` -> `public/index.html` (Status Dashboard)
   - `GET /api/health` -> `api/index.py` (Health Check)
   - `GET /api/status` -> `api/index.py` (Stage Status)
   - `POST /api/predict` -> `api/index.py` (Forecasting API)
   - `POST /api/cleanup` -> `api/index.py` (6-Hour Cleanup Cron)

---

## 3. STEP 2 — SUPABASE DATABASE PROVISIONING

1. Log in to [Supabase](https://supabase.com) and create a new project named `football-ai-system`.
2. Select your target region (e.g., `us-east-1` or `eu-west-1`).
3. Set a strong database password and store it securely.
4. Navigate to **Project Settings -> API** and copy:
   - **Project URL** (`SUPABASE_URL`)
   - **anon / public key** (`SUPABASE_ANON_KEY`)
   - **service_role key** (`SUPABASE_SERVICE_ROLE_KEY` - SERVER ONLY)
5. Open the **SQL Editor** in Supabase and execute the complete initialization script from `DATABASE.md` (creating `matches`, `predictions`, `match_outcomes`, `audit_logs`, and `research_cache` tables with RLS policies).

---

## 4. STEP 3 — AUTOMATED 6-HOUR CLEANUP & BACKGROUND JOBS

### Option A: Vercel Cron (Built-in)
`vercel.json` includes automated 6-hour cron triggering `POST /api/cleanup` every 6 hours:
```json
"crons": [
  {
    "path": "/api/cleanup",
    "schedule": "0 */6 * * *"
  }
]
```

### Option B: Server-Side PostgreSQL `pg_cron` (Supabase)
To avoid `ERROR: 3F000: schema "cron" does not exist`, enable `pg_cron` first:
```sql
CREATE EXTENSION IF NOT EXISTS pg_cron;

SELECT cron.schedule(
    '0 */6 * * *',
    $$ DELETE FROM research_cache WHERE expires_at <= NOW() AND is_active = FALSE AND retention_required = FALSE; $$
);
```

### Option C: Systemd / Cron Python Scheduler
Run `ScheduledJobRunner` via systemd background service:
```ini
[Unit]
Description=Football AI Scheduled Job Runner
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/football-ai-system
ExecStart=/opt/football-ai-system/venv/bin/python -c "from src.data.scheduler import ScheduledJobRunner; runner = ScheduledJobRunner(); runner.run_6hour_research_cleanup_job()"
Restart=always
RestartSec=21600

[Install]
WantedBy=multi-user.target
```

---

## 5. PRE-LAUNCH VERIFICATION CHECKLIST

- [ ] Vercel root URL loads `public/index.html` status page without 404 error.
- [ ] `GET /api/health` returns `200 OK` with `status: HEALTHY`.
- [ ] `POST /api/predict` generates auditable match report.
- [ ] Supabase database connection verified.
- [ ] RLS policies enabled on all database tables.
- [ ] Service role key restricted strictly to server environment.
- [ ] 6-hour research cache cleanup tested with `dry_run=True`.
- [ ] Permanent predictions protection confirmed (cannot be overwritten or deleted).

---

## 6. ROLLBACK & EMERGENCY PROCEDURE

1. **Database Rollback**: Execute restore from snapshot using `ProductionDatabaseRepository.restore_database(snapshot)`.
2. **Emergency Cleanup Halt**: If abnormal deletion occurs, disable Vercel Cron or `pg_cron` schedule.
3. **Application Rollback**: Revert to last stable release in Vercel Dashboard or checkout release tag:
   ```bash
   git checkout v1.0.0
   ```
