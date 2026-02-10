"""
Lead Scorer - Calculate dependency and qualification scores.

This module implements:
1. Dependency Score: % of company revenue from public contracts
2. Qualification Score: Multi-factor scoring (dependency + activity + sector + contact)

STORY-184: Lead Prospecting Workflow
"""

import logging
from typing import List, Dict
from datetime import datetime, date, timedelta
from decimal import Decimal

from schemas_lead_prospecting import (
    ContractData,
    CompanyData,
    ContactData,
    DependencyScore,
    QualificationScore,
)

logger = logging.getLogger(__name__)


# Revenue estimation by company size (porte)
# Based on BNDES classification and market averages
REVENUE_ESTIMATES = {
    "MEI": Decimal("81000"),  # Up to R$ 81k/year
    "ME": Decimal("360000"),  # Microempresa: up to R$ 360k/year
    "EPP": Decimal("4800000"),  # Small: up to R$ 4.8M/year
    "DEMAIS": Decimal("50000000"),  # Medium: R$ 50M/year average
    "GRANDE": Decimal("500000000"),  # Large: R$ 500M/year average
    "N/A": Decimal("1000000"),  # Default: R$ 1M/year
}


class LeadScorer:
    """Calculate dependency and qualification scores for leads."""

    def calculate_dependency_score(
        self,
        contracts: List[ContractData],
        company_data: CompanyData,
        time_window_months: int = 12,
    ) -> DependencyScore:
        """
        Calculate how dependent a company is on public procurement contracts.

        Formula: (total_contract_value / estimated_annual_revenue) * 100

        Args:
            contracts: List of contracts won by the company
            company_data: Company data from Receita Federal
            time_window_months: Time window for contract analysis

        Returns:
            DependencyScore object
        """
        # Sum contract values
        total_value = sum(c.contract_value for c in contracts)

        # Estimate annual revenue based on company size (porte)
        estimated_revenue = REVENUE_ESTIMATES.get(
            company_data.porte, REVENUE_ESTIMATES["N/A"]
        )

        # Calculate dependency percentage
        if estimated_revenue > 0:
            dependency_pct = float((total_value / estimated_revenue) * 100)
        else:
            dependency_pct = 0.0

        # Classify dependency level
        if dependency_pct >= 70:
            level = "HIGH"
        elif dependency_pct >= 40:
            level = "MEDIUM"
        else:
            level = "LOW"

        return DependencyScore(
            total_contract_value=total_value,
            estimated_annual_revenue=estimated_revenue,
            dependency_percentage=dependency_pct,
            dependency_level=level,
            contract_count=len(contracts),
        )

    def calculate_qualification_score(
        self,
        dependency_score: DependencyScore,
        contracts: List[ContractData],
        sectors: List[str],
        target_sectors: List[str],
        contact_data: ContactData,
    ) -> QualificationScore:
        """
        Calculate multi-factor qualification score (0-10).

        Factors:
        - Dependency Score (40%): How dependent on public contracts
        - Activity Score (20%): Recency of last win
        - Sector Match Score (20%): How well sectors match
        - Contact Quality Score (20%): Quality of contact data

        Args:
            dependency_score: Calculated dependency score
            contracts: List of contracts
            sectors: Company's sectors (from contract objects)
            target_sectors: Target sectors for prospecting
            contact_data: Contact information

        Returns:
            QualificationScore object
        """
        # Factor 1: Dependency Score (40%)
        dep_score = self._score_dependency(dependency_score.dependency_percentage)

        # Factor 2: Activity Score (20%)
        activity_score = self._score_activity(contracts)

        # Factor 3: Sector Match Score (20%)
        sector_score = self._score_sector_match(sectors, target_sectors)

        # Factor 4: Contact Quality Score (20%)
        contact_score = self._score_contact_quality(contact_data)

        # Calculate weighted average
        overall = (
            dep_score * 0.4
            + activity_score * 0.2
            + sector_score * 0.2
            + contact_score * 0.2
        )

        return QualificationScore(
            dependency_score=dep_score,
            activity_score=activity_score,
            sector_match_score=sector_score,
            contact_quality_score=contact_score,
            overall_score=overall,
        )

    def _score_dependency(self, dependency_pct: float) -> float:
        """
        Score dependency percentage (0-10).

        >=70% = 10/10
        60-69% = 7/10
        50-59% = 4/10
        <50% = 0/10
        """
        if dependency_pct >= 70:
            return 10.0
        elif dependency_pct >= 60:
            return 7.0
        elif dependency_pct >= 50:
            return 4.0
        else:
            return 0.0

    def _score_activity(self, contracts: List[ContractData]) -> float:
        """
        Score recency of last contract win (0-10).

        Last 30 days = 10/10
        Last 90 days = 7/10
        Last 180 days = 4/10
        >180 days = 0/10
        """
        if not contracts:
            return 0.0

        # Find most recent contract
        most_recent = max(contracts, key=lambda c: c.contract_date)
        days_ago = (date.today() - most_recent.contract_date).days

        if days_ago <= 30:
            return 10.0
        elif days_ago <= 90:
            return 7.0
        elif days_ago <= 180:
            return 4.0
        else:
            return 0.0

    def _score_sector_match(
        self, company_sectors: List[str], target_sectors: List[str]
    ) -> float:
        """
        Score sector alignment (0-10).

        Exact match = 10/10
        Related match = 6/10
        No match = 2/10
        """
        if not company_sectors or not target_sectors:
            return 2.0

        # Normalize for comparison
        company_set = set(s.lower() for s in company_sectors)
        target_set = set(s.lower() for s in target_sectors)

        # Exact match
        if company_set & target_set:
            return 10.0

        # Related match (contains similar keywords)
        # TODO: Implement more sophisticated sector matching
        return 6.0

    def _score_contact_quality(self, contact_data: ContactData) -> float:
        """
        Score contact data quality (0-10).

        Email + Phone + WhatsApp = 10/10
        Email + Phone = 7/10
        Email only = 4/10
        No email = 0/10
        """
        if not contact_data.email:
            return 0.0

        has_phone = bool(contact_data.phone)
        has_whatsapp = bool(contact_data.whatsapp)

        if has_phone and has_whatsapp:
            return 10.0
        elif has_phone:
            return 7.0
        else:
            return 4.0
