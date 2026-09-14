"""News, Context & Sentiment Engine for evidence-linked contextual sentiment analysis.

Separates facts from opinions/rumours, detects injuries, rotation, congestion, motivation,
and tactical shifts, treating sentiment strictly as a secondary modifier.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from src.research.web_research import ResearchEvidence


class ClaimType(Enum):
    FACT = "FACT"
    RUMOR_OPINION = "RUMOR_OPINION"


@dataclass
class ContextItem:
    """Classified context claim item."""
    claim_id: str
    claim: str
    source_url: str
    claim_type: ClaimType
    context_category: str  # e.g., "injuries", "rotation", "congestion", "motivation", "tactics", "discussion"
    sentiment_score: float  # -1.0 (negative) to +1.0 (positive)
    evidence_linked: bool = True


@dataclass
class ContextSentimentReport:
    """Report summarizing contextual analysis and secondary sentiment modifiers."""
    match_id: str
    fact_count: int
    rumor_count: int
    home_context_score: float  # -1.0 to +1.0
    away_context_score: float  # -1.0 to +1.0
    context_items: List[ContextItem] = field(default_factory=list)
    secondary_confidence_modifier: float = 0.0  # Slight adjustment (-0.1 to +0.1) based on verified context


class ContextSentimentAnalyzer:
    """Analyzes validated research evidence to extract structured context and secondary sentiment."""

    RUMOR_KEYWORDS = ["rumour", "rumor", "speculation", "reportedly", "alleged", "fan opinion", "social media claims"]

    def analyze(self, match_id: str, valid_evidence: List[ResearchEvidence]) -> ContextSentimentReport:
        if not valid_evidence:
            return ContextSentimentReport(
                match_id=match_id,
                fact_count=0,
                rumor_count=0,
                home_context_score=0.0,
                away_context_score=0.0,
                context_items=[],
                secondary_confidence_modifier=0.0
            )

        context_items: List[ContextItem] = []
        fact_count = 0
        rumor_count = 0

        home_score = 0.0
        away_score = 0.0

        for item in valid_evidence:
            claim_lower = item.claim.lower()

            # Separate facts from rumors/opinions
            is_rumor = any(rk in claim_lower for rk in self.RUMOR_KEYWORDS) or item.reliability_score < 0.65
            claim_type = ClaimType.RUMOR_OPINION if is_rumor else ClaimType.FACT

            if claim_type == ClaimType.FACT:
                fact_count += 1
                weight = 1.0
            else:
                rumor_count += 1
                weight = 0.3  # Reduced weight for rumors/opinions

            # Context category detection & sentiment assignment
            sentiment = 0.0
            category = "general_discussion"

            if "injury" in claim_lower or "ruled out" in claim_lower or "suspended" in claim_lower:
                category = "injuries"
                sentiment = -0.6
            elif "fit" in claim_lower or "returned to training" in claim_lower:
                category = "injuries"
                sentiment = +0.5
            elif "rotation" in claim_lower or "rested" in claim_lower:
                category = "rotation"
                sentiment = -0.3
            elif "congestion" in claim_lower or "busy schedule" in claim_lower:
                category = "congestion"
                sentiment = -0.4
            elif "must win" in claim_lower or "high motivation" in claim_lower or "cup final" in claim_lower:
                category = "motivation"
                sentiment = +0.6
            elif "tactical" in claim_lower or "formation" in claim_lower:
                category = "tactics"
                sentiment = +0.2

            # Attribute sentiment to home or away team
            if "home" in claim_lower:
                home_score += sentiment * weight
            elif "away" in claim_lower:
                away_score += sentiment * weight

            context_items.append(ContextItem(
                claim_id=item.evidence_id,
                claim=item.claim,
                source_url=item.source_url,
                claim_type=claim_type,
                context_category=category,
                sentiment_score=sentiment,
                evidence_linked=True
            ))

        # Normalize context scores
        home_score = max(-1.0, min(1.0, round(home_score / max(1, fact_count), 2)))
        away_score = max(-1.0, min(1.0, round(away_score / max(1, fact_count), 2)))

        # Secondary confidence modifier (strictly secondary, max adjustment +/- 0.10)
        modifier = round((home_score - away_score) * 0.05, 2)

        return ContextSentimentReport(
            match_id=match_id,
            fact_count=fact_count,
            rumor_count=rumor_count,
            home_context_score=home_score,
            away_context_score=away_score,
            context_items=context_items,
            secondary_confidence_modifier=modifier
        )
