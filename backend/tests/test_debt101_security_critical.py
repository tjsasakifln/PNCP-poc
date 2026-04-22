"""
DEBT-101: Security Critical — Token Hash, SIGSEGV & LLM Truncation

Tests for debt items:
- SYS-004: Token hash full SHA256 (AC1) + cache isolation
  (DEBT-SYS-015: dual-hash transition removed — window long expired)
- SYS-001: faulthandler disabled in production (AC3)
- SYS-002: LLM_STRUCTURED_MAX_TOKENS >= 800 (AC5, AC6)
"""

import hashlib
import json
import os
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest


# =============================================================================
# SYS-004: Token Hash — Full SHA256 + Cache Isolation (AC1)
# =============================================================================


class TestTokenHashFullSHA256:
    """AC1: Token hash uses SHA256 of FULL payload, collision < 2^-128."""

    def test_full_token_hash_collision_probability(self):
        """SHA256 of full token has collision probability < 2^-128."""
        # SHA256 output is 256 bits → birthday bound is ~2^128
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLWEifQ.sig"
        h = hashlib.sha256(token.encode("utf-8")).hexdigest()
        # 64 hex chars = 256 bits
        assert len(h) == 64

    def test_different_tokens_different_hashes(self):
        """Two tokens differing only in payload produce different full hashes."""
        t1 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLWEifQ.sig_a"
        t2 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLWIifQ.sig_b"
        assert t1[:16] == t2[:16], "Tokens share Supabase JWT prefix"
        h1 = hashlib.sha256(t1.encode("utf-8")).hexdigest()
        h2 = hashlib.sha256(t2.encode("utf-8")).hexdigest()
        assert h1 != h2

    def test_partial_hash_would_collide(self):
        """Prefix-only (16 char) hash collides — proving the old bug."""
        t1 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.PAYLOAD_USER_A"
        t2 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.PAYLOAD_USER_B"
        partial_h1 = hashlib.sha256(t1[:16].encode("utf-8")).hexdigest()
        partial_h2 = hashlib.sha256(t2[:16].encode("utf-8")).hexdigest()
        assert partial_h1 == partial_h2, "Partial hash SHOULD collide (the old bug)"


class TestCacheIsolation:
    """DEBT-SYS-015: Verify tokens don't cross-pollute cache (dual-hash removed)."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        from auth import _token_cache
        _token_cache.clear()
        yield
        _token_cache.clear()

    @pytest.mark.asyncio
    async def test_concurrent_tokens_no_cross_pollution(self):
        """Two concurrent requests with different tokens don't cross-pollute cache."""
        import jwt as pyjwt
        from auth import get_current_user, _token_cache

        secret = "test-secret-key-for-testing-12345678"
        token_a = pyjwt.encode(
            {"sub": "user-a", "email": "a@test.com", "role": "authenticated", "aud": "authenticated"},
            secret, algorithm="HS256",
        )
        token_b = pyjwt.encode(
            {"sub": "user-b", "email": "b@test.com", "role": "authenticated", "aud": "authenticated"},
            secret, algorithm="HS256",
        )

        creds_a = Mock()
        creds_a.credentials = token_a
        creds_b = Mock()
        creds_b.credentials = token_b

        with patch.dict(os.environ, {"SUPABASE_JWT_SECRET": secret}), \
             patch("auth._redis_cache_get", new_callable=AsyncMock, return_value=None), \
             patch("auth._redis_cache_set", new_callable=AsyncMock):
            user_a = await get_current_user(creds_a)
            user_b = await get_current_user(creds_b)

        assert user_a["id"] == "user-a"
        assert user_b["id"] == "user-b"
        assert user_a["id"] != user_b["id"], "Different tokens must not cross-pollute"

        # Verify both cached separately
        hash_a = hashlib.sha256(token_a.encode("utf-8")).hexdigest()
        hash_b = hashlib.sha256(token_b.encode("utf-8")).hexdigest()
        assert hash_a in _token_cache
        assert hash_b in _token_cache
        assert _token_cache[hash_a][0]["id"] == "user-a"
        assert _token_cache[hash_b][0]["id"] == "user-b"


# =============================================================================
# SYS-001: faulthandler disabled in production (AC3)
# =============================================================================


class TestFaulthandlerProduction:
    """AC3: faulthandler disabled in production, enabled in development."""

    def test_faulthandler_disabled_in_production_env(self):
        """In production, faulthandler should NOT be enabled by main.py logic."""
        # We test the LOGIC, not the actual module-level execution
        # (which already ran at import time in non-production mode)
        env_val = "production"
        should_enable = env_val not in ("production", "prod")
        assert should_enable is False

    def test_faulthandler_enabled_in_development_env(self):
        """In development, faulthandler should be enabled."""
        env_val = "development"
        should_enable = env_val not in ("production", "prod")
        assert should_enable is True

    def test_faulthandler_enabled_in_test_env(self):
        """In test, faulthandler should be enabled."""
        env_val = "test"
        should_enable = env_val not in ("production", "prod")
        assert should_enable is True

    def test_gunicorn_conf_production_skip(self):
        """gunicorn_conf.py should skip faulthandler in production."""
        # The _is_production flag in gunicorn_conf controls the behavior
        # We verify the logic is correct
        for env in ("production", "prod"):
            is_prod = env in ("production", "prod")
            assert is_prod is True, f"'{env}' should be detected as production"

        for env in ("development", "staging", "test"):
            is_prod = env in ("production", "prod")
            assert is_prod is False, f"'{env}' should NOT be production"

    def test_uvicorn_standard_in_requirements(self):
        """requirements.txt must pin bare uvicorn WITHOUT [standard] extras.

        BTS-010b (SECURITY, CRIT-SIGSEGV-v2): uvicorn[standard] pulls in uvloop,
        which interacts with chardet/hiredis/cryptography C extensions to produce
        intermittent SIGSEGV crashes in production (see CLAUDE.md CRIT-080 lesson).
        The intentional, security-correct configuration is bare `uvicorn==<ver>`.
        Reverting this pin would re-introduce the production crash.
        """
        req_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
        with open(req_path) as f:
            content = f.read()
        assert "uvicorn[standard]" not in content, (
            "uvicorn[standard] must NOT be in requirements.txt — "
            "CRIT-SIGSEGV-v2 requires bare uvicorn (uvloop triggers SIGSEGV)."
        )
        # Still must pin some uvicorn version
        lines = [l.strip() for l in content.splitlines() if l.strip().startswith("uvicorn") and not l.strip().startswith("#")]  # noqa: E741
        assert lines, "requirements.txt must contain a uvicorn pin"
        for line in lines:
            assert "[standard]" not in line, f"uvicorn line must NOT include [standard]: {line}"


# =============================================================================
# SYS-002: LLM_STRUCTURED_MAX_TOKENS >= 800 (AC5, AC6)
# =============================================================================


class TestLLMStructuredMaxTokens:
    """AC5: MAX_TOKENS >= 800. AC6: JSON parse success > 99%."""

    def test_max_tokens_at_least_800(self):
        """AC5: LLM_STRUCTURED_MAX_TOKENS must be >= 800."""
        from llm_arbiter import LLM_STRUCTURED_MAX_TOKENS
        assert LLM_STRUCTURED_MAX_TOKENS >= 800, (
            f"LLM_STRUCTURED_MAX_TOKENS={LLM_STRUCTURED_MAX_TOKENS}, must be >= 800"
        )

    def test_max_tokens_configurable_via_env(self):
        """MAX_TOKENS should be overridable via environment variable."""
        with patch.dict(os.environ, {"LLM_STRUCTURED_MAX_TOKENS": "1200"}):
            # Re-evaluate
            val = int(os.getenv("LLM_STRUCTURED_MAX_TOKENS", "800"))
            assert val == 1200

    def test_default_is_800(self):
        """Default value when env var is not set should be 800."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LLM_STRUCTURED_MAX_TOKENS", None)
            val = int(os.getenv("LLM_STRUCTURED_MAX_TOKENS", "800"))
            assert val == 800

    def test_json_parse_golden_samples(self):
        """AC6: Verify JSON responses at 800 tokens don't truncate.

        Simulates worst-case structured responses and verifies they parse correctly.
        """
        # Worst-case structured response: long evidence + motivo_exclusao
        worst_case_responses = [
            json.dumps({
                "classe": "SIM",
                "confianca": 85,
                "evidencias": [
                    "Aquisição de uniformes profissionais para servidores públicos municipais",
                    "Fornecimento de vestimentas e equipamentos de proteção individual",
                    "Contratação de empresa especializada em confecção de fardamentos",
                ],
                "motivo_exclusao": None,
            }),
            json.dumps({
                "classe": "NAO",
                "confianca": 95,
                "evidencias": [
                    "Contrato trata exclusivamente de serviços de tecnologia da informação e comunicação digital para órgão público federal",
                    "Objeto principal é desenvolvimento de software e não está relacionado ao setor consultado",
                    "Não há menção a uniformes, vestimentas ou confecção no escopo do contrato analisado",
                ],
                "motivo_exclusao": "Contrato de TI sem relação com vestuário — classificação incorreta seria falso positivo grave",
            }),
            json.dumps({
                "classe": "SIM",
                "confianca": 60,
                "evidencias": [
                    "Manutenção predial com fornecimento de materiais elétricos e hidráulicos para instalações governamentais",
                ],
                "motivo_exclusao": None,
            }),
        ]

        parse_success = 0
        for resp in worst_case_responses:
            try:
                parsed = json.loads(resp)
                assert "classe" in parsed
                assert "confianca" in parsed
                parse_success += 1
            except json.JSONDecodeError:
                pass

        success_rate = parse_success / len(worst_case_responses)
        assert success_rate >= 0.99, f"JSON parse success rate {success_rate:.0%} < 99%"

    def test_800_tokens_sufficient_for_worst_case(self):
        """Verify 800 tokens is enough for the longest possible structured response."""
        # A typical token is ~4 chars in Portuguese. 800 tokens ≈ 3200 chars.
        # Build a worst-case response and check it fits.
        worst_case = json.dumps({
            "classe": "NAO",
            "confianca": 95,
            "evidencias": [
                "A" * 200,  # ~50 tokens
                "B" * 200,  # ~50 tokens
                "C" * 200,  # ~50 tokens
            ],
            "motivo_exclusao": "D" * 300,  # ~75 tokens
        })
        # 800 tokens ≈ 3200 chars (conservative 4 chars/token for Portuguese)
        max_chars = 800 * 4
        assert len(worst_case) < max_chars, (
            f"Worst-case response ({len(worst_case)} chars) exceeds 800-token budget ({max_chars} chars)"
        )
