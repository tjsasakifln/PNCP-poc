"""GTM-FIX-027 Track 3: PCP v2 config + diagnostic logging tests."""
import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from source_config.sources import SourceConfig, get_source_config


def test_pcp_config_v2_url():
    """AC16: PCP config base_url is v2."""
    config = SourceConfig()
    assert "compras.api.portaldecompraspublicas.com.br" in config.portal.base_url


def test_pcp_no_api_key():
    """AC17: PCP credentials are None after load_from_env."""
    config = get_source_config()
    assert config.portal.credentials.api_key is None


def test_pcp_validate_no_warning():
    """AC18: validate() does not warn about PCP API key."""
    config = get_source_config()
    messages = config.validate()
    pcp_warnings = [m for m in messages if "PORTAL_COMPRAS" in m or "Portal de Compras" in m]
    assert len(pcp_warnings) == 0, f"Unexpected PCP warnings: {pcp_warnings}"


@pytest.mark.asyncio
async def test_consolidation_logs_full_traceback(caplog):
    """AC15: Exception logging includes exc_info=True (full traceback)."""
    from consolidation import ConsolidationService
    from clients.base import SourceMetadata

    # Create an async generator that raises an exception
    async def failing_fetch(data_inicial, data_final, ufs):
        raise ValueError("Test error for traceback")
        yield  # Never reached but makes this a generator

    # Create a mock adapter that raises an exception
    mock_adapter = MagicMock()
    mock_adapter.code = "test_source"
    mock_adapter.metadata = SourceMetadata(
        name="Test Source",
        code="test_source",
        base_url="http://test.example.com",
        priority=1,
    )
    mock_adapter.fetch = failing_fetch
    mock_adapter.health_check = AsyncMock(return_value={"status": "available"})
    mock_adapter.close = AsyncMock()

    service = ConsolidationService(
        adapters={"test_source": mock_adapter},
        fail_on_all_errors=False,
    )

    with caplog.at_level(logging.ERROR):
        result = await service.fetch_all(
            data_inicial="2026-01-01",
            data_final="2026-02-17",
        )

    # Verify the error was logged with the new format
    error_logs = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("FAILED" in r.message or "PARTIAL" in r.message for r in error_logs), \
        f"Expected FAILED/PARTIAL in logs, got: {[r.message for r in error_logs]}"

    # Verify exc_info was set (traceback included)
    assert any(r.exc_info is not None for r in error_logs), \
        "Expected exc_info=True in error logs for full traceback"

    await service.close()
