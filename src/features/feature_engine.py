"""Feature engine module for transforming validated research data into objective numerical features."""

from dataclasses import dataclass
from typing import Dict, List, Any
from src.validation.validator import ValidationReport
from src.research.web_research import ResearchEvidence


@dataclass
class MatchFeatureSet:
    """Feature vector for a match using objective data only."""
    match_id: str
    home_availability_ratio: float  # 0.0 to 1.0 (key players available)
    away_availability_ratio: float  # 0.0 to 1.0
    home_rest_days: float
    away_rest_days: float
    weather_impact_score: float  # 0.0 (clear) to 1.0 (extreme)
    evidence_quality_score: float
    is_complete: bool


class FeatureEngine:
    """Extracts features strictly without using reputation, prestige, badge value, or odds."""

    def extract_features(
        self,
        match_id: str,
        valid_evidence: List[ResearchEvidence],
        validation_report: ValidationReport
    ) -> MatchFeatureSet:
        if not validation_report.is_valid:
            return MatchFeatureSet(
                match_id=match_id,
                home_availability_ratio=0.0,
                away_availability_ratio=0.0,
                home_rest_days=0.0,
                away_rest_days=0.0,
                weather_impact_score=0.0,
                evidence_quality_score=0.0,
                is_complete=False
            )

        home_avail = 1.0
        away_avail = 1.0
        home_rest = 4.0
        away_rest = 4.0
        weather_score = 0.0

        for item in valid_evidence:
            claim_lower = item.claim.lower()
            if "home injury" in claim_lower or "home player out" in claim_lower:
                home_avail -= 0.15
            elif "away injury" in claim_lower or "away player out" in claim_lower:
                away_avail -= 0.15
            elif "heavy rain" in claim_lower or "snow" in claim_lower or "high wind" in claim_lower:
                weather_score += 0.3

        home_avail = max(0.0, home_avail)
        away_avail = max(0.0, away_avail)
        weather_score = min(1.0, weather_score)

        return MatchFeatureSet(
            match_id=match_id,
            home_availability_ratio=home_avail,
            away_availability_ratio=away_avail,
            home_rest_days=home_rest,
            away_rest_days=away_rest,
            weather_impact_score=weather_score,
            evidence_quality_score=validation_report.average_reliability,
            is_complete=True
        )
