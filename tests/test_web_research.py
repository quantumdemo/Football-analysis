"""Unit tests for Stage 3 Web Research Engine module."""

import pytest
from datetime import datetime, timezone
from src.research.web_research import ResearchCollector, ResearchEvidence, EvidenceCategory


def test_collect_valid_non_betting_evidence():
    collector = ResearchCollector()
    raw_data = [
        {
            "evidence_id": "ev1",
            "match_id": "M100",
            "claim": "Head coach confirmed starting 4-3-3 formation in pre-match press conference.",
            "source_url": "https://officialclubsite.com/news/1",
            "published_at": "2026-10-15T10:00:00+00:00",
            "reliability_score": 0.95,
            "category": EvidenceCategory.TACTICS.value
        },
        {
            "evidence_id": "ev2",
            "match_id": "M100",
            "claim": "Star striker ruled out for 3 weeks due to hamstring strain.",
            "source_url": "https://bbc.com/sport/football/injuries",
            "published_at": "2026-10-15T12:00:00+00:00",
            "reliability_score": 0.85,
            "category": EvidenceCategory.INJURIES_SUSPENSIONS.value
        }
    ]

    collected = collector.collect_evidence(raw_data)
    assert len(collected) == 2
    assert collected[0].category == "tactics"
    assert collected[1].reliability_score == 0.9  # High reliability domain override


def test_reject_betting_odds_and_tipster_sources():
    collector = ResearchCollector()
    raw_data = [
        {
            "evidence_id": "ev_valid",
            "match_id": "M101",
            "claim": "Heavy rain forecast during match hours.",
            "source_url": "https://weather.com/forecast",
            "published_at": "2026-10-15T14:00:00+00:00",
            "category": EvidenceCategory.WEATHER_PITCH.value
        },
        {
            "evidence_id": "ev_odds",
            "match_id": "M101",
            "claim": "Betting odds cut for Home team win at 1.75 decimal.",
            "source_url": "https://betting365.example.com/odds",
            "published_at": "2026-10-15T14:30:00+00:00",
            "category": "odds"
        },
        {
            "evidence_id": "ev_tipster",
            "match_id": "M101",
            "claim": "Pro tipster pick: Back Over 2.5 goals.",
            "source_url": "https://tipsterpicks.example.com/recommendations",
            "published_at": "2026-10-15T15:00:00+00:00",
            "category": "predictions"
        }
    ]

    collected = collector.collect_evidence(raw_data)
    assert len(collected) == 1
    assert collected[0].evidence_id == "ev_valid"
