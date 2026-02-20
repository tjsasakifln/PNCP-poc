"""
LLM Arbiter for False Positive Elimination (STORY-179 AC3) + Zero Match Classification (GTM-FIX-028).
GTM-RESILIENCE-D02: Structured output with confidence, evidence, and re-ranking support.

Uses GPT-4.1-nano to classify contracts:
- "uncertain zone" (1-5% term density): PRIMARILY about sector? SIM/NAO
- "zero match" (0% keyword match): Is this contract relevant to sector? YES/NO

D-02: When LLM_STRUCTURED_OUTPUT_ENABLED=true, returns JSON with:
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
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from openai import OpenAI
from metrics import LLM_CALLS, LLM_DURATION

# Configure logging
logger = logging.getLogger(__name__)

# OpenAI client (initialized lazily to avoid import-time errors in tests)
_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """Get or initialize OpenAI client (lazy initialization)."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


# LLM configuration
# GTM-FIX-028 AC5: Migrated default from gpt-4o-mini to gpt-4.1-nano (33% cheaper)
LLM_MODEL = os.getenv("LLM_ARBITER_MODEL", "gpt-4.1-nano")
LLM_MAX_TOKENS = int(os.getenv("LLM_ARBITER_MAX_TOKENS", "1"))
LLM_TEMPERATURE = float(os.getenv("LLM_ARBITER_TEMPERATURE", "0"))
LLM_ENABLED = os.getenv("LLM_ARBITER_ENABLED", "true").lower() == "true"

# D-02: Structured output max tokens (accommodates JSON + evidence)
LLM_STRUCTURED_MAX_TOKENS = 150

# D-02 AC9: gpt-4.1-nano pricing (per million tokens)
_PRICING_INPUT_PER_M = 0.10   # USD per 1M input tokens
_PRICING_OUTPUT_PER_M = 0.40  # USD per 1M output tokens
_USD_TO_BRL = 5.0  # approximate

# In-memory cache for LLM decisions (key = MD5 hash of input)
# D-02 AC8: Cache value is now dict (structured) or bool (legacy), keyed with prompt version
_arbiter_cache: dict[str, Any] = {}


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
    evidencias: list[str] = Field(default_factory=list, max_length=3)
    motivo_exclusao: Optional[str] = Field(default=None, max_length=200)
    precisa_mais_dados: bool = False


# ============================================================================
# D-02 AC9: Cost tracking (per-search aggregation)
# ============================================================================

_search_token_stats: dict[str, dict] = {}


def _log_token_usage(
    search_id: str,
    input_tokens: int,
    output_tokens: int,
) -> None:
    """Track token usage per search for cost monitoring (AC9)."""
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
    cost_brl = cost_usd * _USD_TO_BRL
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

_STRUCTURED_JSON_INSTRUCTION = """
Responda em JSON com a estrutura exata:
{"classe": "SIM" ou "NAO", "confianca": 0-100, "evidencias": ["citação 1", "citação 2"], "motivo_exclusao": "razão se NAO", "precisa_mais_dados": false}

REGRAS:
- evidencias: CITAÇÕES LITERAIS do texto do Objeto (copie trechos exatos, não parafraseie), máximo 3, máx 100 chars cada
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

    return f"""Você é um classificador de licitações públicas. Analise se o contrato é PRIMARIAMENTE sobre o setor especificado (> 80% do valor e escopo).

SETOR: {setor_name}
DESCRIÇÃO DO SETOR: {description}

CONTRATO:
Valor: R$ {valor:,.2f}
Objeto: {objeto_truncated}

EXEMPLOS DE CLASSIFICAÇÃO:

SIM:
{sim_lines}
{nao_section}

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

    return f"""Você classifica licitações públicas. Este contrato NÃO contém palavras-chave do setor — analise o OBJETO para determinar se é relevante.

SETOR: {setor_name}
DESCRIÇÃO: {description}

Exemplos de SIM (é sobre o setor):
{sim_lines}
{nao_section}

CONTRATO:
Valor: {valor_display}
Objeto: {objeto_truncated}

Este contrato é sobre {setor_name}?{suffix}"""


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

        # AC6: Validate evidence as literal substrings of objeto
        objeto_lower = objeto.lower()
        validated_evidence = []
        for ev in classification.evidencias:
            if ev and len(ev) <= 100:
                if ev.lower() in objeto_lower:
                    validated_evidence.append(ev)
                else:
                    logger.warning(
                        f"D-02 AC6: Discarding hallucinated evidence (not substring): "
                        f"evidence={ev!r} not found in objeto"
                    )
            elif ev and len(ev) > 100:
                # Truncate to 100 chars and re-validate
                truncated = ev[:100]
                if truncated.lower() in objeto_lower:
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

    D-02: Returns structured dict instead of bool when LLM_STRUCTURED_OUTPUT_ENABLED=true.
    When disabled, returns legacy-compatible dict with confidence=100/0.

    Returns:
        dict with keys:
            is_primary (bool): True if SIM
            confidence (int): 0-100
            evidence (list[str]): Literal text excerpts from objeto
            rejection_reason (str|None): Reason when NAO
            needs_more_data (bool): True when description insufficient
    """
    from config import get_feature_flag

    # CRIT-004 AC13: Include search_id in classification logs for correlation
    from middleware import search_id_var
    _search_id = search_id_var.get("-")

    structured_enabled = get_feature_flag("LLM_STRUCTURED_OUTPUT_ENABLED")

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

    if cache_key in _arbiter_cache:
        logger.debug(
            f"LLM arbiter cache HIT: mode={mode} "
            f"context={context[:50]}... valor={valor}"
        )
        return _arbiter_cache[cache_key]

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

        # Cache the result
        _arbiter_cache[cache_key] = result

        logger.info(
            f"LLM arbiter decision: {_decision} conf={result['confidence']}% | "
            f"search={_search_id} mode={mode} prompt_level={prompt_level} structured={structured_enabled} "
            f"context={context[:50]}... valor=R${valor:,.2f}"
        )

        return result

    except Exception as e:
        LLM_CALLS.labels(model=LLM_MODEL, decision="ERROR", zone=prompt_level).inc()
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

    if cache_key in _arbiter_cache:
        cached = _arbiter_cache[cache_key]
        # Handle both dict (new) and bool (legacy) cache entries
        if isinstance(cached, dict):
            return cached.get("is_primary", False)
        return cached

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

        _arbiter_cache[cache_key] = should_recover

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
    _arbiter_cache = {}
    _search_token_stats.clear()
    _parse_stats.clear()
    logger.info("LLM arbiter cache cleared")
