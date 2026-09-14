"""Calibration & Model Improvement Engine.

Aligns predicted probabilities with empirical observed frequencies using Platt scaling / temperature scaling
and time-aware train/validation/test splitting. Tracks versions for models, features, data, and evaluation results.
"""

from dataclasses import dataclass, field
from datetime import datetime
import math
from typing import List, Dict, Any, Tuple, Optional
from src.backtesting.backtester import HistoricalMatchRecord, BacktestMetricReport


@dataclass
class ModelVersionRecord:
    """Metadata record for a registered model version."""
    model_version_id: str
    feature_set_version: str
    config_version: str
    calibration_method: str
    trained_at: datetime
    train_count: int
    val_count: int
    test_count: int
    test_metrics: Dict[str, float]


class TimeAwareDatasetSplitter:
    """Splits historical match records chronologically into Train, Validation, and Test sets."""

    def split(
        self,
        records: List[HistoricalMatchRecord],
        train_ratio: float = 0.60,
        val_ratio: float = 0.20
    ) -> Tuple[List[HistoricalMatchRecord], List[HistoricalMatchRecord], List[HistoricalMatchRecord]]:
        if not records:
            return [], [], []

        # Sort strictly chronologically by match scheduled time
        sorted_records = sorted(records, key=lambda r: r.match.scheduled_time)

        n = len(sorted_records)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        train_set = sorted_records[:train_end]
        val_set = sorted_records[train_end:val_end]
        test_set = sorted_records[val_end:]

        return train_set, val_set, test_set


class ProbabilityCalibrator:
    """Probability calibrator using temperature scaling and Platt scaling."""

    def __init__(self, temperature: float = 1.0):
        self.temperature = temperature  # Temperature parameter (T > 0)

    def fit_temperature(
        self,
        uncalibrated_probabilities: List[Dict[str, float]],
        actual_outcomes: List[str]
    ) -> float:
        """Fits optimal temperature T to minimize log loss on validation set."""
        if not uncalibrated_probabilities or not actual_outcomes:
            self.temperature = 1.0
            return 1.0

        best_t = 1.0
        best_loss = float("inf")

        # Grid search over T in range [0.5, 2.5]
        for t_step in range(5, 26):
            t = t_step / 10.0
            loss_sum = 0.0

            for p_dict, outcome in zip(uncalibrated_probabilities, actual_outcomes):
                # Apply temperature scaling to logits
                logits = {k: math.log(max(1e-5, v)) / t for k, v in p_dict.items()}
                max_l = max(logits.values())
                exp_logits = {k: math.exp(v - max_l) for k, v in logits.items()}
                denom = sum(exp_logits.values())
                p_calibrated = {k: v / denom for k, v in exp_logits.items()}

                p_act = max(1e-5, p_calibrated.get(outcome.upper(), 0.33333))
                loss_sum += -math.log(p_act)

            if loss_sum < best_loss:
                best_loss = loss_sum
                best_t = t

        self.temperature = best_t
        return best_t

    def calibrate(self, probabilities: Dict[str, float]) -> Dict[str, float]:
        """Calibrates input probabilities using fitted temperature."""
        if self.temperature == 1.0 or not probabilities:
            return probabilities

        logits = {k: math.log(max(1e-5, v)) / self.temperature for k, v in probabilities.items()}
        max_l = max(logits.values())
        exp_logits = {k: math.exp(v - max_l) for k, v in logits.items()}
        denom = sum(exp_logits.values())

        return {k: round(v / denom, 5) for k, v in exp_logits.items()}


class ModelVersionRegistry:
    """Registry tracking versions of models, features, config, and evaluation metric results."""

    def __init__(self):
        self.history: Dict[str, ModelVersionRecord] = {}

    def register_version(
        self,
        model_version_id: str,
        feature_set_version: str,
        config_version: str,
        calibration_method: str,
        trained_at: datetime,
        train_count: int,
        val_count: int,
        test_count: int,
        test_metrics: Dict[str, float]
    ) -> ModelVersionRecord:
        record = ModelVersionRecord(
            model_version_id=model_version_id,
            feature_set_version=feature_set_version,
            config_version=config_version,
            calibration_method=calibration_method,
            trained_at=trained_at,
            train_count=train_count,
            val_count=val_count,
            test_count=test_count,
            test_metrics=test_metrics
        )
        self.history[model_version_id] = record
        return record

    def get_version(self, model_version_id: str) -> Optional[ModelVersionRecord]:
        return self.history.get(model_version_id)
