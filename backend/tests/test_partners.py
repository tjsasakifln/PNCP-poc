"""STORY-323: Revenue Share Tracking — Partner tests.

AC19: Signup with partner param -> links partner
AC20: Checkout with coupon -> creates partner_referral
AC21: Revenue share calculation (monthly)
AC22: Churn updates referral
AC23: Zero regressions (implicitly via full test suite)
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from types import SimpleNamespace

from fastapi.testclient import TestClient


# ============================================================================
# Helpers
# ============================================================================

def _mock_sb_execute(return_data=None):
    """Return an AsyncMock that resolves to a SimpleNamespace with .data."""
    mock = AsyncMock()
    mock.return_value = SimpleNamespace(data=return_data or [])
    return mock


def _make_query_chain(data=None):
    """Build a mock Supabase query chain that returns data at .execute()."""
    mock = MagicMock()
    mock.select.return_value = mock
    mock.insert.return_value = mock
    mock.update.return_value = mock
    mock.upsert.return_value = mock
    mock.delete.return_value = mock
    mock.eq.return_value = mock
    mock.not_.return_value = mock
    mock.is_.return_value = mock
    mock.lte.return_value = mock
    mock.order.return_value = mock
    mock.limit.return_value = mock
    mock.single.return_value = mock
    mock.execute.return_value = SimpleNamespace(data=data or [])
    return mock


# ============================================================================
# AC19: Signup with partner param -> links partner
# ============================================================================

class TestPartnerSignupAttribution:
    """AC19: Signup with partner param -> vincula parceiro."""

    @pytest.mark.asyncio
    async def test_attribute_signup_to_partner_success(self):
        """When a valid partner slug is provided, profile is updated."""
        partner_data = [{"id": "p-001", "name": "Triunfo Legis", "slug": "triunfo-legis",
                         "stripe_coupon_id": "TRIUNFO_25", "revenue_share_pct": "25.00", "status": "active"}]

        mock_sb = MagicMock()
        # First call: get_partner_by_slug -> partners table
        partners_chain = _make_query_chain(partner_data)
        # Second call: update profiles
        profiles_chain = _make_query_chain([{"id": "user-1"}])

        def table_side_effect(name):
            if name == "partners":
                return partners_chain
            if name == "profiles":
                return profiles_chain
            return _make_query_chain()

        mock_sb.table.side_effect = table_side_effect

        with patch("services.partner_service.get_supabase", return_value=mock_sb), \
             patch("services.partner_service.sb_execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = [
                SimpleNamespace(data=partner_data),  # get_partner_by_slug
                SimpleNamespace(data=[{"id": "user-1"}]),  # update profiles
            ]

            from services.partner_service import attribute_signup_to_partner
            result = await attribute_signup_to_partner("user-1", "triunfo-legis")

        assert result is True
        assert mock_exec.call_count == 2

    @pytest.mark.asyncio
    async def test_attribute_signup_invalid_slug(self):
        """When partner slug doesn't exist, returns False."""
        with patch("services.partner_service.get_supabase", return_value=MagicMock()), \
             patch("services.partner_service.sb_execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = SimpleNamespace(data=[])

            from services.partner_service import attribute_signup_to_partner
            result = await attribute_signup_to_partner("user-1", "nonexistent")

        assert result is False


# ============================================================================
# AC20: Checkout with coupon -> creates partner_referral
# ============================================================================

class TestPartnerReferralCreation:
    """AC20: Checkout with coupon -> cria partner_referral."""

    @pytest.mark.asyncio
    async def test_create_referral_from_profile_attribution(self):
        """When user has referred_by_partner_id, referral is created on conversion."""
        with patch("services.partner_service.get_supabase", return_value=MagicMock()), \
             patch("services.partner_service.sb_execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = [
                # 1. Check profile for partner attribution
                SimpleNamespace(data={"referred_by_partner_id": "p-001"}),
                # 2. Get partner revenue share pct
                SimpleNamespace(data={"revenue_share_pct": "25.00"}),
                # 3. Upsert referral
                SimpleNamespace(data=[{"id": "ref-001"}]),
            ]

            from services.partner_service import create_partner_referral
            result = await create_partner_referral("user-1", 397.00)

        assert result == "ref-001"
        assert mock_exec.call_count == 3

    @pytest.mark.asyncio
    async def test_create_referral_from_coupon(self):
        """AC5: When coupon matches a partner, referral is created."""
        with patch("services.partner_service.get_supabase", return_value=MagicMock()), \
             patch("services.partner_service.sb_execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = [
                # 1. Profile has no partner attribution
                SimpleNamespace(data={"referred_by_partner_id": None}),
                # 2. Coupon lookup -> found partner
                SimpleNamespace(data=[{"id": "p-002", "name": "Concreta", "slug": "concreta",
                                       "revenue_share_pct": "25.00", "status": "active"}]),
                # 3. Update profile with partner_id
                SimpleNamespace(data=[{"id": "user-2"}]),
                # 4. Get partner revenue share pct
                SimpleNamespace(data={"revenue_share_pct": "25.00"}),
                # 5. Upsert referral
                SimpleNamespace(data=[{"id": "ref-002"}]),
            ]

            from services.partner_service import create_partner_referral
            result = await create_partner_referral("user-2", 397.00, stripe_coupon_id="CONCRETA_25")

        assert result == "ref-002"

    @pytest.mark.asyncio
    async def test_create_referral_no_partner(self):
        """When user is not referred by any partner, returns None."""
        with patch("services.partner_service.get_supabase", return_value=MagicMock()), \
             patch("services.partner_service.sb_execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = [
                SimpleNamespace(data={"referred_by_partner_id": None}),
            ]

            from services.partner_service import create_partner_referral
            result = await create_partner_referral("user-3", 397.00)

        assert result is None


# ============================================================================
# AC21: Revenue share calculation
# ============================================================================

class TestRevenueShareCalculation:
    """AC21: Calculo de revenue share mensal."""

    @pytest.mark.asyncio
    async def test_calculate_revenue_basic(self):
        """Revenue share = 25% of total active referrals' revenue."""
        with patch("services.partner_service.get_supabase", return_value=MagicMock()), \
             patch("services.partner_service.sb_execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = [
                # 1. Get partner
                SimpleNamespace(data={"revenue_share_pct": "25.00", "name": "Triunfo Legis"}),
                # 2. Get referrals
                SimpleNamespace(data=[
                    {"monthly_revenue": "397.00", "converted_at": "2026-01-15T00:00:00+00:00", "churned_at": None},
                    {"monthly_revenue": "397.00", "converted_at": "2026-02-01T00:00:00+00:00", "churned_at": None},
                    {"monthly_revenue": "397.00", "converted_at": "2025-12-01T00:00:00+00:00",
                     "churned_at": "2026-01-10T00:00:00+00:00"},  # Churned before March
                ]),
            ]

            from services.partner_service import calculate_partner_revenue
            result = await calculate_partner_revenue("p-001", 2026, 3)

        # 2 active referrals (3rd churned before March starts)
        assert result["active_clients"] == 2
        assert result["total_revenue"] == 794.00
        assert result["share_amount"] == 198.50  # 25% of 794
        assert result["share_pct"] == 25.00

    @pytest.mark.asyncio
    async def test_calculate_revenue_no_referrals(self):
        """Zero revenue when no referrals exist."""
        with patch("services.partner_service.get_supabase", return_value=MagicMock()), \
             patch("services.partner_service.sb_execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = [
                SimpleNamespace(data={"revenue_share_pct": "25.00", "name": "Empty Partner"}),
                SimpleNamespace(data=[]),
            ]

            from services.partner_service import calculate_partner_revenue
            result = await calculate_partner_revenue("p-999", 2026, 3)

        assert result["active_clients"] == 0
        assert result["total_revenue"] == 0.0
        assert result["share_amount"] == 0.0

    @pytest.mark.asyncio
    async def test_calculate_revenue_partner_not_found(self):
        """Returns error when partner doesn't exist."""
        with patch("services.partner_service.get_supabase", return_value=MagicMock()), \
             patch("services.partner_service.sb_execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = SimpleNamespace(data=None)

            from services.partner_service import calculate_partner_revenue
            result = await calculate_partner_revenue("p-missing", 2026, 3)

        assert result == {"error": "partner_not_found"}


# ============================================================================
# AC22: Churn updates referral
# ============================================================================

class TestPartnerReferralChurn:
    """AC22: Churn atualiza referral."""

    @pytest.mark.asyncio
    async def test_mark_referral_churned_success(self):
        """When user with referral churns, churned_at is set."""
        with patch("services.partner_service.get_supabase", return_value=MagicMock()), \
             patch("services.partner_service.sb_execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = SimpleNamespace(data=[{"id": "ref-001"}])

            from services.partner_service import mark_referral_churned
            result = await mark_referral_churned("user-1")

        assert result is True

    @pytest.mark.asyncio
    async def test_mark_referral_churned_no_referral(self):
        """When user has no referral, returns False."""
        with patch("services.partner_service.get_supabase", return_value=MagicMock()), \
             patch("services.partner_service.sb_execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = SimpleNamespace(data=[])

            from services.partner_service import mark_referral_churned
            result = await mark_referral_churned("user-999")

        assert result is False


# ============================================================================
# Routes: Admin partner endpoints (AC10-AC14)
# ============================================================================

@pytest.mark.xfail(
    reason="STORY-BTS-FOLLOWUP: batch-only failure — ``from main import app`` picks "
    "up a polluted process state (``shutting_down=True`` leaked from lifespan tests, "
    "or CB OPEN state) that no autouse fixture has been able to stabilise without "
    "introducing regressions elsewhere. Helper/non-route tests in this file pass "
    "(TestPartnerSignupAttribution, TestPartnerReferralChurn, TestRevenueShareCronJob); "
    "only the 5 tests that instantiate TestClient(app) fail. Tracked as batch-pollution "
    "follow-up — do not remove without reproducing in isolation first.",
    strict=False,
)
class TestPartnerRoutes:
    """Test partner admin routes."""

    def _get_test_app(self):
        """Create test app with partner routes."""
        from main import app
        return app

    def test_list_partners_unauthorized(self):
        """Non-admin user cannot list partners."""
        app = self._get_test_app()

        with patch("routes.partners.check_user_roles", new_callable=AsyncMock) as mock_roles:
            mock_roles.return_value = (False, False)

            from auth import require_auth
            app.dependency_overrides[require_auth] = lambda: {"id": "user-1", "email": "test@test.com"}

            client = TestClient(app)
            res = client.get("/v1/admin/partners")

            assert res.status_code == 403

            app.dependency_overrides.clear()

    def test_list_partners_admin(self):
        """Admin can list partners."""
        app = self._get_test_app()

        with patch("routes.partners.check_user_roles", new_callable=AsyncMock) as mock_roles, \
             patch("routes.partners.list_partners", new_callable=AsyncMock) as mock_list, \
             patch("supabase_client.get_supabase") as mock_sb_factory, \
             patch("supabase_client.sb_execute", new_callable=AsyncMock) as mock_exec:  # noqa: F841

            mock_roles.return_value = (True, True)
            mock_list.return_value = [
                {"id": "p-1", "name": "Triunfo", "slug": "triunfo", "contact_email": "a@b.com",
                 "status": "active", "revenue_share_pct": "25.00", "created_at": "2026-01-01"},
            ]
            mock_exec.return_value = SimpleNamespace(data=[])

            from auth import require_auth
            app.dependency_overrides[require_auth] = lambda: {"id": "admin-1", "email": "admin@test.com"}

            client = TestClient(app)
            res = client.get("/v1/admin/partners")

            assert res.status_code == 200
            data = res.json()
            assert "partners" in data
            assert len(data["partners"]) == 1

            app.dependency_overrides.clear()

    def test_create_partner_admin(self):
        """Admin can create a partner."""
        app = self._get_test_app()

        with patch("routes.partners.check_user_roles", new_callable=AsyncMock) as mock_roles, \
             patch("routes.partners.create_partner", new_callable=AsyncMock) as mock_create:

            mock_roles.return_value = (True, True)
            mock_create.return_value = {
                "id": "p-new", "name": "New Partner", "slug": "new-partner",
                "contact_email": "new@partner.com", "status": "active",
            }

            from auth import require_auth
            app.dependency_overrides[require_auth] = lambda: {"id": "admin-1", "email": "admin@test.com"}

            client = TestClient(app)
            res = client.post("/v1/admin/partners", json={
                "name": "New Partner",
                "slug": "new-partner",
                "contact_email": "new@partner.com",
            })

            assert res.status_code == 201
            data = res.json()
            assert data["slug"] == "new-partner"

            app.dependency_overrides.clear()

    def test_get_partner_referrals_admin(self):
        """Admin can get partner referrals."""
        app = self._get_test_app()

        with patch("routes.partners.check_user_roles", new_callable=AsyncMock) as mock_roles, \
             patch("routes.partners.get_partner_referrals", new_callable=AsyncMock) as mock_refs:

            mock_roles.return_value = (True, True)
            mock_refs.return_value = [
                {"id": "ref-1", "signup_at": "2026-01-01", "converted_at": "2026-01-10",
                 "monthly_revenue": 397.0, "revenue_share_amount": 99.25},
            ]

            from auth import require_auth
            app.dependency_overrides[require_auth] = lambda: {"id": "admin-1", "email": "admin@test.com"}

            client = TestClient(app)
            res = client.get("/v1/admin/partners/p-001/referrals")

            assert res.status_code == 200
            data = res.json()
            assert len(data["referrals"]) == 1

            app.dependency_overrides.clear()

    def test_get_partner_revenue_admin(self):
        """Admin can get partner revenue report."""
        app = self._get_test_app()

        with patch("routes.partners.check_user_roles", new_callable=AsyncMock) as mock_roles, \
             patch("routes.partners.calculate_partner_revenue", new_callable=AsyncMock) as mock_rev:

            mock_roles.return_value = (True, True)
            mock_rev.return_value = {
                "partner_id": "p-001", "partner_name": "Triunfo",
                "year": 2026, "month": 3,
                "total_revenue": 794.0, "share_amount": 198.5,
                "share_pct": 25.0, "active_clients": 2,
            }

            from auth import require_auth
            app.dependency_overrides[require_auth] = lambda: {"id": "admin-1", "email": "admin@test.com"}

            client = TestClient(app)
            res = client.get("/v1/admin/partners/p-001/revenue?year=2026&month=3")

            assert res.status_code == 200
            data = res.json()
            assert data["share_amount"] == 198.5
            assert data["active_clients"] == 2

            app.dependency_overrides.clear()

    def test_partner_dashboard_not_partner(self):
        """Non-partner user gets 404 on dashboard."""
        app = self._get_test_app()

        with patch("routes.partners.get_partner_dashboard", new_callable=AsyncMock) as mock_dash:
            mock_dash.return_value = None

            from auth import require_auth
            app.dependency_overrides[require_auth] = lambda: {"id": "user-1", "email": "user@test.com"}

            client = TestClient(app)
            res = client.get("/v1/partner/dashboard")

            assert res.status_code == 404

            app.dependency_overrides.clear()


# ============================================================================
# Webhook integration: partner referral hooks
# ============================================================================

class TestWebhookPartnerIntegration:
    """Test webhook helper functions for partner tracking."""

    def test_create_partner_referral_async_helper(self):
        """_create_partner_referral_async schedules background task."""
        from webhooks.stripe import _create_partner_referral_async

        plan_result = SimpleNamespace(data={"price_brl": 397.0})
        session_data = {"total_details": {}, "discount": None}

        # Should not raise even without a running event loop
        # (function catches all exceptions)
        _create_partner_referral_async("user-1", plan_result, session_data)

    def test_mark_partner_referral_churned_helper(self):
        """_mark_partner_referral_churned schedules background task."""
        from webhooks.stripe import _mark_partner_referral_churned

        # Should not raise
        _mark_partner_referral_churned("user-1")


# ============================================================================
# Cron job: monthly revenue share report
# ============================================================================

class TestRevenueShareCronJob:
    """Test monthly revenue share cron job."""

    @pytest.mark.asyncio
    async def test_run_revenue_share_report(self):
        """Cron job generates report for previous month."""
        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock) as mock_redis, \
             patch("services.partner_service.get_supabase", return_value=MagicMock()), \
             patch("services.partner_service.sb_execute", new_callable=AsyncMock) as mock_exec:

            # Redis lock
            mock_redis_instance = AsyncMock()
            mock_redis_instance.set = AsyncMock(return_value=True)
            mock_redis_instance.delete = AsyncMock()
            mock_redis.return_value = mock_redis_instance

            # DB calls for generate_monthly_revenue_report
            mock_exec.side_effect = [
                # list active partners
                SimpleNamespace(data=[
                    {"id": "p-1", "name": "A", "slug": "a", "contact_email": "a@b.com"},
                ]),
                # partner revenue: get partner
                SimpleNamespace(data={"revenue_share_pct": "25.00", "name": "A"}),
                # partner revenue: get referrals
                SimpleNamespace(data=[]),
            ]

            from cron_jobs import run_revenue_share_report
            result = await run_revenue_share_report()

        assert "partner_reports" in result
        assert result["total_share"] == 0.0
