"""Unit tests for Stage 8 Specialist Markets Engine."""

import pytest
from src.features.feature_engine import MatchFeatureSet
from src.models.forecast import ForecastDistribution
from src.markets.specialist_markets import SpecialistMarketEngine, SpecialistMarketForecast


@pytest.fixture
def sample_feature_set():
    return MatchFeatureSet(
        match_id="M100",
        home_form_ppg=2.1, away_form_ppg=1.2,
        home_goals_scored_per_game=1.8, home_goals_conceded_per_game=0.9,
        away_goals_scored_per_game=1.1, away_goals_conceded_per_game=1.5,
        home_xg_per_game=1.9, home_xga_per_game=0.95,
        away_xg_per_game=1.0, away_xga_per_game=1.4,
        home_shots_per_game=14.0, home_sot_per_game=5.1,
        away_shots_per_game=10.5, away_sot_per_game=3.2,
        home_possession_avg=56.0, away_possession_avg=44.0,
        home_btts_rate=0.60, away_btts_rate=0.50,
        home_clean_sheet_rate=0.40, away_clean_sheet_rate=0.20,
        home_corners_per_game=6.0, away_corners_per_game=4.0,
        home_cards_per_game=1.5, away_cards_per_game=2.5,
        home_fouls_per_game=10.5, away_fouls_per_game=13.5,
        home_offsides_per_game=2.1, away_offsides_per_game=1.7,
        home_rest_days=4.0, away_rest_days=3.0,
        home_availability_ratio=0.95, away_availability_ratio=0.85,
        tactical_defensive_bias=0.0, weather_impact_score=0.1,
        objective_opponent_strength_diff=0.9,
        evidence_quality_score=0.9,
        is_complete=True
    )


@pytest.fixture
def sample_forecast():
    return ForecastDistribution(
        match_id="M100",
        p_home_win=0.50,
        p_draw=0.30,
        p_away_win=0.20,
        expected_home_goals=1.8,
        expected_away_goals=1.0,
        p_over_2_5_goals=0.58,
        p_under_2_5_goals=0.42,
        model_confidence=0.85,
        uncertainty_score=0.15
    )


def test_specialist_goals_btts(sample_feature_set, sample_forecast):
    engine = SpecialistMarketEngine()
    result = engine.forecast_goals_btts(sample_feature_set, sample_forecast)
    assert round(result.probabilities["BTTS_Yes"] + result.probabilities["BTTS_No"], 4) == 1.0
    assert result.expected_value == 2.8


def test_specialist_corners(sample_feature_set):
    engine = SpecialistMarketEngine()
    result = engine.forecast_corners(sample_feature_set)
    assert round(result.probabilities["Over_9.5_Corners"] + result.probabilities["Under_9.5_Corners"], 4) == 1.0
    assert result.expected_value == 10.0


def test_specialist_cards(sample_feature_set):
    engine = SpecialistMarketEngine()
    result = engine.forecast_cards(sample_feature_set)
    assert round(result.probabilities["Over_4.5_Cards"] + result.probabilities["Under_4.5_Cards"], 4) == 1.0
    assert result.expected_value == 4.0


def test_specialist_correct_score(sample_forecast):
    engine = SpecialistMarketEngine()
    result = engine.forecast_correct_score(sample_forecast)
    assert round(sum(result.probabilities.values()), 4) == 1.0
    assert "1-0" in result.probabilities
    assert "2-1" in result.probabilities


def test_specialist_combinations(sample_forecast, sample_feature_set):
    engine = SpecialistMarketEngine()
    result = engine.forecast_combinations(sample_forecast, sample_feature_set)
    assert round(sum(result.probabilities.values()), 4) == 1.0
    assert "Home_and_BTTS_Yes" in result.probabilities


def test_specialist_half_by_half(sample_forecast):
    engine = SpecialistMarketEngine()
    result = engine.forecast_half_by_half(sample_forecast)
    assert round(sum(result.probabilities.values()), 4) == 1.0
    assert "1st_Half_Home" in result.probabilities
