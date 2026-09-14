# FOOTBALL AI INTELLIGENCE SYSTEM

[![Build & Test Status](https://img.shields.io/badge/Tests-90%20Passed-brightgreen.svg)](https://github.com/your-org/football-ai-system)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-Supabase%20%2F%20PostgreSQL-emerald.svg)](https://supabase.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

> **PROBABILISTIC FORECASTING SYSTEM FOR FOOTBALL MATCHES**
> *Operates strictly on objective statistical evidence, non-gambling web research, and probabilistic calibration. Enforces non-negotiable constitution rules prohibiting club reputation features, bookmaker odds, and unevidenced assumptions.*

---

## 1. NON-NEGOTIABLE CONSTITUTION RULES
1. **Probabilistic Outputs Only**: The system produces calibrated probability distributions ($P(Home) + P(Draw) + P(Away) = 1.0$). Guaranteed wins, certainty, or financial profit promises are strictly forbidden.
2. **Zero Club Reputation / Prestige Features**: Team names are treated strictly as string identifiers (`team_id`). Popularity, historical prestige, badge value, or perceived team strength are excluded from predictive models.
3. **Total Exclusion of Betting Inputs**: Bookmaker odds, betting lines, tipster picks, and gambling platform predictions are strictly filtered out and excluded from all predictive pipelines.
4. **Source Freshness & Reliability Tracking**: Every external claim must have an associated source domain, publication timestamp, and reliability score.
5. **No Data Invention**: Missing data is marked `UNAVAILABLE`, `UNCERTAIN`, or `CONFLICTING`. Imputation or fabrication of missing evidence is forbidden.
6. **Explicit Abstention Support**: The system must return `NO_BET / INSUFFICIENT EVIDENCE` whenever data density is insufficient, evidence conflicts, or model uncertainty exceeds safe thresholds.

---

## 2. END-TO-END SYSTEM PIPELINE ARCHITECTURE

```
                                  +-----------------------+
                                  |      MATCH INPUT      |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |  MATCH IDENTIFICATION |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |  WEB RESEARCH ENGINE  |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |    DATA VALIDATION    |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |STATISTICAL FEATURES   |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  | FORECASTING ENGINE    |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |   MARKET MAPPING      |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |  RISK / NO-BET ENGINE |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  | FINAL AUDITABLE REPORT|
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  | SUPABASE DATABASE DB  |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  | HISTORICAL VALIDATION |
                                  |   & CALIBRATION       |
                                  +-----------------------+
```

---

## 3. PROJECT DIRECTORY STRUCTURE

```
FOOTBALL_AI_SYSTEM/
├── config/
│   └── config.json                  # System configuration parameters
├── docs/
│   ├── 00_MASTER_SPECIFICATION.md   # System constitution and core rules
│   ├── 01_ARCHITECTURE.md           # Subpackage architecture specification
│   ├── 02_DATA_SCHEMA.md            # Data contract definitions
│   ├── 03_WEB_RESEARCH_RULES.md     # Research collection and filtering rules
│   ├── ...                          # Detailed specifications (Stage 0 to 25)
│   ├── 15_PROJECT_STATUS.md         # Stage status tracking (Stages 0-25 PASS)
│   └── 18_RETENTION_AND_CLEANUP_SPEC.md # 6-Hour database cleanup specification
├── markets/
│   └── Matches-market.md            # Market catalogue taxonomy definitions
├── src/
│   ├── match/                       # Match identification and resolution
│   ├── research/                    # Web research collection & domain reliability
│   ├── data/                        # Database repository, scheduler & 6-hr retention
│   ├── validation/                  # Data validation & contradiction detection
│   ├── features/                    # Feature extraction (no reputation/odds)
│   ├── models/                      # Forecast, calibration, lifecycle & evolution
│   ├── markets/                     # Market mapper & specialist market engines
│   ├── sentiment/                   # Context & sentiment analyzer
│   ├── risk/                        # Multi-factor risk & NO_BET decision engine
│   ├── reporting/                   # Auditable report generator & monitoring
│   ├── audit/                       # Programmatic system auditor
│   ├── backtesting/                 # Backtester, historical validator & shadow trader
│   ├── config.py                    # Configuration loader
│   ├── errors.py                    # Custom exception hierarchy
│   ├── logging.py                   # Structured logger
│   └── pipeline.py                  # End-to-end 14-stage pipeline orchestrator
├── tests/                           # 90 automated unit & integration tests
├── .env.example                     # Environment variables template
├── DATABASE.md                      # Database schema & RLS documentation
├── DEPLOYMENT.md                    # Production deployment guide
├── OPERATIONS.md                    # Operations manual & incident protocol
└── README.md                        # Master project documentation
```

---

## 4. BEGINNER QUICK START GUIDE

### Prerequisites
- Python 3.12+ installed.
- Git installed.

### 1. Clone & Setup Local Environment
```bash
git clone https://github.com/your-org/football-ai-system.git
cd football-ai-system

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements (if requirements.txt exists) or dev dependencies
pip install pytest
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```
*(Optionally edit `.env` with your Supabase credentials or leave default local settings).*

### 3. Run Automated Test Suite
Execute the comprehensive test suite (90 tests across all 26 stages):
```bash
PYTHONPATH=. pytest
```

### 4. Execute a Sample Pre-Match Pipeline Run
```python
from src.pipeline import FootballAIPipeline

pipeline = FootballAIPipeline()

raw_match = {
    "home_team_id": "TEAM_ARSENAL",
    "away_team_id": "TEAM_CHELSEA",
    "scheduled_time": "2025-05-10T15:00:00Z",
    "competition": "Premier League",
    "venue": "Emirates Stadium"
}

raw_evidence = [
    {
        "source_url": "https://official-news.com/lineups",
        "published_at": "2025-05-09T10:00:00Z",
        "category": "TEAM_NEWS",
        "content": "Arsenal star striker confirmed fit for derby fixture.",
        "reliability_score": 0.85
    }
]

report = pipeline.process_match(raw_match, raw_evidence)
print(f"Match ID: {report.match_id}")
print(f"Decision: {report.decision}")
print(f"1X2 Distribution: Home={report.home_win_prob:.2f}, Draw={report.draw_prob:.2f}, Away={report.away_win_prob:.2f}")
```

---

## 5. DATABASE ARCHITECTURE & 6-HOUR CLEANUP SYSTEM

The system uses **Supabase / PostgreSQL** with a decoupled repository pattern (`ProductionDatabaseRepository`).

### Table Classification Matrix

| Table Name | Classification | Retention Policy | Purge Schedule |
|------------|----------------|------------------|----------------|
| `matches` | `PERMANENT` | Do NOT delete | NEVER |
| `predictions` | `PERMANENT` | Do NOT delete (Immutable) | NEVER |
| `match_outcomes` | `PERMANENT` | Do NOT delete | NEVER |
| `backtesting_results` | `PERMANENT` | Do NOT delete | NEVER |
| `calibration_data` | `PERMANENT` | Do NOT delete | NEVER |
| `model_versions` | `PERMANENT` | Do NOT delete | NEVER |
| `audit_logs` | `AUDIT_REQUIRED` | Preserve for security/compliance | NEVER |
| `research_cache` | `CACHE` | Expire & delete expired records | 6 Hours |
| `web_research_raw` | `CACHE` | Expire & delete expired records | 6 Hours |
| `temporary_feature_cache` | `CACHE` | Expire & delete expired records | 6 Hours |
| `temporary_research_sessions` | `SHORT_TERM` | Delete inactive after 6 hrs | 6 Hours |

### Automated 6-Hour Cleanup Safety Safeguards
- **Expired Criteria**: Records are deleted only if `expires_at <= current_utc_time` AND `is_active == False` AND `retention_required == False`.
- **Permanent Data Protection**: Deletion attempts on permanent tables raise `RetentionSafetyError`.
- **Abnormal Volume Stops**: If a cleanup execution attempts to delete >5,000 records or >50% of the cache, the job halts immediately and alerts operators.
- **Idempotency**: Rerunning cleanup produces 0 additional deletions.

---

## 6. API & CORE INTERFACES

### `FootballAIPipeline.process_match(...)`
Orchestrates the 14 core stages from fixture input to final auditable report generation.
- **Inputs**: `raw_match_input` (dict), `raw_evidence_items` (list[dict]), `historical_stats` (optional dict), `as_of_time` (optional datetime).
- **Output**: `AuditableMatchReport` dataclass object containing match verification, valid evidence summary, feature set, forecast distribution, mapped markets, risk evaluation, and probabilistic disclaimers.

### `ScheduledJobRunner.run_6hour_research_cleanup_job(dry_run=False)`
Executes background 6-hour research cache retention cleanup across temporary tables.
- **Inputs**: `dry_run` (bool, default `False`).
- **Output**: List of `RetentionJobLog` dataclass objects recording examined counts, deleted counts, skipped counts, duration, and status.

---

## 7. DOCUMENTATION INDEX
- **`DATABASE.md`**: Complete database schema, migration SQL scripts, Row Level Security (RLS) policies, and retention architecture.
- **`DEPLOYMENT.md`**: Step-by-step production deployment guide for Supabase, Python background schedulers, and environment setup.
- **`OPERATIONS.md`**: Operations manual detailing system health monitoring, incident severity classification, model lifecycle updates, and disaster recovery.
- **`docs/`**: Comprehensive stage-by-stage technical specifications (Stages 0 through 25).

---

## 8. MASTER LAUNCH CHECKLIST
- [x] **Stage 0–14 Core Pipeline**: Full end-to-end forecasting pipeline built and integrated.
- [x] **Stage 15 System Audit**: Programmatic auditor verifies 100% compliance with Master Rules.
- [x] **Stage 16–17 Validation & Paper Trading**: Multi-market backtesting and immutable shadow trading engines operational.
- [x] **Stage 18 Production Infrastructure**: Supabase database repository abstraction and rate-limited scheduler deployed.
- [x] **Stage 19–21 Launch & Monitoring**: Private beta manager, v1.0.0 public launch smoke testing, and system health monitor active.
- [x] **Stage 22–24 Evaluation & Extension**: Continuous drift evaluation, controlled model lifecycle updates, and market extension manager online.
- [x] **Stage 25 Product Evolution**: Long-term ML experiment tracking and spec coherence audits active.
- [x] **6-Hour Database Cleanup**: Policy-driven automated cleanup purging temporary research cache every 6 hours while protecting permanent predictions.
- [x] **Test Verification**: 90/90 Pytest unit and integration tests passing cleanly (`PYTHONPATH=. pytest`).
