"""Forecast distribution contracts."""

from dataclasses import dataclass


@dataclass
class ForecastDistribution:
    """Probabilistic match outcome distribution (must sum to 1.0)."""
    match_id: str
    p_home_win: float
    p_draw: float
    p_away_win: float
    model_confidence: float

    def __post_init__(self):
        total = round(self.p_home_win + self.p_draw + self.p_away_win, 5)
        if total != 1.0:
            raise ValueError(f"Probabilities must sum to 1.0, got {total}")
