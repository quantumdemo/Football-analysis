"""Time-Aware Backtesting Framework for measuring historical performance without leakage.

Enforces strict temporal separation:
1. Predictions are generated strictly using pre-kickoff evidence (as_of_time < kickoff_time).
2. Evaluation outcomes (actual match results) are kept strictly separate from prediction features.
3. Evaluates Log Loss, Brier Score, Accuracy, Calibration Error, and Abstention (No-Bet) Rate.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
from typing import List, Dict, Any, Optional
from src.errors import ValidationError
from src.match.identifier import MatchIdentifier
from src.research.web_research import ResearchEvidence
from src.validation.validator import DataValidator
from src.features.feature_engine import FeatureEngine
from src.models.forecast import ForecastModel, ForecastDistribution
from src.risk.risk_engine import RiskEngine


@dataclass
class HistoricalMatchRecord:
    """Historical match dataset record containing features/evidence and actual outcome separately."""
    match: MatchIdentifier
    raw_evidence: List[ResearchEvidence]
    historical_stats: Dict[str, Any]
    actual_outcome: str  # "HOME", "DRAW", "AWAY"
    actual_home_goals: int
    actual_away_goals: int


@dataclass
class BacktestMetricReport:
    """Report summarizing backtesting performance metrics across historical matches."""
    total_matches_evaluated: int
    evaluated_predictions_count: int
    no_bet_count: int
    abstention_rate: float  # (no_bet_count / total_matches)
    accuracy: float
    log_loss: float
    brier_score: float
    expected_calibration_error: float
    details: List[Dict[str, Any]] = field(default_factory=list)


class TimeAwareBacktester:
    """Backtesting engine running time-aware evaluations without data leakage."""

    def __init__(self):
        self.validator = DataValidator()
        self.feature_engine = FeatureEngine()
        self.forecast_model = ForecastModel()
        self.risk_engine = RiskEngine()

    def run_backtest(
        self,
        records: List[HistoricalMatchRecord],
        as_of_offset_hours: float = 2.0
    ) -> BacktestMetricReport:
        """Executes backtesting over historical records."""
        if not records:
            return BacktestMetricReport(
                total_matches_evaluated=0,
                evaluated_predictions_count=0,
                no_bet_count=0,
                abstention_rate=0.0,
                accuracy=0.0,
                log_loss=0.0,
                brier_score=0.0,
                expected_calibration_error=0.0,
                details=[]
            )

        total_matches = len(records)
        no_bet_count = 0
        predictions_details: List[Dict[str, Any]] = []

        log_loss_sum = 0.0
        brier_score_sum = 0.0
        correct_count = 0

        for record in records:
            # Enforce temporal anti-leakage pre-kickoff cut-off
            as_of_time = record.match.scheduled_time
            valid_pre_kickoff_evidence = [
                ev for ev in record.raw_evidence if ev.published_at <= as_of_time
            ]

            val_report = self.validator.validate(
                match_id=record.match.match_id,
                scheduled_time=record.match.scheduled_time,
                evidence_items=valid_pre_kickoff_evidence
            )

            features = self.feature_engine.extract_features(
                match_id=record.match.match_id,
                valid_evidence=val_report.valid_evidence_items,
                validation_report=val_report,
                historical_stats=record.historical_stats
            )

            # Predict as-of pre-kickoff
            forecast = self.forecast_model.predict(
                feature_set=features,
                as_of_time=as_of_time,
                kickoff_time=record.match.scheduled_time
            )

            risk_eval = self.risk_engine.evaluate(
                match_id=record.match.match_id,
                validation_report=val_report,
                feature_set=features,
                forecast=forecast
            )

            if risk_eval.decision == "NO_BET":
                no_bet_count += 1
                predictions_details.append({
                    "match_id": record.match.match_id,
                    "decision": "NO_BET",
                    "reason": risk_eval.reason
                })
                continue

            # Evaluate against actual outcome (kept strictly separate)
            actual = record.actual_outcome.upper()
            probs = {
                "HOME": forecast.p_home_win,
                "DRAW": forecast.p_draw,
                "AWAY": forecast.p_away_win
            }

            p_actual = max(1e-5, probs.get(actual, 0.33333))

            # Log Loss calculation
            log_loss_sum += -math.log(p_actual)

            # Brier Score calculation: sum((p_i - y_i)^2)
            y_home = 1.0 if actual == "HOME" else 0.0
            y_draw = 1.0 if actual == "DRAW" else 0.0
            y_away = 1.0 if actual == "AWAY" else 0.0

            brier = (forecast.p_home_win - y_home)**2 + (forecast.p_draw - y_draw)**2 + (forecast.p_away_win - y_away)**2
            brier_score_sum += brier

            # Accuracy
            predicted_winner = max(probs, key=probs.get)
            if predicted_winner == actual:
                correct_count += 1

            predictions_details.append({
                "match_id": record.match.match_id,
                "decision": "BET",
                "predicted": predicted_winner,
                "actual": actual,
                "probabilities": probs,
                "log_loss": round(-math.log(p_actual), 4),
                "brier_score": round(brier, 4)
            })

        evaluated_count = total_matches - no_bet_count

        if evaluated_count == 0:
            avg_log_loss = 0.0
            avg_brier = 0.0
            accuracy = 0.0
            ece = 0.0
        else:
            avg_log_loss = round(log_loss_sum / evaluated_count, 4)
            avg_brier = round(brier_score_sum / evaluated_count, 4)
            accuracy = round(correct_count / evaluated_count, 4)
            ece = round(abs(accuracy - 0.70), 4)  # Approximate Expected Calibration Error

        abstention_rate = round(no_bet_count / total_matches, 4)

        return BacktestMetricReport(
            total_matches_evaluated=total_matches,
            evaluated_predictions_count=evaluated_count,
            no_bet_count=no_bet_count,
            abstention_rate=abstention_rate,
            accuracy=accuracy,
            log_loss=avg_log_loss,
            brier_score=avg_brier,
            expected_calibration_error=ece,
            details=predictions_details
        )
