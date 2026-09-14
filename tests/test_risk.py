"""Tests for risk engine and NO_BET triggers."""

import pytest
from datetime import datetime, timedelta
from src.validation.validator import ValidationReport
from src.models.forecast import ForecastDistribution
from src.risk.risk_engine import RiskEngine


def test_no_bet_triggered_on_invalid_validation():
    risk_engine = RiskEngine()

    validation_failed = ValidationReport(
        match_id="M100",
        is_valid=False,
        freshness_ok=True,
        missing_data_fields=["tactics"],
        conflicting_claims=[],
        prohibited_items_rejected=1,
        valid_evidence_count=1,
        average_reliability=0.7
    )

    forecast = ForecastDistribution(
        match_id="M100",
        p_home_win=0.33333,
        p_draw=0.33334,
        p_away_win=0.33333,
        model_confidence=0.0
    )

    evaluation = risk_engine.evaluate("M100", validation_failed, forecast)

    assert evaluation.decision == "NO_BET"
    assert "INSUFFICIENT EVIDENCE" in evaluation.reason


def test_no_bet_triggered_on_conflicting_data():
    risk_engine = RiskEngine()

    validation_conflict = ValidationReport(
        match_id="M101",
        is_valid=False,
        freshness_ok=True,
        missing_data_fields=[],
        conflicting_claims=["Conflict: Player A starting vs Player A injured"],
        prohibited_items_rejected=0,
        valid_evidence_count=2,
        average_reliability=0.8
    )

    forecast = ForecastDistribution(
        match_id="M101",
        p_home_win=0.45,
        p_draw=0.30,
        p_away_win=0.25,
        model_confidence=0.8
    )

    evaluation = risk_engine.evaluate("M101", validation_conflict, forecast)

    assert evaluation.decision == "NO_BET"
    assert "Conflicting claims" in evaluation.reason
