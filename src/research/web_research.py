"""Web research evidence interfaces."""

from dataclasses import dataclass
from datetime import datetime
from typing import List

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
    category: str
    is_prohibited: bool = False

    def __post_init__(self):
        claim_lower = self.claim.lower()
        url_lower = self.source_url.lower()
        if any(kw in claim_lower or kw in url_lower for kw in PROHIBITED_KEYWORDS):
            self.is_prohibited = True
