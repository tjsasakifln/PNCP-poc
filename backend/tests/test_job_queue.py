"""GTM-RESILIENCE-F01: Tests for ARQ job queue infrastructure.

Tests cover:
- AC2: get_arq_pool() creates pool and handles failures
- AC3: is_queue_available() returns bool
- AC4: get_queue_health() returns status string
- AC5: WorkerSettings configured correctly
- AC7-AC11: llm_summary_job function
- AC12-AC16: excel_generation_job function
- AC17/AC22: Queue vs inline pipeline decision
- AC23-AC28: Result persistence, SSE emission, enqueue logic
"""

import json
import sys
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# AC2/AC3: Pool management
# ============================================================================

class TestPoolManagement:
    """AC2: get_arq_pool() singleton with ping health check."""

    @pytest.mark.asyncio
    async def test_get_arq_pool_returns_none_without_redis(self):
        """Pool returns None when REDIS_URL not set."""
        import job_queue
        job_queue._arq_pool = None

        with patch.object(job_queue, "_get_redis_settings", side_effect=ValueError("no REDIS_URL")):
            pool = await job_queue.get_arq_pool()
            assert pool is None

    @pytest.mark.asyncio
    async def test_get_arq_pool_returns_pool_on_success(self):
        """Pool returns ArqRedis instance when Redis available."""
        import job_queue
        job_queue._arq_pool = None

        mock_pool = AsyncMock()
        mock_pool.ping = AsyncMock(return_value=True)

        with patch("arq.create_pool", new_callable=lambda: AsyncMock(return_value=mock_pool)):
            with patch.object(job_queue, "_get_redis_settings", return_value=MagicMock()):
                pool = await job_queue.get_arq_pool()
                assert pool is mock_pool
        job_queue._arq_pool = None

    @pytest.mark.asyncio
    async def test_get_arq_pool_reuses_existing(self):
        """Pool is singleton — second call reuses."""
        import job_queue

        mock_pool = AsyncMock()
        mock_pool.ping = AsyncMock(return_value=True)
        job_queue._arq_pool = mock_pool

        pool = await job_queue.get_arq_pool()
        assert pool is mock_pool
        job_queue._arq_pool = None

    @pytest.mark.asyncio
    async def test_get_arq_pool_reconnects_on_ping_failure(self):
        """Pool reconnects when existing pool fails ping."""
        import job_queue

        dead_pool = AsyncMock()
        dead_pool.ping = AsyncMock(side_effect=ConnectionError("dead"))
        job_queue._arq_pool = dead_pool

        new_pool = AsyncMock()
        new_pool.ping = AsyncMock(return_value=True)

        with patch("arq.create_pool", new_callable=lambda: AsyncMock(return_value=new_pool)):
            with patch.object(job_queue, "_get_redis_settings", return_value=MagicMock()):
                pool = await job_queue.get_arq_pool()
                assert pool is new_pool
        job_queue._arq_pool = None

    @pytest.mark.asyncio
    async def test_close_arq_pool(self):
        """close_arq_pool() closes and resets singleton."""
        import job_queue

        mock_pool = AsyncMock()
        job_queue._arq_pool = mock_pool

        await job_queue.close_arq_pool()
        assert job_queue._arq_pool is None
        mock_pool.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_arq_pool_noop_when_none(self):
        """close_arq_pool() is no-op when no pool exists."""
        import job_queue
        job_queue._arq_pool = None
        await job_queue.close_arq_pool()  # should not raise


# ============================================================================
# AC3: is_queue_available()
# ============================================================================

class TestIsQueueAvailable:
    """AC3: Boolean check for queue readiness."""

    @pytest.mark.asyncio
    async def test_available_when_pool_responds(self):
        import job_queue

        mock_pool = AsyncMock()
        mock_pool.ping = AsyncMock(return_value=True)
        job_queue._arq_pool = mock_pool

        assert await job_queue.is_queue_available() is True
        job_queue._arq_pool = None

    @pytest.mark.asyncio
    async def test_unavailable_when_no_pool(self):
        import job_queue
        job_queue._arq_pool = None

        with patch.object(job_queue, "_get_redis_settings", side_effect=ValueError("no REDIS_URL")):
            assert await job_queue.is_queue_available() is False

    @pytest.mark.asyncio
    async def test_unavailable_when_ping_fails(self):
        import job_queue

        mock_pool = AsyncMock()
        mock_pool.ping = AsyncMock(side_effect=ConnectionError("dead"))
        job_queue._arq_pool = mock_pool

        with patch("arq.create_pool", new_callable=lambda: AsyncMock(side_effect=ConnectionError)):
            with patch.object(job_queue, "_get_redis_settings", return_value=MagicMock()):
                assert await job_queue.is_queue_available() is False
        job_queue._arq_pool = None


# ============================================================================
# AC4: get_queue_health()
# ============================================================================

class TestQueueHealth:
    """AC4: Health check string for /v1/health endpoint."""

    @pytest.mark.asyncio
    async def test_healthy(self):
        import job_queue
        with patch.object(job_queue, "is_queue_available", new_callable=lambda: AsyncMock(return_value=True)):
            assert await job_queue.get_queue_health() == "healthy"

    @pytest.mark.asyncio
    async def test_unavailable(self):
        import job_queue
        with patch.object(job_queue, "is_queue_available", new_callable=lambda: AsyncMock(return_value=False)):
            assert await job_queue.get_queue_health() == "unavailable"


# ============================================================================
# AC5: WorkerSettings
# ============================================================================

class TestWorkerSettings:
    """AC5: ARQ worker configuration."""

    def test_functions_registered(self):
        from job_queue import WorkerSettings, llm_summary_job, excel_generation_job
        assert llm_summary_job in WorkerSettings.functions
        assert excel_generation_job in WorkerSettings.functions

    def test_max_tries(self):
        from job_queue import WorkerSettings
        assert WorkerSettings.max_tries == 3

    def test_job_timeout(self):
        # GTM-ARCH-001: Increased from 60 to 300 to support search_job (multi-UF up to 300s)
        from job_queue import WorkerSettings
        assert WorkerSettings.job_timeout == 300

    def test_max_jobs(self):
        from job_queue import WorkerSettings
        assert WorkerSettings.max_jobs == 10

    def test_retry_delay(self):
        from job_queue import WorkerSettings
        assert WorkerSettings.retry_delay == 5.0  # CRIT-038: increased for Redis recovery


# ============================================================================
# CRIT-051 AC6: ARQ worker log config
# ============================================================================

class TestArqLogConfig:
    """CRIT-051 AC6: arq_log_config uses ext://sys.stdout."""

    def test_arq_log_config_exists(self):
        from job_queue import arq_log_config
        assert isinstance(arq_log_config, dict)

    def test_handler_stream_is_stdout(self):
        """AC6: The stdout handler must use ext://sys.stdout, not stderr."""
        from job_queue import arq_log_config
        handler = arq_log_config["handlers"]["stdout"]
        assert handler["stream"] == "ext://sys.stdout"

    def test_handler_class_is_stream_handler(self):
        from job_queue import arq_log_config
        handler = arq_log_config["handlers"]["stdout"]
        assert handler["class"] == "logging.StreamHandler"

    def test_root_logger_uses_stdout_handler(self):
        from job_queue import arq_log_config
        root = arq_log_config["root"]
        assert "stdout" in root["handlers"]

    def test_log_config_is_valid_dict_config(self):
        """Verify the dict can be applied via logging.config.dictConfig without error."""
        import logging.config
        from job_queue import arq_log_config
        # Should not raise — validates the dict is structurally valid
        logging.config.dictConfig(arq_log_config)

    def test_does_not_disable_existing_loggers(self):
        from job_queue import arq_log_config
        assert arq_log_config.get("disable_existing_loggers") is False


# ============================================================================
# AC6: Redis settings parsing
# ============================================================================

class _FakeRedisSettings:
    """Minimal stand-in for arq.connections.RedisSettings (not installed locally)."""
    def __init__(self, host="localhost", port=6379, password=None, database=0,
                 conn_timeout=None, conn_retries=None, conn_retry_delay=None, ssl=False,
                 retry_on_timeout=False, retry_on_error=None, max_connections=None):
        self.host = host
        self.port = port
        self.password = password
        self.database = database
        self.conn_timeout = conn_timeout
        self.conn_retries = conn_retries
        self.conn_retry_delay = conn_retry_delay
        self.ssl = ssl
        self.retry_on_timeout = retry_on_timeout
        self.retry_on_error = retry_on_error
        self.max_connections = max_connections


class TestRedisSettings:
    """AC6: _get_redis_settings parses REDIS_URL correctly."""

    @pytest.fixture(autouse=True)
    def _ensure_arq_connections(self):
        """Ensure arq.connections module has a proper RedisSettings, even if
        other test files replaced sys.modules['arq.connections'] with a plain MagicMock."""
        import types
        fake_mod = types.ModuleType("arq.connections")
        fake_mod.RedisSettings = _FakeRedisSettings
        with patch.dict(sys.modules, {"arq.connections": fake_mod}):
            yield

    def test_parses_full_url(self):
        from job_queue import _get_redis_settings
        with patch.dict("os.environ", {"REDIS_URL": "rediss://:secret@redis.example.com:6380/2"}):
            settings = _get_redis_settings()
            assert settings.host == "redis.example.com"
            assert settings.port == 6380
            assert settings.conn_timeout == 10
            assert settings.conn_retries == 5
            assert settings.conn_retry_delay == 2.0
            assert settings.ssl is True
            # CRIT-038: Verify hardened settings
            assert settings.retry_on_timeout is True
            assert settings.max_connections == 50
            assert TimeoutError in settings.retry_on_error
            assert ConnectionError in settings.retry_on_error
            assert OSError in settings.retry_on_error

    def test_parses_minimal_url(self):
        from job_queue import _get_redis_settings
        with patch.dict("os.environ", {"REDIS_URL": "redis://localhost:6379/0"}):
            settings = _get_redis_settings()
            assert settings.host == "localhost"
            assert settings.port == 6379
            assert settings.conn_timeout == 10
            assert settings.conn_retries == 5
            assert settings.conn_retry_delay == 2.0
            assert settings.ssl is False
            # CRIT-038: Verify hardened settings
            assert settings.retry_on_timeout is True
            assert settings.max_connections == 50

    def test_raises_without_redis_url(self):
        from job_queue import _get_redis_settings
        import os
        with patch.dict("os.environ", {}, clear=True):
            os.environ.pop("REDIS_URL", None)
            with pytest.raises(ValueError, match="REDIS_URL"):
                _get_redis_settings()


# ============================================================================
# Enqueue logic
# ============================================================================

class TestEnqueueJob:
    """enqueue_job() dispatches to ARQ pool."""

    @pytest.mark.asyncio
    async def test_enqueue_success(self):
        import job_queue

        mock_pool = AsyncMock()
        mock_job = MagicMock()
        mock_job.job_id = "test-123"
        mock_pool.enqueue_job = AsyncMock(return_value=mock_job)
        mock_pool.ping = AsyncMock(return_value=True)
        job_queue._arq_pool = mock_pool

        result = await job_queue.enqueue_job("llm_summary_job", "s1", [], "sector")
        assert result is mock_job
        mock_pool.enqueue_job.assert_awaited_once()
        job_queue._arq_pool = None

    @pytest.mark.asyncio
    async def test_enqueue_returns_none_when_unavailable(self):
        import job_queue
        job_queue._arq_pool = None

        with patch.object(job_queue, "_get_redis_settings", side_effect=ValueError("no REDIS_URL")):
            result = await job_queue.enqueue_job("llm_summary_job", "s1", [], "sector")
            assert result is None

    @pytest.mark.asyncio
    async def test_enqueue_handles_exception(self):
        import job_queue

        mock_pool = AsyncMock()
        mock_pool.ping = AsyncMock(return_value=True)
        mock_pool.enqueue_job = AsyncMock(side_effect=RuntimeError("enqueue failed"))
        job_queue._arq_pool = mock_pool

        result = await job_queue.enqueue_job("llm_summary_job", "s1", [], "sector")
        assert result is None
        job_queue._arq_pool = None


# ============================================================================
# Result persistence
# ============================================================================

class TestResultPersistence:
    """AC9/AC14: persist_job_result / get_job_result."""

    @pytest.mark.asyncio
    async def test_persist_stores_with_ttl(self):
        """persist_job_result stores JSON with 1h TTL."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()

        with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=mock_redis)):
            from job_queue import persist_job_result
            await persist_job_result("search-1", "resumo_json", {"key": "value"})

        mock_redis.set.assert_awaited_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "smartlic:job_result:search-1:resumo_json"
        assert call_args[1].get("ex") == 3600 or (len(call_args[0]) > 2 and call_args[0][2] == 3600)

    @pytest.mark.asyncio
    async def test_get_returns_deserialized_json(self):
        """get_job_result deserializes JSON from Redis."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({"key": "value"}))

        with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=mock_redis)):
            from job_queue import get_job_result
            result = await get_job_result("search-1", "resumo_json")
            assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_returns_none_when_missing(self):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=mock_redis)):
            from job_queue import get_job_result
            result = await get_job_result("search-1", "nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_persist_noop_without_redis(self):
        with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=None)):
            from job_queue import persist_job_result
            await persist_job_result("s1", "field", "value")  # should not raise

    @pytest.mark.asyncio
    async def test_get_noop_without_redis(self):
        with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=None)):
            from job_queue import get_job_result
            result = await get_job_result("s1", "field")
            assert result is None


# ============================================================================
# AC7-AC11: LLM Summary Job
# ============================================================================

class TestLlmSummaryJob:
    """AC7-AC11: Background LLM summary generation."""

    @pytest.mark.asyncio
    async def test_generates_summary_successfully(self):
        """AC8: Calls gerar_resumo and persists result."""
        from job_queue import llm_summary_job

        mock_resumo = MagicMock()
        mock_resumo.total_oportunidades = 5
        mock_resumo.valor_total = 100000
        mock_resumo.model_dump = MagicMock(return_value={
            "resumo_executivo": "Test summary",
            "total_oportunidades": 3,
            "valor_total": 50000,
            "destaques": ["d1"],
        })

        licitacoes = [
            {"valorTotalEstimado": 20000},
            {"valorTotalEstimado": 30000},
            {"valorTotalEstimado": 50000},
        ]

        with patch("llm.gerar_resumo", return_value=mock_resumo) as mock_gerar:
            with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=AsyncMock(set=AsyncMock()))):
                with patch("progress.get_tracker", new_callable=lambda: AsyncMock(return_value=None)):
                    result = await llm_summary_job({}, "search-1", licitacoes, "vestuario")

        mock_gerar.assert_called_once_with(licitacoes, sector_name="vestuario", termos_busca=None)
        assert result is not None

    @pytest.mark.asyncio
    async def test_falls_back_on_llm_failure(self):
        """AC8: Falls back to gerar_resumo_fallback on LLM error."""
        from job_queue import llm_summary_job

        mock_fallback = MagicMock()
        mock_fallback.total_oportunidades = 2
        mock_fallback.valor_total = 0
        mock_fallback.model_dump = MagicMock(return_value={"resumo_executivo": "Fallback"})

        with patch("llm.gerar_resumo", side_effect=RuntimeError("OpenAI down")):
            with patch("llm.gerar_resumo_fallback", return_value=mock_fallback) as mock_fb:
                with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=AsyncMock(set=AsyncMock()))):
                    with patch("progress.get_tracker", new_callable=lambda: AsyncMock(return_value=None)):
                        await llm_summary_job({}, "s1", [{"valorTotalEstimado": 10}], "limpeza")

        mock_fb.assert_called_once()

    @pytest.mark.asyncio
    async def test_emits_sse_event(self):
        """AC19: Emits llm_ready SSE event after completion."""
        from job_queue import llm_summary_job

        mock_resumo = MagicMock()
        mock_resumo.total_oportunidades = 1
        mock_resumo.valor_total = 0
        mock_resumo.model_dump = MagicMock(return_value={"resumo_executivo": "Test"})

        mock_tracker = AsyncMock()

        with patch("llm.gerar_resumo", return_value=mock_resumo):
            with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=AsyncMock(set=AsyncMock()))):
                with patch("progress.get_tracker", new_callable=lambda: AsyncMock(return_value=mock_tracker)):
                    await llm_summary_job({}, "s1", [], "sector")

        mock_tracker.emit.assert_awaited_once_with(
            "llm_ready", 85, "Resumo pronto",
            resumo=mock_resumo.model_dump(),
        )

    @pytest.mark.asyncio
    async def test_overrides_counts_with_actuals(self):
        """AC8: Overrides LLM-generated counts with actual values."""
        from job_queue import llm_summary_job

        mock_resumo = MagicMock()
        mock_resumo.total_oportunidades = 999
        mock_resumo.valor_total = 999999
        mock_resumo.model_dump = MagicMock(return_value={})

        licitacoes = [
            {"valorTotalEstimado": 100},
            {"valorTotalEstimado": 200},
        ]

        with patch("llm.gerar_resumo", return_value=mock_resumo):
            with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=AsyncMock(set=AsyncMock()))):
                with patch("progress.get_tracker", new_callable=lambda: AsyncMock(return_value=None)):
                    await llm_summary_job({}, "s1", licitacoes, "sector")

        assert mock_resumo.total_oportunidades == 2
        assert mock_resumo.valor_total == 300


# ============================================================================
# AC12-AC16: Excel Generation Job
# ============================================================================

class TestExcelGenerationJob:
    """AC12-AC16: Background Excel generation."""

    @pytest.mark.asyncio
    async def test_generates_and_uploads(self):
        """AC13: Calls create_excel + upload_excel."""
        from job_queue import excel_generation_job

        mock_buffer = BytesIO(b"fake excel data")
        mock_storage = {"signed_url": "https://example.com/file.xlsx", "file_path": "test.xlsx"}

        with patch("excel.create_excel", return_value=mock_buffer):
            with patch("storage.upload_excel", return_value=mock_storage):
                with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=AsyncMock(set=AsyncMock()))):
                    with patch("progress.get_tracker", new_callable=lambda: AsyncMock(return_value=None)):
                        result = await excel_generation_job({}, "s1", [{"data": 1}], True)

        assert result["excel_status"] == "ready"
        assert result["download_url"] == "https://example.com/file.xlsx"

    @pytest.mark.asyncio
    async def test_skips_when_not_allowed(self):
        """AC13: Skips Excel when allow_excel=False."""
        from job_queue import excel_generation_job

        with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=AsyncMock(set=AsyncMock()))):
            with patch("progress.get_tracker", new_callable=lambda: AsyncMock(return_value=None)):
                result = await excel_generation_job({}, "s1", [], False)

        assert result["excel_status"] == "skipped"
        assert result["download_url"] is None

    @pytest.mark.asyncio
    async def test_handles_upload_failure(self):
        """AC15: Returns failed status on upload error."""
        from job_queue import excel_generation_job

        mock_buffer = BytesIO(b"data")

        with patch("excel.create_excel", return_value=mock_buffer):
            with patch("storage.upload_excel", side_effect=RuntimeError("S3 error")):
                with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=AsyncMock(set=AsyncMock()))):
                    with patch("progress.get_tracker", new_callable=lambda: AsyncMock(return_value=None)):
                        result = await excel_generation_job({}, "s1", [{}], True)

        assert result["excel_status"] == "failed"
        assert result["download_url"] is None

    @pytest.mark.asyncio
    async def test_emits_sse_ready_event(self):
        """AC20: Emits excel_ready SSE event with download_url."""
        from job_queue import excel_generation_job

        mock_buffer = BytesIO(b"data")
        mock_storage = {"signed_url": "https://dl.example.com/file.xlsx", "file_path": "f.xlsx"}
        mock_tracker = AsyncMock()

        with patch("excel.create_excel", return_value=mock_buffer):
            with patch("storage.upload_excel", return_value=mock_storage):
                with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=AsyncMock(set=AsyncMock()))):
                    with patch("progress.get_tracker", new_callable=lambda: AsyncMock(return_value=mock_tracker)):
                        await excel_generation_job({}, "s1", [{}], True)

        mock_tracker.emit.assert_awaited_once_with(
            "excel_ready", 98, "Planilha pronta para download",
            download_url="https://dl.example.com/file.xlsx",
        )

    @pytest.mark.asyncio
    async def test_emits_sse_failed_event(self):
        """AC20: Emits excel_ready with failed status on error."""
        from job_queue import excel_generation_job

        mock_buffer = BytesIO(b"data")
        mock_tracker = AsyncMock()

        with patch("excel.create_excel", return_value=mock_buffer):
            with patch("storage.upload_excel", return_value=None):
                with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=AsyncMock(set=AsyncMock()))):
                    with patch("progress.get_tracker", new_callable=lambda: AsyncMock(return_value=mock_tracker)):
                        await excel_generation_job({}, "s1", [{}], True)

        mock_tracker.emit.assert_awaited_once_with(
            "excel_ready", 98, "Erro ao gerar planilha. Tente novamente.",
            excel_status="failed",
        )

    @pytest.mark.asyncio
    async def test_handles_create_excel_failure(self):
        """AC15: Handles create_excel() throwing."""
        from job_queue import excel_generation_job

        with patch("excel.create_excel", side_effect=RuntimeError("openpyxl error")):
            with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=AsyncMock(set=AsyncMock()))):
                with patch("progress.get_tracker", new_callable=lambda: AsyncMock(return_value=None)):
                    result = await excel_generation_job({}, "s1", [{}], True)

        assert result["excel_status"] == "failed"


# ============================================================================
# AC17/AC22: Pipeline integration — queue vs inline decision
# ============================================================================

class TestPipelineQueueDecision:
    """AC17/AC22: Pipeline dispatches to queue or falls back to inline."""

    def test_busca_response_has_llm_status_field(self):
        """AC18: BuscaResponse schema includes llm_status."""
        from schemas import BuscaResponse
        fields = BuscaResponse.model_fields
        assert "llm_status" in fields

    def test_busca_response_has_excel_status_field(self):
        """AC18: BuscaResponse schema includes excel_status."""
        from schemas import BuscaResponse
        fields = BuscaResponse.model_fields
        assert "excel_status" in fields

    def test_health_dependencies_has_queue_field(self):
        """AC4: HealthDependencies includes queue status."""
        from schemas import HealthDependencies
        fields = HealthDependencies.model_fields
        assert "queue" in fields

    def test_search_context_has_queue_fields(self):
        """SearchContext carries queue mode state."""
        from search_context import SearchContext
        ctx = SearchContext(request=MagicMock(), user={})
        assert ctx.queue_mode is False
        assert ctx.llm_status is None
        assert ctx.excel_status is None

    def test_search_context_queue_mode_settable(self):
        """SearchContext queue fields are writable."""
        from search_context import SearchContext
        ctx = SearchContext(request=MagicMock(), user={})
        ctx.queue_mode = True
        ctx.llm_status = "processing"
        ctx.excel_status = "processing"
        assert ctx.queue_mode is True
        assert ctx.llm_status == "processing"
        assert ctx.excel_status == "processing"
