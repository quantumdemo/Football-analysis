# FOOTBALL AI INTELLIGENCE SYSTEM

[![Build & Test Status](https://img.shields.io/badge/Tests-94%20Passed-brightgreen.svg)](https://github.com/your-org/football-ai-system)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Hosting](https://img.shields.io/badge/Hosting-Vercel%20Serverless-black.svg)](https://vercel.com/)
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
├── api/
│   └── index.py                     # Vercel serverless Python HTTP handler
├── config/
│   └── config.json                  # System configuration parameters
├── docs/
│   ├── 00_MASTER_SPECIFICATION.md   # System constitution and core rules
│   ├── ...                          # Detailed specifications (Stage 0 to 25)
│   ├── 15_PROJECT_STATUS.md         # Stage status tracking (Stages 0-25 PASS)
│   └── 18_RETENTION_AND_CLEANUP_SPEC.md # 6-Hour database cleanup specification
├── markets/
│   └── Matches-market.md            # Market catalogue taxonomy definitions
├── public/
│   └── index.html                   # Vercel root status dashboard (prevents 404)
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
├── tests/                           # 94 automated unit & integration tests
├── .env.example                     # Environment variables template
├── DATABASE.md                      # Database schema & RLS documentation
├── DEPLOYMENT.md                    # Production deployment guide
├── OPERATIONS.md                    # Operations manual & incident protocol
├── vercel.json                      # Vercel routing configuration
└── README.md                        # Master project documentation
```

---

## 4. VERCEL DEPLOYMENT & SERVERLESS ENDPOINTS

The repository is configured for Vercel deployment with `@vercel/python` serverless functions and static dashboard routing.

### Serverless API Routes
- `GET  /` -> `public/index.html` (System Status Dashboard)
- `GET  /api/health` -> Returns operational metrics and system status.
- `GET  /api/status` -> Returns stage completion matrix (Stages 0–25 PASS).
- `POST /api/predict` -> Executes pre-match prediction pipeline.
- `POST /api/cleanup` -> Executes automated 6-hour research cache cleanup (Manual/External HTTP trigger).

---

## 5. BEGINNER QUICK START GUIDE

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

# Install requirements
pip install pytest
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```

### 3. Run Automated Test Suite
Execute the comprehensive test suite (94 tests across all 26 stages and serverless API):
```bash
PYTHONPATH=. pytest
```

---

## 6. DOCUMENTATION INDEX
- **`DATABASE.md`**: Complete database schema, migration SQL scripts, Row Level Security (RLS) policies, and retention architecture.
- **`DEPLOYMENT.md`**: Step-by-step production deployment guide for Vercel, Supabase, and background schedulers.
- **`OPERATIONS.md`**: Operations manual detailing system health monitoring, incident severity classification, model lifecycle updates, and disaster recovery.
- **`docs/`**: Comprehensive stage-by-stage technical specifications (Stages 0 through 25).
