"""Tests for data contract initializations."""

import pytest
from datetime import datetime, timezone
from src.match.identifier import MatchIdentifier
from src.models.forecast import ForecastDistribution
from src.research.web_research import ResearchEvidence


def test_match_identifier_valid():
    now = datetime.now(timezone.utc)
    match = MatchIdentifier("M1", "TEAM_A", "TEAM_B", now, "Premier")
    assert match.match_id == "M1"


def test_match_identifier_identical_teams():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError):
        MatchIdentifier("M1", "TEAM_A", "TEAM_A", now, "Premier")


def test_forecast_distribution_sum_validation():
    with pytest.raises(ValueError):
        ForecastDistribution("M1", 0.5, 0.5, 0.5, 1.5, 1.0, 0.6, 0.4, 0.8, 0.2)


def test_prohibited_research_keyword():
    now = datetime.now(timezone.utc)
    item = ResearchEvidence("e1", "M1", "Check tipster prediction", "https://tipster.com", now, 0.8, "odds")
    assert item.is_prohibited is True
