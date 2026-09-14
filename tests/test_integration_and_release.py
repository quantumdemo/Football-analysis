"""Final Integration & Release Readiness Test Suite for Stage 14."""

import pytest
from datetime import datetime, timedelta, timezone
from src.errors import ValidationError
from src.pipeline import FootballAIPipeline
from src.research.web_research import EvidenceCategory


@pytest.fixture
def pipeline_instance():
    return FootballAIPipeline()


@pytest.fixture
def valid_match_input():
    now = datetime.now(timezone.utc)
    return {
        "match_id": "M_RELEASE_100",
        "home_team": "Alpha_FC",
        "away_team": "Beta_United",
        "competition": "Champions League",
        "scheduled_time": (now + timedelta(hours=24)).isoformat(),
        "venue": "Olympic Stadium",
        "season": "2026-2027"
    }


@pytest.fixture
def valid_evidence():
    now = datetime.now(timezone.utc)
    return [
        {
            "evidence_id": "ev_1",
            "match_id": "M_RELEASE_100",
            "claim": "Head coach confirmed 4-3-3 tactical line-up in pre-match press conference.",
            "source_url": "https://bbc.com/sport/football/tactics",
            "published_at": (now - timedelta(hours=4)).isoformat(),
            "reliability_score": 0.95,
            "category": EvidenceCategory.TACTICS.value
        },
        {
            "evidence_id": "ev_2",
            "match_id": "M_RELEASE_100",
            "claim": "Starting defender returned to training; team news confirmed.",
            "source_url": "https://officialclub.com/news/1",
            "published_at": (now - timedelta(hours=2)).isoformat(),
            "reliability_score": 0.90,
            "category": EvidenceCategory.TEAM_NEWS.value
        }
    ]


def test_full_pipeline_valid_match_flow(pipeline_instance, valid_match_input, valid_evidence):
    report = pipeline_instance.process_match(valid_match_input, valid_evidence)

    assert report.match_id == "M_RELEASE_100"
    assert report.risk_and_nobet_assessment["decision"] == "BET"
    p_1x2_sum = round(sum(report.probabilistic_forecast["outcome_1x2_probabilities"].values()), 5)
    assert p_1x2_sum == 1.0
    assert "PROBABILISTIC FORECAST ONLY" in report.disclaimer
    assert report.audit_metadata["model_version"] == "1.0.0"


def test_full_pipeline_triggers_no_bet_on_gambling_odds_only(pipeline_instance, valid_match_input):
    now = datetime.now(timezone.utc)
    # Only bookmaker odds provided -> strictly filtered out -> leads to missing categories -> NO_BET
    odds_evidence = [
        {
            "evidence_id": "ev_odds",
            "match_id": "M_RELEASE_100",
            "claim": "Bookmaker odds favor Home team at 1.50 decimal odds.",
            "source_url": "https://bettingodds.example.com/odds",
            "published_at": (now - timedelta(hours=1)).isoformat(),
            "reliability_score": 0.90,
            "category": "odds"
        }
    ]

    report = pipeline_instance.process_match(valid_match_input, odds_evidence)

    assert report.match_id == "M_RELEASE_100"
    assert report.risk_and_nobet_assessment["decision"] == "NO_BET"
    assert report.validation_summary["prohibited_items_rejected"] == 1
    assert "NO BET / INSUFFICIENT EVIDENCE" in report.risk_and_nobet_assessment["reason"]


def test_full_pipeline_triggers_no_bet_on_conflicting_evidence(pipeline_instance, valid_match_input):
    now = datetime.now(timezone.utc)
    conflicting_evidence = [
        {
            "evidence_id": "ev_c1",
            "match_id": "M_RELEASE_100",
            "claim": "Conflict: Player A is fit vs Player A is injured",
            "source_url": "https://bbc.com/sport/1",
            "published_at": (now - timedelta(hours=3)).isoformat(),
            "reliability_score": 0.85,
            "category": EvidenceCategory.TEAM_NEWS.value
        },
        {
            "evidence_id": "ev_c2",
            "match_id": "M_RELEASE_100",
            "claim": "4-3-3 tactics expected.",
            "source_url": "https://bbc.com/sport/2",
            "published_at": (now - timedelta(hours=2)).isoformat(),
            "reliability_score": 0.85,
            "category": EvidenceCategory.TACTICS.value
        }
    ]

    report = pipeline_instance.process_match(valid_match_input, conflicting_evidence)

    assert report.match_id == "M_RELEASE_100"
    assert report.risk_and_nobet_assessment["decision"] == "NO_BET"
    assert "Source contradiction conflict detected" in report.risk_and_nobet_assessment["reason"]


def test_full_pipeline_prevents_future_data_leakage(pipeline_instance, valid_match_input, valid_evidence):
    now = datetime.now(timezone.utc)
    future_as_of = now + timedelta(hours=48)  # After kickoff time

    with pytest.raises(ValidationError):
        pipeline_instance.process_match(
            valid_match_input,
            valid_evidence,
            as_of_time=future_as_of
        )
