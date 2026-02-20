# GTM-RESILIENCE-B04 — Provisionar Redis na Railway e Migrar InMemoryCache

**Track:** B — Cache Inteligente
**Prioridade:** P0
**Sprint:** 1
**Estimativa:** 2-3 horas
**Gaps Endereados:** C-04, I-05
**Dependencias:** Nenhuma (prerequisito para B-01 e B-06)
**Autor:** @pm
**Data:** 2026-02-18

---

## Contexto

O backend SmartLic possui o package `redis==5.3.1` instalado e todo o codigo de integracao pronto (`redis_pool.py`), mas **Redis nao esta provisionado na Railway**. A variavel `REDIS_URL` nao existe no ambiente de producao, fazendo com que `get_redis_pool()` retorne `None` e o sistema opere exclusivamente com `InMemoryCache` como L2.

### Estado Atual

- **redis_pool.py**: Completamente implementado com async pool, fallback InMemoryCache, health check
- **InMemoryCache**: LRU com max 10K entries, TTL support, funcional mas **per-worker**
- **Gunicorn**: 2 workers UvicornWorker (`WEB_CONCURRENCY=2`)
- **Impacto**: Cache L2 nao compartilhado entre workers — worker A tem cache diferente de worker B
- **progress.py**: Suporta Redis pub/sub para SSE distribuido, mas cai no fallback asyncio.Queue

### Consequencias da Ausencia de Redis

| Aspecto | Sem Redis | Com Redis |
|---------|-----------|-----------|
| Cache L2 | Per-worker (2 caches isolados) | Compartilhado (1 cache unificado) |
| Circuit breaker | Per-worker (estados divergentes) | Compartilhado (estado consistente) |
| Rate limiter | Per-worker (bypass entre workers) | Compartilhado (rate limit real) |
| SSE progress | asyncio.Queue (single worker) | pub/sub (cross-worker) |
| Hit rate | ~50% do potencial | 100% do potencial |

### Custo Railway Redis

Railway Redis addon: ~$5-10/mês para instancia basica (suficiente para POC).

---

## Problema

1. **Cache per-worker**: 2 workers Gunicorn mantem caches L2 independentes; cache miss em worker A mesmo que worker B ja tenha os dados
2. **Circuit breaker divergente**: Worker A pode estar degraded enquanto worker B esta healthy — UX inconsistente
3. **Rate limiter bypassavel**: Rate limit de 10 req/s e por worker; 2 workers = 20 req/s efetivo contra PNCP
4. **SSE cross-worker impossivel**: Se o POST /buscar vai para worker A e o GET /buscar-progress vai para worker B, o SSE nao recebe eventos

---

## Solucao

### 1. Provisionar Redis na Railway

```bash
# Via Railway CLI (preferido - CLAUDE.md instrui usar CLI)
railway add --plugin redis
# Isso automaticamente seta REDIS_URL no ambiente
```

Alternativa via dashboard se CLI nao suportar plugin add.

### 2. Verificar Conexao

Apos provisionar, `redis_pool.py:get_redis_pool()` detecta `REDIS_URL` automaticamente e inicializa o pool. Nenhuma alteracao de codigo necessaria no happy path.

### 3. Health Endpoint

O endpoint `GET /v1/health` ja verifica Redis via `is_redis_available()`. Verificar que reporta `redis: "connected"` apos provisionar.

### 4. Fallback Preservado

Se Redis ficar indisponivel em producao, o sistema DEVE continuar operando com InMemoryCache. Essa resiliencia ja existe em `redis_pool.py` e deve ser preservada.

---

## Criterios de Aceite

### AC1 — Redis provisionado na Railway
Redis addon adicionado ao projeto Railway, instancia running, URL acessivel.
**Teste**: `railway variables` mostra `REDIS_URL` configurado.

### AC2 — REDIS_URL configurado no ambiente backend
Variavel de ambiente `REDIS_URL` disponivel para o servico backend. Formato: `redis://default:password@host:port`.
**Teste**: `railway run printenv | grep REDIS_URL` retorna URL valida.

### AC3 — Conexao bem-sucedida no startup
Log de startup do backend mostra `"Redis pool connected: host:port (max_connections=20)"` em vez de `"REDIS_URL not set"`.
**Teste**: `railway logs` apos deploy mostra mensagem de conexao Redis.

### AC4 — Health endpoint reporta Redis connected
`GET /v1/health` retorna `"redis": "connected"` (ou equivalente) em vez de `"redis": "unavailable"`.
**Teste**: curl ao health endpoint em producao retorna status Redis.

### AC5 — Cache L2 compartilhado entre workers
Setar cache via worker A; ler via worker B. Ambos veem o mesmo dado.
**Teste**: Fazer busca em producao (POST /buscar); verificar via `railway run python -c "from redis_pool import ...; print(cache.get(key))"` que dado existe no Redis.

### AC6 — SSE progress via Redis pub/sub
Quando `REDIS_URL` esta configurado, `ProgressTracker` usa Redis pub/sub para eventos SSE em vez de asyncio.Queue local.
**Teste**: Verificar log `"Using Redis pub/sub for progress"` (ou equivalente) em producao; SSE funcional em busca real.

### AC7 — Fallback InMemoryCache preservado
Se Redis ficar indisponivel temporariamente, o sistema deve:
1. Detectar falha de conexao
2. Logar warning (nao error)
3. Continuar operando com InMemoryCache
4. Reconectar automaticamente quando Redis voltar
**Teste**: Simular falha de Redis (desconectar temporariamente); verificar que buscas continuam funcionando; reconectar; verificar que Redis e re-utilizado.

### AC8 — Metricas de Redis no health endpoint
Health endpoint inclui: `redis_connected: bool`, `redis_latency_ms: float` (ping), `redis_memory_used_mb: float`.
**Teste**: Chamar health endpoint; verificar 3 campos presentes e com valores razoaveis.

### AC9 — Nenhuma alteracao de codigo em redis_pool.py
O arquivo `redis_pool.py` ja esta completamente implementado. Esta story e exclusivamente de infraestrutura (provisionar + configurar). Se alguma alteracao de codigo for necessaria, documentar o motivo.
**Teste**: `git diff backend/redis_pool.py` vazio apos deploy (ou com justificativa documentada).

### AC10 — Documentacao de operacao
Arquivo `docs/ops/redis-railway.md` com: como provisionar, como monitorar, como fazer failover, como limpar cache manualmente.
**Teste**: Arquivo existe com as 4 secoes.

---

## Arquivos Afetados

| Arquivo | Alteracao |
|---------|-----------|
| Railway config | Adicionar Redis addon |
| Railway env vars | `REDIS_URL` setado automaticamente |
| `backend/main.py` | Possivelmente adicionar metricas de Redis ao health (AC8) |
| `docs/ops/redis-railway.md` | Novo: documentacao operacional |
| Nenhum arquivo de codigo backend | `redis_pool.py` ja esta pronto |

---

## Nota sobre Seguranca

- `REDIS_URL` contem credenciais — nunca commitar no repositorio
- Railway gerencia a URL como env var do servico (seguro por padrao)
- Conexao Redis na Railway e interna (mesma rede privada, sem exposicao publica)

---

## Dependencias

- Nenhuma dependencia de outras stories
- **E prerequisito para**: B-01 (dedup de revalidacoes), B-06 (circuit breaker compartilhado), A-02 (SSE degraded cross-worker)

---

## Procedimento de Rollback

Se Redis causar problemas em producao:
1. Setar `REDIS_URL=""` (string vazia) via `railway variables set REDIS_URL=""`
2. Deploy automatico (Railway redeploy on env change)
3. Sistema cai no InMemoryCache fallback automaticamente
4. Zero downtime — fallback e transparente

---

## Definition of Done

- [x] Redis addon provisionado na Railway
- [x] REDIS_URL configurado e acessivel pelo backend
- [x] Log de startup confirma conexao Redis
- [x] Health endpoint reporta Redis connected
- [x] Cache compartilhado entre workers verificado
- [x] Fallback InMemoryCache testado (desconectar Redis temporariamente)
- [x] Documentacao operacional criada
- [ ] Zero regressoes em producao apos deploy
