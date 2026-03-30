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
    """
    Filtra licitações por status do processo licitatório.

    IMPORTANTE: Esta função usa INFERÊNCIA DE STATUS baseada em múltiplos campos
    (datas, valores, situação textual) porque a API PNCP não retorna um campo
    de status padronizado. Ver status_inference.py para detalhes da lógica.

    Args:
        licitacoes: Lista de licitações da API PNCP (deve ter `_status_inferido`)
        status: Status desejado:
            - "recebendo_proposta": Licitações abertas para envio de propostas
            - "em_julgamento": Propostas encerradas, em análise
            - "encerrada": Processo finalizado
            - "todos": Sem filtro (retorna todas)

    Returns:
        Lista filtrada de licitações

    Examples:
        >>> from status_inference import enriquecer_com_status_inferido
        >>> bids = [
        ...     {"dataEncerramentoProposta": "2026-12-31T10:00:00"},
        ...     {"valorTotalHomologado": 100000},
        ... ]
        >>> enriquecer_com_status_inferido(bids)  # Adiciona _status_inferido
        >>> filtrar_por_status(bids, "recebendo_proposta")
        [{'dataEncerramentoProposta': '2026-12-31T10:00:00', '_status_inferido': 'recebendo_proposta'}]
    """
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
    """
    Filtra licitações por modalidade de contratação.

    Códigos de modalidade conforme PNCP:
        1 - Pregão Eletrônico
        2 - Pregão Presencial
        3 - Concorrência
        4 - Tomada de Preços
        5 - Convite
        6 - Dispensa de Licitação
        7 - Inexigibilidade
        8 - Credenciamento
        9 - Leilão
        10 - Diálogo Competitivo

    Args:
        licitacoes: Lista de licitações
        modalidades: Lista de códigos de modalidade (None = todas)

    Returns:
        Lista filtrada de licitações

    Examples:
        >>> bids = [
        ...     {"modalidadeId": 1, "objeto": "Pregão"},
        ...     {"modalidadeId": 6, "objeto": "Dispensa"},
        ... ]
        >>> filtrar_por_modalidade(bids, [1, 2])
        [{'modalidadeId': 1, 'objeto': 'Pregão'}]
    """
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
    """
    Filtra licitações por esfera governamental.

    Args:
        licitacoes: Lista de licitações
        esferas: Lista de códigos de esfera:
            - "F" = Federal (União, autarquias federais, empresas públicas federais)
            - "E" = Estadual (Estados, DF, autarquias estaduais)
            - "M" = Municipal (Prefeituras, câmaras, autarquias municipais)

    Returns:
        Lista filtrada de licitações

    Examples:
        >>> bids = [
        ...     {"esferaId": "F", "orgao": "Ministério da Saúde"},
        ...     {"esferaId": "M", "orgao": "Prefeitura de SP"},
        ... ]
        >>> filtrar_por_esfera(bids, ["M"])
        [{'esferaId': 'M', 'orgao': 'Prefeitura de SP'}]
    """
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
    """
    STORY-240 AC3: Filter out bids whose proposal deadline has already passed.

    Rejects bids where dataEncerramentoProposta <= now().
    Bids without a deadline date are KEPT (conservative approach).

    Args:
        licitacoes: List of raw PNCP bid dictionaries

    Returns:
        Tuple of (approved bids list, count of rejected bids)
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
