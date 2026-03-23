"""
LLM Arbiter for False Positive Elimination (STORY-179 AC3) + Zero Match Classification (GTM-FIX-028).
GTM-RESILIENCE-D02: Structured output with confidence, evidence, and re-ranking support.

Uses GPT-4.1-nano to classify contracts:
- "uncertain zone" (1-5% term density): PRIMARILY about sector? SIM/NAO
- "zero match" (0% keyword match): Is this contract relevant to sector? YES/NO

D-02: Returns structured JSON with:
  classe (SIM/NAO), confianca (0-100), evidencias (literal citations), motivo_exclusao

Cost: ~R$ 0.00007 per classification (structured) vs ~R$ 0.00002 (binary)
Latency: ~60ms per call (structured) vs ~50ms (binary)
Cache: In-memory MD5-based cache for repeated queries
"""

import hashlib
import json
import logging
import os
import time as _time_module
from collections import OrderedDict
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from openai import OpenAI
from metrics import (
    LLM_CALLS, LLM_DURATION, EVIDENCE_PREFIX_STRIPPED, ARBITER_CACHE_SIZE,
    ARBITER_CACHE_HITS, ARBITER_CACHE_MISSES, ARBITER_CACHE_EVICTIONS,
)

# Configure logging
logger = logging.getLogger(__name__)

# HARDEN-001 / DEBT-103 AC1: OpenAI client timeout (default 600s → 15s → 5s)
# GPT-4.1-nano p99 ≈ 1s; 5s = 5× p99. Prevents thread starvation on LLM hangs.
# Configurable via OPENAI_TIMEOUT_S (preferred) or LLM_TIMEOUT_S (legacy alias).
_LLM_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT_S", os.getenv("LLM_TIMEOUT_S", "5")))

# OpenAI client (initialized lazily to avoid import-time errors in tests)
_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """Get or initialize OpenAI client (lazy initialization)."""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=_LLM_TIMEOUT,
            max_retries=1,
        )
    return _client


# LLM configuration
# GTM-FIX-028 AC5: Migrated default from gpt-4o-mini to gpt-4.1-nano (33% cheaper)
LLM_MODEL = os.getenv("LLM_ARBITER_MODEL", "gpt-4.1-nano")
LLM_MAX_TOKENS = int(os.getenv("LLM_ARBITER_MAX_TOKENS", "1"))
LLM_TEMPERATURE = float(os.getenv("LLM_ARBITER_TEMPERATURE", "0"))
LLM_ENABLED = os.getenv("LLM_ARBITER_ENABLED", "true").lower() == "true"

# D-02: Structured output max tokens (accommodates JSON + evidence)
# DEBT-101 AC5: Increased 300 → 800. 300 still caused JSON truncation in 20-30%
# of calls (CRIT-038/SYS-002). 800 tokens accommodates worst-case JSON responses
# with 3 evidence items + motivo_exclusao. Cost: +500 tokens × $0.40/M = +R$0.001/call.
LLM_STRUCTURED_MAX_TOKENS = int(os.getenv("LLM_STRUCTURED_MAX_TOKENS", "800"))

# D-02 AC9: gpt-4.1-nano pricing (per million tokens)
_PRICING_INPUT_PER_M = 0.10   # USD per 1M input tokens
_PRICING_OUTPUT_PER_M = 0.40  # USD per 1M output tokens
# DEBT-325: Configurable via USD_TO_BRL_RATE env var (default 5.0)
def _get_usd_to_brl() -> float:
    """Lazy import to avoid circular dependency with config at module level."""
    from config import USD_TO_BRL_RATE
    return USD_TO_BRL_RATE

# In-memory L1 cache for LLM decisions (key = MD5 hash of input)
# D-02 AC8: Cache value is now dict (structured) or bool (legacy), keyed with prompt version
# STORY-294 AC3: L2 cache in Redis hash with 1h TTL for cross-worker sharing
# HARDEN-009 / DEBT-103 AC3: LRU eviction with configurable size limit
_ARBITER_CACHE_MAX = int(os.getenv("LRU_MAX_SIZE", "5000"))
_arbiter_cache: OrderedDict[str, Any] = OrderedDict()
_ARBITER_REDIS_PREFIX = "smartlic:arbiter:"


def _arbiter_cache_set(key: str, value: Any) -> None:
    """HARDEN-009 / DEBT-103 AC4: Set cache entry with LRU eviction + metrics."""
    _arbiter_cache[key] = value
    _arbiter_cache.move_to_end(key)
    while len(_arbiter_cache) > _ARBITER_CACHE_MAX:
        _arbiter_cache.popitem(last=False)
        ARBITER_CACHE_EVICTIONS.inc()
    ARBITER_CACHE_SIZE.set(len(_arbiter_cache))


# ============================================================================
# STORY-294 AC3: Redis L2 cache helpers (sync — runs in ThreadPoolExecutor)
# ============================================================================


def _arbiter_cache_get_redis(cache_key: str) -> Optional[Any]:
    """Read from Redis L2 cache (sync). Returns None on miss or error."""
    try:
        from redis_pool import get_sync_redis
        redis = get_sync_redis()
        if not redis:
            return None

        key = f"{_ARBITER_REDIS_PREFIX}{cache_key}"
        data = redis.get(key)
        if data:
            result = json.loads(data)
            # Promote to L1 for fast subsequent access
            _arbiter_cache_set(cache_key, result)
            logger.debug(f"STORY-294: Arbiter cache L2 HIT: {cache_key[:16]}...")
            return result
    except Exception as e:
        try:
            from metrics import STATE_STORE_ERRORS
            STATE_STORE_ERRORS.labels(store="arbiter", operation="read").inc()
        except Exception:
            pass
        logger.warning(f"STORY-294: Arbiter cache Redis read failed: {e}")
        import sentry_sdk
        sentry_sdk.capture_exception(e)
    return None


def _arbiter_cache_set_redis(cache_key: str, value: Any) -> None:
    """Write to Redis L2 cache (sync). Fire-and-forget on error."""
    try:
        from redis_pool import get_sync_redis
        redis = get_sync_redis()
        if not redis:
            return

        from config import ARBITER_REDIS_TTL
        key = f"{_ARBITER_REDIS_PREFIX}{cache_key}"
        redis.setex(key, ARBITER_REDIS_TTL, json.dumps(value, default=str))
    except Exception as e:
        try:
            from metrics import STATE_STORE_ERRORS
            STATE_STORE_ERRORS.labels(store="arbiter", operation="write").inc()
        except Exception:
            pass
        logger.warning(f"STORY-294: Arbiter cache Redis write failed: {e}")
        import sentry_sdk
        sentry_sdk.capture_exception(e)


# ============================================================================
# D-02 AC1: Structured Output Schema
# ============================================================================

class LLMClassification(BaseModel):
    """D-02 AC1: Structured classification result from LLM arbiter.

    Fields:
        classe: Binary decision — SIM (relevant) or NAO (not relevant)
        confianca: Confidence 0-100%
        evidencias: Up to 3 literal text excerpts from procurement description
        motivo_exclusao: Filled only when classe="NAO" — reason for exclusion
        precisa_mais_dados: True when LLM detects insufficient description
    """
    classe: Literal["SIM", "NAO"]
    confianca: int = Field(ge=0, le=100)
    evidencias: list[str] = Field(default_factory=list)
    motivo_exclusao: Optional[str] = Field(default=None)
    precisa_mais_dados: bool = False

    @field_validator("evidencias", mode="before")
    @classmethod
    def _cap_evidencias(cls, v: list[str]) -> list[str]:
        """Truncate to 3 items — LLM occasionally returns 4+."""
        if isinstance(v, list) and len(v) > 3:
            return v[:3]
        return v

    @field_validator("motivo_exclusao", mode="before")
    @classmethod
    def _cap_motivo(cls, v: str | None) -> str | None:
        """Truncate to 500 chars — LLM occasionally exceeds limits."""
        if isinstance(v, str) and len(v) > 500:
            return v[:497] + "..."
        return v


# ============================================================================
# D-02 AC9: Cost tracking (per-search aggregation)
# ============================================================================

_search_token_stats: dict[str, dict] = {}


def _log_token_usage(
    search_id: str,
    input_tokens: int,
    output_tokens: int,
    call_type: str = "arbiter",
) -> None:
    """Track token usage per search for cost monitoring (AC9) + DEBT-110 AC14."""
    if search_id not in _search_token_stats:
        _search_token_stats[search_id] = {
            "llm_tokens_input": 0,
            "llm_tokens_output": 0,
            "llm_calls": 0,
        }
    stats = _search_token_stats[search_id]
    stats["llm_tokens_input"] += input_tokens
    stats["llm_tokens_output"] += output_tokens
    stats["llm_calls"] += 1

    # DEBT-110 AC14: Cumulative cost metric (Prometheus)
    cost_usd = (
        input_tokens * _PRICING_INPUT_PER_M / 1_000_000
        + output_tokens * _PRICING_OUTPUT_PER_M / 1_000_000
    )
    cost_brl = cost_usd * _get_usd_to_brl()
    try:
        from metrics import LLM_COST_BRL
        LLM_COST_BRL.labels(model=LLM_MODEL, call_type=call_type).inc(cost_brl)
    except Exception:
        pass  # Never let metrics break LLM flow


def get_search_cost_stats(search_id: str) -> dict:
    """Get token usage and estimated cost for a search (AC9).

    Returns:
        Dict with llm_tokens_input, llm_tokens_output, llm_cost_estimated_brl, llm_calls
    """
    stats = _search_token_stats.pop(search_id, {
        "llm_tokens_input": 0, "llm_tokens_output": 0, "llm_calls": 0,
    })
    cost_usd = (
        stats["llm_tokens_input"] * _PRICING_INPUT_PER_M / 1_000_000
        + stats["llm_tokens_output"] * _PRICING_OUTPUT_PER_M / 1_000_000
    )
    cost_brl = cost_usd * _get_usd_to_brl()
    stats["llm_cost_estimated_brl"] = round(cost_brl, 6)

    # AC9: Alert if cost > R$ 0.10 per search
    if cost_brl > 0.10:
        logger.warning(
            f"D-02 AC9: High LLM cost for search {search_id}: "
            f"R$ {cost_brl:.4f} ({stats['llm_calls']} calls, "
            f"{stats['llm_tokens_input']}in/{stats['llm_tokens_output']}out tokens)"
        )

    return stats


# ============================================================================
# Prompt builders (updated for structured output)
# ============================================================================

# STORY-328 AC13: Dynamic negative examples per sector (org name traps)
_SECTOR_NEGATIVE_EXAMPLES: dict[str, list[str]] = {
    "saude": [
        "Locação de veículos para Secretaria de Saúde",
        "Material de escritório para Hospital Municipal",
        "Construção de muro na Unidade de Saúde",
    ],
    "informatica": [
        "Uniformes para Secretaria de Tecnologia",
        "Material de limpeza para Instituto de Tecnologia",
        "Reforma predial na Secretaria de Tecnologia da Informação",
    ],
    "vigilancia": [
        "Material de escritório para Secretaria de Segurança Pública",
        "Gêneros alimentícios para Departamento de Segurança",
        "Locação de veículos para Secretaria de Segurança",
    ],
    "vestuario": [
        "Equipamentos de informática para fábrica de confecções",
        "Manutenção predial em loja de roupas",
    ],
    "alimentos": [
        "Material de escritório para Secretaria de Alimentação",
        "Reforma na cozinha da Secretaria de Agricultura",
    ],
    "facilities": [
        "Material de escritório para empresa de limpeza",
        "Uniformes para equipe de conservação",
    ],
    "engenharia_rodoviaria": [
        "Material de escritório para Departamento de Estradas",
        "Uniformes para equipe de rodovias",
    ],
    "transporte": [
        "Material de escritório para Secretaria de Transportes",
        "Uniformes para Departamento de Trânsito",
    ],
    "materiais_eletricos": [
        "Material de limpeza para Companhia de Energia",
        "Uniformes para equipe da Eletrobras",
    ],
    "materiais_hidraulicos": [
        "Material de escritório para SABESP",
        "Uniformes para equipe de saneamento",
    ],
    "mobiliario": [
        "Material de limpeza para fábrica de móveis",
        "Combustível para Secretaria de Administração",
    ],
    "papelaria": [
        "Combustível para gráfica municipal",
        "Uniformes para equipe de impressão",
    ],
    "software": [
        "Material de escritório para empresa de software",
        "Uniformes para equipe de TI",
    ],
    "manutencao_predial": [
        "Material de escritório para equipe de manutenção",
        "Gêneros alimentícios para prédio público",
    ],
}


def _get_sector_negative_examples(setor_id: str) -> list[str]:
    """Return dynamic negative examples for a sector (AC13)."""
    return _SECTOR_NEGATIVE_EXAMPLES.get(setor_id, [])


_STRUCTURED_JSON_INSTRUCTION = """
Responda em JSON com a estrutura exata:
{"classe": "SIM" ou "NAO", "confianca": 0-100, "evidencias": ["citação 1", "citação 2"], "motivo_exclusao": "razão se NAO", "precisa_mais_dados": false}

REGRAS:
- evidencias: use COPY-PASTE exato de trechos do campo Objeto acima — cada evidência DEVE ser uma substring que aparece literalmente no texto do Objeto, sem alterar, adicionar ou remover nenhuma palavra. Se não encontrar trecho literal relevante, retorne evidencias como lista vazia [].
- confianca: 100 se palavras-chave primárias presentes, 50 se ambíguo, 0 se claramente fora do setor
- motivo_exclusao: preencha APENAS quando classe="NAO"
- precisa_mais_dados: true se a descrição é muito curta/vaga para decidir"""


def _build_conservative_prompt(
    setor_id: Optional[str],
    setor_name: str,
    objeto_truncated: str,
    valor: float,
    structured: bool = False,
) -> str:
    """Build sector-aware conservative prompt with dynamic examples (STORY-251)."""
    from sectors import get_sector

    if not setor_id:
        return _build_standard_sector_prompt(setor_name, objeto_truncated, valor, structured)

    try:
        config = get_sector(setor_id)
    except (KeyError, Exception):
        logger.warning(f"Sector '{setor_id}' not found for conservative prompt, using standard")
        return _build_standard_sector_prompt(setor_name, objeto_truncated, valor, structured)

    description = config.description or setor_name
    keywords = sorted(config.keywords)[:3]
    sim_lines = "\n".join(f'- "Aquisição de {kw} para órgão público"' for kw in keywords)
    exclusions = sorted(config.exclusions)[:3]
    nao_section = ""
    if exclusions:
        nao_lines = "\n".join(f'- "{exc}"' for exc in exclusions)
        nao_section = f"\nNAO:\n{nao_lines}"

    suffix = _STRUCTURED_JSON_INSTRUCTION if structured else "\nResponda APENAS: SIM ou NAO"

    # STORY-328 AC13: Dynamic negative examples per sector (org name traps)
    _neg_examples = _get_sector_negative_examples(setor_id)
    neg_section = ""
    if _neg_examples:
        neg_lines = "\n".join(f'- "{ex}" → NAO' for ex in _neg_examples)
        neg_section = f"\nARMADILHAS (contêm nome de órgão, NÃO são do setor):\n{neg_lines}"

    return f"""Você é um classificador de licitações públicas. Analise se o contrato é PRIMARIAMENTE sobre o setor especificado (> 80% do valor e escopo).

SETOR: {setor_name}
DESCRIÇÃO DO SETOR: {description}

ATENÇÃO CRÍTICA: O campo 'Objeto' pode conter o nome do órgão comprador (ex: 'Secretaria de Saúde', 'Secretaria de Tecnologia', 'Prefeitura Municipal'). IGNORE completamente nomes de órgãos, secretarias, hospitais, universidades e institutos. Foque EXCLUSIVAMENTE no que está sendo CONTRATADO ou ADQUIRIDO.

CONTRATO:
Valor: R$ {valor:,.2f}
Objeto: {objeto_truncated}

EXEMPLOS DE CLASSIFICAÇÃO:

SIM:
{sim_lines}
{nao_section}
{neg_section}

Este contrato é PRIMARIAMENTE sobre {setor_name}?{suffix}"""


def _build_standard_sector_prompt(
    setor_name: str,
    objeto_truncated: str,
    valor: float,
    structured: bool = False,
) -> str:
    """Build standard sector prompt without examples (density 3-8% or fallback)."""
    suffix = _STRUCTURED_JSON_INSTRUCTION if structured else "\nResponda APENAS: SIM ou NAO"

    return f"""Setor: {setor_name}
Valor: R$ {valor:,.2f}
Objeto: {objeto_truncated}

Este contrato é PRIMARIAMENTE sobre {setor_name}?{suffix}"""


def _build_term_search_prompt(
    termos: list[str],
    objeto_truncated: str,
    valor: float,
    structured: bool = False,
) -> str:
    """STORY-267 AC1: Build term-aware prompt for custom search terms.

    Focuses exclusively on user's search terms — does NOT mention any sector name.
    Asks: "Is this contract relevant for someone searching these terms?"
    """
    termos_display = ", ".join(termos)
    valor_display = f"R$ {valor:,.2f}" if valor > 0 else "Não informado"
    suffix = _STRUCTURED_JSON_INSTRUCTION if structured else "\nResponda APENAS: SIM ou NAO"

    return f"""Você classifica licitações públicas. O usuário buscou os seguintes termos:
Termos buscados: {termos_display}

CONTRATO:
Valor: {valor_display}
Objeto: {objeto_truncated}

Este contrato é RELEVANTE para alguém que busca "{termos_display}"?
Considere: o objeto deve ser PRIMARIAMENTE sobre os termos buscados, não apenas mencioná-los de forma tangencial.{suffix}"""


def _build_zero_match_prompt(
    setor_id: Optional[str],
    setor_name: str,
    objeto_truncated: str,
    valor: float,
    structured: bool = False,
) -> str:
    """Build sector-aware prompt for bids with ZERO keyword matches (GTM-FIX-028 AC4)."""
    from sectors import get_sector

    valor_display = f"R$ {valor:,.2f}" if valor > 0 else "Não informado"
    suffix = _STRUCTURED_JSON_INSTRUCTION if structured else "\nResponda APENAS: SIM ou NAO"

    if not setor_id:
        return f"""SETOR: {setor_name}

CONTRATO:
Valor: {valor_display}
Objeto: {objeto_truncated}

Este contrato é sobre {setor_name}?{suffix}"""

    try:
        config = get_sector(setor_id)
    except (KeyError, Exception):
        logger.warning(f"Sector '{setor_id}' not found for zero_match prompt, using fallback")
        return f"""SETOR: {setor_name}

CONTRATO:
Valor: {valor_display}
Objeto: {objeto_truncated}

Este contrato é sobre {setor_name}?{suffix}"""

    description = config.description or setor_name
    keywords = sorted(config.keywords)[:5]
    sim_lines = "\n".join(f'- "{kw}"' for kw in keywords)
    exclusions = sorted(config.exclusions)[:3]
    nao_section = ""
    if exclusions:
        nao_lines = "\n".join(f'- "{exc}"' for exc in exclusions)
        nao_section = f"\nExemplos de NÃO (não é sobre o setor):\n{nao_lines}"

    # STORY-328 AC13: Dynamic negative examples per sector (org name traps)
    _neg_examples = _get_sector_negative_examples(setor_id)
    neg_section = ""
    if _neg_examples:
        neg_lines = "\n".join(f'- "{ex}" → NAO' for ex in _neg_examples)
        neg_section = f"\nExemplos de ARMADILHA (contêm nome de órgão, NÃO são do setor):\n{neg_lines}"

    return f"""Você classifica licitações públicas. Este contrato NÃO contém palavras-chave do setor — analise o OBJETO para determinar se é relevante.

SETOR: {setor_name}
DESCRIÇÃO: {description}

ATENÇÃO CRÍTICA: O campo 'Objeto' pode conter o nome do órgão comprador (ex: 'Secretaria de Saúde', 'Secretaria de Tecnologia', 'Prefeitura Municipal'). IGNORE completamente nomes de órgãos, secretarias, hospitais, universidades e institutos. Foque EXCLUSIVAMENTE no que está sendo CONTRATADO ou ADQUIRIDO.

Exemplos de SIM (é sobre o setor):
{sim_lines}
{nao_section}
{neg_section}

CONTRATO:
Valor: {valor_display}
Objeto: {objeto_truncated}

Este contrato é sobre {setor_name}?{suffix}"""


# ============================================================================
# CRIT-035: Strip LLM-added field-name prefixes from evidence
# ============================================================================

_KNOWN_PREFIXES = ["objeto:", "descrição:", "descricao:", "título:", "titulo:", "title:", "description:"]


def _strip_evidence_prefix(evidence: str) -> tuple[str, bool]:
    """Strip common field-name prefixes that GPT adds to evidence (CRIT-035).

    GPT-4.1-nano systematically adds prefixes like "Objeto:" when copying text
    from procurement descriptions, causing substring validation to fail.

    Returns:
        tuple: (cleaned_evidence, was_stripped)
    """
    ev_lower = evidence.strip().lower()
    for prefix in _KNOWN_PREFIXES:
        if ev_lower.startswith(prefix):
            stripped = evidence.strip()[len(prefix):].strip()
            if stripped:  # Don't return empty string
                logger.debug(
                    f"CRIT-035: Evidence prefix stripped: '{evidence.strip()[:len(prefix)]}' "
                    f"→ checking cleaned evidence"
                )
                EVIDENCE_PREFIX_STRIPPED.inc()
                return stripped, True
    return evidence, False


# ============================================================================
# D-02 AC3: Robust JSON parser with fallback
# ============================================================================

# D-02: Track parse success rate per search
_parse_stats: dict[str, dict] = {}


def _parse_structured_response(
    raw_content: str,
    objeto: str,
    search_id: str = "",
) -> LLMClassification:
    """Parse LLM JSON response into LLMClassification with robust fallback (AC3).

    If JSON is invalid, falls back to SIM/NAO detection in raw text (legacy behavior).
    Evidence is validated as substring of objeto (AC6 hallucination guard).

    Args:
        raw_content: Raw LLM response string
        objeto: Original procurement object text (for evidence validation)
        search_id: For parse rate tracking

    Returns:
        LLMClassification with validated fields
    """
    # Track parse attempts
    if search_id:
        if search_id not in _parse_stats:
            _parse_stats[search_id] = {"attempts": 0, "json_success": 0, "fallback": 0}
        _parse_stats[search_id]["attempts"] += 1

    # Try JSON parse first
    try:
        data = json.loads(raw_content.strip())
        classification = LLMClassification.model_validate(data)

        # AC6 + CRIT-022: Validate evidence as literal substrings of objeto
        # Use normalize_text() for accent/punctuation/whitespace normalization
        # (LLM often returns text without accents or with normalized whitespace)
        from filter import normalize_text as _normalize
        objeto_normalized = _normalize(objeto)
        validated_evidence = []
        for ev in classification.evidencias:
            if ev and len(ev) <= 100:
                if _normalize(ev) in objeto_normalized:
                    validated_evidence.append(ev)
                else:
                    # CRIT-035: Try stripping known prefixes before discarding
                    stripped_ev, was_stripped = _strip_evidence_prefix(ev)
                    if was_stripped and _normalize(stripped_ev) in objeto_normalized:
                        validated_evidence.append(stripped_ev)
                    else:
                        logger.warning(
                            f"D-02 AC6: Discarding hallucinated evidence (not substring): "
                            f"evidence={ev!r} not found in objeto"
                        )
            elif ev and len(ev) > 100:
                # Truncate to 100 chars and re-validate
                truncated = ev[:100]
                if _normalize(truncated) in objeto_normalized:
                    validated_evidence.append(truncated)

        classification.evidencias = validated_evidence

        if search_id:
            _parse_stats[search_id]["json_success"] += 1

        return classification

    except (json.JSONDecodeError, Exception) as e:
        # AC3: Fallback to SIM/NAO detection in raw text
        logger.warning(
            f"D-02 AC3: JSON parse failed, using text fallback: {e} | "
            f"raw={raw_content[:200]!r}"
        )

        if search_id:
            _parse_stats[search_id]["fallback"] += 1

        raw_upper = raw_content.strip().upper()
        if "SIM" in raw_upper:
            return LLMClassification(
                classe="SIM", confianca=60, evidencias=[],
                motivo_exclusao=None, precisa_mais_dados=False,
            )
        else:
            return LLMClassification(
                classe="NAO", confianca=40, evidencias=[],
                motivo_exclusao="Fallback: LLM returned non-JSON response",
                precisa_mais_dados=False,
            )


def get_parse_stats(search_id: str) -> dict:
    """Get structured parse success rate for a search."""
    return _parse_stats.pop(search_id, {"attempts": 0, "json_success": 0, "fallback": 0})


# ============================================================================
# Main classification function
# ============================================================================

def classify_contract_primary_match(
    objeto: str,
    valor: float,
    setor_name: Optional[str] = None,
    termos_busca: Optional[list[str]] = None,
    prompt_level: str = "standard",
    setor_id: Optional[str] = None,
    search_id: str = "",
) -> dict:
    """Classify if contract is PRIMARILY about sector/terms.

    D-02: Returns structured dict with confidence, evidence, and rejection reason.

    Returns:
        dict with keys:
            is_primary (bool): True if SIM
            confidence (int): 0-100
            evidence (list[str]): Literal text excerpts from objeto
            rejection_reason (str|None): Reason when NAO
            needs_more_data (bool): True when description insufficient
    """
    # CRIT-004 AC13: Include search_id in classification logs for correlation
    from middleware import search_id_var
    _search_id = search_id_var.get("-")

    # DEBT-128: Structured output is always-on (LLM_STRUCTURED_OUTPUT_ENABLED removed)
    structured_enabled = True

    # Feature flag check
    if not LLM_ENABLED:
        logger.warning(
            "LLM arbiter disabled (LLM_ARBITER_ENABLED=false). "
            "Accepting ambiguous contract by default."
        )
        return {"is_primary": True, "confidence": 50, "evidence": [],
                "rejection_reason": None, "needs_more_data": False}

    # Validate inputs
    if not setor_name and not termos_busca:
        logger.error(
            "classify_contract_primary_match called without setor_name or termos_busca"
        )
        return {"is_primary": True, "confidence": 50, "evidence": [],
                "rejection_reason": None, "needs_more_data": False}

    # Truncate objeto to 500 chars (AC3.7 - save tokens)
    objeto_truncated = objeto[:500]

    # Build prompt based on mode and prompt_level
    if setor_name:
        mode = "setor"
        context = setor_name

        if prompt_level == "zero_match":
            user_prompt = _build_zero_match_prompt(
                setor_id=setor_id, setor_name=setor_name,
                objeto_truncated=objeto_truncated, valor=valor,
                structured=structured_enabled,
            )
        elif prompt_level == "conservative":
            user_prompt = _build_conservative_prompt(
                setor_id=setor_id, setor_name=setor_name,
                objeto_truncated=objeto_truncated, valor=valor,
                structured=structured_enabled,
            )
        else:
            user_prompt = _build_standard_sector_prompt(
                setor_name=setor_name, objeto_truncated=objeto_truncated,
                valor=valor, structured=structured_enabled,
            )
    else:
        mode = "termos"
        context = ", ".join(termos_busca) if termos_busca else ""
        suffix = _STRUCTURED_JSON_INSTRUCTION if structured_enabled else "\nResponda APENAS: SIM ou NAO"
        user_prompt = f"""Termos buscados: {context}
Valor: R$ {valor:,.2f}
Objeto: {objeto_truncated}

Os termos buscados descrevem o OBJETO PRINCIPAL deste contrato (não itens secundários)?{suffix}"""

    # D-02 AC8: Cache key includes "v2" when structured to avoid old/new collision
    prompt_version = "v2" if structured_enabled else "v1"
    cache_key = hashlib.md5(
        f"{prompt_version}:{mode}:{context}:{valor}:{objeto_truncated}:{prompt_level}:{setor_id or ''}".encode()
    ).hexdigest()

    # STORY-294 / DEBT-103 AC4: L1 (in-memory) → L2 (Redis) cache lookup with metrics
    if cache_key in _arbiter_cache:
        _arbiter_cache.move_to_end(cache_key)
        ARBITER_CACHE_HITS.labels(level="l1").inc()
        logger.debug(
            f"LLM arbiter cache L1 HIT: mode={mode} "
            f"context={context[:50]}... valor={valor}"
        )
        return _arbiter_cache[cache_key]

    redis_cached = _arbiter_cache_get_redis(cache_key)
    if redis_cached is not None:
        ARBITER_CACHE_HITS.labels(level="l2").inc()
        return redis_cached

    ARBITER_CACHE_MISSES.inc()

    # Call LLM
    try:
        if structured_enabled:
            system_prompt = (
                "Você é um classificador conservador de licitações públicas. "
                "Em caso de dúvida, responda NAO. "
                "Apenas responda SIM se o contrato é CLARAMENTE e PRIMARIAMENTE sobre o setor. "
                "Responda em formato JSON válido conforme a estrutura solicitada."
            )
            effective_max_tokens = LLM_STRUCTURED_MAX_TOKENS
        else:
            system_prompt = (
                "Você é um classificador conservador de licitações. "
                "Em caso de dúvida, responda NAO. "
                "Apenas responda SIM se o contrato é CLARAMENTE e PRIMARIAMENTE sobre o setor. "
                "Responda APENAS 'SIM' ou 'NAO'."
            )
            effective_max_tokens = LLM_MAX_TOKENS

        api_kwargs: dict[str, Any] = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": effective_max_tokens,
            "temperature": LLM_TEMPERATURE,
        }
        # D-02 AC2: Request JSON format when structured output is enabled
        if structured_enabled:
            api_kwargs["response_format"] = {"type": "json_object"}

        _llm_start = _time_module.time()
        response = _get_client().chat.completions.create(**api_kwargs)
        _llm_elapsed = _time_module.time() - _llm_start

        raw_content = response.choices[0].message.content.strip()

        # D-02 AC9: Track token usage
        usage = getattr(response, "usage", None)
        if usage and search_id:
            _log_token_usage(
                search_id,
                input_tokens=getattr(usage, "prompt_tokens", 0),
                output_tokens=getattr(usage, "completion_tokens", 0),
            )

        # Parse response
        if structured_enabled:
            classification = _parse_structured_response(raw_content, objeto, search_id)
            is_primary = classification.classe == "SIM"
            result = {
                "is_primary": is_primary,
                "confidence": classification.confianca,
                "evidence": classification.evidencias,
                "rejection_reason": classification.motivo_exclusao,
                "needs_more_data": classification.precisa_mais_dados,
            }
        else:
            # Legacy binary mode
            llm_response = raw_content.upper()
            is_primary = llm_response == "SIM"
            result = {
                "is_primary": is_primary,
                "confidence": 100 if is_primary else 0,
                "evidence": [],
                "rejection_reason": None,
                "needs_more_data": False,
            }

        # E-03: Prometheus metrics
        _decision = "SIM" if is_primary else "NAO"
        LLM_DURATION.labels(model=LLM_MODEL, decision=_decision).observe(_llm_elapsed)
        LLM_CALLS.labels(model=LLM_MODEL, decision=_decision, zone=prompt_level).inc()

        # Cache the result (L1 + L2)
        _arbiter_cache_set(cache_key, result)
        _arbiter_cache_set_redis(cache_key, result)

        logger.info(
            f"LLM arbiter decision: {_decision} conf={result['confidence']}% | "
            f"search={_search_id} mode={mode} prompt_level={prompt_level} structured={structured_enabled} "
            f"context={context[:50]}... valor=R${valor:,.2f}"
        )

        return result

    except Exception as e:
        LLM_CALLS.labels(model=LLM_MODEL, decision="ERROR", zone=prompt_level).inc()

        # STORY-354 AC1+AC8: When LLM fails for zero-match bids, return PENDING_REVIEW
        # instead of REJECT — prevents silent loss of potentially relevant opportunities.
        from config import LLM_FALLBACK_PENDING_ENABLED
        if LLM_FALLBACK_PENDING_ENABLED and prompt_level == "zero_match":
            logger.warning(
                f"LLM arbiter FAILED (PENDING_REVIEW fallback): {e} | "
                f"search={_search_id} mode={mode} context={context[:50]}... valor={valor:,.2f}"
            )
            from metrics import LLM_FALLBACK_PENDING
            _sector_label = context[:50] if mode == "setor" else "termos"
            _reason = type(e).__name__
            LLM_FALLBACK_PENDING.labels(sector=_sector_label, reason=_reason).inc()
            result = {
                "is_primary": False,
                "confidence": 0,
                "evidence": [],
                "rejection_reason": "LLM unavailable",
                "needs_more_data": False,
                "pending_review": True,
            }
            return result

        logger.error(
            f"LLM arbiter FAILED (defaulting to REJECT): {e} | "
            f"search={_search_id} mode={mode} context={context[:50]}... valor={valor:,.2f}"
        )
        # AC3: Conservative fallback on error — REJECT with confidence 0
        result = {
            "is_primary": False,
            "confidence": 0,
            "evidence": [],
            "rejection_reason": "LLM unavailable",
            "needs_more_data": False,
        }
        return result


# ============================================================================
# UX-402: Batch zero-match classification
# ============================================================================


def _build_zero_match_batch_prompt(
    setor_id: Optional[str],
    setor_name: str,
    items: list[dict],
) -> str:
    """Build a batch prompt for classifying multiple zero-match items at once (AC1).

    Args:
        setor_id: Sector ID for sector-aware prompt
        setor_name: Human-readable sector name
        items: List of dicts with 'objeto' (str) and 'valor' (float)

    Returns:
        Prompt string with numbered list of items
    """
    from sectors import get_sector

    # Build sector context
    description = setor_name
    keywords_section = ""
    exclusions_section = ""
    neg_section = ""

    if setor_id:
        try:
            config = get_sector(setor_id)
            description = config.description or setor_name
            keywords = sorted(config.keywords)[:5]
            keywords_section = "\nPalavras-chave do setor: " + ", ".join(keywords)
            exclusions = sorted(config.exclusions)[:3]
            if exclusions:
                exclusions_section = "\nExemplos de NÃO: " + ", ".join(exclusions)
            _neg_examples = _get_sector_negative_examples(setor_id)
            if _neg_examples:
                neg_lines = "; ".join(_neg_examples[:3])
                neg_section = f"\nARMADILHAS (nome de órgão ≠ setor): {neg_lines}"
        except (KeyError, Exception):
            logger.warning(f"Sector '{setor_id}' not found for batch prompt, using fallback")

    # Build numbered item list
    item_lines = []
    for i, item in enumerate(items, 1):
        obj = item["objeto"][:200]  # Truncate each to save tokens
        val = item["valor"]
        val_display = f"R$ {val:,.2f}" if val > 0 else "N/I"
        item_lines.append(f"{i}. [{val_display}] {obj}")

    items_text = "\n".join(item_lines)

    return f"""Você classifica licitações públicas em lote. Analise cada contrato e determine se é PRIMARIAMENTE sobre o setor especificado.

SETOR: {setor_name}
DESCRIÇÃO: {description}
{keywords_section}
{exclusions_section}
{neg_section}

ATENÇÃO: IGNORE nomes de órgãos/secretarias. Foque no que está sendo CONTRATADO.

CONTRATOS:
{items_text}

Responda APENAS com uma lista numerada de YES ou NO, uma por linha. Exemplo:
1. YES
2. NO
3. YES"""


def _build_zero_match_batch_prompt_terms(
    termos: list[str],
    items: list[dict],
) -> str:
    """Build a batch prompt for term-based zero-match classification (AC1).

    Args:
        termos: User's custom search terms
        items: List of dicts with 'objeto' (str) and 'valor' (float)

    Returns:
        Prompt string with numbered list of items
    """
    termos_display = ", ".join(termos)

    item_lines = []
    for i, item in enumerate(items, 1):
        obj = item["objeto"][:200]
        val = item["valor"]
        val_display = f"R$ {val:,.2f}" if val > 0 else "N/I"
        item_lines.append(f"{i}. [{val_display}] {obj}")

    items_text = "\n".join(item_lines)

    return f"""Você classifica licitações públicas em lote. Analise cada contrato e determine se é RELEVANTE para os termos buscados.

Termos buscados: {termos_display}

CONTRATOS:
{items_text}

Responda APENAS com uma lista numerada de YES ou NO, uma por linha. Exemplo:
1. YES
2. NO
3. YES"""


def _parse_batch_response(raw_content: str, expected_count: int) -> Optional[list[bool]]:
    """Parse a batch YES/NO response into a list of booleans (AC1, AC5).

    Args:
        raw_content: Raw LLM response with numbered YES/NO lines
        expected_count: Number of expected responses

    Returns:
        List of booleans (True=YES, False=NO), or None if count mismatch (AC5)
    """
    import re
    lines = raw_content.strip().split("\n")
    results = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Match patterns like "1. YES", "1.YES", "1) YES", "1 YES", "YES"
        match = re.match(r'^\d+[\.\):\s]*\s*(YES|NO|SIM|NAO|NÃO)\s*$', line, re.IGNORECASE)
        if match:
            decision = match.group(1).upper()
            results.append(decision in ("YES", "SIM"))

    if len(results) != expected_count:
        logger.warning(
            f"UX-402 AC5: Batch response count mismatch: "
            f"expected={expected_count}, got={len(results)}. "
            f"Rejecting all (zero noise philosophy). Raw: {raw_content[:300]!r}"
        )
        return None

    return results


def _classify_zero_match_batch(
    items: list[dict],
    setor_name: Optional[str] = None,
    setor_id: Optional[str] = None,
    termos_busca: Optional[list[str]] = None,
    search_id: str = "",
) -> list[dict]:
    """Classify multiple zero-match items in a single LLM call (AC1).

    Sends up to 20 items per batch. Returns list of classification results
    in the same order as input items.

    Args:
        items: List of dicts with 'objeto' and 'valor' keys
        setor_name: Sector name (for sector-based classification)
        setor_id: Sector ID (for sector-aware prompt)
        termos_busca: Custom search terms (for term-based classification)
        search_id: For cost tracking

    Returns:
        List of dicts with 'is_primary', 'confidence', 'evidence', 'rejection_reason',
        'needs_more_data' keys. Same length as input.
    """
    from config import LLM_ZERO_MATCH_BATCH_TIMEOUT

    if not items:
        return []

    # Build prompt
    if termos_busca:
        user_prompt = _build_zero_match_batch_prompt_terms(termos_busca, items)
    else:
        user_prompt = _build_zero_match_batch_prompt(setor_id, setor_name or "", items)

    system_prompt = (
        "Você é um classificador conservador de licitações públicas. "
        "Em caso de dúvida, responda NO. "
        "Responda APENAS com uma lista numerada de YES ou NO."
    )

    try:
        _llm_start = _time_module.time()
        response = _get_client().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max(len(items) * 15, 100),  # ~15 tokens per "N. YES\n"
            temperature=LLM_TEMPERATURE,
            timeout=LLM_ZERO_MATCH_BATCH_TIMEOUT,
        )
        _llm_elapsed = _time_module.time() - _llm_start

        raw_content = response.choices[0].message.content.strip()

        # Track token usage
        usage = getattr(response, "usage", None)
        if usage and search_id:
            _log_token_usage(
                search_id,
                input_tokens=getattr(usage, "prompt_tokens", 0),
                output_tokens=getattr(usage, "completion_tokens", 0),
            )

        # Parse response
        decisions = _parse_batch_response(raw_content, len(items))

        if decisions is None:
            # AC5: Count mismatch → reject all
            LLM_CALLS.labels(model=LLM_MODEL, decision="BATCH_MISMATCH", zone="zero_match_batch").inc()
            return [
                {
                    "is_primary": False,
                    "confidence": 0,
                    "evidence": [],
                    "rejection_reason": "Batch response count mismatch",
                    "needs_more_data": False,
                }
                for _ in items
            ]

        # Build results
        results = []
        yes_count = 0
        no_count = 0
        for is_yes in decisions:
            if is_yes:
                yes_count += 1
                results.append({
                    "is_primary": True,
                    "confidence": 60,  # Batch has lower confidence than individual
                    "evidence": [],
                    "rejection_reason": None,
                    "needs_more_data": False,
                })
            else:
                no_count += 1
                results.append({
                    "is_primary": False,
                    "confidence": 0,
                    "evidence": [],
                    "rejection_reason": "LLM batch: not primarily about sector",
                    "needs_more_data": False,
                })

        # Prometheus metrics
        LLM_DURATION.labels(model=LLM_MODEL, decision="BATCH").observe(_llm_elapsed)
        LLM_CALLS.labels(model=LLM_MODEL, decision="SIM", zone="zero_match_batch").inc(yes_count)
        LLM_CALLS.labels(model=LLM_MODEL, decision="NAO", zone="zero_match_batch").inc(no_count)

        logger.info(
            f"UX-402: Batch zero-match classified {len(items)} items in {_llm_elapsed:.2f}s: "
            f"{yes_count} YES, {no_count} NO"
        )

        return results

    except Exception as e:
        LLM_CALLS.labels(model=LLM_MODEL, decision="ERROR", zone="zero_match_batch").inc()
        logger.error(f"UX-402: Batch zero-match FAILED: {e}")
        raise  # Let caller handle fallback


def classify_contract_recovery(
    objeto: str,
    valor: float,
    rejection_reason: str,
    setor_name: Optional[str] = None,
    termos_busca: Optional[list[str]] = None,
    near_miss_info: Optional[str] = None,
) -> bool:
    """Use LLM to determine if a REJECTED contract should be RECOVERED (STORY-179 AC13).

    Recovery always uses binary mode (no structured output needed — it's an override check).
    """
    # Feature flag check
    if not LLM_ENABLED:
        logger.warning(
            "LLM arbiter disabled (LLM_ARBITER_ENABLED=false). "
            "Not recovering rejected contract."
        )
        return False

    # Validate inputs
    if not setor_name and not termos_busca:
        logger.error(
            "classify_contract_recovery called without setor_name or termos_busca"
        )
        return False

    objeto_truncated = objeto[:500]

    if setor_name:
        mode = "setor_recovery"
        context = setor_name
        additional_info = f"\nMotivo da rejeição: {rejection_reason}"
        if near_miss_info:
            additional_info += f"\nSinônimos encontrados: {near_miss_info}"

        user_prompt = f"""Este contrato foi REJEITADO automaticamente por: {rejection_reason}

Setor: {setor_name}
Valor: R$ {valor:,.2f}
Objeto: {objeto_truncated}
{additional_info if near_miss_info else ""}

Apesar da rejeição automática, este contrato é RELEVANTE para {setor_name}?
Responda APENAS: SIM ou NAO"""
    else:
        mode = "termos_recovery"
        context = ", ".join(termos_busca) if termos_busca else ""
        user_prompt = f"""Este contrato foi REJEITADO automaticamente por: {rejection_reason}

Termos buscados: {context}
Valor: R$ {valor:,.2f}
Objeto: {objeto_truncated}

Apesar da rejeição, os termos buscados descrevem o OBJETO PRINCIPAL deste contrato?
Responda APENAS: SIM ou NAO"""

    cache_key = hashlib.md5(
        f"{mode}:{context}:{valor}:{objeto_truncated}:{rejection_reason}".encode()
    ).hexdigest()

    # STORY-294: L1 (in-memory) → L2 (Redis) cache lookup
    if cache_key in _arbiter_cache:
        _arbiter_cache.move_to_end(cache_key)
        cached = _arbiter_cache[cache_key]
        if isinstance(cached, dict):
            return cached.get("is_primary", False)
        return cached

    redis_cached = _arbiter_cache_get_redis(cache_key)
    if redis_cached is not None:
        if isinstance(redis_cached, dict):
            return redis_cached.get("is_primary", False)
        return redis_cached

    try:
        system_prompt = (
            "Você é um classificador de licitações que avalia se contratos rejeitados "
            "automaticamente são relevantes. Responda APENAS 'SIM' ou 'NAO'."
        )

        _llm_start = _time_module.time()
        response = _get_client().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
        )
        _llm_elapsed = _time_module.time() - _llm_start

        llm_response = response.choices[0].message.content.strip().upper()
        should_recover = llm_response == "SIM"

        _decision = "SIM" if should_recover else "NAO"
        LLM_DURATION.labels(model=LLM_MODEL, decision=_decision).observe(_llm_elapsed)
        LLM_CALLS.labels(model=LLM_MODEL, decision=_decision, zone="recovery").inc()

        _arbiter_cache_set(cache_key, should_recover)
        _arbiter_cache_set_redis(cache_key, should_recover)

        logger.debug(
            f"LLM recovery decision: {llm_response} | "
            f"mode={mode} reason={rejection_reason} valor={valor:,.2f}"
        )

        return should_recover

    except Exception as e:
        LLM_CALLS.labels(model=LLM_MODEL, decision="ERROR", zone="recovery").inc()
        logger.error(
            f"LLM recovery FAILED (defaulting to NO RECOVERY): {e} | "
            f"mode={mode} reason={rejection_reason} valor={valor:,.2f}"
        )
        return False


def get_cache_stats() -> dict[str, int]:
    """Get LLM arbiter cache statistics."""
    return {
        "cache_size": len(_arbiter_cache),
        "total_entries": len(_arbiter_cache),
    }


def clear_cache() -> None:
    """Clear the LLM arbiter cache (for testing/debugging)."""
    global _arbiter_cache
    _arbiter_cache = OrderedDict()
    ARBITER_CACHE_SIZE.set(0)
    _search_token_stats.clear()
    _parse_stats.clear()
    logger.info("LLM arbiter cache cleared")
