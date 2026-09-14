"""Validation report contracts."""

from dataclasses import dataclass, field
from typing import List
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
