"""Tests for STORY-356 — Pipeline limit enforcement in backend.

AC6: Trial user tries to add item #6, receives 403 PIPELINE_LIMIT_EXCEEDED.
AC7: Paid user adds items without limit.
"""

from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from auth import require_auth
from database import get_user_db
from routes.pipeline import router


MOCK_TRIAL_USER = {"id": "trial-user-uuid", "email": "trial@test.com", "role": "authenticated"}
MOCK_PAID_USER = {"id": "paid-user-uuid", "email": "paid@test.com", "role": "authenticated"}
MOCK_MASTER_USER = {"id": "master-uuid", "email": "master@test.com", "role": "authenticated"}

PNCP_ID = "12345678-1-000001/2026"

SAMPLE_ITEM = {
    "id": "item-uuid-1234",
    "user_id": MOCK_TRIAL_USER["id"],
    "pncp_id": PNCP_ID,
    "objeto": "Aquisição de uniformes",
    "orgao": "Prefeitura de São Paulo",
    "uf": "SP",
    "valor_estimado": 150000.0,
    "data_encerramento": "2026-03-01T23:59:59",
    "link_pncp": "https://pncp.gov.br/app/editais/12345",
    "stage": "descoberta",
    "notes": None,
    "created_at": "2026-02-14T10:00:00",
    "updated_at": "2026-02-14T10:00:00",
}

PIPELINE_ITEM_PAYLOAD = {
    "pncp_id": PNCP_ID,
    "objeto": "Aquisição de uniformes",
    "orgao": "Prefeitura de São Paulo",
    "uf": "SP",
    "valor_estimado": 150000.0,
    "data_encerramento": "2026-03-01T23:59:59",
    "link_pncp": "https://pncp.gov.br/app/editais/12345",
}


def _create_client(user=None, mock_user_db=None):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: (user or MOCK_TRIAL_USER)
    # Only inject get_user_db for GET tests (SYS-023). POST uses get_supabase().
    if mock_user_db is not None:
        app.dependency_overrides[get_user_db] = lambda: mock_user_db
    return TestClient(app)


def _mock_sb(count=0):
    """Build a fluent-chainable Supabase mock with configurable count."""
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
    result = Mock(data=[], count=count)
    sb.execute.return_value = result
    return sb


async def _noop_write_access(user):
    return None


# ============================================================================
# AC6: Trial user — pipeline limit enforced
# ============================================================================


class TestTrialPipelineLimit:
    """AC6: Trial user tries to add item #6, receives 403."""

    @patch("routes.pipeline._check_pipeline_write_access", _noop_write_access)
    @patch("routes.pipeline.get_supabase")
    @patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False)
    @patch("quota.check_quota")
    def test_trial_user_at_limit_gets_403(
        self, mock_check_quota, mock_has_master, mock_get_sb
    ):
        """Trial user with 5 items (at limit) gets 403 PIPELINE_LIMIT_EXCEEDED."""
        mock_check_quota.return_value = Mock(
            plan_id="free_trial",
            allowed=True,
            capabilities={"allow_pipeline": True},
        )
        sb = _mock_sb(count=5)  # Already has 5 items
        mock_get_sb.return_value = sb  # used by _check_pipeline_limit
        client = _create_client(MOCK_TRIAL_USER)  # user_db not needed (403 before insert)

        resp = client.post("/pipeline", json=PIPELINE_ITEM_PAYLOAD)

        assert resp.status_code == 403
        body = resp.json()["detail"]
        assert body["error_code"] == "PIPELINE_LIMIT_EXCEEDED"
        assert body["limit"] == 5
        assert body["current"] == 5

    @patch("routes.pipeline._check_pipeline_write_access", _noop_write_access)
    @patch("routes.pipeline.get_supabase")
    @patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False)
    @patch("quota.check_quota")
    def test_trial_user_over_limit_gets_403(
        self, mock_check_quota, mock_has_master, mock_get_sb
    ):
        """Trial user with 7 items (over limit) gets 403."""
        mock_check_quota.return_value = Mock(
            plan_id="free_trial",
            allowed=True,
            capabilities={"allow_pipeline": True},
        )
        sb = _mock_sb(count=7)
        mock_get_sb.return_value = sb  # used by _check_pipeline_limit
        client = _create_client(MOCK_TRIAL_USER)  # user_db not needed (403 before insert)

        resp = client.post("/pipeline", json=PIPELINE_ITEM_PAYLOAD)

        assert resp.status_code == 403
        body = resp.json()["detail"]
        assert body["error_code"] == "PIPELINE_LIMIT_EXCEEDED"
        assert body["limit"] == 5
        assert body["current"] == 7

    @patch("routes.pipeline._check_pipeline_write_access", _noop_write_access)
    @patch("routes.pipeline.get_supabase")
    @patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False)
    @patch("quota.check_quota")
    def test_trial_user_below_limit_succeeds(
        self, mock_check_quota, mock_has_master, mock_get_sb
    ):
        """Trial user with 4 items (below limit) can add another."""
        mock_check_quota.return_value = Mock(
            plan_id="free_trial",
            allowed=True,
            capabilities={"allow_pipeline": True},
        )
        # get_supabase() is used by both _check_pipeline_limit (count) and POST handler (insert)
        sb = _mock_sb(count=4)
        sb.execute.side_effect = [
            Mock(data=[], count=4),  # count query in _check_pipeline_limit
            Mock(data=[SAMPLE_ITEM]),  # insert query in POST handler
        ]
        mock_get_sb.return_value = sb
        client = _create_client(MOCK_TRIAL_USER)

        resp = client.post("/pipeline", json=PIPELINE_ITEM_PAYLOAD)

        assert resp.status_code == 201
        assert resp.json()["pncp_id"] == PNCP_ID

    @patch("routes.pipeline._check_pipeline_write_access", _noop_write_access)
    @patch("routes.pipeline.get_supabase")
    @patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False)
    @patch("quota.check_quota")
    @patch("config.TRIAL_PAYWALL_MAX_PIPELINE", 3)
    def test_custom_trial_limit_honored(
        self, mock_check_quota, mock_has_master, mock_get_sb
    ):
        """Custom TRIAL_PAYWALL_MAX_PIPELINE value (3) is honored."""
        mock_check_quota.return_value = Mock(
            plan_id="free_trial",
            allowed=True,
            capabilities={"allow_pipeline": True},
        )
        sb = _mock_sb(count=3)
        mock_get_sb.return_value = sb  # used by _check_pipeline_limit
        client = _create_client(MOCK_TRIAL_USER)  # user_db not needed (403 before insert)

        resp = client.post("/pipeline", json=PIPELINE_ITEM_PAYLOAD)

        assert resp.status_code == 403
        body = resp.json()["detail"]
        assert body["limit"] == 3
        assert body["current"] == 3


# ============================================================================
# AC7: Paid user — no limit
# ============================================================================


class TestPaidUserNoPipelineLimit:
    """AC7: Paid user adds items without limit."""

    @patch("routes.pipeline._check_pipeline_write_access", _noop_write_access)
    @patch("routes.pipeline.get_supabase")
    @patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False)
    @patch("quota.check_quota")
    def test_smartlic_pro_no_limit(
        self, mock_check_quota, mock_has_master, mock_get_sb
    ):
        """SmartLic Pro user with 100 items can still add."""
        mock_check_quota.return_value = Mock(
            plan_id="smartlic_pro",
            allowed=True,
            capabilities={"allow_pipeline": True},
        )
        # Paid users skip _check_pipeline_limit; insert goes via get_supabase()
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[SAMPLE_ITEM])
        mock_get_sb.return_value = sb
        client = _create_client(MOCK_PAID_USER)

        resp = client.post("/pipeline", json=PIPELINE_ITEM_PAYLOAD)

        assert resp.status_code == 201

    @patch("routes.pipeline._check_pipeline_write_access", _noop_write_access)
    @patch("routes.pipeline.get_supabase")
    @patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False)
    @patch("quota.check_quota")
    def test_sala_guerra_no_limit(
        self, mock_check_quota, mock_has_master, mock_get_sb
    ):
        """Sala de Guerra user has no pipeline limit."""
        mock_check_quota.return_value = Mock(
            plan_id="sala_guerra",
            allowed=True,
            capabilities={"allow_pipeline": True},
        )
        # Paid users skip _check_pipeline_limit; insert goes via get_supabase()
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[SAMPLE_ITEM])
        mock_get_sb.return_value = sb
        client = _create_client(MOCK_PAID_USER)

        resp = client.post("/pipeline", json=PIPELINE_ITEM_PAYLOAD)

        assert resp.status_code == 201

    @patch("routes.pipeline._check_pipeline_write_access", _noop_write_access)
    @patch("routes.pipeline.get_supabase")
    @patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False)
    @patch("quota.check_quota")
    def test_maquina_no_limit(
        self, mock_check_quota, mock_has_master, mock_get_sb
    ):
        """Maquina plan user has no pipeline limit."""
        mock_check_quota.return_value = Mock(
            plan_id="maquina",
            allowed=True,
            capabilities={"allow_pipeline": True},
        )
        # Paid users skip _check_pipeline_limit; insert goes via get_supabase()
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[SAMPLE_ITEM])
        mock_get_sb.return_value = sb
        client = _create_client(MOCK_PAID_USER)

        resp = client.post("/pipeline", json=PIPELINE_ITEM_PAYLOAD)

        assert resp.status_code == 201


# ============================================================================
# Master bypass
# ============================================================================


class TestMasterBypassPipelineLimit:
    """Master users bypass pipeline limit entirely."""

    @patch("routes.pipeline._check_pipeline_write_access", _noop_write_access)
    @patch("routes.pipeline.get_supabase")
    @patch("authorization.has_master_access", new_callable=AsyncMock, return_value=True)
    def test_master_bypasses_limit(self, mock_has_master, mock_get_sb):
        """Master user can add items regardless of count."""
        # Masters bypass _check_pipeline_limit entirely; insert goes via get_supabase()
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[SAMPLE_ITEM])
        mock_get_sb.return_value = sb
        client = _create_client(MOCK_MASTER_USER)

        resp = client.post("/pipeline", json=PIPELINE_ITEM_PAYLOAD)

        assert resp.status_code == 201


# ============================================================================
# Response body format
# ============================================================================


class TestPipelineLimitResponseFormat:
    """Verify the 403 response body matches AC3 spec exactly."""

    @patch("routes.pipeline._check_pipeline_write_access", _noop_write_access)
    @patch("routes.pipeline.get_supabase")
    @patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False)
    @patch("quota.check_quota")
    def test_403_body_has_required_fields(
        self, mock_check_quota, mock_has_master, mock_get_sb
    ):
        """403 body must have error_code, limit, and current."""
        mock_check_quota.return_value = Mock(
            plan_id="free_trial",
            allowed=True,
            capabilities={"allow_pipeline": True},
        )
        sb = _mock_sb(count=5)
        mock_get_sb.return_value = sb  # used by _check_pipeline_limit
        client = _create_client(MOCK_TRIAL_USER)  # user_db not needed (403 before insert)

        resp = client.post("/pipeline", json=PIPELINE_ITEM_PAYLOAD)

        assert resp.status_code == 403
        body = resp.json()["detail"]
        assert set(body.keys()) == {"error_code", "limit", "current"}
        assert body["error_code"] == "PIPELINE_LIMIT_EXCEEDED"
        assert isinstance(body["limit"], int)
        assert isinstance(body["current"], int)
