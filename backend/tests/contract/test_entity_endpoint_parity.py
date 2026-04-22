"""CRIT-DATA-PARITY-001 — Entity endpoint parity contract tests (skeleton).

Caso-farol: CRIT-SEO-011 descobriu que `/v1/municipios/sao-paulo-sp/profile`
retorna 500 editais enquanto `/v1/blog/stats/cidade/sao-paulo` retorna 0 —
o mesmo município, mesmo dataset, endpoints diferentes. Essa suite valida
que pares de endpoints que agregam o mesmo atributo retornem valores
dentro de 5% de drift.

Este é o Sprint 2 skeleton (3 pairs piloto: SP, RJ, BH). Sprints futuros
expandem para órgãos, fornecedores, setores×UF.

Policy:
- Skipped quando ``PARITY_TARGET_URL`` não está setado (roda local-only
  se operador quiser).
- CI nightly executa via workflow dedicado — advisory, não bloqueante.
- Failure aqui indica drift real em produção → abrir issue P0 manualmente.
"""
from __future__ import annotations

import os

import httpx
import pytest

pytestmark = [pytest.mark.parity]

TARGET_URL = os.environ.get("PARITY_TARGET_URL")
DRIFT_TOLERANCE = 0.05  # 5% — absorve janelas de tempo ligeiramente diferentes

# Cidades piloto: SP (maior volume), RJ (2o maior), BH (controle regional).
# Sem acentos no slug — caso-farol do CRIT-SEO-011 já está resolvido pelo fix
# aplicado em get_cidade_stats(), este teste garante que a paridade se mantém.
PILOT_CITIES = [
    {"slug_profile": "sao-paulo-sp", "slug_blog": "sao-paulo"},
    {"slug_profile": "rio-de-janeiro-rj", "slug_blog": "rio-de-janeiro"},
    {"slug_profile": "belo-horizonte-mg", "slug_blog": "belo-horizonte"},
]


pytestmark.append(
    pytest.mark.skipif(
        not TARGET_URL,
        reason="PARITY_TARGET_URL not set — skeleton only runs against live target",
    )
)


def _drift_pct(a: float, b: float) -> float:
    """Relative drift: |a - b| / max(|a|, |b|, 1). Returns 0.0..1.0."""
    denom = max(abs(a), abs(b), 1)
    return abs(a - b) / denom


def _fetch_json(path: str) -> dict:
    """Fetch JSON from target. Raises on non-2xx."""
    with httpx.Client(base_url=TARGET_URL, timeout=30.0) as client:
        r = client.get(path)
        r.raise_for_status()
        return r.json()


@pytest.mark.parametrize("city", PILOT_CITIES, ids=lambda c: c["slug_blog"])
def test_municipio_profile_vs_blog_stats_cidade_total_editais(city: dict) -> None:
    """Pair: /v1/municipios/{slug}/profile ↔ /v1/blog/stats/cidade/{cidade}.

    Atributos comparados:
      - total_licitacoes_abertas (profile) vs total_editais (blog stats)

    Ambos agregam `pncp_raw_bids` + `is_active=true` + últimas janelas
    similares. Devem estar dentro de 5% de drift.
    """
    profile = _fetch_json(f"/v1/municipios/{city['slug_profile']}/profile")
    blog_stats = _fetch_json(f"/v1/blog/stats/cidade/{city['slug_blog']}")

    total_profile = float(profile.get("total_licitacoes_abertas") or 0)
    total_blog = float(blog_stats.get("total_editais") or 0)

    # Se ambos são 0, paridade trivial — mas levantamos sinal para investigação
    # manual (municípios piloto têm volume conhecido; 0/0 em produção indica
    # outro bug, ex.: datalake vazio).
    if total_profile == 0 and total_blog == 0:
        pytest.skip(
            f"{city['slug_blog']}: ambos endpoints retornam 0 — suspeita de "
            "datalake vazio ou janela fria; investigar manualmente"
        )

    drift = _drift_pct(total_profile, total_blog)
    assert drift <= DRIFT_TOLERANCE, (
        f"CRIT-DATA-PARITY-001 DRIFT — {city['slug_blog']}: "
        f"profile.total_licitacoes_abertas={total_profile} vs "
        f"blog_stats.total_editais={total_blog} → drift={drift:.1%} "
        f"(threshold {DRIFT_TOLERANCE:.0%})"
    )


@pytest.mark.parametrize("city", PILOT_CITIES, ids=lambda c: c["slug_blog"])
def test_municipio_profile_vs_blog_stats_cidade_avg_value(city: dict) -> None:
    """Pair avg_value: profile.valor_medio_licitacoes vs blog_stats.avg_value.

    Tolerância de 5% absorve pequenas diferenças de arredondamento ou
    inclusão de outliers; drift maior indica filtros divergentes.
    """
    profile = _fetch_json(f"/v1/municipios/{city['slug_profile']}/profile")
    blog_stats = _fetch_json(f"/v1/blog/stats/cidade/{city['slug_blog']}")

    avg_profile = float(profile.get("valor_medio_licitacoes") or 0)
    avg_blog = float(blog_stats.get("avg_value") or 0)

    if avg_profile == 0 and avg_blog == 0:
        pytest.skip(f"{city['slug_blog']}: avg_value=0 em ambos — datalake vazio?")

    drift = _drift_pct(avg_profile, avg_blog)
    assert drift <= DRIFT_TOLERANCE, (
        f"CRIT-DATA-PARITY-001 DRIFT — {city['slug_blog']} avg_value: "
        f"profile={avg_profile:.2f} vs blog_stats={avg_blog:.2f} → "
        f"drift={drift:.1%} (threshold {DRIFT_TOLERANCE:.0%})"
    )
