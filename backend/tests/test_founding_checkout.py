"""STORY-BIZ-001: tests for founding customer checkout route + webhook handlers."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Enable Stripe key before importing the route so FOUNDING_COUPON_ID etc.
# get the normal defaults.
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake")

from routes.founding import (  # noqa: E402
    FoundingCheckoutRequest,
    _is_valid_cnpj_check_digits,
    _client_ip,
    router as founding_router,
)
from webhooks.handlers.founding import (  # noqa: E402
    mark_founding_lead_abandoned,
    mark_founding_lead_completed,
)


# ---------------------------------------------------------------------------
# CNPJ validator
# ---------------------------------------------------------------------------


def test_cnpj_validator_accepts_known_valid():
    # Well-known public CNPJ of the Brazilian Federal Treasury (valid check digits)
    assert _is_valid_cnpj_check_digits("00394460000141")


def test_cnpj_validator_rejects_wrong_check_digit():
    assert not _is_valid_cnpj_check_digits("00394460000199")


def test_cnpj_validator_rejects_all_equal_digits():
    assert not _is_valid_cnpj_check_digits("00000000000000")
    assert not _is_valid_cnpj_check_digits("11111111111111")


def test_cnpj_validator_rejects_non_numeric():
    assert not _is_valid_cnpj_check_digits("abc39446000141")


def test_cnpj_validator_rejects_wrong_length():
    assert not _is_valid_cnpj_check_digits("003944600001")


# ---------------------------------------------------------------------------
# Pydantic payload validation
# ---------------------------------------------------------------------------


def _valid_payload_args(**overrides):
    base = {
        "email": "founder@empresa.com.br",
        "nome": "Maria Silva",
        "cnpj": "00.394.460/0001-41",
        "razao_social": "Tesouro Nacional Brasil",
        "motivo": (
            "Nossa empresa atua ha 5 anos em licitacoes B2G no setor de engenharia "
            "rodoviaria e vemos no SmartLic um diferencial competitivo para ganhar "
            "escala em monitoramento de editais e qualificacao rapida de oportunidades."
        ),
    }
    base.update(overrides)
    return base


def test_payload_accepts_masked_cnpj():
    req = FoundingCheckoutRequest(**_valid_payload_args())
    assert req.cnpj == "00394460000141"


def test_payload_rejects_short_motivo():
    with pytest.raises(Exception):
        FoundingCheckoutRequest(**_valid_payload_args(motivo="muito curto"))


def test_payload_rejects_invalid_cnpj():
    with pytest.raises(Exception):
        FoundingCheckoutRequest(**_valid_payload_args(cnpj="11.111.111/1111-11"))


def test_payload_rejects_bad_email():
    with pytest.raises(Exception):
        FoundingCheckoutRequest(**_valid_payload_args(email="not-an-email"))


def test_payload_lowercases_email():
    req = FoundingCheckoutRequest(**_valid_payload_args(email="Mixed.CASE@EXAMPLE.COM"))
    assert req.email == "mixed.case@example.com"


# ---------------------------------------------------------------------------
# _client_ip helper
# ---------------------------------------------------------------------------


def test_client_ip_prefers_xff_header():
    req = MagicMock()
    req.headers = {"x-forwarded-for": "203.0.113.1, 10.0.0.2"}
    req.client = MagicMock(host="10.0.0.3")
    assert _client_ip(req) == "203.0.113.1"


def test_client_ip_falls_back_to_client_host():
    req = MagicMock()
    req.headers = {}
    req.client = MagicMock(host="10.0.0.3")
    assert _client_ip(req) == "10.0.0.3"


def test_client_ip_returns_unknown_when_missing():
    req = MagicMock()
    req.headers = {}
    req.client = None
    assert _client_ip(req) == "unknown"


# ---------------------------------------------------------------------------
# Webhook handlers
# ---------------------------------------------------------------------------


def _mk_table_mock(data):
    tbl = MagicMock()
    tbl.table.return_value = tbl
    tbl.update.return_value = tbl
    tbl.eq.return_value = tbl
    tbl.execute.return_value = MagicMock(data=data)
    return tbl


def test_mark_founding_lead_completed_skips_non_founding_session():
    sb = _mk_table_mock(data=[])
    session = {"id": "cs_test_123", "metadata": {"source": "regular"}, "customer": "cus_1"}
    mark_founding_lead_completed(sb, session)
    # Handler exits early — no table access
    assert not sb.update.called


def test_mark_founding_lead_completed_updates_row():
    sb = _mk_table_mock(data=[{"id": "lead-1"}])
    session = {
        "id": "cs_test_123",
        "metadata": {"source": "founding"},
        "customer": "cus_42",
    }
    mark_founding_lead_completed(sb, session)
    sb.table.assert_called_with("founding_leads")
    sb.update.assert_called_once()
    update_payload = sb.update.call_args.args[0]
    assert update_payload["checkout_status"] == "completed"
    assert update_payload["stripe_customer_id"] == "cus_42"
    assert "completed_at" in update_payload


def test_mark_founding_lead_abandoned_updates_only_pending_rows():
    sb = _mk_table_mock(data=[{"id": "lead-1"}])
    session = {"id": "cs_test_987", "metadata": {"source": "founding"}}
    mark_founding_lead_abandoned(sb, session)
    # Second .eq narrows by pending status — confirm it was called
    assert sb.eq.call_count == 2
    calls = [c.args for c in sb.eq.call_args_list]
    assert ("checkout_session_id", "cs_test_987") in calls
    assert ("checkout_status", "pending") in calls


def test_mark_founding_lead_abandoned_skips_non_founding():
    sb = _mk_table_mock(data=[])
    mark_founding_lead_abandoned(sb, {"id": "cs", "metadata": {"source": "x"}})
    assert not sb.update.called


def test_mark_founding_lead_completed_survives_db_error():
    sb = MagicMock()
    sb.table.side_effect = Exception("db unreachable")
    # Should not raise
    mark_founding_lead_completed(
        sb,
        {"id": "cs_test", "metadata": {"source": "founding"}, "customer": "cus"},
    )


# ---------------------------------------------------------------------------
# Route integration (rate-limit + validation errors without hitting Stripe)
# ---------------------------------------------------------------------------


@pytest.fixture
def app_with_founding():
    app = FastAPI()
    app.include_router(founding_router, prefix="/v1")
    return app


def test_founding_route_rejects_short_motivo(app_with_founding):
    client = TestClient(app_with_founding)
    payload = _valid_payload_args(motivo="curto")
    r = client.post("/v1/founding/checkout", json=payload)
    assert r.status_code == 422


def test_founding_route_rejects_invalid_cnpj(app_with_founding):
    client = TestClient(app_with_founding)
    payload = _valid_payload_args(cnpj="11.111.111/1111-11")
    r = client.post("/v1/founding/checkout", json=payload)
    assert r.status_code == 422


@patch("routes.founding.get_supabase")
def test_founding_route_returns_409_when_email_already_has_profile(
    mock_get_supabase, app_with_founding
):
    fake_sb = MagicMock()
    fake_sb.table.return_value = fake_sb
    fake_sb.select.return_value = fake_sb
    fake_sb.eq.return_value = fake_sb
    fake_sb.limit.return_value = fake_sb
    fake_sb.execute.return_value = MagicMock(data=[{"id": "existing-user"}])
    mock_get_supabase.return_value = fake_sb

    client = TestClient(app_with_founding)
    r = client.post("/v1/founding/checkout", json=_valid_payload_args())
    assert r.status_code == 409
    assert "já possui conta" in r.json()["detail"].lower() or "ja possui" in r.json()["detail"].lower()
