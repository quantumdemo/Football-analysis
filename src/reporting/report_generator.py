"""Final Reporting Engine producing auditable user-facing match reports.

Compiles match verification, evidence attribution, statistics, squad/news, context,
probabilistic forecasts (strictly as probabilities, never certainty), candidate markets,
risk/NO_BET status, data freshness, and model versioning.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.match.identifier import MatchIdentifier
from src.validation.validator import ValidationReport
from src.features.feature_engine import MatchFeatureSet
from src.models.forecast import ForecastDistribution
from src.markets.market_mapper import MarketMappingReport
from src.sentiment.sentiment_analyzer import ContextSentimentReport
from src.risk.risk_engine import RiskEvaluation


@dataclass
class MatchReport:
    """Legacy/Skeleton match report container."""
    match_id: str
    decision: str
    report_data: Dict[str, Any]


@dataclass
class AuditableMatchReport:
    """Auditable match intelligence report."""
    match_id: str
    match_verification: Dict[str, Any]
    validation_summary: Dict[str, Any]
    objective_statistics: Dict[str, Any]
    context_and_news: Dict[str, Any]
    probabilistic_forecast: Dict[str, Any]
    mapped_market_candidates: List[Dict[str, Any]]
    risk_and_nobet_assessment: Dict[str, Any]
    audit_metadata: Dict[str, Any]
    disclaimer: str = "PROBABILISTIC FORECAST ONLY. ESTIMATES ARE PROBABILISTIC AND DO NOT CONSTITUTE GUARANTEED WINS OR CERTAINTY."

    def to_dict(self) -> Dict[str, Any]:
        """Converts report to dictionary representation."""
        return asdict(self)


class ReportGenerator:
    """Generates structured, auditable match intelligence reports."""

    def __init__(self, model_version: str = "1.0.0", feature_version: str = "1.0.0"):
        self.model_version = model_version
        self.feature_version = feature_version

    def generate_auditable_report(
        self,
        match: MatchIdentifier,
        validation_report: ValidationReport,
        feature_set: MatchFeatureSet,
        forecast: ForecastDistribution,
        risk_eval: RiskEvaluation,
        market_mappings: Optional[List[MarketMappingReport]] = None,
        sentiment_report: Optional[ContextSentimentReport] = None
    ) -> AuditableMatchReport:
        if market_mappings is None:
            market_mappings = []

        # 1. Match Verification & Identifiers
        match_verification = {
            "match_id": match.match_id,
            "home_team_id": match.home_team_id,
            "away_team_id": match.away_team_id,
            "scheduled_time": match.scheduled_time.isoformat(),
            "competition": match.competition,
            "venue": match.venue,
            "season": match.season,
            "status": match.status.value,
            "verification_notes": match.verification_notes
        }

        # 2. Validation & Evidence Summary
        validation_summary = {
            "is_valid": validation_report.is_valid,
            "overall_state": validation_report.overall_state.value,
            "freshness_ok": validation_report.freshness_ok,
            "valid_evidence_count": validation_report.valid_evidence_count,
            "duplicate_claims_removed": validation_report.duplicate_claims_removed,
            "prohibited_items_rejected": validation_report.prohibited_items_rejected,
            "average_reliability": validation_report.average_reliability,
            "missing_data_fields": validation_report.missing_data_fields,
            "conflicting_claims": validation_report.conflicting_claims,
            "evidence_items": [
                {
                    "evidence_id": item.evidence.evidence_id,
                    "claim": item.evidence.claim,
                    "source_url": item.evidence.source_url,
                    "published_at": item.evidence.published_at.isoformat(),
                    "reliability": item.evidence.reliability_score,
                    "state": item.state.value
                } for item in validation_report.validated_items
            ]
        }

        # 3. Objective Statistics
        objective_statistics = {
            "home_form_ppg": feature_set.home_form_ppg,
            "away_form_ppg": feature_set.away_form_ppg,
            "home_goals_scored": feature_set.home_goals_scored_per_game,
            "home_goals_conceded": feature_set.home_goals_conceded_per_game,
            "away_goals_scored": feature_set.away_goals_scored_per_game,
            "away_goals_conceded": feature_set.away_goals_conceded_per_game,
            "home_xg": feature_set.home_xg_per_game,
            "away_xg": feature_set.away_xg_per_game,
            "home_availability_ratio": feature_set.home_availability_ratio,
            "away_availability_ratio": feature_set.away_availability_ratio,
            "home_rest_days": feature_set.home_rest_days,
            "away_rest_days": feature_set.away_rest_days,
            "weather_impact_score": feature_set.weather_impact_score
        }

        # 4. Context & Sentiment
        context_and_news = {
            "fact_count": sentiment_report.fact_count if sentiment_report else 0,
            "rumor_count": sentiment_report.rumor_count if sentiment_report else 0,
            "home_context_score": sentiment_report.home_context_score if sentiment_report else 0.0,
            "away_context_score": sentiment_report.away_context_score if sentiment_report else 0.0,
            "secondary_modifier": sentiment_report.secondary_confidence_modifier if sentiment_report else 0.0
        }

        # 5. Probabilistic Forecast
        probabilistic_forecast = {
            "outcome_1x2_probabilities": {
                "home_win": forecast.p_home_win,
                "draw": forecast.p_draw,
                "away_win": forecast.p_away_win
            },
            "expected_goals": {
                "home": forecast.expected_home_goals,
                "away": forecast.expected_away_goals
            },
            "over_under_2_5_probabilities": {
                "over": forecast.p_over_2_5_goals,
                "under": forecast.p_under_2_5_goals
            },
            "model_confidence": forecast.model_confidence,
            "uncertainty_score": forecast.uncertainty_score
        }

        # 6. Mapped Markets
        mapped_market_candidates = [
            {
                "market_id": m.market_id,
                "market_name": m.market_name,
                "settlement_period": m.settlement_period,
                "is_supported": m.is_supported,
                "selections": [
                    {
                        "selection": sel.selection_name,
                        "projected_probability": sel.projected_probability
                    } for sel in m.selection_forecasts
                ]
            } for m in market_mappings
        ]

        # 7. Risk & No-Bet Assessment
        risk_and_nobet_assessment = {
            "decision": risk_eval.decision,
            "reason": risk_eval.reason,
            "confidence_score": risk_eval.confidence_score,
            "uncertainty_score": risk_eval.uncertainty_score,
            "approved_candidate_markets": risk_eval.approved_candidate_markets,
            "risk_factors": risk_eval.risk_factors
        }

        # 8. Audit Metadata
        audit_metadata = {
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "model_version": self.model_version,
            "feature_version": self.feature_version,
            "data_freshness_ok": validation_report.freshness_ok
        }

        return AuditableMatchReport(
            match_id=match.match_id,
            match_verification=match_verification,
            validation_summary=validation_summary,
            objective_statistics=objective_statistics,
            context_and_news=context_and_news,
            probabilistic_forecast=probabilistic_forecast,
            mapped_market_candidates=mapped_market_candidates,
            risk_and_nobet_assessment=risk_and_nobet_assessment,
            audit_metadata=audit_metadata
        )
