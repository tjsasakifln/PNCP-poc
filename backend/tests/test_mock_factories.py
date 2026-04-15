"""Tests for TD-SYS-022 mock factory helpers."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from tests.helpers.mock_factories import MockSupabaseBuilder, MockPNCPBuilder, MockLLMBuilder


class TestMockSupabaseBuilder:
    def test_with_data_returns_data_on_execute(self):
        mock = MockSupabaseBuilder().with_data([{"id": "1", "name": "test"}]).build()
        result = mock.table("profiles").select("*").execute()
        assert result.data == [{"id": "1", "name": "test"}]

    def test_with_empty_returns_empty_list(self):
        mock = MockSupabaseBuilder().with_empty().build()
        result = mock.execute()
        assert result.data == []

    def test_with_error_raises_exception(self):
        mock = MockSupabaseBuilder().with_error("Connection failed").build()
        with pytest.raises(Exception, match="Connection failed"):
            mock.execute()

    def test_method_chaining_works(self):
        mock = MockSupabaseBuilder().with_data([{"id": "1"}]).build()
        # All these should not raise
        result = (
            mock.table("x")
            .select("*")
            .eq("id", "1")
            .order("created_at")
            .limit(10)
            .execute()
        )
        assert result.data == [{"id": "1"}]

    def test_with_single_returns_single_item(self):
        mock = MockSupabaseBuilder().with_single({"id": "42"}).build()
        result = mock.execute()
        assert result.data == [{"id": "42"}]

    def test_with_count_sets_count(self):
        mock = MockSupabaseBuilder().with_data([]).with_count(99).build()
        result = mock.execute()
        assert result.count == 99

    def test_error_result_has_none_data(self):
        mock = MockSupabaseBuilder().with_error("DB down").build()
        with pytest.raises(Exception):
            mock.execute()

    def test_rpc_chaining_works(self):
        mock = MockSupabaseBuilder().with_data([{"value": 1}]).build()
        result = mock.rpc("my_function", {}).execute()
        assert result.data == [{"value": 1}]


class TestMockPNCPBuilder:
    @pytest.mark.asyncio
    async def test_with_results_returns_items(self):
        items = [{"id": "licitacao-1"}, {"id": "licitacao-2"}]
        mock = MockPNCPBuilder().with_results(items).build()
        result = await mock.buscar_todas_ufs_paralelo("SP", "vestuario", 10)
        assert result == items

    @pytest.mark.asyncio
    async def test_with_empty_returns_empty(self):
        mock = MockPNCPBuilder().with_empty().build()
        result = await mock.buscar_todas_ufs_paralelo()
        assert result == []

    @pytest.mark.asyncio
    async def test_with_error_raises_on_buscar(self):
        exc = RuntimeError("PNCP unreachable")
        mock = MockPNCPBuilder().with_error(exc).build()
        with pytest.raises(RuntimeError, match="PNCP unreachable"):
            await mock.buscar_todas_ufs_paralelo()

    @pytest.mark.asyncio
    async def test_buscar_licitacoes_uf_returns_dict(self):
        items = [{"id": "lic-1"}]
        mock = MockPNCPBuilder().with_results(items).build()
        result = await mock.buscar_licitacoes_uf("SP", 1)
        assert result["data"] == items
        assert result["totalRegistros"] == 1

    @pytest.mark.asyncio
    async def test_with_total_overrides_count(self):
        mock = MockPNCPBuilder().with_results([{"id": "x"}]).with_total(500).build()
        result = await mock.buscar_licitacoes_uf("SP", 1)
        assert result["totalRegistros"] == 500


class TestMockLLMBuilder:
    @pytest.mark.asyncio
    async def test_accepting_returns_yes(self):
        mock = MockLLMBuilder().accepting().build()
        result = await mock.chat.completions.create(messages=[], model="gpt-4")
        assert result.choices[0].message.content == "YES"

    @pytest.mark.asyncio
    async def test_rejecting_returns_no(self):
        mock = MockLLMBuilder().rejecting().build()
        result = await mock.chat.completions.create(messages=[], model="gpt-4")
        assert result.choices[0].message.content == "NO"

    @pytest.mark.asyncio
    async def test_with_error_raises(self):
        mock = MockLLMBuilder().with_error(Exception("API timeout")).build()
        with pytest.raises(Exception, match="API timeout"):
            await mock.chat.completions.create(messages=[], model="gpt-4")

    @pytest.mark.asyncio
    async def test_usage_fields_present(self):
        mock = MockLLMBuilder().accepting().build()
        result = await mock.chat.completions.create(messages=[], model="gpt-4")
        assert result.usage.prompt_tokens == 100
        assert result.usage.completion_tokens == 1

    def test_default_decision_is_yes(self):
        builder = MockLLMBuilder()
        assert builder._decision == "YES"


class TestBuilderFixtures:
    def test_mock_supabase_builder_fixture(self, mock_supabase_builder):
        mock = mock_supabase_builder.with_data([{"id": "test"}]).build()
        assert mock.execute().data == [{"id": "test"}]

    def test_mock_pncp_builder_fixture_exists(self, mock_pncp_builder):
        assert mock_pncp_builder is not None
        mock = mock_pncp_builder.with_empty().build()
        assert mock is not None

    def test_mock_llm_builder_fixture_exists(self, mock_llm_builder):
        assert mock_llm_builder is not None
        mock = mock_llm_builder.accepting().build()
        assert mock is not None

    def test_supabase_builder_is_fresh_per_test(self, mock_supabase_builder):
        # Each fixture call should return a fresh builder
        assert mock_supabase_builder._data == []
        assert mock_supabase_builder._error is None
