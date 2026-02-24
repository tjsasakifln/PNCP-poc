"""
Lead Scorer - Calculate dependency and qualification scores.

This module implements:
1. Dependency Score: % of company revenue from public contracts (deprecated)
2. Qualification Score: Multi-factor scoring (deprecated)
3. Buy-Intent Score: 6-factor model (primary)
4. Growth Metrics: Computed procurement activity metrics

STORY-184: Lead Prospecting Workflow
"""

import logging
from typing import List, Optional
from datetime import date, timedelta
from decimal import Decimal

from schemas_lead_prospecting import (
    ContractData,
    CompanyData,
    ContactData,
    DependencyScore,
    QualificationScore,
    BuyIntentScore,
    GrowthMetrics,
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

    # ------------------------------------------------------------------
    # Buy-Intent Score — 6-factor model (primary scoring)
    # ------------------------------------------------------------------

    def calculate_buy_intent_score(
        self,
        contracts: List[ContractData],
        company_data: CompanyData,
        contact_data: ContactData,
        participation_count: int,
        win_count: int,
        months: int = 12,
        buy_signals: Optional[List[str]] = None,
    ) -> BuyIntentScore:
        """
        Calculate 6-factor buy-intent score (0-10).

        This is the primary scoring model, replacing the legacy
        DependencyScore + QualificationScore combination.

        Factors and weights:
            operational_intensity  25%
            recent_growth          20%
            portfolio_complexity   15%
            bottleneck_signal      20%
            public_dependency      10%
            contact_quality        10%

        Args:
            contracts: Contracts won by the company.
            company_data: Receita Federal company data.
            contact_data: Contact information.
            participation_count: Total bid participations in the time window.
            win_count: Total wins (should equal ``len(contracts)`` when
                all wins are provided, but may differ if only a sample is
                available).
            months: Analysis time window in months (default 12).
            buy_signals: Optional list of external signals detected.

        Returns:
            BuyIntentScore with all 6 factors and weighted overall.
        """
        oi = self._score_operational_intensity(participation_count, months)
        rg = self._score_recent_growth(contracts, months)
        pc = self._score_portfolio_complexity(contracts)
        bs = self._score_bottleneck_signal(participation_count, win_count)
        pd = self._score_public_dependency(contracts, company_data)
        cq = self._score_buy_intent_contact_quality(contact_data)

        overall = (
            oi * 0.25
            + rg * 0.20
            + pc * 0.15
            + bs * 0.20
            + pd * 0.10
            + cq * 0.10
        )

        return BuyIntentScore(
            operational_intensity=oi,
            recent_growth=rg,
            portfolio_complexity=pc,
            bottleneck_signal=bs,
            public_dependency=pd,
            contact_quality=cq,
            overall_score=round(overall, 2),
            buy_signals=buy_signals or [],
        )

    def calculate_growth_metrics(
        self,
        contracts: List[ContractData],
        participation_count: int,
        months: int = 12,
    ) -> GrowthMetrics:
        """
        Compute growth metrics from contract history.

        Args:
            contracts: List of contracts in the analysis window.
            participation_count: Total bid participations (wins + losses).
            months: Analysis time window in months.

        Returns:
            GrowthMetrics with computed fields.
        """
        win_count = len(contracts)
        win_rate = win_count / participation_count if participation_count > 0 else 0.0

        total_value = sum(c.contract_value for c in contracts)
        avg_value = total_value / win_count if win_count > 0 else Decimal("0")

        # Unique organs and segments (approximate from contract objects)
        unique_organs = len({c.municipality for c in contracts})
        unique_segments = len({c.uf for c in contracts})

        # Quarter-over-quarter growth
        quarter_growth = self._calculate_quarter_growth(contracts)

        return GrowthMetrics(
            participation_count=participation_count,
            win_count=win_count,
            win_rate=round(win_rate, 4),
            avg_contract_value=avg_value,
            quarter_growth_pct=round(quarter_growth, 2),
            unique_organs=unique_organs,
            unique_segments=unique_segments,
        )

    # ------------------------------------------------------------------
    # Private helpers — buy-intent factor calculators
    # ------------------------------------------------------------------

    @staticmethod
    def _score_operational_intensity(
        participation_count: int, months: int  # noqa: ARG004
    ) -> float:
        """
        Score operational intensity (0-10).

        0 participations   -> 0
        1-3 participations -> 3
        4-8 participations -> 5
        9-15 participations -> 7
        16+ participations -> 10
        """
        if participation_count <= 0:
            return 0.0
        elif participation_count <= 3:
            return 3.0
        elif participation_count <= 8:
            return 5.0
        elif participation_count <= 15:
            return 7.0
        else:
            return 10.0

    def _score_recent_growth(
        self, contracts: List[ContractData], months: int  # noqa: ARG002
    ) -> float:
        """
        Score recent growth (0-10).

        Compares last quarter contract value vs previous quarter.
        >=50% growth -> 10
        >=20% growth -> 8
        >=10% growth -> 6
        0-10% growth -> 3
        negative     -> 1
        No data      -> 0
        """
        growth = self._calculate_quarter_growth(contracts)
        if growth is None:
            return 0.0
        elif growth >= 50:
            return 10.0
        elif growth >= 20:
            return 8.0
        elif growth >= 10:
            return 6.0
        elif growth >= 0:
            return 3.0
        else:
            return 1.0

    @staticmethod
    def _score_portfolio_complexity(contracts: List[ContractData]) -> float:
        """
        Score portfolio complexity (0-10).

        Counts unique contracting organs (approximated by municipality)
        and unique segments (approximated by UF).

        1 organ      -> 2
        2-3 organs   -> 5
        4-6 organs   -> 7
        7+ organs    -> 10
        """
        if not contracts:
            return 0.0

        unique_organs = len({c.municipality for c in contracts})

        if unique_organs <= 1:
            return 2.0
        elif unique_organs <= 3:
            return 5.0
        elif unique_organs <= 6:
            return 7.0
        else:
            return 10.0

    @staticmethod
    def _score_bottleneck_signal(
        participation_count: int, win_count: int
    ) -> float:
        """
        Score bottleneck signal (0-10).

        Low win rate = high score (company needs help).
        win_rate < 15%  -> 10 (huge bottleneck)
        15-30%          -> 8
        30-50%          -> 5
        > 50%           -> 2
        No participations -> 0
        """
        if participation_count <= 0:
            return 0.0

        win_rate = win_count / participation_count

        if win_rate < 0.15:
            return 10.0
        elif win_rate < 0.30:
            return 8.0
        elif win_rate < 0.50:
            return 5.0
        else:
            return 2.0

    def _score_public_dependency(
        self,
        contracts: List[ContractData],
        company_data: CompanyData,
    ) -> float:
        """
        Score public dependency (0-10) using a linear scale.

        0% dependency  -> 0
        100% dependency -> 10
        Linear interpolation between.
        """
        total_value = sum(c.contract_value for c in contracts)
        estimated_revenue = REVENUE_ESTIMATES.get(
            company_data.porte, REVENUE_ESTIMATES["N/A"]
        )

        if estimated_revenue <= 0:
            return 0.0

        dependency_pct = float((total_value / estimated_revenue) * 100)
        # Clamp to [0, 100] then scale to [0, 10]
        clamped = max(0.0, min(dependency_pct, 100.0))
        return round(clamped / 10.0, 2)

    @staticmethod
    def _score_buy_intent_contact_quality(contact_data: ContactData) -> float:
        """
        Score contact quality for buy-intent model (0-10).

        email + phone  -> 10
        email only     -> 7
        phone only     -> 5
        neither        -> 0

        WhatsApp is not required (relaxed from legacy scorer).
        """
        has_email = bool(contact_data.email)
        has_phone = bool(contact_data.phone)

        if has_email and has_phone:
            return 10.0
        elif has_email:
            return 7.0
        elif has_phone:
            return 5.0
        else:
            return 0.0

    @staticmethod
    def _calculate_quarter_growth(
        contracts: List[ContractData],
    ) -> Optional[float]:
        """
        Calculate quarter-over-quarter growth in total contract value.

        Compares the most recent 90-day period against the preceding 90
        days. Returns percentage growth (e.g. 25.0 means +25%), or None
        if there is insufficient data.
        """
        if not contracts:
            return None

        today = date.today()
        q_recent_start = today - timedelta(days=90)
        q_prev_start = today - timedelta(days=180)

        recent_value = sum(
            c.contract_value
            for c in contracts
            if c.contract_date >= q_recent_start
        )
        prev_value = sum(
            c.contract_value
            for c in contracts
            if q_prev_start <= c.contract_date < q_recent_start
        )

        if prev_value <= 0:
            # No previous-quarter data — can't compute growth
            return 0.0 if recent_value <= 0 else 100.0

        growth = float((recent_value - prev_value) / prev_value * 100)
        return growth
