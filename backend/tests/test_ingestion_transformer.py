"""Unit tests for ingestion/transformer.py — compute_content_hash, transform_pncp_item, transform_batch."""

import hashlib
import logging

import pytest

from ingestion.transformer import (
    compute_content_hash,
    transform_batch,
    transform_pncp_item,
)

# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

SAMPLE_PNCP_ITEM = {
    "numeroControlePNCP": "12345678000100-1-000001/2026",
    "objetoCompra": "Contratação de empresa para execução de obra de pavimentação asfáltica",
    "valorTotalEstimado": 1500000.00,
    "modalidadeId": 6,
    "modalidadeNome": "Pregão - Eletrônico",
    "situacaoCompraNome": "Divulgada",
    "dataPublicacaoPncp": "2026-03-20T10:00:00Z",
    "dataAberturaProposta": "2026-04-01T09:00:00Z",
    "dataEncerramentoProposta": "2026-04-01T18:00:00Z",
    "linkSistemaOrigem": "https://compras.gov.br/edital/12345",
    "orgaoEntidade": {
        "razaoSocial": "Prefeitura Municipal de São Paulo",
        "cnpj": "12345678000100",
        "esferaId": "M",
    },
    "unidadeOrgao": {
        "ufSigla": "SP",
        "municipioNome": "São Paulo",
        "codigoMunicipioIbge": "3550308",
        "nomeUnidade": "Secretaria de Infraestrutura",
    },
}


# ---------------------------------------------------------------------------
# compute_content_hash
# ---------------------------------------------------------------------------


class TestComputeContentHash:
    """Tests for compute_content_hash()."""

    def test_same_input_produces_same_hash(self):
        """Identical dicts must produce the same SHA-256 hex digest."""
        h1 = compute_content_hash(SAMPLE_PNCP_ITEM)
        h2 = compute_content_hash(SAMPLE_PNCP_ITEM)
        assert h1 == h2

    def test_returns_valid_sha256_hex(self):
        """Result must be a 64-character lowercase hex string."""
        h = compute_content_hash(SAMPLE_PNCP_ITEM)
        assert isinstance(h, str)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_different_valor_produces_different_hash(self):
        """Changing valorTotalEstimado must change the hash."""
        modified = dict(SAMPLE_PNCP_ITEM, valorTotalEstimado=999.99)
        h_original = compute_content_hash(SAMPLE_PNCP_ITEM)
        h_modified = compute_content_hash(modified)
        assert h_original != h_modified

    def test_different_objeto_produces_different_hash(self):
        """Changing objetoCompra must change the hash."""
        modified = dict(SAMPLE_PNCP_ITEM, objetoCompra="Serviço de limpeza urbana")
        assert compute_content_hash(SAMPLE_PNCP_ITEM) != compute_content_hash(modified)

    def test_different_situacao_produces_different_hash(self):
        """Changing situacaoCompraNome must change the hash."""
        modified = dict(SAMPLE_PNCP_ITEM, situacaoCompraNome="Encerrada")
        assert compute_content_hash(SAMPLE_PNCP_ITEM) != compute_content_hash(modified)

    def test_none_objeto_handled(self):
        """None objetoCompra must not raise — treated as empty string."""
        item = dict(SAMPLE_PNCP_ITEM, objetoCompra=None)
        h = compute_content_hash(item)
        assert isinstance(h, str) and len(h) == 64

    def test_none_valor_handled(self):
        """None valorTotalEstimado must not raise."""
        item = dict(SAMPLE_PNCP_ITEM, valorTotalEstimado=None)
        h = compute_content_hash(item)
        assert isinstance(h, str) and len(h) == 64

    def test_none_situacao_falls_back_to_situacaoCompra(self):
        """When situacaoCompraNome is absent, situacaoCompra is used instead."""
        item = {k: v for k, v in SAMPLE_PNCP_ITEM.items() if k != "situacaoCompraNome"}
        item["situacaoCompra"] = "Divulgada"
        # Hash should match SAMPLE_PNCP_ITEM because the canonical value is the same
        assert compute_content_hash(item) == compute_content_hash(SAMPLE_PNCP_ITEM)

    def test_all_none_fields_returns_hash_of_empty_canonical(self):
        """All None fields must produce a deterministic hash (not crash)."""
        empty = {}
        canonical = "||"
        expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        assert compute_content_hash(empty) == expected

    def test_case_insensitive_objeto(self):
        """Hash must be case-insensitive on objetoCompra."""
        lower = dict(SAMPLE_PNCP_ITEM, objetoCompra="pavimentação asfáltica")
        upper = dict(SAMPLE_PNCP_ITEM, objetoCompra="PAVIMENTAÇÃO ASFÁLTICA")
        assert compute_content_hash(lower) == compute_content_hash(upper)

    def test_strips_whitespace_objeto(self):
        """Leading/trailing whitespace in objetoCompra must be ignored."""
        spaced = dict(SAMPLE_PNCP_ITEM, objetoCompra="  pavimentação  ")
        trimmed = dict(SAMPLE_PNCP_ITEM, objetoCompra="pavimentação")
        assert compute_content_hash(spaced) == compute_content_hash(trimmed)


# ---------------------------------------------------------------------------
# transform_pncp_item
# ---------------------------------------------------------------------------


class TestTransformPncpItem:
    """Tests for transform_pncp_item()."""

    def test_all_fields_mapped_correctly(self):
        """All expected columns must be present and correctly mapped."""
        row = transform_pncp_item(SAMPLE_PNCP_ITEM)

        assert row["pncp_id"] == "12345678000100-1-000001/2026"
        assert row["objeto_compra"] == (
            "Contratação de empresa para execução de obra de pavimentação asfáltica"
        )
        assert row["valor_total_estimado"] == 1500000.00
        assert row["modalidade_id"] == 6
        assert row["modalidade_nome"] == "Pregão - Eletrônico"
        assert row["situacao_compra"] == "Divulgada"
        assert row["esfera_id"] == "M"
        assert row["uf"] == "SP"
        assert row["municipio"] == "São Paulo"
        assert row["codigo_municipio_ibge"] == "3550308"
        assert row["orgao_razao_social"] == "Prefeitura Municipal de São Paulo"
        assert row["orgao_cnpj"] == "12345678000100"
        assert row["unidade_nome"] == "Secretaria de Infraestrutura"
        assert row["data_publicacao"] == "2026-03-20T10:00:00Z"
        assert row["data_abertura"] == "2026-04-01T09:00:00Z"
        assert row["data_encerramento"] == "2026-04-01T18:00:00Z"
        assert row["link_sistema_origem"] == "https://compras.gov.br/edital/12345"
        assert row["source"] == "pncp"
        assert row["crawl_batch_id"] is None
        assert "content_hash" in row
        assert "raw_payload" in row

    def test_link_pncp_constructed_correctly(self):
        """link_pncp must be built from the pncp_id using the expected base URL."""
        row = transform_pncp_item(SAMPLE_PNCP_ITEM)
        expected = "https://pncp.gov.br/app/editais/12345678000100-1-000001/2026"
        assert row["link_pncp"] == expected

    def test_custom_source_tag(self):
        """source parameter must be passed through to the row."""
        row = transform_pncp_item(SAMPLE_PNCP_ITEM, source="comprasgov")
        assert row["source"] == "comprasgov"

    def test_crawl_batch_id_passed_through(self):
        """crawl_batch_id keyword argument must appear in the row."""
        row = transform_pncp_item(SAMPLE_PNCP_ITEM, crawl_batch_id="batch_20260325")
        assert row["crawl_batch_id"] == "batch_20260325"

    def test_missing_pncp_id_raises_value_error(self):
        """Item without numeroControlePNCP must raise ValueError."""
        item = {k: v for k, v in SAMPLE_PNCP_ITEM.items() if k != "numeroControlePNCP"}
        with pytest.raises(ValueError, match="numeroControlePNCP"):
            transform_pncp_item(item)

    def test_empty_pncp_id_raises_value_error(self):
        """Item with empty numeroControlePNCP must raise ValueError."""
        item = dict(SAMPLE_PNCP_ITEM, numeroControlePNCP="   ")
        with pytest.raises(ValueError):
            transform_pncp_item(item)

    def test_missing_optional_orgao_does_not_crash(self):
        """Item without orgaoEntidade must not raise."""
        item = {k: v for k, v in SAMPLE_PNCP_ITEM.items() if k != "orgaoEntidade"}
        row = transform_pncp_item(item)
        assert row["orgao_cnpj"] == ""
        assert row["esfera_id"] is None

    def test_missing_optional_unidade_does_not_crash(self):
        """Item without unidadeOrgao must not raise."""
        item = {k: v for k, v in SAMPLE_PNCP_ITEM.items() if k != "unidadeOrgao"}
        row = transform_pncp_item(item)
        assert row["uf"] == ""
        assert row["municipio"] == ""
        assert row["codigo_municipio_ibge"] == ""

    def test_missing_optional_dates_are_none(self):
        """Missing optional date fields must not crash.

        STORY-2.12 AC4 (2026-04-14): data_abertura now falls back to
        data_publicacao when dataAberturaProposta is absent, so the bid is
        still indexable. data_encerramento stays None (meaningful: 'open
        indefinitely' for p_modo='abertas').
        """
        item = {
            k: v
            for k, v in SAMPLE_PNCP_ITEM.items()
            if k not in ("dataAberturaProposta", "dataEncerramentoProposta")
        }
        row = transform_pncp_item(item)
        # STORY-2.12 AC4: data_abertura now defaults to data_publicacao
        assert row["data_abertura"] == row["data_publicacao"]
        assert row["data_encerramento"] is None

    def test_modalidade_falls_back_to_codigo_field(self):
        """modalidadeId absent → codigoModalidadeContratacao is used as fallback."""
        item = {k: v for k, v in SAMPLE_PNCP_ITEM.items() if k != "modalidadeId"}
        item["codigoModalidadeContratacao"] = 5
        row = transform_pncp_item(item)
        assert row["modalidade_id"] == 5

    def test_situacao_falls_back_to_situacao_compra_field(self):
        """situacaoCompraNome absent → situacaoCompra is used as fallback."""
        item = {k: v for k, v in SAMPLE_PNCP_ITEM.items() if k != "situacaoCompraNome"}
        item["situacaoCompra"] = "Encerrada"
        row = transform_pncp_item(item)
        assert row["situacao_compra"] == "Encerrada"

    def test_raw_payload_preserved(self):
        """raw_payload must be the original item dict."""
        row = transform_pncp_item(SAMPLE_PNCP_ITEM)
        assert row["raw_payload"] is SAMPLE_PNCP_ITEM

    def test_content_hash_is_valid_sha256(self):
        """content_hash must be a 64-char hex string."""
        row = transform_pncp_item(SAMPLE_PNCP_ITEM)
        assert isinstance(row["content_hash"], str)
        assert len(row["content_hash"]) == 64

    def test_uf_falls_back_to_top_level_field(self):
        """uf read from top-level field when unidadeOrgao.ufSigla is absent."""
        item = dict(SAMPLE_PNCP_ITEM)
        item["unidadeOrgao"] = {}
        item["uf"] = "MG"
        row = transform_pncp_item(item)
        assert row["uf"] == "MG"

    def test_orgao_razao_social_falls_back_to_unidade_nome(self):
        """When orgao.razaoSocial is absent, unidade.nomeUnidade is used."""
        item = dict(SAMPLE_PNCP_ITEM)
        item["orgaoEntidade"] = {"cnpj": "99999999000100"}
        row = transform_pncp_item(item)
        assert row["orgao_razao_social"] == "Secretaria de Infraestrutura"


# ---------------------------------------------------------------------------
# transform_batch
# ---------------------------------------------------------------------------


class TestTransformBatch:
    """Tests for transform_batch()."""

    def test_empty_list_returns_empty_list(self):
        assert transform_batch([]) == []

    def test_all_valid_items_transformed(self):
        """All valid items must appear in the result."""
        item2 = dict(SAMPLE_PNCP_ITEM, numeroControlePNCP="99999999000100-1-000002/2026")
        result = transform_batch([SAMPLE_PNCP_ITEM, item2])
        assert len(result) == 2
        assert result[0]["pncp_id"] == "12345678000100-1-000001/2026"
        assert result[1]["pncp_id"] == "99999999000100-1-000002/2026"

    def test_invalid_item_skipped_with_warning(self, caplog):
        """Items missing numeroControlePNCP must be skipped and a warning logged."""
        invalid = {"objetoCompra": "Serviço de limpeza", "valorTotalEstimado": 100.0}
        with caplog.at_level(logging.WARNING, logger="ingestion.transformer"):
            result = transform_batch([invalid, SAMPLE_PNCP_ITEM])
        assert len(result) == 1
        assert result[0]["pncp_id"] == "12345678000100-1-000001/2026"
        assert any("skipping" in msg.lower() for msg in caplog.messages)

    def test_all_invalid_returns_empty_list(self, caplog):
        """All invalid items must return empty list without raising."""
        items = [{"objetoCompra": "X"}, {"valorTotalEstimado": 0}]
        with caplog.at_level(logging.WARNING, logger="ingestion.transformer"):
            result = transform_batch(items)
        assert result == []

    def test_source_propagated(self):
        """source kwarg must be forwarded to each transformed row."""
        result = transform_batch([SAMPLE_PNCP_ITEM], source="portal")
        assert result[0]["source"] == "portal"

    def test_crawl_batch_id_propagated(self):
        """crawl_batch_id kwarg must be forwarded to each transformed row."""
        result = transform_batch([SAMPLE_PNCP_ITEM], crawl_batch_id="run_abc")
        assert result[0]["crawl_batch_id"] == "run_abc"

    def test_skipped_count_logged_at_info(self, caplog):
        """When items are skipped an info message with totals must be logged."""
        valid = SAMPLE_PNCP_ITEM
        invalid = {"nope": "nope"}
        with caplog.at_level(logging.INFO, logger="ingestion.transformer"):
            transform_batch([valid, invalid])
        combined = " ".join(caplog.messages)
        assert "transformed" in combined or "skipped" in combined

    def test_exception_in_middle_does_not_stop_processing(self):
        """A bad item in the middle must not prevent processing subsequent items."""
        item_a = SAMPLE_PNCP_ITEM
        item_bad = {}
        item_c = dict(SAMPLE_PNCP_ITEM, numeroControlePNCP="33333333000100-1-000003/2026")
        result = transform_batch([item_a, item_bad, item_c])
        pncp_ids = [r["pncp_id"] for r in result]
        assert "12345678000100-1-000001/2026" in pncp_ids
        assert "33333333000100-1-000003/2026" in pncp_ids
        assert len(result) == 2
