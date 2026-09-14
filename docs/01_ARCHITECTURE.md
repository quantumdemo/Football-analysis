# 01. ARCHITECTURE SPECIFICATION

## System Architecture

The FOOTBALL AI INTELLIGENCE SYSTEM follows a strictly modular, decoupled architecture.

### Directory Mapping
- `src/match/`: Handles raw match input and ID assignment.
- `src/research/`: Ingests non-betting web research and tracks source reliability/freshness.
- `src/data/`: Data ingestion, schemas, and persistence layer.
- `src/validation/`: Enforces data integrity, flags stale/conflicting/missing data.
- `src/features/`: Computes objective match features (excluding prestige, odds, tipsters).
- `src/models/` & `src/sentiment/`: Probabilistic forecasting models and sentiment analysis.
- `src/markets/`: Maps projected probabilities onto market options.
- `src/risk/`: Implements uncertainty checks and NO BET triggers.
- `src/reporting/`: Generates final structured reports.
