"""Tests for research ingestion and data validation."""

import pytest
from datetime import datetime, timedelta, timezone
from src.research.web_research import ResearchEvidence, ResearchIngestor
from src.validation.validator import DataValidator


def test_prohibited_sources_rejected():
    now = datetime.now(timezone.utc)
    evidence_good = ResearchEvidence(
        evidence_id="1",
        match_id="M100",
        claim="Home striker returned to full training.",
        source_url="https://sportsnews.example.com/team-news",
        published_at=now - timedelta(hours=10),
        reliability_score=0.8,
        category="team_news"
    )

    evidence_odds = ResearchEvidence(
        evidence_id="2",
        match_id="M100",
        claim="Bookmaker odds favor Home win at 1.80",
        source_url="https://bettingodds.example.com/match",
        published_at=now - timedelta(hours=5),
        reliability_score=0.9,
        category="odds"
    )

    ingestor = ResearchIngestor()
    filtered = ingestor.ingest_evidence([evidence_good, evidence_odds])

    assert len(filtered) == 1
    assert filtered[0].evidence_id == "1"


def test_missing_required_category_invalidates():
    now = datetime.now(timezone.utc)
    match_time = now + timedelta(hours=12)
    validator = DataValidator()

    evidence_team_news = ResearchEvidence(
        evidence_id="1",
        match_id="M100",
        claim="Home team wingers are fit.",
        source_url="https://news.example.com/item1",
        published_at=now - timedelta(hours=2),
        reliability_score=0.8,
        category="team_news"
    )

    report = validator.validate(
        match_id="M100",
        scheduled_time=match_time,
        evidence_items=[evidence_team_news],
        required_categories=["team_news", "tactics"]
    )

    assert not report.is_valid
    assert "tactics" in report.missing_data_fields
