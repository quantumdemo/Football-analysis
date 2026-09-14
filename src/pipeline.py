"""End-to-End Football AI Pipeline orchestrating stages from input to final report."""

from datetime import datetime
from typing import List, Dict, Any
from src.match.identifier import MatchIdentifier, create_match_identifier
from src.research.web_research import ResearchEvidence, ResearchIngestor
from src.validation.validator import DataValidator
from src.features.feature_engine import FeatureEngine
from src.models.forecast import ForecastModel
from src.risk.risk_engine import RiskEngine
from src.reporting.report_generator import ReportGenerator


class FootballAIPipeline:
    """Orchestrates the 14-stage Football AI pipeline."""

    def __init__(self):
        self.ingestor = ResearchIngestor()
        self.validator = DataValidator()
        self.feature_engine = FeatureEngine()
        self.forecast_model = ForecastModel()
        self.risk_engine = RiskEngine()
        self.report_generator = ReportGenerator()

    def process_match(
        self,
        match_id: str,
        home_team_id: str,
        away_team_id: str,
        scheduled_time: datetime,
        competition: str,
        raw_evidence: List[ResearchEvidence]
    ) -> Dict[str, Any]:
        # Stage 1 & 2: Match Identification
        match_info = create_match_identifier(
            match_id=match_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            scheduled_time=scheduled_time,
            competition=competition
        )

        # Stage 3 & 4: Web Research Ingestion & Data Validation
        validation_report = self.validator.validate(
            match_id=match_id,
            scheduled_time=scheduled_time,
            evidence_items=raw_evidence
        )

        # Stage 5: Feature Engine (receives strictly validated evidence items)
        features = self.feature_engine.extract_features(
            match_id=match_id,
            valid_evidence=validation_report.valid_evidence_items,
            validation_report=validation_report
        )

        # Stage 6 & 7: Forecast Models & Probability Engine
        forecast = self.forecast_model.predict(features)

        # Stage 10: Risk/No-Bet Decision
        risk_decision = self.risk_engine.evaluate(
            match_id=match_id,
            validation_report=validation_report,
            forecast=forecast
        )

        # Stage 11: Final Report
        report = self.report_generator.generate_report(
            match=match_info,
            validation=validation_report,
            forecast=forecast,
            risk=risk_decision
        )

        return report
