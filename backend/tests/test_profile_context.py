"""Tests for profile context endpoints (STORY-247 AC5)."""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_user():
    return {"id": "550e8400-e29b-41d4-a716-446655440000", "email": "test@example.com"}


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


@pytest.fixture
def client(mock_user, mock_db):
    from main import app
    from auth import require_auth
    from database import get_db

    app.dependency_overrides[require_auth] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


class TestPerfilContextoSchema:
    """AC1: Test PerfilContexto Pydantic schema validation."""

    def test_valid_full_context(self):
        from schemas import PerfilContexto

        ctx = PerfilContexto(
            ufs_atuacao=["SP", "RJ", "MG"],
            porte_empresa="ME",
            experiencia_licitacoes="PRIMEIRA_VEZ",
            faixa_valor_min=50000,
            faixa_valor_max=500000,
            modalidades_interesse=[4, 6],
            palavras_chave=["uniforme", "jaleco"],
        )
        assert ctx.ufs_atuacao == ["SP", "RJ", "MG"]
        assert ctx.porte_empresa.value == "ME"
        assert ctx.experiencia_licitacoes.value == "PRIMEIRA_VEZ"
        assert ctx.faixa_valor_min == 50000
        assert ctx.faixa_valor_max == 500000

    def test_valid_minimal_context(self):
        from schemas import PerfilContexto

        ctx = PerfilContexto(
            ufs_atuacao=["SP"],
            porte_empresa="GRANDE",
            experiencia_licitacoes="EXPERIENTE",
        )
        assert ctx.faixa_valor_min is None
        assert ctx.faixa_valor_max is None
        assert ctx.modalidades_interesse is None
        assert ctx.palavras_chave is None

    def test_invalid_empty_ufs(self):
        from schemas import PerfilContexto

        with pytest.raises(Exception):
            PerfilContexto(
                ufs_atuacao=[],
                porte_empresa="ME",
                experiencia_licitacoes="INICIANTE",
            )

    def test_invalid_uf_code(self):
        from schemas import PerfilContexto

        with pytest.raises(Exception) as exc:
            PerfilContexto(
                ufs_atuacao=["XX"],
                porte_empresa="ME",
                experiencia_licitacoes="INICIANTE",
            )
        assert "inválidas" in str(exc.value).lower() or "invalid" in str(exc.value).lower()

    def test_invalid_value_range(self):
        from schemas import PerfilContexto

        with pytest.raises(Exception) as exc:
            PerfilContexto(
                ufs_atuacao=["SP"],
                porte_empresa="EPP",
                experiencia_licitacoes="INICIANTE",
                faixa_valor_min=500000,
                faixa_valor_max=50000,
            )
        assert "faixa_valor_max" in str(exc.value)

    def test_invalid_porte(self):
        from schemas import PerfilContexto

        with pytest.raises(Exception):
            PerfilContexto(
                ufs_atuacao=["SP"],
                porte_empresa="INVALIDO",
                experiencia_licitacoes="INICIANTE",
            )

    def test_invalid_experiencia(self):
        from schemas import PerfilContexto

        with pytest.raises(Exception):
            PerfilContexto(
                ufs_atuacao=["SP"],
                porte_empresa="ME",
                experiencia_licitacoes="INVALIDO",
            )

    def test_ufs_normalized_to_uppercase(self):
        from schemas import PerfilContexto

        ctx = PerfilContexto(
            ufs_atuacao=["sp", "rj"],
            porte_empresa="ME",
            experiencia_licitacoes="PRIMEIRA_VEZ",
        )
        assert ctx.ufs_atuacao == ["SP", "RJ"]

    def test_keywords_stripped(self):
        from schemas import PerfilContexto

        ctx = PerfilContexto(
            ufs_atuacao=["SP"],
            porte_empresa="ME",
            experiencia_licitacoes="PRIMEIRA_VEZ",
            palavras_chave=["  uniforme  ", "jaleco", "  "],
        )
        assert ctx.palavras_chave == ["uniforme", "jaleco"]

    def test_too_many_keywords(self):
        from schemas import PerfilContexto

        with pytest.raises(Exception):
            PerfilContexto(
                ufs_atuacao=["SP"],
                porte_empresa="ME",
                experiencia_licitacoes="PRIMEIRA_VEZ",
                palavras_chave=[f"keyword_{i}" for i in range(25)],
            )


class TestSaveProfileContext:
    """AC2: Test PUT /v1/profile/context endpoint."""

    def test_save_context_success(self, client, mock_db):
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        response = client.put("/v1/profile/context", json={
            "ufs_atuacao": ["SP", "RJ"],
            "porte_empresa": "ME",
            "experiencia_licitacoes": "PRIMEIRA_VEZ",
            "faixa_valor_min": 50000,
            "faixa_valor_max": 500000,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True
        assert data["context_data"]["porte_empresa"] == "ME"
        assert data["context_data"]["ufs_atuacao"] == ["SP", "RJ"]

    def test_save_context_minimal(self, client, mock_db):
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        response = client.put("/v1/profile/context", json={
            "ufs_atuacao": ["MG"],
            "porte_empresa": "GRANDE",
            "experiencia_licitacoes": "EXPERIENTE",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True
        assert "faixa_valor_min" not in data["context_data"]

    def test_save_context_invalid_payload(self, client):
        response = client.put("/v1/profile/context", json={
            "porte_empresa": "ME",
        })
        assert response.status_code == 422

    def test_save_context_db_error(self, client, mock_db):
        mock_db.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("DB error")

        response = client.put("/v1/profile/context", json={
            "ufs_atuacao": ["SP"],
            "porte_empresa": "ME",
            "experiencia_licitacoes": "INICIANTE",
        })

        assert response.status_code == 500


class TestGetProfileContext:
    """AC3: Test GET /v1/profile/context endpoint."""

    def test_get_context_with_data(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"context_data": {"porte_empresa": "ME", "ufs_atuacao": ["SP"]}}
        )

        response = client.get("/v1/profile/context")
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True
        assert data["context_data"]["porte_empresa"] == "ME"

    def test_get_context_empty(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"context_data": {}}
        )

        response = client.get("/v1/profile/context")
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is False
        assert data["context_data"] == {}

    def test_get_context_null(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"context_data": None}
        )

        response = client.get("/v1/profile/context")
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is False

    def test_get_context_db_error(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("DB error")

        response = client.get("/v1/profile/context")
        assert response.status_code == 500
