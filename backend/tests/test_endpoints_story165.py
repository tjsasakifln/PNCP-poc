"""Tests for /api/me and updated /api/buscar endpoints (STORY-165)."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from main import app


client = TestClient(app)


class TestMeEndpoint:
    """Test /api/me endpoint."""

    @patch("main.require_auth")
    @patch("quota.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_returns_user_profile_with_capabilities(
        self, mock_get_used, mock_get_supabase, mock_require_auth
    ):
        """Should return complete user profile with plan capabilities."""
        # Mock auth
        mock_require_auth.return_value = {"id": "user-123"}

        # Mock quota
        mock_get_used.return_value = 23

        # Mock Supabase
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock subscription
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "sub-123",
                "plan_id": "consultor_agil",
                "expires_at": None,
            }
        ]

        # Mock user email
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "email": "test@example.com"
        }

        response = client.get("/me")

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == "user-123"
        assert data["email"] == "test@example.com"
        assert data["plan_id"] == "consultor_agil"
        assert data["plan_name"] == "Consultor Ágil"
        assert data["quota_used"] == 23
        assert data["quota_remaining"] == 27  # 50 - 23
        assert "capabilities" in data
        assert data["capabilities"]["max_history_days"] == 30
        assert data["capabilities"]["allow_excel"] is False

    @patch("main.require_auth")
    @patch("quota.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_returns_trial_info_for_free_users(
        self, mock_get_used, mock_get_supabase, mock_require_auth
    ):
        """Should include trial_expires_at for FREE trial users."""
        mock_require_auth.return_value = {"id": "user-123"}
        mock_get_used.return_value = 5

        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock trial subscription
        future_date = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "sub-123",
                "plan_id": "free_trial",
                "expires_at": future_date,
            }
        ]

        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "email": "trial@example.com"
        }

        response = client.get("/me")

        assert response.status_code == 200
        data = response.json()

        assert data["plan_id"] == "free_trial"
        assert data["subscription_status"] == "trial"
        assert data["trial_expires_at"] is not None

    @patch("main.require_auth")
    @patch("quota.check_quota")
    @patch("quota.get_supabase")
    def test_handles_quota_check_failure_gracefully(
        self, mock_get_supabase, mock_check_quota, mock_require_auth
    ):
        """Should return safe fallback if quota check fails."""
        mock_require_auth.return_value = {"id": "user-123"}
        mock_check_quota.side_effect = Exception("Database error")

        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "email": "test@example.com"
        }

        response = client.get("/me")

        assert response.status_code == 200
        data = response.json()

        # Should have fallback values
        assert data["plan_id"] == "free_trial"
        assert "capabilities" in data


class TestBuscarEndpointQuotaValidation:
    """Test /api/buscar quota and rate limit validation."""

    @patch("main.require_auth")
    @patch("quota.check_quota")
    def test_blocks_request_when_quota_exhausted(self, mock_check_quota, mock_require_auth):
        """Should return 403 when monthly quota exhausted."""
        mock_require_auth.return_value = {"id": "user-123"}

        # Mock exhausted quota
        from quota import QuotaInfo, PLAN_CAPABILITIES
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

    @patch("main.require_auth")
    @patch("quota.check_quota")
    def test_blocks_request_when_trial_expired(self, mock_check_quota, mock_require_auth):
        """Should return 403 when trial expired."""
        mock_require_auth.return_value = {"id": "user-123"}

        from quota import QuotaInfo, PLAN_CAPABILITIES
        mock_check_quota.return_value = QuotaInfo(
            allowed=False,
            plan_id="free_trial",
            plan_name="FREE Trial",
            capabilities=PLAN_CAPABILITIES["free_trial"],
            quota_used=0,
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

    @patch("main.require_auth")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("pncp_client.fetch_all")
    @patch("filter.apply_filters")
    def test_increments_quota_on_successful_search(
        self,
        mock_apply_filters,
        mock_fetch_all,
        mock_increment_quota,
        mock_check_quota,
        mock_require_auth,
    ):
        """Should increment quota after successful search."""
        mock_require_auth.return_value = {"id": "user-123"}

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

        # Mock PNCP response
        mock_fetch_all.return_value = []
        mock_apply_filters.return_value = ([], 0)
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


class TestBuscarEndpointExcelGating:
    """Test Excel export gating by plan."""

    @patch("main.require_auth")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("pncp_client.fetch_all")
    @patch("filter.apply_filters")
    @patch("excel.create_excel")
    def test_generates_excel_for_maquina_plan(
        self,
        mock_create_excel,
        mock_apply_filters,
        mock_fetch_all,
        mock_increment_quota,
        mock_check_quota,
        mock_require_auth,
    ):
        """Should generate Excel for Máquina plan (allow_excel=True)."""
        mock_require_auth.return_value = {"id": "user-123"}

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

        # Mock search results
        mock_fetch_all.return_value = []
        mock_apply_filters.return_value = ([{"test": "data"}], 0)
        mock_increment_quota.return_value = 101

        # Mock Excel generation
        from io import BytesIO
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
        assert data["upgrade_message"] is None

    @patch("main.require_auth")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("pncp_client.fetch_all")
    @patch("filter.apply_filters")
    def test_skips_excel_for_consultor_plan(
        self,
        mock_apply_filters,
        mock_fetch_all,
        mock_increment_quota,
        mock_check_quota,
        mock_require_auth,
    ):
        """Should skip Excel for Consultor Ágil plan (allow_excel=False)."""
        mock_require_auth.return_value = {"id": "user-123"}

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

        # Mock search results
        mock_fetch_all.return_value = []
        mock_apply_filters.return_value = ([{"test": "data"}], 0)
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


class TestBuscarEndpointFallbackBehavior:
    """Test fallback behavior when quota/rate limiting fails."""

    @patch("main.require_auth")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("pncp_client.fetch_all")
    @patch("filter.apply_filters")
    def test_continues_on_quota_increment_failure(
        self,
        mock_apply_filters,
        mock_fetch_all,
        mock_increment_quota,
        mock_check_quota,
        mock_require_auth,
    ):
        """Should continue search even if quota increment fails."""
        mock_require_auth.return_value = {"id": "user-123"}

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

        # Mock search results
        mock_fetch_all.return_value = []
        mock_apply_filters.return_value = ([], 0)

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

        # Should have fallback quota values
        assert "quota_used" in data
        assert "quota_remaining" in data
