"""Core Forecasting Engine producing probabilistic outcome distributions and goal forecasts."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import math
from src.errors import ValidationError
from src.features.feature_engine import MatchFeatureSet


@dataclass
class ForecastDistribution:
    """Probabilistic match outcome and goal forecast distribution (must sum to 1.0)."""
    match_id: str
    p_home_win: float
    p_draw: float
    p_away_win: float
    expected_home_goals: float
    expected_away_goals: float
    p_over_2_5_goals: float
    p_under_2_5_goals: float
    model_confidence: float
    uncertainty_score: float

    def __post_init__(self):
        total_1x2 = round(self.p_home_win + self.p_draw + self.p_away_win, 5)
        if total_1x2 != 1.0:
            raise ValueError(f"1X2 probabilities must sum to 1.0, got {total_1x2}")

        total_ou = round(self.p_over_2_5_goals + self.p_under_2_5_goals, 5)
        if total_ou != 1.0:
            raise ValueError(f"Over/Under 2.5 probabilities must sum to 1.0, got {total_ou}")

    def to_evaluation_hook_dict(self) -> Dict[str, Any]:
        """Provides raw outputs for backtesting and calibration evaluation hooks."""
        return {
            "match_id": self.match_id,
            "probabilities_1x2": {
                "home": self.p_home_win,
                "draw": self.p_draw,
                "away": self.p_away_win
            },
            "expected_goals": {
                "home": self.expected_home_goals,
                "away": self.expected_away_goals,
                "total": round(self.expected_home_goals + self.expected_away_goals, 3)
            },
            "probabilities_over_under_2_5": {
                "over": self.p_over_2_5_goals,
                "under": self.p_under_2_5_goals
            },
            "metrics": {
                "confidence": self.model_confidence,
                "uncertainty": self.uncertainty_score
            }
        }


class ForecastModel:
    """Core probabilistic forecasting engine based strictly on objective features."""

    def predict(
        self,
        feature_set: MatchFeatureSet,
        as_of_time: Optional[datetime] = None,
        kickoff_time: Optional[datetime] = None
    ) -> ForecastDistribution:
        # Prevent future data leakage
        if as_of_time and kickoff_time and as_of_time > kickoff_time:
            raise ValidationError("Future data leakage error: as_of_time is after match kickoff time.")

        if not feature_set.is_complete:
            # Return uncalibrated fallback distribution with high uncertainty
            return ForecastDistribution(
                match_id=feature_set.match_id,
                p_home_win=0.33333,
                p_draw=0.33334,
                p_away_win=0.33333,
                expected_home_goals=1.20,
                expected_away_goals=1.20,
                p_over_2_5_goals=0.50,
                p_under_2_5_goals=0.50,
                model_confidence=0.0,
                uncertainty_score=1.0
            )

        # Objective feature baseline calculation
        home_base_lambda = (feature_set.home_goals_scored_per_game + feature_set.away_goals_conceded_per_game) / 2.0
        away_base_lambda = (feature_set.away_goals_scored_per_game + feature_set.home_goals_conceded_per_game) / 2.0

        # Adjust for player availability & rest
        exp_home_g = max(0.2, home_base_lambda * feature_set.home_availability_ratio + (feature_set.home_rest_days - 3.0) * 0.03)
        exp_away_g = max(0.2, away_base_lambda * feature_set.away_availability_ratio + (feature_set.away_rest_days - 3.0) * 0.03)

        # Goal expectations
        total_exp_goals = exp_home_g + exp_away_g

        # Poisson-like goal distribution approximation for Over/Under 2.5
        # P(Under 2.5) ~ P(0) + P(1) + P(2) with Poisson parameter = total_exp_goals
        p_0 = math.exp(-total_exp_goals)
        p_1 = total_exp_goals * math.exp(-total_exp_goals)
        p_2 = (total_exp_goals ** 2 / 2.0) * math.exp(-total_exp_goals)
        p_under = round(p_0 + p_1 + p_2, 5)
        p_under = max(0.01, min(0.99, p_under))
        p_over = round(1.0 - p_under, 5)

        # 1X2 raw strength logits
        diff = (exp_home_g - exp_away_g) + 0.15 * feature_set.objective_opponent_strength_diff + 0.10  # home advantage
        raw_home = max(0.01, 0.38 + diff * 0.25)
        raw_away = max(0.01, 0.32 - diff * 0.25)
        raw_draw = max(0.01, 0.30 - abs(diff) * 0.05)

        s = raw_home + raw_draw + raw_away
        p_home = round(raw_home / s, 5)
        p_draw = round(raw_draw / s, 5)
        p_away = round(1.0 - p_home - p_draw, 5)

        # Uncertainty metrics
        uncertainty = round(1.0 - feature_set.evidence_quality_score + feature_set.weather_impact_score * 0.3, 3)
        uncertainty = max(0.0, min(1.0, uncertainty))
        confidence = round(1.0 - uncertainty, 3)

        return ForecastDistribution(
            match_id=feature_set.match_id,
            p_home_win=p_home,
            p_draw=p_draw,
            p_away_win=p_away,
            expected_home_goals=round(exp_home_g, 2),
            expected_away_goals=round(exp_away_g, 2),
            p_over_2_5_goals=p_over,
            p_under_2_5_goals=p_under,
            model_confidence=confidence,
            uncertainty_score=uncertainty
        )
