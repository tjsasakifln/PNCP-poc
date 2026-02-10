"""
Pydantic schemas for lead prospecting workflow (STORY-184).

These schemas define the data models for:
- PNCP contract data
- Receita Federal company data
- Contact information from web search
- Strategic intelligence
- Dependency scoring
- Qualification scoring
- Lead profiles
- Lead history (deduplication)
"""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class ContractData(BaseModel):
    """Single contract from PNCP API."""

    cnpj: str = Field(..., description="CNPJ of winning company (14 digits)")
    company_name: str = Field(..., description="Razão social")
    contract_value: Decimal = Field(..., description="Contract value (R$)")
    contract_date: date = Field(..., description="Signature date")
    contract_object: str = Field(..., description="Contract description")
    uf: str = Field(..., description="State (UF)")
    municipality: str = Field(..., description="Municipality")
    contract_id: str = Field(..., description="Unique PNCP contract ID")

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        """Validate CNPJ format (14 digits)."""
        cleaned = v.replace(".", "").replace("/", "").replace("-", "")
        if not cleaned.isdigit() or len(cleaned) != 14:
            raise ValueError(f"Invalid CNPJ format: {v}")
        return cleaned


class CompanyData(BaseModel):
    """Company data from Receita Federal API."""

    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    situacao: str = Field(..., description="ATIVA, BAIXADA, etc.")
    porte: str = Field(..., description="MEI, ME, EPP, GRANDE")
    capital_social: Decimal
    cnae_principal: str = Field(..., description="Primary CNAE description")
    cnae_codigo: str = Field(..., description="CNAE code")
    data_abertura: date
    municipio: str
    uf: str
    email: Optional[str] = None
    telefone: Optional[str] = None


class ContactData(BaseModel):
    """Contact information from web search."""

    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(
        None, description="Format: +55 XX XXXXX-XXXX or (XX) XXXXX-XXXX"
    )
    whatsapp: Optional[str] = Field(
        None, description="Format: +55 XX XXXXX-XXXX or (XX) XXXXX-XXXX"
    )
    website: Optional[str] = None
    source: str = Field(
        ...,
        description="Where data was found (e.g., 'company website', 'Google Maps')",
    )


class StrategicIntelligence(BaseModel):
    """Strategic intelligence from web search."""

    summary: str = Field(..., description="1-2 paragraph summary")
    recent_news: List[str] = Field(
        default_factory=list, description="Recent news headlines"
    )
    market_positioning: Optional[str] = None
    pain_points: Optional[str] = None


class DependencyScore(BaseModel):
    """Dependency score calculation."""

    total_contract_value: Decimal = Field(
        ..., description="Sum of all contracts (R$)"
    )
    estimated_annual_revenue: Decimal = Field(
        ..., description="Estimated annual revenue (R$)"
    )
    dependency_percentage: float = Field(
        ..., description="(contracts / revenue) * 100"
    )
    dependency_level: str = Field(
        ..., description="HIGH (>=70%), MEDIUM (40-69%), LOW (<40%)"
    )
    contract_count: int = Field(..., description="Number of contracts in period")


class QualificationScore(BaseModel):
    """Multi-factor qualification score."""

    dependency_score: float = Field(..., ge=0, le=10, description="Weighted 40%")
    activity_score: float = Field(..., ge=0, le=10, description="Weighted 20%")
    sector_match_score: float = Field(..., ge=0, le=10, description="Weighted 20%")
    contact_quality_score: float = Field(..., ge=0, le=10, description="Weighted 20%")
    overall_score: float = Field(..., ge=0, le=10, description="Weighted average")


class LeadProfile(BaseModel):
    """Complete lead profile for output."""

    # Identification
    cnpj: str
    company_name: str
    nome_fantasia: Optional[str] = None

    # Company data
    company_data: CompanyData

    # Procurement profile
    contracts: List[ContractData]
    dependency_score: DependencyScore

    # Contact information
    contact_data: ContactData

    # Strategic intelligence
    intelligence: StrategicIntelligence

    # Personalized message
    personalized_message: str

    # Qualification
    qualification: QualificationScore

    # Metadata
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    sectors: List[str] = Field(default_factory=list, description="Matched sectors")


class LeadHistory(BaseModel):
    """Lead history entry (AC10 - Deduplication)."""

    cnpj: str
    company_name: str
    first_discovered: datetime
    last_seen: datetime
    times_discovered: int = 1
    qualification_score: float
    contact_made: bool = False
    converted: bool = False
    notes: str = ""


class LeadHistoryFile(BaseModel):
    """Lead history file structure (cnpj-history.json)."""

    version: str = "1.0"
    last_updated: datetime
    total_leads: int
    leads: List[LeadHistory]
