"""Forecasting engine generating probabilistic forecasts."""

from dataclasses import dataclass
from typing import Dict
from src.features.feature_engine import MatchFeatureSet


@dataclass
class ForecastDistribution:
    """Probabilistic match outcome distribution (must sum to 1.0)."""
    match_id: str
    p_home_win: float
    p_draw: float
    p_away_win: float
    model_confidence: float

    def __post_init__(self):
        total = round(self.p_home_win + self.p_draw + self.p_away_win, 5)
        if total != 1.0:
            raise ValueError(f"Probabilities must sum to 1.0, got {total}")


class ForecastModel:
    """Produces probabilistic estimates based strictly on objective feature sets."""

    def predict(self, feature_set: MatchFeatureSet) -> ForecastDistribution:
        if not feature_set.is_complete:
            # Fallback uniform uncalibrated distribution with 0 confidence
            return ForecastDistribution(
                match_id=feature_set.match_id,
                p_home_win=0.33333,
                p_draw=0.33334,
                p_away_win=0.33333,
                model_confidence=0.0
            )

        # Objective feature logic
        home_advantage = 0.08
        diff_avail = (feature_set.home_availability_ratio - feature_set.away_availability_ratio) * 0.2
        diff_rest = (feature_set.home_rest_days - feature_set.away_rest_days) * 0.02

        raw_home = 0.38 + home_advantage + diff_avail + diff_rest
        raw_away = 0.32 - diff_avail - diff_rest
        raw_draw = 0.30

        # Normalize
        s = raw_home + raw_draw + raw_away
        p_home = round(raw_home / s, 5)
        p_draw = round(raw_draw / s, 5)
        p_away = round(1.0 - p_home - p_draw, 5)

        confidence = round(feature_set.evidence_quality_score * (1.0 - feature_set.weather_impact_score * 0.2), 3)

        return ForecastDistribution(
            match_id=feature_set.match_id,
            p_home_win=p_home,
            p_draw=p_draw,
            p_away_win=p_away,
            model_confidence=confidence
        )
