"""CRIT-007 AC1-AC2: Shared fixtures for integration tests.

Provides:
- FastAPI TestClient with mocked external dependencies
- Mock Supabase client (configurable failure modes)
- Mock PNCP API responses
- Mock Redis pool
- Authenticated user fixture
- Sample licitacao data

All integration tests use @pytest.mark.integration marker (AC5).
"""

import asyncio
import os
import sys
import time
import warnings
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from types import SimpleNamespace

# Suppress warnings that fire from async mocks used with create_task() in sync TestClient
warnings.filterwarnings("ignore", message="coroutine.*was never awaited", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", message="datetime.datetime.utcnow", category=DeprecationWarning)

# Ensure backend is on sys.path
backend_dir = os.path.join(os.path.dirname(__file__), "..", "..")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Pre-set critical env vars before any module imports to prevent real API calls
os.environ["ENABLE_MULTI_SOURCE"] = "false"


# ---------------------------------------------------------------------------
# Environment setup (must happen before importing backend modules)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def integration_env(monkeypatch):
    """Set environment variables required by backend modules."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("ENCRYPTION_KEY", "bzc732A921Puw9JN4lrzMo1nw0EjlcUdAyR6Z6N7Sqc=")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("SENTRY_DSN", "")
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")


# ---------------------------------------------------------------------------
# AC2: Mock Supabase client
# ---------------------------------------------------------------------------

class MockSupabaseTable:
    """Chainable mock for Supabase table operations."""

    def __init__(self, data=None, error=None):
        self._data = data if data is not None else []
        self._error = error

    def select(self, *args, **kwargs):
        return self

    def insert(self, *args, **kwargs):
        return self

    def upsert(self, *args, **kwargs):
        return self

    def update(self, *args, **kwargs):
        return self

    def delete(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def neq(self, *args, **kwargs):
        return self

    def gt(self, *args, **kwargs):
        return self

    def gte(self, *args, **kwargs):
        return self

    def lt(self, *args, **kwargs):
        return self

    def lte(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def single(self, *args, **kwargs):
        return self

    def ilike(self, *args, **kwargs):
        return self

    def execute(self):
        if self._error:
            raise self._error
        return SimpleNamespace(data=self._data, count=len(self._data) if self._data else 0)


class MockSupabaseClient:
    """Configurable mock Supabase client.

    Usage:
        client = MockSupabaseClient()
        client.set_table_data("profiles", [{"id": "...", "email": "..."}])
        client.fail_all()  # Makes ALL operations raise
    """

    def __init__(self):
        self._table_data = {}
        self._table_errors = {}
        self._global_error = None

    def set_table_data(self, table_name: str, data: list):
        self._table_data[table_name] = data

    def set_table_error(self, table_name: str, error: Exception):
        self._table_errors[table_name] = error

    def fail_all(self, error: Exception = None):
        self._global_error = error or Exception("Supabase totally unavailable")

    def table(self, name: str):
        if self._global_error:
            return MockSupabaseTable(error=self._global_error)
        if name in self._table_errors:
            return MockSupabaseTable(error=self._table_errors[name])
        return MockSupabaseTable(data=self._table_data.get(name, []))

    def rpc(self, *args, **kwargs):
        if self._global_error:
            raise self._global_error
        return MockSupabaseTable()

    def storage(self):
        mock = Mock()
        mock.from_.return_value = mock
        mock.upload.return_value = {"Key": "test-key"}
        mock.create_signed_url.return_value = {"signedURL": "https://test.storage/file.xlsx"}
        return mock


@pytest.fixture
def mock_supabase_client():
    """Configurable mock Supabase client for integration tests."""
    return MockSupabaseClient()


@pytest.fixture
def supabase_total_failure():
    """Supabase client that fails on ALL operations."""
    client = MockSupabaseClient()
    client.fail_all()
    return client


# ---------------------------------------------------------------------------
# AC2: Mock PNCP responses
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_licitacoes_raw():
    """Sample raw licitacao data as returned by PNCP API."""
    return [
        {
            "codigoCompra": "COMP-001",
            "numeroControlePNCP": "12345678000100-1-000001/2026",
            "objetoCompra": "Aquisicao de uniformes escolares para rede municipal",
            "nomeOrgao": "Prefeitura Municipal de Sao Paulo",
            "uf": "SP",
            "municipio": "Sao Paulo",
            "valorTotalEstimado": 150000.00,
            "modalidadeNome": "Pregao Eletronico",
            "codigoModalidadeContratacao": 6,
            "dataPublicacaoPncp": "2026-02-01",
            "dataAberturaProposta": "2026-02-15",
            "dataEncerramentoProposta": "2026-03-15",
            "situacaoCompra": "Aberta",
            "linkSistemaOrigem": "https://pncp.gov.br/app/editais/123",
            "_source": "PNCP",
            "_relevance_score": 0.85,
            "_matched_terms": ["uniformes", "escolares"],
            "_relevance_source": "keyword",
        },
        {
            "codigoCompra": "COMP-002",
            "numeroControlePNCP": "98765432000100-1-000002/2026",
            "objetoCompra": "Fornecimento de camisetas e calcas para funcionarios",
            "nomeOrgao": "Secretaria de Educacao do Estado",
            "uf": "RJ",
            "municipio": "Rio de Janeiro",
            "valorTotalEstimado": 80000.00,
            "modalidadeNome": "Pregao Eletronico",
            "codigoModalidadeContratacao": 6,
            "dataPublicacaoPncp": "2026-02-05",
            "dataAberturaProposta": "2026-02-20",
            "dataEncerramentoProposta": "2026-03-20",
            "situacaoCompra": "Aberta",
            "linkSistemaOrigem": "https://pncp.gov.br/app/editais/456",
            "_source": "PNCP",
            "_relevance_score": 0.72,
            "_matched_terms": ["camisetas"],
            "_relevance_source": "keyword",
        },
        {
            "codigoCompra": "COMP-003",
            "objetoCompra": "Compra de tecidos para confeccao de uniformes hospitalares",
            "nomeOrgao": "Hospital Estadual",
            "uf": "MG",
            "municipio": "Belo Horizonte",
            "valorTotalEstimado": 200000.00,
            "modalidadeNome": "Concorrencia Eletronica",
            "codigoModalidadeContratacao": 4,
            "dataPublicacaoPncp": "2026-02-10",
            "dataAberturaProposta": "2026-02-25",
            "dataEncerramentoProposta": "2026-03-25",
            "situacaoCompra": "Aberta",
            "_source": "PNCP",
            "_relevance_score": 0.65,
            "_matched_terms": ["uniformes"],
            "_relevance_source": "keyword",
        },
    ]


# ---------------------------------------------------------------------------
# AC2: Mock Redis
# ---------------------------------------------------------------------------

class MockRedis:
    """In-memory Redis mock for integration tests."""

    def __init__(self):
        self._store = {}
        self._available = True

    async def ping(self):
        if not self._available:
            raise ConnectionError("Redis unavailable")
        return True

    async def get(self, key):
        if not self._available:
            raise ConnectionError("Redis unavailable")
        return self._store.get(key)

    async def set(self, key, value, ex=None):
        if not self._available:
            raise ConnectionError("Redis unavailable")
        self._store[key] = value

    async def delete(self, *keys):
        if not self._available:
            raise ConnectionError("Redis unavailable")
        for k in keys:
            self._store.pop(k, None)

    async def publish(self, channel, message):
        if not self._available:
            raise ConnectionError("Redis unavailable")

    async def close(self):
        pass

    def set_unavailable(self):
        self._available = False


@pytest.fixture
def mock_redis():
    """Mock Redis instance for integration tests."""
    return MockRedis()


# ---------------------------------------------------------------------------
# AC2: FastAPI TestClient with dependency overrides
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_user():
    """Authenticated test user."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "role": "authenticated",
    }


@pytest.fixture
def mock_quota_info():
    """Standard quota info for test user."""
    return SimpleNamespace(
        allowed=True,
        plan_id="professional",
        plan_name="Profissional",
        quota_used=5,
        quota_remaining=95,
        capabilities={
            "allow_excel": True,
            "max_requests_per_month": 100,
            "max_date_range_days": 30,
            "max_ufs": 27,
            "max_requests_per_min": 10,
        },
        quota_reset_date=None,
        trial_expires_at=None,
        error_message=None,
    )


@pytest.fixture
def integration_app(mock_user, mock_supabase_client, mock_redis, mock_quota_info):
    """FastAPI TestClient with all external dependencies mocked.

    This is the core fixture for integration tests. It:
    - Overrides auth to return mock_user
    - Mocks Supabase client
    - Mocks Redis pool
    - Mocks PNCP API (must be further patched per test)
    - Mocks LLM (OpenAI) calls
    - Mocks storage uploads
    """
    from fastapi.testclient import TestClient
    from main import app
    from auth import require_auth

    # Override auth dependency
    app.dependency_overrides[require_auth] = lambda: mock_user

    # Mock rate limiter to always allow (prevents 429 during test runs)
    mock_rate_limiter = Mock()
    mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

    # Apply patches
    patches = [
        patch("supabase_client.get_supabase", return_value=mock_supabase_client),
        patch("database.get_db", return_value=mock_supabase_client),
        patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis),
        patch("redis_pool.get_fallback_cache", return_value=Mock(get=AsyncMock(return_value=None), set=AsyncMock())),
        patch("search_cache.get_from_cache_cascade", new_callable=AsyncMock, return_value=None),
        patch("search_cache.save_to_cache", new_callable=AsyncMock),
        patch("search_cache.get_from_cache", new_callable=AsyncMock, return_value=None),
        patch("quota.check_quota", return_value=mock_quota_info),
        patch("quota.check_and_increment_quota_atomic", return_value=(True, 6, 94)),
        patch("quota.register_search_session", new_callable=AsyncMock, return_value="session-test-id"),
        patch("quota.update_search_session_status", new_callable=AsyncMock),
        patch("storage.upload_excel", return_value={"file_path": "test.xlsx", "signed_url": "https://test.storage/test.xlsx"}),
        # search_pipeline uses `from storage import upload_excel` (top-level),
        # so we must also patch the name in search_pipeline's namespace.
        patch("search_pipeline.upload_excel", return_value={"file_path": "test.xlsx", "signed_url": "https://test.storage/test.xlsx", "file_id": "test-file-id", "expires_in": 3600}),
        patch("llm.gerar_resumo", return_value=_make_mock_resumo()),
        patch("llm.gerar_resumo_fallback", return_value=_make_mock_resumo(fallback=True)),
        # search_pipeline uses `from llm import gerar_resumo, gerar_resumo_fallback` (top-level),
        # so we must also patch the names in search_pipeline's namespace.
        patch("search_pipeline.gerar_resumo", return_value=_make_mock_resumo()),
        patch("search_pipeline.gerar_resumo_fallback", return_value=_make_mock_resumo(fallback=True)),
        patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=False),
        patch("job_queue.enqueue_job", new_callable=AsyncMock, return_value=None),
        # Rate limiter: always allow requests
        patch("routes.search.rate_limiter", mock_rate_limiter),
        # Authorization: skip Supabase role check
        patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)),
        patch("metrics.SEARCH_DURATION", Mock(labels=Mock(return_value=Mock(observe=Mock())))),
        patch("metrics.FETCH_DURATION", Mock(labels=Mock(return_value=Mock(observe=Mock())))),
        patch("metrics.CACHE_HITS", Mock(labels=Mock(return_value=Mock(inc=Mock())))),
        patch("metrics.CACHE_MISSES", Mock(labels=Mock(return_value=Mock(inc=Mock())))),
        patch("metrics.ACTIVE_SEARCHES", Mock(inc=Mock(), dec=Mock())),
        patch("metrics.SEARCHES", Mock(labels=Mock(return_value=Mock(inc=Mock())))),
        patch("metrics.FILTER_DECISIONS", Mock(labels=Mock(return_value=Mock(inc=Mock())))),
        patch("metrics.SEARCH_RESPONSE_STATE", Mock(labels=Mock(return_value=Mock(inc=Mock())))),
        patch("metrics.SEARCH_ERROR_TYPE", Mock(labels=Mock(return_value=Mock(inc=Mock())))),
        patch("telemetry.get_tracer", return_value=Mock(start_as_current_span=MagicMock())),
        patch("telemetry.optional_span", return_value=MagicMock(__enter__=Mock(return_value=Mock(set_attribute=Mock(), record_exception=Mock(), set_status=Mock())), __exit__=Mock(return_value=False))),
        patch("telemetry.get_trace_id", return_value="test-trace-id"),
        patch("sentry_sdk.capture_exception"),
        patch("sentry_sdk.set_tag"),
        # CRIT-003: Mock state machine
        patch("search_state_manager.create_state_machine", new_callable=AsyncMock, return_value=Mock(
            transition_to=AsyncMock(),
            fail=AsyncMock(),
            timeout=AsyncMock(),
            rate_limited=AsyncMock(),
            is_terminal=False,
        )),
        patch("search_state_manager.get_state_machine", return_value=None),
        patch("search_state_manager.remove_state_machine"),
        patch("search_state_manager.get_search_status", new_callable=AsyncMock, return_value=None),
        patch("search_state_manager.get_timeline", new_callable=AsyncMock, return_value=[]),
        patch("search_state_manager.get_current_state", new_callable=AsyncMock, return_value=None),
    ]

    started = [p.start() for p in patches]

    client = TestClient(app, raise_server_exceptions=False)
    yield client

    # Cleanup
    for p in patches:
        p.stop()
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _make_mock_resumo(fallback=False):
    """Create a mock ResumoEstrategico instance."""
    from schemas import ResumoEstrategico, Recomendacao
    return ResumoEstrategico(
        resumo_executivo="Resumo de teste" + (" (fallback)" if fallback else ""),
        total_oportunidades=3,
        valor_total=430000.0,
        destaques=["Uniformes escolares em SP"],
        alerta_urgencia=None,
        recomendacoes=[
            Recomendacao(
                oportunidade="Prefeitura de SP - Uniformes Escolares",
                valor=150000.0,
                urgencia="media",
                acao_sugerida="Priorizar pregoes eletronicos",
                justificativa="Valor compativel com porte da empresa.",
            )
        ],
        alertas_urgencia=[],
        insight_setorial="Setor de vestuario com demanda estavel.",
    )


def make_busca_request(
    ufs=None,
    data_inicial="2026-02-01",
    data_final="2026-02-15",
    search_id=None,
    setor_id="vestuario",
    force_fresh=False,
):
    """Build a standard BuscaRequest payload for testing."""
    import uuid
    return {
        "ufs": ufs or ["SP"],
        "data_inicial": data_inicial,
        "data_final": data_final,
        "setor_id": setor_id,
        "search_id": search_id or str(uuid.uuid4()),
        "force_fresh": force_fresh,
    }


def make_pncp_success_response(licitacoes, page=1, total_pages=1):
    """Build a mock PNCP API page response."""
    return {
        "data": licitacoes,
        "page": page,
        "totalPages": total_pages,
        "totalRegistros": len(licitacoes),
    }
