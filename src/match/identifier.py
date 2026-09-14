"""Match identification data structures."""

from dataclasses import dataclass
from datetime import datetime


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
