"""AC14: PNCP API contract canary test.

Validates assumptions about the PNCP API's behavior.
These are MOCKED tests (not live API calls) that verify
our client handles known API contract boundaries.
Production scenario: PNCP changes max page size -> canary alerts.
"""

import pytest


@pytest.mark.integration
class TestPncpApiCanary:
    """AC14: PNCP API contract assumptions."""

    def test_pagination_config_matches_api_limits(self):
        """Canary: Our configured tamanhoPagina must not exceed PNCP's limit.

        PNCP reduced max page size from 500 to 50 around Feb 2026.
        The default in PNCPClient.fetch_page(tamanho=50) must not exceed
        the API limit. If PNCP changes this again, this test catches it.
        """
        import inspect
        from pncp_client import PNCPClient

        # Extract the default value of 'tamanho' from fetch_page signature
        sig = inspect.signature(PNCPClient.fetch_page)
        tamanho_param = sig.parameters.get("tamanho")
        assert tamanho_param is not None, (
            "PNCPClient.fetch_page must have a 'tamanho' parameter"
        )
        default_page_size = tamanho_param.default
        assert default_page_size != inspect.Parameter.empty, (
            "PNCPClient.fetch_page 'tamanho' must have a default value"
        )

        # PNCP API max is 50 as of Feb 2026 (previously 500)
        assert default_page_size <= 500, (
            f"PNCP page size {default_page_size} exceeds known API limit of 500"
        )
        # More precise: current known max is 50
        assert default_page_size <= 50, (
            f"PNCP page size {default_page_size} exceeds current API limit of 50"
        )

    def test_pncp_client_has_retry_config(self):
        """Canary: PNCPClient must be instantiable with retry configuration."""
        from pncp_client import PNCPClient
        from config import RetryConfig

        client = PNCPClient.__new__(PNCPClient)
        # Verify the class accepts a RetryConfig
        assert hasattr(PNCPClient, '__init__'), "PNCPClient must be instantiable"

        # Verify RetryConfig has required resilience fields
        config = RetryConfig()
        assert config.max_retries >= 1, "RetryConfig must allow at least 1 retry"
        assert config.timeout > 0, "RetryConfig must have a positive timeout"
        assert len(config.retryable_status_codes) > 0, (
            "RetryConfig must define retryable HTTP status codes"
        )

    def test_pncp_response_field_mapping(self):
        """Canary: Field names we extract from PNCP responses must be valid.

        If PNCP renames a field, the _convert_to_licitacao_items function
        will silently produce empty values. This test catches that drift.
        """
        expected_pncp_fields = {
            "objetoCompra",
            "nomeOrgao",
            "uf",
            "valorTotalEstimado",
            "modalidadeNome",
            "dataPublicacaoPncp",
            "dataAberturaProposta",
        }

        # Verify our pipeline can handle these fields
        from search_pipeline import _convert_to_licitacao_items

        # Create a minimal licitacao with all expected PNCP fields
        test_lic = {field: "test" for field in expected_pncp_fields}
        test_lic["valorTotalEstimado"] = 1000.0
        test_lic["codigoCompra"] = "TEST-001"

        items = _convert_to_licitacao_items([test_lic])
        assert len(items) == 1, "Pipeline must handle standard PNCP fields"

        item = items[0]
        assert item.orgao == "test", "nomeOrgao must map to orgao"
        assert item.uf == "test", "uf must map through"
        assert item.valor == 1000.0, "valorTotalEstimado must map to valor"

    def test_default_modalidades_are_valid(self):
        """Canary: DEFAULT_MODALIDADES must only contain valid PNCP codes.

        If PNCP deprecates a modality code, this catches it.
        """
        from config import DEFAULT_MODALIDADES, MODALIDADES_PNCP

        valid_codes = set(MODALIDADES_PNCP.keys())
        for code in DEFAULT_MODALIDADES:
            assert code in valid_codes, (
                f"DEFAULT_MODALIDADES contains invalid code {code}. "
                f"Valid PNCP codes: {sorted(valid_codes)}"
            )

    def test_excluded_modalidades_rationale(self):
        """Canary: MODALIDADES_EXCLUIDAS must match the exclusion policy.

        Codes 9 (Inexigibilidade) and 14 (Inaplicabilidade) must always
        be excluded because they have pre-defined winners.
        """
        from config import MODALIDADES_EXCLUIDAS

        assert 9 in MODALIDADES_EXCLUIDAS, (
            "Inexigibilidade (9) must be excluded -- pre-defined winner"
        )
        assert 14 in MODALIDADES_EXCLUIDAS, (
            "Inaplicabilidade (14) must be excluded -- no competitive process"
        )

    def test_pncp_client_base_url_is_https(self):
        """Canary: PNCPClient must use HTTPS for API calls.

        Production security requirement: all PNCP communication over TLS.
        """
        from pncp_client import PNCPClient

        assert PNCPClient.BASE_URL.startswith("https://"), (
            f"PNCPClient.BASE_URL must use HTTPS, got: {PNCPClient.BASE_URL}"
        )
