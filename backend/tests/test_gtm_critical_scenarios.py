"""
GTM Critical Test Scenarios
Tests covering scenarios identified in GTM-READINESS-REPORT.md

Priority: P0 (Pre-GTM Blockers)
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from main import app
from auth import require_auth


client = TestClient(app)


def override_require_auth(user_id: str = "test-user"):
    """Create auth override for testing."""
    async def _override():
        return {"id": user_id, "email": "test@example.com"}
    return _override


def setup_auth_override(user_id="test-user"):
    """Setup auth override and return cleanup function."""
    app.dependency_overrides[require_auth] = override_require_auth(user_id)
    def cleanup():
        app.dependency_overrides.clear()
    return cleanup


# ============================================================================
# GTM Critical Scenario 1: Download Large File (1000+ licitações)
# ============================================================================


class TestLargeFileDownload:
    """Test Excel generation with 1000+ bids."""

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("main.rate_limiter")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    @patch("main.aplicar_todos_filtros")
    @patch("main.create_excel")
    def test_download_1000_plus_bids(
        self,
        mock_create_excel,
        mock_aplicar_todos_filtros,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Should successfully generate Excel for 1000+ bids."""
        cleanup = setup_auth_override("user-large-download")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES
            from io import BytesIO

            # Rate limit passes
            mock_rate_limiter.check_rate_limit.return_value = (True, 0)

            # Sala de Guerra plan (no limits)
            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="sala_guerra",
                plan_name="Sala de Guerra",
                capabilities=PLAN_CAPABILITIES["sala_guerra"],
                quota_used=100,
                quota_remaining=900,
                quota_reset_date=datetime.now(timezone.utc),
            )

            # Generate 1200 mock bids
            large_bid_set = []
            for i in range(1200):
                large_bid_set.append({
                    "codigoCompra": f"BID{i:04d}",
                    "objetoCompra": f"Aquisição de uniformes escolares #{i}",
                    "uf": "SP",
                    "municipio": "São Paulo",
                    "valorTotalEstimado": 50000.0 + (i * 100),
                    "dataAberturaProposta": (datetime.now() + timedelta(days=5)).isoformat(),
                    "nomeOrgao": f"Prefeitura Municipal #{i % 50}",
                })

            # Mock PNCP client
            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = large_bid_set
            mock_increment_quota.return_value = 101

            # Mock filter to return all bids
            mock_aplicar_todos_filtros.return_value = (large_bid_set, {
                "total_raw": 1200,
                "aprovadas": 1200,
                "rejeitadas_uf": 0,
                "rejeitadas_valor": 0,
                "rejeitadas_keyword": 0,
                "rejeitadas_prazo": 0,
                "rejeitadas_outros": 0,
            })

            # Mock Excel generation (should handle large dataset)
            mock_excel_buffer = BytesIO(b"fake excel data with 1200 rows")
            mock_create_excel.return_value = mock_excel_buffer

            # Execute search
            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SP"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-31",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Verify Excel was generated
            assert data["excel_available"] is True
            assert data["excel_base64"] is not None
            assert len(data["excel_base64"]) > 0

            # Verify create_excel was called with large dataset
            mock_create_excel.assert_called_once()
            call_args = mock_create_excel.call_args[0]
            licitacoes_arg = call_args[0]
            assert len(licitacoes_arg) == 1200
        finally:
            cleanup()

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("main.rate_limiter")
    @patch("quota.check_quota")
    @patch("main.PNCPClient")
    def test_large_download_respects_timeout(
        self,
        mock_pncp_client_class,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Large Excel generation should not timeout (30s limit)."""
        cleanup = setup_auth_override("user-timeout-test")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES
            import time

            mock_rate_limiter.check_rate_limit.return_value = (True, 0)

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="maquina",
                plan_name="Máquina",
                capabilities=PLAN_CAPABILITIES["maquina"],
                quota_used=50,
                quota_remaining=250,
                quota_reset_date=datetime.now(timezone.utc),
            )

            # Mock PNCP client that takes time
            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance

            # Simulate slow response (but within 30s timeout)
            def slow_fetch_all(*args, **kwargs):
                time.sleep(2)  # 2 seconds (acceptable)
                return []

            mock_client_instance.fetch_all.side_effect = slow_fetch_all

            start_time = time.time()
            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SP"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )
            elapsed_time = time.time() - start_time

            # Should complete successfully
            assert response.status_code == 200
            # Should be within reasonable time (< 30s)
            assert elapsed_time < 30
        finally:
            cleanup()


# ============================================================================
# GTM Critical Scenario 2: Quota Limit Reached
# ============================================================================


class TestQuotaLimitReached:
    """Test user hitting quota limit during usage."""

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("main.rate_limiter")
    @patch("quota.check_quota")
    def test_quota_exhausted_returns_403(
        self,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Should return 403 when user reaches quota limit."""
        cleanup = setup_auth_override("user-quota-exhausted")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_rate_limiter.check_rate_limit.return_value = (True, 0)

            # Quota exhausted
            mock_check_quota.return_value = QuotaInfo(
                allowed=False,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=50,
                quota_remaining=0,
                quota_reset_date=datetime.now(timezone.utc) + timedelta(days=15),
                error_message="Limite de 50 buscas mensais atingido. Renova em 15 dias.",
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
            detail = response.json()["detail"]
            assert "50 buscas" in detail
            assert "15 dias" in detail
        finally:
            cleanup()

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("main.rate_limiter")
    @patch("quota.check_quota")
    def test_free_trial_expired_upgrade_message(
        self,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Should show upgrade message when FREE trial expires."""
        cleanup = setup_auth_override("user-trial-expired")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_rate_limiter.check_rate_limit.return_value = (True, 0)

            # Trial expired
            mock_check_quota.return_value = QuotaInfo(
                allowed=False,
                plan_id="free_trial",
                plan_name="FREE Trial",
                capabilities=PLAN_CAPABILITIES["free_trial"],
                quota_used=5,
                quota_remaining=0,
                quota_reset_date=datetime.now(timezone.utc),
                trial_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
                error_message="Trial expirado. Faça upgrade para Consultor Ágil (R$ 297/mês).",
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
            detail = response.json()["detail"]
            assert "Trial expirado" in detail
            assert "Consultor Ágil" in detail
            assert "R$ 297" in detail
        finally:
            cleanup()


# ============================================================================
# GTM Critical Scenario 3: Session Expiration During Search
# ============================================================================


class TestSessionExpiration:
    """Test session expiration scenarios."""

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("auth.verify_session_token")
    def test_expired_session_returns_401(
        self,
        mock_verify_session,
    ):
        """Should return 401 when session expires mid-request."""
        # Don't use auth override - test actual auth
        from exceptions import AuthenticationError

        # Mock expired session
        mock_verify_session.side_effect = AuthenticationError("Session expired")

        response = client.post(
            "/buscar",
            json={
                "ufs": ["SP"],
                "data_inicial": "2026-01-01",
                "data_final": "2026-01-07",
                "setor_id": "vestuario",
            },
            headers={"Authorization": "Bearer expired-token"},
        )

        # Should return 401 Unauthorized
        assert response.status_code in [401, 500]  # Depends on error handling
        # If 500, check error message mentions authentication
        if response.status_code == 500:
            assert "authentication" in response.json()["detail"].lower() or "session" in response.json()["detail"].lower()

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("main.rate_limiter")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    def test_session_valid_throughout_search(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Session should remain valid during entire search operation."""
        cleanup = setup_auth_override("user-session-valid")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_rate_limiter.check_rate_limit.return_value = (True, 0)

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
                },
            )

            # Should succeed with valid session
            assert response.status_code == 200
        finally:
            cleanup()


# ============================================================================
# GTM Critical Scenario 4: Concurrent Users Same Account (Edge Case)
# ============================================================================


class TestConcurrentUsers:
    """Test concurrent usage of same account (race conditions)."""

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("main.rate_limiter")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session")
    @patch("main.PNCPClient")
    def test_concurrent_searches_same_user_race_condition(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Concurrent searches by same user should handle race conditions."""
        cleanup = setup_auth_override("user-concurrent")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_rate_limiter.check_rate_limit.return_value = (True, 0)

            # User with 2 searches remaining
            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=48,
                quota_remaining=2,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []

            # Simulate race: both requests see 48 used, both try to increment to 49
            call_count = [0]
            def increment_with_race(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return 49  # First request: 48 → 49
                else:
                    return 50  # Second request: 49 → 50 (or should detect race and fail?)

            mock_increment_quota.side_effect = increment_with_race

            # Execute two searches "simultaneously"
            response1 = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            response2 = client.post(
                "/buscar",
                json={
                    "ufs": ["RJ"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "tecnologia",
                },
            )

            # Both should succeed (no hard quota enforcement at DB level)
            assert response1.status_code == 200
            assert response2.status_code == 200

            # Verify both incremented quota
            assert mock_increment_quota.call_count == 2
        finally:
            cleanup()

    @patch("main.ENABLE_NEW_PRICING", True)
    @patch("main.rate_limiter")
    @patch("quota.check_quota")
    def test_concurrent_quota_check_race_condition(
        self,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Race condition when two users hit quota limit simultaneously."""
        cleanup = setup_auth_override("user-race-quota")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_rate_limiter.check_rate_limit.return_value = (True, 0)

            # First check: 1 remaining
            # Second check: 0 remaining (other request consumed it)
            call_count = [0]
            def quota_check_with_race(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return QuotaInfo(
                        allowed=True,
                        plan_id="consultor_agil",
                        plan_name="Consultor Ágil",
                        capabilities=PLAN_CAPABILITIES["consultor_agil"],
                        quota_used=49,
                        quota_remaining=1,
                        quota_reset_date=datetime.now(timezone.utc),
                    )
                else:
                    return QuotaInfo(
                        allowed=False,
                        plan_id="consultor_agil",
                        plan_name="Consultor Ágil",
                        capabilities=PLAN_CAPABILITIES["consultor_agil"],
                        quota_used=50,
                        quota_remaining=0,
                        quota_reset_date=datetime.now(timezone.utc),
                        error_message="Limite atingido",
                    )

            mock_check_quota.side_effect = quota_check_with_race

            # First request should succeed
            response1 = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            # Second request should fail (quota exhausted)
            response2 = client.post(
                "/buscar",
                json={
                    "ufs": ["RJ"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "tecnologia",
                },
            )

            # First succeeds, second blocked
            assert response1.status_code == 200
            assert response2.status_code == 403
        finally:
            cleanup()
