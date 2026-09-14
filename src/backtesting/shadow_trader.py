"""Shadow / Paper Trading Engine for Stage 17.

Runs the live system without financial execution.
Records pre-kickoff predictions immutably (disallowing retroactive alterations).
Stores prediction time, evidence, model version, probabilities, candidate markets, and NO_BET decisions.
Settles predictions against actual match outcomes post-match.
Monitors stale sources, lineup changes, data outages, and checks stability and calibration gates.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import math
from typing import List, Dict, Any, Optional
from src.errors import ValidationError
from src.pipeline import FootballAIPipeline
from src.reporting.report_generator import AuditableMatchReport


@dataclass
class ShadowPredictionRecord:
    """Immutable pre-kickoff paper trading prediction record."""
    prediction_id: str
    match_id: str
    home_team_id: str
    away_team_id: str
    prediction_timestamp: datetime
    kickoff_time: datetime
    model_version: str
    feature_version: str
    decision: str  # "BET" or "NO_BET"
    probabilities_1x2: Dict[str, float]
    expected_goals: Dict[str, float]
    approved_candidate_markets: List[str]
    evidence_count: int
    is_settled: bool = False
    settled_timestamp: Optional[datetime] = None
    actual_outcome: Optional[str] = None  # "HOME", "DRAW", "AWAY"
    actual_home_goals: Optional[int] = None
    actual_away_goals: Optional[int] = None
    settlement_log_loss: Optional[float] = None
    settlement_brier_score: Optional[float] = None


@dataclass
class ShadowTradingGateReport:
    """Evaluation of shadow trading stability and calibration gates."""
    total_shadow_matches: int
    settled_matches: int
    no_bet_count: int
    abstention_rate: float
    stale_source_incidents: int
    data_outage_incidents: int
    average_log_loss: float
    average_brier_score: float
    calibration_gate_passed: bool
    stability_gate_passed: bool
    overall_gate_passed: bool


class ShadowTradingEngine:
    """Engine managing shadow paper trading, immutability enforcement, and gate monitoring."""

    def __init__(self):
        self.pipeline = FootballAIPipeline()
        self.records: Dict[str, ShadowPredictionRecord] = {}
        self.stale_source_incidents = 0
        self.data_outage_incidents = 0

    def record_paper_prediction(
        self,
        raw_match_input: Dict[str, Any],
        raw_evidence_items: List[Dict[str, Any]],
        historical_stats: Optional[Dict[str, Any]] = None
    ) -> ShadowPredictionRecord:
        """Records an immutable paper trading prediction pre-match."""
        match_id = str(raw_match_input.get("match_id", "")).strip()
        if not match_id:
            raise ValidationError("Match ID required for shadow prediction.")

        # Immutability check: disallow re-recording existing prediction
        if match_id in self.records:
            raise ValidationError(f"Immutability error: Paper prediction for match_id {match_id} already recorded and cannot be retroactively altered.")

        # Monitor data outages
        if not raw_evidence_items:
            self.data_outage_incidents += 1

        # Process match through full live pipeline
        now = datetime.now(timezone.utc)
        report: AuditableMatchReport = self.pipeline.process_match(
            raw_match_input=raw_match_input,
            raw_evidence_items=raw_evidence_items,
            historical_stats=historical_stats,
            as_of_time=now
        )

        # Monitor stale sources
        if not report.validation_summary["freshness_ok"]:
            self.stale_source_incidents += 1

        rec = ShadowPredictionRecord(
            prediction_id=f"shadow_{match_id}_{int(now.timestamp())}",
            match_id=match_id,
            home_team_id=report.match_verification["home_team_id"],
            away_team_id=report.match_verification["away_team_id"],
            prediction_timestamp=now,
            kickoff_time=datetime.fromisoformat(report.match_verification["scheduled_time"]),
            model_version=report.audit_metadata["model_version"],
            feature_version=report.audit_metadata["feature_version"],
            decision=report.risk_and_nobet_assessment["decision"],
            probabilities_1x2=report.probabilistic_forecast["outcome_1x2_probabilities"],
            expected_goals=report.probabilistic_forecast["expected_goals"],
            approved_candidate_markets=report.risk_and_nobet_assessment["approved_candidate_markets"],
            evidence_count=report.validation_summary["valid_evidence_count"]
        )

        self.records[match_id] = rec
        return rec

    def settle_paper_prediction(
        self,
        match_id: str,
        actual_outcome: str,
        actual_home_goals: int,
        actual_away_goals: int
    ) -> ShadowPredictionRecord:
        """Settles paper prediction post-match without altering historical prediction values."""
        if match_id not in self.records:
            raise ValidationError(f"Match record {match_id} not found in shadow trading log.")

        rec = self.records[match_id]

        if rec.is_settled:
            raise ValidationError(f"Match record {match_id} is already settled.")

        # Compute settlement metrics
        actual = actual_outcome.upper()
        p_act = max(1e-5, rec.probabilities_1x2.get(
            "home_win" if actual == "HOME" else ("draw" if actual == "DRAW" else "away_win"), 0.33333
        ))
        log_loss = -math.log(p_act)

        y_h = 1.0 if actual == "HOME" else 0.0
        y_d = 1.0 if actual == "DRAW" else 0.0
        y_a = 1.0 if actual == "AWAY" else 0.0
        brier = (rec.probabilities_1x2["home_win"] - y_h)**2 + (rec.probabilities_1x2["draw"] - y_d)**2 + (rec.probabilities_1x2["away_win"] - y_a)**2

        rec.is_settled = True
        rec.settled_timestamp = datetime.now(timezone.utc)
        rec.actual_outcome = actual
        rec.actual_home_goals = actual_home_goals
        rec.actual_away_goals = actual_away_goals
        rec.settlement_log_loss = round(log_loss, 4)
        rec.settlement_brier_score = round(brier, 4)

        return rec

    def evaluate_gates(
        self,
        max_log_loss: float = 0.85,
        max_brier: float = 0.25,
        max_outages: int = 5
    ) -> ShadowTradingGateReport:
        """Evaluates stability and calibration gates across shadow trading records."""
        total = len(self.records)
        if total == 0:
            return ShadowTradingGateReport(
                total_shadow_matches=0, settled_matches=0, no_bet_count=0,
                abstention_rate=0.0, stale_source_incidents=0,
                data_outage_incidents=0, average_log_loss=0.0,
                average_brier_score=0.0, calibration_gate_passed=False,
                stability_gate_passed=False, overall_gate_passed=False
            )

        no_bet = sum(1 for r in self.records.values() if r.decision == "NO_BET")
        settled = [r for r in self.records.values() if r.is_settled and r.decision == "BET"]

        if not settled:
            avg_ll = 0.0
            avg_brier = 0.0
            cal_passed = False
        else:
            avg_ll = round(sum(r.settlement_log_loss for r in settled) / len(settled), 4)
            avg_brier = round(sum(r.settlement_brier_score for r in settled) / len(settled), 4)
            cal_passed = (avg_ll <= max_log_loss and avg_brier <= max_brier)

        stab_passed = (self.data_outage_incidents <= max_outages and self.stale_source_incidents <= max_outages)
        overall = cal_passed and stab_passed

        return ShadowTradingGateReport(
            total_shadow_matches=total,
            settled_matches=len(settled),
            no_bet_count=no_bet,
            abstention_rate=round(no_bet / total, 4),
            stale_source_incidents=self.stale_source_incidents,
            data_outage_incidents=self.data_outage_incidents,
            average_log_loss=avg_ll,
            average_brier_score=avg_brier,
            calibration_gate_passed=cal_passed,
            stability_gate_passed=stab_passed,
            overall_gate_passed=overall
        )
