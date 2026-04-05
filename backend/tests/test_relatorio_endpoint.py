"""Tests for the Panorama 2026 T1 lead capture endpoint (SEO-PLAYBOOK).

Covers:
- POST /v1/relatorio-2026-t1/request — valid payload, validation errors,
  DB persistence, best-effort email delivery.
"""

from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


# ---------------------------------------------------------------------------
# Fake Supabase (mirrors the tiny fluent fake used in test_referral.py)
# ---------------------------------------------------------------------------


class _FakeTable:
    """Tiny fake supporting the upsert().execute() chain used by the route."""

    def __init__(self, store: list, fail_on_upsert: bool = False):
        self._store = store
        self._fail = fail_on_upsert
        self._pending_row = None

    def upsert(self, row, on_conflict=None):  # noqa: ARG002
        self._pending_row = dict(row)
        return self

    def execute(self):
        if self._fail:
            raise RuntimeError("simulated db failure")
        # Naive dedup on (email, source)
        email = self._pending_row.get("email")
        source = self._pending_row.get("source")
        for existing in self._store:
            if existing.get("email") == email and existing.get("source") == source:
                existing.update(self._pending_row)
                return MagicMock(data=[existing])
        row = dict(self._pending_row)
        row.setdefault("id", f"lead-{len(self._store) + 1}")
        self._store.append(row)
        return MagicMock(data=[row])


class FakeSupabase:
    def __init__(self, fail_on_upsert: bool = False):
        self.report_leads: list = []
        self._fail = fail_on_upsert
        self.table_calls: list = []

    def table(self, name):
        self.table_calls.append(name)
        assert name == "report_leads", f"unexpected table {name}"
        return _FakeTable(self.report_leads, fail_on_upsert=self._fail)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_sb():
    sb = FakeSupabase()
    with patch("supabase_client.get_supabase", return_value=sb), \
         patch("email_service.send_email", return_value="mock-email-id"):
        yield sb


@pytest.fixture
def fake_sb_db_fail():
    sb = FakeSupabase(fail_on_upsert=True)
    with patch("supabase_client.get_supabase", return_value=sb), \
         patch("email_service.send_email", return_value="mock-email-id"):
        yield sb


@pytest.fixture
def fake_sb_email_fail():
    sb = FakeSupabase()
    with patch("supabase_client.get_supabase", return_value=sb), \
         patch("email_service.send_email", side_effect=RuntimeError("resend down")):
        yield sb


def _valid_payload(**overrides):
    base = {
        "email": "journalist@valor.com.br",
        "empresa": "Valor Econômico",
        "cargo": "diretor",
        "newsletter_opt_in": True,
    }
    base.update(overrides)
    return base


ENDPOINT = "/v1/relatorio-2026-t1/request"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_valid_payload_returns_download_url(fake_sb):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(ENDPOINT, json=_valid_payload())

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["download_url"].startswith("https://")
    assert data["download_url"].endswith(".pdf")
    assert data["email_queued"] is True


@pytest.mark.asyncio
async def test_request_invalid_email_returns_422(fake_sb):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(ENDPOINT, json=_valid_payload(email="not-an-email"))
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_request_missing_empresa_returns_422(fake_sb):
    payload = _valid_payload()
    payload.pop("empresa")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(ENDPOINT, json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_request_invalid_cargo_returns_422(fake_sb):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(ENDPOINT, json=_valid_payload(cargo="ceo"))
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_request_persists_to_db(fake_sb):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            ENDPOINT,
            json=_valid_payload(email="Gestor@Empresa.com", empresa="  Empresa X  "),
        )
    assert r.status_code == 200
    assert len(fake_sb.report_leads) == 1
    row = fake_sb.report_leads[0]
    # Email is lowercased, empresa is stripped
    assert row["email"] == "gestor@empresa.com"
    assert row["empresa"] == "Empresa X"
    assert row["cargo"] == "diretor"
    assert row["newsletter_opt_in"] is True
    assert row["source"] == "panorama-2026-t1"
    assert "ip_hash" in row


@pytest.mark.asyncio
async def test_request_email_failure_does_not_block_lead_capture(fake_sb_email_fail):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(ENDPOINT, json=_valid_payload())
    assert r.status_code == 200
    data = r.json()
    assert data["email_queued"] is False
    # Lead was still persisted
    assert len(fake_sb_email_fail.report_leads) == 1


@pytest.mark.asyncio
async def test_request_db_failure_returns_500(fake_sb_db_fail):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(ENDPOINT, json=_valid_payload())
    assert r.status_code == 500
    assert len(fake_sb_db_fail.report_leads) == 0
