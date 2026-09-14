"""Risk evaluation contracts."""

from dataclasses import dataclass


@dataclass
class RiskEvaluation:
    """Outcome of risk assessment."""
    match_id: str
    decision: str  # "BET" or "NO_BET"
    reason: str
    confidence_score: float
