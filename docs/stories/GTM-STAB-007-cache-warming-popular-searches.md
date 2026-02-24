# GTM-STAB-007 — Cache Warming para Buscas Populares

**Status:** To Do
**Priority:** P1 — High (transforma busca de 60-120s em <2s)
**Severity:** Performance — sem cache, toda busca é fresh API call
**Created:** 2026-02-24
**Sprint:** GTM Stabilization
**Relates to:** GTM-STAB-001 (migrations), GTM-RESILIENCE-B01 (SWR background refresh), GTM-RESILIENCE-B02 (hot/warm/cold)

---

## Problema

Com o cache quebrado (GTM-STAB-001), toda busca vai direto para PNCP/PCP/ComprasGov. Mesmo após fix do cache, a **primeira busca de cada combinação** setor+UFs+período ainda será lenta (30-90s).

Para experiência enterprise, as buscas mais comuns devem ser **instantâneas** (<2s).

### Padrão de buscas esperado:

- 15 setores × 27 UFs × 1 período = ~400 combinações possíveis
- Na prática: ~80% das buscas concentram em ~30 combinações (top setores + top UFs)
- Top 5 setores: vestuario, informatica, engenharia, saude, facilities
- Top 5 UFs: SP, MG, RJ, BA, RS
- Período: default 10 dias (fixo)

### Benefício:

- Busca cached: **<2s** (Supabase read + InMemory hit)
- Busca fresh: **30-90s** (PNCP + filtro + LLM)
- Cache warming: transformar 80% das buscas em cached

---

## Acceptance Criteria

### AC1: Cron job de cache warming
- [ ] Novo job ARQ: `cache_warming_job` em `job_queue.py`
- [ ] Executa a cada 4h (alinhado com cache TTL de 4h do InMemory)
- [ ] Lista de combinações a aquecer:
  ```python
  WARM_COMBINATIONS = [
      # Top 5 setores × Top 10 UFs = 50 combinações
      {"setor": "vestuario", "ufs": ["SP"]},
      {"setor": "vestuario", "ufs": ["MG"]},
      {"setor": "vestuario", "ufs": ["RJ"]},
      # ... etc
  ]
  ```
- [ ] Cada combinação = uma busca completa (PNCP + filtro + cache save)
- [ ] Rate limiting: max 2 buscas simultâneas, 5s delay entre buscas
- [ ] Total: ~50 combinações × 30s avg = ~25 min de warming (cabe no intervalo de 4h)

### AC2: Smart warming baseado em analytics
- [ ] Ao invés de lista estática, usar tabela `search_sessions` para identificar buscas mais frequentes
- [ ] Query: top 50 combinações (setor + ufs) por contagem nos últimos 7 dias
- [ ] Priorizar por frequência + recência
- [ ] Atualizar lista dinamicamente a cada execução do cron

### AC3: Warming com budget de tempo
- [ ] Timeout total do warming: 30 minutos
- [ ] Se ultrapassa budget, parar (próximas combinações serão aquecidas no próximo ciclo)
- [ ] Log: "Cache warming: 45/50 combinações aquecidas em 28min"
- [ ] Metric: `smartlic_cache_warming_duration_seconds`, `smartlic_cache_warming_combinations_total`

### AC4: Não interferir com buscas de usuário
- [ ] Warming jobs usam prioridade BAIXA (PNCP batching com delay extra: 3s entre UFs)
- [ ] Se busca de usuário em andamento, pausar warming (detectar via `active_searches` gauge)
- [ ] Circuit breaker: se PNCP rate-limited durante warming, parar imediatamente
- [ ] User_id para warming: usar user_id do admin ou system UUID especial

### AC5: Startup warming (cold start)
- [ ] No startup do web process, após `_check_cache_schema()`:
  - Verificar se cache está vazio (ou >4h stale para top combinations)
  - Se sim: disparar warming das top 10 combinações em background
  - NÃO bloquear startup — usar `asyncio.create_task()`
- [ ] Isso cobre cenários de redeploy (cache InMemory perdido)

### AC6: Testes
- [ ] Backend: test cache_warming_job executa e salva cache para N combinações
- [ ] Backend: test smart warming query retorna top combinações por frequência
- [ ] Backend: test budget timeout para warming em 30min
- [ ] Backend: test warming pausa quando busca de usuário ativa

---

## Arquivos Envolvidos

| Arquivo | Ação |
|---------|------|
| `backend/job_queue.py` | AC1: cache_warming_job function |
| `backend/cron_jobs.py` | AC1+AC5: scheduling + startup warming |
| `backend/search_cache.py` | AC2: query popular combinations |
| `backend/config.py` | AC1: CACHE_WARMING_ENABLED, CACHE_WARMING_INTERVAL, CACHE_WARMING_CONCURRENCY |
| `backend/metrics.py` | AC3: warming metrics |

---

## Decisões Técnicas

- **ARQ job > asyncio.create_task** — Warming é heavy (50 API calls). Deve rodar no worker process, não no web process.
- **4h interval** — Alinhado com InMemory TTL. Cache aquecido a cada 4h garante que nunca expira antes do próximo aquecimento.
- **Smart warming** — Lista estática funciona no MVP, mas analytics-driven escala melhor quando mais usuários entram.
- **System user_id** — Warming cache precisa de user_id para salvar. Usar UUID fixo de "system" e garantir que profiles tem esse UUID.

## Estimativa
- **Esforço:** 4-6h
- **Risco:** Baixo (job isolado, não afeta pipeline)
- **Squad:** @dev (cron + warming job) + @data-engineer (smart query) + @qa (validation)
