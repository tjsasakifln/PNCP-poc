# GTM-STAB-003 — Adequar Timeout Chain ao Railway Hard Limit (120s)

**Status:** To Do
**Priority:** P0 — Blocker (causa direta do HTTP 524 que o usuário vê)
**Severity:** Backend — busca excede 120s → Railway mata → 524
**Created:** 2026-02-24
**Sprint:** GTM Stabilization (imediato)
**Relates to:** GTM-INFRA-001 (timeout chain), GTM-FIX-029 (timeout chain fix), CRIT-012 (SSE heartbeat)
**Sentry:** WORKER TIMEOUT pid:4 (4), SIGABRT (4), CancelledError consolidation (3), failed to pipe response (19)

---

## Problema

O Railway tem um **hard proxy timeout de ~120 segundos**. Qualquer request que exceda esse tempo é terminado pelo proxy Railway com um 524 (ou o equivalente — a conexão é simplesmente cortada).

### Timeout chain atual (EXCEDE Railway):

```
Frontend fetch:        480s  ← ABSURDO — nunca vai ser honrado
Next.js proxy:         480s  ← Idem
Pipeline total:        360s  ← 3x o limite Railway
Consolidation:         300s  ← 2.5x
Per-Source (PNCP):     180s  ← 1.5x
Per-UF:                 90s  ← OK individual, mas soma > 120s
Gunicorn worker:       180s  ← Worker sobrevive, Railway não
```

### O que acontece:
1. Usuário busca 4 UFs (ES, MG, RJ, SP)
2. PNCP em batches de 5 → 1 batch, mas cada UF pode levar até 90s
3. Se 2 UFs demoram (MG=60s, SP=70s), total já é >120s
4. Railway corta → Gunicorn detecta client disconnect → eventual SIGABRT
5. SSE stream morre → "failed to pipe response" no frontend
6. Usuário vê 524 com "Erro ao buscar licitações"

### Por que piorou:
- PNCP API ficou mais lenta (rate limits mais agressivos pós-fev 2026)
- Sem cache funcional (GTM-STAB-001), toda busca é fresh → demora mais
- Default 10 dias de período → mais páginas por UF → mais tempo

---

## Acceptance Criteria

### AC1: Reduzir timeout chain para caber em 110s (margem de 10s)
- [ ] Definir novo chain:
  ```
  Railway hard limit:    120s  (imutável)
  Frontend fetch:        115s  (margem 5s para cleanup)
  Next.js proxy:         115s
  Pipeline total:        110s  (margem 10s)
  Consolidation:         100s  (margem 10s)
  Per-Source (PNCP):      80s  (cabe no consolidation)
  Per-UF:                 30s  (agressivo mas funcional)
  Gunicorn worker:       120s  (match Railway, não maior)
  ```
- [ ] Atualizar `backend/config.py` — `CONSOLIDATION_TIMEOUT`, `PNCP_TIMEOUT_PER_UF`, etc.
- [ ] Atualizar `backend/start.sh` — `GUNICORN_TIMEOUT` default 180→120
- [ ] Atualizar `frontend/app/api/buscar/route.ts` — fetch timeout
- [ ] Atualizar `frontend/app/buscar/page.tsx` — client timeout

### AC2: Per-UF timeout agressivo com early abort
- [ ] `pncp_client.py` — `PNCP_TIMEOUT_PER_UF`: 90s → 30s
- [ ] Se UF não responde em 30s, marcar como failed e mover para próxima
- [ ] Emitir SSE `uf_status("MG", "failed", reason="timeout_30s")` imediatamente
- [ ] Auto-retry (se existir) com timeout 15s (não 120s como hoje — `PNCP_TIMEOUT_PER_UF_DEGRADED`)

### AC3: Consolidation early return
- [ ] Em `consolidation.py`, se >80% das UFs responderam E tempo > 80s, retornar partial result
- [ ] Não esperar por UFs lentas — retornar o que temos
- [ ] `ConsolidationResult.is_partial = True` com `degradation_reason` explicando quais UFs ficaram de fora
- [ ] Filtro e ranking rodam sobre o que foi coletado

### AC4: Pipeline budget guard
- [ ] Em `search_pipeline.py`, adicionar "time budget" check entre cada estágio
- [ ] Se `elapsed > 90s` antes de entrar em filtering, skip LLM classification (usar keyword-only)
- [ ] Se `elapsed > 100s` antes de viability, skip viability assessment
- [ ] Cada skip deve setar flag no response para frontend exibir "Resultados simplificados"
- [ ] NUNCA exceder 110s — retornar o que tiver, mesmo que incompleto

### AC5: Frontend timeout alignment
- [ ] `frontend/app/api/buscar/route.ts` — AbortController timeout: 115s
- [ ] `frontend/app/buscar/page.tsx` — useSearch timeout: 115s
- [ ] SSE progress: se 100s sem evento `complete`, exibir "Finalizando busca..." (não esperar indefinidamente)
- [ ] Ao receber 524: exibir mensagem amigável, NÃO "Erro ao buscar licitações"

### AC6: Gunicorn timeout aligned
- [ ] `start.sh` — `GUNICORN_TIMEOUT=120` (match Railway, was 180)
- [ ] `GUNICORN_GRACEFUL_TIMEOUT=30` (was 120 — não precisa de 2min para graceful)
- [ ] Isso elimina WORKER TIMEOUT e SIGABRT (Railway mata antes do Gunicorn)

### AC7: Validação em produção
- [ ] Busca com 4 UFs (ES, MG, RJ, SP), setor vestuario, 10 dias
- [ ] Request completa em <110s (verificar via Railway logs)
- [ ] Se alguma UF timeout, resultado parcial exibido (não 524)
- [ ] Sentry: 0 novos WORKER TIMEOUT em 24h
- [ ] Sentry: 0 novos "failed to pipe response" em 24h

---

## Arquivos Envolvidos

| Arquivo | Ação |
|---------|------|
| `backend/config.py` | Timeouts: CONSOLIDATION_TIMEOUT, PNCP_TIMEOUT_PER_UF, PIPELINE_TIMEOUT |
| `backend/start.sh:37-47` | GUNICORN_TIMEOUT 180→120, GRACEFUL_TIMEOUT 120→30 |
| `backend/search_pipeline.py` | AC4: time budget guard entre estágios |
| `backend/consolidation.py` | AC3: early return quando >80% UFs + >80s |
| `backend/pncp_client.py` | AC2: per-UF 90→30s, retry 120→15s |
| `frontend/app/api/buscar/route.ts` | AC5: fetch timeout 480→115s |
| `frontend/app/buscar/page.tsx` | AC5: useSearch timeout 480→115s |

---

## Decisões Técnicas

- **30s per-UF é agressivo mas correto** — PNCP saudável responde em 2-8s. 30s captura lentos sem matar o orçamento total. Se demorar >30s, provavelmente vai timeout de qualquer forma.
- **Early return > esperar tudo** — Enterprise UX = "resultados parciais rápidos" > "resultados completos depois de 3min de loading"
- **Time budget guard** — Pattern comum em pipelines (Elasticsearch usa, Google Search usa). Cada estágio tem orçamento, quando acaba, simplifica processamento.
- **Gunicorn = Railway** — Manter Gunicorn timeout ≤ Railway elimina SIGABRT (Railway mata primeiro, Gunicorn nunca precisa)

## Estimativa
- **Esforço:** 4-6h
- **Risco:** Médio (redução de timeout pode causar mais partial results, mas melhor que 524)
- **Squad:** @dev (backend timeout chain) + @dev (frontend alignment) + @qa (E2E timing tests)
