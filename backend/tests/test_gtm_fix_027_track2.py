"""GTM-FIX-027 Track 2: Status filter date range tests."""
import pytest
from datetime import date, timedelta, datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from search_pipeline import SearchPipeline
from schemas import BuscaRequest


@pytest.mark.asyncio
async def test_abertas_mode_uses_wide_window():
    """AC8+AC13: Default date range for modo_busca='abertas' is a wide window.

    STORY-BTS-009: The original test expected a 10-day window. Production
    `pipeline/stages/prepare.py` was updated (commit `933a5c6a`
    "feat(ingestion): cobertura 100% de editais abertos — backfill + purge por
    encerramento") to set a **730-day** window because the search_datalake RPC
    ignores date bounds entirely for `abertas` mode (only filters by
    `data_encerramento > now()`); wide defaults just keep the cache key and
    logging surface meaningful. This test mirrors that production contract.
    """
    # Create a valid request with required fields (modo_busca will override dates)
    today = date.today()
    request = BuscaRequest(
        setor_id="vestuario",
        ufs=["SP"],
        data_inicial=(today - timedelta(days=1)).isoformat(),  # dummy value
        data_final=today.isoformat(),  # dummy value
        modo_busca="abertas",
    )

    class FakeContext:
        def __init__(self):
            self.request = request
            self.sector = None
            self.tracker = None  # SSE progress tracker not needed for this test

    ctx = FakeContext()

    # Mock get_sector
    with patch('pipeline.stages.prepare.get_sector') as mock_get_sector:
        mock_get_sector.return_value = MagicMock(
            name="Vestuário",
            keywords=["vestuario"],
            exclusions=[],
            custom_terms=None
        )

        # Create pipeline with minimal dependencies
        deps = SimpleNamespace(
            validate_terms=lambda terms: {'valid': True, 'terms': []}
        )
        pipeline = SearchPipeline(deps)

        # Call stage_prepare which overrides dates for modo_busca='abertas'
        await pipeline.stage_prepare(ctx)

    today_utc = datetime.now(timezone.utc).date()
    expected_start = (today_utc - timedelta(days=730)).isoformat()
    expected_end = today_utc.isoformat()
    assert ctx.request.data_inicial == expected_start, f"Expected {expected_start}, got {ctx.request.data_inicial}"
    assert ctx.request.data_final == expected_end


def test_status_inference_not_modified():
    """AC9: 'divulgada' NOT in situacoes_abertas (2026-02-09 fix preserved)."""
    from status_inference import inferir_status_licitacao
    import inspect

    # Get the source code
    source = inspect.getsource(inferir_status_licitacao)

    # Verify that "divulgada" is NOT in situacoes_abertas list
    # Find the situacoes_abertas definition
    if "situacoes_abertas" in source.lower():
        # Extract the list definition
        start_idx = source.lower().index("situacoes_abertas")
        list_section = source[start_idx:start_idx + 300]
        # Check that "divulgada" is not in the list
        assert '"divulgada"' not in list_section.lower(), "divulgada should NOT be in situacoes_abertas"
        assert "'divulgada'" not in list_section.lower(), "divulgada should NOT be in situacoes_abertas"

    # Test that a bid with "Divulgada no PNCP" status is NOT classified as recebendo_proposta
    # (unless it has future closing date which would override the status text)
    bid_divulgada = {
        "situacaoCompraNome": "Divulgada no PNCP",
        "valorTotalHomologado": None,
        "dataEncerramentoProposta": None,  # No date info, only status text
    }
    status = inferir_status_licitacao(bid_divulgada)
    # Should fall back to "todos" since divulgada is not in situacoes_abertas anymore
    assert status == "todos", f"Divulgada should return 'todos' (fallback), got '{status}'"
