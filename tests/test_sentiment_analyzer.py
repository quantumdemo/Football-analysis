"""Unit tests for Stage 9 News, Context & Sentiment Engine."""

import pytest
from datetime import datetime, timezone
from src.research.web_research import ResearchEvidence, EvidenceCategory
from src.sentiment.sentiment_analyzer import ContextSentimentAnalyzer, ClaimType, ContextSentimentReport


def test_analyze_facts_vs_rumors():
    analyzer = ContextSentimentAnalyzer()
    now = datetime.now(timezone.utc)

    evidence = [
        ResearchEvidence("e1", "M100", "Home team head coach confirmed defender injury in press conference.", "https://official.com/1", now, 0.95, EvidenceCategory.INJURIES_SUSPENSIONS.value),
        ResearchEvidence("e2", "M100", "Social media rumour claims away striker had disagreement with manager.", "https://fanforum.com/2", now, 0.50, EvidenceCategory.PUBLIC_DISCUSSION.value)
    ]

    report = analyzer.analyze("M100", evidence)
    assert report.match_id == "M100"
    assert report.fact_count == 1
    assert report.rumor_count == 1
    assert report.context_items[0].claim_type == ClaimType.FACT
    assert report.context_items[1].claim_type == ClaimType.RUMOR_OPINION


def test_analyze_context_categories_and_secondary_modifier():
    analyzer = ContextSentimentAnalyzer()
    now = datetime.now(timezone.utc)

    evidence = [
        ResearchEvidence("e1", "M100", "Home team facing high motivation in must win derby match.", "https://bbc.com/sport/1", now, 0.90, EvidenceCategory.MANAGER_COMMENTS.value),
        ResearchEvidence("e2", "M100", "Away team suffering from fixture congestion and busy schedule.", "https://bbc.com/sport/2", now, 0.90, EvidenceCategory.REST_CONGESTION.value)
    ]

    report = analyzer.analyze("M100", evidence)
    assert report.home_context_score > 0.0
    assert report.away_context_score < 0.0
    assert report.secondary_confidence_modifier > 0.0


def test_analyze_empty_evidence():
    analyzer = ContextSentimentAnalyzer()
    report = analyzer.analyze("M101", [])

    assert report.match_id == "M101"
    assert report.fact_count == 0
    assert report.rumor_count == 0
    assert report.secondary_confidence_modifier == 0.0
