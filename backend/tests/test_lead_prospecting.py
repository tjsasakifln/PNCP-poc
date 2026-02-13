"""
STORY-224 Track 5: Lead Prospecting Tests (AC28-AC30)

Tests for lead scoring and deduplication modules.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import List

from lead_scorer import LeadScorer
from lead_deduplicator import LeadDeduplicator
from schemas_lead_prospecting import (
    ContractData,
    CompanyData,
    ContactData,
    DependencyScore,
    QualificationScore,
    LeadProfile,
    LeadHistory,
    LeadHistoryFile,
    StrategicIntelligence,
)


# ============================================================================
# Test Data Factories
# ============================================================================


def create_contract(
    cnpj: str = "12345678000190",
    company_name: str = "Test Company",
    value: Decimal = Decimal("100000.00"),
    days_ago: int = 0,
    contract_object: str = "Fornecimento de uniformes",
    uf: str = "SP",
    municipality: str = "São Paulo",
    contract_id: str = "CONT-001",
) -> ContractData:
    """Factory for creating test ContractData."""
    return ContractData(
        cnpj=cnpj,
        company_name=company_name,
        contract_value=value,
        contract_date=date.today() - timedelta(days=days_ago),
        contract_object=contract_object,
        uf=uf,
        municipality=municipality,
        contract_id=contract_id,
    )


def create_company(
    cnpj: str = "12345678000190",
    razao_social: str = "Test Company LTDA",
    porte: str = "ME",
    capital_social: Decimal = Decimal("50000.00"),
    email: str = "contato@test.com",
    telefone: str = "(11) 1234-5678",
) -> CompanyData:
    """Factory for creating test CompanyData."""
    return CompanyData(
        cnpj=cnpj,
        razao_social=razao_social,
        nome_fantasia="Test Company",
        situacao="ATIVA",
        porte=porte,
        capital_social=capital_social,
        cnae_principal="Comércio varejista",
        cnae_codigo="4711-3/01",
        data_abertura=date(2020, 1, 1),
        municipio="São Paulo",
        uf="SP",
        email=email,
        telefone=telefone,
    )


def create_contact(
    email: str | None = "contato@test.com",
    phone: str | None = "(11) 1234-5678",
    whatsapp: str | None = None,
    website: str | None = None,
    source: str = "receita_federal",
) -> ContactData:
    """Factory for creating test ContactData."""
    return ContactData(
        email=email,
        phone=phone,
        whatsapp=whatsapp,
        website=website,
        source=source,
    )


def create_lead_profile(
    cnpj: str = "12345678000190",
    company_name: str = "Test Company",
    overall_score: float = 7.5,
) -> LeadProfile:
    """Factory for creating test LeadProfile (required by add_leads_to_history)."""
    company = create_company(cnpj=cnpj)
    contracts = [create_contract(cnpj=cnpj, value=Decimal("100000.00"))]
    contact = create_contact()
    dep_score = DependencyScore(
        total_contract_value=Decimal("100000.00"),
        estimated_annual_revenue=Decimal("360000.00"),
        dependency_percentage=27.78,
        dependency_level="LOW",
        contract_count=1,
    )
    qualification = QualificationScore(
        dependency_score=4.0,
        activity_score=10.0,
        sector_match_score=10.0,
        contact_quality_score=7.0,
        overall_score=overall_score,
    )
    intelligence = StrategicIntelligence(
        summary="Test lead for unit testing.",
    )
    return LeadProfile(
        cnpj=cnpj,
        company_name=company_name,
        company_data=company,
        contracts=contracts,
        dependency_score=dep_score,
        contact_data=contact,
        intelligence=intelligence,
        personalized_message="Test message",
        qualification=qualification,
        sectors=["UNIFORMES"],
    )


# ============================================================================
# TestLeadScorerDependency
# ============================================================================


class TestLeadScorerDependency:
    """Test dependency score calculation."""

    def test_high_dependency_mei_company(self):
        """MEI with large contracts should result in HIGH dependency."""
        scorer = LeadScorer()

        # MEI estimated revenue: 81k
        # Contract value: 70k
        # Dependency: (70k / 81k) * 100 = 86.4% -> HIGH
        company = create_company(porte="MEI")
        contracts = [
            create_contract(value=Decimal("70000.00")),
        ]

        result = scorer.calculate_dependency_score(contracts, company, time_window_months=12)

        assert result.dependency_level == "HIGH"
        assert result.dependency_percentage >= 70.0
        assert result.total_contract_value == Decimal("70000.00")
        assert result.estimated_annual_revenue == Decimal("81000.00")

    def test_low_dependency_large_company(self):
        """GRANDE company with small contracts should result in LOW dependency."""
        scorer = LeadScorer()

        # GRANDE estimated revenue: 500M
        # Contract value: 100k
        # Dependency: (100k / 500M) * 100 = 0.02% -> LOW
        company = create_company(porte="GRANDE")
        contracts = [
            create_contract(value=Decimal("100000.00")),
        ]

        result = scorer.calculate_dependency_score(contracts, company, time_window_months=12)

        assert result.dependency_level == "LOW"
        assert result.dependency_percentage < 40.0
        assert result.total_contract_value == Decimal("100000.00")
        assert result.estimated_annual_revenue == Decimal("500000000.00")

    def test_medium_dependency(self):
        """EPP with moderate contracts should result in MEDIUM dependency."""
        scorer = LeadScorer()

        # EPP estimated revenue: 4.8M
        # Contract value: 2.5M
        # Dependency: (2.5M / 4.8M) * 100 = 52.08% -> MEDIUM
        company = create_company(porte="EPP")
        contracts = [
            create_contract(value=Decimal("2500000.00")),
        ]

        result = scorer.calculate_dependency_score(contracts, company, time_window_months=12)

        assert result.dependency_level == "MEDIUM"
        assert 40.0 <= result.dependency_percentage < 70.0
        assert result.total_contract_value == Decimal("2500000.00")
        assert result.estimated_annual_revenue == Decimal("4800000.00")

    def test_zero_contracts(self):
        """Empty contract list should result in 0% dependency."""
        scorer = LeadScorer()

        company = create_company(porte="ME")
        contracts: List[ContractData] = []

        result = scorer.calculate_dependency_score(contracts, company, time_window_months=12)

        assert result.dependency_level == "LOW"
        assert result.dependency_percentage == 0.0
        assert result.total_contract_value == Decimal("0.00")
        assert result.contract_count == 0

    def test_unknown_porte_uses_default(self):
        """Unknown porte should use N/A default of 1M."""
        scorer = LeadScorer()

        # Unknown porte -> 1M default revenue
        # Contract value: 600k
        # Dependency: (600k / 1M) * 100 = 60% -> MEDIUM
        company = create_company(porte="UNKNOWN_PORTE")
        contracts = [
            create_contract(value=Decimal("600000.00")),
        ]

        result = scorer.calculate_dependency_score(contracts, company, time_window_months=12)

        # Should use N/A default (1M)
        assert result.estimated_annual_revenue == Decimal("1000000.00")
        assert result.dependency_level == "MEDIUM"
        assert 40.0 <= result.dependency_percentage < 70.0


# ============================================================================
# TestLeadScorerActivity
# ============================================================================


class TestLeadScorerActivity:
    """Test activity score calculation."""

    def test_recent_contract_30_days(self):
        """Contract within last 30 days should score 10."""
        scorer = LeadScorer()

        contracts = [
            create_contract(days_ago=15),  # 15 days ago
        ]

        score = scorer._score_activity(contracts)
        assert score == 10

    def test_contract_90_days(self):
        """Contract within 31-90 days should score 7."""
        scorer = LeadScorer()

        contracts = [
            create_contract(days_ago=60),  # 60 days ago
        ]

        score = scorer._score_activity(contracts)
        assert score == 7

    def test_contract_180_days(self):
        """Contract within 91-180 days should score 4."""
        scorer = LeadScorer()

        contracts = [
            create_contract(days_ago=120),  # 120 days ago
        ]

        score = scorer._score_activity(contracts)
        assert score == 4

    def test_old_contract_over_180_days(self):
        """Contract over 180 days should score 0."""
        scorer = LeadScorer()

        contracts = [
            create_contract(days_ago=200),  # 200 days ago
        ]

        score = scorer._score_activity(contracts)
        assert score == 0

    def test_no_contracts(self):
        """No contracts should score 0."""
        scorer = LeadScorer()

        contracts: List[ContractData] = []

        score = scorer._score_activity(contracts)
        assert score == 0


# ============================================================================
# TestLeadScorerSectorMatch
# ============================================================================


class TestLeadScorerSectorMatch:
    """Test sector match score calculation."""

    def test_exact_match(self):
        """Exact sector match should score 10."""
        scorer = LeadScorer()

        company_sectors = ["UNIFORMES", "FACILITIES_MANAGEMENT"]
        target_sectors = ["UNIFORMES", "MEDICAL"]

        score = scorer._score_sector_match(company_sectors, target_sectors)
        assert score == 10.0

    def test_no_match_different_sectors(self):
        """Non-overlapping sectors score 6.0 (related match via RELATED_SECTORS map)."""
        scorer = LeadScorer()

        company_sectors = ["CONSTRUCTION", "ENGINEERING"]
        target_sectors = ["UNIFORMES", "MEDICAL"]

        score = scorer._score_sector_match(company_sectors, target_sectors)
        # No exact match; result depends on RELATED_SECTORS map
        assert score in [2.0, 6.0]

    def test_empty_sectors_score_2(self):
        """Empty company_sectors or target_sectors should score 2."""
        scorer = LeadScorer()

        assert scorer._score_sector_match([], ["UNIFORMES"]) == 2.0
        assert scorer._score_sector_match(["UNIFORMES"], []) == 2.0
        assert scorer._score_sector_match([], []) == 2.0


# ============================================================================
# TestLeadScorerContactQuality
# ============================================================================


class TestLeadScorerContactQuality:
    """Test contact quality score calculation."""

    def test_full_contact(self):
        """Email + phone + whatsapp should score 10."""
        scorer = LeadScorer()

        contact = create_contact(
            email="contato@test.com",
            phone="(11) 1234-5678",
            whatsapp="11987654321",
        )

        score = scorer._score_contact_quality(contact)
        assert score == 10

    def test_email_and_phone(self):
        """Email + phone (no whatsapp) should score 7."""
        scorer = LeadScorer()

        contact = create_contact(
            email="contato@test.com",
            phone="(11) 1234-5678",
            whatsapp=None,
        )

        score = scorer._score_contact_quality(contact)
        assert score == 7

    def test_email_only(self):
        """Email only should score 4."""
        scorer = LeadScorer()

        contact = create_contact(
            email="contato@test.com",
            phone=None,
            whatsapp=None,
        )

        score = scorer._score_contact_quality(contact)
        assert score == 4

    def test_no_email(self):
        """No email should score 0."""
        scorer = LeadScorer()

        contact = create_contact(
            email=None,
            phone="(11) 1234-5678",
            whatsapp="11987654321",
        )

        score = scorer._score_contact_quality(contact)
        assert score == 0


# ============================================================================
# TestLeadScorerQualification
# ============================================================================


class TestLeadScorerQualification:
    """Test overall qualification score calculation."""

    def test_overall_score_calculation(self):
        """Verify weighted formula: dependency 40%, activity 20%, sector 20%, contact 20%."""
        scorer = LeadScorer()

        # Setup for high-quality lead
        company = create_company(porte="ME")  # 360k revenue
        contracts = [
            create_contract(value=Decimal("250000.00"), days_ago=15),  # Recent, high value
        ]

        # Dependency: (250k / 360k) * 100 = 69.4% -> MEDIUM (score ~7)
        dependency_score = scorer.calculate_dependency_score(contracts, company)

        company_sectors = ["UNIFORMES"]
        target_sectors = ["UNIFORMES", "MEDICAL"]

        contact = create_contact(
            email="contato@test.com",
            phone="(11) 1234-5678",
            whatsapp="11987654321",
        )

        result = scorer.calculate_qualification_score(
            dependency_score,
            contracts,
            company_sectors,
            target_sectors,
            contact,
        )

        # overall_score is 0-10 weighted average
        assert 0 <= result.overall_score <= 10

        # Verify individual component scores are present
        assert result.dependency_score >= 0
        assert result.activity_score >= 0
        assert result.sector_match_score >= 0
        assert result.contact_quality_score >= 0

        # Verify weighted calculation approximately
        # dependency_weight=40%, activity=20%, sector=20%, contact=20%
        expected = (
            result.dependency_score * 0.4 +
            result.activity_score * 0.2 +
            result.sector_match_score * 0.2 +
            result.contact_quality_score * 0.2
        )
        assert abs(result.overall_score - expected) < 0.01


# ============================================================================
# TestLeadDeduplicator
# ============================================================================


class TestLeadDeduplicator:
    """Test lead deduplication functionality."""

    def test_empty_history(self, tmp_path: Path):
        """Non-existent history file should return empty history."""
        history_file = tmp_path / "leads_history.json"
        deduplicator = LeadDeduplicator(history_file=str(history_file))

        history = deduplicator.load_history()

        assert history.total_leads == 0
        assert history.leads == []
        assert deduplicator.get_existing_cnpjs() == set()

    def test_filter_new_cnpjs(self, tmp_path: Path):
        """Filter should exclude existing CNPJs and return only new ones."""
        history_file = tmp_path / "leads_history.json"
        deduplicator = LeadDeduplicator(history_file=str(history_file))

        # Add existing leads (add_leads_to_history takes List[LeadProfile])
        existing_leads = [
            create_lead_profile(cnpj="12345678000190", company_name="Existing 1"),
            create_lead_profile(cnpj="98765432000100", company_name="Existing 2"),
        ]
        deduplicator.add_leads_to_history(existing_leads)

        # Try to filter mix of new and existing CNPJs
        candidate_cnpjs = [
            "12345678000190",  # Existing
            "11111111000111",  # New
            "98765432000100",  # Existing
            "22222222000122",  # New
        ]

        new_cnpjs = deduplicator.filter_new_cnpjs(candidate_cnpjs)

        assert len(new_cnpjs) == 2
        assert "11111111000111" in new_cnpjs
        assert "22222222000122" in new_cnpjs
        assert "12345678000190" not in new_cnpjs
        assert "98765432000100" not in new_cnpjs

    def test_add_leads_to_history(self, tmp_path: Path):
        """Adding leads should increase total count and persist to file."""
        history_file = tmp_path / "leads_history.json"
        deduplicator = LeadDeduplicator(history_file=str(history_file))

        new_leads = [
            create_lead_profile(cnpj="12345678000190", company_name="New Lead 1"),
            create_lead_profile(cnpj="98765432000100", company_name="New Lead 2"),
        ]

        total = deduplicator.add_leads_to_history(new_leads)

        assert total == 2

        # Verify persistence
        deduplicator2 = LeadDeduplicator(history_file=str(history_file))
        history = deduplicator2.load_history()
        assert history.total_leads == 2
        assert len(history.leads) == 2

    def test_update_lead_status(self, tmp_path: Path):
        """Updating lead status should modify existing lead."""
        history_file = tmp_path / "leads_history.json"
        deduplicator = LeadDeduplicator(history_file=str(history_file))

        lead = create_lead_profile(cnpj="12345678000190", company_name="Test Lead")
        deduplicator.add_leads_to_history([lead])

        # Update status
        deduplicator.update_lead_status(
            cnpj="12345678000190",
            contact_made=True,
            converted=False,
            notes="Made initial contact via email",
        )

        # Verify update
        history = deduplicator.load_history()
        updated_lead = next(l for l in history.leads if l.cnpj == "12345678000190")

        assert updated_lead.contact_made is True
        assert updated_lead.converted is False
        assert updated_lead.notes == "Made initial contact via email"

    def test_save_and_load_roundtrip(self, tmp_path: Path):
        """Save and load should preserve all data."""
        history_file = tmp_path / "leads_history.json"
        deduplicator = LeadDeduplicator(history_file=str(history_file))

        leads = [
            create_lead_profile(cnpj="12345678000190", company_name="Company A"),
            create_lead_profile(cnpj="98765432000100", company_name="Company B"),
        ]

        deduplicator.add_leads_to_history(leads)

        # Update first lead
        deduplicator.update_lead_status(
            cnpj="12345678000190",
            contact_made=True,
            notes="Initial contact made",
        )

        # Load in new instance
        deduplicator2 = LeadDeduplicator(history_file=str(history_file))
        history = deduplicator2.load_history()

        assert history.total_leads == 2
        assert len(history.leads) == 2

        # Verify first lead
        lead1 = next(l for l in history.leads if l.cnpj == "12345678000190")
        assert lead1.company_name == "Company A"
        assert lead1.contact_made is True
        assert lead1.converted is False
        assert lead1.notes == "Initial contact made"

        # Verify second lead
        lead2 = next(l for l in history.leads if l.cnpj == "98765432000100")
        assert lead2.company_name == "Company B"
        assert lead2.contact_made is False
        assert lead2.converted is False
        assert lead2.notes == ""  # Default is empty string, not None
