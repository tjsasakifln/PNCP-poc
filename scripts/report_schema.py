"""
Pydantic v2 schema for B2G Report JSON.

Defines typed contracts between pipeline phases:
  Phase 1 (Collection) -> ReportDataCollected
  Phase 2-5 (Analyst)  -> EditalEnriched fields
  Phase 7 (Auditor)    -> DeliveryValidation
  Phase 6 (Render)     -> ReportDataFinal (full)

Usage:
    from report_schema import ReportDataCollected, ReportDataFinal, validate_phase1, validate_post_enrichment

    # Validate Phase 1 output
    errors = validate_phase1(json_data)

    # Validate post-enrichment (pre-Auditor)
    errors = validate_post_enrichment(json_data)
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Shared / auxiliary models
# ---------------------------------------------------------------------------


class SourceTag(BaseModel):
    """Provenance tag attached to data sections indicating how data was obtained."""

    model_config = ConfigDict(extra="allow")

    status: str
    timestamp: str
    detail: str | None = None


class EmpresaProfile(BaseModel):
    """Company profile assembled during Phase 1 from OpenCNPJ + PNCP + Portal Transparencia.

    Note: JSON keys ``_source`` and ``_sector_divergence`` are mapped to
    ``source_tag`` and ``sector_divergence`` respectively to comply with
    Pydantic v2's prohibition on leading-underscore field names.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    cnpj: str
    razao_social: str
    nome_fantasia: str | None = None
    cnae_principal: str
    cnaes_secundarios: str | None = None
    porte: str | None = None
    capital_social: float | None = None
    cidade_sede: str | None = None
    uf_sede: str | None = None
    situacao_cadastral: str | None = None
    email: str | None = None
    telefones: list[str] = Field(default_factory=list)
    qsa: list[dict[str, Any]] = Field(default_factory=list)
    sancoes: dict[str, Any] = Field(default_factory=dict)
    historico_contratos: list[dict[str, Any]] = Field(default_factory=list)
    mei: bool | None = False
    simples_nacional: bool | None = False
    source_tag: SourceTag | None = Field(default=None, alias="_source")
    sector_divergence: dict[str, Any] | None = Field(
        default=None, alias="_sector_divergence"
    )


class RiskScore(BaseModel):
    """Multi-factor risk score (0-100) computed per edital."""

    model_config = ConfigDict(extra="allow")

    total: float
    habilitacao: float
    financeiro: float
    geografico: float
    prazo: float
    competitivo: float
    vetoed: bool = False
    veto_reasons: list[str] = Field(default_factory=list)
    fiscal_risk: dict[str, Any] | None = None


class WinProbability(BaseModel):
    """Estimated probability of winning the bid."""

    model_config = ConfigDict(extra="allow")

    probability: float
    prob_min: float | None = None
    prob_max: float | None = None
    factors: dict[str, Any] | None = None


class PriceBenchmark(BaseModel):
    """Historical price benchmark from similar contracts."""

    model_config = ConfigDict(extra="allow")

    min: float | None = None
    median: float | None = None
    max: float | None = None
    vs_estimado: str | None = None  # ABAIXO / DENTRO / ACIMA
    sample_size: int = 0


class AlertaCritico(BaseModel):
    """Critical alert raised during risk assessment."""

    model_config = ConfigDict(extra="allow")

    tipo: str
    severidade: str  # CRITICO, ALTO, MEDIO
    mensagem: str | None = None
    descricao: str | None = None
    acao_requerida: str | None = None
    prazo_sugerido: str | None = None


# ---------------------------------------------------------------------------
# Edital models (Phase 1 base + Analyst enrichment)
# ---------------------------------------------------------------------------


class EditalBase(BaseModel):
    """Phase 1 output -- raw collected fields per edital with computed scores.

    Fields like ``competitive_intel`` and ``cronograma`` use ``Any`` because
    the pipeline emits them as either ``dict`` or ``list[dict]`` depending on
    the data source and enrichment phase.
    """

    model_config = ConfigDict(extra="allow")

    objeto: str
    orgao: str
    uf: str
    municipio: str | None = None
    valor_estimado: float | None = None
    modalidade: str
    data_abertura: str | None = None
    data_encerramento: str | None = None
    dias_restantes: int | None = None
    fonte: str
    link: str | None = None

    # Computed scores (may be absent if pipeline step was skipped)
    risk_score: RiskScore | None = None
    win_probability: WinProbability | None = None
    roi_potential: dict[str, Any] | None = None
    price_benchmark: PriceBenchmark | None = None

    # Alerts and qualifications
    alertas_criticos: list[AlertaCritico] = Field(default_factory=list)
    acervo_status: str | None = None  # CONFIRMADO / PARCIAL / NAO_VERIFICADO
    acervo_detalhes: dict[str, Any] | None = None
    habilitacao_analysis: dict[str, Any] | None = None
    competitive_intel: list[dict[str, Any]] | dict[str, Any] | None = None

    # Geography and timeline
    distancia: dict[str, Any] | None = None
    cronograma: list[dict[str, Any]] | dict[str, Any] | None = None

    # Sensitivity and scenario analysis
    sensitivity: dict[str, Any] | None = None
    scenarios: dict[str, Any] | None = None


class EditalEnriched(EditalBase):
    """Extends EditalBase with Analyst enrichment fields (Phases 2-5)."""

    recomendacao: str | None = None  # PARTICIPAR / AVALIAR COM CAUTELA / NAO RECOMENDADO
    justificativa: str | None = None
    analise_documental: str | dict[str, Any] | None = None
    analise_detalhada: str | None = None
    analise_resumo: str | None = None
    red_flags_documentais: list[str] | None = None
    condicionantes: list[str] | None = None
    alternativa_participacao: str | None = None


# ---------------------------------------------------------------------------
# Auditor / delivery gate models (Phase 7)
# ---------------------------------------------------------------------------


class AuditorCheck(BaseModel):
    """Single check performed by the Auditor gate."""

    model_config = ConfigDict(extra="allow")

    edital_id: str
    check: str  # C1..C16
    status: str  # PASS / FAIL
    motivo: str | None = None


class DeliveryValidation(BaseModel):
    """Phase 7 adversarial audit gate output."""

    model_config = ConfigDict(extra="allow")

    gate_deterministic: str | None = None
    gate_adversarial: str  # PASSED / REVISED / BLOCKED
    checks_total: int = 0
    checks_failed: int = 0
    checks_detail: list[AuditorCheck] = Field(default_factory=list)
    rebaixamentos: list[dict[str, Any]] = Field(default_factory=list)
    block_reasons: list[str] = Field(default_factory=list)
    revisions_made: list[str] = Field(default_factory=list)
    reader_persona: str | None = None


# ---------------------------------------------------------------------------
# Report-level metadata
# ---------------------------------------------------------------------------


class ReportMetadata(BaseModel):
    """Metadata about report generation: timestamps, source statuses, coverage."""

    model_config = ConfigDict(extra="allow")

    generated_at: str
    generator: str
    sources: dict[str, SourceTag] = Field(default_factory=dict)
    coverage: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Top-level report models
# ---------------------------------------------------------------------------


class ReportDataCollected(BaseModel):
    """Phase 1 output -- everything collected before Analyst enrichment.

    Note: JSON keys starting with ``_`` are mapped to underscore-free names:
      - ``_metadata`` -> ``metadata``
      - ``_keywords_source`` -> ``keywords_source``
    Use ``populate_by_name=True`` so both the alias and the Python name work.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    metadata: ReportMetadata | None = Field(default=None, alias="_metadata")
    empresa: EmpresaProfile
    setor: str
    keywords: list[str] = Field(default_factory=list)
    editais: list[EditalBase] = Field(default_factory=list)
    activity_clusters: list[dict[str, Any]] = Field(default_factory=list)
    keywords_source: str | None = Field(default=None, alias="_keywords_source")
    querido_diario: list[dict[str, Any]] = Field(default_factory=list)
    sicaf: dict[str, Any] = Field(default_factory=dict)


class ReportDataFinal(BaseModel):
    """Full enriched report -- all phases complete, ready for PDF render.

    Inherits the same alias mapping as ReportDataCollected plus additional
    Analyst, Auditor, and portfolio fields.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    metadata: ReportMetadata | None = Field(default=None, alias="_metadata")
    empresa: EmpresaProfile
    setor: str
    keywords: list[str] = Field(default_factory=list)
    editais: list[EditalEnriched] = Field(default_factory=list)
    activity_clusters: list[dict[str, Any]] = Field(default_factory=list)
    keywords_source: str | None = Field(default=None, alias="_keywords_source")
    querido_diario: list[dict[str, Any]] = Field(default_factory=list)
    sicaf: dict[str, Any] = Field(default_factory=dict)

    # Analyst enrichment (report-level)
    resumo_executivo: dict[str, Any] | None = None
    inteligencia_mercado: dict[str, Any] | None = None
    proximos_passos: list[dict[str, Any]] | None = None

    # Auditor gate
    delivery_validation: DeliveryValidation | None = None

    # Portfolio optimization and maturity
    portfolio: dict[str, Any] | None = None
    maturity_profile: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def validate_phase1(data: dict[str, Any]) -> list[str]:
    """Validate Phase 1 JSON against ReportDataCollected schema.

    Returns list of error strings (empty = valid).
    """
    errors: list[str] = []
    try:
        ReportDataCollected.model_validate(data)
    except Exception as exc:
        for err in _extract_pydantic_errors(exc):
            errors.append(err)
    return errors


def validate_post_enrichment(data: dict[str, Any]) -> list[str]:
    """Validate post-enrichment JSON -- checks Analyst required fields.

    Returns list of error strings (empty = valid).

    Checks performed:
      - Pydantic schema validation (ReportDataFinal)
      - Every edital has recomendacao
      - Every edital with recomendacao has justificativa
      - PARTICIPAR/AVALIAR editais have analise_documental
      - resumo_executivo exists
      - Recommendation counts are internally consistent
    """
    errors: list[str] = []

    # 1. Schema-level validation
    try:
        ReportDataFinal.model_validate(data)
    except Exception as exc:
        for err in _extract_pydantic_errors(exc):
            errors.append(err)

    editais = data.get("editais", [])

    # 2. Every edital must have recomendacao
    no_rec = [
        i for i, e in enumerate(editais, 1) if not e.get("recomendacao")
    ]
    if no_rec:
        errors.append(
            f"{len(no_rec)} editais sem recomendacao: "
            f"#{', #'.join(str(x) for x in no_rec[:10])}"
        )

    # 3. Every edital with recomendacao must have justificativa
    no_just = [
        i
        for i, e in enumerate(editais, 1)
        if e.get("recomendacao") and not e.get("justificativa")
    ]
    if no_just:
        errors.append(
            f"{len(no_just)} editais com recomendacao mas sem justificativa: "
            f"#{', #'.join(str(x) for x in no_just[:10])}"
        )

    # 4. PARTICIPAR / AVALIAR COM CAUTELA editais should have analise_documental
    participar_avaliar = [
        e
        for e in editais
        if (e.get("recomendacao") or "").upper()
        in ("PARTICIPAR", "AVALIAR COM CAUTELA")
    ]
    no_doc = [
        i
        for i, e in enumerate(editais, 1)
        if (e.get("recomendacao") or "").upper()
        in ("PARTICIPAR", "AVALIAR COM CAUTELA")
        and not e.get("analise_documental")
    ]
    if no_doc and participar_avaliar:
        pct = len(no_doc) / len(participar_avaliar) * 100
        if pct > 50:
            errors.append(
                f"{len(no_doc)}/{len(participar_avaliar)} editais PARTICIPAR/AVALIAR "
                f"sem analise_documental ({pct:.0f}%)"
            )

    # 5. resumo_executivo must exist
    if not data.get("resumo_executivo"):
        errors.append("resumo_executivo ausente no relatorio final")

    # 6. Recommendation count consistency
    rec_counts: dict[str, int] = {}
    for e in editais:
        rec = (e.get("recomendacao") or "SEM_RECOMENDACAO").upper()
        rec_counts[rec] = rec_counts.get(rec, 0) + 1

    total_with_rec = sum(
        v for k, v in rec_counts.items() if k != "SEM_RECOMENDACAO"
    )
    total_editais = len(editais)
    if total_editais > 0 and total_with_rec < total_editais:
        missing = total_editais - total_with_rec
        errors.append(
            f"Recommendation coverage incomplete: {missing}/{total_editais} "
            f"editais without recomendacao"
        )

    return errors


def _extract_pydantic_errors(exc: Exception) -> list[str]:
    """Extract human-readable error strings from a Pydantic ValidationError."""
    errors: list[str] = []
    if hasattr(exc, "errors"):
        for err in exc.errors():  # type: ignore[union-attr]
            loc = " -> ".join(str(part) for part in err.get("loc", []))
            msg = err.get("msg", str(err))
            errors.append(f"[{loc}] {msg}")
    else:
        errors.append(str(exc))
    return errors
