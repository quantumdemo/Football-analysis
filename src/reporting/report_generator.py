"""Reporting module generating structured intelligence reports."""

from dataclasses import dataclass
from typing import Dict, Any, List
from src.match.identifier import MatchIdentifier
from src.validation.validator import ValidationReport
from src.models.forecast import ForecastDistribution
from src.risk.risk_engine import RiskEvaluation


class ReportGenerator:
    """Generates structured JSON-like or text reports for match intelligence."""

    def generate_report(
        self,
        match: MatchIdentifier,
        validation: ValidationReport,
        forecast: ForecastDistribution,
        risk: RiskEvaluation
    ) -> Dict[str, Any]:
        return {
            "match_id": match.match_id,
            "home_team_id": match.home_team_id,
            "away_team_id": match.away_team_id,
            "scheduled_time": match.scheduled_time.isoformat(),
            "competition": match.competition,
            "validation_status": {
                "is_valid": validation.is_valid,
                "missing_fields": validation.missing_data_fields,
                "conflicts": validation.conflicting_claims,
                "prohibited_rejected": validation.prohibited_items_rejected,
                "evidence_count": validation.valid_evidence_count,
                "avg_reliability": validation.average_reliability
            },
            "forecast": {
                "p_home_win": forecast.p_home_win,
                "p_draw": forecast.p_draw,
                "p_away_win": forecast.p_away_win,
                "confidence": forecast.model_confidence
            },
            "risk_assessment": {
                "decision": risk.decision,
                "reason": risk.reason,
                "confidence": risk.confidence_score
            },
            "disclaimer": "PROBABILISTIC FORECAST ONLY. NO GUARANTEED WINS OR CERTAINTY."
        }
