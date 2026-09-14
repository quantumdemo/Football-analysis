"""Unit tests for Stage 7 Market Mapping Engine."""

import pytest
from src.models.forecast import ForecastDistribution
from src.markets.market_mapper import MarketRegistry, MarketMapper, MarketMappingReport


def test_market_registry_parsing():
    registry = MarketRegistry("markets/Matches-market.md")
    assert len(registry.registry) > 0

    market_1x2 = registry.get_market("1x2_(home___draw___away)")
    assert market_1x2 is not None
    assert market_1x2.is_supported is True


def test_market_mapper_1x2():
    mapper = MarketMapper()
    forecast = ForecastDistribution(
        match_id="M100",
        p_home_win=0.50,
        p_draw=0.30,
        p_away_win=0.20,
        expected_home_goals=1.8,
        expected_away_goals=1.0,
        p_over_2_5_goals=0.55,
        p_under_2_5_goals=0.45,
        model_confidence=0.85,
        uncertainty_score=0.15
    )

    report = mapper.map_market(forecast, "1x2_(home___draw___away)")
    assert report.is_supported is True
    assert len(report.selection_forecasts) == 3
    assert report.selection_forecasts[0].selection_name == "Home (1)"
    assert report.selection_forecasts[0].projected_probability == 0.50


def test_market_mapper_double_chance():
    mapper = MarketMapper()
    forecast = ForecastDistribution(
        match_id="M101",
        p_home_win=0.40,
        p_draw=0.35,
        p_away_win=0.25,
        expected_home_goals=1.4,
        expected_away_goals=1.1,
        p_over_2_5_goals=0.48,
        p_under_2_5_goals=0.52,
        model_confidence=0.80,
        uncertainty_score=0.20
    )

    report = mapper.map_market(forecast, "double_chance")
    assert report.is_supported is True
    assert len(report.selection_forecasts) == 3
    # 1X = 0.40 + 0.35 = 0.75
    assert report.selection_forecasts[0].projected_probability == 0.75


def test_market_mapper_unsupported_market():
    mapper = MarketMapper()
    forecast = ForecastDistribution(
        match_id="M102",
        p_home_win=0.33,
        p_draw=0.33,
        p_away_win=0.34,
        expected_home_goals=1.0,
        expected_away_goals=1.0,
        p_over_2_5_goals=0.50,
        p_under_2_5_goals=0.50,
        model_confidence=0.50,
        uncertainty_score=0.50
    )

    report = mapper.map_market(forecast, "exotic_unsupported_player_props_xyz")
    assert report.is_supported is False
    assert len(report.selection_forecasts) == 0
    assert "Unsupported" in report.mapping_notes
