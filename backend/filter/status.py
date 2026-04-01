"""DEBT-110 AC4: Status, modalidade, esfera, and deadline filtering.

Extracted from filter.py. Contains list-level filters that operate
on collections of procurement bids.
"""

import logging
from typing import Dict, List, Tuple


# Configure logging
logger = logging.getLogger(__name__)


def filtrar_por_status(
    licitacoes: List[dict],
    status: str = "todos"
) -> List[dict]:
    """Filter bids by inferred status. Uses _status_inferido field if present, else raw API fields."""
    if not status or status == "todos":
        logger.debug("filtrar_por_status: status='todos', retornando todas")
        return licitacoes

    # Importa função de inferência (lazy import para evitar circular dependency)
    from status_inference import inferir_status_licitacao

    resultado: List[dict] = []
    inferencias_realizadas = 0

    for lic in licitacoes:
        # Usa status inferido se já existir (enriquecido previamente)
        # Caso contrário, infere on-the-fly
        if "_status_inferido" in lic:
            status_lic = lic["_status_inferido"]
        else:
            status_lic = inferir_status_licitacao(lic)
            lic["_status_inferido"] = status_lic  # Cache para próximos filtros
            inferencias_realizadas += 1

        # Compara com status solicitado
        if status_lic == status.lower():
            resultado.append(lic)

    if inferencias_realizadas > 0:
        logger.debug(
            f"filtrar_por_status: realizadas {inferencias_realizadas} "
            f"inferências on-the-fly"
        )

    logger.debug(
        f"filtrar_por_status: {len(licitacoes)} -> {len(resultado)} "
        f"(status='{status}')"
    )
    return resultado


def filtrar_por_modalidade(
    licitacoes: List[dict],
    modalidades: List[int] | None
) -> List[dict]:
    """Filter bids by modalidade ID list. None = all."""
    if not modalidades:
        logger.debug("filtrar_por_modalidade: modalidades=None, retornando todas")
        return licitacoes

    resultado: List[dict] = []
    for lic in licitacoes:
        # A API PNCP pode usar diferentes nomes de campo para modalidade
        modalidade_id = (
            lic.get("modalidadeId")
            or lic.get("codigoModalidadeContratacao")
            or lic.get("modalidade_id")
        )

        # Tenta converter para int se for string
        if modalidade_id is not None:
            try:
                modalidade_id = int(modalidade_id)
            except (ValueError, TypeError):
                modalidade_id = None

        if modalidade_id in modalidades:
            resultado.append(lic)

    logger.debug(
        f"filtrar_por_modalidade: {len(licitacoes)} -> {len(resultado)} "
        f"(modalidades={modalidades})"
    )
    return resultado


def filtrar_por_esfera(
    licitacoes: List[dict],
    esferas: List[str] | None
) -> List[dict]:
    """Filter bids by government sphere (F/E/M). None = all. Falls back to organ-name heuristics."""
    if not esferas:
        logger.debug("filtrar_por_esfera: esferas=None, retornando todas")
        return licitacoes

    # Normaliza para uppercase
    esferas_upper = [e.upper() for e in esferas]

    # Mapeamento de fallback baseado no tipo/nome do órgão
    esfera_keywords: Dict[str, List[str]] = {
        "F": [
            "federal", "união", "ministerio", "ministério",
            "autarquia federal", "empresa pública federal",
            "universidade federal", "instituto federal",
            "agência", "agencia", "ibama", "inss", "receita federal",
        ],
        "E": [
            "estadual", "estado", "secretaria de estado",
            "autarquia estadual", "governador", "governo do estado",
            "tribunal de justiça", "detran", "polícia militar",
            "policia militar", "assembleia legislativa",
        ],
        "M": [
            "municipal", "prefeitura", "câmara municipal", "camara municipal",
            "secretaria municipal", "autarquia municipal",
            "prefeito", "vereador", "município", "municipio",
        ],
    }

    resultado: List[dict] = []
    for lic in licitacoes:
        # Primeiro tenta pelo campo esferaId direto
        esfera_id = (
            lic.get("esferaId", "")
            or lic.get("esfera", "")
            or lic.get("tipoEsfera", "")
            or ""
        ).upper()

        if esfera_id in esferas_upper:
            resultado.append(lic)
            continue

        # Fallback: analisa pelo tipo/nome do órgão
        tipo_orgao = (
            lic.get("tipoOrgao", "")
            or lic.get("nomeOrgao", "")
            or lic.get("orgao", "")
            or ""
        ).lower()

        for esfera in esferas_upper:
            keywords = esfera_keywords.get(esfera, [])
            if any(kw in tipo_orgao for kw in keywords):
                resultado.append(lic)
                break

    logger.debug(
        f"filtrar_por_esfera: {len(licitacoes)} -> {len(resultado)} "
        f"(esferas={esferas})"
    )
    return resultado


def filtrar_por_prazo_aberto(
    licitacoes: List[dict],
) -> Tuple[List[dict], int]:
    """Reject bids with past dataEncerramentoProposta. Bids without deadline are kept.

    Returns (approved_list, rejected_count).
    """
    from datetime import datetime, timezone

    aprovadas: List[dict] = []
    rejeitadas = 0

    for lic in licitacoes:
        data_fim_str = lic.get("dataEncerramentoProposta")
        if not data_fim_str:
            # No deadline date → keep (conservative)
            aprovadas.append(lic)
            continue

        try:
            data_fim = datetime.fromisoformat(
                data_fim_str.replace("Z", "+00:00")
            )
            # GTM-FIX-031: Ensure both datetimes are tz-aware to avoid crash
            if data_fim.tzinfo is None:
                data_fim = data_fim.replace(tzinfo=timezone.utc)
            agora = datetime.now(timezone.utc)
            if data_fim <= agora:
                rejeitadas += 1
                logger.debug(
                    f"filtrar_por_prazo_aberto: rejeitada (encerrada em {data_fim_str}): "
                    f"{lic.get('objetoCompra', '')[:80]}"
                )
                continue
        except (ValueError, AttributeError):
            # If date parsing fails, keep (conservative)
            logger.warning(f"filtrar_por_prazo_aberto: data inválida: '{data_fim_str}'")

        aprovadas.append(lic)

    logger.info(
        f"filtrar_por_prazo_aberto: {len(aprovadas)} aprovadas, {rejeitadas} rejeitadas "
        f"(total: {len(licitacoes)})"
    )
    return aprovadas, rejeitadas
