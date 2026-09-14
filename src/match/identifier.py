"""Match identification module."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MatchIdentifier:
    """Represents a football match using team names strictly as unique string identifiers."""
    match_id: str
    home_team_id: str
    away_team_id: str
    scheduled_time: datetime
    competition: str

    def __post_init__(self):
        if not self.match_id or not self.home_team_id or not self.away_team_id:
            raise ValueError("Match ID, home team ID, and away team ID must be non-empty strings.")
        if self.home_team_id == self.away_team_id:
            raise ValueError("Home team ID and away team ID cannot be identical.")


def create_match_identifier(
    match_id: str,
    home_team_id: str,
    away_team_id: str,
    scheduled_time: datetime,
    competition: str
) -> MatchIdentifier:
    """Factory function to create a validated MatchIdentifier."""
    return MatchIdentifier(
        match_id=match_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        scheduled_time=scheduled_time,
        competition=competition
    )
