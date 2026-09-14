"""Market Mapping Engine & Registry Parser.

Parses markets/Matches-market.md taxonomy, maps projected outcome probabilities onto market selections,
defines settlement periods, and handles unsupported markets without using bookmaker odds or predictions.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.models.forecast import ForecastDistribution


@dataclass
class MarketDefinition:
    """Definition of a wagering market taxonomy item."""
    market_id: str
    category_name: str
    market_name: str
    settlement_period: str  # e.g. "Full Time", "1st Half", "2nd Half"
    valid_selections: List[str]
    is_supported: bool = True


@dataclass
class MarketSelectionForecast:
    """Projected probability for a specific market selection."""
    selection_name: str
    projected_probability: float
    confidence_score: float


@dataclass
class MarketMappingReport:
    """Container for mapped market selection probabilities."""
    match_id: str
    market_id: str
    market_name: str
    settlement_period: str
    is_supported: bool
    selection_forecasts: List[MarketSelectionForecast] = field(default_factory=list)
    mapping_notes: Optional[str] = None


class MarketRegistry:
    """Parses and holds the taxonomy of markets from markets/Matches-market.md."""

    def __init__(self, catalog_path: str = "markets/Matches-market.md"):
        self.catalog_path = Path(catalog_path)
        self.registry: Dict[str, MarketDefinition] = {}
        self._load_and_parse_catalog()

    def _load_and_parse_catalog(self):
        if not self.catalog_path.exists():
            return

        with open(self.catalog_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        current_category = "General"
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("## "):
                current_category = line_str.replace("## ", "").strip()
            elif line_str.startswith("- ") or line_str.startswith("  - "):
                market_name = line_str.lstrip("- ").strip()
                market_id = market_name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")

                settlement = "Full Time"
                if "1st half" in market_name.lower():
                    settlement = "1st Half"
                elif "2nd half" in market_name.lower():
                    settlement = "2nd Half"

                selections = ["Option_1", "Option_2"]
                if "1x2" in market_name.lower():
                    selections = ["Home (1)", "Draw (X)", "Away (2)"]
                elif "double chance" in market_name.lower():
                    selections = ["Home or Draw (1X)", "Home or Away (12)", "Draw or Away (X2)"]
                elif "draw no bet" in market_name.lower():
                    selections = ["Home", "Away"]
                elif "over/under" in market_name.lower():
                    selections = ["Over", "Under"]

                supported = any(sup in market_id for sup in ["1x2", "double_chance", "draw_no_bet", "over_under", "both_teams"])

                self.registry[market_id] = MarketDefinition(
                    market_id=market_id,
                    category_name=current_category,
                    market_name=market_name,
                    settlement_period=settlement,
                    valid_selections=selections,
                    is_supported=supported
                )

    def get_market(self, market_id: str) -> Optional[MarketDefinition]:
        return self.registry.get(market_id)


class MarketMapper:
    """Maps raw ForecastDistribution probabilities onto structured market selections."""

    def __init__(self, registry: Optional[MarketRegistry] = None):
        self.registry = registry or MarketRegistry()

    def map_market(self, forecast: ForecastDistribution, market_id: str) -> MarketMappingReport:
        market_def = self.registry.get_market(market_id)

        if not market_def or not market_def.is_supported:
            return MarketMappingReport(
                match_id=forecast.match_id,
                market_id=market_id,
                market_name=market_def.market_name if market_def else market_id,
                settlement_period=market_def.settlement_period if market_def else "Full Time",
                is_supported=False,
                selection_forecasts=[],
                mapping_notes="Unsupported or unregistered market in current forecasting pipeline."
            )

        selections: List[MarketSelectionForecast] = []

        if "1x2" in market_id and "1st" not in market_id and "2nd" not in market_id:
            selections = [
                MarketSelectionForecast("Home (1)", forecast.p_home_win, forecast.model_confidence),
                MarketSelectionForecast("Draw (X)", forecast.p_draw, forecast.model_confidence),
                MarketSelectionForecast("Away (2)", forecast.p_away_win, forecast.model_confidence)
            ]
        elif "double_chance" in market_id:
            p_1x = round(forecast.p_home_win + forecast.p_draw, 5)
            p_12 = round(forecast.p_home_win + forecast.p_away_win, 5)
            p_x2 = round(forecast.p_draw + forecast.p_away_win, 5)
            selections = [
                MarketSelectionForecast("Home or Draw (1X)", p_1x, forecast.model_confidence),
                MarketSelectionForecast("Home or Away (12)", p_12, forecast.model_confidence),
                MarketSelectionForecast("Draw or Away (X2)", p_x2, forecast.model_confidence)
            ]
        elif "draw_no_bet" in market_id:
            # Re-normalize Home and Away ignoring Draw
            dnb_sum = forecast.p_home_win + forecast.p_away_win
            if dnb_sum > 0:
                p_home_dnb = round(forecast.p_home_win / dnb_sum, 5)
                p_away_dnb = round(forecast.p_away_win / dnb_sum, 5)
            else:
                p_home_dnb, p_away_dnb = 0.5, 0.5
            selections = [
                MarketSelectionForecast("Home", p_home_dnb, forecast.model_confidence),
                MarketSelectionForecast("Away", p_away_dnb, forecast.model_confidence)
            ]
        elif "over_under" in market_id or "0.5" in market_id or "1.5" in market_id or "2.5" in market_id:
            selections = [
                MarketSelectionForecast("Over 2.5", forecast.p_over_2_5_goals, forecast.model_confidence),
                MarketSelectionForecast("Under 2.5", forecast.p_under_2_5_goals, forecast.model_confidence)
            ]

        return MarketMappingReport(
            match_id=forecast.match_id,
            market_id=market_id,
            market_name=market_def.market_name,
            settlement_period=market_def.settlement_period,
            is_supported=True,
            selection_forecasts=selections,
            mapping_notes="Successfully mapped forecast probabilities to market taxonomy."
        )
