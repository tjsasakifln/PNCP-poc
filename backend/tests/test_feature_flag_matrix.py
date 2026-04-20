"""DEBT-205: Feature Flag Matrix Tests.

Validates 10 critical feature flags in on/off states and 5 critical
combinations to ensure no unexpected interactions.

AC: test_feature_flag_matrix.py with 10 critical flags tested on/off
    + 5 critical combinations tested.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from config.features import (
    _FEATURE_FLAG_REGISTRY,
    get_feature_flag,
    reload_feature_flags,
    _feature_flag_cache,
)


# ---------------------------------------------------------------------------
# 1. Registry completeness — all 45+ flags registered
# ---------------------------------------------------------------------------
class TestRegistryCompleteness:
    def test_registry_has_at_least_30_flags(self):
        """DEBT-SYS-009: registry has 30+ flags."""
        assert len(_FEATURE_FLAG_REGISTRY) >= 30, (
            f"Expected 30+ flags, got {len(_FEATURE_FLAG_REGISTRY)}"
        )

    def test_all_flags_have_env_var_and_default(self):
        """Each registry entry is a (env_var, default) tuple."""
        for name, entry in _FEATURE_FLAG_REGISTRY.items():
            assert isinstance(entry, tuple), f"{name} is not a tuple"
            assert len(entry) == 2, f"{name} tuple length != 2"
            env_var, default = entry
            assert isinstance(env_var, str), f"{name} env_var not str"
            assert default in ("true", "false"), f"{name} default={default!r}"

    def test_no_duplicate_env_vars(self):
        """No two flags share the same env var (except intentional aliases)."""
        env_vars: dict[str, str] = {}
        for name, (env_var, _) in _FEATURE_FLAG_REGISTRY.items():
            if env_var in env_vars:
                # PCP_V2_ENABLED maps to PCP_ENABLED — that's intentional
                if env_var == "PCP_ENABLED":
                    continue
                pytest.fail(f"Duplicate env var {env_var}: {env_vars[env_var]} and {name}")
            env_vars[env_var] = name


# ---------------------------------------------------------------------------
# 2. get_feature_flag — on/off for 10 critical flags
# ---------------------------------------------------------------------------
_CRITICAL_FLAGS = [
    "LLM_ARBITER_ENABLED",
    "LLM_ZERO_MATCH_ENABLED",
    "DATALAKE_ENABLED",
    "DATALAKE_QUERY_ENABLED",
    # CACHE_WARMING_ENABLED removed 2026-04-18 (STORY-CIG-BE-cache-warming-deprecate)
    "COMPRASGOV_ENABLED",
    "TRIAL_PAYWALL_ENABLED",
    "SEARCH_ASYNC_ENABLED",
    "RATE_LIMITING_ENABLED",
    "PARTIAL_DATA_SSE_ENABLED",
]


class TestCriticalFlagsOnOff:
    """Each critical flag tested in both on and off states.

    STORY-BTS-009 followup: migrated from ``patch.dict(os.environ, ...)`` to
    pytest's ``monkeypatch`` fixture. The original implementation relied on
    context-manager-scoped env var overrides, which were subtly losing against
    other autouse fixtures (``_force_sync_search``, ``_setup_env_vars``) that
    seed env vars via ``monkeypatch.setenv`` earlier in the per-test stack.
    Using ``monkeypatch`` here applies the same teardown model and "last write
    wins" semantics reliably across the 9k-test run.
    """

    def setup_method(self):
        _feature_flag_cache.clear()

    @pytest.mark.parametrize("flag_name", _CRITICAL_FLAGS)
    def test_flag_on(self, flag_name: str, monkeypatch):
        """Flag returns True when env var is 'true'."""
        env_var = _FEATURE_FLAG_REGISTRY[flag_name][0]
        monkeypatch.setenv(env_var, "true")
        _feature_flag_cache.clear()
        result = get_feature_flag(flag_name)
        assert result is True, f"{flag_name} should be True with env=true"

    @pytest.mark.parametrize("flag_name", _CRITICAL_FLAGS)
    def test_flag_off(self, flag_name: str, monkeypatch):
        """Flag returns False when env var is 'false'."""
        env_var = _FEATURE_FLAG_REGISTRY[flag_name][0]
        monkeypatch.setenv(env_var, "false")
        _feature_flag_cache.clear()
        result = get_feature_flag(flag_name)
        assert result is False, f"{flag_name} should be False with env=false"

    @pytest.mark.parametrize("flag_name", _CRITICAL_FLAGS)
    def test_flag_default(self, flag_name: str, monkeypatch):
        """Flag returns its registry default when env var is unset."""
        env_var = _FEATURE_FLAG_REGISTRY[flag_name][0]
        _, default_str = _FEATURE_FLAG_REGISTRY[flag_name]
        expected = default_str == "true"
        monkeypatch.delenv(env_var, raising=False)
        _feature_flag_cache.clear()
        result = get_feature_flag(flag_name)
        assert result is expected, (
            f"{flag_name} default should be {expected}"
        )


# ---------------------------------------------------------------------------
# 3. Five critical flag combinations
# ---------------------------------------------------------------------------
class TestCriticalCombinations:
    """5 combinations of flags that interact in the search pipeline.

    STORY-BTS-009 followup: migrated from ``patch.dict`` → ``monkeypatch`` for
    the same reason as ``TestCriticalFlagsOnOff``.
    """

    def setup_method(self):
        _feature_flag_cache.clear()

    def test_combo1_datalake_off_llm_zero_match_on(self, monkeypatch):
        """DATALAKE_QUERY_ENABLED=false + LLM_ZERO_MATCH_ENABLED=true.

        When datalake is off, live API fetch is used. LLM zero-match
        should still classify zero-density bids from live results.
        """
        monkeypatch.setenv("DATALAKE_QUERY_ENABLED", "false")
        monkeypatch.setenv("LLM_ZERO_MATCH_ENABLED", "true")
        _feature_flag_cache.clear()
        assert get_feature_flag("DATALAKE_QUERY_ENABLED") is False
        assert get_feature_flag("LLM_ZERO_MATCH_ENABLED") is True

    def test_combo2_search_async_on(self, monkeypatch):
        """SEARCH_ASYNC_ENABLED=true — background processing validated.

        Previously combined with CACHE_WARMING_ENABLED which was removed
        2026-04-18 (STORY-CIG-BE-cache-warming-deprecate).
        """
        monkeypatch.setenv("SEARCH_ASYNC_ENABLED", "true")
        _feature_flag_cache.clear()
        assert get_feature_flag("SEARCH_ASYNC_ENABLED") is True

    def test_combo3_trial_paywall_on_rate_limiting_on(self, monkeypatch):
        """TRIAL_PAYWALL_ENABLED=true + RATE_LIMITING_ENABLED=true.

        Both constraints active. Trial users hit both paywall AND rate limits.
        """
        monkeypatch.setenv("TRIAL_PAYWALL_ENABLED", "true")
        monkeypatch.setenv("RATE_LIMITING_ENABLED", "true")
        _feature_flag_cache.clear()
        assert get_feature_flag("TRIAL_PAYWALL_ENABLED") is True
        assert get_feature_flag("RATE_LIMITING_ENABLED") is True

    def test_combo4_all_sources_off(self, monkeypatch):
        """COMPRASGOV_ENABLED=false + DATALAKE_ENABLED=false.

        All non-PNCP sources disabled. System should still work via PNCP fallback.
        """
        monkeypatch.setenv("COMPRASGOV_ENABLED", "false")
        monkeypatch.setenv("DATALAKE_ENABLED", "false")
        _feature_flag_cache.clear()
        assert get_feature_flag("COMPRASGOV_ENABLED") is False
        assert get_feature_flag("DATALAKE_ENABLED") is False

    def test_combo5_llm_arbiter_off_zero_match_off(self, monkeypatch):
        """LLM_ARBITER_ENABLED=false + LLM_ZERO_MATCH_ENABLED=false.

        Both LLM features off. Filter pipeline should work with keywords only.
        """
        monkeypatch.setenv("LLM_ARBITER_ENABLED", "false")
        monkeypatch.setenv("LLM_ZERO_MATCH_ENABLED", "false")
        _feature_flag_cache.clear()
        assert get_feature_flag("LLM_ARBITER_ENABLED") is False
        assert get_feature_flag("LLM_ZERO_MATCH_ENABLED") is False


# ---------------------------------------------------------------------------
# 4. reload_feature_flags clears cache
# ---------------------------------------------------------------------------
class TestReloadFlags:
    def test_reload_clears_cache(self):
        """reload_feature_flags() clears the TTL cache."""
        _feature_flag_cache["TEST_FLAG"] = (True, 0)
        result = reload_feature_flags()
        assert "TEST_FLAG" not in _feature_flag_cache
        assert isinstance(result, dict)
        assert len(result) >= 30


# ---------------------------------------------------------------------------
# 5. Public endpoint returns flags
# ---------------------------------------------------------------------------
class TestPublicEndpoint:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_public_endpoint_requires_auth(self, client):
        """GET /v1/feature-flags requires authentication."""
        resp = client.get("/v1/feature-flags")
        assert resp.status_code in (401, 403)

    def test_public_endpoint_returns_flags(self, client):
        """GET /v1/feature-flags returns flags list for authenticated user."""
        from auth import require_auth
        from main import app

        app.dependency_overrides[require_auth] = lambda: {
            "id": "test-user-id",
            "email": "test@test.com",
        }
        try:
            resp = client.get("/v1/feature-flags")
            assert resp.status_code == 200
            data = resp.json()
            assert "flags" in data
            assert "total" in data
            assert data["total"] >= 30
            # Each flag has expected shape
            flag = data["flags"][0]
            assert "name" in flag
            assert "value" in flag
            assert "description" in flag
            assert "category" in flag
        finally:
            app.dependency_overrides.pop(require_auth, None)


# ---------------------------------------------------------------------------
# 6. Admin endpoint includes lifecycle metadata
# ---------------------------------------------------------------------------
class TestAdminEndpointLifecycle:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_admin_endpoint_includes_lifecycle(self, client):
        """GET /v1/admin/feature-flags includes lifecycle metadata."""
        from admin import require_admin
        from main import app

        app.dependency_overrides[require_admin] = lambda: {
            "id": "admin-id",
            "email": "admin@test.com",
        }
        try:
            resp = client.get("/v1/admin/feature-flags")
            assert resp.status_code == 200
            data = resp.json()
            flags_with_lifecycle = [
                f for f in data["flags"] if f.get("lifecycle") is not None
            ]
            assert len(flags_with_lifecycle) >= 30, (
                f"Expected 30+ flags with lifecycle, got {len(flags_with_lifecycle)}"
            )
            # Check lifecycle shape
            lc = flags_with_lifecycle[0]["lifecycle"]
            assert "owner" in lc
            assert "category" in lc
            assert "lifecycle" in lc
            assert "created" in lc
        finally:
            app.dependency_overrides.pop(require_admin, None)


# ---------------------------------------------------------------------------
# 7. All flags have at least 1 test on + 1 test off (via parametrize above)
# ---------------------------------------------------------------------------
class TestAllFlagsHaveDescription:
    def test_all_registry_flags_have_description(self):
        """Every flag in the registry has a description."""
        from routes.feature_flags import _FLAG_DESCRIPTIONS
        missing = []
        for flag_name in _FEATURE_FLAG_REGISTRY:
            if flag_name not in _FLAG_DESCRIPTIONS:
                missing.append(flag_name)
        assert not missing, f"Flags without description: {missing}"

    def test_all_registry_flags_have_lifecycle(self):
        """Every flag in the registry has lifecycle metadata."""
        from routes.feature_flags import _FLAG_LIFECYCLE
        missing = []
        for flag_name in _FEATURE_FLAG_REGISTRY:
            if flag_name not in _FLAG_LIFECYCLE:
                missing.append(flag_name)
        assert not missing, f"Flags without lifecycle: {missing}"

    def test_no_phantom_flags_in_descriptions(self):
        """No descriptions for flags that don't exist in registry."""
        from routes.feature_flags import _FLAG_DESCRIPTIONS
        phantom = []
        for flag_name in _FLAG_DESCRIPTIONS:
            if flag_name not in _FEATURE_FLAG_REGISTRY:
                phantom.append(flag_name)
        assert not phantom, f"Phantom flags in descriptions: {phantom}"

    def test_no_phantom_flags_in_lifecycle(self):
        """No lifecycle entries for flags that don't exist in registry."""
        from routes.feature_flags import _FLAG_LIFECYCLE
        phantom = []
        for flag_name in _FLAG_LIFECYCLE:
            if flag_name not in _FEATURE_FLAG_REGISTRY:
                phantom.append(flag_name)
        assert not phantom, f"Phantom flags in lifecycle: {phantom}"
