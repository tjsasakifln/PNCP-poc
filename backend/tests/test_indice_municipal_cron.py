"""Tests for STORY-435 AC7: Índice Municipal quarterly cron job."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone


def test_prev_quarter_label_q1():
    """Q1 -> previous year Q4."""
    from jobs.cron.indice_municipal import _prev_quarter_label
    with patch("jobs.cron.indice_municipal.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 2, 15, tzinfo=timezone.utc)
        result = _prev_quarter_label()
    assert result == "2025-Q4"


def test_prev_quarter_label_q2():
    """Q2 -> Q1 of same year."""
    from jobs.cron.indice_municipal import _prev_quarter_label
    with patch("jobs.cron.indice_municipal.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 5, 10, tzinfo=timezone.utc)
        result = _prev_quarter_label()
    assert result == "2026-Q1"


def test_prev_quarter_label_q3():
    """Q3 -> Q2 of same year."""
    from jobs.cron.indice_municipal import _prev_quarter_label
    with patch("jobs.cron.indice_municipal.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 8, 1, tzinfo=timezone.utc)
        result = _prev_quarter_label()
    assert result == "2026-Q2"


def test_prev_quarter_label_q4():
    """Q4 -> Q3 of same year."""
    from jobs.cron.indice_municipal import _prev_quarter_label
    with patch("jobs.cron.indice_municipal.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 11, 1, tzinfo=timezone.utc)
        result = _prev_quarter_label()
    assert result == "2026-Q3"


@pytest.mark.asyncio
async def test_run_indice_municipal_recalc_calls_service():
    """run_indice_municipal_recalc chama recalcular_municipios_existentes."""
    mock_result = {
        "periodo": "2026-Q1", "calculated": 5,
        "persisted": 5, "errors": 0, "duration_s": 1.2,
    }
    mock_recalc = AsyncMock(return_value=mock_result)
    mock_send_email = AsyncMock()

    import jobs.cron.indice_municipal as cron_mod
    with (
        patch.object(cron_mod, "_prev_quarter_label", return_value="2026-Q1"),
        patch.dict("sys.modules", {
            "services.indice_municipal": MagicMock(
                recalcular_municipios_existentes=mock_recalc
            ),
            "email_service": MagicMock(send_email_async=mock_send_email),
        }),
    ):
        result = await cron_mod.run_indice_municipal_recalc()

    assert result["calculated"] == 5
    assert result["persisted"] == 5
    mock_recalc.assert_called_once_with("2026-Q1")


@pytest.mark.asyncio
async def test_run_indice_municipal_recalc_graceful_on_error():
    """run_indice_municipal_recalc retorna dict de erro sem levantar exceção."""
    import jobs.cron.indice_municipal as cron_mod

    with (
        patch.object(cron_mod, "_prev_quarter_label", return_value="2026-Q1"),
        patch.dict("sys.modules", {
            "services.indice_municipal": MagicMock(
                recalcular_municipios_existentes=AsyncMock(
                    side_effect=RuntimeError("DB offline")
                )
            ),
        }),
    ):
        result = await cron_mod.run_indice_municipal_recalc()

    assert result.get("status") == "error"
    assert "DB offline" in result.get("error", "")


@pytest.mark.asyncio
async def test_run_indice_municipal_recalc_email_failure_does_not_abort():
    """Falha no envio de email não aborta o job — resultado é retornado."""
    mock_result = {
        "periodo": "2026-Q1", "calculated": 3,
        "persisted": 3, "errors": 0, "duration_s": 0.5,
    }
    import jobs.cron.indice_municipal as cron_mod

    with (
        patch.object(cron_mod, "_prev_quarter_label", return_value="2026-Q1"),
        patch.dict("sys.modules", {
            "services.indice_municipal": MagicMock(
                recalcular_municipios_existentes=AsyncMock(return_value=mock_result)
            ),
            "email_service": MagicMock(
                send_email_async=AsyncMock(side_effect=Exception("SMTP error"))
            ),
        }),
    ):
        result = await cron_mod.run_indice_municipal_recalc()

    # Job must succeed even if email fails
    assert result["calculated"] == 3
    assert "error" not in result or result.get("status") != "error"


def test_start_indice_municipal_task_is_importable():
    """start_indice_municipal_task está disponível em cron_jobs facade."""
    from cron_jobs import start_indice_municipal_task
    assert callable(start_indice_municipal_task)


def test_run_indice_municipal_recalc_is_importable():
    """run_indice_municipal_recalc está disponível em cron_jobs facade."""
    from cron_jobs import run_indice_municipal_recalc
    assert callable(run_indice_municipal_recalc)


def test_indice_municipal_interval_is_90_days():
    """INDICE_MUNICIPAL_INTERVAL deve ser 90 dias em segundos."""
    from jobs.cron.indice_municipal import INDICE_MUNICIPAL_INTERVAL
    assert INDICE_MUNICIPAL_INTERVAL == 90 * 24 * 60 * 60
