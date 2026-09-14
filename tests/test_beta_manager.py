"""Unit tests for Stage 19 Private Beta Release Manager."""

import pytest
from datetime import datetime, timedelta, timezone
from src.errors import ValidationError
from src.research.web_research import EvidenceCategory
from src.reporting.beta_manager import PrivateBetaManager, PrivateBetaSummaryReport


@pytest.fixture
def beta_manager():
    return PrivateBetaManager()


@pytest.fixture
def sample_match_input():
    now = datetime.now(timezone.utc)
    return {
        "match_id": "M_BETA_100",
        "home_team": "Team_Alpha",
        "away_team": "Team_Beta",
        "competition": "Premier Division",
        "scheduled_time": (now + timedelta(hours=24)).isoformat()
    }


@pytest.fixture
def sample_evidence():
    now = datetime.now(timezone.utc)
    return [
        {
            "evidence_id": "ev1",
            "match_id": "M_BETA_100",
            "claim": "Team news update: Squad fit for selection.",
            "source_url": "https://bbc.com/sport/1",
            "published_at": (now - timedelta(hours=2)).isoformat(),
            "reliability_score": 0.90,
            "category": EvidenceCategory.TEAM_NEWS.value
        },
        {
            "evidence_id": "ev2",
            "match_id": "M_BETA_100",
            "claim": "Tactics confirmed: 4-3-3 formation.",
            "source_url": "https://bbc.com/sport/2",
            "published_at": (now - timedelta(hours=1)).isoformat(),
            "reliability_score": 0.90,
            "category": EvidenceCategory.TACTICS.value
        }
    ]


def test_beta_user_journey_execution(beta_manager, sample_match_input, sample_evidence):
    report = beta_manager.execute_beta_user_journey("user_beta_1", sample_match_input, sample_evidence)

    assert report.match_id == "M_BETA_100"
    assert report.risk_and_nobet_assessment["decision"] in ("BET", "NO_BET")
    assert len(beta_manager.session_logs) == 1


def test_beta_safety_check_never_fabricates_prediction_on_empty_evidence(beta_manager, sample_match_input):
    # Empty evidence input -> must return NO_BET report safely
    report = beta_manager.execute_beta_user_journey("user_beta_2", sample_match_input, [])

    assert report.match_id == "M_BETA_100"
    assert report.risk_and_nobet_assessment["decision"] == "NO_BET"


def test_beta_feedback_and_summary_collection(beta_manager, sample_match_input, sample_evidence):
    beta_manager.execute_beta_user_journey("user_beta_1", sample_match_input, sample_evidence)

    beta_manager.record_user_feedback(
        user_id="user_beta_1",
        match_id="M_BETA_100",
        latency_ms=120.0,
        clarity_rating=5,
        usefulness_rating=4
    )

    summary = beta_manager.get_beta_summary()
    assert isinstance(summary, PrivateBetaSummaryReport)
    assert summary.total_sessions_run == 1
    assert summary.total_feedback_count == 1
    assert summary.average_clarity_score == 5.0
    assert summary.average_usefulness_score == 4.0
    assert summary.fabricated_prediction_incidents == 0
