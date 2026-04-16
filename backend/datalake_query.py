"""Query the PNCP data lake (pncp_raw_bids) instead of hitting the live API.

When DATALAKE_QUERY_ENABLED=true, the search pipeline calls query_datalake()
instead of PNCPClient. The returned records are in the SAME flat dict format
produced by PNCPClient._normalize_item(), so filter.py / llm.py / excel.py
work without any changes.

Full-text search uses PostgreSQL tsquery via the search_datalake RPC function.
STORY-437: multi-column FTS (A/B/C weights), websearch_to_tsquery for custom
  terms, trigram fallback when FTS returns 0 results.
STORY-438: hybrid semantic search via pgvector embeddings (opt-in, EMBEDDING_ENABLED).
Falls back to an empty list (fail-open) if Supabase is unreachable.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# S3-FIX: In-memory TTL cache for datalake queries (avoids repeated Supabase
# round-trips and mitigates timeout impact on retries).
# ---------------------------------------------------------------------------

_CACHE_TTL = 3600  # 1 hour
_CACHE_MAX_ENTRIES = 50

# dict[str, tuple[float, list[dict]]]  — key -> (expiry_timestamp, results)
_query_cache: dict[str, tuple[float, list[dict]]] = {}

# STORY-438: In-memory cache for query embeddings (avoids repeated OpenAI calls)
_EMBEDDING_CACHE_TTL = 3600  # 1 hour
_EMBEDDING_CACHE_MAX_ENTRIES = 100
_embedding_cache: dict[str, tuple[float, list[float]]] = {}


def _cache_key(
    ufs: list[str],
    data_inicial: str,
    data_final: str,
    tsquery: str | None,
    websearch_text: str | None,
    modo_busca: str,
) -> str:
    """Deterministic cache key from query parameters.

    For "abertas" mode, the key is date-independent because the RPC
    ignores date params and only filters by data_encerramento > now().
    """
    ufs_sorted = ",".join(sorted(ufs))
    q = f"{tsquery or ''}|{websearch_text or ''}"
    if modo_busca == "abertas":
        return f"{ufs_sorted}|abertas|{q}"
    return f"{ufs_sorted}|{data_inicial}|{data_final}|{q}|{modo_busca}"


def _cache_get(key: str) -> list[dict] | None:
    """Return cached results if key exists and is not expired."""
    entry = _query_cache.get(key)
    if entry is None:
        return None
    expiry, results = entry
    if time.monotonic() > expiry:
        del _query_cache[key]
        return None
    return results


def _cache_put(key: str, results: list[dict]) -> None:
    """Store results in cache, evicting oldest entry if at capacity."""
    if len(_query_cache) >= _CACHE_MAX_ENTRIES:
        # Evict the entry with the earliest expiry
        oldest_key = min(_query_cache, key=lambda k: _query_cache[k][0])
        del _query_cache[oldest_key]
    _query_cache[key] = (time.monotonic() + _CACHE_TTL, results)

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

    STORY-437: Uses websearch_to_tsquery for custom terms, trigram fallback on 0 results.
    STORY-438: Hybrid semantic search when EMBEDDING_ENABLED=true.

    Args:
        ufs: List of UF codes, e.g. ["SC", "PR"]. Required.
        data_inicial: Start date, "YYYY-MM-DD".
        data_final: End date, "YYYY-MM-DD".
        modalidades: Modality codes to include (None = all).
        keywords: Sector keywords (OR-joined tsquery).
        custom_terms: User-supplied terms (websearch_to_tsquery in SQL).
        valor_min: Minimum estimated value (None = no lower bound).
        valor_max: Maximum estimated value (None = no upper bound).
        esferas: Esfera codes to include (None = all).
        modo_busca: "publicacao" or "abertura".
        limit: Max rows returned by the RPC.

    Returns:
        List of flat bid dicts compatible with _normalize_item() output.
        Returns [] on any error (fail-open).
    """
    from config.features import TRIGRAM_FALLBACK_ENABLED, EMBEDDING_ENABLED

    tsquery, websearch_text = _build_tsquery(keywords, custom_terms)

    # S3-FIX: Check in-memory cache before hitting Supabase
    _ck = _cache_key(ufs, data_inicial, data_final, tsquery, websearch_text, modo_busca)
    _cached = _cache_get(_ck)
    if _cached is not None:
        logger.info(
            f"[DatalakeQuery] Cache HIT for {len(ufs)} UFs, "
            f"returning {len(_cached)} cached records"
        )
        return _cached

    try:
        from supabase_client import get_supabase
        sb = get_supabase()
    except Exception as e:
        logger.warning(f"[DatalakeQuery] Supabase unavailable: {e}")
        return []

    # STORY-438: Generate query embedding when enabled
    query_embedding: list[float] | None = None
    if EMBEDDING_ENABLED:
        query_text = _build_embedding_query_text(keywords, custom_terms)
        if query_text:
            query_embedding = await _get_query_embedding(query_text)

    rpc_params: dict[str, Any] = {
        "p_ufs": ufs,
        "p_date_start": data_inicial,
        "p_date_end": data_final,
        "p_tsquery": tsquery,
        "p_websearch_text": websearch_text,
        "p_modalidades": modalidades,
        "p_valor_min": valor_min,
        "p_valor_max": valor_max,
        "p_esferas": esferas,
        "p_modo": modo_busca,
        "p_limit": limit,
    }

    # STORY-438: Include embedding when available
    if query_embedding is not None:
        rpc_params["p_embedding"] = query_embedding

    logger.info(
        f"[DatalakeQuery] ufs={ufs}, dates={data_inicial}/{data_final}, "
        f"tsquery={tsquery!r}, websearch={websearch_text!r}, "
        f"embedding={'yes' if query_embedding else 'no'}, limit={limit}"
    )

    # PostgREST caps results at 1000 rows per call.
    # Paginate per-UF to avoid truncação em queries multi-UF.
    _POSTGREST_ROW_CAP = 1000
    rows: list[dict] = []
    for uf in ufs:
        uf_params = {**rpc_params, "p_ufs": [uf]}
        try:
            result = sb.rpc("search_datalake", uf_params).execute()
            uf_rows = result.data or []
            # Detecta possível truncamento silencioso do PostgREST (limite 1000 linhas/chamada)
            if len(uf_rows) == _POSTGREST_ROW_CAP:
                logger.warning(
                    f"[DatalakeQuery] UF {uf} returned exactly {_POSTGREST_ROW_CAP} rows "
                    f"— possível truncamento silencioso do PostgREST. "
                    f"Considere reduzir o intervalo de datas ou aumentar a granularidade da query."
                )
                try:
                    from metrics import DATALAKE_TRUNCATION_SUSPECTED
                    DATALAKE_TRUNCATION_SUSPECTED.labels(uf=uf).inc()
                except Exception:
                    pass  # Métricas são opcionais — nunca bloqueiam o fluxo principal
            rows.extend(uf_rows)
        except Exception as e:
            logger.warning(f"[DatalakeQuery] RPC failed for UF={uf}: {type(e).__name__}: {e}")

    if not rows:
        # STORY-437 AC3: Trigram fallback when FTS returns 0
        if TRIGRAM_FALLBACK_ENABLED and (tsquery or websearch_text):
            trigram_term = _build_trigram_term(keywords, custom_terms)
            if trigram_term:
                rows = _query_trigram_fallback(sb, trigram_term, ufs, limit)
                if rows:
                    normalized = [_row_to_normalized(row) for row in rows]
                    for r in normalized:
                        r["_source"] = "trigram_fallback"
                    logger.info(
                        '{"event": "trigram_fallback_activated", "query": %r, "results_found": %d}',
                        trigram_term, len(normalized),
                    )
                    _cache_put(_ck, normalized)
                    return normalized

        logger.warning("[DatalakeQuery] All UF queries returned 0 rows")
        return []

    normalized = [_row_to_normalized(row) for row in rows]

    logger.info(f"[DatalakeQuery] Returned {len(normalized)} records from local DB ({len(ufs)} UFs)")

    # S3-FIX: Cache results before returning
    _cache_put(_ck, normalized)

    return normalized


def _query_trigram_fallback(
    sb: Any,
    query_term: str,
    ufs: list[str],
    limit: int,
) -> list[dict]:
    """Call the search_datalake_trigram_fallback RPC. Returns raw rows."""
    try:
        result = sb.rpc(
            "search_datalake_trigram_fallback",
            {"p_query_term": query_term, "p_ufs": ufs, "p_limit": limit},
        ).execute()
        return result.data or []
    except Exception as e:
        logger.warning(f"[DatalakeQuery] Trigram fallback RPC failed: {type(e).__name__}: {e}")
        return []


# ---------------------------------------------------------------------------
# STORY-438: Embedding helpers
# ---------------------------------------------------------------------------


def _build_embedding_query_text(
    keywords: list[str] | None,
    custom_terms: list[str] | None,
) -> str | None:
    """Build plain text for embedding query from keywords + custom terms."""
    parts: list[str] = []
    if keywords:
        parts.extend([k.strip() for k in keywords if k and k.strip()])
    if custom_terms:
        parts.extend([t.strip() for t in custom_terms if t and t.strip()])
    if not parts:
        return None
    return " ".join(parts)


async def _get_query_embedding(query_text: str) -> list[float] | None:
    """Get embedding for query text, using in-memory cache (TTL 1h).

    Returns None on failure (fallback to FTS-only search).
    """
    # Check cache first
    entry = _embedding_cache.get(query_text)
    if entry is not None:
        expiry, vector = entry
        if time.monotonic() < expiry:
            return vector
        else:
            del _embedding_cache[query_text]

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=[query_text],
            dimensions=256,
        )
        vector = response.data[0].embedding

        # Cache the result
        if len(_embedding_cache) >= _EMBEDDING_CACHE_MAX_ENTRIES:
            oldest_key = min(_embedding_cache, key=lambda k: _embedding_cache[k][0])
            del _embedding_cache[oldest_key]
        _embedding_cache[query_text] = (time.monotonic() + _EMBEDDING_CACHE_TTL, vector)

        return vector
    except Exception as e:
        logger.warning(
            f"[DatalakeQuery] Query embedding failed — falling back to FTS only: "
            f"{type(e).__name__}: {e}"
        )
        return None


# ---------------------------------------------------------------------------
# tsquery construction (STORY-437 AC2)
# ---------------------------------------------------------------------------


def _build_tsquery(
    keywords: list[str] | None,
    custom_terms: list[str] | None,
) -> tuple[str | None, str | None]:
    """Build PostgreSQL query components from sector keywords and custom terms.

    Returns a tuple (tsquery_text, websearch_text):
    - tsquery_text: sector keywords OR-joined using raw tsquery syntax
      (passed as p_tsquery to the RPC, handled by to_tsquery in SQL)
    - websearch_text: user custom terms as raw text for websearch_to_tsquery
      in SQL (supports "exact phrase", -exclusion, implicit AND)

    Strategy:
    - Sector keywords -> tsquery_text (OR-joined with |, phrases with <->)
    - Custom terms -> websearch_text (raw text, sent to PostgreSQL's
      websearch_to_tsquery which handles natural language queries)
    - When only keywords:      (tsquery_text, None)
    - When only custom terms:  (None, websearch_text)
    - When both:               (tsquery_text, websearch_text) — SQL ANDs them

    Examples:
        keywords=["construção", "obras"], custom_terms=None
          -> ("construção | obras", None)

        keywords=None, custom_terms=["asfalto"]
          -> (None, "asfalto")

        keywords=["pavimentação"], custom_terms=["asfalto"]
          -> ("pavimentação", "asfalto")
          SQL does: to_tsquery(pavimentação) && websearch_to_tsquery(asfalto)

        keywords=None, custom_terms=['"limpeza hospitalar"']
          -> (None, '"limpeza hospitalar"')
          SQL does: websearch_to_tsquery('"limpeza hospitalar"') — exact phrase

        keywords=None, custom_terms=["-escolar"]
          -> (None, "-escolar")
          SQL does: websearch_to_tsquery('-escolar') — excludes "escolar"
    """
    tsquery_text: str | None = None
    websearch_text: str | None = None

    if keywords:
        cleaned = [_clean_token(k) for k in keywords if k and k.strip()]
        if cleaned:
            keyword_tokens = [_keyword_to_tstoken(k) for k in cleaned]
            if len(keyword_tokens) == 1:
                tsquery_text = keyword_tokens[0]
            else:
                tsquery_text = " | ".join(keyword_tokens)

    if custom_terms:
        # Preserve raw custom terms for websearch_to_tsquery (don't strip special chars)
        cleaned_custom = [t.strip() for t in custom_terms if t and t.strip()]
        if cleaned_custom:
            websearch_text = " ".join(cleaned_custom)

    return (tsquery_text, websearch_text)


def _build_trigram_term(
    keywords: list[str] | None,
    custom_terms: list[str] | None,
) -> str | None:
    """Build a plain-text term for trigram similarity search.

    Strips tsquery syntax artifacts and returns a clean plain-text string
    suitable for word_similarity().
    """
    parts: list[str] = []
    if keywords:
        parts.extend([_clean_token(k) for k in keywords if k and k.strip()])
    if custom_terms:
        parts.extend([t.strip() for t in custom_terms if t and t.strip()])
    if not parts:
        return None
    # Remove quotes and dashes (tsquery / websearch artifacts not useful for trigram)
    text = " ".join(parts)
    text = re.sub(r'["\-]', ' ', text).strip()
    text = re.sub(r'\s+', ' ', text)
    return text or None


def _clean_token(token: str) -> str:
    """Strip whitespace and remove characters that break tsquery syntax."""
    token = token.strip()
    # Remove characters not valid in tsquery lexemes (keep letters, digits, hyphens)
    token = re.sub(r"[^\w\s\-]", "", token, flags=re.UNICODE)
    return token.strip()


def _keyword_to_tstoken(keyword: str) -> str:
    """Convert a keyword to a tsquery token.

    Single word -> plain lexeme (optionally synonym-expanded — STORY-5.4 AC2).
    Multi-word  -> phrase query using <-> operator (e.g. "pré moldado" -> "pré<->moldado").

    Synonym expansion policy: guarded by `FTS_SYNONYM_EXPANSION_ENABLED`.
    When enabled and the token is single-word, we consult
    `data.fts_synonyms.SYNONYMS`; when hits exist we emit a grouped OR
    block `(term | synonym1 | synonym2)`. Multi-word phrases are NOT
    expanded — phrase matching is brittle and expansion would confuse
    operator precedence.
    """
    words = keyword.split()
    if len(words) != 1:
        return "<->".join(words)

    # Single-word: try synonym expansion (opt-in via feature flag).
    from config import FTS_SYNONYM_EXPANSION_ENABLED

    if not FTS_SYNONYM_EXPANSION_ENABLED:
        return words[0]

    from data.fts_synonyms import expand_term

    expansions = expand_term(words[0].lower())
    if len(expansions) == 1:
        return words[0]
    # Parenthesize so precedence with outer `|` is unambiguous.
    return "(" + " | ".join(expansions) + ")"


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
