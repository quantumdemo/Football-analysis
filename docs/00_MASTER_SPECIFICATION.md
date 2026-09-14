# 00. MASTER SPECIFICATION

## FOOTBALL AI INTELLIGENCE SYSTEM

### 1. NON-NEGOTIABLE MASTER RULES
1. **Probabilistic Nature**: Do not promise guaranteed wins, certainty, or profit. The system produces probabilistic forecasts.
2. **Identifier-Only Team Names**: Do not use club reputation, popularity, historical prestige, badge value, or assumed strength as predictive features. Team names are identifiers only.
3. **External Predictive Evidence**: Use web research, not betting platforms, as predictive evidence. Exclude bookmaker odds, bookmaker predictions, and tipster picks from the predictive engine.
4. **Attribution & Freshness**: Every important external claim must have a source plus freshness/reliability information.
5. **Data Integrity**: Never invent missing data. Mark it unavailable, uncertain, or conflicting.
6. **Architectural Separation**: Separate research, validation, feature engineering, forecasting, market mapping, risk, and reporting.
7. **Risk Safety**: The system must be able to return `NO BET / INSUFFICIENT EVIDENCE`.
8. **Specification Management**: Do not silently change an approved specification. Record changes in `PROJECT_STATUS.md` / changelog.
9. **Stage Gate Rigor**: Do not proceed to a later stage while the current stage is failing.
10. **Backtesting & Calibration**: All probabilities are estimates and must eventually be backtested and calibrated.

### 2. END-TO-END PIPELINE STAGES
`MATCH INPUT` → `MATCH IDENTIFICATION` → `WEB RESEARCH` → `DATA VALIDATION` → `FEATURE ENGINE` → `FORECAST MODELS` → `PROBABILITY ENGINE` → `MARKET MAPPER` → `SPECIALIST MARKETS` → `RISK/NO-BET` → `FINAL REPORT` → `BACKTESTING` → `CALIBRATION` → `MONITORING`
