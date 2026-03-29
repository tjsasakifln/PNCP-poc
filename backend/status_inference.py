"""
Status inference layer for procurement bids (PNCP + PCP v2).

PROBLEMA: APIs de licitação não retornam status consistente. PNCP usa
`situacaoCompraNome` com valores variados; PCP v2 usa `statusProcessoPublico`
com nomenclatura completamente diferente.

SOLUÇÃO: Inferir o status real analisando múltiplos campos (datas, valores,
situação textual), com mapeamento específico por fonte de dados.

CRIT-054: Added PCP v2 status mapping. PCP v2 "Encerrado" means "session ended"
(= em_julgamento), NOT "process finalized" (= encerrada). Without this mapping,
91% of PCP v2 records were incorrectly rejected by the status filter.
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# CRIT-054 AC1: PCP v2 status mapping
# PCP v2 `statusProcessoPublico.descricao` values mapped to internal status.
# These are mapped via `to_legacy_format()` into `situacaoCompraNome`.
#
# Key difference from PNCP: PCP "Encerrado"/"Sessão Encerrada" means the
# bidding session ended (proposals closed), NOT the process is finalized.
# In PNCP, "Encerrada" means fully finalized (homologated/cancelled).
PCP_V2_STATUS_MAP = {
    # recebendo_proposta: actively accepting bids
    "aberto": "recebendo_proposta",
    "sessão pública iniciada": "recebendo_proposta",
    "sessao publica iniciada": "recebendo_proposta",
    "recebendo propostas": "recebendo_proposta",
    "em disputa": "recebendo_proposta",
    "em lances": "recebendo_proposta",
    "período de propostas": "recebendo_proposta",
    "periodo de propostas": "recebendo_proposta",
    # em_julgamento: session closed, under analysis
    "encerrado": "em_julgamento",
    "sessão encerrada": "em_julgamento",
    "sessao encerrada": "em_julgamento",
    "em análise": "em_julgamento",
    "em analise": "em_julgamento",
    "em julgamento": "em_julgamento",
    "classificação": "em_julgamento",
    "classificacao": "em_julgamento",
    "habilitação": "em_julgamento",
    "habilitacao": "em_julgamento",
    "negociação": "em_julgamento",
    "negociacao": "em_julgamento",
    # encerrada: process fully finalized
    "homologado": "encerrada",
    "adjudicado": "encerrada",
    "anulado": "encerrada",
    "revogado": "encerrada",
    "fracassado": "encerrada",
    "deserto": "encerrada",
    "cancelado": "encerrada",
    "suspenso": "encerrada",
}


def _inferir_status_pcp_v2(licitacao: dict) -> str:
    """CRIT-054 AC1/AC2/AC3: Infer status for PCP v2 records.

    PCP v2 uses different status nomenclature from PNCP. Key difference:
    PCP "Encerrado" = session ended (em_julgamento), NOT process finalized.

    Priority:
    1. Mapped status from PCP_V2_STATUS_MAP
    2. Date-based heuristics (dataEncerramentoProposta)
    3. Unknown → "desconhecido" (pass-through, not rejected)
    """
    situacao_nome = (
        licitacao.get("situacaoCompraNome", "")
        or licitacao.get("situacao", "")
        or ""
    ).strip().lower()

    # AC1: Try direct mapping
    mapped = PCP_V2_STATUS_MAP.get(situacao_nome)
    if mapped:
        logger.debug(f"PCP v2 status mapped: '{situacao_nome}' → {mapped}")
        return mapped

    # AC3: Date-based heuristics
    data_encerramento_str = licitacao.get("dataEncerramentoProposta")
    if data_encerramento_str:
        try:
            data_enc = datetime.fromisoformat(
                data_encerramento_str.replace("Z", "+00:00")
            )
            agora = datetime.now(data_enc.tzinfo)
            if agora < data_enc:
                logger.debug(
                    f"PCP v2 status inferred from date: recebendo_proposta "
                    f"(deadline {data_enc.date()} is future)"
                )
                return "recebendo_proposta"
            else:
                logger.debug(
                    f"PCP v2 status inferred from date: em_julgamento "
                    f"(deadline {data_enc.date()} has passed)"
                )
                return "em_julgamento"
        except (ValueError, AttributeError):
            pass

    # AC2: Unknown status — pass-through (fail-open for PCP v2)
    # AC6: Metric for unmapped status
    try:
        from metrics import PCP_STATUS_UNMAPPED_TOTAL
        PCP_STATUS_UNMAPPED_TOTAL.inc()
    except Exception:
        pass
    logger.warning(
        f"PCP v2 status unmapped: '{situacao_nome}' — treating as unknown (pass-through)"
    )
    return "desconhecido"


def inferir_status_licitacao(licitacao: dict) -> str:
    """
    Infere o status real de uma licitação baseado em múltiplos campos.

    CRIT-054: Dispatches to source-specific inference when `_source` field
    is present. PCP v2 records use different status nomenclature from PNCP.

    Args:
        licitacao: Dicionário com dados da licitação (PNCP ou PCP v2)

    Returns:
        Status inferido: "encerrada", "em_julgamento", "recebendo_proposta",
        "desconhecido" (PCP v2 only), ou "todos"
    """
    # CRIT-054: Dispatch to PCP v2-specific inference
    source = licitacao.get("_source", "")
    if source == "PORTAL_COMPRAS":
        return _inferir_status_pcp_v2(licitacao)

    # === Original PNCP inference below ===

    # 1. Extrair campos relevantes
    situacao_nome = (
        licitacao.get("situacaoCompraNome", "")
        or licitacao.get("situacao", "")
        or licitacao.get("statusCompra", "")
        or ""
    ).lower()

    valor_homologado = licitacao.get("valorTotalHomologado")
    data_encerramento_str = licitacao.get("dataEncerramentoProposta")

    # 2. REGRA #1: ENCERRADA (prioridade máxima)
    # Licitação homologada (tem valor final definido) — adjudicação é definitiva
    if valor_homologado is not None and valor_homologado > 0:
        logger.debug(f"Status inferido: encerrada (valor homologado: R$ {valor_homologado})")
        return "encerrada"

    # REGRA #0 (GOLDEN RULE): Data de encerramento é a verdade absoluta.
    # Se dataEncerramentoProposta > agora → está recebendo propostas, ponto final.
    # Nenhuma heurística textual (situacaoCompraNome, etc.) pode contradizer a data.
    # Exceção: homologação (acima) já retornou "encerrada" se aplicável.
    if data_encerramento_str:
        try:
            _data_enc = datetime.fromisoformat(
                data_encerramento_str.replace("Z", "+00:00")
            )
            _agora = datetime.now(_data_enc.tzinfo)
            if _agora < _data_enc:
                logger.debug(
                    f"Status inferido: recebendo_proposta "
                    f"(GOLDEN RULE: prazo {_data_enc.date()} é futuro)"
                )
                return "recebendo_proposta"
        except (ValueError, AttributeError):
            pass

    # IMPORTANTE: Verificar "propostas encerradas" ANTES de "encerrada"
    # "Propostas encerradas" significa julgamento, não finalização
    if "propostas encerradas" in situacao_nome or "proposta encerrada" in situacao_nome:
        logger.debug(f"Status inferido: em_julgamento (situação: '{situacao_nome}')")
        return "em_julgamento"

    # Situação textual indica finalização (só termos definitivos)
    situacoes_finalizadas = [
        "homologada", "adjudicada", "concluída", "concluida",
        "anulada", "revogada", "cancelada", "fracassada",
        "deserta", "suspensa"
    ]
    # "encerrada" sozinha (não "propostas encerradas")
    if any(termo in situacao_nome for termo in situacoes_finalizadas):
        logger.debug(f"Status inferido: encerrada (situação: '{situacao_nome}')")
        return "encerrada"

    # "Encerrada" sozinha (após verificar "propostas encerradas")
    if situacao_nome == "encerrada" or situacao_nome.endswith("encerrada"):
        logger.debug(f"Status inferido: encerrada (situação: '{situacao_nome}')")
        return "encerrada"

    # 3. REGRA #2: Parse de datas (abertura e encerramento)
    data_abertura: Optional[datetime] = None
    data_encerramento: Optional[datetime] = None

    data_abertura_str = licitacao.get("dataAberturaProposta")
    if data_abertura_str:
        try:
            data_abertura = datetime.fromisoformat(
                data_abertura_str.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            logger.warning(f"Data de abertura inválida: '{data_abertura_str}'")

    if data_encerramento_str:
        try:
            # API PNCP retorna ISO 8601: "2026-02-19T08:00:00"
            data_encerramento = datetime.fromisoformat(
                data_encerramento_str.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            logger.warning(
                f"Data de encerramento inválida: '{data_encerramento_str}'"
            )

    # 4. REGRA #3: Validação por intervalo de datas (MAIS PRECISA)
    if data_abertura and data_encerramento:
        agora = datetime.now(data_abertura.tzinfo or data_encerramento.tzinfo)

        # Licitação ainda não abriu (aguardando início)
        if agora < data_abertura:
            logger.debug(
                f"Status inferido: recebendo_proposta "
                f"(aguardando abertura: {data_abertura.date()})"
            )
            return "recebendo_proposta"  # Ou criar status "aguardando_abertura"

        # Licitação ABERTA (data_abertura <= agora < data_encerramento)
        if data_abertura <= agora < data_encerramento:
            logger.debug(
                f"Status inferido: recebendo_proposta "
                f"(aberta: {data_abertura.date()} - {data_encerramento.date()})"
            )
            return "recebendo_proposta"

        # Licitação FECHADA (prazo encerrado)
        if agora >= data_encerramento:
            logger.debug(
                f"Status inferido: em_julgamento "
                f"(prazo encerrado: {data_encerramento.date()})"
            )
            return "em_julgamento"

    # 5. REGRA #4: Fallback - só data de encerramento disponível
    elif data_encerramento:
        agora = datetime.now(data_encerramento.tzinfo)

        if data_encerramento < agora:
            # Prazo já passou
            logger.debug(
                f"Status inferido: em_julgamento "
                f"(prazo encerrado: {data_encerramento.date()})"
            )
            return "em_julgamento"
        else:
            # Prazo futuro - mas verificar se publicação é muito antiga
            # Licitações publicadas há mais de 90 dias com prazo ainda aberto
            # são provavelmente dados inconsistentes da API PNCP
            data_publicacao_str = licitacao.get("dataPublicacaoPncp") or licitacao.get("dataPublicacao")
            if data_publicacao_str:
                try:
                    data_pub = datetime.fromisoformat(
                        data_publicacao_str.replace("Z", "+00:00")
                    )
                    agora_pub = datetime.now(data_pub.tzinfo) if data_pub.tzinfo else agora
                    dias_desde_publicacao = (agora_pub - data_pub).days
                    if dias_desde_publicacao > 90:
                        logger.debug(
                            f"Status inferido: em_julgamento "
                            f"(publicação antiga: {dias_desde_publicacao} dias, "
                            f"prazo futuro suspeito: {data_encerramento.date()})"
                        )
                        return "em_julgamento"
                except (ValueError, AttributeError):
                    pass

            logger.debug(
                f"Status inferido: recebendo_proposta "
                f"(prazo futuro: {data_encerramento.date()})"
            )
            return "recebendo_proposta"

    # 6. REGRA #5: Situação textual indica julgamento
    situacoes_julgamento = [
        "julgamento", "em julgamento", "análise", "analise",
        "classificação", "classificacao", "habilitação", "habilitacao"
        # Nota: "propostas encerradas" já foi verificado na REGRA #1
    ]
    if any(termo in situacao_nome for termo in situacoes_julgamento):
        logger.debug(f"Status inferido: em_julgamento (situação: '{situacao_nome}')")
        return "em_julgamento"

    # 7. REGRA #6: RECEBENDO_PROPOSTA (situação textual)

    # Situação textual indica abertura
    # IMPORTANTE: "divulgada" e "publicada" foram REMOVIDOS desta lista (2026-02-09).
    # "Divulgada no PNCP" significa apenas que foi publicada no portal, NÃO que
    # está aceitando propostas. Classificar essas como "recebendo_proposta" causava
    # licitações fechadas serem exibidas como abertas, destruindo a credibilidade.
    situacoes_abertas = [
        "recebendo", "aberta",
        "vigente", "ativa", "em andamento"
    ]
    if any(termo in situacao_nome for termo in situacoes_abertas):
        logger.debug(f"Status inferido: recebendo_proposta (situação: '{situacao_nome}')")
        return "recebendo_proposta"

    # 8. HEURÍSTICA DE DATA: Publicações antigas sem status explícito
    # Bids publicados há mais de 30 dias quase certamente estão encerrados.
    # Bids publicados há 5 dias ou menos provavelmente ainda estão abertos.
    # Esse heurístico resolve o caso em que PNCP retorna bids sem status
    # (ex: "Divulgada no PNCP") para filtros "encerrada" / "em_julgamento".
    data_pub_str = licitacao.get("dataPublicacaoPncp") or licitacao.get("dataPublicacao")
    if data_pub_str:
        try:
            data_pub = datetime.fromisoformat(data_pub_str.replace("Z", "+00:00"))
            agora_pub = datetime.now(data_pub.tzinfo) if data_pub.tzinfo else datetime.now()
            dias_desde_pub = (agora_pub - data_pub).days
            if dias_desde_pub > 30:
                logger.debug(
                    f"Status inferido: encerrada "
                    f"(data-based heuristic: publicado há {dias_desde_pub} dias)"
                )
                return "encerrada"
            elif dias_desde_pub <= 5:
                logger.debug(
                    f"Status inferido: recebendo_proposta "
                    f"(data-based heuristic: publicado há {dias_desde_pub} dias)"
                )
                return "recebendo_proposta"
        except (ValueError, AttributeError, TypeError):
            pass

    # 9. FALLBACK: Não foi possível determinar com certeza
    # Retorna "todos" para não filtrar essa licitação fora
    # NOTA: Apenas bids sem datas de publicação chegam aqui
    logger.debug(
        f"Status inferido: todos (fallback - dados insuficientes). "
        f"Situação: '{situacao_nome}', Abertura: '{data_abertura_str}', "
        f"Encerramento: '{data_encerramento_str}'"
    )
    return "todos"


def enriquecer_com_status_inferido(licitacoes: list[dict]) -> list[dict]:
    """
    Adiciona campo `_status_inferido` a cada licitação.

    Este campo pode ser usado para filtrar licitações por status
    mesmo quando a API PNCP não fornece essa informação de forma
    consistente.

    IMPORTANTE: Esta função MODIFICA o dicionário original adicionando
    a chave `_status_inferido`. Use antes de aplicar filtros.

    Args:
        licitacoes: Lista de dicionários de licitações da API PNCP

    Returns:
        A mesma lista (modificada in-place) com campo `_status_inferido` adicionado

    Examples:
        >>> bids = [{"dataEncerramentoProposta": "2026-12-31T10:00:00"}]
        >>> enriquecer_com_status_inferido(bids)
        >>> bids[0]["_status_inferido"]
        'recebendo_proposta'
    """
    for lic in licitacoes:
        lic["_status_inferido"] = inferir_status_licitacao(lic)

    logger.info(f"Enriquecidas {len(licitacoes)} licitações com status inferido")
    return licitacoes
