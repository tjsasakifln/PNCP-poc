"""TD-SYS-022: Standardized mock builders for SmartLic test suite.

Usage:
    from tests.helpers.mock_factories import MockSupabaseBuilder, MockLLMBuilder

    supabase = MockSupabaseBuilder().with_data([{"id": "1"}]).build()
    llm = MockLLMBuilder().accepting().build()
"""
from unittest.mock import AsyncMock, Mock
from typing import Any


class MockSupabaseBuilder:
    """Fluent builder for Supabase client mocks.

    The Supabase SDK uses method chaining:
        client.table("x").select("*").eq("id", "1").execute()

    This builder creates a mock that supports this chain and returns
    configurable data from .execute().
    """

    def __init__(self):
        self._data: list = []
        self._error: str | None = None
        self._count: int | None = None

    def with_data(self, data: list) -> "MockSupabaseBuilder":
        """Set the data returned by .execute()."""
        self._data = data
        return self

    def with_single(self, item: dict) -> "MockSupabaseBuilder":
        """Convenience: single-item response."""
        self._data = [item]
        return self

    def with_empty(self) -> "MockSupabaseBuilder":
        """Empty response (no data)."""
        self._data = []
        return self

    def with_error(self, message: str) -> "MockSupabaseBuilder":
        """Simulate a DB error on .execute()."""
        self._error = message
        return self

    def with_count(self, count: int) -> "MockSupabaseBuilder":
        self._count = count
        return self

    def build(self) -> Mock:
        """Build and return the configured Mock."""
        if self._error:
            mock = Mock()
            mock.execute.side_effect = Exception(self._error)
        else:
            execute_result = Mock()
            execute_result.data = self._data
            execute_result.count = self._count
            execute_result.error = None
            mock = Mock()
            mock.execute.return_value = execute_result

        # Chain all common Supabase SDK methods to self
        for method in (
            "table", "select", "insert", "upsert", "update", "delete",
            "eq", "neq", "gt", "lt", "gte", "lte", "in_",
            "order", "limit", "offset", "single", "maybe_single",
            "filter", "contains", "ilike", "like", "is_",
            "range", "match", "not_", "or_", "rpc",
        ):
            getattr(mock, method).return_value = mock

        return mock


class MockPNCPBuilder:
    """Fluent builder for PNCP API client mocks."""

    def __init__(self):
        self._items: list = []
        self._total: int = 0
        self._error: Exception | None = None

    def with_results(self, items: list) -> "MockPNCPBuilder":
        self._items = items
        self._total = len(items)
        return self

    def with_total(self, total: int) -> "MockPNCPBuilder":
        self._total = total
        return self

    def with_error(self, exc: Exception) -> "MockPNCPBuilder":
        self._error = exc
        return self

    def with_empty(self) -> "MockPNCPBuilder":
        self._items = []
        self._total = 0
        return self

    def build(self) -> AsyncMock:
        mock = AsyncMock()
        if self._error:
            mock.buscar_todas_ufs_paralelo.side_effect = self._error
            mock.buscar_licitacoes_uf.side_effect = self._error
        else:
            mock.buscar_todas_ufs_paralelo.return_value = self._items
            mock.buscar_licitacoes_uf.return_value = {
                "data": self._items,
                "totalRegistros": self._total,
            }
        return mock


class MockLLMBuilder:
    """Fluent builder for LLM/OpenAI client mocks."""

    def __init__(self):
        self._decision: str = "YES"
        self._reasoning: str = "Mock reasoning"
        self._error: Exception | None = None

    def accepting(self) -> "MockLLMBuilder":
        """LLM returns YES (relevant)."""
        self._decision = "YES"
        return self

    def rejecting(self) -> "MockLLMBuilder":
        """LLM returns NO (not relevant)."""
        self._decision = "NO"
        return self

    def with_reasoning(self, text: str) -> "MockLLMBuilder":
        self._reasoning = text
        return self

    def with_error(self, exc: Exception) -> "MockLLMBuilder":
        self._error = exc
        return self

    def build(self) -> AsyncMock:
        mock = AsyncMock()
        if self._error:
            mock.chat.completions.create.side_effect = self._error
        else:
            completion = Mock()
            completion.choices = [Mock()]
            completion.choices[0].message = Mock()
            completion.choices[0].message.content = self._decision
            completion.usage = Mock()
            completion.usage.prompt_tokens = 100
            completion.usage.completion_tokens = 1
            mock.chat.completions.create.return_value = completion
        return mock
