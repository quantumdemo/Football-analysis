# 02. DATA SCHEMA SPECIFICATION

Defines data contracts for Match Inputs, Research Evidence, Validated Features, Forecast Outputs, Risk Evaluation, and Reports.

## Key Schemas
- **MatchInput**: `match_id`, `home_team`, `away_team`, `utc_timestamp`, `competition`
- **ResearchItem**: `source_url`, `claim`, `timestamp`, `reliability_score`, `category`
- **ValidationResult**: `is_valid`, `missing_fields`, `conflicting_fields`, `freshness_ok`
- **RiskResult**: `decision` (`BET` or `NO_BET`), `reason`, `confidence_score`
