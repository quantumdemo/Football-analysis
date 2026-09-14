"""Unit tests for Stage 22 Continuous Evaluation & Calibration Engine."""

import pytest
from datetime import datetime, timezone
from src.backtesting.shadow_trader import ShadowPredictionRecord
from src.models.continuous_evaluator import ContinuousEvaluator, RollingPerformanceMetrics, ModelDriftReport


@pytest.fixture
def evaluator():
    return ContinuousEvaluator(baseline_log_loss=0.50, drift_threshold_pct=15.0)


def create_sample_settled_record(match_id: str, p_home: float, outcome: str, evidence_count: int = 3) -> ShadowPredictionRecord:
    now = datetime.now(timezone.utc)
    p_away = round((1.0 - p_home) * 0.5, 4)
    p_draw = round(1.0 - p_home - p_away, 4)

    return ShadowPredictionRecord(
        prediction_id=f"shadow_{match_id}",
        match_id=match_id,
        home_team_id="HOME",
        away_team_id="AWAY",
        prediction_timestamp=now,
        kickoff_time=now,
        model_version="v1.0.0",
        feature_version="v1.0.0",
        decision="BET",
        probabilities_1x2={"home_win": p_home, "draw": p_draw, "away_win": p_away},
        expected_goals={"home": 1.5, "away": 1.0},
        approved_candidate_markets=["1X2"],
        evidence_count=evidence_count,
        is_settled=True,
        settled_timestamp=now,
        actual_outcome=outcome
    )


def test_ingest_and_calculate_rolling_metrics(evaluator):
    rec1 = create_sample_settled_record("M1", 0.70, "HOME")
    rec2 = create_sample_settled_record("M2", 0.60, "HOME")

    evaluator.ingest_settled_prediction(rec1)
    evaluator.ingest_settled_prediction(rec2)

    metrics = evaluator.calculate_rolling_metrics(window_size=10)

    assert isinstance(metrics, RollingPerformanceMetrics)
    assert metrics.window_size == 2
    assert metrics.rolling_log_loss > 0.0
    assert metrics.rolling_brier_score > 0.0


def test_model_drift_detection(evaluator):
    # Ingest records with bad predictions -> high log loss causing model drift
    for i in range(5):
        rec = create_sample_settled_record(f"M_BAD_{i}", 0.10, "HOME")  # Low home probability, actual HOME
        evaluator.ingest_settled_prediction(rec)

    drift_report = evaluator.evaluate_model_drift(model_version_id="v1.0.0", window_size=5)

    assert isinstance(drift_report, ModelDriftReport)
    assert drift_report.model_drift_detected is True
    assert drift_report.flagged_for_manual_review is True
    assert "1X2 Result Market" in drift_report.weak_performing_markets
    assert len(drift_report.review_recommendations) > 0


def test_no_drift_when_performing_well(evaluator):
    # Ingest records with good predictions -> low log loss
    for i in range(5):
        rec = create_sample_settled_record(f"M_GOOD_{i}", 0.85, "HOME")  # High home probability, actual HOME
        evaluator.ingest_settled_prediction(rec)

    drift_report = evaluator.evaluate_model_drift(model_version_id="v1.0.0", window_size=5)

    assert drift_report.model_drift_detected is False
    assert drift_report.flagged_for_manual_review is False
