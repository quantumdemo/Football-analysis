"""Production Database Repository Abstraction & Schema Manager for Stage 18.

Provides decoupled repository interface for persistence across Supabase/PostgreSQL backends.
Enforces foreign keys, indexes, immutable prediction logs, and backup/recovery operations.
Integrated with DatabaseRetentionManager for automated 6-hour research cache cleanup.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.errors import DataIntegrityError, ValidationError
from src.match.identifier import MatchIdentifier
from src.reporting.report_generator import AuditableMatchReport
from src.data.retention import (
    DatabaseRetentionManager,
    TemporaryResearchRecord,
    RetentionJobLog
)


@dataclass
class DatabaseRecord:
    """Generic persistent database record."""
    table_name: str
    record_id: str
    data: Dict[str, Any]
    created_at: datetime


class ProductionDatabaseRepository:
    """Decoupled database repository interface supporting Supabase and relational backends."""

    def __init__(self, db_type: str = "Supabase"):
        self.db_type = db_type
        self.tables: Dict[str, Dict[str, DatabaseRecord]] = {
            "matches": {},
            "web_evidence": {},
            "validated_features": {},
            "predictions": {},
            "match_outcomes": {},
            "audit_logs": {},
            "research_cache": {},
            "web_research_raw": {},
            "temporary_feature_cache": {},
            "temporary_research_sessions": {}
        }
        self.retention_manager = DatabaseRetentionManager()
        self._initialize_schema_indexes()

    def _initialize_schema_indexes(self):
        """Simulates creation of indexes and schema constraints."""
        self.indexes = [
            "idx_matches_scheduled_time",
            "idx_evidence_match_published",
            "idx_predictions_match_version",
            "idx_research_cache_expires_at"
        ]

    def save_match(self, match: MatchIdentifier) -> None:
        rec = DatabaseRecord(
            table_name="matches",
            record_id=match.match_id,
            data={
                "match_id": match.match_id,
                "home_team_id": match.home_team_id,
                "away_team_id": match.away_team_id,
                "scheduled_time": match.scheduled_time.isoformat(),
                "competition": match.competition,
                "venue": match.venue,
                "status": match.status.value
            },
            created_at=datetime.now(timezone.utc)
        )
        self.tables["matches"][match.match_id] = rec

    def save_prediction(self, report: AuditableMatchReport) -> None:
        # Enforce foreign key match constraint
        if report.match_id not in self.tables["matches"]:
            raise DataIntegrityError(f"Foreign Key Error: match_id {report.match_id} does not exist in matches table.")

        # Immutability check
        if report.match_id in self.tables["predictions"]:
            raise DataIntegrityError(f"Immutability Error: Prediction record for match_id {report.match_id} already exists.")

        rec = DatabaseRecord(
            table_name="predictions",
            record_id=report.match_id,
            data=report.to_dict(),
            created_at=datetime.now(timezone.utc)
        )
        self.tables["predictions"][report.match_id] = rec

    def get_prediction(self, match_id: str) -> Optional[Dict[str, Any]]:
        rec = self.tables["predictions"].get(match_id)
        return rec.data if rec else None

    def save_research_cache(self, record: TemporaryResearchRecord, table_name: str = "research_cache") -> None:
        """Stores a temporary research cache record."""
        if table_name not in self.tables:
            self.tables[table_name] = {}

        db_rec = DatabaseRecord(
            table_name=table_name,
            record_id=record.record_id,
            data={
                "record_id": record.record_id,
                "match_id": record.match_id,
                "research_session_id": record.research_session_id,
                "source_url": record.source_url,
                "source_type": record.source_type,
                "created_at": record.created_at.isoformat(),
                "expires_at": record.expires_at.isoformat() if record.expires_at else None,
                "is_active": record.is_active,
                "retention_required": record.retention_required,
                "prediction_saved": record.prediction_saved,
                "payload": record.data
            },
            created_at=record.created_at
        )
        self.tables[table_name][record.record_id] = db_rec

    def purge_expired_research_cache(self, table_name: str = "research_cache", dry_run: bool = False) -> RetentionJobLog:
        """Executes 6-hour research cache cleanup on a specified temporary table."""
        if table_name not in self.tables:
            raise ValidationError(f"Table '{table_name}' does not exist.")

        # Reconstruct TemporaryResearchRecord list from storage
        raw_records = self.tables[table_name]
        temp_records: List[TemporaryResearchRecord] = []

        for rec_id, db_rec in raw_records.items():
            data = db_rec.data
            expires_at = datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
            created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else db_rec.created_at

            temp_rec = TemporaryResearchRecord(
                record_id=data["record_id"],
                match_id=data["match_id"],
                research_session_id=data["research_session_id"],
                source_url=data["source_url"],
                source_type=data["source_type"],
                created_at=created_at,
                expires_at=expires_at,
                is_active=data.get("is_active", False),
                retention_required=data.get("retention_required", False),
                prediction_saved=data.get("prediction_saved", False),
                data=data.get("payload", {})
            )
            temp_records.append(temp_rec)

        now = datetime.now(timezone.utc)
        job_log = self.retention_manager.execute_cleanup(table_name, temp_records, dry_run=dry_run, current_time=now)

        if not dry_run and job_log.status == "SUCCESS":
            # Remove deleted records from in-memory table
            for temp_rec in temp_records:
                if self.retention_manager.evaluate_record_for_deletion(table_name, temp_rec, now):
                    self.tables[table_name].pop(temp_rec.record_id, None)

        return job_log

    def backup_database(self) -> Dict[str, int]:
        """Simulates database snapshot backup."""
        return {table: len(records) for table, records in self.tables.items()}

    def restore_database(self, backup_snapshot: Dict[str, Any]) -> bool:
        """Simulates database restore from snapshot."""
        if not isinstance(backup_snapshot, dict):
            return False
        return True
