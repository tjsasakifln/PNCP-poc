"""Tests for fuzzy deduplication in consolidation (ISSUE-027).

Verifies that the _deduplicate_fuzzy() method correctly identifies and removes
near-duplicate procurement records from the same orgão with different edital
numbers but semantically identical objects.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from consolidation import ConsolidationService
from unified_schemas.unified import UnifiedProcurement


def _make_record(
    *,
    source_id: str = "test-001",
    source_name: str = "PNCP",
    cnpj: str = "83102798000100",
    numero_edital: str = "000061",
    ano: str = "2026",
    objeto: str = "Pavimentação da rua Reinhold Schroeder",
    valor: float = 9_500_000.0,
    uf: str = "SC",
    orgao: str = "Prefeitura Municipal de Indaial",
) -> UnifiedProcurement:
    return UnifiedProcurement(
        source_id=source_id,
        source_name=source_name,
        cnpj_orgao=cnpj,
        numero_edital=numero_edital,
        ano=ano,
        objeto=objeto,
        valor_estimado=valor,
        uf=uf,
        orgao=orgao,
        data_publicacao=datetime(2026, 3, 20, 10, 0, 0),
    )


@pytest.fixture
def svc():
    """ConsolidationService with no adapters (only using dedup methods)."""
    return ConsolidationService(adapters={})


# === _tokenize_objeto tests ===


class TestTokenizeObjeto:
    def test_basic_tokenization(self):
        tokens = ConsolidationService._tokenize_objeto(
            "Pavimentação da rua Reinhold Schroeder"
        )
        assert "pavimentação" in tokens
        assert "rua" in tokens
        assert "reinhold" in tokens
        assert "schroeder" in tokens
        # Stopword removed
        assert "da" not in tokens

    def test_punctuation_removed(self):
        tokens = ConsolidationService._tokenize_objeto(
            "CONSTRUÇÃO CIVIL, VISANDO A CONSTRUÇÃO DO CAPS."
        )
        assert "construção" in tokens
        assert "civil" in tokens
        assert "caps" in tokens
        # Short tokens and stopwords removed
        assert "a" not in tokens
        assert "," not in tokens

    def test_empty_string(self):
        assert ConsolidationService._tokenize_objeto("") == frozenset()

    def test_short_tokens_excluded(self):
        tokens = ConsolidationService._tokenize_objeto("a de em um SP RJ")
        # All tokens are <= 2 chars or stopwords
        assert len(tokens) == 0


# === _jaccard tests ===


class TestJaccard:
    def test_identical(self):
        s = frozenset({"pavimentação", "rua", "reinhold"})
        assert ConsolidationService._jaccard(s, s) == 1.0

    def test_completely_different(self):
        a = frozenset({"pavimentação", "asfalto"})
        b = frozenset({"uniformes", "escolares"})
        assert ConsolidationService._jaccard(a, b) == 0.0

    def test_partial_overlap(self):
        a = frozenset({"pavimentação", "rua", "reinhold", "schroeder"})
        b = frozenset({"pavimentação", "rua", "reinhold", "schroeder", "indaial"})
        sim = ConsolidationService._jaccard(a, b)
        assert 0.7 < sim < 1.0  # 4/5 = 0.8

    def test_empty_sets(self):
        assert ConsolidationService._jaccard(frozenset(), frozenset()) == 0.0
        assert ConsolidationService._jaccard(frozenset({"a"}), frozenset()) == 0.0


# === _deduplicate_fuzzy tests ===


class TestDeduplicateFuzzy:
    def test_identical_objeto_same_cnpj_merged(self, svc):
        """Two editals from same CNPJ with identical objeto = 1 result."""
        rec_a = _make_record(source_id="a", numero_edital="000061")
        rec_b = _make_record(source_id="b", numero_edital="000059")
        result = svc._deduplicate_fuzzy([rec_a, rec_b])
        assert len(result) == 1
        assert result[0].source_id == "a"  # First one kept

    def test_different_objeto_same_cnpj_kept(self, svc):
        """Same CNPJ but different objeto = 2 results."""
        rec_a = _make_record(
            source_id="a",
            numero_edital="000061",
            objeto="Pavimentação da rua Reinhold Schroeder",
        )
        rec_b = _make_record(
            source_id="b",
            numero_edital="000069",
            objeto="Construção da Nova Escola Arapongas no Município de Indaial",
            valor=8_100_000.0,
        )
        result = svc._deduplicate_fuzzy([rec_a, rec_b])
        assert len(result) == 2

    def test_similar_objeto_very_different_valor_kept(self, svc):
        """Same objeto but very different value = different lots, keep both."""
        rec_a = _make_record(source_id="a", valor=9_500_000.0)
        rec_b = _make_record(source_id="b", numero_edital="000062", valor=1_200_000.0)
        result = svc._deduplicate_fuzzy([rec_a, rec_b])
        assert len(result) == 2  # >5% value difference = distinct lots

    def test_different_cnpj_never_merged(self, svc):
        """Identical objeto from different orgãos = always 2 results."""
        rec_a = _make_record(source_id="a", cnpj="83102798000100")
        rec_b = _make_record(source_id="b", cnpj="82892324000146")
        result = svc._deduplicate_fuzzy([rec_a, rec_b])
        assert len(result) == 2

    def test_both_valor_zero_merged(self, svc):
        """Both records have valor=0 — should still merge if objeto matches."""
        rec_a = _make_record(source_id="a", valor=0.0)
        rec_b = _make_record(source_id="b", numero_edital="000059", valor=0.0)
        result = svc._deduplicate_fuzzy([rec_a, rec_b])
        assert len(result) == 1

    def test_single_record_passthrough(self, svc):
        """Single record returns unchanged."""
        rec = _make_record()
        result = svc._deduplicate_fuzzy([rec])
        assert len(result) == 1

    def test_empty_list_passthrough(self, svc):
        result = svc._deduplicate_fuzzy([])
        assert result == []

    def test_multiple_pairs_deduped(self, svc):
        """Multiple duplicate pairs in same block all get deduped."""
        recs = [
            _make_record(source_id="pav1", numero_edital="061", objeto="Pavimentação da rua Reinhold Schroeder", valor=9_500_000),
            _make_record(source_id="pav2", numero_edital="059", objeto="Pavimentação da rua Reinhold Schroeder", valor=9_500_000),
            _make_record(source_id="esc1", numero_edital="069", objeto="Construção da Nova Escola Arapongas no Município de Indaial", valor=8_100_000),
            _make_record(source_id="esc2", numero_edital="062", objeto="Construção da Nova Escola Arapongas no Município de Indaial", valor=8_100_000),
        ]
        result = svc._deduplicate_fuzzy(recs)
        assert len(result) == 2
        ids = {r.source_id for r in result}
        assert "pav1" in ids
        assert "esc1" in ids

    def test_no_cnpj_skipped(self, svc):
        """Records without CNPJ are not blocked and pass through."""
        rec_a = _make_record(source_id="a", cnpj="")
        rec_b = _make_record(source_id="b", cnpj="")
        result = svc._deduplicate_fuzzy([rec_a, rec_b])
        assert len(result) == 2  # Can't block without CNPJ

    def test_jaccard_below_threshold_kept(self, svc):
        """Objects with Jaccard < 0.85 are kept even with same CNPJ+valor."""
        rec_a = _make_record(
            source_id="a",
            objeto="Contratação de empresa para execução de obra de pavimentação asfáltica em vias públicas",
        )
        rec_b = _make_record(
            source_id="b",
            numero_edital="059",
            objeto="Aquisição de materiais de engenharia e embarcações para a companhia de combate",
        )
        result = svc._deduplicate_fuzzy([rec_a, rec_b])
        assert len(result) == 2

    def test_valor_within_5pct_merged(self, svc):
        """Values within 5% should still merge."""
        rec_a = _make_record(source_id="a", valor=10_000_000.0)
        rec_b = _make_record(source_id="b", numero_edital="059", valor=10_400_000.0)
        # 4% difference, within 5% threshold
        result = svc._deduplicate_fuzzy([rec_a, rec_b])
        assert len(result) == 1

    def test_real_world_beta_session_012_case(self, svc):
        """Exact scenario from beta session 012: Engenharia+SC duplicates."""
        recs = [
            _make_record(
                source_id="83102798000100-1-000061/2026",
                cnpj="83102798000100",
                numero_edital="000061",
                objeto="Pavimentação da rua Reinhold Schroeder",
                valor=9_500_000.0,
            ),
            _make_record(
                source_id="83102798000100-1-000059/2026",
                cnpj="83102798000100",
                numero_edital="000059",
                objeto="Pavimentação da rua Reinhold Schroeder",
                valor=9_500_000.0,
            ),
            _make_record(
                source_id="83102798000100-1-000069/2026",
                cnpj="83102798000100",
                numero_edital="000069",
                objeto="Contratação de empresa especializada para execução da obra de construção da Nova Escola Arapongas, no Município de Indaial/SC",
                valor=8_100_000.0,
            ),
            _make_record(
                source_id="83102798000100-1-000062/2026",
                cnpj="83102798000100",
                numero_edital="000062",
                objeto="Contratação de empresa especializada para execução da obra de construção da Nova Escola Arapongas, no Município de Indaial/SC",
                valor=8_100_000.0,
            ),
            _make_record(
                source_id="83102285000107-1-000158/2026",
                cnpj="83102285000107",
                numero_edital="000158",
                objeto="Contratação de empresa especializada para construção de uma Unidade de Atenção Especializada - Policlínica, no município de Balneário Camboriú.",
                valor=20_300_000.0,
            ),
            _make_record(
                source_id="10459525000143-1-000034/2026",
                cnpj="10459525000143",
                numero_edital="000034",
                objeto="Contratação de empresa especializada para construção de uma Unidade de Atenção Especializada - Policlínica, no município de Balneário Camboriú.",
                valor=20_300_000.0,
            ),
        ]
        result = svc._deduplicate_fuzzy(recs)
        # Pair 1 (pav Reinhold): same CNPJ, same objeto, same valor → merged
        # Pair 2 (escola Arapongas): same CNPJ, same objeto, same valor → merged
        # Pair 3 (Policlínica): DIFFERENT CNPJs! → NOT merged (blocking by CNPJ)
        assert len(result) == 4
