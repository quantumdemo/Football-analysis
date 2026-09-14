"""Unit tests for Stage 12 Calibration & Model Improvement Engine."""

import pytest
from datetime import datetime, timedelta, timezone
from src.match.identifier import MatchIdentifier
from src.backtesting.backtester import HistoricalMatchRecord
from src.models.calibration import ProbabilityCalibrator, ModelVersionRegistry, TimeAwareDatasetSplitter


def test_time_aware_dataset_splitter():
    splitter = TimeAwareDatasetSplitter()
    now = datetime.now(timezone.utc)

    records = []
    for i in range(10):
        match_time = now - timedelta(days=10-i)
        match = MatchIdentifier(f"M_{i}", "HOME", "AWAY", match_time, "League")
        records.append(HistoricalMatchRecord(
            match=match,
            raw_evidence=[],
            historical_stats={},
            actual_outcome="HOME",
            actual_home_goals=1,
            actual_away_goals=0
        ))

    train, val, test = splitter.split(records, train_ratio=0.60, val_ratio=0.20)

    assert len(train) == 6
    assert len(val) == 2
    assert len(test) == 2
    # Verify chronological order
    assert train[-1].match.scheduled_time < val[0].match.scheduled_time
    assert val[-1].match.scheduled_time < test[0].match.scheduled_time


def test_probability_calibrator_fitting():
    calibrator = ProbabilityCalibrator()

    uncalibrated = [
        {"HOME": 0.80, "DRAW": 0.10, "AWAY": 0.10},
        {"HOME": 0.75, "DRAW": 0.15, "AWAY": 0.10},
        {"HOME": 0.20, "DRAW": 0.30, "AWAY": 0.50}
    ]
    outcomes = ["HOME", "HOME", "AWAY"]

    fitted_t = calibrator.fit_temperature(uncalibrated, outcomes)
    assert 0.5 <= fitted_t <= 2.5

    calibrated_probs = calibrator.calibrate({"HOME": 0.80, "DRAW": 0.10, "AWAY": 0.10})
    assert round(sum(calibrated_probs.values()), 4) == 1.0


def test_model_version_registry():
    registry = ModelVersionRegistry()
    now = datetime.now(timezone.utc)

    rec = registry.register_version(
        model_version_id="v1.2.0",
        feature_set_version="v1.1",
        config_version="v1.0",
        calibration_method="temperature_scaling",
        trained_at=now,
        train_count=100,
        val_count=20,
        test_count=20,
        test_metrics={"accuracy": 0.72, "log_loss": 0.55, "brier_score": 0.18}
    )

    retrieved = registry.get_version("v1.2.0")
    assert retrieved is not None
    assert retrieved.model_version_id == "v1.2.0"
    assert retrieved.test_metrics["accuracy"] == 0.72
