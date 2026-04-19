"""
Tests for STORY-301 Email Alert System.

Covers:
  AC22: Cron executes search and sends email (alert_service)
  AC23: Dedup filters already-sent items
  AC24: Unsubscribe link deactivates alert (HMAC verification)
  AC25: CRUD endpoints -- create, list, update, delete

Plus: rate limit, per-user limit, filter validation, alert history,
      email template rendering, edge cases.

Key mock patterns (from CLAUDE.md):
  - Auth: app.dependency_overrides[require_auth] (NOT patch on routes)
  - Routes: patch("supabase_client.get_supabase") + patch("supabase_client.sb_execute")
    (routes do lazy `from supabase_client import ...` inside each function)
  - Service layer: patch("services.alert_service.sb_execute")
    (service does top-level `from supabase_client import sb_execute`)
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import sys

# ARQ mock (must be set before importing app)
mock_arq = MagicMock()
sys.modules.setdefault("arq", mock_arq)
sys.modules.setdefault("arq.connections", MagicMock())
sys.modules.setdefault("arq.cron", MagicMock())

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from auth import require_auth  # noqa: E402


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

MOCK_USER = {
    "id": "test-user-uuid-0001",
    "email": "test@example.com",
    "role": "authenticated",
}

ALERT_ID = "alert-uuid-0001"

NOW_ISO = datetime.now(timezone.utc).isoformat()


class MockResponse:
    """Lightweight stand-in for a Supabase postgrest response."""

    def __init__(self, data=None, count=None):
        self.data = data if data is not None else []
        self.count = count


def _mock_sb():
    """Create a fluent-chainable Supabase mock (table->select->eq->...)."""
    sb = MagicMock()
    sb.table.return_value = sb
    sb.select.return_value = sb
    sb.insert.return_value = sb
    sb.upsert.return_value = sb
    sb.update.return_value = sb
    sb.delete.return_value = sb
    sb.eq.return_value = sb
    sb.gte.return_value = sb
    sb.lt.return_value = sb
    sb.order.return_value = sb
    sb.limit.return_value = sb
    sb.range.return_value = sb
    sb.single.return_value = sb
    sb.execute.return_value = MockResponse()
    return sb


def _alert_row(
    alert_id=ALERT_ID,
    user_id=MOCK_USER["id"],
    name="Vestuario Alert",
    filters=None,
    active=True,
):
    """Build a typical alerts table row dict."""
    return {
        "id": alert_id,
        "user_id": user_id,
        "name": name,
        "filters": filters or {"setor": "vestuario", "ufs": ["SP"]},
        "active": active,
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def setup_auth():
    """Override auth dependency for every test in this module."""
    app.dependency_overrides[require_auth] = lambda: MOCK_USER
    yield
    app.dependency_overrides.pop(require_auth, None)


@pytest.fixture(autouse=True)
def _alerts_system_enabled():
    """The alerts router is feature-gated by ``ALERTS_SYSTEM_ENABLED`` (default
    false in production). Without the gate the handlers short-circuit to 404,
    hiding the real CRUD/validation contract. Force the flag on at both the
    import site (``routes.alerts``) and the config module.

    CIG-BE-alerts-endpoint-404: previous suite assumed the flag was on by
    default; it is now gated, so every endpoint returned 404 before any
    validation could run.
    """
    with patch("routes.alerts.ALERTS_SYSTEM_ENABLED", True), \
         patch("config.ALERTS_SYSTEM_ENABLED", True):
        yield


@pytest.fixture
def client():
    return TestClient(app)


# ============================================================================
# AC25: CRUD -- POST /v1/alerts (Create)
# ============================================================================


class TestCreateAlert:
    """POST /v1/alerts -- AC25."""

    def test_create_alert_success(self, client):
        """Creating an alert with valid payload returns 201 and the alert row."""
        row = _alert_row()
        sb = _mock_sb()

        async def fake_sb_execute(query):
            # First call: count check; second call: insert
            return MockResponse(data=[row], count=0)

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.post(
                "/v1/alerts",
                json={"name": "Vestuario Alert", "filters": {"setor": "vestuario", "ufs": ["SP"]}},
            )

        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] == ALERT_ID
        assert body["name"] == "Vestuario Alert"
        assert body["active"] is True

    def test_create_alert_valor_min_gt_max_returns_422(self, client):
        """Filter with valor_min > valor_max returns 422."""
        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[], count=0)

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.post(
                "/v1/alerts",
                json={
                    "name": "Bad Range",
                    "filters": {"valor_min": 100000, "valor_max": 50000},
                },
            )

        assert resp.status_code == 422

    def test_create_alert_invalid_uf_returns_422(self, client):
        """Filter with malformed UF (e.g. '123') returns 422."""
        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[], count=0)

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.post(
                "/v1/alerts",
                json={
                    "name": "Invalid UF",
                    "filters": {"ufs": ["123"]},
                },
            )

        assert resp.status_code == 422

    def test_create_alert_numeric_uf_returns_422(self, client):
        """Filter with numeric UF returns 422."""
        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[], count=0)

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.post(
                "/v1/alerts",
                json={
                    "name": "Numeric UF",
                    "filters": {"ufs": ["99"]},
                },
            )

        assert resp.status_code == 422

    def test_create_alert_per_user_limit_returns_409(self, client):
        """When user already has MAX_ALERTS_PER_USER, returns 409."""
        sb = _mock_sb()

        call_count = 0

        async def fake_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # count check returns limit reached
                return MockResponse(data=[], count=20)
            return MockResponse(data=[_alert_row()])

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute), \
             patch("routes.alerts.MAX_ALERTS_PER_USER", 20):
            resp = client.post(
                "/v1/alerts",
                json={"name": "One too many", "filters": {"setor": "vestuario"}},
            )

        assert resp.status_code == 409
        assert "Limite" in resp.json()["detail"]

    def test_create_alert_empty_name_returns_422(self, client):
        """Pydantic rejects empty name (min_length=1)."""
        resp = client.post(
            "/v1/alerts",
            json={"name": "", "filters": {"setor": "vestuario"}},
        )
        assert resp.status_code == 422

    def test_create_alert_missing_name_returns_422(self, client):
        """Pydantic rejects missing name field."""
        resp = client.post(
            "/v1/alerts",
            json={"filters": {"setor": "vestuario"}},
        )
        assert resp.status_code == 422


# ============================================================================
# AC25: CRUD -- GET /v1/alerts (List)
# ============================================================================


class TestListAlerts:
    """GET /v1/alerts -- AC25."""

    def test_list_alerts_empty(self, client):
        """Returns empty list when user has no alerts."""
        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[], count=0)

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.get("/v1/alerts")

        assert resp.status_code == 200
        body = resp.json()
        assert body["alerts"] == []
        assert body["total"] == 0

    def test_list_alerts_returns_alerts_with_sent_counts(self, client):
        """Returns alerts with sent_count from alert_sent_items."""
        row = _alert_row()
        sb = _mock_sb()

        call_count = 0

        async def fake_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # alerts query
                return MockResponse(data=[row])
            # sent count query
            return MockResponse(data=[], count=5)

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.get("/v1/alerts")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["alerts"][0]["sent_count"] == 5


# ============================================================================
# AC25: CRUD -- PATCH /v1/alerts/{alert_id} (Update)
# ============================================================================


class TestUpdateAlert:
    """PATCH /v1/alerts/{alert_id} -- AC25."""

    def test_update_alert_name(self, client):
        """Updating name succeeds and returns updated row."""
        updated_row = _alert_row(name="New Name")
        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[updated_row])

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.patch(
                f"/v1/alerts/{ALERT_ID}",
                json={"name": "New Name"},
            )

        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_update_alert_deactivate(self, client):
        """Setting active=false deactivates the alert."""
        updated_row = _alert_row(active=False)
        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[updated_row])

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.patch(
                f"/v1/alerts/{ALERT_ID}",
                json={"active": False},
            )

        assert resp.status_code == 200
        assert resp.json()["active"] is False

    def test_update_alert_empty_body_returns_422(self, client):
        """Sending no updatable fields returns 422."""
        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[])

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.patch(
                f"/v1/alerts/{ALERT_ID}",
                json={},
            )

        assert resp.status_code == 422

    def test_update_alert_not_found_returns_404(self, client):
        """Updating a nonexistent alert returns 404."""
        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[])

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.patch(
                "/v1/alerts/nonexistent-id",
                json={"name": "Whatever"},
            )

        assert resp.status_code == 404

    def test_update_alert_invalid_filters_returns_422(self, client):
        """Updating with valor_min > valor_max returns 422."""
        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[])

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.patch(
                f"/v1/alerts/{ALERT_ID}",
                json={"filters": {"valor_min": 200000, "valor_max": 100000}},
            )

        assert resp.status_code == 422


# ============================================================================
# AC25: CRUD -- DELETE /v1/alerts/{alert_id}
# ============================================================================


class TestDeleteAlert:
    """DELETE /v1/alerts/{alert_id} -- AC25."""

    def test_delete_alert_success(self, client):
        """Deleting an existing alert returns 200."""
        row = _alert_row()
        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[row])

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.delete(f"/v1/alerts/{ALERT_ID}")

        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_delete_alert_not_found_returns_404(self, client):
        """Deleting a nonexistent alert returns 404."""
        sb = _mock_sb()

        call_count = 0

        async def fake_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # delete sent_items -- succeeds but empty
                return MockResponse(data=[])
            # delete alert -- empty means not found
            return MockResponse(data=[])

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.delete("/v1/alerts/nonexistent-id")

        assert resp.status_code == 404


# ============================================================================
# AC24: Unsubscribe via HMAC token
# ============================================================================


class TestUnsubscribe:
    """GET /v1/alerts/{alert_id}/unsubscribe -- AC24."""

    def test_unsubscribe_valid_token_deactivates_alert(self, client):
        """Valid HMAC token sets alert.active=False and returns 200 HTML."""
        from routes.alerts import _generate_alert_unsubscribe_token

        token = _generate_alert_unsubscribe_token(ALERT_ID)
        deactivated_row = _alert_row(active=False)
        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[deactivated_row])

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.get(
                f"/v1/alerts/{ALERT_ID}/unsubscribe",
                params={"token": token},
            )

        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "desativado" in resp.text.lower()

    def test_unsubscribe_invalid_token_returns_400(self, client):
        """Invalid HMAC token returns 400 HTML error page."""
        resp = client.get(
            f"/v1/alerts/{ALERT_ID}/unsubscribe",
            params={"token": "invalid-token-value"},
        )

        assert resp.status_code == 400
        assert "text/html" in resp.headers["content-type"]
        assert "inv" in resp.text.lower()  # "Token invalido" rendered in HTML

    def test_unsubscribe_missing_token_returns_422(self, client):
        """Missing token query param returns 422 (FastAPI validation)."""
        resp = client.get(f"/v1/alerts/{ALERT_ID}/unsubscribe")
        assert resp.status_code == 422

    def test_unsubscribe_alert_not_found_returns_404(self, client):
        """Valid token but alert not in DB returns 404 HTML."""
        from routes.alerts import _generate_alert_unsubscribe_token

        token = _generate_alert_unsubscribe_token(ALERT_ID)
        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[])

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.get(
                f"/v1/alerts/{ALERT_ID}/unsubscribe",
                params={"token": token},
            )

        assert resp.status_code == 404

    def test_unsubscribe_token_is_deterministic(self):
        """Same alert_id always produces the same token (HMAC)."""
        from routes.alerts import _generate_alert_unsubscribe_token

        t1 = _generate_alert_unsubscribe_token("some-alert-id")
        t2 = _generate_alert_unsubscribe_token("some-alert-id")
        assert t1 == t2

    def test_different_alert_ids_produce_different_tokens(self):
        """Different alert IDs produce different tokens."""
        from routes.alerts import _generate_alert_unsubscribe_token

        t1 = _generate_alert_unsubscribe_token("alert-aaa")
        t2 = _generate_alert_unsubscribe_token("alert-bbb")
        assert t1 != t2


# ============================================================================
# AC13: GET /v1/alerts/{alert_id}/history
# ============================================================================


class TestAlertHistory:
    """GET /v1/alerts/{alert_id}/history -- AC13."""

    def test_alert_history_returns_paginated_items(self, client):
        """Returns sent items with pagination metadata."""
        sb = _mock_sb()

        call_count = 0

        async def fake_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # ownership check
                return MockResponse(data=[{"id": ALERT_ID, "user_id": MOCK_USER["id"]}])
            # history items
            return MockResponse(
                data=[
                    {
                        "id": "sent-1",
                        "alert_id": ALERT_ID,
                        "item_id": "item-aaa",
                        "sent_at": NOW_ISO,
                    },
                ],
                count=1,
            )

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.get(f"/v1/alerts/{ALERT_ID}/history")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert len(body["items"]) == 1
        assert body["items"][0]["item_id"] == "item-aaa"
        assert body["limit"] == 20
        assert body["offset"] == 0

    def test_alert_history_not_found_returns_404(self, client):
        """Requesting history for nonexistent alert returns 404."""
        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[])

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("supabase_client.sb_execute", side_effect=fake_sb_execute):
            resp = client.get("/v1/alerts/nonexistent-id/history")

        assert resp.status_code == 404


# ============================================================================
# AC23: Dedup logic (alert_service.dedup_results)
# ============================================================================


class TestDedupResults:
    """Dedup filtering -- AC23 (AC6 in alert_service)."""

    def test_dedup_filters_already_sent(self):
        """Items with IDs in sent_ids are filtered out."""
        from services.alert_service import dedup_results

        results = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        sent_ids = {"b"}
        new = dedup_results(results, sent_ids)

        assert len(new) == 2
        assert all(r["id"] != "b" for r in new)

    def test_dedup_empty_sent_ids_returns_all(self):
        """When no items have been sent, all results pass through (early return)."""
        from services.alert_service import dedup_results

        results = [{"id": "a"}, {"id": "b"}]
        new = dedup_results(results, set())

        assert len(new) == 2
        assert new is results  # early return returns original list

    def test_dedup_all_already_sent(self):
        """When every result was already sent, returns empty list."""
        from services.alert_service import dedup_results

        results = [{"id": "x"}, {"id": "y"}]
        sent_ids = {"x", "y"}
        new = dedup_results(results, sent_ids)

        assert new == []

    def test_dedup_empty_results(self):
        """Empty results input returns empty output."""
        from services.alert_service import dedup_results

        new = dedup_results([], {"a", "b"})

        assert new == []

    def test_dedup_items_without_id_excluded_when_sent_ids_nonempty(self):
        """Items missing or having empty 'id' are excluded during dedup."""
        from services.alert_service import dedup_results

        results = [{"id": "a"}, {"titulo": "no-id"}, {"id": ""}]
        # Must have non-empty sent_ids to trigger the filtering path
        sent_ids = {"zzz"}
        new = dedup_results(results, sent_ids)

        # Only "a" has a truthy id and it is not in sent_ids
        assert len(new) == 1
        assert new[0]["id"] == "a"

    def test_dedup_preserves_order(self):
        """Dedup preserves the original order of results."""
        from services.alert_service import dedup_results

        results = [{"id": "c"}, {"id": "a"}, {"id": "b"}]
        sent_ids = {"a"}
        new = dedup_results(results, sent_ids)

        assert [r["id"] for r in new] == ["c", "b"]


# ============================================================================
# AC22: Cron job -- run_all_alerts / process_single_alert
# ============================================================================


class TestRunAllAlerts:
    """Alert cron job integration -- AC22."""

    @pytest.mark.asyncio
    async def test_run_all_alerts_no_active_alerts(self):
        """When there are no active alerts, summary shows 0 total."""
        from services.alert_service import run_all_alerts

        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[])

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            result = await run_all_alerts(db=sb)

        assert result["total_alerts"] == 0
        assert result["sent"] == 0
        assert result["skipped"] == 0
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_process_single_alert_skips_when_rate_limited(self):
        """Rate-limited alert is skipped (AC8)."""
        from services.alert_service import process_single_alert

        sb = _mock_sb()

        alert = {
            "id": ALERT_ID,
            "user_id": MOCK_USER["id"],
            "name": "Test",
            "filters": {"setor": "vestuario"},
            "email": "test@example.com",
            "full_name": "Test User",
        }

        async def fake_sb_execute(query):
            # rate limit check returns recent sent item
            return MockResponse(data=[{"id": "x"}], count=1)

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            result = await process_single_alert(alert, db=sb)

        assert result["skipped"] is True
        assert result["skip_reason"] == "rate_limited"

    @pytest.mark.asyncio
    async def test_process_single_alert_skips_when_no_results(self):
        """Alert with no cached results is skipped."""
        from services.alert_service import process_single_alert

        sb = _mock_sb()

        alert = {
            "id": ALERT_ID,
            "user_id": MOCK_USER["id"],
            "name": "Test",
            "filters": {"setor": "vestuario"},
            "email": "test@example.com",
            "full_name": "Test User",
        }

        call_count = 0

        async def fake_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # rate limit check -- not limited
                return MockResponse(data=[], count=0)
            # search cache query -- empty
            return MockResponse(data=[])

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            result = await process_single_alert(alert, db=sb)

        assert result["skipped"] is True
        assert result["skip_reason"] == "no_results"

    @pytest.mark.asyncio
    async def test_process_single_alert_returns_new_opportunities(self):
        """Alert with new items returns them (not skipped)."""
        from services.alert_service import process_single_alert

        sb = _mock_sb()

        alert = {
            "id": ALERT_ID,
            "user_id": MOCK_USER["id"],
            "name": "Vestuario",
            "filters": {"setor": "vestuario"},
            "email": "test@example.com",
            "full_name": "Test User",
        }

        call_count = 0

        async def fake_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # rate limit check -- not limited
                return MockResponse(data=[], count=0)
            if call_count == 2:
                # search cache query -- has results
                return MockResponse(data=[
                    {
                        "results": [
                            {
                                "id": "bid-1",
                                "objetoCompra": "Uniformes escolares",
                                "nomeOrgao": "Prefeitura SP",
                                "valorTotalEstimado": 50000,
                                "uf": "SP",
                                "modalidade": "Pregao",
                                "linkPncp": "https://pncp.gov.br/123",
                            },
                        ],
                        "search_params": {"setor_id": "vestuario"},
                        "created_at": NOW_ISO,
                    }
                ])
            if call_count == 3:
                # get_sent_item_ids -- nothing sent yet
                return MockResponse(data=[])
            return MockResponse(data=[])

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            result = await process_single_alert(alert, db=sb)

        assert result["skipped"] is False
        assert result["total_count"] == 1
        assert result["opportunities"][0]["id"] == "bid-1"

    @pytest.mark.asyncio
    async def test_process_single_alert_skips_when_all_already_sent(self):
        """When all results were already sent, alert is skipped."""
        from services.alert_service import process_single_alert

        sb = _mock_sb()

        alert = {
            "id": ALERT_ID,
            "user_id": MOCK_USER["id"],
            "name": "Vestuario",
            "filters": {"setor": "vestuario"},
            "email": "test@example.com",
            "full_name": "Test User",
        }

        call_count = 0

        async def fake_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # rate limit check -- not limited
                return MockResponse(data=[], count=0)
            if call_count == 2:
                # search cache -- one result
                return MockResponse(data=[
                    {
                        "results": [
                            {
                                "id": "bid-already",
                                "objetoCompra": "Uniformes",
                                "nomeOrgao": "Org",
                                "valorTotalEstimado": 10000,
                                "uf": "SP",
                            },
                        ],
                        "search_params": {},
                        "created_at": NOW_ISO,
                    }
                ])
            if call_count == 3:
                # get_sent_item_ids -- already sent
                return MockResponse(data=[{"item_id": "bid-already"}])
            return MockResponse(data=[])

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            result = await process_single_alert(alert, db=sb)

        assert result["skipped"] is True
        assert result["skip_reason"] == "all_already_sent"


# ============================================================================
# AC8: Rate limit (check_rate_limit)
# ============================================================================


class TestCheckRateLimit:
    """check_rate_limit -- AC8."""

    @pytest.mark.asyncio
    async def test_rate_limited_when_recently_sent(self):
        """Returns True when items were sent within last 20h."""
        from services.alert_service import check_rate_limit

        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[{"id": "recent"}], count=1)

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            limited = await check_rate_limit(ALERT_ID, db=sb)

        assert limited is True

    @pytest.mark.asyncio
    async def test_not_rate_limited_when_no_recent_sends(self):
        """Returns False when no items were sent in the last 20h."""
        from services.alert_service import check_rate_limit

        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[], count=0)

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            limited = await check_rate_limit(ALERT_ID, db=sb)

        assert limited is False

    @pytest.mark.asyncio
    async def test_rate_limit_fails_open_on_error(self):
        """On database error, fail open (return False = allow send)."""
        from services.alert_service import check_rate_limit

        sb = _mock_sb()

        async def fake_sb_execute(query):
            raise Exception("DB connection failed")

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            limited = await check_rate_limit(ALERT_ID, db=sb)

        assert limited is False


# ============================================================================
# Alert service helpers
# ============================================================================


class TestAlertServiceHelpers:
    """Miscellaneous alert_service helper functions."""

    def test_resolve_alert_name_known_sector(self):
        """Known sector ID maps to friendly display name."""
        from services.alert_service import _resolve_alert_name

        name = _resolve_alert_name({"setor": "vestuario"})
        assert name == "Vestuario e Uniformes"

    def test_resolve_alert_name_unknown_sector(self):
        """Unknown sector ID is returned as-is."""
        from services.alert_service import _resolve_alert_name

        name = _resolve_alert_name({"setor": "custom_sector"})
        assert name == "custom_sector"

    def test_resolve_alert_name_no_sector(self):
        """Empty filters returns default name."""
        from services.alert_service import _resolve_alert_name

        name = _resolve_alert_name({})
        assert name == "suas licitacoes"

    @pytest.mark.asyncio
    async def test_get_active_alerts_returns_enriched_list(self):
        """get_active_alerts enriches alerts with profile data."""
        from services.alert_service import get_active_alerts

        sb = _mock_sb()

        call_count = 0

        async def fake_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # active alerts query
                return MockResponse(data=[
                    {
                        "id": ALERT_ID,
                        "user_id": MOCK_USER["id"],
                        "name": "Test Alert",
                        "filters": {"setor": "vestuario"},
                        "active": True,
                        "created_at": NOW_ISO,
                    }
                ])
            # profile query (single) -- returns dict (not list)
            return MockResponse(data={
                "email": "test@example.com",
                "full_name": "Joao Silva",
            })

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            alerts = await get_active_alerts(db=sb)

        assert len(alerts) == 1
        assert alerts[0]["email"] == "test@example.com"
        assert alerts[0]["full_name"] == "Joao Silva"

    @pytest.mark.asyncio
    async def test_get_active_alerts_skips_user_without_email(self):
        """Alerts for users without email are excluded."""
        from services.alert_service import get_active_alerts

        sb = _mock_sb()

        call_count = 0

        async def fake_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MockResponse(data=[
                    {
                        "id": ALERT_ID,
                        "user_id": MOCK_USER["id"],
                        "name": "No Email Alert",
                        "filters": {},
                        "active": True,
                        "created_at": NOW_ISO,
                    }
                ])
            # profile query -- no email
            return MockResponse(data={"email": None, "full_name": "Ghost"})

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            alerts = await get_active_alerts(db=sb)

        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_track_sent_items_inserts_rows(self):
        """track_sent_items upserts item_ids into alert_sent_items."""
        from services.alert_service import track_sent_items

        sb = _mock_sb()

        calls = []

        async def fake_sb_execute(query):
            calls.append(query)
            return MockResponse(data=[])

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            await track_sent_items(ALERT_ID, ["item-1", "item-2"], db=sb)

        assert len(calls) == 1  # single upsert call

    @pytest.mark.asyncio
    async def test_track_sent_items_noop_for_empty_ids(self):
        """track_sent_items does nothing when item_ids is empty."""
        from services.alert_service import track_sent_items

        sb = _mock_sb()

        calls = []

        async def fake_sb_execute(query):
            calls.append(query)
            return MockResponse(data=[])

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            await track_sent_items(ALERT_ID, [], db=sb)

        assert len(calls) == 0  # no database call

    @pytest.mark.asyncio
    async def test_cleanup_old_sent_items(self):
        """cleanup_old_sent_items deletes records older than N days."""
        from services.alert_service import cleanup_old_sent_items

        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[{"id": "old-1"}, {"id": "old-2"}])

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            count = await cleanup_old_sent_items(days=90, db=sb)

        assert count == 2

    @pytest.mark.asyncio
    async def test_get_active_alerts_returns_empty_on_error(self):
        """DB error in get_active_alerts returns empty list, not exception."""
        from services.alert_service import get_active_alerts

        sb = _mock_sb()

        async def fake_sb_execute(query):
            raise Exception("DB down")

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            alerts = await get_active_alerts(db=sb)

        assert alerts == []

    @pytest.mark.asyncio
    async def test_get_sent_item_ids_returns_set(self):
        """get_sent_item_ids returns a set of item_id strings."""
        from services.alert_service import get_sent_item_ids

        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[
                {"item_id": "item-a"},
                {"item_id": "item-b"},
            ])

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            ids = await get_sent_item_ids(ALERT_ID, db=sb)

        assert ids == {"item-a", "item-b"}

    @pytest.mark.asyncio
    async def test_get_sent_item_ids_empty_on_error(self):
        """get_sent_item_ids returns empty set on error."""
        from services.alert_service import get_sent_item_ids

        sb = _mock_sb()

        async def fake_sb_execute(query):
            raise Exception("Network error")

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            ids = await get_sent_item_ids(ALERT_ID, db=sb)

        assert ids == set()


# ============================================================================
# Email template rendering
# ============================================================================


class TestAlertDigestEmail:
    """Alert digest email template tests."""

    def test_alert_digest_email_renders_with_opportunities(self):
        """Digest email includes user name, alert name, and opportunity data."""
        from templates.emails.alert_digest import render_alert_digest_email

        html = render_alert_digest_email(
            user_name="Joao",
            alert_name="Vestuario",
            opportunities=[
                {
                    "titulo": "Uniformes escolares tipo A",
                    "orgao": "Prefeitura Municipal de SP",
                    "valor_estimado": 50000,
                    "uf": "SP",
                    "modalidade": "Pregao",
                    "link_pncp": "https://pncp.gov.br/app/editais/123",
                    "viability_score": 0.8,
                },
            ],
            total_count=1,
            unsubscribe_url="https://example.com/unsubscribe",
        )

        assert "Joao" in html
        assert "Vestuario" in html
        assert "Uniformes escolares" in html
        assert "unsubscribe" in html.lower() or "Cancelar" in html

    def test_alert_digest_email_renders_empty_state(self):
        """Digest email renders properly when there are no opportunities."""
        from templates.emails.alert_digest import render_alert_digest_email

        html = render_alert_digest_email(
            user_name="Maria",
            alert_name="Software",
            opportunities=[],
            total_count=0,
            unsubscribe_url="https://example.com/unsubscribe",
        )

        assert "Maria" in html
        assert "Software" in html
        assert "nao encontrou" in html.lower() or "novidades" in html.lower()

    def test_alert_digest_subject_plural(self):
        """Subject line uses plural for count > 1."""
        from templates.emails.alert_digest import get_alert_digest_subject

        subject = get_alert_digest_subject(5, "Vestuario")
        assert "SmartLic" in subject
        assert "5" in subject
        assert "novas" in subject

    def test_alert_digest_subject_singular(self):
        """Subject line uses singular for count == 1."""
        from templates.emails.alert_digest import get_alert_digest_subject

        subject = get_alert_digest_subject(1, "Vestuario")
        assert "1 nova" in subject

    def test_alert_digest_subject_zero(self):
        """Subject line shows 'Nenhuma' for count == 0."""
        from templates.emails.alert_digest import get_alert_digest_subject

        subject = get_alert_digest_subject(0, "Vestuario")
        assert "Nenhuma" in subject

    def test_alert_digest_email_limits_to_10_opportunities(self):
        """Email shows at most 10 opportunities even if more are provided."""
        from templates.emails.alert_digest import render_alert_digest_email

        opps = [
            {
                "titulo": f"Oportunidade {i}",
                "orgao": f"Orgao {i}",
                "valor_estimado": 10000 * i,
                "uf": "SP",
                "modalidade": "Pregao",
                "link_pncp": f"https://pncp.gov.br/{i}",
                "viability_score": 0.5,
            }
            for i in range(15)
        ]

        html = render_alert_digest_email(
            user_name="Ana",
            alert_name="Engenharia",
            opportunities=opps,
            total_count=15,
            unsubscribe_url="https://example.com/unsub",
        )

        # Opportunity 0-9 should be included, 10-14 should not
        assert "Oportunidade 9" in html
        assert "Oportunidade 10" not in html
        # CTA should reference total (15)
        assert "15" in html

    def test_alert_digest_email_contains_viability_badge(self):
        """High viability score renders a green 'Alta viabilidade' badge."""
        from templates.emails.alert_digest import render_alert_digest_email

        html = render_alert_digest_email(
            user_name="Pedro",
            alert_name="Saude",
            opportunities=[
                {
                    "titulo": "Equipamentos medicos",
                    "orgao": "Hospital Central",
                    "valor_estimado": 200000,
                    "uf": "RJ",
                    "modalidade": "Pregao",
                    "link_pncp": "https://pncp.gov.br/456",
                    "viability_score": 0.85,
                },
            ],
            total_count=1,
            unsubscribe_url="https://example.com/unsub",
        )

        assert "Alta viabilidade" in html

    def test_alert_digest_email_contains_pncp_link(self):
        """Email renders PNCP links for each opportunity."""
        from templates.emails.alert_digest import render_alert_digest_email

        html = render_alert_digest_email(
            user_name="Carlos",
            alert_name="Mobiliario",
            opportunities=[
                {
                    "titulo": "Moveis de escritorio",
                    "orgao": "Governo do Estado",
                    "valor_estimado": 75000,
                    "uf": "MG",
                    "modalidade": "Concorrencia",
                    "link_pncp": "https://pncp.gov.br/app/editais/789",
                    "viability_score": 0.6,
                },
            ],
            total_count=1,
            unsubscribe_url="https://example.com/unsub",
        )

        assert "https://pncp.gov.br/app/editais/789" in html
        assert "Ver edital completo" in html


# ============================================================================
# Unsubscribe URL generation
# ============================================================================


class TestUnsubscribeUrl:
    """Unsubscribe URL generation helper."""

    def test_get_alert_unsubscribe_url_format(self):
        """URL contains alert_id, token param, and backend host."""
        from routes.alerts import get_alert_unsubscribe_url

        url = get_alert_unsubscribe_url("my-alert-id")
        assert "my-alert-id" in url
        assert "token=" in url
        assert "unsubscribe" in url

    def test_get_alert_unsubscribe_url_uses_backend_url_env(self):
        """URL uses BACKEND_URL env var when set."""
        import os
        from routes.alerts import get_alert_unsubscribe_url

        with patch.dict(os.environ, {"BACKEND_URL": "https://api.smartlic.test"}):
            url = get_alert_unsubscribe_url("test-id")

        assert "https://api.smartlic.test" in url


# ============================================================================
# Execute alert search (cache-based)
# ============================================================================


class TestExecuteAlertSearch:
    """execute_alert_search -- searches cached results with filters."""

    @pytest.mark.asyncio
    async def test_empty_cache_returns_empty(self):
        """No cached results in last 24h returns empty list."""
        from services.alert_service import execute_alert_search

        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[])

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            results = await execute_alert_search({"setor": "vestuario"}, db=sb)

        assert results == []

    @pytest.mark.asyncio
    async def test_filters_by_uf(self):
        """Only items matching alert UFs pass through."""
        from services.alert_service import execute_alert_search

        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[
                {
                    "results": [
                        {"id": "bid-sp", "uf": "SP", "objetoCompra": "Test", "nomeOrgao": "Org"},
                        {"id": "bid-mg", "uf": "MG", "objetoCompra": "Test", "nomeOrgao": "Org"},
                    ],
                    "search_params": {},
                    "created_at": NOW_ISO,
                }
            ])

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            results = await execute_alert_search({"ufs": ["SP"]}, db=sb)

        assert len(results) == 1
        assert results[0]["uf"] == "SP"

    @pytest.mark.asyncio
    async def test_filters_by_value_range(self):
        """Items outside valor_min/valor_max are excluded."""
        from services.alert_service import execute_alert_search

        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[
                {
                    "results": [
                        {"id": "cheap", "valorTotalEstimado": 5000, "objetoCompra": "Test", "nomeOrgao": "Org", "uf": "SP"},
                        {"id": "mid", "valorTotalEstimado": 50000, "objetoCompra": "Test", "nomeOrgao": "Org", "uf": "SP"},
                        {"id": "expensive", "valorTotalEstimado": 500000, "objetoCompra": "Test", "nomeOrgao": "Org", "uf": "SP"},
                    ],
                    "search_params": {},
                    "created_at": NOW_ISO,
                }
            ])

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            results = await execute_alert_search(
                {"valor_min": 10000, "valor_max": 100000}, db=sb,
            )

        ids = {r["id"] for r in results}
        assert "mid" in ids
        assert "cheap" not in ids
        assert "expensive" not in ids

    @pytest.mark.asyncio
    async def test_filters_by_keywords(self):
        """Only items matching keywords in titulo or orgao pass through."""
        from services.alert_service import execute_alert_search

        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[
                {
                    "results": [
                        {"id": "match", "objetoCompra": "Uniformes escolares", "nomeOrgao": "Escola Municipal", "uf": "SP"},
                        {"id": "nomatch", "objetoCompra": "Computadores", "nomeOrgao": "Prefeitura", "uf": "SP"},
                    ],
                    "search_params": {},
                    "created_at": NOW_ISO,
                }
            ])

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            results = await execute_alert_search(
                {"keywords": ["uniformes"]}, db=sb,
            )

        assert len(results) == 1
        assert results[0]["id"] == "match"

    @pytest.mark.asyncio
    async def test_deduplicates_across_cache_entries(self):
        """Same item ID appearing in multiple cache rows is deduplicated."""
        from services.alert_service import execute_alert_search

        sb = _mock_sb()

        async def fake_sb_execute(query):
            return MockResponse(data=[
                {
                    "results": [
                        {"id": "dup-1", "objetoCompra": "Uniformes", "nomeOrgao": "Org", "uf": "SP"},
                    ],
                    "search_params": {},
                    "created_at": NOW_ISO,
                },
                {
                    "results": [
                        {"id": "dup-1", "objetoCompra": "Uniformes", "nomeOrgao": "Org", "uf": "SP"},
                        {"id": "unique-2", "objetoCompra": "Moveis", "nomeOrgao": "Org", "uf": "RJ"},
                    ],
                    "search_params": {},
                    "created_at": NOW_ISO,
                },
            ])

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            results = await execute_alert_search({}, db=sb)

        ids = [r["id"] for r in results]
        assert ids.count("dup-1") == 1
        assert "unique-2" in ids

    @pytest.mark.asyncio
    async def test_search_error_returns_empty(self):
        """DB error in execute_alert_search returns empty list gracefully."""
        from services.alert_service import execute_alert_search

        sb = _mock_sb()

        async def fake_sb_execute(query):
            raise Exception("Cache table unavailable")

        with patch("services.alert_service.get_supabase", return_value=sb), \
             patch("services.alert_service.sb_execute", side_effect=fake_sb_execute):
            results = await execute_alert_search({"setor": "vestuario"}, db=sb)

        assert results == []


# ============================================================================
# Pydantic model validation
# ============================================================================


class TestPydanticValidation:
    """Input validation through Pydantic models."""

    def test_create_alert_name_too_long_returns_422(self, client):
        """Name exceeding 120 chars returns 422."""
        resp = client.post(
            "/v1/alerts",
            json={"name": "x" * 121, "filters": {"setor": "vestuario"}},
        )
        assert resp.status_code == 422

    def test_create_alert_missing_filters_returns_422(self, client):
        """Missing filters field returns 422."""
        resp = client.post(
            "/v1/alerts",
            json={"name": "Test"},
        )
        assert resp.status_code == 422


# ============================================================================
# Template helper functions
# ============================================================================


class TestTemplateHelpers:
    """Alert digest template helper functions."""

    def test_format_brl_millions(self):
        """Values >= 1M display as R$ XM."""
        from templates.emails.alert_digest import _format_brl

        assert "M" in _format_brl(2_500_000)
        assert "R$" in _format_brl(2_500_000)

    def test_format_brl_thousands(self):
        """Values >= 1k display as R$ Xk."""
        from templates.emails.alert_digest import _format_brl

        assert "k" in _format_brl(50_000)

    def test_format_brl_small(self):
        """Values < 1k display as R$ X."""
        from templates.emails.alert_digest import _format_brl

        result = _format_brl(500)
        assert "R$" in result
        assert "500" in result

    def test_viability_badge_high(self):
        """Score >= 0.7 produces 'Alta viabilidade' badge."""
        from templates.emails.alert_digest import _viability_badge

        html = _viability_badge(0.85)
        assert "Alta viabilidade" in html

    def test_viability_badge_medium(self):
        """Score 0.4-0.7 produces 'Viabilidade média' badge."""
        from templates.emails.alert_digest import _viability_badge

        html = _viability_badge(0.5)
        assert "média" in html.lower()

    def test_viability_badge_low(self):
        """Score < 0.4 produces 'Baixa viabilidade' badge."""
        from templates.emails.alert_digest import _viability_badge

        html = _viability_badge(0.2)
        assert "Baixa viabilidade" in html

    def test_viability_badge_none(self):
        """None score produces empty string (no badge)."""
        from templates.emails.alert_digest import _viability_badge

        assert _viability_badge(None) == ""
