"""Unit tests for Stage 11 Time-Aware Backtesting Framework."""

import pytest
from datetime import datetime, timedelta, timezone
from src.match.identifier import MatchIdentifier
from src.research.web_research import ResearchEvidence, EvidenceCategory
from src.backtesting.backtester import TimeAwareBacktester, HistoricalMatchRecord, BacktestMetricReport


def test_backtest_execution():
    backtester = TimeAwareBacktester()
    now = datetime.now(timezone.utc)
    match_time = now - timedelta(hours=24)

    match = MatchIdentifier("M_HIST_1", "TEAM_HOME", "TEAM_AWAY", match_time, "Premier League")

    evidence = [
        ResearchEvidence("e1", "M_HIST_1", "Team news update", "https://official.com/1", match_time - timedelta(hours=2), 0.90, EvidenceCategory.TEAM_NEWS.value),
        ResearchEvidence("e2", "M_HIST_1", "Tactics confirmed 4-3-3", "https://official.com/2", match_time - timedelta(hours=1), 0.90, EvidenceCategory.TACTICS.value)
    ]

    record = HistoricalMatchRecord(
        match=match,
        raw_evidence=evidence,
        historical_stats={
            "home_form_ppg": 2.2, "away_form_ppg": 1.0,
            "home_goals_scored": 2.0, "home_goals_conceded": 0.8,
            "away_goals_scored": 1.0, "away_goals_conceded": 1.8
        },
        actual_outcome="HOME",
        actual_home_goals=2,
        actual_away_goals=0
    )

    report = backtester.run_backtest([record])

    assert report.total_matches_evaluated == 1
    assert report.evaluated_predictions_count == 1
    assert report.no_bet_count == 0
    assert report.abstention_rate == 0.0
    assert report.accuracy == 1.0
    assert report.log_loss > 0.0
    assert report.brier_score >= 0.0


def test_backtest_abstention_rate_when_missing_data():
    backtester = TimeAwareBacktester()
    now = datetime.now(timezone.utc)
    match_time = now - timedelta(hours=24)

    match = MatchIdentifier("M_HIST_2", "TEAM_HOME", "TEAM_AWAY", match_time, "Premier League")

    # Missing required 'tactics' category -> will trigger NO_BET
    evidence = [
        ResearchEvidence("e1", "M_HIST_2", "Team news update", "https://official.com/1", match_time - timedelta(hours=2), 0.90, EvidenceCategory.TEAM_NEWS.value)
    ]

    record = HistoricalMatchRecord(
        match=match,
        raw_evidence=evidence,
        historical_stats={},
        actual_outcome="HOME",
        actual_home_goals=1,
        actual_away_goals=0
    )

    report = backtester.run_backtest([record])

    assert report.total_matches_evaluated == 1
    assert report.no_bet_count == 1
    assert report.abstention_rate == 1.0
    assert report.evaluated_predictions_count == 0
