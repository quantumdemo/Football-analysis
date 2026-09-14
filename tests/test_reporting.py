"""Unit tests for Stage 13 Final Reporting Engine."""

import pytest
from datetime import datetime, timezone
from src.match.identifier import MatchIdentifier
from src.validation.validator import ValidationReport, EvidenceValidationState
from src.features.feature_engine import MatchFeatureSet
from src.models.forecast import ForecastDistribution
from src.risk.risk_engine import RiskEvaluation
from src.reporting.report_generator import ReportGenerator, AuditableMatchReport


@pytest.fixture
def sample_match():
    now = datetime.now(timezone.utc)
    return MatchIdentifier("M100", "TEAM_A", "TEAM_B", now, "Champions League", venue="Main Stadium")


@pytest.fixture
def sample_validation():
    return ValidationReport(
        match_id="M100",
        is_valid=True,
        overall_state=EvidenceValidationState.VERIFIED,
        freshness_ok=True,
        valid_evidence_count=2,
        average_reliability=0.85
    )


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
        evidence_quality_score=0.85,
        is_complete=True
    )


@pytest.fixture
def sample_forecast():
    return ForecastDistribution(
        match_id="M100",
        p_home_win=0.50, p_draw=0.30, p_away_win=0.20,
        expected_home_goals=1.8, expected_away_goals=1.0,
        p_over_2_5_goals=0.58, p_under_2_5_goals=0.42,
        model_confidence=0.85, uncertainty_score=0.15
    )


@pytest.fixture
def sample_risk():
    return RiskEvaluation(
        match_id="M100",
        decision="BET",
        reason="All checks passed",
        confidence_score=0.85,
        uncertainty_score=0.15,
        approved_candidate_markets=["1X2", "Over_Under_2.5"]
    )


def test_generate_auditable_report(sample_match, sample_validation, sample_feature_set, sample_forecast, sample_risk):
    generator = ReportGenerator(model_version="1.0.0", feature_version="1.0.0")

    report = generator.generate_auditable_report(
        match=sample_match,
        validation_report=sample_validation,
        feature_set=sample_feature_set,
        forecast=sample_forecast,
        risk_eval=sample_risk
    )

    assert report.match_id == "M100"
    assert "PROBABILISTIC FORECAST ONLY" in report.disclaimer
    assert report.match_verification["venue"] == "Main Stadium"
    assert report.probabilistic_forecast["outcome_1x2_probabilities"]["home_win"] == 0.50
    assert report.risk_and_nobet_assessment["decision"] == "BET"
    assert report.audit_metadata["model_version"] == "1.0.0"

    report_dict = report.to_dict()
    assert isinstance(report_dict, dict)
    assert report_dict["match_id"] == "M100"
