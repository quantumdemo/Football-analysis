"""Data validation module enforcing freshness, reliability, non-prohibited checks, and identifying missing or conflicting data."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any
from src.research.web_research import ResearchEvidence


@dataclass
class ValidationReport:
    """Report summarizing validation findings for research evidence."""
    match_id: str
    is_valid: bool
    freshness_ok: bool
    missing_data_fields: List[str] = field(default_factory=list)
    conflicting_claims: List[str] = field(default_factory=list)
    prohibited_items_rejected: int = 0
    valid_evidence_count: int = 0
    average_reliability: float = 0.0
    valid_evidence_items: List[ResearchEvidence] = field(default_factory=list)


class DataValidator:
    """Validates research evidence without inventing missing data."""

    def __init__(self, max_age_hours: float = 72.0, min_reliability: float = 0.5):
        self.max_age_hours = max_age_hours
        self.min_reliability = min_reliability

    def validate(
        self,
        match_id: str,
        scheduled_time: datetime,
        evidence_items: List[ResearchEvidence],
        required_categories: List[str] = None
    ) -> ValidationReport:
        if required_categories is None:
            required_categories = ["team_news", "tactics"]

        prohibited_rejected = 0
        valid_items: List[ResearchEvidence] = []
        conflicts: List[str] = []
        found_categories = set()

        for item in evidence_items:
            if item.is_prohibited:
                prohibited_rejected += 1
                continue

            # Check post-kickoff publication
            if item.published_at > scheduled_time:
                continue

            # Check freshness
            age = scheduled_time - item.published_at
            if age.total_seconds() < 0 or age > timedelta(hours=self.max_age_hours):
                continue

            # Check for explicitly conflicting evidence flags
            if "conflict:" in item.claim.lower():
                conflicts.append(item.claim)

            valid_items.append(item)
            found_categories.add(item.category)

        missing_fields = [cat for cat in required_categories if cat not in found_categories]

        if not valid_items:
            avg_rel = 0.0
        else:
            avg_rel = sum(it.reliability_score for it in valid_items) / len(valid_items)

        freshness_ok = len(valid_items) > 0
        is_valid = (
            len(missing_fields) == 0 and
            len(conflicts) == 0 and
            avg_rel >= self.min_reliability
        )

        return ValidationReport(
            match_id=match_id,
            is_valid=is_valid,
            freshness_ok=freshness_ok,
            missing_data_fields=missing_fields,
            conflicting_claims=conflicts,
            prohibited_items_rejected=prohibited_rejected,
            valid_evidence_count=len(valid_items),
            average_reliability=avg_rel,
            valid_evidence_items=valid_items
        )
