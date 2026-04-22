# MON-API-04: `GET /api/v1/benchmark/price` (R$ 1–5/consulta)

**Priority:** P1
**Effort:** M (3 dias)
**Squad:** @dev + @qa
**Status:** Draft
**Epic:** [EPIC-MON-API-2026-04](EPIC-MON-API-2026-04.md)
**Sprint:** Wave 1 (depende MON-API-01 + MON-API-02 + MON-SCH-02)

---

## Contexto

Segundo endpoint monetizado. Retorna distribuição estatística de preço para CATMAT/CATSER + UF + período. Persona: ERPs de compras públicas, sistemas de orçamentação, fintechs com engine de credit scoring que considera preço-alvo.

**Preço mais alto que MON-API-03** (R$ 1–5 vs R$ 0,50–2) porque agregação é computationally expensive + valor percebido maior (é insight, não dado bruto).

---

## Acceptance Criteria

### AC1: Endpoint REST

- [ ] `GET /api/v1/benchmark/price`
- [ ] Query params:
  - `catmat_catser`: string (obrigatório)
  - `uf`: string 2 chars (opcional; default "all")
  - `periodo_meses`: int 3|6|12|24|36 (default 12)
  - `modalidade`: int (opcional; filtra por modalidade PNCP)
  - `esfera`: char F|E|M|D (opcional; Federal/Estadual/Municipal/Distrital)

### AC2: Response schema

```json
{
  "catmat_catser": "150015",
  "catmat_catser_label": "Papel sulfite A4 75g",
  "catmat_catser_tipo": "M",
  "filters": {"uf": "SP", "periodo_meses": 12, "modalidade": null, "esfera": null},
  "period": {"inicio": "2025-04-22", "fim": "2026-04-22"},
  "sample_size": 1247,
  "statistics": {
    "media_cents": 2500,
    "mediana_cents": 2200,
    "p10_cents": 1500,
    "p25_cents": 1900,
    "p50_cents": 2200,
    "p75_cents": 2800,
    "p90_cents": 3500,
    "stddev_cents": 650,
    "coef_variacao": 0.26
  },
  "per_uf": [
    {"uf": "SP", "n": 340, "mediana_cents": 2100, "media_cents": 2450},
    ...
  ],
  "per_modalidade": [
    {"modalidade": 6, "modalidade_label": "Pregão Eletrônico", "n": 892, "mediana_cents": 2150},
    ...
  ],
  "outliers": {
    "above_p95": [{"numero_controle_pncp": "...", "valor_cents": 8500, "desvio_pct": 285.0}, ...],  // top 5
    "below_p05": [...]
  },
  "generated_at": "2026-04-22T14:00:00Z",
  "data_coverage_pct": 87.3  // % dos contratos com CATMAT populado
}
```

### AC3: Uso do RPC MON-SCH-02

- [ ] Consumir `benchmark_by_catmat(catmat, uf, periodo_dias)` criado em MON-SCH-02
- [ ] Cache L1 Redis 1h por `(catmat, uf, periodo, modalidade, esfera)`
- [ ] Se `sample_size < 20` → 404 com mensagem "Amostra insuficiente — tente período maior ou sem filtro UF"

### AC4: Rate limiting mais restritivo

- [ ] Cost: 200 cents (R$ 2,00) por request (mais caro que history)
- [ ] Rate limit: 30 req/min por API key (vs 60 do history) — aggregation é mais pesada

### AC5: Validações

- [ ] `catmat_catser` deve existir em `catmat_catser_catalog` senão 404
- [ ] UF válida (27 + "all")
- [ ] periodo_meses ∈ {3,6,12,24,36}
- [ ] modalidade ∈ {4,5,6,7,8,12}

### AC6: Observability

- [ ] Prometheus: `smartlic_api_benchmark_requests_total{catmat_prefix}`, `smartlic_api_benchmark_coverage_pct`
- [ ] Sentry alert se `data_coverage_pct < 70%` por 3 dias consecutivos para CATMAT popular (sinal de degradação MON-SCH-02)

### AC7: Testes

- [ ] Unit: teste de stats matemática (dados conhecidos → percentis corretos)
- [ ] Integration: mock RPC benchmark + assert response correto
- [ ] Performance: p95 < 300ms (menos dados que history, pode ser mais rápido)
- [ ] Edge: CATMAT com < 20 contratos → 404

---

## Scope

**IN:**
- Endpoint + schema
- Consumo RPC MON-SCH-02
- Cache L1
- Prometheus metrics
- Testes

**OUT:**
- Previsão de preço futuro — v2 (usa MON-AI-03 Radar Preditivo)
- Alerta quando meu preço-alvo está fora do range — add-on separado
- Outliers extremos com explicação LLM — v2

---

## Dependências

- MON-API-01 + MON-API-02
- **MON-SCH-02 (CATMAT/CATSER)** — bloqueador absoluto

---

## Riscos

- **Low coverage em CATMATs raros:** ok para niche query; response vem com `data_coverage_pct` transparente
- **Gaming: usuário tenta monitorar preço via polling frequente:** rate limit 30/min mitiga; considerar subscription-based alerts como upsell (MON-SUB-*)

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `backend/routes/public_api/benchmark_price.py` (novo)
- `backend/schemas/public_api/benchmark_price.py` (novo)
- `backend/tests/routes/public_api/test_benchmark_price.py` (novo)

---

## Definition of Done

- [ ] Endpoint live + 100+ requests bem-sucedidos em staging
- [ ] Cache hit rate > 60% após warmup
- [ ] p95 < 300ms
- [ ] Coverage average > 80% para CATMATs populares
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — segundo endpoint monetizado Camada 4; depende MON-SCH-02 |
