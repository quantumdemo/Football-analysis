"""Unit tests for Stage 23 Controlled Model Lifecycle & Updates."""

import pytest
from src.errors import ValidationError
from src.models.model_lifecycle import ControlledModelLifecycleManager, ModelLifecycleStatus, CandidateModelProposal


@pytest.fixture
def lifecycle_manager():
    return ControlledModelLifecycleManager(current_production_version="v1.0.0", baseline_log_loss=0.50)


def test_propose_candidate_model(lifecycle_manager):
    proposal = lifecycle_manager.propose_candidate_model(
        candidate_id="cand_1",
        proposed_version="v1.1.0",
        feature_set_version="v1.1",
        author="data_scientist_1",
        description="Improved Poisson goal model"
    )

    assert proposal.candidate_id == "cand_1"
    assert proposal.proposed_version == "v1.1.0"
    assert proposal.status == ModelLifecycleStatus.PROPOSED


def test_illegal_stage_skip_raises_error(lifecycle_manager):
    lifecycle_manager.propose_candidate_model("cand_2", "v1.2.0", "v1.0", "author", "desc")

    # Attempting to jump directly from PROPOSED to DEPLOYED must fail
    with pytest.raises(ValidationError):
        lifecycle_manager.transition_stage("cand_2", ModelLifecycleStatus.DEPLOYED)


def test_successful_full_lifecycle_and_deployment(lifecycle_manager):
    candidate_id = "cand_success"
    lifecycle_manager.propose_candidate_model(candidate_id, "v1.1.0", "v1.1", "author", "desc")

    # 1. DEVELOPED
    lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.DEVELOPED)

    # 2. BACKTESTED (Passing gate with log_loss <= 0.50 * 1.05)
    lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.BACKTESTED, {"backtest_log_loss": 0.48})

    # 3. CALIBRATED
    lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.CALIBRATED, {"calibration_ece": 0.04})

    # 4. SHADOW_TESTED
    lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.SHADOW_TESTED, {"shadow_test_passed": True})

    # 5. REVIEWED
    lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.REVIEWED, {"peer_reviewer": "lead_engineer"})

    # 6. APPROVED
    lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.APPROVED)

    # 7. DEPLOYED
    p_deployed = lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.DEPLOYED)

    assert p_deployed.status == ModelLifecycleStatus.DEPLOYED
    assert lifecycle_manager.current_production_version == "v1.1.0"


def test_failing_backtest_gate_auto_rejects_proposal(lifecycle_manager):
    candidate_id = "cand_fail"
    lifecycle_manager.propose_candidate_model(candidate_id, "v1.3.0", "v1.0", "author", "desc")
    lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.DEVELOPED)

    # Log loss 0.70 is much worse than baseline 0.50 -> auto-rejected
    p_rejected = lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.BACKTESTED, {"backtest_log_loss": 0.70})

    assert p_rejected.status == ModelLifecycleStatus.REJECTED
    assert "failed validation gate" in p_rejected.rejection_reason


def test_rollback_production_model(lifecycle_manager):
    # Deploy v1.1.0
    candidate_id = "cand_rb"
    lifecycle_manager.propose_candidate_model(candidate_id, "v1.1.0", "v1.1", "author", "desc")
    lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.DEVELOPED)
    lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.BACKTESTED, {"backtest_log_loss": 0.45})
    lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.CALIBRATED)
    lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.SHADOW_TESTED, {"shadow_test_passed": True})
    lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.REVIEWED, {"peer_reviewer": "reviewer"})
    lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.APPROVED)
    lifecycle_manager.transition_stage(candidate_id, ModelLifecycleStatus.DEPLOYED)

    assert lifecycle_manager.current_production_version == "v1.1.0"

    # Execute rollback
    previous = lifecycle_manager.rollback_production_model()
    assert previous == "v1.0.0"
    assert lifecycle_manager.current_production_version == "v1.0.0"
