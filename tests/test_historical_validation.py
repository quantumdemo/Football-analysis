"""Unit tests for Stage 16 Historical Validation Engine."""

import pytest
from datetime import datetime, timedelta, timezone
from src.match.identifier import MatchIdentifier
from src.research.web_research import ResearchEvidence, EvidenceCategory
from src.backtesting.backtester import HistoricalMatchRecord
from src.backtesting.historical_validator import HistoricalValidationEngine, HistoricalValidationReport


def test_chronological_historical_validation():
    validator = HistoricalValidationEngine()
    now = datetime.now(timezone.utc)

    records = []
    for i in range(10):
        match_time = now - timedelta(days=10 - i)
        match = MatchIdentifier(f"M_VAL_{i}", f"HOME_{i}", f"AWAY_{i}", match_time, "Premier League")

        evidence = [
            ResearchEvidence(f"e1_{i}", f"M_VAL_{i}", "Team news confirmed.", "https://official.com/1", match_time - timedelta(hours=3), 0.90, EvidenceCategory.TEAM_NEWS.value),
            ResearchEvidence(f"e2_{i}", f"M_VAL_{i}", "Tactics confirmed.", "https://official.com/2", match_time - timedelta(hours=2), 0.90, EvidenceCategory.TACTICS.value)
        ]

        records.append(HistoricalMatchRecord(
            match=match,
            raw_evidence=evidence,
            historical_stats={"home_form_ppg": 2.0, "away_form_ppg": 1.0},
            actual_outcome="HOME",
            actual_home_goals=2,
            actual_away_goals=0
        ))

    report = validator.validate_chronologically(records)

    assert isinstance(report, HistoricalValidationReport)
    assert report.total_evaluated > 0
    assert report.overall_log_loss > 0.0
    assert "Premier League" in report.breakdowns_by_competition
    assert "1X2" in report.breakdowns_by_market_family
    assert "HIGH_AVAILABILITY" in report.breakdowns_by_data_availability


def test_validation_abstention_on_weak_data():
    validator = HistoricalValidationEngine()
    now = datetime.now(timezone.utc)
    match_time = now - timedelta(hours=5)

    match = MatchIdentifier("M_WEAK", "HOME", "AWAY", match_time, "La Liga")
    # Weak evidence -> only 1 claim -> missing required tactics category -> NO_BET
    evidence = [
        ResearchEvidence("e1", "M_WEAK", "Team news update", "https://official.com/1", match_time - timedelta(hours=2), 0.90, EvidenceCategory.TEAM_NEWS.value)
    ]

    record = HistoricalMatchRecord(
        match=match,
        raw_evidence=evidence,
        historical_stats={},
        actual_outcome="HOME",
        actual_home_goals=1,
        actual_away_goals=0
    )

    report = validator.validate_chronologically([record])

    assert report.overall_abstention_rate == 1.0
    assert report.total_evaluated == 0
