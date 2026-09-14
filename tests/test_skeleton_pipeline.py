"""Tests for pipeline orchestrator."""

import pytest
from datetime import datetime, timezone, timedelta
from src.pipeline import FootballAIPipeline
from src.research.web_research import EvidenceCategory


def test_pipeline_run():
    pipeline = FootballAIPipeline()
    now = datetime.now(timezone.utc)
    match_input = {
        "match_id": "M100",
        "home_team": "TEAM_HOME",
        "away_team": "TEAM_AWAY",
        "competition": "Champions League",
        "scheduled_time": (now + timedelta(hours=24)).isoformat()
    }

    report = pipeline.process_match(match_input, [])

    assert report.match_id == "M100"
    assert report.risk_and_nobet_assessment["decision"] == "NO_BET"
