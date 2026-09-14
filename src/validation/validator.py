"""Data validation engine enforcing strict quality, freshness, duplicate removal, contradiction detection, and explicit evidence status tracking."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Dict, Any, Set
from src.research.web_research import ResearchEvidence, EvidenceCategory


class EvidenceValidationState(Enum):
    VERIFIED = "VERIFIED"
    LIKELY = "LIKELY"
    UNCERTAIN = "UNCERTAIN"
    CONFLICTING = "CONFLICTING"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class ValidatedEvidenceItem:
    """An individual research evidence item with an explicit validation state."""
    evidence: ResearchEvidence
    state: EvidenceValidationState
    validation_notes: str


@dataclass
class ValidationReport:
    """Report summarizing validation findings for research evidence."""
    match_id: str
    is_valid: bool
    overall_state: EvidenceValidationState
    freshness_ok: bool
    missing_data_fields: List[str] = field(default_factory=list)
    conflicting_claims: List[str] = field(default_factory=list)
    duplicate_claims_removed: int = 0
    prohibited_items_rejected: int = 0
    valid_evidence_count: int = 0
    average_reliability: float = 0.0
    validated_items: List[ValidatedEvidenceItem] = field(default_factory=list)

    @property
    def valid_evidence_items(self) -> List[ResearchEvidence]:
        """Returns underlying ResearchEvidence objects for valid items."""
        return [it.evidence for it in self.validated_items if it.state in (EvidenceValidationState.VERIFIED, EvidenceValidationState.LIKELY)]


class DataValidator:
    """Validates research evidence using explicit states without inventing missing data."""

    def __init__(self, max_age_hours: float = 72.0, min_reliability: float = 0.5):
        self.max_age_hours = max_age_hours
        self.min_reliability = min_reliability

    def validate(
        self,
        match_id: str,
        scheduled_time: datetime,
        evidence_items: List[ResearchEvidence],
        required_categories: List[str] = None
    ) -> ValidationReport:
        if required_categories is None:
            required_categories = [EvidenceCategory.TEAM_NEWS.value, EvidenceCategory.TACTICS.value]

        if not evidence_items:
            return ValidationReport(
                match_id=match_id,
                is_valid=False,
                overall_state=EvidenceValidationState.UNAVAILABLE,
                freshness_ok=False,
                missing_data_fields=required_categories,
                conflicting_claims=[],
                duplicate_claims_removed=0,
                prohibited_items_rejected=0,
                valid_evidence_count=0,
                average_reliability=0.0,
                validated_items=[]
            )

        prohibited_rejected = 0
        duplicates_removed = 0
        seen_claims: Set[str] = set()
        validated_list: List[ValidatedEvidenceItem] = []
        conflicts: List[str] = []
        found_categories: Set[str] = set()

        # Check for direct contradictions (e.g. conflicting injury reports)
        claims_text = [it.claim.lower() for it in evidence_items if not it.is_prohibited]
        has_direct_conflict = any("conflict:" in c or ("fit" in c and "injured" in c) for c in claims_text)

        for item in evidence_items:
            if item.is_prohibited:
                prohibited_rejected += 1
                continue

            claim_norm = item.claim.strip().lower()

            # Duplicate check
            if claim_norm in seen_claims:
                duplicates_removed += 1
                continue
            seen_claims.add(claim_norm)

            # Post-kickoff check
            if item.published_at > scheduled_time:
                validated_list.append(ValidatedEvidenceItem(
                    evidence=item,
                    state=EvidenceValidationState.UNCERTAIN,
                    validation_notes="Published post-kickoff."
                ))
                continue

            # Freshness check
            age = scheduled_time - item.published_at
            if age.total_seconds() < 0 or age > timedelta(hours=self.max_age_hours):
                validated_list.append(ValidatedEvidenceItem(
                    evidence=item,
                    state=EvidenceValidationState.UNCERTAIN,
                    validation_notes=f"Stale evidence (older than {self.max_age_hours}h)."
                ))
                continue

            # Contradiction flag
            if "conflict:" in claim_norm:
                conflicts.append(item.claim)
                validated_list.append(ValidatedEvidenceItem(
                    evidence=item,
                    state=EvidenceValidationState.CONFLICTING,
                    validation_notes="Claim marked as conflicting."
                ))
                continue

            # State assignment based on source reliability
            if item.reliability_score >= 0.85:
                state = EvidenceValidationState.VERIFIED
            elif item.reliability_score >= self.min_reliability:
                state = EvidenceValidationState.LIKELY
            else:
                state = EvidenceValidationState.UNCERTAIN

            validated_list.append(ValidatedEvidenceItem(
                evidence=item,
                state=state,
                validation_notes="Valid evidence."
            ))
            found_categories.add(item.category)

        # Check missing categories
        missing_fields = [cat for cat in required_categories if cat not in found_categories]

        valid_items_only = [v for v in validated_list if v.state in (EvidenceValidationState.VERIFIED, EvidenceValidationState.LIKELY)]

        if not valid_items_only:
            avg_rel = 0.0
            freshness_ok = False
        else:
            avg_rel = sum(it.evidence.reliability_score for it in valid_items_only) / len(valid_items_only)
            freshness_ok = True

        if conflicts or has_direct_conflict:
            overall_state = EvidenceValidationState.CONFLICTING
        elif missing_fields or not valid_items_only:
            overall_state = EvidenceValidationState.UNAVAILABLE
        elif avg_rel < self.min_reliability:
            overall_state = EvidenceValidationState.UNCERTAIN
        else:
            overall_state = EvidenceValidationState.VERIFIED

        is_valid = (overall_state in (EvidenceValidationState.VERIFIED, EvidenceValidationState.LIKELY) and len(missing_fields) == 0)

        return ValidationReport(
            match_id=match_id,
            is_valid=is_valid,
            overall_state=overall_state,
            freshness_ok=freshness_ok,
            missing_data_fields=missing_fields,
            conflicting_claims=conflicts,
            duplicate_claims_removed=duplicates_removed,
            prohibited_items_rejected=prohibited_rejected,
            valid_evidence_count=len(valid_items_only),
            average_reliability=round(avg_rel, 2),
            validated_items=validated_list
        )
