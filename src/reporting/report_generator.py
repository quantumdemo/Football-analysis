"""Report generator contracts."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class MatchReport:
    """Final match report container."""
    match_id: str
    decision: str
    report_data: Dict[str, Any]
