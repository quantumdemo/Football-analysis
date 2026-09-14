"""Unit tests for Stage 2 Match Input and Identification module."""

import pytest
from datetime import datetime, timezone
from src.errors import ValidationError
from src.match.identifier import MatchVerificationStatus
from src.match.resolver import MatchResolver


def test_resolve_valid_match_input():
    resolver = MatchResolver()
    raw = {
        "match_id": "M_2026_001",
        "home_team": "Team_North",
        "away_team": "Team_South",
        "competition": "Premier Division",
        "scheduled_time": "2026-10-15T20:00:00+00:00",
        "venue": "Northern Stadium",
        "season": "2026-2027"
    }

    match = resolver.resolve(raw)
    assert match.match_id == "M_2026_001"
    assert match.home_team_id == "Team_North"
    assert match.away_team_id == "Team_South"
    assert match.competition == "Premier Division"
    assert match.status == MatchVerificationStatus.VERIFIED


def test_resolve_missing_required_fields():
    resolver = MatchResolver()
    raw = {
        "match_id": "M_2026_002",
        "home_team": "Team_North"
        # Missing away_team, competition, scheduled_time
    }

    with pytest.raises(ValidationError):
        resolver.resolve(raw)


def test_resolve_identical_home_away_teams():
    resolver = MatchResolver()
    raw = {
        "match_id": "M_2026_003",
        "home_team": "Team_North",
        "away_team": "Team_North",
        "competition": "Premier Division",
        "scheduled_time": "2026-10-15T20:00:00+00:00"
    }

    with pytest.raises(ValidationError):
        resolver.resolve(raw)


def test_resolve_ambiguous_match_status():
    resolver = MatchResolver()
    raw = {
        "match_id": "M_2026_004",
        "home_team": "Team_A",
        "away_team": "Team_B",
        "competition": "Cup Competition",
        "scheduled_time": "2026-11-01T15:00:00+00:00",
        "is_ambiguous": True
    }

    match = resolver.resolve(raw)
    assert match.status == MatchVerificationStatus.AMBIGUOUS
    assert "ambiguous" in match.verification_notes.lower()
