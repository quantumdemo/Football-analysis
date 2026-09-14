"""Match identification data structures and status tracking."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class MatchVerificationStatus(Enum):
    VERIFIED = "VERIFIED"
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICTING = "CONFLICTING"
    UNVERIFIED = "UNVERIFIED"


@dataclass
class MatchIdentifier:
    """Represents a football match using team names strictly as unique string identifiers."""
    match_id: str
    home_team_id: str
    away_team_id: str
    scheduled_time: datetime
    competition: str
    venue: str = "Unknown Venue"
    season: str = "Current Season"
    status: MatchVerificationStatus = MatchVerificationStatus.VERIFIED
    verification_notes: Optional[str] = None

    def __post_init__(self):
        if not self.match_id or not self.home_team_id or not self.away_team_id:
            raise ValueError("Match ID, home team ID, and away team ID must be non-empty strings.")
        if self.home_team_id.strip().lower() == self.away_team_id.strip().lower():
            raise ValueError("Home team ID and away team ID cannot be identical.")
