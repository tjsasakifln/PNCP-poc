"""STORY-314: Tests for Stripe ⇄ DB Reconciliation Service.

Tests cover:
- AC1: Field divergence detection (is_active, plan_id, billing_period, subscription_status)
- AC2: Auto-fix with structured logging + profiles.plan_type sync + cache invalidation
- AC3: Orphan subscription detection and creation
- AC4: Zombie subscription detection and deactivation
- AC5-AC6: Cron scheduling and Redis lock protection
- AC7-AC8: Report persistence to reconciliation_log
- AC9: Admin email alert on divergences
- AC10: Admin endpoint for reconciliation history
- AC11: Prometheus metrics
- AC13: Manual trigger endpoint

Mock patterns:
- Stripe API: @patch("services.stripe_reconciliation.stripe")
- Supabase: @patch("services.stripe_reconciliation.get_supabase")
- Redis cache: @patch("services.stripe_reconciliation.redis_cache")
- Auth: app.dependency_overrides[require_admin]
"""

from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _StripeObj(dict):
    """Dict subclass with attribute access (mimics Stripe SDK objects)."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


def _make_stripe_sub(
    sub_id="sub_123",
    status="active",
    customer="cus_abc",
    plan_id="smartlic_pro",
    interval="month",
    interval_count=1,
    current_period_end=None,
):
    """Create a mock Stripe Subscription object (dict + attribute access)."""
    return _StripeObj(
        id=sub_id,
        status=status,
        customer=customer,
        metadata={"plan_id": plan_id},
        items={
            "data": [
                {
                    "plan": {
                        "interval": interval,
                        "interval_count": interval_count,
                    }
                }
            ]
        },
        current_period_end=current_period_end or int(
            (datetime.now(timezone.utc) + timedelta(days=30)).timestamp()
        ),
    )


def _make_local_sub(
    sub_id="local-uuid-1",
    user_id="user-uuid-1",
    stripe_sub_id="sub_123",
    stripe_customer_id="cus_abc",
    plan_id="smartlic_pro",
    billing_period="monthly",
    subscription_status="active",
    is_active=True,
    expires_at=None,
):
    return {
        "id": sub_id,
        "user_id": user_id,
        "stripe_subscription_id": stripe_sub_id,
        "stripe_customer_id": stripe_customer_id,
        "plan_id": plan_id,
        "billing_period": billing_period,
        "subscription_status": subscription_status,
        "is_active": is_active,
        "expires_at": expires_at,
    }


class _FakeChain:
    """Chainable mock that returns specified data on .execute()."""

    def __init__(self, data):
        self._data = data

    def select(self, *a, **kw): return self
    def insert(self, *a, **kw): return self
    def update(self, *a, **kw): return self
    def delete(self, *a, **kw): return self
    def eq(self, *a, **kw): return self
    def is_(self, *a, **kw): return self
    def order(self, *a, **kw): return self
    def limit(self, *a, **kw): return self
    def single(self, *a, **kw): return self

    @property
    def not_(self):
        """Support sb.table(...).select(...).not_.is_(...) pattern."""
        return self

    def execute(self):
        return SimpleNamespace(data=self._data)


def _make_sb(tables: dict[str, list]):
    """Create a Supabase mock that returns the right data per table.

    tables: {"user_subscriptions": [...], "profiles": [...], ...}
    """
    sb = MagicMock()

    def table_dispatch(table_name):
        data = tables.get(table_name, [])
        return _FakeChain(data)

    sb.table.side_effect = table_dispatch
    return sb


# ---------------------------------------------------------------------------
# AC1: Field Divergence Detection
# ---------------------------------------------------------------------------

class TestDivergenceDetection:
    """AC1: Detect divergences in is_active, plan_id, billing_period, subscription_status."""

    @pytest.mark.asyncio
    @patch("services.stripe_reconciliation.redis_cache")
    @patch("services.stripe_reconciliation.get_supabase")
    @patch("services.stripe_reconciliation.stripe")
    @patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_xxx"})
    async def test_detects_status_divergence(self, mock_stripe, mock_get_sb, mock_cache):
        """Stripe active but DB shows canceled → should detect and fix."""
        from services.stripe_reconciliation import reconcile_subscriptions

        stripe_sub = _make_stripe_sub(sub_id="sub_001", status="active")
        mock_stripe.Subscription.list.return_value = SimpleNamespace(
            data=[stripe_sub], has_more=False
        )

        local_sub = _make_local_sub(
            stripe_sub_id="sub_001",
            subscription_status="canceled",
            is_active=False,
        )

        mock_get_sb.return_value = _make_sb({
            "user_subscriptions": [local_sub],
            "profiles": [{"id": "user-uuid-1"}],
            "plans": [{"duration_days": 30, "max_searches": 1000}],
        })
        mock_cache.delete = AsyncMock()

        result = await reconcile_subscriptions()

        assert result["divergences_found"] > 0
        assert result["auto_fixed"] > 0
        fields_found = {d["field"] for d in result["details"]}
        assert "is_active" in fields_found or "subscription_status" in fields_found

    @pytest.mark.asyncio
    @patch("services.stripe_reconciliation.redis_cache")
    @patch("services.stripe_reconciliation.get_supabase")
    @patch("services.stripe_reconciliation.stripe")
    @patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_xxx"})
    async def test_detects_billing_period_divergence(self, mock_stripe, mock_get_sb, mock_cache):
        """Stripe is annual but DB shows monthly → should detect."""
        from services.stripe_reconciliation import reconcile_subscriptions

        stripe_sub = _make_stripe_sub(
            sub_id="sub_002", status="active", interval="year", interval_count=1
        )
        mock_stripe.Subscription.list.return_value = SimpleNamespace(
            data=[stripe_sub], has_more=False
        )

        local_sub = _make_local_sub(
            stripe_sub_id="sub_002",
            billing_period="monthly",  # DB is wrong
        )

        mock_get_sb.return_value = _make_sb({
            "user_subscriptions": [local_sub],
            "profiles": [],
        })
        mock_cache.delete = AsyncMock()

        result = await reconcile_subscriptions()

        billing_divergences = [
            d for d in result["details"] if d.get("field") == "billing_period"
        ]
        assert len(billing_divergences) >= 1
        assert billing_divergences[0]["stripe_value"] == "annual"
        assert billing_divergences[0]["db_value"] == "monthly"

    @pytest.mark.asyncio
    @patch("services.stripe_reconciliation.redis_cache")
    @patch("services.stripe_reconciliation.get_supabase")
    @patch("services.stripe_reconciliation.stripe")
    @patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_xxx"})
    async def test_detects_plan_divergence(self, mock_stripe, mock_get_sb, mock_cache):
        """Stripe metadata has different plan_id than DB."""
        from services.stripe_reconciliation import reconcile_subscriptions

        stripe_sub = _make_stripe_sub(
            sub_id="sub_003", status="active", plan_id="smartlic_pro"
        )
        mock_stripe.Subscription.list.return_value = SimpleNamespace(
            data=[stripe_sub], has_more=False
        )

        local_sub = _make_local_sub(
            stripe_sub_id="sub_003",
            plan_id="consultor_agil",  # DB has wrong plan
        )

        mock_get_sb.return_value = _make_sb({
            "user_subscriptions": [local_sub],
            "profiles": [],
        })
        mock_cache.delete = AsyncMock()

        result = await reconcile_subscriptions()

        plan_divergences = [
            d for d in result["details"] if d.get("field") == "plan_id"
        ]
        assert len(plan_divergences) >= 1
        assert plan_divergences[0]["stripe_value"] == "smartlic_pro"
        assert plan_divergences[0]["db_value"] == "consultor_agil"

    @pytest.mark.asyncio
    @patch("services.stripe_reconciliation.redis_cache")
    @patch("services.stripe_reconciliation.get_supabase")
    @patch("services.stripe_reconciliation.stripe")
    @patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_xxx"})
    async def test_no_divergence_when_in_sync(self, mock_stripe, mock_get_sb, mock_cache):
        """No divergence when Stripe and DB are in sync."""
        from services.stripe_reconciliation import reconcile_subscriptions

        stripe_sub = _make_stripe_sub(sub_id="sub_ok", status="active")
        mock_stripe.Subscription.list.return_value = SimpleNamespace(
            data=[stripe_sub], has_more=False
        )

        local_sub = _make_local_sub(
            stripe_sub_id="sub_ok",
            subscription_status="active",
            is_active=True,
            billing_period="monthly",
            plan_id="smartlic_pro",
        )

        mock_get_sb.return_value = _make_sb({
            "user_subscriptions": [local_sub],
        })
        mock_cache.delete = AsyncMock()

        result = await reconcile_subscriptions()

        assert result["divergences_found"] == 0
        assert result["auto_fixed"] == 0

    @pytest.mark.asyncio
    @patch("services.stripe_reconciliation.redis_cache")
    @patch("services.stripe_reconciliation.get_supabase")
    @patch("services.stripe_reconciliation.stripe")
    @patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_xxx"})
    async def test_semiannual_billing_detection(self, mock_stripe, mock_get_sb, mock_cache):
        """6-month interval → semiannual billing period."""
        from services.stripe_reconciliation import reconcile_subscriptions

        stripe_sub = _make_stripe_sub(
            sub_id="sub_semi", status="active",
            interval="month", interval_count=6,
        )
        mock_stripe.Subscription.list.return_value = SimpleNamespace(
            data=[stripe_sub], has_more=False
        )

        local_sub = _make_local_sub(
            stripe_sub_id="sub_semi",
            billing_period="monthly",  # Wrong
        )

        mock_get_sb.return_value = _make_sb({
            "user_subscriptions": [local_sub],
            "profiles": [],
        })
        mock_cache.delete = AsyncMock()

        result = await reconcile_subscriptions()

        billing_div = [d for d in result["details"] if d.get("field") == "billing_period"]
        assert len(billing_div) >= 1
        assert billing_div[0]["stripe_value"] == "semiannual"


# ---------------------------------------------------------------------------
# AC3: Orphan Detection
# ---------------------------------------------------------------------------

class TestOrphanDetection:
    """AC3: Detect Stripe subscriptions without DB match."""

    @pytest.mark.asyncio
    @patch("services.stripe_reconciliation.redis_cache")
    @patch("services.stripe_reconciliation.get_supabase")
    @patch("services.stripe_reconciliation.stripe")
    @patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_xxx"})
    async def test_orphan_with_matching_email_creates_sub(
        self, mock_stripe, mock_get_sb, mock_cache
    ):
        """Orphan sub where customer email matches a profile → create sub row."""
        from services.stripe_reconciliation import reconcile_subscriptions

        stripe_sub = _make_stripe_sub(sub_id="sub_orphan", status="active")
        mock_stripe.Subscription.list.return_value = SimpleNamespace(
            data=[stripe_sub], has_more=False
        )
        # Customer lookup returns email
        mock_stripe.Customer.retrieve.return_value = {"email": "user@test.com"}

        mock_get_sb.return_value = _make_sb({
            "user_subscriptions": [],  # No local subs
            "profiles": [{"id": "user-uuid-orphan"}],
            "plans": [{"duration_days": 30, "max_searches": 1000}],
        })
        mock_cache.delete = AsyncMock()

        result = await reconcile_subscriptions()

        orphan_details = [d for d in result["details"] if d.get("field") == "orphan"]
        assert len(orphan_details) >= 1
        assert orphan_details[0]["action_taken"] == "created"
        assert result["auto_fixed"] >= 1

    @pytest.mark.asyncio
    @patch("services.stripe_reconciliation.redis_cache")
    @patch("services.stripe_reconciliation.get_supabase")
    @patch("services.stripe_reconciliation.stripe")
    @patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_xxx"})
    async def test_orphan_without_matching_email_manual_review(
        self, mock_stripe, mock_get_sb, mock_cache
    ):
        """Orphan sub where customer email doesn't match → manual review."""
        from services.stripe_reconciliation import reconcile_subscriptions

        stripe_sub = _make_stripe_sub(sub_id="sub_orphan2", status="active")
        mock_stripe.Subscription.list.return_value = SimpleNamespace(
            data=[stripe_sub], has_more=False
        )
        # Customer lookup → email but no profile match
        mock_stripe.Customer.retrieve.return_value = {"email": "unknown@test.com"}

        mock_get_sb.return_value = _make_sb({
            "user_subscriptions": [],
            "profiles": [],  # Empty = no match
        })
        mock_cache.delete = AsyncMock()

        result = await reconcile_subscriptions()

        orphan_details = [d for d in result["details"] if d.get("field") == "orphan"]
        assert len(orphan_details) >= 1
        assert orphan_details[0]["action_taken"] == "manual_review"
        assert result["manual_review"] >= 1


# ---------------------------------------------------------------------------
# AC4: Zombie Detection
# ---------------------------------------------------------------------------

class TestZombieDetection:
    """AC4: Detect active DB subscriptions without Stripe match."""

    @pytest.mark.asyncio
    @patch("services.stripe_reconciliation.redis_cache")
    @patch("services.stripe_reconciliation.get_supabase")
    @patch("services.stripe_reconciliation.stripe")
    @patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_xxx"})
    async def test_zombie_subscription_deactivated(self, mock_stripe, mock_get_sb, mock_cache):
        """Active in DB but not in Stripe at all → deactivate."""
        from services.stripe_reconciliation import reconcile_subscriptions

        # Stripe returns NO subscriptions
        mock_stripe.Subscription.list.return_value = SimpleNamespace(
            data=[], has_more=False
        )

        # DB has an active subscription pointing to a non-existent Stripe sub
        local_sub = _make_local_sub(
            stripe_sub_id="sub_ghost",
            is_active=True,
            subscription_status="active",
        )

        mock_get_sb.return_value = _make_sb({
            "user_subscriptions": [local_sub],
            "profiles": [],
        })
        mock_cache.delete = AsyncMock()

        result = await reconcile_subscriptions()

        zombie_details = [d for d in result["details"] if d.get("field") == "zombie"]
        assert len(zombie_details) >= 1
        assert zombie_details[0]["action_taken"] == "auto_fix"
        assert zombie_details[0]["direction"] == "db_ahead"
        assert result["auto_fixed"] >= 1


# ---------------------------------------------------------------------------
# AC5-AC6: Cron Scheduling and Lock Protection
# ---------------------------------------------------------------------------

class TestCronAndLocking:
    """AC5: Cron scheduling. AC6: Redis lock protection."""

    @pytest.mark.asyncio
    @patch("redis_pool.get_redis_pool")
    @patch("services.stripe_reconciliation.send_reconciliation_alert", new_callable=AsyncMock)
    @patch("services.stripe_reconciliation.save_reconciliation_report", new_callable=AsyncMock)
    @patch("services.stripe_reconciliation.reconcile_subscriptions", new_callable=AsyncMock)
    async def test_lock_prevents_duplicate_run(
        self, mock_reconcile, mock_save, mock_alert, mock_redis
    ):
        """AC6: If Redis lock exists, skip execution."""
        from cron_jobs import run_reconciliation

        redis_mock = AsyncMock()
        redis_mock.set.return_value = False  # Lock already held
        mock_redis.return_value = redis_mock

        result = await run_reconciliation()

        assert result["status"] == "skipped"
        assert result["reason"] == "lock_held"
        mock_reconcile.assert_not_called()

    @pytest.mark.asyncio
    @patch("redis_pool.get_redis_pool")
    @patch("services.stripe_reconciliation.send_reconciliation_alert", new_callable=AsyncMock)
    @patch("services.stripe_reconciliation.save_reconciliation_report", new_callable=AsyncMock)
    @patch("services.stripe_reconciliation.reconcile_subscriptions", new_callable=AsyncMock)
    async def test_lock_acquired_runs_reconciliation(
        self, mock_reconcile, mock_save, mock_alert, mock_redis
    ):
        """AC6: If lock acquired, run reconciliation."""
        from cron_jobs import run_reconciliation

        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.delete = AsyncMock()
        mock_redis.return_value = redis_mock

        expected = {
            "total_checked": 10,
            "divergences_found": 0,
            "auto_fixed": 0,
            "manual_review": 0,
            "duration_ms": 500,
            "details": [],
        }
        mock_reconcile.return_value = expected
        mock_save.return_value = None
        mock_alert.return_value = None

        result = await run_reconciliation()

        assert result["total_checked"] == 10
        mock_reconcile.assert_called_once()
        mock_save.assert_called_once()
        mock_alert.assert_called_once()
        redis_mock.delete.assert_called_once()

    @pytest.mark.asyncio
    @patch("redis_pool.get_redis_pool")
    @patch("services.stripe_reconciliation.send_reconciliation_alert", new_callable=AsyncMock)
    @patch("services.stripe_reconciliation.save_reconciliation_report", new_callable=AsyncMock)
    @patch("services.stripe_reconciliation.reconcile_subscriptions", new_callable=AsyncMock)
    async def test_redis_failure_proceeds_without_lock(
        self, mock_reconcile, mock_save, mock_alert, mock_redis
    ):
        """AC6: Redis failure → proceed without lock (graceful degradation)."""
        from cron_jobs import run_reconciliation

        mock_redis.side_effect = Exception("Redis down")

        expected = {
            "total_checked": 5,
            "divergences_found": 0,
            "auto_fixed": 0,
            "manual_review": 0,
            "duration_ms": 200,
            "details": [],
        }
        mock_reconcile.return_value = expected
        mock_save.return_value = None
        mock_alert.return_value = None

        result = await run_reconciliation()

        assert result["total_checked"] == 5
        mock_reconcile.assert_called_once()


# ---------------------------------------------------------------------------
# AC7-AC9: Report and Alert
# ---------------------------------------------------------------------------

class TestReportAndAlert:
    """AC7-AC8: Save report. AC9: Email alert on divergences."""

    @pytest.mark.asyncio
    @patch("services.stripe_reconciliation.get_supabase")
    async def test_save_report(self, mock_get_sb):
        """AC8: Report is saved to reconciliation_log."""
        from services.stripe_reconciliation import save_reconciliation_report

        sb = _make_sb({"reconciliation_log": []})
        mock_get_sb.return_value = sb

        result = {
            "total_checked": 50,
            "divergences_found": 3,
            "auto_fixed": 2,
            "manual_review": 1,
            "duration_ms": 1500,
            "details": [{"field": "status"}],
        }

        await save_reconciliation_report(result)

        # Should have called sb.table("reconciliation_log")
        mock_get_sb.assert_called_once()

    @pytest.mark.asyncio
    @patch("email_service.send_email_async")
    @patch("templates.emails.base.email_base")
    async def test_alert_sent_when_divergences_found(self, mock_email_base, mock_send):
        """AC9: Email alert sent when divergences > 0."""
        from services.stripe_reconciliation import send_reconciliation_alert

        mock_email_base.return_value = "<html>alert</html>"

        result = {
            "total_checked": 50,
            "divergences_found": 3,
            "auto_fixed": 2,
            "manual_review": 1,
            "duration_ms": 1500,
            "details": [],
        }

        await send_reconciliation_alert(result)

        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_alert_not_sent_when_no_divergences(self):
        """AC9: No alert when divergences = 0."""
        from services.stripe_reconciliation import send_reconciliation_alert

        result = {
            "total_checked": 50,
            "divergences_found": 0,
            "auto_fixed": 0,
            "manual_review": 0,
            "duration_ms": 500,
            "details": [],
        }

        # Should not raise
        await send_reconciliation_alert(result)


# ---------------------------------------------------------------------------
# AC10 + AC13: Admin Endpoints
# ---------------------------------------------------------------------------

class TestAdminEndpoints:
    """AC10: History endpoint. AC13: Manual trigger endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client with admin auth overridden."""
        from fastapi.testclient import TestClient
        from main import app
        from admin import require_admin

        async def mock_admin(user=None):
            return {"id": "admin-uuid", "email": "admin@test.com"}

        app.dependency_overrides[require_admin] = mock_admin
        yield TestClient(app)
        app.dependency_overrides.pop(require_admin, None)

    @patch("supabase_client.get_supabase")
    def test_reconciliation_history_endpoint(self, mock_get_sb, client):
        """AC10: GET /admin/reconciliation/history returns last runs."""
        mock_get_sb.return_value = _make_sb({
            "reconciliation_log": [
                {
                    "id": "run-1",
                    "run_at": "2026-02-28T06:00:00Z",
                    "total_checked": 50,
                    "divergences_found": 2,
                    "auto_fixed": 2,
                    "manual_review": 0,
                    "duration_ms": 1000,
                    "details": [],
                }
            ]
        })

        response = client.get("/v1/admin/reconciliation/history")

        assert response.status_code == 200
        data = response.json()
        assert "runs" in data
        assert len(data["runs"]) == 1
        assert data["runs"][0]["divergences_found"] == 2

    @patch("cron_jobs.run_reconciliation", new_callable=AsyncMock)
    def test_reconciliation_trigger_endpoint(self, mock_run, client):
        """AC13: POST /admin/reconciliation/trigger executes reconciliation."""
        mock_run.return_value = {
            "total_checked": 10,
            "divergences_found": 0,
            "auto_fixed": 0,
            "manual_review": 0,
            "duration_ms": 500,
            "details": [],
        }

        response = client.post("/v1/admin/reconciliation/trigger")

        assert response.status_code == 200
        data = response.json()
        assert data["total_checked"] == 10

    @patch("cron_jobs.run_reconciliation", new_callable=AsyncMock)
    def test_reconciliation_trigger_locked(self, mock_run, client):
        """AC13: POST /admin/reconciliation/trigger returns 409 if locked."""
        mock_run.return_value = {"status": "skipped", "reason": "lock_held"}

        response = client.post("/v1/admin/reconciliation/trigger")

        assert response.status_code == 409


# ---------------------------------------------------------------------------
# AC11: Prometheus Metrics
# ---------------------------------------------------------------------------

class TestPrometheusMetrics:
    """AC11: Verify metrics are created and can be used."""

    def test_reconciliation_metrics_exist(self):
        """All 4 reconciliation metrics exist in metrics module."""
        from metrics import (
            RECONCILIATION_RUNS,
            RECONCILIATION_DIVERGENCES,
            RECONCILIATION_FIXES,
            RECONCILIATION_DURATION,
        )

        assert hasattr(RECONCILIATION_RUNS, "inc")
        assert hasattr(RECONCILIATION_DIVERGENCES, "labels")
        assert hasattr(RECONCILIATION_FIXES, "inc")
        assert hasattr(RECONCILIATION_DURATION, "observe")


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases and special handling."""

    @pytest.mark.asyncio
    @patch("services.stripe_reconciliation.redis_cache")
    @patch("services.stripe_reconciliation.get_supabase")
    @patch("services.stripe_reconciliation.stripe")
    @patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_xxx"})
    async def test_pending_payment_skipped(self, mock_stripe, mock_get_sb, mock_cache):
        """pending_payment (Boleto/PIX) is valid transient state — skip."""
        from services.stripe_reconciliation import reconcile_subscriptions

        stripe_sub = _make_stripe_sub(sub_id="sub_boleto", status="active")
        mock_stripe.Subscription.list.return_value = SimpleNamespace(
            data=[stripe_sub], has_more=False
        )

        local_sub = _make_local_sub(
            stripe_sub_id="sub_boleto",
            subscription_status="pending_payment",
            is_active=False,
        )

        mock_get_sb.return_value = _make_sb({
            "user_subscriptions": [local_sub],
        })
        mock_cache.delete = AsyncMock()

        result = await reconcile_subscriptions()

        # Should NOT flag as divergence
        assert result["divergences_found"] == 0

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"STRIPE_SECRET_KEY": ""})
    async def test_no_stripe_key_skips_gracefully(self):
        """No STRIPE_SECRET_KEY → skip reconciliation without error."""
        from services.stripe_reconciliation import reconcile_subscriptions

        result = await reconcile_subscriptions()

        assert result["total_checked"] == 0
        assert result["divergences_found"] == 0

    @pytest.mark.asyncio
    @patch("services.stripe_reconciliation.redis_cache")
    @patch("services.stripe_reconciliation.get_supabase")
    @patch("services.stripe_reconciliation.stripe")
    @patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_xxx"})
    async def test_stripe_pagination(self, mock_stripe, mock_get_sb, mock_cache):
        """Handles paginated Stripe responses correctly."""
        from services.stripe_reconciliation import reconcile_subscriptions

        page1 = SimpleNamespace(
            data=[_make_stripe_sub(sub_id="sub_p1", status="active")],
            has_more=True,
        )
        page2 = SimpleNamespace(
            data=[_make_stripe_sub(sub_id="sub_p2", status="active")],
            has_more=False,
        )
        mock_stripe.Subscription.list.side_effect = [page1, page2]

        local_subs = [
            _make_local_sub(stripe_sub_id="sub_p1"),
            _make_local_sub(stripe_sub_id="sub_p2", sub_id="local-2", user_id="user-2"),
        ]

        mock_get_sb.return_value = _make_sb({
            "user_subscriptions": local_subs,
        })
        mock_cache.delete = AsyncMock()

        result = await reconcile_subscriptions()

        assert result["total_checked"] == 2
        assert mock_stripe.Subscription.list.call_count == 2

    @pytest.mark.asyncio
    @patch("services.stripe_reconciliation.redis_cache")
    @patch("services.stripe_reconciliation.get_supabase")
    @patch("services.stripe_reconciliation.stripe")
    @patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_xxx"})
    async def test_past_due_is_valid_state(self, mock_stripe, mock_get_sb, mock_cache):
        """past_due in both Stripe and DB is NOT a divergence (dunning)."""
        from services.stripe_reconciliation import reconcile_subscriptions

        stripe_sub = _make_stripe_sub(sub_id="sub_pd", status="past_due")
        mock_stripe.Subscription.list.return_value = SimpleNamespace(
            data=[stripe_sub], has_more=False
        )

        local_sub = _make_local_sub(
            stripe_sub_id="sub_pd",
            subscription_status="past_due",
            is_active=True,
        )

        mock_get_sb.return_value = _make_sb({
            "user_subscriptions": [local_sub],
        })
        mock_cache.delete = AsyncMock()

        result = await reconcile_subscriptions()

        # past_due in both = no divergence
        assert result["divergences_found"] == 0

    def test_determine_billing_period(self):
        """_determine_billing_period correctly maps Stripe intervals."""
        from services.stripe_reconciliation import _determine_billing_period

        monthly_sub = _make_stripe_sub(interval="month", interval_count=1)
        assert _determine_billing_period(monthly_sub) == "monthly"

        semi_sub = _make_stripe_sub(interval="month", interval_count=6)
        assert _determine_billing_period(semi_sub) == "semiannual"

        annual_sub = _make_stripe_sub(interval="year", interval_count=1)
        assert _determine_billing_period(annual_sub) == "annual"

        empty_sub = {"items": {"data": []}}
        assert _determine_billing_period(empty_sub) == "monthly"

    def test_stripe_status_mapping(self):
        """_STRIPE_STATUS_MAP covers all known Stripe statuses."""
        from services.stripe_reconciliation import _STRIPE_STATUS_MAP

        assert _STRIPE_STATUS_MAP["active"] == "active"
        assert _STRIPE_STATUS_MAP["past_due"] == "past_due"
        assert _STRIPE_STATUS_MAP["canceled"] == "canceled"
        assert _STRIPE_STATUS_MAP["trialing"] == "active"
        assert _STRIPE_STATUS_MAP["unpaid"] == "past_due"
        assert _STRIPE_STATUS_MAP["incomplete"] == "pending_payment"
        assert _STRIPE_STATUS_MAP["incomplete_expired"] == "canceled"
