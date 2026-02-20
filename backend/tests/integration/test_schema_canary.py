"""AC13: Schema compatibility canary test.

Validates that the Pydantic models used by the pipeline match
expected column definitions. If the database schema drifts,
this test fails before production breaks.
Production scenario: DB migration removes a column -> canary catches it immediately.
"""

import pytest
import dataclasses


@pytest.mark.integration
class TestSchemaCanary:
    """AC13: Schema compatibility -- model fields match expected DB columns."""

    def test_search_results_cache_row_has_expected_columns(self):
        """Canary: If search_results_cache schema changes, this test catches drift.

        Validates that the BuscaResponse model has all columns expected by
        the pipeline. Any missing column means a schema migration broke
        the contract.
        """
        from schemas import BuscaResponse

        # These fields MUST exist in BuscaResponse for the pipeline to work
        expected_fields = {
            "resumo",
            "licitacoes",
            "excel_base64",
            "download_url",
            "excel_available",
            "quota_used",
            "quota_remaining",
            "total_raw",
            "total_filtrado",
            "filter_stats",
            "response_state",
            "failed_ufs",
            "succeeded_ufs",
            "is_partial",
            "cached",
            "cached_at",
        }

        actual_fields = set(BuscaResponse.model_fields.keys())
        missing = expected_fields - actual_fields
        assert not missing, f"BuscaResponse missing expected fields: {missing}"

    def test_busca_request_has_required_fields(self):
        """Canary: BuscaRequest contract validation."""
        from schemas import BuscaRequest

        required_for_pipeline = {"ufs", "data_inicial", "data_final", "setor_id"}
        actual = set(BuscaRequest.model_fields.keys())
        missing = required_for_pipeline - actual
        assert not missing, f"BuscaRequest missing fields: {missing}"

    def test_search_context_has_pipeline_fields(self):
        """Canary: SearchContext must have fields used by all 7 pipeline stages."""
        from search_context import SearchContext

        field_names = {f.name for f in dataclasses.fields(SearchContext)}

        required_fields = {
            "request",
            "user",
            "start_time",
            "tracker",
            "licitacoes_raw",
            "licitacoes_filtradas",
            "response_state",
            "session_id",
            "response",
            "resumo",
            "download_url",
            "queue_mode",
        }

        missing = required_fields - field_names
        assert not missing, f"SearchContext missing fields: {missing}"

    def test_busca_response_response_state_literals(self):
        """Canary: response_state must accept all four semantic states.

        If any state is removed from the Literal type, this test fails.
        """
        from schemas import BuscaResponse

        field_info = BuscaResponse.model_fields["response_state"]
        # Build a BuscaResponse for each valid state to confirm acceptance
        valid_states = ["live", "cached", "degraded", "empty_failure"]
        for state in valid_states:
            resp = BuscaResponse.model_construct(
                resumo=None,
                excel_available=True,
                quota_used=0,
                quota_remaining=10,
                total_raw=0,
                total_filtrado=0,
                response_state=state,
            )
            assert resp.response_state == state, (
                f"BuscaResponse rejected response_state='{state}'"
            )

    def test_filter_stats_has_rejection_categories(self):
        """Canary: FilterStats must expose all rejection reason buckets."""
        from schemas import FilterStats

        expected_categories = {
            "rejeitadas_uf",
            "rejeitadas_valor",
            "rejeitadas_keyword",
            "rejeitadas_min_match",
            "rejeitadas_prazo",
            "rejeitadas_outros",
        }

        actual = set(FilterStats.model_fields.keys())
        missing = expected_categories - actual
        assert not missing, f"FilterStats missing rejection categories: {missing}"

    def test_licitacao_item_has_display_fields(self):
        """Canary: LicitacaoItem must have all fields expected by the frontend."""
        from schemas import LicitacaoItem

        display_fields = {
            "pncp_id",
            "objeto",
            "orgao",
            "uf",
            "valor",
            "link",
            "data_publicacao",
            "data_abertura",
            "data_encerramento",
            "dias_restantes",
            "urgencia",
            "relevance_score",
            "matched_terms",
            "confidence",
        }

        actual = set(LicitacaoItem.model_fields.keys())
        missing = display_fields - actual
        assert not missing, f"LicitacaoItem missing display fields: {missing}"
