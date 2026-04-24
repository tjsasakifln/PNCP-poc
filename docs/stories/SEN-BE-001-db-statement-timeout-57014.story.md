# SEN-BE-001: DB statement_timeout (code 57014) cancelando queries em produção

**Status:** Ready
**Origem:** Sentry unresolved (smartlic-backend, 14d window) — issues 7403161892 (120 evt), 7409552060 (7 evt), 7398298813 (48 evt, ConnectionTerminated correlato)
**Prioridade:** P0 — Crítico (queries de preço/contratos/orgão abortam sem resposta ao usuário)
**Complexidade:** M (Medium)
**Owner:** @data-engineer + @dev
**Tipo:** Performance / Reliability

---

## Problema

PostgreSQL está cancelando queries longas via `statement_timeout` (SQLSTATE `57014` — "canceling statement due to statement timeout") em 3 rotas de produção:

1. `routes.itens_publicos.item_profile` — `price_data` query falha repetidamente (ex.: "Mesa de escritório 1,20x0,60m") — **120 eventos em 14d**
2. `routes.orgao_publico.orgao_stats` — falha com `ConnectionTerminated` (HTTP/2 stream terminado pós-timeout) — **48 eventos**
3. `contratos` DB query por sector/uf/municipio (ex.: `manutencao_predial/MA/Caxias`) — **7 eventos**

Sintomas:
- Requisições do usuário retornam erro 500 ou timeout de proxy (Railway 120s)
- Sentry registra mensagem exata: `{'message': 'canceling statement due to statement timeout', 'code': '57014'}`
- Correlação com saturação de conexões (ver SEN-BE-004 para ConnectionTerminated)

Hipóteses de causa raiz:
- Queries sem índice coberto nos filtros `sector + uf + municipio` em `supplier_contracts`
- `price_data` query em `itens_publicos` faz agregação full-scan sem particionamento
- `statement_timeout` atual no Supabase pool possivelmente <30s — não leaveshead room para agregações legítimas

---

## Critérios de Aceite

- [ ] **AC1:** Explain plan documentado em `docs/explain-plans/SEN-BE-001.md` para as 3 queries culpadas (price_data, orgao_stats, contratos by sector/uf/municipio) com `EXPLAIN (ANALYZE, BUFFERS)`
- [ ] **AC2:** Índice(s) novos criados via migration `supabase/migrations/YYYYMMDDHHMMSS_sen_be_001_stats_timeout.sql` + `.down.sql` pareado
- [ ] **AC3:** Após deploy, Sentry issue `7403161892` não recebe eventos novos por 48h consecutivas (verificar via `GET /api/0/issues/7403161892/` → `lastSeen` não avança)
- [ ] **AC4:** p95 de `/v1/itens/*/profile`, `/v1/orgao/*/stats`, `/v1/contratos/*/{uf}/stats` cai abaixo de 10s (métrica: `smartlic_request_duration_seconds_bucket`)
- [ ] **AC5:** Teste de integração `backend/tests/integration/test_stats_queries_under_load.py` valida timeout <10s em query de pior caso (big sector = "manutencao_predial" + UF grande)
- [ ] **AC6:** Se causa for `statement_timeout` muito apertado, documentar valor atual + novo em ADR curto (`docs/adr/ADR-SEN-BE-001-statement-timeout.md`)

### Anti-requisitos

- NÃO desabilitar `statement_timeout` globalmente — proteção contra runaway queries deve permanecer
- NÃO mascarar erro 57014 com `try/except: pass` — query precisa retornar rápido ou degradar com cache

---

## Referência de implementação

Arquivos prováveis:
- `backend/routes/itens_publicos.py::item_profile` (price_data query)
- `backend/routes/orgao_publico.py::orgao_stats`
- `backend/routes/contratos_publicos.py` (sector/uf/municipio filter)
- Supabase migrations: `supplier_contracts` GIN/btree indexes

Candidatos a índice:
```sql
-- Confirmar via EXPLAIN antes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_supplier_contracts_sector_uf_municipio
  ON supplier_contracts (sector_id, uf, municipio)
  WHERE is_active = true;
```

---

## Riscos

- **R1 (Alto):** Criar índice em `supplier_contracts` (~2M rows) bloqueia writes se não usar `CONCURRENTLY`. **Mitigação:** migration usa `CREATE INDEX CONCURRENTLY` + roda fora do horário de ingestion peak (2am BRT)
- **R2 (Médio):** Aumentar `statement_timeout` pode mascarar regressões futuras. **Mitigação:** manter timeout atual, fixar queries
- **R3 (Baixo):** Rotas cachê passa a servir stale data por mais tempo se trocarmos timeout por cache — documentar no ADR

## Dependências

- SEN-BE-004 (ConnectionTerminated) pode compartilhar causa raiz — investigar conjunto
- Acesso Supabase para EXPLAIN ANALYZE em produção (ou dump local)

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada a partir de Sentry scan (3 issues correlacionadas, 175 eventos combinados) |
| 2026-04-23 | @po | Validação 10/10 → **GO**. Staleness Sentry: LIVE (lastSeen 2026-04-22). Promovida Draft → Ready |
