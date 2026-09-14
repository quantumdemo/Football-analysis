"""Match resolver module for ingesting raw inputs and verifying match identity."""

from datetime import datetime
from typing import Dict, Any, Optional
from src.errors import ValidationError
from src.match.identifier import MatchIdentifier, MatchVerificationStatus


class MatchResolver:
    """Resolves raw user match inputs into verified MatchIdentifier objects."""

    def resolve(self, raw_input: Dict[str, Any]) -> MatchIdentifier:
        """Parses and verifies raw match input, stopping if identity cannot be verified."""
        home_team = str(raw_input.get("home_team") or raw_input.get("home_team_id") or "").strip()
        away_team = str(raw_input.get("away_team") or raw_input.get("away_team_id") or "").strip()
        match_id = str(raw_input.get("match_id", "")).strip() or f"M_{home_team}_{away_team}"
        competition = str(raw_input.get("competition", "")).strip()
        venue = str(raw_input.get("venue", "Unknown Venue")).strip()
        season = str(raw_input.get("season", "Current Season")).strip()
        raw_time = raw_input.get("scheduled_time")

        # Validation check for missing fundamental fields
        if not match_id or not home_team or not away_team or not competition:
            raise ValidationError(
                f"Match input incomplete. Required fields missing. Given: {raw_input}"
            )

        # Ambiguity check: identical team names
        if home_team.lower() == away_team.lower():
            raise ValidationError(
                f"Conflicting match input: Home team '{home_team}' and Away team '{away_team}' are identical."
            )

        # Datetime resolution
        if isinstance(raw_time, str):
            try:
                scheduled_time = datetime.fromisoformat(raw_time)
            except ValueError:
                raise ValidationError(f"Invalid scheduled_time format: {raw_time}")
        elif isinstance(raw_time, datetime):
            scheduled_time = raw_time
        else:
            raise ValidationError("Missing or invalid scheduled_time in match input.")

        # Check for ambiguity flags in input
        if raw_input.get("is_ambiguous", False):
            return MatchIdentifier(
                match_id=match_id,
                home_team_id=home_team,
                away_team_id=away_team,
                scheduled_time=scheduled_time,
                competition=competition,
                venue=venue,
                season=season,
                status=MatchVerificationStatus.AMBIGUOUS,
                verification_notes="Fixture identity marked ambiguous by source."
            )

        return MatchIdentifier(
            match_id=match_id,
            home_team_id=home_team,
            away_team_id=away_team,
            scheduled_time=scheduled_time,
            competition=competition,
            venue=venue,
            season=season,
            status=MatchVerificationStatus.VERIFIED,
            verification_notes="Match identity verified successfully."
        )
