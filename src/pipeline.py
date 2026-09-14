"""Full End-to-End Integrated Football AI Pipeline orchestrating Stages 1 through 13."""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.config import SystemConfig
from src.logging import setup_logger
from src.match.identifier import MatchIdentifier
from src.match.resolver import MatchResolver
from src.research.web_research import ResearchCollector, ResearchEvidence
from src.validation.validator import DataValidator
from src.features.feature_engine import FeatureEngine
from src.models.forecast import ForecastModel
from src.markets.market_mapper import MarketRegistry, MarketMapper
from src.markets.specialist_markets import SpecialistMarketEngine
from src.sentiment.sentiment_analyzer import ContextSentimentAnalyzer
from src.risk.risk_engine import RiskEngine
from src.reporting.report_generator import ReportGenerator, AuditableMatchReport


class FootballAIPipeline:
    """Orchestrates the complete 14-stage Football AI System pipeline."""

    def __init__(self, config_path: str = "config/config.json"):
        self.config = SystemConfig.load_from_file(config_path)
        self.logger = setup_logger("FootballAIPipeline")

        self.resolver = MatchResolver()
        self.research_collector = ResearchCollector(min_reliability=self.config.min_reliability_score)
        self.validator = DataValidator(max_age_hours=self.config.freshness_threshold_hours, min_reliability=self.config.min_reliability_score)
        self.feature_engine = FeatureEngine()
        self.forecast_model = ForecastModel()
        self.market_registry = MarketRegistry()
        self.market_mapper = MarketMapper(self.market_registry)
        self.specialist_engine = SpecialistMarketEngine()
        self.sentiment_analyzer = ContextSentimentAnalyzer()
        self.risk_engine = RiskEngine(min_reliability=self.config.min_reliability_score)
        self.report_generator = ReportGenerator(model_version=self.config.version)

        self.logger.info("Football AI Pipeline fully initialized.")

    def process_match(
        self,
        raw_match_input: Dict[str, Any],
        raw_evidence_items: List[Dict[str, Any]],
        historical_stats: Optional[Dict[str, Any]] = None,
        as_of_time: Optional[datetime] = None
    ) -> AuditableMatchReport:
        """Executes the full pipeline for a match fixture."""
        # Stage 1 & 2: Match Identification & Resolution
        match = self.resolver.resolve(raw_match_input)
        self.logger.info(f"Processing match ID: {match.match_id} ({match.home_team_id} vs {match.away_team_id})")

        # Stage 3: Web Research Collection & Gambling Source Exclusion
        collected_evidence = self.research_collector.collect_evidence(raw_evidence_items)

        # Stage 4: Data Validation & State Tracking
        validation_report = self.validator.validate(
            match_id=match.match_id,
            scheduled_time=match.scheduled_time,
            evidence_items=collected_evidence
        )

        # Stage 5: Feature Extraction (no reputation or odds)
        features = self.feature_engine.extract_features(
            match_id=match.match_id,
            valid_evidence=validation_report.valid_evidence_items,
            validation_report=validation_report,
            historical_stats=historical_stats
        )

        # Stage 6: Core Probabilistic Forecasting
        forecast = self.forecast_model.predict(
            feature_set=features,
            as_of_time=as_of_time or match.scheduled_time,
            kickoff_time=match.scheduled_time
        )

        # Stage 7: Market Mapping
        market_1x2 = self.market_mapper.map_market(forecast, "1x2_(home___draw___away)")
        market_ou = self.market_mapper.map_market(forecast, "over_under")
        market_dc = self.market_mapper.map_market(forecast, "double_chance")
        mappings = [market_1x2, market_ou, market_dc]

        # Stage 9: Context & Secondary Sentiment
        sentiment_report = self.sentiment_analyzer.analyze(
            match_id=match.match_id,
            valid_evidence=validation_report.valid_evidence_items
        )

        # Stage 10: Multi-Factor Risk & No-Bet Assessment
        risk_evaluation = self.risk_engine.evaluate(
            match_id=match.match_id,
            validation_report=validation_report,
            feature_set=features,
            forecast=forecast,
            sentiment_report=sentiment_report
        )

        # Stage 13: Final Auditable Report Generation
        report = self.report_generator.generate_auditable_report(
            match=match,
            validation_report=validation_report,
            feature_set=features,
            forecast=forecast,
            risk_eval=risk_evaluation,
            market_mappings=mappings,
            sentiment_report=sentiment_report
        )

        self.logger.info(f"Report generated for match ID {match.match_id} with decision: {risk_evaluation.decision}")
        return report
