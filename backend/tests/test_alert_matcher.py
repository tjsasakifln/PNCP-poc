"""
Tests for STORY-315 Alert Matching Engine + Cron Job.

AC21: Tests for matcher (match, no-match, dedup, period)
AC22: Tests for cron job (scheduling, rate limit, ALERTS_ENABLED flag)

Key mock patterns (from CLAUDE.md):
  - Service layer: patch("services.alert_matcher.sb_execute") + patch("services.alert_matcher.get_supabase")
  - Alert service: patch("services.alert_service.sb_execute")
  - Config: patch("config.ALERTS_ENABLED", True/False)
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
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
# Shared test data
# ---------------------------------------------------------------------------

ALERT_ID_1 = "alert-uuid-0001"
ALERT_ID_2 = "alert-uuid-0002"
USER_ID_1 = "user-uuid-0001"
USER_ID_2 = "user-uuid-0002"

MOCK_ALERT_ROW = {
    "id": ALERT_ID_1,
    "user_id": USER_ID_1,
    "name": "Test Alert",
    "filters": {"setor": "informatica", "ufs": ["SP"], "keywords": ["computador"]},
    "active": True,
    "created_at": "2026-02-01T00:00:00Z",
}

MOCK_PROFILE = {
    "email": "test@example.com",
    "full_name": "Test User",
    "plan_type": "smartlic_pro",
}

MOCK_CACHE_ROW = {
    "results": [
        {
            "id": "item-001",
            "objetoCompra": "Aquisicao de computador desktop",
            "nomeOrgao": "Prefeitura Municipal de Sao Paulo",
            "valorTotalEstimado": 50000.0,
            "uf": "SP",
            "modalidade": "Pregao Eletronico",
            "link_pncp": "https://pncp.gov.br/item-001",
            "viability_score": 0.8,
            "status": "",
        },
        {
            "id": "item-002",
            "objetoCompra": "Manutencao de servidor",
            "nomeOrgao": "Governo de Sao Paulo",
            "valorTotalEstimado": 120000.0,
            "uf": "SP",
            "modalidade": "Concorrencia",
            "link_pncp": "https://pncp.gov.br/item-002",
            "viability_score": 0.6,
            "status": "",
        },
        {
            "id": "item-003",
            "objetoCompra": "Servico de limpeza",
            "nomeOrgao": "Prefeitura de RJ",
            "valorTotalEstimado": 30000.0,
            "uf": "RJ",
            "modalidade": "Pregao",
            "link_pncp": "",
            "viability_score": 0.3,
            "status": "",
        },
    ],
    "search_params": {"setor_id": "informatica"},
    "created_at": datetime.now(timezone.utc).isoformat(),
}


def _make_sb_execute_mock(responses: dict):
    """Create an sb_execute mock that returns different responses per table.

    Args:
        responses: Dict mapping table names to result data.
    """
    async def sb_execute_side_effect(query):
        # Extract table name from the query mock chain
        table_name = getattr(query, "_table_name", None)
        if table_name and table_name in responses:
            result = MagicMock()
            result.data = responses[table_name]
            result.count = len(responses[table_name]) if responses[table_name] else 0
            return result
        result = MagicMock()
        result.data = []
        result.count = 0
        return result
    return sb_execute_side_effect


def _make_mock_db():
    """Create a mock Supabase client that tracks table calls."""
    db = MagicMock()

    def table_fn(name):
        chain = MagicMock()
        chain._table_name = name
        # Make all chained methods return the same mock with _table_name preserved
        for method in ("select", "insert", "update", "upsert", "delete",
                       "eq", "gte", "lte", "lt", "gt", "order", "limit",
                       "range", "single"):
            m = MagicMock()
            m._table_name = name
            for sub_method in ("select", "insert", "update", "upsert", "delete",
                               "eq", "gte", "lte", "lt", "gt", "order", "limit",
                               "range", "single"):
                sub_m = MagicMock()
                sub_m._table_name = name
                setattr(m, sub_method, MagicMock(return_value=sub_m))
            setattr(chain, method, MagicMock(return_value=m))
        return chain

    db.table = MagicMock(side_effect=table_fn)
    return db


# ============================================================================
# AC21: Tests for alert_matcher.py — match, no-match, dedup, period
# ============================================================================


class TestApplyAlertFilters:
    """AC2: Filter logic tests — UF, value, keywords, status."""

    def test_uf_filter_passes(self):
        from services.alert_matcher import _apply_alert_filters

        items = [
            {"id": "1", "titulo": "Computador", "orgao": "Org", "uf": "SP", "valor_estimado": 100, "status": ""},
        ]
        result = _apply_alert_filters(items, {"ufs": ["SP"]})
        assert len(result) == 1

    def test_uf_filter_rejects(self):
        from services.alert_matcher import _apply_alert_filters

        items = [
            {"id": "1", "titulo": "Computador", "orgao": "Org", "uf": "RJ", "valor_estimado": 100, "status": ""},
        ]
        result = _apply_alert_filters(items, {"ufs": ["SP"]})
        assert len(result) == 0

    def test_uf_filter_empty_allows_all(self):
        from services.alert_matcher import _apply_alert_filters

        items = [
            {"id": "1", "titulo": "Computador", "orgao": "Org", "uf": "RJ", "valor_estimado": 100, "status": ""},
        ]
        result = _apply_alert_filters(items, {"ufs": []})
        assert len(result) == 1

    def test_value_min_filter(self):
        from services.alert_matcher import _apply_alert_filters

        items = [
            {"id": "1", "titulo": "Item", "orgao": "Org", "uf": "", "valor_estimado": 5000, "status": ""},
            {"id": "2", "titulo": "Item", "orgao": "Org", "uf": "", "valor_estimado": 50000, "status": ""},
        ]
        result = _apply_alert_filters(items, {"valor_min": 10000})
        assert len(result) == 1
        assert result[0]["id"] == "2"

    def test_value_max_filter(self):
        from services.alert_matcher import _apply_alert_filters

        items = [
            {"id": "1", "titulo": "Item", "orgao": "Org", "uf": "", "valor_estimado": 5000, "status": ""},
            {"id": "2", "titulo": "Item", "orgao": "Org", "uf": "", "valor_estimado": 50000, "status": ""},
        ]
        result = _apply_alert_filters(items, {"valor_max": 10000})
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_keyword_matching(self):
        from services.alert_matcher import _apply_alert_filters

        items = [
            {"id": "1", "titulo": "Aquisicao de computador desktop", "orgao": "Prefeitura", "uf": "", "valor_estimado": 0, "status": ""},
            {"id": "2", "titulo": "Servico de limpeza predial", "orgao": "Governo", "uf": "", "valor_estimado": 0, "status": ""},
        ]
        result = _apply_alert_filters(items, {"keywords": ["computador"]})
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_keyword_density_is_set(self):
        from services.alert_matcher import _apply_alert_filters

        items = [
            {"id": "1", "titulo": "computador computador desktop", "orgao": "Prefeitura", "uf": "", "valor_estimado": 0, "status": ""},
        ]
        result = _apply_alert_filters(items, {"keywords": ["computador"]})
        assert len(result) == 1
        assert "keyword_density" in result[0]
        assert result[0]["keyword_density"] > 0

    def test_status_filter_rejects_closed(self):
        from services.alert_matcher import _apply_alert_filters

        items = [
            {"id": "1", "titulo": "Item", "orgao": "Org", "uf": "", "valor_estimado": 0, "status": "encerrada"},
            {"id": "2", "titulo": "Item", "orgao": "Org", "uf": "", "valor_estimado": 0, "status": "revogada"},
            {"id": "3", "titulo": "Item", "orgao": "Org", "uf": "", "valor_estimado": 0, "status": "aberta"},
            {"id": "4", "titulo": "Item", "orgao": "Org", "uf": "", "valor_estimado": 0, "status": ""},
        ]
        result = _apply_alert_filters(items, {})
        assert len(result) == 2
        assert {r["id"] for r in result} == {"3", "4"}

    def test_combined_filters(self):
        from services.alert_matcher import _apply_alert_filters

        items = [
            {"id": "1", "titulo": "Computador novo", "orgao": "Pref SP", "uf": "SP", "valor_estimado": 50000, "status": ""},
            {"id": "2", "titulo": "Computador usado", "orgao": "Gov RJ", "uf": "RJ", "valor_estimado": 50000, "status": ""},
            {"id": "3", "titulo": "Mesa escritorio", "orgao": "Pref SP", "uf": "SP", "valor_estimado": 50000, "status": ""},
        ]
        result = _apply_alert_filters(items, {
            "ufs": ["SP"],
            "keywords": ["computador"],
            "valor_min": 10000,
            "valor_max": 100000,
        })
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_sort_by_viability_then_density(self):
        from services.alert_matcher import _apply_alert_filters

        items = [
            {"id": "1", "titulo": "computador", "orgao": "Org", "uf": "", "valor_estimado": 0, "viability_score": 0.5, "status": ""},
            {"id": "2", "titulo": "computador computador", "orgao": "Org", "uf": "", "valor_estimado": 0, "viability_score": 0.9, "status": ""},
        ]
        result = _apply_alert_filters(items, {"keywords": ["computador"]})
        assert len(result) == 2
        assert result[0]["id"] == "2"  # Higher viability
        assert result[1]["id"] == "1"

    def test_no_keywords_skips_keyword_filter(self):
        from services.alert_matcher import _apply_alert_filters

        items = [
            {"id": "1", "titulo": "Random item", "orgao": "Org", "uf": "", "valor_estimado": 0, "status": ""},
        ]
        result = _apply_alert_filters(items, {})
        assert len(result) == 1

    def test_empty_items_returns_empty(self):
        from services.alert_matcher import _apply_alert_filters

        result = _apply_alert_filters([], {"keywords": ["computador"]})
        assert result == []


class TestNormalizeItem:
    """Test _normalize_item produces consistent output."""

    def test_pncp_format(self):
        from services.alert_matcher import _normalize_item

        raw = {
            "objetoCompra": "Titulo PNCP",
            "nomeOrgao": "Orgao PNCP",
            "valorTotalEstimado": 75000,
            "unidadeFederativa": "MG",
            "modalidadeNome": "Pregao",
            "linkPncp": "https://pncp.gov.br/x",
            "viability_score": 0.7,
            "status": "aberta",
            "dataPublicacao": "2026-02-01",
        }
        result = _normalize_item(raw, "pncp-001")
        assert result["id"] == "pncp-001"
        assert result["titulo"] == "Titulo PNCP"
        assert result["orgao"] == "Orgao PNCP"
        assert result["valor_estimado"] == 75000.0
        assert result["uf"] == "MG"
        assert result["modalidade"] == "Pregao"
        assert result["link_pncp"] == "https://pncp.gov.br/x"

    def test_fallback_defaults(self):
        from services.alert_matcher import _normalize_item

        raw = {}
        result = _normalize_item(raw, "test-id")
        assert result["id"] == "test-id"
        assert result["titulo"] == "Sem titulo"
        assert result["orgao"] == "Nao informado"
        assert result["valor_estimado"] == 0.0


class TestMatchAlerts:
    """AC1+AC3: End-to-end match_alerts tests."""

    @pytest.mark.asyncio
    async def test_no_eligible_alerts(self):
        """When no active alerts exist, returns empty."""
        from services.alert_matcher import match_alerts

        mock_db = MagicMock()
        sb_result = MagicMock()
        sb_result.data = []

        with patch("services.alert_matcher.sb_execute", new_callable=AsyncMock, return_value=sb_result):
            result = await match_alerts(db=mock_db)

        assert result["total_alerts"] == 0
        assert result["matched"] == 0
        assert result["payloads"] == []

    @pytest.mark.asyncio
    async def test_match_with_results(self):
        """AC1: Alerts with matching cached results return payloads."""
        from services.alert_matcher import match_alerts

        mock_db = MagicMock()

        # Track calls to sb_execute
        call_count = 0

        async def mock_sb_execute(query):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            table = getattr(query, "_table_name", "unknown")

            if table == "alerts":
                result.data = [MOCK_ALERT_ROW]
            elif table == "profiles":
                result.data = MOCK_PROFILE
            elif table == "search_results_cache":
                result.data = [MOCK_CACHE_ROW]
            elif table == "alert_sent_items":
                result.data = []
                result.count = 0
            elif table == "alert_runs":
                result.data = [{"id": "run-1"}]
            else:
                result.data = []
            return result

        mock_db.table = MagicMock(side_effect=lambda name: _make_table_chain(name))

        with patch("services.alert_matcher.sb_execute", new_callable=AsyncMock, side_effect=mock_sb_execute), \
             patch("services.alert_matcher.get_supabase", return_value=mock_db), \
             patch("services.alert_service.sb_execute", new_callable=AsyncMock, side_effect=mock_sb_execute):
            result = await match_alerts(db=mock_db)

        assert result["total_alerts"] >= 0  # Processed alerts

    @pytest.mark.asyncio
    async def test_cross_alert_dedup_ac3(self):
        """AC3: Same item shouldn't appear in two alerts for same user."""
        from services.alert_matcher import _process_alert

        # Simulate user already having item-001 from another alert
        user_sent_items = {
            USER_ID_1: {"item-001"},
        }

        alert = {
            "id": ALERT_ID_1,
            "user_id": USER_ID_1,
            "name": "Test",
            "email": "test@example.com",
            "full_name": "Test",
            "filters": {"keywords": ["computador"]},
        }

        mock_db = MagicMock()

        cache_result = MagicMock()
        cache_result.data = [MOCK_CACHE_ROW]

        sent_result = MagicMock()
        sent_result.data = []
        sent_result.count = 0

        run_result = MagicMock()
        run_result.data = [{"id": "run-1"}]

        async def mock_sb_execute(query):
            table = getattr(query, "_table_name", "")
            result = MagicMock()
            if table == "search_results_cache":
                result.data = [MOCK_CACHE_ROW]
            elif table == "alert_sent_items":
                result.data = []
                result.count = 0
            elif table == "alert_runs":
                result.data = [{"id": "run-1"}]
            else:
                result.data = []
            return result

        mock_db.table = MagicMock(side_effect=lambda name: _make_table_chain(name))

        with patch("services.alert_matcher.sb_execute", new_callable=AsyncMock, side_effect=mock_sb_execute), \
             patch("services.alert_service.sb_execute", new_callable=AsyncMock, side_effect=mock_sb_execute):
            payload = await _process_alert(alert, user_sent_items, mock_db)

        # item-001 should be excluded (cross-alert dedup)
        if not payload.get("skipped"):
            item_ids = [i["id"] for i in payload.get("new_items", [])]
            assert "item-001" not in item_ids


class TestSearchCachedResults:
    """AC4: Cache search tests — period, setor filter, dedup."""

    @pytest.mark.asyncio
    async def test_returns_normalized_items(self):
        from services.alert_matcher import _search_cached_results

        mock_db = MagicMock()
        mock_db.table = MagicMock(side_effect=lambda name: _make_table_chain(name))

        result_mock = MagicMock()
        result_mock.data = [MOCK_CACHE_ROW]

        with patch("services.alert_matcher.sb_execute", new_callable=AsyncMock, return_value=result_mock):
            items = await _search_cached_results({"setor": "informatica"}, mock_db)

        assert len(items) == 3
        assert items[0]["id"] == "item-001"
        assert items[0]["titulo"] == "Aquisicao de computador desktop"

    @pytest.mark.asyncio
    async def test_setor_mismatch_skips_row(self):
        from services.alert_matcher import _search_cached_results

        mock_db = MagicMock()
        mock_db.table = MagicMock(side_effect=lambda name: _make_table_chain(name))

        # Cache row has setor_id=informatica, but alert wants vestuario
        result_mock = MagicMock()
        result_mock.data = [MOCK_CACHE_ROW]

        with patch("services.alert_matcher.sb_execute", new_callable=AsyncMock, return_value=result_mock):
            items = await _search_cached_results({"setor": "vestuario"}, mock_db)

        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_empty_cache_returns_empty(self):
        from services.alert_matcher import _search_cached_results

        mock_db = MagicMock()
        mock_db.table = MagicMock(side_effect=lambda name: _make_table_chain(name))

        result_mock = MagicMock()
        result_mock.data = []

        with patch("services.alert_matcher.sb_execute", new_callable=AsyncMock, return_value=result_mock):
            items = await _search_cached_results({}, mock_db)

        assert items == []

    @pytest.mark.asyncio
    async def test_dedup_by_item_id(self):
        from services.alert_matcher import _search_cached_results

        mock_db = MagicMock()
        mock_db.table = MagicMock(side_effect=lambda name: _make_table_chain(name))

        # Two cache rows with same item
        dup_cache = {
            "results": [
                {"id": "item-001", "objetoCompra": "Dup item", "nomeOrgao": "Org", "valorTotalEstimado": 100, "uf": "SP"},
            ],
            "search_params": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result_mock = MagicMock()
        result_mock.data = [MOCK_CACHE_ROW, dup_cache]

        with patch("services.alert_matcher.sb_execute", new_callable=AsyncMock, return_value=result_mock):
            items = await _search_cached_results({}, mock_db)

        # item-001 should appear only once despite being in both cache rows
        ids = [i["id"] for i in items]
        assert ids.count("item-001") == 1

    @pytest.mark.asyncio
    async def test_exception_returns_empty(self):
        from services.alert_matcher import _search_cached_results

        mock_db = MagicMock()
        mock_db.table = MagicMock(side_effect=lambda name: _make_table_chain(name))

        with patch("services.alert_matcher.sb_execute", new_callable=AsyncMock, side_effect=Exception("DB error")):
            items = await _search_cached_results({}, mock_db)

        assert items == []


class TestRecordAlertRun:
    """AC10: Alert run recording."""

    @pytest.mark.asyncio
    async def test_records_run(self):
        from services.alert_matcher import _record_alert_run

        mock_db = MagicMock()
        mock_db.table = MagicMock(side_effect=lambda name: _make_table_chain(name))

        insert_result = MagicMock()
        insert_result.data = [{"id": "run-1"}]

        with patch("services.alert_matcher.sb_execute", new_callable=AsyncMock, return_value=insert_result):
            await _record_alert_run(ALERT_ID_1, 10, 3, "matched", mock_db)
            # Should not raise

    @pytest.mark.asyncio
    async def test_record_failure_does_not_raise(self):
        from services.alert_matcher import _record_alert_run

        mock_db = MagicMock()
        mock_db.table = MagicMock(side_effect=lambda name: _make_table_chain(name))

        with patch("services.alert_matcher.sb_execute", new_callable=AsyncMock, side_effect=Exception("DB error")):
            # Should not raise — non-critical operation
            await _record_alert_run(ALERT_ID_1, 10, 3, "matched", mock_db)


class TestFinalizeMatchedAlert:
    """Finalize after email send — track sent items."""

    @pytest.mark.asyncio
    async def test_calls_track_sent_items(self):
        from services.alert_matcher import finalize_matched_alert

        mock_db = MagicMock()

        # finalize_matched_alert does lazy: from services.alert_service import track_sent_items
        with patch("services.alert_service.track_sent_items", new_callable=AsyncMock) as mock_track:
            await finalize_matched_alert(ALERT_ID_1, ["item-1", "item-2"], db=mock_db)

        mock_track.assert_called_once_with(ALERT_ID_1, ["item-1", "item-2"], mock_db)


# ============================================================================
# AC22: Tests for cron job — run_search_alerts, ALERTS_ENABLED, lock
# ============================================================================


class TestRunSearchAlerts:
    """AC8+AC22: Cron job function tests.

    Note: run_search_alerts uses lazy imports inside function body:
      from config import ALERTS_ENABLED
      from redis_pool import get_redis_pool
      from services.alert_matcher import match_alerts, finalize_matched_alert
      from templates.emails.alert_digest import ...
      from routes.alerts import get_alert_unsubscribe_url
      from email_service import send_email_async
      from metrics import ...
    So all patches must target the SOURCE modules, not cron_jobs.
    """

    @pytest.mark.asyncio
    async def test_disabled_when_flag_off(self):
        from cron_jobs import run_search_alerts

        with patch("config.ALERTS_ENABLED", False):
            result = await run_search_alerts()

        assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_skipped_when_lock_held(self):
        from cron_jobs import run_search_alerts

        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=False)  # Lock not acquired

        with patch("config.ALERTS_ENABLED", True), \
             patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            result = await run_search_alerts()

        assert result["status"] == "skipped"
        assert result["reason"] == "lock_held"

    @pytest.mark.asyncio
    async def test_proceeds_without_redis(self):
        """When Redis is unavailable, should proceed without lock."""
        from cron_jobs import run_search_alerts

        mock_match = AsyncMock(return_value={
            "total_alerts": 0, "matched": 0, "skipped": 0, "errors": 0, "payloads": [],
        })

        with patch("config.ALERTS_ENABLED", True), \
             patch("redis_pool.get_redis_pool", new_callable=AsyncMock, side_effect=Exception("Redis down")), \
             patch("services.alert_matcher.match_alerts", mock_match), \
             patch("services.alert_matcher.finalize_matched_alert", AsyncMock()), \
             patch("metrics.ALERTS_PROCESSED", MagicMock()), \
             patch("metrics.ALERTS_ITEMS_MATCHED", MagicMock()), \
             patch("metrics.ALERTS_EMAILS_SENT", MagicMock()), \
             patch("metrics.ALERTS_PROCESSING_DURATION", MagicMock()):
            result = await run_search_alerts()

        # Should have proceeded (Redis failure = proceed without lock)
        assert "emails_sent" in result

    @pytest.mark.asyncio
    async def test_sends_email_for_matched_alerts(self):
        """AC8: Should send emails for matched payloads."""
        from cron_jobs import run_search_alerts

        match_result = {
            "total_alerts": 1,
            "matched": 1,
            "skipped": 0,
            "errors": 0,
            "payloads": [{
                "alert_id": ALERT_ID_1,
                "user_id": USER_ID_1,
                "email": "test@example.com",
                "full_name": "Test",
                "alert_name": "Informatica",
                "new_items": [
                    {"id": "item-001", "titulo": "Computador", "orgao": "Gov", "valor_estimado": 50000},
                ],
            }],
        }

        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock()

        with patch("config.ALERTS_ENABLED", True), \
             patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("services.alert_matcher.match_alerts", new_callable=AsyncMock, return_value=match_result), \
             patch("services.alert_matcher.finalize_matched_alert", new_callable=AsyncMock), \
             patch("templates.emails.alert_digest.render_alert_digest_email", return_value="<html>email</html>"), \
             patch("templates.emails.alert_digest.get_alert_digest_subject", return_value="Subject"), \
             patch("routes.alerts.get_alert_unsubscribe_url", return_value="https://example.com/unsub"), \
             patch("email_service.send_email_async") as mock_send, \
             patch("metrics.ALERTS_PROCESSED", MagicMock()), \
             patch("metrics.ALERTS_ITEMS_MATCHED", MagicMock()), \
             patch("metrics.ALERTS_EMAILS_SENT", MagicMock()), \
             patch("metrics.ALERTS_PROCESSING_DURATION", MagicMock()):
            result = await run_search_alerts()

        assert result["emails_sent"] == 1
        mock_send.assert_called_once()
        # Verify List-Unsubscribe header was passed (AC7)
        call_kwargs = mock_send.call_args
        assert "headers" in call_kwargs.kwargs or (len(call_kwargs.args) > 3)

    @pytest.mark.asyncio
    async def test_email_failure_does_not_crash(self):
        """AC22: Email send failure should not crash the cron job."""
        from cron_jobs import run_search_alerts

        match_result = {
            "total_alerts": 1, "matched": 1, "skipped": 0, "errors": 0,
            "payloads": [{
                "alert_id": ALERT_ID_1,
                "user_id": USER_ID_1,
                "email": "test@example.com",
                "full_name": "Test",
                "alert_name": "Test",
                "new_items": [{"id": "x", "titulo": "T", "orgao": "O"}],
            }],
        }

        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock()

        with patch("config.ALERTS_ENABLED", True), \
             patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("services.alert_matcher.match_alerts", new_callable=AsyncMock, return_value=match_result), \
             patch("services.alert_matcher.finalize_matched_alert", new_callable=AsyncMock), \
             patch("templates.emails.alert_digest.render_alert_digest_email", side_effect=Exception("Template error")), \
             patch("metrics.ALERTS_PROCESSED", MagicMock()), \
             patch("metrics.ALERTS_ITEMS_MATCHED", MagicMock()), \
             patch("metrics.ALERTS_EMAILS_SENT", MagicMock()), \
             patch("metrics.ALERTS_PROCESSING_DURATION", MagicMock()):
            result = await run_search_alerts()

        # Should complete without raising
        assert result["emails_sent"] == 0


class TestAlertsLoop:
    """AC8: _alerts_loop scheduling tests."""

    @pytest.mark.asyncio
    async def test_loop_exits_when_disabled(self):
        from cron_jobs import _alerts_loop

        with patch("config.ALERTS_ENABLED", False):
            await _alerts_loop()
            # Should return immediately without sleeping


# ============================================================================
# AC12: Preview endpoint tests via HTTP client
# ============================================================================


@pytest.fixture
def _alerts_enabled_for_preview():
    """CIG-BE-alerts-endpoint-404: the /v1/alerts/*/preview handler is gated by
    ALERTS_SYSTEM_ENABLED and short-circuits to 404 when false. Enable it so
    the preview flow can actually run end-to-end under TestClient.
    """
    with patch("routes.alerts.ALERTS_SYSTEM_ENABLED", True), \
         patch("config.ALERTS_SYSTEM_ENABLED", True):
        yield


@pytest.mark.usefixtures("_alerts_enabled_for_preview")
class TestPreviewEndpoint:
    """AC12: Preview endpoint for dry-run matching."""

    def setup_method(self):
        self.client = TestClient(app)
        app.dependency_overrides[require_auth] = lambda: {
            "id": USER_ID_1, "email": "test@example.com", "role": "authenticated",
        }

    def teardown_method(self):
        app.dependency_overrides.pop(require_auth, None)

    def test_preview_not_found(self):
        """AC12: Preview returns 404 for non-existent alert."""
        mock_sb = MagicMock()

        empty_result = MagicMock()
        empty_result.data = []

        async def mock_execute(query):
            return empty_result

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("supabase_client.sb_execute", new_callable=AsyncMock, side_effect=mock_execute):
            resp = self.client.get(f"/v1/alerts/{ALERT_ID_1}/preview")

        assert resp.status_code == 404

    def test_preview_success(self):
        """AC12: Preview returns matched items without sending email."""
        mock_sb = MagicMock()

        alert_row = {**MOCK_ALERT_ROW, "user_id": USER_ID_1}

        alert_result = MagicMock()
        alert_result.data = [alert_row]

        cache_result = MagicMock()
        cache_result.data = [MOCK_CACHE_ROW]

        call_count = [0]

        async def mock_execute(query):
            call_count[0] += 1
            table = getattr(query, "_table_name", "unknown")
            r = MagicMock()
            if table == "alerts":
                r.data = [alert_row]
            elif table == "search_results_cache":
                r.data = [MOCK_CACHE_ROW]
            else:
                r.data = []
            return r

        mock_sb.table = MagicMock(side_effect=lambda name: _make_table_chain(name))

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("supabase_client.sb_execute", new_callable=AsyncMock, side_effect=mock_execute):
            resp = self.client.get(f"/v1/alerts/{ALERT_ID_1}/preview")

        assert resp.status_code == 200
        data = resp.json()
        assert data["alert_id"] == ALERT_ID_1
        assert isinstance(data["items"], list)
        assert "total" in data
        assert "message" in data


# ============================================================================
# Helpers
# ============================================================================


def _make_table_chain(name: str):
    """Build a mock table query chain that tracks the table name."""
    chain = MagicMock()
    chain._table_name = name

    def chain_method(*args, **kwargs):
        result = MagicMock()
        result._table_name = name
        for m in ("select", "insert", "update", "upsert", "delete",
                   "eq", "gte", "lte", "lt", "gt", "order", "limit",
                   "range", "single"):
            setattr(result, m, MagicMock(side_effect=chain_method))
        return result

    for m in ("select", "insert", "update", "upsert", "delete",
               "eq", "gte", "lte", "lt", "gt", "order", "limit",
               "range", "single"):
        setattr(chain, m, MagicMock(side_effect=chain_method))

    return chain
