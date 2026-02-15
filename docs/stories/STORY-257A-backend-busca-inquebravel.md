# STORY-257A: Backend — Busca Inquebrável

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-257A |
| **Priority** | P0 (GTM-blocker) |
| **Sprint** | Sprint 2 |
| **Estimate** | 6h |
| **Depends on** | STORY-252 (multi-source foundation) |
| **Blocks** | GTM launch readiness |
| **Paired with** | STORY-257B (frontend UX) |

## Filosofia

> **"Degraded ≠ Dead. Always try. Never leave the user empty-handed."**

O PNCP é a única fonte relevante hoje. As demais (ComprasGov, Portal, Licitar) ou estão fora do ar, ou sem credenciais. O sistema PRECISA extrair dados do PNCP mesmo quando ele está instável — com paciência, inteligência e transparência.

**Regra de ouro:** O usuário NUNCA deve ver "nenhum resultado" quando existem licitações abertas. Se o PNCP está lento, tentamos mais. Se está fora, servimos cache. Se não temos cache, dizemos honestamente o que está acontecendo e oferecemos voltar depois.

**Regra de linguagem:** NUNCA expor nomes técnicos de fontes ao usuário (PNCP, ComprasGov, etc). Na interface, usar sempre **"nossas fontes"** ou **"fontes de dados governamentais"**. Nomes técnicos ficam APENAS em logs e Sentry.

## Problema (evidência Sentry 2026-02-14T23:55)

```
23:55:19.573  PNCP circuit breaker already degraded — skipping PNCP entirely
23:55:19.573  PNCP: 0 records in 9ms                    ← NEM TENTOU
23:55:20.229  [COMPRAS_GOV] Server error 503. Retrying in 2.1s
23:55:22.454  [COMPRAS_GOV] Server error 503. Retrying in 4.5s
23:55:27.104  [COMPRAS_GOV] Server error 503. Retrying in 8.2s
23:55:35.867  [COMPRAS_GOV] Error after 16299ms         ← 16s PARA NADA
23:55:35.870  All sources failed                         ← ZERO RESULTADOS
```

**Diagnóstico:** O PNCP nem foi consultado (circuit breaker de busca anterior). ComprasGov deu 503 em todas as tentativas. Resultado: 16 segundos de espera → zero oportunidades → usuário frustrado.

### Fragilidades identificadas

| # | Sev | Problema | Impacto |
|---|-----|----------|---------|
| 1 | **CRITICAL** | Circuit breaker degraded = **skip total** do PNCP | Uma busca anterior ruim mata TODAS as buscas seguintes por 5min |
| 2 | **CRITICAL** | Sem cache de resultados | Blackout total quando fontes caem, mesmo se busca idêntica funcionou 1h atrás |
| 3 | **HIGH** | Health canary não distingue 4xx de 5xx | HTTP 400 (params errados) trip o breaker como se fosse server down |
| 4 | **HIGH** | Race condition no circuit breaker | Mutação de estado sem asyncio.Lock |
| 5 | **HIGH** | Resource leak no fallback adapter | HTTP client nunca fechado |
| 6 | **MEDIUM** | `is_available()` retorna True sem credentials | Fontes fantasmas contam como "tentadas" |
| 7 | **MEDIUM** | Resultados parciais silenciosos | UFs que falham somem sem aviso |
| 8 | **LOW** | Non-dict results silenciosamente descartados | Sem log de diagnóstico |

---

## Solução: 4 Tracks

### Track 1: Circuit Breaker Reform — "Degraded ≠ Dead" (2h)

**Problema central:** Quando o circuit breaker entra em modo degraded, o PNCP é COMPLETAMENTE ignorado. Isso transforma uma instabilidade temporária em blackout total.

**Nova filosofia:** Degraded mode = "ser mais paciente e cauteloso", NÃO "desistir".

- [x] **AC1: Degraded mode tenta com concorrência reduzida**
  - `pncp_client.py:buscar_todas_ufs_paralelo()`: quando `is_degraded=True`, reduzir `max_concurrent` de 10 para 3
  - Priorizar UFs por população (SP, RJ, MG, BA, PR, RS, PE, CE, SC, GO primeiro)
  - Aumentar `timeout_per_uf` de 30s para 45s em degraded mode
  - Log: `"PNCP degraded — trying with reduced concurrency (3 UFs, 45s timeout)"`
  - **Critério:** Busca com circuit breaker degraded DEVE tentar o PNCP (não pular)

- [x] **AC2: Threshold e cooldown ajustados**
  - `PNCP_CIRCUIT_BREAKER_THRESHOLD`: 5 → 8 (mais tolerante antes de trip)
  - `PNCP_CIRCUIT_BREAKER_COOLDOWN`: 300s → 120s (recupera mais rápido)
  - Manter configurável via env var (não hardcode)
  - **Critério:** Pelo menos 8 timeouts consecutivos antes de entrar em degraded

- [x] **AC3: Health canary distingue 4xx de 5xx**
  - `pncp_client.py` health canary: HTTP 4xx (400, 404, 422) = client error → NÃO trip breaker
  - HTTP 4xx: logar `WARN canary_client_error status={code} body={body[:200]}` e **prosseguir com busca normal**
  - HTTP 5xx (500, 502, 503) e timeout = server error → `record_failure()` normalmente
  - Revisar params do canary (data range, modalidade) para garantir que são válidos no PNCP
  - **Critério:** HTTP 400 no canary não ativa degraded mode

- [x] **AC4: Race condition fix + separar check de mutação**
  - `pncp_client.py:86-96`: separar `is_degraded` (read-only property) de `try_recover()` (muta estado)
  - `is_degraded` apenas checa `time.time() < degraded_until` — sem side effects
  - `try_recover()` adquire `asyncio.Lock`, checa expiração, reseta se expirado
  - Health canary DEVE usar `record_failure()` em vez de mutação direta de `degraded_until`
  - Lock timeout: 1s (se não conseguir lock, prosseguir com estado atual)
  - **Critério:** Nenhuma mutação de estado do circuit breaker acontece sem Lock

### Track 2: Resultados Parciais como Feature (1.5h)

**Problema:** Se 20/27 UFs retornam dados e 7 falham, o sistema retorna os 20 mas não informa que 7 faltaram. O usuário não sabe se está vendo o quadro completo.

- [x] **AC5: Response inclui `failed_ufs` e `succeeded_ufs`**
  - Adicionar ao response JSON de `/buscar`:
    ```json
    {
      "succeeded_ufs": ["SP", "RJ", "MG", ...],
      "failed_ufs": ["BA", "CE"],
      "total_ufs_requested": 27,
      "is_partial": true
    }
    ```
  - `pncp_client.py:buscar_todas_ufs_paralelo()`: rastrear quais UFs retornaram dados vs quais falharam/timeout
  - `search_pipeline.py`: propagar `failed_ufs` no contexto e incluir no response
  - **Critério:** Frontend recebe lista exata de UFs que falharam

- [x] **AC6: Progresso SSE per-UF com status detalhado**
  - `progress.py`: novo tipo de evento `uf_status` com campos:
    ```json
    {"stage": "uf_status", "uf": "SP", "status": "success", "count": 47}
    {"stage": "uf_status", "uf": "BA", "status": "retrying", "attempt": 2, "max": 5}
    {"stage": "uf_status", "uf": "CE", "status": "failed", "reason": "timeout"}
    ```
  - Emitir evento quando cada UF: inicia, retenta, finaliza (sucesso ou falha)
  - **Critério:** Frontend recebe status individual por UF via SSE

- [x] **AC7: Auto-retry de UFs falhas**
  - Após o fetch principal, se `failed_ufs` não está vazio e `succeeded_ufs` não está vazio:
    - Esperar 5s e retentar UFs falhas com timeout estendido (45s)
    - Máximo 1 round de retry automático
    - Se recuperar dados, emitir SSE `uf_status` com `status: "recovered"` e incluir novos resultados
  - Não bloquear a resposta principal — o retry é fire-and-forget que atualiza via SSE
  - **Critério:** UFs que falharam por timeout são retentadas automaticamente uma vez

### Track 3: Cache de Resultados — "Never Empty-Handed" (1.5h)

**Problema:** Quando todas as fontes caem, o usuário vê zero resultados, mesmo que a busca idêntica tenha funcionado horas atrás.

- [x] **AC8: Cache write-through em busca bem-sucedida**
  - Usar `InMemoryCache` existente (`redis_pool.py`)
  - Cache key: `search_cache:{sha256(json.dumps(sorted_params))}` onde params = `{setor_id, ufs, status, modalidades, modo_busca}`
    - **Excluir datas do cache key** — queremos servir resultados recentes mesmo se datas mudaram ligeiramente
  - Valor: JSON `{licitacoes: [...], resumo: {...}, total: N, cached_at: ISO, search_params: {...}}`
  - TTL: 4 horas (licitações abertas mudam lentamente)
  - Apenas cachear quando `total > 0` (nunca cachear resultados vazios)
  - **Critério:** Busca com resultados grava no cache automaticamente

- [x] **AC9: Cache hit quando AllSourcesFailedError**
  - Em `search_pipeline.py`, no catch de `AllSourcesFailedError`:
    1. Tentar cache hit com mesmos params
    2. Se hit: retornar resultados com `cached: true`, `cached_at: "2026-02-14T22:00:00Z"`
    3. Se miss: retornar resposta vazia com `degradation_reason` humanizado
  - Response com cache inclui flag `cached: true` para frontend exibir banner
  - **Critério:** Busca que falha mas tem cache retorna dados em <1s (não 16s de timeout)

- [x] **AC10: `force_fresh` param para bypass de cache**
  - Adicionar campo opcional `force_fresh: bool = False` no `BuscaRequest` schema
  - Quando `force_fresh=True`: ignorar cache no read (mas ainda fazer write-through)
  - Usar quando usuário clica "Atualizar dados" no frontend
  - **Critério:** Request com `force_fresh=true` sempre tenta fontes primárias

- [x] **AC11: Persistência de última busca por usuário (Supabase)**
  - Tabela `search_results_cache`:
    ```sql
    CREATE TABLE search_results_cache (
      id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
      user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
      params_hash TEXT NOT NULL,
      search_params JSONB NOT NULL,
      results JSONB NOT NULL,
      total_results INTEGER NOT NULL,
      created_at TIMESTAMPTZ DEFAULT now(),
      UNIQUE(user_id, params_hash)
    );
    CREATE INDEX idx_search_cache_user ON search_results_cache(user_id, created_at DESC);
    ```
  - Gravar quando busca retorna `total > 0` (async, não bloqueia response)
  - Consultar quando AllSourcesFailed E InMemoryCache miss
  - Limpeza: manter apenas últimas 5 buscas por usuário (cron ou on-write)
  - **Critério:** Mesmo após redeploy (que limpa InMemoryCache), cache Supabase serve dados

### Track 4: Fixes Técnicos Consolidados (1h)

- [x] **AC12: Fix resource leak no fallback adapter**
  - `consolidation.py`: método `close()` deve fechar `self._fallback_adapter` se existir
  - Usar `async with` ou try/finally para garantir cleanup
  - **Critério:** Nenhum HTTP client leak após busca

- [x] **AC13: `is_available()` retorna False sem credentials**
  - `sources.py:236`: checar se API key está configurada quando source requer autenticação
  - Health endpoint: reportar `pending_credentials` para fontes enabled sem key
  - `search_pipeline.py`: não passar fontes com `is_available()=False` ao ConsolidationService
  - **Critério:** Fontes sem credenciais não são tentadas (evita timeout fantasma)

- [x] **AC14: Log non-dict results do gather**
  - `consolidation.py:182`: quando `asyncio.gather` retorna resultado non-dict, logar `WARN unexpected_result type={type} value={str(val)[:200]}`
  - **Critério:** Nenhum resultado silenciosamente descartado sem log

- [x] **AC15: Observabilidade por busca**
  - Log estruturado JSON no final de cada busca:
    ```json
    {
      "event": "search_complete",
      "sources_attempted": ["PNCP", "COMPRAS_GOV"],
      "sources_succeeded": ["PNCP"],
      "sources_failed": ["COMPRAS_GOV"],
      "cache_hit": false,
      "circuit_breaker_state": "healthy",
      "total_results": 87,
      "ufs_requested": 27,
      "ufs_succeeded": 25,
      "ufs_failed": 2,
      "latency_ms": 12340
    }
    ```
  - Sentry event `source_blackout` (severity=error) quando todas as fontes falham
  - **Critério:** Cada busca gera exatamente 1 log estruturado de resumo

---

## Testes

### Backend (10 testes)

- [x] **T1:** Circuit breaker degraded: busca TENTA com concorrência reduzida (não pula)
- [x] **T2:** Circuit breaker threshold: 7 falhas consecutivas → ainda healthy. 8ª falha → degraded
- [x] **T3:** Circuit breaker cooldown: após 120s, estado volta para healthy
- [x] **T4:** Health canary 400: NÃO ativa circuit breaker, busca prossegue normalmente
- [x] **T5:** Health canary 503: ATIVA circuit breaker via `record_failure()`
- [x] **T6:** Race condition: `record_failure()` e `try_recover()` usam Lock (testar com concurrent tasks)
- [x] **T7:** Cache write-through: busca com resultados grava no cache
- [x] **T8:** Cache hit no AllSourcesFailedError: retorna dados com `cached=true`
- [x] **T9:** `is_available()` retorna False para fonte enabled sem API key
- [x] **T10:** Response inclui `failed_ufs` quando UFs falham por timeout
- [x] **T11:** Per-UF status callback invocation (fetching → success)
- [x] **T12:** Auto-retry of failed UFs (retry → recovered)
- [x] **T13:** Structured log fields verification

---

## Arquivos a Modificar

| Arquivo | Track | Mudanças |
|---------|-------|---------|
| `backend/pncp_client.py` | T1 | AC1-AC4: circuit breaker reform, canary 4xx/5xx, race condition, degraded concurrency |
| `backend/search_pipeline.py` | T2,T3,T4 | AC5,AC7,AC9,AC10,AC13: partial results, cache layer, is_available filter |
| `backend/progress.py` | T2 | AC6: evento `uf_status` com status individual |
| `backend/schemas.py` | T2,T3 | AC5,AC10: `failed_ufs`, `force_fresh` fields |
| `backend/consolidation.py` | T4 | AC12,AC14: resource leak fix, log non-dict |
| `backend/source_config/sources.py` | T4 | AC13: `is_available()` check credentials |
| `backend/redis_pool.py` | T3 | AC8: verificar InMemoryCache para resultados |
| `supabase/migrations/` | T3 | AC11: tabela `search_results_cache` |
| `backend/config.py` | T1 | AC2: novos defaults para threshold/cooldown |

---

## Riscos e Mitigações

| Risco | Prob | Impacto | Mitigação |
|-------|------|---------|-----------|
| PNCP degraded mode com 3 UFs ainda dá timeout | Média | Resultados parciais reduzidos | Priorizar UFs por pop; 45s timeout; cache como fallback |
| Cache de 4h serve licitação já encerrada | Baixa | Usuário tenta participar de lic. fechada | Banner claro no frontend (STORY-257B); TTL conservador |
| Lock no circuit breaker causa deadlock | Baixa | Busca trava | Timeout de 1s no Lock; fallthrough |
| InMemoryCache perdido no redeploy | Certa | Cold start sem cache | AC11 (Supabase) como segundo nível; reconstrói organicamente |
| Tabela search_results_cache cresce demais | Baixa | Performance DB | Limit 5 por usuário; cleanup on-write |

## Definition of Done

- [x] Todos os ACs checked
- [x] `pytest` sem regressões (baseline: 21 pre-existing)
- [x] Busca com circuit breaker degraded TENTA o PNCP (não pula)
- [x] HTTP 400 no canary não causa blackout
- [x] Busca idêntica que funcionou 2h atrás serve cache quando fontes caem
- [x] Response inclui `failed_ufs` para transparência ao frontend
- [x] Race conditions eliminadas (Lock em todas as mutações)
- [x] Nenhum nome técnico de fonte exposto ao usuário (PNCP, ComprasGov → "nossas fontes")
- [x] Log estruturado JSON em cada busca para observabilidade
