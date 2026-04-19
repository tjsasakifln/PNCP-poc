"""Core LLM classification logic, cache, and cost tracking.

TD-009: Extracted from llm_arbiter.py as part of DEBT-07 module split.
Contains the OpenAI client, in-memory/Redis cache, LLMClassification model,
parsing helpers, and the main classify_contract_primary_match() function.
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
    LLM_FALLBACK_REJECTS_TOTAL,
)

logger = logging.getLogger(__name__)

# HARDEN-001 / DEBT-103 AC1: OpenAI client timeout
from config.features import LLM_TIMEOUT_S as _LLM_TIMEOUT

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
LLM_MODEL = os.getenv("LLM_ARBITER_MODEL", "gpt-4.1-nano")
LLM_MAX_TOKENS = int(os.getenv("LLM_ARBITER_MAX_TOKENS", "1"))
LLM_TEMPERATURE = float(os.getenv("LLM_ARBITER_TEMPERATURE", "0"))
LLM_ENABLED = os.getenv("LLM_ARBITER_ENABLED", "true").lower() == "true"

# D-02 AC5: Structured output max tokens
LLM_STRUCTURED_MAX_TOKENS = int(os.getenv("LLM_STRUCTURED_MAX_TOKENS", "800"))

# D-02 AC9: gpt-4.1-nano pricing (per million tokens)
_PRICING_INPUT_PER_M = 0.10
_PRICING_OUTPUT_PER_M = 0.40


def _get_usd_to_brl() -> float:
    """Lazy import to avoid circular dependency with config at module level."""
    from config import USD_TO_BRL_RATE
    return USD_TO_BRL_RATE


# In-memory L1 cache for LLM decisions (key = MD5 hash of input)
# HARDEN-009 / DEBT-103 AC3: LRU eviction with configurable size limit
_ARBITER_CACHE_MAX = int(os.getenv("LRU_MAX_SIZE", "5000"))
_arbiter_cache: OrderedDict[str, Any] = OrderedDict()
_ARBITER_REDIS_PREFIX = "smartlic:arbiter:"


def _arbiter_cache_set(key: str, value: Any) -> None:
    """HARDEN-009 / DEBT-103 AC4: Set cache entry with LRU eviction + metrics."""
    _arbiter_cache[key] = value
    _arbiter_cache.move_to_end(key)
    # Lazy import via facade so tests can override _ARBITER_CACHE_MAX on llm_arbiter (AC2)
    import llm_arbiter as _lm
    while len(_arbiter_cache) > _lm._ARBITER_CACHE_MAX:
        _arbiter_cache.popitem(last=False)
        ARBITER_CACHE_EVICTIONS.inc()
    ARBITER_CACHE_SIZE.set(len(_arbiter_cache))


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
    """D-02 AC1: Structured classification result from LLM arbiter."""
    classe: Literal["SIM", "NAO"]
    confianca: int = Field(ge=0, le=100)
    evidencias: list[str] = Field(default_factory=list)
    motivo_exclusao: Optional[str] = Field(default=None)
    precisa_mais_dados: bool = False

    @field_validator("evidencias", mode="before")
    @classmethod
    def _cap_evidencias(cls, v: list[str]) -> list[str]:
        if isinstance(v, list) and len(v) > 3:
            return v[:3]
        return v

    @field_validator("motivo_exclusao", mode="before")
    @classmethod
    def _cap_motivo(cls, v: str | None) -> str | None:
        if isinstance(v, str) and len(v) > 500:
            return v[:497] + "..."
        return v


# ============================================================================
# D-02 AC9: Cost tracking (per-search aggregation)
# ============================================================================

_search_token_stats: dict[str, dict] = {}

# DEBT-v3-S2 AC4: Rolling window cost tracker for hourly alert
_hourly_cost_usd: list[tuple[float, float]] = []  # [(timestamp, cost_usd), ...]
_COST_WINDOW_S = 3600  # 1 hour
_cost_alert_fired = False


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

    cost_usd = (
        input_tokens * _PRICING_INPUT_PER_M / 1_000_000
        + output_tokens * _PRICING_OUTPUT_PER_M / 1_000_000
    )
    cost_brl = cost_usd * _get_usd_to_brl()
    try:
        from metrics import LLM_COST_BRL, LLM_COST_USD, LLM_TOKENS_DETAILED
        LLM_COST_BRL.labels(model=LLM_MODEL, call_type=call_type).inc(cost_brl)
        LLM_COST_USD.labels(model=LLM_MODEL, operation=call_type).inc(cost_usd)
        LLM_TOKENS_DETAILED.labels(model=LLM_MODEL, operation=call_type, direction="input").inc(input_tokens)
        LLM_TOKENS_DETAILED.labels(model=LLM_MODEL, operation=call_type, direction="output").inc(output_tokens)
    except Exception:
        pass

    # STORY-2.11 (EPIC-TD-2026Q2 P0): Track monthly cumulative cost for budget cap.
    # classify_contract_primary_match roda em ``asyncio.to_thread``; disparamos o
    # async track via ensure_future se houver loop rodando, senão contamos skip.
    # CIG-BE-asyncio-run-production-scan Phase 2 Option C:
    # thread pool worker without running loop — skip and count, not spin a new
    # loop (long-term Option A = run_coroutine_threadsafe on main app loop).
    try:
        import asyncio as _asyncio
        from llm_budget import track_llm_cost as _track

        try:
            _loop = _asyncio.get_running_loop()
            _asyncio.ensure_future(_track(cost_usd))
        except RuntimeError:
            from metrics import LLM_BUDGET_TRACK_SKIPPED as _skipped

            _skipped.labels(reason="no_running_loop").inc()
    except Exception:
        pass

    try:
        global _cost_alert_fired
        now = _time_module.time()
        _hourly_cost_usd.append((now, cost_usd))
        cutoff = now - _COST_WINDOW_S
        while _hourly_cost_usd and _hourly_cost_usd[0][0] < cutoff:
            _hourly_cost_usd.pop(0)
        hourly_total = sum(c for _, c in _hourly_cost_usd)
        from config.features import LLM_COST_ALERT_THRESHOLD
        if hourly_total > LLM_COST_ALERT_THRESHOLD:
            if not _cost_alert_fired:
                _cost_alert_fired = True
                logger.warning(
                    f"DEBT-v3-S2 AC4: LLM cost alert — ${hourly_total:.4f}/hour "
                    f"exceeds threshold ${LLM_COST_ALERT_THRESHOLD:.2f}/hour"
                )
        else:
            _cost_alert_fired = False
    except Exception:
        pass


def get_search_cost_stats(search_id: str) -> dict:
    """Get token usage and estimated cost for a search (AC9)."""
    stats = _search_token_stats.pop(search_id, {
        "llm_tokens_input": 0, "llm_tokens_output": 0, "llm_calls": 0,
    })
    cost_usd = (
        stats["llm_tokens_input"] * _PRICING_INPUT_PER_M / 1_000_000
        + stats["llm_tokens_output"] * _PRICING_OUTPUT_PER_M / 1_000_000
    )
    cost_brl = cost_usd * _get_usd_to_brl()
    stats["llm_cost_estimated_brl"] = round(cost_brl, 6)

    if cost_brl > 0.10:
        logger.warning(
            f"D-02 AC9: High LLM cost for search {search_id}: "
            f"R$ {cost_brl:.4f} ({stats['llm_calls']} calls, "
            f"{stats['llm_tokens_input']}in/{stats['llm_tokens_output']}out tokens)"
        )

    return stats


# ============================================================================
# CRIT-035: Strip LLM-added field-name prefixes from evidence
# ============================================================================

_KNOWN_PREFIXES = ["objeto:", "descrição:", "descricao:", "título:", "titulo:", "title:", "description:"]


def _strip_evidence_prefix(evidence: str) -> tuple[str, bool]:
    """Strip common field-name prefixes that GPT adds to evidence (CRIT-035)."""
    ev_lower = evidence.strip().lower()
    for prefix in _KNOWN_PREFIXES:
        if ev_lower.startswith(prefix):
            stripped = evidence.strip()[len(prefix):].strip()
            if stripped:
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

_parse_stats: dict[str, dict] = {}


def _parse_structured_response(
    raw_content: str,
    objeto: str,
    search_id: str = "",
) -> LLMClassification:
    """Parse LLM JSON response into LLMClassification with robust fallback (AC3)."""
    if search_id:
        if search_id not in _parse_stats:
            _parse_stats[search_id] = {"attempts": 0, "json_success": 0, "fallback": 0}
        _parse_stats[search_id]["attempts"] += 1

    try:
        data = json.loads(raw_content.strip())
        classification = LLMClassification.model_validate(data)

        from filter import normalize_text as _normalize
        objeto_normalized = _normalize(objeto)
        validated_evidence = []
        for ev in classification.evidencias:
            if ev and len(ev) <= 100:
                if _normalize(ev) in objeto_normalized:
                    validated_evidence.append(ev)
                else:
                    stripped_ev, was_stripped = _strip_evidence_prefix(ev)
                    if was_stripped and _normalize(stripped_ev) in objeto_normalized:
                        validated_evidence.append(stripped_ev)
                    else:
                        logger.warning(
                            f"D-02 AC6: Discarding hallucinated evidence (not substring): "
                            f"evidence={ev!r} not found in objeto"
                        )
            elif ev and len(ev) > 100:
                truncated = ev[:100]
                if _normalize(truncated) in objeto_normalized:
                    validated_evidence.append(truncated)

        classification.evidencias = validated_evidence

        if search_id:
            _parse_stats[search_id]["json_success"] += 1

        return classification

    except (json.JSONDecodeError, Exception) as e:
        logger.warning(
            f"D-02 AC3: JSON parse failed, using text fallback: {e} | "
            f"raw={raw_content[:200]!r}"
        )

        if search_id:
            _parse_stats[search_id]["fallback"] += 1

        raw_upper = raw_content.strip().upper()
        has_sim = "SIM" in raw_upper
        has_nao = "NAO" in raw_upper or "NÃO" in raw_content.strip().upper()
        if has_sim and not has_nao:
            return LLMClassification(
                classe="SIM", confianca=45, evidencias=[],
                motivo_exclusao=None, precisa_mais_dados=False,
            )
        else:
            return LLMClassification(
                classe="NAO", confianca=40, evidencias=[],
                motivo_exclusao="Fallback: LLM returned non-JSON response or ambiguous SIM/NAO",
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
    """
    from middleware import search_id_var
    _search_id = search_id_var.get("-")

    structured_enabled = True

    # Lazy import via facade so patch("llm_arbiter.LLM_ENABLED", False) works in tests (AC2)
    import llm_arbiter as _lm
    if not _lm.LLM_ENABLED:
        logger.warning(
            "LLM arbiter disabled (LLM_ARBITER_ENABLED=false). "
            "Accepting ambiguous contract by default."
        )
        return {"is_primary": True, "confidence": 50, "evidence": [],
                "rejection_reason": None, "needs_more_data": False}

    if not setor_name and not termos_busca:
        logger.error(
            "classify_contract_primary_match called without setor_name or termos_busca"
        )
        return {"is_primary": True, "confidence": 50, "evidence": [],
                "rejection_reason": None, "needs_more_data": False}

    objeto_truncated = objeto[:500]

    from llm_arbiter.prompt_builder import (
        _build_zero_match_prompt,
        _build_conservative_prompt,
        _build_standard_sector_prompt,
    )

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
        from llm_arbiter.prompt_builder import _STRUCTURED_JSON_INSTRUCTION
        suffix = _STRUCTURED_JSON_INSTRUCTION if structured_enabled else "\nResponda APENAS: SIM ou NAO"
        user_prompt = f"""Termos buscados: {context}
Valor: R$ {valor:,.2f}
Objeto: {objeto_truncated}

Os termos buscados descrevem o OBJETO PRINCIPAL deste contrato (não itens secundários)?{suffix}"""

    prompt_version = "v2" if structured_enabled else "v1"
    cache_key = hashlib.md5(
        f"{prompt_version}:{mode}:{context}:{valor}:{objeto_truncated}:{prompt_level}:{setor_id or ''}".encode()
    ).hexdigest()

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

    # STORY-2.11 (EPIC-TD-2026Q2 P0): Budget cap — se o teto mensal foi atingido,
    # curto-circuita antes de chamar a OpenAI. Retorna PENDING_REVIEW (gray zone),
    # evitando hard-reject silencioso em caso de burst de custo.
    try:
        from llm_budget import is_budget_exceeded_sync

        if is_budget_exceeded_sync():
            logger.warning(
                f"STORY-2.11: LLM monthly budget exceeded — returning PENDING_REVIEW | "
                f"search={_search_id} mode={mode} prompt_level={prompt_level}"
            )
            try:
                from metrics import LLM_BUDGET_REJECTIONS
                LLM_BUDGET_REJECTIONS.labels(caller="arbiter").inc()
            except Exception:
                pass
            return {
                "is_primary": False,
                "confidence": 0,
                "evidence": [],
                "rejection_reason": "llm_budget_exceeded",
                "needs_more_data": False,
                "pending_review": True,
                "_classification_source": "budget_cap",
            }
    except Exception:
        # Nunca bloqueia por erro em budget check
        pass

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
        if structured_enabled:
            api_kwargs["response_format"] = {"type": "json_object"}

        _llm_start = _time_module.time()
        # Lazy import via facade so patch("llm_arbiter._get_client") works in tests (AC2)
        import llm_arbiter as _lm
        response = _lm._get_client().chat.completions.create(**api_kwargs)
        _llm_elapsed = _time_module.time() - _llm_start

        raw_content = response.choices[0].message.content.strip()

        usage = getattr(response, "usage", None)
        if usage and search_id:
            _log_token_usage(
                search_id,
                input_tokens=getattr(usage, "prompt_tokens", 0),
                output_tokens=getattr(usage, "completion_tokens", 0),
            )

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
            llm_response = raw_content.upper()
            is_primary = llm_response == "SIM"
            result = {
                "is_primary": is_primary,
                "confidence": 100 if is_primary else 0,
                "evidence": [],
                "rejection_reason": None,
                "needs_more_data": False,
            }

        _decision = "SIM" if is_primary else "NAO"
        LLM_DURATION.labels(model=LLM_MODEL, decision=_decision).observe(_llm_elapsed)
        LLM_CALLS.labels(model=LLM_MODEL, decision=_decision, zone=prompt_level).inc()

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

        from config import LLM_FALLBACK_PENDING_ENABLED
        _gray_zone_levels = {"zero_match", "standard", "conservative"}
        if LLM_FALLBACK_PENDING_ENABLED and prompt_level in _gray_zone_levels:
            logger.warning(
                f"LLM arbiter FAILED (PENDING_REVIEW fallback): {e} | "
                f"search={_search_id} mode={mode} prompt_level={prompt_level} "
                f"context={context[:50]}... valor={valor:,.2f}"
            )
            from metrics import LLM_FALLBACK_PENDING
            _sector_label = context[:50] if mode == "setor" else "termos"
            _reason = type(e).__name__
            LLM_FALLBACK_PENDING.labels(sector=_sector_label, reason=_reason).inc()
            _pending_confidence = 40 if prompt_level in {"standard", "conservative"} else 0
            result = {
                "is_primary": False,
                "confidence": _pending_confidence,
                "evidence": [],
                "rejection_reason": "LLM unavailable",
                "needs_more_data": False,
                "pending_review": True,
                "_classification_source": "llm_fallback_pending",
            }
            return result

        logger.error(
            f"LLM arbiter FAILED (defaulting to REJECT): {e} | "
            f"search={_search_id} mode={mode} context={context[:50]}... valor={valor:,.2f}"
        )
        try:
            _setor_label = setor_id or "unknown"
            _reason = type(e).__name__
            LLM_FALLBACK_REJECTS_TOTAL.labels(setor=_setor_label, reason=_reason).inc()
        except Exception:
            pass
        result = {
            "is_primary": False,
            "confidence": 0,
            "evidence": [],
            "rejection_reason": "LLM unavailable",
            "needs_more_data": False,
        }
        return result


# ============================================================================
# Cache management
# ============================================================================

def get_cache_stats() -> dict[str, int]:
    """Get LLM arbiter cache statistics."""
    return {
        "cache_size": len(_arbiter_cache),
        "total_entries": len(_arbiter_cache),
    }


def clear_cache() -> None:
    """Clear the LLM arbiter cache (for testing/debugging)."""
    # Use .clear() to preserve the shared object reference (facade re-exports same dict)
    _arbiter_cache.clear()
    ARBITER_CACHE_SIZE.set(0)
    _search_token_stats.clear()
    _parse_stats.clear()
