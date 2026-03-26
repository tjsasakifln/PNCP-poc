"""Query the PNCP data lake (pncp_raw_bids) instead of hitting the live API.

When DATALAKE_QUERY_ENABLED=true, the search pipeline calls query_datalake()
instead of PNCPClient. The returned records are in the SAME flat dict format
produced by PNCPClient._normalize_item(), so filter.py / llm.py / excel.py
work without any changes.

Full-text search uses PostgreSQL tsquery via the search_datalake RPC function.
Falls back to an empty list (fail-open) if Supabase is unreachable.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def query_datalake(
    *,
    ufs: list[str],
    data_inicial: str,
    data_final: str,
    modalidades: list[int] | None = None,
    keywords: list[str] | None = None,
    custom_terms: list[str] | None = None,
    valor_min: float | None = None,
    valor_max: float | None = None,
    esferas: list[str] | None = None,
    modo_busca: str = "publicacao",
    limit: int = 2000,
) -> list[dict]:
    """Query pncp_raw_bids via the search_datalake Supabase RPC.

    Returns records in the SAME flat dict format as PNCPClient._normalize_item()
    so downstream filter.py / llm.py / excel.py work unchanged.

    Args:
        ufs: List of UF codes, e.g. ["SC", "PR"]. Required.
        data_inicial: Start date, "YYYY-MM-DD".
        data_final: End date, "YYYY-MM-DD".
        modalidades: Modality codes to include (None = all).
        keywords: Sector keywords (OR-joined in tsquery).
        custom_terms: User-supplied terms (AND-joined on top of keywords).
        valor_min: Minimum estimated value (None = no lower bound).
        valor_max: Maximum estimated value (None = no upper bound).
        esferas: Esfera codes to include (None = all).
        modo_busca: "publicacao" or "abertura".
        limit: Max rows returned by the RPC.

    Returns:
        List of flat bid dicts compatible with _normalize_item() output.
        Returns [] on any error (fail-open).
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()
    except Exception as e:
        logger.warning(f"[DatalakeQuery] Supabase unavailable: {e}")
        return []

    tsquery = _build_tsquery(keywords, custom_terms)

    rpc_params: dict[str, Any] = {
        "p_ufs": ufs,
        "p_date_start": data_inicial,
        "p_date_end": data_final,
        "p_tsquery": tsquery,
        "p_modalidades": modalidades,
        "p_valor_min": valor_min,
        "p_valor_max": valor_max,
        "p_esferas": esferas,
        "p_modo": modo_busca,
        "p_limit": limit,
    }

    logger.info(
        f"[DatalakeQuery] ufs={ufs}, dates={data_inicial}/{data_final}, "
        f"tsquery={tsquery!r}, limit={limit}"
    )

    try:
        result = sb.rpc("search_datalake", rpc_params).execute()
    except Exception as e:
        logger.error(f"[DatalakeQuery] RPC failed: {type(e).__name__}: {e}")
        return []

    rows = result.data or []
    normalized = [_row_to_normalized(row) for row in rows]

    logger.info(f"[DatalakeQuery] Returned {len(normalized)} records from local DB")
    return normalized


# ---------------------------------------------------------------------------
# tsquery construction
# ---------------------------------------------------------------------------


def _build_tsquery(
    keywords: list[str] | None,
    custom_terms: list[str] | None,
) -> str | None:
    """Build a PostgreSQL tsquery string from sector keywords and custom terms.

    Strategy:
    - Keywords are OR-joined (any keyword can match).
    - Custom terms are AND-joined on top of the keyword block.
    - Multi-word keywords are wrapped in a phrase query (<->).
    - Returns None when both inputs are empty/None (search_datalake RPC
      should treat None as "no full-text filter — return all rows").

    Examples:
        keywords=["construção", "obras"], custom_terms=None
          -> "construção | obras"

        keywords=["pavimentação"], custom_terms=["asfalto"]
          -> "(pavimentação) & asfalto"

        keywords=None, custom_terms=["creche", "escola"]
          -> "creche & escola"
    """
    parts: list[str] = []

    if keywords:
        cleaned = [_clean_token(k) for k in keywords if k and k.strip()]
        if cleaned:
            keyword_tokens = [_keyword_to_tstoken(k) for k in cleaned]
            parts.append(" | ".join(keyword_tokens))

    if custom_terms:
        cleaned = [_clean_token(t) for t in custom_terms if t and t.strip()]
        if cleaned:
            custom_tokens = [_keyword_to_tstoken(t) for t in cleaned]
            parts.extend(custom_tokens)

    if not parts:
        return None

    if len(parts) == 1:
        return parts[0]

    # keyword block AND each custom term
    keyword_block = parts[0]
    extra_terms = parts[1:]
    combined = f"({keyword_block})" + "".join(f" & {t}" for t in extra_terms)
    return combined


def _clean_token(token: str) -> str:
    """Strip whitespace and remove characters that break tsquery syntax."""
    token = token.strip()
    # Remove characters not valid in tsquery lexemes (keep letters, digits, hyphens)
    token = re.sub(r"[^\w\s\-]", "", token, flags=re.UNICODE)
    return token.strip()


def _keyword_to_tstoken(keyword: str) -> str:
    """Convert a keyword to a tsquery token.

    Single word -> plain lexeme.
    Multi-word  -> phrase query using <-> operator (e.g. "pré moldado" -> "pré<->moldado").
    """
    words = keyword.split()
    if len(words) == 1:
        return words[0]
    return "<->".join(words)


# ---------------------------------------------------------------------------
# Row → normalized dict
# ---------------------------------------------------------------------------


def _row_to_normalized(row: dict) -> dict:
    """Map a search_datalake RPC row to the flat dict produced by _normalize_item().

    The search_datalake RPC returns columns directly from pncp_raw_bids (no
    raw_data JSONB — the table doesn't store it to stay within Supabase FREE
    tier limits).

    RPC column              | Flat key
    ----------------------- | ---------------------------
    pncp_id                 | numeroControlePNCP + codigoCompra
    uf                      | uf
    municipio               | municipio
    orgao_razao_social      | nomeOrgao
    orgao_cnpj              | orgaoCnpj
    objeto_compra           | objetoCompra
    valor_total_estimado    | valorTotalEstimado
    modalidade_id           | codigoModalidadeContratacao
    modalidade_nome         | modalidadeNome
    situacao_compra         | situacaoCompraId
    data_publicacao         | dataPublicacaoFormatted
    data_abertura           | dataAberturaProposta
    data_encerramento       | dataEncerramentoProposta
    link_pncp               | linkSistemaOrigem
    esfera_id               | esferaId
    """
    result: dict = {}

    pncp_id = row.get("pncp_id") or ""
    if pncp_id:
        result["numeroControlePNCP"] = pncp_id
        result["codigoCompra"] = pncp_id

    uf = row.get("uf") or ""
    if uf:
        result["uf"] = uf

    municipio = row.get("municipio") or ""
    if municipio:
        result["municipio"] = municipio

    orgao = row.get("orgao_razao_social") or ""
    if orgao:
        result["nomeOrgao"] = orgao

    orgao_cnpj = row.get("orgao_cnpj") or ""
    if orgao_cnpj:
        result["orgaoCnpj"] = orgao_cnpj

    objeto_compra = row.get("objeto_compra") or ""
    if objeto_compra:
        result["objetoCompra"] = objeto_compra

    valor = row.get("valor_total_estimado")
    if valor is not None:
        try:
            result["valorTotalEstimado"] = float(valor)
        except (TypeError, ValueError):
            pass

    modalidade_id = row.get("modalidade_id")
    if modalidade_id is not None:
        result["codigoModalidadeContratacao"] = int(modalidade_id)

    modalidade_nome = row.get("modalidade_nome") or ""
    if modalidade_nome:
        result["modalidadeNome"] = modalidade_nome

    situacao = row.get("situacao_compra") or ""
    if situacao:
        result["situacaoCompraId"] = situacao

    data_publicacao = row.get("data_publicacao")
    if data_publicacao:
        result["dataPublicacaoFormatted"] = str(data_publicacao)

    data_abertura = row.get("data_abertura")
    if data_abertura:
        result["dataAberturaProposta"] = str(data_abertura)

    data_encerramento = row.get("data_encerramento")
    if data_encerramento:
        result["dataEncerramentoProposta"] = str(data_encerramento)

    link = row.get("link_pncp") or ""
    if link:
        result["linkSistemaOrigem"] = link

    esfera_id = row.get("esfera_id")
    if esfera_id is not None:
        result["esferaId"] = esfera_id

    # Tag as datalake source for observability (does not affect downstream logic)
    result["_source"] = "datalake"

    return result
