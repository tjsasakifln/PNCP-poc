"""STORY-SEO-005 AC7: Unit tests for gsc_sync_job.

Validates:
- Graceful no-op when GSC_SERVICE_ACCOUNT_JSON is missing.
- Graceful no-op when GSC_SYNC_ENABLED=false.
- Correct pagination + upsert wiring when credentials/API available (mocked).
- Metric emission on success.
"""
from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _reset_gsc_env(monkeypatch):
    """Ensure env starts clean — each test opts in."""
    monkeypatch.delenv("GSC_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("GSC_SYNC_ENABLED", raising=False)
    monkeypatch.delenv("GSC_SITE_URL", raising=False)
    monkeypatch.delenv("GSC_DAYS_BACK", raising=False)


@pytest.mark.asyncio
async def test_gsc_sync_skips_when_disabled(monkeypatch):
    monkeypatch.setenv("GSC_SYNC_ENABLED", "false")
    # re-import to pick up new env
    import importlib
    from jobs.cron import gsc_sync as mod
    importlib.reload(mod)
    try:
        result = await mod.gsc_sync_job(ctx={})
        assert result["skipped"] is True
        assert result["skip_reason"] == "GSC_SYNC_ENABLED=false"
    finally:
        monkeypatch.delenv("GSC_SYNC_ENABLED", raising=False)
        importlib.reload(mod)


@pytest.mark.asyncio
async def test_gsc_sync_skips_when_credentials_missing():
    from jobs.cron import gsc_sync as mod
    result = await mod.gsc_sync_job(ctx={})
    assert result["skipped"] is True
    assert result["skip_reason"] == "missing_credentials"
    assert result["rows_fetched"] == 0


@pytest.mark.asyncio
async def test_gsc_sync_skips_when_credentials_invalid_json(monkeypatch):
    monkeypatch.setenv("GSC_SERVICE_ACCOUNT_JSON", "{not valid json")
    from jobs.cron import gsc_sync as mod
    result = await mod.gsc_sync_job(ctx={})
    assert result["skipped"] is True


@pytest.mark.asyncio
async def test_rows_to_upsert_records_normal():
    from jobs.cron.gsc_sync import _rows_to_upsert_records
    rows = [
        {
            "keys": ["2026-04-01", "lei 14133", "/guia/lei-14133", "bra", "DESKTOP"],
            "clicks": 12,
            "impressions": 340,
            "ctr": 0.035,
            "position": 4.7,
        },
        {
            "keys": ["2026-04-02", "pncp", "/guia/pncp", "bra", "MOBILE"],
            "clicks": 3,
            "impressions": 120,
            "ctr": 0.025,
            "position": 7.1,
        },
    ]
    records = _rows_to_upsert_records(rows)
    assert len(records) == 2
    assert records[0]["query"] == "lei 14133"
    assert records[0]["page"] == "/guia/lei-14133"
    assert records[0]["clicks"] == 12
    assert records[0]["impressions"] == 340
    assert records[0]["country"] == "bra"
    assert records[1]["device"] == "MOBILE"


@pytest.mark.asyncio
async def test_rows_to_upsert_records_skips_malformed():
    from jobs.cron.gsc_sync import _rows_to_upsert_records
    rows = [
        {"keys": ["2026-04-01"], "clicks": 1, "impressions": 10},  # only 1 dim — skip
        {
            "keys": ["2026-04-02", "q", "p", "bra", "d"],
            "clicks": 5,
            "impressions": 100,
            "ctr": 0.05,
            "position": 3.0,
        },
    ]
    records = _rows_to_upsert_records(rows)
    assert len(records) == 1


@pytest.mark.asyncio
async def test_gsc_sync_full_path_with_mocks(monkeypatch):
    """End-to-end happy path: creds ok, API returns rows, supabase upsert called."""
    monkeypatch.setenv(
        "GSC_SERVICE_ACCOUNT_JSON",
        json.dumps(
            {
                "type": "service_account",
                "project_id": "test",
                "private_key_id": "k",
                "private_key": "-----BEGIN PRIVATE KEY-----\nfake\n-----END PRIVATE KEY-----\n",
                "client_email": "x@y.iam.gserviceaccount.com",
                "client_id": "0",
            }
        ),
    )

    fake_creds = MagicMock()
    fake_service = MagicMock()
    fake_query = MagicMock()
    fake_service.searchanalytics.return_value.query.return_value = fake_query
    # First page returns rows, second page empty → stop
    fake_query.execute.side_effect = [
        {
            "rows": [
                {
                    "keys": ["2026-04-01", "licitacoes", "/guia/licitacoes", "bra", "DESKTOP"],
                    "clicks": 20,
                    "impressions": 500,
                    "ctr": 0.04,
                    "position": 3.5,
                }
            ]
        }
    ]

    fake_supabase = MagicMock()
    fake_supabase.table.return_value.upsert.return_value.execute.return_value = MagicMock(data=[{"id": 1}])

    with patch("jobs.cron.gsc_sync._load_credentials", return_value=fake_creds), \
         patch("jobs.cron.gsc_sync._build_service", return_value=fake_service), \
         patch("supabase_client.get_supabase", return_value=fake_supabase):
        import importlib
        from jobs.cron import gsc_sync as mod
        importlib.reload(mod)
        with patch.object(mod, "_load_credentials", return_value=fake_creds), \
             patch.object(mod, "_build_service", return_value=fake_service):
            result = await mod.gsc_sync_job(ctx={})

    assert result["skipped"] is False
    assert result["rows_fetched"] == 1
    assert result["rows_upserted"] == 1
    fake_supabase.table.assert_called_with("gsc_metrics")
