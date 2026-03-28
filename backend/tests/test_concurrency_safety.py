"""
STORY-307: Concurrency Safety — Atomic Operations in Critical Paths

Tests for:
  AC21: Two webhooks with same event_id — only one processes
  AC22: Webhook stuck in 'processing' for >5 min — reprocessed
  AC23: Pipeline update with correct version — success
  AC24: Pipeline update with wrong version — 409
  AC25: Quota increment concurrent — count increments correctly
  AC26: Quota fallback with nonexistent row — creates with count=1

Mocking Strategy:
  - @patch('webhooks.stripe.stripe.Webhook.construct_event') for Stripe
  - @patch('webhooks.stripe.get_supabase') for DB (webhook tests)
  - @patch('routes.pipeline.get_supabase') for DB (pipeline tests)
  - Use proper dependency_overrides for auth (not patch import)
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from auth import require_auth
from database import get_user_db


# ============================================================================
# Shared Fixtures & Helpers
# ============================================================================

MOCK_USER = {"id": "user-concurrency-uuid", "email": "concurrent@test.com", "role": "authenticated"}


@pytest.fixture
def mock_request():
    """Mock FastAPI Request with async body() method."""
    request = AsyncMock()
    request.body = AsyncMock(return_value=b'{"id":"evt_concurrent_123"}')
    request.headers = {"stripe-signature": "t=1234567890,v1=sig"}
    return request


@pytest.fixture
def make_stripe_event():
    """Factory for Stripe Event mocks."""
    def _make(event_id="evt_concurrent_123", event_type="customer.subscription.updated",
              data_object=None):
        event = Mock()
        event.id = event_id
        event.type = event_type
        if data_object is None:
            data_object = Mock()
            data_object.id = "sub_test_456"
            data_object.get = lambda key, default=None: {
                "plan": {"interval": "year", "interval_count": 1},
                "items": {"data": [{"plan": {"interval": "year", "interval_count": 1}}]},
                "customer": "cus_test_789",
                "metadata": {"plan_id": "smartlic_pro"},
                "subscription": "sub_test_456",
            }.get(key, default)
        event.data = Mock()
        event.data.object = data_object
        return event
    return _make


def _make_webhook_sb():
    """Build Supabase mock for webhook tests with per-table tracking."""
    sb = MagicMock()
    _table_mocks = {}

    def _make_chain():
        chain = MagicMock()
        chain.select.return_value = chain
        chain.insert.return_value = chain
        chain.update.return_value = chain
        chain.upsert.return_value = chain
        chain.delete.return_value = chain
        chain.eq.return_value = chain
        chain.limit.return_value = chain
        chain.single.return_value = chain
        chain.order.return_value = chain
        chain.execute.return_value = Mock(data=[])
        return chain

    def table_factory(name):
        if name not in _table_mocks:
            _table_mocks[name] = _make_chain()
        return _table_mocks[name]

    sb.table = MagicMock(side_effect=table_factory)
    sb._table_mocks = _table_mocks
    return sb


# ============================================================================
# Pipeline helpers
# ============================================================================

async def _noop_check_pipeline_write_access(user):
    return None


async def _noop_check_pipeline_read_access(user):
    return None


def _mock_pipeline_sb():
    """Build a fluent-chainable Supabase mock for pipeline tests."""
    sb = Mock()
    sb.table.return_value = sb
    sb.select.return_value = sb
    sb.insert.return_value = sb
    sb.update.return_value = sb
    sb.delete.return_value = sb
    sb.eq.return_value = sb
    not_mock = Mock()
    not_mock.in_.return_value = sb
    not_mock.is_.return_value = sb
    sb.not_ = not_mock
    sb.in_.return_value = sb
    sb.lte.return_value = sb
    sb.is_.return_value = sb
    sb.order.return_value = sb
    sb.range.return_value = sb
    result = Mock(data=[], count=0)
    sb.execute.return_value = result
    return sb


def _create_pipeline_client(user=None, mock_user_db=None):
    from routes.pipeline import router
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: (user or MOCK_USER)
    # Only inject get_user_db for GET tests (SYS-023). PATCH uses get_supabase().
    if mock_user_db is not None:
        app.dependency_overrides[get_user_db] = lambda: mock_user_db
    return TestClient(app)


SAMPLE_PIPELINE_ITEM = {
    "id": "item-uuid-concurrent",
    "user_id": MOCK_USER["id"],
    "pncp_id": "12345678-1-000001/2026",
    "objeto": "Aquisição de equipamentos",
    "orgao": "Prefeitura Municipal",
    "uf": "SP",
    "valor_estimado": 100000.0,
    "data_encerramento": "2026-03-01T23:59:59",
    "link_pncp": "https://pncp.gov.br/app/editais/12345",
    "stage": "descoberta",
    "notes": None,
    "created_at": "2026-02-27T10:00:00",
    "updated_at": "2026-02-27T10:00:00",
    "version": 1,
}


# ============================================================================
# Fix 1: Stripe Webhook Atomicity (AC21-AC22)
# ============================================================================

class TestStripeWebhookAtomicity:
    """STORY-307 Fix 1: Stripe webhook TOCTOU elimination."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache', new_callable=AsyncMock)
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac21_first_webhook_processes(
        self, mock_construct, mock_get_sb, mock_redis, mock_request, make_stripe_event
    ):
        """AC21 (part 1): First webhook with event_id claims and processes."""
        from webhooks.stripe import stripe_webhook

        event = make_stripe_event(event_id="evt_duplicate_test")
        mock_construct.return_value = event

        sb = _make_webhook_sb()
        mock_get_sb.return_value = sb

        # Upsert succeeds — event claimed for processing
        events_chain = sb.table("stripe_webhook_events")
        events_chain.upsert.return_value = events_chain
        events_chain.execute.return_value = Mock(data=[{"id": "evt_duplicate_test"}])

        # Configure subscription lookup
        subs_chain = sb.table("user_subscriptions")
        subs_chain.execute.return_value = Mock(data=[{
            "id": "sub-local",
            "user_id": "user_123",
            "plan_id": "smartlic_pro",
        }])

        result = await stripe_webhook(mock_request)
        assert result["status"] == "success"
        assert result["event_id"] == "evt_duplicate_test"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache', new_callable=AsyncMock)
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac21_duplicate_webhook_skipped(
        self, mock_construct, mock_get_sb, mock_redis, mock_request, make_stripe_event
    ):
        """AC21 (part 2): Second webhook with same event_id returns already_processed."""
        from webhooks.stripe import stripe_webhook

        event = make_stripe_event(event_id="evt_duplicate_test")
        mock_construct.return_value = event

        sb = MagicMock()
        mock_get_sb.return_value = sb

        # Build chain where upsert returns empty (event already exists)
        upsert_chain = MagicMock()
        upsert_chain.execute.return_value = Mock(data=[])

        # Build chain for the stuck check SELECT
        select_chain = MagicMock()
        select_chain.eq.return_value = select_chain
        select_chain.limit.return_value = select_chain
        select_chain.execute.return_value = Mock(data=[{
            "id": "evt_duplicate_test",
            "status": "completed",
            "received_at": datetime.now(timezone.utc).isoformat(),
        }])

        # Track which operation is being built
        call_count = {"n": 0}
        def table_side_effect(name):
            call_count["n"] += 1
            if call_count["n"] == 1:
                # First table call: upsert operation
                chain = MagicMock()
                chain.upsert.return_value = upsert_chain
                return chain
            else:
                # Second table call: select for stuck check
                chain = MagicMock()
                chain.select.return_value = select_chain
                return chain

        sb.table = MagicMock(side_effect=table_side_effect)

        result = await stripe_webhook(mock_request)
        assert result["status"] == "already_processed"
        assert result["event_id"] == "evt_duplicate_test"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache', new_callable=AsyncMock)
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac22_stuck_webhook_reprocessed(
        self, mock_construct, mock_get_sb, mock_redis, mock_request, make_stripe_event
    ):
        """AC22: Webhook stuck in 'processing' for >5 min is reprocessed."""
        from webhooks.stripe import stripe_webhook

        event = make_stripe_event(event_id="evt_stuck_test")
        mock_construct.return_value = event

        sb = _make_webhook_sb()
        mock_get_sb.return_value = sb

        events_chain = sb.table("stripe_webhook_events")

        # Upsert returns empty — event exists (can't claim)
        upsert_chain = MagicMock()
        upsert_chain.execute.return_value = Mock(data=[])
        events_chain.upsert.return_value = upsert_chain

        # Stuck check: event is 'processing' with received_at > 5 min ago
        stuck_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        select_chain = MagicMock()
        select_chain.eq.return_value = select_chain
        select_chain.limit.return_value = select_chain
        select_chain.execute.return_value = Mock(data=[{
            "id": "evt_stuck_test",
            "status": "processing",
            "received_at": stuck_time,
        }])
        events_chain.select.return_value = select_chain

        # Update for reprocessing claim
        update_chain = MagicMock()
        update_chain.eq.return_value = update_chain
        update_chain.execute.return_value = Mock(data=[{"id": "evt_stuck_test"}])
        events_chain.update.return_value = update_chain

        # Configure subscription lookup for event processing
        subs_chain = sb.table("user_subscriptions")
        subs_chain.execute.return_value = Mock(data=[{
            "id": "sub-local",
            "user_id": "user_123",
            "plan_id": "smartlic_pro",
        }])

        result = await stripe_webhook(mock_request)
        assert result["status"] == "success"

        # Verify the update was called to reclaim the stuck event
        events_chain.update.assert_called()

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache', new_callable=AsyncMock)
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac3_failed_processing_marks_event_failed(
        self, mock_construct, mock_get_sb, mock_redis, mock_request, make_stripe_event
    ):
        """AC3: If processing fails, status is set to 'failed'."""
        from webhooks.stripe import stripe_webhook

        event = make_stripe_event(
            event_id="evt_fail_test",
            event_type="checkout.session.completed",
        )
        # Make the checkout handler fail
        checkout_data = Mock()
        checkout_data.get = lambda key, default=None: {
            "client_reference_id": "user_123",
            "metadata": {"plan_id": "smartlic_pro", "billing_period": "monthly"},
            "subscription": "sub_test",
            "customer": "cus_test",
            "payment_status": "paid",
        }.get(key, default)
        event.data.object = checkout_data
        mock_construct.return_value = event

        sb = _make_webhook_sb()
        mock_get_sb.return_value = sb

        # Upsert succeeds (claim event)
        events_chain = sb.table("stripe_webhook_events")
        upsert_chain = MagicMock()
        upsert_chain.execute.return_value = Mock(data=[{"id": "evt_fail_test"}])
        events_chain.upsert.return_value = upsert_chain

        # Plans lookup fails → causes processing error
        plans_chain = sb.table("plans")
        plans_chain.select.return_value = plans_chain
        plans_chain.eq.return_value = plans_chain
        plans_chain.single.return_value = plans_chain
        plans_chain.execute.side_effect = Exception("DB connection lost")

        with pytest.raises(HTTPException) as exc_info:
            await stripe_webhook(mock_request)

        assert exc_info.value.status_code == 500

        # Verify event was marked as failed
        update_calls = events_chain.update.call_args_list
        failed_updates = [
            call for call in update_calls
            if call[0] and isinstance(call[0][0], dict) and call[0][0].get("status") == "failed"
        ]
        assert len(failed_updates) >= 1, "Event should be marked as 'failed' on processing error"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache', new_callable=AsyncMock)
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac5_signature_verified_before_insert(
        self, mock_construct, mock_get_sb, mock_redis, mock_request
    ):
        """AC5: Signature verification happens BEFORE the INSERT ON CONFLICT."""
        from webhooks.stripe import stripe_webhook
        import stripe as stripe_mod

        # Signature verification fails
        mock_construct.side_effect = stripe_mod.error.SignatureVerificationError(
            "Invalid signature", "sig_header"
        )

        # Supabase should NOT be called at all
        sb = _make_webhook_sb()
        mock_get_sb.return_value = sb

        with pytest.raises(HTTPException) as exc_info:
            await stripe_webhook(mock_request)

        assert exc_info.value.status_code == 400

        # Verify no DB operations happened
        sb.table.assert_not_called()


# ============================================================================
# Fix 2: Pipeline Optimistic Locking (AC23-AC24)
# ============================================================================

class TestPipelineOptimisticLocking:
    """STORY-307 Fix 2: Pipeline version-based conflict detection."""

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_ac23_update_with_correct_version_succeeds(self, mock_get_sb):
        """AC23: Pipeline update with matching version succeeds."""
        sb = _mock_pipeline_sb()
        updated_item = {**SAMPLE_PIPELINE_ITEM, "stage": "analise", "version": 2}
        sb.execute.return_value = Mock(data=[updated_item])
        mock_get_sb.return_value = sb

        client = _create_pipeline_client()
        resp = client.patch(
            f"/pipeline/{SAMPLE_PIPELINE_ITEM['id']}",
            json={"stage": "analise", "version": 1},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["stage"] == "analise"
        assert body["version"] == 2

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    @patch("routes.pipeline.sb_execute")
    def test_ac24_update_with_wrong_version_returns_409(self, mock_sb_exec, mock_get_sb):
        """AC24: Pipeline update with stale version returns 409 Conflict."""
        sb = _mock_pipeline_sb()
        mock_get_sb.return_value = sb

        # First sb_execute call: version mismatch → 0 rows
        # Second sb_execute call: item exists (confirm 409, not 404)
        mock_sb_exec.side_effect = [
            Mock(data=[]),  # UPDATE with wrong version → no match
            Mock(data=[{"id": SAMPLE_PIPELINE_ITEM["id"], "version": 3}]),  # EXISTS check
        ]

        client = _create_pipeline_client()
        resp = client.patch(
            f"/pipeline/{SAMPLE_PIPELINE_ITEM['id']}",
            json={"stage": "analise", "version": 1},  # Stale version
        )

        assert resp.status_code == 409
        body = resp.json()
        assert "atualizado" in body["detail"].lower()

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    @patch("routes.pipeline.sb_execute")
    def test_ac24_update_nonexistent_item_returns_404(self, mock_sb_exec, mock_get_sb):
        """AC24 edge: version mismatch on non-existent item → 404 not 409."""
        sb = _mock_pipeline_sb()
        mock_get_sb.return_value = sb

        # Both calls return empty — item doesn't exist
        mock_sb_exec.side_effect = [
            Mock(data=[]),  # UPDATE → no match
            Mock(data=[]),  # EXISTS check → not found
        ]

        client = _create_pipeline_client()
        resp = client.patch(
            "/pipeline/nonexistent-id",
            json={"stage": "analise", "version": 1},
        )

        assert resp.status_code == 404

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    def test_ac12_get_pipeline_returns_version(self):
        """AC12: GET pipeline items includes version field in response."""
        sb = _mock_pipeline_sb()
        sb.execute.return_value = Mock(
            data=[SAMPLE_PIPELINE_ITEM],
            count=1,
        )

        client = _create_pipeline_client(mock_user_db=sb)
        resp = client.get("/pipeline")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 1
        assert "version" in body["items"][0]
        assert body["items"][0]["version"] == 1

    @patch("routes.pipeline._check_pipeline_write_access", _noop_check_pipeline_write_access)
    @patch("routes.pipeline._check_pipeline_read_access", _noop_check_pipeline_read_access)
    @patch("routes.pipeline.get_supabase")
    def test_legacy_update_without_version_still_works(self, mock_get_sb):
        """Backward compat: update without version uses legacy path."""
        sb = _mock_pipeline_sb()
        sb.execute.return_value = Mock(data=[SAMPLE_PIPELINE_ITEM])
        mock_get_sb.return_value = sb

        client = _create_pipeline_client()
        resp = client.patch(
            f"/pipeline/{SAMPLE_PIPELINE_ITEM['id']}",
            json={"stage": "analise"},  # No version field
        )

        assert resp.status_code == 200


# ============================================================================
# Fix 3: Quota Atomicity (AC25-AC26)
# ============================================================================

class TestQuotaAtomicity:
    """STORY-307 Fix 3: Quota fallback atomic increment."""

    def setup_method(self):
        """Clear plan capabilities cache between tests."""
        try:
            import quota
            quota._plan_capabilities_cache = None
            quota._plan_capabilities_cache_time = 0
        except Exception:
            pass

    @patch("supabase_client.get_supabase")
    def test_ac25_atomic_increment_uses_rpc(self, mock_get_sb):
        """AC25: Quota increment uses atomic RPC (no read-modify-write)."""
        from quota import increment_monthly_quota

        sb = MagicMock()
        mock_get_sb.return_value = sb

        # Primary RPC fails (not available)
        sb.rpc.return_value.execute.side_effect = [
            Exception("function increment_quota_atomic does not exist"),
            # Fallback RPC succeeds
            Mock(data=[{"new_count": 6}]),
        ]

        result = increment_monthly_quota("user-atomic-test", max_quota=50)
        assert result == 6

        # Verify RPC was called (not read-then-write)
        rpc_calls = sb.rpc.call_args_list
        assert len(rpc_calls) >= 2
        # Second call should be the fallback atomic RPC
        assert rpc_calls[1][0][0] == "increment_quota_fallback_atomic"

    @patch("supabase_client.get_supabase")
    def test_ac26_fallback_creates_new_row(self, mock_get_sb):
        """AC26: Quota fallback with nonexistent row creates with count=1."""
        from quota import increment_monthly_quota

        sb = MagicMock()
        mock_get_sb.return_value = sb

        # Primary RPC fails
        sb.rpc.return_value.execute.side_effect = [
            Exception("function increment_quota_atomic does not exist"),
            # Fallback RPC also fails (function not deployed yet)
            Exception("function increment_quota_fallback_atomic does not exist"),
        ]

        # Last-resort upsert path
        sb.table.return_value = sb
        sb.upsert.return_value = sb
        sb.execute.return_value = Mock(data=[{"searches_count": 1}])

        with patch("quota.get_monthly_quota_used", return_value=1):
            result = increment_monthly_quota("user-new-quota", max_quota=50)

        assert result == 1

        # Verify upsert was called (creates row if not exists)
        sb.upsert.assert_called_once()
        upsert_args = sb.upsert.call_args[0][0]
        assert upsert_args["searches_count"] == 1
        assert upsert_args["user_id"] == "user-new-quota"

    @patch("supabase_client.get_supabase")
    def test_ac15_no_read_modify_write_in_fallback(self, mock_get_sb):
        """AC15: Fallback path does NOT call get_monthly_quota_used before write."""
        from quota import increment_monthly_quota

        sb = MagicMock()
        mock_get_sb.return_value = sb

        # Primary RPC fails
        sb.rpc.return_value.execute.side_effect = [
            Exception("not available"),
            # Fallback RPC succeeds
            Mock(data=[{"new_count": 42}]),
        ]

        with patch("quota.get_monthly_quota_used") as mock_read:
            result = increment_monthly_quota("user-no-rmw", max_quota=100)

        # get_monthly_quota_used should NOT be called in the atomic path
        # (it was the source of the race condition)
        assert result == 42
        mock_read.assert_not_called()


# ============================================================================
# Migration Validation (AC16-AC20)
# ============================================================================

class TestMigrationContent:
    """Validate migration SQL content for STORY-307 (split into 4 files by STORY-318)."""

    @pytest.fixture
    def migrations_dir(self):
        from pathlib import Path
        return Path(__file__).parent.parent.parent / "supabase" / "migrations"

    @pytest.fixture
    def stripe_webhook_sql(self, migrations_dir):
        return (migrations_dir / "20260227120001_concurrency_stripe_webhook.sql").read_text(encoding="utf-8")

    @pytest.fixture
    def pipeline_version_sql(self, migrations_dir):
        return (migrations_dir / "20260227120002_concurrency_pipeline_version.sql").read_text(encoding="utf-8")

    @pytest.fixture
    def quota_rpc_sql(self, migrations_dir):
        return (migrations_dir / "20260227120003_concurrency_quota_rpc.sql").read_text(encoding="utf-8")

    @pytest.fixture
    def quota_rpc_grant_sql(self, migrations_dir):
        return (migrations_dir / "20260227120004_concurrency_quota_rpc_grant.sql").read_text(encoding="utf-8")

    def test_ac16_status_column_added(self, stripe_webhook_sql):
        """AC16: Migration adds status column to stripe_webhook_events."""
        assert "ADD COLUMN" in stripe_webhook_sql
        assert "status" in stripe_webhook_sql
        assert "VARCHAR(20)" in stripe_webhook_sql

    def test_ac17_received_at_column_added(self, stripe_webhook_sql):
        """AC17: Migration adds received_at to stripe_webhook_events."""
        assert "received_at" in stripe_webhook_sql
        assert "TIMESTAMPTZ" in stripe_webhook_sql

    def test_ac18_version_column_added(self, pipeline_version_sql):
        """AC18: Migration adds version column to pipeline_items."""
        assert "pipeline_items" in pipeline_version_sql
        assert "version" in pipeline_version_sql
        assert "INTEGER" in pipeline_version_sql
        assert "DEFAULT 1" in pipeline_version_sql

    def test_ac19_grant_update(self, stripe_webhook_sql):
        """AC19: GRANT UPDATE on stripe_webhook_events to service_role."""
        assert "GRANT UPDATE ON stripe_webhook_events TO service_role" in stripe_webhook_sql

    def test_atomic_fallback_rpc_created(self, quota_rpc_sql):
        """Migration creates increment_quota_fallback_atomic function."""
        assert "increment_quota_fallback_atomic" in quota_rpc_sql
        assert "ON CONFLICT" in quota_rpc_sql
        assert "searches_count + 1" in quota_rpc_sql
