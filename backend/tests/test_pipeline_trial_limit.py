"""STORY-446: Pipeline trial limit tests.

Verifies that TRIAL_PAYWALL_MAX_PIPELINE default is 5 and that the
enforcement logic correctly allows/blocks trial and paid users.
"""
from unittest.mock import Mock, patch, AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth import require_auth
from routes.pipeline import router


MOCK_TRIAL_USER = {"id": "trial-446-uuid", "email": "trial446@test.com", "role": "authenticated"}
MOCK_PAID_USER = {"id": "paid-446-uuid", "email": "paid446@test.com", "role": "authenticated"}

PIPELINE_ITEM_PAYLOAD = {
    "pncp_id": "99999999-1-000446/2026",
    "objeto": "Fornecimento de materiais de escritório",
    "orgao": "Câmara Municipal de Curitiba",
    "uf": "PR",
    "valor_estimado": 25000.0,
    "data_encerramento": "2026-06-01T23:59:59",
    "link_pncp": "https://pncp.gov.br/app/editais/99999",
}

SAMPLE_ITEM = {
    "id": "item-446-uuid",
    "user_id": MOCK_TRIAL_USER["id"],
    "pncp_id": "99999999-1-000446/2026",
    "objeto": "Fornecimento de materiais de escritório",
    "orgao": "Câmara Municipal de Curitiba",
    "uf": "PR",
    "valor_estimado": 25000.0,
    "data_encerramento": "2026-06-01T23:59:59",
    "link_pncp": "https://pncp.gov.br/app/editais/99999",
    "stage": "descoberta",
    "notes": None,
    "created_at": "2026-04-12T10:00:00",
    "updated_at": "2026-04-12T10:00:00",
}


def _create_client(user):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: user
    return TestClient(app)


def _mock_sb(count=0):
    sb = Mock()
    sb.table.return_value = sb
    sb.select.return_value = sb
    sb.insert.return_value = sb
    sb.upsert.return_value = sb
    sb.update.return_value = sb
    sb.delete.return_value = sb
    sb.eq.return_value = sb
    sb.limit.return_value = sb
    not_mock = Mock()
    not_mock.in_.return_value = sb
    not_mock.is_.return_value = sb
    sb.not_ = not_mock
    sb.in_.return_value = sb
    sb.lte.return_value = sb
    sb.is_.return_value = sb
    sb.order.return_value = sb
    sb.range.return_value = sb
    sb.execute.return_value = Mock(data=[], count=count)
    return sb


async def _noop_write_access(user):
    return None


# ---------------------------------------------------------------------------
# STORY-446 AC1: Default limit is 5
# ---------------------------------------------------------------------------


def test_default_pipeline_limit_is_5():
    """STORY-446: TRIAL_PAYWALL_MAX_PIPELINE default must be 5."""
    import config
    assert config.TRIAL_PAYWALL_MAX_PIPELINE == 5


# ---------------------------------------------------------------------------
# STORY-446 AC2: Trial user can add up to the limit (4 items → 201)
# ---------------------------------------------------------------------------


@patch("routes.pipeline._check_pipeline_write_access", _noop_write_access)
@patch("routes.pipeline.get_supabase")
@patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False)
@patch("quota.check_quota")
def test_trial_user_can_add_up_to_limit(mock_check_quota, mock_has_master, mock_get_sb):
    """Trial user with 4 items (below limit of 5) can add another — 201."""
    mock_check_quota.return_value = Mock(
        plan_id="free_trial",
        allowed=True,
        capabilities={"allow_pipeline": True},
    )
    sb = _mock_sb()
    sb.execute.side_effect = [
        Mock(data=[], count=4),    # count query in _check_pipeline_limit
        Mock(data=[SAMPLE_ITEM]),  # insert query in POST handler
    ]
    mock_get_sb.return_value = sb
    client = _create_client(MOCK_TRIAL_USER)

    resp = client.post("/pipeline", json=PIPELINE_ITEM_PAYLOAD)

    assert resp.status_code == 201
    assert resp.json()["pncp_id"] == PIPELINE_ITEM_PAYLOAD["pncp_id"]


# ---------------------------------------------------------------------------
# STORY-446 AC2: Trial user is blocked at limit (5 items → 403)
# ---------------------------------------------------------------------------


@patch("routes.pipeline._check_pipeline_write_access", _noop_write_access)
@patch("routes.pipeline.get_supabase")
@patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False)
@patch("quota.check_quota")
def test_trial_user_blocked_at_limit(mock_check_quota, mock_has_master, mock_get_sb):
    """Trial user already at 5 items gets 403 PIPELINE_LIMIT_EXCEEDED."""
    mock_check_quota.return_value = Mock(
        plan_id="free_trial",
        allowed=True,
        capabilities={"allow_pipeline": True},
    )
    sb = _mock_sb(count=5)
    mock_get_sb.return_value = sb
    client = _create_client(MOCK_TRIAL_USER)

    resp = client.post("/pipeline", json=PIPELINE_ITEM_PAYLOAD)

    assert resp.status_code == 403
    body = resp.json()["detail"]
    assert body["error_code"] == "PIPELINE_LIMIT_EXCEEDED"
    assert body["limit"] == 5
    assert body["current"] == 5


# ---------------------------------------------------------------------------
# STORY-446 AC3: Paid user has no limit (10 items → 201)
# ---------------------------------------------------------------------------


@patch("routes.pipeline._check_pipeline_write_access", _noop_write_access)
@patch("routes.pipeline.get_supabase")
@patch("authorization.has_master_access", new_callable=AsyncMock, return_value=False)
@patch("quota.check_quota")
def test_paid_user_no_limit(mock_check_quota, mock_has_master, mock_get_sb):
    """Paid user with 10 items can still add — no limit enforced."""
    mock_check_quota.return_value = Mock(
        plan_id="smartlic_pro",
        allowed=True,
        capabilities={"allow_pipeline": True},
    )
    # Paid users skip _check_pipeline_limit; only the insert query is called.
    sb = _mock_sb()
    sb.execute.return_value = Mock(data=[SAMPLE_ITEM])
    mock_get_sb.return_value = sb
    client = _create_client(MOCK_PAID_USER)

    resp = client.post("/pipeline", json=PIPELINE_ITEM_PAYLOAD)

    assert resp.status_code == 201
