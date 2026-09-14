"""Integration tests for the full end-to-end Football AI Pipeline."""

import pytest
from datetime import datetime, timedelta, timezone
from src.pipeline import FootballAIPipeline
from src.research.web_research import ResearchEvidence


def test_pipeline_normal_valid_match():
    pipeline = FootballAIPipeline()
    now = datetime.now(timezone.utc)
    scheduled = now + timedelta(hours=24)

    evidence = [
        ResearchEvidence(
            evidence_id="e1",
            match_id="M_VAL_01",
            claim="Home team head coach announced 4-3-3 tactical line-up.",
            source_url="https://officialclubnews.com/tactics",
            published_at=now - timedelta(hours=4),
            reliability_score=0.9,
            category="tactics"
        ),
        ResearchEvidence(
            evidence_id="e2",
            match_id="M_VAL_01",
            claim="Key defender returned to training, team news confirmed.",
            source_url="https://reliablejournal.com/team-news",
            published_at=now - timedelta(hours=2),
            reliability_score=0.85,
            category="team_news"
        )
    ]

    report = pipeline.process_match(
        match_id="M_VAL_01",
        home_team_id="TEAM_ALPHA",
        away_team_id="TEAM_BETA",
        scheduled_time=scheduled,
        competition="League One",
        raw_evidence=evidence
    )

    assert report["match_id"] == "M_VAL_01"
    assert report["validation_status"]["is_valid"] is True
    assert report["risk_assessment"]["decision"] == "BET"
    p_sum = report["forecast"]["p_home_win"] + report["forecast"]["p_draw"] + report["forecast"]["p_away_win"]
    assert abs(p_sum - 1.0) < 1e-4


def test_pipeline_triggers_no_bet_when_bookmaker_odds_only():
    pipeline = FootballAIPipeline()
    now = datetime.now(timezone.utc)
    scheduled = now + timedelta(hours=24)

    # Only bookmaker odds provided (should be filtered out)
    evidence = [
        ResearchEvidence(
            evidence_id="e_odds",
            match_id="M_VAL_02",
            claim="Bookmaker odds give Home team 1.50 decimal odds.",
            source_url="https://bettingodds.com/odds",
            published_at=now - timedelta(hours=1),
            reliability_score=0.9,
            category="odds"
        )
    ]

    report = pipeline.process_match(
        match_id="M_VAL_02",
        home_team_id="TEAM_GAMMA",
        away_team_id="TEAM_DELTA",
        scheduled_time=scheduled,
        competition="League One",
        raw_evidence=evidence
    )

    assert report["match_id"] == "M_VAL_02"
    assert report["validation_status"]["prohibited_rejected"] == 1
    assert report["risk_assessment"]["decision"] == "NO_BET"
