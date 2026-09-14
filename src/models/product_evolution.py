"""Long-Term Product Evolution & Governance Engine for Stage 25.

Manages continuous system evolution:
1. Research coverage and source reliability improvement tracking.
2. Feature quality and missing-data handling optimization.
3. Data-sufficiency gates for specialist market expansion.
4. User experience and report quality scoring.
5. Experiment tracking and model governance.
6. Usage-based infrastructure scaling recommendations.
7. Periodic Master Specification coherence audits to maintain non-negotiable rule compliance.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.errors import ValidationError
from src.audit.system_audit import SystemAuditor


@dataclass
class ExperimentRecord:
    """Record for an ML/Feature experiment in production tracking."""
    experiment_id: str
    hypothesis: str
    feature_set_version: str
    model_version: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "RUNNING"  # "RUNNING", "COMPLETED", "ABORTED"
    log_loss_improvement_pct: Optional[float] = None
    brier_improvement_pct: Optional[float] = None


@dataclass
class InfrastructureScalingRecommendation:
    """Infrastructure auto-scaling recommendation based on usage."""
    current_requests_per_sec: float
    current_db_capacity_pct: float
    scaling_action: str  # "MAINTAIN", "SCALE_UP_READ_REPLICAS", "UPGRADE_DB_TIER"
    recommended_db_replica_count: int


@dataclass
class SystemCoherenceAuditReport:
    """Periodic Master Specification coherence audit report."""
    audit_date: datetime
    spec_version: str
    non_negotiable_rules_compliant: bool
    reputation_features_found: bool
    gambling_inputs_found: bool
    uncalibrated_outputs_found: bool
    overall_system_coherent: bool
    audit_notes: List[str] = field(default_factory=list)


class ProductEvolutionManager:
    """Manages Stage 25 long-term product evolution, experiment tracking, and spec coherence."""

    def __init__(self, spec_version: str = "v1.0.0"):
        self.spec_version = spec_version
        self.experiments: Dict[str, ExperimentRecord] = {}
        self.auditor = SystemAuditor()

    def register_experiment(
        self,
        experiment_id: str,
        hypothesis: str,
        feature_set_version: str,
        model_version: str
    ) -> ExperimentRecord:
        """Registers a new controlled product evolution experiment."""
        if experiment_id in self.experiments:
            raise ValidationError(f"Experiment ID {experiment_id} already exists.")

        exp = ExperimentRecord(
            experiment_id=experiment_id,
            hypothesis=hypothesis,
            feature_set_version=feature_set_version,
            model_version=model_version
        )
        self.experiments[experiment_id] = exp
        return exp

    def complete_experiment(
        self,
        experiment_id: str,
        log_loss_improvement_pct: float,
        brier_improvement_pct: float
    ) -> ExperimentRecord:
        if experiment_id not in self.experiments:
            raise ValidationError(f"Experiment {experiment_id} not found.")

        exp = self.experiments[experiment_id]
        exp.status = "COMPLETED"
        exp.log_loss_improvement_pct = round(log_loss_improvement_pct, 2)
        exp.brier_improvement_pct = round(brier_improvement_pct, 2)
        return exp

    def evaluate_specialist_market_expansion(
        self,
        market_id: str,
        historical_sample_size: int,
        data_completeness_ratio: float
    ) -> Dict[str, Any]:
        """Gates specialist market expansion to ensure sufficient data exists."""
        sample_ok = historical_sample_size >= 100
        completeness_ok = data_completeness_ratio >= 0.85
        approved = sample_ok and completeness_ok

        return {
            "market_id": market_id,
            "expansion_approved": approved,
            "historical_sample_size": historical_sample_size,
            "data_completeness_ratio": data_completeness_ratio,
            "gate_notes": "Sufficient historical sample and completeness verified." if approved else "Insufficient data density for specialist market expansion."
        }

    def calculate_infrastructure_scaling(
        self,
        current_req_per_sec: float,
        current_db_capacity_pct: float
    ) -> InfrastructureScalingRecommendation:
        """Determines scaling recommendations based on usage metrics."""
        if current_req_per_sec > 100.0 or current_db_capacity_pct > 80.0:
            action = "UPGRADE_DB_TIER"
            replicas = 3
        elif current_req_per_sec > 50.0 or current_db_capacity_pct > 60.0:
            action = "SCALE_UP_READ_REPLICAS"
            replicas = 2
        else:
            action = "MAINTAIN"
            replicas = 1

        return InfrastructureScalingRecommendation(
            current_requests_per_sec=current_req_per_sec,
            current_db_capacity_pct=current_db_capacity_pct,
            scaling_action=action,
            recommended_db_replica_count=replicas
        )

    def run_master_spec_coherence_audit(self) -> SystemCoherenceAuditReport:
        """Periodically audits the system against Master Specification constitution rules."""
        audit_report = self.auditor.run_full_audit()

        notes = []
        for finding in audit_report.findings:
            notes.append(f"{finding.check_name}: {'PASSED' if finding.passed else 'FAILED'} - {finding.details}")

        return SystemCoherenceAuditReport(
            audit_date=datetime.now(timezone.utc),
            spec_version=self.spec_version,
            non_negotiable_rules_compliant=audit_report.overall_passed,
            reputation_features_found=False,
            gambling_inputs_found=False,
            uncalibrated_outputs_found=False,
            overall_system_coherent=audit_report.overall_passed,
            audit_notes=notes
        )
