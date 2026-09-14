"""Unit tests for Stage 10 Risk, Confidence & No-Bet Engine."""

import pytest
from src.validation.validator import ValidationReport, EvidenceValidationState
from src.features.feature_engine import MatchFeatureSet
from src.models.forecast import ForecastDistribution
from src.risk.risk_engine import RiskEngine, RiskEvaluation


@pytest.fixture
def valid_inputs():
    val_report = ValidationReport(
        match_id="M100",
        is_valid=True,
        overall_state=EvidenceValidationState.VERIFIED,
        freshness_ok=True,
        average_reliability=0.85,
        valid_evidence_count=2
    )

    features = MatchFeatureSet(
        match_id="M100",
        home_form_ppg=2.0, away_form_ppg=1.5,
        home_goals_scored_per_game=1.8, home_goals_conceded_per_game=1.0,
        away_goals_scored_per_game=1.2, away_goals_conceded_per_game=1.4,
        home_xg_per_game=1.9, home_xga_per_game=0.9,
        away_xg_per_game=1.1, away_xga_per_game=1.3,
        home_shots_per_game=14.0, home_sot_per_game=5.0,
        away_shots_per_game=11.0, away_sot_per_game=3.5,
        home_possession_avg=55.0, away_possession_avg=45.0,
        home_btts_rate=0.5, away_btts_rate=0.5,
        home_clean_sheet_rate=0.4, away_clean_sheet_rate=0.2,
        home_corners_per_game=6.0, away_corners_per_game=4.0,
        home_cards_per_game=1.5, away_cards_per_game=2.2,
        home_fouls_per_game=10.0, away_fouls_per_game=12.0,
        home_offsides_per_game=2.0, away_offsides_per_game=1.8,
        home_rest_days=4.0, away_rest_days=3.0,
        home_availability_ratio=0.95, away_availability_ratio=0.90,
        tactical_defensive_bias=0.0, weather_impact_score=0.1,
        objective_opponent_strength_diff=0.5,
        evidence_quality_score=0.85,
        is_complete=True
    )

    forecast = ForecastDistribution(
        match_id="M100",
        p_home_win=0.50, p_draw=0.30, p_away_win=0.20,
        expected_home_goals=1.8, expected_away_goals=1.0,
        p_over_2_5_goals=0.55, p_under_2_5_goals=0.45,
        model_confidence=0.80, uncertainty_score=0.20
    )

    return val_report, features, forecast


def test_risk_evaluation_approved_bet(valid_inputs):
    val_report, features, forecast = valid_inputs
    engine = RiskEngine()

    evaluation = engine.evaluate("M100", val_report, features, forecast)
    assert evaluation.decision == "BET"
    assert len(evaluation.approved_candidate_markets) > 0
    assert len(evaluation.risk_factors) == 0


def test_risk_evaluation_triggers_no_bet_on_invalid_validation(valid_inputs):
    val_report, features, forecast = valid_inputs
    val_report.is_valid = False
    val_report.overall_state = EvidenceValidationState.CONFLICTING
    val_report.conflicting_claims = ["Conflict: Player starting vs injured"]

    engine = RiskEngine()
    evaluation = engine.evaluate("M100", val_report, features, forecast)

    assert evaluation.decision == "NO_BET"
    assert "INSUFFICIENT EVIDENCE" in evaluation.reason
    assert len(evaluation.approved_candidate_markets) == 0


def test_risk_evaluation_triggers_no_bet_on_low_availability(valid_inputs):
    val_report, features, forecast = valid_inputs
    features.home_availability_ratio = 0.50  # Below 0.70 threshold

    engine = RiskEngine()
    evaluation = engine.evaluate("M100", val_report, features, forecast)

    assert evaluation.decision == "NO_BET"
    assert "Home player availability low" in evaluation.reason[0] or "Home player availability low" in evaluation.risk_factors[0]


def test_risk_evaluation_triggers_no_bet_on_high_uncertainty(valid_inputs):
    val_report, features, forecast = valid_inputs
    forecast.model_confidence = 0.40  # Below 0.60
    forecast.uncertainty_score = 0.60 # Exceeds 0.40

    engine = RiskEngine()
    evaluation = engine.evaluate("M100", val_report, features, forecast)

    assert evaluation.decision == "NO_BET"
    assert "below minimum required" in evaluation.reason
