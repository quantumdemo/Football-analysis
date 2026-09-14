"""Unit tests for Stage 4 Data Validation & Evidence Engine."""

import pytest
from datetime import datetime, timedelta, timezone
from src.research.web_research import ResearchEvidence, EvidenceCategory
from src.validation.validator import DataValidator, EvidenceValidationState


def test_validation_verified_state():
    now = datetime.now(timezone.utc)
    match_time = now + timedelta(hours=24)
    validator = DataValidator()

    evidence = [
        ResearchEvidence("e1", "M100", "Official team news confirmed 4-3-3 tactics", "https://official.com/1", now - timedelta(hours=5), 0.95, EvidenceCategory.TACTICS.value),
        ResearchEvidence("e2", "M100", "Starting defender fit for selection", "https://bbc.com/sport/1", now - timedelta(hours=3), 0.90, EvidenceCategory.TEAM_NEWS.value)
    ]

    report = validator.validate("M100", match_time, evidence)
    assert report.is_valid is True
    assert report.overall_state == EvidenceValidationState.VERIFIED
    assert report.valid_evidence_count == 2


def test_validation_conflicting_state():
    now = datetime.now(timezone.utc)
    match_time = now + timedelta(hours=24)
    validator = DataValidator()

    evidence = [
        ResearchEvidence("e1", "M100", "Conflict: Player A is fit vs Player A is injured", "https://news.com/1", now - timedelta(hours=5), 0.8, EvidenceCategory.TACTICS.value),
        ResearchEvidence("e2", "M100", "Team news update", "https://news.com/2", now - timedelta(hours=3), 0.8, EvidenceCategory.TEAM_NEWS.value)
    ]

    report = validator.validate("M100", match_time, evidence)
    assert report.is_valid is False
    assert report.overall_state == EvidenceValidationState.CONFLICTING


def test_validation_duplicate_removal():
    now = datetime.now(timezone.utc)
    match_time = now + timedelta(hours=24)
    validator = DataValidator()

    evidence = [
        ResearchEvidence("e1", "M100", "Team news update", "https://news.com/1", now - timedelta(hours=5), 0.8, EvidenceCategory.TEAM_NEWS.value),
        ResearchEvidence("e2", "M100", "Team news update", "https://news.com/2", now - timedelta(hours=3), 0.8, EvidenceCategory.TEAM_NEWS.value),
        ResearchEvidence("e3", "M100", "Tactics update", "https://news.com/3", now - timedelta(hours=2), 0.8, EvidenceCategory.TACTICS.value)
    ]

    report = validator.validate("M100", match_time, evidence)
    assert report.duplicate_claims_removed == 1
    assert report.valid_evidence_count == 2


def test_validation_unavailable_state_when_missing_categories():
    now = datetime.now(timezone.utc)
    match_time = now + timedelta(hours=24)
    validator = DataValidator()

    evidence = [
        ResearchEvidence("e1", "M100", "Team news update", "https://news.com/1", now - timedelta(hours=5), 0.8, EvidenceCategory.TEAM_NEWS.value)
        # Missing required 'tactics' category
    ]

    report = validator.validate("M100", match_time, evidence)
    assert report.is_valid is False
    assert report.overall_state == EvidenceValidationState.UNAVAILABLE
    assert "tactics" in report.missing_data_fields
