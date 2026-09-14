"""Tests for Stage 25 Long-Term Product Evolution & Governance Engine."""

import pytest
from src.models.product_evolution import ProductEvolutionManager
from src.errors import ValidationError


def test_experiment_lifecycle():
    manager = ProductEvolutionManager()
    exp = manager.register_experiment(
        experiment_id="EXP_001",
        hypothesis="Test xG decay weighting",
        feature_set_version="v2.1",
        model_version="v2.0"
    )
    assert exp.experiment_id == "EXP_001"
    assert exp.status == "RUNNING"

    # Duplicate registration should raise ValidationError
    with pytest.raises(ValidationError):
        manager.register_experiment(
            experiment_id="EXP_001",
            hypothesis="Duplicate",
            feature_set_version="v2.1",
            model_version="v2.0"
        )

    completed_exp = manager.complete_experiment(
        experiment_id="EXP_001",
        log_loss_improvement_pct=2.5,
        brier_improvement_pct=1.8
    )
    assert completed_exp.status == "COMPLETED"
    assert completed_exp.log_loss_improvement_pct == 2.5
    assert completed_exp.brier_improvement_pct == 1.8


def test_specialist_market_expansion_gating():
    manager = ProductEvolutionManager()

    # Pass case
    res_pass = manager.evaluate_specialist_market_expansion(
        market_id="CORNER_HANDICAP",
        historical_sample_size=150,
        data_completeness_ratio=0.90
    )
    assert res_pass["expansion_approved"] is True

    # Fail case - low sample size
    res_fail_sample = manager.evaluate_specialist_market_expansion(
        market_id="PLAYER_FOULS",
        historical_sample_size=50,
        data_completeness_ratio=0.95
    )
    assert res_fail_sample["expansion_approved"] is False

    # Fail case - low completeness
    res_fail_comp = manager.evaluate_specialist_market_expansion(
        market_id="SHOTS_ON_TARGET",
        historical_sample_size=200,
        data_completeness_ratio=0.70
    )
    assert res_fail_comp["expansion_approved"] is False


def test_infrastructure_scaling_recommendation():
    manager = ProductEvolutionManager()

    rec_maintain = manager.calculate_infrastructure_scaling(
        current_req_per_sec=10.0,
        current_db_capacity_pct=30.0
    )
    assert rec_maintain.scaling_action == "MAINTAIN"
    assert rec_maintain.recommended_db_replica_count == 1

    rec_scale = manager.calculate_infrastructure_scaling(
        current_req_per_sec=60.0,
        current_db_capacity_pct=50.0
    )
    assert rec_scale.scaling_action == "SCALE_UP_READ_REPLICAS"
    assert rec_scale.recommended_db_replica_count == 2

    rec_upgrade = manager.calculate_infrastructure_scaling(
        current_req_per_sec=120.0,
        current_db_capacity_pct=85.0
    )
    assert rec_upgrade.scaling_action == "UPGRADE_DB_TIER"
    assert rec_upgrade.recommended_db_replica_count == 3


def test_master_spec_coherence_audit():
    manager = ProductEvolutionManager()
    audit_report = manager.run_master_spec_coherence_audit()

    assert audit_report.spec_version == "v1.0.0"
    assert audit_report.non_negotiable_rules_compliant is True
    assert audit_report.reputation_features_found is False
    assert audit_report.gambling_inputs_found is False
    assert audit_report.overall_system_coherent is True
    assert len(audit_report.audit_notes) > 0
