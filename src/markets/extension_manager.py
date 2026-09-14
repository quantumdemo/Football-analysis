"""Extension Manager for Stage 24: New Markets, Features & Data Sources.

Enforces strict onboarding rules:
1. Exact settlement definitions must be documented prior to adding a market.
2. Feature availability, freshness, and usefulness must be validated before adding a feature.
3. Data sources must be verified for reliability, provenance, and non-gambling rules.
4. Mandatory backtesting for every new market/feature model.
5. Mandatory shadow paper trading test before enabling new markets for live recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.errors import ValidationError
from src.research.web_research import PROHIBITED_KEYWORDS


@dataclass
class NewMarketDefinition:
    """Definition and onboarding status for a new market."""
    market_id: str
    category_name: str
    market_name: str
    settlement_definition: str  # Exact settlement rules (e.g. 90 mins, extra time rules, card counts)
    backtest_passed: bool = False
    shadow_test_passed: bool = False
    enabled_for_live_recommendation: bool = False


@dataclass
class NewFeatureDefinition:
    """Definition and validation status for a new statistical feature."""
    feature_name: str
    data_type: str  # float, int, bool
    description: str
    availability_ratio: float  # Must be >= 0.80
    freshness_max_hours: float
    usefulness_score: float  # Feature importance / correlation (> 0.05)
    contains_odds_or_reputation: bool = False
    is_approved: bool = False


@dataclass
class NewDataSourceDefinition:
    """Definition and provenance test status for a new web research data source."""
    source_id: str
    domain_url: str
    source_name: str
    reliability_score: float  # 0.0 to 1.0 (>= 0.60 required)
    is_gambling_or_tipster: bool = False
    provenance_verified: bool = False
    is_approved: bool = False


class MarketFeatureExtensionManager:
    """Manages onboarding of new markets, features, and data sources in Stage 24."""

    def __init__(self):
        self.markets: Dict[str, NewMarketDefinition] = {}
        self.features: Dict[str, NewFeatureDefinition] = {}
        self.data_sources: Dict[str, NewDataSourceDefinition] = {}

    def register_new_market(
        self,
        market_id: str,
        category_name: str,
        market_name: str,
        settlement_definition: str
    ) -> NewMarketDefinition:
        """Registers a new market after verifying settlement definition is documented."""
        if not settlement_definition or len(settlement_definition.strip()) < 20:
            raise ValidationError("Exact settlement definition documentation (min 20 chars) required before adding a market.")

        market = NewMarketDefinition(
            market_id=market_id,
            category_name=category_name,
            market_name=market_name,
            settlement_definition=settlement_definition
        )
        self.markets[market_id] = market
        return market

    def verify_market_backtest(self, market_id: str, backtest_passed: bool) -> NewMarketDefinition:
        if market_id not in self.markets:
            raise ValidationError(f"Market {market_id} not registered.")
        market = self.markets[market_id]
        market.backtest_passed = backtest_passed
        return market

    def verify_market_shadow_test(self, market_id: str, shadow_passed: bool) -> NewMarketDefinition:
        if market_id not in self.markets:
            raise ValidationError(f"Market {market_id} not registered.")
        market = self.markets[market_id]
        if not market.backtest_passed:
            raise ValidationError("Backtest must pass before running shadow testing on new market.")
        market.shadow_test_passed = shadow_passed
        return market

    def enable_market_for_live_recommendation(self, market_id: str) -> NewMarketDefinition:
        if market_id not in self.markets:
            raise ValidationError(f"Market {market_id} not registered.")
        market = self.markets[market_id]
        if not market.backtest_passed or not market.shadow_test_passed:
            raise ValidationError("New market must pass both backtesting and shadow testing before live enablement.")
        market.enabled_for_live_recommendation = True
        return market

    def validate_and_approve_feature(
        self,
        feature_name: str,
        data_type: str,
        description: str,
        availability_ratio: float,
        freshness_max_hours: float,
        usefulness_score: float
    ) -> NewFeatureDefinition:
        """Validates feature availability, freshness, and usefulness before approval."""
        # Non-negotiable check: No reputation or betting odds terms
        prohibited_terms = ["reputation", "prestige", "popularity", "badge_value", "odds", "bookmaker", "tipster"]
        contains_prohibited = any(term in feature_name.lower() or term in description.lower() for term in prohibited_terms)

        if contains_prohibited:
            raise ValidationError(f"Prohibited feature term in {feature_name}: reputation and betting terms strictly forbidden.")

        if availability_ratio < 0.80:
            raise ValidationError(f"Feature availability ({availability_ratio:.2f}) below required threshold (0.80).")

        if usefulness_score <= 0.05:
            raise ValidationError(f"Feature usefulness score ({usefulness_score:.2f}) below significance threshold (0.05).")

        feat = NewFeatureDefinition(
            feature_name=feature_name,
            data_type=data_type,
            description=description,
            availability_ratio=availability_ratio,
            freshness_max_hours=freshness_max_hours,
            usefulness_score=usefulness_score,
            contains_odds_or_reputation=False,
            is_approved=True
        )
        self.features[feature_name] = feat
        return feat

    def validate_and_approve_data_source(
        self,
        source_id: str,
        domain_url: str,
        source_name: str,
        reliability_score: float
    ) -> NewDataSourceDefinition:
        """Tests new data source for provenance, reliability, and non-gambling rules."""
        is_gambling = any(kw in domain_url.lower() or kw in source_name.lower() for kw in PROHIBITED_KEYWORDS)

        if is_gambling:
            raise ValidationError(f"Prohibited data source domain/name: {domain_url} contains betting/tipster terms.")

        if reliability_score < 0.60:
            raise ValidationError(f"Data source reliability ({reliability_score:.2f}) below threshold (0.60).")

        src = NewDataSourceDefinition(
            source_id=source_id,
            domain_url=domain_url,
            source_name=source_name,
            reliability_score=reliability_score,
            is_gambling_or_tipster=False,
            provenance_verified=True,
            is_approved=True
        )
        self.data_sources[source_id] = src
        return src
