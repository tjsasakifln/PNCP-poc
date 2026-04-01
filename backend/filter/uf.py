"""DEBT-110 AC4: UF, geo, and batch filtering.

Extracted from filter.py. Contains single-bid filtering (filter_licitacao),
batch processing (filter_batch), and geographic filters (orgao, municipio).
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from filter.keywords import (
    KEYWORDS_EXCLUSAO,
    KEYWORDS_UNIFORMES,
    match_keywords,
    normalize_text,
)

logger = logging.getLogger(__name__)


def filter_licitacao(
    licitacao: dict,
    ufs_selecionadas: Set[str],
    keywords: Set[str] | None = None,
    exclusions: Set[str] | None = None,
    context_required: Dict[str, Set[str]] | None = None,
    filter_closed: bool = False,
) -> Tuple[bool, Optional[str]]:
    """Apply UF + keyword + optional deadline filters to a single bid.

    Returns (passed: bool, rejection_reason: str | None).
    """
    # 1. UF Filter (fastest check)
    uf = licitacao.get("uf", "")
    if uf not in ufs_selecionadas:
        return False, f"UF '{uf}' não selecionada"

    # VALUE RANGE FILTER REMOVED (2026-02-05)
    # Previously filtered by valor_min/valor_max (R$ 10k - R$ 10M)
    # Now returns ALL results regardless of value to maximize opportunities

    # 2. Keyword Filter (most expensive - regex matching)
    kw = keywords if keywords else set()
    exc = exclusions if exclusions else set()
    objeto = licitacao.get("objetoCompra", "")
    if not kw:
        match, keywords_found = True, []  # RC1-FIX: no keywords = accept
    else:
        match, keywords_found = match_keywords(objeto, kw, exc, context_required)

    if not match:
        return False, "Não contém keywords do setor"

    # 4. Deadline Filter - OPTIONAL
    # When filter_closed=True, reject bids whose proposal submission deadline
    # (dataEncerramentoProposta) has already passed. This is used when the user
    # explicitly filters by status="recebendo_proposta" to ensure only truly
    # open bids are returned.
    #
    # Note: dataAberturaProposta is the OPENING date for proposals, NOT the
    # deadline. The correct deadline field from the PNCP API is
    # dataEncerramentoProposta.
    #
    # Referencia: Investigacao 2026-01-28 - docs/investigations/
    if filter_closed:
        data_fim_str = licitacao.get("dataEncerramentoProposta")
        if data_fim_str:
            try:
                data_fim = datetime.fromisoformat(
                    data_fim_str.replace("Z", "+00:00")
                )
                agora = datetime.now(data_fim.tzinfo)
                if data_fim < agora:
                    return False, "Prazo de submissao encerrado"
            except (ValueError, AttributeError):
                # If date parsing fails, don't reject (conservative approach)
                logger.warning(
                    f"Data de encerramento invalida: '{data_fim_str}'"
                )

    return True, None


def filter_batch(
    licitacoes: List[dict],
    ufs_selecionadas: Set[str],
    keywords: Set[str] | None = None,
    exclusions: Set[str] | None = None,
    context_required: Dict[str, Set[str]] | None = None,
) -> Tuple[List[dict], Dict[str, int]]:
    """Filter a batch of bids and return (approved_list, stats_dict)."""
    aprovadas: List[dict] = []
    stats: Dict[str, int] = {
        "total": len(licitacoes),
        "aprovadas": 0,
        "rejeitadas_uf": 0,
        "rejeitadas_keyword": 0,
        "rejeitadas_prazo": 0,
        "rejeitadas_outros": 0,
    }

    for lic in licitacoes:
        aprovada, motivo = filter_licitacao(
            lic, ufs_selecionadas, keywords, exclusions, context_required
        )

        if aprovada:
            aprovadas.append(lic)
            stats["aprovadas"] += 1
        else:
            # Categorize rejection reason for statistics
            motivo_lower = (motivo or "").lower()
            if "uf" in motivo_lower and "não selecionada" in motivo_lower:
                stats["rejeitadas_uf"] += 1
            elif "keyword" in motivo_lower:
                stats["rejeitadas_keyword"] += 1
            elif "prazo" in motivo_lower:
                stats["rejeitadas_prazo"] += 1
            else:
                stats["rejeitadas_outros"] += 1

    return aprovadas, stats


def filtrar_por_orgao(
    licitacoes: List[dict],
    orgaos: List[str] | None
) -> List[dict]:
    """Filter bids by organ name (partial, normalized match). None = all."""
    if not orgaos:
        logger.debug("filtrar_por_orgao: orgaos=None, retornando todas")
        return licitacoes

    # Normaliza os termos de busca
    orgaos_norm = [normalize_text(o) for o in orgaos if o]

    if not orgaos_norm:
        return licitacoes

    resultado: List[dict] = []
    for lic in licitacoes:
        # Tenta diferentes campos que podem conter o nome do órgão
        nome_orgao = (
            lic.get("nomeOrgao", "")
            or lic.get("orgao", "")
            or lic.get("nomeUnidade", "")
            or lic.get("entidade", "")
            or ""
        )
        nome_orgao_norm = normalize_text(nome_orgao)

        # Verifica se algum termo de busca está presente (busca parcial)
        for termo in orgaos_norm:
            if termo in nome_orgao_norm:
                resultado.append(lic)
                break  # Evita duplicatas

    logger.debug(
        f"filtrar_por_orgao: {len(licitacoes)} -> {len(resultado)} "
        f"(orgaos={len(orgaos)} termos)"
    )
    return resultado


def filtrar_por_municipio(
    licitacoes: List[dict],
    municipios: List[str] | None
) -> List[dict]:
    """Filter bids by IBGE municipality code. None = all."""
    if not municipios:
        logger.debug("filtrar_por_municipio: municipios=None, retornando todas")
        return licitacoes

    # Normaliza códigos para string
    municipios_str = [str(m).strip() for m in municipios]

    resultado: List[dict] = []
    for lic in licitacoes:
        # A API PNCP pode usar diferentes campos para código do município
        codigo_ibge = (
            lic.get("codigoMunicipioIbge")
            or lic.get("municipioId")
            or lic.get("codigoMunicipio")
            or lic.get("ibge")
            or ""
        )
        codigo_ibge = str(codigo_ibge).strip()

        if codigo_ibge in municipios_str:
            resultado.append(lic)

    logger.debug(
        f"filtrar_por_municipio: {len(licitacoes)} -> {len(resultado)} "
        f"(municipios={len(municipios)} códigos)"
    )
    return resultado
