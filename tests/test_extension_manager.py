"""Unit tests for Stage 24 Extension Manager for New Markets, Features & Data Sources."""

import pytest
from src.errors import ValidationError
from src.markets.extension_manager import MarketFeatureExtensionManager, NewMarketDefinition, NewFeatureDefinition, NewDataSourceDefinition


@pytest.fixture
def ext_manager():
    return MarketFeatureExtensionManager()


def test_register_new_market_requires_settlement_definition(ext_manager):
    # Short/missing settlement definition must fail
    with pytest.raises(ValidationError):
        ext_manager.register_new_market("m1", "Cards", "Total Cards Over 3.5", "Short def")

    market = ext_manager.register_new_market(
        "m1", "Cards", "Total Cards Over 3.5",
        "Settled at 90 minutes full time based on official referee match report. Second yellow cards count as 1 red."
    )
    assert market.market_id == "m1"
    assert market.backtest_passed is False
    assert market.shadow_test_passed is False


def test_enable_market_requires_backtest_and_shadow_test(ext_manager):
    ext_manager.register_new_market(
        "m2", "Corners", "1st Half Corners Over 4.5",
        "Settled at half time based on official corner kicks taken before 45min whistle."
    )

    # Enabling without passing tests must fail
    with pytest.raises(ValidationError):
        ext_manager.enable_market_for_live_recommendation("m2")

    # Verify backtest
    ext_manager.verify_market_backtest("m2", True)
    # Enabling without shadow test must still fail
    with pytest.raises(ValidationError):
        ext_manager.enable_market_for_live_recommendation("m2")

    # Verify shadow test
    ext_manager.verify_market_shadow_test("m2", True)

    enabled_market = ext_manager.enable_market_for_live_recommendation("m2")
    assert enabled_market.enabled_for_live_recommendation is True


def test_validate_and_approve_feature_rejects_reputation_and_low_usefulness(ext_manager):
    # Prohibited reputation feature term must fail
    with pytest.raises(ValidationError):
        ext_manager.validate_and_approve_feature("club_reputation_score", "float", "Prestige rating", 0.9, 24.0, 0.20)

    # Low availability must fail
    with pytest.raises(ValidationError):
        ext_manager.validate_and_approve_feature("team_xg_5_matches", "float", "Recent xG avg", 0.50, 24.0, 0.20)

    # Valid objective feature passes
    feat = ext_manager.validate_and_approve_feature("team_xg_5_matches", "float", "Recent xG avg", 0.90, 24.0, 0.15)
    assert feat.is_approved is True


def test_validate_and_approve_data_source_rejects_gambling_sources(ext_manager):
    # Gambling domain must fail
    with pytest.raises(ValidationError):
        ext_manager.validate_and_approve_data_source("src_odds", "https://bet365.example.com", "Betting Site", 0.90)

    # Valid sports news domain passes
    src = ext_manager.validate_and_approve_data_source("src_bbc", "https://bbc.com/sport", "BBC Sport", 0.95)
    assert src.is_approved is True
    assert src.provenance_verified is True
