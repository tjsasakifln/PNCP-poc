# STORY-359: Transparência de degradação SSE para o usuário

**Prioridade:** P2
**Tipo:** fix (UX)
**Sprint:** Sprint 3
**Estimativa:** S
**Origem:** Conselho CTO Advisory Board — Auditoria de Promessas (2026-03-01)
**Dependências:** Nenhuma
**Bloqueado por:** —
**Bloqueia:** —
**Paralelo com:** STORY-353, STORY-358, STORY-360

---

## Contexto

Quando SSE falha, o frontend cai silenciosamente para progresso simulado baseado em tempo. O usuário vê barra de progresso avançando mas não sabe que é simulação. Se a busca falhar, a barra "mentiu". Transparência > perfeição.

## Promessa Afetada

> Confiança geral do usuário no sistema

## Causa Raiz

SSE fallback simulado é silencioso. `EnhancedLoadingProgress.tsx` usa time-based progress quando real SSE events não chegam. Sem indicação visual de que progresso é estimado.

## Critérios de Aceite

- [x] AC1: Quando SSE cai para fallback simulado, exibir indicador discreto: ícone de info + tooltip "Progresso estimado (conexão em tempo real indisponível)"
- [x] AC2: Se SSE reconectar com sucesso, remover indicador e mostrar progresso real
- [x] AC3: Não bloquear UX — indicador é informativo, não alarme (cor cinza/azul, não vermelho)
- [x] AC4: Prometheus counter `smartlic_sse_fallback_simulated_total` no frontend (via telemetry endpoint)
- [x] AC5: Testes: SSE fail → indicador aparece → SSE reconnect → indicador some

## Arquivos Afetados

- `frontend/components/EnhancedLoadingProgress.tsx` — replaced banner with discrete indicator (AC1-3)
- `frontend/hooks/useSearchSSE.ts` — fire-and-forget POST on fallback (AC4)
- `backend/metrics.py` — `SSE_FALLBACK_SIMULATED_TOTAL` counter (AC4)
- `backend/routes/metrics_api.py` — `POST /v1/metrics/sse-fallback` endpoint (AC4)
- `frontend/app/api/metrics/sse-fallback/route.ts` — Next.js proxy (AC4)
- `frontend/__tests__/sse-fallback-indicator.test.tsx` — 10 tests (AC5)
- `backend/tests/test_sse_fallback_telemetry.py` — 4 tests (AC4)
- `frontend/__tests__/EnhancedLoadingProgress.test.tsx` — updated assertions (AC1)
- `frontend/__tests__/gtm-fix-033-sse-resilience.test.tsx` — updated assertions (AC1)

## Validação

| Métrica | Threshold | Onde medir |
|---------|-----------|------------|
| `smartlic_sse_fallback_simulated_total` | Trending down | Prometheus |
