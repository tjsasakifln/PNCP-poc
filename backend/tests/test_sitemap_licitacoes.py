"""Tests for GET /v1/sitemap/licitacoes-indexable — SEO-471.

Cobre a lógica de union bids + contracts, threshold env vars,
deduplicação, cache, schema backward-compatibility e logs.
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_cache():
    """Limpa cache in-memory antes e depois de cada teste."""
    import routes.sitemap_licitacoes as mod
    mod._cache = None
    yield
    mod._cache = None


@pytest.fixture
def client():
    from startup.app_factory import create_app
    app = create_app()
    return TestClient(app)


@pytest.fixture
def client_with_admin(client):
    """Client com override de admin auth."""
    from startup.app_factory import create_app
    from admin import require_admin

    app = create_app()
    app.dependency_overrides[require_admin] = lambda: {"sub": "admin-user"}
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bids_combos(*pairs):
    """Cria lista de combos [{setor, uf}] a partir de pares (setor, uf)."""
    return [{"setor": s, "uf": u} for s, u in pairs]


def _make_rpc_mock(count_by_uf: dict[str, int]):
    """Monta mock de supabase.rpc() que retorna count baseado no UF do argumento."""

    def _execute(setor_id=None, keywords=None, uf=None, _params=None):
        # _params é o dict passado para rpc()
        pass

    class _RpcChain:
        def __init__(self, fn_name, params):
            self._uf = (params or {}).get("p_uf", "XX")

        def execute(self):
            m = MagicMock()
            m.data = count_by_uf.get(self._uf.upper(), 0)
            return m

    mock_sb = MagicMock()
    mock_sb.rpc.side_effect = lambda fn, params: _RpcChain(fn, params)
    return mock_sb


# ---------------------------------------------------------------------------
# AC1 — Union bids OR contracts
# ---------------------------------------------------------------------------


class TestUnionBidsContracts:
    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    @patch("routes.sitemap_licitacoes._compute_contracts_combos", new_callable=AsyncMock)
    def test_returns_bids_combos_only_when_no_contracts(
        self, mock_contracts, mock_bids, client
    ):
        """Quando contracts retorna vazio, apenas bids são retornados."""
        mock_bids.return_value = _make_bids_combos(("saude", "sp"), ("saude", "rj"))
        mock_contracts.return_value = []

        resp = client.get("/v1/sitemap/licitacoes-indexable")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert {"setor": "saude", "uf": "sp"} in data["combos"]
        assert {"setor": "saude", "uf": "rj"} in data["combos"]

    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    @patch("routes.sitemap_licitacoes._compute_contracts_combos", new_callable=AsyncMock)
    def test_contracts_combos_added_when_bids_empty(
        self, mock_contracts, mock_bids, client
    ):
        """Contratos são incluídos mesmo quando bids está vazio."""
        mock_bids.return_value = []
        mock_contracts.return_value = _make_bids_combos(("limpeza", "am"), ("limpeza", "pa"))

        resp = client.get("/v1/sitemap/licitacoes-indexable")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert {"setor": "limpeza", "uf": "am"} in data["combos"]

    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    @patch("routes.sitemap_licitacoes._compute_contracts_combos", new_callable=AsyncMock)
    def test_union_deduplication(self, mock_contracts, mock_bids, client):
        """Combo presente em bids E contracts aparece apenas 1x no resultado."""
        mock_bids.return_value = _make_bids_combos(("ti", "sp"), ("ti", "mg"))
        mock_contracts.return_value = _make_bids_combos(("ti", "sp"), ("ti", "ba"))

        resp = client.get("/v1/sitemap/licitacoes-indexable")
        data = resp.json()
        # "ti-sp" dedupado; "ti-mg" de bids; "ti-ba" de contracts
        assert data["total"] == 3
        combos_tuples = {(c["setor"], c["uf"]) for c in data["combos"]}
        assert ("ti", "sp") in combos_tuples
        assert ("ti", "mg") in combos_tuples
        assert ("ti", "ba") in combos_tuples

    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    @patch("routes.sitemap_licitacoes._compute_contracts_combos", new_callable=AsyncMock)
    def test_contracts_dont_add_duplicates_over_bids(self, mock_contracts, mock_bids, client):
        """Contracts não adiciona combo que já existe em bids."""
        mock_bids.return_value = _make_bids_combos(("educacao", "go"), ("educacao", "sp"))
        # Contracts retorna 1 novo (am) + 1 duplicado de bids (go)
        mock_contracts.return_value = _make_bids_combos(("educacao", "go"), ("educacao", "am"))

        resp = client.get("/v1/sitemap/licitacoes-indexable")
        data = resp.json()
        # Total deve ser 3: go (bids), sp (bids), am (contracts)
        assert data["total"] == 3
        uf_set = {c["uf"] for c in data["combos"]}
        assert uf_set == {"go", "sp", "am"}

        # Verificar ausência de duplicatas no response
        seen = set()
        for c in data["combos"]:
            key = (c["setor"], c["uf"])
            assert key not in seen, f"Combo duplicado encontrado: {key}"
            seen.add(key)


# ---------------------------------------------------------------------------
# AC2/AC3 — RPC count_contracts_by_setor_uf
# ---------------------------------------------------------------------------


class TestContractsRpc:
    @patch("supabase_client.get_supabase")
    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    def test_rpc_called_with_keywords_and_uf(self, mock_bids, mock_get_sb, client):
        """RPC é chamada com p_keywords e p_uf para cada UF."""
        mock_bids.return_value = []

        # Mock supabase: retorna count=5 apenas para AM
        mock_sb = _make_rpc_mock({"AM": 5})
        mock_get_sb.return_value = mock_sb

        with patch.dict("os.environ", {"MIN_CONTRACTS_FOR_INDEX": "1"}):
            resp = client.get("/v1/sitemap/licitacoes-indexable")
        assert resp.status_code == 200

        # Verifica que rpc() foi chamado com nome correto
        assert mock_sb.rpc.called
        call_args = mock_sb.rpc.call_args_list[0]
        assert call_args[0][0] == "count_contracts_by_setor_uf"
        params = call_args[0][1]
        assert "p_keywords" in params
        assert "p_uf" in params
        assert isinstance(params["p_keywords"], list)

    @patch("supabase_client.get_supabase")
    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    def test_contracts_below_threshold_excluded(self, mock_bids, mock_get_sb, client):
        """Contratos com count < threshold não são incluídos."""
        mock_bids.return_value = []
        # Retorna count=0 para todas as UFs
        mock_sb = _make_rpc_mock({})
        mock_get_sb.return_value = mock_sb

        with patch.dict("os.environ", {"MIN_CONTRACTS_FOR_INDEX": "1"}):
            resp = client.get("/v1/sitemap/licitacoes-indexable")
        data = resp.json()
        assert data["total"] == 0
        assert data["combos"] == []

    @patch("supabase_client.get_supabase")
    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    def test_contracts_rpc_failure_graceful(self, mock_bids, mock_get_sb, client):
        """Falha no supabase client não causa 500 — retorna apenas bids."""
        mock_bids.return_value = _make_bids_combos(("saude", "sp"))
        mock_get_sb.side_effect = Exception("conexão falhou")

        resp = client.get("/v1/sitemap/licitacoes-indexable")
        assert resp.status_code == 200
        data = resp.json()
        # Retorna apenas bids; contracts falhou graciosamente
        assert data["total"] == 1
        assert {"setor": "saude", "uf": "sp"} in data["combos"]


# ---------------------------------------------------------------------------
# AC5 — MIN_CONTRACTS_FOR_INDEX env var
# ---------------------------------------------------------------------------


class TestContractsThreshold:
    @patch("supabase_client.get_supabase")
    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    def test_threshold_1_includes_single_contract(self, mock_bids, mock_get_sb, client):
        """Threshold=1 inclui UFs com ao menos 1 contrato."""
        mock_bids.return_value = []
        mock_sb = _make_rpc_mock({"SP": 1, "RJ": 0, "MG": 3})
        mock_get_sb.return_value = mock_sb

        with patch.dict("os.environ", {"MIN_CONTRACTS_FOR_INDEX": "1"}):
            resp = client.get("/v1/sitemap/licitacoes-indexable")
        data = resp.json()
        uf_set = {c["uf"] for c in data["combos"]}
        assert "sp" in uf_set
        assert "mg" in uf_set
        assert "rj" not in uf_set

    @patch("supabase_client.get_supabase")
    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    def test_threshold_2_excludes_single_contract(self, mock_bids, mock_get_sb, client):
        """Threshold=2 exclui UFs com apenas 1 contrato."""
        mock_bids.return_value = []
        mock_sb = _make_rpc_mock({"SP": 1, "MG": 2})
        mock_get_sb.return_value = mock_sb

        with patch.dict("os.environ", {"MIN_CONTRACTS_FOR_INDEX": "2"}):
            resp = client.get("/v1/sitemap/licitacoes-indexable")
        data = resp.json()
        uf_set = {c["uf"] for c in data["combos"]}
        assert "mg" in uf_set
        assert "sp" not in uf_set


# ---------------------------------------------------------------------------
# AC7 — Cache 24h e admin refresh
# ---------------------------------------------------------------------------


class TestCache:
    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    @patch("routes.sitemap_licitacoes._compute_contracts_combos", new_callable=AsyncMock)
    def test_cache_serves_second_request(self, mock_contracts, mock_bids, client):
        """Segunda requisição usa cache — _compute_indexable_combos chamado 1x."""
        mock_bids.return_value = _make_bids_combos(("saude", "sp"))
        mock_contracts.return_value = []

        resp1 = client.get("/v1/sitemap/licitacoes-indexable")
        resp2 = client.get("/v1/sitemap/licitacoes-indexable")

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json() == resp2.json()
        # Cada função de compute chamada apenas 1x (cache na segunda request)
        assert mock_bids.call_count == 1
        assert mock_contracts.call_count == 1

    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    @patch("routes.sitemap_licitacoes._compute_contracts_combos", new_callable=AsyncMock)
    def test_admin_refresh_clears_cache_and_recomputes(
        self, mock_contracts, mock_bids, client_with_admin
    ):
        """POST /admin/sitemap-cache/refresh invalida cache e recomputa."""
        mock_bids.return_value = _make_bids_combos(("saude", "sp"))
        mock_contracts.return_value = []

        # Primeira request popula cache
        client_with_admin.get("/v1/sitemap/licitacoes-indexable")
        assert mock_bids.call_count == 1

        # Admin refresh deve recomputar
        mock_bids.return_value = _make_bids_combos(("saude", "sp"), ("saude", "rj"))
        resp = client_with_admin.post("/v1/admin/sitemap-cache/refresh")
        assert resp.status_code == 200
        assert resp.json()["status"] == "refreshed"
        assert mock_bids.call_count == 2

        # Próxima GET deve servir resultado atualizado do cache
        resp_get = client_with_admin.get("/v1/sitemap/licitacoes-indexable")
        assert resp_get.json()["total"] == 2
        assert mock_bids.call_count == 2  # ainda 2 — cache válido


# ---------------------------------------------------------------------------
# AC8 — Schema backward-compatibility
# ---------------------------------------------------------------------------


class TestSchema:
    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    @patch("routes.sitemap_licitacoes._compute_contracts_combos", new_callable=AsyncMock)
    def test_backward_compatible_schema(self, mock_contracts, mock_bids, client):
        """Response mantém campos combos, total, threshold, updated_at."""
        mock_bids.return_value = _make_bids_combos(("ti", "sp"))
        mock_contracts.return_value = []

        resp = client.get("/v1/sitemap/licitacoes-indexable")
        data = resp.json()
        assert "combos" in data
        assert "total" in data
        assert "threshold" in data
        assert "updated_at" in data

        assert isinstance(data["combos"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["threshold"], int)
        assert isinstance(data["updated_at"], str)

    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    @patch("routes.sitemap_licitacoes._compute_contracts_combos", new_callable=AsyncMock)
    def test_threshold_field_reflects_bids_threshold(self, mock_contracts, mock_bids, client):
        """Campo 'threshold' reflete MIN_ACTIVE_BIDS_FOR_INDEX."""
        mock_bids.return_value = []
        mock_contracts.return_value = []

        with patch.dict("os.environ", {"MIN_ACTIVE_BIDS_FOR_INDEX": "3"}):
            resp = client.get("/v1/sitemap/licitacoes-indexable")
        data = resp.json()
        assert data["threshold"] == 3

    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    @patch("routes.sitemap_licitacoes._compute_contracts_combos", new_callable=AsyncMock)
    def test_combo_fields(self, mock_contracts, mock_bids, client):
        """Cada combo tem exatamente os campos 'setor' e 'uf'."""
        mock_bids.return_value = _make_bids_combos(("construcao", "go"))
        mock_contracts.return_value = []

        resp = client.get("/v1/sitemap/licitacoes-indexable")
        data = resp.json()
        assert len(data["combos"]) == 1
        combo = data["combos"][0]
        assert set(combo.keys()) == {"setor", "uf"}
        assert combo["setor"] == "construcao"
        assert combo["uf"] == "go"


# ---------------------------------------------------------------------------
# AC9 — Log INFO com contagem de bids vs contratos
# ---------------------------------------------------------------------------


class TestLogging:
    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    @patch("routes.sitemap_licitacoes._compute_contracts_combos", new_callable=AsyncMock)
    def test_log_reports_bids_and_contracts_counts(
        self, mock_contracts, mock_bids, client, caplog
    ):
        """Log INFO reporta quantos combos vieram de bids e quantos de contratos."""
        mock_bids.return_value = _make_bids_combos(("saude", "sp"), ("saude", "rj"))
        mock_contracts.return_value = _make_bids_combos(
            ("saude", "sp"),  # duplicado — não deve ser contado como "exclusivo"
            ("saude", "am"),  # novo — deve aparecer no log como 1 de contratos
        )

        with caplog.at_level(logging.INFO, logger="routes.sitemap_licitacoes"):
            client.get("/v1/sitemap/licitacoes-indexable")

        # Deve haver log com "2 combos de bids" e "1 combos exclusivos de contratos"
        log_messages = "\n".join(caplog.messages)
        assert "2" in log_messages  # bids count
        assert "1" in log_messages  # contracts_only count
        assert "3" in log_messages  # total

    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    @patch("routes.sitemap_licitacoes._compute_contracts_combos", new_callable=AsyncMock)
    def test_log_zero_contracts_when_all_deduplicated(
        self, mock_contracts, mock_bids, client, caplog
    ):
        """Log reporta 0 contratos exclusivos quando todos são duplicatas de bids."""
        mock_bids.return_value = _make_bids_combos(("ti", "sp"))
        mock_contracts.return_value = _make_bids_combos(("ti", "sp"))

        with caplog.at_level(logging.INFO, logger="routes.sitemap_licitacoes"):
            client.get("/v1/sitemap/licitacoes-indexable")

        log_messages = "\n".join(caplog.messages)
        # "0 combos exclusivos de contratos"
        assert "0" in log_messages


# ---------------------------------------------------------------------------
# AC4 — Paralelismo: asyncio.gather para 15 setores
# ---------------------------------------------------------------------------


class TestParallelism:
    @patch("supabase_client.get_supabase")
    @patch("routes.sitemap_licitacoes._compute_bids_combos", new_callable=AsyncMock)
    def test_contracts_gather_called_per_sector(self, mock_bids, mock_get_sb, client):
        """RPC é chamada para múltiplos setores (gather paralelo)."""
        mock_bids.return_value = []
        # Retorna count=1 apenas para SP
        mock_sb = _make_rpc_mock({"SP": 1})
        mock_get_sb.return_value = mock_sb

        with patch.dict("os.environ", {"MIN_CONTRACTS_FOR_INDEX": "1"}):
            resp = client.get("/v1/sitemap/licitacoes-indexable")
        assert resp.status_code == 200

        # rpc() deve ter sido chamado ao menos 27 vezes (27 UFs × N setores)
        assert mock_sb.rpc.call_count >= 27
