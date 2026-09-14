"""Specialist Markets Engine for incremental category-by-category probabilistic modeling.

Includes models for:
1. Goals & BTTS
2. Corners
3. Cards & Bookings
4. Offsides & Fouls
5. Shots & Shots on Target (SOT)
6. Player Markets
7. Goal Timing / Minutes
8. Correct Score & Multiscores
9. Combination Markets
10. Half-by-Half Markets
"""

from dataclasses import dataclass, field
import math
from typing import Dict, List, Any, Optional
from src.features.feature_engine import MatchFeatureSet
from src.models.forecast import ForecastDistribution


@dataclass
class SpecialistMarketForecast:
    """Forecast output for a specialist market category."""
    category_name: str
    probabilities: Dict[str, float]
    expected_value: Optional[float] = None
    confidence_score: float = 0.8
    notes: str = "Calculated from objective features."

    def __post_init__(self):
        # Verify probability sum if discrete options present
        if self.probabilities:
            total = round(sum(self.probabilities.values()), 4)
            if abs(total - 1.0) > 1e-3 and not any(k.endswith("_expected") for k in self.probabilities):
                raise ValueError(f"Probabilities for category {self.category_name} must sum to 1.0, got {total}")


class SpecialistMarketEngine:
    """Calculates specialist market probabilities category by category."""

    def forecast_goals_btts(self, features: MatchFeatureSet, forecast: ForecastDistribution) -> SpecialistMarketForecast:
        """1. Goals & Both Teams To Score (BTTS)."""
        p_btts_yes = round(features.home_btts_rate * 0.5 + features.away_btts_rate * 0.5, 4)
        p_btts_no = round(1.0 - p_btts_yes, 4)
        return SpecialistMarketForecast(
            category_name="Goals / BTTS",
            probabilities={"BTTS_Yes": p_btts_yes, "BTTS_No": p_btts_no},
            expected_value=round(forecast.expected_home_goals + forecast.expected_away_goals, 2),
            confidence_score=forecast.model_confidence
        )

    def forecast_corners(self, features: MatchFeatureSet) -> SpecialistMarketForecast:
        """2. Corners Markets."""
        exp_corners = round(features.home_corners_per_game + features.away_corners_per_game, 2)
        p_under_9_5 = round(max(0.01, min(0.99, 1.0 - (exp_corners / 18.0))), 4)
        p_over_9_5 = round(1.0 - p_under_9_5, 4)
        return SpecialistMarketForecast(
            category_name="Corners",
            probabilities={"Over_9.5_Corners": p_over_9_5, "Under_9.5_Corners": p_under_9_5},
            expected_value=exp_corners,
            confidence_score=0.8
        )

    def forecast_cards(self, features: MatchFeatureSet) -> SpecialistMarketForecast:
        """3. Bookings & Cards Markets."""
        exp_cards = round(features.home_cards_per_game + features.away_cards_per_game, 2)
        p_under_4_5 = round(max(0.01, min(0.99, 1.0 - (exp_cards / 8.0))), 4)
        p_over_4_5 = round(1.0 - p_under_4_5, 4)
        return SpecialistMarketForecast(
            category_name="Cards / Bookings",
            probabilities={"Over_4.5_Cards": p_over_4_5, "Under_4.5_Cards": p_under_4_5},
            expected_value=exp_cards,
            confidence_score=0.8
        )

    def forecast_offsides_fouls(self, features: MatchFeatureSet) -> SpecialistMarketForecast:
        """4. Offsides & Fouls Markets."""
        exp_fouls = round(features.home_fouls_per_game + features.away_fouls_per_game, 2)
        p_under_24_5 = round(max(0.01, min(0.99, 1.0 - (exp_fouls / 40.0))), 4)
        p_over_24_5 = round(1.0 - p_under_24_5, 4)
        return SpecialistMarketForecast(
            category_name="Offsides / Fouls",
            probabilities={"Over_24.5_Fouls": p_over_24_5, "Under_24.5_Fouls": p_under_24_5},
            expected_value=exp_fouls,
            confidence_score=0.8
        )

    def forecast_shots_sot(self, features: MatchFeatureSet) -> SpecialistMarketForecast:
        """5. Shots & Shots on Target (SOT) Markets."""
        exp_shots = round(features.home_shots_per_game + features.away_shots_per_game, 2)
        p_under_23_5 = round(max(0.01, min(0.99, 1.0 - (exp_shots / 45.0))), 4)
        p_over_23_5 = round(1.0 - p_under_23_5, 4)
        return SpecialistMarketForecast(
            category_name="Shots / SOT",
            probabilities={"Over_23.5_Shots": p_over_23_5, "Under_23.5_Shots": p_under_23_5},
            expected_value=exp_shots,
            confidence_score=0.8
        )

    def forecast_player_markets(self, player_name: str, exp_goals: float) -> SpecialistMarketForecast:
        """6. Player Markets."""
        p_score = round(max(0.01, min(0.90, exp_goals * 0.35)), 4)
        p_no_score = round(1.0 - p_score, 4)
        return SpecialistMarketForecast(
            category_name=f"Player Markets ({player_name})",
            probabilities={"To_Score_Anytime": p_score, "No_Goal": p_no_score},
            confidence_score=0.75
        )

    def forecast_goal_timing(self, forecast: ForecastDistribution) -> SpecialistMarketForecast:
        """7. Goal Timing / Minutes Markets."""
        p_early_goal = round(max(0.05, min(0.80, (forecast.expected_home_goals + forecast.expected_away_goals) * 0.25)), 4)
        p_late_or_no_goal = round(1.0 - p_early_goal, 4)
        return SpecialistMarketForecast(
            category_name="Goal Timing",
            probabilities={"Goal_0_to_30_Min": p_early_goal, "No_Goal_0_to_30_Min": p_late_or_no_goal},
            confidence_score= forecast.model_confidence
        )

    def forecast_correct_score(self, forecast: ForecastDistribution) -> SpecialistMarketForecast:
        """8. Correct Score Matrix using Bivariate Poisson distribution."""
        lambda_h = forecast.expected_home_goals
        lambda_a = forecast.expected_away_goals

        scores = {}
        for h in range(4):
            for a in range(4):
                p_h = (math.exp(-lambda_h) * (lambda_h ** h)) / math.factorial(h)
                p_a = (math.exp(-lambda_a) * (lambda_a ** a)) / math.factorial(a)
                scores[f"{h}-{a}"] = p_h * p_a

        # Normalize score matrix
        total_p = sum(scores.values())
        norm_scores = {k: round(v / total_p, 4) for k, v in scores.items()}
        # Ensure exact 1.0 sum
        s = sum(norm_scores.values())
        diff = round(1.0 - s, 4)
        norm_scores["1-1"] = round(norm_scores["1-1"] + diff, 4)

        return SpecialistMarketForecast(
            category_name="Correct Score",
            probabilities=norm_scores,
            confidence_score=forecast.model_confidence
        )

    def forecast_combinations(self, forecast: ForecastDistribution, features: MatchFeatureSet) -> SpecialistMarketForecast:
        """9. Combination Markets (Result + BTTS)."""
        p_btts = features.home_btts_rate * 0.5 + features.away_btts_rate * 0.5

        raw_combo = {
            "Home_and_BTTS_Yes": forecast.p_home_win * p_btts,
            "Home_and_BTTS_No": forecast.p_home_win * (1.0 - p_btts),
            "Draw_and_BTTS_Yes": forecast.p_draw * p_btts,
            "Draw_and_BTTS_No": forecast.p_draw * (1.0 - p_btts),
            "Away_and_BTTS_Yes": forecast.p_away_win * p_btts,
            "Away_and_BTTS_No": forecast.p_away_win * (1.0 - p_btts)
        }
        total = sum(raw_combo.values())
        norm_combo = {k: round(v / total, 4) for k, v in raw_combo.items()}
        diff = round(1.0 - sum(norm_combo.values()), 4)
        norm_combo["Home_and_BTTS_Yes"] = round(norm_combo["Home_and_BTTS_Yes"] + diff, 4)

        return SpecialistMarketForecast(
            category_name="Combinations (Result + BTTS)",
            probabilities=norm_combo,
            confidence_score=forecast.model_confidence
        )

    def forecast_half_by_half(self, forecast: ForecastDistribution) -> SpecialistMarketForecast:
        """10. Half-by-Half Markets."""
        p_1st_home = round(forecast.p_home_win * 0.7 + 0.1, 4)
        p_1st_draw = round(forecast.p_draw * 1.1, 4)
        p_1st_away = round(1.0 - p_1st_home - p_1st_draw, 4)

        p_1st_away = max(0.01, p_1st_away)
        s = p_1st_home + p_1st_draw + p_1st_away
        norm_1st = {
            "1st_Half_Home": round(p_1st_home / s, 4),
            "1st_Half_Draw": round(p_1st_draw / s, 4),
            "1st_Half_Away": round(1.0 - round(p_1st_home / s, 4) - round(p_1st_draw / s, 4), 4)
        }

        return SpecialistMarketForecast(
            category_name="Half-by-Half (1st Half Result)",
            probabilities=norm_1st,
            confidence_score=forecast.model_confidence
        )
