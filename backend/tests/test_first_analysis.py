"""Tests for first analysis endpoint (GTM-004 AC1-4)."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from main import app
from auth import require_auth


def override_require_auth(user_id: str = "test-user-123"):
    """Create a dependency override for require_auth."""
    async def _override():
        return {"id": user_id, "email": "test@example.com"}
    return _override


@pytest.fixture(autouse=True)
def setup_auth():
    """Setup auth override for all tests in this module."""
    app.dependency_overrides[require_auth] = override_require_auth()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_tracker():
    """Mock progress tracker."""
    tracker = MagicMock()
    tracker.emit = AsyncMock()
    tracker.emit_complete = AsyncMock()
    tracker.emit_error = AsyncMock()
    return tracker


@pytest.fixture
def mock_pipeline(mock_tracker):
    """Mock create_tracker and _run_first_analysis_pipeline."""
    with patch("routes.onboarding.create_tracker", new_callable=AsyncMock) as mock_ct, \
         patch("routes.onboarding._run_first_analysis_pipeline", new_callable=AsyncMock) as mock_run:
        mock_ct.return_value = mock_tracker
        yield mock_ct, mock_run


class TestFirstAnalysis:
    """Test POST /v1/first-analysis endpoint."""

    @pytest.mark.asyncio
    async def test_ac1_cnae_maps_to_sector(self, mock_pipeline):
        """AC1: CNAE code maps to correct sector."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/first-analysis",
                json={
                    "cnae": "4781-4/00",
                    "objetivo_principal": "Uniformes escolares",
                    "ufs": ["SP"],
                    "faixa_valor_min": 50000,
                    "faixa_valor_max": 500000,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["setor_id"] == "vestuario"
            assert data["status"] == "in_progress"
            assert "search_id" in data

    @pytest.mark.asyncio
    async def test_ac1_facilities_cnae(self, mock_pipeline):
        """AC1: Facilities CNAE maps correctly."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/first-analysis",
                json={
                    "cnae": "8121-4/00",
                    "objetivo_principal": "Serviços de limpeza",
                    "ufs": ["RJ"],
                },
            )
            assert response.status_code == 200
            assert response.json()["setor_id"] == "facilities"

    @pytest.mark.asyncio
    async def test_ac2_derives_search_params(self, mock_pipeline):
        """AC2: Endpoint derives search params from profile."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/first-analysis",
                json={
                    "cnae": "4781",
                    "objetivo_principal": "Encontrar oportunidades",
                    "ufs": ["SP", "RJ", "MG"],
                    "faixa_valor_min": 100000,
                    "faixa_valor_max": 500000,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "in_progress"
            assert "SP" in data["message"]

    @pytest.mark.asyncio
    async def test_ac3_returns_search_id(self, mock_pipeline):
        """AC3: Returns search_id for SSE tracking."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/first-analysis",
                json={
                    "cnae": "4781",
                    "objetivo_principal": "Test",
                    "ufs": ["SP"],
                },
            )
            data = response.json()
            assert "search_id" in data
            # search_id should be UUID format
            assert len(data["search_id"]) == 36
            assert data["search_id"].count("-") == 4

    @pytest.mark.asyncio
    async def test_ac5_schema_backward_compatible(self):
        """AC5: New PerfilContexto fields are optional (backward compat)."""
        from schemas import PerfilContexto

        # Old format (no new fields) still works
        old_profile = PerfilContexto(
            ufs_atuacao=["SP"],
            porte_empresa="EPP",
            experiencia_licitacoes="INICIANTE",
        )
        assert old_profile.cnae is None
        assert old_profile.objetivo_principal is None
        assert old_profile.ticket_medio_desejado is None

        # New format with new fields
        new_profile = PerfilContexto(
            ufs_atuacao=["SP", "RJ"],
            porte_empresa="MEDIO",
            experiencia_licitacoes="EXPERIENTE",
            cnae="4781-4/00",
            objetivo_principal="Uniformes escolares acima de R$ 100k",
            ticket_medio_desejado=200000,
        )
        assert new_profile.cnae == "4781-4/00"
        assert new_profile.objetivo_principal == "Uniformes escolares acima de R$ 100k"
        assert new_profile.ticket_medio_desejado == 200000

    @pytest.mark.asyncio
    async def test_invalid_ufs_rejected(self, mock_pipeline):
        """Invalid UF codes are rejected."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/first-analysis",
                json={
                    "cnae": "4781",
                    "objetivo_principal": "Test",
                    "ufs": ["XX"],  # Invalid UF
                },
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_message_includes_ufs(self, mock_pipeline):
        """Response message includes UF list."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/first-analysis",
                json={
                    "cnae": "4781",
                    "objetivo_principal": "Test",
                    "ufs": ["SP", "RJ"],
                },
            )
            data = response.json()
            assert "SP" in data["message"]
            assert "RJ" in data["message"]
