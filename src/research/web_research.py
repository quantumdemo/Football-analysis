"""Web research module for ingesting external evidence with source, freshness, and reliability metadata."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

PROHIBITED_KEYWORDS = [
    "odds", "bookmaker", "betting", "tipster", "stake", "handicap odds",
    "over/under odds", "prediction market", "gambling", "pinnacle", "bet365"
]


@dataclass
class ResearchEvidence:
    """Represents an external evidence item collected via web research."""
    evidence_id: str
    match_id: str
    claim: str
    source_url: str
    published_at: datetime
    reliability_score: float  # 0.0 to 1.0
    category: str  # e.g., "team_news", "weather", "tactics", "schedule"
    is_prohibited: bool = False

    def __post_init__(self):
        # Enforce rule: exclude bookmaker odds, predictions, tipster picks
        claim_lower = self.claim.lower()
        url_lower = self.source_url.lower()
        if any(keyword in claim_lower or keyword in url_lower for keyword in PROHIBITED_KEYWORDS):
            self.is_prohibited = True


class ResearchIngestor:
    """Ingests and filters web research evidence."""

    def __init__(self, prohibited_keywords: Optional[List[str]] = None):
        self.prohibited_keywords = prohibited_keywords or PROHIBITED_KEYWORDS

    def ingest_evidence(self, evidence_list: List[ResearchEvidence]) -> List[ResearchEvidence]:
        """Filters out evidence originating from gambling/odds/tipster sources."""
        valid_evidence = []
        for item in evidence_list:
            if not item.is_prohibited:
                valid_evidence.append(item)
        return valid_evidence
