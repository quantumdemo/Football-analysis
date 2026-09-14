"""Controlled Model Lifecycle & Evolution Engine for Stage 23.

Enforces mandatory model evolution lifecycle:
PROPOSE → DEVELOP → BACKTEST → CALIBRATE → SHADOW TEST → REVIEW → APPROVE → DEPLOY → MONITOR.

Rules:
1. AI agents/automated systems MUST NOT directly rewrite production predictive logic without controlled review.
2. Every prediction carries an explicit model and feature version identifier.
3. Historical production model versions are retained to support instant rollback.
4. Candidate models are compared against current production baseline; proposals failing validation gates are rejected.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from src.errors import ValidationError


class ModelLifecycleStatus(Enum):
    PROPOSED = "PROPOSED"
    DEVELOPED = "DEVELOPED"
    BACKTESTED = "BACKTESTED"
    CALIBRATED = "CALIBRATED"
    SHADOW_TESTED = "SHADOW_TESTED"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    DEPLOYED = "DEPLOYED"
    REJECTED = "REJECTED"
    ROLLED_BACK = "ROLLED_BACK"


# Allowed stage transitions in strict order
VALID_STAGE_TRANSITIONS = {
    ModelLifecycleStatus.PROPOSED: [ModelLifecycleStatus.DEVELOPED, ModelLifecycleStatus.REJECTED],
    ModelLifecycleStatus.DEVELOPED: [ModelLifecycleStatus.BACKTESTED, ModelLifecycleStatus.REJECTED],
    ModelLifecycleStatus.BACKTESTED: [ModelLifecycleStatus.CALIBRATED, ModelLifecycleStatus.REJECTED],
    ModelLifecycleStatus.CALIBRATED: [ModelLifecycleStatus.SHADOW_TESTED, ModelLifecycleStatus.REJECTED],
    ModelLifecycleStatus.SHADOW_TESTED: [ModelLifecycleStatus.REVIEWED, ModelLifecycleStatus.REJECTED],
    ModelLifecycleStatus.REVIEWED: [ModelLifecycleStatus.APPROVED, ModelLifecycleStatus.REJECTED],
    ModelLifecycleStatus.APPROVED: [ModelLifecycleStatus.DEPLOYED, ModelLifecycleStatus.REJECTED],
    ModelLifecycleStatus.DEPLOYED: [ModelLifecycleStatus.ROLLED_BACK],
    ModelLifecycleStatus.ROLLED_BACK: [],
    ModelLifecycleStatus.REJECTED: []
}


@dataclass
class CandidateModelProposal:
    """Proposal record for a candidate model version."""
    candidate_id: str
    proposed_version: str
    feature_set_version: str
    author: str
    description: str
    status: ModelLifecycleStatus = ModelLifecycleStatus.PROPOSED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    backtest_log_loss: Optional[float] = None
    backtest_brier_score: Optional[float] = None
    calibration_ece: Optional[float] = None
    shadow_test_passed: Optional[bool] = None
    peer_reviewer: Optional[str] = None
    rejection_reason: Optional[str] = None


class ControlledModelLifecycleManager:
    """Manages controlled model lifecycle, baseline comparisons, approval gates, and rollbacks."""

    def __init__(self, current_production_version: str = "v1.0.0", baseline_log_loss: float = 0.55):
        self.current_production_version = current_production_version
        self.baseline_log_loss = baseline_log_loss
        self.active_proposals: Dict[str, CandidateModelProposal] = {}
        self.version_history: Dict[str, CandidateModelProposal] = {}
        self.production_history: List[str] = [current_production_version]

    def propose_candidate_model(
        self,
        candidate_id: str,
        proposed_version: str,
        feature_set_version: str,
        author: str,
        description: str
    ) -> CandidateModelProposal:
        if candidate_id in self.active_proposals:
            raise ValidationError(f"Proposal candidate_id {candidate_id} already exists.")

        proposal = CandidateModelProposal(
            candidate_id=candidate_id,
            proposed_version=proposed_version,
            feature_set_version=feature_set_version,
            author=author,
            description=description,
            status=ModelLifecycleStatus.PROPOSED
        )
        self.active_proposals[candidate_id] = proposal
        return proposal

    def transition_stage(
        self,
        candidate_id: str,
        target_status: ModelLifecycleStatus,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CandidateModelProposal:
        if candidate_id not in self.active_proposals:
            raise ValidationError(f"Candidate model proposal {candidate_id} not found.")

        proposal = self.active_proposals[candidate_id]
        allowed_next = VALID_STAGE_TRANSITIONS.get(proposal.status, [])

        if target_status not in allowed_next:
            raise ValidationError(
                f"Illegal stage transition from {proposal.status.value} to {target_status.value}. "
                f"Required lifecycle path: PROPOSE -> DEVELOP -> BACKTEST -> CALIBRATE -> SHADOW TEST -> REVIEW -> APPROVE -> DEPLOY."
            )

        meta = metadata or {}

        # Validation gate checks per transition
        if target_status == ModelLifecycleStatus.BACKTESTED:
            log_loss = float(meta.get("backtest_log_loss", 1.0))
            # Reject if candidate log loss is > 5% worse than production baseline
            if log_loss > self.baseline_log_loss * 1.05:
                proposal.status = ModelLifecycleStatus.REJECTED
                proposal.rejection_reason = f"Backtest log loss ({log_loss:.4f}) failed validation gate (> 5% worse than baseline {self.baseline_log_loss:.4f})."
                return proposal
            proposal.backtest_log_loss = log_loss
            proposal.backtest_brier_score = float(meta.get("backtest_brier_score", 0.20))

        elif target_status == ModelLifecycleStatus.CALIBRATED:
            proposal.calibration_ece = float(meta.get("calibration_ece", 0.05))

        elif target_status == ModelLifecycleStatus.SHADOW_TESTED:
            shadow_passed = bool(meta.get("shadow_test_passed", False))
            if not shadow_passed:
                proposal.status = ModelLifecycleStatus.REJECTED
                proposal.rejection_reason = "Shadow paper trading gate failed."
                return proposal
            proposal.shadow_test_passed = True

        elif target_status == ModelLifecycleStatus.REVIEWED:
            reviewer = meta.get("peer_reviewer")
            if not reviewer:
                raise ValidationError("Peer reviewer identifier required for REVIEWED stage.")
            proposal.peer_reviewer = reviewer

        elif target_status == ModelLifecycleStatus.DEPLOYED:
            if proposal.status != ModelLifecycleStatus.APPROVED:
                raise ValidationError("Direct deployment without APPROVED status is strictly prohibited.")
            # Promote candidate to current production version and retain previous
            self.production_history.append(self.current_production_version)
            self.current_production_version = proposal.proposed_version

        proposal.status = target_status
        self.version_history[proposal.proposed_version] = proposal
        return proposal

    def rollback_production_model(self) -> str:
        """Rolls back current production model to previous active production version."""
        if len(self.production_history) <= 1:
            raise ValidationError("No previous production version available for rollback.")

        previous_version = self.production_history.pop()
        old_active = self.current_production_version
        self.current_production_version = previous_version

        if old_active in self.version_history:
            self.version_history[old_active].status = ModelLifecycleStatus.ROLLED_BACK

        return previous_version
