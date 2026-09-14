"""Unit tests for Stage 18 Production Infrastructure & Database."""

import pytest
from datetime import datetime, timedelta, timezone
from src.errors import DataIntegrityError, ValidationError
from src.match.identifier import MatchIdentifier
from src.data.database import ProductionDatabaseRepository
from src.data.scheduler import ScheduledJobRunner
from src.research.web_research import EvidenceCategory


@pytest.fixture
def db_repo():
    return ProductionDatabaseRepository("Supabase")


@pytest.fixture
def sample_match():
    now = datetime.now(timezone.utc)
    return MatchIdentifier("M_PROD_100", "TEAM_A", "TEAM_B", now + timedelta(hours=24), "Premier League")


def test_database_save_and_retrieve_match(db_repo, sample_match):
    db_repo.save_match(sample_match)
    assert "M_PROD_100" in db_repo.tables["matches"]


def test_database_foreign_key_constraint(db_repo, sample_match):
    # Trying to save prediction for non-existent match must raise DataIntegrityError
    now = datetime.now(timezone.utc)
    match_unregistered = MatchIdentifier("M_UNREG", "TEAM_A", "TEAM_B", now, "Premier League")

    runner = ScheduledJobRunner(db_repo)

    # If match is registered first, prediction save succeeds
    raw_input = {
        "match_id": "M_PROD_100",
        "home_team": "TEAM_A",
        "away_team": "TEAM_B",
        "competition": "Premier League",
        "scheduled_time": (now + timedelta(hours=24)).isoformat()
    }
    evidence = [{
        "evidence_id": "ev1",
        "match_id": "M_PROD_100",
        "claim": "Team news",
        "source_url": "https://bbc.com/1",
        "published_at": now.isoformat(),
        "category": EvidenceCategory.TEAM_NEWS.value
    }]

    output = runner.run_prediction_job(raw_input, evidence)
    assert output["match_id"] == "M_PROD_100"
    assert "M_PROD_100" in db_repo.tables["predictions"]


def test_database_backup_and_restore(db_repo, sample_match):
    db_repo.save_match(sample_match)
    backup = db_repo.backup_database()

    assert "matches" in backup
    assert backup["matches"] == 1
    assert db_repo.restore_database(backup) is True


def test_rate_limiting_protection(db_repo):
    runner = ScheduledJobRunner(db_repo, max_requests_per_min=2)
    now = datetime.now(timezone.utc)

    raw_input = {
        "match_id": "M_RATE_1",
        "home_team": "TEAM_A",
        "away_team": "TEAM_B",
        "competition": "Premier League",
        "scheduled_time": (now + timedelta(hours=24)).isoformat()
    }

    runner.run_prediction_job(raw_input, [])
    runner.run_prediction_job({**raw_input, "match_id": "M_RATE_2"}, [])

    # Third request within 1 min exceeds max 2 requests/min
    with pytest.raises(ValidationError):
        runner.run_prediction_job({**raw_input, "match_id": "M_RATE_3"}, [])
