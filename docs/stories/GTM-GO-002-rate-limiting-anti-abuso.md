# GTM-GO-002: Rate Limiting Anti-Abuso em Endpoints Críticos

## Epic
GTM Readiness — Redução de Risco Operacional

## Sprint
Sprint GO: Eliminação de Bloqueadores GTM

## Prioridade
P1 — Risco financeiro + reputacional

## Estimativa
4h

## Status: PENDING

---

## Risco Mitigado

**Risco:** Um único usuário (malicioso ou por bug de integração) pode disparar centenas de buscas por minuto no endpoint `/buscar`, cada uma acionando pipeline multi-fonte (PNCP + PCP + ComprasGov), chamadas LLM (GPT-4.1-nano), e geração de Excel. O custo é multiplicado por busca: ~R$0.003 LLM + compute Railway + egress Redis + I/O Supabase.

**Impacto se materializar:**
- **Financeiro:** 1.000 buscas abusivas × R$0.003 LLM = R$3, mas o custo real está no compute Railway (~R$0.05/busca em CPU/memória) + 1.000 requests paralelos ao PNCP → rate limit 429 → circuit breaker abre → **todos os usuários legítimos perdem acesso à busca** por 120s (cooldown do CB).
- **Reputacional:** Usuários legítimos veem "Fontes indisponíveis" porque um abusador esgotou o rate limit compartilhado do PNCP.
- **Operacional:** Sem per-user rate limit, não há como distinguir tráfego legítimo de abuso nos logs.

**Estado atual vs. risco:**
Existe rate limit global no PNCP (10 tokens, 10/s refill em `rate_limiter.py`), mas ele é compartilhado por todos os usuários. Um único abusador esgota os tokens de todos. O endpoint `/buscar` em si não tem rate limit per-user.

## Estado Técnico Atual

### O que existe:

1. **`backend/rate_limiter.py`** — Classe `RateLimiter` com Redis backend + fallback InMemory
   - `check_rate_limit(key, max_requests, window_seconds)` — token bucket por chave
   - `RedisRateLimiter` — Lua script atômico para rate limit global de APIs externas
   - Instâncias globais: `pncp_rate_limiter` (10 tokens), `pcp_rate_limiter` (5 tokens)

2. **Endpoints com rate limit hoje:**
   - `/v1/feedback` — 50/hora per-user (429 implementado)
   - `/auth/resend-confirmation` — 60s cooldown per-email
   - `/v1/first-analysis` — usa instância do rate_limiter

3. **Endpoints SEM rate limit (vulneráveis):**
   - `POST /buscar` — nenhum per-user limit
   - `POST /login` (Supabase Auth) — nenhuma proteção anti-brute-force no proxy
   - `POST /signup` — nenhuma proteção anti-bot
   - `GET /buscar-progress/{id}` (SSE) — nenhum limit de conexões
   - `GET /v1/admin/*` — sem rate limit (protegido por role, mas sem limite de requests)

### Fragilidade:
O `RateLimiter` já existe e funciona — é infraestrutura pronta. Falta apenas aplicá-lo aos endpoints críticos. O custo de implementação é baixo (decorator/dependency injection) mas o risco de não implementar é alto.

## Objetivo

Impedir que um único usuário ou IP consiga degradar o serviço para outros usuários através de volume abusivo de requests, com limites que não impactem uso legítimo e respostas 429 informativas.

## Critérios de Aceite

### Rate Limit na Busca

- [ ] AC1: `POST /buscar` retorna HTTP 429 quando usuário autenticado excede **10 buscas por minuto**
  - **Evidência:** Teste automatizado que faz 11 requests em sequência e verifica 429 na 11ª
  - **Métrica:** 10 req/min per-user (configurável via `SEARCH_RATE_LIMIT_PER_MINUTE`, default 10)

- [ ] AC2: Resposta 429 inclui body JSON com `detail`, `retry_after_seconds`, e `correlation_id`
  - **Evidência:** Teste verifica schema da resposta 429

- [ ] AC3: Header `Retry-After` presente na resposta 429 com valor em segundos
  - **Evidência:** Teste verifica header

### Rate Limit na Autenticação

- [ ] AC4: `POST /api/auth/login` (proxy Next.js) retorna 429 quando **mesmo IP** excede **5 tentativas em 5 minutos**
  - **Evidência:** Teste automatizado no proxy
  - **Métrica:** 5 tentativas / 5 min per-IP

- [ ] AC5: `POST /api/auth/signup` retorna 429 quando **mesmo IP** excede **3 registros em 10 minutos**
  - **Evidência:** Teste automatizado no proxy
  - **Métrica:** 3 registros / 10 min per-IP

### Rate Limit no SSE

- [ ] AC6: Máximo de **3 conexões SSE simultâneas** por usuário autenticado em `/buscar-progress/{id}`
  - **Evidência:** Teste que abre 4 conexões e verifica que a 4ª é rejeitada (429 ou connection close)
  - **Métrica:** 3 conexões simultâneas per-user

### Implementação Backend

- [ ] AC7: Dependency `require_rate_limit(max_requests, window_seconds)` criada como FastAPI Depends reutilizável
  - **Evidência:** Código da dependency + docstring com exemplos de uso

- [ ] AC8: Rate limit usa Redis quando disponível, fallback para InMemory (mesma lógica do `RateLimiter` existente)
  - **Evidência:** Teste com Redis mock indisponível → fallback funciona

- [ ] AC9: Rate limit por user_id (autenticado) ou por IP (não autenticado), nunca por ambos simultaneamente
  - **Evidência:** Teste verifica isolamento — usuário A no limite não bloqueia usuário B

- [ ] AC10: Configuração via env vars: `SEARCH_RATE_LIMIT_PER_MINUTE=10`, `AUTH_RATE_LIMIT_PER_5MIN=5`, `SSE_MAX_CONNECTIONS=3`
  - **Evidência:** Vars documentadas no `.env.example`

### Logging e Observabilidade

- [ ] AC11: Todo 429 logado como WARNING com: `user_id`/`ip`, `endpoint`, `current_count`, `limit`, `correlation_id`
  - **Evidência:** Teste verifica log output

- [ ] AC12: Prometheus counter `smartlic_rate_limit_exceeded_total` com labels `endpoint`, `limit_type` (user/ip)
  - **Evidência:** Teste verifica incremento do counter

## Testes

### Backend (pytest) — mínimo 12 testes

- [ ] T1: `POST /buscar` com 10 requests → todas 200. 11ª → 429
- [ ] T2: Resposta 429 tem `detail`, `retry_after_seconds`, `correlation_id`
- [ ] T3: Header `Retry-After` presente e numérico
- [ ] T4: Rate limit isolado por user_id — user A no limite, user B faz request normalmente
- [ ] T5: Redis indisponível → fallback InMemory funciona
- [ ] T6: Window expira → requests liberados novamente
- [ ] T7: SSE 3 conexões → ok. 4ª → rejeitada
- [ ] T8: Counter Prometheus incrementa em 429
- [ ] T9: Log WARNING emitido com campos corretos
- [ ] T10: Config via env var override funciona
- [ ] T11: Endpoint não autenticado (login) usa IP como chave
- [ ] T12: IPs distintos têm contadores independentes

### Frontend (jest) — mínimo 3 testes

- [ ] T13: Proxy `/api/auth/login` retorna 429 com mensagem PT-BR após exceder limite
- [ ] T14: Proxy `/api/auth/signup` retorna 429 com mensagem PT-BR
- [ ] T15: Busca recebe 429 → useSearch exibe mensagem "Muitas consultas. Aguarde X segundos."

### Teste de Falha

- [ ] T16: Simular burst de 50 requests em 10s para `/buscar` → sistema responde 429 para excedentes, requests legítimos de outros users não são afetados
  - **Evidência:** Locust scenario ou script pytest que valida isolamento

## Métricas de Sucesso

| Métrica | Antes | Depois | Verificação |
|---------|-------|--------|-------------|
| Rate limit per-user em /buscar | ∞ (sem limite) | 10/min | Teste T1 |
| Rate limit em auth endpoints | ∞ | 5/5min (login), 3/10min (signup) | Testes T13-T14 |
| SSE connections per-user | ∞ | 3 simultâneas | Teste T7 |
| Endpoints críticos sem rate limit | 5 | 0 | Contagem de endpoints |
| Abuso detectável via logs | Não | Sim (WARNING + counter) | Teste T8-T9 |

## Rollback

1. **Remover dependency:** Comentar `Depends(require_rate_limit(...))` das rotas afetadas
2. **Feature flag:** `RATE_LIMITING_ENABLED=false` desativa todos os rate limits (dependency retorna imediatamente)
3. **Tempo de rollback:** < 5 minutos (1 env var no Railway)
4. **Impacto do rollback:** Volta ao estado atual (sem rate limit per-user). Nenhum dado perdido.

## Idempotência

- Rate limit counters em Redis expiram automaticamente (TTL = window_seconds)
- InMemory counters resetam no restart do processo
- Re-aplicar a dependency não cria efeitos cumulativos

## Arquivos Modificados

| Arquivo | Tipo |
|---------|------|
| `backend/rate_limiter.py` | Modificado — `require_rate_limit` dependency + SSE limiter |
| `backend/routes/search.py` | Modificado — `Depends(require_rate_limit(10, 60))` |
| `backend/main.py` | Modificado — SSE connection tracking |
| `backend/config.py` | Modificado — novas env vars |
| `backend/metrics.py` | Modificado — counter `rate_limit_exceeded_total` |
| `frontend/app/api/auth/login/route.ts` | Modificado — IP rate limit middleware (se existir proxy) |
| `.env.example` | Modificado — documentar rate limit vars |
| `backend/tests/test_rate_limiting.py` | Criado — 12+ testes |
| `frontend/__tests__/api/auth-rate-limit.test.ts` | Criado — 3 testes |

## Dependências

| Tipo | Item | Motivo |
|------|------|--------|
| Usa | `backend/rate_limiter.py` | Infraestrutura existente |
| Usa | `backend/metrics.py` | Prometheus counter |
| Paralela | GTM-GO-001 | Alertas + rate limit são complementares |
