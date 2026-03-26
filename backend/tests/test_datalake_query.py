"""Unit tests for datalake_query.py — query_datalake, _build_tsquery, _row_to_normalized."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from datalake_query import _build_tsquery, _row_to_normalized, query_datalake


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


# ---------------------------------------------------------------------------
# _build_tsquery
# ---------------------------------------------------------------------------


class TestBuildTsquery:
    """Tests for _build_tsquery()."""

    def test_returns_none_when_both_inputs_none(self):
        assert _build_tsquery(None, None) is None

    def test_returns_none_when_both_inputs_empty(self):
        assert _build_tsquery([], []) is None

    def test_returns_none_for_whitespace_only_keywords(self):
        assert _build_tsquery(["  ", " "], None) is None

    def test_single_keyword_returns_plain_token(self):
        result = _build_tsquery(["construção"], None)
        assert result == "construção"

    def test_multiple_keywords_joined_with_or(self):
        result = _build_tsquery(["construção", "obras"], None)
        assert result == "construção | obras"

    def test_single_custom_term_no_keywords(self):
        result = _build_tsquery(None, ["asfalto"])
        assert result == "asfalto"

    def test_multiple_custom_terms_joined_with_and(self):
        # Custom terms are appended to parts individually; combining logic wraps
        # the first element in parens and AND's the rest.
        # parts = ["creche", "escola"] → keyword_block="creche", extra=["escola"]
        # → "(creche) & escola"
        result = _build_tsquery(None, ["creche", "escola"])
        assert result == "(creche) & escola"

    def test_keywords_and_custom_terms_combined(self):
        result = _build_tsquery(["pavimentação"], ["asfalto"])
        assert result == "(pavimentação) & asfalto"

    def test_multiple_keywords_with_custom_term(self):
        result = _build_tsquery(["construção", "obras"], ["asfalto"])
        assert result == "(construção | obras) & asfalto"

    def test_multi_word_keyword_becomes_phrase_query(self):
        """Multi-word keywords must be joined with <-> for phrase matching."""
        result = _build_tsquery(["pré moldado"], None)
        assert result == "pré<->moldado"

    def test_multi_word_custom_term_becomes_phrase_query(self):
        result = _build_tsquery(None, ["creche municipal"])
        assert result == "creche<->municipal"

    def test_three_word_phrase(self):
        result = _build_tsquery(["pavimentação de ruas"], None)
        assert result == "pavimentação<->de<->ruas"

    def test_special_chars_stripped_from_keywords(self):
        """Characters that break tsquery must be removed."""
        result = _build_tsquery(["obras!"], None)
        assert "!" not in result

    def test_keywords_or_joined_custom_and_joined(self):
        """Keywords block OR'd; each custom term AND'd separately."""
        result = _build_tsquery(["construção", "obras"], ["asfalto", "concreto"])
        # parts = ["construção | obras", "asfalto", "concreto"]
        # → "(construção | obras) & asfalto & concreto"
        assert result is not None
        assert "construção | obras" in result
        assert "& asfalto" in result
        assert "& concreto" in result

    def test_empty_keyword_strings_filtered_out(self):
        """Empty strings in keywords list must be ignored."""
        result = _build_tsquery(["", "construção", ""], None)
        assert result == "construção"

    def test_empty_custom_term_strings_filtered_out(self):
        result = _build_tsquery(None, ["", "escola", ""])
        assert result == "escola"


# ---------------------------------------------------------------------------
# query_datalake
# ---------------------------------------------------------------------------


class TestQueryDatalake:
    """Tests for query_datalake().

    datalake_query.py imports get_supabase inside the function body with
    ``from supabase_client import get_supabase``, so we must patch it at the
    supabase_client module level (where it is defined).
    """

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
        mock_sb.rpc.return_value.execute.return_value.data = []
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

        _, rpc_params = mock_sb.rpc.call_args[0]
        assert rpc_params["p_ufs"] == ["PR", "SC"]
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

        _, rpc_params = mock_sb.rpc.call_args[0]
        assert rpc_params["p_tsquery"] == "construção | obras"

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_tsquery_none_when_no_keywords_or_custom_terms(self, mock_get_sb):
        """No keywords and no custom_terms must send p_tsquery=None."""
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
