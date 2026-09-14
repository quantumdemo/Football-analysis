# PRODUCTION DEPLOYMENT GUIDE

## 1. OVERVIEW & PRE-REQUISITES
This deployment guide details the steps required to deploy the **Football AI Intelligence System** to production.

### Required External Services & Credentials
1. **GitHub Repository**: Source code repository.
2. **Supabase Database Account**: Primary production PostgreSQL backend provider.
3. **Python 3.12 Server / Container Runtime**: Production hosting for backend background runners and API endpoints.

---

## 2. STEP 1 — SUPABASE DATABASE PROVISIONING

1. Log in to [Supabase](https://supabase.com) and create a new project named `football-ai-system`.
2. Select your target region (e.g., `us-east-1` or `eu-west-1`).
3. Set a strong database password and store it securely.
4. Navigate to **Project Settings -> API** and copy:
   - **Project URL** (`SUPABASE_URL`)
   - **anon / public key** (`SUPABASE_ANON_KEY`)
   - **service_role key** (`SUPABASE_SERVICE_ROLE_KEY` - SERVER ONLY)
5. Open the **SQL Editor** in Supabase and execute the complete initialization script from `DATABASE.md` (creating `matches`, `predictions`, `match_outcomes`, `audit_logs`, and `research_cache` tables with RLS policies).

---

## 3. STEP 2 — PYTHON ENVIRONMENT & SCHEDULER DEPLOYMENT

1. Clone the repository on your production Linux server / container host:
   ```bash
   git clone https://github.com/your-org/football-ai-system.git
   cd football-ai-system
   ```
2. Install Python 3.12 and dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/venv/activate
   pip install -r requirements.txt  # or install pytest, etc.
   ```
3. Create production `.env` file:
   ```bash
   cp .env.example .env
   ```
4. Populate `.env` with production secrets:
   ```env
   ENV=production
   LOG_LEVEL=INFO
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOi...
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...
   CRON_SECRET=your_production_cron_secret
   ```

---

## 4. STEP 3 — AUTOMATED 6-HOUR CLEANUP & BACKGROUND JOBS

### Option A: Server-Side PostgreSQL `pg_cron` (Recommended for Supabase)
To avoid `ERROR: 3F000: schema "cron" does not exist`, enable the `pg_cron` extension first:
1. In Supabase Dashboard, go to **Database -> Extensions**, search for `pg_cron`, and click **Enable**.
2. Alternatively, run in the Supabase SQL Editor:
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_cron;
   ```
3. Then schedule the cleanup job:
   ```sql
   SELECT cron.schedule(
       '0 */6 * * *',
       $$ DELETE FROM research_cache WHERE expires_at <= NOW() AND is_active = FALSE AND retention_required = FALSE; $$
   );
   ```

### Option B: Systemd / Cron Python Scheduler
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

## 5. OPTIONAL HTTP API SERVER / FRONTEND HOSTING

«STATUS: NOT IMPLEMENTED IN CORE CLI ENGINE - OPTIONAL WEB FRONTEND EXTENSION»

If deploying an optional HTTP REST API wrapper (e.g. FastAPI / Flask / Next.js):
1. Create serverless API routes or ASGI app wrapping `FootballAIPipeline`.
2. Set environment variables on your hosting provider (Vercel / Render / AWS Lambda).
3. Connect `SUPABASE_URL` and `SUPABASE_ANON_KEY` to client apps.

---

## 6. PRE-LAUNCH VERIFICATION CHECKLIST

- [ ] `PYTHONPATH=. pytest` passes all 90 tests cleanly.
- [ ] Supabase database connection verified.
- [ ] RLS policies enabled on all database tables.
- [ ] Service role key restricted strictly to server environment.
- [ ] 6-hour research cache cleanup tested with `dry_run=True`.
- [ ] Permanent predictions protection confirmed (cannot be overwritten or deleted).
- [ ] System Health Monitor reporting `HEALTHY` status.

---

## 7. ROLLBACK & EMERGENCY PROCEDURE

1. **Database Rollback**: Execute restore from snapshot using `ProductionDatabaseRepository.restore_database(snapshot)`.
2. **Emergency Cleanup Halt**: If abnormal deletion occurs, disable `pg_cron` schedule:
   ```sql
   SELECT cron.unschedule('0 */6 * * *');
   ```
3. **Application Rollback**: Revert to last stable git release tag:
   ```bash
   git checkout v1.0.0
   ```
