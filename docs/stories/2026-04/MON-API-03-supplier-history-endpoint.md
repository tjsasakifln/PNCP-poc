# MON-API-03: `GET /api/v1/supplier/{cnpj}/history` (R$ 0,50–2/consulta)

**Priority:** P1
**Effort:** M (3 dias)
**Squad:** @dev + @qa
**Status:** Draft
**Epic:** [EPIC-MON-API-2026-04](EPIC-MON-API-2026-04.md)
**Sprint:** Wave 1 (depende MON-API-01 + MON-API-02)

---

## Contexto

Primeiro endpoint monetizado da Camada 4. Retorna histórico consolidado de contratos por CNPJ — útil para fintechs de crédito PME (due diligence), plataformas de compliance (KYB), ERPs (enrichment de fornecedor), sites B2B.

---

## Acceptance Criteria

### AC1: Endpoint REST

- [ ] `GET /api/v1/supplier/{cnpj}/history`
- [ ] Autenticação: `X-API-Key` obrigatório (MON-API-01)
- [ ] Query params opcionais:
  - `periodo_inicio`: date (default: 5 anos atrás)
  - `periodo_fim`: date (default: hoje)
  - `uf`: string 2 chars (filtro opcional)
  - `limit`: int (1-100, default 50)
  - `offset`: int (default 0)
  - `include_details`: bool (default true — embeddded contracts; false = só aggregates)

### AC2: Response schema

```json
{
  "cnpj": "12345678000100",
  "nome_fornecedor": "EMPRESA X LTDA",
  "period": {"inicio": "2021-04-22", "fim": "2026-04-22"},
  "aggregates": {
    "total_contratos": 127,
    "total_valor_cents": 4525000000,
    "unique_buyers": 14,
    "avg_valor_cents": 35629921,
    "min_valor_cents": 500000,
    "max_valor_cents": 1200000000,
    "first_contract_date": "2021-07-15",
    "last_contract_date": "2026-03-28"
  },
  "top_buyers": [
    {"orgao_cnpj": "...", "orgao_nome": "...", "contratos_count": 34, "valor_total_cents": 12500000000, "share_pct": 27.6},
    ...
  ],
  "sector_breakdown": [
    {"setor": "informatica", "contratos": 45, "valor_total_cents": 18000000000, "share_pct": 39.8},
    ...
  ],
  "uf_breakdown": [...],
  "modalidade_breakdown": [...],
  "contracts": [  // if include_details=true
    {"numero_controle_pncp": "...", "orgao_nome": "...", "uf": "SP", "valor_cents": 500000, "data_assinatura": "...", "objeto_resumo": "..."},
    ...
  ],
  "pagination": {"limit": 50, "offset": 0, "total": 127, "next_offset": 50},
  "generated_at": "2026-04-22T14:00:00Z",
  "cache_status": "fresh"
}
```

- [ ] Branding header em todas as responses: `X-Data-Source: SmartLic / PNCP`
- [ ] Cache-Control: `public, max-age=3600` (1h TTL)
- [ ] Cost header: `X-Cost-Cents: 100` (para transparência)

### AC3: Performance

- [ ] p95 latency < 500ms
- [ ] Usar índice composto existente `(ni_fornecedor, data_assinatura DESC)`
- [ ] Aggregates calculados em uma RPC única (`supplier_history_aggregated`)
- [ ] L1 cache Redis 5 min por `(cnpj, params_hash)`

### AC4: Validações

- [ ] CNPJ: 14 dígitos, passa validação checksum (reusa `backend/utils/cnpj.py` se existir)
- [ ] periodo_fim >= periodo_inicio
- [ ] CNPJ não encontrado → 404 com body `{error: "supplier_not_found", cnpj: "..."}`
- [ ] 0 contratos no período → 200 com aggregates zerados + array vazio

### AC5: Metered billing integration

- [ ] Cost fixo: 100 cents (R$ 1,00) por request
- [ ] Variação por volume (Stripe tier discount já configurado em MON-API-02)
- [ ] Após response: fire-and-forget `log_api_usage` via MON-API-02

### AC6: Documentação OpenAPI

- [ ] Schema Pydantic completo para request/response
- [ ] Description com exemplo de cURL + Python
- [ ] Visível em `/api/docs-public` (MON-API-05)

### AC7: Testes

- [ ] Unit: `test_supplier_history_endpoint.py`
  - Happy path: CNPJ com 10 contratos → aggregates corretos
  - Filtro UF → subset correto
  - CNPJ inválido (checksum) → 400
  - CNPJ não existe → 404
  - Paginação: limit=10 offset=20 → retorna correto
- [ ] Performance: 100 queries concorrentes p95 < 500ms
- [ ] Integration: com API key + metered billing → log_api_usage chamado

---

## Scope

**IN:**
- Endpoint + schema Pydantic
- RPC agregador
- L1 cache Redis
- Metered billing integration
- OpenAPI docs
- Testes

**OUT:**
- Full-text search em `objeto_contrato` — v2
- Webhook "novo contrato para CNPJ X" — v2
- GraphQL alternative — fora de escopo
- Export Excel/CSV pelo endpoint — usuário monta com os dados retornados

---

## Dependências

- MON-API-01 + MON-API-02 (bloqueadores)
- Dados de `pncp_supplier_contracts` (já existem)

---

## Riscos

- **CNPJ com 10k+ contratos (governo federal como fornecedor???):** limite implícito via `limit=100` + paginação; se > 1M contratos, response pode timeout → adicionar hard limit 5000 contracts
- **Privacy concerns:** dados são públicos (lei transparência) mas CNPJs podem pedir remoção por LGPD — add endpoint futuro `/supplier/{cnpj}/opt-out`

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `backend/routes/public_api/supplier_history.py` (novo)
- `backend/schemas/public_api/supplier_history.py` (novo)
- `supabase/migrations/.../create_supplier_history_rpc.sql` + `.down.sql`
- `backend/utils/cnpj.py` (criar se não existe)
- `backend/tests/routes/public_api/test_supplier_history.py` (novo)

---

## Definition of Done

- [ ] Endpoint live em prod com feature flag `ENABLE_PUBLIC_API=true`
- [ ] 3 test API keys fazendo requests bem-sucedidos
- [ ] Métricas Prometheus: `smartlic_api_supplier_history_requests_total`, `smartlic_api_supplier_history_latency_seconds`
- [ ] p95 < 500ms medido com 100 req/s
- [ ] OpenAPI visível e válido
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — primeiro endpoint monetizado da Camada 4 |
