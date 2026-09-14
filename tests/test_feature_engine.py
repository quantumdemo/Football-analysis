"""Unit tests for Stage 5 Statistical Feature Engine."""

import pytest
from datetime import datetime, timezone
from src.research.web_research import ResearchEvidence, EvidenceCategory
from src.validation.validator import ValidationReport, EvidenceValidationState
from src.features.feature_engine import FeatureEngine, MatchFeatureSet


def test_extract_features_valid_match():
    engine = FeatureEngine()
    now = datetime.now(timezone.utc)

    report = ValidationReport(
        match_id="M100",
        is_valid=True,
        overall_state=EvidenceValidationState.VERIFIED,
        freshness_ok=True,
        valid_evidence_count=2,
        average_reliability=0.9
    )

    evidence = [
        ResearchEvidence("e1", "M100", "Home player out with injury", "https://official.com/1", now, 0.9, EvidenceCategory.INJURIES_SUSPENSIONS.value),
        ResearchEvidence("e2", "M100", "Defensive tactics planned by away team", "https://news.com/2", now, 0.9, EvidenceCategory.TACTICS.value)
    ]

    stats = {
        "home_form_ppg": 2.1,
        "away_form_ppg": 1.2,
        "home_xg": 1.85,
        "home_xga": 0.95,
        "away_xg": None,  # Missing optional xG
        "away_xga": None
    }

    features = engine.extract_features("M100", evidence, report, stats)

    assert features.match_id == "M100"
    assert features.is_complete is True
    assert features.home_form_ppg == 2.1
    assert features.away_form_ppg == 1.2
    assert features.home_xg_per_game == 1.85
    assert features.away_xg_per_game is None  # Does not invent missing xG data
    assert features.home_availability_ratio == 0.85
    assert features.objective_opponent_strength_diff == 0.9  # 2.1 - 1.2


def test_extract_features_invalid_validation_returns_incomplete():
    engine = FeatureEngine()

    report = ValidationReport(
        match_id="M101",
        is_valid=False,
        overall_state=EvidenceValidationState.UNAVAILABLE,
        freshness_ok=False,
        valid_evidence_count=0
    )

    features = engine.extract_features("M101", [], report)

    assert features.match_id == "M101"
    assert features.is_complete is False


def test_no_reputation_attributes_in_feature_set():
    field_names = set(MatchFeatureSet.__dataclass_fields__.keys())
    prohibited_terms = ["reputation", "prestige", "popularity", "badge_value", "odds", "bookmaker"]
    for term in prohibited_terms:
        for field_name in field_names:
            assert term not in field_name.lower()
