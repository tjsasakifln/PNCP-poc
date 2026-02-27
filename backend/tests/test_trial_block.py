"""
STORY-265: Tests for trial hard block after 7-day expiry.

Tests:
- AC17: Integration test — expired trial blocked on ALL mutable endpoints
- AC18: Read-only endpoints (GET /pipeline, GET /sessions) still work with expired trial
- AC19: require_active_plan returns 403 with correct structured body
- AC21: Paid plan bypasses require_active_plan
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

from main import app
from auth import require_auth
from quota import QuotaInfo, PLAN_CAPABILITIES, get_quota_reset_date


# ============================================================================
# Helpers
# ============================================================================

def _make_expired_trial_quota() -> QuotaInfo:
    """Create a QuotaInfo representing an expired free trial."""
    return QuotaInfo(
        allowed=False,
        plan_id="free_trial",
        plan_name="FREE Trial",
        capabilities=PLAN_CAPABILITIES["free_trial"],
        quota_used=3,
        quota_remaining=0,
        quota_reset_date=get_quota_reset_date(),
        trial_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        error_message="Seu trial de 7 dias expirou. Veja o valor que você analisou — continue tendo vantagem competitiva.",
    )


def _make_active_trial_quota() -> QuotaInfo:
    """Create a QuotaInfo representing an active free trial."""
    return QuotaInfo(
        allowed=True,
        plan_id="free_trial",
        plan_name="FREE Trial",
        capabilities=PLAN_CAPABILITIES["free_trial"],
        quota_used=1,
        quota_remaining=999,
        quota_reset_date=get_quota_reset_date(),
        trial_expires_at=datetime.now(timezone.utc) + timedelta(days=5),
        error_message=None,
    )


def _make_paid_plan_quota() -> QuotaInfo:
    """Create a QuotaInfo representing a paid SmartLic Pro plan."""
    return QuotaInfo(
        allowed=True,
        plan_id="smartlic_pro",
        plan_name="SmartLic Pro",
        capabilities=PLAN_CAPABILITIES["smartlic_pro"],
        quota_used=10,
        quota_remaining=990,
        quota_reset_date=get_quota_reset_date(),
        trial_expires_at=None,
        error_message=None,
    )


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def setup_overrides():
    """Set up auth override for all tests."""
    app.dependency_overrides[require_auth] = lambda: {"id": "test-trial-user", "email": "trial@example.com"}
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ============================================================================
# AC19: require_active_plan returns 403 with structured body
# ============================================================================

class TestRequireActivePlanDecorator:
    """AC19: Verify require_active_plan returns correct 403 structure."""

    @pytest.mark.asyncio
    async def test_expired_trial_returns_403_trial_expired(self):
        """AC19 + AC8: expired trial → 403 with error='trial_expired'."""
        from quota import require_active_plan

        expired_quota = _make_expired_trial_quota()
        user = {"id": "test-trial-user", "email": "trial@example.com"}

        with patch("quota.check_quota", return_value=expired_quota), \
             patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await require_active_plan(user)

            assert exc_info.value.status_code == 403
            detail = exc_info.value.detail
            assert detail["error"] == "trial_expired"
            assert detail["upgrade_url"] == "/planos"
            assert "message" in detail

    @pytest.mark.asyncio
    async def test_expired_paid_plan_returns_403_plan_expired(self):
        """AC19: expired paid plan → 403 with error='plan_expired'."""
        from quota import require_active_plan

        expired_paid = QuotaInfo(
            allowed=False,
            plan_id="smartlic_pro",
            plan_name="SmartLic Pro",
            capabilities=PLAN_CAPABILITIES["smartlic_pro"],
            quota_used=100,
            quota_remaining=0,
            quota_reset_date=get_quota_reset_date(),
            trial_expires_at=None,
            error_message="Sua assinatura expirou.",
        )
        user = {"id": "test-paid-user", "email": "paid@example.com"}

        with patch("quota.check_quota", return_value=expired_paid), \
             patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await require_active_plan(user)

            assert exc_info.value.status_code == 403
            detail = exc_info.value.detail
            assert detail["error"] == "plan_expired"

    @pytest.mark.asyncio
    async def test_active_trial_passes_through(self):
        """AC21 variant: active trial passes through require_active_plan."""
        from quota import require_active_plan

        active_quota = _make_active_trial_quota()
        user = {"id": "test-active-user", "email": "active@example.com"}

        with patch("quota.check_quota", return_value=active_quota), \
             patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False):
            result = await require_active_plan(user)
            assert result == user

    @pytest.mark.asyncio
    async def test_paid_plan_bypasses_block(self):
        """AC21: Paid plan is NOT affected by require_active_plan."""
        from quota import require_active_plan

        paid_quota = _make_paid_plan_quota()
        user = {"id": "test-pro-user", "email": "pro@example.com"}

        with patch("quota.check_quota", return_value=paid_quota), \
             patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False):
            result = await require_active_plan(user)
            assert result == user

    @pytest.mark.asyncio
    async def test_master_bypasses_block(self):
        """AC21 variant: master/admin bypasses require_active_plan even if quota says blocked."""
        from quota import require_active_plan

        user = {"id": "test-master-user", "email": "admin@example.com"}

        with patch("authorization.has_master_access", new_callable=AsyncMock, return_value=True):
            result = await require_active_plan(user)
            assert result == user

    @pytest.mark.asyncio
    async def test_structured_log_on_block(self):
        """AC12: Structured log emitted when trial is blocked."""
        from quota import require_active_plan

        expired_quota = _make_expired_trial_quota()
        user = {"id": "test-log-user", "email": "log@example.com"}

        with patch("quota.check_quota", return_value=expired_quota), \
             patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False), \
             patch("quota.logger") as mock_logger:
            from fastapi import HTTPException
            with pytest.raises(HTTPException):
                await require_active_plan(user)

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "trial_blocked"
            extra = call_args[1]["extra"]
            assert extra["error_type"] == "trial_expired"
            assert extra["plan_id"] == "free_trial"
            assert "days_overdue" in extra


# ============================================================================
# AC17: Integration test — expired trial blocked on mutable endpoints
# ============================================================================

class TestExpiredTrialBlocksMutableEndpoints:
    """AC17: Verify expired trial is blocked on ALL mutable endpoints."""

    def test_post_buscar_blocked(self, client):
        """AC1+AC17: POST /buscar returns 403 for expired trial."""
        expired_quota = _make_expired_trial_quota()

        with patch("quota.check_quota", return_value=expired_quota), \
             patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False):
            response = client.post(
                "/v1/buscar",
                json={
                    "ufs": ["SP"],
                    "data_inicial": "2026-02-01",
                    "data_final": "2026-02-10",
                    "setor_id": "vestuario",
                },
            )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "trial_expired"
        assert data["detail"]["upgrade_url"] == "/planos"

    def test_post_pipeline_blocked(self, client):
        """AC2+AC17: POST /pipeline returns 403 for expired trial."""
        expired_quota = _make_expired_trial_quota()

        with patch("quota.check_quota", return_value=expired_quota), \
             patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False):
            response = client.post(
                "/pipeline",
                json={
                    "pncp_id": "12345678000100-1-000001/2026",
                    "objeto": "Test procurement",
                    "orgao": "Test Agency",
                    "uf": "SP",
                    "valor_estimado": 100000,
                },
            )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "trial_expired"

    def test_patch_pipeline_blocked(self, client):
        """AC2+AC17: PATCH /pipeline/{id} returns 403 for expired trial."""
        expired_quota = _make_expired_trial_quota()

        with patch("quota.check_quota", return_value=expired_quota), \
             patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False):
            response = client.patch(
                "/pipeline/some-item-id",
                json={"stage": "analise"},
            )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "trial_expired"

    def test_delete_pipeline_blocked(self, client):
        """AC2+AC17: DELETE /pipeline/{id} returns 403 for expired trial."""
        expired_quota = _make_expired_trial_quota()

        with patch("quota.check_quota", return_value=expired_quota), \
             patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False):
            response = client.delete("/pipeline/some-item-id")

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "trial_expired"

    def test_post_first_analysis_blocked(self, client):
        """AC5+AC17: POST /v1/first-analysis returns 403 for expired trial."""
        expired_quota = _make_expired_trial_quota()

        with patch("quota.check_quota", return_value=expired_quota), \
             patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False):
            response = client.post(
                "/v1/first-analysis",
                json={
                    "cnae": "4781-4/00",
                    "objetivo_principal": "Uniformes escolares",
                    "ufs": ["SP"],
                    "faixa_valor_min": 50000,
                    "faixa_valor_max": 500000,
                },
            )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "trial_expired"


# ============================================================================
# AC18: Read-only endpoints still work with expired trial
# ============================================================================

class TestExpiredTrialReadOnlyEndpoints:
    """AC18: Verify read-only endpoints remain accessible for expired trials."""

    def test_get_pipeline_accessible(self, client):
        """AC3+AC18: GET /pipeline accessible for expired trial (read-only)."""
        expired_quota = _make_expired_trial_quota()

        # Mock Supabase response for pipeline items
        mock_result = MagicMock()
        mock_result.data = []

        with patch("quota.check_quota", return_value=expired_quota), \
             patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False), \
             patch("routes.pipeline.get_supabase") as mock_supa:
            mock_supa.return_value.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
            response = client.get("/pipeline")

        assert response.status_code == 200

    def test_get_pipeline_alerts_accessible(self, client):
        """AC3+AC18: GET /pipeline/alerts accessible for expired trial."""
        expired_quota = _make_expired_trial_quota()

        mock_result = MagicMock()
        mock_result.data = []

        with patch("quota.check_quota", return_value=expired_quota), \
             patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False), \
             patch("routes.pipeline.get_supabase") as mock_supa:
            mock_supa.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
            response = client.get("/pipeline/alerts")

        assert response.status_code == 200

    def test_get_sessions_accessible(self, client):
        """AC6+AC18: GET /sessions accessible for expired trial (read-only).

        Note: sessions route uses database.get_db (not supabase_client.get_supabase).
        """
        expired_quota = _make_expired_trial_quota()

        mock_result = MagicMock()
        mock_result.data = []

        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result

        from database import get_db
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("quota.check_quota", return_value=expired_quota), \
                 patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False):
                response = client.get("/sessions")

            assert response.status_code == 200
        finally:
            # Restore only auth override (autouse fixture clears all at end)
            if get_db in app.dependency_overrides:
                del app.dependency_overrides[get_db]


# ============================================================================
# AC21: Paid plan bypasses block on all endpoints
# ============================================================================

class TestPaidPlanBypass:
    """AC21: Verify paid plans are NOT affected by trial block logic."""

    @pytest.mark.asyncio
    async def test_paid_plan_can_post_buscar(self):
        """AC21: POST /buscar succeeds for paid plan (not blocked by require_active_plan).

        We directly test require_active_plan to confirm paid plans pass through,
        avoiding the full endpoint mock complexity.
        """
        from quota import require_active_plan

        paid_quota = _make_paid_plan_quota()
        user = {"id": "test-trial-user", "email": "trial@example.com"}

        with patch("quota.check_quota", return_value=paid_quota), \
             patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False):
            result = await require_active_plan(user)

        # Should pass through without raising HTTPException 403
        assert result == user

    def test_paid_plan_can_post_pipeline(self, client):
        """AC21: POST /pipeline succeeds for paid plan."""
        paid_quota = _make_paid_plan_quota()

        mock_result = MagicMock()
        mock_result.data = {
            "id": "new-item-id",
            "user_id": "test-trial-user",
            "pncp_id": "12345678000100-1-000001/2026",
            "objeto": "Test procurement",
            "orgao": "Test Agency",
            "uf": "SP",
            "valor_estimado": 100000,
            "stage": "descoberta",
            "notes": None,
            "created_at": "2026-02-20T10:00:00+00:00",
            "updated_at": "2026-02-20T10:00:00+00:00",
        }

        with patch("quota.check_quota", return_value=paid_quota), \
             patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False), \
             patch("routes.pipeline.get_supabase") as mock_supa:
            mock_supa.return_value.table.return_value.insert.return_value.execute.return_value = mock_result
            response = client.post(
                "/pipeline",
                json={
                    "pncp_id": "12345678000100-1-000001/2026",
                    "objeto": "Test procurement",
                    "orgao": "Test Agency",
                    "uf": "SP",
                    "valor_estimado": 100000,
                },
            )

        # Should NOT be 403
        assert response.status_code != 403
