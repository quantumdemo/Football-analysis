"""Comprehensive unit tests for 6-hour Database Research Retention & Cleanup Engine."""

import pytest
from datetime import datetime, timezone, timedelta
from src.data.retention import (
    DatabaseRetentionManager,
    TemporaryResearchRecord,
    RetentionPolicy,
    RetentionClass,
    RetentionSafetyError
)
from src.data.database import ProductionDatabaseRepository
from src.data.scheduler import ScheduledJobRunner
from src.errors import ValidationError


def test_retention_policy_classification_and_validation():
    manager = DatabaseRetentionManager()

    # Verify default policies
    cache_policy = manager.get_policy("research_cache")
    assert cache_policy.retention_class == RetentionClass.CACHE
    assert cache_policy.allow_purge is True

    predictions_policy = manager.get_policy("predictions")
    assert predictions_policy.retention_class == RetentionClass.PERMANENT
    assert predictions_policy.allow_purge is False

    # Unregistered table raises ValidationError
    with pytest.raises(ValidationError):
        manager.get_policy("unregistered_table")


def test_expired_vs_active_and_protected_records():
    manager = DatabaseRetentionManager()
    now = datetime.now(timezone.utc)
    past = now - timedelta(hours=7)
    future = now + timedelta(hours=2)

    # 1. Expired record -> eligible
    rec_expired = TemporaryResearchRecord(
        record_id="REC_01",
        match_id="MATCH_101",
        research_session_id="SESS_01",
        source_url="https://sports.example.com/lineups",
        source_type="LINEUP_NEWS",
        created_at=past,
        expires_at=past + timedelta(hours=6),
        is_active=False,
        retention_required=False
    )
    assert manager.evaluate_record_for_deletion("research_cache", rec_expired, now) is True

    # 2. Non-expired record -> preserved
    rec_future = TemporaryResearchRecord(
        record_id="REC_02",
        match_id="MATCH_101",
        research_session_id="SESS_01",
        source_url="https://sports.example.com/stats",
        source_type="TEAM_STATS",
        created_at=now,
        expires_at=future,
        is_active=False
    )
    assert manager.evaluate_record_for_deletion("research_cache", rec_future, now) is False

    # 3. Active research session -> preserved
    rec_active = TemporaryResearchRecord(
        record_id="REC_03",
        match_id="MATCH_101",
        research_session_id="SESS_01",
        source_url="https://sports.example.com/active",
        source_type="LIVE_INJURY",
        created_at=past,
        expires_at=past + timedelta(hours=6),
        is_active=True
    )
    assert manager.evaluate_record_for_deletion("research_cache", rec_active, now) is False

    # 4. Retention required flag -> preserved
    rec_retained = TemporaryResearchRecord(
        record_id="REC_04",
        match_id="MATCH_101",
        research_session_id="SESS_01",
        source_url="https://sports.example.com/audit",
        source_type="AUDIT_HOLD",
        created_at=past,
        expires_at=past + timedelta(hours=6),
        is_active=False,
        retention_required=True
    )
    assert manager.evaluate_record_for_deletion("research_cache", rec_retained, now) is False


def test_prohibited_deletion_on_permanent_tables():
    manager = DatabaseRetentionManager()
    now = datetime.now(timezone.utc)

    dummy_record = TemporaryResearchRecord(
        record_id="REC_PERM",
        match_id="MATCH_101",
        research_session_id="SESS_PERM",
        source_url="n/a",
        source_type="PREDICTION_DATA",
        created_at=now - timedelta(days=30),
        expires_at=now - timedelta(days=29)
    )

    # Permanent tables must reject cleanup and raise RetentionSafetyError
    with pytest.raises(RetentionSafetyError):
        manager.execute_cleanup("predictions", [dummy_record], current_time=now)

    with pytest.raises(RetentionSafetyError):
        manager.execute_cleanup("matches", [dummy_record], current_time=now)


def test_abnormal_deletion_threshold_protection():
    manager = DatabaseRetentionManager(max_allowed_deletions_per_run=10)
    now = datetime.now(timezone.utc)
    past = now - timedelta(hours=10)

    # Create 15 expired records exceeding max limit of 10
    expired_records = [
        TemporaryResearchRecord(
            record_id=f"REC_{i}",
            match_id="MATCH_101",
            research_session_id="SESS_01",
            source_url="https://example.com",
            source_type="CACHE",
            created_at=past,
            expires_at=past + timedelta(hours=6)
        )
        for i in range(15)
    ]

    with pytest.raises(RetentionSafetyError):
        manager.execute_cleanup("research_cache", expired_records, current_time=now)


def test_repository_and_scheduler_integration_and_idempotency():
    repo = ProductionDatabaseRepository()
    scheduler = ScheduledJobRunner(db_repo=repo)

    now = datetime.now(timezone.utc)
    past = now - timedelta(hours=8)

    # Seed research_cache with 2 expired and 1 active record
    rec_exp1 = TemporaryResearchRecord(
        record_id="EXP_1",
        match_id="M1",
        research_session_id="S1",
        source_url="http://src1.com",
        source_type="RAW",
        created_at=past,
        expires_at=past + timedelta(hours=6),
        is_active=False
    )
    rec_exp2 = TemporaryResearchRecord(
        record_id="EXP_2",
        match_id="M1",
        research_session_id="S1",
        source_url="http://src2.com",
        source_type="RAW",
        created_at=past,
        expires_at=past + timedelta(hours=6),
        is_active=False
    )
    rec_act = TemporaryResearchRecord(
        record_id="ACT_1",
        match_id="M1",
        research_session_id="S1",
        source_url="http://src3.com",
        source_type="RAW",
        created_at=past,
        expires_at=past + timedelta(hours=6),
        is_active=True
    )

    repo.save_research_cache(rec_exp1, table_name="research_cache")
    repo.save_research_cache(rec_exp2, table_name="research_cache")
    repo.save_research_cache(rec_act, table_name="research_cache")

    assert len(repo.tables["research_cache"]) == 3

    # Dry-run test
    dry_logs = scheduler.run_6hour_research_cleanup_job(dry_run=True)
    res_cache_dry_log = [l for l in dry_logs if "research_cache" in l.job_id][0]
    assert res_cache_dry_log.records_deleted == 2
    assert len(repo.tables["research_cache"]) == 3  # Unmodified in dry-run

    # Live execution
    live_logs = scheduler.run_6hour_research_cleanup_job(dry_run=False)
    res_cache_live_log = [l for l in live_logs if "research_cache" in l.job_id][0]
    assert res_cache_live_log.records_deleted == 2
    assert len(repo.tables["research_cache"]) == 1
    assert "ACT_1" in repo.tables["research_cache"]

    # Idempotency check: rerun cleanup -> 0 records deleted
    idem_logs = scheduler.run_6hour_research_cleanup_job(dry_run=False)
    res_cache_idem_log = [l for l in idem_logs if "research_cache" in l.job_id][0]
    assert res_cache_idem_log.records_deleted == 0
    assert len(repo.tables["research_cache"]) == 1
