"""CRIT-054: PCP v2 status mapping tests.

Tests cover:
- AC1: PCP v2 status values mapped correctly to internal enum
- AC2: Unknown PCP v2 status → desconhecido (pass-through, not rejected)
- AC3: Date-based heuristics for PCP v2
- AC4: Filter passes through desconhecido PCP v2 records
- AC5: Integration scenarios (PNCP down + PCP v2 only)
- AC6: Metrics emitted for unmapped status
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from status_inference import (
    PCP_V2_STATUS_MAP,
    _inferir_status_pcp_v2,
    inferir_status_licitacao,
    enriquecer_com_status_inferido,
)


# ============================================================================
# AC1: PCP v2 status mapping
# ============================================================================


class TestPcpV2StatusMapping:
    """AC1: Verify all known PCP v2 status values are mapped correctly."""

    @pytest.mark.parametrize(
        "pcp_status,expected",
        [
            ("aberto", "recebendo_proposta"),
            ("sessão pública iniciada", "recebendo_proposta"),
            ("sessao publica iniciada", "recebendo_proposta"),
            ("recebendo propostas", "recebendo_proposta"),
            ("em disputa", "recebendo_proposta"),
            ("em lances", "recebendo_proposta"),
            ("período de propostas", "recebendo_proposta"),
            ("periodo de propostas", "recebendo_proposta"),
        ],
    )
    def test_open_statuses_map_to_recebendo_proposta(self, pcp_status, expected):
        """PCP v2 open/active statuses → recebendo_proposta."""
        lic = {"_source": "PORTAL_COMPRAS", "situacaoCompraNome": pcp_status}
        assert inferir_status_licitacao(lic) == expected

    @pytest.mark.parametrize(
        "pcp_status,expected",
        [
            ("encerrado", "em_julgamento"),
            ("sessão encerrada", "em_julgamento"),
            ("sessao encerrada", "em_julgamento"),
            ("em análise", "em_julgamento"),
            ("em analise", "em_julgamento"),
            ("em julgamento", "em_julgamento"),
            ("classificação", "em_julgamento"),
            ("classificacao", "em_julgamento"),
            ("habilitação", "em_julgamento"),
            ("habilitacao", "em_julgamento"),
            ("negociação", "em_julgamento"),
            ("negociacao", "em_julgamento"),
        ],
    )
    def test_closed_session_maps_to_em_julgamento(self, pcp_status, expected):
        """PCP v2 'Encerrado' means session closed (em_julgamento), NOT finalized."""
        lic = {"_source": "PORTAL_COMPRAS", "situacaoCompraNome": pcp_status}
        assert inferir_status_licitacao(lic) == expected

    @pytest.mark.parametrize(
        "pcp_status,expected",
        [
            ("homologado", "encerrada"),
            ("adjudicado", "encerrada"),
            ("anulado", "encerrada"),
            ("revogado", "encerrada"),
            ("fracassado", "encerrada"),
            ("deserto", "encerrada"),
            ("cancelado", "encerrada"),
            ("suspenso", "encerrada"),
        ],
    )
    def test_finalized_statuses_map_to_encerrada(self, pcp_status, expected):
        """PCP v2 finalized statuses → encerrada."""
        lic = {"_source": "PORTAL_COMPRAS", "situacaoCompraNome": pcp_status}
        assert inferir_status_licitacao(lic) == expected

    def test_case_insensitive_matching(self):
        """Status mapping is case-insensitive (lowercase comparison)."""
        lic = {"_source": "PORTAL_COMPRAS", "situacaoCompraNome": "Sessão Pública Iniciada"}
        assert inferir_status_licitacao(lic) == "recebendo_proposta"

    def test_pncp_records_unaffected(self):
        """PNCP records (no _source or _source=PNCP) use original inference."""
        lic_no_source = {"situacaoCompraNome": "Aberta"}
        assert inferir_status_licitacao(lic_no_source) == "recebendo_proposta"

        lic_pncp = {"_source": "PNCP", "situacaoCompraNome": "Aberta"}
        assert inferir_status_licitacao(lic_pncp) == "recebendo_proposta"

    def test_pncp_encerrada_still_works(self):
        """PNCP 'Encerrada' still maps to encerrada (original behavior)."""
        lic = {"situacaoCompraNome": "encerrada"}
        assert inferir_status_licitacao(lic) == "encerrada"

    def test_pcp_encerrado_is_em_julgamento_not_encerrada(self):
        """KEY BUG FIX: PCP 'Encerrado' is em_julgamento, NOT encerrada."""
        lic = {"_source": "PORTAL_COMPRAS", "situacaoCompraNome": "Encerrado"}
        result = inferir_status_licitacao(lic)
        assert result == "em_julgamento", (
            f"PCP 'Encerrado' should be em_julgamento (session ended, not finalized), "
            f"got '{result}'"
        )


# ============================================================================
# AC2: Unknown status → desconhecido (pass-through)
# ============================================================================


class TestPcpV2UnknownStatus:
    """AC2: Unknown PCP v2 status treated as desconhecido (not rejected)."""

    def test_unknown_status_returns_desconhecido(self):
        """Unmapped PCP v2 status → desconhecido."""
        lic = {"_source": "PORTAL_COMPRAS", "situacaoCompraNome": "Status Inventado XYZ"}
        assert inferir_status_licitacao(lic) == "desconhecido"

    def test_empty_status_with_no_dates_returns_desconhecido(self):
        """PCP v2 with empty status and no dates → desconhecido."""
        lic = {"_source": "PORTAL_COMPRAS", "situacaoCompraNome": ""}
        assert inferir_status_licitacao(lic) == "desconhecido"

    def test_none_status_returns_desconhecido(self):
        """PCP v2 with None status fields → desconhecido."""
        lic = {"_source": "PORTAL_COMPRAS"}
        assert inferir_status_licitacao(lic) == "desconhecido"


# ============================================================================
# AC3: Date-based heuristics for PCP v2
# ============================================================================


class TestPcpV2DateHeuristics:
    """AC3: Date-based status inference for PCP v2 with unmapped status."""

    def test_future_deadline_is_recebendo_proposta(self):
        """PCP v2 with unmapped status + future deadline → recebendo_proposta."""
        future = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        lic = {
            "_source": "PORTAL_COMPRAS",
            "situacaoCompraNome": "Status Desconhecido",
            "dataEncerramentoProposta": future,
        }
        assert inferir_status_licitacao(lic) == "recebendo_proposta"

    def test_past_deadline_is_em_julgamento(self):
        """PCP v2 with unmapped status + past deadline → em_julgamento."""
        past = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        lic = {
            "_source": "PORTAL_COMPRAS",
            "situacaoCompraNome": "Status Desconhecido",
            "dataEncerramentoProposta": past,
        }
        assert inferir_status_licitacao(lic) == "em_julgamento"

    def test_mapped_status_takes_priority_over_dates(self):
        """Mapped status has priority over date heuristics."""
        future = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        lic = {
            "_source": "PORTAL_COMPRAS",
            "situacaoCompraNome": "Encerrado",  # Maps to em_julgamento
            "dataEncerramentoProposta": future,  # Date says recebendo
        }
        # Mapped status wins
        assert inferir_status_licitacao(lic) == "em_julgamento"

    def test_no_dates_no_mapping_is_desconhecido(self):
        """No dates + unmapped status → desconhecido."""
        lic = {
            "_source": "PORTAL_COMPRAS",
            "situacaoCompraNome": "Novo Status 2027",
        }
        assert inferir_status_licitacao(lic) == "desconhecido"

    def test_invalid_date_falls_to_desconhecido(self):
        """Invalid date format → falls through to desconhecido."""
        lic = {
            "_source": "PORTAL_COMPRAS",
            "situacaoCompraNome": "Status Desconhecido",
            "dataEncerramentoProposta": "NOT_A_DATE",
        }
        assert inferir_status_licitacao(lic) == "desconhecido"


# ============================================================================
# AC4: Filter passes through desconhecido PCP v2 records
# ============================================================================


class TestFilterPassthroughPcpV2:
    """AC4: Status filter tolerates PCP v2 desconhecido records.

    Uses filtrar_por_status() directly to isolate status filter behavior
    from keyword/value/etc filters.
    """

    def _make_pcp_bid(self, status_inferido, source_id="pcp_123"):
        """Create a PCP v2 bid dict."""
        return {
            "objetoCompra": "Fornecimento de materiais",
            "uf": "SP",
            "_source": "PORTAL_COMPRAS",
            "_status_inferido": status_inferido,
        }

    def _make_pncp_bid(self, status_inferido, source_id="pncp_456"):
        """Create a PNCP bid dict."""
        return {
            "objetoCompra": "Serviço de limpeza",
            "uf": "SP",
            "_source": "PNCP",
            "_status_inferido": status_inferido,
        }

    def test_desconhecido_pcp_passes_status_filter(self):
        """PCP v2 bid with desconhecido status passes through status filter.

        Tests the core status filter logic in aplicar_todos_filtros (Etapa 2).
        """
        from filter import aplicar_todos_filtros

        bids = [self._make_pcp_bid("desconhecido")]
        # Use aplicar_todos_filtros with status="todos" first to verify no status rejection
        # Then test with recebendo_proposta to verify pass-through
        _, stats_todos = aplicar_todos_filtros(bids, ufs_selecionadas={"SP"}, status="todos")
        assert stats_todos["rejeitadas_status"] == 0, "status=todos should not reject"

        bids2 = [self._make_pcp_bid("desconhecido")]
        _, stats_filter = aplicar_todos_filtros(bids2, ufs_selecionadas={"SP"}, status="recebendo_proposta")
        assert stats_filter["rejeitadas_status"] == 0, (
            f"PCP v2 desconhecido should pass through status filter, got rejected: {stats_filter}"
        )
        assert bids2[0].get("_status_unconfirmed") is True

    def test_todos_pcp_passes_status_filter(self):
        """PCP v2 bid with 'todos' inferred status passes through."""
        from filter import aplicar_todos_filtros

        bids = [self._make_pcp_bid("todos")]
        _, stats = aplicar_todos_filtros(bids, ufs_selecionadas={"SP"}, status="recebendo_proposta")
        assert stats["rejeitadas_status"] == 0

    def test_pncp_todos_still_rejected(self):
        """PNCP bid with 'todos' status is rejected (no pass-through for PNCP)."""
        from filter import aplicar_todos_filtros

        bids = [self._make_pncp_bid("todos")]
        _, stats = aplicar_todos_filtros(bids, ufs_selecionadas={"SP"}, status="recebendo_proposta")
        assert stats["rejeitadas_status"] >= 1

    def test_correctly_mapped_pcp_passes_normally(self):
        """PCP v2 bid with correctly mapped status passes normal filter."""
        from filter import aplicar_todos_filtros

        bids = [self._make_pcp_bid("recebendo_proposta")]
        _, stats = aplicar_todos_filtros(bids, ufs_selecionadas={"SP"}, status="recebendo_proposta")
        assert stats["rejeitadas_status"] == 0
        # No _status_unconfirmed flag for correctly mapped records
        assert bids[0].get("_status_unconfirmed") is None

    def test_mismatched_pcp_still_rejected(self):
        """PCP v2 bid with wrong mapped status is still rejected."""
        from filter import aplicar_todos_filtros

        bids = [self._make_pcp_bid("encerrada")]
        _, stats = aplicar_todos_filtros(bids, ufs_selecionadas={"SP"}, status="recebendo_proposta")
        assert stats["rejeitadas_status"] >= 1


# ============================================================================
# AC5: Integration — enriquecer_com_status_inferido with PCP v2
# ============================================================================


class TestEnrichmentPcpV2Integration:
    """AC5: Status enrichment works correctly for mixed PNCP + PCP v2 records."""

    def test_enrichment_dispatches_by_source(self):
        """enriquecer_com_status_inferido uses PCP v2 logic for PCP records."""
        future = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        lics = [
            # PCP v2 record with "Encerrado" (should be em_julgamento, not encerrada)
            {
                "_source": "PORTAL_COMPRAS",
                "situacaoCompraNome": "Encerrado",
                "dataEncerramentoProposta": future,
            },
            # PNCP record with future deadline (should be recebendo_proposta via dates)
            {
                "_source": "PNCP",
                "dataAberturaProposta": (
                    datetime.now(timezone.utc) - timedelta(days=1)
                ).isoformat(),
                "dataEncerramentoProposta": future,
            },
        ]

        enriquecer_com_status_inferido(lics)

        # PCP v2 "Encerrado" → em_julgamento (mapped, not date-based)
        assert lics[0]["_status_inferido"] == "em_julgamento"
        # PNCP with future deadline → recebendo_proposta
        assert lics[1]["_status_inferido"] == "recebendo_proposta"

    def test_pcp_sessao_publica_iniciada_not_rejected(self):
        """Real PCP v2 sample: 'Sessão Pública Iniciada' should be recebendo_proposta."""
        lic = {
            "_source": "PORTAL_COMPRAS",
            "situacaoCompraNome": "Sessão Pública Iniciada",
        }
        enriquecer_com_status_inferido([lic])
        assert lic["_status_inferido"] == "recebendo_proposta"

    def test_91_percent_rejection_scenario_fixed(self):
        """Reproduce the CRIT-054 bug: 95/104 PCP v2 records rejected.

        Before fix: PCP 'Encerrado' → encerrada → rejected by recebendo_proposta filter.
        After fix: PCP 'Encerrado' → em_julgamento → still rejected, BUT 'Aberto'/
        'Sessão Pública Iniciada' → recebendo_proposta → PASSES filter.

        Tests status filter only (using aplicar_todos_filtros with status="recebendo_proposta").
        Keyword rejections are separate; this test verifies status pass-through.
        """
        future = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

        # Simulate 104 PCP records with realistic status distribution
        lics = []
        # 40 "Aberto" — should pass recebendo_proposta filter
        for i in range(40):
            lics.append({
                "_source": "PORTAL_COMPRAS",
                "situacaoCompraNome": "Aberto",
                "dataEncerramentoProposta": future,
                "uf": "SP",
                "objetoCompra": f"Item {i}",
            })
        # 30 "Sessão Pública Iniciada" — should pass
        for i in range(40, 70):
            lics.append({
                "_source": "PORTAL_COMPRAS",
                "situacaoCompraNome": "Sessão Pública Iniciada",
                "dataEncerramentoProposta": future,
                "uf": "SP",
                "objetoCompra": f"Item {i}",
            })
        # 25 "Encerrado" — should be em_julgamento (rejected by recebendo filter, correct)
        past = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        for i in range(70, 95):
            lics.append({
                "_source": "PORTAL_COMPRAS",
                "situacaoCompraNome": "Encerrado",
                "dataEncerramentoProposta": past,
                "uf": "SP",
                "objetoCompra": f"Item {i}",
            })
        # 9 "Unknown Status" — should pass through as desconhecido
        for i in range(95, 104):
            lics.append({
                "_source": "PORTAL_COMPRAS",
                "situacaoCompraNome": "Novo Status 2027",
                "uf": "SP",
                "objetoCompra": f"Item {i}",
            })

        enriquecer_com_status_inferido(lics)

        # Verify status inference distribution
        status_dist = {}
        for lic in lics:
            s = lic["_status_inferido"]
            status_dist[s] = status_dist.get(s, 0) + 1

        # 40 Aberto + 30 Sessão Pública = 70 recebendo_proposta
        assert status_dist.get("recebendo_proposta", 0) == 70
        # 25 Encerrado = 25 em_julgamento
        assert status_dist.get("em_julgamento", 0) == 25
        # 9 Unknown = 9 desconhecido
        assert status_dist.get("desconhecido", 0) == 9

        from filter import aplicar_todos_filtros

        _, stats = aplicar_todos_filtros(
            lics,
            ufs_selecionadas={"SP"},
            status="recebendo_proposta",
        )

        # Status rejections: only the 25 "Encerrado" (em_julgamento) should be rejected
        assert stats["rejeitadas_status"] == 25, (
            f"Expected 25 status rejections (Encerrado→em_julgamento), "
            f"got {stats['rejeitadas_status']}"
        )
        # 70 recebendo + 9 desconhecido (pass-through) = 79 pass status filter
        # (they may still be rejected by keyword filter downstream, that's OK)


# ============================================================================
# AC6: Metrics
# ============================================================================


class TestPcpV2Metrics:
    """AC6: Verify metrics are emitted for unmapped status."""

    def test_unmapped_status_increments_counter(self):
        """PCP_STATUS_UNMAPPED_TOTAL incremented for unknown status."""
        with patch("metrics.PCP_STATUS_UNMAPPED_TOTAL") as mock_counter:
            lic = {"_source": "PORTAL_COMPRAS", "situacaoCompraNome": "Inventado"}
            result = inferir_status_licitacao(lic)
            assert result == "desconhecido"
            mock_counter.inc.assert_called_once()

    def test_mapped_status_does_not_increment_counter(self):
        """PCP_STATUS_UNMAPPED_TOTAL NOT incremented for mapped status."""
        with patch("metrics.PCP_STATUS_UNMAPPED_TOTAL") as mock_counter:
            lic = {"_source": "PORTAL_COMPRAS", "situacaoCompraNome": "Aberto"}
            result = inferir_status_licitacao(lic)
            assert result == "recebendo_proposta"
            mock_counter.inc.assert_not_called()


# ============================================================================
# Regression: Existing PNCP inference not broken
# ============================================================================


class TestPncpRegressions:
    """Verify existing PNCP inference is unaffected by CRIT-054 changes."""

    def test_pncp_homologacao_still_encerrada(self):
        lic = {"valorTotalHomologado": 100000.0}
        assert inferir_status_licitacao(lic) == "encerrada"

    def test_pncp_propostas_encerradas_still_em_julgamento(self):
        lic = {"situacaoCompraNome": "Propostas encerradas"}
        assert inferir_status_licitacao(lic) == "em_julgamento"

    def test_pncp_divulgada_still_todos(self):
        lic = {"situacaoCompraNome": "Divulgada no PNCP"}
        assert inferir_status_licitacao(lic) == "todos"

    def test_pncp_date_inference_unchanged(self):
        future = (datetime.now() + timedelta(days=7)).isoformat()
        past = (datetime.now() - timedelta(days=1)).isoformat()
        lic = {
            "dataAberturaProposta": past,
            "dataEncerramentoProposta": future,
        }
        assert inferir_status_licitacao(lic) == "recebendo_proposta"

    def test_pncp_empty_fallback_unchanged(self):
        lic = {}
        assert inferir_status_licitacao(lic) == "todos"
