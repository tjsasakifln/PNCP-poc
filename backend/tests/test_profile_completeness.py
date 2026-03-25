"""Tests for STORY-260 AC18: Profile completeness endpoint.

Covers:
- GET /v1/profile/completeness with empty/partial/full profiles
- next_question follows priority order
- PUT /v1/profile/context accepts new fields (atestados, capacidade_funcionarios, faturamento_anual)
- Atestados validation
- Edge cases: all None, partial fill
- DB mock via app.dependency_overrides pattern

SYS-023: Profile context endpoints now use get_user_db (user-scoped client).
Tests override get_user_db with mock_db to maintain the same testing pattern.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from main import app
from auth import require_auth
from database import get_db, get_user_db


TEST_USER = {"id": "test-user-id", "email": "test@example.com"}


@pytest.fixture(autouse=True)
def setup_auth():
    """Override auth for all tests."""
    app.dependency_overrides[require_auth] = lambda: TEST_USER
    yield
    app.dependency_overrides.pop(require_auth, None)


@pytest.fixture
def mock_db():
    """Provide a mock DB and inject it via dependency override."""
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    # SYS-023: Profile context/completeness endpoints now use get_user_db
    app.dependency_overrides[get_user_db] = lambda: db
    yield db
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_user_db, None)


@pytest.fixture
def client():
    return TestClient(app)


def _make_db_result(context_data: dict) -> MagicMock:
    """Build a mock DB result that returns context_data from single().execute()."""
    result = MagicMock()
    result.data = {"context_data": context_data}
    mock_chain = MagicMock()
    mock_chain.single.return_value.execute.return_value = result
    return mock_chain


# ============================================================================
# GET /v1/profile/completeness
# ============================================================================

class TestProfileCompletenessEndpoint:
    """Tests for GET /v1/profile/completeness."""

    def test_empty_profile_returns_zero_percent(self, client, mock_db):
        """Empty context_data -> 0% completeness."""
        mock_chain = _make_db_result({})
        mock_db.table.return_value.select.return_value.eq.return_value = mock_chain

        response = client.get("/v1/profile/completeness")

        assert response.status_code == 200
        data = response.json()
        assert data["completeness_pct"] == 0
        assert data["filled_fields"] == 0
        assert data["is_complete"] is False

    def test_full_profile_returns_100_percent(self, client, mock_db):
        """All tracked fields present -> 100% completeness."""
        full_context = {
            "ufs_atuacao": ["SP", "RJ"],
            "porte_empresa": "ME",
            "experiencia_licitacoes": "EXPERIENTE",
            "faixa_valor_min": 50_000.0,
            "capacidade_funcionarios": 20,
            "faturamento_anual": 1_500_000.0,
            "atestados": ["iso_9001"],
        }
        mock_chain = _make_db_result(full_context)
        mock_db.table.return_value.select.return_value.eq.return_value = mock_chain

        response = client.get("/v1/profile/completeness")

        assert response.status_code == 200
        data = response.json()
        assert data["completeness_pct"] == 100
        assert data["is_complete"] is True
        assert data["missing_fields"] == []
        assert data["next_question"] is None

    def test_partial_profile_correct_percentage(self, client, mock_db):
        """Partial profile returns accurate percentage (2 of 7 fields filled)."""
        partial_context = {
            "ufs_atuacao": ["SP"],
            "porte_empresa": "EPP",
            # 5 fields missing
        }
        mock_chain = _make_db_result(partial_context)
        mock_db.table.return_value.select.return_value.eq.return_value = mock_chain

        response = client.get("/v1/profile/completeness")

        assert response.status_code == 200
        data = response.json()
        # 2 filled out of 7 -> 28.57% -> rounds to 29%
        assert data["filled_fields"] == 2
        assert data["total_fields"] == 7
        assert data["completeness_pct"] == 29

    def test_next_question_follows_priority_order(self, client, mock_db):
        """next_question is the first missing field from _QUESTION_PRIORITY."""
        # Only ufs_atuacao filled — missing: porte_empresa, experiencia_licitacoes,
        # faixa_valor_min, capacidade_funcionarios, faturamento_anual, atestados
        # Priority: porte_empresa first
        context = {"ufs_atuacao": ["SP"]}
        mock_chain = _make_db_result(context)
        mock_db.table.return_value.select.return_value.eq.return_value = mock_chain

        response = client.get("/v1/profile/completeness")

        assert response.status_code == 200
        data = response.json()
        assert data["next_question"] == "porte_empresa"

    def test_next_question_skips_filled_priority_fields(self, client, mock_db):
        """next_question skips already-filled priority fields."""
        # porte_empresa filled, experiencia_licitacoes missing -> next is experiencia_licitacoes
        context = {
            "ufs_atuacao": ["SP"],
            "porte_empresa": "ME",
        }
        mock_chain = _make_db_result(context)
        mock_db.table.return_value.select.return_value.eq.return_value = mock_chain

        response = client.get("/v1/profile/completeness")

        assert response.status_code == 200
        data = response.json()
        assert data["next_question"] == "experiencia_licitacoes"

    def test_next_question_falls_back_to_first_missing(self, client, mock_db):
        """When all priority fields filled, next_question is first missing field."""
        # Fill all priority fields, leave ufs_atuacao missing
        # But ufs_atuacao is first in _PROFILE_FIELDS list and not in _QUESTION_PRIORITY
        context = {
            "porte_empresa": "ME",
            "experiencia_licitacoes": "EXPERIENTE",
            "faixa_valor_min": 50_000.0,
            "capacidade_funcionarios": 10,
            "atestados": ["crea"],
        }
        # Missing: ufs_atuacao, faturamento_anual
        mock_chain = _make_db_result(context)
        mock_db.table.return_value.select.return_value.eq.return_value = mock_chain

        response = client.get("/v1/profile/completeness")

        assert response.status_code == 200
        data = response.json()
        # next_question should be something from the missing list
        assert data["next_question"] is not None
        assert data["next_question"] in data["missing_fields"]

    def test_missing_fields_listed_correctly(self, client, mock_db):
        """missing_fields contains only fields not yet filled."""
        context = {
            "ufs_atuacao": ["SP"],
            "porte_empresa": "ME",
        }
        mock_chain = _make_db_result(context)
        mock_db.table.return_value.select.return_value.eq.return_value = mock_chain

        response = client.get("/v1/profile/completeness")

        assert response.status_code == 200
        data = response.json()
        missing = data["missing_fields"]
        assert "ufs_atuacao" not in missing
        assert "porte_empresa" not in missing
        assert "experiencia_licitacoes" in missing
        assert "atestados" in missing

    def test_db_error_returns_empty_fallback(self, client, mock_db):
        """UX-429: DB failure returns 0% completeness (graceful fallback) instead of 500."""
        mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception(
            "DB error"
        )

        response = client.get("/v1/profile/completeness")

        assert response.status_code == 200
        data = response.json()
        assert data["completeness_pct"] == 0
        assert data["filled_fields"] == 0
        assert data["is_complete"] is False

    def test_none_context_data_treated_as_empty(self, client, mock_db):
        """Null context_data in DB is treated as empty dict -> 0%."""
        result = MagicMock()
        result.data = {"context_data": None}
        mock_chain = MagicMock()
        mock_chain.single.return_value.execute.return_value = result
        mock_db.table.return_value.select.return_value.eq.return_value = mock_chain

        response = client.get("/v1/profile/completeness")

        assert response.status_code == 200
        data = response.json()
        assert data["completeness_pct"] == 0

    def test_empty_list_field_treated_as_missing(self, client, mock_db):
        """Fields with empty list [] are counted as missing."""
        context = {"ufs_atuacao": []}  # Empty list
        mock_chain = _make_db_result(context)
        mock_db.table.return_value.select.return_value.eq.return_value = mock_chain

        response = client.get("/v1/profile/completeness")

        assert response.status_code == 200
        data = response.json()
        assert "ufs_atuacao" in data["missing_fields"]

    def test_empty_string_field_treated_as_missing(self, client, mock_db):
        """Fields with empty string '' are counted as missing."""
        context = {"porte_empresa": ""}  # Empty string
        mock_chain = _make_db_result(context)
        mock_db.table.return_value.select.return_value.eq.return_value = mock_chain

        response = client.get("/v1/profile/completeness")

        assert response.status_code == 200
        data = response.json()
        assert "porte_empresa" in data["missing_fields"]


# ============================================================================
# PUT /v1/profile/context — accepts new STORY-260 fields
# ============================================================================

class TestProfileContextPut:
    """Test PUT /v1/profile/context accepts STORY-260 expanded fields."""

    def test_accepts_atestados_field(self, client, mock_db):
        """PUT /v1/profile/context accepts atestados list."""
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        payload = {
            "ufs_atuacao": ["SP"],
            "porte_empresa": "ME",
            "experiencia_licitacoes": "INICIANTE",
            "atestados": ["iso_9001", "crea"],
        }
        response = client.put("/v1/profile/context", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True

    def test_accepts_capacidade_funcionarios_field(self, client, mock_db):
        """PUT /v1/profile/context accepts capacidade_funcionarios integer."""
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        payload = {
            "ufs_atuacao": ["SP"],
            "porte_empresa": "EPP",
            "experiencia_licitacoes": "EXPERIENTE",
            "capacidade_funcionarios": 50,
        }
        response = client.put("/v1/profile/context", json=payload)

        assert response.status_code == 200

    def test_accepts_faturamento_anual_field(self, client, mock_db):
        """PUT /v1/profile/context accepts faturamento_anual float."""
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        payload = {
            "ufs_atuacao": ["RJ"],
            "porte_empresa": "GRANDE",
            "experiencia_licitacoes": "EXPERIENTE",
            "faturamento_anual": 10_000_000.0,
        }
        response = client.put("/v1/profile/context", json=payload)

        assert response.status_code == 200

    def test_accepts_all_new_fields_together(self, client, mock_db):
        """PUT accepts atestados + capacidade_funcionarios + faturamento_anual together."""
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        payload = {
            "ufs_atuacao": ["SP", "MG"],
            "porte_empresa": "ME",
            "experiencia_licitacoes": "EXPERIENTE",
            "atestados": ["iso_9001"],
            "capacidade_funcionarios": 25,
            "faturamento_anual": 2_500_000.0,
        }
        response = client.put("/v1/profile/context", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "context_data" in data

    def test_atestados_accepts_valid_list(self, client, mock_db):
        """atestados field accepts a list of strings."""
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        payload = {
            "ufs_atuacao": ["SP"],
            "porte_empresa": "ME",
            "experiencia_licitacoes": "INICIANTE",
            "atestados": ["iso_9001", "crea_rj", "anvisa"],
        }
        response = client.put("/v1/profile/context", json=payload)

        assert response.status_code == 200

    def test_atestados_none_is_accepted(self, client, mock_db):
        """atestados=None (omitted) is accepted (optional field)."""
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        payload = {
            "ufs_atuacao": ["SP"],
            "porte_empresa": "ME",
            "experiencia_licitacoes": "INICIANTE",
            # atestados omitted
        }
        response = client.put("/v1/profile/context", json=payload)

        assert response.status_code == 200

    def test_value_range_max_must_exceed_min(self, client, mock_db):
        """faixa_valor_max must be >= faixa_valor_min (validated by schema)."""
        payload = {
            "ufs_atuacao": ["SP"],
            "porte_empresa": "ME",
            "experiencia_licitacoes": "INICIANTE",
            "faixa_valor_min": 500_000.0,
            "faixa_valor_max": 100_000.0,  # Less than min — invalid
        }
        response = client.put("/v1/profile/context", json=payload)

        assert response.status_code == 422

    def test_invalid_uf_returns_422(self, client, mock_db):
        """Invalid UF code returns 422."""
        payload = {
            "ufs_atuacao": ["XX"],  # Invalid UF
            "porte_empresa": "ME",
            "experiencia_licitacoes": "INICIANTE",
        }
        response = client.put("/v1/profile/context", json=payload)

        assert response.status_code == 422

    def test_capacidade_funcionarios_negative_rejected(self, client, mock_db):
        """Negative capacidade_funcionarios is rejected."""
        payload = {
            "ufs_atuacao": ["SP"],
            "porte_empresa": "ME",
            "experiencia_licitacoes": "INICIANTE",
            "capacidade_funcionarios": -1,
        }
        response = client.put("/v1/profile/context", json=payload)

        assert response.status_code == 422

    def test_faturamento_anual_negative_rejected(self, client, mock_db):
        """Negative faturamento_anual is rejected."""
        payload = {
            "ufs_atuacao": ["SP"],
            "porte_empresa": "ME",
            "experiencia_licitacoes": "INICIANTE",
            "faturamento_anual": -500.0,
        }
        response = client.put("/v1/profile/context", json=payload)

        assert response.status_code == 422

    def test_db_error_returns_500(self, client, mock_db):
        """DB error during save returns 500."""
        mock_db.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception(
            "DB error"
        )

        payload = {
            "ufs_atuacao": ["SP"],
            "porte_empresa": "ME",
            "experiencia_licitacoes": "INICIANTE",
        }
        response = client.put("/v1/profile/context", json=payload)

        assert response.status_code == 500
