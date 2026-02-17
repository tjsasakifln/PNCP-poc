# GTM-FIX-011: Ativar Portal de Compras Públicas como Segunda Fonte de Dados

## Dimension Impact
- Moves D01 (Data Completeness) +2 (7/10 → 9/10)
- Moves D09 (Copy Accuracy) +1 (claims de "múltiplas fontes" tornam-se verdadeiros)
- Moves D04 (Error Handling) +0.5 (duas fontes = fallback natural)

## Problem
SmartLic busca oportunidades exclusivamente no PNCP. Porém, milhares de licitações municipais são publicadas apenas no Portal de Compras Públicas (PCP). Com a obtenção da API key do PCP, temos a oportunidade de ampliar significativamente a cobertura.

## Descoberta Crítica (Squad Review 2026-02-16)

O codebase **já possui infraestrutura multi-source completa**:

- `backend/clients/base.py` — `SourceAdapter` ABC, `UnifiedProcurement` model, `SourceMetadata`, `SourceStatus`, exception hierarchy
- `backend/clients/portal_compras_client.py` — `PortalComprasAdapter` (609 linhas) implementando `SourceAdapter` com retry, rate limiting, normalization, health checks. Endpoints com TODOs/placeholders.
- `backend/consolidation.py` — `ConsolidationService` com parallel fetch, dedup por `dedup_key`, partial failure, fallback cascade, health-aware timeouts
- `backend/source_config/sources.py` — `SourceCode.PORTAL` já no enum, `SourceHealthRegistry` com `record_success()`/`record_failure()`
- `backend/pncp_client.py` — `PNCPLegacyAdapter` wrapping PNCP como `SourceAdapter`

**Esta story NÃO cria código novo.** Ela completa e ativa o que já existe.

## Solution
1. **Completar** `PortalComprasAdapter.fetch()` com endpoints reais da PCP API
2. **Implementar** `PortalComprasAdapter.normalize()` mapeando campos PCP → `UnifiedProcurement`
3. **Registrar** adapter na configuração de produção (API key + feature flag)
4. **Verificar** `ConsolidationService.fetch_all()` orquestra PNCP + PCP corretamente
5. **Adicionar** indicadores de fonte no frontend (simplificados)

## API PCP — Resumo Técnico

**Base URL:** `https://apipcp.portaldecompraspublicas.com.br`
**Teste:** `https://apipcp.wcompras.com.br`
**Auth:** `publicKey` como parâmetro na URL (env var `PCP_PUBLIC_KEY`, NUNCA hardcoded)

### Endpoints Prioritários

#### A) Processos abertos
```
GET /publico/obterprocessosabertos?publicKey={key}&dataInicio={DD/MM/AAAA}&dataFim={DD/MM/AAAA}&uf={UF}&pagina={N}
```
- Campos: `idLicitacao`, `DS_OBJETO`, `unidadeCompradora.{nomeComprador, Cidade, UF}`, `lotes[].itens[].{DS_ITEM, QT_ITENS, VL_UNITARIO_ESTIMADO}`
- Paginação: `quantidadeTotal` + cálculo (sem `temProximaPagina`)
- Valor: Somatório `VL_UNITARIO_ESTIMADO * QT_ITENS` por item

#### B) Processos recebendo propostas
```
GET /publico/obterlistaprocessosrecebendopropostas?publicKey={key}&uf={UF}
```
- Inclui `cnaes[]` — mapeia para `cnae_mapping.py`
- Filtro UF obrigatório, sem filtro de data

#### C) Lista com status
```
GET /publico/obterlistadeprocessos?publicKey={key}&cdSituacao={1-8}&dataInicio={}&dataFim={}&pagina={N}
```

### Diferenças Críticas vs PNCP

| Aspecto | PNCP | PCP |
|---------|------|-----|
| Valor | `valorTotalEstimado` (float) | Somatório `VL_UNITARIO_ESTIMADO * QT_ITENS` |
| Data format | `YYYY-MM-DD` | `DD/MM/AAAA` |
| Paginação | `temProximaPagina` flag | `quantidadeTotal` + cálculo |
| Keyword field | `objetoCompra` | `DS_OBJETO` + `DS_ITEM` (itens) |
| CNAE | Não disponível | Disponível (endpoint B) |
| ID único | `numeroControlePNCP` | `idLicitacao` (Integer) |

## Acceptance Criteria

### Backend — Completar PortalComprasAdapter

- [ ] AC1: Atualizar endpoints em `clients/portal_compras_client.py` com URLs reais da API PCP (substituir TODOs/placeholders)
- [ ] AC2: Implementar `fetch()` usando endpoint A (processos abertos) com paginação via `quantidadeTotal`
- [ ] AC3: Implementar `normalize()` mapeando campos PCP → `UnifiedProcurement` com `dedup_key` correto (CNPJ + edital, usando pattern existente de `_generate_dedup_key()`)
- [ ] AC4: Auth via `PCP_PUBLIC_KEY` env var — NUNCA hardcoded em código ou documentação
- [ ] AC5: Validar retry + rate limiting já existentes no adapter. Ajustar se necessário (iniciar conservador: 5 req/s)
- [ ] AC6: Health check retorna `SourceStatus` corretamente (verificar auth 401 = key expirada)

### Backend — Normalização de Dados

- [ ] AC7: Criar `DateParser` utility com conversão bidirecional DD/MM/AAAA ↔ YYYY-MM-DD + validação (rejeitar datas inválidas com log warning)
- [ ] AC8: Implementar `calculate_total_value(lotes)` com edge cases: NULL → skip com warning, QT_ITENS <= 0 → skip, lotes vazio → 0.0, resultado com `round(total, 2)`
- [ ] AC9: Concatenar `DS_OBJETO` + todos `DS_ITEM` dos lotes para campo `objeto` (keyword matching funciona sem alterar `filter.py`)
- [ ] AC10: ID único prefixado: `pcp_{idLicitacao}` para evitar colisão
- [ ] AC11: Link: `https://www.portaldecompraspublicas.com.br/processos/{idLicitacao}`
- [ ] AC12: Campo `source` = `"Portal"` (usando `SourceCode.PORTAL` existente)

### Backend — Orquestração (usar ConsolidationService existente)

- [ ] AC13: Verificar `ConsolidationService.fetch_all()` orquestra PNCP + PCP em paralelo corretamente
- [ ] AC14: Verificar dedup via `UnifiedProcurement._generate_dedup_key()` funciona cross-source (CNPJ + edital é superior ao hash de objeto+orgao)
- [ ] AC15: Verificar partial failure: PCP down → PNCP results normais (e vice-versa) via `ConsolidationResult.is_partial`
- [ ] AC16: Feature flag `PCP_ENABLED` (default `true`) para desabilitar sem deploy
- [ ] AC17: Monitorar discrepância de valor: se PCP e PNCP retornam mesma licitação com valores >5% diferentes, logar warning

### Frontend — Indicadores de Fonte (simplificados per UX review)

- [ ] AC18: Adicionar `sources_used: string[]` ao TypeScript type de `BuscaResponse`
- [ ] AC19: Resumo consolidado: "142 resultados (2 fontes consultadas)" — tooltip com breakdown por fonte
- [ ] AC20: Progress bar unificado: "Consultando fontes (8/54 regiões processadas)" — NÃO split PNCP vs PCP
- [ ] AC21: Partial failure: "Busca concluída | Uma fonte temporariamente indisponível (dados podem estar incompletos)" — sem mencionar nome técnico da fonte
- [ ] AC22: Source badges OCULTOS por default. Toggle "Mostrar fontes" para power users. Quando visível: ícone + cor (Database azul = PNCP, ShoppingCart verde = PCP)

### Configuração

- [ ] AC23: `PCP_PUBLIC_KEY` em `.env.example` com placeholder (sem key real)
- [ ] AC24: `PCP_PUBLIC_KEY` configurado em Railway production
- [ ] AC25: `PCP_ENABLED=true` em Railway production
- [ ] AC26: `PCP_TIMEOUT=30` e `PCP_RATE_LIMIT_RPS=5` configuráveis

### Tests

- [ ] AC27: Testes para `PortalComprasAdapter`: auth, fetch, normalize, pagination, health check (~20 testes, espelhando `test_pncp_client.py`)
- [ ] AC28: Testes para `DateParser`: DD/MM/AAAA→ISO, ISO→DD/MM/AAAA, datas inválidas, edge cases
- [ ] AC29: Testes para `calculate_total_value`: normal, NULL qty, zero qty, negative qty, empty lotes
- [ ] AC30: Testes para dedup cross-source: mesma licitação em PNCP e PCP → 1 resultado
- [ ] AC31: Testes para partial failure: PCP down → PNCP ok → resultados parciais sem erro
- [ ] AC32: Frontend: test source summary, test partial failure banner, test toggle source badges
- [ ] AC33: Integration test: mock ambas APIs → verify merged + deduped + correct source metadata

## Effort: S (1-2 days)

Reduzido de M (3-5d) porque a infraestrutura multi-source já existe. Trabalho real:
- Completar/verificar PortalComprasAdapter: 4h
- DateParser + calculate_total_value: 2h
- Wiring + config produção: 1h
- Frontend source indicators: 4h
- Testes: 4h

## Priority: P0 (Competitive advantage + validates copy claims)

## Dependencies
- GTM-FIX-005 (circuit breaker per-source) — verificar se SourceHealthRegistry existente já cobre, senão é pré-requisito

## Files to Modify
- `backend/clients/portal_compras_client.py` (completar endpoints + normalize)
- `backend/source_config/sources.py` (verificar config do PORTAL)
- `backend/config.py` (add PCP_ENABLED, PCP_TIMEOUT, PCP_RATE_LIMIT_RPS)
- `.env.example` (PCP config vars com placeholder)

## Files to Create
- `backend/utils/date_parser.py` (NEW — ~40 linhas, conversão DD/MM/AAAA ↔ YYYY-MM-DD)
- `backend/tests/test_portal_compras_client.py` (NEW — ~400 linhas, espelhando test_pncp_client.py)
- `backend/tests/test_date_parser.py` (NEW — ~60 linhas)

## Files NOT to Create (já existem)
- ~~`backend/pcp_client.py`~~ → usar `clients/portal_compras_client.py`
- ~~`backend/data_source_aggregator.py`~~ → usar `consolidation.py`
- ~~`backend/tests/test_data_source_aggregator.py`~~ → usar `test_consolidation.py`

## Architecture Decision

### Por que NÃO criar novo client/aggregator?

O codebase já implementa o pattern `SourceAdapter` + `ConsolidationService`:

```
SearchPipeline
  └─ ConsolidationService (existente)
       ├─ PNCPLegacyAdapter (existente)
       ├─ PortalComprasAdapter (existente, completar)
       ├─ ComprasGovAdapter (existente)
       └─ [futuro: LicitarAdapter, QueridoDiarioAdapter]
```

Criar um segundo aggregator (`DataSourceAggregator`) violaria o Open/Closed Principle e produziria dois layers de orquestração competindo. A `ConsolidationService` já faz: parallel fetch, dedup, partial failure, health-aware timeouts, fallback cascade.

## Security Notes
- `PCP_PUBLIC_KEY` é credential — NUNCA hardcoded, apenas env var
- Não logar a key em mensagens de erro/debug
- HTTPS exclusivamente
- Sanitizar responses antes de processar
- Health check verifica auth 401 (key expirada → alerta Sentry)

## Monitoring
- Sentry: tag `source=Portal` para erros da PCP API
- Mixpanel: `search_completed` com `sources_used` property
- Alert: PCP retorna 0 resultados por >1h → possível key expirada
- Dashboard: dedup rate (% duplicatas), coverage gap (PCP-only vs PNCP-only)

## Review History
- **2026-02-16 (criação):** Story original propunha novo `pcp_client.py` + `DataSourceAggregator`
- **2026-02-16 (squad review):** 5 agentes (architect, dev, QA, UX, data-engineer) identificaram infraestrutura multi-source existente. Story reescrita para completar `PortalComprasAdapter` + usar `ConsolidationService`. Effort reduzido de M(3-5d) para S(1-2d). UX simplificou source badges (ocultos por default).
