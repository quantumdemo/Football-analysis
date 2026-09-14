"""Match feature set contracts."""

from dataclasses import dataclass


@dataclass
class MatchFeatureSet:
    """Feature vector for a match using objective data only."""
    match_id: str
    home_availability_ratio: float
    away_availability_ratio: float
    home_rest_days: float
    away_rest_days: float
    weather_impact_score: float
    evidence_quality_score: float
    is_complete: bool
