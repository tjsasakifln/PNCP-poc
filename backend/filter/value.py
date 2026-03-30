"""DEBT-110 AC4: Value range filtering and result pagination.

Extracted from filter.py. Contains numeric value filtering
and page-based result slicing.
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def filtrar_por_valor(
    licitacoes: List[dict],
    valor_min: float | None = None,
    valor_max: float | None = None
) -> List[dict]:
    """
    Filtra licitações por faixa de valor estimado.

    Args:
        licitacoes: Lista de licitações
        valor_min: Valor mínimo (None = sem limite inferior)
        valor_max: Valor máximo (None = sem limite superior)

    Returns:
        Lista filtrada de licitações

    Examples:
        >>> bids = [
        ...     {"valorTotalEstimado": 50000},
        ...     {"valorTotalEstimado": 200000},
        ...     {"valorTotalEstimado": 1000000},
        ... ]
        >>> filtrar_por_valor(bids, valor_min=100000, valor_max=500000)
        [{'valorTotalEstimado': 200000}]
    """
    if valor_min is None and valor_max is None:
        logger.debug("filtrar_por_valor: sem limites, retornando todas")
        return licitacoes

    resultado: List[dict] = []
    for lic in licitacoes:
        # Tenta diferentes campos que podem conter o valor
        valor_raw = (
            lic.get("valorTotalEstimado")
            or lic.get("valorEstimado")
            or lic.get("valor")
        )

        # UX-401: Bids with no value data (None/0) pass through value filters
        # instead of being rejected — the value is simply unavailable, not zero
        if valor_raw is None or valor_raw == 0:
            resultado.append(lic)
            continue

        # Converte string para float se necessário (formato brasileiro)
        if isinstance(valor_raw, str):
            try:
                # Remove pontos de milhar e troca vírgula por ponto
                valor_limpo = valor_raw.replace(".", "").replace(",", ".")
                valor = float(valor_limpo)
            except ValueError:
                resultado.append(lic)
                continue
        elif isinstance(valor_raw, (int, float)):
            valor = float(valor_raw)
        else:
            resultado.append(lic)
            continue

        # Aplica filtros de valor
        if valor_min is not None and valor < valor_min:
            continue
        if valor_max is not None and valor > valor_max:
            continue

        resultado.append(lic)

    logger.debug(
        f"filtrar_por_valor: {len(licitacoes)} -> {len(resultado)} "
        f"(min={valor_min}, max={valor_max})"
    )
    return resultado


def paginar_resultados(
    licitacoes: List[dict],
    pagina: int = 1,
    itens_por_pagina: int = 20
) -> Tuple[List[dict], Dict[str, int]]:
    """
    Pagina os resultados de licitações.

    Args:
        licitacoes: Lista completa de licitações
        pagina: Número da página (1-indexed). Padrão: 1.
        itens_por_pagina: Quantidade de itens por página. Padrão: 20.

    Returns:
        Tuple contendo:
        - List[dict]: Licitações da página solicitada
        - Dict[str, int]: Metadados de paginação com:
            - total: Total de itens
            - pagina: Página atual
            - itens_por_pagina: Itens por página
            - total_paginas: Total de páginas
            - inicio: Índice do primeiro item (0-indexed)
            - fim: Índice do último item (exclusivo)

    Examples:
        >>> bids = [{"id": i} for i in range(100)]
        >>> page, meta = paginar_resultados(bids, pagina=2, itens_por_pagina=20)
        >>> len(page)
        20
        >>> meta["total"]
        100
        >>> meta["total_paginas"]
        5
        >>> meta["inicio"]
        20
    """
    total = len(licitacoes)

    if total == 0:
        return [], {
            "total": 0,
            "pagina": 1,
            "itens_por_pagina": itens_por_pagina,
            "total_paginas": 0,
            "inicio": 0,
            "fim": 0,
        }

    # Calcula total de páginas
    total_paginas = (total + itens_por_pagina - 1) // itens_por_pagina

    # Garante que a página está dentro dos limites
    pagina = max(1, min(pagina, total_paginas))

    # Calcula índices de início e fim
    inicio = (pagina - 1) * itens_por_pagina
    fim = min(inicio + itens_por_pagina, total)

    # Extrai a página
    pagina_resultado = licitacoes[inicio:fim]

    metadata = {
        "total": total,
        "pagina": pagina,
        "itens_por_pagina": itens_por_pagina,
        "total_paginas": total_paginas,
        "inicio": inicio,
        "fim": fim,
    }

    logger.debug(
        f"paginar_resultados: página {pagina}/{total_paginas} "
        f"(itens {inicio+1}-{fim} de {total})"
    )

    return pagina_resultado, metadata
