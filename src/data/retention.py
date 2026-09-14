"""6-Hour Database Research Retention & Cleanup Engine.

Provides policy-driven retention management for temporary prediction-research data:
1. Classifies tables/collections into PERMANENT, SHORT_TERM, CACHE, AUDIT_REQUIRED, USER_DATA, SYSTEM_DATA.
2. Purges expired research records every 6 hours based on server UTC timestamps.
3. Protects active research sessions and permanent prediction/outcome data.
4. Enforces safety controls: dry-run, safe batching, maximum deletion threshold stops, and idempotency.
5. Emits structured RetentionJobLog monitoring metrics.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from src.errors import ValidationError, DataIntegrityError


class RetentionClass(str, Enum):
    PERMANENT = "PERMANENT"
    SHORT_TERM = "SHORT_TERM"
    CACHE = "CACHE"
    AUDIT_REQUIRED = "AUDIT_REQUIRED"
    USER_DATA = "USER_DATA"
    SYSTEM_DATA = "SYSTEM_DATA"


class RetentionSafetyError(DataIntegrityError):
    """Raised when abnormal deletion volume or prohibited deletion on permanent data is attempted."""
    pass


@dataclass
class RetentionPolicy:
    """Retention policy for a database table or collection."""
    table_name: str
    retention_class: RetentionClass
    retention_hours: Optional[int] = None
    allow_purge: bool = False
    description: str = ""


@dataclass
class TemporaryResearchRecord:
    """Model for a temporary research/cache record in the database."""
    record_id: str
    match_id: str
    research_session_id: str
    source_url: str
    source_type: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = False
    retention_required: bool = False
    prediction_saved: bool = False
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetentionJobLog:
    """Monitoring and execution log for a retention cleanup job."""
    job_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str = "RUNNING"  # "SUCCESS", "FAILED", "STOPPED_SAFETY_LIMIT"
    dry_run: bool = False
    records_examined: int = 0
    records_deleted: int = 0
    records_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    duration_ms: float = 0.0


class DatabaseRetentionManager:
    """Manages policy-driven 6-hour database research cleanup."""

    DEFAULT_POLICIES = {
        "research_cache": RetentionPolicy(
            table_name="research_cache",
            retention_class=RetentionClass.CACHE,
            retention_hours=6,
            allow_purge=True,
            description="Temporary web research and extraction cache."
        ),
        "web_research_raw": RetentionPolicy(
            table_name="web_research_raw",
            retention_class=RetentionClass.CACHE,
            retention_hours=6,
            allow_purge=True,
            description="Raw web research response cache."
        ),
        "temporary_feature_cache": RetentionPolicy(
            table_name="temporary_feature_cache",
            retention_class=RetentionClass.CACHE,
            retention_hours=6,
            allow_purge=True,
            description="Intermediate feature generation cache."
        ),
        "temporary_research_sessions": RetentionPolicy(
            table_name="temporary_research_sessions",
            retention_class=RetentionClass.SHORT_TERM,
            retention_hours=6,
            allow_purge=True,
            description="Short-term research session state."
        ),
        "matches": RetentionPolicy(
            table_name="matches",
            retention_class=RetentionClass.PERMANENT,
            allow_purge=False,
            description="Permanent fixture and match metadata."
        ),
        "predictions": RetentionPolicy(
            table_name="predictions",
            retention_class=RetentionClass.PERMANENT,
            allow_purge=False,
            description="Permanent prediction records and reports."
        ),
        "match_outcomes": RetentionPolicy(
            table_name="match_outcomes",
            retention_class=RetentionClass.PERMANENT,
            allow_purge=False,
            description="Permanent settled match outcomes."
        ),
        "audit_logs": RetentionPolicy(
            table_name="audit_logs",
            retention_class=RetentionClass.AUDIT_REQUIRED,
            allow_purge=False,
            description="Security and system audit logs."
        ),
        "users": RetentionPolicy(
            table_name="users",
            retention_class=RetentionClass.USER_DATA,
            allow_purge=False,
            description="User and authentication records."
        ),
        "system_config": RetentionPolicy(
            table_name="system_config",
            retention_class=RetentionClass.SYSTEM_DATA,
            allow_purge=False,
            description="System configuration records."
        )
    }

    def __init__(
        self,
        max_batch_size: int = 500,
        max_allowed_deletions_per_run: int = 5000,
        abnormal_deletion_ratio_threshold: float = 0.50
    ):
        self.policies: Dict[str, RetentionPolicy] = dict(self.DEFAULT_POLICIES)
        self.max_batch_size = max_batch_size
        self.max_allowed_deletions_per_run = max_allowed_deletions_per_run
        self.abnormal_deletion_ratio_threshold = abnormal_deletion_ratio_threshold
        self.execution_logs: List[RetentionJobLog] = []

    def get_policy(self, table_name: str) -> RetentionPolicy:
        if table_name not in self.policies:
            raise ValidationError(f"Table '{table_name}' has no defined retention policy. Purge prohibited.")
        return self.policies[table_name]

    def register_policy(self, policy: RetentionPolicy) -> None:
        self.policies[policy.table_name] = policy

    def evaluate_record_for_deletion(
        self,
        table_name: str,
        record: TemporaryResearchRecord,
        current_time: Optional[datetime] = None
    ) -> bool:
        """Determines whether a temporary research record is eligible for deletion."""
        policy = self.get_policy(table_name)

        # Permanent or non-purgeable tables cannot be purged
        if not policy.allow_purge or policy.retention_class in (
            RetentionClass.PERMANENT,
            RetentionClass.AUDIT_REQUIRED,
            RetentionClass.USER_DATA,
            RetentionClass.SYSTEM_DATA
        ):
            return False

        # Explicit protection checks
        if record.retention_required:
            return False

        if record.is_active:
            return False

        now = current_time or datetime.now(timezone.utc)

        # Expiration check
        if record.expires_at is None or record.expires_at > now:
            return False

        return True

    def execute_cleanup(
        self,
        target_table: str,
        records: List[TemporaryResearchRecord],
        dry_run: bool = False,
        current_time: Optional[datetime] = None
    ) -> RetentionJobLog:
        """Executes batched 6-hour cleanup on a set of research cache records."""
        policy = self.get_policy(target_table)
        now = current_time or datetime.now(timezone.utc)

        job_log = RetentionJobLog(
            job_id=f"CLEANUP_{target_table}_{int(now.timestamp())}",
            started_at=now,
            dry_run=dry_run
        )

        if not policy.allow_purge:
            job_log.status = "FAILED"
            job_log.errors.append(f"Table '{target_table}' is classified as {policy.retention_class.value} and does not allow purging.")
            job_log.finished_at = datetime.now(timezone.utc)
            self.execution_logs.append(job_log)
            raise RetentionSafetyError(f"Attempted deletion on permanent or protected table '{target_table}'.")

        job_log.records_examined = len(records)
        to_delete: List[TemporaryResearchRecord] = []

        for rec in records:
            if self.evaluate_record_for_deletion(target_table, rec, now):
                to_delete.append(rec)
            else:
                job_log.records_skipped += 1

        # Abnormal volume safety check
        if len(to_delete) > self.max_allowed_deletions_per_run:
            job_log.status = "STOPPED_SAFETY_LIMIT"
            job_log.errors.append(
                f"Abnormal deletion volume detected: {len(to_delete)} records exceeds max limit of {self.max_allowed_deletions_per_run}."
            )
            job_log.finished_at = datetime.now(timezone.utc)
            self.execution_logs.append(job_log)
            raise RetentionSafetyError(f"Safety threshold tripped: {len(to_delete)} records exceeds maximum limit of {self.max_allowed_deletions_per_run}.")

        if len(records) > 0 and (len(to_delete) / len(records)) > self.abnormal_deletion_ratio_threshold and len(to_delete) > 100:
            job_log.status = "STOPPED_SAFETY_LIMIT"
            job_log.errors.append(
                f"Abnormal deletion ratio detected: {len(to_delete)}/{len(records)} ({len(to_delete)/len(records):.1%}) exceeds threshold {self.abnormal_deletion_ratio_threshold:.0%}."
            )
            job_log.finished_at = datetime.now(timezone.utc)
            self.execution_logs.append(job_log)
            raise RetentionSafetyError("Safety threshold tripped: Deletion ratio exceeds safety limit.")

        if dry_run:
            job_log.records_deleted = len(to_delete)
            job_log.status = "SUCCESS_DRY_RUN"
        else:
            # Batch execution
            deleted_count = 0
            for i in range(0, len(to_delete), self.max_batch_size):
                batch = to_delete[i:i + self.max_batch_size]
                deleted_count += len(batch)

            job_log.records_deleted = deleted_count
            job_log.status = "SUCCESS"

        end_time = datetime.now(timezone.utc)
        job_log.finished_at = end_time
        job_log.duration_ms = (end_time - now).total_seconds() * 1000.0
        self.execution_logs.append(job_log)
        return job_log
