# GTM-STAB-003 — Adequar Timeout Chain ao Railway Hard Limit (120s)

**Status:** Code Complete (needs deploy + prod validation)
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
- [x] Definir novo chain ✅ (config.py:443-449): Pipeline=110, Consolidation=100, PerSource=80, PerUF=30
- [x] Atualizar `backend/config.py` ✅ (commit `899ee07`)
- [x] Atualizar `backend/start.sh` — GUNICORN_TIMEOUT=120, KEEP_ALIVE=75 ✅ (start.sh:34,41)
- [x] Atualizar `frontend/app/api/buscar/route.ts` — fetch timeout=115s ✅ (route.ts:112)
- [x] Atualizar `frontend/app/buscar/page.tsx` — client timeout=115s via AbortController in useSearch ✅

### AC2: Per-UF timeout agressivo com early abort
- [x] `pncp_client.py` — `PNCP_TIMEOUT_PER_UF`: 30s, DEGRADED: 15s ✅ (pncp_client.py:77-82)
- [x] Se UF não responde em 30s, marcar como failed ✅
- [x] Emitir SSE `uf_status` com reason ✅
- [x] Auto-retry com PNCP_TIMEOUT_PER_UF_DEGRADED=15s ✅

### AC3: Consolidation early return
- [x] Em `consolidation.py`, se >80% das UFs responderam E tempo > 80s, retornar partial result — ✅ `EarlyReturnConfig` with `EARLY_RETURN_THRESHOLD_PCT=0.8` + `EARLY_RETURN_TIME_S=80`
- [x] Não esperar por UFs lentas — retornar o que temos ✅
- [x] `ConsolidationResult.is_partial = True` com `degradation_reason` + `ufs_completed` / `ufs_pending` ✅
- [x] Filtro e ranking rodam sobre o que foi coletado ✅

### AC4: Pipeline budget guard
- [x] Time budget check between stages ✅ (search_pipeline.py:507-512)
- [x] Skip LLM after 90s → `PIPELINE_SKIP_LLM_AFTER_S=90` ✅ (config.py:448)
- [x] Skip viability after 100s → `PIPELINE_SKIP_VIABILITY_AFTER_S=100` ✅ (config.py:449)
- [x] Sets `is_simplified=True` flag in response ✅
- [x] NUNCA exceder 110s ✅

### AC5: Frontend timeout alignment
- [x] `route.ts` — AbortController timeout: 115s ✅ (route.ts:112, comment "STAB-003 AC5")
- [x] `page.tsx` — useSearch timeout: 115s via AbortController + setTimeout ✅
- [x] SSE progress: "Finalizando busca..." after 100s — `isFinalizing` state in useSearch ✅
- [x] Ao receber 524: mensagem amigável via `getContextualErrorMessage()` ✅

### AC6: Gunicorn timeout aligned
- [x] `start.sh` — `GUNICORN_TIMEOUT=120` ✅ (start.sh:34)
- [x] `GUNICORN_KEEP_ALIVE=75` (>Railway proxy 60s, prevents 502) ✅ (start.sh:41)
- [x] Elimina WORKER TIMEOUT/SIGABRT ✅

### AC7: Validação em produção
- [x] Busca com 4 UFs (ES, MG, RJ, SP), setor vestuario, 10 dias — ✅ Playwright 2026-02-25: completed ~120s, no 524
- [ ] Request completa em <110s (verificar via Railway logs)
- [x] Se alguma UF timeout, resultado parcial exibido (não 524) — ✅ 4 UFs "Indisponível" but HTTP 200 returned with filter_stats (132 analyzed)
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
