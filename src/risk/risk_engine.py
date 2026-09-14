"""Risk engine enforcing NO BET triggers when evidence is insufficient, conflicting, or low-quality."""

from dataclasses import dataclass
from typing import Optional, Any
from src.validation.validator import ValidationReport
from src.models.forecast import ForecastDistribution


@dataclass
class RiskEvaluation:
    """Outcome of risk assessment."""
    match_id: str
    decision: str  # "BET" or "NO_BET"
    reason: str
    confidence_score: float


class RiskEngine:
    """Assesses risk factors and outputs NO_BET when evidence fails thresholds."""

    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence

    def evaluate(
        self,
        match_id: str,
        validation_report: ValidationReport,
        forecast: ForecastDistribution
    ) -> RiskEvaluation:
        # Check validation failure or missing data
        if not validation_report.is_valid:
            reasons = []
            if validation_report.missing_data_fields:
                reasons.append(f"Missing required categories: {validation_report.missing_data_fields}")
            if validation_report.conflicting_claims:
                reasons.append(f"Conflicting claims detected: {validation_report.conflicting_claims}")
            if validation_report.average_reliability < 0.5:
                reasons.append(f"Average evidence reliability low: {validation_report.average_reliability:.2f}")
            if not reasons:
                reasons.append("Validation failed due to staleness or post-kickoff evidence")

            return RiskEvaluation(
                match_id=match_id,
                decision="NO_BET",
                reason="INSUFFICIENT EVIDENCE / VALIDATION FAILURE: " + " | ".join(reasons),
                confidence_score=forecast.model_confidence
            )

        # Check model confidence
        if forecast.model_confidence < self.min_confidence:
            return RiskEvaluation(
                match_id=match_id,
                decision="NO_BET",
                reason=f"Model confidence ({forecast.model_confidence:.2f}) below threshold ({self.min_confidence:.2f})",
                confidence_score=forecast.model_confidence
            )

        return RiskEvaluation(
            match_id=match_id,
            decision="BET",
            reason="All validation checks passed with sufficient evidence confidence.",
            confidence_score=forecast.model_confidence
        )
