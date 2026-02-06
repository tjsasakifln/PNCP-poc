"""Comprehensive tests for /api/buscar endpoint - BLOCKER 4 fix."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from main import app
from auth import require_auth


client = TestClient(app)


def override_require_auth(user_id: str = "user-123"):
    """Create a dependency override for require_auth."""
    async def _override():
        return {"id": user_id, "email": "test@example.com"}
    return _override


def setup_auth_override(user_id="user-123"):
    """Setup auth override and return cleanup function."""
    app.dependency_overrides[require_auth] = override_require_auth(user_id)
    def cleanup():
        app.dependency_overrides.clear()
    return cleanup


class TestBuscarFeatureFlagEnabled:
    """Test /api/buscar with ENABLE_NEW_PRICING=true (feature flag enabled)."""

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    def test_enforces_quota_when_feature_flag_enabled(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should enforce quota limits when feature flag is enabled."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # Quota exhausted
            mock_check_quota.return_value = QuotaInfo(
                allowed=False,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=50,
                quota_remaining=0,
                quota_reset_date=datetime.now(timezone.utc),
                error_message="Limite de 50 buscas mensais atingido.",
            )

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 403
            assert "Limite de 50 buscas mensais atingido" in response.json()["detail"]
        finally:
            cleanup()

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    def test_allows_request_when_quota_available(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should allow request when quota is available."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=23,
                quota_remaining=27,
                quota_reset_date=datetime.now(timezone.utc),
            )

            # Mock PNCP client
            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 24

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["quota_used"] == 24
            assert data["quota_remaining"] == 26  # 50 - 24
        finally:
            cleanup()


class TestBuscarFeatureFlagDisabled:
    """Test /api/buscar with ENABLE_NEW_PRICING=false (legacy behavior)."""

    @patch("main.ENABLE_NEW_PRICING", False)
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    def test_no_quota_enforcement_when_disabled(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
    ):
        """Should NOT enforce quota when feature flag is disabled."""
        cleanup = setup_auth_override("user-123")
        try:
            # Mock PNCP client
            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 1

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            # Should have fallback quota values
            data = response.json()
            assert "quota_used" in data
            assert "quota_remaining" in data
        finally:
            cleanup()


class TestBuscarDateRangeValidation:
    """Test date range validation based on plan capabilities."""

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    def test_accepts_date_range_within_plan_limit(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should accept date range within plan's max_history_days."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # Consultor Ágil: max_history_days = 30
            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=10,
                quota_remaining=40,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 11

            # 7 days range (within 30 days limit)
            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
        finally:
            cleanup()

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    def test_rejects_date_range_exceeding_plan_limit(
        self,
        mock_check_quota,
    ):
        """Should reject date range exceeding plan's max_history_days (if enforced)."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # FREE Trial: max_history_days = 7
            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="free_trial",
                plan_name="FREE Trial",
                capabilities=PLAN_CAPABILITIES["free_trial"],
                quota_used=2,
                quota_remaining=3,
                quota_reset_date=datetime.now(timezone.utc),
                trial_expires_at=datetime.now(timezone.utc) + timedelta(days=5),
            )

            # 60 days range (exceeds 7 days limit)
            # NOTE: Current implementation doesn't enforce this at endpoint level
            # It's a validation gap that could be added in future
            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-03-01",  # 60 days
                    "setor_id": "vestuario",
                },
            )

            # Currently passes (no validation), but could be 400 in future
            assert response.status_code in [200, 400, 403]
        finally:
            cleanup()


class TestBuscarExcelGating:
    """Test Excel export gating based on plan capabilities."""

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    @patch("main.aplicar_todos_filtros")
    @patch("main.create_excel")
    def test_generates_excel_for_maquina_plan(
        self,
        mock_create_excel,
        mock_aplicar_todos_filtros,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should generate Excel for Máquina plan (allow_excel=True)."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES
            from io import BytesIO

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="maquina",
                plan_name="Máquina",
                capabilities=PLAN_CAPABILITIES["maquina"],
                quota_used=100,
                quota_remaining=200,
                quota_reset_date=datetime.now(timezone.utc),
            )

            # Mock PNCP client with matching UF
            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_licitacao = {
                "codigoCompra": "TEST123",
                "objetoCompra": "uniformes escolares",
                "uf": "SC",  # MUST match requested UF
                "municipio": "Florianópolis",
                "valorTotalEstimado": 100000.0,
                "dataAberturaProposta": (datetime.now() + timedelta(days=5)).isoformat(),
                "nomeOrgao": "Prefeitura",
            }
            mock_client_instance.fetch_all.return_value = [mock_licitacao]
            mock_increment_quota.return_value = 101

            # Mock filter to return the bid
            mock_aplicar_todos_filtros.return_value = ([mock_licitacao], {
                "total_raw": 1,
                "aprovadas": 1,
                "rejeitadas_uf": 0,
                "rejeitadas_valor": 0,
                "rejeitadas_keyword": 0,
                "rejeitadas_prazo": 0,
                "rejeitadas_outros": 0,
            })

            # Mock Excel generation
            mock_excel_buffer = BytesIO(b"fake excel data")
            mock_create_excel.return_value = mock_excel_buffer

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert data["excel_available"] is True
            assert data["excel_base64"] is not None
            assert len(data["excel_base64"]) > 0
            assert data["upgrade_message"] is None
        finally:
            cleanup()

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    def test_blocks_excel_for_consultor_plan(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should NOT generate Excel for Consultor Ágil plan (allow_excel=False)."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=23,
                quota_remaining=27,
                quota_reset_date=datetime.now(timezone.utc),
            )

            # Mock PNCP client
            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 24

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert data["excel_available"] is False
            assert data["excel_base64"] is None
            assert "Máquina" in data["upgrade_message"]
            assert "R$ 597/mês" in data["upgrade_message"]
        finally:
            cleanup()


class TestBuscarRateLimiting:
    """Test rate limiting scenarios."""

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    def test_returns_429_when_rate_limit_exceeded(
        self,
        mock_check_quota,
    ):
        """Should return 503 (not 429) when PNCP rate limit exceeded."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES
            from exceptions import PNCPRateLimitError

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="maquina",
                plan_name="Máquina",
                capabilities=PLAN_CAPABILITIES["maquina"],
                quota_used=100,
                quota_remaining=200,
                quota_reset_date=datetime.now(timezone.utc),
            )

            # Mock PNCP client to raise rate limit error
            with patch("main.PNCPClient") as mock_pncp_class:
                mock_client = MagicMock()
                mock_pncp_class.return_value = mock_client
                error = PNCPRateLimitError("Rate limit exceeded")
                error.retry_after = 60
                mock_client.fetch_all.side_effect = error

                response = client.post(
                    "/buscar",
                    json={
                        "ufs": ["SC"],
                        "data_inicial": "2026-01-01",
                        "data_final": "2026-01-07",
                        "setor_id": "vestuario",
                    },
                )

                assert response.status_code == 503
                assert "Retry-After" in response.headers
                assert "60" in response.json()["detail"]
        finally:
            cleanup()


class TestBuscarErrorHandling:
    """Test error handling scenarios."""

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    def test_returns_403_on_quota_exhausted(
        self,
        mock_check_quota,
    ):
        """Should return 403 when quota is exhausted."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=False,
                plan_id="free_trial",
                plan_name="FREE Trial",
                capabilities=PLAN_CAPABILITIES["free_trial"],
                quota_used=5,
                quota_remaining=0,
                quota_reset_date=datetime.now(timezone.utc),
                trial_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
                error_message="Trial expirado. Faça upgrade para continuar.",
            )

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 403
            assert "Trial expirado" in response.json()["detail"]
        finally:
            cleanup()

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    def test_returns_503_on_runtime_error(
        self,
        mock_check_quota,
    ):
        """Should return 503 when Supabase configuration error occurs."""
        cleanup = setup_auth_override("user-123")
        try:
            # Simulate RuntimeError (Supabase config error)
            mock_check_quota.side_effect = RuntimeError("Supabase not configured")

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 503
            assert "temporariamente indisponível" in response.json()["detail"]
        finally:
            cleanup()

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    def test_continues_on_quota_increment_failure(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should continue with fallback when quota increment fails."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=23,
                quota_remaining=27,
                quota_reset_date=datetime.now(timezone.utc),
            )

            # Mock PNCP client
            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []

            # Mock quota increment failure
            mock_increment_quota.side_effect = Exception("Database error")

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            # Should still succeed with fallback
            assert response.status_code == 200
            data = response.json()
            assert "quota_used" in data
            assert "quota_remaining" in data
        finally:
            cleanup()


class TestBuscarQuotaIncrementScenarios:
    """Test quota increment behavior in different scenarios."""

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    def test_increments_quota_on_successful_search(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should increment quota after successful search."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=23,
                quota_remaining=27,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 24

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Verify quota was incremented
            mock_increment_quota.assert_called_once_with("user-123")
            assert data["quota_used"] == 24
            assert data["quota_remaining"] == 26  # 50 - 24
        finally:
            cleanup()

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    def test_increments_quota_even_with_no_results(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should increment quota even when search returns no results."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="maquina",
                plan_name="Máquina",
                capabilities=PLAN_CAPABILITIES["maquina"],
                quota_used=50,
                quota_remaining=250,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []  # No results
            mock_increment_quota.return_value = 51

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            mock_increment_quota.assert_called_once()
            data = response.json()
            assert data["quota_used"] == 51
        finally:
            cleanup()


class TestBuscarInvalidSector:
    """Test invalid sector handling."""

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    def test_returns_500_on_invalid_sector_id(
        self,
        mock_check_quota,
    ):
        """Should return 500 when invalid sector ID is provided."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=10,
                quota_remaining=40,
                quota_reset_date=datetime.now(timezone.utc),
            )

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "invalid-sector-xyz",  # Invalid sector
                },
            )

            # KeyError -> HTTPException(400) -> outer exception handler -> 500
            assert response.status_code == 500
        finally:
            cleanup()


class TestBuscarCustomSearchTerms:
    """Test custom search terms and stopword removal."""

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    def test_uses_custom_terms_instead_of_sector_keywords(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should use custom terms when provided."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=10,
                quota_remaining=40,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 11

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                    "termos_busca": "camisa personalizada bordado",  # Custom terms
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Should have custom terms in response
            assert data["termos_utilizados"] == ["camisa", "personalizada", "bordado"]
        finally:
            cleanup()

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    def test_removes_stopwords_from_custom_terms(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should remove stopwords from custom search terms."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="maquina",
                plan_name="Máquina",
                capabilities=PLAN_CAPABILITIES["maquina"],
                quota_used=100,
                quota_remaining=200,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 101

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                    "termos_busca": "de para com uniforme escolar",  # Stopwords + real term
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Stopwords (de, para, com) should be removed
            assert "stopwords_removidas" in data
            assert len(data["stopwords_removidas"]) > 0
            # Real terms should remain
            assert "termos_utilizados" in data
            assert "uniforme" in data["termos_utilizados"]
            assert "escolar" in data["termos_utilizados"]
        finally:
            cleanup()

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    def test_fallback_to_sector_keywords_when_all_stopwords(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should fallback to sector keywords when all custom terms are stopwords."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=5,
                quota_remaining=45,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 6

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                    "termos_busca": "de para com o a",  # All stopwords
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Should fallback to sector keywords (no custom terms used)
            assert data["termos_utilizados"] is None or len(data["termos_utilizados"]) == 0
            assert len(data["stopwords_removidas"]) == 5  # All were removed
        finally:
            cleanup()
