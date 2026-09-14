"""Unit tests for Stage 6 Core Forecasting Engine."""

import pytest
from datetime import datetime, timedelta, timezone
from src.errors import ValidationError
from src.features.feature_engine import MatchFeatureSet
from src.models.forecast import ForecastModel, ForecastDistribution


def test_forecast_predict_valid():
    model = ForecastModel()

    features = MatchFeatureSet(
        match_id="M100",
        home_form_ppg=2.1, away_form_ppg=1.2,
        home_goals_scored_per_game=1.8, home_goals_conceded_per_game=0.9,
        away_goals_scored_per_game=1.1, away_goals_conceded_per_game=1.5,
        home_xg_per_game=1.9, home_xga_per_game=0.95,
        away_xg_per_game=1.0, away_xga_per_game=1.4,
        home_shots_per_game=14.0, home_sot_per_game=5.1,
        away_shots_per_game=10.5, away_sot_per_game=3.2,
        home_possession_avg=56.0, away_possession_avg=44.0,
        home_btts_rate=0.5, away_btts_rate=0.5,
        home_clean_sheet_rate=0.4, away_clean_sheet_rate=0.2,
        home_corners_per_game=6.0, away_corners_per_game=3.8,
        home_cards_per_game=1.5, away_cards_per_game=2.2,
        home_fouls_per_game=10.0, away_fouls_per_game=13.0,
        home_offsides_per_game=2.1, away_offsides_per_game=1.7,
        home_rest_days=4.0, away_rest_days=3.0,
        home_availability_ratio=0.95, away_availability_ratio=0.85,
        tactical_defensive_bias=0.0, weather_impact_score=0.1,
        objective_opponent_strength_diff=0.9,
        evidence_quality_score=0.9,
        is_complete=True
    )

    now = datetime.now(timezone.utc)
    kickoff = now + timedelta(hours=24)

    forecast = model.predict(features, as_of_time=now, kickoff_time=kickoff)

    assert forecast.match_id == "M100"
    assert round(forecast.p_home_win + forecast.p_draw + forecast.p_away_win, 5) == 1.0
    assert round(forecast.p_over_2_5_goals + forecast.p_under_2_5_goals, 5) == 1.0
    assert forecast.expected_home_goals > 0.0
    assert forecast.expected_away_goals > 0.0
    assert 0.0 <= forecast.model_confidence <= 1.0


def test_forecast_prevents_future_data_leakage():
    model = ForecastModel()
    now = datetime.now(timezone.utc)
    past_kickoff = now - timedelta(hours=2)  # Kickoff was 2 hours ago
    as_of = now  # as_of is after kickoff

    features = MatchFeatureSet(
        match_id="M101",
        home_form_ppg=1.5, away_form_ppg=1.5,
        home_goals_scored_per_game=1.0, home_goals_conceded_per_game=1.0,
        away_goals_scored_per_game=1.0, away_goals_conceded_per_game=1.0,
        home_xg_per_game=None, home_xga_per_game=None,
        away_xg_per_game=None, away_xga_per_game=None,
        home_shots_per_game=10.0, home_sot_per_game=3.0,
        away_shots_per_game=10.0, away_sot_per_game=3.0,
        home_possession_avg=50.0, away_possession_avg=50.0,
        home_btts_rate=0.5, away_btts_rate=0.5,
        home_clean_sheet_rate=0.3, away_clean_sheet_rate=0.3,
        home_corners_per_game=5.0, away_corners_per_game=5.0,
        home_cards_per_game=2.0, away_cards_per_game=2.0,
        home_fouls_per_game=11.0, away_fouls_per_game=11.0,
        home_offsides_per_game=2.0, away_offsides_per_game=2.0,
        home_rest_days=4.0, away_rest_days=4.0,
        home_availability_ratio=1.0, away_availability_ratio=1.0,
        tactical_defensive_bias=0.0, weather_impact_score=0.0,
        objective_opponent_strength_diff=0.0,
        evidence_quality_score=0.8,
        is_complete=True
    )

    with pytest.raises(ValidationError):
        model.predict(features, as_of_time=as_of, kickoff_time=past_kickoff)


def test_evaluation_hook_export():
    forecast = ForecastDistribution(
        match_id="M102",
        p_home_win=0.45,
        p_draw=0.30,
        p_away_win=0.25,
        expected_home_goals=1.6,
        expected_away_goals=1.1,
        p_over_2_5_goals=0.55,
        p_under_2_5_goals=0.45,
        model_confidence=0.8,
        uncertainty_score=0.2
    )

    hook_dict = forecast.to_evaluation_hook_dict()
    assert hook_dict["match_id"] == "M102"
    assert hook_dict["probabilities_1x2"]["home"] == 0.45
    assert hook_dict["expected_goals"]["total"] == 2.7
