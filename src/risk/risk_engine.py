"""Risk, Confidence & No-Bet Engine for preventing forced selections.

Evaluates data quality, model disagreement, lineup/availability uncertainty, source conflicts,
and model reliability. Returns candidate markets only when all conditions are satisfied;
otherwise returns NO_BET / INSUFFICIENT EVIDENCE.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from src.validation.validator import ValidationReport, EvidenceValidationState
from src.models.forecast import ForecastDistribution
from src.features.feature_engine import MatchFeatureSet
from src.sentiment.sentiment_analyzer import ContextSentimentReport


@dataclass
class RiskEvaluation:
    """Outcome of risk assessment for match selection."""
    match_id: str
    decision: str  # "BET" or "NO_BET"
    reason: str
    confidence_score: float
    uncertainty_score: float
    approved_candidate_markets: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)


class RiskEngine:
    """Evaluates multi-factor risk and outputs NO_BET when evidence fails strict thresholds."""

    def __init__(
        self,
        min_confidence: float = 0.60,
        max_uncertainty: float = 0.40,
        min_reliability: float = 0.60,
        min_availability: float = 0.70
    ):
        self.min_confidence = min_confidence
        self.max_uncertainty = max_uncertainty
        self.min_reliability = min_reliability
        self.min_availability = min_availability

    def evaluate(
        self,
        match_id: str,
        validation_report: ValidationReport,
        feature_set: MatchFeatureSet,
        forecast: ForecastDistribution,
        sentiment_report: Optional[ContextSentimentReport] = None,
        candidate_markets: Optional[List[str]] = None
    ) -> RiskEvaluation:
        if candidate_markets is None:
            candidate_markets = ["1X2", "Over_Under_2.5", "BTTS"]

        risk_factors: List[str] = []

        # 1. Validation report state check
        if not validation_report.is_valid:
            if validation_report.overall_state == EvidenceValidationState.CONFLICTING:
                risk_factors.append(f"Source contradiction conflict detected: {validation_report.conflicting_claims}")
            if validation_report.overall_state == EvidenceValidationState.UNAVAILABLE:
                risk_factors.append(f"Missing required core data fields: {validation_report.missing_data_fields}")
            if not validation_report.freshness_ok:
                risk_factors.append("Evidence staleness check failed.")

        # 2. Source reliability check
        if validation_report.average_reliability < self.min_reliability:
            risk_factors.append(
                f"Average evidence reliability ({validation_report.average_reliability:.2f}) below threshold ({self.min_reliability:.2f})"
            )

        # 3. Lineup / Availability uncertainty check
        if feature_set.home_availability_ratio < self.min_availability:
            risk_factors.append(f"Home player availability low ({feature_set.home_availability_ratio:.2f})")
        if feature_set.away_availability_ratio < self.min_availability:
            risk_factors.append(f"Away player availability low ({feature_set.away_availability_ratio:.2f})")

        # 4. Model confidence & uncertainty check
        adjusted_confidence = forecast.model_confidence
        if sentiment_report:
            adjusted_confidence += sentiment_report.secondary_confidence_modifier

        if adjusted_confidence < self.min_confidence:
            risk_factors.append(
                f"Model confidence ({adjusted_confidence:.2f}) below minimum required ({self.min_confidence:.2f})"
            )
        if forecast.uncertainty_score > self.max_uncertainty:
            risk_factors.append(
                f"Model uncertainty ({forecast.uncertainty_score:.2f}) exceeds maximum allowed ({self.max_uncertainty:.2f})"
            )

        # Decision rule
        if risk_factors:
            return RiskEvaluation(
                match_id=match_id,
                decision="NO_BET",
                reason="NO BET / INSUFFICIENT EVIDENCE: " + " | ".join(risk_factors),
                confidence_score=round(adjusted_confidence, 2),
                uncertainty_score=forecast.uncertainty_score,
                approved_candidate_markets=[],
                risk_factors=risk_factors
            )

        return RiskEvaluation(
            match_id=match_id,
            decision="BET",
            reason="All risk and validation conditions satisfied. Candidate markets approved.",
            confidence_score=round(adjusted_confidence, 2),
            uncertainty_score=forecast.uncertainty_score,
            approved_candidate_markets=candidate_markets,
            risk_factors=[]
        )
