"""Unit tests for datalake_query.py — query_datalake, _build_tsquery, _row_to_normalized.

STORY-437: Tests for websearch_to_tsquery routing and trigram fallback.
STORY-438: Tests for query embedding generation and hybrid search.
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from datalake_query import (
    _build_tsquery,
    _build_trigram_term,
    _row_to_normalized,
    query_datalake,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SAMPLE_DB_ROW = {
    "pncp_id": "12345678000100-1-000001/2026",
    "uf": "SP",
    "municipio": "São Paulo",
    "orgao_razao_social": "Prefeitura Municipal de São Paulo",
    "orgao_cnpj": "12345678000100",
    "objeto_compra": "Obra de pavimentação asfáltica",
    "valor_total_estimado": 1500000.0,
    "modalidade_id": 6,
    "modalidade_nome": "Pregão - Eletrônico",
    "situacao_compra": "Divulgada",
    "data_publicacao": "2026-03-20T10:00:00Z",
    "data_abertura": "2026-04-01T09:00:00Z",
    "data_encerramento": "2026-04-15T18:00:00Z",
    "link_pncp": "https://pncp.gov.br/app/editais/12345678000100-1-000001/2026",
    "esfera_id": "M",
    "ts_rank": 0.5,
}

SAMPLE_TRIGRAM_ROW = {
    **SAMPLE_DB_ROW,
    "sim_score": 0.75,
}


# ---------------------------------------------------------------------------
# _build_tsquery (STORY-437 AC2)
# Returns tuple[str | None, str | None]: (tsquery_text, websearch_text)
# ---------------------------------------------------------------------------


class TestBuildTsquery:
    """Tests for _build_tsquery() — now returns (tsquery_text, websearch_text) tuple."""

    def test_returns_none_none_when_both_inputs_none(self):
        assert _build_tsquery(None, None) == (None, None)

    def test_returns_none_none_when_both_inputs_empty(self):
        assert _build_tsquery([], []) == (None, None)

    def test_returns_none_none_for_whitespace_only_keywords(self):
        assert _build_tsquery(["  ", " "], None) == (None, None)

    def test_single_keyword_goes_to_tsquery(self):
        tsq, ws = _build_tsquery(["construção"], None)
        assert tsq == "construção"
        assert ws is None

    def test_multiple_keywords_or_joined_in_tsquery(self):
        tsq, ws = _build_tsquery(["construção", "obras"], None)
        assert tsq == "construção | obras"
        assert ws is None

    def test_single_custom_term_goes_to_websearch_text(self):
        tsq, ws = _build_tsquery(None, ["asfalto"])
        assert tsq is None
        assert ws == "asfalto"

    def test_multiple_custom_terms_joined_with_space_in_websearch(self):
        # websearch_to_tsquery('portuguese', 'creche escola') = creche AND escola
        tsq, ws = _build_tsquery(None, ["creche", "escola"])
        assert tsq is None
        assert ws == "creche escola"

    def test_keywords_go_to_tsquery_custom_to_websearch(self):
        tsq, ws = _build_tsquery(["pavimentação"], ["asfalto"])
        assert tsq == "pavimentação"
        assert ws == "asfalto"

    def test_multiple_keywords_and_custom_term_separated(self):
        tsq, ws = _build_tsquery(["construção", "obras"], ["asfalto"])
        assert tsq == "construção | obras"
        assert ws == "asfalto"

    def test_multi_word_keyword_becomes_phrase_query_in_tsquery(self):
        """Multi-word keywords must be joined with <-> for phrase matching."""
        tsq, ws = _build_tsquery(["pré moldado"], None)
        assert tsq == "pré<->moldado"
        assert ws is None

    def test_multi_word_custom_term_preserved_raw_in_websearch(self):
        """Multi-word custom terms are kept as-is for websearch_to_tsquery."""
        tsq, ws = _build_tsquery(None, ["creche municipal"])
        assert tsq is None
        assert ws == "creche municipal"

    def test_three_word_phrase_keyword(self):
        tsq, ws = _build_tsquery(["pavimentação de ruas"], None)
        assert tsq == "pavimentação<->de<->ruas"

    def test_special_chars_stripped_from_keywords_not_custom(self):
        """Characters that break tsquery must be removed from keywords."""
        tsq, _ = _build_tsquery(["obras!"], None)
        assert tsq is not None
        assert "!" not in tsq

    def test_keywords_or_joined_custom_joined_with_space(self):
        """Keywords block OR'd; custom terms space-joined for websearch."""
        tsq, ws = _build_tsquery(["construção", "obras"], ["asfalto", "concreto"])
        assert tsq == "construção | obras"
        assert ws == "asfalto concreto"

    def test_empty_keyword_strings_filtered_out(self):
        """Empty strings in keywords list must be ignored."""
        tsq, _ = _build_tsquery(["", "construção", ""], None)
        assert tsq == "construção"

    def test_empty_custom_term_strings_filtered_out(self):
        _, ws = _build_tsquery(None, ["", "escola", ""])
        assert ws == "escola"

    def test_custom_term_with_quotes_preserved(self):
        """Quoted phrases must be preserved verbatim for websearch_to_tsquery."""
        _, ws = _build_tsquery(None, ['"limpeza hospitalar"'])
        assert ws == '"limpeza hospitalar"'

    def test_custom_term_with_exclusion_preserved(self):
        """Exclusion prefix must be preserved verbatim for websearch_to_tsquery."""
        _, ws = _build_tsquery(None, ["-escolar"])
        assert ws == "-escolar"


# ---------------------------------------------------------------------------
# _build_trigram_term (STORY-437 AC3)
# ---------------------------------------------------------------------------


class TestBuildTrigramTerm:
    """Tests for _build_trigram_term()."""

    def test_keywords_only(self):
        result = _build_trigram_term(["construção", "obras"], None)
        assert "construção" in result
        assert "obras" in result

    def test_custom_only(self):
        result = _build_trigram_term(None, ["asfalto"])
        assert result == "asfalto"

    def test_both_combined(self):
        result = _build_trigram_term(["pavimentação"], ["asfalto"])
        assert "pavimentação" in result
        assert "asfalto" in result

    def test_returns_none_when_empty(self):
        assert _build_trigram_term(None, None) is None
        assert _build_trigram_term([], []) is None

    def test_quotes_and_dashes_removed(self):
        """Quotes and dashes from websearch syntax should be stripped for trigram."""
        result = _build_trigram_term(None, ['"limpeza hospitalar"', "-escolar"])
        assert '"' not in result
        assert result.startswith("-") is False


# ---------------------------------------------------------------------------
# query_datalake
# ---------------------------------------------------------------------------


class TestQueryDatalake:
    """Tests for query_datalake().

    datalake_query.py imports get_supabase inside the function body with
    ``from supabase_client import get_supabase``, so we must patch it at the
    supabase_client module level (where it is defined).

    Both _query_cache and _embedding_cache are module-level singletons — must
    be cleared between tests to prevent cross-test cache pollution.
    """

    @pytest.fixture(autouse=True)
    def clear_datalake_caches(self):
        """Clear module-level caches before and after each test."""
        import datalake_query
        datalake_query._query_cache.clear()
        datalake_query._embedding_cache.clear()
        yield
        datalake_query._query_cache.clear()
        datalake_query._embedding_cache.clear()

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_returns_normalized_records(self, mock_get_sb):
        """Must return a list of normalized dicts from the RPC rows."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = [SAMPLE_DB_ROW]
        mock_get_sb.return_value = mock_sb

        result = await query_datalake(
            ufs=["SP"],
            data_inicial="2026-03-15",
            data_final="2026-03-25",
        )

        assert len(result) == 1
        assert result[0]["numeroControlePNCP"] == "12345678000100-1-000001/2026"  # mapped from pncp_id
        assert result[0]["uf"] == "SP"

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_calls_search_datalake_rpc(self, mock_get_sb):
        """Must invoke the search_datalake RPC function."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = []
        mock_get_sb.return_value = mock_sb

        await query_datalake(
            ufs=["SC"],
            data_inicial="2026-03-10",
            data_final="2026-03-20",
        )

        mock_sb.rpc.assert_called_once()
        rpc_args = mock_sb.rpc.call_args[0]
        assert rpc_args[0] == "search_datalake"

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_rpc_params_passed_correctly(self, mock_get_sb):
        """All query parameters must be forwarded to the RPC as p_* keys."""
        mock_sb = MagicMock()
        # Return non-empty data so trigram fallback is NOT activated (avoids 3rd call)
        mock_sb.rpc.return_value.execute.return_value.data = [SAMPLE_DB_ROW]
        mock_get_sb.return_value = mock_sb

        await query_datalake(
            ufs=["PR", "SC"],
            data_inicial="2026-03-01",
            data_final="2026-03-31",
            modalidades=[5, 6],
            keywords=["construção"],
            custom_terms=["asfalto"],
            valor_min=100000.0,
            valor_max=5000000.0,
            esferas=["M"],
            modo_busca="abertura",
            limit=500,
        )

        # query_datalake paginates per-UF (PostgREST 1000-row cap), so the
        # RPC is called once per UF.  Non-empty results prevent trigram fallback.
        assert mock_sb.rpc.call_count == 2
        all_uf_params = [call[0][1]["p_ufs"] for call in mock_sb.rpc.call_args_list]
        assert ["PR"] in all_uf_params
        assert ["SC"] in all_uf_params

        # Check shared (non-UF) params from the first call
        _, rpc_params = mock_sb.rpc.call_args_list[0][0]
        assert rpc_params["p_date_start"] == "2026-03-01"
        assert rpc_params["p_date_end"] == "2026-03-31"
        assert rpc_params["p_modalidades"] == [5, 6]
        assert rpc_params["p_valor_min"] == 100000.0
        assert rpc_params["p_valor_max"] == 5000000.0
        assert rpc_params["p_esferas"] == ["M"]
        assert rpc_params["p_modo"] == "abertura"
        assert rpc_params["p_limit"] == 500

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_tsquery_built_from_keywords(self, mock_get_sb):
        """keywords param must result in a non-None p_tsquery in the RPC call."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = []
        mock_get_sb.return_value = mock_sb

        await query_datalake(
            ufs=["SP"],
            data_inicial="2026-03-01",
            data_final="2026-03-31",
            keywords=["construção", "obras"],
        )

        # Use call_args_list[0] — the FIRST RPC call is always search_datalake.
        # TRIGRAM_FALLBACK_ENABLED may be True, making search_datalake_trigram_fallback
        # the *last* call; call_args would point to that one (lacks p_tsquery).
        _, rpc_params = mock_sb.rpc.call_args_list[0][0]
        assert rpc_params["p_tsquery"] == "construção | obras"
        assert rpc_params["p_websearch_text"] is None

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_websearch_text_passed_for_custom_terms(self, mock_get_sb):
        """custom_terms must result in p_websearch_text in the RPC call (STORY-437 AC2)."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = []
        mock_get_sb.return_value = mock_sb

        await query_datalake(
            ufs=["SP"],
            data_inicial="2026-03-01",
            data_final="2026-03-31",
            custom_terms=["limpeza", "hospitalar"],
        )

        # Use call_args_list[0] to inspect the search_datalake call specifically.
        _, rpc_params = mock_sb.rpc.call_args_list[0][0]
        assert rpc_params["p_tsquery"] is None
        assert rpc_params["p_websearch_text"] == "limpeza hospitalar"

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_both_tsquery_and_websearch_when_keywords_and_custom(self, mock_get_sb):
        """When both keywords and custom_terms provided, both params are set."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = []
        mock_get_sb.return_value = mock_sb

        await query_datalake(
            ufs=["SP"],
            data_inicial="2026-03-01",
            data_final="2026-03-31",
            keywords=["pavimentação"],
            custom_terms=["asfalto"],
        )

        # Use call_args_list[0] to inspect the search_datalake call specifically.
        _, rpc_params = mock_sb.rpc.call_args_list[0][0]
        assert rpc_params["p_tsquery"] == "pavimentação"
        assert rpc_params["p_websearch_text"] == "asfalto"

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_tsquery_none_when_no_keywords_or_custom_terms(self, mock_get_sb):
        """No keywords and no custom_terms must send p_tsquery=None and p_websearch_text=None."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = []
        mock_get_sb.return_value = mock_sb

        await query_datalake(
            ufs=["SP"],
            data_inicial="2026-03-01",
            data_final="2026-03-31",
        )

        _, rpc_params = mock_sb.rpc.call_args[0]
        assert rpc_params["p_tsquery"] is None
        assert rpc_params["p_websearch_text"] is None

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_supabase_unavailable(self, caplog):
        """When get_supabase raises, must return [] (fail-open)."""
        with patch("supabase_client.get_supabase", side_effect=RuntimeError("unavailable")):
            with caplog.at_level(logging.WARNING, logger="datalake_query"):
                result = await query_datalake(
                    ufs=["SP"],
                    data_inicial="2026-03-01",
                    data_final="2026-03-31",
                )
        assert result == []

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_returns_empty_list_when_rpc_raises(self, mock_get_sb, caplog):
        """RPC exceptions must be swallowed and [] returned (fail-open)."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.side_effect = RuntimeError("RPC error")
        mock_get_sb.return_value = mock_sb

        with caplog.at_level(logging.ERROR, logger="datalake_query"):
            result = await query_datalake(
                ufs=["SP"],
                data_inicial="2026-03-01",
                data_final="2026-03-31",
            )
        assert result == []

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_empty_rpc_response_returns_empty_list(self, mock_get_sb):
        """RPC returning None data must return []."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = None
        mock_get_sb.return_value = mock_sb

        result = await query_datalake(
            ufs=["SP"],
            data_inicial="2026-03-01",
            data_final="2026-03-31",
        )
        assert result == []

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_multiple_rows_all_normalized(self, mock_get_sb):
        """All RPC rows must be normalized and returned."""
        row2 = dict(SAMPLE_DB_ROW, pncp_id="99999999000100-1-000002/2026")
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = [SAMPLE_DB_ROW, row2]
        mock_get_sb.return_value = mock_sb

        result = await query_datalake(
            ufs=["SP"],
            data_inicial="2026-03-01",
            data_final="2026-03-31",
        )
        assert len(result) == 2

    # --- STORY-437 AC3: Trigram fallback ---

    @pytest.mark.asyncio
    @patch("config.features.TRIGRAM_FALLBACK_ENABLED", True)
    @patch("supabase_client.get_supabase")
    async def test_trigram_fallback_activates_when_fts_returns_empty(self, mock_get_sb):
        """When FTS returns 0 results and TRIGRAM_FALLBACK_ENABLED, must call trigram RPC."""
        mock_sb = MagicMock()

        def mock_rpc(rpc_name, params):
            m = MagicMock()
            if rpc_name == "search_datalake":
                m.execute.return_value.data = []
            elif rpc_name == "search_datalake_trigram_fallback":
                m.execute.return_value.data = [SAMPLE_TRIGRAM_ROW]
            else:
                m.execute.return_value.data = []
            return m

        mock_sb.rpc.side_effect = mock_rpc
        mock_get_sb.return_value = mock_sb

        result = await query_datalake(
            ufs=["SP"],
            data_inicial="2026-03-01",
            data_final="2026-03-31",
            keywords=["construção"],
        )

        # Must have called both RPCs
        rpc_names = [call[0][0] for call in mock_sb.rpc.call_args_list]
        assert "search_datalake_trigram_fallback" in rpc_names

        # Results must be tagged as trigram_fallback
        assert len(result) == 1
        assert result[0]["_source"] == "trigram_fallback"

    @pytest.mark.asyncio
    @patch("config.features.TRIGRAM_FALLBACK_ENABLED", False)
    @patch("supabase_client.get_supabase")
    async def test_trigram_fallback_not_called_when_disabled(self, mock_get_sb):
        """When TRIGRAM_FALLBACK_ENABLED=False, must NOT call trigram RPC."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = []
        mock_get_sb.return_value = mock_sb

        result = await query_datalake(
            ufs=["SP"],
            data_inicial="2026-03-01",
            data_final="2026-03-31",
            keywords=["construção"],
        )

        # Only search_datalake should have been called
        rpc_names = [call[0][0] for call in mock_sb.rpc.call_args_list]
        assert "search_datalake_trigram_fallback" not in rpc_names
        assert result == []

    @pytest.mark.asyncio
    @patch("config.features.TRIGRAM_FALLBACK_ENABLED", True)
    @patch("supabase_client.get_supabase")
    async def test_trigram_fallback_not_called_when_fts_returns_results(self, mock_get_sb):
        """When FTS returns results, trigram fallback must NOT be called."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = [SAMPLE_DB_ROW]
        mock_get_sb.return_value = mock_sb

        result = await query_datalake(
            ufs=["SP"],
            data_inicial="2026-03-01",
            data_final="2026-03-31",
            keywords=["pavimentação"],
        )

        rpc_names = [call[0][0] for call in mock_sb.rpc.call_args_list]
        assert "search_datalake_trigram_fallback" not in rpc_names
        assert len(result) == 1

    @pytest.mark.asyncio
    @patch("config.features.TRIGRAM_FALLBACK_ENABLED", True)
    @patch("supabase_client.get_supabase")
    async def test_trigram_fallback_not_called_when_no_search_terms(self, mock_get_sb):
        """Without any search terms, trigram fallback must NOT be called."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = []
        mock_get_sb.return_value = mock_sb

        result = await query_datalake(
            ufs=["SP"],
            data_inicial="2026-03-01",
            data_final="2026-03-31",
        )

        rpc_names = [call[0][0] for call in mock_sb.rpc.call_args_list]
        assert "search_datalake_trigram_fallback" not in rpc_names
        assert result == []

    # --- STORY-438 AC4: Query embedding ---

    @pytest.mark.asyncio
    @patch("config.features.EMBEDDING_ENABLED", True)
    @patch("supabase_client.get_supabase")
    async def test_embedding_passed_in_rpc_params_when_enabled(self, mock_get_sb):
        """When EMBEDDING_ENABLED=True and embedding succeeds, p_embedding in RPC params."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = [SAMPLE_DB_ROW]
        mock_get_sb.return_value = mock_sb

        fake_embedding = [0.1] * 256

        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=fake_embedding)]
        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        with patch("openai.AsyncOpenAI", return_value=mock_openai_client):
            result = await query_datalake(
                ufs=["SP"],
                data_inicial="2026-03-01",
                data_final="2026-03-31",
                keywords=["limpeza"],
            )

        _, rpc_params = mock_sb.rpc.call_args[0]
        assert "p_embedding" in rpc_params
        assert rpc_params["p_embedding"] == fake_embedding

    @pytest.mark.asyncio
    @patch("config.features.EMBEDDING_ENABLED", False)
    @patch("supabase_client.get_supabase")
    async def test_embedding_not_in_rpc_params_when_disabled(self, mock_get_sb):
        """When EMBEDDING_ENABLED=False, p_embedding must NOT be in RPC params."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = [SAMPLE_DB_ROW]
        mock_get_sb.return_value = mock_sb

        await query_datalake(
            ufs=["SP"],
            data_inicial="2026-03-01",
            data_final="2026-03-31",
            keywords=["limpeza"],
        )

        _, rpc_params = mock_sb.rpc.call_args[0]
        assert "p_embedding" not in rpc_params

    @pytest.mark.asyncio
    @patch("config.features.EMBEDDING_ENABLED", True)
    @patch("supabase_client.get_supabase")
    async def test_embedding_failure_falls_back_to_fts_only(self, mock_get_sb):
        """When embedding generation fails, search must still proceed (FTS only)."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = [SAMPLE_DB_ROW]
        mock_get_sb.return_value = mock_sb

        mock_openai_client = MagicMock()
        mock_openai_client.embeddings.create = AsyncMock(side_effect=RuntimeError("rate limit"))

        with patch("openai.AsyncOpenAI", return_value=mock_openai_client):
            result = await query_datalake(
                ufs=["SP"],
                data_inicial="2026-03-01",
                data_final="2026-03-31",
                keywords=["limpeza"],
            )

        # Search still completed despite embedding failure
        assert len(result) == 1
        # p_embedding was NOT sent (embedding was None, not included)
        _, rpc_params = mock_sb.rpc.call_args[0]
        assert "p_embedding" not in rpc_params

    @pytest.mark.asyncio
    @patch("config.features.EMBEDDING_ENABLED", True)
    @patch("supabase_client.get_supabase")
    async def test_query_embedding_cached_on_second_call(self, mock_get_sb):
        """Second call with same terms must use cached embedding (no OpenAI call)."""
        import datalake_query
        # Clear embedding cache before test
        datalake_query._embedding_cache.clear()
        datalake_query._query_cache.clear()

        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = [SAMPLE_DB_ROW]
        mock_get_sb.return_value = mock_sb

        fake_embedding = [0.2] * 256
        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=fake_embedding)]
        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        with patch("openai.AsyncOpenAI", return_value=mock_openai_client):
            # First call — generates embedding
            await query_datalake(
                ufs=["SP"],
                data_inicial="2026-03-01",
                data_final="2026-03-31",
                keywords=["limpeza"],
            )
            # Second call — should NOT call OpenAI again (embedding is cached)
            datalake_query._query_cache.clear()  # Clear query cache to force RPC call
            await query_datalake(
                ufs=["SP"],
                data_inicial="2026-03-01",
                data_final="2026-03-31",
                keywords=["limpeza"],
            )

        # OpenAI should have been called exactly once
        assert mock_openai_client.embeddings.create.call_count == 1


# ---------------------------------------------------------------------------
# _row_to_normalized
# ---------------------------------------------------------------------------


class TestRowToNormalized:
    """Tests for _row_to_normalized()."""

    def test_maps_pncp_id_to_normalized_fields(self):
        """pncp_id must be mapped to both numeroControlePNCP and codigoCompra."""
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["numeroControlePNCP"] == "12345678000100-1-000001/2026"
        assert result["codigoCompra"] == "12345678000100-1-000001/2026"

    def test_maps_uf(self):
        assert _row_to_normalized(SAMPLE_DB_ROW)["uf"] == "SP"

    def test_maps_municipio(self):
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["municipio"] == "São Paulo"

    def test_maps_orgao_razao_social_to_nome_orgao(self):
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["nomeOrgao"] == "Prefeitura Municipal de São Paulo"

    def test_maps_objeto_compra(self):
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["objetoCompra"] == "Obra de pavimentação asfáltica"

    def test_maps_valor_total_estimado_as_float(self):
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["valorTotalEstimado"] == 1500000.0
        assert isinstance(result["valorTotalEstimado"], float)

    def test_maps_modalidade_id_to_codigo_modalidade(self):
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["codigoModalidadeContratacao"] == 6
        assert isinstance(result["codigoModalidadeContratacao"], int)

    def test_maps_modalidade_nome(self):
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["modalidadeNome"] == "Pregão - Eletrônico"

    def test_maps_situacao_compra(self):
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["situacaoCompraId"] == "Divulgada"

    def test_maps_data_publicacao_to_data_publicacao_formatted(self):
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["dataPublicacaoFormatted"] == "2026-03-20T10:00:00Z"

    def test_maps_data_abertura(self):
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["dataAberturaProposta"] == "2026-04-01T09:00:00Z"

    def test_maps_link_pncp_to_link_sistema_origem(self):
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["linkSistemaOrigem"] == "https://pncp.gov.br/app/editais/12345678000100-1-000001/2026"

    def test_maps_esfera_id(self):
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["esferaId"] == "M"

    def test_source_tag_set_to_datalake(self):
        """Result must include _source='datalake' tag."""
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["_source"] == "datalake"

    def test_missing_optional_columns_do_not_crash(self):
        """Row missing optional columns must not raise."""
        minimal_row = {
            "pncp_id": "11111111000100-1-000001/2026",
            "uf": "AC",
        }
        result = _row_to_normalized(minimal_row)
        assert result["numeroControlePNCP"] == "11111111000100-1-000001/2026"
        assert result["uf"] == "AC"
        assert result["_source"] == "datalake"

    def test_maps_data_encerramento(self):
        """data_encerramento must be mapped to dataEncerramentoProposta."""
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["dataEncerramentoProposta"] == "2026-04-15T18:00:00Z"

    def test_maps_orgao_cnpj(self):
        """orgao_cnpj must be mapped to orgaoCnpj."""
        result = _row_to_normalized(SAMPLE_DB_ROW)
        assert result["orgaoCnpj"] == "12345678000100"

    def test_valor_string_coerced_to_float(self):
        """String valor_total_estimado (from Supabase) must be cast to float."""
        row = dict(SAMPLE_DB_ROW, valor_total_estimado="250000.50")
        result = _row_to_normalized(row)
        assert result["valorTotalEstimado"] == 250000.50
        assert isinstance(result["valorTotalEstimado"], float)

    def test_empty_pncp_id_omits_key(self):
        """When pncp_id is empty, numeroControlePNCP should not be set."""
        row = {"pncp_id": "", "uf": "SP"}
        result = _row_to_normalized(row)
        assert "numeroControlePNCP" not in result

    def test_trigram_row_with_sim_score_normalizes_cleanly(self):
        """Trigram rows include sim_score — must be ignored gracefully."""
        result = _row_to_normalized(SAMPLE_TRIGRAM_ROW)
        assert result["objetoCompra"] == SAMPLE_DB_ROW["objeto_compra"]
        assert "sim_score" not in result
