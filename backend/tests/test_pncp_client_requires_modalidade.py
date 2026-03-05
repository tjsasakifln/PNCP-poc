"""CRIT-FLT-008 AC3: Validate that PNCP requests without codigoModalidadeContratacao are blocked.

The PNCP API changed codigoModalidadeContratacao from optional to required.
Requests without it return HTTP 400. These tests verify our guards catch this
before any request leaves the application.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pncp_client import PNCPClient, AsyncPNCPClient


class TestSyncClientRequiresModalidade:
    """Tests for synchronous PNCPClient modalidade guard."""

    def setup_method(self):
        self.client = PNCPClient()

    def test_fetch_page_rejects_zero_modalidade(self):
        """fetch_page raises ValueError when modalidade=0."""
        with pytest.raises(ValueError, match="codigoModalidadeContratacao is required"):
            self.client.fetch_page(
                data_inicial="2026-01-01",
                data_final="2026-01-10",
                modalidade=0,
                uf="SP",
            )

    def test_fetch_page_accepts_valid_modalidade(self):
        """fetch_page does NOT raise ValueError when modalidade is valid (e.g., 6).

        We mock session.get to avoid hitting the real API and verify the guard
        is not triggered for valid modalidade values.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "data": [],
            "totalRegistros": 0,
            "totalPaginas": 0,
            "paginaAtual": 1,
            "temProximaPagina": False,
        }

        # Patch session.get on the already-created client instance
        self.client.session.get = MagicMock(return_value=mock_response)

        result = self.client.fetch_page(
            data_inicial="2026-01-01",
            data_final="2026-01-10",
            modalidade=6,
            uf="SP",
        )
        assert result["totalRegistros"] == 0

        # Verify the request was made with codigoModalidadeContratacao
        call_kwargs = self.client.session.get.call_args
        params_sent = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params", {})
        assert params_sent.get("codigoModalidadeContratacao") == 6


class TestAsyncClientRequiresModalidade:
    """Tests for asynchronous AsyncPNCPClient modalidade guard."""

    @pytest.mark.asyncio
    async def test_fetch_page_async_rejects_zero_modalidade(self):
        """_fetch_page_async raises ValueError when modalidade=0."""
        async with AsyncPNCPClient() as client:
            with pytest.raises(ValueError, match="codigoModalidadeContratacao is required"):
                await client._fetch_page_async(
                    data_inicial="2026-01-01",
                    data_final="2026-01-10",
                    modalidade=0,
                    uf="SP",
                )

    @pytest.mark.asyncio
    async def test_fetch_page_async_accepts_valid_modalidade(self):
        """_fetch_page_async does NOT raise ValueError when modalidade is valid."""
        async with AsyncPNCPClient() as client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [],
                "totalRegistros": 0,
                "totalPaginas": 0,
                "paginaAtual": 1,
                "temProximaPagina": False,
            }
            mock_response.headers = {"content-type": "application/json"}
            mock_response.text = ""

            client._client.get = AsyncMock(return_value=mock_response)

            result = await client._fetch_page_async(
                data_inicial="2026-01-01",
                data_final="2026-01-10",
                modalidade=6,
                uf="SP",
            )
            assert result["totalRegistros"] == 0


class TestHealthCanaryIncludesModalidade:
    """CRIT-FLT-008 AC2: Verify health_canary sends codigoModalidadeContratacao."""

    @pytest.mark.asyncio
    @patch("cron_jobs.get_pncp_cron_status", return_value={"status": "healthy", "latency_ms": 100, "updated_at": 1000})
    async def test_health_canary_params_include_modalidade(self, _mock_cron):
        """health_canary must include codigoModalidadeContratacao in its request params."""
        async with AsyncPNCPClient() as client:
            captured_params = {}

            async def mock_get(url, params=None, **kwargs):
                captured_params.update(params or {})
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {"data": [], "totalRegistros": 0}
                return mock_resp

            client._client.get = mock_get

            await client.health_canary()

            assert "codigoModalidadeContratacao" in captured_params, (
                "health_canary MUST send codigoModalidadeContratacao — "
                "PNCP API returns HTTP 400 without it"
            )
            assert captured_params["codigoModalidadeContratacao"] == 6

    @pytest.mark.asyncio
    @patch("cron_jobs.get_pncp_cron_status", return_value={"status": "healthy", "latency_ms": 100, "updated_at": 1000})
    async def test_health_canary_params_include_all_required_fields(self, _mock_cron):
        """health_canary must send all PNCP required params."""
        async with AsyncPNCPClient() as client:
            captured_params = {}

            async def mock_get(url, params=None, **kwargs):
                captured_params.update(params or {})
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {"data": [], "totalRegistros": 0}
                return mock_resp

            client._client.get = mock_get
            await client.health_canary()

            required_fields = [
                "dataInicial",
                "dataFinal",
                "codigoModalidadeContratacao",
                "pagina",
                "tamanhoPagina",
            ]
            for field in required_fields:
                assert field in captured_params, f"health_canary missing required param: {field}"


class TestBuildPncpLinkPriority:
    """CRIT-FLT-008 AC4: Verify link priority in _build_pncp_link."""

    def test_prioritizes_link_sistema_origem(self):
        """linkSistemaOrigem should be used when present."""
        from search_pipeline import _build_pncp_link

        lic = {
            "linkSistemaOrigem": "https://compras.gov.br/edital/123",
            "linkProcessoEletronico": "https://processo.gov.br/456",
        }
        assert _build_pncp_link(lic) == "https://compras.gov.br/edital/123"

    def test_falls_back_to_link_processo_eletronico(self):
        """Falls back to linkProcessoEletronico when linkSistemaOrigem is absent."""
        from search_pipeline import _build_pncp_link

        lic = {"linkProcessoEletronico": "https://processo.gov.br/456"}
        assert _build_pncp_link(lic) == "https://processo.gov.br/456"

    def test_constructs_url_from_numero_controle(self):
        """Constructs PNCP URL from numeroControlePNCP when both links are absent."""
        from search_pipeline import _build_pncp_link

        lic = {"numeroControlePNCP": "12345678000190-1-000001/2026"}
        result = _build_pncp_link(lic)
        assert "pncp.gov.br/app/editais" in result
        assert "12345678000190" in result

    def test_returns_none_when_no_link_data(self):
        """UX-400 AC2: Returns None (not empty string) when no link data is available."""
        from search_pipeline import _build_pncp_link

        assert _build_pncp_link({}) is None
