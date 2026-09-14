"""Unit tests for Stage 17 Shadow / Paper Trading Engine."""

import pytest
from datetime import datetime, timedelta, timezone
from src.errors import ValidationError
from src.research.web_research import EvidenceCategory
from src.backtesting.shadow_trader import ShadowTradingEngine, ShadowPredictionRecord, ShadowTradingGateReport


@pytest.fixture
def shadow_engine():
    return ShadowTradingEngine()


@pytest.fixture
def sample_match_input():
    now = datetime.now(timezone.utc)
    return {
        "match_id": "M_SHADOW_100",
        "home_team": "Team_X",
        "away_team": "Team_Y",
        "competition": "Premier League",
        "scheduled_time": (now + timedelta(hours=12)).isoformat(),
        "venue": "Grand Arena"
    }


@pytest.fixture
def sample_evidence():
    now = datetime.now(timezone.utc)
    return [
        {
            "evidence_id": "e1",
            "match_id": "M_SHADOW_100",
            "claim": "Team news update: Key striker starting.",
            "source_url": "https://official.com/1",
            "published_at": (now - timedelta(hours=2)).isoformat(),
            "reliability_score": 0.90,
            "category": EvidenceCategory.TEAM_NEWS.value
        },
        {
            "evidence_id": "e2",
            "match_id": "M_SHADOW_100",
            "claim": "Tactics confirmed: 4-3-3 setup.",
            "source_url": "https://official.com/2",
            "published_at": (now - timedelta(hours=1)).isoformat(),
            "reliability_score": 0.90,
            "category": EvidenceCategory.TACTICS.value
        }
    ]


@pytest.fixture
def sample_stats():
    return {
        "home_form_ppg": 2.4, "away_form_ppg": 0.8,
        "home_goals_scored": 2.2, "home_goals_conceded": 0.6,
        "away_goals_scored": 0.8, "away_goals_conceded": 2.0
    }


def test_record_paper_prediction(shadow_engine, sample_match_input, sample_evidence, sample_stats):
    rec = shadow_engine.record_paper_prediction(sample_match_input, sample_evidence, sample_stats)

    assert rec.match_id == "M_SHADOW_100"
    assert rec.decision == "BET"
    assert rec.is_settled is False
    assert round(sum(rec.probabilities_1x2.values()), 4) == 1.0


def test_immutability_guard_prevents_retroactive_alteration(shadow_engine, sample_match_input, sample_evidence, sample_stats):
    shadow_engine.record_paper_prediction(sample_match_input, sample_evidence, sample_stats)

    # Attempting to re-record prediction for same match_id must fail
    with pytest.raises(ValidationError):
        shadow_engine.record_paper_prediction(sample_match_input, sample_evidence, sample_stats)


def test_settle_paper_prediction(shadow_engine, sample_match_input, sample_evidence, sample_stats):
    shadow_engine.record_paper_prediction(sample_match_input, sample_evidence, sample_stats)

    settled_rec = shadow_engine.settle_paper_prediction("M_SHADOW_100", "HOME", 2, 0)

    assert settled_rec.is_settled is True
    assert settled_rec.actual_outcome == "HOME"
    assert settled_rec.settlement_log_loss > 0.0
    assert settled_rec.settlement_brier_score >= 0.0


def test_evaluate_gates(shadow_engine, sample_match_input, sample_evidence, sample_stats):
    shadow_engine.record_paper_prediction(sample_match_input, sample_evidence, sample_stats)
    shadow_engine.settle_paper_prediction("M_SHADOW_100", "HOME", 2, 0)

    gate_report = shadow_engine.evaluate_gates(max_log_loss=0.90, max_brier=0.45)

    assert isinstance(gate_report, ShadowTradingGateReport)
    assert gate_report.total_shadow_matches == 1
    assert gate_report.settled_matches == 1
    assert gate_report.calibration_gate_passed is True
    assert gate_report.stability_gate_passed is True
    assert gate_report.overall_gate_passed is True
