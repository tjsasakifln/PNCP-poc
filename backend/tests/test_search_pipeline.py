"""Unit tests for SearchPipeline stages 1-2 (validate and prepare).

STORY-216 AC12: Unit tests for individual pipeline stages.
STORY-217: rate_limiter.check_rate_limit is now async — mocks use AsyncMock.

Covers:
  - Stage 1 (stage_validate): Admin bypass, rate limiting, quota checks (new pricing
    with allowed/denied/fallback), and legacy mode.
  - Stage 2 (stage_prepare): Sector loading, invalid sector, custom terms parsing,
    stopword filtering, and min-match floor calculation.

Run from backend/:
    python -m pytest tests/test_search_pipeline.py -v
"""

import sys
from unittest.mock import MagicMock as _MagicMock

# Pre-mock heavy third-party modules that are imported at module level in the
# search_pipeline import chain but are NOT needed for unit-testing stages 1-2.
# This avoids requiring openai, stripe, etc. to be installed in the test env.
for _mod_name in ("openai",):
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = _MagicMock()

import pytest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, AsyncMock

from search_context import SearchContext
from search_pipeline import SearchPipeline


# ============================================================================
# Factory helpers
# ============================================================================

def _make_async_rate_limiter(**overrides):
    """Create a rate_limiter mock with async check_rate_limit."""
    rl = MagicMock()
    rl.check_rate_limit = AsyncMock(return_value=overrides.get("return_value", (True, 0)))
    return rl


def make_deps(**overrides):
    """Create a deps namespace with sensible defaults for all pipeline dependencies."""
    defaults = {
        "ENABLE_NEW_PRICING": False,
        "PNCPClient": MagicMock,
        "buscar_todas_ufs_paralelo": AsyncMock(return_value=[]),
        "aplicar_todos_filtros": MagicMock(return_value=([], {})),
        "create_excel": MagicMock(),
        "rate_limiter": _make_async_rate_limiter(),
        "check_user_roles": AsyncMock(return_value=(False, False)),
        "match_keywords": MagicMock(return_value=(True, [])),
        "KEYWORDS_UNIFORMES": set(),
        "KEYWORDS_EXCLUSAO": set(),
        "validate_terms": MagicMock(return_value={"valid": [], "ignored": [], "reasons": {}}),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_request(**overrides):
    """Create a minimal BuscaRequest-like object with valid defaults."""
    defaults = {
        "ufs": ["SC"],
        "data_inicial": "2026-01-01",
        "data_final": "2026-01-07",
        "setor_id": "vestuario",
        "termos_busca": None,
        "show_all_matches": False,
        "exclusion_terms": None,
        "status": MagicMock(value="todos"),
        "modalidades": None,
        "valor_minimo": None,
        "valor_maximo": None,
        "esferas": None,
        "municipios": None,
        "ordenacao": "relevancia",
        "search_id": "test-search-123",
        "modo_busca": None,  # STORY-240: "publicacao" or "abertas"
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_ctx(**overrides):
    """Create a SearchContext with sensible defaults.

    Accepts `request_overrides` dict to customize the inner request object,
    and `user` to override the default user dict.
    """
    return SearchContext(
        request=make_request(**overrides.pop("request_overrides", {})),
        user=overrides.pop("user", {"id": "user-123", "email": "test@example.com"}),
        **overrides,
    )


def _make_quota_info(allowed=True, **kw):
    """Build a lightweight QuotaInfo-like object for test assertions."""
    defaults = {
        "allowed": allowed,
        "plan_id": "free_trial",
        "plan_name": "FREE Trial",
        "capabilities": {"max_requests_per_min": 10, "max_requests_per_month": 50, "allow_excel": False},
        "quota_used": 0,
        "quota_remaining": 50,
        "quota_reset_date": datetime.now(timezone.utc),
        "trial_expires_at": None,
        "error_message": "Quota exceeded" if not allowed else None,
    }
    defaults.update(kw)
    return SimpleNamespace(**defaults)


# ============================================================================
# Stage 1: stage_validate
# ============================================================================

class TestStageValidate:
    """Tests for SearchPipeline.stage_validate (Stage 1).

    Verifies admin bypass, rate limiting, and quota resolution across
    new-pricing, legacy, and fallback paths.
    """

    # ------------------------------------------------------------------ #
    # 1. Admin bypass
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @patch("search_pipeline.get_master_quota_info")
    @patch("search_pipeline.get_admin_ids", return_value={"admin-42"})
    async def test_admin_bypass_skips_quota_and_rate_limit(
        self, mock_admin_ids, mock_master_quota
    ):
        """When user ID is in the admin list, quota/rate-limit checks are skipped
        and is_admin=True, is_master=True are set on the context."""
        master_qi = _make_quota_info(plan_id="sala_guerra", plan_name="Sala de Guerra (Admin)")
        mock_master_quota.return_value = master_qi

        deps = make_deps(check_user_roles=AsyncMock(return_value=(False, False)))
        ctx = make_ctx(user={"id": "admin-42", "email": "admin@test.com"})
        pipeline = SearchPipeline(deps)

        await pipeline.stage_validate(ctx)

        assert ctx.is_admin is True
        assert ctx.is_master is True
        assert ctx.quota_info is master_qi
        # Rate limiter must NOT have been called
        deps.rate_limiter.check_rate_limit.assert_not_called()
        mock_master_quota.assert_called_once_with(is_admin=True)

    # ------------------------------------------------------------------ #
    # 2. Rate limit exceeded
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @patch("search_pipeline.get_admin_ids", return_value=set())
    @patch("quota.check_quota")
    async def test_rate_limit_exceeded_raises_429(self, mock_check_quota, _):
        """Non-admin user whose rate limiter returns (False, 30) gets HTTP 429."""
        mock_check_quota.return_value = _make_quota_info(
            capabilities={"max_requests_per_min": 5, "max_requests_per_month": 50, "allow_excel": False}
        )
        rate_limiter = _make_async_rate_limiter(return_value=(False, 30))

        deps = make_deps(rate_limiter=rate_limiter)
        ctx = make_ctx()
        pipeline = SearchPipeline(deps)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await pipeline.stage_validate(ctx)

        assert exc_info.value.status_code == 429
        assert "30" in str(exc_info.value.detail)
        rate_limiter.check_rate_limit.assert_called_once()

    # ------------------------------------------------------------------ #
    # 3. Quota exhausted (new pricing)
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @patch("search_pipeline.get_admin_ids", return_value=set())
    @patch("quota.check_quota")
    async def test_quota_exhausted_new_pricing_raises_403(self, mock_check_quota, _):
        """ENABLE_NEW_PRICING=True, quota.check_quota returns allowed=False -> HTTP 403."""
        mock_check_quota.return_value = _make_quota_info(
            allowed=False,
            error_message="Limite de buscas mensais atingido",
        )
        rate_limiter = _make_async_rate_limiter(return_value=(True, 0))

        deps = make_deps(
            ENABLE_NEW_PRICING=True,
            rate_limiter=rate_limiter,
        )
        ctx = make_ctx()
        pipeline = SearchPipeline(deps)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await pipeline.stage_validate(ctx)

        assert exc_info.value.status_code == 403

    # ------------------------------------------------------------------ #
    # 4. Quota fallback on exception
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @patch("search_pipeline.get_admin_ids", return_value=set())
    @patch("quota.create_fallback_quota_info")
    @patch("quota.check_quota")
    async def test_quota_fallback_on_exception(
        self, mock_check_quota, mock_fallback, _
    ):
        """ENABLE_NEW_PRICING=True, quota.check_quota raises generic Exception ->
        ctx.quota_info is set to fallback (no crash)."""
        # First call (rate-limit pre-check) succeeds; second call (quota resolution) fails
        good_qi = _make_quota_info()
        mock_check_quota.side_effect = [good_qi, Exception("Supabase down")]

        fallback_qi = _make_quota_info(plan_id="fallback", plan_name="Fallback")
        mock_fallback.return_value = fallback_qi

        rate_limiter = _make_async_rate_limiter(return_value=(True, 0))

        deps = make_deps(
            ENABLE_NEW_PRICING=True,
            rate_limiter=rate_limiter,
        )
        ctx = make_ctx()
        pipeline = SearchPipeline(deps)

        await pipeline.stage_validate(ctx)

        assert ctx.quota_info is fallback_qi
        mock_fallback.assert_called_once_with("user-123")

    # ------------------------------------------------------------------ #
    # 5. Legacy mode (ENABLE_NEW_PRICING=False)
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @patch("search_pipeline.get_admin_ids", return_value=set())
    @patch("quota.create_legacy_quota_info")
    @patch("quota.check_quota")
    async def test_legacy_mode_sets_legacy_quota(
        self, mock_check_quota, mock_legacy, _
    ):
        """ENABLE_NEW_PRICING=False, non-admin user -> ctx.quota_info is legacy."""
        mock_check_quota.return_value = _make_quota_info()
        legacy_qi = _make_quota_info(plan_id="legacy", plan_name="Legacy")
        mock_legacy.return_value = legacy_qi

        rate_limiter = _make_async_rate_limiter(return_value=(True, 0))

        deps = make_deps(
            ENABLE_NEW_PRICING=False,
            rate_limiter=rate_limiter,
        )
        ctx = make_ctx()
        pipeline = SearchPipeline(deps)

        await pipeline.stage_validate(ctx)

        assert ctx.quota_info is legacy_qi
        mock_legacy.assert_called_once()


# ============================================================================
# Stage 2: stage_prepare
# ============================================================================

class TestStagePrepare:
    """Tests for SearchPipeline.stage_prepare (Stage 2).

    Verifies sector loading, custom term parsing, stopword removal,
    and min-match floor calculation.
    """

    def _make_sector(self, **overrides):
        """Build a lightweight sector-like object."""
        defaults = {
            "id": "vestuario",
            "name": "Vestuario",
            "description": "Uniformes e vestuario profissional",
            "keywords": {"uniforme", "camisa", "calca", "jaleco"},
            "exclusions": {"hospitalar", "cirurgico"},
            "context_required_keywords": {"avental": {"uniforme", "fardamento"}},
        }
        defaults.update(overrides)
        return SimpleNamespace(**defaults)

    # ------------------------------------------------------------------ #
    # 1. Sector loading - valid sector
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @patch("search_pipeline.get_sector")
    async def test_sector_loading_sets_active_keywords_from_sector(self, mock_get_sector):
        """Valid setor_id loads sector config and sets active_keywords from sector keywords."""
        sector = self._make_sector()
        mock_get_sector.return_value = sector

        deps = make_deps()
        ctx = make_ctx(request_overrides={"setor_id": "vestuario", "termos_busca": None})
        pipeline = SearchPipeline(deps)

        await pipeline.stage_prepare(ctx)

        mock_get_sector.assert_called_once_with("vestuario")
        assert ctx.sector is sector
        assert ctx.active_keywords == sector.keywords
        assert ctx.custom_terms == []

    # ------------------------------------------------------------------ #
    # 2. Invalid sector raises 400
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @patch("search_pipeline.get_sector")
    async def test_invalid_sector_raises_400(self, mock_get_sector):
        """Invalid setor_id causes get_sector to raise KeyError -> HTTP 400."""
        mock_get_sector.side_effect = KeyError("Setor 'xyz' nao encontrado")

        deps = make_deps()
        ctx = make_ctx(request_overrides={"setor_id": "xyz"})
        pipeline = SearchPipeline(deps)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await pipeline.stage_prepare(ctx)

        assert exc_info.value.status_code == 400

    # ------------------------------------------------------------------ #
    # 3. Custom terms parsing
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @patch("search_pipeline.calculate_min_matches", return_value=1)
    @patch("search_pipeline.parse_search_terms", return_value=["jaleco", "avental"])
    @patch("search_pipeline.get_sector")
    async def test_custom_terms_parsed_and_set_as_active_keywords(
        self, mock_get_sector, mock_parse, mock_calc
    ):
        """termos_busca='jaleco avental' is parsed into custom_terms and those
        become active_keywords (overriding sector keywords)."""
        sector = self._make_sector()
        mock_get_sector.return_value = sector

        validate_terms = MagicMock(return_value={
            "valid": ["jaleco", "avental"],
            "ignored": [],
            "reasons": {},
        })
        deps = make_deps(validate_terms=validate_terms)
        ctx = make_ctx(request_overrides={"termos_busca": "jaleco avental", "show_all_matches": False})
        pipeline = SearchPipeline(deps)

        await pipeline.stage_prepare(ctx)

        mock_parse.assert_called_once_with("jaleco avental")
        validate_terms.assert_called_once_with(["jaleco", "avental"])
        assert ctx.custom_terms == ["jaleco", "avental"]
        assert ctx.active_keywords == {"jaleco", "avental"}

    # ------------------------------------------------------------------ #
    # 4. Custom terms with stopwords
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @patch("search_pipeline.calculate_min_matches", return_value=1)
    @patch("search_pipeline.parse_search_terms", return_value=["jaleco", "de", "avental"])
    @patch("search_pipeline.get_sector")
    async def test_custom_terms_with_stopwords_populates_stopwords_removed(
        self, mock_get_sector, mock_parse, mock_calc
    ):
        """validate_terms returns ignored terms; ctx.stopwords_removed is populated."""
        sector = self._make_sector()
        mock_get_sector.return_value = sector

        validate_terms = MagicMock(return_value={
            "valid": ["jaleco", "avental"],
            "ignored": ["de"],
            "reasons": {"de": "stopword"},
        })
        deps = make_deps(validate_terms=validate_terms)
        ctx = make_ctx(request_overrides={"termos_busca": "jaleco de avental"})
        pipeline = SearchPipeline(deps)

        await pipeline.stage_prepare(ctx)

        assert ctx.custom_terms == ["jaleco", "avental"]
        assert ctx.stopwords_removed == ["de"]
        assert ctx.active_keywords == {"jaleco", "avental"}

    # ------------------------------------------------------------------ #
    # 5. Min match floor calculation
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @patch("search_pipeline.calculate_min_matches", return_value=2)
    @patch("search_pipeline.parse_search_terms", return_value=["jaleco", "avental", "camisa"])
    @patch("search_pipeline.get_sector")
    async def test_min_match_floor_set_when_custom_terms_and_not_show_all(
        self, mock_get_sector, mock_parse, mock_calc
    ):
        """With custom terms and show_all_matches=False, calculate_min_matches
        is called and its result stored in ctx.min_match_floor_value."""
        sector = self._make_sector()
        mock_get_sector.return_value = sector

        validate_terms = MagicMock(return_value={
            "valid": ["jaleco", "avental", "camisa"],
            "ignored": [],
            "reasons": {},
        })
        deps = make_deps(validate_terms=validate_terms)
        ctx = make_ctx(request_overrides={
            "termos_busca": "jaleco avental camisa",
            "show_all_matches": False,
        })
        pipeline = SearchPipeline(deps)

        await pipeline.stage_prepare(ctx)

        mock_calc.assert_called_once_with(3)
        assert ctx.min_match_floor_value == 2
        assert ctx.custom_terms == ["jaleco", "avental", "camisa"]


# --- FRENTE FOXTROT will add Stage 4-5 tests below ---
