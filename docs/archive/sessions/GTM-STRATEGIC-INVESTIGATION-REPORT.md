# GTM Strategic Investigation Report — "Entrega Contínua de Valor"

**Data**: 2026-02-18
**Squad**: 6 agentes paralelos (Architect, Data Engineer, UX Expert, Analyst, DevOps, Architect-Infra)
**Objetivo**: Mapear estado atual do sistema em 6 frentes para criar stories que viabilizem o GTM com confiança.
**Escopo**: Investigação apenas. Nenhuma implementação.

---

## Sumário Executivo

O sistema SmartLic/BidIQ possui uma base técnica **sólida mas incompleta** para a visão de "entrega contínua de valor sob qualquer condição". A investigação de 6 frentes revelou:

- **Pipeline**: 3-tier fallback funcional, mas timeout e empty-response gaps existem
- **Cache**: Arquitetura 3-level (Supabase→Redis→Local) madura, mas sem refresh proativo ou prioridade
- **Frontend**: UX de erro excelente, mas copy degrada percepção de valor ("2 fontes")
- **Classificação**: Pipeline 4-camadas sofisticado, mas sem inspeção item/lote e sem output estruturado do LLM
- **Logging**: 252+ logger calls geram 70-120 linhas/busca, excedendo Railway limits em 3-6x
- **Infra**: Circuit breakers funcionais mas per-worker (sem Redis), sem job queue

### Critério de Produção Proposto

> "Em caso de falha parcial ou total das dependências, o sistema ainda entrega algo útil e compreensível para o usuário? Se não, não está pronto."

---

## FRENTE 1: Pipeline de Busca & Resiliência

### Estado Atual
- Pipeline em 7 estágios: Validate → Prepare → Execute → Filter → Enrich → Generate → Persist
- **Totalmente async** com SSE real-time progress
- 3-tier fallback: Fresh cache (0-6h) → Live fetch → Stale cache (6-24h)
- Multi-source: PNCP + PCP + ComprasGov (consolidation.py)
- Dedup por `cnpj:edital:ano`, prioridade PNCP > ComprasGov > PCP

### Gaps Críticos

| ID | Gap | Arquivo | Linha | Impacto |
|----|-----|---------|-------|---------|
| P-01 | **Timeout não tenta cache** — HTTP 504 retornado sem consultar stale cache | search_pipeline.py | L805-817 | Usuário vê erro quando cache poderia servir |
| P-02 | **Resposta vazia tratada como sucesso** — HTTP 200 com `licitacoes: []` quando all sources fail + no cache | search_pipeline.py | L1300+ | Usuário recebe tela vazia sem orientação |
| P-03 | **SSE não sinaliza degradação** — "complete" emitido mesmo servindo stale cache | progress.py | L143-151 | Frontend não sabe distinguir live vs cached |
| P-04 | **Local file cache (L3) nunca lido** — write funciona, read orphaned | search_pipeline.py | — | 3rd fallback inutilizado |
| P-05 | **Sem circuit breaker para PCP/ComprasGov** — falhas silenciosas sem health tracking | consolidation.py | L238-241 | Sem degradação escalável por fonte |
| P-06 | **Pipeline síncrono para o usuário** — `pipeline.run()` bloqueia até conclusão | routes/search.py | L193 | Sem resposta parcial antecipada |
| P-07 | **Sem endpoint de retry manual** — após cache serving, usuário não pode forçar refresh | — | — | Experiência incompleta |

### Métricas de Referência
- Timeout chain: FE(480s) > Pipeline(360s) > Consolidation(300s) > PerSource(180s) > PerUF(90s)
- Batch: 5 UFs/batch, 2s delay entre batches
- Concorrência: 10 UFs paralelas (semáforo asyncio)

---

## FRENTE 2: Cache & Dados Locais

### Estado Atual
- **3 níveis**: Supabase (24h TTL) → Redis/InMemory (4h TTL) → Local file (24h)
- **SWR policy**: Fresh (0-6h), Stale (6-24h), Expired (>24h, não servido)
- Cache key: SHA256 de `setor_id + ufs_sorted + status + modalidades + modo_busca` (exclui datas intencionalmente)
- Write-through em cascata: Supabase → Redis → Local
- Auto-cleanup: Trigger mantém max 5 entries/user; cron limpa local files cada 6h
- Health endpoint: `GET /v1/health/cache` com probes 3-level

### Gaps Críticos

| ID | Gap | Impacto |
|----|-----|---------|
| C-01 | **Sem background refresh/scheduler** — cache puramente reativo (fetch on demand) | Stale cache servido indefinidamente até próxima busca |
| C-02 | **Sem prioridade hot/warm/cold** — todas as chaves tratadas igualmente | Buscas frequentes expiram junto com raras |
| C-03 | **Sem metadata de health por chave** — falta `fail_streak`, `degraded_until`, `coverage` | Impossível implementar backoff inteligente |
| C-04 | **Redis não configurado em produção** — fallback InMemoryCache ativo | Cache per-worker, sem compartilhamento entre instâncias |
| C-05 | **Analytics module missing** — `analytics_events.py` não existe, tracking silenciosamente falha | Sem cache hit rate, sem métricas de freshness |
| C-06 | **Sem admin panel de cache** — impossível inspecionar/invalidar manualmente | Ops cego para estado do cache |
| C-07 | **Sem stale-while-revalidate real** — serve stale mas não dispara revalidate em background | Próximo request paga custo total de fetch |
| C-08 | **Max 5 entries/user** — FIFO simples, sem value-based retention | Buscas de alto valor evictadas junto com exploratórias |

### Schema Atual vs Necessário

| Campo | Existe | Necessário para Visão |
|-------|--------|----------------------|
| `params_hash` | Sim | Sim |
| `results` (JSONB) | Sim | Sim |
| `sources_json` | Sim | Sim |
| `fetched_at` | Sim | Sim |
| `last_success_at` | **Não** | Sim — rastrear freshness real |
| `last_attempt_at` | **Não** | Sim — evitar re-tentativas imediatas |
| `fail_streak` | **Não** | Sim — circuit breaker por chave |
| `degraded_until` | **Não** | Sim — backoff inteligente |
| `coverage` | **Não** | Sim — quais UFs tiveram dados |
| `priority` | **Não** | Sim — hot/warm/cold classification |
| `fetch_duration_ms` | **Não** | Sim — performance trending |

---

## FRENTE 3: Frontend UX, Estados de Erro & Copy

### Estado Atual
- **Error states**: Excelentes — color-coded (red/yellow), per-source details, recovery paths
- **SSE state machine**: Graceful 1x retry + fallback time-based UI
- **Loading**: Real-time estimation, per-UF progress grid, sticky tracker
- **Relevance badges**: "Palavra-chave" (green) / "Validado por IA" (blue)
- **Cache banner**: Fresh (green) / Stale (amber) com relative time formatting
- **Truncation warning**: Per-source com UF breakdown

### Gaps Críticos — Copy que Degrada Valor

| ID | Gap | Arquivo | Linha | Texto Atual | Recomendação |
|----|-----|---------|-------|-------------|--------------|
| UX-01 | **"Em duas fontes oficiais"** | BeforeAfter.tsx | — | "Visão completa do mercado em duas fontes oficiais" | "+98% das oportunidades do Brasil analisadas" |
| UX-02 | **"Duas das maiores bases"** | DataSourcesSection.tsx | L57 | "Duas das maiores bases de licitações" | "Cobertura nacional de licitações" com % |
| UX-03 | **Source badges citam nomes** | DataSourcesSection.tsx | L71-78 | `['PNCP (Federal)', 'Portal de Compras Públicas', 'Novas fontes em breve']` | Substituir por cobertura + confiabilidade |

### Gaps — Semântica de Estado

| ID | Gap | Impacto |
|----|-----|---------|
| UX-04 | **Alertas vermelhos genéricos** — "Erro" quando deveria ser "dados parciais" | Usuário interpreta como falha total |
| UX-05 | **Sem indicador de cobertura percentual** — falta "7 de 9 UFs processadas" | Usuário não sabe extensão da busca |
| UX-06 | **Sem nível de confiabilidade** — falta indicador de qualidade dos dados | Usuário não sabe se pode confiar |
| UX-07 | **SSE terminal "error"** — deveria ser "degraded" quando cache é servido | Frontend trata cache-serving como erro |

### O Que Funciona Bem (Preservar)
- DegradationBanner com per-source details (collapsible)
- PartialResultsPrompt com UF progress tracking
- EmptyState com filter rejection breakdown + suggestions
- CacheBanner com relative time + source attribution
- 30-second retry cooldown com countdown visual

---

## FRENTE 4: Classificação & Filtros (FP/FN)

### Estado Atual — Pipeline 4-Camadas

```
Camada 0: Pre-Filter (UF, data, status) ────── O(1) lookups
Camada 1: Keyword Match
  ├─ 1A: Exclusion check FIRST (~600 termos) ── fail-fast
  ├─ 1B: Keyword match (~150+ por setor) ────── word boundary regex
  └─ 1C: Context validation (ambiguous terms) ─ confirming context required
Camada 2: Term Density Zoning
  ├─ >5%: AUTO-ACCEPT (keyword) ──────────────── sem LLM
  ├─ 2-5%: LLM standard prompt ──────────────── GPT-4.1-nano
  ├─ 1-2%: LLM conservative prompt (examples) ─ setor-aware
  └─ <1%: AUTO-REJECT ────────────────────────── sem LLM
Camada 3: Red Flags (medical/admin/infra) ──── 2+ matches = reject
Camada 4: Zero-Match LLM ──────────────────── ThreadPoolExecutor(10)
  └─ FLUXO 2 disabled quando zero-match ativo
```

- **15 setores** com keywords, exclusions, context_required, max_contract_value por setor
- **LLM**: GPT-4.1-nano, max_tokens=1 (SIM/NAO), temp=0, cache MD5 in-memory
- **Fallback = REJECT** (conservative: prefere perder ambíguo a incluir lixo)
- **Feature flags**: LLM_ARBITER_ENABLED, LLM_ZERO_MATCH_ENABLED, SYNONYM_MATCHING_ENABLED
- **QA audit**: 10% sampling de decisões LLM

### Gaps Críticos

| ID | Gap | Impacto na Visão |
|----|-----|-----------------|
| CL-01 | **Sem inspeção item/lote** — só analisa `objetoCompra` (descrição genérica) | Perde granularidade: "80% uniforme, 20% TI" invisível |
| CL-02 | **Output LLM binário (SIM/NAO)** — sem evidência, sem confiança, sem motivo | Impossível auditar, re-ranker, ou mostrar "por quê" ao usuário |
| CL-03 | **Sem viability assessment** — "relevante" ≠ "viável para mim" | Usuário vê licitações relevantes mas impraticáveis como FP |
| CL-04 | **Sem user feedback loop** — sistema não aprende com correções | FP/FN persistem sem melhoria contínua |
| CL-05 | **Sem re-ranking** — LLM como gate binário, não como scorer | Oportunidades ambíguas descartadas em vez de rebaixadas |
| CL-06 | **Sem embeddings semânticos** — matching puramente lexical | "Equipamento de vestuário" (sem keyword exata) não detectado |
| CL-07 | **Sem stemming nativo** — usa plural simples (-s, -es) | "Uniformização" ≠ "uniforme" (stemming resolveria) |
| CL-08 | **Sem co-occurrence negative inteligente** — exclusões são lista flat | "Uniforme + fachada" deveria ser padrão, não exclusão individual |
| CL-09 | **FLUXO 2 desativado** quando zero-match LLM ativo | Canal de recovery de FN inativo |

### Oportunidades de Alto Impacto

1. **Inspeção item/lote** (CL-01): PNCP API já fornece `itens[]` com descrição, NCM, unidade, quantidade. Majority rule: >50% itens matching → accept.

2. **LLM output estruturado** (CL-02): Mudar de `max_tokens=1` para JSON com `{classe, confiança, evidências[], motivo}`. Custo: ~5 tokens extra (~R$0.01/mês adicional).

3. **Co-occurrence negative** (CL-08): Pattern matching `uniform* + (fachada|pintura|identidade visual) - (têxtil|EPI|costura)` = reject. Elimina FP sem LLM.

---

## FRENTE 5: Logging & Observabilidade

### Estado Atual — Volume Crítico

| Módulo | Logger Calls | % Total | Hot Path |
|--------|-------------|---------|----------|
| search_pipeline.py | 82 | 32% | Sim |
| pncp_client.py | 75 | 30% | Sim |
| filter.py | 71 | 28% | Sim |
| consolidation.py | 15 | 6% | Sim |
| progress.py | 9 | 4% | Sim |
| **Total** | **252+** | **100%** | — |

**Por busca**: 70-120 log lines
**Por dia (1K buscas)**: 70K-120K log lines
**Railway limit**: ~20K/dia → **excede 3-6x → dropped messages**

### Problemas Específicos

| ID | Problema | Volume | Redução Potencial |
|----|----------|--------|-------------------|
| L-01 | **Filter stats: 9 logger.info separados** | 9 logs/busca | → 1 JSON log (-8) |
| L-02 | **Per-UF logging** (start + completion + recovery) | 15-20 logs/busca | → 1 summary (-12) |
| L-03 | **Per-retry logging** | 5-15 logs/busca | → 1 final outcome (-10) |
| L-04 | **Per-page fetch logging** | 30-50 logs/busca | → 1 aggregate (-40) |
| L-05 | **Circuit breaker debug** (per failure) | 5-10 logs/erro | → 1 on state change (-8) |
| L-06 | **Double exception logging** (stdout + Sentry) | 5-10 logs/busca | → Sentry only (-5) |
| L-07 | **exc_info=True para erros esperados** | stack traces desnecessários | → Conditional (-5) |

**Redução total potencial**: 50-55% (de 120 → 50-60 logs/busca)

### Observabilidade Ausente

| Métrica | Status | Impacto |
|---------|--------|---------|
| Cache hit/miss rate | Ausente | Sem visibilidade de eficácia do cache |
| Request duration (p50/p95/p99) | Calculado mas não exportado | Sem baseline de performance |
| API error rates por fonte | Só Sentry tags | Sem trending |
| Filter pass/reject ratios | Logado mas não metrificado | Sem detecção de anomalias |
| LLM classification accuracy | QA sample 10% | Sem feedback loop |
| Prometheus/StatsD exporter | Ausente | Sem dashboards |

---

## FRENTE 6: Infraestrutura, Circuit Breakers & Concorrência

### Estado Atual

| Aspecto | Implementação | Score |
|---------|--------------|-------|
| Circuit Breaker | Custom `PNCPCircuitBreaker`, per-source singletons | 8/10 |
| Redis | Opcional com InMemoryCache fallback | 9/10 |
| Concorrência | asyncio + Semaphore(10) + batch(5) + delay(2s) | 8/10 |
| Timeout Chain | Strict decreasing, env-configurable | 8/10 |
| Web Server | Gunicorn + UvicornWorker, 2 workers | 8/10 |
| Multi-instância | **Per-worker state divergence** | **5/10** |

### Gaps Críticos

| ID | Gap | Impacto |
|----|-----|---------|
| I-01 | **Circuit breaker state per-worker** — 2 workers divergem | Worker A degraded, Worker B normal = UX inconsistente |
| I-02 | **Rate limiter per-worker** — sem compartilhamento | Rate limit bypassável entre workers |
| I-03 | **Sem job queue** — LLM + Excel inline no request | Workers bloqueados 10-30s por busca |
| I-04 | **Sem background task queue** (Celery/ARQ) — só 1 cron cleanup | Impossível desacoplar heavy work do request |
| I-05 | **Redis não provisionado na Railway** | InMemoryCache = per-worker isolation |
| I-06 | **Sem tracing distribuído** — Jaeger/Datadog absent | Debug multi-worker impossível |
| I-07 | **Near timeout inversion** — PerModality(120s) ≈ PerUF(90s) | Modality pode estourar antes de UF timeout |

### Dependências Instaladas vs Necessárias

| Dep | Status | Uso |
|-----|--------|-----|
| redis==5.3.1 | Instalado, não provisionado | Cache distribuído |
| celery | **Não instalado** | Job queue (LLM, Excel) |
| arq | **Não instalado** | Async job queue alternativo |
| apscheduler | **Não instalado** | Cache warming scheduler |
| circuitbreaker lib | **Não instalado** (custom) | OK — implementação custom suficiente |

---

## MAPA DE STORIES SUGERIDAS (Input para PM)

### Track A: "Nunca Resposta Vazia" (P0)

| Story | Gaps | Descrição |
|-------|------|-----------|
| A-01 | P-01, P-02 | Timeout tenta stale cache antes de 504; empty response → degraded state com orientação |
| A-02 | P-03, UX-07 | SSE event "degraded" quando servindo cache; frontend usa semântica de estado |
| A-03 | P-04 | Ativar leitura do L3 cache (local file) como último recurso |
| A-04 | P-06 | Resposta parcial antecipada — retornar cache imediato + fetch em background via SSE |
| A-05 | UX-04, UX-05 | Substituir alertas vermelhos por indicadores de cobertura (%) e estado operacional |

### Track B: "Cache Inteligente" (P0)

| Story | Gaps | Descrição |
|-------|------|-----------|
| B-01 | C-01, C-07 | Stale-while-revalidate real — serve stale + dispara refresh em background |
| B-02 | C-02, C-08 | Sistema hot/warm/cold — prioridade por frequência de uso + valor do setor |
| B-03 | C-03 | Metadata por chave: `last_success_at`, `fail_streak`, `degraded_until`, `coverage` |
| B-04 | C-04, I-05 | Provisionar Redis na Railway; migrar InMemoryCache → Redis |
| B-05 | C-05, C-06 | Admin cache dashboard + métricas hit rate, age, stale % |
| B-06 | I-01, I-02 | Persist circuit breaker + rate limiter state no Redis |

### Track C: "Valorização de Percepção" (P1)

| Story | Gaps | Descrição |
|-------|------|-----------|
| C-01 | UX-01, UX-02, UX-03 | Reescrever copy: "+98% cobertura nacional" em vez de "2 fontes" |
| C-02 | UX-06 | Indicador de confiabilidade por resultado (keyword/AI/confiança) |
| C-03 | UX-05 | Cobertura percentual visível: "X de Y UFs" + "última atualização há Z min" |

### Track D: "Classificação de Precisão" (P1)

| Story | Gaps | Descrição |
|-------|------|-----------|
| D-01 | CL-01 | Inspeção item/lote — buscar `itens[]` da API PNCP, majority rule |
| D-02 | CL-02, CL-05 | LLM output estruturado: `{classe, confiança, evidências[], motivo}` + re-ranking |
| D-03 | CL-08 | Co-occurrence negative patterns: `keyword + negative_context - positive_signal` |
| D-04 | CL-03 | Viability assessment separado de relevância |
| D-05 | CL-04 | User feedback endpoint: marcar FP/FN → alimentar melhoria contínua |

### Track E: "Log Cirúrgico" (P0)

| Story | Gaps | Descrição |
|-------|------|-----------|
| E-01 | L-01, L-02, L-03, L-04 | Consolidar logs: 1 JSON/estágio em vez de N linhas. Meta: 50-60 logs/busca |
| E-02 | L-05, L-06, L-07 | Dedup: circuit breaker log only on state change; Sentry-only para erros esperados |
| E-03 | Obs gaps | Metrics exporter (Prometheus/StatsD): duration, error rates, cache hit rate |

### Track F: "Infra para Escala" (P2)

| Story | Gaps | Descrição |
|-------|------|-----------|
| F-01 | I-03, I-04 | Job queue (ARQ) para LLM + Excel em background |
| F-02 | I-06 | Distributed tracing (OpenTelemetry) |
| F-03 | I-07 | Realinhar timeout PerModality < PerUF estritamente |

---

## PRIORIZAÇÃO RECOMENDADA

### Sprint 1 (P0 — "Nunca falha para o usuário")

1. **A-01**: Timeout → stale cache (não 504)
2. **A-05**: Semântica de estado no frontend (cobertura %, sem vermelho)
3. **B-04**: Redis na Railway
4. **B-06**: Circuit breaker no Redis (shared state)
5. **E-01**: Reduzir logs 50% (Railway rate limit)
6. **C-01**: Copy "+98% cobertura" (substituir "2 fontes")

### Sprint 2 (P1 — "Cache como colchão")

7. **B-01**: Stale-while-revalidate real
8. **B-02**: Hot/warm/cold priority
9. **B-03**: Metadata health por chave
10. **A-02**: SSE event "degraded"
11. **D-03**: Co-occurrence negative (FP reduction sem LLM)
12. **E-03**: Metrics exporter

### Sprint 3 (P1 — "Inteligência de classificação")

13. **D-01**: Inspeção item/lote
14. **D-02**: LLM output estruturado + re-ranking
15. **B-05**: Admin cache dashboard
16. **C-02**: Indicador confiabilidade
17. **C-03**: Cobertura percentual visível

### Sprint 4 (P2 — "Escala e feedback")

18. **F-01**: Job queue (ARQ)
19. **D-04**: Viability assessment
20. **D-05**: User feedback loop
21. **F-02**: Distributed tracing

---

## CRITÉRIO DE "PRONTO PARA COBRAR CARO"

> O usuário **nunca** vê vermelho por indisponibilidade do PCP, PNCP ou qualquer outra fonte.
> No pior caso, vê "dados com X minutos de defasagem" e um indicador de cobertura.
> O sistema continua tentando por trás, com parcimônia.

**Teste de validação**: Desligar PNCP + PCP simultaneamente. O usuário deve:
1. Receber resultados do cache (com timestamp)
2. Ver "Cobertura: dados de 2h atrás, atualizando..."
3. Não ver nenhum alerta vermelho
4. Receber atualização via SSE quando fontes voltarem

---

## PRINCÍPIO ARQUITETURAL (Adicionar à Memória)

> **Cache = Colchão de Impacto, não Acelerador.**
> Acelerador falha junto com a fonte. Colchão absorve o impacto e permite vender assinatura.

> **Qualquer funcionalidade nova ou existente deve ser avaliada sob um único critério:**
> Em caso de falha parcial ou total das dependências, o sistema ainda entrega algo útil e compreensível para o usuário?
> Se não, a implementação não está pronta para produção.
