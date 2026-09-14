# 17. STAGE 18 — PRODUCTION INFRASTRUCTURE & DATABASE SPECIFICATION

## 1. PRODUCTION DATABASE SELECTION: SUPABASE
**Selected Database**: **Supabase (PostgreSQL)** is finalized as the primary production backend.
Supabase provides relational SQL analysis across matches, events, statistical features, forecast probabilities, market mapping, actual outcomes, backtest metrics, and model versions.

The data-access layer remains strictly decoupled via abstract repository interfaces (`ProductionDatabaseRepository`) to ensure provider isolation.

---

## 2. PRODUCTION SCHEMA & CONSTRAINTS

### Database Tables:
1. `matches`: `match_id` (PK), `home_team_id`, `away_team_id`, `scheduled_time`, `competition`, `venue`, `status`, `created_at`
2. `web_evidence`: `evidence_id` (PK), `match_id` (FK), `claim`, `source_url`, `published_at`, `reliability_score`, `category`, `is_prohibited`
3. `validated_features`: `match_id` (PK/FK), `feature_vector_json`, `is_complete`, `created_at`
4. `predictions`: `prediction_id` (PK), `match_id` (FK), `prediction_timestamp`, `model_version`, `decision`, `probabilities_1x2_json`, `expected_goals_json`, `created_at`
5. `match_outcomes`: `match_id` (PK/FK), `actual_outcome`, `home_goals`, `away_goals`, `settled_at`
6. `audit_logs`: `log_id` (PK), `event_type`, `details_json`, `timestamp`

### Indexes:
- `idx_matches_scheduled_time`: B-Tree index on `matches(scheduled_time)` for fast temporal pre-kickoff queries.
- `idx_evidence_match_published`: Compound index on `web_evidence(match_id, published_at)`.
- `idx_predictions_match_version`: Compound index on `predictions(match_id, model_version)`.

---

## 3. SECURITY & ENVIRONMENT VARIABLES
- Secrets (service role keys, DB passwords, JWT secrets) MUST NEVER be committed to version control.
- Secrets are loaded dynamically via environment variables (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `DATABASE_URL`).

---

## 4. SCHEDULED JOBS & WORKFLOWS
1. **Research Ingestion Job**: Ingests pre-match news and filters gambling keywords every 15 minutes.
2. **Feature Refresh Job**: Computes objective match feature vectors 2 hours prior to kickoff.
3. **Prediction Job**: Generates immutable pre-match forecast reports 1 hour prior to kickoff.
4. **Post-Match Settlement Job**: Settles predictions against actual match outcomes 3 hours post-kickoff.

---

## 5. RATE LIMITING & ABUSE PROTECTION
- API rate limit: 60 requests/minute per client IP.
- Payload size limit: 1 MB max per request.

---

## 6. BACKUP, DEPLOYMENT & RECOVERY PROCEDURES
- **Daily Automated Backups**: Point-in-time recovery (PITR) enabled on Supabase.
- **Rollback Procedure**: Revert database migrations via versioned migration scripts and rollback application release image.
