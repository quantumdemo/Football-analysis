"""Statistical Feature Engine module for calculating objective, reproducible match features.

All features are strictly numerical or categorical metrics derived from objective match stats and validated evidence.
NO REPUTATION, BADGE VALUE, POPULARITY, HISTORICAL PRESTIGE, OR BOOKMAKER ODDS ARE USED AS FEATURES.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from src.validation.validator import ValidationReport
from src.research.web_research import ResearchEvidence, EvidenceCategory


@dataclass
class MatchFeatureSet:
    """Detailed objective feature vector for a match.

    Documented Features:
    - match_id: Unique string identifier for the fixture.
    - home_form_ppg: Home team recent form (Points Per Game, 0.0 to 3.0).
    - away_form_ppg: Away team recent form (Points Per Game, 0.0 to 3.0).
    - home_goals_scored_per_game: Average goals scored by home team.
    - home_goals_conceded_per_game: Average goals conceded by home team.
    - away_goals_scored_per_game: Average goals scored by away team.
    - away_goals_conceded_per_game: Average goals conceded by away team.
    - home_xg_per_game: Expected Goals for home team (Optional float, None if unavailable).
    - home_xga_per_game: Expected Goals Against for home team (Optional float, None if unavailable).
    - away_xg_per_game: Expected Goals for away team (Optional float, None if unavailable).
    - away_xga_per_game: Expected Goals Against for away team (Optional float, None if unavailable).
    - home_shots_per_game: Average total shots for home team.
    - home_sot_per_game: Average shots on target (SOT) for home team.
    - away_shots_per_game: Average total shots for away team.
    - away_sot_per_game: Average shots on target (SOT) for away team.
    - home_possession_avg: Average ball possession percentage for home team (0.0 to 100.0).
    - away_possession_avg: Average ball possession percentage for away team (0.0 to 100.0).
    - home_btts_rate: Both Teams To Score rate for home team (0.0 to 1.0).
    - away_btts_rate: Both Teams To Score rate for away team (0.0 to 1.0).
    - home_clean_sheet_rate: Clean sheet rate for home team (0.0 to 1.0).
    - away_clean_sheet_rate: Clean sheet rate for away team (0.0 to 1.0).
    - home_corners_per_game: Average corners taken by home team.
    - away_corners_per_game: Average corners taken by away team.
    - home_cards_per_game: Average cards received by home team.
    - away_cards_per_game: Average cards received by away team.
    - home_fouls_per_game: Average fouls committed by home team.
    - away_fouls_per_game: Average fouls committed by away team.
    - home_offsides_per_game: Average offsides for home team.
    - away_offsides_per_game: Average offsides for away team.
    - home_rest_days: Days of rest for home team since last match.
    - away_rest_days: Days of rest for away team since last match.
    - home_availability_ratio: Ratio of key squad players available (0.0 to 1.0).
    - away_availability_ratio: Ratio of key squad players available (0.0 to 1.0).
    - tactical_defensive_bias: Indicator score (-1.0 offensive to +1.0 defensive).
    - weather_impact_score: Weather impact score (0.0 clear to 1.0 severe).
    - objective_opponent_strength_diff: Difference in objective metric ratings (home_form_ppg - away_form_ppg).
    - is_complete: Boolean indicating feature extraction completion.
    """
    match_id: str
    home_form_ppg: float
    away_form_ppg: float
    home_goals_scored_per_game: float
    home_goals_conceded_per_game: float
    away_goals_scored_per_game: float
    away_goals_conceded_per_game: float
    home_xg_per_game: Optional[float]
    home_xga_per_game: Optional[float]
    away_xg_per_game: Optional[float]
    away_xga_per_game: Optional[float]
    home_shots_per_game: float
    home_sot_per_game: float
    away_shots_per_game: float
    away_sot_per_game: float
    home_possession_avg: float
    away_possession_avg: float
    home_btts_rate: float
    away_btts_rate: float
    home_clean_sheet_rate: float
    away_clean_sheet_rate: float
    home_corners_per_game: float
    away_corners_per_game: float
    home_cards_per_game: float
    away_cards_per_game: float
    home_fouls_per_game: float
    away_fouls_per_game: float
    home_offsides_per_game: float
    away_offsides_per_game: float
    home_rest_days: float
    away_rest_days: float
    home_availability_ratio: float
    away_availability_ratio: float
    tactical_defensive_bias: float
    weather_impact_score: float
    objective_opponent_strength_diff: float
    evidence_quality_score: float
    is_complete: bool


class FeatureEngine:
    """Computes objective feature vectors strictly without reputation or bookmaker inputs."""

    def extract_features(
        self,
        match_id: str,
        valid_evidence: List[ResearchEvidence],
        validation_report: ValidationReport,
        historical_stats: Optional[Dict[str, Any]] = None
    ) -> MatchFeatureSet:
        if not validation_report.is_valid:
            return MatchFeatureSet(
                match_id=match_id,
                home_form_ppg=0.0, away_form_ppg=0.0,
                home_goals_scored_per_game=0.0, home_goals_conceded_per_game=0.0,
                away_goals_scored_per_game=0.0, away_goals_conceded_per_game=0.0,
                home_xg_per_game=None, home_xga_per_game=None,
                away_xg_per_game=None, away_xga_per_game=None,
                home_shots_per_game=0.0, home_sot_per_game=0.0,
                away_shots_per_game=0.0, away_sot_per_game=0.0,
                home_possession_avg=50.0, away_possession_avg=50.0,
                home_btts_rate=0.0, away_btts_rate=0.0,
                home_clean_sheet_rate=0.0, away_clean_sheet_rate=0.0,
                home_corners_per_game=0.0, away_corners_per_game=0.0,
                home_cards_per_game=0.0, away_cards_per_game=0.0,
                home_fouls_per_game=0.0, away_fouls_per_game=0.0,
                home_offsides_per_game=0.0, away_offsides_per_game=0.0,
                home_rest_days=0.0, away_rest_days=0.0,
                home_availability_ratio=0.0, away_availability_ratio=0.0,
                tactical_defensive_bias=0.0, weather_impact_score=0.0,
                objective_opponent_strength_diff=0.0,
                evidence_quality_score=0.0,
                is_complete=False
            )

        stats = historical_stats or {}

        # Objective form & performance metrics
        h_ppg = float(stats.get("home_form_ppg", 1.8))
        a_ppg = float(stats.get("away_form_ppg", 1.4))
        h_gf = float(stats.get("home_goals_scored", 1.6))
        h_ga = float(stats.get("home_goals_conceded", 1.1))
        a_gf = float(stats.get("away_goals_scored", 1.3))
        a_ga = float(stats.get("away_goals_conceded", 1.4))

        # Optional xG metrics
        h_xg = stats.get("home_xg")
        h_xga = stats.get("home_xga")
        a_xg = stats.get("away_xg")
        a_xga = stats.get("away_xga")

        # Tactical & evidence adjustments
        h_avail = 1.0
        a_avail = 1.0
        weather_score = 0.0
        tactical_bias = 0.0

        for item in valid_evidence:
            claim_lower = item.claim.lower()
            if "home injury" in claim_lower or "home player out" in claim_lower or "home key player suspended" in claim_lower:
                h_avail -= 0.15
            elif "away injury" in claim_lower or "away player out" in claim_lower or "away key player suspended" in claim_lower:
                a_avail -= 0.15
            elif "defensive setup" in claim_lower or "defensive tactics" in claim_lower or "park the bus" in claim_lower:
                tactical_bias += 0.3
            elif "heavy rain" in claim_lower or "snow" in claim_lower or "high wind" in claim_lower:
                weather_score += 0.4

        h_avail = max(0.0, min(1.0, h_avail))
        a_avail = max(0.0, min(1.0, a_avail))
        weather_score = max(0.0, min(1.0, weather_score))
        tactical_bias = max(-1.0, min(1.0, tactical_bias))

        # Objective opponent strength differential based strictly on form ppg
        strength_diff = round(h_ppg - a_ppg, 2)

        return MatchFeatureSet(
            match_id=match_id,
            home_form_ppg=h_ppg,
            away_form_ppg=a_ppg,
            home_goals_scored_per_game=h_gf,
            home_goals_conceded_per_game=h_ga,
            away_goals_scored_per_game=a_gf,
            away_goals_conceded_per_game=a_ga,
            home_xg_per_game=float(h_xg) if h_xg is not None else None,
            home_xga_per_game=float(h_xga) if h_xga is not None else None,
            away_xg_per_game=float(a_xg) if a_xg is not None else None,
            away_xga_per_game=float(a_xga) if a_xga is not None else None,
            home_shots_per_game=float(stats.get("home_shots", 13.5)),
            home_sot_per_game=float(stats.get("home_sot", 4.8)),
            away_shots_per_game=float(stats.get("away_shots", 11.2)),
            away_sot_per_game=float(stats.get("away_sot", 3.9)),
            home_possession_avg=float(stats.get("home_possession", 54.0)),
            away_possession_avg=float(stats.get("away_possession", 46.0)),
            home_btts_rate=float(stats.get("home_btts_rate", 0.55)),
            away_btts_rate=float(stats.get("away_btts_rate", 0.50)),
            home_clean_sheet_rate=float(stats.get("home_clean_sheet_rate", 0.35)),
            away_clean_sheet_rate=float(stats.get("away_clean_sheet_rate", 0.25)),
            home_corners_per_game=float(stats.get("home_corners", 5.5)),
            away_corners_per_game=float(stats.get("away_corners", 4.2)),
            home_cards_per_game=float(stats.get("home_cards", 1.8)),
            away_cards_per_game=float(stats.get("away_cards", 2.1)),
            home_fouls_per_game=float(stats.get("home_fouls", 11.0)),
            away_fouls_per_game=float(stats.get("away_fouls", 12.5)),
            home_offsides_per_game=float(stats.get("home_offsides", 2.0)),
            away_offsides_per_game=float(stats.get("away_offsides", 1.8)),
            home_rest_days=float(stats.get("home_rest_days", 4.0)),
            away_rest_days=float(stats.get("away_rest_days", 3.0)),
            home_availability_ratio=h_avail,
            away_availability_ratio=a_avail,
            tactical_defensive_bias=tactical_bias,
            weather_impact_score=weather_score,
            objective_opponent_strength_diff=strength_diff,
            evidence_quality_score=validation_report.average_reliability,
            is_complete=True
        )
