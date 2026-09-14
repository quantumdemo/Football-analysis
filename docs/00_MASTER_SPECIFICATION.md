# 00. MASTER SPECIFICATION (SYSTEM CONSTITUTION)

## STAGE 0 — MASTER SPECIFICATION & CONSTITUTION

### 1. OBJECTIVES
The FOOTBALL AI INTELLIGENCE SYSTEM is designed to generate probabilistic forecasts for football match outcomes based strictly on objective evidence, web research, team availability news, tactical insights, fixture schedule, and weather metrics.

The system DOES NOT predict definite outcomes, promise guaranteed wins, certainty, or financial profit. All outputs are probabilistic estimates that must be backtested and calibrated.

---

### 2. FORBIDDEN SHORTCUTS
1. **Club Reputation / Badge Value**: Team names are strictly string identifiers (`home_team_id`, `away_team_id`). Club popularity, historical prestige, badge value, brand, or assumed strength MUST NOT be used as predictive features.
2. **Betting Platform Inputs**: Bookmaker odds, betting lines, bookmaker probabilities, prediction markets, and tipster picks MUST NOT be used as predictive evidence. Any research items containing betting odds or tipster recommendations MUST be rejected at ingestion/validation.
3. **Data Imputation / Invention**: Missing or unavailable data MUST NEVER be invented or imputed with fake defaults. It must be explicitly marked missing, uncertain, or conflicting.
4. **Market Catalogue Misuse**: `markets/Matches-market.md` serves strictly as a market catalogue (defining market types like 1X2, Asian Handicap, Over/Under). It MUST NEVER be used as a source for match prediction.

---

### 3. DATA AND SOURCE RULES
1. **Freshness**: Every research evidence claim must include a publication timestamp. Evidence published post-kickoff or older than configurable freshness limits (e.g. 72 hours) must be invalidated.
2. **Reliability & Source Attribution**: Every claim must record its source URL and a reliability score (0.0 to 1.0).
3. **Contradictions & Conflict Index**: If claims contradict each other (e.g., player starting vs. player injured), the evidence must be flagged as conflicting.

---

### 4. PREDICTION PRINCIPLES
1. **Probabilistic Outputs**: All forecast distributions must output probabilities for mutually exclusive outcomes (e.g. Home, Draw, Away) that sum exactly to 1.0.
2. **Model Confidence**: Confidence scores reflect evidence quality, freshness, and weather/environmental stability.

---

### 5. MARKET PRINCIPLES
1. Market mapping translates predicted outcome probabilities to standard wagering market formats (e.g., 1X2, Over/Under Goals, Asian Handicap).
2. `markets/Matches-market.md` is a structural market taxonomy document defining valid market formats.

---

### 6. RISK & NO-BET RULES
The system MUST emit `NO_BET` / `INSUFFICIENT EVIDENCE` if:
1. Core required research categories (e.g., team news, tactics) are missing.
2. Contradictory/conflicting claims exist.
3. Average evidence reliability falls below the minimum required threshold (e.g., 0.50).
4. Model confidence score falls below minimum risk tolerance.

---

### 7. TESTING PHILOSOPHY
1. Comprehensive test suite using Pytest.
2. Required test coverage: normal data flow, stale data rejection, missing category detection, conflicting evidence handling, rejection of bookmaker sources, and end-to-end pipeline execution.

---

### 8. STAGE BOUNDARIES AND DEFINITION OF DONE
1. Pipeline consists of 14 sequential stages:
   `MATCH INPUT` → `MATCH IDENTIFICATION` → `WEB RESEARCH` → `DATA VALIDATION` → `FEATURE ENGINE` → `FORECAST MODELS` → `PROBABILITY ENGINE` → `MARKET MAPPER` → `SPECIALIST MARKETS` → `RISK/NO-BET` → `FINAL REPORT` → `BACKTESTING` → `CALIBRATION` → `MONITORING`
2. **Stage 0 Definition of Done**:
   - Master specification constitution written in `docs/00_MASTER_SPECIFICATION.md`.
   - All 16 specification documents (`docs/00` to `docs/15`) created and aligned.
   - Project directory structure established.
   - Config and `markets/Matches-market.md` present.
   - Zero prediction engine execution in Stage 0 beyond structural validation.
   - Stage 0 marked PASS in `docs/15_PROJECT_STATUS.md`.
