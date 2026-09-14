# PRODUCTION DEPLOYMENT GUIDE

## 1. OVERVIEW & PRE-REQUISITES
This deployment guide details the steps required to deploy the **Football AI Intelligence System** to production.

### Supported Hosting Providers
1. **Vercel** (Serverless API + Static Status Dashboard Landing Page).
2. **Supabase / PostgreSQL** (Production database provider with automated `pg_cron` 6-hour research cache cleanup).
3. **Linux / Container Runtime** (Optional Python `ScheduledJobRunner` background runner).

---

## 2. STEP 1 — VERCEL DEPLOYMENT (WITHOUT CRON LIMITATION)

When deploying to Vercel, the repository includes `vercel.json`, `api/index.py` (Vercel Python serverless request handler), and `public/index.html` (root dashboard page) to prevent browser `404 NOT_FOUND` errors.

> **Note on Vercel Cron**: Vercel Cron is explicitly disabled in `vercel.json` because Vercel Hobby accounts restrict cron schedules to once per day. The automated 6-hour cleanup is managed directly on Supabase via `pg_cron` (or via external runner calling `POST /api/cleanup`).

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
   - `POST /api/cleanup` -> `api/index.py` (Manual / External HTTP Cleanup Trigger)

---

## 3. STEP 2 — SUPABASE DATABASE PROVISIONING & AUTOMATED 6-HOUR CLEANUP

1. Log in to [Supabase](https://supabase.com) and create a new project named `football-ai-system`.
2. Select your target region (e.g., `us-east-1` or `eu-west-1`).
3. Set a strong database password and store it securely.
4. Navigate to **Project Settings -> API** and copy:
   - **Project URL** (`SUPABASE_URL`)
   - **anon / public key** (`SUPABASE_ANON_KEY`)
   - **service_role key** (`SUPABASE_SERVICE_ROLE_KEY` - SERVER ONLY)
5. Open the **SQL Editor** in Supabase and execute the complete initialization script from `DATABASE.md`.
6. Enable the `pg_cron` extension in Supabase (**Database -> Extensions -> Enable pg_cron** or run `CREATE EXTENSION IF NOT EXISTS pg_cron;`).
7. Schedule the 6-hour research cache cleanup in Supabase:
   ```sql
   SELECT cron.schedule(
       '0 */6 * * *',
       $$ DELETE FROM research_cache WHERE expires_at <= NOW() AND is_active = FALSE AND retention_required = FALSE; $$
   );
   ```

---

## 4. PRE-LAUNCH VERIFICATION CHECKLIST

- [ ] Vercel root URL loads `public/index.html` status page without 404 error.
- [ ] Vercel deployment succeeds without cron plan restriction error.
- [ ] `GET /api/health` returns `200 OK` with `status: HEALTHY`.
- [ ] `POST /api/predict` generates auditable match report.
- [ ] Supabase database connection verified.
- [ ] Supabase `pg_cron` schedule active for 6-hour research cache cleanup.
- [ ] RLS policies enabled on all database tables.
- [ ] Permanent predictions protection confirmed (cannot be overwritten or deleted).

---

## 5. ROLLBACK & EMERGENCY PROCEDURE

1. **Database Rollback**: Execute restore from snapshot using `ProductionDatabaseRepository.restore_database(snapshot)`.
2. **Emergency Cleanup Halt**: If abnormal deletion occurs, disable Supabase `pg_cron` schedule:
   ```sql
   SELECT cron.unschedule('0 */6 * * *');
   ```
3. **Application Rollback**: Revert to last stable release in Vercel Dashboard or checkout release tag:
   ```bash
   git checkout v1.0.0
   ```
