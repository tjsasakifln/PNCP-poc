"""
LLM Arbiter for False Positive Elimination (STORY-179 AC3) + Zero Match Classification (GTM-FIX-028).

Uses GPT-4.1-nano to classify contracts:
- "uncertain zone" (1-5% term density): PRIMARILY about sector? SIM/NAO
- "zero match" (0% keyword match): Is this contract relevant to sector? YES/NO

Cost: ~R$ 0.00002 per classification (gpt-4.1-nano)
Latency: ~50ms per call
Cache: In-memory MD5-based cache for repeated queries
"""

import hashlib
import logging
import os
from typing import Optional

from openai import OpenAI

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

# In-memory cache for LLM decisions (key = MD5 hash of input)
# TODO: Migrate to Redis in production when volume > 10,000 contracts/day
_arbiter_cache: dict[str, bool] = {}


def _build_conservative_prompt(
    setor_id: Optional[str],
    setor_name: str,
    objeto_truncated: str,
    valor: float,
) -> str:
    """
    Build sector-aware conservative prompt with dynamic examples (STORY-251).

    When setor_id is provided and found in sectors_data.yaml, generates a prompt
    using the sector's description and auto-generated examples from keywords/exclusions.
    Falls back to standard prompt if sector not found.

    Args:
        setor_id: Sector identifier for dynamic lookup (e.g., "vestuario")
        setor_name: Human-readable sector name
        objeto_truncated: Truncated procurement object description
        valor: Total estimated value

    Returns:
        Formatted prompt string for LLM classification
    """
    from sectors import get_sector

    if not setor_id:
        # No sector ID — fall back to standard prompt (no examples)
        return _build_standard_sector_prompt(setor_name, objeto_truncated, valor)

    try:
        config = get_sector(setor_id)
    except (KeyError, Exception):
        # Sector not found — graceful fallback to standard prompt (AC7)
        logger.warning(f"Sector '{setor_id}' not found for conservative prompt, using standard")
        return _build_standard_sector_prompt(setor_name, objeto_truncated, valor)

    description = config.description or setor_name

    # AC5: Generate SIM examples from top keywords (sorted for determinism)
    keywords = sorted(config.keywords)[:3]
    sim_lines = "\n".join(f'- "Aquisição de {kw} para órgão público"' for kw in keywords)

    # AC6/AC9: Generate NAO examples from top exclusions; omit section if none
    exclusions = sorted(config.exclusions)[:3]
    nao_section = ""
    if exclusions:
        nao_lines = "\n".join(f'- "{exc}"' for exc in exclusions)
        nao_section = f"\nNAO:\n{nao_lines}"

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

Este contrato é PRIMARIAMENTE sobre {setor_name}?
Responda APENAS: SIM ou NAO"""


def _build_standard_sector_prompt(
    setor_name: str,
    objeto_truncated: str,
    valor: float,
) -> str:
    """Build standard sector prompt without examples (density 3-8% or fallback)."""
    return f"""Setor: {setor_name}
Valor: R$ {valor:,.2f}
Objeto: {objeto_truncated}

Este contrato é PRIMARIAMENTE sobre {setor_name}?
Responda APENAS: SIM ou NAO"""


def _build_zero_match_prompt(
    setor_id: Optional[str],
    setor_name: str,
    objeto_truncated: str,
    valor: float,
) -> str:
    """
    Build sector-aware prompt for bids with ZERO keyword matches (GTM-FIX-028 AC4).

    These bids had no keyword overlap at all, so we ask the LLM to classify
    purely based on the object description and sector context.

    Includes:
    - Sector name and description
    - Top 5 keywords as YES examples
    - Top 3 exclusions as NO examples
    - Value shown as "Não informado" when 0.0 (PCP v2 has no value data)
    """
    from sectors import get_sector

    valor_display = f"R$ {valor:,.2f}" if valor > 0 else "Não informado"

    if not setor_id:
        return f"""SETOR: {setor_name}

CONTRATO:
Valor: {valor_display}
Objeto: {objeto_truncated}

Este contrato é sobre {setor_name}? Responda APENAS: SIM ou NAO"""

    try:
        config = get_sector(setor_id)
    except (KeyError, Exception):
        logger.warning(f"Sector '{setor_id}' not found for zero_match prompt, using fallback")
        return f"""SETOR: {setor_name}

CONTRATO:
Valor: {valor_display}
Objeto: {objeto_truncated}

Este contrato é sobre {setor_name}? Responda APENAS: SIM ou NAO"""

    description = config.description or setor_name

    # AC4: Top 5 keywords as YES examples
    keywords = sorted(config.keywords)[:5]
    sim_lines = "\n".join(f'- "{kw}"' for kw in keywords)

    # AC4: Top 3 exclusions as NO examples
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

Este contrato é sobre {setor_name}? Responda APENAS: SIM ou NAO"""


def classify_contract_primary_match(
    objeto: str,
    valor: float,
    setor_name: Optional[str] = None,
    termos_busca: Optional[list[str]] = None,
    prompt_level: str = "standard",
    setor_id: Optional[str] = None,
) -> bool:
    """
    Use GPT-4o-mini to determine if contract is PRIMARILY about sector or custom terms.

    This function is called for contracts in the "uncertain zone" (1-5% term density)
    where simple keyword matching is ambiguous. It prevents false positives like:
    - R$ 47.6M "melhorias urbanas" with R$ 50K uniformes (NOT primarily uniformes)
    - R$ 10M software development with "servidor" (server, not public servant)

    Two modes:
    1. **Sector mode** (setor_name provided): "É PRIMARIAMENTE sobre {setor}?"
    2. **Custom terms mode** (termos_busca provided): "Termos descrevem objeto PRINCIPAL?"

    Args:
        objeto: Procurement object description (objetoCompra from PNCP)
        valor: Total estimated value (valorTotalEstimado)
        setor_name: Sector name (e.g., "Vestuário e Uniformes") for sector mode
        termos_busca: List of custom search terms for custom mode

    Returns:
        bool: True if PRIMARILY about sector/terms (SIM), False otherwise (NAO)

    Examples:
        >>> # FALSE POSITIVE - Should return False
        >>> classify_contract_primary_match(
        ...     objeto="MELHORIAS URBANAS incluindo uniformes para agentes",
        ...     valor=47_600_000,
        ...     setor_name="Vestuário e Uniformes"
        ... )
        False

        >>> # LEGITIMATE - Should return True
        >>> classify_contract_primary_match(
        ...     objeto="Uniformes escolares diversos para rede municipal",
        ...     valor=3_000_000,
        ...     setor_name="Vestuário e Uniformes"
        ... )
        True
    """
    # Feature flag check
    if not LLM_ENABLED:
        logger.warning(
            "LLM arbiter disabled (LLM_ARBITER_ENABLED=false). "
            "Accepting ambiguous contract by default."
        )
        return True  # Fallback: accept (legacy behavior)

    # Validate inputs
    if not setor_name and not termos_busca:
        logger.error(
            "classify_contract_primary_match called without setor_name or termos_busca"
        )
        return True  # Conservative: accept if misconfigured

    # Truncate objeto to 500 chars (AC3.7 - save tokens)
    objeto_truncated = objeto[:500]

    # STORY-181 AC3: Determine mode and build prompt (dual-level)
    # GTM-FIX-028 AC4: Added "zero_match" prompt level for bids with 0 keyword matches
    if setor_name:
        mode = "setor"
        context = setor_name

        if prompt_level == "zero_match":
            # GTM-FIX-028: Zero keyword match — sector-aware classification prompt
            user_prompt = _build_zero_match_prompt(
                setor_id=setor_id,
                setor_name=setor_name,
                objeto_truncated=objeto_truncated,
                valor=valor,
            )
        elif prompt_level == "conservative":
            # STORY-251: Dynamic conservative prompt with sector-aware examples
            user_prompt = _build_conservative_prompt(
                setor_id=setor_id,
                setor_name=setor_name,
                objeto_truncated=objeto_truncated,
                valor=valor,
            )
        else:
            # Standard prompt (density 3-8%)
            user_prompt = _build_standard_sector_prompt(
                setor_name=setor_name,
                objeto_truncated=objeto_truncated,
                valor=valor,
            )
    else:
        mode = "termos"
        context = ", ".join(termos_busca) if termos_busca else ""
        user_prompt = f"""Termos buscados: {context}
Valor: R$ {valor:,.2f}
Objeto: {objeto_truncated}

Os termos buscados descrevem o OBJETO PRINCIPAL deste contrato (não itens secundários)?
Responda APENAS: SIM ou NAO"""

    # AC3.5: Check cache (MD5 hash of mode:context:valor:objeto:prompt_level:setor_id)
    cache_key = hashlib.md5(
        f"{mode}:{context}:{valor}:{objeto_truncated}:{prompt_level}:{setor_id or ''}".encode()
    ).hexdigest()

    if cache_key in _arbiter_cache:
        logger.debug(
            f"LLM arbiter cache HIT: mode={mode} "
            f"context={context[:50]}... valor={valor}"
        )
        return _arbiter_cache[cache_key]

    # AC3.6: Fallback on LLM failure
    try:
        # STORY-181 AC3.5: More restrictive system message
        system_prompt = (
            "Você é um classificador conservador de licitações. "
            "Em caso de dúvida, responda NAO. "
            "Apenas responda SIM se o contrato é CLARAMENTE e PRIMARIAMENTE sobre o setor. "
            "Responda APENAS 'SIM' ou 'NAO'."
        )

        response = _get_client().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=LLM_MAX_TOKENS,  # Force single-token response
            temperature=LLM_TEMPERATURE,  # Deterministic
        )

        # Extract response
        llm_response = response.choices[0].message.content.strip().upper()
        is_primary = llm_response == "SIM"

        # Cache the decision
        _arbiter_cache[cache_key] = is_primary

        # HOTFIX 2026-02-10: Enhanced logging with prompt_level for debugging
        logger.info(
            f"LLM arbiter decision: {llm_response} | "
            f"mode={mode} prompt_level={prompt_level} "
            f"context={context[:50]}... valor=R${valor:,.2f}"
        )

        return is_primary

    except Exception as e:
        logger.error(
            f"LLM arbiter FAILED (defaulting to REJECT): {e} | "
            f"mode={mode} context={context[:50]}... valor={valor:,.2f}"
        )
        # AC3.6: Conservative fallback - REJECT if uncertain
        # Better to reject 1 ambiguous contract than approve 1 catastrophic false positive
        return False


def classify_contract_recovery(
    objeto: str,
    valor: float,
    rejection_reason: str,
    setor_name: Optional[str] = None,
    termos_busca: Optional[list[str]] = None,
    near_miss_info: Optional[str] = None,
) -> bool:
    """
    Use LLM to determine if a REJECTED contract should be RECOVERED (STORY-179 AC13).

    This function is called for contracts rejected by exclusion keywords or that
    had near-miss synonym matches. It prevents false negatives like:
    - "Servidor de rede" rejected by "servidor público" exclusion (should recover - is TI)
    - "Manutenção predial" rejected by "obra" exclusion (should recover - is facilities)

    Args:
        objeto: Procurement object description
        valor: Total estimated value
        rejection_reason: Why it was rejected ("exclusion", "synonym_near_miss", etc.)
        setor_name: Sector name for sector mode
        termos_busca: Custom search terms for custom mode
        near_miss_info: Info about near-miss synonyms if applicable

    Returns:
        bool: True if should be RECOVERED (relevant despite rejection), False otherwise

    Examples:
        >>> # Should RECOVER - IT equipment, not public servant
        >>> classify_contract_recovery(
        ...     objeto="Servidor de rede para secretaria de TI",
        ...     valor=500_000,
        ...     rejection_reason="exclusion: servidor público",
        ...     setor_name="Informática e Tecnologia"
        ... )
        True

        >>> # Should NOT recover - actually about public servants
        >>> classify_contract_recovery(
        ...     objeto="Capacitação de servidores públicos municipais",
        ...     valor=100_000,
        ...     rejection_reason="exclusion: servidor público",
        ...     setor_name="Informática e Tecnologia"
        ... )
        False
    """
    # Feature flag check
    if not LLM_ENABLED:
        logger.warning(
            "LLM arbiter disabled (LLM_ARBITER_ENABLED=false). "
            "Not recovering rejected contract."
        )
        return False  # Don't recover if LLM disabled

    # Validate inputs
    if not setor_name and not termos_busca:
        logger.error(
            "classify_contract_recovery called without setor_name or termos_busca"
        )
        return False  # Don't recover if misconfigured

    # Truncate objeto to 500 chars
    objeto_truncated = objeto[:500]

    # Build recovery prompt
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

    # Check cache
    cache_key = hashlib.md5(
        f"{mode}:{context}:{valor}:{objeto_truncated}:{rejection_reason}".encode()
    ).hexdigest()

    if cache_key in _arbiter_cache:
        logger.debug(
            f"LLM recovery cache HIT: mode={mode} "
            f"reason={rejection_reason} valor={valor}"
        )
        return _arbiter_cache[cache_key]

    # Call LLM
    try:
        system_prompt = (
            "Você é um classificador de licitações que avalia se contratos rejeitados "
            "automaticamente são relevantes. Responda APENAS 'SIM' ou 'NAO'."
        )

        response = _get_client().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
        )

        llm_response = response.choices[0].message.content.strip().upper()
        should_recover = llm_response == "SIM"

        # Cache decision
        _arbiter_cache[cache_key] = should_recover

        logger.debug(
            f"LLM recovery decision: {llm_response} | "
            f"mode={mode} reason={rejection_reason} valor={valor:,.2f}"
        )

        return should_recover

    except Exception as e:
        logger.error(
            f"LLM recovery FAILED (defaulting to NO RECOVERY): {e} | "
            f"mode={mode} reason={rejection_reason} valor={valor:,.2f}"
        )
        # Conservative: don't recover if LLM fails
        return False


def get_cache_stats() -> dict[str, int]:
    """
    Get LLM arbiter cache statistics.

    Returns:
        dict: {"cache_size": int, "total_entries": int}
    """
    return {
        "cache_size": len(_arbiter_cache),
        "total_entries": len(_arbiter_cache),
    }


def clear_cache() -> None:
    """Clear the LLM arbiter cache (for testing/debugging)."""
    global _arbiter_cache
    _arbiter_cache = {}
    logger.info("LLM arbiter cache cleared")
