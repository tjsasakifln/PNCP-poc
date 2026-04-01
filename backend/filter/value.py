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
    """Filter bids by estimated value range (None = no limit). Bids with None/0 value pass through."""
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
    """Paginate results. Returns (page_items, metadata_dict)."""
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
