"""Scheduled Job Runner for managing production workflows, rate limiting, and abuse protection."""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import time
from typing import List, Dict, Any, Optional
from src.errors import ValidationError
from src.pipeline import FootballAIPipeline
from src.data.database import ProductionDatabaseRepository
from src.data.retention import RetentionJobLog


class ScheduledJobRunner:
    """Manages scheduled production jobs (research, feature refresh, prediction, 6-hour research cleanup)."""

    def __init__(self, db_repo: Optional[ProductionDatabaseRepository] = None, max_requests_per_min: int = 60):
        self.pipeline = FootballAIPipeline()
        self.db = db_repo or ProductionDatabaseRepository()
        self.max_requests_per_min = max_requests_per_min
        self.request_timestamps: List[datetime] = []

    def _check_rate_limit(self) -> None:
        """Enforces rate limit (e.g. 60 requests/min)."""
        now = datetime.now(timezone.utc)
        self.request_timestamps = [ts for ts in self.request_timestamps if (now - ts).total_seconds() < 60]

        if len(self.request_timestamps) >= self.max_requests_per_min:
            raise ValidationError(f"Rate limit exceeded ({self.max_requests_per_min} requests/min max).")

        self.request_timestamps.append(now)

    def run_prediction_job(
        self,
        raw_match_input: Dict[str, Any],
        raw_evidence_items: List[Dict[str, Any]],
        historical_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Runs scheduled pre-match prediction job."""
        self._check_rate_limit()

        # 1. Resolve and save match
        match = self.pipeline.resolver.resolve(raw_match_input)
        self.db.save_match(match)

        # 2. Process match through pipeline
        report = self.pipeline.process_match(
            raw_match_input=raw_match_input,
            raw_evidence_items=raw_evidence_items,
            historical_stats=historical_stats
        )

        # 3. Save prediction
        self.db.save_prediction(report)

        return report.to_dict()

    def run_6hour_research_cleanup_job(self, dry_run: bool = False) -> List[RetentionJobLog]:
        """Runs scheduled 6-hour database research retention cleanup across temporary research tables."""
        self._check_rate_limit()

        temp_tables = [
            "research_cache",
            "web_research_raw",
            "temporary_feature_cache",
            "temporary_research_sessions"
        ]

        logs: List[RetentionJobLog] = []
        for table in temp_tables:
            log = self.db.purge_expired_research_cache(table_name=table, dry_run=dry_run)
            logs.append(log)

        return logs
