"""Web research module for ingesting, filtering, and scoring non-betting football evidence."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any


class EvidenceCategory(Enum):
    TEAM_NEWS = "team_news"
    LINEUPS = "lineups"
    INJURIES_SUSPENSIONS = "injuries_suspensions"
    TACTICS = "tactics"
    MANAGER_COMMENTS = "manager_comments"
    TABLE_H2H = "table_h2h"
    REST_CONGESTION = "rest_congestion"
    WEATHER_PITCH = "weather_pitch"
    PUBLIC_DISCUSSION = "public_discussion"
    OTHER = "other"


PROHIBITED_KEYWORDS = [
    "odds", "bookmaker", "betting", "tipster", "stake", "handicap odds",
    "over/under odds", "prediction market", "gambling", "pinnacle", "bet365",
    "unibet", "williamhill", "bwin", "1xbet", "punter", "free bet"
]

HIGH_RELIABILITY_DOMAINS = [
    "official", "bbc.com", "reuters.com", "skysports.com", "theguardian.com",
    "kicker.de", "lequipe.fr", "marca.com", "gazetta.it"
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


class ResearchCollector:
    """Ingests and validates web research evidence strictly flagging betting platforms and tipsters."""

    def __init__(self, min_reliability: float = 0.5):
        self.min_reliability = min_reliability

    def collect_evidence(self, raw_items: List[Dict[str, Any]]) -> List[ResearchEvidence]:
        """Ingests raw evidence dictionaries and attributes metadata."""
        processed_items: List[ResearchEvidence] = []

        for item in raw_items:
            evidence_id = str(item.get("evidence_id", f"ev_{len(processed_items)+1}"))
            match_id = str(item.get("match_id", ""))
            claim = str(item.get("claim", "")).strip()
            source_url = str(item.get("source_url", "")).strip()
            category_str = str(item.get("category", EvidenceCategory.OTHER.value)).lower()
            published_raw = item.get("published_at")

            if isinstance(published_raw, str):
                published_at = datetime.fromisoformat(published_raw)
            elif isinstance(published_raw, datetime):
                published_at = published_raw
            else:
                published_at = datetime.now(timezone.utc)

            # Reliability scoring heuristic based on source domain
            base_reliability = float(item.get("reliability_score", 0.7))
            if any(domain in source_url.lower() for domain in HIGH_RELIABILITY_DOMAINS):
                base_reliability = max(base_reliability, 0.9)

            evidence = ResearchEvidence(
                evidence_id=evidence_id,
                match_id=match_id,
                claim=claim,
                source_url=source_url,
                published_at=published_at,
                reliability_score=round(base_reliability, 2),
                category=category_str
            )

            processed_items.append(evidence)

        return processed_items

    def ingest_evidence(self, evidence_list: List[ResearchEvidence]) -> List[ResearchEvidence]:
        """Filters out prohibited evidence originating from gambling/odds/tipster sources."""
        return [it for it in evidence_list if not it.is_prohibited]
