"""Tests for POST /v1/lead-capture — COPY-COP-006 + REPO-004 (#756).

Covers:
- All 14 valid sources return 201 (old + new)
- Invalid source returns 422
- Invalid email returns 422
- mensagem > 500 chars returns 422
- modalidade_interesse invalid value returns 422
- Backward compat: legacy sources still work
- New sources stored in ``lead_captures`` table
- Legacy sources stored in ``leads`` table
- DB failure returns 201 (fail-open)
- Rate limiter integration
"""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from startup.app_factory import create_app
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client — patches supabase_client.get_supabase."""
    mock = Mock()
    mock.table.return_value = mock
    mock.upsert.return_value = mock
    mock.insert.return_value = mock
    mock.execute.return_value = Mock(data=[{"id": "test-uuid"}])
    return mock


def _post(client, payload):
    """Helper: POST to /v1/lead-capture with payload."""
    return client.post("/v1/lead-capture", json=payload)


# ---------------------------------------------------------------------------
# Valid sources — all 14 must return 201
# ---------------------------------------------------------------------------

ALL_SOURCES = [
    # Legacy (REPO-004)
    "calculadora", "cnpj", "alertas",
    "consultoria", "radar", "report", "intel", "diagnostico",
    # New (COPY-COP-006)
    "lead_magnet_1", "lead_magnet_2", "lead_magnet_3",
    "newsletter", "exit_intent", "seo_banner",
]


class TestAllSourcesAccepted:
    @pytest.mark.parametrize("source", ALL_SOURCES)
    def test_valid_source_returns_201(self, client, mock_supabase, source):
        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {"email": "test@example.com", "source": source})
        assert resp.status_code == 201, f"Failed for source={source}: {resp.text}"
        assert resp.json()["success"] is True
        assert resp.json().get("receipt_id")


# ---------------------------------------------------------------------------
# Validation — bad source → 422
# ---------------------------------------------------------------------------

class TestSourceValidation:
    def test_invalid_source_returns_422(self, client):
        with patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {"email": "test@example.com", "source": "unknown_source"})
        assert resp.status_code == 422

    def test_empty_source_returns_422(self, client):
        with patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {"email": "test@example.com", "source": ""})
        assert resp.status_code == 422

    def test_missing_source_returns_422(self, client):
        with patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {"email": "test@example.com"})
        assert resp.status_code == 422

    def test_missing_email_returns_422(self, client):
        with patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {"source": "calculadora"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Email validation (now uses Pydantic field_validator → 422)
# ---------------------------------------------------------------------------

class TestEmailValidation:
    def test_invalid_email_returns_422(self, client):
        with patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {"email": "not-an-email", "source": "calculadora"})
        assert resp.status_code == 422

    def test_empty_email_returns_422(self, client):
        with patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {"email": "", "source": "calculadora"})
        assert resp.status_code == 422

    def test_email_without_at_returns_422(self, client):
        with patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {"email": "testexample.com", "source": "calculadora"})
        assert resp.status_code == 422

    def test_email_without_domain_returns_422(self, client):
        with patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {"email": "test@", "source": "calculadora"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# mensagem max_length = 500
# ---------------------------------------------------------------------------

class TestMensagemValidation:
    def test_mensagem_at_max_length_accepted(self, client, mock_supabase):
        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {
                "email": "test@example.com",
                "source": "diagnostico",
                "mensagem": "a" * 500,
            })
        assert resp.status_code == 201

    def test_mensagem_over_max_length_returns_422(self, client):
        with patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {
                "email": "test@example.com",
                "source": "diagnostico",
                "mensagem": "a" * 501,
            })
        assert resp.status_code == 422

    def test_mensagem_none_accepted(self, client, mock_supabase):
        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {
                "email": "test@example.com",
                "source": "diagnostico",
                "mensagem": None,
            })
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# modalidade_interesse validation
# ---------------------------------------------------------------------------

class TestModalidadeInteresse:
    @pytest.mark.parametrize("value", ["radar", "report", "intel", "nao_sei"])
    def test_valid_modalidade_accepted(self, client, mock_supabase, value):
        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {
                "email": "test@example.com",
                "source": "diagnostico",
                "modalidade_interesse": value,
            })
        assert resp.status_code == 201

    def test_invalid_modalidade_returns_422(self, client):
        with patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {
                "email": "test@example.com",
                "source": "diagnostico",
                "modalidade_interesse": "outro",
            })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Backward compatibility — legacy sources + legacy-only fields
# ---------------------------------------------------------------------------

class TestBackwardCompat:
    def test_calculadora_legacy_payload(self, client, mock_supabase):
        """Original calculadora payload still works unchanged."""
        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {
                "email": "legado@example.com",
                "source": "calculadora",
                "setor": "saude",
                "uf": "SP",
                "captured_at": "2026-05-07T12:00:00Z",
            })
        assert resp.status_code == 201

    def test_cnpj_legacy_payload(self, client, mock_supabase):
        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {
                "email": "legado@example.com",
                "source": "cnpj",
                "setor": "construcao",
            })
        assert resp.status_code == 201

    def test_alertas_legacy_payload(self, client, mock_supabase):
        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {
                "email": "legado@example.com",
                "source": "alertas",
                "uf": "RJ",
            })
        assert resp.status_code == 201

    def test_minimal_payload_only_email_and_source(self, client, mock_supabase):
        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {"email": "min@example.com", "source": "radar"})
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# New optional fields accepted (REPO-004)
# ---------------------------------------------------------------------------

class TestNewOptionalFields:
    def test_full_diagnostico_payload_accepted(self, client, mock_supabase):
        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {
                "email": "empresa@example.com",
                "source": "diagnostico",
                "nome": "João Silva",
                "empresa": "Acme Ltda",
                "cnpj": "12.345.678/0001-90",
                "telefone": "11999990000",
                "modalidade_interesse": "report",
                "mensagem": "Quero saber mais sobre relatórios de inteligência.",
                "utm_source": "google",
                "utm_campaign": "b2g-q2-2026",
                "referer_path": "/observatorio/licitacoes-ti",
                "setor": "tecnologia",
                "uf": "SP",
            })
        assert resp.status_code == 201

    def test_utm_fields_only(self, client, mock_supabase):
        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {
                "email": "utm@example.com",
                "source": "consultoria",
                "utm_source": "linkedin",
                "utm_campaign": "founders",
            })
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# DB failure — fail-open behavior preserved (still returns 201)
# ---------------------------------------------------------------------------

class TestFailOpen:
    def test_db_failure_still_returns_success(self, client):
        """Route fails-open: DB errors logged but 201 returned."""
        mock_sb = Mock()
        mock_sb.table.side_effect = Exception("DB connection failed")
        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {"email": "test@example.com", "source": "calculadora"})
        assert resp.status_code == 201
        assert resp.json()["success"] is True
        assert resp.json().get("receipt_id")


class TestOutboxDurability:
    def test_persist_failure_returns_503(self, client, mock_supabase, tmp_path, monkeypatch):
        blocked = tmp_path / "not-a-dir"
        blocked.write_text("file")
        monkeypatch.setenv("LEAD_OUTBOX_PATH", str(blocked / "outbox.jsonl"))
        from leads.outbox import reset_outbox_state

        reset_outbox_state()
        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {"email": "outbox@example.com", "source": "consultoria"})
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# New sources route to lead_captures table
# ---------------------------------------------------------------------------

class TestNewSourcesRouting:
    def test_new_source_inserts_into_lead_captures(self, client):
        """New source should call insert on lead_captures table, not upsert on leads."""
        lead_captures_calls = []
        leads_calls = []

        def fake_table(name):
            mock = Mock()
            if name == "lead_captures":
                mock.insert.return_value = mock
                mock.insert.side_effect = lambda r: (
                    lead_captures_calls.append(r) or mock
                )
                mock.execute.return_value = Mock(data=[{"id": "lc-uuid"}])
            elif name == "leads":
                mock.upsert.return_value = mock
                mock.upsert.side_effect = lambda r, on_conflict=None: (
                    leads_calls.append(r) or mock
                )
                mock.execute.return_value = Mock(data=[{"id": "lead-uuid"}])
            return mock

        sb = Mock()
        sb.table.side_effect = fake_table

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {
                "email": "novo@exemplo.com",
                "source": "lead_magnet_1",
                "sector": "informatica",
                "origin_url": "https://smartlic.tech/guia",
            })

        assert resp.status_code == 201
        # Must have called lead_captures.insert
        assert len(lead_captures_calls) == 1
        assert lead_captures_calls[0]["email"] == "novo@exemplo.com"
        assert lead_captures_calls[0]["source"] == "lead_magnet_1"
        assert lead_captures_calls[0]["sector"] == "informatica"
        assert lead_captures_calls[0]["origin_url"] == "https://smartlic.tech/guia"
        # Must NOT have called leads.upsert
        assert len(leads_calls) == 0

    def test_legacy_source_does_not_call_lead_captures(self, client):
        """Legacy source should NOT call lead_captures table."""
        lead_captures_calls = []
        leads_calls = []

        def fake_table(name):
            mock = Mock()
            if name == "lead_captures":
                mock.insert.return_value = mock
                mock.insert.side_effect = lambda r: (
                    lead_captures_calls.append(r) or mock
                )
                mock.execute.return_value = Mock(data=[{"id": "lc-uuid"}])
            elif name == "leads":
                mock.upsert.return_value = mock
                mock.upsert.side_effect = lambda r, on_conflict=None: (
                    leads_calls.append(r) or mock
                )
                mock.execute.return_value = Mock(data=[{"id": "lead-uuid"}])
            return mock

        sb = Mock()
        sb.table.side_effect = fake_table

        with patch("supabase_client.get_supabase", return_value=sb), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {
                "email": "legado@exemplo.com",
                "source": "calculadora",
            })

        assert resp.status_code == 201
        assert len(leads_calls) == 1
        assert len(lead_captures_calls) == 0


# ---------------------------------------------------------------------------
# origin_url and metadata fields for new sources
# ---------------------------------------------------------------------------

class TestNewSourceFields:
    def test_origin_url_acceptance(self, client, mock_supabase):
        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {
                "email": "test@example.com",
                "source": "newsletter",
                "origin_url": "https://smartlic.tech/licitacoes/saude",
            })
        assert resp.status_code == 201

    def test_sector_in_new_source(self, client, mock_supabase):
        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("routes.lead_capture.require_rate_limit", return_value=lambda: None):
            resp = _post(client, {
                "email": "test@example.com",
                "source": "seo_banner",
                "sector": "engenharia",
                "origin_url": "https://smartlic.tech/licitacoes/engenharia",
            })
        assert resp.status_code == 201
