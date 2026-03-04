"""
Tests for GTM-FIX-041 and GTM-FIX-042 — LLM summary and badge fixes.

GTM-FIX-041: AI summary uses search terms instead of sector name
GTM-FIX-042: Negative days badge in fallback summary
"""

from datetime import datetime, timedelta, timezone

from llm import gerar_resumo_fallback


# ─────────────────────────────────────────────────────────────────────────────
# GTM-FIX-041: Search terms in summaries
# ─────────────────────────────────────────────────────────────────────────────


def test_fallback_with_termos_busca_in_resumo_executivo():
    """AC1: termos_busca appears in resumo_executivo instead of sector_name."""
    licitacoes = [
        {"nomeOrgao": "Prefeitura de SP", "uf": "SP", "valorTotalEstimado": 150_000.0,
         "dataAberturaProposta": "2026-03-01T10:00:00"},
    ]
    resumo = gerar_resumo_fallback(licitacoes, sector_name="uniformes", termos_busca="calibração de equipamentos")

    assert "calibração de equipamentos" in resumo.resumo_executivo
    assert "uniformes" not in resumo.resumo_executivo.lower()


def test_fallback_with_termos_busca_in_insight_setorial():
    """AC1: insight_setorial uses 'Análise de' format when termos_busca present."""
    licitacoes = [{"nomeOrgao": "Órgão A", "uf": "SP", "valorTotalEstimado": 100_000.0}]
    resumo = gerar_resumo_fallback(licitacoes, sector_name="vestuário", termos_busca="calibração de equipamentos")

    assert "Análise de 'calibração de equipamentos'" in resumo.insight_setorial
    assert "Setor de" not in resumo.insight_setorial


def test_fallback_with_sector_unchanged_when_no_termos():
    """Regression: sector_name used when termos_busca is None."""
    licitacoes = [{"nomeOrgao": "Prefeitura de RJ", "uf": "RJ", "valorTotalEstimado": 200_000.0}]
    resumo = gerar_resumo_fallback(licitacoes, sector_name="Vestuário", termos_busca=None)

    assert "Vestuário" in resumo.resumo_executivo
    assert "Setor de Vestuário" in resumo.insight_setorial


def test_fallback_empty_list_with_termos_busca():
    """AC1: Empty list uses termos_busca in insight."""
    resumo = gerar_resumo_fallback([], sector_name="uniformes", termos_busca="filtração de ar")

    assert resumo.total_oportunidades == 0
    assert "filtração de ar" in resumo.insight_setorial


def test_fallback_empty_list_with_sector_only():
    """Regression: Empty list with no termos uses sector_name."""
    resumo = gerar_resumo_fallback([], sector_name="Software e Sistemas", termos_busca=None)

    assert resumo.total_oportunidades == 0
    assert "Software e Sistemas" in resumo.insight_setorial


# ─────────────────────────────────────────────────────────────────────────────
# GTM-FIX-042: No negative days in alerts
# ─────────────────────────────────────────────────────────────────────────────


def test_fallback_no_alert_for_expired_bids():
    """AC3: Expired bids (dias_restantes < 0) should NOT generate urgency alerts."""
    data_expirada = (datetime.now(timezone.utc) - timedelta(days=21)).isoformat()
    licitacoes = [
        {"nomeOrgao": "Prefeitura Expirada", "uf": "SP", "valorTotalEstimado": 100_000.0,
         "dataAberturaProposta": data_expirada},
    ]
    resumo = gerar_resumo_fallback(licitacoes)

    assert resumo.alerta_urgencia is None
    assert len(resumo.alertas_urgencia) == 0


def test_fallback_alert_for_urgent_bids():
    """Regression: Bids expiring in < 3 days should still get urgency alerts."""
    data_urgente = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    licitacoes = [
        {"nomeOrgao": "Prefeitura Urgente", "uf": "MG", "valorTotalEstimado": 200_000.0,
         "dataAberturaProposta": data_urgente},
    ]
    resumo = gerar_resumo_fallback(licitacoes)

    assert resumo.alerta_urgencia is not None
    assert "Prefeitura Urgente" in resumo.alerta_urgencia
    assert "encerra em" in resumo.alerta_urgencia


def test_fallback_mixed_expired_and_urgent():
    """Only urgent bids should generate alerts, not expired ones."""
    data_expirada = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    data_urgente = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    licitacoes = [
        {"nomeOrgao": "Órgão Expirado", "uf": "SP", "valorTotalEstimado": 100_000.0,
         "dataAberturaProposta": data_expirada},
        {"nomeOrgao": "Órgão Urgente", "uf": "RJ", "valorTotalEstimado": 150_000.0,
         "dataAberturaProposta": data_urgente},
    ]
    resumo = gerar_resumo_fallback(licitacoes)

    assert len(resumo.alertas_urgencia) == 1
    assert "Órgão Urgente" in resumo.alertas_urgencia[0]
    assert "Órgão Expirado" not in resumo.alertas_urgencia[0]


def test_fallback_expired_bid_urgencia_baixa():
    """Expired bids should get urgencia='baixa' in recommendations."""
    data_expirada = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    licitacoes = [
        {"nomeOrgao": "Órgão Alto Valor", "uf": "SP", "valorTotalEstimado": 500_000.0,
         "dataAberturaProposta": data_expirada, "objetoCompra": "Contratação X"},
    ]
    resumo = gerar_resumo_fallback(licitacoes)

    for rec in resumo.recomendacoes:
        if "Órgão Alto Valor" in rec.oportunidade:
            assert rec.urgencia == "baixa"


# ─────────────────────────────────────────────────────────────────────────────
# Integration: Both fixes combined
# ─────────────────────────────────────────────────────────────────────────────


def test_fallback_termos_with_expired_bids():
    """Combined: termos_busca + expired bids → terms in summary, no alerts."""
    data_expirada = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    licitacoes = [
        {"nomeOrgao": "Órgão Antigo", "uf": "RS", "valorTotalEstimado": 100_000.0,
         "dataAberturaProposta": data_expirada},
    ]
    resumo = gerar_resumo_fallback(licitacoes, sector_name="Energia", termos_busca="painéis solares")

    assert "painéis solares" in resumo.resumo_executivo
    assert len(resumo.alertas_urgencia) == 0
    assert resumo.alerta_urgencia is None
