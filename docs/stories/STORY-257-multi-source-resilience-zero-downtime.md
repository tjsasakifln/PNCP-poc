# STORY-257: Multi-Source Resilience — Zero-Downtime Search When External APIs Fail

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-257 |
| **Priority** | P0 (GTM-critical) |
| **Sprint** | Sprint 2 |
| **Estimate** | 8h |
| **Depends on** | STORY-252 (multi-source foundation) |
| **Blocks** | GTM launch readiness |

## Problema

Em 2026-02-14 (validacao STORY-249 AC9), todas as fontes de dados falharam simultaneamente:

1. **PNCP API**: Health canary retornou HTTP 400 -> circuit breaker ativado em modo `degraded` por 300s -> **0 resultados**
2. **COMPRAS_GOV**: HTTP 503 "Service Unavailable" apos 2 retries (1.3s + 5.6s) -> **falha total apos 15s**
3. **Portal de Compras**: Habilitado mas `PORTAL_COMPRAS_API_KEY` nao configurada -> **inoperante**
4. **Licitar Digital**: Habilitado mas `LICITAR_API_KEY` nao configurada -> **inoperante**

**Resultado para o usuario**: Mensagem "Nenhuma fonte de dados respondeu" apos ~15s de espera. Busca completamente indisponivel.

### Logs relevantes (Railway 2026-02-14T23:54)
```
Using sector: Saude (268 keywords)              <- sector_id correto propagado
Multi-source fetch enabled, using ConsolidationService
Enabled sources: ['PNCP', 'Portal', 'Licitar', 'ComprasGov']
WARNING: Portal de Compras enabled but PORTAL_COMPRAS_API_KEY not set
WARNING: Licitar Digital enabled but LICITAR_API_KEY not set
PNCP health canary: unexpected status 400
PNCP circuit breaker set to degraded for 300s
PNCP health canary failed - returning empty results
[COMPRAS_GOV] Server error 503. Retrying in 1.3s
[COMPRAS_GOV] Server error 503. Retrying in 5.6s
[CONSOLIDATION] COMPRAS_GOV: error after 15097ms
All sources failed -> "Nenhuma fonte de dados respondeu"
```

### Impacto
- Qualquer indisponibilidade simultanea do PNCP + COMPRAS_GOV (as unicas 2 fontes com credentials) causa **blackout total**
- Portal e Licitar estao habilitados na config mas sem API keys -> contam como "fontes" no log mas nunca retornam dados
- O `is_available()` em `sources.py:236` retorna `True` sempre, mesmo sem credentials -> fontes fantasmas

### Audit de fragilidades (codebase scan 2026-02-14)

| # | Severidade | Arquivo | Linha(s) | Problema |
|---|-----------|---------|----------|----------|
| 1 | **HIGH** | `pncp_client.py` | 797-798 | Race condition: health canary seta `degraded_until` e `consecutive_failures` sem o `asyncio.Lock` do circuit breaker |
| 2 | **HIGH** | `consolidation.py` | 481-487 | Resource leak: `_fallback_adapter` (ComprasGov) nunca tem `close()` chamado — HTTP client leaks |
| 3 | **MEDIUM** | `sources.py` | 236 | `is_available()` retorna `True` sempre, mesmo sem credentials |
| 4 | **MEDIUM** | `pncp_client.py` | 86-96 | `is_degraded` property tem side-effects (reset state) sem lock |
| 5 | **MEDIUM** | `pncp_client.py` | 777 | Health canary nao distingue 400 (bad params) de 500 (server error) |
| 6 | **MEDIUM** | `search_pipeline.py` | 527-529 | Novo `ComprasGovAdapter` criado como fallback a cada request (rate-limit state nao compartilhado) |
| 7 | **MEDIUM** | `redis_pool.py` | 170-171 | Redis permanentemente desabilitado apos 1 falha de conexao no startup |
| 8 | **LOW** | `sources.py` | 97 | Health status reseta para "healthy" apos 5min fixo sem backoff |
| 9 | **LOW** | `consolidation.py` | 182 | Resultados non-dict do gather silenciosamente descartados (sem log) |
| 10 | **LOW** | `search_pipeline.py` | 518-522 | Portal silenciosamente excluido quando key ausente; SSE progress so reporta PNCP |
| 11 | **LOW** | `redis_pool.py` | 92-94 | `exists()` refresh LRU position via side-effect de `get()` |

### Analise do frontend (audit 2026-02-14)

| Area | Estado atual | Gap |
|------|-------------|-----|
| Retry automatico | 1 retry para 503 apenas (useSearch.ts:242) | Nao retenta 500, 502, network errors |
| Proxy retry | 2 tentativas para 503/conn (route.ts:70) | 502 explicitamente excluido |
| Cache de resultados | **Nenhum** (so sessionStorage para redirect auth) | Zero stale-while-revalidate |
| Mensagens de erro | 6 estados distintos via DegradationBanner | Mensagens usam ASCII-only (sem acentos) |
| Retry manual | Botao "Tentar novamente" em error e all-down | Sem delay progressivo |

---

## Solucao

### Track 1: Habilitar fontes pendentes — Portal de Compras e Licitar Digital (2h)

**Problema**: 2 de 4 fontes estao habilitadas mas sem API keys configuradas. Em vez de descartar, precisamos ativa-las.

- [ ] **AC1:** Investigar processo de obtencao de API key do Portal de Compras Publicas (`apipcp.portaldecompraspublicas.com.br`). Documentar em `docs/guides/multi-source-credentials.md`: URL de cadastro, tipo de credencial (API key, OAuth, CNPJ+token), tempo de aprovacao, limites de rate, formato de request.
- [ ] **AC2:** Investigar processo de obtencao de API key do Licitar Digital (`api.licitar.digital/v1`). Documentar no mesmo guia: processo de cadastro, pricing (free tier?), limites, autenticacao.
- [ ] **AC3:** Configurar `PORTAL_COMPRAS_API_KEY` no Railway (env var) quando credencial obtida. Verificar com uma request de teste via `curl` ou script.
- [ ] **AC4:** Configurar `LICITAR_API_KEY` no Railway quando credencial obtida. Verificar com request de teste.
- [ ] **AC5:** `sources.py:236` — `is_available()` deve retornar `False` quando `enabled=True` mas credentials ausentes. Log de startup deve distinguir: `Portal: enabled=True, available=False (missing API key)` vs `Portal: enabled=True, available=True`.
- [ ] **AC6:** Health endpoint `/sources/health` deve reportar status `pending_credentials` (nao `disabled` nem `healthy`) para fontes habilitadas sem key — sinalizando que a intencao e ativa-las.
- [ ] **AC7:** `search_pipeline.py` — fontes com `is_available()=False` nao devem ser passadas ao `ConsolidationService`, evitando tentativa de request que vai falhar e timeout desnecessario.

### Track 2: Circuit breaker PNCP — corrigir canary e race conditions (2h)

**Problema**: Health canary com params invalidos retorna 400, que e tratado como "API down". Race condition no circuit breaker.

- [ ] **AC8:** Health canary: distinguir HTTP 4xx (client error — canary malformado) de HTTP 5xx (server error). Apenas 5xx, timeout, ou connection refused devem ativar degraded mode.
- [ ] **AC9:** HTTP 400 no health canary: logar `WARN canary_client_error` mas **prosseguir com busca normal** (sem circuit breaker). Incluir no log o body da resposta 400 para diagnostico.
- [ ] **AC10:** Revisar parametros do health canary (`pncp_client.py:744-770`). A query atual usa `dataInicial=dataFinal=hoje` com `codigoModalidadeContratacao=6`. Validar se esses parametros sao aceitos pelo PNCP. Se 400 for esperado, ajustar para parametros sabidamente validos (ex: data range de 7 dias, sem filtro de modalidade).
- [ ] **AC11:** **Fix race condition** (`pncp_client.py:797-798`): health canary DEVE usar o `asyncio.Lock` do circuit breaker ao mutar `degraded_until` e `consecutive_failures`. Usar `record_failure()` em vez de mutacao direta.
- [ ] **AC12:** **Fix `is_degraded` side-effects** (`pncp_client.py:86-96`): a property que reseta `degraded_until` e `consecutive_failures` deve adquirir o lock antes de mutar estado. Alternativa: separar check (`is_degraded`) de mutacao (`try_recover()`).

### Track 3: Cache de resultados para resiliencia (2h)

**Problema**: Quando todas as fontes caem, o usuario ve zero resultados mesmo que a mesma busca tenha retornado dados horas atras. Nao existe cache de resultados no frontend nem no backend.

- [ ] **AC13:** Backend: implementar cache de resultados de busca usando `InMemoryCache` (ja existente em `redis_pool.py`).
  - Cache key: SHA-256 de `json.dumps(sorted({setor_id, ufs, data_inicial, data_final, status, modalidades, modo_busca}))`.
  - Valor: JSON serializado de `{licitacoes, resumo, total, timestamp}`.
  - TTL: 2 horas via `setex()` (licitacoes abertas mudam lentamente; 2h e conservador).
  - **Limite**: apenas cachear resultados com `total > 0` (nao cachear resultados vazios).
- [ ] **AC14:** Quando **todas as fontes falham** (`AllSourcesFailedError`), tentar cache hit antes de retornar erro. Se cache hit: retornar resultados com flags `cached: true`, `cached_at: ISO timestamp` no response JSON.
- [ ] **AC15:** Quando busca retorna dados frescos com sucesso, atualizar o cache (write-through).
- [ ] **AC16:** **Fix resource leak** (`consolidation.py:481-487`): metodo `close()` deve tambem fechar `self._fallback_adapter` se existir.
- [ ] **AC17:** **Fix silently dropped results** (`consolidation.py:182`): quando `asyncio.gather` retorna resultado non-dict (exception nao capturada por `_wrap_source`), logar warning com detalhes em vez de silenciosamente ignorar.

### Track 4: Frontend — retry inteligente e exibicao de cache (1h)

**Problema**: Frontend so retenta 503 (1x). Nao ha cache de resultados. Mensagens sem acentos.

- [ ] **AC18:** `useSearch.ts`: expandir retry automatico para incluir 500 e 502 (alem de 503). Max 2 retries com delay progressivo: 3s, 8s.
- [ ] **AC19:** Quando response contem `cached: true`, exibir `DegradationBanner` variant="warning" com mensagem: "Fontes de dados temporariamente indisponíveis. Mostrando resultados de [cached_at formatado]. Dados podem estar desatualizados."
- [ ] **AC20:** Botao "Atualizar dados" no banner de cache que forca nova busca (ignora cache no request: `?force_fresh=true`).
- [ ] **AC21:** Corrigir mensagens ASCII-only no `DegradationBanner.tsx` e `SearchResults.tsx` — usar acentos corretos em portugues ("estão indisponíveis", nao "estao indisponiveis").

### Track 5: Observabilidade e alertas (1h)

**Problema**: Sem metricas de uptime por fonte, nao sabemos a frequencia dos blackouts.

- [ ] **AC22:** Adicionar log estruturado no final de cada busca com: `{sources_attempted, sources_succeeded, sources_failed, cache_hit, total_results, latency_ms}`. Formato JSON para parsing em Railway/Sentry.
- [ ] **AC23:** Quando todas as fontes falham, emitir evento Sentry `source_blackout` com severity=error, incluindo: fontes tentadas, erros por fonte, se cache foi usado.
- [ ] **AC24:** Health endpoint `/sources/health` deve incluir `last_success_at` e `consecutive_failures` por fonte, para monitoramento externo.

---

## Arquivos a Modificar

| Arquivo | Track | Mudancas |
|---------|-------|---------|
| `backend/source_config/sources.py` | T1 | AC5-AC7: `is_available()` fix, health status `pending_credentials` |
| `backend/pncp_client.py` | T2 | AC8-AC12: canary 4xx vs 5xx, race condition fix, `is_degraded` lock |
| `backend/search_pipeline.py` | T1,T3 | AC7: skip unavailable sources; AC13-AC15: cache layer |
| `backend/consolidation.py` | T3 | AC16: close fallback adapter; AC17: log non-dict results |
| `backend/redis_pool.py` | T3 | AC13: verificar InMemoryCache adequacao para cache de resultados |
| `frontend/app/buscar/hooks/useSearch.ts` | T4 | AC18: retry 500/502; AC20: force_fresh param |
| `frontend/app/buscar/components/SearchResults.tsx` | T4 | AC19: banner de cache |
| `frontend/app/buscar/components/DegradationBanner.tsx` | T4 | AC21: acentos corretos |
| `docs/guides/multi-source-credentials.md` | T1 | AC1-AC2: guia de obtencao de API keys |

---

## Testes

### Backend
- [ ] **T1:** Unit: `is_available()` retorna `False` quando enabled=True mas sem API key.
- [ ] **T2:** Unit: health canary 400 nao ativa circuit breaker; 500 ativa.
- [ ] **T3:** Unit: circuit breaker `record_failure()` e thread-safe (usa Lock).
- [ ] **T4:** Unit: cache hit quando `AllSourcesFailedError` — retorna dados com `cached=True`.
- [ ] **T5:** Unit: cache miss + `AllSourcesFailedError` — retorna erro humanizado.
- [ ] **T6:** Unit: cache write-through em busca bem-sucedida.
- [ ] **T7:** Unit: `consolidation.close()` fecha fallback adapter.
- [ ] **T8:** Unit: resultados non-dict do gather sao logados (nao silenciados).
- [ ] **T9:** Integration: busca com PNCP health canary 400 ainda retorna resultados (canary ignorado).
- [ ] **T10:** Integration: busca com todas as fontes down + cache hit retorna dados cacheados.

### Frontend
- [ ] **T11:** Jest: retry automatico em 500 e 502 (mock fetch).
- [ ] **T12:** Jest: banner de cache visivel quando response contem `cached: true`.
- [ ] **T13:** Jest: botao "Atualizar dados" envia `force_fresh=true`.
- [ ] **T14:** Visual: mensagens com acentos corretos (snapshot test).

---

## Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|--------------|---------|-----------|
| Portal/Licitar nao oferecem free tier ou exigem CNPJ juridico | Media | Reduz cobertura multi-source | AC1-AC2 documentam alternativas. Se nao viavel, desabilitar explicitamente com `ENABLE_SOURCE_PORTAL=false` |
| Cache de 2h serve dados muito desatualizados | Baixa | Usuario ve licitacao ja encerrada | TTL conservador (2h) + banner explicito + botao "Atualizar dados" |
| Race condition fix no circuit breaker introduz deadlock | Baixa | Busca trava | Lock com timeout de 1s; fallthrough para state anterior se timeout |
| InMemoryCache perde dados no redeploy | Certa | Cache cold start | Aceitavel para v1. Redis futuro resolve. Cache se reconstroi organicamente com buscas dos usuarios |

## Dependencias externas

| Dependencia | Owner | Status | Bloqueante? |
|-------------|-------|--------|-------------|
| API key Portal de Compras | Tiago (cadastro) | Pendente | Nao (AC3 so apos obtencao) |
| API key Licitar Digital | Tiago (cadastro) | Pendente | Nao (AC4 so apos obtencao) |
| PNCP API disponivel para teste | Governo Federal | Intermitente | Nao (circuit breaker fix e independente) |

## Definition of Done
- Todos os ACs checked
- `pytest` sem regressoes (baseline: 21 pre-existing)
- `npm test` sem regressoes (baseline: 70 pre-existing)
- TypeScript clean (`npx tsc --noEmit`)
- Busca funcional mesmo com PNCP + COMPRAS_GOV simultaneamente down (via cache)
- Race conditions eliminadas no circuit breaker (Lock em todas as mutacoes)
- Resource leak do fallback adapter corrigido
- Mensagens de erro humanizadas com acentos corretos
- Guia de credenciais documentado para Portal e Licitar
