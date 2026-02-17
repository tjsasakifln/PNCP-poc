"""Comprehensive tests for PortalComprasAdapter and calculate_total_value.

Tests cover:
- calculate_total_value function (AC29)
- Health check with various scenarios (AC27)
- Fetch with pagination, auth errors, per-UF (AC27)
- Normalize field mapping (AC27)
- Metadata validation
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from clients.base import (
    SourceAuthError,
    SourceParseError,
    SourceStatus,
    SourceTimeoutError,
)
from clients.portal_compras_client import PortalComprasAdapter, calculate_total_value


# ============ Fixtures ============


@pytest.fixture
def adapter():
    """Adapter with valid API key."""
    return PortalComprasAdapter(api_key="test-key-123", timeout=5)


@pytest.fixture
def adapter_no_key():
    """Adapter without API key."""
    return PortalComprasAdapter(api_key="", timeout=5)


@pytest.fixture
def sample_pcp_record():
    """Sample PCP API record for normalize tests."""
    return {
        "idLicitacao": "12345",
        "DS_OBJETO": "Fornecimento de uniformes profissionais",
        "lotes": [
            {
                "numeroLote": "1",
                "itens": [
                    {
                        "DS_ITEM": "Camisa polo manga curta",
                        "VL_UNITARIO_ESTIMADO": 45.50,
                        "QT_ITENS": 100,
                    },
                    {
                        "DS_ITEM": "Calça profissional",
                        "VL_UNITARIO_ESTIMADO": 89.90,
                        "QT_ITENS": 100,
                    },
                ],
            },
            {
                "numeroLote": "2",
                "itens": [
                    {
                        "DS_ITEM": "Sapato de segurança",
                        "VL_UNITARIO_ESTIMADO": 120.00,
                        "QT_ITENS": 50,
                    },
                ],
            },
        ],
        "unidadeCompradora": {
            "nomeComprador": "Prefeitura Municipal de Campinas",
            "CNPJ": "11223344000155",
            "Cidade": "Campinas",
            "UF": "SP",
        },
        "dataPublicacao": "15/01/2026 10:30:00",
        "dataAbertura": "25/01/2026",
        "dataEncerramento": "31/01/2026",
        "numeroEdital": "001/2026",
        "ano": "2026",
        "modalidade": "Pregão Eletrônico",
        "situacao": "Aberto",
    }


# ============ TestCalculateTotalValue (AC29) ============


class TestCalculateTotalValue:
    """Test calculate_total_value function with edge cases."""

    def test_normal_case_multiple_lots(self):
        """Test calculation with 2 lots, 3 items → correct sum."""
        lotes = [
            {
                "itens": [
                    {"VL_UNITARIO_ESTIMADO": 10.0, "QT_ITENS": 5},
                    {"VL_UNITARIO_ESTIMADO": 20.0, "QT_ITENS": 3},
                ]
            },
            {
                "itens": [
                    {"VL_UNITARIO_ESTIMADO": 15.0, "QT_ITENS": 2},
                ]
            },
        ]
        # Expected: (10*5) + (20*3) + (15*2) = 50 + 60 + 30 = 140.0
        assert calculate_total_value(lotes) == 140.0

    def test_null_quantity_skips_item(self):
        """Test that NULL qty → skip item with warning."""
        lotes = [
            {
                "itens": [
                    {"VL_UNITARIO_ESTIMADO": 10.0, "QT_ITENS": None},
                    {"VL_UNITARIO_ESTIMADO": 20.0, "QT_ITENS": 5},
                ]
            }
        ]
        # Expected: only 20*5 = 100.0
        assert calculate_total_value(lotes) == 100.0

    def test_null_value_skips_item(self):
        """Test that NULL value → skip item with warning."""
        lotes = [
            {
                "itens": [
                    {"VL_UNITARIO_ESTIMADO": None, "QT_ITENS": 10},
                    {"VL_UNITARIO_ESTIMADO": 15.0, "QT_ITENS": 2},
                ]
            }
        ]
        # Expected: only 15*2 = 30.0
        assert calculate_total_value(lotes) == 30.0

    def test_zero_quantity_skips_item(self):
        """Test that qty = 0 → skip item."""
        lotes = [
            {
                "itens": [
                    {"VL_UNITARIO_ESTIMADO": 10.0, "QT_ITENS": 0},
                    {"VL_UNITARIO_ESTIMADO": 20.0, "QT_ITENS": 5},
                ]
            }
        ]
        # Expected: only 20*5 = 100.0
        assert calculate_total_value(lotes) == 100.0

    def test_negative_quantity_skips_item(self):
        """Test that qty < 0 → skip item."""
        lotes = [
            {
                "itens": [
                    {"VL_UNITARIO_ESTIMADO": 10.0, "QT_ITENS": -5},
                    {"VL_UNITARIO_ESTIMADO": 20.0, "QT_ITENS": 3},
                ]
            }
        ]
        # Expected: only 20*3 = 60.0
        assert calculate_total_value(lotes) == 60.0

    def test_empty_lotes_returns_zero(self):
        """Test that empty lotes → 0.0."""
        assert calculate_total_value([]) == 0.0

    def test_non_numeric_values_skipped(self):
        """Test that non-numeric values → skip item."""
        lotes = [
            {
                "itens": [
                    {"VL_UNITARIO_ESTIMADO": "abc", "QT_ITENS": 10},
                    {"VL_UNITARIO_ESTIMADO": 20.0, "QT_ITENS": "xyz"},
                    {"VL_UNITARIO_ESTIMADO": 15.0, "QT_ITENS": 2},
                ]
            }
        ]
        # Expected: only 15*2 = 30.0
        assert calculate_total_value(lotes) == 30.0

    def test_rounding_to_2_decimals(self):
        """Test that result rounded to 2 decimal places."""
        lotes = [
            {
                "itens": [
                    {"VL_UNITARIO_ESTIMADO": 10.123, "QT_ITENS": 3},
                ]
            }
        ]
        # Expected: 10.123 * 3 = 30.369 → rounded to 30.37
        assert calculate_total_value(lotes) == 30.37

    def test_missing_itens_key(self):
        """Test that missing 'itens' key → treated as empty."""
        lotes = [{"numeroLote": "1"}]
        assert calculate_total_value(lotes) == 0.0

    def test_none_itens_value(self):
        """Test that itens = None → treated as empty."""
        lotes = [{"itens": None}]
        assert calculate_total_value(lotes) == 0.0


# ============ TestHealthCheck (AC27) ============


class TestHealthCheck:
    """Test health_check with various scenarios."""

    @pytest.mark.asyncio
    async def test_health_check_with_valid_key(self, adapter):
        """Test health_check with API key → AVAILABLE."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        # Mock time for fast response (<3s)
        with patch.object(asyncio, "get_running_loop") as mock_loop:
            mock_loop.return_value.time.side_effect = [0.0, 0.5]  # 500ms elapsed
            status = await adapter.health_check()

        assert status == SourceStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_health_check_no_key(self, adapter_no_key):
        """Test health_check without API key → UNAVAILABLE."""
        status = await adapter_no_key.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_health_check_auth_failure(self, adapter):
        """Test health_check with 401 → UNAVAILABLE."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_health_check_timeout(self, adapter):
        """Test health_check with timeout → UNAVAILABLE."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_health_check_slow_response(self, adapter):
        """Test health_check with >3s response → DEGRADED."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        # Mock time for slow response (>3s)
        with patch.object(asyncio, "get_running_loop") as mock_loop:
            mock_loop.return_value.time.side_effect = [0.0, 3.5]  # 3500ms elapsed
            status = await adapter.health_check()

        assert status == SourceStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_health_check_403_forbidden(self, adapter):
        """Test health_check with 403 → UNAVAILABLE."""
        mock_response = MagicMock()
        mock_response.status_code = 403

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_health_check_server_error(self, adapter):
        """Test health_check with 500 → DEGRADED."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch.object(asyncio, "get_running_loop") as mock_loop:
            mock_loop.return_value.time.side_effect = [0.0, 1.0]
            status = await adapter.health_check()

        assert status == SourceStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_health_check_request_error(self, adapter):
        """Test health_check with RequestError → UNAVAILABLE."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE


# ============ TestFetch (AC27) ============


class TestFetch:
    """Test fetch with pagination, auth errors, per-UF."""

    @pytest.mark.asyncio
    async def test_fetch_no_api_key_returns_empty(self, adapter_no_key):
        """Test that fetch with no API key returns empty (no crash)."""
        records = []
        async for record in adapter_no_key.fetch("2026-01-01", "2026-01-31"):
            records.append(record)

        assert len(records) == 0

    @pytest.mark.asyncio
    async def test_fetch_single_page(self, adapter):
        """Test fetch with single page of 3 records."""
        mock_response = [
            {
                "idLicitacao": "P001",
                "DS_OBJETO": "Objeto 1",
                "lotes": [],
                "valorEstimado": 10000,
                "unidadeCompradora": {"UF": "SP"},
            },
            {
                "idLicitacao": "P002",
                "DS_OBJETO": "Objeto 2",
                "lotes": [],
                "valorEstimado": 20000,
                "unidadeCompradora": {"UF": "SP"},
            },
            {
                "idLicitacao": "P003",
                "DS_OBJETO": "Objeto 3",
                "lotes": [],
                "valorEstimado": 30000,
                "unidadeCompradora": {"UF": "SP"},
            },
        ]

        with patch.object(
            adapter, "_request_with_retry", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            records = []
            async for record in adapter.fetch("2026-01-01", "2026-01-31", ufs={"SP"}):
                records.append(record)

        assert len(records) == 3
        assert records[0].source_id == "pcp_P001"
        assert records[1].source_id == "pcp_P002"
        assert records[2].source_id == "pcp_P003"

    @pytest.mark.asyncio
    async def test_fetch_pagination(self, adapter):
        """Test fetch with pagination (2 pages)."""
        page1_response = {
            "processos": [
                {
                    "idLicitacao": "P001",
                    "DS_OBJETO": "Objeto 1",
                    "lotes": [],
                    "valorEstimado": 10000,
                    "unidadeCompradora": {"UF": "SP"},
                },
            ],
            "quantidadeTotal": 2,
        }

        page2_response = {
            "processos": [
                {
                    "idLicitacao": "P002",
                    "DS_OBJETO": "Objeto 2",
                    "lotes": [],
                    "valorEstimado": 20000,
                    "unidadeCompradora": {"UF": "SP"},
                },
            ],
            "quantidadeTotal": 2,
        }

        with patch.object(
            adapter, "_request_with_retry", new_callable=AsyncMock
        ) as mock_request:
            mock_request.side_effect = [page1_response, page2_response]

            records = []
            async for record in adapter.fetch("2026-01-01", "2026-01-31", ufs={"SP"}):
                records.append(record)

        assert len(records) == 2
        assert records[0].source_id == "pcp_P001"
        assert records[1].source_id == "pcp_P002"

    @pytest.mark.asyncio
    async def test_fetch_auth_error_raises(self, adapter):
        """Test fetch with auth error raises SourceAuthError."""
        with patch.object(
            adapter, "_request_with_retry", new_callable=AsyncMock
        ) as mock_request:
            mock_request.side_effect = SourceAuthError("PORTAL_COMPRAS", "Invalid key")

            with pytest.raises(SourceAuthError):
                records = []
                async for record in adapter.fetch("2026-01-01", "2026-01-31"):
                    records.append(record)

    @pytest.mark.asyncio
    async def test_fetch_per_uf(self, adapter):
        """Test fetch with multiple UFs iterates per-UF."""
        sp_response = [
            {
                "idLicitacao": "SP001",
                "DS_OBJETO": "SP Objeto",
                "lotes": [],
                "valorEstimado": 10000,
                "unidadeCompradora": {"UF": "SP"},
            },
        ]

        rj_response = [
            {
                "idLicitacao": "RJ001",
                "DS_OBJETO": "RJ Objeto",
                "lotes": [],
                "valorEstimado": 20000,
                "unidadeCompradora": {"UF": "RJ"},
            },
        ]

        with patch.object(
            adapter, "_request_with_retry", new_callable=AsyncMock
        ) as mock_request:
            mock_request.side_effect = [sp_response, rj_response]

            records = []
            async for record in adapter.fetch(
                "2026-01-01", "2026-01-31", ufs={"SP", "RJ"}
            ):
                records.append(record)

        assert len(records) == 2
        # Should be sorted by UF (RJ, SP)
        ufs_fetched = {r.uf for r in records}
        assert ufs_fetched == {"SP", "RJ"}

    @pytest.mark.asyncio
    async def test_fetch_empty_response(self, adapter):
        """Test fetch with empty response returns 0 records."""
        with patch.object(
            adapter, "_request_with_retry", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = []

            records = []
            async for record in adapter.fetch("2026-01-01", "2026-01-31"):
                records.append(record)

        assert len(records) == 0

    @pytest.mark.asyncio
    async def test_fetch_deduplication(self, adapter):
        """Test fetch deduplicates records with same source_id."""
        # Response with duplicate idLicitacao
        mock_response = [
            {
                "idLicitacao": "P001",
                "DS_OBJETO": "Objeto 1",
                "lotes": [],
                "valorEstimado": 10000,
                "unidadeCompradora": {"UF": "SP"},
            },
            {
                "idLicitacao": "P001",  # Duplicate
                "DS_OBJETO": "Objeto 1 duplicado",
                "lotes": [],
                "valorEstimado": 10000,
                "unidadeCompradora": {"UF": "SP"},
            },
        ]

        with patch.object(
            adapter, "_request_with_retry", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            records = []
            async for record in adapter.fetch("2026-01-01", "2026-01-31"):
                records.append(record)

        assert len(records) == 1  # Only one record, duplicate skipped
        assert records[0].source_id == "pcp_P001"

    @pytest.mark.asyncio
    async def test_fetch_normalize_error_skips_record(self, adapter):
        """Test fetch skips record if normalize fails."""
        mock_response = [
            {
                # Missing idLicitacao → normalize will fail
                "DS_OBJETO": "Objeto sem ID",
                "lotes": [],
            },
            {
                "idLicitacao": "P002",
                "DS_OBJETO": "Objeto valido",
                "lotes": [],
                "valorEstimado": 10000,
                "unidadeCompradora": {"UF": "SP"},
            },
        ]

        with patch.object(
            adapter, "_request_with_retry", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            records = []
            async for record in adapter.fetch("2026-01-01", "2026-01-31"):
                records.append(record)

        assert len(records) == 1  # Only valid record
        assert records[0].source_id == "pcp_P002"


# ============ TestNormalize (AC27) ============


class TestNormalize:
    """Test normalize field mapping."""

    def test_normalize_full_record(self, adapter, sample_pcp_record):
        """Test normalize with full PCP record maps all fields correctly."""
        record = adapter.normalize(sample_pcp_record)

        assert record.source_id == "pcp_12345"
        assert record.source_name == "PORTAL_COMPRAS"
        assert "Fornecimento de uniformes profissionais" in record.objeto
        assert "Camisa polo manga curta" in record.objeto
        assert "Calça profissional" in record.objeto
        assert "Sapato de segurança" in record.objeto
        # Value: (45.5*100) + (89.9*100) + (120*50) = 4550 + 8990 + 6000 = 19540.0
        assert record.valor_estimado == 19540.0
        assert record.orgao == "Prefeitura Municipal de Campinas"
        assert record.cnpj_orgao == "11223344000155"
        assert record.uf == "SP"
        assert record.municipio == "Campinas"
        assert record.numero_edital == "001/2026"
        assert record.ano == "2026"
        assert record.modalidade == "Pregão Eletrônico"
        assert record.situacao == "Aberto"
        assert (
            record.link_portal
            == "https://www.portaldecompraspublicas.com.br/processos/12345"
        )

    def test_normalize_source_id_prefix(self, adapter):
        """Test normalize prefixes source_id with 'pcp_'."""
        raw = {
            "idLicitacao": "ABC123",
            "DS_OBJETO": "Test",
            "lotes": [],
            "unidadeCompradora": {},
        }
        record = adapter.normalize(raw)
        assert record.source_id == "pcp_ABC123"

    def test_normalize_objeto_concatenation(self, adapter):
        """Test normalize concatenates DS_OBJETO + DS_ITEM with ' | '."""
        raw = {
            "idLicitacao": "123",
            "DS_OBJETO": "Contratação de serviços",
            "lotes": [
                {
                    "itens": [
                        {"DS_ITEM": "Item A", "VL_UNITARIO_ESTIMADO": 10, "QT_ITENS": 1},
                        {"DS_ITEM": "Item B", "VL_UNITARIO_ESTIMADO": 20, "QT_ITENS": 1},
                    ]
                }
            ],
            "unidadeCompradora": {},
        }
        record = adapter.normalize(raw)
        assert record.objeto == "Contratação de serviços | Item A | Item B"

    def test_normalize_value_from_lotes(self, adapter):
        """Test normalize calculates value from lotes using calculate_total_value."""
        raw = {
            "idLicitacao": "123",
            "DS_OBJETO": "Test",
            "lotes": [
                {
                    "itens": [
                        {"VL_UNITARIO_ESTIMADO": 100.0, "QT_ITENS": 5},
                        {"VL_UNITARIO_ESTIMADO": 50.0, "QT_ITENS": 10},
                    ]
                }
            ],
            "unidadeCompradora": {},
        }
        record = adapter.normalize(raw)
        # Expected: (100*5) + (50*10) = 500 + 500 = 1000.0
        assert record.valor_estimado == 1000.0

    def test_normalize_missing_id_raises_error(self, adapter):
        """Test normalize raises SourceParseError when idLicitacao missing."""
        raw = {
            "DS_OBJETO": "Objeto sem ID",
            "lotes": [],
            "unidadeCompradora": {},
        }
        with pytest.raises(SourceParseError) as excinfo:
            adapter.normalize(raw)

        assert "idLicitacao" in str(excinfo.value)

    def test_normalize_portal_link(self, adapter):
        """Test normalize creates correct portal link."""
        raw = {
            "idLicitacao": "XYZ789",
            "DS_OBJETO": "Test",
            "lotes": [],
            "unidadeCompradora": {},
        }
        record = adapter.normalize(raw)
        assert (
            record.link_portal
            == "https://www.portaldecompraspublicas.com.br/processos/XYZ789"
        )

    def test_normalize_fallback_value_from_top_level(self, adapter):
        """Test normalize uses valorEstimado fallback when lotes are empty."""
        raw = {
            "idLicitacao": "123",
            "DS_OBJETO": "Test",
            "lotes": [],
            "valorEstimado": 5000.0,
            "unidadeCompradora": {},
        }
        record = adapter.normalize(raw)
        assert record.valor_estimado == 5000.0

    def test_normalize_uf_from_top_level(self, adapter):
        """Test normalize uses UF from top-level if unidadeCompradora.UF missing."""
        raw = {
            "idLicitacao": "123",
            "DS_OBJETO": "Test",
            "lotes": [],
            "UF": "MG",
            "unidadeCompradora": {},
        }
        record = adapter.normalize(raw)
        assert record.uf == "MG"

    def test_normalize_ano_from_data_publicacao(self, adapter):
        """Test normalize extracts ano from dataPublicacao when 'ano' missing."""
        raw = {
            "idLicitacao": "123",
            "DS_OBJETO": "Test",
            "lotes": [],
            "dataPublicacao": "15/03/2025",
            "unidadeCompradora": {},
        }
        record = adapter.normalize(raw)
        assert record.ano == "2025"

    def test_normalize_unidade_compradora_as_string(self, adapter):
        """Test normalize handles unidadeCompradora as string (edge case)."""
        raw = {
            "idLicitacao": "123",
            "DS_OBJETO": "Test",
            "lotes": [],
            "unidadeCompradora": "Some Agency Name",
        }
        record = adapter.normalize(raw)
        assert record.orgao == "Some Agency Name"
        assert record.cnpj_orgao == ""

    def test_normalize_date_parsing_dd_mm_yyyy(self, adapter):
        """Test normalize parses DD/MM/YYYY dates correctly."""
        raw = {
            "idLicitacao": "123",
            "DS_OBJETO": "Test",
            "lotes": [],
            "dataPublicacao": "20/02/2026",
            "dataAbertura": "25/02/2026 14:30:00",
            "unidadeCompradora": {},
        }
        record = adapter.normalize(raw)
        assert record.data_publicacao is not None
        assert record.data_publicacao.day == 20
        assert record.data_publicacao.month == 2
        assert record.data_publicacao.year == 2026

        assert record.data_abertura is not None
        assert record.data_abertura.day == 25

    def test_normalize_date_parsing_iso(self, adapter):
        """Test normalize parses ISO dates correctly."""
        raw = {
            "idLicitacao": "123",
            "DS_OBJETO": "Test",
            "lotes": [],
            "dataPublicacao": "2026-02-20T10:30:00Z",
            "unidadeCompradora": {},
        }
        record = adapter.normalize(raw)
        assert record.data_publicacao is not None
        assert record.data_publicacao.year == 2026
        assert record.data_publicacao.month == 2
        assert record.data_publicacao.day == 20


# ============ TestMetadata ============


class TestMetadata:
    """Test adapter metadata."""

    def test_metadata_code(self, adapter):
        """Test metadata code == 'PORTAL_COMPRAS'."""
        assert adapter.metadata.code == "PORTAL_COMPRAS"

    def test_metadata_priority(self, adapter):
        """Test metadata priority == 2."""
        assert adapter.metadata.priority == 2

    def test_metadata_name(self, adapter):
        """Test metadata has correct name."""
        assert adapter.metadata.name == "Portal de Compras Publicas"

    def test_metadata_base_url(self, adapter):
        """Test metadata base_url is correct."""
        assert (
            adapter.metadata.base_url
            == "https://apipcp.portaldecompraspublicas.com.br"
        )

    def test_metadata_rate_limit(self, adapter):
        """Test metadata rate_limit_rps == 5.0."""
        assert adapter.metadata.rate_limit_rps == 5.0

    def test_metadata_capabilities(self, adapter):
        """Test metadata includes expected capabilities."""
        from clients.base import SourceCapability

        assert SourceCapability.PAGINATION in adapter.metadata.capabilities
        assert SourceCapability.DATE_RANGE in adapter.metadata.capabilities
        assert SourceCapability.FILTER_BY_UF in adapter.metadata.capabilities


# ============ TestRequestWithRetry ============


class TestRequestWithRetry:
    """Test _request_with_retry retry logic and error handling."""

    @pytest.mark.asyncio
    async def test_request_includes_public_key_param(self, adapter):
        """Test _request_with_retry adds publicKey to params."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        await adapter._request_with_retry("GET", "/test", params={"foo": "bar"})

        # Verify publicKey was added to params
        call_args = mock_client.request.call_args
        assert call_args.kwargs["params"]["publicKey"] == "test-key-123"
        assert call_args.kwargs["params"]["foo"] == "bar"

    @pytest.mark.asyncio
    async def test_request_429_retries_with_retry_after(self, adapter):
        """Test _request_with_retry retries on 429 with Retry-After."""
        mock_client = AsyncMock()
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "2"}

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"success": True}

        mock_client.request = AsyncMock(
            side_effect=[mock_response_429, mock_response_200]
        )
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await adapter._request_with_retry("GET", "/test")

        assert result == {"success": True}
        mock_sleep.assert_called_once_with(2)

    @pytest.mark.asyncio
    async def test_request_500_retries_with_backoff(self, adapter):
        """Test _request_with_retry retries on 500 with exponential backoff."""
        mock_client = AsyncMock()
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_response_500.text = "Internal Server Error"

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"success": True}

        mock_client.request = AsyncMock(
            side_effect=[mock_response_500, mock_response_200]
        )
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await adapter._request_with_retry("GET", "/test")

        assert result == {"success": True}
        assert mock_sleep.called

    @pytest.mark.asyncio
    async def test_request_timeout_retries_then_raises(self, adapter):
        """Test _request_with_retry retries timeout then raises SourceTimeoutError."""
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout")
        )
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(SourceTimeoutError):
                await adapter._request_with_retry("GET", "/test")

        # Should retry MAX_RETRIES times
        assert mock_client.request.call_count == adapter.MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_request_204_returns_empty_list(self, adapter):
        """Test _request_with_retry returns [] on 204 No Content."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        result = await adapter._request_with_retry("GET", "/test")
        assert result == []


# ============ TestClose ============


class TestClose:
    """Test async context manager and close behavior."""

    @pytest.mark.asyncio
    async def test_close_closes_client(self, adapter):
        """Test close() closes the HTTP client."""
        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        adapter._client = mock_client

        await adapter.close()

        mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager(self, adapter):
        """Test adapter works as async context manager."""
        async with adapter as a:
            assert a is adapter

        # Should close client on exit
        if adapter._client:
            assert adapter._client.is_closed or adapter._client is None
