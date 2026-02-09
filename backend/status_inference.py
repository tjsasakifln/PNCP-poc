"""
Status inference layer for PNCP procurement bids.

PROBLEMA: A API PNCP não retorna um campo de status consistente para filtrar
licitações abertas/em julgamento/encerradas. O campo `situacaoCompraNome`
existe mas tem valores variados e não padronizados.

SOLUÇÃO: Inferir o status real da licitação analisando múltiplos campos:
- Datas (abertura, encerramento, homologação)
- Valores (homologado vs estimado)
- Situação textual (quando disponível)

Isso permite filtrar licitações por status mesmo quando a API não fornece
essa informação de forma estruturada.
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def inferir_status_licitacao(licitacao: dict) -> str:
    """
    Infere o status real de uma licitação baseado em múltiplos campos.

    Lógica de inferência (em ordem de prioridade):

    1. ENCERRADA (processo finalizado):
       - Tem valor homologado (valorTotalHomologado não-null)
       - OU situação indica finalização ("homologada", "adjudicada",
         "anulada", "revogada", "fracassada", "deserta", "suspensa")

    2. EM_JULGAMENTO (propostas fechadas, aguardando resultado):
       - Data de encerramento no passado
       - E ainda não homologada (valorTotalHomologado == null)
       - OU situação indica julgamento ("julgamento", "análise", "classificação")

    3. RECEBENDO_PROPOSTA (ainda aberta):
       - Data de encerramento no futuro
       - OU situação indica abertura ("divulgada", "publicada", "aberta",
         "recebendo", "vigente")

    4. TODOS (fallback quando não há informação suficiente):
       - Quando não é possível determinar o status com certeza

    Args:
        licitacao: Dicionário com dados da licitação da API PNCP

    Returns:
        Status inferido: "encerrada", "em_julgamento", "recebendo_proposta", ou "todos"

    Examples:
        >>> # Licitação aberta (prazo futuro)
        >>> bid = {
        ...     "dataEncerramentoProposta": "2026-12-31T10:00:00",
        ...     "valorTotalHomologado": None
        ... }
        >>> inferir_status_licitacao(bid)
        'recebendo_proposta'

        >>> # Licitação em julgamento (prazo passado, sem homologação)
        >>> bid = {
        ...     "dataEncerramentoProposta": "2025-01-01T10:00:00",
        ...     "valorTotalHomologado": None
        ... }
        >>> inferir_status_licitacao(bid)
        'em_julgamento'

        >>> # Licitação encerrada (homologada)
        >>> bid = {
        ...     "dataEncerramentoProposta": "2025-01-01T10:00:00",
        ...     "valorTotalHomologado": 100000.0
        ... }
        >>> inferir_status_licitacao(bid)
        'encerrada'
    """
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
    # Licitação homologada (tem valor final definido)
    if valor_homologado is not None and valor_homologado > 0:
        logger.debug(f"Status inferido: encerrada (valor homologado: R$ {valor_homologado})")
        return "encerrada"

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

    # 8. FALLBACK: Não foi possível determinar com certeza
    # Retorna "todos" para não filtrar essa licitação fora
    # NOTA: "Divulgada no PNCP" e "Publicada" caem aqui — status indeterminado
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
